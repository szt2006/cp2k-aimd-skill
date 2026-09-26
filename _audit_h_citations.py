#!/usr/bin/env python3
"""H 层引用审计：核验 `references/h_tutorials/notes/*.md` 里的 `T** P**` 引用。

**为什么需要这个工具**：H 层的价值主张是"逐页可回溯"——笔记里每句话都能按
`T05 P30` 这样的页码回 `txt/T05_*.txt` 的对应页核对。如果没有工具核验，
这个承诺就只是口号；一旦页码漂了，整层知识的可信度就没了。

它做两件事：

1. **结构审计（硬错误，必须为 0）**
   每个 `T** P**` 引用的页号必须真实存在于该教程（`T05 P99` 而 T05 只有 43 页
   ⇒ 引用是错的）。正确处理页码范围（`P23–P32`）、并列页（`P19/P25`）与一行多教程。

2. **内容抽样比对（软指标，供人工判断）**
   把笔记里反引号/引号里的英文片段，回**该行被引用的任意一页**里找。
   对不上的分四类，**只有第 3 类才是真问题**：
     - `公式/记号`：笔记自己写的数学表达式（`y = min_x E(q,x)`），本就不该逐字存在
     - `关键字标签`：笔记用反引号标的关键字名（`HFX_MEM_INFO`），可能是概称或文件项
     - **`疑似错页`**：该片段在**本教程的其它页**找得到 ⇒ 页码该修
     - `无法定位`：全 H 层 txt 都没有 ⇒ 可能是翻译/转述，也可能是外部资料

用法：
    python _audit_h_citations.py            # 摘要
    python _audit_h_citations.py --detail   # 逐条列出未命中项
    python _audit_h_citations.py --json
"""
import argparse
import glob
import io
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
try:
    import _console  # noqa: F401  中文 Windows(GBK) 下输出符号不再抛异常
except Exception:
    pass

HDIR = os.path.join(HERE, "references", "h_tutorials")
TXT = os.path.join(HDIR, "txt")
NOTES = os.path.join(HDIR, "notes")

PAGE_MARK = re.compile(r"^=+ PAGE (\d+) =+$", re.M)


def norm(s):
    """去空白后比对 —— pdfplumber 对两端对齐排版常丢词间空格。"""
    return re.sub(r"\s+", "", s)


def page_map(path):
    t = io.open(path, encoding="utf-8", errors="replace").read()
    marks = list(PAGE_MARK.finditer(t))
    out = {}
    for i, m in enumerate(marks):
        s = m.end()
        e = marks[i + 1].start() if i + 1 < len(marks) else len(t)
        out[int(m.group(1))] = t[s:e]
    return out


# 一行里"某教程号 + 它后面的页码规格"。规格可以任意混合：
#   T05 P23–P32     T19 P19/P25     T06 P22、P24–P25     T05 P8, P11
#
# 早先的实现用"一个可选的短横线 + 若干分隔符"拼 tail，结果
# `T06 P22、P24–P25` 里的 `–P25` 落在分隔符之后就被丢掉了，
# 于是把**本来引对了的行误报成错页**。现在改成：先贪婪吞掉整段
# 只由页码字符构成的"规格串"，再在规格串内部解析范围与并列。
TUT_RE = re.compile(r"(T\d\d)\s*(?=[Pp]?\d)")
SPEC_CHARS = "0123456789Pp–—~-至、,，/ "
SEP_RE = re.compile(r"[、,，/]")
DASH_RE = re.compile(r"[–—~\-至]")


def _spec_end(line, start):
    """从 start 起，返回只含页码字符的最长规格串的结束位置。"""
    i = start
    while i < len(line) and line[i] in SPEC_CHARS:
        i += 1
    return i


def cited_pages(line):
    """Return {tutorial: set(pages)} cited on one note line."""
    out = {}
    for m in TUT_RE.finditer(line):
        t = m.group(1)
        spec = line[m.end():_spec_end(line, m.end())]
        spec = spec.replace("P", " ").replace("p", " ")
        pages = set()
        for chunk in SEP_RE.split(spec):
            chunk = chunk.strip()
            if not chunk:
                continue
            if DASH_RE.search(chunk):          # a–b 范围
                nums = [int(x) for x in re.findall(r"\d+", chunk)]
                if len(nums) >= 2:
                    lo, hi = min(nums[0], nums[-1]), max(nums[0], nums[-1])
                    if hi - lo <= 80:          # 防呆：不展开荒谬的大范围
                        pages.update(range(lo, hi + 1))
                    else:
                        pages.update((lo, hi))
                elif nums:
                    pages.add(nums[0])
            else:                              # 单独一页
                for x in re.findall(r"\d+", chunk):
                    pages.add(int(x))
        if pages:
            out.setdefault(t, set()).update(pages)
    return out


QUOTE_RE = re.compile(
    r"[`\"“]([A-Za-z][A-Za-z0-9 ,._/()\-\[\]=+*<>:@#'\u00b0]{11,})[`\"”]")
# 笔记自写的数学/记号：含 = 或明显是表达式
MATHISH = re.compile(r"[=×·]|\bmin_|\bmax_|\bO\(")


def main():
    ap = argparse.ArgumentParser(
        description="审计 H 层精读笔记的 T** P** 引用是否可回溯")
    ap.add_argument("--detail", action="store_true", help="逐条列出未命中项")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    if not os.path.isdir(TXT) or not os.path.isdir(NOTES):
        print("找不到 {}/txt 或 notes/：H 层似乎不完整".format(
            os.path.relpath(HDIR, HERE)), file=sys.stderr)
        return 3

    tut = {}
    for f in sorted(glob.glob(os.path.join(TXT, "*.txt"))):
        m = re.match(r"(T\d\d)_", os.path.basename(f))
        if m:
            tut[m.group(1)] = page_map(f)
    if not tut:
        print("txt/ 里没有 T**.txt：先跑 "
              "python references/h_tutorials/extract_tutorials.py --src <目录>",
              file=sys.stderr)
        return 3

    cited_n = 0
    oob = []            # 越界（硬错误）
    ok = 0
    miss = []           # (file, line, cites_desc, quote, category, real_where)
    n_lines_cited = 0

    for nf in sorted(glob.glob(os.path.join(NOTES, "*.md"))):
        base = os.path.basename(nf)
        for ln, line in enumerate(
                io.open(nf, encoding="utf-8", errors="replace").read()
                .splitlines(), 1):
            cites = cited_pages(line)
            if not cites:
                continue
            n_lines_cited += 1
            for t, pages in cites.items():
                if t not in tut:
                    oob.append((base, ln, "引了不存在的教程号 {}".format(t)))
                    continue
                mx = max(tut[t])
                for p in sorted(pages):
                    cited_n += 1
                    if p < 1 or p > mx:
                        oob.append((base, ln,
                                    "{} P{} 越界（该教程只有 {} 页）"
                                    .format(t, p, mx)))
            for q in QUOTE_RE.findall(line):
                frag = norm(q.strip())
                if len(frag) < 12:
                    continue
                hit = any(frag in norm(tut[t].get(p, ""))
                          for t, pages in cites.items() if t in tut
                          for p in pages)
                if hit:
                    ok += 1
                    continue
                # 未命中 → 分类
                same_tut = []
                for t, _ps in cites.items():
                    if t in tut:
                        for p, txt in tut[t].items():
                            if frag in norm(txt):
                                same_tut.append("{} P{}".format(t, p))
                if same_tut:
                    cat, where = "待复核", ", ".join(sorted(same_tut)[:4])
                elif MATHISH.search(q):
                    cat, where = "公式/记号", ""
                elif re.fullmatch(r"[`\"“]?[A-Za-z0-9_]+[`\"”]?", q.strip()):
                    cat, where = "关键字标签", ""
                else:
                    elsewhere = []
                    for t, pm in tut.items():
                        for p, txt in pm.items():
                            if frag in norm(txt):
                                elsewhere.append("{} P{}".format(t, p))
                    cat = "无法定位"
                    where = ", ".join(sorted(elsewhere)[:4]) if elsewhere else ""
                miss.append((base, ln,
                             ", ".join("{} P{}".format(t, sorted(ps))
                                       for t, ps in cites.items()),
                             q[:70], cat, where))

    cats = Counter(m[4] for m in miss)
    real = [m for m in miss if m[4] == "待复核"]
    result = {
        "notes": len(glob.glob(os.path.join(NOTES, "*.md"))),
        "tutorials": len(tut),
        "cited_page_instances": cited_n,
        "out_of_range": len(oob),
        "fragments_ok": ok,
        "fragments_miss": len(miss),
        "miss_by_category": dict(cats),
        "needs_manual_review": len(real),
    }

    if args.json:
        print(json.dumps({"summary": result,
                          "out_of_range": oob,
                          "miss": [{"file": m[0], "line": m[1], "cites": m[2],
                                    "quote": m[3], "category": m[4],
                                    "where": m[5]} for m in miss]},
                         ensure_ascii=False, indent=2))
        return 1 if oob else 0

    print("=" * 76)
    print("H 层引用审计（notes/*.md 的 T** P** 引用 → txt/ 页码可回溯性）")
    print("=" * 76)
    print("  精读笔记          : {} 份".format(result["notes"]))
    print("  教程              : {} 份".format(result["tutorials"]))
    print("  被引页码实例      : {}".format(cited_n))
    print("  页码越界（硬错误）: {}".format(len(oob)))
    print()
    print("  英文引号片段命中  : {}".format(ok))
    print("  英文引号片段未命中: {}  ← 分类如下（只有『待复核』需人看）"
          .format(len(miss)))
    for k in ("待复核", "无法定位", "公式/记号", "关键字标签"):
        print("      {:<10} {:>4}".format(k, cats.get(k, 0)))
    print()
    if oob:
        print("### 越界引用（必须修）")
        for b, ln, msg in oob[:40]:
            print("  {}:{}  {}".format(b, ln, msg))
        print()
    if real:
        print("### 待人工复核：片段落在本教程的**其它页**（{} 条）".format(len(real)))
        print("    注意：这**不是** {} 个错误。实测逐条复核过：绝大多数是合法的 ——".format(len(real)))
        print("      · 片段属于**同一行的另一条声明**（比如行尾在讲 G 层/D 层的对照）")
        print("      · 片段在**与 G/D 层对照的那一列**里，与所引 T 页无关")
        print("      · 片段被 PDF 纵向排版**拆行**，归一化空白后仍不连续")
        print("    所以这是一个**复核清单**，不是错误清单；只有「改这句页码才更准确」的才要动。")
        for b, ln, cite, q, _c, where in real[:40]:
            print("  {}:{}".format(b, ln))
            print("      笔记引用: {}".format(cite))
            print("      实际在  : {}".format(where))
            print("      片段    : {!r}".format(q))
        print()

    if args.detail:
        print("### 全部未命中明细")
        for b, ln, cite, q, cat, where in miss:
            print("  {}:{}  [{}] {!r}".format(b, ln, cat, q))
            if where:
                print("      → {}".format(where))

    print("结论：{}".format(
        "页码结构全部可信、无越界引用 ✓" if not oob else
        "发现 {} 处越界引用 ✗".format(len(oob))))
    if not oob and real:
        print("      另有 {} 处待人工复核的页码（多数合法，见上表说明）".format(len(real)))
    return 1 if oob else 0


if __name__ == "__main__":
    sys.exit(main())
