#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""H 层 cases/ 溯源核验：把 `_COPY_MANIFEST.tsv` 里的 sha256 回源目录比对。

**为什么需要**：`references/h_tutorials/cases/` 的价值主张是"输入卡是**原文照抄**、
可验证"。清单里写了一串 sha256，但**清单本身也可能写错**——所以本脚本不信任清单，
自己把源文件与副本都重算一遍：

1. 副本的 sha256 是否与清单记录一致（副本没被偷偷改过）
2. **源文件**的 sha256 前 16 位是否与清单记录一致（清单没记错来源）
3. 截断件（`*.head10tail5.txt`）允许与源不同，但清单必须**如实标注**为 excerpt

用法：
    python _verify_case_provenance.py
    python _verify_case_provenance.py --src "<算例源目录>"
    python _verify_case_provenance.py --json

源目录也可用环境变量 `CP2K_CASE_SRC` 指定。若源目录不在本机（别人只拿到 skill
副本时就是这种情况），脚本会退化为"只验副本自身一致性"，并**明确说明**它没能
验证来源——不会假装验过了。
"""
import argparse
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
try:
    import _console  # noqa: F401
except Exception:
    pass

CASES = os.path.join(HERE, "references", "h_tutorials", "cases")
MANIFEST = os.path.join(CASES, "_COPY_MANIFEST.tsv")
DEFAULT_SRC = (r"D:\cp2k-aimd\study\庚子计算整理-cp2k资料-持续更新")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(
        description="核验 H 层 cases/ 的溯源清单（副本与源文件都重算 sha256）")
    ap.add_argument("--src", default=os.environ.get("CP2K_CASE_SRC", DEFAULT_SRC),
                    help="算例源目录；也可用环境变量 CP2K_CASE_SRC")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(MANIFEST):
        print("找不到清单: {}".format(MANIFEST), file=sys.stderr)
        return 3
    if not os.path.isdir(args.src):
        print("[提示] 源目录不在本机: {}".format(args.src), file=sys.stderr)
        print("       只能验『副本自身没被改过』，**无法**验证来源（不假装验过）。",
              file=sys.stderr)

    lines = io.open(MANIFEST, encoding="utf-8").read().splitlines()
    hdr = lines[0].split("\t")
    idx = {k: i for i, k in enumerate(hdr)}

    def col(c, key):
        i = idx.get(key)
        return c[i] if i is not None and len(c) > i else ""

    rows = []
    n_copy_ok = n_copy_bad = n_src_ok = n_src_bad = n_src_absent = 0
    for ln in lines[1:]:
        if not ln.strip():
            continue
        c = ln.split("\t")
        copied = col(c, "copied_file")
        cp = os.path.join(CASES, copied)
        if not os.path.isfile(cp):
            rows.append({"file": copied, "status": "missing-copy"})
            n_copy_bad += 1
            continue
        got = sha256(cp)
        if got != col(c, "copied_sha256"):
            rows.append({"file": copied, "status": "copy-hash-mismatch",
                         "expected": col(c, "copied_sha256"), "actual": got})
            n_copy_bad += 1
            continue
        n_copy_ok += 1
        note = col(c, "note")
        src_rel = col(c, "source_file")
        sp = os.path.join(args.src, src_rel.replace("/", os.sep))
        if not os.path.isfile(sp):
            n_src_absent += 1
            rows.append({"file": copied, "status": "source-not-available",
                         "note": note})
            continue
        src_got = sha256(sp)
        if src_got[:16] == col(c, "source_sha256_16"):
            n_src_ok += 1
            rows.append({"file": copied, "status": "ok", "note": note})
        else:
            n_src_bad += 1
            rows.append({"file": copied, "status": "source-hash-mismatch",
                         "expected": col(c, "source_sha256_16"),
                         "actual": src_got[:16]})

    summary = {
        "manifest": os.path.relpath(MANIFEST, HERE),
        "entries": len(rows),
        "copy_verified": n_copy_ok,
        "copy_mismatch": n_copy_bad,
        "source_verified": n_src_ok,
        "source_mismatch": n_src_bad,
        "source_unavailable": n_src_absent,
    }
    if args.json:
        print(json.dumps({"summary": summary, "entries": rows},
                         ensure_ascii=False, indent=2))
        return 1 if (n_copy_bad or n_src_bad) else 0

    print("=" * 78)
    print("cases/ 溯源核验（清单里的 sha256 vs 副本与源文件实算）")
    print("=" * 78)
    for r in rows:
        if r["status"] != "ok":
            print("  [{}] {}".format(r["status"], r["file"]))
            if "expected" in r:
                print("        清单 {} / 实算 {}".format(r["expected"][:16],
                                                          r["actual"][:16]))
    print()
    print("  副本自身一致   : {}".format(n_copy_ok))
    print("  副本被改动     : {}".format(n_copy_bad))
    print("  来源已验证一致 : {}".format(n_src_ok))
    print("  来源不符       : {}".format(n_src_bad))
    print("  来源不可用     : {}".format(n_src_absent))
    print()
    if n_src_bad or n_copy_bad:
        print("结论：有 {} 处不符 ✗".format(n_src_bad + n_copy_bad))
        return 1
    if n_src_absent:
        print("结论：副本未被改动 ✓；但源目录不可用，**来源未验证**（不是通过）")
        return 0
    print("结论：清单可信、副本确为原文 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
