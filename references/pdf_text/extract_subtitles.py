#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把课程视频字幕原样落入 E 层（`S*.txt`），并输出溯源清单。

为什么需要这个脚本
------------------
`course_learned.md` 与 `course_notes.md` 都声称"6 份字幕逐行处理"，但**字幕原文
此前并不在仓库里**，导致：
  1. 所有"字幕第 N 行"的引用**无法核对**；
  2. 各 `learn_L*.md` 头部写的是原作者本机绝对路径
     （`D:\\石大\\化学软件\\...`），该路径在任何其他机器上都不存在；
  3. 一个实际后果：`course_learned.md` 曾因搜错文件而判定"BSSE 全文零命中"，
     而 BSSE 其实在 `2.txt`/`3.txt` 里出现 19 次。

命名与行号约定
--------------
  * `S1.1.txt` `S1.2.txt` `S2.txt` `S3.txt` `S4.txt` `S5.txt`
    —— 与原始文件名 **1:1**（`S` = 字幕），便于回溯到课程资料目录。
  * 文件内容 **逐字原样复制，不添加任何头/尾注释**，
    因此"S 文件的第 N 行"== "原字幕的第 N 行"，
    `learn_L*.md` 与综合稿里的行号引用**永久有效**。
  * 换行统一为 LF（不改动行数）；溯源信息（原始文件名/行数/sha256）
    另存到本文件运行时打印的清单里，由人工写入 `README.md` 与对应表。

用法
----
    set CP2K_COURSE_SRC=D:\\cp2k-aimd\\study\\讲义和课程视频字幕
    python extract_subtitles.py
或
    python extract_subtitles.py --src "D:\\cp2k-aimd\\study\\讲义和课程视频字幕"
"""
import argparse
import hashlib
import os
import sys

# --- 控制台编码兼容层（中文 Windows/GBK 下输出不再抛异常）---
# 本脚本在 references/pdf_text/ 下，兼容层在 <repo>/scripts/_console.py。
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

SUBTITLES = ["1.1.txt", "1.2.txt", "2.txt", "3.txt", "4.txt", "5.txt"]


def out_name(name):
    """1.1.txt -> S1.1.txt ；2.txt -> S2.txt"""
    return "S" + name


def main():
    ap = argparse.ArgumentParser(description="把课程字幕原样落入 E 层 S*.txt")
    ap.add_argument("--src", default=os.environ.get("CP2K_COURSE_SRC"),
                    help="课程资料目录（含讲义 PDF 与字幕 txt）；"
                         "也可用环境变量 CP2K_COURSE_SRC")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)),
                    help="输出目录，默认为本脚本所在目录（references/pdf_text/）")
    args = ap.parse_args()

    if not args.src:
        sys.exit("请用 --src 指定课程资料目录，或设置环境变量 CP2K_COURSE_SRC。")
    if not os.path.isdir(args.src):
        sys.exit(f"目录不存在：{args.src}")

    os.makedirs(args.out, exist_ok=True)
    rows = []
    for name in SUBTITLES:
        src = os.path.join(args.src, name)
        if not os.path.isfile(src):
            print(f"MISSING: {src}")
            continue
        with open(src, "rb") as fh:
            raw = fh.read()
        # 统一换行（不改行数）：CRLF -> LF
        data = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        dst = os.path.join(args.out, out_name(name))
        with open(dst, "wb") as fh:
            fh.write(data)
        text = data.decode("utf-8")
        nlines = text.count("\n") + (0 if text.endswith("\n") else 1)
        digest = hashlib.sha256(data).hexdigest()
        rows.append((name, out_name(name), nlines, len(data), digest))
        print(f"WROTE {dst}  lines={nlines}  bytes={len(data)}")

    if rows:
        print()
        print("=== 溯源清单（写入 README.md / 对应表的出处） ===")
        print(f"{'原始文件':<12}{'仓库内':<12}{'行数':>7}{'字节':>9}  sha256(前16)")
        for name, out, nlines, nbytes, digest in rows:
            print(f"{name:<12}{out:<12}{nlines:>7}{nbytes:>9}  {digest[:16]}")
        total = sum(r[2] for r in rows)
        print(f"{'合计':<12}{'':<12}{total:>7}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
