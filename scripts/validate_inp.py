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
import glob
import os
import re
import shutil
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

# ---------------------------------------------------------------------------
# CP2K section-name whitelist (used to flag likely typos as warnings).
#
# 这里是**手工维护的常用子集**，只用来在官方全量表缺失时兜底、以及给
# sorted_suggestion() 提供"近邻"。
#
# 真正的判定用官方全量表 `_cp2k_sections.SECTIONS`（1342 个 SECTION，由
# `_gen_cp2k_sections.py` 从 cp2k-input-tools 自带的官方 cp2k_input.xml 生成）。
# 为什么必须用全量表：手工子集只有 156 个、覆盖率 12%，像 `&MULLIKEN`
# （官方 `&DFT/&PRINT` 下的布局分析段）这种**完全合法**的段会被误报成
# "possible typo" —— 这是拿 H 层 cases/ 里的**真实生产输入卡**去跑才暴露的。
# ---------------------------------------------------------------------------
try:                                  # 纯数据模块；缺了就退回手工子集
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _cp2k_sections import SECTIONS as _OFFICIAL_SECTIONS
except Exception:                     # pragma: no cover
    _OFFICIAL_SECTIONS = frozenset()

KNOWN_SECTIONS = {
    # top level
    "GLOBAL", "FORCE_EVAL", "MOTION", "EXT_RESTART", "MULTIPLE_FORCE_EVALS",
    "OPTIMIZE_INPUT", "PRINT", "TEST", "VIBRATIONAL_ANALYSIS",
    # &GLOBAL/TIMINGS 是官方段（G 层 official/20_input_reference_tree.md 有），
    # 早先漏收会误报 "possible typo"。
    "TIMINGS",
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
    # CONSTRAINT 的官方子段（references/official/20_input_reference_tree.md：
    # &MOTION/CONSTRAINT 共 10 个子段）。G3X3/G4X6/HBONDS 由 gen_inp.py 的
    # --constraint-g3x3 / --constraint-hbonds 直接发射，缺了会误报 "possible typo"。
    "COLLECTIVE", "COLVAR_RESTART", "CONSTRAINT_INFO", "FIX_ATOM_RESTART",
    "G3X3", "G4X6", "HBONDS", "LAGRANGE_MULTIPLIERS", "VIRTUAL_SITE",
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

# 判定用集合 = 官方全量 ∪ 手工子集（手工那份含本 skill 自造的别名，别丢）
ALL_SECTIONS = frozenset(KNOWN_SECTIONS) | frozenset(_OFFICIAL_SECTIONS)

VALID_RUN_TYPES = {
    "ENERGY", "ENERGY_FORCE", "WAVEFUNCTION_OPT", "GEO_OPT", "CELL_OPT",
    "MD", "MC", "SHELL_OPT", "BAND", "NEB", "LINE_SEARCH", "TS",
    "TRANSITION_STATE", "VIBRATIONAL_ANALYSIS", "DEBUG", "MASTER",
    "BSSE", "ALMO", "EIP",
}

# METHOD 的合法写法。"QS" 是 QUICKSTEP 的官方缩写（H 层 T07 P8 原文写法），
# 早先漏收会把教材风格的正确输入报成 "not a known value"。
VALID_METHODS = {"QUICKSTEP", "QS", "FIST", "MIXED", "QM", "QMMM", "SE",
                 "DRIVER", "LIBXSMM"}

VALID_OPTIMIZERS = {
    "BFGS", "CG", "LBFGS", "DIIS", "BROYDEN", "NEWTON", "SAFE", "CG_INLINE",
}

REQUIRED_TOP = {"GLOBAL", "FORCE_EVAL"}
# RUN_TYPE values that imply MOTION is needed
MOTION_RUN_TYPES = {"GEO_OPT", "CELL_OPT", "MD", "MC", "BAND", "NEB",
                    "SHELL_OPT", "LINE_SEARCH", "TS", "TRANSITION_STATE",
                    "VIBRATIONAL_ANALYSIS"}

# ---------------------------------------------------------------------------
# 高风险「错名 → 正确写法」映射表（**已知会把用户带沟里的**错名，不是全量白名单）
#
# 为什么只做这一小张表：`validate_inp.py` 的定位是**轻量 linter**。做完整的
# 关键字白名单必然误报（CP2K 有上千个关键字，且大量关键字在多个段里重名、
# 还有别名），一旦开始误报，用户就会习惯性忽略它 —— 那比不查更糟。
# 这里只收「实测会静默通过、而 CP2K 又不认识/语义完全不同」的错名：
# 它们要么让作业跑不起来，要么让用户以为自己开了某个功能。
#
# 每条的判据都来自官方 `cp2k_input.xml`（`_kw_probe.py --find <名>`）：
#   SURFACE_DIPOLE_DIRECTION → 0 命中；真名 `SURF_DIP_DIR`
#   SMEARING                → 0 命中；真名 `SMEAR`（&SCF 下）
#   FIXED_Z                 → 0 命中；晶胞方向约束是 `&CELL_OPT CONSTRAINT Z`
#   COUPLING_REGION         → 0 命中；热浴区域是 `&THERMOSTAT REGION`
#   U_EFFECTIVE             → 0 命中；DFT+U 是 `U_MINUS_J`（&KIND/&DFT_PLUS_U）
#   INCREM                  → 0 命中（VASP 的写法）；CP2K 用 `TARGET_GROWTH`
# ---------------------------------------------------------------------------
KNOWN_BAD_KEYWORDS = {
    "SURFACE_DIPOLE_DIRECTION": (
        "&DFT 下写 `SURF_DIP_DIR Z`（偶极校正方向，默认 Z）",
        "官方 `SURFACE_DIPOLE_CORRECTION` 的别名是 SURFACE_DIPOLE / SURF_DIP，"
        "**方向关键字叫 SURF_DIP_DIR**；SURFACE_DIPOLE_DIRECTION 在官方 XML 里 "
        "**0 命中**（写了它 CP2K 会直接报 unknown keyword）"),
    "SMEARING": (
        "&SCF 下写 `SMEAR FERMI_DIRAC`（可选 `&SMEAR` 子段设 ELECTRONIC_TEMPERATURE）",
        "官方关键字是 `SMEAR`（&FORCE_EVAL/&DFT/&SCF）；SMEARING 0 命中。"
        "写 SMEARING 的作业会因 unknown keyword 起不来，而金属/窄带体系"
        "恰恰最需要它"),
    "FIXED_Z": (
        "想让晶胞的 z 方向不弛豫 → `&MOTION/&CELL_OPT CONSTRAINT Z`；"
        "想冻结原子 → `&MOTION/&CONSTRAINT/&FIXED_ATOMS LIST 1..54`",
        "FIXED_Z 0 命中。这两个概念经常被混：**CELL_OPT CONSTRAINT 管晶胞分量，"
        "FIXED_ATOMS 管原子**。二维材料保真空层要的是前者"),
    "COUPLING_REGION": (
        "&MOTION/&MD/&THERMOSTAT 下写 `REGION GLOBAL|MOLECULE|MASSIVE`",
        "COUPLING_REGION 0 命中；官方关键字是 `REGION`（取值与讲师口述的"
        "三元组完全一致）"),
    "U_EFFECTIVE": (
        "`&KIND/&DFT_PLUS_U U_MINUS_J [eV] <值>`（官方默认单位是 hartree）",
        "U_EFFECTIVE 0 命中；DFT+U 的有效 U 值关键字是 `U_MINUS_J`。"
        "注意单位：默认 hartree，按 eV 给的数必须写成 `U_MINUS_J [eV] 3.0`，"
        "否则 3.0 被当成 3 hartree ≈ 81.6 eV"),
    "INCREM": (
        "CP2K 没有 INCREM（那是 VASP 的写法）：约束用 "
        "`&MOTION/&CONSTRAINT/&COLLECTIVE TARGET_GROWTH <值>`（配合 &COLVAR）",
        "INCREM 在官方 XML 里 0 命中。VASP 的 `INCREM`（每步增加约束量）"
        "在 CP2K 里的对应物是 `&COLLECTIVE/TARGET_GROWTH`"),
}

SECTION_RE = re.compile(r"^\s*&(\w+|\$\{?\w+\}?)\s*(.*)$")
END_RE = re.compile(r"^\s*&END\s*(\w*)\s*$")

# CP2K 的**官方注释符是 `!`**（H 层 T08 P7 / T09 全篇）。
# 早先只 strip `#`，导致 `&END GLOBAL   ! 注释` 这种完全合法的写法被判
# "unknown section '&END'" + "unclosed section '&GLOBAL'"（实跑 3 个 error）。
# 这里同时接受 `!` 与 `#`（`#` 留给本 skill 早期笔记与外部脚本）。
_COMMENT_CHARS = "!#"


def strip_comment(line):
    """去掉 CP2K 行内注释。`!` 是官方注释符，`#` 一并接受。"""
    for i, ch in enumerate(line):
        if ch in _COMMENT_CHARS:
            return line[:i].rstrip()
    return line.rstrip()


# ---------------------------------------------------------------------------
# CP2K 前处理（preprocessor）感知层
#
# CP2K 输入支持一套 `@` 指令（H 层 T09 P7–P23 完整讲过）：
#   @SET VAR value          定义变量（**只能有 3 个 token**，多的都并入值）
#   ${VAR} / $VAR           引用变量，可出现在值、段名、&EACH 的键里
#   @INCLUDE 'file'         文本包含（可嵌套，可递归）
#   @IF ( ${VAR} == X ) … @ELIF … @ELSE … @ENDIF
#
# 早先的校验器不认识这些，会把**官方教材风格的正确输入**判废：
#   * @SET + @INCLUDE 风格 → 误报 "missing required top-level section &FORCE_EVAL"
#     （因为被包含的文件根本没读）
#   * &${RTYPE} 形式的动态段名 → 误报 "unknown section"
# 现在：@INCLUDE 递归展开、@SET 变量做文本替换、@IF/@ENDIF 只吃掉指令行
# （不求值条件，两个分支都照常做结构检查 —— 宁多查不漏查）。
# ---------------------------------------------------------------------------
AT_RE = re.compile(r"^\s*@(\w+)\b\s*(.*)$")
VAR_RE = re.compile(r"\$\{(\w+)\}|\$(\w+)")
_UNRESOLVED = "__CP2K_UNRESOLVED_VAR__"
# @IF/@ELIF 的比较式里可能有 @SET 变量，替换后再判断"真假"没有意义，故只记录。
_MAX_INCLUDE_DEPTH = 32


def _read_lines(path):
    """读 UTF-8 文本，**容忍并剥离 BOM**。

    用记事本 / PowerShell 5.1 的 `Set-Content -Encoding UTF8` 保存的 .inp 会带
    U+FEFF。CP2K **自己读不了带 BOM 的输入**（首行 `&GLOBAL` 变成 `\\ufeff&GLOBAL`），
    而校验器若也不剥 BOM，就会把 BOM 的锅算成"&END 没有对应段"，报一个和真因
    毫无关系的错。这里剥掉 BOM 让检查能正常进行，同时在 parse() 里**显式警告**
    用户另存为无 BOM。
    """
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        return fh.read().splitlines()


def _has_bom(path):
    try:
        with open(path, "rb") as fh:
            return fh.read(3) == b"\xef\xbb\xbf"
    except OSError:
        return False


# ---------------------------------------------------------------------------
# &FIXED_ATOMS 索引越界检查所需的两个小工具
# ---------------------------------------------------------------------------
def _is_atom_line(parts):
    """&COORD 里的一行原子？判据：第一列不是数字/关键字，后三列都是浮点数。

    `SCALED T` / `UNIT angstrom` / `COORD_FILE_NAME x.xyz` 这些关键字行都
    不足 4 列或第 2 列不是浮点，自然被排除。
    """
    if len(parts) < 4 or parts[0].startswith("&"):
        return False
    if parts[0].upper() in ("SCALED", "UNIT", "COORD_FILE_NAME",
                            "COORD_FILE_FORMAT"):
        return False
    try:
        float(parts[1]), float(parts[2]), float(parts[3])
    except ValueError:
        return False
    return True


def _looks_like_index_tokens(parts):
    """一行全是 FIXED_ATOMS 的索引写法（`1` / `139..170` / `1,2,3`）？

    真实卡片会把一个 LIST 折行写，也可能连写多个 LIST：
        LIST  1..54
        LIST  289..324
    两种都要收。
    """
    if not parts:
        return False
    for p in parts:
        t = p.strip().strip(",")
        if not t:
            continue
        body = t.replace("..", " ").split()
        if not body:
            return False
        for tok in body:
            if not tok.lstrip("+-").isdigit():
                return False
    return True


def expand_index_specs(tokens):
    """把 `['1..54', '289..324', '3']` 展开成 (索引集合, 非法 token 列表)。"""
    idxs = set()
    bad = []
    for raw in tokens:
        for tok in raw.replace(",", " ").split():
            if ".." in tok:
                lo_s, _, hi_s = tok.partition("..")
                try:
                    lo, hi = int(lo_s), int(hi_s)
                except ValueError:
                    bad.append(tok)
                    continue
                if lo > hi:
                    lo, hi = hi, lo
                idxs.update(range(lo, hi + 1))
            else:
                try:
                    idxs.add(int(tok))
                except ValueError:
                    bad.append(tok)
    return idxs, bad


def _fmt_ranges(values):
    """[1,2,3,7,9,10] -> '1..3, 7, 9..10'（把越界的那部分讲清楚）。"""
    vs = sorted(set(values))
    if not vs:
        return ""
    out = []
    start = prev = vs[0]
    for v in vs[1:]:
        if v == prev + 1:
            prev = v
            continue
        out.append(str(start) if start == prev else f"{start}..{prev}")
        start = prev = v
    out.append(str(start) if start == prev else f"{start}..{prev}")
    return ", ".join(out)


def expand(path, variables=None, seen=None, errors=None, warnings=None,
           label=None, depth=0, flags=None):
    """展开 `@SET` / `@INCLUDE` / `${VAR}`，返回 ``[(标签, 行文本, 行号)]``。

    * 标签在主文件里是 ``L12``，在 ``@INCLUDE`` 进来的文件里是
      ``common.inp:L5``，这样报错能定位到真正的来源文件。
    * ``@INCLUDE`` 循环引用用 ``seen``（绝对路径集合）拦住。
    * ``flags`` 是调用方传进来的 set，出现条件指令时加 ``"cond"``。
    """
    variables = {} if variables is None else variables
    seen = set() if seen is None else seen
    errors = [] if errors is None else errors
    warnings = [] if warnings is None else warnings
    flags = set() if flags is None else flags

    try:
        real = os.path.abspath(path)
    except OSError:
        real = path
    if real in seen:
        warnings.append(f"{label or path}: @INCLUDE 循环引用，已跳过 '{path}'")
        return []
    if depth > _MAX_INCLUDE_DEPTH:
        errors.append(f"{label or path}: @INCLUDE 嵌套超过 "
                      f"{_MAX_INCLUDE_DEPTH} 层，疑似循环引用")
        return []
    seen.add(real)

    try:
        raw = _read_lines(path)
    except FileNotFoundError:
        errors.append(f"找不到 @INCLUDE 的文件: {path}")
        return []
    except OSError as e:
        errors.append(f"无法读取 @INCLUDE 的文件 {path}: {e}")
        return []

    out = []
    for i, raw_line in enumerate(raw, 1):
        tag = f"L{i}" if label is None else f"{label}:L{i}"
        line = strip_comment(raw_line)

        ma = AT_RE.match(line)
        if ma:
            directive = ma.group(1).upper()
            rest = ma.group(2).strip()
            if directive == "SET":
                # @SET VAR value —— 变量名之后的**全部**内容都是值
                # （T09 P8 反例：`@SET MD_DT 1.5 ! comment` 会把注释并进值里）。
                parts = rest.split(None, 1)
                if len(parts) < 2:
                    warnings.append(f"{tag}: @SET 缺少变量名或值（应为 "
                                    f"'@SET VAR value'，且整行只有 3 个 token）")
                else:
                    variables[parts[0]] = parts[1].strip()
                continue
            if directive == "INCLUDE":
                inc = rest.strip().strip("'\"")
                if not inc:
                    errors.append(f"{tag}: @INCLUDE 后面没有文件名")
                    continue
                if not os.path.isabs(inc):
                    inc = os.path.join(os.path.dirname(os.path.abspath(path)), inc)
                out.extend(expand(inc, variables, seen, errors, warnings,
                                  label=os.path.basename(inc), depth=depth + 1,
                                  flags=flags))
                continue
            if directive in ("IF", "ELIF", "ELSE", "ENDIF"):
                # 条件块：不做真值求值，只把指令行吃掉，两个分支都照常检查。
                flags.add("cond")
                continue
            if directive in ("ERROR", "WARNING"):
                continue
            warnings.append(f"{tag}: 未知前处理指令 '@{directive}'（已跳过）")
            continue

        # 变量替换（值、段名、&EACH 的键里都可能出现）
        if "$" in line:
            def _sub(m):
                name = m.group(1) or m.group(2)
                return variables.get(name, _UNRESOLVED + name)
            line = VAR_RE.sub(_sub, line)

        out.append((tag, line, i))
    return out


def parse(path):
    """Return (errors, warnings, lines)."""
    errors = []
    warnings = []
    try:
        _read_lines(path)
    except FileNotFoundError:
        return [f"找不到文件: {path}（请检查路径；或用 --coord 让 gen_inp.py 直接写坐标）"], warnings, []
    except IsADirectoryError:
        return [f"给的是目录，不是 .inp 文件: {path}"], warnings, []
    except PermissionError:
        return [f"无权限读取: {path}"], warnings, []
    except OSError as e:
        return [f"无法读取文件: {e}"], warnings, []

    flags = set()
    if _has_bom(path):
        warnings.append("文件带 UTF-8 BOM（U+FEFF）。CP2K 解析首行会失败，"
                        "请另存为『UTF-8 无 BOM』（本校验已自动忽略 BOM 继续检查）")
    expanded = expand(path, errors=errors, warnings=warnings, flags=flags)
    raw = [ln for (_tag, ln, _n) in expanded]
    has_includes = any(":" in t for (t, _l, _n) in expanded)

    stack = []          # list of (section_name, 标签)
    seen_top = set()
    run_type = None
    method = None
    dyn_names = set()   # 含未解析 ${VAR} 的段名（不做白名单检查）
    basis_files = set()     # BASIS_SET_FILE_NAME 给过的库文件
    basis_values = []       # 主基组名
    aux_basis_values = []   # ADMM 辅助基组名（BASIS_SET AUX_FIT）
    has_subsys = False
    has_dft_or_mm = False
    kind_count = 0
    has_cell_or_coord = False
    in_subsys = False
    # --- &FIXED_ATOMS 越界检查的证据（结论在循环后统一判定）---
    cur_coord = None        # 正在统计的 &COORD 块：[1,1,...] 或 None
    coord_atom_counts = []  # 每个数到原子的 &COORD 块各有多少个原子
    cur_fixed = None        # 正在收集的 &FIXED_ATOMS：['139..170', ...] 或 None
    fixed_tag = None
    fixed_specs = []        # [(标签, [token,...]), ...]
    topology_tags = []      # &TOPOLOGY 出现处
    # 只有设了 COORD_FILE_NAME / CONN_FILE_NAME 的 &TOPOLOGY 才真的从外部读结构，
    # 也只有它才与内联 &COORD 互斥（见下方告警处的长注释）。
    topology_file_tags = []
    cur_topology_tag = None  # 当前正在读的 &TOPOLOGY 起始行
    # `&DFT/&POISSON PERIODIC` 与 `&SUBSYS/&CELL PERIODIC` 的一致性证据。
    # 官方 schema 对 &POISSON/PERIODIC 原话："this only applies to the electrostatics.
    # See the CELL section to specify the periodicity used for e.g. the pair lists.
    # Typically the settings should be the same." ⇒ 两者不一致要提醒。
    periodic = {"POISSON": None, "CELL": None}
    periodic_tag = {"POISSON": None, "CELL": None}
    # --- CELL_OPT / 应力 / 晶胞对称性 / MD 的证据（结论在循环后统一判定）---
    stress_tensor = None        # &FORCE_EVAL 顶层的 STRESS_TENSOR 值
    stress_tag = None
    cell_symmetry = None        # &SUBSYS/&CELL SYMMETRY 的值
    keep_symmetry = None        # &MOTION/&CELL_OPT KEEP_SYMMETRY 的值
    keep_symmetry_tag = None
    has_cell_opt = False
    cell_opt_tag = None
    ensemble = None             # &MOTION/&MD ENSEMBLE 的值
    ensemble_tag = None
    has_thermostat = False      # &MOTION/&MD/&THERMOSTAT 是否存在
    eps_scf = None              # &SCF EPS_SCF 的值（字符串）
    eps_scf_tag = None

    for tag, line, _lineno in expanded:
        i = tag
        if not line.strip():
            continue

        me = END_RE.match(line)
        if me:
            closed = me.group(1)
            if not stack:
                errors.append(f"{i}: &END {closed or ''} with no open section")
                continue
            opened, oline = stack.pop()
            if closed and closed.upper() != opened:
                errors.append(f"{i}: &END {closed} closes '&{opened}' "
                              f"(opened at {oline})")
            if opened == "COORD" and cur_coord is not None:
                if cur_coord:
                    coord_atom_counts.append(len(cur_coord))
                cur_coord = None
            if opened == "FIXED_ATOMS" and cur_fixed is not None:
                if cur_fixed:
                    fixed_specs.append((fixed_tag, list(cur_fixed)))
                cur_fixed = None
            if opened == "SUBSYS":
                in_subsys = False
                if not kind_count:
                    errors.append(f"{oline}: &SUBSYS has no &KIND section")
                if not has_cell_or_coord:
                    errors.append(f"{oline}: &SUBSYS has neither &CELL nor &COORD")
            if opened == "FORCE_EVAL":
                if not has_dft_or_mm:
                    errors.append(f"{oline}: &FORCE_EVAL missing &DFT/&MM/&MIXED")
                if not has_subsys:
                    errors.append(f"{oline}: &FORCE_EVAL missing &SUBSYS")
            continue

        m = SECTION_RE.match(line)
        if m:
            name = m.group(1).upper()
            if _UNRESOLVED in name:
                # &${RTYPE} 这种动态段名，@SET 没定义过 → 只记不判
                dyn_names.add(name)
            elif name not in ALL_SECTIONS:
                warnings.append(f"{i}: unknown section '&{name}' "
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
            if name == "COORD":
                cur_coord = []
            if name == "FIXED_ATOMS":
                cur_fixed = []
                fixed_tag = i
            if name == "TOPOLOGY":
                topology_tags.append(i)
            if name == "CELL_OPT" and parent == "MOTION":
                has_cell_opt = True
                if cell_opt_tag is None:
                    cell_opt_tag = i
            if name == "THERMOSTAT" and parent == "MD":
                has_thermostat = True
            # close handling for SUBSYS
            if parent == "SUBSYS" and name not in ("KIND", "CELL", "COORD",
                                                   "TOPOLOGY", "COLVAR", "DIPOLE",
                                                   "VELOCITY", "GB", "THERMOSTAT",
                                                   "PRINT", "CORE_COORD"):
                in_subsys = False
            stack.append((name, i))
            continue

        # ---- &COORD 原子行 / &FIXED_ATOMS LIST 的证据收集（结论在循环后判定）----
        kparts = line.strip().split()
        if cur_coord is not None and _is_atom_line(kparts):
            cur_coord.append(1)
        if cur_fixed is not None and kparts:
            if kparts[0].upper() == "LIST":
                cur_fixed.extend(kparts[1:])
            elif _looks_like_index_tokens(kparts):
                # LIST 折行 / 前一行 LIST 的续行
                cur_fixed.extend(kparts)

        # keyword line inside GLOBAL / FORCE_EVAL
        kw = line.strip().split()[0].upper() if line.strip() else ""
        if stack:
            top = stack[0][0]
            sec = stack[-1][0]
            # ---- 高风险错名（已知会静默通过、CP2K 却不认识的关键字）----
            # 判据与出处见 KNOWN_BAD_KEYWORDS 上方的说明。
            if kw in KNOWN_BAD_KEYWORDS:
                fix, why = KNOWN_BAD_KEYWORDS[kw]
                errors.append(
                    f"{i}: 关键字 '{kw}' 在 CP2K 官方输入参考里**不存在**"
                    f"（当前段 &{sec}）。{why}。正确写法：{fix}")
            if top == "GLOBAL" and sec == "GLOBAL":
                if kw == "RUN_TYPE":
                    val = line.strip().split(None, 1)[1].strip().upper() \
                        if len(line.strip().split()) > 1 else ""
                    run_type = val
                    if val and val not in VALID_RUN_TYPES:
                        warnings.append(f"{i}: RUN_TYPE '{val}' not a known value")
            if sec == "FORCE_EVAL" and kw == "METHOD":
                val = line.strip().split(None, 1)[1].strip().upper() \
                    if len(line.strip().split()) > 1 else ""
                method = val
                if val and val not in VALID_METHODS:
                    warnings.append(f"{i}: METHOD '{val}' not a known value")
            # 基组 ↔ 基组库文件配套检查的证据收集（结论在循环后统一判定）
            parts = line.strip().split()
            if sec == "DFT" and kw == "BASIS_SET_FILE_NAME":
                basis_files.update(p.upper() for p in parts[1:])
            elif sec == "DFT" and kw == "BASIS_SET" and len(parts) == 2:
                basis_values.append(parts[1].upper())
            elif sec == "KIND" and kw == "BASIS_SET":
                if len(parts) >= 3 and parts[1].upper() == "AUX_FIT":
                    aux_basis_values.append(parts[2].upper())
                elif len(parts) == 2:
                    basis_values.append(parts[1].upper())
            # &POISSON PERIODIC 与 &CELL PERIODIC 的一致性证据
            # （段的官方别名：POISSON / POISSON_SOLVER / PSOLVER）
            elif kw == "PERIODIC" and len(parts) >= 2:
                val = parts[1].upper()
                if sec in ("POISSON", "POISSON_SOLVER", "PSOLVER"):
                    periodic["POISSON"] = val
                    periodic_tag["POISSON"] = i
                elif sec == "CELL":
                    periodic["CELL"] = val
                    periodic_tag["CELL"] = i
            # ---- CELL_OPT / 应力 / 晶胞对称性 的证据 ----
            # STRESS_TENSOR 只认 **&FORCE_EVAL 顶层的关键字**（不是在
            # &FORCE_EVAL/&PRINT 里那个同名的打印段，后者只管"打印"）。
            elif kw == "STRESS_TENSOR" and sec == "FORCE_EVAL" and len(parts) >= 2:
                stress_tensor = parts[1].upper()
                stress_tag = i
            elif kw == "SYMMETRY" and sec == "CELL" and len(parts) >= 2:
                cell_symmetry = parts[1].upper()
            elif kw == "KEEP_SYMMETRY" and sec == "CELL_OPT" and len(parts) >= 2:
                keep_symmetry = parts[1].upper()
                keep_symmetry_tag = i
            elif kw == "TYPE" and sec == "CELL_OPT" and len(parts) >= 2:
                # 官方 05_optimization.md:129：&MOTION/&CELL_OPT/TYPE 在 **2026.2
                # 被移除**，晶胞优化始终用 DIRECT_CELL_OPT。本机校验用的
                # cp2k_input.xml 仍收这个关键字（旧版），所以只给 warning。
                warnings.append(
                    f"{i}: &CELL_OPT 下的 'TYPE {parts[1].upper()}' 在 **CP2K 2026.2 "
                    f"起已被移除**（官方版本变更记录），晶胞优化现在始终是 "
                    f"DIRECT_CELL_OPT（原子与晶胞**同时**优化）。它只在旧版有效："
                    f"若你确实要用交替方案（TYPE GEO_OPT），必须同时定义 "
                    f"&MOTION/&GEO_OPT 段；新版写它会被忽略/报未知关键字。")
            # ---- MD 系综 / 热浴 / SCF 精度 的证据 ----
            elif kw == "ENSEMBLE" and sec == "MD" and len(parts) >= 2:
                ensemble = parts[1].upper()
                ensemble_tag = i
            elif kw == "EPS_SCF" and sec == "SCF" and len(parts) >= 2:
                eps_scf = parts[1]
                eps_scf_tag = i

    if stack:
        for name, ln in stack:
            errors.append(f"unclosed section '&{name}' (opened at {ln})")

    # top-level checks
    for req in REQUIRED_TOP:
        if req not in seen_top:
            extra = "（注意：@INCLUDE 的文件若缺失，其中的段落不算数）" \
                if has_includes else ""
            errors.append(f"missing required top-level section &{req}{extra}")
    if run_type in MOTION_RUN_TYPES and "MOTION" not in seen_top:
        # T09 P23 的官方模板用 `@IF ( ${RTYPE} /= ENERGY_FORCE )` 把 &MOTION 变成
        # 条件段；条件不成立时没有 &MOTION 是**合法的**。前处理里我们不做真值
        # 求值，所以只要文件里出现过条件指令，就降级成 warning 而不是 error。
        msg = f"RUN_TYPE {run_type} requires a &MOTION section"
        (warnings if "cond" in flags else errors).append(
            msg + ("（文件用了 @IF 条件段，可能被条件排除，请自行确认）"
                   if "cond" in flags else ""))
    for nm in sorted(dyn_names):
        warnings.append(f"动态段名 '&{nm}' 里的变量未被 @SET 定义，"
                        f"已跳过段名检查")

    # -----------------------------------------------------------------------
    # CELL_OPT ⇒ 必须有可用的 STRESS_TENSOR（error）
    #
    # 为什么必须是 error 而不是 warning：官方 `&FORCE_EVAL/STRESS_TENSOR` 默认是
    # `NONE`，而 `RUN_TYPE CELL_OPT` **靠应力/压力驱动**（官方原话 "优化由受力
    # 驱动，CELL_OPT 还额外由应力驱动"）。没有应力张量，晶胞优化根本拿不到
    # 更新方向 —— 这不是"精度差一点"，是"这个输入做不了它宣称要做的事"。
    # 官方 §4.2 的 CELL_OPT 示例第一行就显式写了 `STRESS_TENSOR ANALYTICAL`
    # （references/official/05_optimization.md:101）。
    # -----------------------------------------------------------------------
    if run_type == "CELL_OPT" or has_cell_opt:
        _ok_stress = stress_tensor not in (None, "NONE")
        if not _ok_stress:
            _where = "RUN_TYPE CELL_OPT" if run_type == "CELL_OPT" \
                else f"&MOTION/&CELL_OPT（{cell_opt_tag}）"
            errors.append(
                f"{_where} 但没有可用的 STRESS_TENSOR"
                + (f"（{stress_tag} 处写的是 NONE）" if stress_tag else
                   "（&FORCE_EVAL 顶层没有这一行）")
                + "。官方 &FORCE_EVAL/STRESS_TENSOR 默认是 NONE，而 CELL_OPT "
                  "**靠应力/压力驱动**：拿不到应力，晶胞优化没有更新方向，"
                  "跑不出来或结果无意义。请在 &FORCE_EVAL 下加一行 "
                  "`STRESS_TENSOR ANALYTICAL`（数值应力写 `STRESS_TENSOR "
                  "NUMERICAL`，每个优化步会多算几次受力、明显更慢）。"
                  "依据：references/official/05_optimization.md:91/101/367。"
                  "gen_inp.py --type cell_opt 现在默认就发 ANALYTICAL。")

    # -----------------------------------------------------------------------
    # KEEP_SYMMETRY 必须配 &CELL SYMMETRY（warning，不是 error）
    #
    # 官方 Note 原文："KEEP_SYMMETRY 应始终与 FORCE_EVAL/SUBSYS/CELL/SYMMETRY
    # 指定的晶胞对称性一起使用"，而 `&CELL SYMMETRY` 官方默认是 `NONE`。
    # 只写 KEEP_SYMMETRY T 时**该开关空转**、没有任何效果，但输入语法完全合法
    # —— 所以是 warning（我们不知道用户是不是故意的）。
    # -----------------------------------------------------------------------
    if keep_symmetry in ("T", "TRUE", ".TRUE.", "1", "YES", "ON"):
        if cell_symmetry in (None, "NONE"):
            warnings.append(
                f"{keep_symmetry_tag}: KEEP_SYMMETRY {keep_symmetry} 目前是"
                f"**空转** —— "
                + ("&SUBSYS/&CELL 里没有 SYMMETRY 行" if cell_symmetry is None
                   else "&SUBSYS/&CELL SYMMETRY 写的是 NONE")
                + "。官方原话（references/official/05_optimization.md:355）："
                  "“KEEP_SYMMETRY 应始终与 FORCE_EVAL/SUBSYS/CELL/SYMMETRY "
                  "指定的晶胞对称性一起使用”；&CELL/SYMMETRY 的官方默认是 "
                  "NONE（`_kw_probe.py --section FORCE_EVAL/SUBSYS/CELL`）。"
                  "⇒ 要么在 &CELL 下写 `SYMMETRY <晶系>`（cubic / hexagonal / "
                  "tetragonal / orthorhombic / monoclinic / triclinic / "
                  "rhombohedral …，gen_inp.py 用 --cell-symmetry <晶系>），"
                  "要么把 KEEP_SYMMETRY 删掉，别留一个不起作用的开关。")

    # -----------------------------------------------------------------------
    # RUN_TYPE MD 的两条"一定会在 AIMD 上出事"的一致性检查（warning）
    #
    # 出处：`references/decide.md` §13/§22.7 与 F 层 playbook（症状→处方）；
    # 工具层此前一条都不查（`grep TIMESTEP|EPS_SCF scripts/validate_inp.py`
    # 零命中），而这两项正是长 AIMD 最常见的两种"白烧机时"。
    # -----------------------------------------------------------------------
    if run_type == "MD":
        if ensemble and ensemble.startswith("NVE") and has_thermostat:
            warnings.append(
                f"{ensemble_tag}: ENSEMBLE {ensemble} 与 &MOTION/&MD/&THERMOSTAT "
                f"**同时出现**，但两者语义冲突 —— 官方 ENSEMBLE 对 NVE 的定义是"
                f"“constant energy (microcanonical)”（微正则：N、V、E 恒定），"
                f"而 &THERMOSTAT/TYPE 的官方说明是“用于**恒温系综**的热浴”"
                f"（`_kw_probe.py --section MOTION/MD` 与 "
                f"`--section MOTION/MD/THERMOSTAT`）。⇒ NVE 下热浴**不生效**，"
                f"你得到的是“看起来配了热浴、实际完全不控温”的输入。"
                f"要控温请把系综改成 NVT（或 NPT_I/NPT_F）；"
                f"真要跑微正则就把 &THERMOSTAT 段删掉，别留一个不起作用的开关。")
        if ensemble and ensemble.startswith(("NVT", "NPT")) and not has_thermostat:
            warnings.append(
                f"{ensemble_tag}: ENSEMBLE {ensemble} 但没有 "
                f"&MOTION/&MD/&THERMOSTAT 段。官方 THERMOSTAT/TYPE 默认是 NONE"
                f" ⇒ 温度**不受控**，轨迹实际上在按 NVE 自由演化，"
                f"不能按 {ensemble} 的系综解读（含氢/金属体系温度容易飙升）。"
                f"请加 &THERMOSTAT TYPE CSVR（常规）/ NOSE / AD_LANGEVIN（表面）。")
        _loose = False
        if eps_scf is None:
            _loose = True
            _eps_txt = "未显式设置（CP2K 默认 1.0E-5）"
        else:
            try:
                _loose = float(eps_scf) > 1.0E-5
                _eps_txt = eps_scf
            except ValueError:
                _loose = False
                _eps_txt = eps_scf
        if _loose:
            warnings.append(
                f"{eps_scf_tag or '&SCF'}: RUN_TYPE MD 的 EPS_SCF = {_eps_txt}"
                f"，对**长 AIMD 偏松**。经验口径：1E-4 会看到能量漂移"
                f"（守恒量守不住）、1E-5 才『变好』、1E-6~1E-7 趋于不变；"
                f"生产 AIMD 建议 1.0E-6（含氢/金属尤其），"
                f"跑不动再权衡步长与机时。"
                f"（出处：references/decide.md §22.7 / playbook.md §0.2）")

    # `&POISSON PERIODIC` 与 `&CELL PERIODIC` 必须一致。
    # 官方 schema 对 &POISSON/PERIODIC 原话："Important notice, this only applies to
    # the electrostatics. See the CELL section to specify the periodicity used for e.g.
    # the pair lists. Typically the settings should be the same."
    # 两者默认值都是 XYZ，所以缺省当 XYZ 处理。
    p_poi = periodic["POISSON"] or "XYZ"
    p_cel = periodic["CELL"] or "XYZ"
    if p_poi != p_cel:
        where = []
        if periodic_tag["POISSON"]:
            where.append("&POISSON PERIODIC {}（{}）".format(
                p_poi, periodic_tag["POISSON"]))
        else:
            where.append("&POISSON PERIODIC 未写（默认 XYZ）")
        if periodic_tag["CELL"]:
            where.append("&CELL PERIODIC {}（{}）".format(
                p_cel, periodic_tag["CELL"]))
        else:
            where.append("&CELL PERIODIC 未写（默认 XYZ）")
        warnings.append(
            "两项 PERIODIC 不一致：" + "，".join(where)
            + "。官方原文提醒 `&POISSON/PERIODIC` **只管静电**，pair list / 结构的"
              "周期性由 `&CELL/PERIODIC` 决定，**两者的设置通常应当相同**。"
              "不一致的典型后果：孤立分子只设了 &POISSON 而 &CELL 仍是 XYZ ⇒ "
              "邻居表按三维周期建（白算镜像）；表面 slab 只设了 &POISSON XY 而 "
              "&CELL 仍是 XYZ ⇒ z 方向多一层周期性镜像。")

    # 基组 ↔ 基组库文件配套检查。
    # MOLOPT 族基组住在 BASIS_MOLOPT，BASIS_SET 里没有它们；ADMM 辅助基组
    # （cFIT/FIT/pFIT 族）住在 BASIS_ADMM(_MOLOPT)。写错库文件名是新手最常
    # 踩的坑：CP2K 直接 "basis set not found" 退出，而报错完全指不到"文件没配"。
    #
    # 注意 BASIS_SET_FILE_NAME 的值常常是**带路径**的 ——
    # 真实生产输入卡写的是 `${DATAPATH}/BASIS_MOLOPT`（见 H 层 cases/），
    # 所以只能比 basename，不能用整串相等（早先的写法会把它误报成"没配"）。
    def _has_lib(name):
        for f in basis_files:
            base = f.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
            if base == name:
                return True
        return False

    molopt = [b for b in basis_values if "MOLOPT" in b]
    plain = [b for b in basis_values if "MOLOPT" not in b]
    if molopt and not _has_lib("BASIS_MOLOPT"):
        warnings.append(
            "用了 MOLOPT 族基组（{}）但没有 BASIS_SET_FILE_NAME BASIS_MOLOPT："
            "这些基组在 BASIS_MOLOPT 文件里，BASIS_SET 文件里没有，"
            "CP2K 会报找不到基组".format(", ".join(sorted(set(molopt)))))
    if plain and not _has_lib("BASIS_SET"):
        warnings.append(
            "用了 GTH/PADE 族基组（{}）但没有 BASIS_SET_FILE_NAME BASIS_SET"
            "（若你确定默认值够用可忽略）".format(", ".join(sorted(set(plain)))))
    admm = [b for b in aux_basis_values if b.startswith(("CFIT", "FIT", "PFIT"))]
    if admm and not any(f.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
                        .startswith("BASIS_ADMM") for f in basis_files):
        warnings.append(
            "用了 ADMM 辅助基组（{}）但没有 BASIS_SET_FILE_NAME BASIS_ADMM"
            "（或 BASIS_ADMM_MOLOPT）：CP2K 会报找不到辅助基组"
            .format(", ".join(sorted(set(admm)))))
    if method == "QUICKSTEP" and run_type in ("GEO_OPT", "CELL_OPT", "MD"):
        # OPTIMIZER sanity is checked structurally below if MOTION present
        pass

    # -----------------------------------------------------------------------
    # &MOTION/&CONSTRAINT/&FIXED_ATOMS 索引越界检查
    #
    # 为什么必须有这一条：CP2K 对越界的 LIST 索引**既不报错也不警告** ——
    # 它照常打印 "MD| Constraints activated"，然后一个原子都冻不上，作业
    # 一路跑完、结果物理全错。H 层 cases/ 里 5 张真实生产卡就有 4 张踩了
    # 这个坑（cu100-h2o-aimd 请求 LIST 139..170，体系却只有 132 个原子）。
    # -----------------------------------------------------------------------
    n_atoms = max(coord_atom_counts) if coord_atom_counts else None
    # ⚠️ 只有**真的从外部文件读结构**的 &TOPOLOGY 才与内联 &COORD 冲突。
    # 判据来自官方 XML 的 `FORCE_EVAL/SUBSYS/TOPOLOGY`：18 个关键字里只有两个是
    # 「从文件读结构」——`COORD_FILE_NAME`（坐标）与 `CONN_FILE_NAME`（连接性）；
    # 其余（`USE_ELEMENT_AS_KIND`/`MOL_CHECK`/`NUMBER_OF_ATOMS`…）与全部子段
    # （`&CENTER_COORDINATES`/`&GENERATE`/`&MOL_SET`/`&DUMP_*`/`&EXCLUDE_*`）
    # **都不读外部结构**。
    # 早先只要看到 &TOPOLOGY 就报"内联 &COORD 被忽略" ⇒ 对
    # `&TOPOLOGY/&CENTER_COORDINATES`（WAVELET 求解器要求分子居中时的标准写法，
    # 见 gen_inp.py 的 `--periodic none`）**是假阳性**，而且措辞会吓到用户
    # （实测该写法下内联 &COORD 完全生效：|ΣF| = 0.0002 a.u.）。
    # 这里用**事后扫描**判定：从 &TOPOLOGY 起点扫到配对的 &END TOPOLOGY，
    # 看块内有没有那两个关键字（比在解析循环里跟踪更稳，不依赖循环内部状态）。
    topology_file_tags = []
    for _t in topology_tags:
        # `topology_tags` 里存的其实是形如 `"L72"` 的**标签串**（上游 append 的 `i`
        # 不是 enumerate 行号，而是带 `L` 前缀的位置标签）⇒ 这里把数字抠出来，
        # 无论给的是 `72` 还是 `"L72"` 都能定位。
        _digits = "".join(c for c in str(_t) if c.isdigit())
        _n = int(_digits) if _digits else 0
        if not (1 <= _n <= len(raw)):
            continue
        _depth = 0
        for _ln in raw[_n - 1:]:
            _s = _ln.strip().upper()
            if _s.startswith("&TOPOLOGY"):
                _depth += 1
            elif _s.startswith("&END TOPOLOGY"):
                _depth -= 1
                if _depth <= 0:
                    break
            elif _depth > 0 and "&" not in _s:
                _parts = _s.split()
                if _parts and _parts[0] in ("COORD_FILE_NAME", "CONN_FILE_NAME"):
                    topology_file_tags.append("L{}".format(_n))
                    break
    if topology_file_tags and coord_atom_counts:
        warnings.append(
            "&SUBSYS 里同时出现内联 &COORD（{} 个原子）与 &TOPOLOGY 的 "
            "`COORD_FILE_NAME`/`CONN_FILE_NAME`（{}）："
            "CP2K 会从外部文件读结构、内联 &COORD 被忽略；"
            "两者原子数若不一致，&FIXED_ATOMS 的索引就会指向错误的原子。"
            .format(max(coord_atom_counts), topology_file_tags[0]))

    for tag, tokens in fixed_specs:
        idxs, bad = expand_index_specs(tokens)
        if bad:
            warnings.append(
                f"{tag}: &FIXED_ATOMS 的 LIST 里有无法解析的 token："
                + ", ".join(repr(b) for b in bad[:5]))
        if not idxs:
            continue
        nonpos = sorted(x for x in idxs if x <= 0)
        if nonpos:
            warnings.append(
                f"{tag}: &FIXED_ATOMS 的 LIST 含非正索引 {_fmt_ranges(nonpos)}，"
                f"已跳过越界判定（本检查只认显式的正整数索引）")
            idxs = {x for x in idxs if x > 0}
            if not idxs:
                continue
        if n_atoms is None:
            # 坐标不可见（&COORD 里只有 @INCLUDE 且目标不存在，或结构来自
            # &TOPOLOGY 外部文件）→ **不要瞎报错**，只提示无法核对。
            warnings.append(
                f"{tag}: 无法核对 &MOTION/&CONSTRAINT/&FIXED_ATOMS 的索引"
                f"（{_fmt_ranges(idxs)}）是否越界：本文件的坐标不可见"
                f"（没有可数的 &COORD 原子行，例如 &COORD 里只有 @INCLUDE 而"
                f"目标文件不存在，或用 &TOPOLOGY 从外部文件读结构）。"
                f"请自行确认这些索引不超过体系原子数。")
            continue
        over = sorted(x for x in idxs if x > n_atoms)
        if over:
            errors.append(
                f"{tag}: &MOTION/&CONSTRAINT/&FIXED_ATOMS 的 LIST 索引越界 —— "
                f"{_fmt_ranges(over)} 超出体系原子数 {n_atoms}"
                f"（该 LIST 最大索引 {max(idxs)}）。"
                f"CP2K 对越界索引**不报错也不警告**：它会照常打印 "
                f"'Constraints activated'，但这些索引指向的原子不存在，"
                f"结果是一个原子都没冻上、作业照跑、物理结果全错。"
                f"请按坐标文件里的实际原子顺序把索引改成不超过 {n_atoms} 的"
                f"正整数（本检查不替你猜该冻哪些原子）。")

    return errors, warnings, raw


def sorted_suggestion(name):
    """Return up to 3 closest known section names (Levenshtein-ish).

    从官方全量表里挑近邻，这样提示的是**真实存在的段名**。
    """
    cands = sorted(ALL_SECTIONS, key=lambda s: dist(s, name))[:3]
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
    ap.add_argument("--json", action="store_true",
                    help="输出 JSON（给 agent 用）")
    args = ap.parse_args()

    # 自行展开通配符：bash 会替程序展开，但 Windows 的 cmd / PowerShell 对原生程序
    # **不展开**，于是 `python validate_inp.py examples/0*/*.inp` 在 Windows 上会把
    # 字面量当文件名。
    #   * 通配符没匹配到任何文件 → 友好中文（而不是 Windows 的 Errno 22）
    #   * 非通配符路径原样保留 → 照常走"找不到文件"分支
    files = []
    unmatched_globs = []
    for pat in args.files:
        hits = sorted(glob.glob(pat))
        if hits:
            files.extend(hits)
        elif any(c in pat for c in "*?["):
            unmatched_globs.append(pat)
        else:
            files.append(pat)

    rc = 0
    results = []
    for pat in unmatched_globs:
        rc = 1
        results.append({"file": pat, "errors": [f"找不到匹配「{pat}」的文件"],
                        "warnings": [], "ok": False})
        if not args.json:
            print(f"== lint {pat} ==")
            print(f"  [ERROR] 找不到匹配「{pat}」的文件（请检查路径或通配符）")
            print("  RESULT: 1 error(s), 0 warning(s)")

    for f in files:
        errors, warnings, _ = parse(f)
        results.append({"file": f, "errors": errors, "warnings": warnings,
                        "ok": not errors})
        if errors:
            rc = 1
        if not args.json:
            print(f"== lint {f} ==")
            for w in warnings:
                print(f"  [warn] {w}")
            if errors:
                for e in errors:
                    print(f"  [ERROR] {e}")
                print(f"  RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
            else:
                print(f"  RESULT: OK ({len(warnings)} warning(s))")

        if args.cp2klint:
            cp2k = shutil.which("cp2klint") or os.environ.get("CP2KLINT")
            if cp2k:
                if not args.json:
                    print(f"== cp2klint {f} ==")
                r = subprocess.run([cp2k, f],
                                   capture_output=True, text=True,
                                   encoding="utf-8", errors="replace")
                results[-1]["cp2klint_rc"] = r.returncode
                results[-1]["cp2klint_out"] = (r.stdout + r.stderr)[-2000:]
                rc = rc or r.returncode
            else:
                results[-1]["cp2klint_rc"] = None
                if not args.json:
                    print("  (cp2klint not found on PATH; skipped)")

    if args.json:
        import json
        print(json.dumps({"ok": rc == 0, "results": results},
                         ensure_ascii=False, indent=2))
    sys.exit(rc)


if __name__ == "__main__":
    main()
