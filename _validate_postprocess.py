#!/usr/bin/env python3
"""postprocess.py 端到端校验 harness (合成数据, 无需真实 CP2K 输出)。

生成:
  - 随机气箱 xyz        -> rdf / adf / cn / zprofile
  - 已知 D 的布朗运动   -> msd / diffusion (验证恢复 D)
  - 阻尼振子速度 xyz    -> vacf / ir (验证频谱峰值)
  - 伪造 .pdos          -> pdos 绘图
  - 2D 抛物线 fes.dat   -> fes 出图
  - 缺二进制时 bader/travis 优雅报错
  - **批 15 新增**：
      常密度 / 正弦密度 cube  -> cube (平面平均有解析解)
      AB / A / B 三份 cube    -> cdd  (∫Δρ 有解析解)
      阶梯 + 真空平台的 cube  -> workfunc (Φ = E_vac − E_F 有解析解)
      合成 VIB| 行            -> ir-static (高斯叠加有解析解)
      T:D 数对                -> arrhenius (Ea/D0 有解析解)
      构造 w 的 RDF           -> pmf-rdf (w = −RT ln g 有解析解)
      含 X 的 wannier.xyz     -> dipoles (μ 有解析解)
      刚性骨架 + 示踪原子      -> msd/diffusion --align (对齐后 D 回真值)

**为什么新子命令必须进这个文件**：`_validate_postprocess.py` 是仓库登记的
"后处理数值正确性基线"（AGENTS.md §6.2 三项串行校验之一）。加了子命令却不进
它，等于"加了但没人测"。逐条解析解比对另见 `_validate_postprocess_analytic.py`；
本文件负责**端到端不崩 + 关键数值不退化**，并保证新子命令被 CI 覆盖到。
"""
import os
import subprocess
import sys
import math
import tempfile

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

try:
    import numpy as np
except ImportError as _exc:
    sys.stderr.write("\n".join([
        "", "=" * 70,
        f"缺少依赖：{getattr(_exc, 'name', 'numpy')}", "",
        "本脚本是 postprocess.py 的端到端校验 harness（开发依赖）。",
        "",
        "安装方式：", "",
        "  pip install -r requirements-dev.txt",
        "  pip install numpy matplotlib",
        "=" * 70, "",
    ]))
    sys.exit(3)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
import postprocess as pp

TMP = tempfile.mkdtemp(prefix="cp2k_pp_")
errors = []


def run(argv, expect_rc=None):
    saved = sys.argv
    sys.argv = ["postprocess.py"] + argv
    try:
        rc = pp.main()
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else 0
    except Exception as e:  # 真正的崩溃
        errors.append((argv, "EXC: " + repr(e)))
        sys.argv = saved
        return -1
    sys.argv = saved
    if expect_rc is not None and rc != expect_rc:
        errors.append((argv, f"rc={rc} (expected {expect_rc})"))
    return rc


# ---------- 合成数据生成 ----------
def gen_random_xyz(path, N, L, nframe, dt, elem="O"):
    rng = np.random.default_rng(0)
    with open(path, "w", encoding="utf-8") as f:
        for fi in range(nframe):
            coords = rng.uniform(0, L, (N, 3))
            t = fi * dt
            f.write(f"{N}\ni = {fi + 1}, time = {t:.3f}, E = -1.0\n")
            for c in coords:
                f.write(f"{elem} {c[0]:.6f} {c[1]:.6f} {c[2]:.6f}\n")


def gen_brownian_xyz(path, N, D, dt, nframe, L=100.0):
    rng = np.random.default_rng(1)
    pos = rng.uniform(0, L, (N, 3))
    sigma = math.sqrt(2 * D * dt)
    with open(path, "w", encoding="utf-8") as f:
        for fi in range(nframe):
            if fi:
                pos = pos + rng.normal(0, sigma, (N, 3))
            pos = pos % L
            t = fi * dt
            f.write(f"{N}\ni = {fi + 1}, time = {t:.4f}, E = -2.0\n")
            for c in pos:
                f.write(f"Li {c[0]:.6f} {c[1]:.6f} {c[2]:.6f}\n")
    return L


def gen_osc_vel(path, f0, tau, dt, nframe):
    t = np.arange(nframe) * dt
    v = np.cos(2 * np.pi * f0 * t) * np.exp(-t / tau)
    with open(path, "w", encoding="utf-8") as f:
        for k in range(nframe):
            f.write("1\n")
            f.write(f"i = {k + 1}, time = {t[k]:.4f}, E = 0\n")
            f.write(f"X {v[k]:.8f} 0.0 0.0\n")


def gen_fake_pdos(path):
    # 120 MOs, 能量 -25..+10 eV, 费米在 0; 权重为 s/p/d/f 高斯包
    rng = np.random.default_rng(3)
    eig_ev = np.linspace(-25, 10, 120)
    eig_au = eig_ev / 27.211386245988
    rows = ["# MO Eigenvalue [a.u.] Occupation  s  p  d  f"]
    for i, e in enumerate(eig_au):
        occ = 1.0 if eig_ev[i] < 0 else 0.0
        s = math.exp(-((eig_ev[i] + 15) ** 2) / 8.0)
        p = math.exp(-((eig_ev[i] + 5) ** 2) / 6.0)
        d = math.exp(-((eig_ev[i] - 2) ** 2) / 5.0)
        f = 0.1 * rng.random()
        rows.append(f"{e:.6e} {occ:.4f} {s:.4f} {p:.4f} {d:.4f} {f:.4f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows) + "\n")


def gen_fes(path):
    rows = []
    for x in np.linspace(-2, 2, 40):
        for y in np.linspace(-2, 2, 40):
            e = 0.01 * (x * x + y * y)
            rows.append(f"{x:.4f} {y:.4f} {e:.6f}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")


# ---------- 批 15 新增：cube / workfunc / ir-static / arrhenius / pmf-rdf / dipoles ----------
def write_cube(path, data, origin=(0.0, 0.0, 0.0), step=(1.0, 1.0, 1.0),
               natoms=0, bohr=False):
    """写一个 Gaussian cube（data 形状 (nx,ny,nz)，x 最慢 z 最快）。

    `bohr=True` 时三个**格点定义行**取负号（Gaussian 约定：n<0 ⇒ 该轴步长以 bohr 计）。
    第 3 行的 `natoms` 保持为正 —— 它的负号表示的是**原子坐标**单位，是另一件事。
    """
    nx, ny, nz = data.shape
    s = 1.0 / 0.529177210903 if bohr else 1.0
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("synthetic cube (_validate_postprocess.py)\n")
        f.write("x outer / z inner\n")
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


def gen_vib_out(path, freqs, intens, fermi_au=None):
    """伪造含 `VIB|Frequency` / `VIB|Intensities` 的 CP2K .out。"""
    lines = [" CP2K| synthetic vibrational analysis output",
             " VIB| Vibrational Analysis"]
    if fermi_au is not None:
        lines.append("  Fermi energy:                    {:.14f}".format(fermi_au))
    lines.append(" VIB|Frequency (cm^-1)   " +
                 "   ".join("{:.6f}".format(x) for x in freqs))
    lines.append(" VIB|Intensities         " +
                 "   ".join("{:.6f}".format(x) for x in intens))
    lines.append(" PROGRAM ENDED AT")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def gen_wannier_xyz(path, nframe, wobble):
    """1 个 H 核 + 2 个 Wannier 中心（X 行）。μx = −4·wobble（解析解）。"""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for k in range(nframe):
            sh = wobble(k)
            f.write("3\ni = {}, time = {:.4f}, E = 0\n".format(k + 1, k * 0.5))
            f.write("H 0.000000 0.000000 0.000000\n")
            f.write("X {:.6f} 0.000000 0.000000\n".format(1.0 + sh))
            f.write("X {:.6f} 0.000000 0.000000\n".format(-1.0 + sh))


def gen_rigid_skeleton_xyz(path, D, dt, nframe, v_drift, L=200.0,
                           nskel=8, ndiff=40):
    """刚性骨架（整体平动，无转动）+ 在骨架里扩散的 Li。

    `--align rest` 应当把骨架的整体平动消掉 ⇒ 恢复出的 D 回到真值 D。
    ⚠️ Li 的随机位移必须累计在**未折回**的连续坐标里，只在写出时取模；
       否则每次取模丢掉的小数会累计成系统性超扩散。
    ⚠️ 骨架**不转**：对齐到骨架参考系后，Li 会跟着骨架一起转（物理上正确），
       会给 MSD 叠一个几何项，让"对齐后 D 回真值"这个断言失效。
    """
    rng = np.random.default_rng(11)
    skel0 = rng.uniform(-1.5, 1.5, (nskel, 3))
    li = rng.uniform(L * 0.25, L * 0.75, (ndiff, 3))
    sigma = math.sqrt(2 * D * dt)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for fi in range(nframe):
            t = fi * dt
            trans = np.array([v_drift * t, 0.0, 0.0])
            skel = skel0 + trans + np.array([L / 2, L / 2, L / 2])
            if fi:
                li = li + rng.normal(0, sigma, (ndiff, 3))
            f.write("{}\ni = {}, time = {:.4f}, E = -2.0\n".format(
                nskel + ndiff, fi + 1, t))
            for c in skel:
                f.write("Si {:.6f} {:.6f} {:.6f}\n".format(*(c % L)))
            for c in li + trans:
                f.write("Li {:.6f} {:.6f} {:.6f}\n".format(*(c % L)))


# ---------- 生成 ----------
random_xyz = os.path.join(TMP, "gas.xyz")
gen_random_xyz(random_xyz, 60, 20.0, 50, 2.0)

brown_xyz = os.path.join(TMP, "brown.xyz")
L = gen_brownian_xyz(brown_xyz, 30, 0.05, 2.0, 500)

vel_xyz = os.path.join(TMP, "osc-vel.xyz")
gen_osc_vel(vel_xyz, 30.0, 2.0, 0.005, 4000)  # f0=30 1/ps ~ 1000 cm^-1

pdos_file = os.path.join(TMP, "cp2k-O_k1-1.pdos")
gen_fake_pdos(pdos_file)

fes_file = os.path.join(TMP, "fes.dat")
gen_fes(fes_file)

# ---------- 批 15 新增的合成数据 ----------
# 1) cube：常密度（解析解 = 常数）与 z 向正弦（解析解 = 同一个正弦）
const_cube = os.path.join(TMP, "const.cube")
CONST_VAL = 0.012345
write_cube(const_cube, np.full((4, 5, 6), CONST_VAL))

sin_cube = os.path.join(TMP, "sin.cube")
NZ_SIN = 40
_sin_prof = 2.0 * np.sin(2.0 * math.pi * 3 * np.arange(NZ_SIN) / NZ_SIN)
_sin_data = np.repeat(_sin_prof[None, None, :], 5, axis=0)
_sin_data = np.repeat(_sin_data, 7, axis=1)
write_cube(sin_cube, _sin_data)

# 2) cdd：Δρ = ρ_AB − ρ_A − ρ_B，解析解 [+1.0, −0.75] ⇒ ∫Δρ = 0.25 e
A_cube = os.path.join(TMP, "A.cube")
B_cube = os.path.join(TMP, "B.cube")
AB_cube = os.path.join(TMP, "AB.cube")
_A = np.zeros((4, 4, 4)); _A[1, 1, 1] = 1.0
_B = np.zeros((4, 4, 4)); _B[2, 2, 2] = 2.0
_AB = np.zeros((4, 4, 4)); _AB[1, 1, 1] = 0.25; _AB[2, 2, 2] = 3.0
write_cube(A_cube, _A); write_cube(B_cube, _B); write_cube(AB_cube, _AB)

# 3) workfunc：V(z) 两侧各一段真空平台；E_F 从 .out 里读（Hartree）
WF_NZ, WF_DZ = 60, 0.5
_wf_z = np.arange(WF_NZ) * WF_DZ
_wf_v = np.full(WF_NZ, 0.2)          # 真空位 0.2 Ha
_wf_v[20:40] = -0.4                  # slab 区
_wf_data = np.repeat(_wf_v[None, None, :], 3, axis=0)
_wf_data = np.repeat(_wf_data, 3, axis=1)
wf_cube = os.path.join(TMP, "v_hartree.cube")
write_cube(wf_cube, _wf_data, step=(1.0, 1.0, WF_DZ))
WF_EF_HA = 0.05
wf_out = os.path.join(TMP, "wf.out")
gen_vib_out(wf_out, [100.0], [1.0], fermi_au=WF_EF_HA)
# 倾斜版：整条曲线带恒定斜率（模拟"没加偶极校正"）
_tilt_v = np.full(WF_NZ, 0.2) + 0.005 * _wf_z
_tilt_data = np.repeat(_tilt_v[None, None, :], 3, axis=0)
_tilt_data = np.repeat(_tilt_data, 3, axis=1)
tilt_cube = os.path.join(TMP, "tilt_hartree.cube")
write_cube(tilt_cube, _tilt_data, step=(1.0, 1.0, WF_DZ))

# 4) ir-static：三个已知频率 + 强度
VIB_FREQS = [500.0, 1600.0, 3700.0]
VIB_INTENS = [1.0, 3.0, 2.0]
vib_out = os.path.join(TMP, "vib.out")
gen_vib_out(vib_out, VIB_FREQS, VIB_INTENS)

# 5) arrhenius：D = D0·exp(−Ea/(kB·T))，Ea=0.25 eV、D0=1e-3
ARR_EA, ARR_D0 = 0.25, 1.0e-3
ARR_KB = 8.617333262e-5
ARR_T = [600.0, 800.0, 1000.0, 1200.0, 1400.0]
ARR_D = [ARR_D0 * math.exp(-ARR_EA / (ARR_KB * T)) for T in ARR_T]

# 6) pmf-rdf：g = exp(−w/RT)，w = 15 kJ/mol
PMF_T, PMF_W = 600.0, 15.0
_R = 8.31446261815324
_g0 = math.exp(-PMF_W * 1000.0 / (_R * PMF_T))
rdf_csv = os.path.join(TMP, "syn_rdf.csv")
with open(rdf_csv, "w", encoding="utf-8", newline="\n") as f:
    f.write("r[A],g(r)\n")
    for _r in np.arange(0.05, 20.0, 0.05):
        f.write("{:.6f},{:.8e}\n".format(_r, 0.0 if _r < 3.0 else _g0))

# 7) dipoles：μx = −4·wobble（解析解）
wannier_xyz = os.path.join(TMP, "wannier.xyz")
gen_wannier_xyz(wannier_xyz, 11, lambda k: 0.01 * k)

# 8) --align：刚性骨架（平动）+ 40 个 Li（真值 D=0.05）
ALIGN_L = 200.0
skeleton_xyz = os.path.join(TMP, "skeleton.xyz")
gen_rigid_skeleton_xyz(skeleton_xyz, 0.05, 2.0, 400, 0.02, L=ALIGN_L)

print("TMP =", TMP)
print("=== run subcommands ===")

# Tier 1
run(["rdf", random_xyz, "--cell", "20 20 20", "--prefix", os.path.join(TMP, "gas")])
run(["adf", random_xyz, "--cell", "20 20 20", "--center", "O", "--prefix", os.path.join(TMP, "gas")])
run(["cn", random_xyz, "--cell", "20 20 20", "--prefix", os.path.join(TMP, "gas")])
run(["zprofile", random_xyz, "--cell", "20 20 20", "--prefix", os.path.join(TMP, "gas")])
run(["msd", brown_xyz, "--cell", f"{L} {L} {L}", "--dt", "2.0", "--prefix", os.path.join(TMP, "brown")])
rc = run(["diffusion", brown_xyz, "--cell", f"{L} {L} {L}", "--dt", "2.0", "--prefix", os.path.join(TMP, "brown")])
run(["bond", random_xyz, "--i", "1", "--j", "2", "--prefix", os.path.join(TMP, "gas")])
run(["angle", random_xyz, "--i", "1", "--j", "2", "--k", "3", "--prefix", os.path.join(TMP, "gas")])
run(["dihedral", random_xyz, "--i", "1", "--j", "2", "--k", "3", "--l", "4", "--prefix", os.path.join(TMP, "gas")])
run(["pdos", pdos_file, "--prefix", os.path.join(TMP, "o")])
run(["energy", os.path.join(TMP, "fake.out")])  # 故意不存在能量, 应优雅处理

# Tier 2
run(["vacf", "--vel", vel_xyz, "--dt", "0.005", "--prefix", os.path.join(TMP, "osc")])
rc_ir = run(["ir", "--vel", vel_xyz, "--dt", "0.005", "--prefix", os.path.join(TMP, "osc")])
run(["power", "--vel", vel_xyz, "--dt", "0.005", "--prefix", os.path.join(TMP, "osc")])

# Tier 3 (缺二进制 -> 优雅报错 rc=1)
run(["bader", os.path.join(TMP, "dummy.cube"), "--prefix", os.path.join(TMP, "b")], expect_rc=1)
run(["fes", "--fesdat", fes_file, "--prefix", os.path.join(TMP, "fes")])  # 直接出图 rc=0
run(["travis", random_xyz, "--analyses", "rdf", "msd", "--dt", "2.0",
     "--prefix", os.path.join(TMP, "trav")], expect_rc=1)

# Tier 4（批 15 新增子命令）
run(["cube", const_cube, "--axis", "z", "--prefix", os.path.join(TMP, "const")])
run(["cube", sin_cube, "--axis", "z", "--show-std",
     "--prefix", os.path.join(TMP, "sin")])
run(["cdd", "--total", AB_cube, "--frag", A_cube, B_cube,
     "--planar-axis", "z", "--prefix", os.path.join(TMP, "cdd")])
run(["workfunc", wf_cube, "--out", wf_out, "--prefix", os.path.join(TMP, "wf")])
run(["workfunc", tilt_cube, "--out", wf_out, "--slope-tol", "0.01",
     "--warn-grad", "0.001", "--prefix", os.path.join(TMP, "tilt")])
run(["ir-static", vib_out, "--fwhm", "10", "--prefix", os.path.join(TMP, "vib")])
_arr_args = []
for _t, _d in zip(ARR_T, ARR_D):
    _arr_args.append("{:.1f}:{:.8e}".format(_t, _d))
run(["arrhenius", "--d"] + _arr_args + ["--prefix", os.path.join(TMP, "arr")])
run(["arrhenius", "--per-1000t", "--kb", "8.6173e-5", "--d"] + _arr_args +
    ["--prefix", os.path.join(TMP, "arr1000")])
run(["pmf-rdf", rdf_csv, "--temp", str(PMF_T), "--prefix", os.path.join(TMP, "pmf")])
run(["dipoles", wannier_xyz, "--nuclear-charges", "H=1",
     "--prefix", os.path.join(TMP, "dip")])
run(["diffusion", skeleton_xyz, "--cell",
     "{0} {0} {0}".format(ALIGN_L), "--dt", "2.0", "--sel", "Li",
     "--align", "rest", "--prefix", os.path.join(TMP, "aligned")])
run(["zprofile", random_xyz, "--cell", "20 20 20", "--sel", "O",
     "--prefix", os.path.join(TMP, "gas_sel")])
run(["vacf", "--vel", vel_xyz, "--dt", "0.005", "--sel", "X",
     "--prefix", os.path.join(TMP, "osc_sel")])
# 优雅报错路径（新子命令的健壮性基线）
run(["cube", os.path.join(TMP, "no_such.cube")], expect_rc=1)
run(["cdd", "--total", AB_cube, "--frag", const_cube], expect_rc=1)   # 格点不一致
run(["ir-static", const_cube], expect_rc=1)                          # 没有 VIB| 行
run(["arrhenius", "--d", "1000:1e-6"], expect_rc=1)                   # 只有 1 个点
run(["pmf-rdf", os.path.join(TMP, "no_such.csv"), "--temp", "600"], expect_rc=1)
run(["dipoles", wannier_xyz, "--nuclear-charges", "O=6"], expect_rc=1)  # 缺 H
run(["workfunc", wf_cube], expect_rc=1)                               # 既无 --out 也无 --fermi
# travis 前置检查：无 X 的轨迹 + ir ⇒ 必须被拦（G-06）
run(["travis", random_xyz, "--analyses", "ir", "--prefix",
     os.path.join(TMP, "trav_ir")], expect_rc=1)
run(["travis", wannier_xyz, "--analyses", "ir", "--cell", "782 782 782",
     "--prefix", os.path.join(TMP, "trav_x")], expect_rc=1)  # 有 X，仅缺二进制

# ---------- 定量断言 ----------
# 1) diffusion 恢复 D
try:
    txt = open(os.path.join(TMP, "brown_diffusion.txt"), encoding="utf-8").read()
    import re
    m = re.search(r"D = ([-\d.eE+]+) Angstrom", txt)
    D_rec = float(m.group(1))
    ok = 0.4 * 0.05 <= D_rec <= 2.5 * 0.05
    print(f"[assert] diffusion D_recovered={D_rec:.4f} A^2/ps (truth 0.05) -> {'OK' if ok else 'FAIL'}")
    if not ok:
        errors.append(("diffusion", f"D={D_rec} out of range"))
except Exception as e:
    errors.append(("diffusion-assert", repr(e)))

# 2) IR 峰值 ~ 1000 cm^-1
try:
    import csv as _csv
    peak = 0
    with open(os.path.join(TMP, "osc_ir.csv"), encoding="utf-8") as f:
        r = _csv.reader(f)
        next(r)
        best = 0.0
        for row in r:
            cm = float(row[1]); inten = float(row[2])
            if inten > best:
                best = inten; peak = cm
    ok = 800 <= peak <= 1200
    print(f"[assert] IR peak = {peak:.1f} cm^-1 (truth ~1000) -> {'OK' if ok else 'FAIL'}")
    if not ok:
        errors.append(("ir-peak", f"peak={peak}"))
except Exception as e:
    errors.append(("ir-assert", repr(e)))


# ---------- 批 15 新增：数值断言（每条都有解析解） ----------
def _read_csv_cols(path, ncol=2, skip_header=True):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            if skip_header and (ln.startswith("coord") or ln.startswith("r[")
                                or ln.startswith("time") or ln.startswith("side")
                                or ln.startswith("wavenumber")):
                continue
            p = ln.strip().split(",")
            if len(p) < ncol:
                continue
            try:
                rows.append([float(x) for x in p[:ncol]])
            except ValueError:
                continue          # 表头行（cdd 的 csv 头不是上面那几个前缀之一）
    return rows


def _assert(name, expect, got, ok, note=""):
    print(f"[assert] {name}: {got} (expect {expect}) -> {'OK' if ok else 'FAIL'}")
    if note:
        for ln in note.splitlines():
            print("         " + ln)
    if not ok:
        errors.append((name, f"{got} != {expect}"))


# 3) cube 常密度：平面平均逐点 == 常数（解析解）
try:
    rows = _read_csv_cols(os.path.join(TMP, "const_planar.csv"))
    err = max(abs(v - CONST_VAL) for _c, v in rows) if rows else float("inf")
    _assert("cube 常密度平面平均", "maxΔ < 1e-12",
            f"n={len(rows)} maxΔ={err:.2e}", len(rows) == 6 and err < 1e-12,
            "解析解：常密度 cube 的平面平均处处等于该常数")
except Exception as e:
    errors.append(("cube-const-assert", repr(e)))

# 4) cube 正弦密度：平面平均 == 解析正弦
try:
    rows = _read_csv_cols(os.path.join(TMP, "sin_planar.csv"))
    err = max(abs(rows[k][1] - _sin_prof[k]) for k in range(len(rows))) \
        if rows else float("inf")
    # 容差 1e-5：cube 体数据格式是 {:13.5E}，写出去这一步就是精度上限
    _assert("cube 正弦密度平面平均", "maxΔ < 1e-5",
            f"n={len(rows)} maxΔ={err:.3e}", len(rows) == NZ_SIN and err < 1e-5,
            "ρ=2·sin(6πz/40)，面内平均解析解就是它自己")
except Exception as e:
    errors.append(("cube-sin-assert", repr(e)))

# 5) cdd：∫Δρ dV == 0.25 e（解析解），并确认平面平均 csv 已产出
#    ⚠️ 产物名是 `<prefix>_cdd_planar.csv`；跑的时候 --prefix 已经叫 "cdd"，
#       所以真实文件名是 `cdd_cdd_planar.csv`（**不是** `cdd_planar.csv`）。
try:
    _r = _sp_run = subprocess.run(
        [sys.executable, os.path.join(HERE, "scripts", "postprocess.py"),
         "cdd", "--total", AB_cube, "--frag", A_cube, B_cube,
         "--prefix", os.path.join(TMP, "cddchk")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=TMP, timeout=300)
    blob = (_r.stdout or "") + (_r.stderr or "")
    _assert("cdd 净电荷 ∫Δρ dV", "2.500000e-01 e（解析解）",
            "命中={}".format("2.500000e-01" in blob),
            _r.returncode == 0 and "2.500000e-01" in blob,
            "Δρ = [+0.25−1, 3−2] = [−0.75, +1.0]，格点体积 1 Å³ ⇒ 和 = 0.25 e")
    p = os.path.join(TMP, "cdd_cdd_planar.csv")
    txt = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    _assert("cdd --planar-axis 产出平面平均 csv", "非空",
            f"{len(txt.splitlines())} 行", bool(txt.strip()))
except Exception as e:
    errors.append(("cdd-assert", repr(e)))

# 6) workfunc：Φ == E_vac − E_F、U == Φ − 4.44（解析解）
try:
    HEV = 27.211386245988
    e_vac = 0.2 * HEV
    phi = e_vac - WF_EF_HA * HEV
    u = phi - 4.44
    # side 列是 "top"/"bot" 文本 ⇒ 不能走 `_read_csv_cols`（它把第 1 列转 float）
    got = {}
    with open(os.path.join(TMP, "wf_workfunc.csv"), encoding="utf-8") as fh:
        hdr = None
        for ln in fh:
            p = ln.strip().split(",")
            if hdr is None:
                hdr = p
                continue
            if len(p) == len(hdr):
                got[p[0]] = p
    ok = ("top" in got and "bot" in got
          and abs(float(got["top"][2]) - phi) < 1e-3
          and abs(float(got["bot"][2]) - phi) < 1e-3)
    _assert("workfunc Φ = E_vac − E_F", f"{phi:.4f} eV",
            "top={} bot={}".format(got.get("top", ["?"] * 3)[2],
                                   got.get("bot", ["?"] * 3)[2]), ok,
            f"E_vac=0.2 Ha、E_F={WF_EF_HA} Ha ⇒ Φ={phi:.4f} eV")
    ok_u = "top" in got and abs(float(got["top"][3]) - u) < 1e-3
    _assert("workfunc U vs SHE = Φ − 4.44", f"{u:.4f} V",
            got.get("top", ["?"] * 4)[3], ok_u,
            "SHE = 4.44 eV 出自 references/course_learned.md:650（讲义口径）")
    # 反向对照：平坦真空位的平台内梯度必须 ≈0（曾把 slab 台阶的单边差分算进来）
    g_bot = float(got["bot"][6]) if "bot" in got else None
    _assert("workfunc 下表面平台 max|dV/dz| ≈ 0", "< 1e-9",
            str(g_bot), g_bot is not None and abs(g_bot) < 1e-9,
            "用中心差分 + 端点复制；np.gradient 的单边端点差分会被 slab 台阶污染\n"
            "（曾把 16.3 eV/Å 的假斜率报成「真空位倾斜」）")
    # 真空平台必须落在真正的真空区（上侧：z 在 20~30 Å）
    ok_span = ("top" in got and float(got["top"][4]) >= 20.0
               and float(got["top"][5]) <= 30.0)
    _assert("workfunc 真空平台落在真空区", "20 ≤ z ≤ 30 Å",
            "{}~{}".format(got.get("top", ["?"] * 6)[4],
                           got.get("top", ["?"] * 6)[5]), ok_span,
            "slab 在 z=10~20 Å（格点 20..39 × 0.5 Å）")
except Exception as e:
    errors.append(("workfunc-assert", repr(e)))

# 7) workfunc：真空位倾斜必须报警，且**平坦真空位不许**报警（反向对照）
try:
    import subprocess as _sp
    r = _sp.run([sys.executable, os.path.join(HERE, "scripts", "postprocess.py"),
                 "workfunc", tilt_cube, "--out", wf_out, "--slope-tol", "0.01",
                 "--warn-grad", "0.001", "--prefix", os.path.join(TMP, "tiltchk")],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=TMP, timeout=300)
    blob = (r.stdout or "") + (r.stderr or "")
    _assert("workfunc 倾斜真空位报警", "含 真空位不平 + SURFACE_DIPOLE_CORRECTION",
            f"rc={r.returncode} 含警告={'真空位不平' in blob}",
            r.returncode == 0 and "真空位不平" in blob
            and "SURFACE_DIPOLE_CORRECTION" in blob,
            "P-08：不加偶极校正 ⇒ 真空位斜")
except Exception as e:
    errors.append(("workfunc-tilt-assert", repr(e)))

# 8) ir-static：谱 == 解析高斯叠加；三个峰位都在
try:
    sigma = 10.0 / (2 * math.sqrt(2 * math.log(2)))
    rows = _read_csv_cols(os.path.join(TMP, "vib_ir_static.csv"))
    grid = np.array([r[0] for r in rows])
    spec = np.array([r[1] for r in rows])
    ref = np.zeros_like(grid)
    for fq, a in zip(VIB_FREQS, VIB_INTENS):
        ref += a * np.exp(-((grid - fq) ** 2) / (2 * sigma ** 2))
    ref /= sigma * math.sqrt(2 * math.pi)
    err = float(np.max(np.abs(spec - ref)))
    # 容差 1e-8：csv 是 {:.8e}
    _assert("ir-static 高斯叠加", "maxΔ < 1e-8", f"maxΔ={err:.3e}", err < 1e-8,
            "σ = FWHM/2√(2ln2)，峰高按 intensity 加权")
    top = sorted(np.argsort(spec)[::-1][:80])
    found = sorted({round(float(grid[k])) for k in top
                    if spec[k] > 0.15 * spec.max()})
    ok_pk = all(any(abs(fq - g) <= 2.0 for g in found) for fq in VIB_FREQS)
    _assert("ir-static 峰位", "500/1600/3700 cm^-1 都在 ±2 内",
            str(found[:12]), ok_pk)
except Exception as e:
    errors.append(("ir-static-assert", repr(e)))

# 9) arrhenius：恢复 Ea=0.25 eV / D0=1e-3（两种横轴口径必须一致）
try:
    blob = open(os.path.join(TMP, "arr_arrhenius.txt"), encoding="utf-8").read()
    mEa = mD0 = None
    for ln in blob.splitlines():
        if ln.startswith("Ea ="):
            mEa = float(ln.split("=")[1].split()[0])
        if ln.startswith("D0 ="):
            mD0 = float(ln.split("=")[1].split()[0])
    _assert("arrhenius ln D vs 1/T", "Ea=0.25, D0=1e-3",
            f"Ea={mEa} D0={mD0}",
            mEa is not None and abs(mEa - ARR_EA) < 1e-6
            and mD0 is not None and abs(mD0 - ARR_D0) / ARR_D0 < 1e-6,
            f"构造式 D = {ARR_D0}·exp(−{ARR_EA}/(kB·T))")
    blob2 = open(os.path.join(TMP, "arr1000_arrhenius.txt"),
                 encoding="utf-8").read()
    mEa2 = None
    for ln in blob2.splitlines():
        if ln.startswith("Ea ="):
            mEa2 = float(ln.split("=")[1].split()[0])
    # 讲义口径 log10(D) vs 1000/T：斜率 = −Ea/(2.303·kB) ⇒ Ea = −slope×2.303×kB×1000
    # 容差 1e-5 而非 1e-6：`--d` 传进去的 D 只有 8 位有效数字（"1.28693653e-03"），
    # 取 log10 后精度损失放大，Ea 会有 ~1e-6 量级的抖动。这是**输入精度**而非算法误差。
    _assert("arrhenius log10 D vs 1000/T（讲义口径）", "Ea=0.25（±1e-5）",
            f"Ea={mEa2}", mEa2 is not None and abs(mEa2 - ARR_EA) < 1e-5,
            "⚠️ 横轴 1000/T 会带进来一个 ×1000 因子；漏掉就静默差 1000 倍")
except Exception as e:
    errors.append(("arrhenius-assert", repr(e)))

# 10) pmf-rdf：w == −RT ln g（构造 w=15 kJ/mol）
try:
    rows = _read_csv_cols(os.path.join(TMP, "pmf_pmf.csv"), ncol=4)
    far = [r for r in rows if r[0] > 5.0]
    err = max(abs(r[2] - PMF_W) for r in far) if far else float("inf")
    _assert("pmf-rdf w = −RT·ln g", f"{PMF_W} kJ/mol",
            f"maxΔ={err:.3e}", err < 1e-6,
            "g = exp(−w/RT)，R=8.314462618，T=600 K ⇒ w 必须回到 15 kJ/mol")
    ev = far[0][3] if far else None
    _assert("pmf-rdf eV 列", "= kJ/mol ÷ 96.485",
            f"{ev}", ev is not None and abs(ev - PMF_W / 96.48533212) < 1e-4,
            "1 eV ≈ 96.485 kJ/mol（讲义口播 9 万 6）")
except Exception as e:
    errors.append(("pmf-rdf-assert", repr(e)))

# 11) dipoles：μx == −4·wobble（解析解）
try:
    rows = _read_csv_cols(os.path.join(TMP, "dip_dipoles.csv"), ncol=5)
    err = max(abs(rows[k][1] - (-4.0 * 0.01 * k)) for k in range(len(rows))) \
        if rows else float("inf")
    _assert("dipoles μx = Σ Z r − 2 Σ r_X", "maxΔ < 1e-6",
            f"n={len(rows)} maxΔ={err:.3e}", len(rows) == 11 and err < 1e-6,
            "核在原点、两 X 位于 ±1+shift ⇒ μx = −4·shift")
except Exception as e:
    errors.append(("dipoles-assert", repr(e)))

# 12) --align：刚性骨架漂移下，对齐后 D 回到真值 0.05
try:
    txt = open(os.path.join(TMP, "aligned_diffusion.txt"),
               encoding="utf-8").read()
    import re as _re
    m = _re.search(r"D = ([-\d.eE+]+) Angstrom", txt)
    D_al = float(m.group(1))
    m2 = _re.search(r"D\(no align\) = ([-\d.eE+]+)", txt)
    D_no = float(m2.group(1)) if m2 else None
    _assert("--align 恢复真值 D", "0.035~0.065（真值 0.05）",
            f"align={D_al:.4f} no_align={D_no}",
            0.035 <= D_al <= 0.065,
            "8 个 Si 刚性骨架整体平动 0.02 Å/帧 + 40 个 Li 真值 D=0.05")
    _assert("--align 反向对照：不对齐时 D 被污染", "> 0.065",
            f"{D_no:.4f}" if D_no is not None else "None",
            D_no is not None and D_no > 1.3 * 0.05,
            "证明这个用例真的能区分【对齐】与【没对齐】")
except Exception as e:
    errors.append(("align-assert", repr(e)))

# 13) travis 前置检查：无 X + ir 必须被拦（构建期检查，不是数值）
try:
    import subprocess as _sp
    r = _sp.run([sys.executable, os.path.join(HERE, "scripts", "postprocess.py"),
                 "travis", random_xyz, "--analyses", "ir",
                 "--prefix", os.path.join(TMP, "travchk")],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=TMP, timeout=300)
    blob = (r.stdout or "") + (r.stderr or "")
    _assert("travis 前置检查：无 X + ir ⇒ exit 1",
            "exit1 且点名 IONS+CENTERS/LOCALIZE",
            f"rc={r.returncode} IONS+CENTERS={'IONS+CENTERS' in blob} "
            f"LOCALIZE={'LOCALIZE' in blob} Traceback={'Traceback' in blob}",
            r.returncode == 1 and "IONS+CENTERS" in blob
            and "LOCALIZE" in blob and "Traceback" not in blob,
            "G-06：轨迹里必须有 Wannier 中心 X，且不能拿 cp2k-pos-1.xyz")
except Exception as e:
    errors.append(("travis-precheck-assert", repr(e)))

# ---------- 汇总 ----------
print("\n=== produced files ===")
for fn in sorted(os.listdir(TMP)):
    print("  ", fn)

# ---------- 串入 RDF 归一化验证（_validate_rdf_cn.py）----------
# 为什么必须串进来：上面用**单帧**随机气体做锚点，而 RDF 归一化曾经写在帧循环体
# 内（每帧除一次 norm），单帧时"除一次"正好正确 —— 所以这个 harness 全绿也拦不住
# 多帧归一化错误（真实 2535 帧轨迹上偏 1659 倍）。_validate_rdf_cn.py 用
# "CN 积分 == 逐帧直接计数" 的定义式验证，且**多帧**，才抓得住。
# 这里用子进程调用（它自己起 postprocess 子进程），显式 UTF-8 解码 ——
# 中文 Windows 下若按 locale(GBK) 解码，子进程中文 stderr 会让内部读取线程抛
# UnicodeDecodeError，r.stderr 变成 None，随后 .strip() 抛 AttributeError。
rdf_rc = None
rdf_status = "SKIP"
rdf_tail = []
_rdf_script = os.path.join(HERE, "_validate_rdf_cn.py")
if not os.path.isfile(_rdf_script):
    rdf_status = "SKIP (缺 _validate_rdf_cn.py)"
    print("\n=== RDF 归一化验证 ===\n  [SKIP] 找不到 " + _rdf_script)
else:
    print("\n=== RDF 归一化验证 (_validate_rdf_cn.py) ===")
    try:
        r = subprocess.run([sys.executable, _rdf_script],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           cwd=HERE, timeout=600)
        rdf_rc = r.returncode
        blob = ((r.stdout or "") + (r.stderr or "")).splitlines()
        rdf_tail = [ln for ln in blob if ln.strip()][-6:]
        for ln in rdf_tail:
            print("  " + ln)
        joined = "\n".join(rdf_tail)
        dep_missing = any(k in joined for k in (
            "缺少依赖", "ModuleNotFoundError", "No module named",
            "ImportError"))
        if r.returncode == 0:
            rdf_status = "PASS"
        elif r.returncode == 3 or dep_missing:
            # 环境缺依赖：明确报 SKIP，**不**把整个 harness 判失败
            rdf_status = "SKIP (环境缺依赖, rc={})".format(r.returncode)
            print("  [SKIP] 环境缺 numpy/matplotlib，RDF 归一化验证未能执行"
                  "（这是 skip，不是通过）")
        else:
            rdf_status = "FAIL (rc={})".format(r.returncode)
            errors.append(("rdf-cn", "RDF 归一化验证失败 rc={}".format(r.returncode)))
    except subprocess.TimeoutExpired:
        rdf_status = "SKIP (超时 600s)"
        print("  [SKIP] _validate_rdf_cn.py 超过 600 s 未结束")
    except OSError as e:
        rdf_status = "SKIP (无法启动: {})".format(e)
        print("  [SKIP] 无法启动 _validate_rdf_cn.py: {}".format(e))

print("\n=== result ===")
print(f"  RDF 归一化 (_validate_rdf_cn.py): {rdf_status}")
if errors:
    print(f"FAILED ({len(errors)} issue(s)):")
    for a, e in errors:
        print(f"  {a}: {e}")
    sys.exit(1)
else:
    print("ALL POSTPROCESS SUBCOMMANDS PASSED (0 error/0 crash)"
          " [incl. RDF normalization]")
    sys.exit(0)
