import os, sys

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber not installed")

# 课程 PDF 所在目录：用环境变量覆盖，避免写死本机绝对路径
SRC = os.environ.get("CP2K_COURSE_SRC")
if not SRC:
    sys.exit("请先设置环境变量 CP2K_COURSE_SRC 指向课程 PDF 所在目录，例如：\n"
             "  set CP2K_COURSE_SRC=D:\\path\\to\\讲义和课程视频字幕")
# 输出目录：固定为脚本自身所在目录（pdf_text/），可移植到任意机器
OUT = os.path.dirname(os.path.abspath(__file__))

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
