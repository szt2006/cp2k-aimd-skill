#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""GBK 控制台回归：中文 Windows（代码页 936）下所有入口不许抛 UnicodeEncodeError。

**为什么需要**：`scripts/_console.py` 是一个兼容层，作用是让 CLI 在中文 Windows
的 GBK 控制台下 print `✓ ✗ • ⚠ ✖ ⑪ ↻ Å ² ³` 这类 GBK **无法表示**的字符时不再抛
`UnicodeEncodeError`。但"某个脚本忘了挂兼容层"这件事，**只有真的用 GBK 编码去跑
才会暴露** —— 在 UTF-8 环境里跑一万次都是绿的。

本脚本用 `PYTHONIOENCODING=gbk` 强制子进程的 stdout/stderr 用 GBK（strict），
逐个跑完整入口并断言：

1. 输出里**没有** `UnicodeEncodeError`
2. 输出里**没有** `Traceback`
3. 退出码符合该用例的期望（健壮性基线：`--help`→0、无参数→2、
   缺文件→1 且是**友好中文**而不是 traceback）

用法：
    python _validate_gbk.py            # 全部用例
    python _validate_gbk.py --list     # 只列用例
    python _validate_gbk.py --json
"""
import argparse
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
try:
    import _console  # noqa: F401
except Exception:
    pass

PY = sys.executable
S = os.path.join(HERE, "scripts")
BAD = ("UnicodeEncodeError", "Traceback (most recent call last)")

# 派生失败时的兜底清单（正常路径不用它，见 entry_points()）
FALLBACK_ENTRY_POINTS = [
    "scripts/doctor.py", "scripts/wizard.py", "scripts/guide.py",
    "scripts/recommend.py", "scripts/gen_inp.py",
    "scripts/validate_inp.py", "scripts/parse_output.py",
    "scripts/diagnose.py", "scripts/postprocess.py",
    "_doc_consistency.py", "_validate_all.py",
    "_validate_postprocess.py", "_official_validate.py",
    "_kw_probe.py", "_audit_h_citations.py",
    "_validate_rdf_cn.py", "_verify_case_provenance.py",
    "_validate_real_data.py", "_collect_new_items.py",
]


def entry_points():
    """入口清单**只从 `_doc_consistency.ENTRY_POINTS` 派生**（唯一真源）。

    早先这里另抄了一份硬编码清单，**两份已经漂移**：`ENTRY_POINTS` 有 29 个入口，
    本回归只跑 21 个 —— `extract_pdf.py` / `extract_subtitles.py` /
    `build_mapping.py` / `_gen_cp2k_sections.py` / `_validate_gbk.py` /
    `_inject_test.py` / `_validate_all_suites.py`，以及本轮新增的
    `_audit_videonotes_citations.py`，**全都在覆盖之外**。

    后果是"**静态检查说它挂了 `_console`、运行时却从没在 GBK 下跑过**"这个组合
    是可能的 —— 而 GBK 回归的整个卖点就是"真的在 GBK 下跑一遍"。
    改成派生后，往 `ENTRY_POINTS` 加一条就**自动**进入本回归，不会再漂。
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_dc_for_gbk", os.path.join(HERE, "_doc_consistency.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        rels = list(mod.ENTRY_POINTS)
    except Exception as e:                      # 派生失败要看得见，不能静默变少
        print("  ⚠ 无法从 _doc_consistency.ENTRY_POINTS 派生入口清单"
              "（{}: {}），改用兜底清单".format(type(e).__name__, e))
        rels = list(FALLBACK_ENTRY_POINTS)
    return [r for r in rels if os.path.isfile(os.path.join(HERE, r))]


def cases():
    """(标签, argv, 期望退出码集合, 工作目录)。期望用集合，因为有的用例可有多种合法码。"""
    out = []
    # ---- 每个入口的 --help（基线：exit 0，且会打印含符号的说明）----
    for rel in entry_points():
        if os.path.isfile(os.path.join(HERE, rel)):
            out.append(("{} --help".format(os.path.basename(rel)),
                        [rel, "--help"], {0}, HERE))
    # ---- 无参数（基线：usage + exit 2）----
    for rel in ["scripts/validate_inp.py", "scripts/parse_output.py",
                "scripts/diagnose.py", "scripts/recommend.py"]:
        out.append(("{} (无参数)".format(os.path.basename(rel)),
                    [rel], {2}, HERE))
    # ---- guide：11 个阶段逐个 show ----
    for st in ["define", "build", "decide", "converge", "optimize", "static",
               "dynamics", "react", "postproc", "diagnose", "report"]:
        out.append(("guide show " + st, ["scripts/guide.py", "show", st],
                    {0}, HERE))
    out.append(("guide list", ["scripts/guide.py", "list"], {0}, HERE))
    # ---- recommend：各目标（会打印含 ✓/⚠ 的推荐表）----
    # 注意 `--elements` 是**必需**参数，goal 的合法取值见 argparse 的 choices
    # （energy / geo_opt / cell_opt / md / neb / vib / ts / qmmm）。
    for goal in ["energy", "geo_opt", "cell_opt", "md", "neb", "vib", "ts",
                 "qmmm"]:
        out.append(("recommend --elements Si --goal " + goal,
                    ["scripts/recommend.py", "--elements", "Si",
                     "--goal", goal], {0}, HERE))
    # 金属 + 杂化 + DFT+U（走最多分支的推荐路径）。
    # 色散开关是 `--vdw {auto,yes,no}`（**不是** `--dispersion`，后者是 gen_inp 的）。
    out.append(("recommend 金属+HSE06+U",
                ["scripts/recommend.py", "--elements", "Au", "O", "Cu",
                 "--goal", "geo_opt", "--functional", "HSE06", "--plus-u",
                 "auto", "--smear", "--vdw", "yes"], {0}, HERE))
    # ---- gen_inp：8 类模板 + 进阶开关（符号最多的路径）----
    tmp = os.environ.get("TEMP", ".")
    for ty in ["static", "geo_opt", "cell_opt", "aimd_md", "metadyn", "neb",
               "vib", "qmmm"]:
        out.append(("gen_inp --type " + ty,
                    ["scripts/gen_inp.py", "--type", ty, "--project", "gbk",
                     "-o", os.path.join(tmp, "_gbk_{}.inp".format(ty))],
                    {0, 1}, HERE))
    out.append(("gen_inp HSE06+ADMM+props",
                ["scripts/gen_inp.py", "--type", "geo_opt", "--project", "gbk2",
                 "--elem", "Au", "O", "--functional", "HSE06", "--admm",
                 "--properties", "dos", "pdos", "mulliken",
                 "--dispersion", "-o", os.path.join(tmp, "_gbk_x.inp")],
                {0}, HERE))
    out.append(("gen_inp --walltime",
                ["scripts/gen_inp.py", "--type", "aimd_md", "--project", "gbk3",
                 "--elem", "Cu", "--walltime", "82800",
                 "-o", os.path.join(tmp, "_gbk_w.inp")], {0}, HERE))
    # ---- 缺文件（基线：友好中文 + exit 1，不抛 traceback）----
    out.append(("parse_output 缺文件",
                ["scripts/parse_output.py", "no_such_file.out"], {1}, HERE))
    out.append(("validate_inp 缺文件",
                ["scripts/validate_inp.py", "no_such_file.inp"], {1}, HERE))
    out.append(("diagnose 缺文件",
                ["scripts/diagnose.py", "no_such_file.out"], {1}, HERE))
    out.append(("postprocess 缺文件",
                ["scripts/postprocess.py", "energy", "no_such.ener"], {1}, HERE))
    # ---- 新增工具的正常路径（会打印 ✓ / 表格）----
    out.append(("doctor --quiet", ["scripts/doctor.py", "--quiet"], {0}, HERE))
    out.append(("_doc_consistency --list",
                ["_doc_consistency.py", "--list"], {0}, HERE))
    out.append(("_kw_probe 关键字",
                ["_kw_probe.py", "MOTION/MD/THERMOSTAT/NOSE/TIMECON"],
                {0}, HERE))
    out.append(("_kw_probe --section --json",
                ["_kw_probe.py", "--section", "MOTION/MD/THERMOSTAT/CSVR",
                 "--json"], {0}, HERE))
    out.append(("_audit_h_citations", ["_audit_h_citations.py"], {0}, HERE))
    out.append(("_validate_rdf_cn", ["_validate_rdf_cn.py"], {0}, HERE))
    out.append(("_verify_case_provenance",
                ["_verify_case_provenance.py"], {0}, HERE))
    out.append(("_validate_real_data", ["_validate_real_data.py"], {0}, HERE))
    # ---- H 层 / E 层脚本 ----
    out.append(("extract_tutorials --list",
                ["references/h_tutorials/extract_tutorials.py", "--list"],
                {0, 1, 2}, HERE))
    out.append(("extract_doc --list", ["references/h_tutorials/extract_doc.py",
                                       "--list"], {0, 1, 2}, HERE))
    return out


def main():
    ap = argparse.ArgumentParser(description="GBK 控制台回归")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cs = cases()
    if args.list:
        for label, argv, want, _cwd in cs:
            print("  {:<42} want={}".format(label, sorted(want)))
        print("共 {} 个用例".format(len(cs)))
        return 0

    env = dict(os.environ)
    # 关键：强制子进程输出用 GBK（strict）。没挂 _console 的脚本在这里必炸。
    env["PYTHONIOENCODING"] = "gbk"
    env["PYTHONUTF8"] = "0"

    fails = []
    for label, argv, want, cwd in cs:
        cmd = [PY, os.path.join(HERE, argv[0])] + argv[1:]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               env=env, cwd=cwd, timeout=180)
        except subprocess.TimeoutExpired:
            fails.append((label, "超时"))
            print("  [FAIL] {:<44} 超时".format(label))
            continue
        blob = (r.stdout or "") + (r.stderr or "")
        hit = [b for b in BAD if b in blob]
        if hit:
            fails.append((label, "出现 " + "/".join(hit)))
            print("  [FAIL] {:<44} {}".format(label, "/".join(hit)))
            for ln in blob.splitlines():
                if any(b in ln for b in BAD):
                    print("         " + ln.strip()[:120])
            continue
        if r.returncode not in want:
            fails.append((label, "exit={} 期望 {}".format(r.returncode,
                                                          sorted(want))))
            print("  [FAIL] {:<44} exit={} 期望 {}".format(
                label, r.returncode, sorted(want)))
            continue

    print()
    print("=" * 72)
    print("GBK 控制台回归（PYTHONIOENCODING=gbk，强制用代码页 936 的编码集）")
    print("=" * 72)
    print("  用例 {} 个，失败 {} 个".format(len(cs), len(fails)))
    if fails:
        print()
        for label, why in fails:
            print("  - {:<44} {}".format(label, why))
    print("结论：{}".format("全部通过 ✓ —— 没有脚本在 GBK 下抛异常"
                          if not fails else
                          "{} 个用例失败 ✗".format(len(fails))))
    if args.json:
        print(json.dumps({"total": len(cs), "failed": len(fails),
                          "failures": [{"case": a, "why": b} for a, b in fails]},
                         ensure_ascii=False, indent=2))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
