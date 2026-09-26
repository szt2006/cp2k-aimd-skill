#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「逐页/逐行学习稿」里标【新】的条目抽出来，并核对它们**是否真的落进了消费层**。

为什么需要它
------------
`references/MAINTENANCE.md` 的 Phase 3 曾经失守：`learn_L*.md` 做得很好，
但 `course_learned.md` 只吸收了其中一部分，文件末尾却写"所有【新】标记项已落入本库、
6 份字幕全部逐行处理"。复核发现 `IRC`、`相空间`、`OSZICAR`、`xdat2vdat.pl`、
`Anderson 热浴` 等在消费层**零命中**——**声明是假的，而且当时无人能证伪**。

所以现在要求 Phase 3 的完成判据可机械核验。本脚本就是那个核验工具：
从学习稿抽【新】条目 → 对消费层做**线索检索** → 给出"疑似已落 / 疑似未落"的分诊。

⚠️ **这是分诊工具，不是证明**：`【新】` 条目是一句中文论述，不可能在消费层里
逐字出现。脚本只提取若干**线索词**（元素/程序名/关键词/数字），
命中任一即算"疑似已落"。所以：
  * 报"疑似未落"的**必须人工过一遍**再决定是补写还是显式标注"暂不收录 + 理由"；
  * 报"疑似已落"的也可能只是**提到了词**而没写进实质内容，同样建议抽查。
**结论请写成"已落 X 条 / 暂缓 Y 条（见清单）"，不要写"全部已收录"。**

用法
----
    # 1) 只看统计（学习稿 + 精读报告各多少条【新】）
    python _collect_new_items.py --stats

    # 2) 生成清单 + 覆盖核对报告
    python _collect_new_items.py --verify

    # 3) 指定精读报告目录（默认读环境变量 CP2K_EXTRACT_DIR）
    python _collect_new_items.py --verify --reports "D:\\path\\to\\_extract"

零依赖，只用标准库。
"""
import argparse
import os
import re
import sys

try:
    import os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    for _d in (_here, _os.path.join(_here, "scripts")):
        if _d not in _sys.path:
            _sys.path.insert(0, _d)
    import _console  # noqa: F401  导入即生效，见 scripts/_console.py
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
PDFTEXT = os.path.join(HERE, "references", "pdf_text")

# 【新】的几种写法都要认
NEW_PAT = re.compile(r"【新[^】]*】")
SEC_PAT = re.compile(r"^(#{2,3})\s+(.*)$")

# 消费层：{相对路径: 层名}
CONSUMERS = {
    "references/course_learned.md": "B 课程综合",
    "references/course_notes.md": "C 速查",
    "references/decide.md": "A 决策库",
    "references/playbook.md": "F 实战手册",
    "references/postprocess.md": "后处理",
    "references/course_survey.md": "C 资料梳理",
}

# 抽线索词时忽略的泛用词（避免"命中"变成噪音）
STOP = set("""的 了 是 在 与 和 或 及 等 为 把 被 对 从 到 中 上 下 内 外 一 二 三 四 五
与 也 都 就 会 能 可 要 需 应 不 无 有 这 那 其 该 此 我 你 他 它
条 个 项 点 面 时 后 前 里 处 说 明 注 见 详 参 例 如 若 则 即 又 更 最
the and for with from that this are was were has have not you can will
""".split())


def scan_file(path):
    """返回 [(行号, 所属章节, 条目全文)]。

    注意：`learn_L*.md` 的【新】**大量挂在章节标题上**
    （如 `## 12. 水盒子建模（P38–P41）【新】`），所以标题行也要当条目收，
    否则会严重漏计（实测：只收正文会把 learn 的 50+ 条算成 4 条）。
    """
    out, section = [], ""
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return out
    with fh:
        for i, raw in enumerate(fh, 1):
            ln = raw.rstrip("\n")
            m = SEC_PAT.match(ln.strip())
            if m:
                section = m.group(2).strip()
                # 标题本身带【新】→ 也是一条
                if NEW_PAT.search(section):
                    out.append((i, section, section))
                continue
            if NEW_PAT.search(ln):
                out.append((i, section, ln.strip()))
    return out


def clues(text):
    """抽出可用于在消费层里检索的线索词。"""
    t = NEW_PAT.sub(" ", text)
    got = []
    # 1) 反引号里的代码/关键词 —— 最可靠的线索
    got += re.findall(r"`([^`]{2,40})`", t)
    # 2) 数字带单位 / 纯数字（如 1E-6、10 Å、0.0005）
    got += re.findall(r"\b\d+(?:\.\d+)?(?:[eE][-+]?\d+)?\s*(?:Å|fs|ps|eV|Ry|K|%|kcal/mol)?\b", t)
    # 3) 拉丁词（程序名/关键字：CP2K、VASPKIT、EPS_SCF、MDALGO…）
    got += re.findall(r"\b[A-Za-z][A-Za-z0-9_\-\.]{2,30}\b", t)
    # 清理
    seen, res = set(), []
    for c in got:
        c = c.strip()
        if len(c) < 2 or c.lower() in STOP or c in seen:
            continue
        # 排除"报告内部条目号"（B12 / A8 / C2 / S4 …）——它们是笔记的编号，
        # 不是知识内容，拿去找必然落空，会造成假阴性。
        if re.fullmatch(r"[A-Za-z]\d{1,2}", c):
            continue
        # 排除形如 S1_1 / learn_L5 的文件名指代
        if re.fullmatch(r"(?i)(s\d(_\d)?|l\d|learn_l\d)", c):
            continue
        seen.add(c)
        res.append(c)
    return res[:12]


def main():
    ap = argparse.ArgumentParser(description="抽【新】条目并核对是否落进消费层")
    ap.add_argument("--reports", default=os.environ.get("CP2K_EXTRACT_DIR", ""),
                    help="精读报告目录（含 S*.md）；默认读环境变量 CP2K_EXTRACT_DIR")
    ap.add_argument("--stats", action="store_true", help="只打印统计")
    ap.add_argument("--verify", action="store_true", help="生成清单 + 覆盖核对")
    ap.add_argument("--out", default=os.path.join(HERE, "_new_items_report.md"))
    args = ap.parse_args()

    # 收集来源：E 层学习稿 + （可选）精读报告
    sources = []
    for n in range(1, 6):
        p = os.path.join(PDFTEXT, f"learn_L{n}.md")
        if os.path.isfile(p):
            sources.append(p)
    if args.reports and os.path.isdir(args.reports):
        for fn in sorted(os.listdir(args.reports)):
            if re.match(r"^S\d(_\d)?\.md$", fn):
                sources.append(os.path.join(args.reports, fn))
    elif args.reports:
        sys.stderr.write(f"（提示）精读报告目录不存在，跳过：{args.reports}\n")

    items = []
    per_source = {}
    for p in sources:
        got = scan_file(p)
        per_source[os.path.basename(p)] = len(got)
        for lineno, sec, text in got:
            items.append((os.path.basename(p), lineno, sec, text))

    if args.stats or not args.verify:
        print("=== 【新】条目统计 ===")
        zero = []
        for k, v in per_source.items():
            print(f"  {k:<14} {v:>4}")
            if v == 0:
                zero.append(k)
        print(f"  {'合计':<14} {len(items):>4}")
        if zero:
            print(f"\n注：{'、'.join(zero)} 计 0 条，通常是**该稿没用 `【新】` 标记**"
                  f"（改用「仅字幕有/PDF 没有」之类的小节来组织），不是没有新增内容——"
                  f"这类稿子请人工看它的\"缺口/仅字幕有\"小节。")
        if not args.verify:
            print("\n加 --verify 生成清单与覆盖核对报告。")
        return 0

    # 读消费层全文
    cons_text = {}
    for rel in CONSUMERS:
        p = os.path.join(HERE, rel)
        if os.path.isfile(p):
            with open(p, encoding="utf-8", errors="replace") as fh:
                cons_text[rel] = fh.read()

    L = ["# 【新】条目 → 消费层 覆盖核对（分诊报告）\n",
         "> 由 `_collect_new_items.py --verify` 生成。**这是分诊，不是证明**：",
         "> 【新】条目是中文论述，不可能在消费层逐字出现；脚本只做**线索词检索**。",
         "> 「疑似未落」必须人工过一遍再决定补写还是标注「暂不收录 + 理由」。",
         "> **结论请写成「已落 X 条 / 暂缓 Y 条」，不要写「全部已收录」。**\n",
         "> ⚠️ 线索词只取**反引号代码、数字、拉丁词**；纯中文且不含数字/代码的条目",
         "> 抽不出线索，会被单列为「需人工」——**那不是「未落」，是脚本判不了**。\n"]
    hit_n = miss_n = manual_n = 0
    misses = []
    for src, lineno, sec, text in items:
        cl = clues(text)
        if not cl:
            # 纯中文、无数字/代码 → 无法自动判，单列（避免误报成"未落"）
            manual_n += 1
            L.append(f"- [需人工·无线索词] `{src}:{lineno}` {text[:160]}  \n"
                     f"  → 脚本抽不出拉丁词/数字/代码，请在消费层按**语义**人工确认")
            continue
        where = [CONSUMERS[rel] for rel, body in cons_text.items()
                 if any(c in body for c in cl)]
        if where:
            hit_n += 1
            tag = "疑似已落"
            detail = "、".join(sorted(set(where)))
        else:
            miss_n += 1
            tag = "**疑似未落**"
            detail = "（线索词：" + "、".join(cl[:6]) + "）"
            misses.append((src, lineno, sec, text))
        L.append(f"- [{tag}] `{src}:{lineno}` {text[:160]}  \n  → {detail}")

    summary = (f"\n---\n\n## 汇总\n\n"
               f"- 【新】条目总数：**{len(items)}**\n"
               f"- 疑似已落：**{hit_n}**\n"
               f"- **疑似未落：{miss_n}**（需人工确认）\n"
               f"- 需人工（抽不出线索词，脚本判不了）：**{manual_n}**\n"
               f"- 消费层扫描范围：{', '.join(sorted(CONSUMERS.values()))}\n\n"
               f"> 判定口径：命中任一**线索词**（反引号代码 / 数字 / 拉丁词）即算「疑似已落」。\n"
               f"> 消费层若用**不同措辞**表达了同一件事，会被算成「疑似未落」——这是已知的假阴性来源，\n"
               f"> 所以「疑似未落」是**待查清单**，不是结论。\n")
    L.append(summary)

    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"WROTE {args.out}")
    print(f"【新】条目 {len(items)} 条：疑似已落 {hit_n}，疑似未落 {miss_n}，"
          f"需人工（无线索词）{manual_n}")
    if misses:
        print("\n疑似未落（前 20 条，完整清单见报告）：")
        for src, lineno, sec, text in misses[:20]:
            print(f"  · {src}:{lineno}  {text[:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
