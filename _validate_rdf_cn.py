#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""RDF 归一化的解析型验证：配位数必须等于直接数出来的平均近邻数。

**为什么需要这个测试**：`postprocess.py` 的 RDF 归一化曾经写在帧循环体内
（每帧都除一次 norm），帧数越多偏得越狠 —— 真实 2535 帧轨迹上偏 **1659 倍**。
原有的 `_validate_postprocess.py` 用**单帧**随机气体做锚点，单帧时"除一次"
正好正确，所以一直是绿的。**单帧锚点抓不到多帧归一化错误。**

这里用定义来验，不依赖任何参照实现：

    CN(r_max) = ∫₀^{r_max} g(r) · ρ_B · 4πr² dr

物理含义是"A 原子周围 r_max 内的 B 原子平均个数"，可以**直接逐帧数**出来。
两者对上，归一化就是对的。

用法：python _validate_rdf_cn.py [--postprocess 路径] [--frames N]

`--postprocess` 可以指向**另一个副本**的 postprocess.py，用来做 A/B 对照
（证明修复前后确实不同）。例如指向未修的 v1.1 副本：
    python _validate_rdf_cn.py --postprocess ..\cp2k-aimd-v1.1\scripts\postprocess.py
"""
import argparse
import io
import math
import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
try:
    import _console  # noqa: F401
except Exception:
    pass

PY = sys.executable


def write_xyz(path, frames):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        for els, xyz in frames:
            fh.write("{}\nframe\n".format(len(els)))
            for e, (x, y, z) in zip(els, xyz):
                fh.write("{} {:.6f} {:.6f} {:.6f}\n".format(e, x, y, z))


def pbc_delta(a, b, L):
    d = []
    for k in range(3):
        v = a[k] - b[k]
        v -= L[k] * round(v / L[k])
        d.append(v)
    return math.sqrt(sum(x * x for x in d))


def direct_cn(els, frames, a_el, b_el, rmax, L):
    """逐帧直接数 A 周围 rmax 内的 B 个数，取平均。"""
    tot, n_a = 0, 0
    for els_f, xyz in frames:
        ia = [i for i, e in enumerate(els_f) if e == a_el]
        ib = [i for i, e in enumerate(els_f) if e == b_el]
        for i in ia:
            n_a += 1
            for j in ib:
                if i == j:
                    continue
                if pbc_delta(xyz[i], xyz[j], L) < rmax:
                    tot += 1
    return tot / n_a


def main():
    ap = argparse.ArgumentParser(description="RDF 归一化解析型验证")
    ap.add_argument("--postprocess", default=os.path.join(
        HERE, "scripts", "postprocess.py"),
        help="要测的 postprocess.py（默认本仓库的；可指向别的副本做 A/B 对照）")
    ap.add_argument("--frames", type=int, default=40, help="帧数（>1 才能暴露重复归一化）")
    args = ap.parse_args()
    PP = os.path.abspath(args.postprocess)

    random.seed(20261006)
    L = [12.0, 12.0, 12.0]
    # 1 个 A(=O) + 24 个 B(=H)，随机分布在盒子里、**多帧**（关键：M>1）
    # 位置随机 ⇒ 没有解析解，但配位数可以直接数，两者必须一致。
    M = args.frames
    frames = []
    for _ in range(M):
        els = ["O"] + ["H"] * 24
        xyz = [(random.uniform(0, L[0]), random.uniform(0, L[1]),
                random.uniform(0, L[2])) for _ in els]
        frames.append((els, xyz))

    rmax = 5.0
    box = "{:.6f} 0 0 0 {:.6f} 0 0 0 {:.6f}".format(*L)
    with tempfile.TemporaryDirectory() as td:
        traj = os.path.join(td, "mix.xyz")
        write_xyz(traj, frames)
        # postprocess 用 --prefix 指定输出前缀（不是 -o），产物是 <prefix>_rdf.csv
        pref = os.path.join(td, "rdf")
        out = pref + "_rdf.csv"
        cmd = [PY, PP, "rdf", traj, "--pairs", "O H", "--rmax", str(rmax),
               "--bins", "250", "--cell", box, "--prefix", pref]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print("[FAIL] postprocess rdf 跑失败:\n" + (r.stderr or "")[-1500:])
            return 1
        if not os.path.isfile(out):
            print("[FAIL] 没生成 CSV: " + out)
            return 1

        rows = [ln.split(",") for ln in
                io.open(out, encoding="utf-8").read().splitlines() if ln.strip()]
        hdr, data = rows[0], rows[1:]
        # 列名是 g_<元素1>-<元素2>，顺序按元素排序（O,H → g_H-O），这里放宽匹配
        cand = [i for i, h in enumerate(hdr)
                if h.startswith("g_") and {*h[2:].split("-")} == {"O", "H"}]
        if not cand:
            print("[FAIL] CSV 表头里找不到 O-H 列: " + repr(hdr))
            return 1
        icol = cand[0]
        rcol = hdr.index("r[A]")

        V = L[0] * L[1] * L[2]
        rho_b = 24 / V
        # CN = Σ g(r) ρ_B 4πr² dr
        cn = 0.0
        prev_r = None
        peak = 0.0
        for row in data:
            rv = float(row[rcol])
            g = float(row[icol])
            peak = max(peak, g)
            if prev_r is not None:
                dr = rv - prev_r
                rc = 0.5 * (rv + prev_r)
                cn += g * rho_b * 4 * math.pi * rc * rc * dr
            prev_r = rv

    cn_direct = direct_cn(["O"] + ["H"] * 24, frames, "O", "H", rmax, L)

    print("=" * 70)
    print("RDF 归一化验证（多帧 {} 帧，O + 24H 随机气体，rmax={} Å）".format(M, rmax))
    print("=" * 70)
    print("  曲线峰值 g_max        : {:.4f}".format(peak))
    print("  积分得到配位数 CN     : {:.6f}".format(cn))
    print("  逐帧直接数出配位数    : {:.6f}".format(cn_direct))
    rel = abs(cn - cn_direct) / cn_direct if cn_direct else float("inf")
    print("  相对偏差              : {:.4%}".format(rel))
    print()
    # 数值积分用矩形法，且 g(r) 有噪声，1% 以内即认为归一化正确
    if rel < 0.01:
        print("结论：归一化正确 ✓（多帧不再重复相除）")
        return 0
    print("结论：归一化仍有问题 ✗ —— CN 与直接计数不符")
    return 1


if __name__ == "__main__":
    sys.exit(main())
