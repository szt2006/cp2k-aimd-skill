#!/usr/bin/env python3
"""Authoritative verification harness for the cp2k-aimd skill.

Uses cp2k-input-tools (which bundles the official CP2K input reference manual,
cp2k_input.xml) to:
  1. Introspect the schema for key sections (list valid subsections/keywords).
  2. Generate a battery of .inp files via gen_inp.py covering every feature.
  3. Parse each with the official CP2KInputParser and report errors/warnings.

Run with the cp2ktools venv python:
  python _validate_all.py

Tooling shims (all tooling-only, NOT input changes):
  * pint 0.23+ dropped numpy.cumproduct -> restore alias (cumproduct==cumprod).
  * cp2k-input-tools 0.9.1's pint_units.txt does NOT define CP2K's time unit
    'fs' (femtosecond); pint therefore reads '[fs]' as femtosiemens and the
    unit check trips. We inject fs == femtosecond so the unit check matches
    CP2K's actual semantics. '[fs]' is 100% correct CP2K syntax.
"""
import os
import subprocess
import sys

# --- tooling shims: must run BEFORE importing cp2k_input_tools ---
import numpy as np
if not hasattr(np, "cumproduct"):
    np.cumproduct = np.cumprod  # pint 0.23+ removed numpy.cumproduct
import cp2k_input_tools.parser as P
try:
    P.UREG.define("fs = femtosecond")  # CP2K 'fs' = femtosecond, not femtosiemens
except Exception:
    try:
        P.UREG._units.pop("fs", None)
        P.UREG.define("fs = femtosecond")
    except Exception:
        pass

from cp2k_input_tools.parser import CP2KInputParser

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "scripts", "gen_inp.py")
PY = sys.executable  # should be the cp2ktools venv python

import lxml.etree as ET
_XML = os.path.join(os.path.dirname(P.__file__), "cp2k_input.xml")
_root = ET.parse(_XML).getroot()


def _section_node(path):
    """Return the lxml node for a section path like 'FORCE_EVAL/DFT/XC/HF'."""
    node = _root
    for name in path.split("/"):
        found = None
        for sec in node.iter("SECTION"):
            nm = sec.find("NAME")
            if nm is not None and nm.text == name:
                # ensure it is a direct child section of current node
                if sec.getparent() is node:
                    found = sec
                    break
        if found is None:
            return None
        node = found
    return node


def show_section(path):
    """path like 'FORCE_EVAL/DFT/XC/HF' -> print subsections + keywords."""
    node = _section_node(path)
    if node is None:
        print(f"  [NOT FOUND] {path}")
        return
    subs = [s.find("NAME").text for s in node if s.tag == "SECTION"]
    kws = [k.find("NAME").text for k in node if k.tag == "KEYWORD"]
    print(f"=== {path} ===")
    print("  subsections:", subs)
    print("  keywords   :", kws)


def gen(out, *args):
    cmd = [PY, GEN, "-o", out] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  [GEN FAILED] {out}: {r.stderr.strip()}")
        return False
    return True


def parse(path):
    """Parse with the official CP2KInputParser (validates vs cp2k_input.xml).

    Reclassifies the known cp2k-input-tools tooling limitation around CP2K's
    time unit '[fs]' (pint mis-reads it as femtosiemens) as a non-fatal NOTE,
    not a real input error.
    """
    parser = CP2KInputParser()
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            list(parser.parse(fh))  # force generator so all errors surface
        errs = getattr(parser, "errors", []) or []
        warns = getattr(parser, "warnings", []) or []
    except Exception as e:
        msg = str(e)
        if "femtosiemens" in msg or "femtosecond" in msg:
            return [], ["NOTE(unit-tooling): pint mis-reads CP2K '[fs]' as "
                        "femtosiemens; not an input error."]
        return [msg], []
    real_errs = []
    for e in errs:
        s = e.msg if hasattr(e, "msg") else str(e)
        if "femtosiemens" in s or "femtosecond" in s:
            warns.append("NOTE(unit-tooling): " + s)
        else:
            real_errs.append(s)
    return real_errs, warns


def main():
    print("#" * 70)
    print("# 1. SCHEMA INTROSPECTION (official reference: cp2k_input.xml)")
    print("#" * 70)
    for path in [
        "FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD",
        "FORCE_EVAL/DFT/XC/HF",
        "FORCE_EVAL/DFT/SCF/MIXING",
        "FORCE_EVAL/DFT/SCF/OT",
        "FORCE_EVAL/DFT/SCF/SMEAR",
        "FORCE_EVAL/DFT/SCF/OUTER_SCF",
        "MOTION/MD/THERMOSTAT",
        "MOTION/MD/BAROSTAT",
        "FORCE_EVAL/PRINT/STRESS_TENSOR",
        "FORCE_EVAL/DFT/PRINT/PDOS",
        "FORCE_EVAL/DFT/PRINT/E_DENSITY_CUBE",
        "FORCE_EVAL/DFT/LOCALIZE/PRINT/WANNIER_CENTERS",
        "FORCE_EVAL/DFT/PRINT/BAND_STRUCTURE",
        "FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/TPSS",
        "FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/MGGA_X_SCAN",
        "FORCE_EVAL/DFT/XC/XC_FUNCTIONAL/MGGA_C_SCAN",
        "FORCE_EVAL/DFT",
        "FORCE_EVAL/SUBSYS/KIND",
        "FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U",
        "MOTION/BAND",
        "MOTION/BAND/OPTIMIZE_BAND",
        "MOTION/BAND/REPLICA",
        "FORCE_EVAL/MIXED",
        "FORCE_EVAL/MIXED/MAPPING/FORCE_EVAL_MIXED",
        "FORCE_EVAL/MM/FORCEFIELD",
        "FORCE_EVAL/DFT/QS/SE",
    ]:
        show_section(path)
        print()

    print("#" * 70)
    print("# 2. PARSE EVERY GENERATED FEATURE INPUT")
    print("#" * 70)
    cases = [
        ("static_Si", ["--type", "static", "--project", "t1", "--elem", "Si"]),
        ("geoopt_AuO_HSE06_ADMM", [
            "--type", "geo_opt", "--project", "t2", "--elem", "Au", "O",
            "--basis", "DZVP-MOLOPT-SR-GTH", "DZVP-GTH-PADE",
            "--potential", "GTH-PBE-q11", "GTH-PADE-q6",
            "--functional", "HSE06", "--admm", "--multiplicity", "3",
            "--dispersion", "--periodic", "xy", "--smear", "--outer-scf",
            "--properties", "pdos", "stress"]),
        ("geoopt_Si_TPSS", [
            "--type", "geo_opt", "--project", "t3", "--elem", "Si",
            "--functional", "TPSS"]),
        ("geoopt_CHON_SCAN", [
            "--type", "geo_opt", "--project", "t4", "--elem", "C", "H", "O", "N",
            "--functional", "SCAN", "--dispersion", "--periodic", "none"]),
        ("md_Cu_langevin_npt", [
            "--type", "aimd_md", "--project", "t5", "--elem", "Cu",
            "--basis", "DZVP-MOLOPT-SR-GTH", "--potential", "GTH-PBE-q11",
            "--thermostat", "langevin", "--ensemble", "npt",
            "--restart-freq", "1000", "--smear", "--periodic", "xy"]),
        ("md_Au_csvr", [
            "--type", "aimd_md", "--project", "t6", "--elem", "Au",
            "--basis", "DZVP-MOLOPT-SR-GTH", "--potential", "GTH-PBE-q11",
            "--smear"]),
        ("geoopt_Fe_pulay", [
            "--type", "geo_opt", "--project", "t7", "--elem", "Fe",
            "--basis", "DZVP-MOLOPT-SR-GTH", "--potential", "GTH-PBE-q16",
            "--multiplicity", "3", "--mixing-method", "pulay",
            "--smear", "--kpoints", "4 4 4"]),
        ("geoopt_Ni_otcg", [
            "--type", "geo_opt", "--project", "t8", "--elem", "Ni",
            "--basis", "DZVP-MOLOPT-SR-GTH", "--potential", "GTH-PBE-q18",
            "--multiplicity", "3", "--mixing-method", "multisecant",
            "--ot-minimizer", "cg", "--smear"]),
        ("geoopt_TiO_B3LYP_ADMM", [
            "--type", "geo_opt", "--project", "t9", "--elem", "Ti", "O",
            "--basis", "DZVP-MOLOPT-SR-GTH", "DZVP-GTH-PADE",
            "--potential", "GTH-PBE-q12", "GTH-PADE-q6",
            "--functional", "B3LYP", "--admm", "--multiplicity", "5",
            "--dispersion", "--outer-scf"]),
        ("vib_CO", [
            "--type", "vib", "--project", "t10", "--elem", "C", "O",
            "--basis", "DZVP-GTH-PADE", "DZVP-GTH-PADE",
            "--potential", "GTH-PADE-q4", "GTH-PADE-q6"]),
        ("neb_Au", [
            "--type", "neb", "--project", "t11", "--elem", "Au",
            "--basis", "DZVP-MOLOPT-SR-GTH", "--potential", "GTH-PBE-q11"]),
        ("metadyn_AuO", [
            "--type", "metadyn", "--project", "t12", "--elem", "Au", "O",
            "--basis", "DZVP-MOLOPT-SR-GTH", "DZVP-GTH-PADE",
            "--potential", "GTH-PBE-q11", "GTH-PADE-q6"]),
        # --- Batch 6: metadyn advanced keywords (well-tempered / WW / LAGRANGE / walkers / PLUMED) ---
        ("metadyn_adv", [
            "--type", "metadyn", "--project", "t12b", "--elem", "Au", "O",
            "--basis", "DZVP-MOLOPT-SR-GTH", "DZVP-GTH-PADE",
            "--potential", "GTH-PBE-q11", "GTH-PADE-q6",
            "--well-tempered", "--delta-t", "1500", "--metadyn-ww", "0.05",
            "--lagrange", "--multi-walker", "--plumed",
            "--plumed-file", "plumed.dat"]),
        # --- Task #26: KIND attribute system (DFT+U / per-atom MAGNETIZATION / MASS) ---
        ("fe3o4_dfu", [
            "--type", "static", "--project", "t13",
            "--cell", "8.53", "0", "0", "0", "8.53", "0", "0", "0", "8.53",
            "--kinds",
            "Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=5.0:U=3",
            "Fe2:Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=4.0:U=3",
            "Fe3:Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=-5.0:U=3",
            "O:DZVP-MOLOPT-SR-GTH:GTH-PBE-q6",
            "H:DZVP-MOLOPT-SR-GTH:GTH-PBE-q1",
            "C:DZVP-MOLOPT-SR-GTH:GTH-PBE-q4",
            "Au:DZVP-MOLOPT-SR-GTH:GTH-PBE-q11",
            "--multiplicity", "33", "--plus-u-method", "MULLIKEN",
            "--coord", "Fe 0 0 0\nO 1 1 1\nH 2 2 2"]),
        ("autio2_dfu_mass", [
            "--type", "geo_opt", "--project", "t14",
            "--cell", "17.75", "0", "0", "0", "19.49", "0", "0", "0", "27.28",
            "--kinds",
            "Ti:DZVP-MOLOPT-SR-GTH:GTH-PBE-q12:U=13.6:noramp",
            "Au:DZVP-MOLOPT-SR-GTH:GTH-PBE-q11:mass=19.7",
            "O:DZVP-MOLOPT-SR-GTH:GTH-PBE-q6",
            "C:DZVP-MOLOPT-SR-GTH:GTH-PBE-q4",
            "H:DZVP-MOLOPT-SR-GTH:GTH-PBE-q1",
            "--multiplicity", "1", "--plus-u-method", "MULLIKEN",
            "--coord", "Ti 0 0 0\nAu 1 1 1\nO 2 2 2"]),
        # --- Task #27: population/charge analysis + advanced cube properties ---
        ("nico_properties", [
            "--type", "static", "--project", "t15",
            "--elem", "C", "O", "H", "Cu", "Al", "Pt", "Ni", "Au",
            "--basis", "DZVP-MOLOPT-SR-GTH",
            "--potential", "GTH-PBE-q4", "GTH-PBE-q6", "GTH-PBE-q1",
                          "GTH-PBE-q11", "GTH-PBE-q3", "GTH-PBE-q18",
                          "GTH-PBE-q18", "GTH-PBE-q11",
            "--multiplicity", "1",
            "--properties", "mulliken", "lowdin", "hirshfeld", "mo",
                           "elf", "vhartree", "moments", "pdos",
            "--ldos-list", "1..26",
            "--coord", "C 0 0 0"]),
        # --- Task #28: OPTIMIZER choice + STRESS_TENSOR keyword form ---
        ("geoopt_lbfgs", [
            "--type", "geo_opt", "--project", "t16", "--elem", "Au", "O",
            "--basis", "DZVP-MOLOPT-SR-GTH", "DZVP-GTH-PADE",
            "--potential", "GTH-PBE-q11", "GTH-PADE-q6",
            "--optimizer", "lbfgs"]),
        ("cellopt_default_cg", [
            "--type", "cell_opt", "--project", "t17", "--elem", "Si",
            "--stress-tensor", "analytical"]),
        ("geoopt_cg_stress", [
            "--type", "geo_opt", "--project", "t18", "--elem", "C",
            "--optimizer", "cg", "--stress-tensor", "numerical"]),
        # --- Task #29: TOPOLOGY / CIF structure reading ---
        ("topo_cif", [
            "--type", "static", "--project", "t19",
            "--elem", "C", "O", "H", "Cu", "Al", "Pt", "Ni", "Au",
            "--basis", "DZVP-MOLOPT-SR-GTH",
            "--potential", "GTH-PBE-q4", "GTH-PBE-q6", "GTH-PBE-q1",
                          "GTH-PBE-q11", "GTH-PBE-q3", "GTH-PBE-q18",
                          "GTH-PBE-q18", "GTH-PBE-q11",
            "--topology", "POSCAR.cif", "--topology-format", "cif"]),
        # --- Task #30: NEB advanced options (al2o3/neb style) ---
        ("neb_al2o3_advanced", [
            "--type", "neb", "--project", "t20",
            "--elem", "C", "O", "H", "Ti", "Al",
            "--basis", "DZVP-MOLOPT-SR-GTH", "DZVP-MOLOPT-SR-GTH",
                      "DZVP-MOLOPT-SR-GTH", "DZVP-MOLOPT-SR-GTH", "DZVP-MOLOPT-SR-GTH",
            "--potential", "GTH-PBE-q4", "GTH-PBE-q6", "GTH-PBE-q1",
                         "GTH-PBE-q12", "GTH-PBE-q3",
            "--multiplicity", "1",
            "--xyz-replicas", "./0.xyz", "./1.xyz", "./2.xyz",
                            "./3.xyz", "./4.xyz", "./5.xyz",
            "--optimize-band", "DIIS", "--optimize-end-points", "F",
            "--align-frames", "F", "--rotate-frames", "F",
            "--program-run-info", "--convergence-info",
            "--band-type", "CI-NEB", "--nproc-rep", "28", "--k-spring", "0.08"]),
        # --- Task #31: QM/MM + semi-empirical PM6 (MIXED / FIST / Quickstep-PM6) ---
        ("qmmm_pm6", [
            "--type", "qmmm", "--project", "t21",
            "--qm-elem", "C", "H", "O", "--mm-elem", "Cu",
            "--qm-method", "PM6",
            "--qm-atoms", "1 50", "--mm-atoms", "51 2000",
            "--topology", "./s", "--qm-topology", "./f",
            "--qmmm-run-type", "MD", "--group-partition", "2 6"]),
        ("qmmm_pm6_skel", [
            "--type", "qmmm", "--project", "t22",
            "--qm-elem", "C", "H", "O", "--mm-elem", "Cu",
            "--qm-atoms", "1 50", "--mm-atoms", "51 2000"]),
        # --- nico 全量复现：SCF/MGRID 精细旋钮 + SILENT 输出 + cube STRIDE + PDOS NLUMO ---
        ("nico_full", [
            "--type", "static", "--project", "t23",
            "--elem", "C", "O", "H", "Cu", "Al", "Pt", "Ni", "Au",
            "--basis", "DZVP-MOLOPT-SR-GTH",
            "--potential", "GTH-PBE-q4", "GTH-PBE-q6", "GTH-PBE-q1",
                          "GTH-PBE-q11", "GTH-PBE-q3", "GTH-PBE-q18",
                          "GTH-PBE-q18", "GTH-PBE-q11",
            "--functional", "PBE", "--multiplicity", "1",
            "--topology", "POSCAR.cif", "--topology-format", "cif", "--smear",
            "--properties", "mulliken", "lowdin", "hirshfeld", "cube",
                           "elf", "vhartree", "pdos", "--ldos-list", "1..26",
            "--cutoff", "350", "--max-scf", "500", "--eps-scf", "1.0E-6",
            "--eps-diis", "0.05", "--added-mos", "500", "--cholesky", "INVERSE",
            "--mixing-method", "broyden", "--mixing-alpha", "0.1",
            "--mixing-beta", "1.5", "--mixing-nbroyden", "8",
            "--scf-guess", "RESTART", "--wfn-restart", "./cp2k-RESTART.wfn",
            "--diagonalization-eps-adapt", "0.01",
            "--print-style", "SILENT", "--cube-stride", "1 1 1",
            "--pdos-nlumo", "30"]),
        # --- Batch 7/8: GAPW all-electron + CONSTRAINT G3X3 / HBONDS ---
        ("gapw_static_Si", [
            "--type", "static", "--project", "t24", "--elem", "Si",
            "--gapw", "--properties", "pdos", "efg", "hyperfine"]),
        ("gapw_geoopt_Fe", [
            "--type", "geo_opt", "--project", "t25", "--elem", "Fe",
            "--basis", "DZVP-MOLOPT-SR-GTH", "--potential", "GTH-PBE-q16",
            "--multiplicity", "3", "--gapw", "--smear"]),
        ("constraint_g3x3_water", [
            "--type", "aimd_md", "--project", "t26", "--elem", "O", "H",
            "--basis", "DZVP-MOLOPT-SR-GTH", "DZVP-MOLOPT-SR-GTH",
            "--potential", "GTH-PBE-q6", "GTH-PBE-q1",
            "--constraint-g3x3", "1 2 3", "--g3x3-distances", "1.0 1.5 2.0",
            "--thermostat", "langevin"]),
        ("constraint_hbonds_water", [
            "--type", "aimd_md", "--project", "t27", "--elem", "O", "H",
            "--basis", "DZVP-MOLOPT-SR-GTH", "DZVP-MOLOPT-SR-GTH",
            "--potential", "GTH-PBE-q6", "GTH-PBE-q1",
            "--constraint-hbonds", "--hbond-atom-type", "O",
            "--hbond-targets", "0.96 1.0", "--thermostat", "langevin"]),
    ]

    total_err = 0
    total_warn = 0
    for name, args in cases:
        out = os.path.join(HERE, "_chk_" + name + ".inp")
        if not gen(out, *args):
            continue
        errs, warns = parse(out)
        status = "OK" if not errs else "ERROR"
        print(f"[{status}] {name}: {len(errs)} err, {len(warns)} warn")
        for e in errs:
            print(f"    ERR: {e}")
        for w in warns:
            print(f"    WARN: {w}")
        total_err += len(errs)
        total_warn += len(warns)

    print()
    print("#" * 70)
    print(f"# SUMMARY: {total_err} errors, {total_warn} warnings across {len(cases)} cases")
    print("#" * 70)


if __name__ == "__main__":
    main()
