#!/usr/bin/env python3
"""CP2K 后处理引擎 —— skill 闭环的第 5 步(跑完读结果之后)。

读 CP2K 产出的轨迹 / .out / .pdos / .cube / metadyn restart，直接算出常用的
后处理量并出图(.png) 与数据(.csv)。分两层：

  核心层(纯 numpy + matplotlib，零外部依赖)：
    energy    能量/温度曲线          (from .out / .ener)
    rdf       径向分布函数 g(r)       (from 轨迹 xyz + cell)
    msd       均方位移               (from 轨迹 xyz + cell)
    diffusion 扩散系数 D (Einstein)  (from 轨迹 xyz + cell)
    bond      键长时间序列+分布       (from 轨迹 xyz)
    angle     键角时间序列+分布
    dihedral  二面角时间序列+分布
    pdos      态密度/投影态密度绘图   (from .pdos + Fermi)
    adf       角分布函数             (from 轨迹 xyz + cell)
    cn        配位数                 (from rdf)
    zprofile  轴向密度剖面           (from 轨迹 xyz + cell)
    vacf      速度自相关函数          (from 速度 xyz, 或位置 xyz 差分近似)
    ir        红外/振动态密度(FFT)    (from vacf)
    power     功率谱(= ir 别名)

  桥接层(检测外部二进制, 调用并解析; 缺失时给指引不中断)：
    bader     检测 bader -> 跑 -> 解析 ACF.dat (需 --properties cube 产出的 cube)
    fes       调用 CP2K graph 工具 -> 解析 fes.dat -> 2D 等值线 (需 metadyn restart)
    travis    检测 travis -> 生成控制文件 -> 运行 -> 解析 csv (IR/Raman 等)

所有子命令支持 --prefix 指定输出名(默认用输入文件名派生)；图与 csv 落在
当前目录。时间单位默认 ps(CP2K 轨迹注释行 time=... 即 ps)，坐标默认 Å。

衔接(见 references/postprocess.md)：
  gen_inp.py 布 PRINT -> cp2k 跑 -> 产出 xyz/.out/.pdos/cube/restart
             -> postprocess.py 吃这些文件 -> 出图/csv -> diagnose 判读 -> 回 gen_inp 调参
"""
import argparse
import os
import re
import shutil
import sys
import math

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

# 收集本进程写出的产物路径（--json 时回报给调用方）
_OUTPUTS = []

# --- 物理常数（**只此一处**，所有子命令共用；避免各函数各写一个数）----------
#
# 单位换算的依据（每条都在 --help 或 CSV 表头里复述，用户能自查）：
#   HARTREE_EV : 1 Hartree = 27.211386245988 eV（CODATA；与 _parse_pdos_file 用的同值）
#   HARTREE_TO_KJMOL : 1 Hartree = 2625.5 kJ/mol（= 27.211386×96.485，与 _plot_fes 同值）
#   BOHR_ANG   : 1 bohr = 0.529177210903 Å（Gaussian cube 的负格点数约定 = 坐标以 bohr 计）
#   SHE_EV     : **标准氢电极的绝对电势 4.44 eV**（庚子讲义口径，`course_learned.md:808–809`、
#                `:2227`："真空能级作零点时 SHE = 4.44 eV（最被广泛接受的数值）"；
#                算例 `course_learned.md:809`：Φ = 5.26 eV → 5.26 − 4.44 = +0.82 V。
#                另见 `playbook.md:40`、`learn_L3.md:834`、`learn_L4.md:476`。
#                ⚠️ 不要凭记忆改成 4.5 / 4.6 —— 本仓库的权威口径就是 4.44。）
#   R_GAS      : 8.31446261815324 J·mol⁻¹·K⁻¹
#   KB_EV      : 8.617333262e-5 eV/K（= R/N_A，Arrhenius 与 −RT·ln g 都从这里派生）
HARTREE_EV = 27.211386245988
HARTREE_TO_KJMOL = 2625.5
BOHR_ANG = 0.529177210903
SHE_EV = 4.44
R_GAS = 8.31446261815324
KB_EV = R_GAS / 96485.33212
# 1 eV ≈ 96.485 kJ/mol（= 96485.33212/1000）；讲义口播"9 万 6"（`postprocess.md:103`）
KJMOL_PER_EV = 96.48533212

try:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as _exc:  # 友好提示，不让用户面对 traceback
    _missing = getattr(_exc, "name", "numpy/matplotlib")
    sys.stderr.write(
        "\n".join([
            "",
            "=" * 68,
            f"缺少依赖：{_missing}",
            "",
            "postprocess.py 需要 numpy 与 matplotlib（核心层全部子命令）。",
            "安装方式（任选其一）：",
            "",
            "  pip install -r requirements.txt",
            "  pip install numpy matplotlib",
            "",
            "若只想跑不需要绘图的桥接命令（bader/fes/travis），",
            "仍需 numpy 解析数据；请先装好依赖再运行。",
            "=" * 68,
            "",
        ])
    )
    sys.exit(3)


# --------------------------------------------------------------------------
# IO helpers
# --------------------------------------------------------------------------
def read_xyz(path):
    """读 CP2K 多帧 xyz。

    返回 (elements, frames, times, energies):
      elements : list[str]        首帧原子符号
      frames   : np.ndarray       shape (nframe, N, 3)
      times    : np.ndarray       shape (nframe,) 或 None (无 time 注释)
      energies : np.ndarray       shape (nframe,) 或 None (无 E 注释)
    """
    text = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    elements = None
    frames = []
    times = []
    energies = []
    has_time = False
    has_energy = False
    i = 0
    n = len(text)
    while i < n:
        line = text[i].strip()
        if not line:
            i += 1
            continue
        # 帧头: 原子数
        try:
            nat = int(line)
        except ValueError:
            i += 1
            continue
        i += 1
        if i >= n:
            break
        comment = text[i]
        i += 1
        coords = []
        sym = []
        for _ in range(nat):
            if i >= n:
                break
            parts = text[i].split()
            sym.append(parts[0])
            coords.append([float(parts[1]), float(parts[2]), float(parts[3])])
            i += 1
        if elements is None:
            elements = sym
        frames.append(np.array(coords, dtype=float))
        mt = re.search(r"time\s*=\s*([-\d.eE+]+)", comment)
        me = re.search(r"\bE\s*=\s*([-\d.eE+]+)", comment)
        if mt:
            times.append(float(mt.group(1)))
            has_time = True
        if me:
            energies.append(float(me.group(1)))
            has_energy = True
    frames = np.array(frames)
    times = np.array(times) if has_time else None
    energies = np.array(energies) if has_energy else None
    return elements, frames, times, energies


def parse_cell_arg(s):
    """'a b c' -> 立方; 'ax ay az bx by bz cx cy cz' -> 一般 3x3。返回 3x3 ndarray。"""
    v = [float(x) for x in s.split()]
    if len(v) == 3:
        a, b, c = v
        return np.array([[a, 0, 0], [0, b, 0], [0, 0, c]], dtype=float)
    if len(v) == 9:
        return np.array(v, dtype=float).reshape(3, 3)
    raise ValueError("--cell 需 3 个(立方)或 9 个(一般)浮点数")


def parse_cell_from_out(path):
    """从 .out 解析 CELL| Vector a/b/c [angstrom]。失败返回 None。"""
    try:
        lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    except OSError:
        return None
    vec = {}
    for ln in lines:
        m = re.search(r"CELL\|\s*Vector\s+([abc])\s*\[angstrom\]\s*:\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)", ln)
        if m:
            vec[m.group(1)] = [float(m.group(2)), float(m.group(3)), float(m.group(4))]
    if set("abc") <= set(vec):
        return np.array([vec["a"], vec["b"], vec["c"]], dtype=float)
    return None


def get_cell(args, nframes_hint=None):
    """按优先级: --cell > .out 解析 > None(非周期)。

    注意（2026-10 核查）：第二个分支（从 `args.out` 解析 `.out` 的 `CELL|` 行）
    目前**是死代码**——没有任何子命令定义过 `--out`，所以 `getattr(args, "out", None)`
    永远取不到值。保留它是为了将来真加 `--out` 时能直接用；但**当下的行为等价于
    "只认 `--cell`"**，所以 `--cell` 的帮助文本已改为"必须显式给"。
    调用方（如 `cmd_rdf`）在 `H is None` 时会打印 `NON-PBC(包围盒近似)`，供用户自查。
    """
    if getattr(args, "cell", None):
        return parse_cell_arg(args.cell)
    if getattr(args, "out", None) and os.path.exists(args.out):
        c = parse_cell_from_out(args.out)
        if c is not None:
            return c
    return None


def pbc_dist(r1, r2, H, Hinv):
    """最小镜像约定下的两原子距离。"""
    f = Hinv @ (r1 - r2)
    f -= np.round(f)
    return float(np.linalg.norm(H @ f))


def unwrap_traj(frames, H):
    """把每原子轨迹做 PBC 解包裹, 得到连续坐标(用于 MSD)。"""
    M, N, _ = frames.shape
    un = np.zeros_like(frames)
    un[0] = frames[0]
    if H is None:
        return frames.copy()
    Hinv = np.linalg.inv(H)
    for k in range(1, M):
        d = frames[k] - un[k - 1]
        f = Hinv @ d.T
        f -= np.round(f)
        un[k] = un[k - 1] + (H @ f).T
    return un


def save_png(fig, path):
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    _OUTPUTS.append(path)
    return path


def write_csv(path, header, rows):
    if isinstance(header, list):
        header = ",".join(header)
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + "\n")
        for r in rows:
            f.write(",".join(str(x) for x in r) + "\n")
    _OUTPUTS.append(path)
    return path


def out_prefix(args):
    p = getattr(args, "prefix", None)
    if p:
        return p
    src = getattr(args, "traj", None) or getattr(args, "out", None) \
        or getattr(args, "xyz", None) or getattr(args, "pdos", None) \
        or getattr(args, "vel", None) or "cp2k"
    base = os.path.basename(str(src))
    return os.path.splitext(base)[0]


def ensure_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)


# --------------------------------------------------------------------------
# energy
# --------------------------------------------------------------------------
# 结构 / 轨迹类扩展名。列在这里的不是"白名单"，只是**输入类型校验**的判据之一
# （另一个判据是 xyz 的行形状），用来把"把轨迹喂给 energy"这类误用挡在门外。
_STRUCTURE_EXTS = {
    ".xyz", ".pdb", ".cell", ".cif", ".poscar", ".vasp", ".gro",
    ".car", ".arc", ".coord", ".txyz", ".dump", ".lammpstrj",
}


def looks_like_structure(path, lines):
    """判断"这个文件看起来是结构/轨迹文件，而不是能量文件"。

    返回 ``(True, 判据说明)`` 或 ``(False, "")``。

    判据**只用「扩展名 + 行形状」两条**，刻意不用「ENERGY| 正则没命中就报错」——
    真实 CP2K ``.ener`` 文件里确实**没有** ``ENERGY|`` 字样，必须继续走后面
    "两列 step energy" 的退化分支（见 cmd_energy）。本函数只负责识别
    "一眼就是结构/轨迹"的输入。
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in _STRUCTURE_EXTS:
        return True, "扩展名 {} 属于结构/轨迹格式".format(ext)
    # xyz 行形状：第一个非空行是纯整数(原子数)，紧接着一行不是纯数字(注释行)
    body = [ln for ln in lines if ln.strip()]
    if len(body) >= 2:
        try:
            nat = int(body[0].strip())
        except ValueError:
            nat = None
        if nat is not None and nat > 0:
            first_tok = body[1].split()[0] if body[1].split() else ""
            try:
                float(first_tok)
                numeric_second = True
            except ValueError:
                numeric_second = False
            if not numeric_second:
                return True, ("首行是原子数 {}、次行是注释行"
                              "（典型的多帧 xyz 轨迹形状）".format(nat))
    return False, ""


def _energy_wrong_file_error(path, reason):
    """给"把结构/轨迹文件喂给 energy"的友好中文提示（不抛 traceback）。"""
    print("", file=sys.stderr)
    print("=" * 68, file=sys.stderr)
    print("[ERROR] 这个文件是**结构/轨迹**，不是能量文件：", file=sys.stderr)
    print("        {}".format(path), file=sys.stderr)
    print("        判定依据：{}".format(reason), file=sys.stderr)
    print("", file=sys.stderr)
    print("energy 子命令只吃下面两类文件：", file=sys.stderr)
    print("  * CP2K 输出 .out —— 能量行长这样（本命令就在这里找）：", file=sys.stderr)
    print("      ENERGY| Total FORCE_EVAL ( QS ) energy (a.u.):   -2791.864262806741863",
          file=sys.stderr)
    print("  * CP2K 能量文件 .ener —— **两列** `step energy`，", file=sys.stderr)
    print("      文件里**没有** ENERGY| 字样（这种情况本命令照样支持）", file=sys.stderr)
    print("", file=sys.stderr)
    print("轨迹文件（.xyz / .pdb / .cell …）请改用对应的后处理子命令，例如：", file=sys.stderr)
    print('  python scripts/postprocess.py rdf       "<traj.xyz>" --cell "a b c"',
          file=sys.stderr)
    print('  python scripts/postprocess.py msd       "<traj.xyz>" --cell "a b c" --dt <ps>',
          file=sys.stderr)
    print('  python scripts/postprocess.py diffusion "<traj.xyz>" --cell "a b c" --dt <ps>',
          file=sys.stderr)
    print("  （另有 bond / angle / dihedral / adf / cn / zprofile / vacf / ir …，"
          "见 postprocess.py --help）", file=sys.stderr)
    print("=" * 68, file=sys.stderr)


def _ener_header_cols(ln):
    """从 `.ener` 表头解析各字段的**数据列号**。

    🔴 **为什么不能拿 token 序号当列号**（2026-10 真机实测抓到的静默错值）：
    CP2K 官方 `.ener` 的表头是

        #   Step Nr.   Time[fs]   Kin.[a.u.]   Temp[K]   Pot.[a.u.]   Cons Qty[a.u.]   UsedTime[s]

    它比数据行**多出 `#`、`Nr.`、`Qty[a.u.]` 三个 token**（`Step Nr.` 与 `Cons Qty[a.u.]`
    各是两个 token 描述一列）。按 token 序号定位就会整体右移：表头 `Pot` 落在第 6 位，
    而数据行第 6 列其实是 **UsedTime（每步墙钟秒数）** —— 实测一份真实 `.ener` 被报成
    `energy final = 14.79 a.u.`（真实的势能是 `-17.12`），温度被报成 `-17.12 K`，
    **退出码 0、照常出图出 CSV**。而且它还会**盖掉**本来正确的"按列数回退"分支。

    正确做法：把表头里**能识别**的字段按出现顺序编号 —— 第 k 个被识别到的字段就是第 k 列。
    `#` / `Nr.` / `Qty[a.u.]` 识别不出来，自然不占编号。标准表头于是得到
    `s=0, t=1, k=2, T=3, e=4, c=5, w=6`，与数据行完全对齐。
    """
    # 顺序要紧：`usedtime` 必须在 `time` 之前判，否则 UsedTime 会被当成 Time。
    keys = (("usedtime", "w"), ("time", "t"), ("step", "s"),
            ("kin", "k"), ("temp", "T"), ("pot", "e"), ("cons", "c"))
    cols, n = {}, 0
    for tk in ln.split():
        t = tk.strip().lower().lstrip("#")
        if not t:
            continue
        hit = None
        for key, tag in keys:
            if t.startswith(key):
                hit = tag
                break
        if hit is None:
            continue                     # `Nr.` / `Qty[a.u.]` 等不对应数据列
        if hit not in cols:
            cols[hit] = n
        n += 1
    return cols


def _parse_ener(lines):
    """解析 CP2K 的 `.ener`（无 `ENERGY|` 字样），返回 ``(steps, energies, temps)``。

    **为什么不能取最后一列**：CP2K 官方 `.ener` 的标准列序是 **7 列** ——

        Step  Time[fs]  Kin.[a.u.]  Temp[K]  Pot.[a.u.]  Cons Qty[a.u.]  UsedTime[s]

    最后一列 `UsedTime` 是**每步墙钟耗时（秒）**。早先的实现取 `parts[-1]`，
    在真实 7 列文件上把"秒"当成"能量"交出去：实测 `final = 17.5 a.u.`
    而真实势能是 `-100.05`，**退出码还是 0**、照常出图出 CSV。

    列数分派规则（先看表头，再退回按列数判断）：

    * 有表头且含 `Pot` ⇒ 用表头定位（最稳）
    * 7 列 ⇒ 能量取第 5 列（`Pot`）、温度取第 4 列（`Temp`）
    * 6 列 ⇒ 形如 `Step Time Kin Temp Pot Cons`，能量取第 5 列
    * 5 列 ⇒ 形如 `Step Time Kin Temp Pot`，能量取最后一列
    * 2 列 ⇒ `step energy`，能量取最后一列（最初支持的那种简写）
    * 其它列数 ⇒ 取倒数第二列并给出提示（不静默）
    """
    ei, ti, si = None, None, None
    for ln in lines[:8]:                      # 表头只可能在前几行
        low = ln.lower()
        if "pot" in low and ("step" in low or "time" in low):
            cols = _ener_header_cols(ln)
            ei, ti, si = cols.get("e"), cols.get("T"), cols.get("s")
            break
    steps, energies, temps = [], [], []
    nrow = 0
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        try:
            vals = [float(x) for x in parts]
        except ValueError:
            continue                          # 表头行/非数据行
        nrow += 1
        n = len(vals)
        if ei is not None and n > ei:
            e = vals[ei]
        elif n >= 6:
            e = vals[4]                       # Pot：7 列与 6 列都在这个位置
        else:
            e = vals[-1]                      # 2/5 列简写
        energies.append(e)
        if si is not None and n > si:
            steps.append(int(vals[si]))
        else:
            steps.append(nrow)
        if ti is not None and n > ti:
            temps.append(vals[ti])
        elif n >= 6 and n > 3:
            temps.append(vals[3])             # Temp
    return steps, energies, temps


def cmd_energy(args):
    path = args.out
    if not os.path.exists(path):
        print(f"ERROR: 找不到能量文件 {path}")
        return 1
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    energies = []
    for ln in lines:
        m = re.search(r"ENERGY\|\s+Total FORCE_EVAL.*?:\s*([-\d.eE+]+)", ln)
        if m:
            energies.append(float(m.group(1)))
    temps = []
    for ln in lines:
        low = ln.lower()
        if "emperature" not in low:
            continue
        # 只收**动力学温度[K]**。排除同一 .out 里其它带 "temperature" 的行：
        #   * Electronic temperature [a.u.] —— SCF 展宽参数，不是离子温度；
        #   * MD| Temperature tolerance [K]  —— 容差，不是温度；
        #   * 带 [a.u.] 的任何行。
        # 再要求行内有 '='：真正的逐步温度行是 ' TEMPERATURE [K] = <inst> <avg>'，
        # 而 ' MD| Temperature [K]  300.00'（协议头）/ ' Initial Temperature 300.00 K'
        # 没有 '='。这样温度序列与能量序列**逐步对齐**（实测都是 2535 点）。
        if "electronic" in low or "tolerance" in low or "[a.u.]" in low:
            continue
        if "=" not in ln:
            continue
        # 严格浮点正则。旧写法 `[-\d.eE+]+` 会把 "temperature" 自带的 e/E
        # 本身当成数字（在真实 .out 上 2537/2540 行都命中 'e' / 'E' / '.'），
        # 于是 float('.') 抛 ValueError —— 真实生产 .out 上 cmd_energy 直接
        # traceback（违反 AGENTS.md §6.3「任何情况都不抛 traceback」）。
        m = re.search(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eEdD][-+]?\d+)?",
                      ln.split("emperature")[-1])
        if m:
            try:
                temps.append(float(m.group(0)))
            except ValueError:
                pass
    if not energies:
        # 没有任何 ENERGY| 命中 —— 先做**输入类型校验**：若这是结构/轨迹文件，
        # 说明用户给错了文件；否则才走 .ener 两列退化分支。
        # （此前不校验，直接把任意两列数字当能量收下：真实 21 MB 的
        #   cp2k-pos-1.xyz 会被收成 337155 个"能量点"、退出码 0、产出 7 MB 垃圾 CSV。）
        looks_bad, reason = looks_like_structure(path, lines)
        if looks_bad:
            _energy_wrong_file_error(path, reason)
            return 1
    if not energies:
        # 退化分支：CP2K 的 `.ener`（文件里没有 `ENERGY|` 字样）。
        #
        # ⚠️ 这里**不能取 `parts[-1]`**。CP2K 官方 `.ener` 的标准列序是 7 列：
        #     Step  Time[fs]  Kin.[a.u.]  Temp[K]  Pot.[a.u.]  Cons Qty[a.u.]  UsedTime[s]
        # 最后一列是**每步墙钟耗时（秒）**，与能量毫无关系。早先取 `parts[-1]`
        # 会在真实 7 列文件上静默给出错值：实测 `final = 17.5 a.u.` 而真实势能是
        # `-100.05`，且 **exit 0**、照常出图出 CSV —— 属于"悄悄给错答案"。
        steps, energies, ener_temps = _parse_ener(lines)
        if ener_temps and not temps:
            temps = ener_temps
    if not energies:
        print("ERROR: 未在文件中找到能量记录(ENERGY| Total FORCE_EVAL)。")
        return 1
    energies = np.array(energies)
    prefix = out_prefix(args)
    csv = prefix + "_energy.csv"
    write_csv(csv, "step,energy_a.u.", [[i + 1, e] for i, e in enumerate(energies)])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(range(1, len(energies) + 1), energies, lw=1.0)
    ax.set_xlabel("step")
    # 纵轴语义：`&ener` 的 `Pot` 列与 `.out` 的 `ENERGY|` 都是**势能**
    # （BOMD 里核在 BO 面上的势能）。图上标"total energy"会与 MD 语境冲突
    # （NVT 下"总能量"不守恒，守恒的是"体系能量 + 热浴能量"），
    # 而标题写的是 "Potential energy trajectory" —— 两处必须一致。
    ax.set_ylabel("potential energy [a.u.]")
    ax.set_title("Potential energy trajectory")
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_energy.png")
    print(f"energy: {len(energies)} points; final = {energies[-1]:.8f} a.u.")
    if temps:
        tcsv = prefix + "_temperature.csv"
        write_csv(tcsv, "step,temperature[K]", [[i + 1, t] for i, t in enumerate(temps)])
        fig2, ax2 = plt.subplots(figsize=(7, 4))
        ax2.plot(range(1, len(temps) + 1), temps, lw=1.0)
        ax2.set_xlabel("step")
        ax2.set_ylabel("temperature [K]")
        ax2.set_title("Temperature trajectory")
        ax2.grid(alpha=0.3)
        save_png(fig2, prefix + "_temperature.png")
        print(f"temperature: {len(temps)} points; final = {temps[-1]:.2f} K")
    print(f"written: {prefix}_energy.png (+ .csv)")
    return 0


# --------------------------------------------------------------------------
# rdf
# --------------------------------------------------------------------------
def _select_pairs(elements, pairs_arg):
    """把 `--pairs` 的写法解析成 (元素A, 元素B) 列表。

    `--pairs` 的**每一项**是一对、用空格分隔，例如 `--pairs "O H" "O O"`。
    早先的实现直接 `a, b = p.split()`，用户按直觉写 `--pairs O H`（两个参数、
    各含一个元素）就会抛 `ValueError: not enough values to unpack` 的
    traceback —— 违反 AGENTS.md §6.3 的健壮性基线（不抛 traceback）。
    现在给友好中文提示 + exit 2。
    """
    uniq = sorted(set(elements))
    if pairs_arg:
        pairs = []
        for p in pairs_arg:
            toks = p.replace(",", " ").replace("-", " ").split()
            if len(toks) != 2:
                print(
                    f"\n[ERROR] --pairs 的每一项必须是**一对**元素、用空格分隔，"
                    f"收到的是 {p!r}\n"
                    f"  正确写法: --pairs \"O H\" \"O O\"\n"
                    f"  常见错法: --pairs O H   （这是两个参数，各含一个元素）\n"
                    f"  本体系可用元素: {', '.join(uniq)}",
                    file=sys.stderr)
                sys.exit(2)
            pairs.append(tuple(sorted((toks[0], toks[1]))))
        return pairs
    # 全部唯一元素对
    return [tuple(sorted((a, b))) for a in uniq for b in uniq if a <= b]


def cmd_rdf(args):
    elements, frames, _, _ = read_xyz(args.traj)
    H = get_cell(args)
    cell_note = "PBC" if H is not None else "NON-PBC(包围盒近似)"
    pairs = _select_pairs(elements, args.pairs)
    rmax = args.rmax
    nbins = args.bins
    dr = rmax / nbins
    r_centers = np.linspace(dr / 2, rmax - dr / 2, nbins)
    hist = {p: np.zeros(nbins) for p in pairs}
    M, N, _ = frames.shape
    idx_by_elem = {e: [i for i, x in enumerate(elements) if x == e] for e in set(elements)}
    if H is not None:
        Hinv = np.linalg.inv(H)
        V = abs(np.linalg.det(H))
    else:
        lo = frames.min(axis=(0, 1))
        hi = frames.max(axis=(0, 1))
        V = float(np.prod(hi - lo))
    for fi in range(M):
        fr = frames[fi]
        for (a, b) in pairs:
            ia = idx_by_elem.get(a, [])
            ib = idx_by_elem.get(b, [])
            if not ia or not ib:
                continue
            for i in ia:
                for j in ib:
                    if i == j and a == b:
                        continue
                    if H is not None:
                        d = pbc_dist(fr[i], fr[j], H, Hinv)
                    else:
                        d = float(np.linalg.norm(fr[i] - fr[j]))
                    if d < rmax:
                        bin_idx = int(d / dr)
                        if bin_idx < nbins:
                            hist[(a, b)][bin_idx] += 1
    # 归一化**必须放在帧循环之外**：先把所有帧的计数累加，最后统一除一次。
    #
    # 修 bug 记录：这两行原来在 `for fi in range(M)` 的**循环体内**，于是每读
    # 一帧就把"历史累计直方图"整体再除一次 norm，效果是第 k 帧的贡献被除了
    # norm**(M-k+1) 次 —— 帧数越多偏得越狠。实测真实 2535 帧轨迹：g_H-O 峰值
    # 算出 0.0707（应为 ~117），配位数 0.0024（应为 1.0000，因为每个 H 恰好
    # 连 1 个 O），**偏 1659 倍**。单帧体系不会暴露（除一次正好），所以原有的
    # 单帧合成数据 harness 一直是绿的 —— 这个 bug 是靠真实多帧轨迹才抓出来的。
    for (a, b) in pairs:
        ia = idx_by_elem.get(a, [])
        ib = idx_by_elem.get(b, [])
        if not ia or not ib:
            continue
        # 归一化因子: 该对 (A 原子数 * 帧数) * 4πr² dr * rho_b
        norm = len(ia) * M * 4 * math.pi * r_centers**2 * dr * (len(ib) / V)
        hist[(a, b)] = hist[(a, b)] / norm
    prefix = out_prefix(args)
    rows = [["r[A]"] + [f"g_{a}-{b}" for (a, b) in pairs]]
    for k in range(nbins):
        rows.append([f"{r_centers[k]:.4f}"] + [f"{hist[p][k]:.6f}" for p in pairs])
    csv = prefix + "_rdf.csv"
    write_csv(csv, rows[0], rows[1:])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for (a, b) in pairs:
        ax.plot(r_centers, hist[(a, b)], lw=1.2, label=f"{a}-{b}")
    ax.set_xlabel("r [Angstrom]")
    ax.set_ylabel("g(r)")
    ax.set_title(f"Radial distribution function ({cell_note})")
    ax.legend()
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_rdf.png")
    print(f"RDF: {len(pairs)} pair(s), rmax={rmax} A, {nbins} bins -> {prefix}_rdf.png")
    return 0


# --------------------------------------------------------------------------
# msd
# --------------------------------------------------------------------------
def unwrap_traj_frac(frames, H):
    """unwrap **并返回每帧质心的晶格坐标（分数坐标）**，用于事后扣除整体平动。

    为什么要多返回这一项：unwrapping 会把"骨架的整体漂移"也忠实地累加进
    连续坐标里（这本来是对的，否则跨边界的原子会跳）。但讲师的口径是
    **算 MSD 前要把整个晶胞的整体平动消除掉**（vn2 C-02 / G-01），
    所以需要知道每帧被 unwrap 了多少格矢，事后才能把"只属于骨架的平移"减掉。
    """
    M, N, _ = frames.shape
    un = np.zeros_like(frames)
    shift = np.zeros((M, 3))
    un[0] = frames[0]
    if H is None:
        return frames.copy(), shift
    Hinv = np.linalg.inv(H)
    for k in range(1, M):
        d = frames[k] - un[k - 1]
        f = Hinv @ d.T
        f -= np.round(f)
        un[k] = un[k - 1] + (H @ f).T
        shift[k] = shift[k - 1] + f.sum(axis=1)
    return un, shift


def kabsch_rotate(cur, ref):
    """Kabsch 算法：求把 `cur` 叠到 `ref` 的最优刚体旋转矩阵（零依赖，只用 SVD）。

    返回 3×3 ndarray（行列式强制为 +1 —— 反射不是刚体运动）。
    原子数 < 2 时无旋转可言，返回单位矩阵。
    """
    if cur.shape[0] < 2:
        return np.eye(3)
    P = cur - cur.mean(axis=0)
    Q = ref - ref.mean(axis=0)
    Hh = P.T @ Q                       # 3×3 协方差
    U, _s, Vt = np.linalg.svd(Hh)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1.0, 1.0, d if d != 0 else 1.0])
    return Vt.T @ D @ U.T


def align_traj(frames, un, ref_idx, H):
    """对每帧相对参考帧做**刚体对齐**（消除骨架整体平动 + 转动）。

    `ref_idx` 是**参考组**（VMD 的 `Reference mol`）：默认取"被跟踪物种以外的
    骨架原子"（对齐后骨架不动，正好看被跟踪物种自己的运动）；也可以由用户
    显式指定。逐步做什么 —— 与 VMD `m2msd` 的 `align` 同语义：

      1. **消平动**：取参考组每帧的质心 `com_k`，把**整帧所有原子**平移 `−com_k`
         （这一步就是讲师说的"消除整个晶胞整体的它的这个平动"）；
      2. **消转动**：对参考组做 Kabsch（`kabsch_rotate`）求最优刚体旋转 `R_k`，
         再把整帧旋转 `R_k`，使参考组每帧姿态都回到第 0 帧的姿态。

    ⚠️ **不要**试图去"撤销 unwrap 加回去的整数格矢"——`unwrap_traj_frac` 的
    整数格矢位移是**让轨迹连续所必需的**，不是漂移；减去它反而会把参考组拆散。
    （本轮第一版就是这么写的：对刚体参考组残余漂移高达 60 Å，等于没对齐。）

    返回 ``(aligned_frames, info)``；info 里带参考组残余漂移，供打印对比。
    """
    M = frames.shape[0]
    r = np.array(sorted(ref_idx), dtype=int)
    n_sel = len(r)
    if n_sel == 0:
        raise ValueError("align_traj 的参考组为空 —— 调用方必须先拦掉这种输入"
                         "（否则 MSD 会静默变成 nan）")
    com = un[:, r, :].mean(axis=1)          # (M, 3)
    out = un - com[:, None, :]              # 第 1 步：消平动（对全部原子）
    if n_sel >= 2:
        ref_pos = out[0][r]                 # 参考帧的参考组（已居中）
        for k in range(M):
            R = kabsch_rotate(out[k][r], ref_pos)
            out[k] = out[k] @ R.T           # 第 2 步：消转动（对全部原子）
    resid = out[:, r, :].mean(axis=1) - out[0, r, :].mean(axis=0)
    return out, {
        "n_ref": n_sel,
        "ref_residual_drift_A": float(np.max(np.linalg.norm(resid, axis=1))),
        "translation_removed_A": float(np.max(np.linalg.norm(
            com - com[0], axis=1))),
    }


def compute_msd(frames, H, sel, dim, align_ref_idx=None):
    un, _shift = unwrap_traj_frac(frames, H)
    info = None
    if align_ref_idx is not None:
        un, info = align_traj(frames, un, align_ref_idx, H)
    if sel is not None:
        un = un[:, sel, :]
    M = un.shape[0]
    msd = np.zeros(M)
    # 多时间原点平均
    for dt in range(1, M):
        disp = un[dt:] - un[:-dt]
        sq = np.sum(disp**2, axis=2)
        msd[dt] = sq.mean()
    msd[0] = 0.0
    return msd, info  # in Angstrom^2


def _resolve_align(align, elements):
    """把 `--align` 的取值解析成**参考组**原子索引（VMD 的 `Reference mol`）。

    * ``None``         → 不做对齐（向后兼容的默认）
    * ``"rest"``       → **所有原子**（= 消掉整帧的平动/转动；只有 N=1 时才与
                         `--sel` 同义）
    * 其它字符串        → 同 `--sel` 的语法（元素符号 / `1..10` 索引区间）。
                         ⚠️ 若与 `--sel` 指向同一批原子，等于"把被跟踪物种自己
                         钉住"，MSD 会趋零 —— 会打一条显式警告。
    """
    if align is None:
        return None, None
    if align.lower() in ("rest", "all"):
        return list(range(len(elements))), "全体系"
    idx = _parse_sel(align, elements)
    if idx is None or len(idx) == 0:
        # 元素符号不在体系里 / 区间越界 ⇒ 按"骨架 = 除 --sel 以外"处理
        return None, "无法解析"
    return sorted(set(idx)), align


def _parse_sel(sel, elements):
    if sel is None:
        return None
    if re.fullmatch(r"[A-Z][a-z]?", sel):
        return [i for i, e in enumerate(elements) if e == sel]
    # 索引区间 "1..10 20..25"
    idx = []
    for part in sel.split():
        if ".." in part:
            a, b = part.split("..")
            idx += list(range(int(a) - 1, int(b)))
        else:
            idx.append(int(part) - 1)
    return idx


def _msd_sel_arg(args, elements):
    """`--sel` + `--align` 的联合解析（msd / diffusion / vacf 共用口径）。

    返回 ``(sel_idx, ref_idx, notes)``；`notes` 是给人看的中文提示列表。
    """
    notes = []
    sel = _parse_sel(args.sel, elements) if getattr(args, "sel", None) else None
    if getattr(args, "sel", None) and not sel:
        notes.append("--sel {!r} 在这个轨迹里没匹配到任何原子，已按**全原子**处理".format(
            args.sel))
    align = getattr(args, "align", None)
    ref = None
    if align is not None:
        a = str(align).strip()
        if a.lower() in ("rest", "all"):
            if sel is None:
                ref = list(range(len(elements)))
                notes.append("--align rest：对**全体系**做刚体对齐（N={}）".format(
                    len(elements)))
            else:
                ref = [k for k in range(len(elements)) if k not in set(sel)]
                if ref:
                    notes.append("--align rest：参考组 = 除 --sel 选中原子以外的 "
                                 "{} 个骨架原子".format(len(ref)))
                else:
                    # 退化：--sel 把**所有**原子都选走了 ⇒ 参考组是空集。
                    # 早期版本会让 align_traj 对空数组求均值 ⇒ MSD 全 nan，
                    # 而退出码仍是 0、CSV 里写满 "nan" —— **静默错值**。
                    print("", file=sys.stderr)
                    print("[WARN] --align rest 的参考组为空（--sel {!r} 选中了全部 "
                          "{} 个原子）⇒ **不做对齐**。".format(
                              args.sel, len(elements)), file=sys.stderr)
                    print("       想消整体平动请写 `--align all`；"
                          "想以骨架为参考请让 `--sel` 只选被跟踪的物种。",
                          file=sys.stderr)
                    ref = None
                    notes.append("--align rest 退化为不对齐（参考组为空）")
        else:
            ref = _parse_sel(a, elements)
            if not ref:
                notes.append("--align {!r} 没匹配到原子，**未做对齐**".format(a))
                ref = None
            else:
                notes.append("--align {}：参考组 {} 个原子".format(a, len(ref)))
        if ref is not None and sel is not None and set(ref) == set(sel):
            print("", file=sys.stderr)
            print("[WARN] --align 的参考组与 --sel 的跟踪组**是同一批原子** —— "
                  "MSD 会被压到 ≈0。", file=sys.stderr)
            print("       通常想要的是「骨架对齐、看骨架里某种离子自己怎么动」："
                  "用 `--align rest` 或显式给骨架元素。", file=sys.stderr)
    return sel, ref, notes


def cmd_msd(args):
    elements, frames, times, _ = read_xyz(args.traj)
    H = get_cell(args)
    sel, ref, notes = _msd_sel_arg(args, elements)
    for n in notes:
        print("  " + n)
    msd, info = compute_msd(frames, H, sel, args.dim, ref)
    if info:
        print("  对齐后参考组残余漂移 = {:.4f} Å（扣掉的平动最大 {:.4f} Å）".format(
            info["ref_residual_drift_A"], info["translation_removed_A"]))
    if times is not None:
        t = times
    elif len(frames) > 1:
        dt = args.dt if args.dt else 1.0
        t = np.arange(len(frames)) * dt
    else:
        t = np.arange(len(frames))
    prefix = out_prefix(args)
    csv = prefix + "_msd.csv"
    write_csv(csv, "time[ps],MSD[A^2]", [[t[k], msd[k]] for k in range(len(t))])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(t, msd, lw=1.2)
    ax.set_xlabel("time [ps]")
    ax.set_ylabel("MSD [Angstrom^2]")
    tag = " + align({})".format(args.align) if ref is not None else ""
    ax.set_title(f"Mean square displacement (dim={args.dim}){tag}")
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_msd.png")
    print(f"MSD: {len(t)} frames -> {prefix}_msd.png")
    return 0


def cmd_diffusion(args):
    elements, frames, times, _ = read_xyz(args.traj)
    H = get_cell(args)
    sel, ref, notes = _msd_sel_arg(args, elements)
    for n in notes:
        print("  " + n)
    msd, info = compute_msd(frames, H, sel, args.dim, ref)
    if times is not None:
        t = times
    else:
        dt = args.dt if args.dt else 1.0
        t = np.arange(len(frames)) * dt
    n = len(t)
    lo = int(n * args.fit_lo)
    hi = int(n * args.fit_hi)
    lo = max(lo, 1)
    if hi <= lo:
        hi = n
    slope, intercept = np.polyfit(t[lo:hi], msd[lo:hi], 1)
    d_aps = slope / (2 * args.dim)            # Angstrom^2 / ps
    d_cgs = d_aps * 1e-4                       # cm^2 / s
    # 对齐前/后的 D 对比（G-01 明确要求：让"漂移是否显著"一眼可见）
    d_raw = None
    if ref is not None:
        msd_raw, _ = compute_msd(frames, H, sel, args.dim, None)
        s_raw, _i = np.polyfit(t[lo:hi], msd_raw[lo:hi], 1)
        d_raw = s_raw / (2 * args.dim)
    prefix = out_prefix(args)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(t, msd, lw=1.2, label="MSD")
    ax.plot(t[lo:hi], slope * t[lo:hi] + intercept, "r--", label=f"fit (D={d_aps:.4f} A^2/ps)")
    ax.set_xlabel("time [ps]")
    ax.set_ylabel("MSD [Angstrom^2]")
    tag = " + align({})".format(args.align) if ref is not None else ""
    ax.set_title(f"Diffusion coefficient (dim={args.dim}){tag}")
    ax.legend()
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_diffusion.png")
    txt = prefix + "_diffusion.txt"
    with open(txt, "w", encoding="utf-8") as f:
        f.write(f"D = {d_aps:.6f} Angstrom^2/ps = {d_cgs:.6e} cm^2/s\n")
        f.write(f"fit range: steps {lo}..{hi} (t={t[lo]:.3f}..{t[hi-1]:.3f} ps)\n")
        f.write(f"MSD slope = {slope:.6f} Angstrom^2/ps\n")
        f.write(f"align = {args.align if ref is not None else 'off'}\n")
        if d_raw is not None:
            f.write(f"D(no align) = {d_raw:.6f} Angstrom^2/ps\n")
            f.write(f"align/raw ratio = {d_aps / d_raw if d_raw else float('nan'):.4f}\n")
    print(f"Diffusion: D = {d_aps:.6f} A^2/ps = {d_cgs:.4e} cm^2/s  (fit {lo}..{hi})")
    if d_raw is not None:
        print(f"  对齐前 D = {d_raw:.6f} A^2/ps  →  对齐后 D = {d_aps:.6f} A^2/ps"
              f"  (比值 {d_aps / d_raw if d_raw else float('nan'):.4f})")
        print("  比值明显 ≠1 ⇒ 骨架整体平动/转动原本在污染 D；"
              "也可以据此判断模型是不是太小")
        if info:
            print("  对齐后参考组残余漂移 = {:.4f} Å".format(info["ref_residual_drift_A"]))
    print(f"written: {prefix}_diffusion.png + .txt")
    return 0


# --------------------------------------------------------------------------
# bond / angle / dihedral
# --------------------------------------------------------------------------
def cmd_bond(args):
    _, frames, times, _ = read_xyz(args.traj)
    i, j = args.i - 1, args.j - 1
    dist = np.linalg.norm(frames[:, i] - frames[:, j], axis=1)
    prefix = out_prefix(args)
    csv = prefix + "_bond.csv"
    write_csv(csv, "step,distance[A]", [[k + 1, dist[k]] for k in range(len(dist))])
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(range(1, len(dist) + 1), dist, lw=1.0)
    ax[0].set_xlabel("step"); ax[0].set_ylabel("bond [A]")
    ax[0].set_title(f"bond {args.i}-{args.j}")
    ax[0].grid(alpha=0.3)
    ax[1].hist(dist, bins=args.hbins, color="steelblue", alpha=0.8)
    ax[1].set_xlabel("bond [A]"); ax[1].set_ylabel("count")
    ax[1].set_title("distribution")
    save_png(fig, prefix + "_bond.png")
    print(f"bond {args.i}-{args.j}: mean={dist.mean():.4f} A, std={dist.std():.4f} -> {prefix}_bond.png")
    return 0


def _angle(v1, v2):
    c = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    c = max(-1.0, min(1.0, c))
    return math.degrees(math.acos(c))


def cmd_angle(args):
    _, frames, _, _ = read_xyz(args.traj)
    i, j, k = args.i - 1, args.j - 1, args.k - 1
    ang = np.array([_angle(frames[m, i] - frames[m, j], frames[m, k] - frames[m, j])
                    for m in range(len(frames))])
    prefix = out_prefix(args)
    csv = prefix + "_angle.csv"
    write_csv(csv, "step,angle[deg]", [[m + 1, ang[m]] for m in range(len(ang))])
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(range(1, len(ang) + 1), ang, lw=1.0)
    ax[0].set_xlabel("step"); ax[0].set_ylabel("angle [deg]")
    ax[0].set_title(f"angle {args.i}-{args.j}-{args.k}")
    ax[0].grid(alpha=0.3)
    ax[1].hist(ang, bins=args.hbins, color="seagreen", alpha=0.8)
    ax[1].set_xlabel("angle [deg]"); ax[1].set_ylabel("count")
    ax[1].set_title("distribution")
    save_png(fig, prefix + "_angle.png")
    print(f"angle {args.i}-{args.j}-{args.k}: mean={ang.mean():.2f} deg -> {prefix}_angle.png")
    return 0


def _dihedral(p0, p1, p2, p3):
    b0 = p0 - p1
    b1 = p2 - p1
    b2 = p3 - p2
    n1 = np.cross(b0, b1)
    n2 = np.cross(b1, b2)
    m1 = np.cross(n1, b1 / np.linalg.norm(b1))
    x = np.dot(n1, n2)
    y = np.dot(m1, n2)
    return math.degrees(math.atan2(y, x))


def cmd_dihedral(args):
    _, frames, _, _ = read_xyz(args.traj)
    i, j, k, l = args.i - 1, args.j - 1, args.k - 1, args.l - 1
    dh = np.array([_dihedral(frames[m, i], frames[m, j], frames[m, k], frames[m, l])
                   for m in range(len(frames))])
    prefix = out_prefix(args)
    csv = prefix + "_dihedral.csv"
    write_csv(csv, "step,dihedral[deg]", [[m + 1, dh[m]] for m in range(len(dh))])
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(range(1, len(dh) + 1), dh, lw=1.0)
    ax[0].set_xlabel("step"); ax[0].set_ylabel("dihedral [deg]")
    ax[0].set_title(f"dihedral {args.i}-{args.j}-{args.k}-{args.l}")
    ax[0].grid(alpha=0.3)
    ax[1].hist(dh, bins=args.hbins, color="indianred", alpha=0.8)
    ax[1].set_xlabel("dihedral [deg]"); ax[1].set_ylabel("count")
    ax[1].set_title("distribution")
    save_png(fig, prefix + "_dihedral.png")
    print(f"dihedral {args.i}-{args.j}-{args.k}-{args.l}: mean={dh.mean():.2f} deg -> {prefix}_dihedral.png")
    return 0


# --------------------------------------------------------------------------
# pdos
# --------------------------------------------------------------------------
def _pdos_files(path):
    if os.path.isdir(path):
        import glob
        return sorted(glob.glob(os.path.join(path, "*.pdos")))
    return [path]


def _parse_pdos_file(fpath):
    """返回 (eig_eV[MO], occ[MO], weights[MO, nchan])。"""
    rows = []
    for ln in open(fpath, encoding="utf-8", errors="ignore"):
        if ln.startswith("#") or not ln.strip():
            continue
        parts = ln.split()
        try:
            nums = [float(x) for x in parts]
        except ValueError:
            continue
        if len(nums) < 3:
            continue
        rows.append(nums)
    if not rows:
        return None
    arr = np.array(rows)
    eig = arr[:, 0] * 27.211386245988  # a.u. -> eV
    occ = arr[:, 1]
    weights = arr[:, 2:]              # 各角动量通道投影权重
    return eig, occ, weights


def cmd_pdos(args):
    files = _pdos_files(args.pdos)
    if not files:
        print("ERROR: 未找到 .pdos 文件。")
        return 1
    sigma = args.broaden
    dE = args.de
    all_eig = []
    occ_all = []
    w_all = []
    kind_all = []
    for f in files:
        p = _parse_pdos_file(f)
        if p is None:
            continue
        eig, occ, w = p
        all_eig.append(eig)
        occ_all.append(occ)
        w_all.append(w)
        m = re.search(r"-(.+?)_k\d+-\d+\.pdos", os.path.basename(f))
        kind = m.group(1) if m else os.path.basename(f)
        kind_all.extend([kind] * len(eig))
    all_eig = np.concatenate(all_eig)
    occ_all = np.concatenate(occ_all)
    w_all = np.concatenate(w_all, axis=0)
    # Fermi 参考
    if args.fermi is not None:
        fermi = args.fermi
    else:
        # 占据跨越 0.5 处
        order = np.argsort(all_eig)
        eo = all_eig[order]
        oo = occ_all[order]
        fermi = eo[np.argmin(np.abs(oo - 0.5))]
    e0 = all_eig.min() - 1.0
    e1 = all_eig.max() + 1.0
    grid = np.arange(e0, e1, dE)
    total = np.zeros_like(grid)
    # 总 DOS
    for m in range(len(all_eig)):
        total += occ_all[m] * np.sum(w_all[m]) * np.exp(-((grid - all_eig[m])**2) / (2 * sigma**2))
    total /= sigma * math.sqrt(2 * math.pi)
    # 按 kind 分解
    kinds = sorted(set(kind_all))
    per_kind = {k: np.zeros_like(grid) for k in kinds}
    for m in range(len(all_eig)):
        k = kind_all[m]
        per_kind[k] += occ_all[m] * np.sum(w_all[m]) * np.exp(-((grid - all_eig[m])**2) / (2 * sigma**2))
    for k in per_kind:
        per_kind[k] /= sigma * math.sqrt(2 * math.pi)
    E = grid - fermi
    prefix = out_prefix(args)
    header = "E-Ef[eV],total_DOS"
    rows = [[f"{E[i]:.4f}", f"{total[i]:.6e}"] for i in range(len(grid))]
    for k in kinds:
        header += f",{k}"
        for i in range(len(grid)):
            rows[i].append(f"{per_kind[k][i]:.6e}")
    csv = prefix + "_pdos.csv"
    write_csv(csv, header, rows)
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(E, total, "k-", lw=1.3, label="total")
    for k in kinds:
        ax.plot(E, per_kind[k], lw=1.0, label=k)
    ax.axvline(0, color="gray", ls="--", lw=0.8)
    ax.set_xlabel("E - E_F [eV]")
    ax.set_ylabel("DOS")
    ax.set_title(f"PDOS (broaden={sigma} eV)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_pdos.png")
    print(f"PDOS: {len(files)} file(s), Fermi@={fermi:.4f} eV, kinds={kinds} -> {prefix}_pdos.png")
    return 0


# --------------------------------------------------------------------------
# adf (angular distribution)
# --------------------------------------------------------------------------
def cmd_adf(args):
    elements, frames, _, _ = read_xyz(args.traj)
    H = get_cell(args)
    rcut = args.rcut
    center = args.center
    idx_center = [i for i, e in enumerate(elements) if e == center]
    if not idx_center:
        print(f"ERROR: 体系中没有 {center} 原子。")
        return 1
    nbins = args.bins
    hist = np.zeros(nbins)
    M = len(frames)
    if H is not None:
        Hinv = np.linalg.inv(H)
    for fi in range(M):
        fr = frames[fi]
        for ic in idx_center:
            neigh = []
            for j in range(len(fr)):
                if j == ic:
                    continue
                if H is not None:
                    d = pbc_dist(fr[ic], fr[j], H, Hinv)
                else:
                    d = float(np.linalg.norm(fr[ic] - fr[j]))
                if d < rcut:
                    neigh.append(fr[j] - fr[ic])
            for a in range(len(neigh)):
                for b in range(a + 1, len(neigh)):
                    ang = _angle(neigh[a], neigh[b])
                    bin_idx = min(int(ang / 180.0 * nbins), nbins - 1)
                    hist[bin_idx] += 1
    prefix = out_prefix(args)
    ang_axis = np.linspace(0, 180, nbins, endpoint=False)
    csv = prefix + "_adf.csv"
    write_csv(csv, "angle[deg],count", [[f"{ang_axis[k]:.2f}", hist[k]] for k in range(nbins)])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(ang_axis, hist, lw=1.2)
    ax.set_xlabel("angle [deg]")
    ax.set_ylabel("count")
    ax.set_title(f"Angular distribution (center={center}, rcut={rcut} A)")
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_adf.png")
    print(f"ADF: center={center}, rcut={rcut} A -> {prefix}_adf.png")
    return 0


# --------------------------------------------------------------------------
# cn (coordination number, from rdf integral)
# --------------------------------------------------------------------------
def cmd_cn(args):
    # 复用 rdf 计算, 但直接输出配位数
    elements, frames, _, _ = read_xyz(args.traj)
    H = get_cell(args)
    pairs = _select_pairs(elements, args.pairs)
    rmax = args.rcut
    nbins = args.bins
    dr = rmax / nbins
    r_centers = np.linspace(dr / 2, rmax - dr / 2, nbins)
    M, N, _ = frames.shape
    idx_by_elem = {e: [i for i, x in enumerate(elements) if x == e] for e in set(elements)}
    if H is not None:
        Hinv = np.linalg.inv(H)
        V = abs(np.linalg.det(H))
    else:
        lo = frames.min(axis=(0, 1)); hi = frames.max(axis=(0, 1))
        V = float(np.prod(hi - lo))
    results = {}
    for (a, b) in pairs:
        ia = idx_by_elem.get(a, []); ib = idx_by_elem.get(b, [])
        if not ia or not ib:
            continue
        na, nb = len(ia), len(ib)
        rho_b = nb / V
        hist = np.zeros(nbins)
        for fi in range(M):
            fr = frames[fi]
            for i in ia:
                for j in ib:
                    if i == j and a == b:
                        continue
                    d = pbc_dist(fr[i], fr[j], H, Hinv) if H is not None else float(np.linalg.norm(fr[i] - fr[j]))
                    if d < rmax:
                        bin_idx = int(d / dr)
                        if bin_idx < nbins:
                            hist[bin_idx] += 1
        cn = np.sum(hist * 4 * math.pi * r_centers**2 * dr) / (na * M)
        results[f"{a}-{b}"] = cn
    prefix = out_prefix(args)
    txt = prefix + "_cn.txt"
    with open(txt, "w", encoding="utf-8") as f:
        for k, v in results.items():
            f.write(f"CN({k}) within {args.rcut} A = {v:.4f}\n")
    print("Coordination numbers:")
    for k, v in results.items():
        print(f"  CN({k}) <= {args.rcut} A = {v:.4f}")
    print(f"written: {txt}")
    return 0


# --------------------------------------------------------------------------
# zprofile
# --------------------------------------------------------------------------
def cmd_zprofile(args):
    elements, frames, _, _ = read_xyz(args.traj)
    H = get_cell(args)
    n_all = len(elements)
    if getattr(args, "sel", None):
        idx = _parse_sel(args.sel, elements)
        if not idx:
            print("  [warn] --sel {!r} 没匹配到任何原子，已按**全原子**处理".format(
                args.sel), file=sys.stderr)
        else:
            frames = frames[:, idx, :]
            print("  zprofile --sel {} ⇒ {} / {} 个原子".format(
                args.sel, len(idx), n_all))
    if H is not None:
        # 横截面积 = |a x b|
        cross = np.cross(H[0], H[1])
        area = float(np.linalg.norm(cross))
        zs = frames[:, :, 2]
        zmin, zmax = 0.0, float(np.linalg.norm(H[2]))
    else:
        zs = frames[:, :, 2]
        zmin, zmax = zs.min(), zs.max()
        area = 1.0
    nbins = args.bins
    hist, edges = np.histogram(zs.ravel(), bins=nbins, range=(zmin, zmax))
    width = (zmax - zmin) / nbins
    dens = hist / (area * width * len(frames))
    zc = 0.5 * (edges[:-1] + edges[1:])
    prefix = out_prefix(args)
    csv = prefix + "_zprofile.csv"
    write_csv(csv, "z[A],density[1/A^3]", [[f"{zc[k]:.4f}", dens[k]] for k in range(nbins)])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(zc, dens, lw=1.3)
    ax.set_xlabel("z [Angstrom]")
    ax.set_ylabel("number density [1/A^3]")
    tag = "  [sel={}]".format(args.sel) if getattr(args, "sel", None) else ""
    ax.set_title("Density profile along z" + tag)
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_zprofile.png")
    print(f"z-profile: {nbins} bins -> {prefix}_zprofile.png")
    return 0


# --------------------------------------------------------------------------
# vacf / ir / power
# --------------------------------------------------------------------------
def _velocity_sel(vel, elements, sel_arg):
    """把速度帧按 `--sel` 裁到子集。返回 ``(vel_sub, n_sel, note)``。

    ⚠️ 归一化口径（vn2 G-02 明确要求）：加选区后 `compute_vacf()` 的分母用的
    必须是**选中原子数**，否则曲线幅值语义会变（C(0) 仍是 1，但收敛后的
    振荡强度不再可比）。
    """
    if not sel_arg:
        return vel, vel.shape[1], None
    idx = _parse_sel(sel_arg, elements)
    if not idx:
        return vel, vel.shape[1], ("--sel {!r} 没匹配到任何原子，已按**全原子**处理"
                                   .format(sel_arg))
    return vel[:, idx, :], len(idx), ("--sel {} ⇒ {} 个原子（归一分母同步改为该数）"
                                      .format(sel_arg, len(idx)))


def _read_velocities(args):
    """返回速度帧 (M,N,3)、时间数组、元素符号。优先 --vel; 否则用 --traj 位置差分近似。"""
    if getattr(args, "vel", None):
        elements, vel, times, _ = read_xyz(args.vel)
        return vel, times, elements
    # 位置差分近似
    elements, frames, times, _ = read_xyz(args.traj)
    if times is not None and len(times) > 1:
        dt = float(np.median(np.diff(times)))
    else:
        dt = args.dt if args.dt else 1.0
    vel = np.zeros_like(frames)
    vel[1:-1] = (frames[2:] - frames[:-2]) / (2 * dt)
    vel[0] = vel[1]
    vel[-1] = vel[-2]
    print("NOTE: 无速度文件, 用位置中心差分近似 v≈Δr/Δt (精度有限)。")
    return vel, times, elements


def compute_vacf(vel):
    M, N, _ = vel.shape
    vacf = np.zeros(M)
    for dt in range(M):
        a = vel[dt:]
        b = vel[:M - dt]
        c = np.sum(a * b)  # sum over atoms & components
        vacf[dt] = c / (N * (M - dt))
    vacf[0] = vacf[0] if vacf[0] != 0 else 1.0
    vacf /= vacf[0]
    return vacf


def cmd_vacf(args):
    vel, times, elements = _read_velocities(args)
    vel, n_sel, note = _velocity_sel(vel, elements, getattr(args, "sel", None))
    if note:
        print("  " + note)
    vacf = compute_vacf(vel)
    if times is not None:
        t = times
    else:
        dt = args.dt if args.dt else 1.0
        t = np.arange(len(vacf)) * dt
    prefix = out_prefix(args)
    csv = prefix + "_vacf.csv"
    write_csv(csv, "time[ps],VACF", [[t[k], vacf[k]] for k in range(len(t))])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(t, vacf, lw=1.2)
    ax.set_xlabel("time [ps]")
    ax.set_ylabel("VACF (norm.)")
    ax.set_title("Velocity autocorrelation function" +
                 ("  [sel={}]".format(args.sel) if args.sel else ""))
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_vacf.png")
    print(f"VACF: {len(t)} points, {n_sel} atoms -> {prefix}_vacf.png")
    return 0


def cmd_ir(args):
    vel, times, elements = _read_velocities(args)
    vel, n_sel, note = _velocity_sel(vel, elements, getattr(args, "sel", None))
    if note:
        print("  " + note)
    vacf = compute_vacf(vel)
    if times is not None and len(times) > 1:
        dt = float(np.median(np.diff(times)))
    else:
        dt = args.dt if args.dt else 1.0
    n = len(vacf)
    # 加 Hanning 窗减少泄漏
    window = np.hanning(n)
    vacf_w = vacf * window
    spec = np.abs(np.fft.rfft(vacf_w))
    freq_ps = np.fft.rfftfreq(n, d=dt)  # 1/ps
    freq_cm = freq_ps * 33.356  # 1/ps -> cm^-1  (c=29.979 cm/ps)
    prefix = out_prefix(args)
    csv = prefix + "_ir.csv"
    write_csv(csv, "freq[1/ps],freq[cm-1],intensity",
              [[f"{freq_ps[k]:.6f}", f"{freq_cm[k]:.4f}", spec[k]] for k in range(len(spec))])
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(freq_cm, spec, lw=1.2, color="purple")
    ax.set_xlabel("wavenumber [cm^-1]")
    ax.set_ylabel("intensity (a.u.)")
    ax.set_title("IR / vibrational DOS (FFT of VACF)" +
                 ("  [sel={}]".format(args.sel) if args.sel else ""))
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_ir.png")
    peak = freq_cm[1 + np.argmax(spec[1:])]
    print(f"IR/VDoS: peak ≈ {peak:.1f} cm^-1 ({n_sel} atoms) -> {prefix}_ir.png")
    return 0


def cmd_power(args):
    return cmd_ir(args)


# ==========================================================================
# cube 类后处理底座（Gaussian cube 解析 + 平面平均）
# ==========================================================================
# 为什么要有这一整块：`bader` 虽然吃 cube，但它只把 cube 转给外部二进制、
# 再解析 `ACF.dat`，**本身不做任何 cube 数学**。于是课程"电子结构十项"里凡是
# 需要读格点数据的（ELF / 电荷密度差分 / 平面平均 / 静电势 / 功函 / 电极电势）
# 全部无工具支撑。下面的 `_read_cube()` 是这些子命令的**共同底座**。
#
# Gaussian cube 格式（Gaussian / CP2K 通用；CP2K 由 `&PRINT/&E_DENSITY_CUBE`
# 或 `V_HARTREE_CUBE` / `ELF_CUBE` / `MO_CUBES` 发射）：
#
#   第 1 行   注释（CP2K 写 "CP2K Cube file..."）
#   第 2 行   注释
#   第 3 行   natoms  ox oy oz
#             natoms > 0  → 原子坐标以 **bohr** 计
#             natoms < 0  → 原子坐标以 **Å** 计（个数取绝对值）
#   接下来 natoms 行：  Z  q  x  y  z
#   再 3 行：           n  ax ay az      （n<0 → 该轴步进矢量以 Å 计；n = 格点数）
#   其余：体数据，**z 最快、y 次之、x 最慢**（x 是最外层慢循环）
#
# ⚠️ CP2K 的 `STRIDE`（官方默认 `2 2 2`）会让 cube 里的格点**不等于 FFT 网格**，
#    但**沿轴的位置坐标仍由"原点 + 步进矢量"给出** —— 所以平面平均的横坐标
#    必须按 `origin + k·step` 算，**不许**拿 `CUTOFF` 反推网格数（G-03 的原话）。

_CUBE_AXIS_INFO = {
    "x": (0, (1, 2), "y-z"),
    "y": (1, (0, 2), "x-z"),
    "z": (2, (0, 1), "x-y"),
    "xy": (2, (0, 1), "x-y"),
    "xz": (1, (0, 2), "x-z"),
    "yz": (0, (1, 2), "y-z"),
}


def _cube_bad(path, step, detail):
    """cube 解析失败的统一出口：**说清失败在哪一步**（G-03 的稳健性要求）。

    返回 ``(None, 中文错误串)``，由调用方打印后 ``return 1``。
    """
    return None, ("cube 解析失败于【{}】这一步：\n"
                  "  文件: {}\n"
                  "  详情: {}\n"
                  "  Gaussian cube 的头结构: 2 行注释 -> 'natoms ox oy oz' -> "
                  "natoms 行原子 -> 3 行'(n) ax ay az' -> 体数据(x 最慢/z 最快)".format(
                      step, path, detail))


def read_cube(path):
    """零依赖读 Gaussian cube。返回 ``(info, None)`` 或 ``(None, 中文错误串)``。

    info 是 dict:
      comment  : list[str]        前两行注释
      atoms    : np.ndarray (nat,5) [Z, q, x_ang, y_ang, z_ang]
      origin   : np.ndarray (3,)   原点（Å）
      npts     : tuple[int,int,int] 各轴格点数
      steps    : np.ndarray (3,3)  每轴步进矢量（Å）
      data     : np.ndarray (nx,ny,nz)  **索引语义 [ix, iy, iz]**
      pos      : list[np.ndarray]  每轴的格点坐标（Å；= origin 分量 + k·step 分量）
      volume   : float             单格点体积（Å³）= |det(steps)|
    """
    if not os.path.exists(path):
        return None, ("找不到 cube 文件：{}\n"
                      "  请确认路径；cube 由 CP2K 的 `&PRINT/&E_DENSITY_CUBE`、"
                      "`V_HARTREE_CUBE`、`ELF_CUBE`、`MO_CUBES` 发射".format(path))
    if os.path.isdir(path):
        return None, "期望 cube 文件但给的是目录：{}".format(path)
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        return None, "cube 文件读不出来：{}\n  {}".format(path, exc)
    # cube 是纯 ASCII；用 errors='replace' 保证不因个别脏字节崩掉
    lines = raw.decode("utf-8", errors="replace").splitlines()
    if len(lines) < 6:
        return _cube_bad(path, "读前 6 行", "文件只有 {} 行，连 cube 头都放不下".format(len(lines)))
    comment = [lines[0], lines[1]]
    # --- 第 3 行: natoms ox oy oz ---
    parts = lines[2].split()
    if len(parts) < 4:
        return _cube_bad(path, "第 3 行 natoms ox oy oz",
                         "期望 ≥4 个数，实得 {!r}".format(lines[2][:80]))
    try:
        natoms = int(float(parts[0]))
        origin = np.array([float(x) for x in parts[1:4]], dtype=float)
    except ValueError:
        return _cube_bad(path, "第 3 行 natoms ox oy oz",
                         "非数值 {!r}".format(lines[2][:80]))
    bohr_coords = natoms < 0            # Gaussian 约定：负的 natoms ⇒ 坐标以 Å 计
    natoms = abs(natoms)
    if natoms > 10_000_000:
        return _cube_bad(path, "第 3 行 natoms", "原子数 {} 不合理".format(natoms))
    if bohr_coords:
        origin = origin * BOHR_ANG
    # --- natoms 行原子 ---
    i = 3
    atoms = []
    for k in range(natoms):
        if i >= len(lines):
            return _cube_bad(path, "读原子行（第 {} 个原子）".format(k + 1),
                             "文件提前结束")
        p = lines[i].split()
        i += 1
        if len(p) < 5:
            return _cube_bad(path, "读原子行（第 {} 个原子）".format(k + 1),
                             "期望 5 列 'Z q x y z'，实得 {!r}".format(lines[i - 1][:80]))
        try:
            row = [float(x) for x in p[:5]]
        except ValueError:
            return _cube_bad(path, "读原子行（第 {} 个原子）".format(k + 1),
                             "非数值 {!r}".format(lines[i - 1][:80]))
        if bohr_coords:
            row[2:] = [v * BOHR_ANG for v in row[2:]]
        atoms.append(row)
    atoms = np.array(atoms, dtype=float) if atoms else np.zeros((0, 5))
    # --- 3 行格点定义 ---
    npts = []
    steps = []
    for ax in range(3):
        if i >= len(lines):
            return _cube_bad(path, "读第 {} 条格点定义行".format(ax + 1), "文件提前结束")
        p = lines[i].split()
        i += 1
        if len(p) < 4:
            return _cube_bad(path, "读第 {} 条格点定义行".format(ax + 1),
                             "期望 4 列 'n ax ay az'，实得 {!r}".format(lines[i - 1][:80]))
        try:
            n = int(float(p[0]))
            step = np.array([float(x) for x in p[1:4]], dtype=float)
        except ValueError:
            return _cube_bad(path, "读第 {} 条格点定义行".format(ax + 1),
                             "非数值 {!r}".format(lines[i - 1][:80]))
        if n == 0:
            return _cube_bad(path, "读第 {} 条格点定义行".format(ax + 1),
                             "格点数为 0")
        neg = n < 0
        npts.append(abs(n))
        steps.append(step * BOHR_ANG if neg else step)
    npts = tuple(npts)
    steps = np.array(steps, dtype=float)
    # --- 体数据（**一次读完再 split，比逐行读快很多**）---
    total = npts[0] * npts[1] * npts[2]
    tail = " ".join(lines[i:]).split()
    if len(tail) < total:
        return _cube_bad(
            path, "读体数据",
            "头声明 {}×{}×{} = {} 个格点，体数据只有 {} 个数（文件被截断？"
            "或 STRIDE 与格点定义不一致）".format(
                npts[0], npts[1], npts[2], total, len(tail)))
    try:
        vals = np.array(tail[:total], dtype=float)
    except ValueError:
        bad = next((t for t in tail[:total] if not _is_float(t)), "?")
        return _cube_bad(path, "读体数据", "存在非数值 token {!r}".format(bad[:40]))
    # cube 存储次序: x 最慢、z 最快 ⇒ reshape(nx, ny, nz) 后 [ix, iy, iz] 直接可用
    data = vals.reshape(npts[0], npts[1], npts[2])
    pos = [origin[k] + steps[k, k] * np.arange(npts[k]) for k in range(3)]
    volume = abs(float(np.linalg.det(steps)))
    info = {
        "comment": comment, "atoms": atoms, "origin": origin, "npts": npts,
        "steps": steps, "data": data, "pos": pos, "volume": volume,
    }
    return info, None


def _is_float(tok):
    try:
        float(tok)
        return True
    except ValueError:
        return False


def cube_axis_coords(cube, axis):
    """沿 `axis` 的格点坐标（Å）。

    直角步进矢量时直接用 `origin[k] + m·step[k][k]`；斜晶胞时退化为把格点
    3D 位置**投影到该轴单位矢量**上（仍然单调、可画）。
    """
    ai = _CUBE_AXIS_INFO[axis][0]
    n = cube["npts"][ai]
    st = cube["steps"][ai]
    # 步进矢量只有第 ai 个分量非零 ⇒ 真·一维步进，直接线性
    others = [k for k in range(3) if k != ai]
    if all(abs(st[k]) < 1e-9 for k in others):
        return cube["origin"][ai] + st[ai] * np.arange(n)
    # 斜晶胞：把格点 3D 位置投影到该轴步进矢量方向（仍然单调、可画）
    u = st / np.linalg.norm(st)
    base = float(np.dot(cube["origin"], u))
    return base + np.linalg.norm(st) * np.arange(n)


def planar_average(cube, axis):
    """沿 `axis` 对另两轴求平均。返回 ``(coord[n], mean[n], std[n])``。

    返回的是**面内平均**（`mean`）；宏观平均（整体平均成一个常数）由
    `--macro` 单独给出，因为讲师把两者分得很清楚（vn5 L399–416）。
    """
    ai, avg_axes, _label = _CUBE_AXIS_INFO[axis]
    d = cube["data"]
    mean = d.mean(axis=tuple(avg_axes))
    std = d.std(axis=tuple(avg_axes))
    if mean.shape[0] != cube["npts"][ai]:
        # 理论上不可达；留一条防御以免将来 reshape 语义改动后静默出错
        raise ValueError("plane-mean 形状 {} 与轴 {} 的格点数 {} 不一致".format(
            mean.shape, axis, cube["npts"][ai]))
    return cube_axis_coords(cube, axis), mean, std


def _cube_src(args, names=("cube", "cubes")):
    """从 args 里取"输入 cube"以派生默认前缀（不比 `out_prefix` 猜得更多）。"""
    for nm in names:
        v = getattr(args, nm, None)
        if isinstance(v, (list, tuple)):
            v = v[0] if v else None
        if v:
            return str(v)
    return None


def _out_prefix_with_cube(args):
    """`out_prefix` + cube 位置参数的回退；**只在新子命令里用**。

    为什么不改 `out_prefix` 本身：`bader` 也吃一个叫 `cube` 的位置参数，
    改它会**静默改变 bader 的产物名**（`cp2k_bader.csv` → `<cubename>_bader.csv`）。
    向后兼容优先，所以这里另开一个薄包装。

    派生规则 = **只砍最后一个扩展名**（与 `out_prefix` 对 traj/out 的口径一致）：
    `v_hartree.cube` → `v_hartree`。所以 `-pos-1.xyz` 那种多点名字不会被误砍。
    """
    if getattr(args, "prefix", None):
        return args.prefix
    src = _cube_src(args)
    for nm in ("freqfile", "out", "traj", "rdf", "wannier"):
        src = src or getattr(args, nm, None)
    if src:
        base = os.path.basename(str(src))
        return base.rsplit(".", 1)[0] if "." in base else base
    return "cp2k"


def _cube_axis_arg(s):
    a = str(s).strip().lower()
    if a not in _CUBE_AXIS_INFO:
        raise argparse.ArgumentTypeError(
            "--axis 只支持 x/y/z/xy/xz/yz（xy = 对 x、y 求平均 ⇒ 横坐标是 z），实得 {!r}".format(s))
    return a


def cmd_cube(args):
    """G-03：读 Gaussian cube → 指定轴的平面平均曲线（+ CSV/PNG/JSON）。"""
    axis = args.axis
    ai, _avg, label = _CUBE_AXIS_INFO[axis]
    cubes = []
    for p in args.cubes:
        c, err = read_cube(p)
        if c is None:
            print("\n[ERROR] " + err, file=sys.stderr)
            return 1
        cubes.append((p, c))
    prefix = _out_prefix_with_cube(args)
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    header = ["coord[Angstrom]"]
    cols = []
    summary = []
    for p, c in cubes:
        coord, mean, std = planar_average(c, axis)
        tag = os.path.splitext(os.path.basename(p))[0] if len(cubes) > 1 else "value"
        cols.append((tag, mean))
        header.append(tag)
        macro = float(c["data"].mean())
        summary.append({
            "file": p,
            "natoms": int(c["atoms"].shape[0]),
            "ngrid": list(c["npts"]),
            "voxel_volume_A3": c["volume"],
            "axis": axis,
            "macro_average": macro,
            "plane_average_min": float(mean.min()),
            "plane_average_max": float(mean.max()),
        })
        lbl = os.path.basename(p) if len(cubes) > 1 else None
        ax.plot(coord, mean, lw=1.4, label=lbl)
        if len(cubes) == 1 and args.show_std:
            ax.fill_between(coord, mean - std, mean + std, alpha=0.18,
                            color="steelblue", label="面内 ±1σ")
    rows = []
    for k in range(len(cols[0][1])):
        rows.append(["{:.6f}".format(coord[k])] +
                    ["{:.8e}".format(c[1][k]) for c in cols])
    csv = prefix + "_planar.csv"
    write_csv(csv, header, rows)
    ax.set_xlabel("{} [Angstrom]".format(axis))
    ax.set_ylabel("planar average")
    ax.set_title("Cube planar average along {} (面内平均 {})".format(axis, label))
    if len(cubes) > 1:
        ax.legend(fontsize=8)
    elif args.show_std:
        ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_planar.png")
    print("cube 平面平均：{} 个文件, axis={}, 格点 {}".format(
        len(cubes), axis, [s["ngrid"] for s in summary]))
    for s in summary:
        print("  {}  原子数={}  宏观平均={:.8e}  面内平均范围=[{:.6e}, {:.6e}]".format(
            os.path.basename(s["file"]), s["natoms"], s["macro_average"],
            s["plane_average_min"], s["plane_average_max"]))
    print("written: {} + {}".format(csv, prefix + "_planar.png"))
    if args.json:
        import json
        print(json.dumps({"command": "cube", "axis": axis, "cubes": summary},
                         ensure_ascii=False))
    return 0


def cmd_cdd(args):
    """G-04：电荷密度差分 Δρ = ρ_AB − Σρ_frag（可选再平面平均）。"""
    tot, err = read_cube(args.total)
    if tot is None:
        print("\n[ERROR] --total " + err, file=sys.stderr)
        return 1
    frags = []
    for p in args.frag:
        c, err = read_cube(p)
        if c is None:
            print("\n[ERROR] --frag " + err, file=sys.stderr)
            return 1
        frags.append((p, c))
    # 格点一致性校验（G-04 明确要求"否则中文报错并给出检查方向"）
    for p, c in frags:
        if c["npts"] != tot["npts"]:
            print("", file=sys.stderr)
            print("[ERROR] cube 格点数不一致，无法做 3D 减法。", file=sys.stderr)
            print("  --total {}: {}".format(args.total, list(tot["npts"])),
                  file=sys.stderr)
            print("  --frag  {}: {}".format(p, list(c["npts"])), file=sys.stderr)
            print("  检查方向：① 三个 cube 是否用了**同一个 `STRIDE`**"
                  "（官方默认 2 2 2，讲义要求 1 1 1）；", file=sys.stderr)
            print("            ② 是否同一个 `&CELL`（改了盒子必须重算）；",
                  file=sys.stderr)
            print("            ③ 是否同一个 `CUTOFF`（格点数由 CUTOFF 决定）。",
                  file=sys.stderr)
            return 1
        if not np.allclose(c["origin"], tot["origin"], atol=1e-6) or \
                not np.allclose(c["steps"], tot["steps"], atol=1e-6):
            print("", file=sys.stderr)
            print("[ERROR] cube 的原点/步进矢量不一致：{}".format(p), file=sys.stderr)
            print("  格点数虽然相同，但格点位置不同 ⇒ 逐点相减没有物理意义。",
                  file=sys.stderr)
            return 1
    rho = tot["data"].copy()
    for _p, c in frags:
        rho = rho - c["data"]        # 变形电荷密度：Σρ_frag 就是孤立原子密度叠加
    out_cube = (args.out_cube or (_out_prefix_with_cube(args) + "_cdd.cube"))
    _write_cube(out_cube, tot, rho * HARTREE_EV,
                "CDD d_rho = rho_total - sum(rho_frag), unit=eV/Angstrom^3")
    dv = tot["volume"]
    net = float(rho.sum() * dv)
    pos = float(np.clip(rho, 0, None).sum() * dv)
    neg = float(np.clip(rho, -np.inf, 0).sum() * dv)
    print("电荷密度差分 Δρ = ρ_AB − Σρ_frag（{} 个片段）".format(len(frags)))
    print("  ∫Δρ dV = {:.6e} e   （>0 表示差分区电子增多；≈0 才守恒）".format(net))
    print("  ∫Δρ⁺ dV = {:.6e} e ;  ∫Δρ⁻ dV = {:.6e} e".format(pos, neg))
    print("  ⚠️ ∫Δρ 不严格为 0 是正常的：差分图看的是**空间分布**（正=增加、负=减少）")
    print("     而不是绝对电子数；片段参考态与整体态基组/赝势不同就会有残差。")
    print("  产物 cube 单位 = eV/Å³（把 a.u. 乘了 {:.6f}），值可直接进 VESTA 看正负区".format(
        HARTREE_EV))
    print("  ⚠️ 三个 cube 必须是【同一个 STRIDE / 同一个 CELL】；"
          "且**两个片段一定不要再优化**，否则差分图是错的（vn5 N-03/P-01）")
    written = [out_cube]
    if args.planar_axis:
        coord, mean, _std = planar_average({"data": rho, "npts": tot["npts"],
                                            "steps": tot["steps"],
                                            "origin": tot["origin"]}, args.planar_axis)
        mean_ev = mean * HARTREE_EV
        csv = _out_prefix_with_cube(args) + "_cdd_planar.csv"
        write_csv(csv, "coord[Angstrom],d_rho[eV/A^3]",
                  [["{:.6f}".format(coord[k]), "{:.8e}".format(mean_ev[k])]
                   for k in range(len(coord))])
        fig, ax = plt.subplots(figsize=(7.0, 4.4))
        ax.axhline(0, color="gray", lw=0.8)
        ax.plot(coord, mean_ev, lw=1.4, color="crimson")
        ax.fill_between(coord, 0, mean_ev, where=(mean_ev >= 0),
                        color="crimson", alpha=0.25, label="Δρ > 0 电子增多")
        ax.fill_between(coord, 0, mean_ev, where=(mean_ev < 0),
                        color="steelblue", alpha=0.25, label="Δρ < 0 电子减少")
        ax.set_xlabel("{} [Angstrom]".format(args.planar_axis))
        ax.set_ylabel("Δρ planar average [eV/A^3]")
        ax.set_title("Charge density difference (planar average along {})".format(
            args.planar_axis))
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        png = _out_prefix_with_cube(args) + "_cdd_planar.png"
        save_png(fig, png)
        written += [csv, png]
        print("  Δρ 平面平均: 最大 +{:.4e} / 最小 {:.4e} eV/Å³".format(
            float(mean_ev.max()), float(mean_ev.min())))
    print("written: " + " + ".join(written))
    if args.json:
        import json
        print(json.dumps({"command": "cdd", "net_charge_e": net,
                          "positive_e": pos, "negative_e": neg,
                          "outputs": written}, ensure_ascii=False))
    return 0


def _write_cube(path, tmpl, data, comment):
    """按 `tmpl` 的格点定义写一个新 cube。

    坐标统一以 **Å** 给出 ⇒ **三个格点定义行取负号**（Gaussian 约定：n<0 表示
    该轴步进矢量以 Å 计）。⚠️ 第 3 行的 `natoms` **必须保持为正** —— 它的负号
    在 cube 约定里表示的是"**原子坐标**以 bohr 计"，与格点单位是两件事。
    第一版把 natoms 也写成 `-0`/`-1`，于是 `read_cube` 会去按 bohr 折原点，
    并且把第一条格点定义行当成原子行读 ⇒ 自己写出去的 cube 自己读不回来。
    """
    n = tmpl["npts"]
    st = tmpl["steps"]
    org = tmpl["origin"]
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(comment + "\n")
        f.write("CP2K skill postprocess.py\n")
        f.write("{:5d} {:13.6f} {:13.6f} {:13.6f}\n".format(
            int(tmpl["atoms"].shape[0]), org[0], org[1], org[2]))
        for row in tmpl["atoms"]:
            f.write("{:5d} {:13.6f} {:13.6f} {:13.6f} {:13.6f}\n".format(
                int(row[0]), row[1], row[2], row[3], row[4]))
        for k in range(3):
            f.write("{:5d} {:13.6f} {:13.6f} {:13.6f}\n".format(
                -int(n[k]), st[k][0], st[k][1], st[k][2]))
        flat = data.reshape(-1)          # x 最慢、z 最快 ⇒ C 序 ravel 即正确
        for k in range(0, flat.size, 6):
            f.write("".join("{:13.5E}".format(v) for v in flat[k:k + 6]) + "\n")
    _OUTPUTS.append(path)
    return path


# ==========================================================================
# workfunc：Hartree 势平面平均 → 真空平台 → 功函 Φ → 相对 SHE 的电极电势
# ==========================================================================
# Φ = E_vac − E_F（`playbook.md:529`）；相对 SHE 的电极电势 =
# Φ − 4.44 V（`course_learned.md:650–651`，算例 Φ = 5.26 eV → +0.82 V）。
#
# 单位是本条最容易错的地方（vn5 N-19 / `course_learned.md:1024`）：
# **CP2K 的 `Fermi energy:` 行默认以 Hartree 打印**（`official/01_global_and_units.md:544`、
# `h_tutorials/notes/05_howto_exercises.md:1022` 的 `0.20867150262130` 就是 hartree）；
# 但 `.pdos` 头注释里的 `E(Fermi) = ... a.u.` 也可能被写成 eV。所以**必须按行内单位标注换算**。

_FERMI_PATTERNS = (
    # 例: "Fermi energy:                          0.20867150262130"
    (re.compile(r"Fermi\s+energy\s*[:=]\s*([-+]?\d+\.?\d*(?:[eEdD][-+]?\d+)?)"),
     "hartree"),
    # 例: "E(Fermi) =     0.122425 a.u."
    (re.compile(r"E\s*\(\s*Fermi\s*\)\s*[:=]\s*([-+]?\d+\.?\d*(?:[eEdD][-+]?\d+)?)"),
     "hartree"),
    # 例: "fermi energy [eV] =   -5.1234"
    (re.compile(r"fermi\s+energy\s*\[\s*(eV|hartree|a\.u\.)\s*\]\s*[:=]\s*"
                r"([-+]?\d+\.?\d*(?:[eEdD][-+]?\d+)?)", re.I), "declared"),
    # VASP 风格 OUTCAR: "E-fermi :   5.1234     eV"
    (re.compile(r"E-fermi\s*:\s*([-+]?\d+\.?\d*(?:[eEdD][-+]?\d+)?)\s*(eV)?"),
     "vasp"),
)


def parse_fermi_level(path):
    """从 `.out` / `.pdos` 里解析费米能级，**按行内单位换算成 eV**。

    返回 ``(E_F_eV, 命中的原行, 说明)``，失败返回 ``(None, None, 原因)``。
    """
    if not os.path.exists(path):
        return None, None, "找不到文件 {}".format(path)
    try:
        blob = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError as exc:
        return None, None, "读不了 {}: {}".format(path, exc)
    for ln in blob:
        for rx, kind in _FERMI_PATTERNS:
            m = rx.search(ln)
            if not m:
                continue
            if kind == "declared":
                unit = m.group(1).lower().replace(".", "")
                raw = float(m.group(2))
                if unit in ("ev",):
                    return raw, ln.strip(), "行内声明 [eV]，直接采用"
                return raw * HARTREE_EV, ln.strip(), "行内声明 hartree/a.u.，已 ×27.2114 转 eV"
            if kind == "vasp":
                raw = float(m.group(1))
                # OUTCAR 的 E-fermi 单位是 eV
                return (raw if m.group(2) else raw), ln.strip(), "E-fermi 行（VASP 口径，eV）"
            # kind == "hartree"
            raw = float(m.group(1).replace("D", "E").replace("d", "e"))
            if re.search(r"\beV\b", ln) and not re.search(r"hartree|a\.u\.", ln, re.I):
                return raw, ln.strip(), "同一行标注 eV，直接采用"
            return raw * HARTREE_EV, ln.strip(), "默认 Hartree，已 ×27.2114 转 eV"
    return None, None, "文件里没有任何可识别的费米能级行"


def _find_vacuum_plateau(coord, v, from_top, window_A, tol_ev_per_A):
    """在 coord/v 曲线上找**最长平坦段**。

    返回 ``(E_vac_eV, 段起下标, 段止下标, 段内 max|dV/dcoord|, 长度Å)``；
    找不到任何平坦段时返回 ``(None, None, None, None, None)``。

    `from_top=False` ⇒ 只看曲线**前半段**（下表面真空区）；True ⇒ 只看**后半段**。

    判据：先用中心差分算 dV/dcoord（**不用 np.gradient 的单边端点值** —— 端点
    那里正好是"slab 台阶"的位置，单边差分会被台阶污染成假斜率），再取
    |dV/dcoord| < tol 的**连续最长段**。
    """
    n = len(coord)
    if n < 3:
        return None, None, None, None, None
    d = np.zeros(n)
    d[1:-1] = (v[2:] - v[:-2]) / (coord[2:] - coord[:-2])
    # 端点用**相邻内侧点**的斜率（而不是跨端点的单边差分）——见上面 docstring
    d[0] = d[1]
    d[-1] = d[-2]
    flat = np.abs(d) < tol_ev_per_A
    i0, i1 = (n // 2, n) if from_top else (0, n // 2)
    best = None
    k = i0
    while k < i1:
        if not flat[k]:
            k += 1
            continue
        a = k
        while k + 1 < i1 and flat[k + 1]:
            k += 1
        b = k
        span = float(coord[b] - coord[a])
        # 长度下限：--vacuum-window（避免把"某两个点碰巧都平"当成真空段）
        if span >= min(window_A, coord[i1 - 1] - coord[i0]):
            if best is None or span > best[3]:
                best = (a, b, float(np.max(np.abs(d[a:b + 1]))), span)
        k += 1
    if best is None:
        return None, None, None, None, None
    a, b, g, span = best
    return float(v[a:b + 1].mean()), a, b, g, span


def _fallback_vacuum(v_ev, coord, from_top):
    """**整条曲线都被宏观斜率污染**时的降级出口。

    返回与 `_find_vacuum_plateau` 同形的 5 元组：取该半段的均值作"名义 E_vac"，
    并把该半段的 max|dV/dz| **照实**报出来 —— 这样倾斜告警仍然会触发，
    用户能立刻看到"斜率是 0.005 eV/Å，不是平台"。

    ⚠️ 这条分支本身就是**诊断结论**（典型成因：非对称 slab 没开
    `SURFACE_DIPOLE_CORRECTION`），所以绝不能在这里 `return 1` 把用户挡回去。
    """
    n = len(coord)
    i0, i1 = (n // 2, n) if from_top else (0, n // 2)
    if i1 - i0 < 3:
        return None, None, None, None, None
    d = np.zeros(n)
    d[1:-1] = (v_ev[2:] - v_ev[:-2]) / (coord[2:] - coord[:-2])
    d[0] = d[1]
    d[-1] = d[-2]
    g = float(np.max(np.abs(d[i0:i1])))
    return (float(v_ev[i0:i1].mean()), i0, i1 - 1, g,
            float(coord[i1 - 1] - coord[i0]))


def cmd_workfunc(args):
    cube, err = read_cube(args.cube)
    if cube is None:
        print("\n[ERROR] " + err, file=sys.stderr)
        return 1
    axis = args.axis
    coord, mean, _std = planar_average(cube, axis)
    # Hartree 势 cube 的格点值单位是 Hartree ⇒ 转 eV
    v_ev = mean * HARTREE_EV
    if args.out:
        ef, raw_line, why = parse_fermi_level(args.out)
        if ef is None:
            print("", file=sys.stderr)
            print("[ERROR] 未能从 {} 解析费米能级：{}".format(args.out, why),
                  file=sys.stderr)
            print("  本命令认这三种写法（**必须按行内单位标注换算**）：",
                  file=sys.stderr)
            print("    Fermi energy:                          0.20867150262130   "
                  "（默认 Hartree）", file=sys.stderr)
            print("    E(Fermi) = 0.122425 a.u.  （在 .pdos 头注释里）",
                  file=sys.stderr)
            print("    fermi energy [eV] = -5.1234        （行内声明单位）",
                  file=sys.stderr)
            print("  也可以直接给 `--fermi <eV>` 跳过解析。", file=sys.stderr)
            return 1
    else:
        ef = args.fermi
        raw_line, why = None, "由 --fermi 直接给出（eV）"
    if ef is None:
        print("[ERROR] 需要 --out <cp2k.out> 或 --fermi <eV> 才能算功函。",
              file=sys.stderr)
        return 1
    # 两侧分别找真空平台
    top = _find_vacuum_plateau(coord, v_ev, True, args.vacuum_window, args.slope_tol)
    bot = _find_vacuum_plateau(coord, v_ev, False, args.vacuum_window, args.slope_tol)
    # 退化：整条曲线都有宏观斜率（典型的"没加偶极校正"）⇒ 找不到任何"平坦"段。
    # 这时**不能**直接报错退出：那等于把最需要诊断的情形挡在门外。改成取该半段
    # 的均值作为可诊断的 E_vac，并把真实斜率照实报出来触发倾斜警告。
    tilt_note = None
    if top[0] is None or bot[0] is None:
        if top[0] is None:
            top = _fallback_vacuum(v_ev, coord, True)
        if bot[0] is None:
            bot = _fallback_vacuum(v_ev, coord, False)
        tilt_note = ("在 |dV/dz| < {:g} eV/Å 的严格判据下**找不到平坦真空段** —— "
                     "整条曲线都带宏观斜率。已退化为"
                     "「取该半段均值」给出可诊断的 E_vac；数值**不可直接引用**，"
                     "先修模型。".format(args.slope_tol))
    prefix = _out_prefix_with_cube(args)
    rows = []
    res = {"E_Fermi_eV": ef, "SHE_eV": args.she}
    if abs(args.she - SHE_EV) > 1e-9:
        print("  [note] 你把 SHE 参考改成了 {:.4f} eV（仓库/讲义口径是 {:.2f} eV）"
              "——请确认这是有意为之。".format(args.she, SHE_EV))
    if tilt_note:
        print("", file=sys.stderr)
        print("[WARN] " + tilt_note, file=sys.stderr)
    for name, vac, tag in (("top", top, "上表面"), ("bot", bot, "下表面")):
        e_vac, a, b, g, span = vac
        if e_vac is None:
            print("  [WARN] {} 侧找不到 ≥{:.1f} Å 的平坦真空段，跳过。".format(
                tag, args.vacuum_window))
            continue
        phi = e_vac - ef
        u_she = phi - args.she
        res["E_vac_{}".format(name)] = e_vac
        res["Phi_{}".format(name)] = phi
        res["U_vs_SHE_{}".format(name)] = u_she
        res["plateau_{}".format(name)] = [float(coord[a]), float(coord[b])]
        res["plateau_width_{}".format(name)] = span
        res["max_grad_{}".format(name)] = g
        rows.append([name, "{:.6f}".format(e_vac), "{:.6f}".format(phi),
                     "{:.6f}".format(u_she), "{:.4f}".format(coord[a]),
                     "{:.4f}".format(coord[b]), "{:.6f}".format(g),
                     "{:.4f}".format(span),
                     "{:.8f}".format(e_vac / HARTREE_EV),
                     "{:.8f}".format(phi / HARTREE_EV)])
    csv = prefix + "_workfunc.csv"
    write_csv(csv,
              "side,E_vac[eV],Phi[eV],U_vs_SHE[V],plateau_from[A],plateau_to[A],"
              "max|dV/dz|[eV/A],plateau_width[A],E_vac[hartree],Phi[hartree]", rows)
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.plot(coord, v_ev, lw=1.5, color="navy", label="V(z) planar average")
    ax.axhline(ef, color="green", ls="--", lw=1.0,
               label="E_Fermi = {:.3f} eV".format(ef))
    for name, vac, color in (("top", top, "crimson"), ("bot", bot, "darkorange")):
        e_vac, a, b, _g, _span = vac
        if e_vac is None:
            continue
        ax.axhline(e_vac, color=color, ls=":", lw=1.0,
                   label="E_vac({}) = {:.3f} eV".format(name, e_vac))
        ax.axvspan(coord[a], coord[b], color=color, alpha=0.12)
    ax.set_xlabel("{} [Angstrom]".format(axis))
    ax.set_ylabel("V [eV]")
    ax.set_title("Work function  Φ = E_vac − E_F   (SHE = {:.2f} eV)".format(args.she))
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    png = prefix + "_workfunc.png"
    save_png(fig, png)
    print("功函 Φ = E_vac − E_F（Hartree 势 cube 平面平均 {}-轴）".format(axis))
    print("  费米能级 E_F = {:.6f} eV   来源：{}".format(ef, why))
    if raw_line:
        print("    命中行: {}".format(raw_line))
    for r in rows:
        print("  {} 侧: E_vac={} eV  Φ={} eV  相对 SHE 电极电势 U={} V".format(
            r[0], r[1], r[2], r[3]))
        print("          真空平台: {} ~ {} Å，平台内 max|dV/dz|={} eV/Å".format(
            r[4], r[5], r[6]))
    # --- 真空位倾斜告警（vn5 P-08 / N-18 / N-44）---
    for r in rows:
        if float(r[6]) > args.warn_grad:
            print("", file=sys.stderr)
            print("[WARN] {} 侧真空位不平（平台内 max|dV/dz| = {} eV/Å > {:.4f}）——"
                  "真空段有**宏观电场**残留。".format(r[0], r[6], args.warn_grad),
                  file=sys.stderr)
            print("       典型原因：**非对称 slab 没开偶极校正**。",
                  file=sys.stderr)
            print("       处方：&FORCE_EVAL/&DFT 下加 `&SURFACE_DIPOLE_CORRECTION ON`"
                  "（必要时给 `SURF_DIP_DIR`）。", file=sys.stderr)
            print("       ⚠️ 官方硬限制：该校正**只对法向平行于某一笛卡尔轴的 slab 实现**"
                  "（`_kw_probe.py FORCE_EVAL/DFT/SURFACE_DIPOLE_CORRECTION` → default F）。",
                  file=sys.stderr)
            print("       未加校正时 Φ 会随真空层厚度漂移，两侧 Φ 也对不上 —— 先修模型再采信数值。",
                  file=sys.stderr)
    print("written: {} + {}".format(csv, png))
    if args.json:
        import json
        print(json.dumps({"command": "workfunc", "she_eV": args.she,
                          "fermi_source": why, **res}, ensure_ascii=False))
    return 0


# ==========================================================================
# ir-static：频率 + 强度 → 高斯展宽静态红外谱（区别于 VACF-FFT 的 `ir`）
# ==========================================================================
# 两条路**不是同一件事**（`postprocess.md:158`、vn4 G-03）：
#   * `ir`        = AIMD → VACF → FFT。峰宽是"真实"的（含非谐与温度效应）。
#   * `ir-static` = `&VIBRATIONAL_ANALYSIS` 的**单值频率 + 强度** → **人为高斯展宽**。
# 讲师原话"其实我是有一个程序的，但这里没有总结出来"（`course_learned.md:1363`）。

_FREQ_INLINE = re.compile(r"VIB\|\s*Frequency\s*\(cm\^-?1\)\s*(.*)$")
_INT_INLINE = re.compile(r"VIB\|\s*Intensities?\s*(.*)$")
_FREQ_BLOCK = re.compile(r"VIB\|\s*(?:Frequency|Frequencies)\b.*?(?:cm\^-?1)?")


def parse_vib(path):
    """从 CP2K `.out` 解析 `VIB|Frequency` 与 `VIB|Intensities`。

    返回 ``(freqs_cm, ints, notes)``；``ints`` 可与 freq 等长或为 None。
    CP2K 的实际打印形态（两种都要认）：
      A) 同一行:  ``VIB|Frequency (cm^-1)   130.033994  350.664678 ...``
      B) 分两行:  ``VIB|Frequency (cm^-1)`` / ``VIB|  130.033994 ...``
                  ``VIB|Intensities`` / ``VIB|  0.006627 ...``
    """
    if not os.path.exists(path):
        return None, None, ["找不到文件 {}".format(path)]
    notes = []
    freqs, ints = [], []
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    mode = None
    for ln in lines:
        if "VIB|" not in ln:
            continue
        m = _FREQ_INLINE.search(ln)
        if m:
            got = [float(x) for x in m.group(1).split() if _is_float(x)]
            if got:
                freqs += got
                mode = None
                continue
            mode = "freq"
            continue
        m = _INT_INLINE.search(ln)
        if m:
            got = [float(x) for x in m.group(1).split() if _is_float(x)]
            if got:
                ints += got
                mode = None
                continue
            mode = "int"
            continue
        # 续行: "VIB|   ...numbers..."
        if mode:
            body = ln.split("VIB|", 1)[1]
            got = [float(x) for x in body.split() if _is_float(x)]
            if got:
                (freqs if mode == "freq" else ints).extend(got)
            else:
                # 遇到非数值的 VIB| 行（如表格边框）就结束续行模式
                mode = None
    if not freqs:
        notes.append("没有解析到任何 `VIB|Frequency` 行 —— 说明该 .out 里没有振动分析结果")
        return None, None, notes
    if not ints:
        notes.append("没有解析到 `VIB|Intensities` 行 —— 需要输入里加 `INTENSITIES T`；"
                     "本命令退化为**等权**展宽（所有峰高相同）")
        ints = None
    elif len(ints) != len(freqs):
        notes.append("强度个数 {} 与频率个数 {} 不一致 —— 只取前 {} 个配对".format(
            len(ints), len(freqs), min(len(ints), len(freqs))))
        ints = ints[:len(freqs)]
    return np.array(freqs, dtype=float), (None if ints is None else np.array(ints, dtype=float)), notes


def cmd_ir_static(args):
    freqs, ints, notes = parse_vib(args.freqfile)
    for n in notes:
        print("  [note] " + n)
    if freqs is None:
        print("\n[ERROR] {} 里没有可用的振动数据。".format(args.freqfile),
              file=sys.stderr)
        print("  本命令读 CP2K `.out` 的 `VIB|Frequency (cm^-1)` + `VIB|Intensities`；"
              "先跑 `&VIBRATIONAL_ANALYSIS`（`gen_inp.py --type vib`）。", file=sys.stderr)
        return 1
    # 丢掉虚频（负 cm^-1）——它们不是吸收峰，但要单独报出来
    imag = freqs[freqs < 0]
    real = freqs[freqs >= 0]
    if ints is not None:
        ints_real = ints[freqs >= 0]
    else:
        ints_real = np.ones_like(real)
    sigma = args.fwhm / (2.0 * math.sqrt(2.0 * math.log(2.0)))   # FWHM → σ
    fmax = args.fmax if args.fmax else float(max(4000.0, real.max() * 1.15 + 5 * args.fwhm))
    grid = np.arange(0.0, fmax, args.df)
    spec = np.zeros_like(grid)
    for f, a in zip(real, ints_real):
        spec += a * np.exp(-((grid - f) ** 2) / (2.0 * sigma ** 2))
    spec /= sigma * math.sqrt(2.0 * math.pi)
    prefix = _out_prefix_with_cube(args)
    csv = prefix + "_ir_static.csv"
    write_csv(csv, "wavenumber[cm-1],intensity[a.u.]",
              [["{:.4f}".format(grid[k]), "{:.8e}".format(spec[k])]
               for k in range(len(grid))])
    fig, ax = plt.subplots(figsize=(7.4, 4.5))
    ax.plot(grid, spec, lw=1.4, color="darkred")
    ax.set_xlabel("wavenumber [cm^-1]")
    ax.set_ylabel("intensity [a.u.]")
    ax.set_title("Static IR (Gaussian broadening, FWHM = {:.1f} cm^-1)".format(args.fwhm))
    ax.grid(alpha=0.3)
    png = prefix + "_ir_static.png"
    save_png(fig, png)
    print("静态 IR（频率+强度 → 高斯展宽）：{} 个实频模式, FWHM={} cm^-1".format(
        len(real), args.fwhm))
    if imag.size:
        print("  ⚠️ 有 {} 个虚频（{} cm^-1），**未计入谱**：它们不是吸收峰，"
              "而是鞍点/数值噪声".format(
                  imag.size, ", ".join("{:.2f}".format(x) for x in imag[:8])))
    top = np.argsort(spec)[::-1][:5]
    print("  最强峰位 (cm^-1): " +
          ", ".join("{:.1f}".format(grid[k]) for k in top if spec[k] > 0))
    print("  ⚠️ 本谱的峰宽是**人为**的（与 `ir` 子命令的 VACF-FFT 不同，后者峰宽更真实）")
    print("written: {} + {}".format(csv, png))
    if args.json:
        import json
        print(json.dumps({"command": "ir-static", "n_modes": int(len(real)),
                          "n_imag": int(imag.size), "fwhm_cm1": args.fwhm,
                          "peaks_cm1": [float(grid[k]) for k in top if spec[k] > 0]},
                         ensure_ascii=False))
    return 0


# ==========================================================================
# arrhenius：多温度 D → ln D vs 1/T → Ea 与 D₀
# ==========================================================================
# 讲义用的是 **`log D` vs `1000/T`**（`learn_L3.md:832`）：
#     斜率 = −Ea / (2.303 · k_B)      （2.303 = ln 10，因为用了 log10）
#     本例斜率 −1.07871、k_B = 8.6173e-5 eV
#     ⇒ Ea = 1.07871 × 2.303 × 8.6173e-5 = 2.1409e-4 keV = 0.2141 eV ✓
#     （与 `course_learned.md:344`、`learn_L3.md:832` 的 0.2141 eV 一致 —— 量纲自检通过）
# 用自然对数 ln D vs 1/T 时斜率 = −Ea/k_B，两式等价（差 2.303 因子）。


def _pair_parser(s):
    """把 `"1000:1.2e-6"` 或 `"1000,1.2e-6"` 解成 (T, D)。"""
    for sep in (":", ",", "=", "/"):
        if sep in s:
            a, b = s.split(sep, 1)
            return float(a), float(b)
    raise ValueError("--d 的每一项要写成 `T:D`（例 1000:1.2e-6），实得 {!r}".format(s))


def _collect_diffusion_files(paths):
    """从若干 `*_diffusion.txt` 里抠出 (T, D)。**不猜温度**：拿不到 T 就报错。"""
    pairs, problems = [], []
    for p in paths:
        if not os.path.exists(p):
            problems.append("{} 不存在".format(p))
            continue
        txt = open(p, encoding="utf-8", errors="replace").read()
        mD = re.search(r"D\s*=\s*([-+\d.eE]+)\s*Angstrom\^2/ps", txt)
        if not mD:
            mD = re.search(r"D\s*=\s*([-+\d.eE]+)\s*A\^2/ps", txt)
        mT = re.search(r"temperature\s*[:=]?\s*([-+\d.]+)\s*K", txt, re.I)
        if not mD:
            problems.append("{} 里找不到 `D = ... Angstrom^2/ps`".format(p))
            continue
        if not mT:
            problems.append("{} 里找不到温度 —— 请用 `--d T:D` 显式给，"
                            "或在文件名/文件里带 `T=... K`".format(p))
            continue
        pairs.append((float(mT.group(1)), float(mD.group(1))))
    return pairs, problems


def cmd_arrhenius(args):
    pairs, problems = [], []
    if args.d:
        p, probs = [], []
        for s in args.d:
            try:
                p.append(_pair_parser(s))
            except ValueError as e:
                probs.append(str(e))
        pairs, problems = p, probs
    if args.diffusion:
        p2, probs2 = _collect_diffusion_files(args.diffusion)
        pairs += p2
        problems += probs2
    if problems or len(pairs) < 2:
        print("", file=sys.stderr)
        print("[ERROR] 需要**至少两对** (T, D) 才能做 Arrhenius 拟合。", file=sys.stderr)
        for pr in problems:
            print("  - " + pr, file=sys.stderr)
        if len(pairs) < 2 and not problems:
            print("  只拿到 {} 对。".format(len(pairs)), file=sys.stderr)
        print("", file=sys.stderr)
        print("  用法：", file=sys.stderr)
        print("    python scripts/postprocess.py arrhenius --d \"600:1.0e-6\" "
              "\"800:5.0e-6\" \"1000:2.0e-5\"", file=sys.stderr)
        print("    python scripts/postprocess.py arrhenius --diffusion "
              "d600_diffusion.txt d800_diffusion.txt ...", file=sys.stderr)
        return 1
    T = np.array([x[0] for x in pairs], dtype=float)
    D = np.array([x[1] for x in pairs], dtype=float)
    if np.any(T <= 0):
        print("[ERROR] 温度必须 > 0 K。", file=sys.stderr)
        return 1
    if np.any(D <= 0):
        print("[ERROR] 扩散系数必须 > 0（要取对数）。实得最小值 {}。".format(D.min()),
              file=sys.stderr)
        return 1
    if len(set(T.tolist())) < 2:
        print("[ERROR] 至少要有两个**不同**温度。", file=sys.stderr)
        return 1
    kb = args.kb
    if args.per_1000t:
        x = 1000.0 / T
        y = np.log10(D)
        slope, intercept = np.polyfit(x, y, 1)
        # 讲义口径（`learn_L3.md:832`）：**log(D) 对 1000/T** 的斜率
        #     = −Ea / (2.303 · k_B)          （2.303 = ln 10）
        # ⇒ Ea = −slope × 2.303 × k_B × 1000
        #                          ^^^^^^
        # ⚠️ **这个 1000 是横轴 1000/T 带进来的**，不是笔误。用讲义算例自检：
        #     1.07871 × 2.302585 × 8.6173e-5 × 1000 = 0.2141 eV ✓
        #    （与 `learn_L3.md:832` / `L1.txt:1170`「求得：E = 0.2141 eV」一致）
        # 另一个坑：必须写成 `-(slope * a * b)`。写成 `-slope * a * b` 会被解析成
        # `((-slope) * a) * b` —— 那是**另一个值**，而且静默不报错（本轮实测踩过）。
        Ea = -(slope * math.log(10.0) * kb * 1000.0)
        D0 = 10.0 ** intercept
        xlabel = "1000/T [1/K]"
        ylabel = "log10 D [cm^2/s or A^2/ps, 同输入单位]"
    else:
        x = 1.0 / T
        y = np.log(D)
        slope, intercept = np.polyfit(x, y, 1)
        # ln D = ln D0 − Ea/(k_B·T) ⇒ slope = −Ea/k_B ⇒ Ea = −slope·k_B
        # 这条横轴是 1/T，**没有** 1000 因子；与上面那条必须给出同一个 Ea。
        Ea = -(slope * kb)
        D0 = math.exp(intercept)
        xlabel = "1/T [1/K]"
        ylabel = "ln D [同输入单位]"
    # 拟合质量
    yhat = slope * x + intercept
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    prefix = args.prefix or "arrhenius"
    csv = prefix + "_arrhenius.csv"
    rows = [["{:.6f}".format(T[k]), "{:.8e}".format(D[k]),
             "{:.8e}".format(x[k]), "{:.8e}".format(y[k])] for k in range(len(T))]
    write_csv(csv, "T[K],D,{},{},fit".format(xlabel, ylabel),
              [rows[k] + ["{:.8e}".format(yhat[k])] for k in range(len(T))])
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.plot(x, y, "o", ms=6, color="navy", label="data")
    xs = np.linspace(x.min(), x.max(), 100)
    ax.plot(xs, slope * xs + intercept, "r--", lw=1.2,
            label="fit: slope={:.6g}, R²={:.5f}".format(slope, r2))
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title("Arrhenius: Ea = {:.4f} eV, D0 = {:.4e}".format(Ea, D0))
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    png = prefix + "_arrhenius.png"
    save_png(fig, png)
    txt = prefix + "_arrhenius.txt"
    with open(txt, "w", encoding="utf-8") as f:
        f.write("n_points = {}\n".format(len(T)))
        f.write("axis = {}\n".format(xlabel))
        f.write("slope = {:.8g}\n".format(slope))
        f.write("intercept = {:.8g}\n".format(intercept))
        f.write("k_B = {:.8e} eV/K\n".format(kb))
        f.write("Ea = {:.6f} eV = {:.6f} kJ/mol\n".format(Ea, Ea * KJMOL_PER_EV))
        f.write("D0 = {:.6e} (单位同输入 D)\n".format(D0))
        f.write("R^2 = {:.6f}\n".format(r2))
    _OUTPUTS.append(txt)
    print("Arrhenius 拟合：{} 个温度点".format(len(T)))
    print("  横轴 {}  纵轴 {}".format(xlabel, ylabel))
    print("  斜率 = {:.6g}   截距 = {:.6g}   R² = {:.6f}".format(slope, intercept, r2))
    print("  Ea = {:.6f} eV = {:.4f} kJ/mol".format(Ea, Ea * KJMOL_PER_EV))
    print("  D0 = {:.6e} （单位与输入 D 相同）".format(D0))
    if args.per_1000t:
        print("  公式（讲义口径，`learn_L3.md:832`）：斜率 = −Ea/(2.303·k_B) "
              "⇒ Ea = −slope × 2.303 × k_B × 1000")
        print("      （末尾的 1000 来自横轴 1000/T；讲义算例：1.07871 × 2.303 × "
              "8.6173e-5 × 1000 = 0.2141 eV）")
    else:
        print("  公式：ln D = ln D0 − Ea/(k_B·T) ⇒ 斜率 = −Ea/k_B")
    if r2 < 0.95:
        print("  [WARN] R² = {:.4f} < 0.95 —— 拟合很差。常见原因：".format(r2))
        print("         ① 温度范围太窄（讲师用 600/800/1000/1200/1400 K）；")
        print("         ② 某个温度的 MSD 还没进入线性扩散区（拟合区间没取对）；")
        print("         ③ 体系在某个温度发生了相变/熔化，不该用同一条 Arrhenius 线。")
    print("written: {} + {} + {}".format(csv, png, txt))
    if args.json:
        import json
        print(json.dumps({"command": "arrhenius", "n_points": len(T),
                          "slope": slope, "intercept": intercept, "R2": r2,
                          "Ea_eV": Ea, "Ea_kJmol": Ea * KJMOL_PER_EV,
                          "D0": D0, "axis": xlabel}, ensure_ascii=False))
    return 0


# ==========================================================================
# pmf-rdf：由 RDF 反推第一→第二配位层交换的能垒 w(r) = −RT·ln g(r)
# ==========================================================================
def _read_two_col(path):
    rows = []
    for ln in open(path, encoding="utf-8", errors="replace"):
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        p = s.replace(",", " ").split()
        if len(p) < 2:
            continue
        try:
            rows.append((float(p[0]), float(p[1])))
        except ValueError:
            continue
    return rows


def cmd_pmf_rdf(args):
    if not os.path.exists(args.rdf):
        print("\n[ERROR] 找不到 RDF 文件: {}".format(args.rdf), file=sys.stderr)
        print("  先跑 `postprocess.py rdf <traj.xyz> --cell \"a b c\"` 得到 `*_rdf.csv`。",
              file=sys.stderr)
        return 1
    rows = _read_two_col(args.rdf)
    if len(rows) < 3:
        print("\n[ERROR] {} 里没有可用的两列 (r, g) 数据。".format(args.rdf),
              file=sys.stderr)
        return 1
    r = np.array([x[0] for x in rows], dtype=float)
    g = np.array([x[1] for x in rows], dtype=float)
    if args.rmax:
        keep = r <= args.rmax
        r, g = r[keep], g[keep]
    # g → 0 时 ln g → −∞：加一个地板，避免 inf 污染整条曲线（并在输出里标注）
    floor = args.gfloor
    nzero = int(np.sum(g <= floor))
    gc = np.clip(g, floor, None)
    w_kj = -R_GAS * args.temp * np.log(gc) / 1000.0      # J/mol -> kJ/mol
    w_ev = w_kj / KJMOL_PER_EV
    prefix = args.prefix or os.path.splitext(os.path.basename(args.rdf))[0]
    csv = prefix + "_pmf.csv"
    write_csv(csv, "r[Angstrom],g(r),w[kJ/mol],w[eV]",
              [["{:.6f}".format(r[k]), "{:.8e}".format(g[k]),
                "{:.6f}".format(w_kj[k]), "{:.6f}".format(w_ev[k])]
               for k in range(len(r))])
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.plot(r, g, lw=1.4, color="steelblue", label="g(r)")
    ax.set_xlabel("r [Angstrom]")
    ax.set_ylabel("g(r)", color="steelblue")
    ax.tick_params(axis="y", labelcolor="steelblue")
    ax2 = ax.twinx()
    ax2.plot(r, w_kj, lw=1.4, color="crimson", label="w(r) = −RT ln g")
    ax2.set_ylabel("w(r) [kJ/mol]", color="crimson")
    ax2.tick_params(axis="y", labelcolor="crimson")
    ax.set_title("PMF from RDF:  w(r) = −RT·ln g(r),  T = {} K".format(args.temp))
    ax.grid(alpha=0.3)
    png = prefix + "_pmf.png"
    save_png(fig, png)
    print("由 RDF 反推自由能：w(r) = −R·T·ln g(r)")
    print("  T = {} K,  R = 8.314 J/(mol·K)  ⇒  w[r] 单位 kJ/mol 与 eV 双列".format(args.temp))
    print("  点数 {}，r 范围 {:.3f} ~ {:.3f} Å".format(len(r), r[0], r[-1]))
    if nzero:
        print("  [note] 有 {} 个点的 g ≤ {}（已夹到地板）——这些点的 w 值不可信，"
              "它们正是【概率密度为零】的区间".format(nzero, floor))
    imax = int(np.argmax(w_kj))
    print("  最大能垒位置 r = {:.4f} Å, w = {:.4f} kJ/mol = {:.4f} eV".format(
        r[imax], w_kj[imax], w_ev[imax]))
    print("  ⚠️ **局限（讲师原话「这个迁移能垒比较的局限」）**：只适用于"
          "「**第一配位层与第二配位层之间发生原子交换**」这一类过程，别的过程套不上。")
    print("written: {} + {}".format(csv, png))
    if args.json:
        import json
        print(json.dumps({"command": "pmf-rdf", "temp_K": args.temp,
                          "n_points": int(len(r)), "n_clipped": nzero,
                          "w_max_kJmol": float(w_kj[imax]),
                          "w_max_eV": float(w_ev[imax]),
                          "r_at_max_A": float(r[imax])}, ensure_ascii=False))
    return 0


# ==========================================================================
# dipoles：Wannier 中心 xyz → 每帧总偶极（TRAVIS 前置自检）
# ==========================================================================
def _parse_charges_arg(spec):
    """`"H=1,O=6"` 或 `"H:1,O:6"` → dict；**不做自动猜测**（G-07 明确要求必填）。"""
    out = {}
    for part in re.split(r"[,\s]+", spec.strip()):
        if not part:
            continue
        m = re.match(r"^([A-Za-z]{1,2})\s*[:=]\s*([-+]?\d+\.?\d*)$", part)
        if not m:
            raise ValueError("--nuclear-charges 每项要写成 `元素=电荷`（例 H=1,O=6），"
                             "实得 {!r}".format(part))
        out[m.group(1)] = float(m.group(2))
    if not out:
        raise ValueError("--nuclear-charges 为空")
    return out


def cmd_dipoles(args):
    try:
        qmap = _parse_charges_arg(args.nuclear_charges)
    except ValueError as e:
        print("\n[ERROR] " + str(e), file=sys.stderr)
        return 1
    elements, frames, times, _ = read_xyz(args.wannier)
    if frames.size == 0:
        print("[ERROR] {} 里没有帧。".format(args.wannier), file=sys.stderr)
        return 1
    uniq = sorted(set(elements))
    missing = [e for e in uniq if e not in qmap and e != "X"]
    if missing:
        print("", file=sys.stderr)
        print("[ERROR] 轨迹里有元素没给核电荷: {}".format(", ".join(missing)),
              file=sys.stderr)
        print("  ⚠️ 本命令**刻意不做自动猜测** —— 基组/赝势的有效电荷不是原子序数，"
              "猜错会让偶极整体平移。", file=sys.stderr)
        print("  例: --nuclear-charges \"H=1,O=6\"", file=sys.stderr)
        return 1
    nX = sum(1 for e in elements if e == "X")
    if nX == 0:
        print("", file=sys.stderr)
        print("[ERROR] 这个 xyz 里**没有 Wannier 中心（元素符号 `X` 的行）**，"
              "算不了偶极。", file=sys.stderr)
        print("  处方：在 `&DFT` 下加 `&LOCALIZE`（`METHOD CRAZY` + "
              "`&PRINT/&WANNIER_CENTERS ON`），并开 `IONS+CENTERS`、"
              "`FILENAME = wannier.xyz`、`&EACH MD 1`。", file=sys.stderr)
        print("  不能拿 `cp2k-pos-1.xyz` 来跑（那里只有原子核、没有 X）。",
              file=sys.stderr)
        return 1
    idx_nuc = [k for k, e in enumerate(elements) if e != "X"]
    idx_X = [k for k, e in enumerate(elements) if e == "X"]
    qn = np.array([qmap[elements[k]] for k in idx_nuc], dtype=float)
    mu = np.zeros((len(frames), 3))
    for fi in range(len(frames)):
        f = frames[fi]
        # 正电中心: Σ Z_i r_i ; 负电中心: Σ (-2e) r_X  （成对电子带 2 个电荷，vn5 L137）
        pos = (qn[:, None] * f[idx_nuc]).sum(axis=0)
        neg = -2.0 * f[idx_X].sum(axis=0)
        mu[fi] = pos + neg
    if times is not None:
        t = times
    else:
        t = np.arange(len(frames)) * (args.dt or 1.0)
    mag = np.linalg.norm(mu, axis=1)
    prefix = args.prefix or os.path.splitext(os.path.basename(args.wannier))[0]
    csv = prefix + "_dipoles.csv"
    write_csv(csv, "time[ps],mux[ebohr],muy[ebohr],muz[ebohr],|mu|[ebohr]",
              [["{:.6f}".format(t[k])] + ["{:.8f}".format(mu[k, j]) for j in range(3)]
               + ["{:.8f}".format(mag[k])] for k in range(len(frames))])
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2))
    for j, lab in enumerate(("mu_x", "mu_y", "mu_z")):
        ax[0].plot(t, mu[:, j], lw=1.0, label=lab)
    ax[0].set_xlabel("time [ps]")
    ax[0].set_ylabel("dipole [e·Angstrom]")
    ax[0].set_title("Total dipole vs time (nuclear + Wannier)")
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3)
    ax[1].hist(mag, bins=args.hbins, color="teal", alpha=0.8)
    ax[1].set_xlabel("|mu| [e·Angstrom]")
    ax[1].set_ylabel("count")
    ax[1].set_title("|mu| distribution")
    save_png(fig, prefix + "_dipoles.png")
    print("偶极自检（TRAVIS 前置 sanity check）：{} 帧, {} 个原子核 + {} 个 Wannier 中心".format(
        len(frames), len(idx_nuc), nX))
    print("  |μ| 均值 = {:.6f} e·Å, 标准差 = {:.6f} e·Å".format(
        float(mag.mean()), float(mag.std())))
    print("  各分量标准差: x={:.6f}  y={:.6f}  z={:.6f} e·Å".format(
        *[float(mu[:, j].std()) for j in range(3)]))
    if mag.std() < 1e-9:
        print("", file=sys.stderr)
        print("[WARN] 偶极是一条**直线**（标准差 ≈ 0）—— 轨迹里没有偶极起伏，",
              file=sys.stderr)
        print("       说明 `&LOCALIZE`/`IONS+CENTERS` 没生效，或每帧都在重复同一结构。",
              file=sys.stderr)
        print("       拿这条轨迹去跑 TRAVIS 是白跑。", file=sys.stderr)
    print("  ⚠️ 本命令**不替代** TRAVIS（TRAVIS 还要做 ACF + 变换、Raman/VCD），"
          "只是跑之前先看有没有偶极起伏。")
    print("  ⚠️ 单位是 e·Å（取核电荷为 e 单位）；核电荷**由你显式给出**，脚本不猜。")
    print("written: {} + {}".format(csv, prefix + "_dipoles.png"))
    if args.json:
        import json
        print(json.dumps({"command": "dipoles", "n_frames": len(frames),
                          "n_wannier": nX, "n_nuclei": len(idx_nuc),
                          "mu_mean": float(mag.mean()), "mu_std": float(mag.std()),
                          "flat": bool(mag.std() < 1e-9)}, ensure_ascii=False))
    return 0


# --------------------------------------------------------------------------
# bridge: bader
# --------------------------------------------------------------------------
def cmd_bader(args):
    binpath = shutil.which("bader") or args.bader_bin
    if not binpath:
        print("ERROR: 未检测到 bader 可执行文件。")
        print("  安装: 见 http://theory.cm.utexas.edu/bader/ ; 放入 PATH 后重跑。")
        print(f"  等价手动命令: bader {args.cube}")
        return 1
    import subprocess
    print(f"running: bader {args.cube}")
    r = subprocess.run([binpath, args.cube], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("bader 运行失败:\n" + r.stderr)
        return 1
    acf = os.path.join(os.path.dirname(args.cube) or ".", "ACF.dat")
    if not os.path.exists(acf):
        print("bader 完成, 但未找到 ACF.dat(检查工作目录)。")
        return 0
    prefix = out_prefix(args)
    rows = []
    for ln in open(acf, encoding="utf-8", errors="replace"):
        parts = ln.split()
        if len(parts) >= 7 and parts[0].isdigit():
            rows.append([parts[0], parts[1], parts[-3], parts[-2], parts[-1]])
    csv = prefix + "_bader.csv"
    write_csv(csv, "atom,label,charge,min_dist,vol[A^3]", rows)
    print(f"Bader 电荷已写出: {csv}")
    return 0


# --------------------------------------------------------------------------
# bridge: fes (metadynamics free energy surface)
# --------------------------------------------------------------------------
def _plot_fes(fesdat, prefix, ndim_actual):
    data = []
    for ln in open(fesdat, encoding="utf-8", errors="replace"):
        parts = ln.split()
        if len(parts) < 2:
            continue
        try:
            vals = [float(x) for x in parts]
        except ValueError:
            continue
        data.append(vals)
    data = np.array(data)
    # 列: 前 ndim 为 CV, 最后一列能量(Hartree)
    ncv = data.shape[1] - 1
    cv = data[:, :ncv]
    E = data[:, -1] * 2625.5  # Hartree -> kJ/mol
    fig, ax = plt.subplots(figsize=(7, 5))
    if ncv == 1:
        order = np.argsort(cv[:, 0])
        ax.plot(cv[order, 0], E[order], lw=1.3)
        ax.set_xlabel("CV")
        ax.set_ylabel("F [kJ/mol]")
    elif ncv == 2:
        ax.tricontourf(cv[:, 0], cv[:, 1], E, levels=30, cmap="viridis")
        ax.set_xlabel("CV1")
        ax.set_ylabel("CV2")
        cbar = fig.colorbar(ax.collections[0], ax=ax)
        cbar.set_label("F [kJ/mol]")
    else:
        ax.scatter(cv[:, 0], cv[:, 1], c=E, cmap="viridis", s=8)
        ax.set_xlabel("CV1"); ax.set_ylabel("CV2")
    ax.set_title("Free energy surface (from fes.dat)")
    save_png(fig, prefix + "_fes.png")
    print(f"FES 图已写出: {prefix}_fes.png (dimension={ncv})")


def cmd_fes(args):
    if args.fesdat:
        # 直接对已有 fes.dat 出图
        prefix = out_prefix(args)
        _plot_fes(args.fesdat, prefix, None)
        print(f"written: {prefix}_fes.png")
        return 0
    binpath = shutil.which("graph.psmp") or shutil.which("graph.popt") or shutil.which("graph.sopt") or args.graph_bin
    if not binpath:
        print("ERROR: 未检测到 CP2K graph 工具(graph.psmp/popt/sopt)。")
        print("  该工具在 CP2K 源码 tools/ 目录编译产物; 放入 PATH 或 --graph-bin 指定。")
        print(f"  等价命令: graph -cp2k -ndim {args.ndim} -ndw {args.ndw} -file {args.restart}")
        return 1
    import subprocess
    cmd = [binpath, "-cp2k", "-ndim", str(args.ndim), "-ndw"] + [str(x) for x in args.ndw] + ["-file", args.restart]
    print("running: " + " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("graph 运行失败:\n" + r.stderr)
        return 1
    if not os.path.exists("fes.dat"):
        print("graph 完成但未生成 fes.dat。")
        return 1
    prefix = out_prefix(args)
    _plot_fes("fes.dat", prefix, args.ndim)
    print(f"written: {prefix}_fes.png")
    return 0


# --------------------------------------------------------------------------
# bridge: travis (spectra)
# --------------------------------------------------------------------------
def _scan_xyz_head(path, max_frames=2):
    """轻量扫 xyz 头若干帧（**不读全文**，大轨迹也秒回）。

    返回 ``(元素集合, 已读帧数, 每帧原子数, 是否有 X 行, 错误串)``。
    """
    if not os.path.exists(path):
        return None, 0, None, False, "找不到轨迹文件 {}".format(path)
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError as exc:
        return None, 0, None, False, "打不开 {}: {}".format(path, exc)
    elems, nframes, nat, hasX = set(), 0, None, False
    with fh:
        while nframes < max_frames:
            head = fh.readline()
            if not head:
                break
            head = head.strip()
            if not head:
                continue
            try:
                n = int(head)
            except ValueError:
                continue                     # 非"原子数"行 ⇒ 跳过（容错前导注释）
            nat = n
            fh.readline()                    # 注释行
            for _k in range(n):
                ln = fh.readline()
                if not ln:
                    break
                p = ln.split()
                if not p:
                    continue
                if p[0] == "X":
                    hasX = True
                else:
                    elems.add(p[0])
            nframes += 1
    return elems, nframes, nat, hasX, None


def cmd_travis(args):
    binpath = shutil.which("travis") or args.travis_bin
    # --- 前置检查（G-06：把本讲重复率最高的三个坑做成运行时提示）---
    elems, nframes, nat, hasX, err = _scan_xyz_head(args.traj, 2)
    analyses = [str(a).lower() for a in (args.analyses or [])]
    want_ir = any(a in ("ir", "raman", "vcd", "roa") for a in analyses)
    # 三态语义（必须区分"默认"与"显式 --no-require-x"）：
    #   args.require_x is True  → 用户显式要求检查（--require-x）
    #   args.require_x is False → 用户显式**放弃**检查（--no-require-x）
    #   args.require_x is None  → 默认启发式：算 IR/Raman/VCD/ROA 才要求有 X
    if args.require_x is True:
        need_x = True
    elif args.require_x is False:
        need_x = False
    else:
        need_x = want_ir
    if err:
        print("", file=sys.stderr)
        print("[ERROR] TRAVIS 前置检查失败：" + err, file=sys.stderr)
        return 1
    if not hasX and need_x:
        print("", file=sys.stderr)
        print("=" * 72, file=sys.stderr)
        print("[ERROR] 轨迹里**没有 Wannier 中心（元素符号 X 的行）**，"
              "TRAVIS 算不了真 IR。", file=sys.stderr)
        print("        轨迹: {}（读了 {} 帧，每帧 {} 个原子，元素 {}）".format(
            args.traj, nframes, nat, ", ".join(sorted(elems)) or "?"),
            file=sys.stderr)
        print("", file=sys.stderr)
        print("  处方（三步都要做，缺一不可）：", file=sys.stderr)
        print("    1) 在 `&FORCE_EVAL/&DFT` 下加 `&LOCALIZE`（讲师用 `METHOD CRAZY`）；",
              file=sys.stderr)
        print("    2) `&PRINT/&WANNIER_CENTERS ON` 里开 `IONS+CENTERS`"
              "（官方默认 F —— 不开就只有 X、没有原子核）；", file=sys.stderr)
        print("    3) 同段写 `FILENAME = wannier.xyz` + `&EACH MD 1`"
              "（写 `QS_SCF 10` 会只出 1 帧）。", file=sys.stderr)
        print("    生成入口：`python scripts/gen_inp.py --type aimd_md "
              "--properties wannier`", file=sys.stderr)
        print("", file=sys.stderr)
        print("  ⚠️ **不能拿 `cp2k-pos-1.xyz` 去跑 TRAVIS** —— 那里只有原子核、"
              "没有带负电的电子中心，", file=sys.stderr)
        print("     没有 X 就没有偶极变化，算出来的不是红外谱（`S5.txt:123–132`）。",
              file=sys.stderr)
        print("     若只想跑 rdf/msd 这类不需要偶极的分析，加 `--no-require-x` 放行。",
              file=sys.stderr)
        print("=" * 72, file=sys.stderr)
        return 1
    if not hasX:
        print("", file=sys.stderr)
        print("[WARN] 轨迹里没有 Wannier 中心 `X`。当前 --analyses {} 不需要偶极，"
              "所以放行；".format(" ".join(analyses)), file=sys.stderr)
        print("       但**若要算 IR / Raman / VCD / ROA，必须先加 `&LOCALIZE` "
              "让轨迹带上 X**。", file=sys.stderr)
    # 生成控制文件
    prefix = out_prefix(args)
    ctrl = prefix + ".travis.in"
    with open(ctrl, "w", encoding="utf-8") as f:
        f.write(f"TITLE\n  CP2K postprocess TRAVIS job\nEND\n")
        f.write(f"TIMESTEP\n  {args.dt}\nEND\n")
        f.write(f"COORDINATE_FORMAT\n  XYZ\nEND\n")
        f.write(f"COORDINATE_FILE\n  {args.traj}\nEND\n")
        if args.vel:
            f.write(f"VELOCITY_FILE\n  {args.vel}\nEND\n")
        if args.cell:
            # G-06 第 3 条：控制文件里补 CELL 段（与其它子命令 --cell 语义一致，Å）
            c = parse_cell_arg(args.cell)
            a = float(np.linalg.norm(c[0])); b = float(np.linalg.norm(c[1]))
            cc = float(np.linalg.norm(c[2]))
            al = math.degrees(math.acos(max(-1.0, min(1.0,
                float(np.dot(c[1], c[2]) / (b * cc))))))
            be = math.degrees(math.acos(max(-1.0, min(1.0,
                float(np.dot(c[0], c[2]) / (a * cc))))))
            ga = math.degrees(math.acos(max(-1.0, min(1.0,
                float(np.dot(c[0], c[1]) / (a * b))))))
            f.write("CELL\n  {:.6f} {:.6f} {:.6f} {:.4f} {:.4f} {:.4f}\nEND\n".format(
                a, b, cc, al, be, ga))
        f.write("OUTPUT\n  " + prefix + "\nEND\n")
        f.write("BEGIN ANALYSIS\n")
        for a in args.analyses:
            f.write("  " + a.upper() + "\n")
        f.write("END\n")
    print(f"TRAVIS 控制文件已生成: {ctrl}")
    if not args.cell:
        print("  [note] 未给 --cell ⇒ 控制文件里**没有 CELL 段**；"
              "交互式运行 TRAVIS 时它会问晶胞边长。")
    print("  ⚠️ **单位坑**：TRAVIS 交互式提问的晶胞长度单位是 **pm**（水盒输 782、"
          "不是 7.82）——讲义原话「这个边界要输的是皮米」（`S5.txt:149–159`）。")
    print("  偶极模式选 `1`（Wannier 中心方式，每个 X 带 2 个电荷）。")
    if not binpath:
        print("ERROR: 未检测到 travis 可执行文件(https://www.travis-analyzer.de/)。")
        print("  安装后重跑本命令即可自动执行; 控制文件已备好。")
        return 1
    import subprocess
    r = subprocess.run([binpath, ctrl], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("travis 运行失败:\n" + r.stderr)
        return 1
    print("travis 运行完成, 输出见 " + prefix + "_*.csv")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def add_io(parser):
    parser.add_argument("--prefix", default=None, help="输出文件前缀(默认用输入名派生)")
    parser.add_argument("--cell", default=None,
                        help="晶胞: 'a b c' 或 'ax ay az bx by bz cx cy cz' (Å)。"
                             "**周期体系必须显式给**——不给会退化为 NON-PBC(包围盒近似)，"
                             "RDF/MSD/ADF/CN/zprofile 的结果不可靠（输出里会标 NON-PBC 提醒）")
    parser.add_argument("--json", action="store_true",
                        help="输出 JSON（给 agent 用；列出产物路径与统计）")


def build_parser():
    p = argparse.ArgumentParser(description="CP2K 后处理引擎")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("energy", help="能量/温度曲线")
    sp.add_argument("out")
    add_io(sp)
    sp.set_defaults(func=cmd_energy)

    sp = sub.add_parser("rdf", help="径向分布函数 g(r)")
    sp.add_argument("traj")
    sp.add_argument("--pairs", nargs="*", default=None, help='元素对, 如 "O O" "O H"')
    sp.add_argument("--rmax", type=float, default=10.0)
    sp.add_argument("--bins", type=int, default=200)
    add_io(sp)
    sp.set_defaults(func=cmd_rdf)

    sp = sub.add_parser("msd", help="均方位移")
    sp.add_argument("traj")
    sp.add_argument("--sel", default=None, help="元素符号或索引区间 '1..10'")
    sp.add_argument("--dim", type=int, default=3, choices=[1, 2, 3])
    sp.add_argument("--dt", type=float, default=None, help="步长(ps), 缺省用轨迹注释")
    sp.add_argument("--align", nargs="?", const="rest", default=None, metavar="SEL",
                    help="做刚体对齐消除骨架整体漂移(讲师: 算 MSD 前必须 align)。"
                         "不给值 = 'rest' = 以**除 --sel 以外的骨架原子**为参考组；"
                         "也可显式给元素/索引区间；写 'all' = 对全体系对齐")
    add_io(sp)
    sp.set_defaults(func=cmd_msd)

    sp = sub.add_parser("diffusion", help="扩散系数 D (Einstein)")
    sp.add_argument("traj")
    sp.add_argument("--sel", default=None)
    sp.add_argument("--dim", type=int, default=3, choices=[1, 2, 3])
    sp.add_argument("--dt", type=float, default=None)
    sp.add_argument("--fit-lo", type=float, default=0.2)
    sp.add_argument("--fit-hi", type=float, default=0.8)
    sp.add_argument("--align", nargs="?", const="rest", default=None, metavar="SEL",
                    help="同 msd；给了会**同时输出对齐前后的 D 对比**（判断漂移是否显著）")
    add_io(sp)
    sp.set_defaults(func=cmd_diffusion)

    sp = sub.add_parser("bond", help="键长时间序列+分布")
    sp.add_argument("traj")
    sp.add_argument("--i", type=int, required=True)
    sp.add_argument("--j", type=int, required=True)
    sp.add_argument("--hbins", type=int, default=40)
    add_io(sp)
    sp.set_defaults(func=cmd_bond)

    sp = sub.add_parser("angle", help="键角时间序列+分布")
    sp.add_argument("traj")
    sp.add_argument("--i", type=int, required=True)
    sp.add_argument("--j", type=int, required=True)
    sp.add_argument("--k", type=int, required=True)
    sp.add_argument("--hbins", type=int, default=40)
    add_io(sp)
    sp.set_defaults(func=cmd_angle)

    sp = sub.add_parser("dihedral", help="二面角时间序列+分布")
    sp.add_argument("traj")
    sp.add_argument("--i", type=int, required=True)
    sp.add_argument("--j", type=int, required=True)
    sp.add_argument("--k", type=int, required=True)
    sp.add_argument("--l", type=int, required=True)
    sp.add_argument("--hbins", type=int, default=40)
    add_io(sp)
    sp.set_defaults(func=cmd_dihedral)

    sp = sub.add_parser("pdos", help="态密度/投影态密度绘图")
    sp.add_argument("pdos", help=".pdos 文件或含 .pdos 的目录")
    sp.add_argument("--fermi", type=float, default=None, help="费米能级(eV); 缺省自动检测")
    sp.add_argument("--broaden", type=float, default=0.1, help="展宽 σ (eV)")
    sp.add_argument("--de", type=float, default=0.01, help="能量网格步长 (eV)")
    add_io(sp)
    sp.set_defaults(func=cmd_pdos)

    sp = sub.add_parser("adf", help="角分布函数")
    sp.add_argument("traj")
    sp.add_argument("--center", required=True, help="中心原子元素")
    sp.add_argument("--rcut", type=float, default=3.5)
    sp.add_argument("--bins", type=int, default=180)
    add_io(sp)
    sp.set_defaults(func=cmd_adf)

    sp = sub.add_parser("cn", help="配位数(从 rdf 积分)")
    sp.add_argument("traj")
    sp.add_argument("--pairs", nargs="*", default=None)
    sp.add_argument("--rcut", type=float, default=3.5)
    sp.add_argument("--bins", type=int, default=200)
    add_io(sp)
    sp.set_defaults(func=cmd_cn)

    sp = sub.add_parser("zprofile", help="轴向密度剖面")
    sp.add_argument("traj")
    sp.add_argument("--bins", type=int, default=100)
    sp.add_argument("--sel", default=None,
                    help="按元素/索引筛（如 --sel H）；默认全原子（向后兼容）")
    add_io(sp)
    sp.set_defaults(func=cmd_zprofile)

    sp = sub.add_parser("vacf", help="速度自相关函数")
    sp.add_argument("--vel", default=None, help="速度 xyz(CP2K -vel-1.xyz)")
    sp.add_argument("--traj", default=None, help="位置轨迹(差分近似速度)")
    sp.add_argument("--dt", type=float, default=None)
    sp.add_argument("--sel", default=None,
                    help="选区：元素符号或索引区间 '1..10'。大体系只算关心的"
                         "分子/官能团，否则峰太多看不清；归一分母同步改为选中原子数")
    add_io(sp)
    sp.set_defaults(func=cmd_vacf)

    sp = sub.add_parser("ir", help="红外/振动态密度(FFT of VACF)")
    sp.add_argument("--vel", default=None)
    sp.add_argument("--traj", default=None)
    sp.add_argument("--dt", type=float, default=None)
    sp.add_argument("--sel", default=None, help="同 vacf")
    add_io(sp)
    sp.set_defaults(func=cmd_ir)

    sp = sub.add_parser("power", help="功率谱(= ir)")
    sp.add_argument("--vel", default=None)
    sp.add_argument("--traj", default=None)
    sp.add_argument("--dt", type=float, default=None)
    sp.add_argument("--sel", default=None, help="同 vacf")
    add_io(sp)
    sp.set_defaults(func=cmd_power)

    # ---------------- cube 类（G-03/G-04/G-05 的共同底座）----------------
    sp = sub.add_parser("cube", help="Gaussian cube 平面平均(任意轴)")
    sp.add_argument("cubes", nargs="+", help="一个或多个 .cube"
                                             "(E_DENSITY_CUBE/V_HARTREE_CUBE/ELF_CUBE/MO_CUBES)")
    sp.add_argument("--axis", type=_cube_axis_arg, default="z",
                    help="x|y|z|xy|xz|yz（xy = 对 x、y 求平均 ⇒ 横坐标是 z）；默认 z")
    sp.add_argument("--show-std", action="store_true",
                    help="单文件时叠加面内 ±1σ 阴影带（看面内起伏有多大）")
    add_io(sp)
    sp.set_defaults(func=cmd_cube)

    sp = sub.add_parser("cdd", help="电荷密度差分 Δρ = ρ_AB − Σρ_frag")
    sp.add_argument("--total", required=True, help="整体(或吸附后)的 cube")
    sp.add_argument("--frag", nargs="+", required=True,
                    help="片段 cube（每个片段各一份；变形电荷密度就传孤立原子密度）")
    sp.add_argument("--planar-axis", default=None,
                    choices=["x", "y", "z", "xy", "xz", "yz"],
                    help="给了就再做一次平面平均并出图")
    sp.add_argument("--out-cube", default=None, help="差分 cube 的输出名")
    sp.add_argument("--deformation", action="store_true",
                    help="按【变形电荷密度】ρ_SCF − Σρ_孤立原子 理解（算法完全相同，"
                         "只是语义提示）。⚠️ 两个片段一定不要再单独优化")
    add_io(sp)
    sp.set_defaults(func=cmd_cdd)

    sp = sub.add_parser("workfunc", help="功函 Φ = E_vac − E_F → 相对 SHE 的电极电势")
    sp.add_argument("cube", help="Hartree 势 cube（`V_HARTREE_CUBE` 产出）")
    sp.add_argument("--out", default=None, help="CP2K .out（解析费米能级）")
    sp.add_argument("--fermi", type=float, default=None,
                    help="直接给费米能级(eV)，跳过 .out 解析")
    sp.add_argument("--axis", type=_cube_axis_arg, default="z")
    sp.add_argument("--vacuum-window", type=float, default=2.0,
                    help="判真空平台的滑窗宽度(Å)，默认 2.0")
    sp.add_argument("--slope-tol", type=float, default=0.01,
                    help="判定「平坦」的阈值 |dV/dz| (eV/Å)，默认 0.01")
    sp.add_argument("--warn-grad", type=float, default=0.05,
                    help="超过该 |dV/dz| (eV/Å) 就警告「真空位倾斜」，默认 0.05")
    sp.add_argument("--she", type=float, default=SHE_EV,
                    help="SHE 绝对电势(eV)，默认 {}（讲义口径，别乱改）".format(SHE_EV))
    add_io(sp)
    sp.set_defaults(func=cmd_workfunc)

    sp = sub.add_parser("ir-static", help="静态 IR(频率+强度 → 高斯展宽)")
    sp.add_argument("freqfile", help="含 VIB|Frequency / VIB|Intensities 的 cp2k .out")
    sp.add_argument("--fwhm", type=float, default=20.0, help="高斯展宽 FWHM (cm^-1)")
    sp.add_argument("--df", type=float, default=1.0, help="频率网格步长 (cm^-1)")
    sp.add_argument("--fmax", type=float, default=None, help="横轴上限 (cm^-1)")
    add_io(sp)
    sp.set_defaults(func=cmd_ir_static)

    sp = sub.add_parser("arrhenius", help="多温度 D → Ea 与 D0")
    sp.add_argument("--d", nargs="*", default=None,
                    help='多组 (T:D)，如 --d "600:1e-6" "800:5e-6" "1000:2e-5"')
    sp.add_argument("--diffusion", nargs="*", default=None,
                    help="若干 *_diffusion.txt（文件里必须能读到 D 和 `T=... K`）")
    sp.add_argument("--per-1000t", action="store_true",
                    help="用讲义的 log10(D) vs 1000/T 横轴（斜率 = −Ea/(2.303·k_B)）")
    sp.add_argument("--kb", type=float, default=KB_EV,
                    help="玻尔兹曼常数(eV/K)，默认 {}".format(KB_EV))
    add_io(sp)
    sp.set_defaults(func=cmd_arrhenius)

    sp = sub.add_parser("pmf-rdf", help="由 RDF 反推能垒 w(r) = −RT·ln g(r)")
    sp.add_argument("rdf", help="rdf 子命令产出的 *_rdf.csv（两列 r,g）")
    sp.add_argument("--temp", type=float, required=True, help="实际模拟温度 (K)")
    sp.add_argument("--rmax", type=float, default=None, help="只算到该 r (Å)")
    sp.add_argument("--gfloor", type=float, default=1e-6,
                    help="ln g 的地板（g 小于它按它算），默认 1e-6")
    add_io(sp)
    sp.set_defaults(func=cmd_pmf_rdf)

    sp = sub.add_parser("dipoles", help="Wannier 中心 → 每帧偶极(TRAVIS 前置自检)")
    sp.add_argument("wannier", help="含 X 行的 wannier.xyz")
    sp.add_argument("--nuclear-charges", required=True,
                    help='核电荷，如 "H=1,O=6"（**必填，脚本不自动猜**）')
    sp.add_argument("--dt", type=float, default=None, help="无 time 注释时的步长(ps)")
    sp.add_argument("--hbins", type=int, default=40)
    add_io(sp)
    sp.set_defaults(func=cmd_dipoles)

    sp = sub.add_parser("bader", help="Bader 电荷(需 bader 二进制)")
    sp.add_argument("cube", help="电子密度 cube (--properties cube 产出)")
    sp.add_argument("--bader-bin", default=None)
    add_io(sp)
    sp.set_defaults(func=cmd_bader)

    sp = sub.add_parser("fes", help="元动力学自由能面(需 CP2K graph)")
    sp.add_argument("--restart", default=None, help="metadyn restart 文件")
    sp.add_argument("--fesdat", default=None, help="直接对已有 fes.dat 出图")
    sp.add_argument("--ndim", type=int, default=2, help="实际 CV 维数(务必填真实值!)")
    sp.add_argument("--ndw", nargs="+", type=int, default=[1, 2], help="投影到的 CV")
    sp.add_argument("--graph-bin", default=None)
    add_io(sp)
    sp.set_defaults(func=cmd_fes)

    sp = sub.add_parser("travis", help="TRAVIS 谱学桥接(需 travis 二进制)")
    sp.add_argument("traj")
    sp.add_argument("--vel", default=None)
    sp.add_argument("--analyses", nargs="+", default=["rdf", "msd"], help="如 rdf msd ir")
    sp.add_argument("--dt", type=float, default=1.0)
    sp.add_argument("--travis-bin", default=None)
    sp.add_argument("--require-x", dest="require_x", action="store_true",
                    default=None,
                    help="强制要求轨迹里有 Wannier 中心 X（默认：analyses 含 ir/raman/"
                         "vcd/roa 时自动要求）")
    sp.add_argument("--no-require-x", dest="require_x", action="store_false",
                    help="即使算 IR 也不检查 X（不推荐）")
    add_io(sp)
    sp.set_defaults(func=cmd_travis)

    return p


def main():
    p = build_parser()
    args = p.parse_args()
    if not getattr(args, "cmd", None):
        p.print_help()
        print("\n提示：先选一个子命令，例如："
              "python postprocess.py energy cp2k.out", file=sys.stderr)
        return 2
    want_json = bool(getattr(args, "json", False))
    # --json 模式下抑制子命令的散装 stdout，最后统一输出一个 JSON
    real_stdout = sys.stdout
    if want_json:
        import io
        sys.stdout = io.StringIO()
    try:
        rc = args.func(args)
    except FileNotFoundError as e:
        # 健壮性基线（CONTRIBUTING.md §3.4）：文件不存在 → 友好中文提示 + exit 1
        sys.stdout = real_stdout
        print(f"\n[ERROR] 找不到文件: {e.filename or e}", file=sys.stderr)
        print("  请检查路径是否正确；后处理命令需要 CP2K 的轨迹/输出/.pdos/.cube 文件。",
              file=sys.stderr)
        return 1
    except IsADirectoryError as e:
        sys.stdout = real_stdout
        print(f"\n[ERROR] 期望文件但给的是目录: {e.filename or e}", file=sys.stderr)
        return 1
    except PermissionError as e:
        sys.stdout = real_stdout
        print(f"\n[ERROR] 无权限读取: {e.filename or e}", file=sys.stderr)
        return 1
    except (ValueError, TypeError, KeyError, IndexError, ZeroDivisionError,
            np.linalg.LinAlgError) as e:
        # 数据本身有问题（cube 格点不自洽、数组形状对不上、晶胞奇异…）。
        # 这个兜底是**故意的**：健壮性基线要求"不抛 traceback"，而上面那三个
        # OSError 子类只挡文件问题。踩过实例：`_find_vacuum_plateau` 里写错
        # 元组下标（IndexError），用户看到的是 12 行 traceback 而不是提示。
        # 注意：**不**捕获 KeyboardInterrupt / SystemExit / MemoryError。
        sys.stdout = real_stdout
        print("", file=sys.stderr)
        print(f"[ERROR] 子命令 {args.cmd} 处理数据时失败："
              f"{type(e).__name__}: {e}", file=sys.stderr)
        print("  这通常是**输入数据的问题**（格点/形状/单位不自洽）而不是崩溃。",
              file=sys.stderr)
        print("  请核对：① 文件类型是否对得上子命令；② 尺寸/格点是否一致；"
              "③ `--cell` 是否给了正确的晶胞。", file=sys.stderr)
        print("  原始 traceback（供排查）：", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1

    if want_json:
        captured = sys.stdout.getvalue()
        sys.stdout = real_stdout
        import json
        print(json.dumps({
            "ok": rc == 0,
            "command": args.cmd,
            "outputs": _OUTPUTS,
            "stdout": captured[-4000:],
        }, ensure_ascii=False, indent=2))
    return rc


if __name__ == "__main__":
    sys.exit(main())
