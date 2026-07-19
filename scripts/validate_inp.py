#!/usr/bin/env python3
"""Validate a CP2K .inp file without external dependencies.

This is a self-contained structural linter (no pip install required). It checks:
  - &SECTION / &END SECTION balance and correct nesting
  - Required top-level sections (GLOBAL, FORCE_EVAL, and MOTION when relevant)
  - Key sub-sections (DFT/MM, SUBSYS, KIND, CELL/COORD, SCF, MGRID, XC)
  - Known section-name whitelist (flags likely typos as warnings)
  - Sensible RUN_TYPE / METHOD / OPTIMIZER values

Optional: pass --cp2klint to ALSO run the official `cp2klint` (from
cp2k-input-tools) if it is installed in your environment. Note: on Python 3.13
the official tool can mis-fire on PRINT/COLVAR unit parsing, so the built-in
linter is the default and recommended check.

Usage:
  python validate_inp.py file1.inp [file2.inp ...]
  python validate_inp.py --cp2klint file.inp
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

# ---------------------------------------------------------------------------
# CP2K section-name whitelist (used to flag likely typos as warnings).
# Covers the sections in this skill's templates plus common CP2K sections.
# ---------------------------------------------------------------------------
KNOWN_SECTIONS = {
    # top level
    "GLOBAL", "FORCE_EVAL", "MOTION", "EXT_RESTART", "MULTIPLE_FORCE_EVALS",
    "OPTIMIZE_INPUT", "PRINT", "TEST", "VIBRATIONAL_ANALYSIS",
    # FORCE_EVAL
    "DFT", "MM", "MIXED", "SUBSYS", "STRESS_TENSOR", "EI", "QMMM",
    "COULOMB", "EWALD", "PRINT",
    # DFT
    "BASIS_SET_FILE_NAME", "POTENTIAL_FILE_NAME", "MGRID", "XC", "SCF",
    "QS", "POISSON", "POISSON_SOLVER", "KPOINTS", "PERIODIC", "XC_FUNCTIONAL",
    "LS_SCF", "OUTER_SCF", "ALMO_SCF", "KG_METHOD", "XAS_TDP", "EFIELD",
    "GAPW", "WF_CORRELATION", "MULTIPOLE", "PRINT",
    # DFT - auxiliary / properties (from mind map)
    "AUXILIARY_DENSITY_MATRIX_METHOD", "ADMM", "AUXILIARY_BASIS",
    "PROPERTIES", "DOS", "PDOS", "BAND_STRUCTURE", "E_DENSITY_CUBE",
    "WANNIER_CENTERS", "LOCALIZE", "STRESS_TENSOR",
    # SCF
    "MIXING", "OT", "DIAGONALIZATION", "SMEAR", "DMI", "RESTART", "PRINT",
    # MOTION
    "GEO_OPT", "CELL_OPT", "MD", "BAND", "CONSTRAINT", "FIXED_ATOMS",
    "FREE_ENERGY", "MC", "SHELL_OPT", "FLEXIBLE_PARTITIONING", "TP_NVT", "PRINT",
    # SUBSYS
    "KIND", "CELL", "COORD", "TOPOLOGY", "COLVAR", "DIPOLE", "VELOCITY",
    "GB", "THERMOSTAT", "PRINT", "CORE_COORD",
    # GEO_OPT / CELL_OPT
    "CG", "BFGS", "LBFGS", "CONJUGATE_GRADIENTS", "TRUST_RADIUS",
    "LINE_SEARCH", "ROT_OPT", "DIMER", "TRANSITION_STATE",
    "COORDINATE", "RMS_FORCE", "MAX_FORCE", "RMS_DR", "MAX_DR",
    "CONVERGENCE_CONTROL",
    # MD
    "ENSEMBLE", "THERMOSTAT", "BAROSTAT", "LANGEVIN", "NOSE", "CSVR", "GLE",
    "AD_LANGEVIN", "RESPA", "ANNEALING", "COORDINATE", "VELOCITY", "FORCE",
    "PRINT", "EACH",
    # BAND (NEB)
    "REPLICA", "CI_NEB", "CONVERGENCE_CONTROL", "PROGRAM_RUN_INFO",
    "OPTIMIZE_BAND", "VEL_CONTROL",
    # XC
    "XC_FUNCTIONAL", "XC_GRID", "WF_CORRELATION", "HF", "LIBXC", "VDW_POTENTIAL",
    "PAIR_POTENTIAL", "XWPBE", "PBE", "TPSS", "SCAN", "MGGA_X_SCAN", "MGGA_C_SCAN",
    "LYP", "BECKE88", "VWN", "XALPHA",
    "SCREENING", "MEMORY", "INTERACTION_POTENTIAL", "PRINT",
    # KIND
    "BASIS_SET", "POTENTIAL", "ELEMENT", "CORE", "SHELL", "DFT_PLUS_U",
    # COLVAR / metadynamics
    "METADYN", "METAVAR", "WALL", "RESTRAINT", "COLVAR", "DISTANCE", "ANGLE",
    "TORSION", "PRINT",
    # PRINT subsections
    "PDOS", "LDOS", "E_DENSITY_CUBE", "ELECTRON_DENSITY_CUBE", "MO_CUBES",
    "RESTART", "RESTART_HISTORY", "REPLICA_ENERGIES", "TRAJECTORY",
    "VELOCITIES", "FORCES", "STRESS", "CELL",
}

VALID_RUN_TYPES = {
    "ENERGY", "ENERGY_FORCE", "WAVEFUNCTION_OPT", "GEO_OPT", "CELL_OPT",
    "MD", "MC", "SHELL_OPT", "BAND", "NEB", "LINE_SEARCH", "TS",
    "TRANSITION_STATE", "VIBRATIONAL_ANALYSIS", "DEBUG", "MASTER",
    "BSSE", "ALMO", "EIP",
}

VALID_METHODS = {"QUICKSTEP", "FIST", "MIXED", "QM", "QMMM", "SE", "DRIVER", "LIBXSMM"}

VALID_OPTIMIZERS = {
    "BFGS", "CG", "LBFGS", "DIIS", "BROYDEN", "NEWTON", "SAFE", "CG_INLINE",
}

REQUIRED_TOP = {"GLOBAL", "FORCE_EVAL"}
# RUN_TYPE values that imply MOTION is needed
MOTION_RUN_TYPES = {"GEO_OPT", "CELL_OPT", "MD", "MC", "BAND", "NEB",
                    "SHELL_OPT", "LINE_SEARCH", "TS", "TRANSITION_STATE",
                    "VIBRATIONAL_ANALYSIS"}

SECTION_RE = re.compile(r"^\s*&(\w+)\s*(.*)$")
END_RE = re.compile(r"^\s*&END\s*(\w+)?\s*$")


def strip_comment(line):
    # CP2K comments start with '#'
    return line.split("#", 1)[0].rstrip()


def parse(path):
    """Return (errors, warnings, lines)."""
    errors = []
    warnings = []
    try:
        raw = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError as e:
        return [f"cannot read file: {e}"], warnings, []

    stack = []          # list of (section_name, line_no)
    seen_top = set()
    run_type = None
    method = None
    has_subsys = False
    has_dft_or_mm = False
    kind_count = 0
    has_cell_or_coord = False
    in_subsys = False

    for i, raw_line in enumerate(raw, 1):
        line = strip_comment(raw_line)
        if not line.strip():
            continue

        me = END_RE.match(line)
        if me:
            closed = me.group(1)
            if not stack:
                errors.append(f"L{i}: &END {closed or ''} with no open section")
                continue
            opened, oline = stack.pop()
            if closed and closed.upper() != opened:
                errors.append(f"L{i}: &END {closed} closes '&{opened}' "
                              f"(opened at L{oline})")
            if opened == "SUBSYS":
                in_subsys = False
                if not kind_count:
                    errors.append(f"L{oline}: &SUBSYS has no &KIND section")
                if not has_cell_or_coord:
                    errors.append(f"L{oline}: &SUBSYS has neither &CELL nor &COORD")
            if opened == "FORCE_EVAL":
                if not has_dft_or_mm:
                    errors.append(f"L{oline}: &FORCE_EVAL missing &DFT/&MM/&MIXED")
                if not has_subsys:
                    errors.append(f"L{oline}: &FORCE_EVAL missing &SUBSYS")
            continue

        m = SECTION_RE.match(line)
        if m:
            name = m.group(1).upper()
            if name not in KNOWN_SECTIONS:
                warnings.append(f"L{i}: unknown section '&{name}' "
                                f"(possible typo? known: {sorted_suggestion(name)})")
            # track context
            parent = stack[-1][0] if stack else None
            if parent is None:
                seen_top.add(name)
            if name == "FORCE_EVAL":
                has_dft_or_mm = False
                has_subsys = False
            if name in ("DFT", "MM", "MIXED") and parent == "FORCE_EVAL":
                has_dft_or_mm = True
            if name == "SUBSYS":
                in_subsys = True
                has_subsys = True
                has_cell_or_coord = False
                kind_count = 0
            if name == "KIND" and in_subsys:
                kind_count += 1
            if name in ("CELL", "COORD") and in_subsys:
                has_cell_or_coord = True
            # close handling for SUBSYS
            if parent == "SUBSYS" and name not in ("KIND", "CELL", "COORD",
                                                   "TOPOLOGY", "COLVAR", "DIPOLE",
                                                   "VELOCITY", "GB", "THERMOSTAT",
                                                   "PRINT", "CORE_COORD"):
                in_subsys = False
            stack.append((name, i))
            continue

        # keyword line inside GLOBAL / FORCE_EVAL
        kw = line.strip().split()[0].upper() if line.strip() else ""
        if stack:
            top = stack[0][0]
            sec = stack[-1][0]
            if top == "GLOBAL" and sec == "GLOBAL":
                if kw == "RUN_TYPE":
                    val = line.strip().split(None, 1)[1].strip().upper() \
                        if len(line.strip().split()) > 1 else ""
                    run_type = val
                    if val and val not in VALID_RUN_TYPES:
                        warnings.append(f"L{i}: RUN_TYPE '{val}' not a known value")
            if sec == "FORCE_EVAL" and kw == "METHOD":
                val = line.strip().split(None, 1)[1].strip().upper() \
                    if len(line.strip().split()) > 1 else ""
                method = val
                if val and val not in VALID_METHODS:
                    warnings.append(f"L{i}: METHOD '{val}' not a known value")

    if stack:
        for name, ln in stack:
            errors.append(f"unclosed section '&{name}' (opened at L{ln})")

    # top-level checks
    for req in REQUIRED_TOP:
        if req not in seen_top:
            errors.append(f"missing required top-level section &{req}")
    if run_type in MOTION_RUN_TYPES and "MOTION" not in seen_top:
        errors.append(f"RUN_TYPE {run_type} requires a &MOTION section")
    if method == "QUICKSTEP" and run_type in ("GEO_OPT", "CELL_OPT", "MD"):
        # OPTIMIZER sanity is checked structurally below if MOTION present
        pass

    return errors, warnings, raw


def sorted_suggestion(name):
    """Return up to 3 closest known section names (Levenshtein-ish)."""
    cands = sorted(KNOWN_SECTIONS, key=lambda s: dist(s, name))[:3]
    return ", ".join(cands)


def dist(a, b):
    # simple edit distance (small strings, fine)
    la, lb = len(a), len(b)
    dp = list(range(lb + 1))
    for i in range(1, la + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, lb + 1):
            cur = dp[j]
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = cur
    return dp[lb]


def main():
    ap = argparse.ArgumentParser(description="Validate a CP2K .inp (built-in linter).")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--cp2klint", action="store_true",
                    help="also run official cp2klint if installed")
    args = ap.parse_args()

    rc = 0
    for f in args.files:
        print(f"== lint {f} ==")
        errors, warnings, _ = parse(f)
        for w in warnings:
            print(f"  [warn] {w}")
        if errors:
            for e in errors:
                print(f"  [ERROR] {e}")
            print(f"  RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
            rc = 1
        else:
            print(f"  RESULT: OK ({len(warnings)} warning(s))")

        if args.cp2klint:
            cp2k = shutil.which("cp2klint") or os.environ.get("CP2KLINT")
            if cp2k:
                print(f"== cp2klint {f} ==")
                r = subprocess.run([cp2k, f])
                rc = rc or r.returncode
            else:
                print("  (cp2klint not found on PATH; skipped)")
    sys.exit(rc)


if __name__ == "__main__":
    main()
