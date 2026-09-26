import argparse
import os, sys

# --- 控制台编码兼容层（中文 Windows/GBK 下输出不再抛异常）---
# 本脚本在 references/pdf_text/ 下，兼容层在 <repo>/scripts/_console.py。
try:
    _here0 = os.path.dirname(os.path.abspath(__file__))
    _scripts0 = os.path.join(_here0, os.pardir, os.pardir, "scripts")
    for _d in (_here0, _scripts0):
        if _d not in sys.path:
            sys.path.insert(0, _d)
    import _console  # noqa: F401  导入即生效，见 scripts/_console.py
except Exception:
    pass

# --- CLI：**必须放在 import pdfplumber 之前** ---
# `--help` 是仓库统一的健壮性基线（AGENTS.md §6.3：`--help` → exit 0），
# 而 pdfplumber 是可选开发依赖；若放在它后面，没装依赖时连 `--help` 都看不了。
# 本脚本原先完全没有 argparse，`--help` 被当成"没有参数"直接走环境变量检查 → exit 1，
# 是三个 E 层维护脚本里唯一不合基线的一个（由 `_validate_gbk.py` 的 GBK 回归抓到）。
_ap = argparse.ArgumentParser(
    prog="extract_pdf.py",
    description="把 5 份课程讲义 PDF 抽成带 `========== PAGE N ==========` 页码标记的 "
                "L1–L5.txt（E 层原始素材）。属开发/维护脚本，只在需要重新抽取时跑。")
_ap.add_argument("--src", default=None,
                 help="课程 PDF 所在目录；不给则读环境变量 CP2K_COURSE_SRC")
_ap.add_argument("--out", default=None,
                 help="输出目录（默认：本脚本所在目录 references/pdf_text/）")
_ARGS = _ap.parse_args()

try:
    import pdfplumber
except ImportError:
    sys.exit("缺少依赖：pdfplumber（仅在重新抽取课程 PDF 时需要，属开发依赖）\n"
             "安装方式：\n"
             "  pip install -r requirements-dev.txt\n"
             "  pip install pdfplumber")

# 课程 PDF 所在目录：命令行优先，其次环境变量（避免写死本机绝对路径）
SRC = _ARGS.src or os.environ.get("CP2K_COURSE_SRC")
if not SRC:
    sys.exit("请先设置环境变量 CP2K_COURSE_SRC 指向课程 PDF 所在目录（或加 --src <目录>），例如：\n"
             "  set CP2K_COURSE_SRC=D:\\path\\to\\讲义和课程视频字幕")
# 输出目录：默认固定为脚本自身所在目录（pdf_text/），可移植到任意机器
OUT = os.path.abspath(_ARGS.out) if _ARGS.out else os.path.dirname(os.path.abspath(__file__))

pdfs = [
    "庚子计算-AIMD与CP2K讲义-1 - 副本.pdf",
    "庚子计算-AIMD与CP2K讲义-2 - 副本.pdf",
    "庚子计算-AIMD与CP2K讲义-3 - 副本.pdf",
    "庚子计算-AIMD与CP2K讲义-4 - 副本.pdf",
    "庚子计算-AIMD与CP2K讲义-5 - 副本.pdf",
]

os.makedirs(OUT, exist_ok=True)

for p in pdfs:
    path = os.path.join(SRC, p)
    if not os.path.exists(path):
        print("MISSING:", path)
        continue
    # short name: strip prefix + "- 副本"
    base = os.path.splitext(p)[0]
    base = base.replace("庚子计算-AIMD与CP2K讲义-", "L").replace(" - 副本", "")
    outname = base + ".txt"
    out = os.path.join(OUT, outname)
    with pdfplumber.open(path) as pdf:
        npages = len(pdf.pages)
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"# SOURCE: {p}\n# PAGES: {npages}\n\n")
            for i, page in enumerate(pdf.pages):
                txt = page.extract_text() or ""
                f.write(f"\n\n========== PAGE {i+1} ==========\n\n")
                f.write(txt)
                f.write("\n")
    print(f"WROTE {out}  pages={npages}")
