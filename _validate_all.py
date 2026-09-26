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
import glob
import os
import subprocess
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


def _die_missing_deps(missing, detail):
    """友好报错并退出，不打印 traceback。exit 3 = 环境依赖缺失。"""
    sys.stderr.write("\n".join([
        "", "=" * 70,
        f"缺少依赖：{missing}", "",
        "本脚本是 skill 的「权威校验 harness」，属于开发依赖，普通用户无需运行。",
        "",
        "安装方式：", "",
        "  pip install -r requirements-dev.txt",
        "",
        detail,
        "=" * 70, "",
    ]))
    sys.exit(3)


# --- tooling shims: must run BEFORE importing cp2k_input_tools ---
try:
    import numpy as np
except ImportError as _exc:
    _die_missing_deps(
        getattr(_exc, "name", "numpy"),
        "numpy 是校验脚本本身以及 pint 的底层依赖。",
    )

if not hasattr(np, "cumproduct"):
    np.cumproduct = np.cumprod  # pint 0.23+ removed numpy.cumproduct

try:
    import cp2k_input_tools.parser as P
    from cp2k_input_tools.parser import CP2KInputParser
except ImportError as _exc:
    _die_missing_deps(
        getattr(_exc, "name", "cp2k-input-tools"),
        "cp2k-input-tools 自带官方 CP2K 输入参考手册（cp2k_input.xml），\n"
        "是判定输入语法是否合法的唯一权威来源。\n"
        "若上面的包名指向 pint 或 lxml，请一并补齐：\n"
        "  pip install cp2k-input-tools pint lxml",
    )

try:
    P.UREG.define("fs = femtosecond")  # CP2K 'fs' = femtosecond, not femtosiemens
except Exception:
    try:
        P.UREG._units.pop("fs", None)
        P.UREG.define("fs = femtosecond")
    except Exception:
        pass

# 同一类 tooling 缺陷的又一例：关键字名里的 `+`（`IONS+CENTERS`）。
#
# `IONS+CENTERS` 是**官方 XML 里唯一含 `+` 的关键字名**（`<NAME type="default">IONS+CENTERS</NAME>`
# 在 XML 中出现 19 次、同名，全在 Wannier 打印段 `&WANNIER_CENTERS` 下，官方默认 `F`）。
# 而 cp2k-input-tools 0.9.1 的关键字正则写作 `(?P<name>[\w\-_]+)` —— **字符类里没有 `+`**，
# 于是解析到这一行时在 `+` 处截断、把 `IONS` 当成关键字名，报：
#     InvalidNameError: invalid keyword 'IONS' specified and no default keyword for this section
# **这是假 error，输入本身完全合法。**
#
# 为什么以前没暴露：`_validate_all.py` 的用例里**没有 wannier 用例**，而
# `gen_inp.py --properties wannier` 正是要发射 `IONS+CENTERS`（不开它 Wannier 中心
# 就不与原子核写进同一个文件，TRAVIS 要的 `X` 行拿不到）。⇒ 谁加 wannier 用例谁撞。
# 这里把字符类补上 `+`（只放宽一个字符，其余原样；对不含 `+` 的名字行为不变）。
try:
    import re as _re
    P._KEYWORD_MATCH = _re.compile(r"(?P<name>[\w\-_+]+)\s*(?P<value>.*)")
except Exception:
    pass

# 同一类 tooling 缺陷的第二例：cp2k-input-tools 0.9.1 的 pint_units.txt 把
# `wavenumber_t` **注释掉了**（`# wavenumber_t =` 后无定义），于是官方 parser 会报
# `'wavenumber_t' is not defined in the unit registry`。
#
# 但 `[wavenumber_t]` 是**合法的 CP2K 时间单位**（G 层
# references/official/01_global_and_units.md 列出；真实生产 .out 回显
# `Nose-Hoover-Chain time constant [  fs] 33.36` 佐证 `[wavenumber_t] 1000` = 33.36 fs）。
# 不补这一条，**新生成的 `TIMECON [wavenumber_t] 1000`（生产卡写法）就无法被
# 官方 parser 校验**，等于把最该校验的写法排除在外。
#
# 语义：值取波数（cm^-1），CP2K 换算成该振子的周期 t[fs] = 33356.40952 / ν̃[cm^-1]。
# 这里只让单位**可被识别**（量纲 1/长度），不改变 pint 的换算行为。
try:
    P.UREG.define("wavenumber_t = 1 / centimeter")
except Exception:
    try:
        P.UREG._units.pop("wavenumber_t", None)
        P.UREG.define("wavenumber_t = 1 / centimeter")
    except Exception:
        pass

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
    # 必须显式 UTF-8：子进程（gen_inp.py）经 _console 统一输出 UTF-8，
    # 若按 locale(GBK) 解码，遇到中文报错会让内部读取线程抛
    # UnicodeDecodeError，r.stderr 变成 None，随后 .strip() 抛 AttributeError
    # —— 生成失败的诊断信息反而把 harness 自己搞崩。
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(f"  [GEN FAILED] {out}: {(r.stderr or '').strip()}")
        return False
    return True


def parse(path):
    """Parse with the official CP2KInputParser (validates vs cp2k_input.xml).

    Returns ``(errors, warnings, notes)``.

    ``notes`` holds the known cp2k-input-tools tooling limitation around CP2K's
    time unit '[fs]' (pint mis-reads it as femtosiemens). It is recorded for
    transparency but is **not** a real input error and **not** a warning — so it
    neither fails the run nor inflates the warning count.
    """
    parser = CP2KInputParser()
    notes = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            list(parser.parse(fh))  # force generator so all errors surface
        errs = getattr(parser, "errors", []) or []
        warns = getattr(parser, "warnings", []) or []
    except Exception as e:
        msg = str(e)
        if "femtosiemens" in msg or "femtosecond" in msg:
            return [], [], ["NOTE(unit-tooling): pint mis-reads CP2K '[fs]' as "
                            "femtosiemens; not an input error."]
        return [msg], [], []
    real_errs = []
    for e in errs:
        s = e.msg if hasattr(e, "msg") else str(e)
        if "femtosiemens" in s or "femtosecond" in s:
            notes.append("NOTE(unit-tooling): " + s)
        else:
            real_errs.append(s)
    return real_errs, warns, notes


def main():
    # 🔴 `--help` 必须 **exit 0**（AGENTS.md §6.3 的健壮性基线）。
    # 本 harness 没有别的选项，所以早先**干脆没写参数解析** —— 于是 `--help`
    # 被当成"没有参数"、直接跑起全套校验（几十秒），最后按校验结果以**非 0** 退出。
    # 后果不是"少个帮助文档"：`_validate_gbk.py` 会把这个入口也拿来跑一遍，
    # 于是它稳定判红（实测：`[FAIL] _validate_all.py --help  exit=1 期望 [0]`）。
    # 教训与 `references/pdf_text/extract_pdf.py` 那次一样 —— **没有选项不等于可以忽略 `--help``**。
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__ or "用法：python _validate_all.py   （无选项，跑全套输入校验）")
        return 0
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
        # --- Wannier：**唯一行使 `+` 关键字 shim 的用例，别删** ---
        # `--properties wannier` 会发射 `IONS+CENTERS`（官方 XML 里唯一含 `+` 的关键字名）。
        # 没有这个用例，文件顶部的 `_KEYWORD_MATCH` 补丁就是**死代码**，
        # 一旦 cp2k-input-tools 升级或补丁被误删，也没人会发现 —— 直到某天有人
        # 真去算 Wannier 中心，才收到一个莫名其妙的假 `InvalidNameError`。
        ("wannier_aimd", [
            "--type", "aimd_md", "--project", "t28", "--elem", "Cu", "O", "H",
            "--basis", "DZVP-MOLOPT-SR-GTH", "DZVP-MOLOPT-SR-GTH",
            "DZVP-MOLOPT-SR-GTH",
            "--potential", "GTH-PBE", "GTH-PBE-q6", "GTH-PBE-q1",
            "--periodic", "xyz", "--properties", "wannier"]),
    ]

    total_err = 0
    total_warn = 0
    total_note = 0
    gen_failed = []

    for name, args in cases:
        out = os.path.join(HERE, "_chk_" + name + ".inp")
        if not gen(out, *args):
            # 生成失败**必须**计入结果。此前这里只是 `continue`，
            # 于是 summary 照样声称「28 cases 全过」且退出码恒为 0 ——
            # 假绿会让 CI 永远拦不住回归（v2.7.0 的 aimd_md 崩溃就是这样漏掉的）。
            gen_failed.append(name)
            print(f"[GEN-FAIL] {name}: gen_inp.py 未能生成输入")
            continue
        errs, warns, notes = parse(out)
        status = "ERROR" if errs else ("WARN" if warns else "OK")
        extra = f", {len(notes)} note" if notes else ""
        print(f"[{status}] {name}: {len(errs)} err, {len(warns)} warn{extra}")
        for e in errs:
            print(f"    ERR: {e}")
        for w in warns:
            print(f"    WARN: {w}")
        for n in notes:
            print(f"    {n}")
        total_err += len(errs)
        total_warn += len(warns)
        total_note += len(notes)

    checked = len(cases) - len(gen_failed)

    # ---- 另把**仓库里现有的 .inp**（examples/ + verify_out/）也过一遍官方 parser ----
    #
    # 为什么必须做：`examples/*.inp` 对外宣称"已校验的输入"，但它们此前**不在**
    # 本 harness 的覆盖里（本 harness 只解析自己生成的 `_chk_*.inp`）。于是
    # `examples/05_metadyn_fes/metadyn.inp` 把 `K` / `DIRECTION` 直接写在 `&WALL`
    # 下（官方 schema 里它们属于 `&WALL/&QUADRATIC`）**长期没人发现** ——
    # 是给 `_official_validate.py` 加 unit-tooling 分类时才顺带暴露出来的。
    repo_inputs = sorted(glob.glob(os.path.join(HERE, "examples", "*", "*.inp"))
                         + glob.glob(os.path.join(HERE, "verify_out", "*.inp")))
    if repo_inputs:
        print()
        print("#" * 70)
        print("# 3. 仓库现有 .inp（examples/ + verify_out/）过官方 parser")
        print("#" * 70)
        # 复用 `_official_validate.validate_file`，**不另写一份**错误分类 ——
        # 两份逻辑迟早漂移。它已处理两类已知 tooling 限制（`fs`→femtosiemens、
        # `internal_cp2k` 关键字上的显式单位覆盖），并且对后者做了严格前置判定
        # （单位名 pint 认得 + 值全是数字），真错误照常判死。
        try:
            import importlib.util as _ilu
            _spec = _ilu.spec_from_file_location(
                "_ov", os.path.join(HERE, "_official_validate.py"))
            _ov = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_ov)
            _validate_file = _ov.validate_file
        except Exception as _exc:            # pragma: no cover
            _validate_file = None
            print("# [SKIP] 无法导入 _official_validate.py：{}".format(_exc))
        for path in repo_inputs:
            rel = os.path.relpath(path, HERE)
            if _validate_file is None:
                break
            msgs = _validate_file(path)
            real = [m for m in msgs if not m.startswith("NOTE")]
            notes = [m for m in msgs if m.startswith("NOTE")]
            if real:
                total_err += len(real)
                print(f"[ERROR] {rel}: {len(real)} err")
                for e in real:
                    print(f"    ERR: {e}")
            else:
                total_note += len(notes)
                extra = f", {len(notes)} note" if notes else ""
                print(f"[OK]    {rel}: 0 err{extra}")
            checked += 1

    # ---- 仓库现有 .inp 还要过一遍**我们自己的** validate_inp.py ----
    #
    # 官方 parser 只查**语法/schema**，查不出"语义上配错了"的东西。实测它放过了
    # 一批真缺陷（都是本轮存疑查证顺带发现的）：
    #   * `BASIS_SET_FILE_NAME BASIS_SET` + 用了 MOLOPT 族基组 —— MOLOPT 住在
    #     `BASIS_MOLOPT`，跑起来直接 "basis set not found"（8 个文件中招）
    #   * `&POISSON PERIODIC` 与 `&CELL PERIODIC` 不一致（5 个文件中招）
    # 所以这里把 `validate_inp.py` 也跑一遍，**它的 warning 也算失败** ——
    # 否则"示例输入是正确的"这句话就没人守。
    if repo_inputs:
        print()
        print("#" * 70)
        print("# 4. 仓库现有 .inp 过 validate_inp.py（语义检查，warning 也算失败）")
        print("#" * 70)
        VI = os.path.join(HERE, "scripts", "validate_inp.py")
        for path in repo_inputs:
            rel = os.path.relpath(path, HERE)
            r = subprocess.run([PY, VI, path], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            warns = [l for l in (r.stdout or "").splitlines() if "[warn]" in l]
            errs = [l for l in (r.stdout or "").splitlines() if "[ERROR]" in l]
            if errs or warns:
                total_err += len(errs)
                total_warn += len(warns)
                print(f"[ISSUE] {rel}: {len(errs)} err, {len(warns)} warn")
                for l in errs + warns:
                    print("    " + l.strip()[:160])
            else:
                print(f"[OK]    {rel}: 0 err, 0 warn")

    print()
    print("#" * 70)
    print(f"# SUMMARY: {total_err} errors, {total_warn} warnings"
          + (f", {total_note} note(s)" if total_note else "")
          + f" across {checked}/{len(cases) + len(repo_inputs)} cases"
          + f" ({len(cases)} 生成 + {len(repo_inputs)} 仓库现有)")
    if gen_failed:
        print(f"# 生成失败 {len(gen_failed)} 个（**未**计入「解析通过」）："
              + ", ".join(gen_failed))
    print("#" * 70)

    # 退出码：生成失败 / error / warning 任一项都算失败，CI 才拦得住
    return 1 if (gen_failed or total_err or total_warn) else 0


if __name__ == "__main__":
    sys.exit(main())
