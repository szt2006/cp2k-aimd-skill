#!/usr/bin/env python3
"""Generate a CP2K .inp from a template in references/templates/.

Usage:
  python gen_inp.py --type geo_opt --project myproj --elem Si \
      --cell 5.43 0 0  0 5.43 0  0 0 5.43 --xyz struct.xyz -o out.inp

  # spin-polarized open-shell system (radical / adsorbate):
  python gen_inp.py --type geo_opt --project o2 --elem O --multiplicity 3 ...

  # hybrid functional + ADMM (cheap hybrid) + dispersion (catalysis):
  python gen_inp.py --type static --project surf --elem Au \
      --basis DZVP-MOLOPT-SR-GTH --potential GTH-PBE-q11 \
      --functional HSE06 --admm --dispersion ...

  # freeze slab bottom layers:
  python gen_inp.py --type geo_opt --project slab --elem Si \
      --fixed-atoms "1..54 289..324" ...

  # isolated molecule / cluster in vacuum:
  python gen_inp.py --type geo_opt --project mol --elem C --periodic none ...

Placeholders filled: __PROJECT__, __A1__..__C3__, __STRUCTURE_BLOCK__,
__CHARGE__, __SPIN__, __XC_BLOCK__, __VDW_BLOCK__, __POISSON_BLOCK__,
__SMEAR_BLOCK__, __OUTER_SCF_BLOCK__, __CONSTRAINT_BLOCK__, __GLOBAL_PRINT__,
__BAND_TYPE__, __NPROC_REP__, __BASIS_ADMM_FILE__, __ENSEMBLE__,
__BAROSTAT_BLOCK__, __DFT_PRINT_BLOCK__, __FE_PRINT_BLOCK__, __LOCALIZE_BLOCK__.
The __ELEM__ / __BASIS__ / __POTENTIAL__ tokens are expanded into one &KIND
block per element (multi-element supported). With --admm, each &KIND also gets
a BASIS_SET AUX_FIT auxiliary basis. __QS_BLOCK__ holds WF_INTERPOLATION /
EXTRAPOLATION_ORDER for spin-polarized runs (those are &QS keywords).

Advanced per-&KIND control via --kinds (overrides --elem/--basis/--potential):
  NAME:ELEMENT:BASIS:POTENTIAL[:U=<eV>][:mag=<f>][:mass=<f>][:L=<int>][:noramp]
  * NAME may differ from ELEMENT (e.g. separate Fe / Fe2 / Fe3 spin sites).
  * U=  emits &DFT_PLUS_U (DFT+U correction); mag= = per-atom MAGNETIZATION spin;
    mass= = isotope / artificial MASS override. PLUS_U_METHOD is injected into
    &DFT automatically whenever any U= is set.

NEB advanced options (--type neb):
  * --xyz-replicas f0.xyz f1.xyz ...: read replicas from external XYZ files
    (each -> &REPLICA COORD_FILE_NAME <file>); NUMBER_OF_REPLICA auto-set.
    Mutually exclusive with the inline --xyz-init/--xyz-final path.
  * --optimize-band MD|DIIS: OPT_TYPE of &OPTIMIZE_BAND (MD=annealed &MD;
    DIIS=al2o3/neb style with --optimize-end-points F/T).
  * --align-frames / --rotate-frames T|F: &BAND ALIGN_FRAMES / ROTATE_FRAMES.
  * --k-spring <eV/A^2>, --program-run-info, --convergence-info: extra
    &BAND keywords / &PROGRAM_RUN_INFO / &CONVERGENCE_INFO subsections.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "..", "references", "templates")


# ---------------------------------------------------------------------------
# Auxiliary (ADMM) basis mapping: primary basis -> (AUX_FIT name, basis file)
# cFIT3 / FIT3 are the compact ADMM auxiliary bases shipped in BASIS_ADMM /
# BASIS_ADMM_MOLOPT. Larger (cpFIT3, FIT10, ...) improve accuracy if needed.
# ---------------------------------------------------------------------------
AUX_FIT_MAP = {
    "DZVP-MOLOPT-SR-GTH": ("cFIT3", "BASIS_ADMM_MOLOPT"),
    "TZVP-MOLOPT-GTH":     ("cFIT3", "BASIS_ADMM_MOLOPT"),
    "SZV-MOLOPT-GTH":      ("cFIT3", "BASIS_ADMM_MOLOPT"),
    "DZVP-GTH-PADE":       ("cFIT3", "BASIS_ADMM"),
    "TZVP-GTH-PADE":       ("FIT3",  "BASIS_ADMM"),
    "SZV-GTH-PADE":        ("cFIT3", "BASIS_ADMM"),
}


def read_xyz(path):
    if not path:
        return None
    lines = open(path).read().splitlines()
    n = int(lines[0].split()[0])
    coord = []
    for ln in lines[2:2 + n]:
        p = ln.split()
        if len(p) >= 4:
            coord.append(f"{p[0]} {p[1]} {p[2]} {p[3]}")
    return "\n".join(coord)


def expand_ranges(s):
    """Expand CP2K-style 'a..b' ranges inside an atom-list string.

    '1..26 30 32..35' -> '1 2 ... 26 30 32 33 34 35'.
    Real CP2K accepts '..' ranges in LIST keywords, but cp2k-input-tools does
    not expand them and would reject e.g. '1..26'. Expanding here keeps the
    generated input valid for BOTH real CP2K and the reference parser.
    """
    if not s:
        return s
    out = []
    for tok in s.replace(",", " ").split():
        if ".." in tok:
            a, b = tok.split("..", 1)
            try:
                lo, hi = int(a), int(b)
            except ValueError:
                out.append(tok)  # leave unparseable token untouched
                continue
            step = 1 if lo <= hi else -1
            out += [str(i) for i in range(lo, hi + step, step)]
        else:
            out.append(tok)
    return " ".join(out)


# ---------------------------------------------------------------------------
# Conditional block builders. Each returns a string already indented, or "".
# ---------------------------------------------------------------------------

def xc_block(func):
    """Return the &XC_FUNCTIONAL (+ optional &HF) block for a functional."""
    if func == "PADE":
        # LDA (default alias "PADE"): &XC_FUNCTIONAL PADE is the LDA section.
        return (
            "      &XC_FUNCTIONAL PADE\n"
            "      &END XC_FUNCTIONAL"
        )
    if func == "PBE":
        # PBE (GGA): the section name under &XC_FUNCTIONAL is PBE, NOT PADE.
        # (Regression fix: previously PBE wrongly emitted the LDA PADE block.)
        return (
            "      &XC_FUNCTIONAL PBE\n"
            "      &END XC_FUNCTIONAL"
        )
    if func == "HSE06":
        # HSE06 = 75% PBE exchange + 25% short-range HF exchange + PBE corr.
        # The &XWPBE/&PBE decomposition removes the GGA SR exchange that the
        # short-range HF exchange replaces. Short-range kernel via
        # &INTERACTION_POTENTIAL (modern, robust across CP2K versions).
        return (
            "      &XC_FUNCTIONAL\n"
            "        &XWPBE\n"
            "          SCALE_X -0.25\n"
            "          SCALE_X0 1.0\n"
            "          OMEGA 0.11\n"
            "        &END XWPBE\n"
            "        &PBE\n"
            "          SCALE_X 0.0\n"
            "          SCALE_C 1.0\n"
            "        &END PBE\n"
            "      &END XC_FUNCTIONAL\n"
            "      &HF\n"
            "        &SCREENING\n"
            "          EPS_SCHWARZ 1.0E-10\n"
            "        &END SCREENING\n"
            "        &INTERACTION_POTENTIAL\n"
            "          POTENTIAL_TYPE SHORTRANGE\n"
            "          OMEGA 0.11\n"
            "        &END INTERACTION_POTENTIAL\n"
            "        &MEMORY\n"
            "          MAX_MEMORY 512\n"
            "        &END MEMORY\n"
            "        FRACTION 0.25\n"
            "      &END HF"
        )
    if func == "B3LYP":
        # B3LYP is full-range hybrid: 20% exact exchange, no screening.
        return (
            "      &XC_FUNCTIONAL\n"
            "        &LYP\n"
            "          SCALE_C 0.81\n"
            "        &END LYP\n"
            "        &BECKE88\n"
            "          SCALE_X 0.72\n"
            "        &END BECKE88\n"
            "        &VWN\n"
            "          FUNCTIONAL_TYPE VWN3\n"
            "          SCALE_C 0.19\n"
            "        &END VWN\n"
            "        &XALPHA\n"
            "          SCALE_X 0.08\n"
            "        &END XALPHA\n"
            "      &END XC_FUNCTIONAL\n"
            "      &HF\n"
            "        &SCREENING\n"
            "          EPS_SCHWARZ 1.0E-10\n"
            "        &END SCREENING\n"
            "        &MEMORY\n"
            "          MAX_MEMORY 512\n"
            "          EPS_STORAGE_SCALING 1.0E-1\n"
            "        &END MEMORY\n"
            "        FRACTION 0.20\n"
            "      &END HF"
        )
    if func == "TPSS":
        # TPSS is a self-contained MGGA (exchange + correlation).
        return (
            "      &XC_FUNCTIONAL\n"
            "        &TPSS\n"
            "          SCALE_X 1.0\n"
            "          SCALE_C 1.0\n"
            "        &END TPSS\n"
            "      &END XC_FUNCTIONAL"
        )
    if func == "SCAN":
        # SCAN = MGGA_X_SCAN (exchange) + MGGA_C_SCAN (correlation).
        return (
            "      &XC_FUNCTIONAL\n"
            "        &MGGA_X_SCAN\n"
            "          SCALE 1.0\n"
            "        &END MGGA_X_SCAN\n"
            "        &MGGA_C_SCAN\n"
            "          SCALE 1.0\n"
            "        &END MGGA_C_SCAN\n"
            "      &END XC_FUNCTIONAL"
        )

    sys.exit(f"unknown --functional: {func}")


def vdw_block():
    return (
        "    &VDW_POTENTIAL\n"
        "      POTENTIAL_TYPE PAIR_POTENTIAL\n"
        "      &PAIR_POTENTIAL\n"
        "        TYPE DFTD3\n"
        "        PARAMETER_FILE_NAME dftd3.dat\n"
        "        REFERENCE_FUNCTIONAL PBE\n"
        "        R_CUTOFF [angstrom] 12\n"
        "      &END PAIR_POTENTIAL\n"
        "    &END VDW_POTENTIAL"
    )


def poisson_block(periodic):
    if periodic == "none":
        return (
            "    &POISSON\n"
            "      PERIODIC NONE\n"
            "      POISSON_SOLVER WAVELET\n"
            "    &END POISSON"
        )
    if periodic == "xy":
        return (
            "    &POISSON\n"
            "      PERIODIC XY\n"
            "    &END POISSON"
        )
    return ""  # xyz (default): rely on CP2K default PERIODIC xyz


def spin_block(multiplicity):
    """UKS + MULTIPLICITY live directly under &DFT (valid DFT keywords)."""
    if multiplicity and multiplicity > 0:
        return (
            "    UKS\n"
            f"    MULTIPLICITY {multiplicity}"
        )
    return ""


def qs_block(multiplicity, gapw=False):
    """&QS block.

    * --gapw  -> METHOD GAPW (all-electron core reconstruction)
    * UKS     -> WF_INTERPOLATION / EXTRAPOLATION_ORDER (these are &QS keywords,
                 NOT &DFT keywords)
    Emitted only when gapw or spin-polarized; otherwise omitted (CP2K defaults
    to GPW).
    """
    lines = ["    &QS"]
    if gapw:
        lines.append("      METHOD GAPW")
    if multiplicity and multiplicity > 0:
        lines.append("      WF_INTERPOLATION ASPC")
        lines.append("      EXTRAPOLATION_ORDER 3")
    if len(lines) == 1:
        return ""
    lines.append("    &END QS")
    return "\n".join(lines)


def smear_block(enabled):
    if not enabled:
        return ""
    return (
        "      &SMEAR ON\n"
        "        METHOD FERMI_DIRAC\n"
        "        ELECTRONIC_TEMPERATURE [K] 300\n"
        "      &END SMEAR"
    )


def outer_scf_block(enabled):
    if not enabled:
        return ""
    return (
        "      &OUTER_SCF ON\n"
        "        MAX_SCF 5\n"
        "        EPS_SCF 5.0E-6\n"
        "      &END OUTER_SCF"
    )


def admm_block(enabled):
    """ADMM (Auxiliary Density Matrix Method) for affordable hybrid functionals.

    Correct CP2K setup: the auxiliary fit basis goes into each &KIND block
    (BASIS_SET AUX_FIT <name>, handled in replace_kind_block); here we only
    select the ADMM variant and the correction functional. The auxiliary
    basis file name is emitted separately via basis_admm_file_line().
    Reduces HSE06/B3LYP cost 3-5x; essential for >50-atom hybrids.
    """
    if not enabled:
        return ""
    return (
        "    &AUXILIARY_DENSITY_MATRIX_METHOD\n"
        "      METHOD BASIS_PROJECTION\n"
        "      ADMM_PURIFICATION_METHOD MO_DIAG\n"
        "      EXCH_CORRECTION_FUNC PBEX\n"
        "    &END AUXILIARY_DENSITY_MATRIX_METHOD"
    )


def surface_dipole_block(enabled, direction="Z", pos=0.5, switch=0.3):
    """Surface dipole correction for asymmetric slab geometries.

    `SURFACE_DIPOLE_CORRECTION` is a &DFT keyword. When a slab is not
    symmetric (e.g. adsorbate only on one side, or asymmetric terminations),
    the periodic boundary condition creates an artificial surface dipole that
    shifts electrostatic potentials and slows SCF convergence. Enabling this
    correction restores a flat potential in the vacuum region. Default direction
    Z (slab normal), position 0.5 (fraction of the cell along that direction),
    switch 0.3 (smoothing width). Only meaningful for PERIODIC xy / xy? slabs.
    """
    if not enabled:
        return ""
    return (
        "    SURFACE_DIPOLE_CORRECTION T\n"
        "    SURF_DIP_DIR {}\n"
        "    SURF_DIP_POS {}\n"
        "    SURF_DIP_SWITCH {}".format(direction, pos, switch)
    )


def basis_admm_file_line(bases):
    """Return the BASIS_SET_FILE_NAME line(s) for the ADMM auxiliary basis.

    Picks BASIS_ADMM_MOLOPT when any primary basis is MOLOPT-family, else
    BASIS_ADMM. Returns '' when no ADMM is requested.
    """
    if not bases:
        return ""
    molopt = any("MOLOPT" in b for b in bases)
    fname = "BASIS_ADMM_MOLOPT" if molopt else "BASIS_ADMM"
    return "    BASIS_SET_FILE_NAME {}".format(fname)


def mixing_block(method, alpha=None, nbroyden=8, beta=None):
    """SCF mixing method block (only used by diagonalization, ignored by OT).

    BROYDEN_MIXING optionally takes a BETA (mixing of the residual; nico uses
    ALPHA 0.1 / BETA 1.5). BETA is emitted only when given (default: omit).
    """
    if not method or method == "broyden":
        beta_line = "          BETA {}\n".format(beta) if beta is not None else ""
        return (
            "        &MIXING\n"
            "          METHOD BROYDEN_MIXING\n"
            f"          ALPHA {alpha or 0.4}\n"
            + beta_line +
            f"          NBROYDEN {nbroyden}\n"
            "        &END MIXING"
        )
    if method == "pulay":
        return (
            "        &MIXING\n"
            "          METHOD PULAY_MIXING\n"
            f"          ALPHA {alpha or 0.2}\n"
            "          NMIXING 2\n"
            "        &END MIXING"
        )
    if method == "multisecant":
        return (
            "        &MIXING\n"
            "          METHOD MULTISECANT_MIXING\n"
            "          NBUFFER 5\n"
            "        &END MIXING"
        )
    return ""


def ot_minimizer_block(minimizer, preconditioner=None):
    """OT minimizer block. Valid MINIMIZER: DIIS, CG, BROYDEN, SD."""
    if not minimizer or minimizer == "diis":
        return ""
    prec = preconditioner or "FULL_SINGLE_INVERSE"
    m = minimizer.upper()
    return (
        "        &OT\n"
        f"          MINIMIZER {m}\n"
        f"          PRECONDITIONER {prec}\n"
        "        &END OT"
    )


def constraint_block(fixed_atoms, g3x3=None, g3x3_dist=None, hbonds=False,
                     hbond_atom_type=None, hbond_targets=None):
    """Build the &MOTION &CONSTRAINT block.

    Supports three self-contained, schema-valid constraint kinds:
      * FIXED_ATOMS  -- freeze a list of atoms (--fixed-atoms)
      * G3X3         -- 3 atoms / 3 distances SHAKE (--constraint-g3x3 + --g3x3-distances)
      * HBONDS       -- SHAKE on X-H bonds (--constraint-hbonds)
    COLLECTIVE (needs a &DEFINE_COLVAR that the 2026.1 schema does not model)
    is emitted manually by the advisor, not auto-generated.
    """
    parts = []
    if fixed_atoms:
        atoms = expand_ranges(fixed_atoms)
        parts.append(
            "    &FIXED_ATOMS\n"
            f"      LIST {atoms}\n"
            "    &END FIXED_ATOMS"
        )
    if g3x3:
        a = expand_ranges(g3x3)
        parts.append(
            "    &G3X3\n"
            f"      ATOMS {a}\n"
            f"      DISTANCES {g3x3_dist or ''}\n"
            "    &END G3X3"
        )
    if hbonds:
        lines = ["    &HBONDS"]
        if hbond_atom_type:
            lines.append(f"      ATOM_TYPE {hbond_atom_type}")
        if hbond_targets:
            lines.append(f"      TARGETS {hbond_targets}")
        lines.append("    &END HBONDS")
        parts.append("\n".join(lines))
    if not parts:
        return ""
    return "  &CONSTRAINT\n" + "\n".join(parts) + "\n  &END CONSTRAINT"


def metadyn_ww_block(ww):
    """Hill height WW (hartree). Omitted -> CP2K default 0.1."""
    if ww is None:
        return ""
    return "      WW {:.6g}".format(ww)


def metadyn_extra_block(well_tempered, delta_t, wtgamma, lagrange,
                        multi_walker, plumed, plumed_file):
    """Advanced METADYN keywords (well-tempered / LAGRANGE / walkers / PLUMED).

    Returns an indented (&METADYN child) block or "" when nothing is enabled.
    Mirrors decide.md §17 (METADYN) keyword names verified against the manual.
    """
    lines = []
    if well_tempered:
        lines.append("      WELL_TEMPERED T")
        if delta_t is not None:
            lines.append("      DELTA_T [K] {:.6g}".format(delta_t))
        if wtgamma is not None:
            lines.append("      WTGAMMA {:.6g}".format(wtgamma))
    if lagrange:
        lines.append("      LAGRANGE T")
    if multi_walker:
        lines.append("      &MULTIPLE_WALKERS")
        lines.append("      &END MULTIPLE_WALKERS")
    if plumed:
        lines.append("      USE_PLUMED T")
        if plumed_file:
            lines.append("      PLUMED_INPUT_FILE {}".format(plumed_file))
    return "\n".join(lines)


def global_print_block(print_forces):
    if not print_forces:
        return ""
    return (
        "  &PRINT\n"
        "    &FORCES ON\n"
        "    &END FORCES\n"
        "  &END PRINT"
    )


def _pop_sec(name, filename, silent, extra=None):
    """A standard &DFT &PRINT population-analysis subsection.

    With --print-style SILENT, emits '&NAME SILENT' + 'FILENAME <filename>'
    (matches nico's LOWDIN/HIRSHFELD/MULLIKEN blocks). Otherwise emits
    '&NAME ON' with no FILENAME (backward-compatible default).
    """
    out = []
    if silent:
        out.append("    &{} SILENT".format(name))
        out.append("      FILENAME {}".format(filename))
    else:
        out.append("    &{} ON".format(name))
    if extra:
        out += extra
    out.append("    &END {}".format(name))
    return out


def _cube_sec(name, filename, stride, extra=None):
    """A &DFT &PRINT cube subsection (E_DENSITY_CUBE / ELF_CUBE / V_HARTREE_CUBE
    / MO_CUBES). Always ON + FILENAME (matches nico's cube blocks) + STRIDE.
    """
    out = ["    &{} ON".format(name),
           "      FILENAME {}".format(filename),
           "      STRIDE {}".format(stride)]
    if extra:
        out += extra
    out.append("    &END {}".format(name))
    return out


def dft_print_block(props_list, ldos_list=None, print_style="ON",
                    cube_stride="5 5 5", pdos_nlumo=None, pdos_nhomo=None):
    """&DFT &PRINT block (all subsections confirmed against cp2k_input.xml).

    Supported --properties tokens (all under &DFT &PRINT):
      dos          -> &DOS
      pdos         -> &PDOS (with &EACH QS_SCF 1 + optional NLUMO/NHOMO via
                     --pdos-nlumo/--pdos-nhomo); add --ldos-list "1..26" to also
                     emit &PDOS &LDOS LIST <atoms> for per-atom projection
      cube         -> &E_DENSITY_CUBE (FILENAME cube + STRIDE via --cube-stride)
      band         -> &BAND_STRUCTURE (needs user &KPOINT_SET for real bands)
      mulliken     -> &MULLIKEN  (Mulliken 电荷布居分析)
      lowdin       -> &LOWDIN    (Löwdin 正交化布居分析)
      hirshfeld    -> &HIRSHFELD (Hirshfeld 分电荷)
      charges      -> mulliken + lowdin + hirshfeld (全部布居/电荷分析)
      mo           -> &MO_CUBES  (NHOMO 1 / NLUMO 1; 分子轨道 cube)
      elf          -> &ELF_CUBE  (电子局域函数可视化)
      vhartree     -> &V_HARTREE_CUBE (Hartree 势 cube)
      moments      -> &MOMENTS   (电/磁多极矩)

    print_style=ON  (default) : population analyses print ON, no FILENAME.
    print_style=SILENT       : population analyses print SILENT + FILENAME
                               (matches nico's quiet, redirected output).
    cube blocks always carry FILENAME + STRIDE (matches nico).
    """
    if not props_list and not ldos_list:
        return ""
    # 'charges' expands to the three population analyses
    expanded = []
    for p in props_list:
        pl = p.lower()
        if pl == "charges":
            expanded += ["mulliken", "lowdin", "hirshfeld"]
        else:
            expanded.append(pl)
    silent = print_style.upper() == "SILENT"
    lines = ["  &PRINT"]
    for pl in expanded:
        if pl == "dos":
            lines += _pop_sec("DOS", "dos", silent)
        elif pl == "pdos":
            extra = []
            if pdos_nhomo is not None:
                extra.append("      NHOMO {}".format(pdos_nhomo))
            if pdos_nlumo is not None:
                extra.append("      NLUMO {}".format(pdos_nlumo))
            lines += ["    &PDOS ON"]
            lines += extra
            lines.append("      &EACH")
            lines.append("        QS_SCF 1")
            lines.append("      &END EACH")
            if ldos_list:
                lines += ["      &LDOS", "        LIST {}".format(ldos_list),
                          "      &END LDOS"]
            lines.append("    &END PDOS")
        elif pl == "cube":
            lines += _cube_sec("E_DENSITY_CUBE", "cube", cube_stride)
        elif pl == "band":
            lines += ["    &BAND_STRUCTURE", "    &END BAND_STRUCTURE"]
        elif pl == "mulliken":
            lines += _pop_sec("MULLIKEN", "mulliken", silent)
        elif pl == "lowdin":
            lines += _pop_sec("LOWDIN", "lowdin", silent)
        elif pl == "hirshfeld":
            lines += _pop_sec("HIRSHFELD", "hirshfeld", silent)
        elif pl == "mo":
            lines += _cube_sec("MO_CUBES", "mo", cube_stride,
                               extra=["      NHOMO 1", "      NLUMO 1"])
        elif pl == "elf":
            lines += _cube_sec("ELF_CUBE", "elf", cube_stride)
        elif pl == "vhartree":
            lines += _cube_sec("V_HARTREE_CUBE", "hartree", cube_stride)
        elif pl == "moments":
            lines += ["    &MOMENTS", "      MAX_MOMENT 4", "    &END MOMENTS"]
    lines.append("  &END PRINT")
    return "\n".join(lines)


def fe_print_block(props_list):
    """&FORCE_EVAL &PRINT block for STRESS_TENSOR.

    Stress tensor lives under &FORCE_EVAL &PRINT (NOT &DFT &PRINT, NOT
    &PROPERTIES). Dipole moment is classical-MM-only and not emitted for
    Quickstep DFT, so it is intentionally omitted from --properties.
    """
    if not props_list or "stress" not in [p.lower() for p in props_list]:
        return ""
    return (
        "  &PRINT\n"
        "    &STRESS_TENSOR ON\n"
        "    &END STRESS_TENSOR\n"
        "  &END PRINT"
    )


def localize_block(props_list):
    """&DFT &LOCALIZE &PRINT &WANNIER_CENTERS for Wannier center analysis."""
    if not props_list or "wannier" not in [p.lower() for p in props_list]:
        return ""
    return (
        "  &LOCALIZE\n"
        "    METHOD CRAZY\n"
        "    &PRINT\n"
        "      &WANNIER_CENTERS ON\n"
        "        &EACH\n"
        "          QS_SCF 10\n"
        "        &END EACH\n"
        "      &END WANNIER_CENTERS\n"
        "    &END PRINT\n"
        "  &END LOCALIZE"
    )


def restart_block(restart_freq=500, backup=3):
    """Restart / restart-history for long MD runs (placed inside &PRINT).

    BACKUP_COPIES is a keyword of the &RESTART PRINT subsection
    (under MOTION/PRINT/RESTART per the CP2K reference) — it is NOT a &GLOBAL
    keyword, so it is emitted here, inside &RESTART, not in &GLOBAL.
    &RESTART writes the restart file every MD step; &RESTART_HISTORY records
    restart writes at the requested frequency.
    """
    if restart_freq <= 0:
        return ""
    return (
        "    &RESTART\n"
        "      BACKUP_COPIES 3\n"
        "      &EACH\n        MD 1\n      &END EACH\n"
        "    &END RESTART\n"
        "    &RESTART_HISTORY\n"
        "      &EACH\n        MD {}\n".format(restart_freq) +
        "      &END EACH\n"
        "    &END RESTART_HISTORY"
    )


def velocities_block(emit=True):
    """Velocity trajectory for VACF/IR post-processing (placed inside &PRINT).

    CP2K writes velocities to PROJECT-vel-1.xyz each MD step; this is what
    scripts/postprocess.py `vacf`/`ir` consume via --vel. Default ON for MD
    templates; `--no-velocities` turns it off to save disk on long runs.
    """
    if not emit:
        return ""
    return (
        "    &VELOCITIES\n"
        "      &EACH\n        MD 1\n      &END EACH\n"
        "    &END VELOCITIES"
    )



def thermostat_block(kind="csvr", timecon_fs=100):
    """Thermostat block for MD.

    CP2K &THERMOSTAT takes TYPE as a *keyword inside* the section (not a
    section parameter). Valid TYPE: CSVR, NOSE, GLE, AD_LANGEVIN. TIMECON
    lives inside the &CSVR / &NOSE / &AD_LANGEVIN subsection. 'langevin'
    maps to AD_LANGEVIN (a valid, robust thermostat type for surfaces).
    Plain LANGEVIN requires ENSEMBLE LANGEVIN + &THERMAL_REGION, so we use
    AD_LANGEVIN.
    """
    k = (kind or "csvr").lower()
    if k == "nose":
        return (
            "      &THERMOSTAT\n"
            "        TYPE NOSE\n"
            "        &NOSE\n"
            "          TIMECON [fs] {}\n".format(timecon_fs) +
            "        &END NOSE\n"
            "      &END THERMOSTAT"
        )
    if k == "langevin":
        return (
            "      &THERMOSTAT\n"
            "        TYPE AD_LANGEVIN\n"
            "        &AD_LANGEVIN\n"
            "          TIMECON_LANGEVIN [fs] {}\n".format(timecon_fs) +
            "          TIMECON_NH [fs] {}\n".format(timecon_fs) +
            "        &END AD_LANGEVIN\n"
            "      &END THERMOSTAT"
        )
    # default CSVR
    return (
        "      &THERMOSTAT\n"
        "        TYPE CSVR\n"
        "        &CSVR\n"
        "          TIMECON [fs] {}\n".format(timecon_fs) +
        "        &END CSVR\n"
        "      &END THERMOSTAT"
    )


def barostat_block(enabled):
    """BAROSTAT block for NPT (placed inside &MD)."""
    if not enabled:
        return ""
    return (
        "    &BAROSTAT\n"
        "      PRESSURE 1.0\n"
        "      TIMECON [fs] 100\n"
        "    &END BAROSTAT"
    )


def _to_float(tok, spec):
    try:
        return float(tok)
    except ValueError:
        sys.exit("ERROR: --kinds 数值参数非法 '{}' (in: {})".format(tok, spec))


def parse_kinds(specs):
    """Parse --kinds rich specs into a list of KIND dicts.

    Each spec is colon-separated:
        NAME:ELEMENT:BASIS:POTENTIAL[:U=<eV>][:mag=<f>][:mass=<f>][:L=<int>][:noramp]
    The first 3-4 positional fields are NAME, [ELEMENT], BASIS, POTENTIAL.
    If only three positional fields are given (NAME:BASIS:POTENTIAL) the
    NAME is also used as the ELEMENT (kind name == element symbol). Optional
    key=value tokens (and the bare flag 'noramp'):
        U=<eV>   -> enables &DFT_PLUS_U with U_MINUS_J [eV] <val>
        mag=<f>  -> per-&KIND MAGNETIZATION <f> (different spin per atom)
        mass=<f> -> per-&KIND MASS <f> (isotope / artificial mass override)
        L=<int>  -> orbital angular momentum for +U (default 2, d-shell)
        noramp   -> omit U_RAMPING ramping keywords (Au-TiO2 Ti style)
    Examples:
        Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=5.0:U=3
        Fe2:Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=4.0:U=3
        Au:DZVP-MOLOPT-SR-GTH:GTH-PBE-q11:mass=19.7
    """
    kinds = []
    for spec in specs:
        parts = spec.split(":")
        positional, kv = [], {}
        for p in parts:
            if "=" in p:
                k, v = p.split("=", 1)
                kv[k.lower()] = v
            elif p.lower() == "noramp":
                kv["noramp"] = "1"
            else:
                positional.append(p)
        if len(positional) == 4:
            name, element, basis, potential = positional
        elif len(positional) == 3:
            name = element = positional[0]
            basis, potential = positional[1], positional[2]
        else:
            sys.exit("ERROR: --kinds 每项必须形如 "
                     "NAME:ELEMENT:BASIS:POTENTIAL (或 NAME:BASIS:POTENTIAL)，"
                     "再加可选 U=/mag=/mass=/L=/noramp。出错项: {}".format(spec))
        kinds.append({
            "name": name,
            "element": element,
            "basis": basis,
            "potential": potential,
            "u": _to_float(kv["u"], spec) if "u" in kv else None,
            "mag": _to_float(kv["mag"], spec) if "mag" in kv else None,
            "mass": _to_float(kv["mass"], spec) if "mass" in kv else None,
            "l": int(_to_float(kv["l"], spec)) if "l" in kv else 2,
            "noramp": "noramp" in kv,
        })
    return kinds


def dft_plus_u_block(u, l=2, noramp=False):
    """&DFT_PLUS_U block (keyword names verified against cp2k_input.xml).

    Default emits the ramping trio (EPS_U_RAMPING / U_RAMPING /
    INIT_U_RAMPING_EACH_SCF) used by catalytic oxides such as Fe3O4. With
    noramp, only EPS_U_RAMPING is kept (Au-TiO2 Ti style). U_MINUS_J is given
    in [eV] (CP2K default unit for U_MINUS_J).
    """
    lines = ["      &DFT_PLUS_U"]
    if not noramp:
        lines.append("        EPS_U_RAMPING 1.0E-3")
        lines.append("        U_RAMPING 0.1")
        lines.append("        INIT_U_RAMPING_EACH_SCF F")
    else:
        lines.append("        EPS_U_RAMPING 1.0E-3")
    lines.append("        L {}".format(l))
    lines.append("        U_MINUS_J [eV] {}".format(u))
    lines.append("      &END DFT_PLUS_U")
    return "\n".join(lines)


def kind_block(k, admm=False):
    """Render one &KIND block from a KIND dict (see parse_kinds)."""
    lines = ["    &KIND {}".format(k["name"])]
    if k["element"]:
        lines.append("      ELEMENT {}".format(k["element"]))
    if k["mag"] is not None:
        lines.append("      MAGNETIZATION {}".format(k["mag"]))
    lines.append("      BASIS_SET {}".format(k["basis"]))
    if k["potential"]:
        lines.append("      POTENTIAL {}".format(k["potential"]))
    if k["mass"] is not None:
        lines.append("      MASS {}".format(k["mass"]))
    if admm:
        aux, _ = AUX_FIT_MAP.get(k["basis"], ("cFIT3", "BASIS_ADMM"))
        lines.append("      BASIS_SET AUX_FIT {}".format(aux))
    if k["u"] is not None:
        lines.append(dft_plus_u_block(k["u"], k["l"], k["noramp"]))
    lines.append("    &END KIND")
    return "\n".join(lines)


def replace_kind_block(tpl, kinds, admm=False):
    """Replace the single-&KIND __ELEM__ placeholder with one &KIND per entry.

    `kinds` is a list of dicts from parse_kinds() (or built from
    --elem/--basis/--potential). When --admm, an AUX_FIT auxiliary basis is
    added to every kind. The templates ship with the placeholder block:
        &KIND __ELEM__
          ELEMENT __ELEM__
          BASIS_SET __BASIS__
          POTENTIAL __POTENTIAL__
        &END KIND
    """
    new_block = "\n".join(kind_block(k, admm) for k in kinds)
    pat = re.compile(r"\n[ \t]*&KIND __ELEM__.*?&END KIND", re.DOTALL)
    if pat.search(tpl):
        return pat.sub("\n" + new_block, tpl)
    return tpl


def inject_plus_u_method(tpl, method):
    """Inject PLUS_U_METHOD into &DFT (only when any +U kind is present).

    PLUS_U_METHOD is a keyword of &DFT (MULLIKEN / LOWDIN / MARZARI / DUDEI...).
    It is inserted right after the opening &DFT line via regex so no template
    edit is required.
    """
    if not method:
        return tpl
    pat = re.compile(r"(\n[ \t]*&DFT[ \t]*)\n")
    return pat.sub(r"\1\n    PLUS_U_METHOD {}\n".format(method), tpl, count=1)


def optimizer_block(optimizer, max_h_rank=30):
    """&GEO_OPT / &CELL_OPT OPTIMIZER line + its subsection (if any).

    Valid OPTIMIZER: BFGS (no subsection), LBFGS (&LBFGS MAX_H_RANK),
    CG (&CG &LINE_SEARCH TYPE 2PNT). LBFGS/CG are what the 庚子 examples use
    for slab/defect optimizations; BFGS is the default for bulk.
    """
    o = (optimizer or "bfgs").lower()
    if o == "lbfgs":
        return (
            "    OPTIMIZER LBFGS\n"
            "    &LBFGS\n"
            "      MAX_H_RANK {}\n".format(max_h_rank) +
            "    &END LBFGS"
        )
    if o == "cg":
        return (
            "    OPTIMIZER CG\n"
            "    &CG\n"
            "      &LINE_SEARCH\n"
            "        TYPE 2PNT\n"
            "      &END LINE_SEARCH\n"
            "    &END CG"
        )
    # default BFGS
    return "    OPTIMIZER BFGS"


def inject_stress_tensor(tpl, method):
    """Inject STRESS_TENSOR (computation method) into &FORCE_EVAL.

    STRESS_TENSOR is a keyword of &FORCE_EVAL (ANALYTICAL / NUMERICAL) that
    controls HOW the stress tensor is computed -- distinct from
    &PRINT &STRESS_TENSOR which only PRINTS it. The cu-kpoint example uses
    'STRESS_TENSOR ANALYTICAL'. Inserted right after the opening &FORCE_EVAL
    line via regex so no template edit is required.
    """
    if not method:
        return tpl
    pat = re.compile(r"(\n[ \t]*&FORCE_EVAL[ \t]*)\n")
    return pat.sub(r"\1\n  STRESS_TENSOR {}\n".format(method), tpl, count=1)


def tune_scf_block(tpl, cutoff=None, rel_cutoff=None, eps_scf=None,
                   max_scf=None, scf_guess=None, eps_diis=None,
                   added_mos=None, cholesky=None, wfn_restart=None,
                   eps_adapt=None):
    """Apply fine-grained SCF / MGRID knobs to a DFT template via regex.

    Only touches the FIRST occurrence of each keyword (the MGRID / SCF section
    of a Quickstep DFT; QM/MM's PM6 region has no plane-wave cut-off and is
    skipped by the caller). Missing args are left at the template default.
    Optional &SCF keywords (EPS_DIIS / ADDED_MOS / CHOLESKY) are injected right
    after the opening '&SCF' line (order-independent within &SCF).
    WFN_RESTART_FILE_NAME (a &DFT keyword, NOT &SCF) is injected right after
    the opening '&DFT' line. EPS_ADAPT is injected into '&DIAGONALIZATION ...
    ALGORITHM STANDARD' (the only place it is valid).
    """
    if cutoff is not None:
        tpl = re.sub(r"(CUTOFF )\S+", r"\g<1>{}".format(cutoff), tpl, count=1)
    if rel_cutoff is not None:
        tpl = re.sub(r"(REL_CUTOFF )\S+", r"\g<1>{}".format(rel_cutoff), tpl, count=1)
    if eps_scf is not None:
        tpl = re.sub(r"(EPS_SCF )\S+", r"\g<1>{}".format(eps_scf), tpl, count=1)
    if max_scf is not None:
        tpl = re.sub(r"(MAX_SCF )\S+", r"\g<1>{}".format(max_scf), tpl, count=1)
    if scf_guess is not None:
        tpl = re.sub(r"(SCF_GUESS )\S+", r"\g<1>{}".format(scf_guess), tpl, count=1)
    extra = []
    if eps_diis is not None:
        extra.append("      EPS_DIIS {}".format(eps_diis))
    if added_mos is not None:
        extra.append("      ADDED_MOS {}".format(added_mos))
    if cholesky is not None:
        extra.append("      CHOLESKY {}".format(cholesky))
    if extra:
        block = "\n".join(extra)
        tpl = re.sub(r"(\n[ \t]*&SCF[ \t]*\n)",
                     r"\1" + block + "\n", tpl, count=1)
    if wfn_restart is not None:
        tpl = re.sub(r"(\n[ \t]*&DFT[ \t]*)\n",
                     r"\1\n    WFN_RESTART_FILE_NAME {}\n".format(wfn_restart),
                     tpl, count=1)
    if eps_adapt is not None:
        tpl = re.sub(r"(\n[ \t]*ALGORITHM STANDARD\n)",
                     r"\1        EPS_ADAPT {}\n".format(eps_adapt), tpl, count=1)
    return tpl


def optimize_band_block(opt_type, opt_end_points=True):
    """&BAND &OPTIMIZE_BAND block (OPT_TYPE MD or DIIS).

    OPT_TYPE MD emits the &MD subsection (annealed MD band optimization with
    VEL_CONTROL annealing -- the CP2K default for CI-NEB). OPT_TYPE DIIS emits
    only the keywords (OPT_TYPE DIIS + OPTIMIZE_END_POINTS) matching the
    al2o3/neb validated example, which keeps end points fixed; no &DIIS
    subsection is required (it is optional). OPTIMIZE_END_POINTS is a keyword
    of &OPTIMIZE_BAND (not a subsection).
    """
    o = (opt_type or "MD").upper()
    if o == "DIIS":
        return (
            "    &OPTIMIZE_BAND\n"
            "      OPT_TYPE DIIS\n"
            "      OPTIMIZE_END_POINTS {}\n".format("T" if opt_end_points else "F") +
            "    &END OPTIMIZE_BAND"
        )
    # default MD
    return (
        "    &OPTIMIZE_BAND\n"
        "      OPT_TYPE MD\n"
        "      &MD\n"
        "        TIMESTEP 0.5\n"
        "        TEMPERATURE 500.0\n"
        "        MAX_STEPS 300\n"
        "        &VEL_CONTROL\n"
        "          ANNEALING 0.99\n"
        "          PROJ_VELOCITY_VERLET T\n"
        "        &END VEL_CONTROL\n"
        "      &END MD\n"
        "    &END OPTIMIZE_BAND"
    )


def replica_blocks(xyz_replicas, coord_init, coord_final):
    """Emit all &BAND &REPLICA blocks. Returns (n_replica, block_text).

    Two modes:
      * External files: --xyz-replicas f1.xyz f2.xyz ... -> each &REPLICA gets
        a COORD_FILE_NAME <file> (matches al2o3/neb which reads ./0.xyz..).
      * Inline: --xyz-init / --xyz-final (or --coord) -> two &REPLICA blocks
        with inline &COORD. n_replica is then 2.
    """
    if xyz_replicas:
        blocks = []
        for f in xyz_replicas:
            blocks.append(
                "    &REPLICA\n"
                "      COORD_FILE_NAME {}\n".format(f) +
                "    &END REPLICA"
            )
        return len(xyz_replicas), "\n".join(blocks)
    ci = coord_init or "# TODO: initial frame coordinates"
    cf = coord_final or "# TODO: final frame coordinates"
    block = (
        "    &REPLICA\n"
        "      &COORD\n"
        + ci + "\n"
        "      &END COORD\n"
        "    &END REPLICA\n"
        "    &REPLICA\n"
        "      &COORD\n"
        + cf + "\n"
        "      &END COORD\n"
        "    &END REPLICA"
    )
    return 2, block


def kind_block_simple(elems):
    """Emit minimal &KIND blocks (ELEMENT only) for a QM/MM skeleton.

    The PM6 (semi-empirical) QM region and the FIST (classical) MM region do
    not use a Gaussian BASIS_SET / POTENTIAL, so a bare ELEMENT-kind is the
    correct form here (PM6 carries its own Slater-exponent parameters).
    """
    blocks = []
    for e in elems:
        blocks.append("    &KIND {}\n      ELEMENT {}\n    &END KIND".format(e, e))
    return "\n".join(blocks)


def mm_charge_block(mm_elems):
    """&MM &FORCEFIELD &CHARGE per MM element (charge placeholder, edit me).

    ATOM and CHARGE are emitted on separate lines: the cp2k-input-tools
    reference parser rejects the single-line 'ATOM Cu CHARGE 0.0' form.
    """
    lines = ["    &CHARGE"]
    for e in mm_elems:
        lines.append("      ATOM {}".format(e))
        lines.append("      CHARGE 0.0")
    lines.append("    &END CHARGE")
    return "\n".join(lines)


def mm_nonbonded_block(mm_elems):
    """&MM &FORCEFIELD &NONBONDED placeholder skeleton.

    Emits a LENNARD-JONES self-pair per MM element (EPSILON 0.0 / SIGMA 3.166
    / RCUT 15) so the input parses and runs a *degenerate* MM region. Real
    systems must replace these and add cross-term potentials (GENPOT / EAM /
    Buckingham) with parameters from the chosen force field.
    """
    lines = ["    &NONBONDED"]
    for e in mm_elems:
        lines += ["      &LENNARD-JONES",
                  "        atoms {} {}".format(e, e),
                  "        EPSILON 0.0",
                  "        SIGMA 3.166",
                  "        RCUT  15",
                  "      &END LENNARD-JONES"]
    lines.append("      # TODO: add cross-term potentials (GENPOT / EAM / "
                  "Buckingham) for real MM interactions.")
    lines.append("    &END NONBONDED")
    return "\n".join(lines)


def normalize_elists(elems, bases, pots):
    """Align basis/potential lists to the element list (broadcast single)."""
    elems = list(elems or ["Si"])
    bases = list(bases or ["DZVP-GTH-PADE"])
    pots = list(pots or ["GTH-PADE-q4"])
    if len(bases) == 1 and len(elems) > 1:
        bases = bases * len(elems)
    if len(pots) == 1 and len(elems) > 1:
        pots = pots * len(elems)
    if not (len(bases) == len(elems) == len(pots)):
        sys.exit("ERROR: --elem / --basis / --potential 数量不匹配 "
                 "(elem={} basis={} pot={})".format(
                     len(elems), len(bases), len(pots)))
    return elems, bases, pots


def main():
    ap = argparse.ArgumentParser(description="Generate a CP2K .inp from a template.")
    ap.add_argument("--type", required=True,
                    choices=["static", "geo_opt", "cell_opt", "aimd_md",
                             "metadyn", "neb", "vib", "qmmm"])
    ap.add_argument("--project", default="cp2k")
    ap.add_argument("--elem", nargs="+", default=["Si"],
                    help="Element symbol(s). Multi-element example: --elem Au O Cu. "
                         "Each element gets its own &KIND block.")
    ap.add_argument("--basis", nargs="+", default=["DZVP-GTH-PADE"],
                    help="Basis set(s), aligned positionally with --elem. A single "
                         "value applies to all elements. Transition metals: "
                         "DZVP-MOLOPT-SR-GTH.")
    ap.add_argument("--potential", nargs="+", default=["GTH-PADE-q4"],
                    help="Pseudopotential(s) incl. valence charge, aligned with "
                         "--elem. Single value applies to all. e.g. GTH-PBE-q11 (Au).")
    ap.add_argument("--cell", nargs=9, type=float,
                    metavar="A1 A2 A3 B1 B2 B3 C1 C2 C3",
                    default=[5.43, 0, 0, 0, 5.43, 0, 0, 0, 5.43])
    ap.add_argument("--xyz", help="XYZ file with coordinates (for non-NEB types)")
    ap.add_argument("--xyz-init", help="Initial-frame XYZ (NEB)")
    ap.add_argument("--xyz-final", help="Final-frame XYZ (NEB)")
    ap.add_argument("--coord", help="Raw coordinate lines: 'Element x y z' per line")
    # ---- advanced options ----
    ap.add_argument("--charge", type=int, default=0,
                    help="System total charge (default 0).")
    ap.add_argument("--multiplicity", type=int, default=0,
                    help="Spin multiplicity. >0 enables spin-polarized UKS "
                         "(e.g. O2 -> 3, radical -> 2).")
    ap.add_argument("--functional", default="PADE",
                    choices=["PADE", "PBE", "TPSS", "SCAN", "HSE06", "B3LYP"],
                    help="XC functional (default PADE=PBE). HSE06/B3LYP are "
                         "hybrids and add an &HF block (use --admm to make cheap).")
    ap.add_argument("--dispersion", action="store_true",
                    help="Add DFT-D3 van der Waals correction (&VDW_POTENTIAL).")
    ap.add_argument("--periodic", default="xyz", choices=["xyz", "xy", "none"],
                    help="Periodicity: xyz (bulk, default), xy (surface slab, "
                         "z non-periodic), or none (isolated molecule/cluster).")
    ap.add_argument("--kpoints", default="",
                    help="Monkhorst-Pack grid, e.g. '6 6 6' (bulk metal) or "
                         "'4 4 1' (surface slab). Emits &KPOINTS; skip for "
                         "non-periodic / insulators at GAMMA.")
    ap.add_argument("--fixed-atoms", default="",
                    help="Atom list to freeze, e.g. '1..54 289..324' "
                         "(writes &CONSTRAINT &FIXED_ATOMS).")
    # ---- GAPW (all-electron core reconstruction) ----
    ap.add_argument("--gapw", action="store_true",
                    help="Use the GAPW all-electron method (&QS METHOD GAPW) "
                         "for accurate core properties (EFG, hyperfine). "
                         "Requires a basis that describes the core region.")
    # ---- CONSTRAINT advanced (MOTION / CONSTRAINT) ----
    ap.add_argument("--constraint-g3x3", default="",
                    help="3 atom indices for a &GAPW-free &CONSTRAINT &G3X3 "
                         "3-distance shake, e.g. '1 2 3'.")
    ap.add_argument("--g3x3-distances", default="",
                    help="3 target distances (Bohr) for --constraint-g3x3, "
                         "e.g. '1.0 1.5 2.0'.")
    ap.add_argument("--constraint-hbonds", action="store_true",
                    help="Add &CONSTRAINT &HBONDS (SHAKE on X-H bonds).")
    ap.add_argument("--hbond-atom-type", default="",
                    help="ATOM_TYPE for --constraint-hbonds (atom bonded to H).")
    ap.add_argument("--hbond-targets", default="",
                    help="TARGETS distances (Bohr) for --constraint-hbonds.")
    ap.add_argument("--print-forces", action="store_true",
                    help="Add &PRINT &FORCES ON in &GLOBAL (writes atomic forces).")
    ap.add_argument("--smear", action="store_true",
                    help="Add &SCF &SMEAR FERMI_DIRAC 300K (metals / narrow gap).")
    ap.add_argument("--outer-scf", action="store_true",
                    help="Add &SCF &OUTER_SCF (helps OT convergence for hybrids).")
    ap.add_argument("--band-type", default="CI-NEB",
                    help="NEB band type (default CI-NEB; IT-NEB also common).")
    ap.add_argument("--nproc-rep", type=int, default=8,
                    help="NEB &BAND NPROC_REP (MPI ranks per replica).")
    # ---- Metadynamics advanced (FREE_ENERGY / METADYN) ----
    ap.add_argument("--well-tempered", action="store_true",
                    help="Enable well-tempered metadynamics: emits WELL_TEMPERED T "
                         "and (with --delta-t) DELTA_T [K] (or --wtgamma WTGAMMA).")
    ap.add_argument("--delta-t", type=float, default=None,
                    help="Well-tempered bias temperature DELTA_T in K (e.g. 1500). "
                         "Requires --well-tempered.")
    ap.add_argument("--wtgamma", type=float, default=None,
                    help="Well-tempered gamma WTGAMMA (alternative to --delta-t). "
                         "Requires --well-tempered.")
    ap.add_argument("--metadyn-ww", type=float, default=None,
                    help="Hill height WW (hartree); default CP2K 0.1. Larger=hills "
                         "further apart (smoother free-energy surface).")
    ap.add_argument("--lagrange", action="store_true",
                    help="Extended-Lagrangian metadynamics: emits LAGRANGE T "
                         "(CVs get a mass and are propagated dynamically).")
    ap.add_argument("--multi-walker", action="store_true",
                    help="Enable &MULTIPLE_WALKERS (cooperative metadynamics).")
    ap.add_argument("--plumed", action="store_true",
                    help="Drive metadynamics via PLUMED: emits USE_PLUMED T and "
                         "(with --plumed-file) PLUMED_INPUT_FILE <file>.")
    ap.add_argument("--plumed-file", default=None,
                    help="PLUMED input file name for --plumed.")
    ap.add_argument("--admm", action="store_true",
                    help="Enable ADMM auxiliary density matrix method "
                         "(3-5x cheaper hybrid functionals). Auto-adds AUX_FIT "
                         "basis to each &KIND and the BASIS_ADMM file name.")
    ap.add_argument("--surface-dipole", action="store_true",
                    help="Enable &DFT SURFACE_DIPOLE_CORRECTION for asymmetric "
                         "slab geometries (adsorbate on one side, asymmetric "
                         "terminations). Restores flat vacuum potential and "
                         "speeds SCF convergence. Only meaningful for PERIODIC "
                         "xy / x? slabs. Use with ADMM/UKS-safe inputs.")
    ap.add_argument("--dipole-dir", default="Z",
                    help="Surface dipole correction direction (default Z).")
    ap.add_argument("--dipole-pos", type=float, default=0.5,
                    help="Surface dipole correction position as a fraction of "
                         "the cell along --dipole-dir (default 0.5).")
    ap.add_argument("--dipole-switch", type=float, default=0.3,
                    help="Surface dipole correction smoothing switch (default 0.3).")
    ap.add_argument("--mixing-method", default="broyden",
                    choices=["broyden", "pulay", "multisecant"],
                    help="SCF mixing method (diagonalization only). broyden=default; "
                         "pulay/multisecant for difficult convergence.")
    ap.add_argument("--ot-minimizer", default="diis",
                    choices=["diis", "cg", "broyden"],
                    help="OT minimizer. diis=default; cg for difficult systems; "
                         "broyden mixing approximation of inverse Hessian.")
    # ---- SCF / MGRID fine-tuning (复现 nico 等精细调参算例) ----
    ap.add_argument("--cutoff", type=float, default=None,
                    help="&MGRID CUTOFF (plane-wave cut-off, Ry). None=template "
                         "default (300). e.g. 350 for metals with soft GTH.")
    ap.add_argument("--rel-cutoff", type=float, default=None,
                    help="&MGRID REL_CUTOFF (relative cut-off, Ry). None=template "
                         "default (60).")
    ap.add_argument("--eps-scf", default=None,
                    help="&SCF EPS_SCF convergence threshold. None=template "
                         "default (1.0E-7). e.g. 1.0E-6.")
    ap.add_argument("--max-scf", type=int, default=None,
                    help="&SCF MAX_SCF max SCF iterations. None=template default "
                         "(300). e.g. 500.")
    ap.add_argument("--eps-diis", type=float, default=None,
                    help="&SCF EPS_DIIS (DIIS cutoff for mixing; nico uses 0.05). "
                         "None=omit.")
    ap.add_argument("--added-mos", type=int, default=None,
                    help="&SCF ADDED_MOS (extra MOs for metals / smear). None=omit "
                         "(nico uses 500).")
    ap.add_argument("--cholesky", default=None,
                    choices=["INVERSE", "ON", "OFF"],
                    help="&SCF CHOLESKY (Cholesky decomposition of overlap). "
                         "None=omit (nico uses INVERSE).")
    ap.add_argument("--scf-guess", default="ATOMIC",
                    choices=["ATOMIC", "RESTART", "BERYLLIUM"],
                    help="&SCF SCF_GUESS (initial guess). RESTART reads a prior "
                         ".wfn (use with --wfn-restart).")
    ap.add_argument("--wfn-restart", default=None,
                    help="&SCF WFN_RESTART_FILE_NAME <file> (read prior wavefn; "
                         "pair with --scf-guess RESTART). None=omit.")
    ap.add_argument("--diagonalization-eps-adapt", type=float, default=None,
                    help="&DIAGONALIZATION EPS_ADAPT (adaptive DIIS threshold). "
                         "None=omit (nico uses 0.01). Only affects templates that "
                         "expose &DIAGONALIZATION.")
    ap.add_argument("--mixing-alpha", type=float, default=0.4,
                    help="SCF BROYDEN mixing ALPHA (default 0.4; nico uses 0.1).")
    ap.add_argument("--mixing-beta", type=float, default=None,
                    help="SCF BROYDEN mixing BETA (residual mixing; nico uses "
                         "1.5). None=omit (default behavior).")
    ap.add_argument("--mixing-nbroyden", type=int, default=8,
                    help="SCF BROYDEN NBROYDEN buffer size (default 8; nico 8).")
    ap.add_argument("--print-style", default="ON", choices=["ON", "SILENT"],
                    help="&DFT &PRINT output style for population analyses. SILENT "
                         "emits '&NAME SILENT' + 'FILENAME <name>' (quiet, "
                         "redirected output, matches nico); ON is the default.")
    ap.add_argument("--cube-stride", default="5 5 5",
                    help="STRIDE for cube outputs (E_DENSITY_CUBE / ELF_CUBE / "
                         "V_HARTREE_CUBE / MO_CUBES). Default 5 5 5; nico uses "
                         "1 1 1 (every grid point).")
    ap.add_argument("--pdos-nlumo", type=int, default=None,
                    help="&PDOS NLUMO (number of virtual orbitals for projected "
                         "DOS). None=omit (nico uses 30).")
    ap.add_argument("--pdos-nhomo", type=int, default=None,
                    help="&PDOS NHOMO (number of occupied orbitals for projected "
                         "DOS). None=omit (default 1).")
    ap.add_argument("--properties", nargs="+",
                    help="Properties: dos pdos cube band (-> &DFT &PRINT); "
                         "mulliken lowdin hirshfeld charges mo elf vhartree moments "
                         "(-> &DFT &PRINT); stress (-> &FORCE_EVAL &PRINT); "
                         "wannier (-> &DFT &LOCALIZE). 'charges' = mulliken+lowdin+hirshfeld. "
                         "Dipole is classical-MM-only and not emitted for DFT.")
    ap.add_argument("--thermostat", default="csvr",
                    choices=["csvr", "nose", "langevin"],
                    help="MD thermostat. csvr=default; nose; langevin "
                         "(maps to AD_LANGEVIN, robust for surfaces).")
    ap.add_argument("--ensemble", default="nvt",
                    choices=["nve", "nvt", "npt"],
                    help="MD ensemble. npt adds &BAROSTAT automatically.")
    ap.add_argument("--restart-freq", type=int, default=0,
                    help="MD restart write frequency in steps (0=off; "
                         "default 500 for MD, off for other run types).")
    ap.add_argument("--no-velocities", dest="velocities", action="store_false",
                    default=True,
                    help="Turn OFF per-step velocity printing (PROJECT-vel-1.xyz). "
                         "Default ON for MD; velocities are consumed by postprocess.py vacf/ir.")
    ap.add_argument("--qs-eps", default=None,
                    help="QS EPS_DEFAULT value (e.g. 1e-12). Default CP2K 1e-10.")
    ap.add_argument("--ldos-list", default=None,
                    help="Atom index list for PDOS &LDOS projection, e.g. '1..26' "
                         "or '1 2 3'. Emits &PDOS &LDOS LIST <atoms> when --properties pdos.")
    ap.add_argument("--optimizer", default=None,
                    choices=["bfgs", "lbfgs", "cg"],
                    help="Geometry/cell optimizer. bfgs=default (bulk); "
                         "lbfgs/cg for slabs/defects (emits &LBFGS/&CG subsection). "
                         "cell_opt defaults to cg when not specified.")
    ap.add_argument("--stress-tensor", default=None,
                    choices=["analytical", "numerical"],
                    help="&DFT STRESS_TENSOR computation method (ANALYTICAL/NUMERICAL) "
                         "-- distinct from --properties stress which only PRINTS it.")
    ap.add_argument("--topology", default=None,
                    help="Read structure from an external file instead of &COORD, e.g. "
                         "'POSCAR.cif'. Emits &SUBSYS &TOPOLOGY COORD_FILE_NAME <file> "
                         "COORD_FILE_FORMAT <fmt>; mutually exclusive with --xyz/--coord.")
    ap.add_argument("--topology-format", default="cif",
                    help="TOPOLOGY COORD_FILE_FORMAT: cif (default), xyz, pdb, extxyz, "
                         "xyzpdb, gaussian, etc. (matching the --topology file type).")
    ap.add_argument("--kinds", nargs="+", default=None,
                    help="Rich per-&KIND specs (overrides --elem/--basis/--potential). "
                         "Format NAME:ELEMENT:BASIS:POTENTIAL with optional "
                         "U=<eV> mag=<f> mass=<f> L=<int> noramp. With 3 fields "
                         "(NAME:BASIS:POTENTIAL) NAME is also the ELEMENT. "
                         "Example: 'Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=5.0:U=3' "
                         "'Fe2:Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=4.0:U=3' "
                         "'Au:DZVP-MOLOPT-SR-GTH:GTH-PBE-q11:mass=19.7'.")
    ap.add_argument("--plus-u-method", default="MULLIKEN",
                    help="PLUS_U_METHOD for DFT+U (default MULLIKEN). Other valid "
                         "choices: LOWDIN, MARZARI, DUDEI. Injected into &DFT "
                         "automatically when any --kinds entry has U= set.")
    # ---- NEB advanced options (--type neb) ----
    ap.add_argument("--align-frames", default="T", choices=["T", "F"],
                    help="NEB &BAND ALIGN_FRAMES (T=align each replica frame before "
                         "optimization, default T; F=keep frames as given -- e.g. "
                         "vacancy migration where alignment would distort the path).")
    ap.add_argument("--rotate-frames", default="F", choices=["T", "F"],
                    help="NEB &BAND ROTATE_FRAMES (T=rotate frames to best overlap; "
                         "default F). Needed for rotational reaction coordinates.")
    ap.add_argument("--optimize-band", default="MD", choices=["MD", "DIIS"],
                    help="NEB &OPTIMIZE_BAND OPT_TYPE. MD=default annealed MD band "
                         "optimization (emits &MD block); DIIS=fixed-end-point DIIS "
                         "(al2o3/neb style, uses --optimize-end-points).")
    ap.add_argument("--optimize-end-points", default="T", choices=["T", "F"],
                    help="NEB &OPTIMIZE_BAND OPTIMIZE_END_POINTS (T=also relax the "
                         "two end points; F=keep end points fixed, e.g. al2o3/neb).")
    ap.add_argument("--xyz-replicas", nargs="+", default=None,
                    help="Read NEB replicas from external XYZ files instead of inline "
                         "coords: --xyz-replicas ./0.xyz ./1.xyz ... ./N.xyz. Each "
                         "emits &REPLICA COORD_FILE_NAME <file>; NUMBER_OF_REPLICA is "
                         "set automatically to the file count (matches al2o3/neb). "
                         "Mutually exclusive with --xyz-init/--xyz-final.")
    ap.add_argument("--k-spring", type=float, default=0.02,
                    help="NEB &BAND K_SPRING (spring constant between replicas, in "
                         "[eV/angstrom^2]; default 0.02, al2o3/neb uses 0.08).")
    ap.add_argument("--program-run-info", action="store_true",
                    help="Add &BAND &PROGRAM_RUN_INFO ON (prints per-replica run info).")
    ap.add_argument("--convergence-info", action="store_true",
                    help="Add &BAND &CONVERGENCE_INFO ON (prints band convergence info).")
    # ---- QM/MM (--type qmmm) : MIXED + FIST(MM) + Quickstep(PM6 QM) ----
    ap.add_argument("--qm-elem", nargs="+", default=None,
                    help="QM region element(s), e.g. --qm-elem C H O (treated with "
                         "Quickstep + QS METHOD PM6 semi-empirical).")
    ap.add_argument("--mm-elem", nargs="+", default=None,
                    help="MM region element(s), e.g. --mm-elem Cu (treated with "
                         "FIST classical force field).")
    ap.add_argument("--qm-method", default="PM6",
                    choices=["PM6", "PM3", "AM1", "RM1", "MNDO"],
                    help="Semi-empirical method for the QM region (default PM6; "
                         "PM3/AM1/RM1/MNDO also valid QS METHOD values).")
    ap.add_argument("--qm-atoms", default="",
                    help="QM fragment atom range for &MIXED &MAPPING &FRAGMENT 1, "
                         "e.g. '1 56' (atoms 1..56 are the QM region).")
    ap.add_argument("--mm-atoms", default="",
                    help="MM fragment atom range for &MIXED &MAPPING &FRAGMENT 2, "
                         "e.g. '57 2936' (remaining atoms are MM).")
    ap.add_argument("--qm-topology", default="",
                    help="Coordinate file of the QM fragment (Quickstep subsys "
                         "TOPOLOGY). Separate from the full system file. e.g. ./f")
    ap.add_argument("--qmmm-run-type", default="MD",
                    help="GLOBAL RUN_TYPE for the QM/MM job (default MD; use "
                         "GEO_OPT to relax the QM region).")
    ap.add_argument("--group-partition", default="1 1",
                    help="&MIXED GROUP_PARTITION (MPI ranks per mixed eval, e.g. "
                         "'2 6' = 2 for FIST, 6 for Quickstep).")

    ap.add_argument("-o", "--output", required=True)
    args = ap.parse_args()

    tpl_path = os.path.join(TEMPLATES, args.type + ".inp")
    if not os.path.exists(tpl_path):
        sys.exit(f"template not found: {tpl_path}")
    tpl = open(tpl_path).read()

    # Apply fine-grained SCF / MGRID knobs (QM/MM's PM6 region has no
    # plane-wave cut-off, so skip it to avoid clobbering the [angstrom] CUTOFF).
    if args.type != "qmmm":
        tpl = tune_scf_block(
            tpl,
            cutoff=args.cutoff, rel_cutoff=args.rel_cutoff,
            eps_scf=args.eps_scf, max_scf=args.max_scf,
            scf_guess=args.scf_guess, eps_diis=args.eps_diis,
            added_mos=args.added_mos, cholesky=args.cholesky,
            wfn_restart=args.wfn_restart,
            eps_adapt=args.diagonalization_eps_adapt)

    # MD defaults to restart-on (every step + history), other types off.
    if args.type == "aimd_md" and args.restart_freq == 0:
        args.restart_freq = 500

    if args.kinds:
        kinds = parse_kinds(args.kinds)
        any_u = any(k["u"] is not None for k in kinds)
        bases = [k["basis"] for k in kinds]
    else:
        elems, bases, pots = normalize_elists(args.elem, args.basis, args.potential)
        kinds = [{"name": e, "element": e, "basis": b, "potential": p,
                  "u": None, "mag": None, "mass": None, "l": 2, "noramp": False}
                 for e, b, p in zip(elems, bases, pots)]
        any_u = False
    tpl = replace_kind_block(tpl, kinds, admm=args.admm)
    if any_u:
        tpl = inject_plus_u_method(tpl, args.plus_u_method)
    if args.stress_tensor:
        tpl = inject_stress_tensor(tpl, args.stress_tensor.upper())

    # inject &KPOINTS when requested (metals / convergence-critical)
    if args.kpoints and args.periodic != "none":
        try:
            kx, ky, kz = args.kpoints.split()
            kp = ("    &KPOINTS\n"
                  "      SCHEME MONKHORST-PACK {} {} {}\n"
                  "      SYMMETRY OFF\n"
                  "    &END KPOINTS").format(kx, ky, kz)
            tpl = re.sub(r"(\n[ \t]*&END MGRID)", r"\1\n" + kp, tpl, count=1)
        except ValueError:
            sys.exit("ERROR: --kpoints 需要 3 个整数，如 '6 6 6'")

    a = args.cell
    # split properties into the three placement groups
    props = [p.lower() for p in (args.properties or [])]
    _dftprint_ok = {"dos", "pdos", "cube", "band", "mulliken", "lowdin",
                    "hirshfeld", "charges", "mo", "elf", "vhartree", "moments"}
    props_under_dftprint = [p for p in props if p in _dftprint_ok]
    props_under_feprint = [p for p in props if p == "stress"]
    props_under_localize = [p for p in props if p == "wannier"]

    ensemble_map = {"nve": "NVE", "nvt": "NVT", "npt": "NPT_I"}

    repl = {
        "__PROJECT__": args.project,
        "__ELEM__": "",
        "__BASIS__": "",
        "__POTENTIAL__": "",
        "__A1__": str(a[0]), "__A2__": str(a[1]), "__A3__": str(a[2]),
        "__B1__": str(a[3]), "__B2__": str(a[4]), "__B3__": str(a[5]),
        "__C1__": str(a[6]), "__C2__": str(a[7]), "__C3__": str(a[8]),
        "__CHARGE__": str(args.charge),
        "__SPIN__": spin_block(args.multiplicity),
        "__QS_BLOCK__": qs_block(args.multiplicity, args.gapw),
        "__XC_BLOCK__": xc_block(args.functional),
        "__VDW_BLOCK__": vdw_block() if args.dispersion else "",
        "__POISSON_BLOCK__": poisson_block(args.periodic),
        "__SURFACE_DIPOLE_BLOCK__": surface_dipole_block(
            args.surface_dipole, args.dipole_dir, args.dipole_pos,
            args.dipole_switch),
        "__SMEAR_BLOCK__": smear_block(args.smear),
        "__OUTER_SCF_BLOCK__": outer_scf_block(args.outer_scf),
        "__OPTIMIZER_BLOCK__": optimizer_block(
            args.optimizer or ("cg" if args.type == "cell_opt" else "bfgs")),
        "__CONSTRAINT_BLOCK__": constraint_block(
            args.fixed_atoms, args.constraint_g3x3, args.g3x3_distances,
            args.constraint_hbonds, args.hbond_atom_type, args.hbond_targets),
        "__METADYN_WW__": metadyn_ww_block(args.metadyn_ww),
        "__METADYN_EXTRA__": metadyn_extra_block(
            args.well_tempered, args.delta_t, args.wtgamma, args.lagrange,
            args.multi_walker, args.plumed, args.plumed_file),
        "__GLOBAL_PRINT__": global_print_block(args.print_forces),
        "__BAND_TYPE__": args.band_type,
        "__NPROC_REP__": str(args.nproc_rep),
        "__N_REPLICA__": "2",
        "__K_SPRING__": "0.02",
        "__ALIGN_FRAMES__": "T",
        "__ROTATE_FRAMES__": "F",
        "__OPTIMIZE_BAND_BLOCK__": "",
        "__REPLICA_BLOCKS__": "",
        "__PROGRAM_RUN_INFO__": "",
        "__CONVERGENCE_INFO__": "",
        # ---- QM/MM (--type qmmm) tokens ----
        "__RUN_TYPE__": "MD",
        "__GROUP_PARTITION__": "1 1",
        "__QM_ATOMS__": "# TODO: QM atom range, e.g. 1 56",
        "__MM_ATOMS__": "# TODO: MM atom range, e.g. 57 2936",
        "__ALL_KIND_BLOCK__": "",
        "__MM_KIND_BLOCK__": "",
        "__MM_CHARGE_BLOCK__": "",
        "__MM_NONBONDED_BLOCK__": "",
        "__QM_METHOD__": "PM6",
        "__QM_KIND_BLOCK__": "",
        "__QM_TOPOLOGY__": "TODO_qm_fragment.xyz",
        "__COORD_FMT__": "xyz",
        "__TOPOLOGY__": "TODO_full_structure.xyz",
        "__ADMM_BLOCK__": admm_block(args.admm),
        "__BASIS_ADMM_FILE__": basis_admm_file_line(bases) if args.admm else "",
        "__MIXING_BLOCK__": mixing_block(args.mixing_method, args.mixing_alpha,
                                         args.mixing_nbroyden, args.mixing_beta),
        "__OT_BLOCK__": ot_minimizer_block(args.ot_minimizer),
        "__PROPERTIES_BLOCK__": "",  # retired placeholder (no template uses it)
        "__DFT_PRINT_BLOCK__": dft_print_block(
            props_under_dftprint, expand_ranges(args.ldos_list),
            print_style=args.print_style, cube_stride=args.cube_stride,
            pdos_nlumo=args.pdos_nlumo, pdos_nhomo=args.pdos_nhomo),
        "__FE_PRINT_BLOCK__": fe_print_block(props_under_feprint),
        "__LOCALIZE_BLOCK__": localize_block(props_under_localize),
        "__THERMOSTAT_BLOCK__": thermostat_block(args.thermostat),
        "__ENSEMBLE__": ensemble_map.get(args.ensemble, "NVT"),
        "__BAROSTAT_BLOCK__": barostat_block(args.ensemble == "npt"),
        "__RESTART_BLOCK__": restart_block(args.restart_freq) if args.restart_freq > 0 else "",
        "__VELOCITIES_BLOCK__": velocities_block(args.velocities),
    }

    if args.type == "neb":
        ci = read_xyz(args.xyz_init)
        cf = read_xyz(args.xyz_final)
        n_rep, rep_blocks = replica_blocks(args.xyz_replicas, ci, cf)
        repl["__N_REPLICA__"] = str(n_rep)
        repl["__K_SPRING__"] = str(args.k_spring)
        repl["__ALIGN_FRAMES__"] = args.align_frames
        repl["__ROTATE_FRAMES__"] = args.rotate_frames
        repl["__OPTIMIZE_BAND_BLOCK__"] = optimize_band_block(
            args.optimize_band, args.optimize_end_points == "T")
        repl["__REPLICA_BLOCKS__"] = rep_blocks
        repl["__PROGRAM_RUN_INFO__"] = (
            "    &PROGRAM_RUN_INFO ON\n    &END PROGRAM_RUN_INFO"
            if args.program_run_info else "")
        repl["__CONVERGENCE_INFO__"] = (
            "    &CONVERGENCE_INFO ON\n    &END CONVERGENCE_INFO"
            if args.convergence_info else "")
    elif args.type == "qmmm":
        qm = list(args.qm_elem or ["C"])
        mm = list(args.mm_elem or ["Cu"])
        all_elems = qm + mm
        repl["__RUN_TYPE__"] = args.qmmm_run_type
        repl["__GROUP_PARTITION__"] = args.group_partition
        repl["__TOPOLOGY__"] = args.topology or "TODO_full_structure.xyz"
        repl["__COORD_FMT__"] = (args.topology_format or "xyz").lower()
        repl["__QM_ATOMS__"] = args.qm_atoms or "# TODO: QM atom range, e.g. 1 56"
        repl["__MM_ATOMS__"] = args.mm_atoms or "# TODO: MM atom range, e.g. 57 2936"
        repl["__ALL_KIND_BLOCK__"] = kind_block_simple(all_elems)
        repl["__MM_KIND_BLOCK__"] = kind_block_simple(mm)
        repl["__MM_CHARGE_BLOCK__"] = mm_charge_block(mm)
        repl["__MM_NONBONDED_BLOCK__"] = mm_nonbonded_block(mm)
        repl["__QM_METHOD__"] = args.qm_method
        repl["__QM_KIND_BLOCK__"] = kind_block_simple(qm)
        repl["__QM_TOPOLOGY__"] = args.qm_topology or "TODO_qm_fragment.xyz"
    else:
        if args.topology:
            fmt = (args.topology_format or "cif").upper()
            # &TOPOLOGY reads the structure from an external file (CIF/POSCAR/xyz)
            # and replaces &COORD entirely (do NOT also emit &COORD).
            structure = (
                "  &TOPOLOGY\n"
                "    COORD_FILE_NAME {}\n".format(args.topology) +
                "    COORD_FILE_FORMAT {}\n".format(fmt) +
                "  &END TOPOLOGY"
            )
        else:
            if args.xyz:
                coord = read_xyz(args.xyz)
            elif args.coord:
                coord = args.coord
            else:
                coord = "# TODO: fill &COORD with 'Element x y z' per line"
            structure = "  &COORD\n{}\n  &END COORD".format(coord)
        repl["__STRUCTURE_BLOCK__"] = structure

    out = tpl
    for k, v in repl.items():
        out = out.replace(k, v)
    open(args.output, "w").write(out)
    print(f"written: {args.output}")


if __name__ == "__main__":
    main()
