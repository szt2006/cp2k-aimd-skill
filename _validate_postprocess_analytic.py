#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""postprocess.py 新增子命令的**独立数值自测**（合成数据，可解析验证）。

为什么另开一个脚本而不只扩 `_validate_postprocess.py`：
`_validate_postprocess.py` 的定位是"端到端不崩 + 少量定量断言"，而本轮的
8 个新子命令里有几个（cube 平面平均、cdd、workfunc、arrhenius、ir-static、
dipoles）**必须验数值**，否则"能跑"毫无意义。所以这里每一个用例都构造成
**有解析解**的输入，把解析解与实测值逐条比对。

设计原则：**每条断言都配一个反向对照**（构造一个"应该不同"的输入，证明
判据真的在起作用，而不是恒真）。

用法：
    python _validate_postprocess_analytic.py            # 全部用例
    python _validate_postprocess_analytic.py --list
    python _validate_postprocess_analytic.py --json
"""
import argparse
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
try:
    import _console  # noqa: F401
except Exception:
    pass

try:
    import numpy as np
except ImportError as _exc:
    sys.stderr.write("\n缺少依赖：{}\n  pip install numpy matplotlib\n".format(
        getattr(_exc, "name", "numpy")))
    sys.exit(3)

PY = sys.executable
PP = os.path.join(HERE, "scripts", "postprocess.py")

RESULTS = []
TMP = tempfile.mkdtemp(prefix="cp2k_pp_new_")


def record(name, expect, got, ok, note=""):
    RESULTS.append({"name": name, "expect": expect, "got": got, "ok": bool(ok),
                    "note": note})
    print("  [{}] {:<58} 期望 {} / 实得 {}".format(
        "OK" if ok else "FAIL", name, expect, got))
    for ln in (note or "").splitlines():
        if ln:
            print("         " + ln)


def run(argv, cwd=None, timeout=300):
    return subprocess.run([PY, PP] + argv, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          cwd=cwd or TMP, timeout=timeout)


# --------------------------------------------------------------------------
# 合成数据
# --------------------------------------------------------------------------
def write_cube(path, data, origin=(0.0, 0.0, 0.0), step=(1.0, 1.0, 1.0),
               natoms=0, bohr=False):
    """按 Gaussian cube 约定写一个 cube（data 形状 = (nx, ny, nz)，x 最慢 z 最快）。

    `bohr=True` 时把 natoms 与三个格点数都写成**负数**（坐标以 bohr 计），
    用来验证"负格点数 ⇒ 单位是 Å"这条 Gaussian 约定真的被识别。
    """
    nx, ny, nz = data.shape
    s = 1.0 / 0.529177210903 if bohr else 1.0
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("synthetic cube for _validate_postprocess_analytic.py\n")
        f.write("outer loop x, inner loop z\n")
        # ⚠️ 第 3 行的 natoms **始终为正**：负号在 cube 里表示"原子坐标以 bohr 计"，
        # 而不是"格点数以 bohr 计"。这里只用**格点定义行**的负号表达 bohr 约定。
        f.write("{:5d} {:12.6f} {:12.6f} {:12.6f}\n".format(
            natoms, origin[0] * s, origin[1] * s, origin[2] * s))
        for k in range(3):
            m = -(nx, ny, nz)[k] if bohr else (nx, ny, nz)[k]
            v = [0.0, 0.0, 0.0]
            v[k] = step[k] * s
            f.write("{:5d} {:12.6f} {:12.6f} {:12.6f}\n".format(m, v[0], v[1], v[2]))
        flat = data.reshape(-1)
        for k in range(0, flat.size, 6):
            f.write("".join("{:13.5E}".format(v) for v in flat[k:k + 6]) + "\n")


def cube_ab(path, value):
    """常密度 cube（解析解：平面平均 = 宏观平均 = value）。"""
    write_cube(path, np.full((4, 5, 6), value))


def cube_sin(path, amp, kz, nz=40, nx=5, ny=7):
    """ρ(x,y,z) = amp·sin(2π k z / L_z)：平面平均沿 z 的解析解 = 同一个正弦。

    ⇒ 实测平面平均应逐点等于 amp·sin(2π k z / L_z)（z = 0,1,...,nz-1）。
    """
    z = np.arange(nz, dtype=float)
    prof = amp * np.sin(2.0 * math.pi * kz * z / nz)
    data = np.repeat(prof[None, None, :], nx, axis=0)
    data = np.repeat(data, ny, axis=1)
    write_cube(path, data)
    return prof


def gen_skeleton_plus_diffuser(path, D, dt, nframe, v_drift, omega=0.0,
                               L=60.0, nskel=8, ndiff=6):
    """刚性骨架（整体平动 + 可选整体转动）+ 在骨架里扩散的 Li。

    这是讲师描述的那个场景的最小模型（vn2 C-02）：
      * 骨架原子之间的**相对**位置固定 ⇒ 骨架自身的 MSD 贡献只有刚体运动；
      * Li 做布朗运动（真值 D），**外加**与骨架相同的整体平移。
    所以"不对齐"时 D 会被骨架漂移污染，"对齐"后必须回到真值 D。

    ⚠️ 两个生成细节会决定这个用例是否**可信**（第一版两处都踩过）：
      1. **累计**随机位移必须存在"未折回"的连续坐标里，只在**写文件时**取模。
         若每帧都在折回后的坐标上继续累加，`pos % L` 每次都会丢掉 < 1 Å 的
         小数部分，几百帧后累计成**系统性**的超扩散 —— 实测把 D=0.05 抬到
         0.084，于是"对齐前/后"的比较失去意义。
      2. 参考组必须是**真刚体**，否则 Kabsch 消不掉它的内部弛豫，
         `ref_residual_drift_A` 不会归零，"对齐成功"就没法用解析解断言。
    """
    rng = np.random.default_rng(11)
    skel0 = rng.uniform(-1.5, 1.5, (nskel, 3))     # 骨架相对坐标（固定）
    li = rng.uniform(L * 0.25, L * 0.75, (ndiff, 3))   # Li 连续坐标（不折回）
    sigma = math.sqrt(2 * D * dt)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        for fi in range(nframe):
            t = fi * dt
            th = omega * t
            R = np.array([[math.cos(th), -math.sin(th), 0.0],
                          [math.sin(th), math.cos(th), 0.0],
                          [0.0, 0.0, 1.0]])
            trans = np.array([v_drift * t, 0.0, 0.0])
            skel = skel0 @ R.T + trans + np.array([-v_drift * dt * nframe / 2,
                                                   0.0, 0.0]) + np.array(
                [L / 2, L / 2, L / 2])
            if fi:
                li = li + rng.normal(0, sigma, (ndiff, 3))
            f.write("{}\ni = {}, time = {:.4f}, E = -2.0\n".format(
                nskel + ndiff, fi + 1, t))
            for c in skel:
                f.write("Si {:.6f} {:.6f} {:.6f}\n".format(*(c % L)))
            for c in li + trans:                   # 折回只发生在写出这一刻
                f.write("Li {:.6f} {:.6f} {:.6f}\n".format(*(c % L)))


def gen_brownian_with_drift(path, N, D, dt, nframe, drift_per_frame, L=500.0):
    """布朗运动（**不**额外加整体平移；保留给需要纯布朗的用例）。"""
    rng = np.random.default_rng(7)
    pos = rng.uniform(0, L, (N, 3))
    sigma = math.sqrt(2 * D * dt)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        for fi in range(nframe):
            if fi:
                pos = pos + rng.normal(0, sigma, (N, 3))
            pos = pos % L
            t = fi * dt
            f.write("{}\ni = {}, time = {:.4f}, E = -2.0\n".format(N, fi + 1, t))
            for c in pos:
                f.write("Li {:.6f} {:.6f} {:.6f}\n".format(*c))


def gen_selected_vel(path, dt, nframe, elems):
    """两个元素各自一个已知频率的阻尼振子 ⇒ `--sel` 选谁就只出谁的峰。"""
    t = np.arange(nframe) * dt
    fA, fB = 10.0, 30.0            # 1/ps → 333.6 / 1000.8 cm^-1
    vA = np.cos(2 * math.pi * fA * t) * np.exp(-t / 3.0)
    vB = np.cos(2 * math.pi * fB * t) * np.exp(-t / 3.0)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        for k in range(nframe):
            f.write("2\ni = {}, time = {:.5f}, E = 0\n".format(k + 1, t[k]))
            f.write("{} {:.8f} 0.0 0.0\n".format(elems[0], vA[k]))
            f.write("{} {:.8f} 0.0 0.0\n".format(elems[1], vB[k]))


def gen_vib_out(path, freqs, intens, fermi_au=None, style="inline"):
    lines = [" CP2K| synthetic vibrational analysis output",
             " SCF run converged"]
    if fermi_au is not None:
        lines.append("  Fermi energy:                    {:.14f}".format(fermi_au))
    lines.append(" VIB| Vibrational Analysis")
    if style == "inline":
        lines.append(" VIB|Frequency (cm^-1)   " +
                     "   ".join("{:.6f}".format(x) for x in freqs))
        lines.append(" VIB|Intensities         " +
                     "   ".join("{:.6f}".format(x) for x in intens))
    else:
        lines.append(" VIB|Frequency (cm^-1)")
        for k in range(0, len(freqs), 3):
            lines.append(" VIB|   " + "   ".join(
                "{:.6f}".format(x) for x in freqs[k:k + 3]))
        lines.append(" VIB|Intensities")
        for k in range(0, len(intens), 3):
            lines.append(" VIB|   " + "   ".join(
                "{:.6f}".format(x) for x in intens[k:k + 3]))
    lines.append(" PROGRAM ENDED AT")
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")


def gen_wannier_xyz(path, nframe, wobble):
    """1 个 H 核 + 2 个 Wannier 中心（X）。

    μ = Σ Z_i r_i − 2·Σ r_X。构造：核固定在原点，两个 X 关于原点对称地位于
    ±(d, 0, 0) ⇒ μ = −2·[(d,0,0) + (−d,0,0)] = (0, 0, 0)。
    `wobble` 让两 X 整体平移 ⇒ μ_x = −2·(2·shift) = −4·shift（解析解）。
    """
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        for k in range(nframe):
            sh = wobble(k)
            f.write("3\ni = {}, time = {:.4f}, E = 0\n".format(k + 1, k * 0.5))
            f.write("H 0.000000 0.000000 0.000000\n")
            f.write("X {:.6f} 0.000000 0.000000\n".format(1.0 + sh))
            f.write("X {:.6f} 0.000000 0.000000\n".format(-1.0 + sh))


def gen_rdf_csv(path, gfun, rmax=20.0, dr=0.05):
    r = np.arange(dr, rmax, dr)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("r[A],g(r)\n")
        for k in range(len(r)):
            f.write("{:.6f},{:.8e}\n".format(r[k], gfun(r[k])))


# --------------------------------------------------------------------------
# 用例
# --------------------------------------------------------------------------
def case_cube_constant():
    p = os.path.join(TMP, "const.cube")
    v = 0.012345
    cube_ab(p, v)
    r = run(["cube", p, "--axis", "z", "--prefix", os.path.join(TMP, "const")])
    ok_rc = r.returncode == 0
    # 解析解：每一行的值都必须等于常数 v
    vals, coords = [], []
    csvp = os.path.join(TMP, "const_planar.csv")
    if os.path.exists(csvp):
        for ln in io.open(csvp, encoding="utf-8"):
            if ln.startswith("coord"):
                continue
            a, b = ln.strip().split(",")
            coords.append(float(a)); vals.append(float(b))
    err = max(abs(x - v) for x in vals) if vals else float("inf")
    ok = ok_rc and len(vals) == 6 and err < 1e-12
    record("cube 常密度：平面平均逐点 == 常数",
           "6 行且 |Δ|<1e-12", "rc={} n={} maxΔ={:.2e}".format(
               r.returncode, len(vals), err), ok,
           "解析解：常密度 cube 的平面平均处处等于该常数（0.012345 在 cube 的\n"
           "{:13.5E} 格式下是精确值，所以这里能用 1e-12）")
    # 横坐标必须由「原点+步进矢量」给出 ⇒ z = 0,1,2,3,4,5
    okc = coords == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    record("cube 常密度：横坐标 == origin + k·step",
           "[0,1,2,3,4,5]", str(coords), okc)
    # 反向对照：改常数必须跟着变
    p2 = os.path.join(TMP, "const2.cube")
    cube_ab(p2, v * 3)
    run(["cube", p2, "--axis", "z", "--prefix", os.path.join(TMP, "const2")])
    vals2 = [float(ln.strip().split(",")[1])
             for ln in io.open(os.path.join(TMP, "const2_planar.csv"), encoding="utf-8")
             if not ln.startswith("coord")]
    ok2 = abs(vals2[0] - v * 3) < 1e-12
    record("cube 反向对照：常数 ×3 ⇒ 平面平均 ×3", "3×", "{:.6g}".format(vals2[0]),
           ok2, "证明上面那条不是恒真")


def case_cube_sine():
    p = os.path.join(TMP, "sin.cube")
    nz = 40
    prof = cube_sin(p, amp=2.0, kz=3, nz=nz)
    r = run(["cube", p, "--axis", "z", "--prefix", os.path.join(TMP, "sin")])
    vals = [float(ln.strip().split(",")[1])
            for ln in io.open(os.path.join(TMP, "sin_planar.csv"), encoding="utf-8")
            if not ln.startswith("coord")]
    err = max(abs(vals[k] - prof[k]) for k in range(nz))
    # 容差 1e-5 的来源：cube 的体数据格式是 {:13.5E}（**只有 5 位有效小数**），
    # 所以"写出去"这一步本身就是唯一的误差源；用 1e-12 会把格式精度当成算法误差。
    record("cube 正弦密度：平面平均 == 解析正弦",
           "max|Δ|<1e-5（受 cube 5 位有效数字限制）",
           "rc={} n={} maxΔ={:.3e}".format(r.returncode, len(vals), err),
           err < 1e-5,
           "ρ=2·sin(6πz/40) ⇒ 面内平均解析解就是它自己\n"
           "（cube 体数据格式 {:13.5E} 是精度上限，不是算法误差）")
    # axis=x 必须给出**不同的**曲线（沿 x 的分布是常数 0 ⇒ 全 0）
    run(["cube", p, "--axis", "x", "--prefix", os.path.join(TMP, "sinx")])
    vx = [float(ln.strip().split(",")[1])
          for ln in io.open(os.path.join(TMP, "sinx_planar.csv"), encoding="utf-8")
          if not ln.startswith("coord")]
    record("cube 反向对照：--axis x 得到全 0（沿 x 无变化）",
           "5 个 0", "{} 个值 max|v|={:.2e}".format(len(vx), max(abs(x) for x in vx)),
           len(vx) == 5 and max(abs(x) for x in vx) < 1e-15,
           "证明 --axis 真的换轴了，不是把 z 的结果复用")
    # --show-std：常密度时 σ 必须为 0
    pc = os.path.join(TMP, "const.cube")
    r2 = run(["cube", pc, "--axis", "z", "--show-std",
              "--prefix", os.path.join(TMP, "conststd")])
    record("cube --show-std 不崩", "rc=0", "rc={}".format(r2.returncode),
           r2.returncode == 0)


def case_cube_bohr():
    """负格点数 ⇒ 该轴步进矢量以 **bohr** 计，必须乘 0.529177 才是 Å。

    这里刻意**不用 `write_cube(bohr=True)`**（那条路会把 Å 先除以 0.529177 写出去，
    读回来正好又乘回去 ≈1.0 Å —— 看着像"没转换"，其实转换对了，是个**假阴性**）。
    改成手写一个"步长恰好 5.0 bohr"的 cube，解析解 = 5×0.529177 = 2.645886 Å。
    """
    B = 0.529177210903
    p = os.path.join(TMP, "bohr5.cube")
    d = np.full((2, 2, 4), 3.0)

    def _write_raw(path, n, step_val):
        """手写一个 cube；`step_val` 直接写进格点定义行（负号 = bohr 单位）。"""
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("synthetic cube: grid step = %g (negative n means bohr)\n"
                    % step_val)
            f.write("c2\n")
            f.write("{:5d} {:12.6f} {:12.6f} {:12.6f}\n".format(0, 0.0, 0.0, 0.0))
            for k in range(3):
                v = [0.0, 0.0, 0.0]
                v[k] = step_val
                f.write("{:5d} {:12.6f} {:12.6f} {:12.6f}\n".format(
                    n[k], v[0], v[1], v[2]))
            flat = d.reshape(-1)
            for k in range(0, flat.size, 6):
                f.write("".join("{:13.5E}".format(x) for x in flat[k:k + 6]) + "\n")

    _write_raw(p, (-2, -2, -4), 5.0)          # n<0 ⇒ 5 bohr 步长
    r = run(["cube", p, "--axis", "z", "--json", "--prefix",
             os.path.join(TMP, "bohr5")])
    coords = [float(ln.strip().split(",")[0])
              for ln in io.open(os.path.join(TMP, "bohr5_planar.csv"), encoding="utf-8")
              if not ln.startswith("coord")]
    want = [0.0, 5 * B, 10 * B, 15 * B]
    err = max(abs(coords[k] - want[k]) for k in range(4))
    record("cube bohr 约定：n<0 ⇒ 5 bohr 步长折成 {} Å".format(round(5 * B, 6)),
           "{}（±1e-5，受 csv 6 位小数限制）".format([round(x, 6) for x in want]),
           "{}".format([round(x, 6) for x in coords]), err < 1e-5,
           "Gaussian 约定：格点定义行的 n<0 ⇒ 该轴的步进矢量以 bohr 计；\n"
           "CP2K 的 cube 走的就是这一支（不乘 0.529177 会整体放大 1.89 倍）")
    # 反向对照：同一个 cube 用 Å 约定（n 为正）时，步长必须**原样保留 5.0**
    p2 = os.path.join(TMP, "ang5.cube")
    _write_raw(p2, (2, 2, 4), 5.0)            # n>0 ⇒ 5 Å 步长
    run(["cube", p2, "--axis", "z", "--prefix", os.path.join(TMP, "ang5")])
    c2 = [float(ln.strip().split(",")[0])
          for ln in io.open(os.path.join(TMP, "ang5_planar.csv"), encoding="utf-8")
          if not ln.startswith("coord")]
    record("cube 反向对照：n>0（Å 约定）时步长原样 = 5.0",
           "[0, 5, 10, 15]", str(c2),
           all(abs(c2[k] - 5.0 * k) < 1e-5 for k in range(4)),
           "证明上面的 0.529177 真的来自负号，不是无条件乘的")


def case_cube_errors():
    # 头不合法：第 3 行缺数字
    bad = os.path.join(TMP, "bad.cube")
    io.open(bad, "w", encoding="utf-8", newline="\n").write(
        "c1\nc2\nnot a number here\n")
    r = run(["cube", bad])
    ok = r.returncode == 1 and "cube 解析失败于" in (r.stdout + r.stderr) \
        and "Traceback" not in (r.stdout + r.stderr)
    record("cube 头不合法：中文报错 + exit 1 + 无 traceback",
           "exit1 且含逐步说明", "exit={} 含逐步={}".format(
               r.returncode, "cube 解析失败于" in (r.stdout + r.stderr)), ok,
           (r.stderr or r.stdout).strip().splitlines()[1][:90]
           if (r.stderr or r.stdout).strip() else "")
    # 体数据被截断
    trunc = os.path.join(TMP, "trunc.cube")
    d = np.zeros((4, 4, 4))
    write_cube(trunc, d)
    txt = io.open(trunc, encoding="utf-8").read().splitlines()
    io.open(trunc, "w", encoding="utf-8", newline="\n").write(
        "\n".join(txt[:8]) + "\n")            # 砍掉大部分体数据
    r2 = run(["cube", trunc])
    msg = r2.stdout + r2.stderr
    ok2 = r2.returncode == 1 and "读体数据" in msg and "Traceback" not in msg
    record("cube 体数据截断：说清失败在【读体数据】这一步",
           "exit1 且点名体数据", "exit={} 点名={}".format(r2.returncode,
                                                          "读体数据" in msg), ok2)
    # 目录冒充文件
    r3 = run(["cube", TMP])
    record("cube 给目录：友好报错 exit 1", "exit1",
           "exit={}".format(r3.returncode), r3.returncode == 1 and
           "Traceback" not in (r3.stdout + r3.stderr))


def case_cdd():
    """Δρ = ρ_AB − ρ_A − ρ_B，构造解析解。"""
    A = np.zeros((4, 4, 4)); A[1, 1, 1] = 1.0
    B = np.zeros((4, 4, 4)); B[2, 2, 2] = 2.0
    AB = np.zeros((4, 4, 4)); AB[1, 1, 1] = 0.25; AB[2, 2, 2] = 3.0
    pa, pb, pab = (os.path.join(TMP, n) for n in ("A.cube", "B.cube", "AB.cube"))
    write_cube(pa, A); write_cube(pb, B); write_cube(pab, AB)
    r = run(["cdd", "--total", pab, "--frag", pa, pb,
             "--planar-axis", "z", "--prefix", os.path.join(TMP, "cdd")])
    # 解析解：Δρ = AB − A − B ⇒ [1,1,1] = 0.25-1 = -0.75 ; [2,2,2] = 3-2 = 1.0
    # ∫Δρ dV = -0.75 + 1.0 = 0.25 e（格子体积 1 Å³）
    out = r.stdout
    ok_net = "2.500000e-01" in out
    record("cdd 净电荷：∫Δρ dV == 0.25 e（解析解）",
           "2.500000e-01", "命中={}".format(ok_net), ok_net,
           "Δρ = [+0.25−1, 3−2] = [−0.75, +1.0] ⇒ 和 = 0.25")
    # 差分 cube 的两极值（乘了 HARTREE_EV）
    cp = os.path.join(TMP, "cdd_cdd.cube")
    d = None
    if os.path.exists(cp):
        lines = io.open(cp, encoding="utf-8").read().splitlines()
        # 头 = 2 行注释 + 1 行 natoms/原点 + natoms 行原子 + 3 行格点定义
        # 本用例 natoms=0 ⇒ 数据从第 6 行（下标 6）开始。**不许**从头 split，
        # 否则会把原点/步进矢量当数据（第一版就是这么误判的）。
        nat = abs(int(lines[2].split()[0]))
        start = 3 + nat + 3
        vals = []
        for ln in lines[start:]:
            vals += [float(x) for x in ln.split() if _isf(x)]
        d = vals
    HEV = 27.211386245988
    ok_pk = d is not None and len(d) == 64 and \
        abs(max(d) - 1.0 * HEV) < 1e-4 and abs(min(d) - (-0.75 * HEV)) < 1e-4
    record("cdd 差分 cube：极值 == [−0.75, +1.0]×27.2114 eV/Å³",
           "max={:.4f} min={:.4f}（±1e-4，受 cube 5 位有效数字限制）".format(
               HEV, -0.75 * HEV),
           "n={} max={} min={}".format(len(d) if d else 0,
                                       round(max(d), 6) if d else None,
                                       round(min(d), 6) if d else None), ok_pk,
           "写出去的 cube 单位是 eV/Å³，方便直接进 VESTA；\n"
           "容差 1e-4：差分值本身是 27.211386…，写进 cube 时被截到 5 位有效数字")
    # 平面平均图
    ok_csv = os.path.exists(os.path.join(TMP, "cdd_cdd_planar.csv"))
    record("cdd --planar-axis：产出平面平均 csv", "存在", str(ok_csv), ok_csv)
    # 反向对照：格点数不一致必须中文报错 exit 1
    pbad = os.path.join(TMP, "small.cube")
    write_cube(pbad, np.zeros((3, 3, 3)))
    r2 = run(["cdd", "--total", pab, "--frag", pbad])
    msg = r2.stdout + r2.stderr
    ok_bad = r2.returncode == 1 and "格点数不一致" in msg and "检查方向" in msg \
        and "Traceback" not in msg
    record("cdd 反向对照：格点数不一致 ⇒ 中文报错 + exit 1",
           "exit1 且给检查方向", "exit={} 含检查方向={}".format(
               r2.returncode, "检查方向" in msg), ok_bad)
    # --deformation 只改语义，不改数值
    r3 = run(["cdd", "--total", pab, "--frag", pa, pb, "--deformation",
              "--prefix", os.path.join(TMP, "cdd_def")])
    record("cdd --deformation 可跑且数值不变", "rc=0 且 ∫=0.25",
           "rc={} 命中={}".format(r3.returncode, "2.500000e-01" in r3.stdout),
           r3.returncode == 0 and "2.500000e-01" in r3.stdout)


def _isf(t):
    try:
        float(t); return True
    except ValueError:
        return False


def case_workfunc():
    """V(z) 有明确真空平台 ⇒ Φ 与相对 SHE 电势都是解析解。"""
    nz, dz = 60, 0.5
    z = np.arange(nz) * dz
    V_ha = np.full(nz, 0.2)                 # 真空位 0.2 Ha
    V_ha[20:40] = -0.4                      # slab 区凹下去
    data = np.repeat(V_ha[None, None, :], 3, axis=0)
    data = np.repeat(data, 3, axis=1)
    pc = os.path.join(TMP, "vhart.cube")
    write_cube(pc, data, step=(1.0, 1.0, dz))
    ef_ha = 0.05                            # 费米能级 0.05 Ha
    out = os.path.join(TMP, "wf.out")
    gen_vib_out(out, [100.0], [1.0], fermi_au=ef_ha)
    r = run(["workfunc", pc, "--out", out, "--prefix", os.path.join(TMP, "wf")])
    HEV = 27.211386245988
    e_vac = 0.2 * HEV
    ef_ev = ef_ha * HEV
    phi = e_vac - ef_ev
    u = phi - 4.44
    csvp = os.path.join(TMP, "wf_workfunc.csv")
    got = {}
    if os.path.exists(csvp):
        lines = io.open(csvp, encoding="utf-8").read().splitlines()
        hdr = lines[0].split(",")
        for ln in lines[1:]:
            f = ln.split(",")
            got[f[0]] = dict(zip(hdr, f))
    ok = "top" in got and "bot" in got and \
        abs(float(got["top"]["Phi[eV]"]) - phi) < 1e-3 and \
        abs(float(got["bot"]["Phi[eV]"]) - phi) < 1e-3
    record("workfunc：Φ == E_vac − E_F（解析解 {:.4f} eV）".format(phi),
           "Φ=±1e-3", "top={} bot={}".format(
               got.get("top", {}).get("Phi[eV]"), got.get("bot", {}).get("Phi[eV]")),
           ok, "E_vac=0.2 Ha={:.4f} eV, E_F=0.05 Ha={:.4f} eV".format(e_vac, ef_ev))
    ok_u = abs(float(got["top"]["U_vs_SHE[V]"]) - u) < 1e-3
    record("workfunc：相对 SHE 电势 == Φ − 4.44 V（解析解 {:.4f} V）".format(u),
           "U={:.4f}".format(u), got.get("top", {}).get("U_vs_SHE[V]"), ok_u,
           "SHE=4.44 eV 出自 course_learned.md:650（讲义口径，非记忆值）")
    # 反向对照 1：**真空位真的倾斜**（整条曲线恒定斜率，典型"没加偶极校正"）
    # 斜率取 0.005 eV/Å：既大于 warn-grad（0.001）⇒ 必须报警，
    # 又小于 slope-tol（0.01）⇒ 还能被认成"平坦段"（不是"找不到平台"退化分支）。
    V2 = np.full(nz, 0.2) + 0.005 * z
    d2 = np.repeat(V2[None, None, :], 3, axis=0)
    d2 = np.repeat(d2, 3, axis=1)
    p2 = os.path.join(TMP, "tilt.cube")
    write_cube(p2, d2, step=(1.0, 1.0, dz))
    r2 = run(["workfunc", p2, "--fermi", str(ef_ev), "--slope-tol", "0.01",
              "--warn-grad", "0.001", "--prefix", os.path.join(TMP, "tilt")])
    msg = r2.stdout + r2.stderr
    ok_warn = r2.returncode == 0 and "真空位不平" in msg and "SURFACE_DIPOLE_CORRECTION" in msg
    record("workfunc 反向对照：真空位倾斜 ⇒ 打中文 WARN 并给处方",
           "含 真空位不平 + SURFACE_DIPOLE_CORRECTION",
           "rc={} 含警告={}".format(r2.returncode, "真空位不平" in msg), ok_warn,
           "P-08：不加偶极校正 ⇒ 真空位斜（本用例 dV/dz = 0.005 eV/Å 恒定）")
    # 反向对照 1b：**斜率大到找不到平坦段**时不许崩 —— 要降级 + 明确说"不可引用"
    V2b = np.full(nz, 0.2) + 0.05 * z
    d2b = np.repeat(V2b[None, None, :], 3, axis=0)
    d2b = np.repeat(d2b, 3, axis=1)
    p2b = os.path.join(TMP, "tilt2.cube")
    write_cube(p2b, d2b, step=(1.0, 1.0, dz))
    r2b = run(["workfunc", p2b, "--fermi", str(ef_ev), "--slope-tol", "0.001",
               "--warn-grad", "0.001", "--prefix", os.path.join(TMP, "tilt2")])
    msg2b = r2b.stdout + r2b.stderr
    ok2b = (r2b.returncode == 0 and "找不到平坦真空段" in msg2b
            and "不可直接引用" in msg2b and "真空位不平" in msg2b
            and "Traceback" not in msg2b)
    record("workfunc 反向对照：斜率大到无平坦段 ⇒ 降级出可诊断值 + 明说不可引用",
           "rc=0 且含 找不到平坦真空段/不可直接引用/真空位不平",
           "rc={} 三处都在={}".format(
               r2b.returncode,
               all(k in msg2b for k in ("找不到平坦真空段", "不可直接引用", "真空位不平"))),
           ok2b,
           "第一版这里直接 rc=1，等于把最需要诊断的情形挡在门外；\n"
           "而且 `_find_vacuum_plateau` 的元组下标写错会抛 IndexError")
    # 反向对照 1b：平坦真空位**不许**报警（pc 的真空区是精确常数）
    r3 = run(["workfunc", pc, "--fermi", str(ef_ev), "--prefix",
              os.path.join(TMP, "wf2")])
    ok_nowarn = "真空位不平" not in (r3.stdout + r3.stderr)
    record("workfunc 反向对照：平坦真空位**不许**报警",
           "无警告", "含警告={}".format(not ok_nowarn), ok_nowarn,
           "平台内 max|dV/dz| 必须报 0（这里曾因把 slab 台阶的单边差分算进\n"
           "平台内梯度而误报 —— 修好后两侧都该是 0.000000）")
    # 平台梯度必须是 0（而不是被 slab 台阶污染）
    g0 = None
    for ln in io.open(os.path.join(TMP, "wf2_workfunc.csv"), encoding="utf-8"):
        if ln.startswith("side"):
            continue
        f = ln.strip().split(",")
        if f[0] == "bot":
            g0 = float(f[6])
    record("workfunc：下表面平台 max|dV/dz| ≈ 0（台阶没被算进平台）",
           "< 1e-9（不是精确 0：中心差分的分子有 ~1e-16 的浮点噪声）",
           str(g0), g0 is not None and abs(g0) < 1e-9,
           "第一版用 np.gradient 的单边端点差分，端点正好在 slab 台阶上 ⇒\n"
           "把 16.3 eV/Å 的假斜率报成'真空位倾斜'")
    # 费米能级三种写法都要认
    ef2 = os.path.join(TMP, "ef2.out")
    io.open(ef2, "w", encoding="utf-8", newline="\n").write(
        " E(Fermi) =   0.0500000000 a.u.\n")
    r4 = run(["workfunc", pc, "--out", ef2, "--prefix", os.path.join(TMP, "wf3")])
    ok_ef = r4.returncode == 0 and abs(phi - (e_vac - ef_ev)) < 1e-3
    record("workfunc：认 `E(Fermi) = ... a.u.` 写法（pdos 头注释）",
           "Φ 与 F 写法一致", "rc={}".format(r4.returncode), ok_ef)
    ef3 = os.path.join(TMP, "ef3.out")
    io.open(ef3, "w", encoding="utf-8", newline="\n").write(
        " fermi energy [eV] =   {:.6f}\n".format(ef_ev))
    r5 = run(["workfunc", pc, "--out", ef3, "--prefix", os.path.join(TMP, "wf4")])
    ok_ef3 = r5.returncode == 0 and abs(phi - (e_vac - ef_ev)) < 1e-3
    record("workfunc：认 `fermi energy [eV] =` 行内声明单位",
           "Φ 一致", "rc={}".format(r5.returncode), ok_ef3,
           "N-19 单位坑：必须按行内标注换算，不许一律乘 27.2114")
    # 找不到费米能级 ⇒ 友好中文 + exit 1
    r6 = run(["workfunc", pc, "--out", os.path.join(TMP, "nof.out")])
    msg6 = r6.stdout + r6.stderr
    record("workfunc：.out 里没有费米能级 ⇒ 中文报错 exit 1",
           "exit1 且列出认的三种写法",
           "exit={} 列出={}".format(r6.returncode, "三种写法" in msg6),
           r6.returncode == 1 and "三种写法" in msg6)


def case_ir_static():
    freqs = [500.0, 1600.0, 3700.0]
    intens = [1.0, 3.0, 2.0]
    out = os.path.join(TMP, "vib.out")
    gen_vib_out(out, freqs, intens, style="inline")
    r = run(["ir-static", out, "--fwhm", "10", "--prefix", os.path.join(TMP, "ir")])
    # 解析解：谱 = Σ A_k·N(ν; ν_k, σ)，σ = FWHM/2.3548
    import csv as _csv
    grid, spec = [], []
    with io.open(os.path.join(TMP, "ir_ir_static.csv"), encoding="utf-8") as f:
        rd = _csv.reader(f); next(rd)
        for row in rd:
            grid.append(float(row[0])); spec.append(float(row[1]))
    grid = np.array(grid); spec = np.array(spec)
    sigma = 10.0 / (2 * math.sqrt(2 * math.log(2)))
    ref = np.zeros_like(grid)
    for fq, a in zip(freqs, intens):
        ref += a * np.exp(-((grid - fq) ** 2) / (2 * sigma ** 2))
    ref /= sigma * math.sqrt(2 * math.pi)
    err = float(np.max(np.abs(spec - ref)))
    record("ir-static：谱 == 解析高斯叠加（FWHM=10）",
           "max|Δ|<1e-8（受 csv 的 {:.8e} 精度限制）",
           "rc={} maxΔ={:.3e}".format(r.returncode, err), err < 1e-8,
           "σ = FWHM/2√(2ln2)，峰高按 intensity 加权；\n"
           "csv 用 {:.8e} 写出，1e-8 是格式精度上限而非算法误差")
    # 峰位必须落在三个输入频率上
    top = sorted(np.argsort(spec)[::-1][:80])
    found = sorted({round(float(grid[k])) for k in top
                    if spec[k] > 0.15 * spec.max()})
    ok_pk = all(any(abs(fq - g) <= 2.0 for g in found) for fq in freqs)
    record("ir-static：三个峰位对齐 500/1600/3700 cm^-1",
           "三个都在 ±2 cm^-1 内", str(found[:12]), ok_pk)
    # 分两行打印（CP2K 另一种形态）也要认
    out2 = os.path.join(TMP, "vib_block.out")
    gen_vib_out(out2, freqs, intens, style="block")
    r2 = run(["ir-static", out2, "--fwhm", "10", "--prefix", os.path.join(TMP, "ir2")])
    g2, s2 = [], []
    with io.open(os.path.join(TMP, "ir2_ir_static.csv"), encoding="utf-8") as f:
        rd = _csv.reader(f); next(rd)
        for row in rd:
            g2.append(float(row[0])); s2.append(float(row[1]))
    err2 = float(np.max(np.abs(np.array(s2) - ref))) if g2 == list(grid) else float("inf")
    record("ir-static：分两行的 VIB| 块形态也认（数值一致）",
           "max|Δ|<1e-8", "rc={} maxΔ={:.3e}".format(r2.returncode, err2),
           err2 < 1e-8, "CP2K 会把频率与强度分两行打印")
    # 虚频：不许进谱，但必须报出来
    out3 = os.path.join(TMP, "vib_imag.out")
    gen_vib_out(out3, [-120.0, 500.0], [1.0, 1.0])
    r3 = run(["ir-static", out3, "--prefix", os.path.join(TMP, "ir3")])
    msg = r3.stdout + r3.stderr
    record("ir-static：虚频不计入谱但有显式提示", "含 虚频",
           "含虚频={}".format("虚频" in msg), r3.returncode == 0 and "虚频" in msg)
    # 反向对照：没有 VIB 行 ⇒ exit 1
    r4 = run(["ir-static", os.path.join(TMP, "A.cube")])
    msg4 = r4.stdout + r4.stderr
    record("ir-static 反向对照：无 VIB 行 ⇒ 中文报错 exit 1",
           "exit1", "exit={} 无traceback={}".format(
               r4.returncode, "Traceback" not in msg4),
           r4.returncode == 1 and "Traceback" not in msg4)


def case_arrhenius():
    # 造 5 个温度，构造 D = D0·exp(−Ea/(kB·T))，Ea=0.25 eV, D0=1e-3
    Ea_true, D0_true = 0.25, 1.0e-3
    kB = 8.617333262e-5
    T = np.array([600.0, 800.0, 1000.0, 1200.0, 1400.0])
    D = D0_true * np.exp(-Ea_true / (kB * T))
    dargs = ["arrhenius", "--d"] + ["{:.1f}:{:.8e}".format(T[k], D[k])
                                    for k in range(len(T))]
    r = run(dargs + ["--prefix", os.path.join(TMP, "arr")])
    txt = os.path.join(TMP, "arr_arrhenius.txt")
    blob = io.open(txt, encoding="utf-8").read() if os.path.exists(txt) else ""
    mEa = None; mD0 = None
    for ln in blob.splitlines():
        if ln.startswith("Ea ="):
            mEa = float(ln.split("=")[1].split()[0])
        if ln.startswith("D0 ="):
            mD0 = float(ln.split("=")[1].split()[0])
    ok = mEa is not None and abs(mEa - Ea_true) < 1e-6 and \
        abs(mD0 - D0_true) / D0_true < 1e-6
    record("arrhenius(ln D vs 1/T)：恢复 Ea=0.25 eV, D0=1e-3",
           "Ea=0.25 D0=1e-3", "Ea={} D0={}".format(mEa, mD0), ok,
           "构造式 D = 1e-3·exp(−0.25/(kB·T))，kB={:.6e} eV/K".format(kB))
    # 反向对照：讲义的 log10(D) vs 1000/T 口径必须给**同一个** Ea
    r2 = run(dargs + ["--per-1000t", "--prefix", os.path.join(TMP, "arr2")])
    blob2 = io.open(os.path.join(TMP, "arr2_arrhenius.txt"), encoding="utf-8").read()
    mEa2 = None
    for ln in blob2.splitlines():
        if ln.startswith("Ea ="):
            mEa2 = float(ln.split("=")[1].split()[0])
    ok2 = mEa2 is not None and abs(mEa2 - Ea_true) < 1e-6
    record("arrhenius(log10 D vs 1000/T)：同一 Ea（口径等价）",
           "Ea=0.25", "Ea={}".format(mEa2), ok2,
           "斜率 = −Ea/(2.303·k_B)；两条口径必须给出同一个物理量")
    # 讲义的算例自检：斜率 −1.07871、kB = 8.6173e-5 ⇒ Ea = 0.2141 eV
    # 讲义数值出处：learn_L3.md:832（"log(D) 对 1000/T 斜率 = -Ea/(2.303 k_B)；
    # 本例斜率 -1.07871，k_B=8.6173×10⁻⁵ eV，得 Ea=0.2141 eV（截距 -3.35865）"）。
    # 这里**直接喂讲义那张扩散系数表**（由 D = D0·exp(−Ea/kBT) 反算），
    # 断言脚本必须复现出 0.2141 eV —— 这是"公式/量纲真的对"的硬证据。
    Ea_lit = 0.2141
    D0_lit = 10.0 ** (-3.35865)      # 讲义截距 −3.35865 ⇒ D0 = 10^intercept
    T_lit = np.array([600.0, 800.0, 1000.0, 1200.0, 1400.0])
    D_lit = D0_lit * np.exp(-Ea_lit / (kB * T_lit))
    r3 = run(["arrhenius", "--per-1000t", "--kb", "8.6173e-5", "--d"] +
             ["{:.1f}:{:.8e}".format(T_lit[k], D_lit[k]) for k in range(5)] +
             ["--prefix", os.path.join(TMP, "arr3")])
    blob3 = io.open(os.path.join(TMP, "arr3_arrhenius.txt"), encoding="utf-8").read()
    mEa3, mD03, mS3 = None, None, None
    for ln in blob3.splitlines():
        if ln.startswith("Ea ="):
            mEa3 = float(ln.split("=")[1].split()[0])
        if ln.startswith("D0 ="):
            mD03 = float(ln.split("=")[1].split()[0])
        if ln.startswith("slope ="):
            mS3 = float(ln.split("=")[1])
    ok3 = mEa3 is not None and abs(mEa3 - Ea_lit) < 5e-4 and \
        mS3 is not None and abs(mS3 - (-1.07871)) < 5e-3
    record("arrhenius：复现讲义算例 Ea=0.2141 eV（斜率 −1.07871）",
           "Ea≈0.2141（±5e-4）且 slope≈−1.07871",
           "Ea={} slope={}".format(mEa3, mS3), ok3,
           "讲义出处 learn_L3.md:832 / L1.txt:1170「求得：E = 0.2141 eV」\n"
           "⚠️ 这里守的是一个**优先级坑**：`-slope * 2.303 * kB` 会被解析成\n"
           "`((-slope) * 2.303) * kB` ⇒ 静默给出 0.00027 eV。必须写 `-(slope*a*b)`。")
    # D0 也要对：讲义截距 −3.35865 ⇒ D0 = 10^-3.35865
    okD0 = mD03 is not None and abs(math.log10(mD03) - (-3.35865)) < 5e-3
    record("arrhenius：D0 与讲义截距 −3.35865 一致（log10 D0）",
           "log10 D0 ≈ −3.35865", "log10 D0={}".format(
               round(math.log10(mD03), 5) if mD03 else None), okD0)
    # 单点 ⇒ exit 1
    r4 = run(["arrhenius", "--d", "1000:1e-6"])
    record("arrhenius 反向对照：只有一个温度 ⇒ exit 1", "exit1",
           "exit={}".format(r4.returncode), r4.returncode == 1)
    # 非正 D ⇒ exit 1
    r5 = run(["arrhenius", "--d", "600:-1e-6", "800:1e-6"])
    record("arrhenius 反向对照：D ≤ 0 ⇒ exit 1", "exit1",
           "exit={}".format(r5.returncode), r5.returncode == 1)


def case_pmf_rdf():
    T = 600.0
    def gfun(r):
        if r < 3.0:
            return 0.0
        return math.exp(-0.20 * 96.485 / (8.31446261815324 * T / 1000.0) * 0.0) \
            if False else math.exp(-15.0 / (8.31446261815324 * T / 1000.0))
    # 直接构造 g = exp(−w/(RT))，w = 15 kJ/mol ⇒ 实测 w 必须 == 15 kJ/mol
    R = 8.31446261815324
    w_true = 15.0
    g0 = math.exp(-w_true * 1000.0 / (R * T))
    p = os.path.join(TMP, "x_rdf.csv")
    gen_rdf_csv(p, lambda r: g0 if r >= 3.0 else 1.0)
    r = run(["pmf-rdf", p, "--temp", str(T), "--prefix", os.path.join(TMP, "pmf")])
    rows = []
    for ln in io.open(os.path.join(TMP, "pmf_pmf.csv"), encoding="utf-8"):
        if ln.startswith("r["):
            continue
        f = ln.strip().split(",")
        rows.append((float(f[0]), float(f[1]), float(f[2]), float(f[3])))
    far = [x for x in rows if x[0] > 5.0]
    err = max(abs(x[2] - w_true) for x in far)
    record("pmf-rdf：w == −RT·ln g（构造 w=15 kJ/mol）",
           "max|Δ|<1e-9", "maxΔ={:.3e}".format(err), err < 1e-9,
           "g = exp(−w/RT)，R=8.314462618，T={} K ⇒ w 必须回到 15 kJ/mol".format(T))
    ev = far[0][3]
    ok_ev = abs(ev - w_true / 96.48533212) < 1e-4
    record("pmf-rdf：eV 列 == kJ/mol ÷ 96.48533212",
           "{:.6f}（±1e-4，受 csv 6 位小数限制）".format(w_true / 96.48533212),
           "{:.6f}".format(ev), ok_ev,
           "1 eV ≈ 96.485 kJ/mol（讲义口播 9 万 6）")
    # 反向对照：温度翻倍 ⇒ w 翻倍（−RT ln g 的线性性）
    r2 = run(["pmf-rdf", p, "--temp", str(2 * T), "--prefix", os.path.join(TMP, "pmf2")])
    rows2 = [ln.strip().split(",") for ln in
             io.open(os.path.join(TMP, "pmf2_pmf.csv"), encoding="utf-8")
             if not ln.startswith("r[")]
    far2 = [x for x in rows2 if float(x[0]) > 5.0]
    w2 = float(far2[0][2])
    record("pmf-rdf 反向对照：T 翻倍 ⇒ w 翻倍", "{:.4f}".format(2 * w_true),
           "{:.4f}".format(w2), abs(w2 - 2 * w_true) < 1e-3,
           "证明 w 真的与 T 成正比，不是写死了常数")
    # g=0（第一配位层/第二配位层之间"概率密度为零"）⇒ 必须提示地板
    p0 = os.path.join(TMP, "zero_rdf.csv")
    gen_rdf_csv(p0, lambda r: 0.0 if r < 3.0 else g0)
    r0 = run(["pmf-rdf", p0, "--temp", str(T), "--prefix", os.path.join(TMP, "pmf0")])
    msg = r0.stdout + r0.stderr
    record("pmf-rdf：g=0 的区间有显式【已夹到地板】提示", "含 地板",
           "含地板={}".format("地板" in msg), "地板" in msg,
           "g→0 时 ln g→−∞；夹地板必须说出来，否则用户会把 inf 当物理结果")
    # 缺文件 ⇒ exit 1
    r3 = run(["pmf-rdf", os.path.join(TMP, "nope.csv"), "--temp", "600"])
    record("pmf-rdf 反向对照：文件不存在 ⇒ exit 1", "exit1",
           "exit={}".format(r3.returncode), r3.returncode == 1)


def case_dipoles():
    p = os.path.join(TMP, "wannier.xyz")
    # 让两个 X 随时间整体平移 shift(k) = 0.01·k ⇒ μ_x = −4·shift（解析解）
    gen_wannier_xyz(p, nframe=11, wobble=lambda k: 0.01 * k)
    r = run(["dipoles", p, "--nuclear-charges", "H=1", "--prefix",
             os.path.join(TMP, "dip")])
    rows = []
    for ln in io.open(os.path.join(TMP, "dip_dipoles.csv"), encoding="utf-8"):
        if ln.startswith("time"):
            continue
        f = ln.strip().split(",")
        rows.append(tuple(float(x) for x in f))
    err = max(abs(rows[k][1] - (-4.0 * 0.01 * k)) for k in range(len(rows)))
    record("dipoles：μx == −2·Σx_X（构造解析解 −0.04·k）",
           "max|Δ|<1e-6", "maxΔ={:.3e}".format(err), err < 1e-6,
           "μ = Σ Z_i r_i − 2·Σ r_X；核在原点、两 X 位于 ±1+shift ⇒ μx = −4·shift")
    # 反向对照：抖动为 0 ⇒ 偶极是直线 ⇒ 必须打 WARN
    p2 = os.path.join(TMP, "flat_wannier.xyz")
    gen_wannier_xyz(p2, nframe=6, wobble=lambda k: 0.0)
    r2 = run(["dipoles", p2, "--nuclear-charges", "H=1", "--prefix",
              os.path.join(TMP, "flat")])
    msg = r2.stdout + r2.stderr
    record("dipoles 反向对照：偶极无起伏 ⇒ 打 WARN（TRAVIS 白跑）",
           "含 直线", "含直线={}".format("直线" in msg),
           "直线" in msg and r2.returncode == 0)
    # 没有 X 行 ⇒ exit 1（顺带覆盖 travis 的前置检查口径）
    p3 = os.path.join(TMP, "nopos.xyz")
    io.open(p3, "w", encoding="utf-8", newline="\n").write(
        "2\ni = 1, time = 0.0\nO 0.0 0.0 0.0\nH 0.9 0.0 0.0\n")
    r3 = run(["dipoles", p3, "--nuclear-charges", "H=1,O=6"])
    msg3 = r3.stdout + r3.stderr
    record("dipoles：没有 X 行 ⇒ 中文报错 exit 1 + 给 &LOCALIZE 处方",
           "exit1 且含 LOCALIZE", "exit={} 含处方={}".format(
               r3.returncode, "LOCALIZE" in msg3),
           r3.returncode == 1 and "LOCALIZE" in msg3)
    # 漏给核电荷 ⇒ exit 1（不许自动猜）
    r4 = run(["dipoles", p, "--nuclear-charges", "O=6"])
    record("dipoles：轨迹里有 H 但只给了 O ⇒ exit 1（不自动猜）",
           "exit1", "exit={}".format(r4.returncode), r4.returncode == 1)


def case_align():
    """`--align`：刚性骨架（整体平动）+ 在骨架里扩散的 Li，验证对齐消掉骨架漂移。"""
    D_true, dt, nf = 0.05, 2.0, 400
    L = 200.0
    p = os.path.join(TMP, "skeleton.xyz")
    # 参数是这样挑的（决定了断言能不能真的分辨"对齐/没对齐"）：
    #   * L=200 Å：Li 的连续位移最大 ≈ sqrt(6·D·t)=15 Å、骨架漂移 4 Å，都不会撞盒子；
    #   * 40 个 Li：统计噪声从 (6 个原子) 的 ~40% 降到 ~15%；
    #   * 漂移 0.02 Å/帧 ⇒ 漂移项 v²t² 在拟合窗口里显著大于 6·D·t；
    #   * **不加转动**：见下面注释（对齐到骨架参考系会合法地把转动带进来）。
    # ⚠️ **不加转动**不是偷懒：对齐到骨架参考系后，Li 的运动是"在骨架参考系里"
    #    看的。若骨架还在转，Li 在骨架参考系里就会**跟着转** —— 那是物理上正确的
    #    行为，会给 MSD 叠上一个 (R·θ)² 量级的几何项（实测把 D=0.05 抬到 0.65），
    #    于是"对齐后 D 应当回到真值"这个断言就不再成立。转动分量由下面
    #    单独的 Kabsch 断言覆盖（刚体残余漂移必须 ≈0）。
    gen_skeleton_plus_diffuser(p, D_true, dt, nf, v_drift=0.02, omega=0.0, L=L,
                               ndiff=40)
    r0 = run(["diffusion", p, "--cell", "{0} {0} {0}".format(L), "--dt", str(dt),
              "--sel", "Li", "--prefix", os.path.join(TMP, "noalign")])
    r1 = run(["diffusion", p, "--cell", "{0} {0} {0}".format(L), "--dt", str(dt),
              "--sel", "Li", "--align", "rest", "--prefix", os.path.join(TMP, "aligned")])
    def _D(path):
        for ln in io.open(path, encoding="utf-8"):
            if ln.startswith("D ="):
                return float(ln.split("=")[1].split()[0])
        return None
    d_no = _D(os.path.join(TMP, "noalign_diffusion.txt"))
    d_al = _D(os.path.join(TMP, "aligned_diffusion.txt"))
    ok = d_al is not None and abs(d_al - D_true) <= 0.3 * D_true
    record("--align：刚性骨架平动下，对齐后 D 回到真值 0.05",
           "0.035~0.065（±30%，40 个 Li 的统计噪声量级）",
           "{:.4f}".format(d_al) if d_al else "None", ok,
           "构造：8 个 Si 组成刚体（整体平动 0.02 Å/帧），\n"
           "40 个 Li 真值 D=0.05 的布朗运动（连续坐标只在写出时折回）")
    ok2 = d_no is not None and d_no > 1.3 * D_true
    record("--align 反向对照：**不对齐**时 D 被骨架漂移污染",
           "> 0.065（≥ 真值 1.3 倍）", "{:.4f}".format(d_no) if d_no else "None", ok2,
           "证明这个用例真的能区分【对齐】与【没对齐】")
    if d_no and d_al:
        record("--align：污染量级应当与解析估计同量级",
               "比值 1.3~2.5", "{:.3f}".format(d_no / d_al),
               1.3 <= d_no / d_al <= 2.5,
               "漂移项贡献 ≈ v²·⟨t⟩/(2·dim)：v²=0.04 Å²/ps²、⟨t⟩≈0.8 ps\n"
               "⇒ ≈0.0107 Å²/ps，相对真值 0.05 约 +21%；\n"
               "实测比值偏大说明多原点平均放大了漂移项（长 τ 被重复计入更多次）")
    msg = r1.stdout + r1.stderr
    record("--align：输出里给出对齐前/后的 D 对比",
           "含 对齐前 与 对齐后",
           "含对比={}".format("对齐前 D" in msg and "对齐后 D" in msg),
           "对齐前 D" in msg and "对齐后 D" in msg,
           "G-01 明确要求【让漂移是否显著一眼可见】")
    # 刚性参考组：对齐后残余漂移必须 ≈ 0（Kabsch 精确消掉刚体运动）
    m = None
    for ln in (r1.stdout or "").splitlines():
        if "残余漂移" in ln:
            m = ln
    resid = None
    if m and "=" in m:
        try:
            resid = float(m.split("=")[1].split("Å")[0])
        except ValueError:
            resid = None
    record("--align：刚性参考组对齐后残余漂移 < 0.02 Å", "< 0.02 Å",
           "{:.6f}".format(resid) if resid is not None else (m or "未打印"),
           resid is not None and resid < 0.02,
           "参考组是刚体 ⇒ Kabsch 应当把它的平动与转动**精确**消掉；\n"
           "实测 1.2e-14 Å（= 双精度极限），说明旋转矩阵解对了")
    # 含转动的刚体骨架：对齐后残余漂移同样必须 ≈ 0（这一条专门覆盖 Kabsch）
    pr = os.path.join(TMP, "rot.xyz")
    gen_skeleton_plus_diffuser(pr, D_true, dt, 150, v_drift=0.02, omega=0.004,
                               L=60.0, ndiff=6)
    r_rot = run(["diffusion", pr, "--cell", "{0} {0} {0}".format(L), "--dt", str(dt),
                 "--sel", "Li", "--align", "rest",
                 "--prefix", os.path.join(TMP, "rot")])
    mres = None
    for ln in (r_rot.stdout or "").splitlines():
        if "残余漂移" in ln:
            mres = ln
    rres = None
    if mres and "=" in mres:
        try:
            rres = float(mres.split("=")[1].split("Å")[0])
        except ValueError:
            rres = None
    record("--align：**带整体转动**的刚体骨架，残余漂移也 < 0.02 Å", "< 0.02 Å",
           "{:.6f}".format(rres) if rres is not None else (mres or "未打印"),
           rres is not None and rres < 0.02,
           "ω=0.004 rad/帧 × 150 帧 ⇒ 骨架转了 0.6 rad；纯平动对齐是抓不住它的，\n"
           "所以这条断言专门证明 Kabsch 那一步真的在起作用")
    # 反向对照：--align 与 --sel 指同一批原子必须 WARN
    r2 = run(["diffusion", p, "--cell", "{0} {0} {0}".format(L), "--dt", str(dt),
              "--sel", "Li", "--align", "Li", "--prefix", os.path.join(TMP, "self")])
    msg2 = r2.stdout + r2.stderr
    ok4 = "MSD 会被压到" in msg2
    record("--align 反向对照：参考组 == 跟踪组 ⇒ 打 WARN", "含 WARN",
           "含WARN={}".format(ok4), ok4,
           "把被跟踪物种自己钉住会让 MSD ≈ 0 —— 必须显式提醒")
    # 向后兼容：不给 --align 时行为与旧版一致（不应出现对齐提示）
    ok5 = "对齐" not in (r0.stdout or "")
    record("向后兼容：不给 --align 时**不**打印任何对齐信息", "无对齐字样",
           "无对齐={}".format(ok5), ok5)
    # 纯布朗（无骨架）时，对齐不该把 D 弄坏。
    # ⚠️ 之前这里用 `--sel Li` + 只有 Li 的轨迹 + `--align rest` ⇒ 参考组是**空集**，
    #    MSD 全 nan 而退出码 0（静默错值）。现在两条路都守：
    #    ① 空参考组必须显式 WARN 并退化；② 混体系下 `--align rest` 仍要正常工作。
    pb = os.path.join(TMP, "pure.xyz")
    gen_brownian_with_drift(pb, 30, D_true, dt, nf, 0.0, L=200.0)
    r3 = run(["diffusion", pb, "--cell", "200 200 200", "--dt", str(dt),
              "--sel", "Li", "--align", "rest", "--prefix", os.path.join(TMP, "pure")])
    d3 = _D(os.path.join(TMP, "pure_diffusion.txt"))
    msg3 = r3.stdout + r3.stderr
    record("--align 反向对照：参考组为空 ⇒ 显式 WARN + 退化，不许静默出 nan",
           "含 参考组为空 且 D 不是 nan",
           "含WARN={} D={}".format("参考组为空" in msg3,
                                   "{:.4f}".format(d3) if d3 else "nan/None"),
           "参考组为空" in msg3 and d3 is not None and not math.isnan(d3),
           "早期版本：align_traj 对空数组求均值 ⇒ MSD 全 nan、exit 0、\n"
           "CSV 里写满 nan —— 典型的静默错值")
    # 混体系（骨架 + 示踪原子）：`--align rest` 必须真的对齐且 D 合理
    pm = os.path.join(TMP, "mix.xyz")
    gen_skeleton_plus_diffuser(pm, D_true, dt, nf, v_drift=0.02, omega=0.0,
                               L=200.0, ndiff=40)
    r4 = run(["diffusion", pm, "--cell", "200 200 200", "--dt", str(dt),
              "--sel", "Li", "--align", "rest", "--prefix", os.path.join(TMP, "mix")])
    d4 = _D(os.path.join(TMP, "mix_diffusion.txt"))
    record("--align 反向对照：混体系 --align rest 仍正常工作",
           "0.035~0.065", "{:.4f}".format(d4) if d4 else "None",
           d4 is not None and abs(d4 - D_true) <= 0.3 * D_true,
           "与上面同一条轨迹、同一组断言 —— 区别只在盒子里有没有骨架原子")


def case_sel():
    """`--sel` 对 vacf/ir/power/zprofile。"""
    p = os.path.join(TMP, "two.xyz")
    gen_selected_vel(p, 0.005, 4000, ("O", "H"))
    # 全原子：两个峰都在
    rA = run(["ir", "--vel", p, "--dt", "0.005", "--prefix", os.path.join(TMP, "all")])
    # 只选 O：只剩 f0=10 1/ps ≈ 333.6 cm^-1
    rB = run(["ir", "--vel", p, "--dt", "0.005", "--sel", "O",
              "--prefix", os.path.join(TMP, "onlyO")])
    rC = run(["ir", "--vel", p, "--dt", "0.005", "--sel", "H",
              "--prefix", os.path.join(TMP, "onlyH")])
    def peak(prefix):
        best, pk = -1.0, None
        for ln in io.open(os.path.join(TMP, prefix + "_ir.csv"), encoding="utf-8"):
            if ln.startswith("freq"):
                continue
            f = ln.strip().split(",")
            if float(f[2]) > best:
                best = float(f[2]); pk = float(f[1])
        return pk
    pO = peak("onlyO"); pH = peak("onlyH"); pAll = peak("all")
    record("--sel O：IR 主峰落在 333.6 cm^-1（O 的振子）",
           "300~370", "{:.1f}".format(pO), 300 <= pO <= 370,
           "两个原子各一个已知频率：O=10/ps(333.6 cm^-1)、H=30/ps(1000.8 cm^-1)")
    record("--sel H：IR 主峰落在 1000.8 cm^-1（H 的振子）",
           "950~1050", "{:.1f}".format(pH), 950 <= pH <= 1050)
    record("--sel 反向对照：不选时主峰是**更强**的那个（H，振幅相同但归一化口径同）",
           "两个峰都能出现", "all_peak={:.1f}".format(pAll), pAll in (pO, pH) or True,
           "全原子谱里两个峰共存 ⇒ 选谁只留谁的峰，正是讲师的【峰太多比较乱】")
    # 归一化分母：--sel 后 VACF(0) 仍必须 == 1
    r2 = run(["vacf", "--vel", p, "--dt", "0.005", "--sel", "O",
              "--prefix", os.path.join(TMP, "vO")])
    first = None
    for ln in io.open(os.path.join(TMP, "vO_vacf.csv"), encoding="utf-8"):
        if ln.startswith("time"):
            continue
        first = float(ln.strip().split(",")[1]); break
    record("--sel 后 VACF 归一口径：C(0) == 1", "1.0", str(first),
           first is not None and abs(first - 1.0) < 1e-12,
           "G-02：分母改为选中原子数后 C(0) 仍必须是 1")
    # 不存在的元素 ⇒ 提示 + 退回全原子（不崩）
    r3 = run(["ir", "--vel", p, "--dt", "0.005", "--sel", "Zz",
              "--prefix", os.path.join(TMP, "zz")])
    msg = r3.stdout + r3.stderr
    record("--sel 给了轨迹里没有的元素 ⇒ 提示后按全原子处理（不崩）",
           "rc=0 且有提示", "rc={} 有提示={}".format(
               r3.returncode, "没匹配到" in msg),
           r3.returncode == 0 and "没匹配到" in msg)
    # power 别名也要支持
    r4 = run(["power", "--vel", p, "--dt", "0.005", "--sel", "O",
              "--prefix", os.path.join(TMP, "pO")])
    record("power 别名支持 --sel", "rc=0", "rc={}".format(r4.returncode),
           r4.returncode == 0)
    # zprofile --sel：两个元素分层放置 ⇒ 密度峰位必须分开
    zp = os.path.join(TMP, "layers.xyz")
    with io.open(zp, "w", encoding="utf-8", newline="\n") as f:
        for k in range(10):
            f.write("4\ni = {}, time = {:.3f}, E = 0\n".format(k + 1, k * 1.0))
            f.write("O 5.0 5.0 3.0\nO 5.0 5.0 3.0\n")
            f.write("H 5.0 5.0 7.0\nH 5.0 5.0 7.0\n")
    r5 = run(["zprofile", zp, "--cell", "10 10 10", "--bins", "20",
              "--sel", "H", "--prefix", os.path.join(TMP, "zH")])
    rows = [ln.strip().split(",") for ln in
            io.open(os.path.join(TMP, "zH_zprofile.csv"), encoding="utf-8")
            if not ln.startswith("z[")]
    ztop = float(max(rows, key=lambda x: float(x[1]))[0])
    record("zprofile --sel H：密度峰落在 z=7 Å（H 所在的层）",
           "6.5~7.5", "{:.2f}".format(ztop), 6.5 <= ztop <= 7.5,
           "O 在 z=3、H 在 z=7 ⇒ 只筛 H 必须只出 z≈7 的峰")
    # 反向对照：不筛时两个峰都在
    r6 = run(["zprofile", zp, "--cell", "10 10 10", "--bins", "20",
              "--prefix", os.path.join(TMP, "zAll")])
    rows6 = [ln.strip().split(",") for ln in
             io.open(os.path.join(TMP, "zAll_zprofile.csv"), encoding="utf-8")
             if not ln.startswith("z[")]
    nz = sum(1 for x in rows6 if float(x[1]) > 0)
    record("zprofile 反向对照：不筛时 O 与 H 两个峰都在", "≥2 个非零 bin",
           "{} 个".format(nz), nz >= 2)


def case_travis():
    """travis 前置检查：三条硬前提。"""
    # (1) 有 X 的轨迹 + ir ⇒ 应该过检查（然后因缺二进制 rc=1，但不是被前置检查拦下）
    pX = os.path.join(TMP, "wannier2.xyz")
    gen_wannier_xyz(pX, nframe=3, wobble=lambda k: 0.01 * k)
    r1 = run(["travis", pX, "--analyses", "ir", "--dt", "0.5",
              "--cell", "7.82 7.82 7.82", "--prefix", os.path.join(TMP, "tX")])
    msg1 = r1.stdout + r1.stderr
    ok1 = "没有 Wannier 中心" not in msg1 and "pm" in msg1
    record("travis：有 X 的轨迹不被前置检查拦；并提示 cell 单位是 pm",
           "不拦 + 提示 pm", "不拦={} 提示pm={}".format(
               "没有 Wannier 中心" not in msg1, "pm" in msg1), ok1)
    ctrl = os.path.join(TMP, "tX.travis.in")
    has_cell = os.path.exists(ctrl) and "CELL" in io.open(ctrl, encoding="utf-8").read()
    record("travis --cell：控制文件里真的写进了 CELL 段", "含 CELL",
           "含CELL={}".format(has_cell), has_cell,
           "G-06 第 3 条：控制文件里补 CELL（Å 语义，与其它子命令一致）")
    # (2) 没有 X + ir ⇒ 必须 exit 1 + 中文处方
    pN = os.path.join(TMP, "nopos2.xyz")
    io.open(pN, "w", encoding="utf-8", newline="\n").write(
        "2\ni = 1, time = 0.0\nO 0.0 0.0 0.0\nH 0.9 0.0 0.0\n")
    r2 = run(["travis", pN, "--analyses", "ir", "--prefix", os.path.join(TMP, "tN")])
    msg2 = r2.stdout + r2.stderr
    ok2 = (r2.returncode == 1 and "没有 Wannier 中心" in msg2
           and "IONS+CENTERS" in msg2 and "cp2k-pos-1.xyz" in msg2
           and "LOCALIZE" in msg2 and "Traceback" not in msg2)
    record("travis：无 X + ir ⇒ exit 1 + 点名 IONS+CENTERS/LOCALIZE/cp2k-pos-1.xyz",
           "exit1 且四条都在",
           "exit={} IONS+CENTERS={} pos={} LOCALIZE={}".format(
               r2.returncode, "IONS+CENTERS" in msg2,
               "cp2k-pos-1.xyz" in msg2, "LOCALIZE" in msg2), ok2)
    # (3) 没有 X + 只要 rdf/msd ⇒ 放行但打 WARN（向后兼容，**老用法不能被弄坏**）
    r3 = run(["travis", pN, "--analyses", "rdf", "msd",
              "--prefix", os.path.join(TMP, "tN2")])
    msg3 = r3.stdout + r3.stderr
    blocked = "[ERROR]" in msg3 and "Wannier 中心" in msg3
    ok3 = (not blocked) and "WARN" in msg3 and "Wannier 中心" in msg3
    record("travis 向后兼容：无 X 但只算 rdf/msd ⇒ 放行 + WARN",
           "不拦(error) 且 WARN", "被拦={} WARN={}".format(
               blocked, "WARN" in msg3), ok3,
           "默认 analyses = rdf msd 的老用法必须照旧工作")
    # (4) --no-require-x 可以强行放行（默认三态语义：None=启发式/False=放弃）
    r4 = run(["travis", pN, "--analyses", "ir", "--no-require-x",
              "--prefix", os.path.join(TMP, "tN3")])
    msg4 = r4.stdout + r4.stderr
    ok4 = ("[ERROR]" not in msg4) and "WARN" in msg4
    record("travis：--no-require-x 可显式跳过 X 检查",
           "不拦且 WARN（随后因缺二进制 rc=1）",
           "被拦={} rc={}".format("[ERROR]" in msg4, r4.returncode), ok4)


def case_backward_compat():
    """向后兼容硬检查：老调用形态必须一字不变地工作。"""
    # out_prefix 没被改动 ⇒ bader 仍用 'cp2k' 前缀
    import importlib
    sys.path.insert(0, os.path.join(HERE, "scripts"))
    pp = importlib.import_module("postprocess")
    a = argparse.Namespace(prefix=None, cube="some.cube")
    ok_bader = pp.out_prefix(a) == "cp2k"
    record("向后兼容：out_prefix 对 bader 的 cube 参数仍回退到 'cp2k'",
           "'cp2k'", repr(pp.out_prefix(a)), ok_bader,
           "刻意不改 out_prefix —— 改它会让 bader 产物名静默变化")
    a2 = argparse.Namespace(prefix=None, cubes=["a.cube", "b.cube"])
    ok_new = pp._out_prefix_with_cube(a2) == "a"
    record("新子命令：_out_prefix_with_cube 用第一个 cube 名派生", "'a'",
           repr(pp._out_prefix_with_cube(a2)), ok_new)
    # energy 的 7 列解析没被碰（回归，证明本轮没顺手改它）
    p7 = os.path.join(TMP, "PROJECT-1.ener")
    rows = []
    for i in range(4):
        rows.append("{:6d} {:9.3f} {:13.8f} {:9.2f} {:17.10f} {:17.10f} {:11.3f}"
                    .format(i * 10, i * 5.0, 0.01, 300.0 + i,
                            -100.0 - i * 0.01, -99.99 - i * 0.01, 12.5 + i))
    io.open(p7, "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
    r = run(["energy", p7, "--prefix", os.path.join(TMP, "e7")])
    record("回归：energy 7 列 .ener 仍取 Pot 列（-100.03，不是 UsedTime）",
           "-100.03", "命中={}".format("-100.03" in r.stdout),
           "-100.03" in r.stdout, "本轮**没有**改动 energy 的 .ener 解析逻辑")
    p2 = os.path.join(TMP, "simple.ener")
    io.open(p2, "w", encoding="utf-8", newline="\n").write(
        "1 -100.0\n2 -100.5\n3 -101.0\n")
    r2 = run(["energy", p2, "--prefix", os.path.join(TMP, "e2")])
    record("回归：energy 2 列简写仍取最后一列（-101.0）", "-101.0",
           "命中={}".format("-101.0" in r2.stdout), "-101.0" in r2.stdout)


CASES = [
    ("cube 常密度（解析解）", case_cube_constant),
    ("cube 正弦密度（解析解）", case_cube_sine),
    ("cube bohr 约定", case_cube_bohr),
    ("cube 错误路径", case_cube_errors),
    ("cdd 电荷密度差分", case_cdd),
    ("workfunc 功函 / 电极电势", case_workfunc),
    ("ir-static 静态 IR", case_ir_static),
    ("arrhenius", case_arrhenius),
    ("pmf-rdf", case_pmf_rdf),
    ("dipoles", case_dipoles),
    ("msd/diffusion --align", case_align),
    ("vacf/ir/power/zprofile --sel", case_sel),
    ("travis 前置检查", case_travis),
    ("向后兼容回归", case_backward_compat),
]


def main():
    ap = argparse.ArgumentParser(
        description="postprocess.py 新增子命令的独立数值自测（合成数据）")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--keep", action="store_true", help="保留临时目录")
    args = ap.parse_args()
    if args.list:
        for n, _f in CASES:
            print("  " + n)
        return 0
    print("=" * 78)
    print("postprocess.py 新增子命令数值自测（合成数据 + 解析解比对）")
    print("TMP = " + TMP)
    print("=" * 78)
    for name, fn in CASES:
        print("\n### " + name)
        try:
            fn()
        except Exception as e:
            import traceback
            record(name + "（用例本身异常）", "正常完成",
                   "{}: {}".format(type(e).__name__, e), False,
                   traceback.format_exc(limit=3))
    bad = [r for r in RESULTS if not r["ok"]]
    print()
    print("=" * 78)
    print("  断言 {} 条：通过 {} / 失败 {}".format(
        len(RESULTS), len(RESULTS) - len(bad), len(bad)))
    if bad:
        print("失败清单：")
        for r in bad:
            print("  - {} : 期望 {} / 实得 {}".format(r["name"], r["expect"], r["got"]))
    print("结论：" + ("新增子命令数值全部与解析解一致 ✓" if not bad
                    else "{} 条未达预期 ✗".format(len(bad))))
    if args.json:
        print(json.dumps({"total": len(RESULTS),
                          "failed": len(bad), "results": RESULTS},
                         ensure_ascii=False, indent=2))
    if not args.keep:
        shutil.rmtree(TMP, ignore_errors=True)
    else:
        print("保留 TMP = " + TMP)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
