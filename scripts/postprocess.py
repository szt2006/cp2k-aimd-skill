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

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


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
    text = open(path, errors="ignore").read().splitlines()
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
        lines = open(path, errors="ignore").read().splitlines()
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
    """按优先级: --cell > .out 解析 > None(非周期)。"""
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
    return path


def write_csv(path, header, rows):
    if isinstance(header, list):
        header = ",".join(header)
    with open(path, "w") as f:
        f.write(header + "\n")
        for r in rows:
            f.write(",".join(str(x) for x in r) + "\n")
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
def cmd_energy(args):
    path = args.out
    if not os.path.exists(path):
        print(f"ERROR: 找不到能量文件 {path}")
        return 1
    lines = open(path, errors="ignore").read().splitlines()
    energies = []
    for ln in lines:
        m = re.search(r"ENERGY\|\s+Total FORCE_EVAL.*?:\s*([-\d.eE+]+)", ln)
        if m:
            energies.append(float(m.group(1)))
    temps = []
    for ln in lines:
        if "emperature" in ln.lower():
            m = re.search(r"([-\d.eE+]+)", ln.split("emperature")[-1])
            if m:
                temps.append(float(m.group(1)))
    if not energies:
        # 退化: 试 .ener 风格两列
        for ln in lines:
            parts = ln.split()
            if len(parts) >= 2:
                try:
                    energies.append(float(parts[-1]))
                except ValueError:
                    pass
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
    ax.set_ylabel("total energy [a.u.]")
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
    uniq = sorted(set(elements))
    if pairs_arg:
        pairs = []
        for p in pairs_arg:
            a, b = p.split()
            pairs.append(tuple(sorted((a, b))))
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
            na = len(ia)
            nb = len(ib)
            rho_b = nb / V
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
            # 归一化因子: 该对 (A 原子数 * 帧数) * 4πr² dr * rho_b
            norm = na * M * 4 * math.pi * r_centers**2 * dr * rho_b
            hist[(a, b)] /= norm
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
def compute_msd(frames, H, sel, dim):
    un = unwrap_traj(frames, H)
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
    return msd  # in Angstrom^2


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


def cmd_msd(args):
    elements, frames, times, _ = read_xyz(args.traj)
    H = get_cell(args)
    sel = _parse_sel(args.sel, elements)
    msd = compute_msd(frames, H, sel, args.dim)
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
    ax.set_title(f"Mean square displacement (dim={args.dim})")
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_msd.png")
    print(f"MSD: {len(t)} frames -> {prefix}_msd.png")
    return 0


def cmd_diffusion(args):
    elements, frames, times, _ = read_xyz(args.traj)
    H = get_cell(args)
    sel = _parse_sel(args.sel, elements)
    msd = compute_msd(frames, H, sel, args.dim)
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
    prefix = out_prefix(args)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(t, msd, lw=1.2, label="MSD")
    ax.plot(t[lo:hi], slope * t[lo:hi] + intercept, "r--", label=f"fit (D={d_aps:.4f} A^2/ps)")
    ax.set_xlabel("time [ps]")
    ax.set_ylabel("MSD [Angstrom^2]")
    ax.set_title(f"Diffusion coefficient (dim={args.dim})")
    ax.legend()
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_diffusion.png")
    txt = prefix + "_diffusion.txt"
    with open(txt, "w") as f:
        f.write(f"D = {d_aps:.6f} Angstrom^2/ps = {d_cgs:.6e} cm^2/s\n")
        f.write(f"fit range: steps {lo}..{hi} (t={t[lo]:.3f}..{t[hi-1]:.3f} ps)\n")
        f.write(f"MSD slope = {slope:.6f} Angstrom^2/ps\n")
    print(f"Diffusion: D = {d_aps:.6f} A^2/ps = {d_cgs:.4e} cm^2/s  (fit {lo}..{hi})")
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
    for ln in open(fpath, errors="ignore"):
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
    with open(txt, "w") as f:
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
    _, frames, _, _ = read_xyz(args.traj)
    H = get_cell(args)
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
    ax.set_title("Density profile along z")
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_zprofile.png")
    print(f"z-profile: {nbins} bins -> {prefix}_zprofile.png")
    return 0


# --------------------------------------------------------------------------
# vacf / ir / power
# --------------------------------------------------------------------------
def _read_velocities(args):
    """返回速度帧 (M,N,3)。优先 --vel; 否则用 --traj 位置差分近似。"""
    if getattr(args, "vel", None):
        _, vel, times, _ = read_xyz(args.vel)
        return vel, times
    # 位置差分近似
    _, frames, times, _ = read_xyz(args.traj)
    if times is not None and len(times) > 1:
        dt = float(np.median(np.diff(times)))
    else:
        dt = args.dt if args.dt else 1.0
    vel = np.zeros_like(frames)
    vel[1:-1] = (frames[2:] - frames[:-2]) / (2 * dt)
    vel[0] = vel[1]
    vel[-1] = vel[-2]
    print("NOTE: 无速度文件, 用位置中心差分近似 v≈Δr/Δt (精度有限)。")
    return vel, times


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
    vel, times = _read_velocities(args)
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
    ax.set_title("Velocity autocorrelation function")
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_vacf.png")
    print(f"VACF: {len(t)} points -> {prefix}_vacf.png")
    return 0


def cmd_ir(args):
    vel, times = _read_velocities(args)
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
    ax.set_title("IR / vibrational DOS (FFT of VACF)")
    ax.grid(alpha=0.3)
    save_png(fig, prefix + "_ir.png")
    peak = freq_cm[1 + np.argmax(spec[1:])]
    print(f"IR/VDoS: peak ≈ {peak:.1f} cm^-1 -> {prefix}_ir.png")
    return 0


def cmd_power(args):
    return cmd_ir(args)


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
    r = subprocess.run([binpath, args.cube], capture_output=True, text=True)
    if r.returncode != 0:
        print("bader 运行失败:\n" + r.stderr)
        return 1
    acf = os.path.join(os.path.dirname(args.cube) or ".", "ACF.dat")
    if not os.path.exists(acf):
        print("bader 完成, 但未找到 ACF.dat(检查工作目录)。")
        return 0
    prefix = out_prefix(args)
    rows = []
    for ln in open(acf):
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
    for ln in open(fesdat):
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
    r = subprocess.run(cmd, capture_output=True, text=True)
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
def cmd_travis(args):
    binpath = shutil.which("travis") or args.travis_bin
    # 生成控制文件
    prefix = out_prefix(args)
    ctrl = prefix + ".travis.in"
    with open(ctrl, "w") as f:
        f.write(f"TITLE\n  CP2K postprocess TRAVIS job\nEND\n")
        f.write(f"TIMESTEP\n  {args.dt}\nEND\n")
        f.write(f"COORDINATE_FORMAT\n  XYZ\nEND\n")
        f.write(f"COORDINATE_FILE\n  {args.traj}\nEND\n")
        if args.vel:
            f.write(f"VELOCITY_FILE\n  {args.vel}\nEND\n")
        f.write("OUTPUT\n  " + prefix + "\nEND\n")
        f.write("BEGIN ANALYSIS\n")
        for a in args.analyses:
            f.write("  " + a.upper() + "\n")
        f.write("END\n")
    print(f"TRAVIS 控制文件已生成: {ctrl}")
    if not binpath:
        print("ERROR: 未检测到 travis 可执行文件(https://www.travis-analyzer.de/)。")
        print("  安装后重跑本命令即可自动执行; 控制文件已备好。")
        return 1
    import subprocess
    r = subprocess.run([binpath, ctrl], capture_output=True, text=True)
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
                        help="晶胞: 'a b c' 或 'ax ay az bx by bz cx cy cz' (Å)。缺省尝试从 .out 解析")


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
    add_io(sp)
    sp.set_defaults(func=cmd_msd)

    sp = sub.add_parser("diffusion", help="扩散系数 D (Einstein)")
    sp.add_argument("traj")
    sp.add_argument("--sel", default=None)
    sp.add_argument("--dim", type=int, default=3, choices=[1, 2, 3])
    sp.add_argument("--dt", type=float, default=None)
    sp.add_argument("--fit-lo", type=float, default=0.2)
    sp.add_argument("--fit-hi", type=float, default=0.8)
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
    add_io(sp)
    sp.set_defaults(func=cmd_zprofile)

    sp = sub.add_parser("vacf", help="速度自相关函数")
    sp.add_argument("--vel", default=None, help="速度 xyz(CP2K -vel-1.xyz)")
    sp.add_argument("--traj", default=None, help="位置轨迹(差分近似速度)")
    sp.add_argument("--dt", type=float, default=None)
    add_io(sp)
    sp.set_defaults(func=cmd_vacf)

    sp = sub.add_parser("ir", help="红外/振动态密度(FFT of VACF)")
    sp.add_argument("--vel", default=None)
    sp.add_argument("--traj", default=None)
    sp.add_argument("--dt", type=float, default=None)
    add_io(sp)
    sp.set_defaults(func=cmd_ir)

    sp = sub.add_parser("power", help="功率谱(= ir)")
    sp.add_argument("--vel", default=None)
    sp.add_argument("--traj", default=None)
    sp.add_argument("--dt", type=float, default=None)
    add_io(sp)
    sp.set_defaults(func=cmd_power)

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
    add_io(sp)
    sp.set_defaults(func=cmd_travis)

    return p


def main():
    p = build_parser()
    args = p.parse_args()
    if not getattr(args, "cmd", None):
        p.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
