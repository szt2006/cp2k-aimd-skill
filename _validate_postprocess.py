#!/usr/bin/env python3
"""postprocess.py 端到端校验 harness (合成数据, 无需真实 CP2K 输出)。

生成:
  - 随机气箱 xyz        -> rdf / adf / cn / zprofile
  - 已知 D 的布朗运动   -> msd / diffusion (验证恢复 D)
  - 阻尼振子速度 xyz    -> vacf / ir (验证频谱峰值)
  - 伪造 .pdos          -> pdos 绘图
  - 2D 抛物线 fes.dat   -> fes 出图
  - 缺二进制时 bader/travis 优雅报错
"""
import os
import sys
import math
import tempfile

import numpy as np

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
    with open(path, "w") as f:
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
    with open(path, "w") as f:
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
    with open(path, "w") as f:
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
    with open(path, "w") as fh:
        fh.write("\n".join(rows) + "\n")


def gen_fes(path):
    rows = []
    for x in np.linspace(-2, 2, 40):
        for y in np.linspace(-2, 2, 40):
            e = 0.01 * (x * x + y * y)
            rows.append(f"{x:.4f} {y:.4f} {e:.6f}")
    with open(path, "w") as f:
        f.write("\n".join(rows) + "\n")


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

# ---------- 定量断言 ----------
# 1) diffusion 恢复 D
try:
    txt = open(os.path.join(TMP, "brown_diffusion.txt")).read()
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
    with open(os.path.join(TMP, "osc_ir.csv")) as f:
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

# ---------- 汇总 ----------
print("\n=== produced files ===")
for fn in sorted(os.listdir(TMP)):
    print("  ", fn)

print("\n=== result ===")
if errors:
    print(f"FAILED ({len(errors)} issue(s)):")
    for a, e in errors:
        print(f"  {a}: {e}")
    sys.exit(1)
else:
    print("ALL POSTPROCESS SUBCOMMANDS PASSED (0 error/0 crash)")
    sys.exit(0)
