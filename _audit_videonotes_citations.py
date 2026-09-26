#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""E 层引用审计（**两类引用都查**：`videonotes/…` 与 `S*.txt:行号` / `L*.txt`）。

> 📌 **文件名是历史遗留**：本脚本最初只为 `videonotes/`（第二轮视频精读笔记）而写，
> 后来把 `S*.txt:<行号>` 这类**字幕引用**也纳进来了（那才是库里最多的引用形式，
> 实测 **501 条**）。文件名没改是为了不动九处登记点；**以本说明为准**。

**为什么需要**：
1. 本轮把 6 份视频精读笔记（9803 行）的成果并进 A/B/C/F，新增大量形如
   ``videonotes/cp2k-4-…-精读笔记 L1802 [1:12:31]`` 的引用。
   H 层有 `_audit_h_citations.py` 守 `T** P**`，**这一层此前没有任何工具在守** ——
   引用一旦写错行号，读者回原文核对就会落空，而"可溯源"正是这一层的全部价值。
2. B/C 层的引用主要写作 `S1.1.txt:2073`、`S4.txt:2447–2448` 这种**字幕行号**，
   以及 `L1 P66`、`L3.txt:2325` 这种**讲义页码/行号**。这类引用同样会越界，
   而且**库里有 501 条**，比 `videonotes/` 引用还多。故一并纳入。

它查的**硬错误（必须为 0）**：

* `videonotes/…` 部分
  - **笔记名要能唯一解析**到 `references/pdf_text/videonotes/` 下的 6 份之一；
    缩写（`cp2k-4-…-精读笔记`、`cp2k-1-1-…`）按 `…`/`...` 之前的**前缀唯一匹配**。
    解析不出来（拼错、或前缀不唯一）⇒ 读者根本找不到原文。
  - **行号必须在文件范围内**（`L99999` 而该笔记只有 1802 行 ⇒ 引用是错的）；
    支持区间 `L814–816` / `L814-816`，两端都要在范围内。
* `S*.txt:<行号>` 部分
  - 文件名必须是 `references/pdf_text/` 下真实存在的字幕/讲义文件；
  - 行号必须在**该文件的实际行数**范围内；支持 `:2073` 与 `:2447–2448` 两种写法。

**软指标（供人工判断）**：
  - `videonotes/` 引用行附近（±`WINDOW` 行）**应当能找到该类引用附带的时间戳**
    `[mm:ss–mm:ss]`。找不到只说明"时间戳不在这一行附近"，多数仍合法
    （时间戳常标在整段的末尾），故只列为**待复核**，不计失败。

⚠️ **在文档里举例说明"坏写法"时，行号请写成 `L###` 占位**。
本脚本的正则只认 `L` 后面跟**数字**，所以 `videonotes/… L###` 天然被跳过；
若例子写成真数字（`videonotes/… L565`），就会被当成真引用而误报。
这条约定由 `_inject_test.py` 的「`L###` 占位符不算引用」一条钉住，不要改回去。

用法：
    python _audit_videonotes_citations.py             # 摘要
    python _audit_videonotes_citations.py --detail    # 逐条列出待复核项
    python _audit_videonotes_citations.py --json

退出码：0 = 无硬错误；1 = 有硬错误（笔记名解析不了 / 行号越界 / 字幕文件不存在）。
"""
import argparse
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
try:
    import _console  # noqa: F401  中文 Windows(GBK) 下输出符号不再抛异常
except Exception:
    pass

VNOTE_DIR = os.path.join(HERE, "references", "pdf_text", "videonotes")
WINDOW = 60          # 软指标：时间戳应落在引用行 ±WINDOW 行内

# 字幕/讲义引用：`S1.1.txt:2073`、`S4.txt:2447–2448`、`L3.txt:2325`
SREF = re.compile(r"\b(?P<f>[SL]\d(?:\.\d)?\.txt)\s*[:：]\s*(?P<a>\d+)"
                  r"(?:\s*[–—\-~]\s*(?P<b>\d+))?")

# `videonotes/<笔记名> L<行号>[–L<行号>]`，笔记名可含中文/连字符/省略号
CITE = re.compile(
    r"videonotes/(?P<name>[^\s`|()\[\]]+?)"
    r"\s*L(?P<a>\d+)(?:\s*[–—\-~]\s*L?(?P<b>\d+))?")
TS = re.compile(r"\[(\d{1,3}):([0-5]\d)(?:\s*[–—\-~]\s*(\d{1,3}):([0-5]\d))?\]")
# 扫描范围：除 videonotes 自身（那是被引原文）以外的所有 md
SKIP_PARTS = (os.sep + "videonotes" + os.sep,)


def load_notes():
    """返回 [(目录名, 路径, 行数)]。"""
    out = []
    for d in sorted(glob.glob(os.path.join(VNOTE_DIR, "*"))):
        if not os.path.isdir(d):
            continue
        mds = glob.glob(os.path.join(d, "*.md"))
        if not mds:
            continue
        p = mds[0]
        n = len(io.open(p, encoding="utf-8", errors="replace").read().splitlines())
        out.append((os.path.basename(d), p, n))
    return out


def resolve(name, notes):
    """把引用里的笔记名解析到唯一一份笔记。

    先精确匹配目录名/去后缀名；再按 `…`/`...` 之前的前缀做**唯一**前缀匹配。
    返回 (note, None) / (None, 原因)。
    """
    key = name.strip().rstrip("`")
    key = re.split(r"…|\.\.\.", key)[0].strip().rstrip("-—")
    if not key:
        return None, "笔记名为空（只有省略号）"
    exact = [n for n in notes if n[0] == name.strip()]
    if len(exact) == 1:
        return exact[0], None
    hits = [n for n in notes
            if n[0].startswith(key) or n[0].split("-精读笔记")[0].startswith(key)]
    if len(hits) == 1:
        return hits[0], None
    if not hits:
        return None, "找不到以此开头的笔记"
    return None, "前缀不唯一：{}".format("、".join(h[0] for h in hits))


def scan(notes):
    rows = []
    for p in sorted(glob.glob(os.path.join(HERE, "**", "*.md"), recursive=True)):
        if any(s in p for s in SKIP_PARTS):
            continue
        rel = os.path.relpath(p, HERE)
        lines = io.open(p, encoding="utf-8", errors="replace").read().splitlines()
        for i, ln in enumerate(lines):
            for m in CITE.finditer(ln):
                note, err = resolve(m.group("name"), notes)
                a = int(m.group("a"))
                b = int(m.group("b")) if m.group("b") else None
                # 时间戳：先看本行，再看 ±WINDOW 行
                ts_line, ts_txt = None, None
                for j in [i] + [k for w in range(1, WINDOW + 1)
                                for k in (i - w, i + w) if 0 <= k < len(lines)]:
                    t = TS.search(lines[j])
                    if t:
                        ts_line, ts_txt = j, t.group(0)
                        break
                rows.append({"file": rel, "line": i + 1, "note": m.group("name"),
                             "note_dir": note[0] if note else None,
                             "note_lines": note[2] if note else None,
                             "a": a, "b": b, "resolve_err": err,
                             "raw": m.group(0),
                             "ts": ts_txt, "ts_delta": (i - ts_line) if ts_line is not None else None})
    return rows


def subtitle_lengths():
    """`references/pdf_text/` 下各 `S*/L*.txt` 的实际行数（真值来自文件本身）。"""
    out = {}
    for p in glob.glob(os.path.join(HERE, "references", "pdf_text", "*.txt")):
        out[os.path.basename(p)] = len(
            io.open(p, encoding="utf-8", errors="replace").read().splitlines())
    return out


def scan_subtitle_refs():
    """扫 `S*.txt:<行号>` / `L*.txt:<行号>` 引用。

    B/C 层的引用主要就是这种形式（实测 **501 条**），比 `videonotes/` 引用还多；
    它们同样会越界。返回 (rows, lengths)。
    """
    lens = subtitle_lengths()
    rows = []
    for p in sorted(glob.glob(os.path.join(HERE, "**", "*.md"), recursive=True)):
        if any(s in p for s in SKIP_PARTS):
            continue
        rel = os.path.relpath(p, HERE)
        for i, ln in enumerate(
                io.open(p, encoding="utf-8", errors="replace").read().splitlines(), 1):
            for m in SREF.finditer(ln):
                f = m.group("f")
                rows.append({"file": rel, "line": i, "target": f,
                             "a": int(m.group("a")),
                             "b": int(m.group("b")) if m.group("b") else None,
                             "target_lines": lens.get(f),
                             "raw": m.group(0)})
    return rows, lens


def main():
    ap = argparse.ArgumentParser(
        description="E 层引用审计：videonotes/… 引用 + S*.txt:<行号> 字幕引用")
    ap.add_argument("--detail", action="store_true", help="逐条列出问题/待复核项")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    notes = load_notes()
    if not notes:
        print("找不到 videonotes 笔记目录: {}".format(VNOTE_DIR))
        return 1

    rows = scan(notes)
    unresolved = [r for r in rows if r["resolve_err"]]
    oob = [r for r in rows if not r["resolve_err"]
           and (r["a"] < 1 or r["a"] > r["note_lines"]
                or (r["b"] is not None
                    and (r["b"] < 1 or r["b"] > r["note_lines"])))]
    no_ts = [r for r in rows if not r["resolve_err"] and r["ts"] is None]

    # ---- 第二类：`S*.txt:<行号>` / `L*.txt:<行号>` 字幕/讲义引用 ----
    srows, slens = scan_subtitle_refs()
    s_missing = [r for r in srows if r["target_lines"] is None]
    s_oob = [r for r in srows if r["target_lines"] is not None
             and (r["a"] < 1 or r["a"] > r["target_lines"]
                  or (r["b"] is not None
                      and (r["b"] < 1 or r["b"] > r["target_lines"])))]
    hard = len(unresolved) + len(oob) + len(s_missing) + len(s_oob)

    if args.json:
        print(json.dumps({"total": len(rows), "notes": [
            {"dir": d, "lines": n} for d, _p, n in notes],
            "unresolved": unresolved, "out_of_range": oob,
            "no_timestamp_nearby": len(no_ts),
            "subtitle_refs": {"total": len(srows),
                              "file_missing": s_missing,
                              "out_of_range": s_oob,
                              "lengths": slens}}, ensure_ascii=False, indent=2))
        return 1 if hard else 0

    print("=" * 74)
    print("E 层引用审计（videonotes/… 引用 + S*.txt:<行号> 字幕引用）")
    print("=" * 74)
    print("笔记 {} 份 / 共 {} 行".format(
        len(notes), sum(n for _d, _p, n in notes)))
    for d, _p, n in notes:
        print("  {:>5} 行  {}".format(n, d))
    print()
    print("① videonotes 引用 {} 处（分布在 {} 个文件）".format(
        len(rows), len({r["file"] for r in rows})))
    by_file = {}
    for r in rows:
        by_file.setdefault(r["file"], []).append(r)
    for f, rs in sorted(by_file.items(), key=lambda kv: -len(kv[1])):
        print("  {:>4} 处  {}".format(len(rs), f))
    print("② 字幕/讲义引用（`S*.txt:行号`）{} 处（分布在 {} 个文件；"
          "对照 {} 份 S*/L*.txt 的实际行数）".format(
              len(srows), len({r["file"] for r in srows}), len(slens)))

    if unresolved:
        print("\n✗ 笔记名解析不了（{} 处）—— 读者无法回原文：".format(len(unresolved)))
        for r in unresolved:
            print("  {}:{}  `{}`  ⇒ {}".format(r["file"], r["line"], r["raw"],
                                               r["resolve_err"]))
    if oob:
        print("\n✗ 行号越界（{} 处）—— 引用是错的：".format(len(oob)))
        for r in oob:
            print("  {}:{}  `{}`  ⇒ 该笔记只有 {} 行".format(
                r["file"], r["line"], r["raw"], r["note_lines"]))
    if s_missing:
        print("\n✗ 字幕文件不存在（{} 处）—— 引用指不到任何文件：".format(len(s_missing)))
        for r in s_missing:
            print("  {}:{}  `{}`  ⇒ references/pdf_text/ 下没有这个文件".format(
                r["file"], r["line"], r["raw"]))
    if s_oob:
        print("\n✗ 字幕行号越界（{} 处）—— 引用是错的：".format(len(s_oob)))
        for r in s_oob:
            print("  {}:{}  `{}`  ⇒ {} 只有 {} 行".format(
                r["file"], r["line"], r["raw"], r["target"], r["target_lines"]))
    if args.detail and no_ts:
        print("\n· 时间戳不在引用行 ±{} 行内（{} 处，多数合法，供人工判断）：".format(
            WINDOW, len(no_ts)))
        for r in no_ts[:60]:
            print("  {}:{}  `{}`".format(r["file"], r["line"], r["raw"]))
        if len(no_ts) > 60:
            print("  …（另有 {} 处，用 --json 取全量）".format(len(no_ts) - 60))

    print()
    print("-" * 74)
    print("硬错误 ①：笔记名不可解析 {} / 行号越界 {}".format(len(unresolved), len(oob)))
    print("硬错误 ②：字幕文件不存在 {} / 字幕行号越界 {}".format(
        len(s_missing), len(s_oob)))
    print("软指标：时间戳不在 ±{} 行内 {} 处（{}，供人工判断）".format(
        WINDOW, len(no_ts),
        "多数合法——时间戳常标在整段末尾" if no_ts else "全部可定位"))
    print("结论：{}".format("引用结构全部可信、无越界 ✓"
                          if not hard
                          else "有 {} 处硬错误 ✗".format(hard)))
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
