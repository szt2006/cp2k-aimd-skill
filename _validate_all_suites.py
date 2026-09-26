#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""一键跑全部验证（"三项校验"已扩到 8 项，这个脚本把它们串起来）。

**为什么要把它们串起来**：本 skill 的验证资产已经长到 8 个 harness，散着跑
容易漏。更要紧的是它们**层级不同** —— 有的必须每次改完都绿（回归），有的是
**证明护栏本身有效**（注入测试），有的在缺外部数据时**应当明确 SKIP 而不是
假装通过**。混在一起报"全绿"会掩盖后两种。

因此本脚本分组呈现，并在最后明确列出"哪些是真跑过、哪些是 SKIP"。

用法：
    python _validate_all_suites.py            # 全部
    python _validate_all_suites.py --quick    # 跳过耗时的（GBK / 注入 / 真实数据）
    python _validate_all_suites.py --json
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
try:
    import _console  # noqa: F401
except Exception:
    pass

PY = sys.executable

# (分组, 标签, 脚本, 期望退出码, 期望在输出里出现的关键行, 是否耗时)
SUITES = [
    ("回归（改完必绿）", "文档口径一致性", "_doc_consistency.py", 0,
     "OK：文档口径全部一致。", False),
    ("回归（改完必绿）", "全量输入校验（含仓库现有 .inp）", "_validate_all.py", 0,
     "0 errors, 0 warnings", True),
    ("回归（改完必绿）", "后处理端到端（含 RDF 归一化）", "_validate_postprocess.py", 0,
     "ALL POSTPROCESS SUBCOMMANDS PASSED", True),
    # 端到端跑通 ≠ 数值对。这一条把新子命令逐条与**解析解**比对（72 条断言，
    # 每条配反向对照），比端到端更严也更慢；两者互补，不要只留一个。
    ("回归（改完必绿）", "后处理解析解自测（72 条断言）", "_validate_postprocess_analytic.py", 0,
     "全部与解析解一致", True),
    ("回归（改完必绿）", "环境自检", "scripts/doctor.py", 0,
     "核心功能可用", False),
    # 知识库的"默认值断言"对官方 XML 逐条核（此前只有 48 条被人工核过）。
    # 它守的是**知识本身**，不是代码 —— 所以独立成一条，别混进代码回归里。
    # 退出码契约：0 = 无不符（未解析不算失败，会如实报数）。
    ("知识层专属护栏", "默认值断言 vs 官方 XML（不符必须 0）", "_audit_claims.py", 0,
     "结论：无不符 ✓", False),
    ("H 层专属护栏", "引用可回溯性（页码越界必须 0）", "_audit_h_citations.py", 0,
     "页码结构全部可信", True),
    ("E 层专属护栏", "引用可回溯性（videonotes 笔记名/行号 + S*.txt:行号）",
     "_audit_videonotes_citations.py", 0, "无越界", True),
    ("H 层专属护栏", "cases 溯源核验", "_verify_case_provenance.py", 0,
     "清单可信、副本确为原文", True),
    ("数值正确性", "RDF 配位数 = 直接计数", "_validate_rdf_cn.py", 0,
     "归一化正确", True),
    ("真实数据（缺源则 SKIP）", "真实 .out / 轨迹回归", "_validate_real_data.py", 0,
     None, True),
    ("编码健壮性", "GBK 控制台回归", "_validate_gbk.py", 0,
     "全部通过", True),
    ("护栏自证", "注入测试（护栏会不会红）", "_inject_test.py", 0,
     "全部护栏都会红", True),
]


def main():
    ap = argparse.ArgumentParser(description="一键跑全部验证")
    ap.add_argument("--quick", action="store_true", help="跳过耗时项")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = []
    group = None
    for grp, label, script, want_rc, want_line, slow in SUITES:
        if args.quick and slow:
            continue
        if grp != group:
            print()
            print("=" * 76)
            print("  " + grp)
            print("=" * 76)
            group = grp
        path = os.path.join(HERE, script)
        if not os.path.isfile(path):
            print("  [缺失] {:<44} {}".format(label, script))
            rows.append({"group": grp, "label": label, "script": script,
                         "status": "missing"})
            continue
        t0 = time.time()
        r = subprocess.run([PY, path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=HERE,
                           timeout=1800)
        dt = time.time() - t0
        blob = (r.stdout or "") + (r.stderr or "")
        skipped = "**SKIP**" in blob or "SKIP (" in blob or "跳过" in blob \
            and "不是通过" in blob
        line_ok = (want_line is None) or (want_line in blob)
        ok = (r.returncode == want_rc) and line_ok
        status = ("skip" if (skipped and r.returncode == 0 and ok)
                  else ("pass" if ok else "fail"))
        print("  [{:<4}] {:<44} exit={} {:.1f}s".format(
            status.upper(), label, r.returncode, dt))
        if want_line:
            got = want_line in blob
            print("         {:<52} {}".format(
                "关键行 " + want_line[:44], "✓" if got else "**缺**"))
        if status == "fail":
            tail = [l for l in blob.splitlines() if l.strip()][-6:]
            for l in tail:
                print("         | " + l[:110])
        rows.append({"group": grp, "label": label, "script": script,
                     "status": status, "exit": r.returncode,
                     "seconds": round(dt, 1)})

    n_pass = sum(1 for r in rows if r["status"] == "pass")
    n_skip = sum(1 for r in rows if r["status"] == "skip")
    n_fail = sum(1 for r in rows if r["status"] == "fail")
    n_missing = sum(1 for r in rows if r["status"] == "missing")
    print()
    print("=" * 76)
    print("  共 {} 项：通过 {} / SKIP {} / 失败 {} / 缺失 {}".format(
        len(rows), n_pass, n_skip, n_fail, n_missing))
    if n_skip:
        print("  ⚠ SKIP **不是通过** —— 上面标 SKIP 的是缺外部数据（如真实 .out"
              "不在本机），")
        print("    它们没有被验证过，别当成绿的。")
    print("结论：{}".format("全部通过 ✓" if not (n_fail or n_missing)
                          else "有 {} 项失败/缺失 ✗".format(n_fail + n_missing)))
    if args.json:
        print(json.dumps({"summary": {"total": len(rows), "pass": n_pass,
                                      "skip": n_skip, "fail": n_fail,
                                      "missing": n_missing},
                          "rows": rows}, ensure_ascii=False, indent=2))
    return 1 if (n_fail or n_missing) else 0


if __name__ == "__main__":
    sys.exit(main())
