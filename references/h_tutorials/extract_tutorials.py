#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「庚子计算整理-cp2k资料」里的官方教程 PDF 抽成 H 层的可溯源分页文本。

背景与定位
----------
`references/h_tutorials/` 是 skill 的 **H 层（官方教程与实战算例）**，与既有各层的边界：
  * **G 层**（`references/official/`）= 官网/手册的**参考条目**采集。它只把这些教程 PDF
    当作**外部资源标题**登记（如 `10_features_resources.md` 里的课程清单），
    **没有收录其教材内容**；
  * **E 层**（`references/pdf_text/`）= **庚子计算课程**的讲义与字幕（第三方培训）；
  * **H 层**（本目录）= **官方 workshop / howto / 夏季学校教材**的一手教学内容
    ＋ 随资料附带的**真实生产算例工程**（含可运行的 .inp/.inc 与真实 .out/轨迹）。

去重
----
源目录里 27 个 PDF 中有 **3 对完全重复**（同一份 PDF 既在顶层、又在
`CP2K官方workshop课件练习资料/` 里），本脚本按 sha256 去重，只抽 **24 份唯一内容**，
并在清单里记下重复关系，避免以后重复劳动。

用法
----
    set CP2K_TUTORIAL_SRC=D:\\cp2k-aimd\\study\\庚子计算整理-cp2k资料-持续更新
    python extract_tutorials.py
或
    python extract_tutorials.py --src "<目录>" [--out <输出目录>] [--list]
"""
import argparse
import hashlib
import os
import sys

# --- 控制台编码兼容层（中文 Windows/GBK 下输出不再抛异常）---
try:
    import os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _scripts = _os.path.join(_here, _os.pardir, _os.pardir, "scripts")
    for _d in (_here, _scripts):
        if _d not in _sys.path:
            _sys.path.insert(0, _d)
    import _console  # noqa: F401  导入即生效，见 scripts/_console.py
except Exception:
    pass

# 稳定的短名映射：源文件名关键片段 → (编号, 短名, 主题)
# 同一个 (编号, 短名) 可以有多条 pattern —— 那是**同一份内容的不同文件名（别名）**。
# 去重时脚本按"路径最短者优先"取正本，所以别名多数情况下只会出现在清单的
# "同内容副本"备注里，不会各占一个编号。
# 顺序即清单顺序（按主题分组：GPW/AIMD 理论 → 并行与输入 → howto → 练习 → 专题 → 入门）
FILTERS = [
    # ---- 官方 workshop 教材 ----
    ("hutter-gpw", "T01", "gpw_hutter", "GPW 方法（Hutter，官方 workshop）"),
    ("Gaussian and Plane Waves Method", "T01", "gpw_hutter",
     "GPW 方法（Hutter，官方 workshop）"),
    ("Ab initio Molecular Dynamics - Juerg Hutter", "T02", "aimd_hutter_ws",
     "从头算分子动力学（Hutter，官方 workshop）"),
    ("hutter-bomd.pdf", "T03", "bomd_hutter", "BOMD 讲义（Hutter）"),
    ("cp2k_moving_atoms", "T04", "moving_atoms", "MD 中原子如何运动（cp2k_moving_atoms）"),
    ("Hybrid Functionals, ADMM", "T05", "hybrid_admm_watkins", "杂化泛函与 ADMM（Watkins）"),
    ("Parallelization, Automatization", "T06", "parallel_input_mueller",
     # 文件名里的 "Parallelization" 是**误导**：PDF 标题页（T06 P1）是
     # "CP2K: Automation, Scripting, Testing"，全篇 42 页**没有** MPI/OpenMP/
     # GROUP_PARTITION 的并行层次内容。此处按 PDF 实际标题写，免得读者被
     # 文件名带偏；并行那部分知识在 G 层与 T08/T19。
     "自动化、脚本化与测试（Mueller；文件名里的 Parallelization 有误导，见 README §3）"),
    # ---- 输入与运行 ----
    ("cp2k_basics", "T07", "cp2k_basics", "CP2K 输入基础（Input Basics）"),
    ("CP2K Input Basics", "T07", "cp2k_basics", "CP2K 输入基础（Input Basics）"),
    ("running_cp2k_calculations2018", "T08", "running2018",
     "Running CP2K calculations 2018"),
    ("cp2k-3.pdf", "T09", "cp2k3_input", "CP2K 输入文件（cp2k-3）"),
    # ---- howto 系列 ----
    ("howto_static_calculation", "T10", "howto_static", "HOWTO：单点静态计算"),
    ("howto_geometry_optimisation", "T11", "howto_geo_opt", "HOWTO：几何优化"),
    ("howto_converging_cutoff", "T12", "howto_cutoff", "HOWTO：截断能收敛测试"),
    # ---- 夏季学校 / workshop 练习 ----
    ("exercises_2016_summer_school_aimd", "T13", "ex2016_aimd", "2016 夏校练习：AIMD"),
    ("exercises_2016_summer_school_gga", "T14", "ex2016_gga",
     "2016 夏校练习：表面 OPT + AIMD（GGA）"),
    ("exercises_2016_summer_school_hfx", "T15", "ex2016_hfx", "2016 夏校练习：杂化泛函 HFX"),
    ("events_2018_summer_school_scf_setup", "T16", "ex2018_scf_setup",
     "2018 夏校：SCF 设置（对角化 vs OT）"),
    ("exercises_2020_uzh_acpc2_ex03", "T17", "ex2020_uzh_neb", "2020 UZH 练习 ex03：NEB"),
    ("官方练习汇总", "T18", "exercises_all", "官方练习汇总（Running CP2K calculations – Exercises）"),
    ("Running CP2K calculations-Exercises", "T18", "exercises_all",
     "官方练习汇总（Running CP2K calculations – Exercises）"),
    # ---- 专题 ----
    ("iannuzzi_cp2k-tutorial-zurich2017", "T19", "iannuzzi_zurich2017",
     "CP2K 教程 Zurich 2017（GPW 与 GAPW，Iannuzzi）"),
    ("ling_basis_pseudo", "T20", "ling_basis_pseudo", "基组与赝势（Ling）"),
    ("Basic Usage of QMMM in CP2K", "T21", "qmmm_basic", "CP2K 中 QM/MM 的基本用法"),
    ("CP2K Quantum Mechanics  Molecular Mechanics 2D Embedding",
     "T22", "qmmm_2d_embedding", "QM/MM 2D 嵌入与应用"),
    ("QMMM approaches in ab initio molecular dynamics", "T23", "qmmm_aimd_approaches",
     "AIMD 中的 QM/MM 方法"),
    # ---- 入门 ----
    ("CP2K使用入门", "T24", "cp2k_intro", "CP2K 使用入门（强烈推荐）"),
]


def clean(txt):
    """去掉 pdfplumber 偶发的 NUL 字节。

    少数 PDF（T04 / T05 / T19 / T23）里的某些字形**没有 ToUnicode 映射**，
    pdfplumber 只能把它们抽成 ``\\x00``，使 .txt 被工具当成二进制文件
    （读不了、grep 也不友好）。这里把 NUL 换成普通空格，**不改动任何可见字符**
    （不折叠空格，以免破坏 pdfplumber 用空格做的缩进布局）。

    ⚠️ **NUL 不是"空格"** —— 本层笔记已逐字符核对（`notes/02_aimd_bomd.md` §7
    第 6 条、`notes/01_gpw_gapw.md` §7 第 1/2 条），实测这些位置原本是
    **数学字体的符号**，按字体分四类：

    * ``CMMI8``  → 希腊字母（如 **π**，`E_cutoff = π²/(2h²)` 里的 π）
    * ``CMSS10`` → **Φ**
    * ``CMSY8``  → **减号**（科学计数法上标里最多，`10⁻⁰⁸` 的 −）
    * 另有 **`ff` 连字** 一类

    ⇒ 换成空格后这些符号的位置会**空一格**，读的时候按上下文还原。
    之所以不换成 U+2212 或 π，是因为**同一个 NUL 在不同页可能是不同符号**，
    凭空补一个具体字符等于**发明原文**；H 层的约定是原文只读、歧义写进笔记。
    """
    return txt.replace("\x00", " ")


def slug_of(name):
    for frag, num, slug, topic in FILTERS:
        if frag in name:
            return num, slug, topic
    return None, None, None


def main():
    ap = argparse.ArgumentParser(description="抽取官方教程 PDF 到 H 层")
    ap.add_argument("--src", default=os.environ.get("CP2K_TUTORIAL_SRC"),
                    help="教程资料目录；也可用环境变量 CP2K_TUTORIAL_SRC")
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "txt"),
        help="输出目录，默认 references/h_tutorials/txt/")
    ap.add_argument("--list", action="store_true", help="只列出清单，不抽取")
    args = ap.parse_args()

    if not args.src or not os.path.isdir(args.src):
        sys.exit("请用 --src 指定教程资料目录，或设置环境变量 CP2K_TUTORIAL_SRC。")

    try:
        import pdfplumber
    except ImportError:
        sys.exit("缺少 pdfplumber：pip install -r requirements-dev.txt")

    # 1) 收集所有 PDF，按 sha256 去重
    pdfs = []
    for dp, dns, fns in os.walk(args.src):
        for fn in fns:
            if fn.lower().endswith(".pdf"):
                pdfs.append(os.path.join(dp, fn))
    pdfs.sort()
    by_hash = {}
    for p in pdfs:
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        by_hash.setdefault(h, []).append(p)

    uniq = []
    for h, paths in by_hash.items():
        paths.sort(key=len)          # 顶层（路径短）的排前面，作为"正本"
        uniq.append((paths[0], paths[1:]))

    # 2) 按 FILTERS 顺序编号
    def order(p):
        num, _, _ = slug_of(os.path.basename(p))
        return (num or "T99", p)
    uniq.sort(key=lambda t: order(t[0]))

    rows = []
    missing = []
    for main_path, dups in uniq:
        base = os.path.basename(main_path)
        num, slug, topic = slug_of(base)
        if num is None:
            missing.append(base)
            continue
        rows.append((num, slug, topic, main_path, dups))

    if args.list:
        print(f"唯一 PDF {len(rows)} 份（共扫描 {len(pdfs)} 个文件，去重 "
              f"{len(pdfs) - len(rows)} 个）")
        for num, slug, topic, main_path, dups in rows:
            mark = f"  ← 另有 {len(dups)} 份同内容副本" if dups else ""
            print(f"  {num} {slug:<22} {topic}{mark}")
        if missing:
            print("\n⚠️ 未在 FILTERS 中登记的文件（需补映射）：")
            for m in missing:
                print("   -", m)
        return 0

    os.makedirs(args.out, exist_ok=True)
    manifest = []
    for num, slug, topic, main_path, dups in rows:
        outfile = os.path.join(args.out, f"{num}_{slug}.txt")
        with pdfplumber.open(main_path) as pdf:
            npages = len(pdf.pages)
            with open(outfile, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(f"# SOURCE: {os.path.basename(main_path)}\n")
                fh.write(f"# PAGES: {npages}\n")
                if dups:
                    fh.write("# DUPLICATES: " +
                             "; ".join(os.path.basename(d) for d in dups) + "\n")
                fh.write(f"# TOPIC: {topic}\n\n")
                for i, page in enumerate(pdf.pages):
                    txt = clean(page.extract_text() or "")
                    fh.write(f"\n\n========== PAGE {i+1} ==========\n\n")
                    fh.write(txt)
                    fh.write("\n")
        size = os.path.getsize(outfile)
        manifest.append((num, slug, topic, os.path.basename(main_path), npages, size))
        print(f"WROTE {num}_{slug}.txt  pages={npages}  {size} bytes")

    print()
    print("=== H 层教程溯源清单 ===")
    print(f"{'编号':<6}{'短名':<24}{'页数':>5}{'字节':>9}  原始文件")
    for num, slug, topic, src, npages, size in manifest:
        print(f"{num:<6}{slug:<24}{npages:>5}{size:>9}  {src}")
    print(f"\n合计 {len(manifest)} 份，{sum(m[4] for m in manifest)} 页")
    if missing:
        print("\n⚠️ 未登记映射的文件（已跳过，请补进 FILTERS）：")
        for m in missing:
            print("   -", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
