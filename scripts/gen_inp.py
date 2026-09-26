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

# --- 控制台编码兼容层（中文 Windows/GBK 下输出 ✓ ⑪ Å 等符号不再抛异常）---
try:
    import os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    for _d in (_here, _os.path.join(_here, "scripts")):
        if _d not in _sys.path:
            _sys.path.insert(0, _d)
    import _console  # noqa: F401  导入即生效，见 scripts/_console.py
except Exception:
    pass

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
    """读 XYZ 坐标文件。健壮性基线：路径不存在/格式错误 → 友好中文 + exit 1。"""
    if not path:
        return None
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except FileNotFoundError:
        print(f"\n[ERROR] 找不到坐标文件: {path}", file=sys.stderr)
        print("  请检查 --xyz 路径是否正确；也可以改用 --coord 直接写坐标：",
              file=sys.stderr)
        print('    --coord "Si 0 0 0"', file=sys.stderr)
        sys.exit(1)
    except IsADirectoryError:
        print(f"\n[ERROR] --xyz 给的是目录，不是文件: {path}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"\n[ERROR] 无权限读取: {path}", file=sys.stderr)
        sys.exit(1)
    if not lines:
        print(f"\n[ERROR] 坐标文件是空的: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        n = int(lines[0].split()[0])
    except (ValueError, IndexError):
        print(f"\n[ERROR] 坐标文件第一行不是原子数: {path}", file=sys.stderr)
        print(f"  XYZ 格式要求第 1 行是原子数，第 2 行是注释，第 3 行起是坐标。",
              file=sys.stderr)
        sys.exit(1)
    coord = []
    for ln in lines[2:2 + n]:
        p = ln.split()
        if len(p) >= 4:
            coord.append(f"{p[0]} {p[1]} {p[2]} {p[3]}")
    if not coord:
        print(f"\n[ERROR] 坐标文件里没读到任何有效坐标行: {path}", file=sys.stderr)
        print("  每行格式应为：元素 x y z（如 'Si 0.0 0.0 0.0'）", file=sys.stderr)
        sys.exit(1)
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


def cell_periodic_line(periodic):
    """`&SUBSYS/&CELL` 里的 `PERIODIC` 行。

    **为什么必须与 `&DFT/&POISSON` 一起发**：官方 schema 对 `&POISSON/PERIODIC`
    的描述原文是 *"Important notice, this only applies to the **electrostatics**.
    See the **CELL** section to specify the periodicity used for e.g. the pair lists.
    **Typically the settings should be the same.**"*

    也就是说 `&POISSON PERIODIC NONE` **只管静电**，pair list / 结构的周期性由
    `&CELL PERIODIC` 决定。早先只发前者 ⇒ "静电按非周期、pair list 仍按 XYZ"，
    两者不一致，正是官方提醒要避免的情形（孤立分子/团簇会白算邻居表，
    表面 slab 的 z 方向也可能多算一层周期性镜像）。
    """
    if periodic == "none":
        return "      PERIODIC NONE"
    if periodic == "xy":
        return "      PERIODIC XY"
    return ""      # xyz（默认）：不发，用 CP2K 自己的默认值


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


def qs_block(multiplicity, gapw=False, wf_extrapolation=False):
    """&QS block.

    * --gapw  -> METHOD GAPW (all-electron core reconstruction)
    * WF_INTERPOLATION ASPC + EXTRAPOLATION_ORDER 3 (these are &QS keywords,
      NOT &DFT keywords)

    WF_INTERPOLATION / EXTRAPOLATION_ORDER 是**波函数外推**：每一步 MD 用上一步
    的波函数/密度外推初猜，能显著减少 SCF 迭代。它对 **MD 是性能关键**，与自旋
    无关 —— 早先的实现只在 `--multiplicity > 0` 时才发，于是所有闭壳层 MD 都白
    白多花 SCF 时间。生产卡（H 层 cases/）7/7 张都写这两行。
    现在的规则：
      * `--multiplicity > 0`            -> 照旧发（保持向后兼容）
      * MD 路线（aimd_md / metadyn）    -> 默认发，见主程序里传的 wf_extrapolation
      * `--no-wf-extrapolation`        -> 一律不发
    Emitted only when gapw or (spin-polarized / WF extrapolation requested);
    otherwise omitted (CP2K defaults to GPW).
    """
    lines = ["    &QS"]
    if gapw:
        lines.append("      METHOD GAPW")
    if (multiplicity and multiplicity > 0) or wf_extrapolation:
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


def basis_library_files(bases):
    """Return the BASIS_SET_FILE_NAME line(s) for the **primary** basis sets.

    MOLOPT-family bases live in ``BASIS_MOLOPT``; ``BASIS_SET`` only holds the
    older GTH/PADE bases.  The templates used to hardcode ``BASIS_SET`` while
    ``recommend.py`` recommends ``DZVP-MOLOPT-SR-GTH`` for metals -- the two
    contradicted each other and the generated input died with
    "basis set not found".  Now the library file follows the basis family.
    """
    files = []
    for b in (bases or []):
        fname = "BASIS_MOLOPT" if "MOLOPT" in b.upper() else "BASIS_SET"
        if fname not in files:
            files.append(fname)
    if not files:
        files = ["BASIS_SET"]
    return "\n".join("    BASIS_SET_FILE_NAME {}".format(f) for f in files)


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

    BROYDEN_MIXING 默认值对齐**真实生产卡**（H 层 cases/ 的 6/6 张非 OT 卡
    一律 ALPHA 0.1 / BETA 1.5 / NBROYDEN 8）：

      &MIXING
        METHOD BROYDEN_MIXING
        ALPHA 0.1        ! 电荷混合系数；0.4 对金属/大体系偏激进、易 SCF 抖
        BETA 1.5         ! 残差混合（Pulay 型），加速收敛
        NBROYDEN 8
      &END MIXING

    早先 ALPHA 默认 0.4 且 BETA 直接省略 —— 与生产写法不一致，金属表面
    体系更容易 SCF 不收敛。PULAY_MIXING 分支保持它自己的默认 0.2
    （`alpha or 0.2`）；此前 `--mixing-alpha` 的全局默认 0.4 会盖掉它，
    现在 CLI 默认改为 None，各方法才真正拿到自己的默认值。
    """
    if not method or method == "broyden":
        a = 0.1 if alpha is None else alpha
        b = 1.5 if beta is None else beta
        # BETA <= 0 视为"不发这一行"，交给 CP2K 默认（给用户一个退出阀）
        beta_line = "          BETA {}\n".format(b) if (b is not None and b > 0) else ""
        return (
            "        &MIXING\n"
            "          METHOD BROYDEN_MIXING\n"
            f"          ALPHA {a}\n"
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


def ot_minimizer_block(minimizer, preconditioner=None, linesearch=None):
    """OT minimizer block. Valid MINIMIZER: DIIS, CG, BROYDEN, SD (official).

    语义（2026-xx 修正）：**只有显式给了 --ot-minimizer 才发 `&OT`**；

      * `minimizer` 为 None/""  ⇒ 返回 ""，走**对角化**路线（与历史默认行为一致）
      * 给了任何值（含 `diis`）  ⇒ 发 `&OT MINIMIZER <值>`

    修正前的实现把 `diis` 当成"没给"（`if not minimizer or minimizer == "diis"`），
    于是 `--ot-minimizer diis` 生成的是**对角化**输入（`&OT` 0 处、
    `&DIAGONALIZATION` 反而是开的），而 help 写的是 "OT minimizer. diis=default"
    —— 用户以为在跑 OT+DIIS，实际跑的是对角化，且没有任何提示。
    官方 `&OT MINIMIZER` 默认是 **CG**，`DIIS` 是**合法**取值，所以"DIIS 就是
    不发 &OT"这个隐含约定既错又不可见。

    PRECONDITIONER 默认仍发 `FULL_SINGLE_INVERSE`（保持既有生成物逐字节不变）；
    官方默认是 `FULL_KINETIC`，可用 --ot-preconditioner 显式指定。
    LINESEARCH 默认**不发**（CP2K 用默认 2PNT），可用 --ot-linesearch 指定。
    """
    if not minimizer:
        return ""
    prec = (preconditioner or "FULL_SINGLE_INVERSE").upper()
    m = minimizer.upper()
    lines = ["        &OT",
             f"          MINIMIZER {m}",
             f"          PRECONDITIONER {prec}"]
    if linesearch:
        lines.append(f"          LINESEARCH {linesearch.upper()}")
    lines.append("        &END OT")
    return "\n".join(lines)


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


def localize_block(props_list, md=False):
    """&DFT &LOCALIZE &PRINT &WANNIER_CENTERS 段（Wannier 中心，供 TRAVIS 做真 IR）。

    修正前只发 `METHOD CRAZY` + `&WANNIER_CENTERS ON` + `&EACH QS_SCF 10`，
    有三个会**直接毁掉下游流程**的缺陷（官方 cp2k_input.xml 定案）：

      * 缺 `IONS+CENTERS`（官方默认 F）：它的语义是 "prints out the wannier
        centers together with the particles" —— 不开它，Wannier 中心与原子核
        **不在同一个文件**里，TRAVIS 需要的"含 `X` 行的 xyz"根本拿不到。
      * 缺 `FILENAME`：默认走 `projectname-filename` 规则，文件名不可预期；
        讲义与 `references/postprocess.md` 都要求固定成 `wannier.xyz`。
      * `&EACH QS_SCF 10` 不是 MD 步：AIMD 里每个 MD 步只做一次（或几次）SCF，
        按 `QS_SCF 10` 计数会得到极稀疏、甚至只有 1 帧的"轨迹"。
        MD 家族（RUN_TYPE MD）改用 `&EACH MD 1`（讲义原文"每个 MD 步骤都输出"）。

    非 MD（static / geo_opt / vib）仍用 `QS_SCF 10`（保持既有生成物不变）。
    """
    if not props_list or "wannier" not in [p.lower() for p in props_list]:
        return ""
    each_key = "MD 1" if md else "QS_SCF 10"
    return (
        "  &LOCALIZE\n"
        "    METHOD CRAZY\n"
        "    &PRINT\n"
        "      &WANNIER_CENTERS ON\n"
        "        IONS+CENTERS\n"
        "        FILENAME wannier.xyz\n"
        "        &EACH\n"
        "          {}\n".format(each_key) +
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



def _fmt_num(v):
    """把 1000.0 打成 '1000'、0.5 打成 '0.5'。

    生成物要跟真实生产卡长得一样：生产写 `TIMECON [wavenumber_t] 1000`，
    不是 `1000.0`。用户从 `--timecon 1000` 传进来的意图就是整数。
    """
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return str(int(f)) if f == int(f) else repr(f)


def thermostat_block(kind="csvr", timecon=100, timecon_unit="fs",
                     nose_length=3, nose_yoshida=3, nose_mts=2):
    """Thermostat block for MD.

    CP2K &THERMOSTAT takes TYPE as a *keyword inside* the section (not a
    section parameter). Valid TYPE: CSVR, NOSE, GLE, AD_LANGEVIN. TIMECON
    lives inside the &CSVR / &NOSE / &AD_LANGEVIN subsection. 'langevin'
    maps to AD_LANGEVIN (a valid, robust thermostat type for surfaces).
    Plain LANGEVIN requires ENSEMBLE LANGEVIN + &THERMAL_REGION, so we use
    AD_LANGEVIN.

    **TIMECON 的单位必须写出来**（`[fs]` / `[wavenumber_t]`）。同一个数字在
    两种单位下语义完全不同：生产卡写 `TIMECON [wavenumber_t] 1000`，CP2K
    回显 `Nose-Hoover-Chain time constant [  fs]  33.36` —— 即 33.36 fs；
    而不带单位的 `TIMECON 1000` 是 1000 **fs**，两者差 30 倍。换算：
        t[fs] = 33356.40952 / ν̃[cm^-1]      （ν̃ 是波数，cm^-1）
        1000 cm^-1 -> 33.36 fs ；100 fs -> 333.56 cm^-1
    所以**抄生产卡时必须连方括号里的单位一起抄**。

    &NOSE 的三个子关键字（生产卡 7/7 都写，.out 实测三行都生效）：
      LENGTH  3  Nose-Hoover 链长（多个热浴串起来，采样更接近正则系综）
      YOSHIDA 3  高阶 Yoshida 积分器阶数（辛积分，能量守恒更好）
      MTS     2  多重时间步（把 thermostat 力按 1/2 步长积分）
    默认就给 3/3/2 —— 这三个值既是**真实生产卡**的写法，也正好等于官方
    `cp2k_input.xml` 里 LENGTH / YOSHIDA / MTS 的默认值（`_kw_probe.py` 可查），
    所以把它们显式写出来只是"把默认写明"，不会改变物理行为。
    想让 CP2K 用自己的默认值（= 不写这行）就传 0 或负数。
    """
    k = (kind or "csvr").lower()
    unit = (timecon_unit or "fs").strip()
    if unit not in ("fs", "wavenumber_t"):
        unit = "fs"
    timecon_line = "          TIMECON [{}] {}\n".format(unit, _fmt_num(timecon))

    def _nose_extra():
        out = []
        if nose_length and nose_length > 0:
            out.append("          LENGTH {}\n".format(int(nose_length)))
        if nose_yoshida and nose_yoshida > 0:
            out.append("          YOSHIDA {}\n".format(int(nose_yoshida)))
        if nose_mts and nose_mts > 0:
            out.append("          MTS {}\n".format(int(nose_mts)))
        return "".join(out)

    if k == "nose":
        return (
            "      &THERMOSTAT\n"
            "        TYPE NOSE\n"
            "        &NOSE\n"
            + _nose_extra() + timecon_line +
            "        &END NOSE\n"
            "      &END THERMOSTAT"
        )
    if k == "langevin":
        return (
            "      &THERMOSTAT\n"
            "        TYPE AD_LANGEVIN\n"
            "        &AD_LANGEVIN\n"
            + "          TIMECON_LANGEVIN [{}] {}\n".format(unit, _fmt_num(timecon))
            + "          TIMECON_NH [{}] {}\n".format(unit, _fmt_num(timecon)) +
            "        &END AD_LANGEVIN\n"
            "      &END THERMOSTAT"
        )
    # default CSVR
    return (
        "      &THERMOSTAT\n"
        "        TYPE CSVR\n"
        "        &CSVR\n"
        + timecon_line +
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


def inject_cell_symmetry(tpl, symmetry):
    """把 `SYMMETRY <晶系>` 注入 `&SUBSYS/&CELL`。

    为什么需要它：官方 `KEEP_SYMMETRY` 的说明原文是 "The initial symmetry must
    be specified in the &CELL section"，而 `&CELL SYMMETRY` 官方默认是 `NONE`
    —— 只写 `KEEP_SYMMETRY T` 而 `&CELL` 里没有 `SYMMETRY` 时该开关**空转**
    （`references/official/05_optimization.md:355`："KEEP_SYMMETRY 应始终与
    FORCE_EVAL/SUBSYS/CELL/SYMMETRY 指定的晶胞对称性一起使用"）。

    用正则注入而**不改模板**：模板同时被用户手工复制，加 token 会在生成物里
    多出一行空白，破坏"未给本开关时生成物逐字节不变"这条向后兼容要求。
    """
    if not symmetry:
        return tpl
    pat = re.compile(r"(\n[ \t]*&CELL[ \t]*)\n")
    return pat.sub(r"\1\n      SYMMETRY {}\n".format(symmetry.upper()), tpl,
                   count=1)


def inject_cell_opt_constraint(tpl, constraint):
    """把 `CONSTRAINT <方向>` 注入 `&MOTION/&CELL_OPT`（晶胞方向约束）。

    官方 schema：`&CELL_OPT/CONSTRAINT` 默认 `NONE`，取值 none|x|y|z|xy|xz|yz，
    "Imposes a constraint on the pressure tensor by fixing the specified cell
    components"。二维材料/表面 slab 的真空层必须靠它保住
    （`references/official/05_optimization.md:346`："对表面或层状系统，通常
    更好的做法是只弛豫物理上有意义的晶胞方向"）。

    注意它与 `&MOTION/&CONSTRAINT`（原子约束，`--fixed-atoms`）**不是一回事**。
    """
    if not constraint:
        return tpl
    pat = re.compile(r"(\n[ \t]*&CELL_OPT[ \t]*)\n")
    return pat.sub(r"\1\n    CONSTRAINT {}\n".format(constraint.upper()), tpl,
                   count=1)


def apply_trajectory_format(tpl, fmt):
    """给 `&MOTION/&PRINT/&TRAJECTORY` 写 `FORMAT <fmt>`。

    讲师反复强调：**晶胞体积在变的场景（CELL_OPT / NPT AIMD）最好存 PDB** ——
    xyz/xmol 不含晶胞信息，PDB 含。官方 `&TRAJECTORY FORMAT` 默认 `XMOL`，
    取值 atomic|dcd|dcd_aligned_cell|pdb|xmol|xyz。

    模板已有 `&TRAJECTORY`（aimd_md / metadyn）→ 直接在其下插一行 FORMAT；
    模板没有（static / geo_opt / cell_opt / vib / neb / qmmm）→ 在 `&MOTION`
    之后新建一个 `&PRINT` 段。两者都**只在用户显式给 --trajectory-format 时**
    才动模板，因此默认生成物逐字节不变。
    """
    if not fmt:
        return tpl
    fmt = fmt.upper()
    m = re.search(r"\n[ \t]*&TRAJECTORY[ \t]*\n", tpl)
    if m:
        return tpl[:m.end()] + "      FORMAT {}\n".format(fmt) + tpl[m.end():]
    block = ("\n  &PRINT\n"
             "    &TRAJECTORY\n"
             "      FORMAT {}\n"
             "      &EACH\n"
             "        MD 1\n"
             "      &END EACH\n"
             "    &END TRAJECTORY\n"
             "  &END PRINT").format(fmt)
    pat = re.compile(r"(\n[ \t]*&MOTION[ \t]*)\n")
    return pat.sub(lambda mm: mm.group(1) + block + "\n", tpl, count=1)


def _note(msg):
    """生成期的中文提示（stdout 保持只有 `written:`，提示统一走 stderr）。

    stderr 也被 `_console.py` 兜底成 errors="replace"，非 GBK 字符最多显示成
    "?"，不会抛异常。
    """
    print("[note] " + msg, file=sys.stderr)


def _flag_given(name):
    """命令行里是否**显式**出现了某个开关（`--x` 或 `--x=值`）。

    用途：判断"用户以为设了、而模板里根本没有出口"的静默失效。不能用
    argparse 的默认值来判断 —— 这些开关大多有非空默认值（如
    `--mixing-method broyden`），按默认值判断会把**没传开关的普通调用**也
    报成"你的开关不生效"，变成噪音。
    """
    return any(a == name or a.startswith(name + "=") for a in sys.argv[1:])


def diagonalization_block(enabled=True, algorithm="STANDARD", eps_adapt=None):
    """&SCF/&DIAGONALIZATION 段（对角化路线）。

    为什么要有它：`--diagonalization-eps-adapt` 早先只能注入**模板里已经写着**
    `ALGORITHM STANDARD` 的 `static.inp`；`aimd_md.inp` 根本没有
    `&DIAGONALIZATION` 段，于是这个选项在 MD 上**无处注入、静默失效**。而真实
    生产卡（H 层 cases/，含 MD 卡）写的就是

      &DIAGONALIZATION
        ALGORITHM STANDARD
        EPS_ADAPT 0.01
      &END DIAGONALIZATION

    - ALGORITHM：对角化算法（CP2K 常用 STANDARD / OT / DAVIDSON / FILTER_MATRIX）
    - EPS_ADAPT：自适应 DIIS 阈值。设 > 0 时，SCF 前期用宽松阈值（快），
      接近收敛才收紧 —— 金属/大体系省时间的关键旋钮。
    OT 路线（显式给了 --ot-minimizer，或 --scf-route ot）下不发本段：CP2K 用
    &OT，&DIAGONALIZATION 会被忽略，发出来只会让人误以为在走对角化。
    """
    if not enabled:
        return ""
    lines = ["      &DIAGONALIZATION",
             "        ALGORITHM {}".format(algorithm or "STANDARD")]
    if eps_adapt is not None:
        lines.append("        EPS_ADAPT {}".format(eps_adapt))
    lines.append("      &END DIAGONALIZATION")
    return "\n".join(lines)


def tune_scf_block(tpl, cutoff=None, rel_cutoff=None, eps_scf=None,
                   max_scf=None, scf_guess=None, eps_diis=None,
                   added_mos=None, cholesky=None, wfn_restart=None,
                   eps_adapt=None, algorithm=None, timestep=None):
    """Apply fine-grained SCF / MGRID knobs to a DFT template via regex.

    Only touches the FIRST occurrence of each keyword (the MGRID / SCF section
    of a Quickstep DFT; QM/MM's PM6 region has no plane-wave cut-off and is
    skipped by the caller). Missing args are left at the template default.
    Optional &SCF keywords (EPS_DIIS / ADDED_MOS / CHOLESKY) are injected right
    after the opening '&SCF' line (order-independent within &SCF).
    WFN_RESTART_FILE_NAME (a &DFT keyword, NOT &SCF) is injected right after
    the opening '&DFT' line. EPS_ADAPT is injected into '&DIAGONALIZATION ...
    ALGORITHM STANDARD' (the only place it is valid); `algorithm` rewrites that
    ALGORITHM value. `timestep` rewrites the first 'TIMESTEP <x>' (MD 与
    OPTIMIZE_BAND 的 TIMESTEP 都叫这个名，模板里只有 MD 那处是字面量).
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
    if timestep is not None:
        # 只改第一条 TIMESTEP（模板里 MD 的 TIMESTEP 是唯一的字面量；
        # neb 模板的 &OPTIMIZE_BAND TIMESTEP 由 optimize_band_block() 生成，
        # 那一步在 token 替换阶段、本函数之后）。
        tpl = re.sub(r"(\n[ \t]*TIMESTEP )[ \t]*\S+",
                     r"\g<1>{}".format(_fmt_num(timestep)), tpl, count=1)
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
    if algorithm is not None:
        # 只改 &DIAGONALIZATION 里那一处 ALGORITHM（锚定段名，避免误伤
        # 其它含 ALGORITHM 关键字的段）。
        tpl = re.sub(r"(&DIAGONALIZATION[ \t]*\n[ \t]*ALGORITHM )[ \t]*\S+",
                     r"\g<1>{}".format(algorithm), tpl, count=1)
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
    ap.add_argument("--coord-include", default=None,
                    help="坐标走 CP2K 前处理器的 @INCLUDE（讲师主推的写法）："
                         "发射 `&COORD` + `@INCLUDE '<path>'` + `&END COORD`，"
                         "坐标本体留在外挂文件里。**该文件必须已经去掉 xyz 的前两行**"
                         "（行数/注释行），只留 'Element x y z' 行；"
                         "路径按相对 .inp 所在目录解析。与 --xyz/--coord/--topology "
                         "互斥（同时给时 --topology 优先）。")
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
    ap.add_argument("--deuterate", action="store_true",
                    help="氘代：把所有 H 的 &KIND MASS 设成 2（已显式给 mass= 的条目"
                         "不覆盖），并在 stderr 说明可放宽的步长。"
                         "依据：H 换成 D 后 O–H 3300 cm^-1 降到 ~2500 cm^-1，"
                         "含氢体系的 TIMESTEP 可从 1.0 fs 放宽到 ~1.2 fs。"
                         "--kinds 里逐条写 mass=2 也等价，本开关只是一键入口。")
    ap.add_argument("--trajectory-format", default=None,
                    choices=["xmol", "xyz", "pdb", "dcd", "atomic",
                             "dcd_aligned_cell"],
                    help="&MOTION/&PRINT/&TRAJECTORY FORMAT（官方默认 XMOL，"
                         "**不含晶胞信息**）。晶胞在变的场景（cell_opt / NPT AIMD）"
                         "建议 pdb。模板已有 &TRAJECTORY 就直接加 FORMAT 行，"
                         "没有（static/geo_opt/cell_opt/vib/neb）就新建一个 "
                         "&PRINT/&TRAJECTORY 段（含 &EACH MD 1）。")
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
                    help="NEB &BAND NPROC_REP（每个 replica 的 MPI 核数）。"
                         "**--type vib 也用同一个 token**（&VIBRATIONAL_ANALYSIS "
                         "NPROC_REP，模板默认 8）：固定原子算频率时 NPROC_REP "
                         "必须取小、让并行结构数尽量多，否则频率不可信。")
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
    ap.add_argument("--ot-minimizer", default=None,
                    choices=["diis", "cg", "broyden", "sd"],
                    help="OT minimizer（&OT MINIMIZER）。**不传 = 走对角化路线**"
                         "（不发 &OT，保持历史默认行为）；传任何值（含 diis）都会"
                         "发射 &OT + MINIMIZER <值>。官方 &OT MINIMIZER 默认 CG、"
                         "合法取值 DIIS/CG/BROYDEN/SD。想显式选路线用 --scf-route。")
    ap.add_argument("--scf-route", default="auto", choices=["auto", "ot", "diag"],
                    help="SCF 路线：auto（默认）= 不传 --ot-minimizer 走对角化、"
                         "传了就走 &OT；ot = 强制 &OT（没给 --ot-minimizer 时用"
                         "官方默认 CG）；diag = 强制对角化（忽略 --ot-minimizer）。")
    ap.add_argument("--ot-preconditioner", default=None,
                    choices=["full_all", "full_single_inverse", "full_single",
                             "full_kinetic", "full_s_inverse", "none"],
                    help="&OT PRECONDITIONER。默认仍发 FULL_SINGLE_INVERSE"
                         "（保持既有生成物不变）；**CP2K 官方默认是 FULL_KINETIC**，"
                         "手写输入卡不写这一行才是 FULL_KINETIC。")
    ap.add_argument("--ot-linesearch", default=None,
                    choices=["none", "2pnt", "3pnt", "gold"],
                    help="&OT LINESEARCH。默认不发（CP2K 用默认 2PNT）。"
                         "讲师建议和 MINIMIZER/PRECONDITIONER 一起测。")
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
                         "None=omit (生产卡用 0.01)。**对角化路线**（不传 "
                         "--ot-minimizer，或 --scf-route diag）才发本段；"
                         "走 &OT 时该段无意义。")
    ap.add_argument("--diagonalization-algorithm", default=None,
                    help="&DIAGONALIZATION ALGORITHM（默认 STANDARD，即生产卡写法）。"
                         "其它常用：OT / DAVIDSON / FILTER_MATRIX。"
                         "只在**对角化路线**生效（不传 --ot-minimizer，"
                         "或 --scf-route diag）。")
    ap.add_argument("--temperature", type=float, default=None,
                    help="&MD TEMPERATURE [K]（目标温度，恒温器据此控温）。"
                         "**模板里是写死的**：aimd_md 600 K、metadyn 450 K；"
                         "不给此开关就沿用模板值。注意官方 CP2K 对 "
                         "`MOTION/MD/TEMPERATURE` 的**默认是 300 K**，"
                         "模板取 600 K 是有意为之（短程 MD 采样更充分），"
                         "**不是官方默认**——要按实验条件算就显式给这个开关。")
    ap.add_argument("--timestep", type=float, default=None,
                    help="&MD TIMESTEP [fs]（模板默认 0.5）。真实生产卡：Cu/水 "
                         "0.5 fs 稳妥；TiO2 这类需要 2 fs（重原子、慢振动）。"
                         "AIMD 一般 0.5–1.0 fs；超过 ~2 fs 要检查能量守恒/漂移。")
    ap.add_argument("--mixing-alpha", type=float, default=None,
                    help="SCF mixing ALPHA。不给（None）按方法取默认："
                         "BROYDEN_MIXING 用 0.1（与真实生产卡一致），"
                         "PULAY_MIXING 用 0.2。0.4 对金属/大体系偏激进、易 SCF 抖动。")
    ap.add_argument("--mixing-beta", type=float, default=1.5,
                    help="SCF BROYDEN mixing BETA (residual mixing; 默认 1.5，"
                         "与真实生产卡一致)。传 <=0 表示不发 BETA 行、用 CP2K 默认。")
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
    ap.add_argument("--thermostat", default=None,
                    choices=["csvr", "nose", "langevin"],
                    help="MD thermostat. 不传=csvr（模板写法）；nose；langevin "
                         "(maps to AD_LANGEVIN, robust for surfaces). "
                         "nose 默认带 LENGTH 3 / YOSHIDA 3 / MTS 2（与真实生产卡一致）。"
                         "**--ensemble nve 时不发 &THERMOSTAT**（NVE 是微正则系综、"
                         "按定义不控温，发了也不生效）。")
    ap.add_argument("--timecon", type=float, default=100.0,
                    help="恒温器 TIMECON 的数值（默认 100）。**必须配合 "
                         "--timecon-unit 看**：同一个数字在两种单位下差 30 倍。")
    ap.add_argument("--timecon-unit", default="fs",
                    choices=["fs", "wavenumber_t"],
                    help="TIMECON 的单位方括号，默认 fs（保持既有行为）。"
                         "真实生产卡一律写 `TIMECON [wavenumber_t] 1000`。"
                         "换算（官方）：t[fs] = 33356.40952 / ν̃[cm^-1]，"
                         "所以 [wavenumber_t] 1000 就等于 [fs] 33.36；"
                         "反过来 [wavenumber_t] 不带单位写成 `TIMECON 1000` 则是 "
                         "1000 fs，差 30 倍。**抄生产卡时必须连方括号单位一起抄**："
                         "`--thermostat nose --timecon 1000 --timecon-unit wavenumber_t`。")
    ap.add_argument("--nose-length", type=int, default=3,
                    help="&NOSE LENGTH（Nose-Hoover 链长，默认 3 —— 与生产卡和 "
                         "CP2K 官方默认值都一致）。<=0 表示不发这一行。")
    ap.add_argument("--nose-yoshida", type=int, default=3,
                    help="&NOSE YOSHIDA（Yoshida 辛积分器阶数，默认 3 —— 与生产卡和 "
                         "CP2K 官方默认值都一致）。<=0 表示不发这一行。")
    ap.add_argument("--nose-mts", type=int, default=2,
                    help="&NOSE MTS（多重时间步数，默认 2 —— 与生产卡和 "
                         "CP2K 官方默认值都一致）。<=0 表示不发这一行。")
    ap.add_argument("--no-wf-extrapolation", dest="wf_extrapolation",
                    action="store_false",
                    help="关掉 &QS WF_INTERPOLATION ASPC + EXTRAPOLATION_ORDER 3。"
                         "MD 路线（aimd_md/metadyn）默认**开**（波函数外推对 MD 是"
                         "性能关键，与自旋无关）；--multiplicity>0 时也默认开。")
    ap.add_argument("--ensemble", default="nvt",
                    choices=["nve", "nvt", "npt"],
                    help="MD ensemble. npt adds &BAROSTAT automatically.")
    ap.add_argument("--restart-freq", type=int, default=0,
                    help="MD restart write frequency in steps (0=off; "
                         "default 500 for MD-family runs -- aimd_md AND metadyn -- "
                         "off for other run types).")
    ap.add_argument("--walltime", type=float, default=None,
                    help="&GLOBAL WALLTIME in seconds. Set it slightly below your "
                         "batch queue limit: CP2K then stops *cleanly* before being "
                         "killed and leaves a usable restart file (official "
                         "tutorials list the wall-clock limit as the #1 cause of "
                         "restarts). Example: --walltime 82800 for a 24 h limit.")
    ap.add_argument("--steps", type=int, default=None,
                    help="MD step count (&MOTION &MD STEPS). Template default is "
                         "500000 (production). For a first smoke test try "
                         "--steps 500 (cheap, ~minutes) before committing to a "
                         "long run. Also applies to --type metadyn.")
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
                    help="&FORCE_EVAL STRESS_TENSOR 的计算方式 "
                         "(ANALYTICAL/NUMERICAL) —— 与只负责“打印”的 "
                         "--properties stress 区分开。官方默认是 NONE；"
                         "**--type cell_opt 未显式给本开关时会自动发 ANALYTICAL**"
                         "（CELL_OPT 靠应力驱动，没有应力张量就跑不动），"
                         "要数值应力就写 --stress-tensor numerical。")
    ap.add_argument("--topology", default=None,
                    help="Read structure from an external file instead of &COORD, e.g. "
                         "'POSCAR.cif'. Emits &SUBSYS &TOPOLOGY COORD_FILE_NAME <file> "
                         "COORD_FILE_FORMAT <fmt>; mutually exclusive with --xyz/--coord.")
    ap.add_argument("--topology-format", default="cif",
                    help="TOPOLOGY COORD_FILE_FORMAT: cif (default), xyz, pdb, extxyz, "
                         "xyzpdb, gaussian, etc. (matching the --topology file type).")
    ap.add_argument("--cell-symmetry", default=None,
                    choices=["none", "triclinic", "monoclinic",
                             "monoclinic_gamma_ab", "orthorhombic",
                             "tetragonal_ab", "tetragonal_ac", "tetragonal_bc",
                             "tetragonal", "rhombohedral", "hexagonal", "cubic"],
                    help="&SUBSYS/&CELL SYMMETRY（官方默认 NONE）。**KEEP_SYMMETRY "
                         "必须配它才有意义**（官方原话：初始对称性必须在 &CELL 里"
                         "指定）。不传时不发这一行，并在 --type cell_opt 时提示"
                         "“KEEP_SYMMETRY 空转”。")
    ap.add_argument("--cell-opt-constraint", default=None,
                    choices=["none", "x", "y", "z", "xy", "xz", "yz"],
                    help="&MOTION/&CELL_OPT CONSTRAINT：固定指定的晶胞分量"
                         "（官方默认 NONE）。二维材料/表面 slab 用它保住真空层"
                         "（--periodic xy 建议 z）。注意它与原子约束 "
                         "&MOTION/&CONSTRAINT（--fixed-atoms）不是一回事。")
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
                    help="NEB &BAND K_SPRING（相邻 replica 之间的弹簧常数）。"
                         "单位是**原子单位 hartree/bohr^2**（官方 XML 对该关键字"
                         "不标注单位 ⇒ CP2K 内部原子单位）；官方默认 0.02，"
                         "粗算常用 0.08（al2o3/neb 写法）。"
                         "**不要按 eV/angstrom^2 理解**。")
    ap.add_argument("--neb-max-force", type=float, default=None,
                    help="NEB &BAND &CONVERGENCE_CONTROL MAX_FORCE"
                         "（默认 0.0006 —— 本 skill 的 GEO_OPT 模板同款门槛，"
                         "便于三件套互比；CP2K 官方默认是 4.5E-4，"
                         "讲义/讲者经验常放宽到 1E-3）。"
                         "注意：&BAND 的收敛判据与 &GEO_OPT 是**两套**关键字。")
    ap.add_argument("--neb-rms-force", type=float, default=None,
                    help="NEB &BAND &CONVERGENCE_CONTROL RMS_FORCE"
                         "（默认 0.0003，与 CP2K 官方默认一致）。")
    ap.add_argument("--program-run-info", action="store_true",
                    help="Add &BAND &PROGRAM_RUN_INFO ON (prints per-replica run info).")
    ap.add_argument("--convergence-info", action="store_true",
                    help="Add &BAND &CONVERGENCE_INFO ON (prints band convergence info).")
    ap.add_argument("--json", action="store_true",
                    help="输出 JSON（给 agent 用）")
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
    # 模板是 UTF-8：必须显式指定编码。
    # 用 locale 默认编码（中文 Windows = GBK）读 UTF-8 模板会抛
    # UnicodeDecodeError，导致 --type aimd_md 等生成直接崩溃。
    tpl = open(tpl_path, encoding="utf-8").read()

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
            eps_adapt=args.diagonalization_eps_adapt,
            algorithm=args.diagonalization_algorithm,
            timestep=args.timestep)

    # MD 路线（aimd_md / metadyn）：&QS 默认发波函数外推（ASPC）。
    # 波函数外推对 MD 是性能关键（每步少几轮 SCF），与自旋无关 ——
    # 生产卡 7/7 都写。由 --no-wf-extrapolation 关掉。
    _MD_TYPES = ("aimd_md", "metadyn")
    wf_extrap = bool(args.wf_extrapolation) and args.type in _MD_TYPES
    # ---- SCF 路线：auto（默认）/ ot / diag ----
    #
    # 修正前 --ot-minimizer 的默认值是 "diis"，而 ot_minimizer_block() 把 diis
    # 当成"没给" ⇒ `--ot-minimizer diis` 生成的是**对角化**输入（&OT 0 处），
    # 用户却以为在跑 OT+DIIS。现在：**显式给了任何值（含 diis）都发 &OT**，
    # 不传则保持历史行为（对角化 ⇒ 与修正前逐字节相同）。
    ot_block = ot_minimizer_block(args.ot_minimizer, args.ot_preconditioner,
                                  args.ot_linesearch)
    if args.scf_route == "diag":
        if ot_block:
            _note("--scf-route diag：已忽略 --ot-minimizer {}，本输入走对角化路线"
                  "（&DIAGONALIZATION）".format(args.ot_minimizer))
        ot_block = ""
    elif args.scf_route == "ot" and not ot_block:
        # 官方 &OT MINIMIZER 默认是 CG —— 强制走 OT 又不指定 minimizer 时用它。
        ot_block = ot_minimizer_block("cg", args.ot_preconditioner,
                                      args.ot_linesearch)
    # &DIAGONALIZATION 只在对角化路线（没发 &OT）才有意义。
    diag_block = diagonalization_block(
        enabled=not ot_block,
        algorithm=args.diagonalization_algorithm or "STANDARD",
        eps_adapt=args.diagonalization_eps_adapt)

    # MD 类默认开 restart（每步 + 历史副本），其它类型默认关。
    #
    # metadyn 与 aimd_md 一样是**长跑**（模板默认 200000 步），而且元动力学的
    # 偏置势/山高历史一旦丢就得从头再跑 —— 重启价值只高不低。早先只给 aimd_md
    # 默认，导致 `--type metadyn` 生成的输入没有 &RESTART_HISTORY，而
    # `diagnose.py` 检测到作业被 kill 时的处方第一条就是"确认 restart 文件在"。
    # 现在两者一致。
    if args.type in ("aimd_md", "metadyn") and args.restart_freq == 0:
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
    kind_names = [k["name"] for k in kinds]
    # ---- 氘代（--deuterate）：H 的 &KIND MASS 设 2 ----
    # 逐条写 --kinds "H:...:mass=2" 早就能做，但入口太深、且 help 里
    # --timestep 与"改了质量就能放宽步长"毫无联动。这里只做两件事：
    #   1) 一键把 H 的 MASS 设 2（**已显式给 mass= 的条目不覆盖**，尊重用户）；
    #   2) 打印可放宽步长的提示。
    _has_h = any((k.get("element") or "").strip().upper() == "H" for k in kinds)
    deuterated = []
    if args.deuterate:
        for k in kinds:
            if (k.get("element") or "").strip().upper() == "H" \
                    and k.get("mass") is None:
                k["mass"] = 2.0
                deuterated.append(k["name"])
        if deuterated:
            _note("--deuterate：已把 {} 的 &KIND MASS 设为 2（氘代）。"
                  "O–H 3300 cm^-1 -> O–D ~2500 cm^-1，含氢体系 TIMESTEP "
                  "可从 1.0 fs 放宽到约 1.2 fs（仍建议先做小步数能量守恒测试）。"
                  .format("、".join(deuterated)))
        else:
            _note("--deuterate：没有找到需要氘代的 H（体系不含 H，或 H 已经显式"
                  "给了 mass=）。")
    tpl = replace_kind_block(tpl, kinds, admm=args.admm)
    if any_u:
        tpl = inject_plus_u_method(tpl, args.plus_u_method)
    # ---- STRESS_TENSOR ----
    # 官方 &FORCE_EVAL/STRESS_TENSOR 默认 NONE，而 RUN_TYPE CELL_OPT 靠应力驱动：
    # 修正前 `--type cell_opt` 不带 --stress-tensor 时**一个应力关键字都不发**，
    # 生成物照常 "written:"、validate_inp 照常 OK，但晶胞优化实际拿不到应力。
    # 现在 cell_opt 默认 ANALYTICAL；用户显式给了值（含 numerical）就尊重用户。
    stress = args.stress_tensor
    if not stress and args.type == "cell_opt":
        stress = "analytical"
        _note("--type cell_opt：已自动发射 STRESS_TENSOR ANALYTICAL"
              "（CELL_OPT 必须有应力张量，官方默认是 NONE）；"
              "要数值应力请显式写 --stress-tensor numerical。")
    if stress:
        tpl = inject_stress_tensor(tpl, stress.upper())

    # ---- 晶胞对称性 / 晶胞方向约束 / 轨迹格式（都只在显式给开关时才动模板）----
    if args.cell_symmetry:
        tpl = inject_cell_symmetry(tpl, args.cell_symmetry)
    elif args.type == "cell_opt":
        _note("模板里的 KEEP_SYMMETRY T 目前是**空转**：官方要求它必须与 "
              "&SUBSYS/&CELL SYMMETRY 一起用（后者默认 NONE）。"
              "要么 --cell-symmetry <晶系> 指定对称性，要么手工删掉 "
              "KEEP_SYMMETRY。")
    if args.cell_opt_constraint and args.cell_opt_constraint != "none":
        tpl = inject_cell_opt_constraint(tpl, args.cell_opt_constraint)
    elif args.type == "cell_opt" and args.periodic == "xy":
        _note("--type cell_opt + --periodic xy（二维材料/表面）：真空方向通常"
              "不应参与弛豫，建议 --cell-opt-constraint z 固定 c 轴，"
              "否则真空层会被优化掉。")
    if args.trajectory_format:
        tpl = apply_trajectory_format(tpl, args.trajectory_format)

    # ---- 含氢体系的步长提示（不改用户给的值，只提示风险）----
    if _has_h and not args.deuterate and args.timestep is not None \
            and args.timestep > 1.0:
        _note("TIMESTEP {} fs + 含氢体系：O–H 振动周期约 10 fs，经验上限是"
              "周期的 1/10（1 fs）、文献常态是 1/20（0.5 fs）。"
              ">1 fs 请用 --deuterate 或做能量守恒测试后再生产。"
              .format(_fmt_num(args.timestep)))
    # ---- 坐标输入方式 × 类型的"静默无效"提示 ----
    # neb.inp 模板没有 __STRUCTURE_BLOCK__：NEB 的坐标只能走
    # --xyz-init/--xyz-final 或 --xyz-replicas，`--coord/--xyz/--coord-include`
    # 在 --type neb 下会被**静默丢掉**。
    if args.type == "neb" and (args.xyz or args.coord or args.coord_include):
        _note("--type neb 的坐标只能由 --xyz-init/--xyz-final（内联两帧）或 "
              "--xyz-replicas（多副本外部文件）提供；你给的 "
              "--xyz/--coord/--coord-include **对 neb 不生效**。")
    # ---- 系综 × 热浴的"静默无效"提示 ----
    if args.type == "aimd_md" and args.ensemble == "nve":
        _note("--ensemble nve：NVE 是**微正则系综**（N、V、E 恒定，官方原文 "
              "constant energy / microcanonical），按定义**不控温** ⇒ 本输入"
              "**不发 &THERMOSTAT 段**"
              + ("；你给的 --thermostat {} 在 NVE 下会被忽略。".format(
                  args.thermostat) if args.thermostat else "。")
              + "要控温请用 --ensemble nvt（默认）或 npt。")
    elif args.type == "metadyn" and args.ensemble != "nvt":
        _note("--type metadyn 的模板把 &MD ENSEMBLE 固定为 NVT、&THERMOSTAT 也写死"
              "为 CSVR，`--ensemble {}` 对 metadyn **不生效**（元动力学本来就"
              "要在恒温下采样）。".format(args.ensemble))
    # ---- &VIBRATIONAL_ANALYSIS + 固定原子：并行结构数提示 ----
    if args.type == "vib" and args.fixed_atoms:
        _note("--type vib + --fixed-atoms：固定原子算频率必须**多开并行结构**"
              "（结构数 = 总核数 / NPROC_REP）。当前 NPROC_REP = {}；"
              "例：56 核写 --nproc-rep 7 ⇒ 8 个并行结构。NPROC_REP 取太大"
              "会让频率不可信。".format(args.nproc_rep))

    # ---- 🔴 &VIBRATIONAL_ANALYSIS 的 INTENSITIES 必须配 &MOMENTS（否则真机直接 Abort）----
    # 模板里 `INTENSITIES T` 是**写死**的，而红外强度要读 [DIPOLE] 这个 result。
    # 没开 &MOMENTS 时 CP2K 会：
    #     [ABORT] Trying to access result ([DIPOLE]) which was never stored!
    #             common/cp_result_methods.F:183
    # 并在算第一个位移时就 Abort（**输入语法完全合法**，所以官方解析器校验不出来 ——
    # `_validate_all.py` 的 vib 用例一直是绿的，是拿真机跑才暴露的）。
    if args.type == "vib" and "&MOMENTS" not in tpl:
        _mom = ["    &PRINT", "      &MOMENTS"]
        if args.periodic == "none":
            # PERIODIC T(默认) 走 Berry 相位；PERIODIC F 走简单算符，
            # 官方描述："The latter normally requires that the CELL is periodic NONE."
            _mom.append("        PERIODIC FALSE")
        _mom += ["        MAX_MOMENT 4", "      &END MOMENTS", "    &END PRINT"]
        _momtxt = "\n".join(_mom)
        # 插到 &DFT 段的 &END DFT 之前（与其它注入一样，用正则而不改模板字节）
        _new, _n = re.subn(r"(?m)^(\s*)&END DFT", _momtxt + r"\n\1&END DFT",
                           tpl, count=1)
        if _n:
            tpl = _new
            _note("--type vib：模板的 `INTENSITIES T` 需要偶极矩，已自动补上 "
                  "`&DFT/&PRINT/&MOMENTS`{}。"
                  "**不补的话真机跑会直接 Abort**："
                  "`Trying to access result ([DIPOLE]) which was never stored`"
                  "（输入语法合法，官方解析器查不出来）。"
                  "要红外强度就别删它；不想要强度可把模板里的 INTENSITIES 改成 F。"
                  .format("（含 `PERIODIC FALSE`，因为 `--periodic none`）"
                          if args.periodic == "none" else ""))
        else:
            _note("⚠️ 想在频率计算里出红外强度（模板 `INTENSITIES T`），但**没能在 "
                  "`&DFT` 段里找到 `&END DFT` 来插入 `&MOMENTS`** —— "
                  "请手动补 `&DFT/&PRINT/&MOMENTS`，否则真机会 Abort。")
    if args.type == "vib":
        _note("⚠️ 频率分析**必须在已充分弛豫的结构上做**：几何没优化完就跑，"
              "Hessian 会被残余梯度污染，频率（尤其低频/虚频）完全不可信。"
              "先跑 `--type geo_opt` 到收敛，再用它最后一帧做 vib。")

    # ---- 🔴 非周期体系：必须让分子居于单胞中心（WAVELET 求解器的硬前提）----
    # 官方 CP2K 教程（T24 §3.4「非周期性体系的计算」）逐字：
    #   「如果设置为 WAVELET，不需要设置非常大的单胞，**但分子必须处于单胞的中心**，
    #     确保单胞的边界处电子密度为 0。可以使用 TOPOLOGY 参数来强制将分子置于单胞的中心。」
    # 违反它的后果是**静默的物理错误**（2026-10 真机实测，H₂O / CUTOFF 300 / 12 Å / 16 核）：
    #     WAVELET + 分子在原点角上 ⇒ E = −29.225 Ha，|ΣF| = **24.72 a.u.**（孤立体系必须为 0！）
    #     WAVELET + 分子居中       ⇒ E = −17.120 Ha，|ΣF| = 0.0005 a.u.  ✅ 与 ANALYTIC/MT 一致
    # 差 12 Ha、力全错，**CP2K 不报任何错、SCF 照常"收敛"** —— 唯一症状就是 ΣF≠0。
    # 顺带：居中后**更快**（70 s vs 109 s），因为之前求解器在跟跨界密度较劲。
    if args.periodic == "none" and "CENTER_COORDINATES" not in tpl:
        _top = ["    &TOPOLOGY",
                "      &CENTER_COORDINATES",
                "      &END CENTER_COORDINATES",
                "    &END TOPOLOGY"]
        # ⚠️ 锚点必须用**模板里真实存在**的东西。第一版锚在 `&COORD` 上 —— 但模板用的是
        # 占位符 `__STRUCTURE_BLOCK__`，`&COORD` 是**后面才插进去的**，所以那时匹配不到，
        # 注入静默失败（只在 note 里留了句"没能插入"，卡片本身照旧错）。
        # 改用 `&END CELL`（模板第 53 行，一定在），插在它后面、仍在 `&SUBSYS` 内。
        _new, _n = re.subn(r"(?m)^(\s*)&END CELL[ \t]*$",
                           lambda m: m.group(0) + "\n" + "\n".join(_top),
                           tpl, count=1)
        if _n:
            tpl = _new
            _note("--periodic none：已自动加入 `&SUBSYS/&TOPOLOGY/&CENTER_COORDINATES`，"
                  "把分子平移到单胞中心。**这是 WAVELET 求解器的硬前提**（官方 T24 §3.4："
                  "「分子必须处于单胞的中心，确保单胞的边界处电子密度为 0」）；"
                  "**违反它不会报错，但结果是错的**：实测偏心时总能量差 12 Ha、"
                  "原子力之和 ΣF 达到 24.7 a.u.（孤立体系必须为 0）。"
                  "若你的坐标本来就在中心，这两行也无害。")
        else:
            _note("⚠️ `--periodic none` 但**没能在 `&SUBSYS` 里找到 `&END CELL` 来插入 "
                  "`&TOPOLOGY/&CENTER_COORDINATES`** —— 请手工确认分子居于单胞中心，"
                  "否则 WAVELET 求解器会给出**静默错误**的结果（实测能量差 12 Ha）。")

    # ---- &VIBRATIONAL_ANALYSIS 的 FULLY_PERIODIC 要跟着体系周期性走 ----
    # 模板写死 `FULLY_PERIODIC T`，对**周期体系**是对的（整体转动无意义，
    # 别让 CP2K 去"清除转动"）；但对**孤立分子**是错的：
    #   官方 `FULLY_PERIODIC` 描述 = "Avoids to clean rotations from the Hessian matrix."（默认 F）
    #   ⇒ `F`（默认）消掉 3 平动 + 3 转动 ⇒ 打印 3N−6 个真振动
    #   ⇒ `T` 只消 3 平动、**保留 3 个转动** ⇒ 打印 3N−3 个（多出 3 个转动模式）
    # 实测（H₂O，N=3）：F → 3 个；T → 6 个；两版都先打印一行 3N=9 个
    # "Cartesian Low frequencies"（那行是消之前的 Hessian 本征值）。
    if args.type == "vib" and args.periodic == "none":
        _new, _n = re.subn(r"(?m)^(\s*)FULLY_PERIODIC\s+T\s*$",
                           r"\g<1>FULLY_PERIODIC F", tpl, count=1)
        if _n:
            tpl = _new
            _note("--type vib + `--periodic none`（孤立分子）：已把 `FULLY_PERIODIC T` "
                  "改为 **`F`** —— 分子体系要消掉 3 平动 + 3 转动，打印 **3N−6** 个真振动；"
                  "留着 `T` 会多出 3 个转动模式（变成 3N−3）。"
                  "周期体系（slab/块体）保持 `T` 是对的：整体转动无意义。")
    # ---- Wannier / TRAVIS 提示（TRAVIS 的两个硬前提最容易踩）----
    if any(p.lower() == "wannier" for p in (args.properties or [])):
        _note("--properties wannier：已发射 `IONS+CENTERS` + `FILENAME wannier.xyz` "
              "+ `&EACH {}`（IONS+CENTERS 官方默认是 F，不开它 Wannier 中心不与"
              "原子核写在同一个文件里，TRAVIS 要的 `X` 行就拿不到）。"
              "TRAVIS 两个硬前提：① **它读不了 cp2k-pos-1.xyz**，必须用它自己那份"
              "含 `X` 的 xyz；② 交互式运行时**晶胞长度单位是 pm**"
              "（20 Å 的盒子要输 2000，不是 20）。"
              .format("MD 1" if args.type in _MD_TYPES else "QS_SCF 10"))

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

    # 算一次混合块；下面还要用它检测"开关没有出口"的静默失效。
    _mixing_txt = mixing_block(args.mixing_method, args.mixing_alpha,
                               args.mixing_nbroyden, args.mixing_beta)
    # ---- "开关算出了内容、模板里却没有出口" 的静默失效自检 ----
    # cell_opt.inp 模板里既没有 __MIXING_BLOCK__ 也没有 __DIAGONALIZATION_BLOCK__，
    # 于是 `--mixing-*` / `--diagonalization-*` 在 --type cell_opt 下**静默消失**
    # （实测：geo_opt 同参数有 &MIXING PULAY / ALGORITHM DAVIDSON，cell_opt 0 处）。
    # 这里只**提示**、不改模板：往模板里加 token 会在生成物里多出空行，
    # 破坏"未给开关时逐字节不变"这条向后兼容要求。
    if args.type == "cell_opt":
        _mix_given = any(_flag_given(f) for f in (
            "--mixing-method", "--mixing-alpha", "--mixing-beta",
            "--mixing-nbroyden"))
        if "__MIXING_BLOCK__" not in tpl and _mixing_txt and _mix_given:
            _note("--type cell_opt 的模板没有 &MIXING 段 ⇒ --mixing-method/"
                  "--mixing-alpha/--mixing-beta/--mixing-nbroyden 对本输入**不生效**。"
                  "cell_opt 默认不发 &MIXING（走 CP2K 默认混合）；要显式控制请手工把 "
                  "&MIXING 加进 &SCF，或改用 --type geo_opt/static 的写法。")
        if "__DIAGONALIZATION_BLOCK__" not in tpl \
                and (_flag_given("--diagonalization-algorithm")
                     or _flag_given("--diagonalization-eps-adapt")):
            _note("--type cell_opt 的模板没有 &DIAGONALIZATION 段 ⇒ "
                  "--diagonalization-algorithm / --diagonalization-eps-adapt 对本输入"
                  "**不生效**（该模板只发 &OT 或什么都不发，CP2K 用自己的默认 SCF 设置）。")

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
        "__QS_BLOCK__": qs_block(args.multiplicity, args.gapw, wf_extrap),
        "__DIAGONALIZATION_BLOCK__": diag_block,
        "__XC_BLOCK__": xc_block(args.functional),
        "__VDW_BLOCK__": vdw_block() if args.dispersion else "",
        "__POISSON_BLOCK__": poisson_block(args.periodic),
        # 与 __POISSON_BLOCK__ **成对**出现：只设 &POISSON/PERIODIC 管不到 pair list，
        # 见 cell_periodic_line() 的说明。
        "__CELL_PERIODIC__": cell_periodic_line(args.periodic),
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
        # NEB &BAND/&CONVERGENCE_CONTROL 的两条判据。默认与修正前**逐字节一致**
        # （0.0006 / 0.0003，即 neb.inp 模板里原来的硬编码值）：模板硬编码的真正
        # 缺陷是"改不了"，不是"值不对"。CP2K 官方默认 MAX_FORCE 4.5E-4、
        # RMS_FORCE 3.0E-4；本 skill 刻意保留 0.0006 与 geo_opt.inp 的
        # MAX_FORCE 6.0E-4 同档，方便"结构优化 / 过渡态 / 频率"三件套互比
        # （三件套共用 FORCE_EVAL 与同一把尺子才有可比性）。要官方值就传
        # --neb-max-force 4.5E-4。
        "__NEB_MAX_FORCE__": (_fmt_num(args.neb_max_force)
                              if args.neb_max_force is not None else "0.0006"),
        "__NEB_RMS_FORCE__": (_fmt_num(args.neb_rms_force)
                              if args.neb_rms_force is not None else "0.0003"),
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
        "__BASIS_FILE__": basis_library_files(bases),
        "__MIXING_BLOCK__": _mixing_txt,
        "__OT_BLOCK__": ot_block,
        "__PROPERTIES_BLOCK__": "",  # retired placeholder (no template uses it)
        "__DFT_PRINT_BLOCK__": dft_print_block(
            props_under_dftprint, expand_ranges(args.ldos_list),
            print_style=args.print_style, cube_stride=args.cube_stride,
            pdos_nlumo=args.pdos_nlumo, pdos_nhomo=args.pdos_nhomo),
        "__FE_PRINT_BLOCK__": fe_print_block(props_under_feprint),
        "__LOCALIZE_BLOCK__": localize_block(props_under_localize,
                                             md=args.type in _MD_TYPES),
        # NVE = 微正则系综（N、V、E 恒定）：官方 ENSEMBLE 项原文就是
        # "NVE: constant energy (microcanonical)"，而 &THERMOSTAT/TYPE 的官方
        # 说明是"用于**恒温系综**的热浴" ⇒ NVE 下热浴**不生效**。模板里
        # `ENSEMBLE __ENSEMBLE__` 与 `__THERMOSTAT_BLOCK__` 是两行独立的 token，
        # 一起发就会得到"看起来配了热浴、实际完全不控温"的假象 —— 与
        # `KEEP_SYMMETRY` 缺 `&CELL SYMMETRY`、`--ot-minimizer diis` 不出 `&OT`
        # 属同一族"静默无效"缺陷。NVE 下直接不发该段（提示见 main 里的 _note）。
        "__THERMOSTAT_BLOCK__": (
            "" if args.ensemble == "nve" else thermostat_block(
                args.thermostat or "csvr", args.timecon, args.timecon_unit,
                args.nose_length, args.nose_yoshida, args.nose_mts)),
        "__ENSEMBLE__": ensemble_map.get(args.ensemble, "NVT"),
        "__STEPS__": str(args.steps if args.steps is not None else
                         (200000 if args.type == "metadyn" else 500000)),
        # TEMPERATURE 的**每模板原值**：aimd_md 600 K、metadyn 450 K。
        # 不传 --temperature 时严格沿用原值（**零行为变化**）；传了就覆盖。
        # 注意这两个都不是官方默认（官方 `MOTION/MD/TEMPERATURE` 默认 300 K）。
        "__TEMPERATURE__": str(args.temperature if args.temperature is not None
                               else (450.0 if args.type == "metadyn" else 600.0)),
        "__BAROSTAT_BLOCK__": barostat_block(args.ensemble == "npt"),
        "__RESTART_BLOCK__": restart_block(args.restart_freq) if args.restart_freq > 0 else "",
        # CP2K 的 WALLTIME 让作业在被批处理系统杀掉前**干净收尾**并留下可用的
        # 重启文件（H 层 T09 P9 原文："for a clean job ending and restart"）。
        # 不给就默认空行 —— 但生产作业应当给，故帮助文本里明确建议。
        "__WALLTIME__": ("    WALLTIME {}".format(int(args.walltime))
                         if args.walltime else ""),
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
            elif args.coord_include:
                # 讲师主推的坐标写法：坐标本体放在外挂文件里，输入卡只写
                # `@INCLUDE 'coord.inc'`。CP2K 前处理器在 &COORD 里照样展开它
                # （H 层 T09 P7–P23 的官方前处理语法）。
                # 注意：@INCLUDE 的目标必须是**去掉 xyz 前两行**的纯坐标行。
                structure = ("  &COORD\n"
                             "    @INCLUDE '{}'\n"
                             "  &END COORD".format(args.coord_include))
            else:
                coord = "# TODO: fill &COORD with 'Element x y z' per line"
            if not args.coord_include:
                structure = "  &COORD\n{}\n  &END COORD".format(coord)
        repl["__STRUCTURE_BLOCK__"] = structure

    out = tpl
    for k, v in repl.items():
        out = out.replace(k, v)
    # 空令牌（如未给 --walltime / --restart-freq）会在原位置留下一行空行；
    # 相邻几个可选块都不发时就会堆出连续空行。CP2K 输入里空行无意义，
    # 折叠成一行让生成物干净、便于人读与 diff。
    out = re.sub(r"\n{3,}", "\n\n", out)
    try:
        # 显式 UTF-8：与模板/仓库编码一致；用 locale 编码写会在遇到
        # GBK 无法表示的字符时抛 UnicodeEncodeError。
        open(args.output, "w", encoding="utf-8").write(out)
    except FileNotFoundError:
        # 健壮性基线：输出目录不存在 → 友好中文提示 + exit 1，不抛 traceback
        _dir = os.path.dirname(os.path.abspath(args.output))
        print(f"\n[ERROR] 输出目录不存在: {_dir}", file=sys.stderr)
        print(f'  请先创建目录：mkdir -p "{_dir}"', file=sys.stderr)
        sys.exit(1)
    except IsADirectoryError:
        print(f"\n[ERROR] 输出路径是目录，不是文件: {args.output}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"\n[ERROR] 无权限写入: {args.output}", file=sys.stderr)
        sys.exit(1)
    if getattr(args, "json", False):
        import json
        print(json.dumps({
            "ok": True,
            "output": args.output,
            "type": args.type,
            "project": args.project,
            "kinds": kind_names,
            "bytes": len(out),
        }, ensure_ascii=False, indent=2))
    else:
        print(f"written: {args.output}")


if __name__ == "__main__":
    main()
