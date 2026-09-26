#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doctor.py —— 一键环境自检（新手第一步跑这个）

它回答一个问题：**"我这台机器上，这个 skill 能不能用？缺什么？"**

检查项（全部只读，不改你的环境）：
  1. Python 版本（>= 3.8）
  2. 仓库完整性（7 个 CLI + 6 个校验 harness + 8 类模板 + G 层 27 文件 + H 层 24 份教程）
  3. 可选依赖（numpy / matplotlib → 只有后处理出图需要）
  4. 开发依赖（cp2k-input-tools / pint / lxml → 只有权威校验需要）
  5. 外部二进制（cp2k / bader / travis / graph → 按需，缺了不影响核心功能）
  6. 三项校验能否运行（只报告可行性，不实际跑）

设计原则：
  - **零依赖**（纯标准库），任何 Python 3.8+ 都能跑；
  - **只报告，不修改**——缺什么就告诉你确切该敲哪条命令；
  - **不吓唬人**：核心 6 个工具零依赖，缺 numpy 也不影响用主流程。

用法：
    python scripts/doctor.py            # 人类可读报告
    python scripts/doctor.py --json     # 机器可读（给 agent 用）
    python scripts/doctor.py --quiet    # 只输出问题（CI 用；有问题才非零退出）

退出码：0 = 核心功能可用；1 = 核心功能有问题；3 = 环境问题（脚本缺失等）。
"""

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys

# --- 控制台编码兼容层（中文 Windows/GBK 下输出 ✓ ⑪ Å 等符号不再抛异常）---
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
ROOT = os.path.dirname(HERE)

MIN_PY = (3, 8)

# 核心 CLI（零依赖，必须齐全）
CORE_CLI = [
    "guide.py", "recommend.py", "gen_inp.py",
    "validate_inp.py", "parse_output.py", "diagnose.py",
    # 力-能量交叉验证（三个物理不变量）；同样零第三方依赖
    "verify_forces.py",
]
# 后处理（需 numpy + matplotlib）
PLOT_CLI = ["postprocess.py"]
# 校验 harness
HARNESS = [
    "_doc_consistency.py", "_validate_postprocess.py",
    "_validate_all.py", "_official_validate.py",
    # 维护审计工具：抽【新】条目 + 核对是否落进消费层
    "_collect_new_items.py",
    # 关键字溯源探针：查官方 cp2k_input.xml 里某 SECTION/KEYWORD 的类型/默认值/单位
    "_kw_probe.py",
    # H 层引用审计：核验精读笔记的 T** P** 页码能否回 txt/ 的对应页对上
    "_audit_h_citations.py",
    # RDF 归一化的解析型验证：配位数 = 直接计数（多帧！单帧抓不到重复归一化）
    "_validate_rdf_cn.py",
    # H 层 cases/ 溯源核验：清单 sha256 vs 副本与源文件重算
    "_verify_case_provenance.py",
    # 真实数据回归（真实 .out / 2535 帧轨迹；源目录不可用时如实 SKIP）
    "_validate_real_data.py",
    # GBK 控制台回归（强制 GBK 编码跑 70 个用例，抓"忘挂 _console 兼容层"）
    "_validate_gbk.py",
    # 注入测试：故意造错证明各护栏会红（防"假绿"）
    "_inject_test.py",
    # 一键跑全部验证（8 个 harness 分组呈现，并区分 PASS / SKIP）
    "_validate_all_suites.py",
    # 段名全量表生成器（结果落在 scripts/_cp2k_sections.py）
    "_gen_cp2k_sections.py",
]
# 由生成器产出的纯数据模块：缺了它，validate_inp.py 的段名判定会退回 156 个
# 手工条目（覆盖率 12%），把 &MULLIKEN 这类官方段误报成 typo。故单列检查。
DATA_MODULES = ["_cp2k_sections.py"]
# H 层（官方教程）自带的抽取脚本。抽出来的 txt/ 已在仓库里，缺脚本不影响使用，
# 但缺了就没法从源 PDF 重新生成/核对，所以单列一项检查。
H_LAYER = [
    os.path.join("references", "h_tutorials", "extract_tutorials.py"),
    os.path.join("references", "h_tutorials", "extract_doc.py"),
    os.path.join("references", "h_tutorials", "README.md"),
]
# 8 类模板
TEMPLATES = [
    "static.inp", "geo_opt.inp", "cell_opt.inp", "aimd_md.inp",
    "metadyn.inp", "neb.inp", "vib.inp", "qmmm.inp",
]


def _check(label, ok, detail="", fix="", required=True):
    """构造一条检查结果。"""
    return {
        "label": label,
        "ok": bool(ok),
        "detail": detail,
        "fix": fix,
        "required": required,
    }


def check_python():
    v = sys.version_info
    ok = (v.major, v.minor) >= MIN_PY
    ver = f"{v.major}.{v.minor}.{v.micro}"
    return _check(
        "Python 版本", ok, f"当前 {ver}（要求 >= {MIN_PY[0]}.{MIN_PY[1]}）",
        fix="" if ok else f"请安装 Python {MIN_PY[0]}.{MIN_PY[1]} 或更高版本：https://www.python.org/downloads/",
    )


def check_repo():
    out = []
    missing_core = [f for f in CORE_CLI if not os.path.isfile(os.path.join(HERE, f))]
    out.append(_check(
        "核心 CLI（6 个，零依赖）",
        not missing_core,
        f"找到 {len(CORE_CLI) - len(missing_core)}/{len(CORE_CLI)}",
        fix=f"缺少 {', '.join(missing_core)}；请重新完整下载仓库（勿只复制部分文件）" if missing_core else "",
    ))

    # 控制台兼容层：中文 Windows（代码页 936/GBK）下所有 CLI 的依赖。
    # 缺了它，doctor/recommend/guide/diagnose 会在 print ✓ ✗ • ⚠ ✖ ⑪ ↻ 时抛
    # UnicodeEncodeError 并打 traceback（v2.7.0 实测缺陷）。
    console_py = os.path.join(HERE, "_console.py")
    has_console = os.path.isfile(console_py)
    out.append(_check(
        "控制台兼容层（中文 Windows 必需）",
        has_console,
        "找到 scripts/_console.py" if has_console else "缺失",
        fix="" if has_console else
        "缺少 scripts/_console.py：中文 Windows(GBK) 下 CLI 会抛 UnicodeEncodeError；"
        "请重新完整下载仓库",
    ))

    missing_plot = [f for f in PLOT_CLI if not os.path.isfile(os.path.join(HERE, f))]
    out.append(_check(
        "后处理 CLI（需 numpy+matplotlib）",
        not missing_plot,
        f"找到 {len(PLOT_CLI) - len(missing_plot)}/{len(PLOT_CLI)}",
        fix=f"缺少 {', '.join(missing_plot)}" if missing_plot else "",
    ))

    missing_h = [f for f in HARNESS if not os.path.isfile(os.path.join(ROOT, f))]
    out.append(_check(
        f"校验 harness（{len(HARNESS)} 个）",
        not missing_h,
        f"找到 {len(HARNESS) - len(missing_h)}/{len(HARNESS)}",
        fix=f"缺少 {', '.join(missing_h)}" if missing_h else "",
        required=False,
    ))

    tdir = os.path.join(ROOT, "references", "templates")
    found_t = [f for f in TEMPLATES if os.path.isfile(os.path.join(tdir, f))] \
        if os.path.isdir(tdir) else []
    out.append(_check(
        "输入模板（8 类）", len(found_t) == len(TEMPLATES),
        f"找到 {len(found_t)}/{len(TEMPLATES)}",
        fix=f"缺少 {', '.join(set(TEMPLATES) - set(found_t))}" if len(found_t) != len(TEMPLATES) else "",
    ))

    missing_dm = [f for f in DATA_MODULES
                  if not os.path.isfile(os.path.join(HERE, f))]
    out.append(_check(
        "段名全量表（validate_inp 用）",
        not missing_dm,
        "找到 scripts/_cp2k_sections.py"
        + ("" if missing_dm else "（1342 个官方 SECTION）"),
        fix="" if not missing_dm else
        "缺少 scripts/_cp2k_sections.py：validate_inp.py 的段名白名单会退回 156 个"
        "手工条目，合法的官方段（如 &MULLIKEN）会被误报成 typo；"
        "跑 python _gen_cp2k_sections.py 可重新生成（需 cp2k-input-tools）",
        required=False,
    ))

    missing_h = [f for f in H_LAYER if not os.path.isfile(os.path.join(ROOT, f))]
    hdir = os.path.join(ROOT, "references", "h_tutorials")
    n_txt = len([f for f in os.listdir(os.path.join(hdir, "txt"))
                 if f.endswith(".txt")]) \
        if os.path.isdir(os.path.join(hdir, "txt")) else 0
    n_notes = len([f for f in os.listdir(os.path.join(hdir, "notes"))
                   if f.endswith(".md")]) \
        if os.path.isdir(os.path.join(hdir, "notes")) else 0
    out.append(_check(
        "H 层官方教程（抽取脚本 + 24 份教程 + 精读笔记）",
        not missing_h and n_txt >= 24,
        f"txt/ {n_txt} 份（预期 24）、notes/ {n_notes} 份、"
        f"脚本 {len(H_LAYER) - len(missing_h)}/{len(H_LAYER)}",
        fix=(f"缺少 {', '.join(missing_h)}；" if missing_h else "")
            + (f"txt/ 只有 {n_txt} 份（预期 24）：跑 "
               "python references/h_tutorials/extract_tutorials.py --src <教程目录> 重新抽取"
               if n_txt < 24 else ""),
        required=False,
    ))

    odir = os.path.join(ROOT, "references", "official")
    n_official = len([f for f in os.listdir(odir) if f.endswith(".md")]) \
        if os.path.isdir(odir) else 0
    out.append(_check(
        "G 层官方权威层", n_official >= 27,
        f"{n_official} 个 .md（预期 27）",
        fix="G 层文件不完整，请重新下载 references/official/ 目录" if n_official < 27 else "",
        required=False,
    ))

    refs = [
        ("A 决策库", "references/decide.md"),
        ("B 课程综合", "references/course_learned.md"),
        ("F 实战手册", "references/playbook.md"),
        ("使用说明", "USAGE.md"),
        ("跨 agent 入口", "AGENTS.md"),
    ]
    for label, rel in refs:
        p = os.path.join(ROOT, rel)
        out.append(_check(
            label, os.path.isfile(p), "存在" if os.path.isfile(p) else "缺失",
            fix=f"缺少 {rel}" if not os.path.isfile(p) else "",
            required=False,
        ))
    return out


def _has_module(name):
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def check_deps():
    out = []
    py = sys.executable

    # 运行依赖（仅后处理需要）
    for mod, pkg in [("numpy", "numpy"), ("matplotlib", "matplotlib")]:
        has = _has_module(mod)
        out.append(_check(
            f"运行依赖 {mod}", has,
            "已安装" if has else "未安装（只有后处理出图需要，其余 6 个工具不受影响）",
            fix="" if has else f'"{py}" -m pip install {pkg}',
            required=False,
        ))

    # 开发依赖（仅权威校验需要）
    for mod, pkg in [("cp2k_input_tools", "cp2k-input-tools"),
                     ("pint", "pint"), ("lxml", "lxml")]:
        has = _has_module(mod)
        out.append(_check(
            f"开发依赖 {mod}", has,
            "已安装" if has else "未安装（只有 _validate_all.py 权威校验需要）",
            fix="" if has else f'"{py}" -m pip install {pkg}',
            required=False,
        ))
    return out


def check_binaries():
    out = []
    specs = [
        ("cp2k", "跑计算（提交作业用）", "必装才能实际算；skill 只生成输入不代跑"),
        ("mpirun", "并行启动 cp2k", "多数集群自带；单机可先不装"),
        ("bader", "Bader 电荷后处理", "只有 postprocess bader 需要"),
        ("travis", "TRAVIS 谱学后处理", "只有 postprocess travis 需要"),
        ("graph", "元动力学自由能面", "只有 postprocess fes 需要（随 CP2K 一起安装）"),
    ]
    for name, why, note in specs:
        path = shutil.which(name)
        out.append(_check(
            f"外部二进制 {name}", path is not None,
            (path or "未找到") + f" —— {why}",
            fix="" if path else f"{note}；缺失不影响生成/校验输入",
            required=False,
        ))
    return out


def check_validators():
    """三项校验的可运行性（只判断，不实跑）。"""
    out = []
    py = sys.executable
    out.append(_check(
        "_doc_consistency.py 可运行", os.path.isfile(os.path.join(ROOT, "_doc_consistency.py")),
        "零依赖，可直接跑",
        fix="缺少该文件" if not os.path.isfile(os.path.join(ROOT, "_doc_consistency.py")) else "",
        required=False,
    ))
    ok_pp = os.path.isfile(os.path.join(ROOT, "_validate_postprocess.py")) and \
        _has_module("numpy") and _has_module("matplotlib")
    out.append(_check(
        "_validate_postprocess.py 可运行", ok_pp,
        "依赖齐全" if ok_pp else "缺 numpy/matplotlib（先装运行依赖）",
        fix="" if ok_pp else f'"{py}" -m pip install -r requirements.txt',
        required=False,
    ))
    ok_all = os.path.isfile(os.path.join(ROOT, "_validate_all.py")) and \
        _has_module("cp2k_input_tools") and _has_module("pint")
    out.append(_check(
        "_validate_all.py 可运行", ok_all,
        "依赖齐全" if ok_all else "缺 cp2k-input-tools/pint（先装开发依赖）",
        fix="" if ok_all else f'"{py}" -m pip install -r requirements-dev.txt',
        required=False,
    ))
    return out


def collect():
    groups = [
        ("环境", [check_python()]),
        ("仓库完整性", check_repo()),
        ("Python 依赖", check_deps()),
        ("外部二进制（按需）", check_binaries()),
        ("校验可运行性", check_validators()),
    ]
    return groups


def render_text(groups):
    ok_all = True
    core_bad = []
    lines = []
    lines.append("=" * 68)
    lines.append("  cp2k-aimd skill 环境自检（doctor.py）")
    lines.append("=" * 68)

    for title, items in groups:
        lines.append("")
        lines.append(f"【{title}】")
        for it in items:
            mark = "✓" if it["ok"] else ("✗" if it["required"] else "·")
            lines.append(f"  {mark} {it['label']}: {it['detail']}")
            if not it["ok"] and it["fix"]:
                lines.append(f"      → 修复：{it['fix']}")
            if not it["ok"] and it["required"]:
                ok_all = False
                core_bad.append(it["label"])

    lines.append("")
    lines.append("-" * 68)
    if ok_all:
        lines.append("结论：核心功能可用 ✓")
        lines.append("")
        lines.append("下一步（新手推荐顺序）：")
        lines.append("  1) python scripts/guide.py list          看项目全流程")
        lines.append("  2) python scripts/wizard.py              问答式生成第一个 .inp")
        lines.append("  3) python scripts/validate_inp.py x.inp  提交前校验")
        lines.append("  或直接读 USAGE.md（30 秒上手）")
    else:
        lines.append("结论：核心功能有问题 ✗")
        lines.append(f"  必须先解决：{', '.join(core_bad)}")
        lines.append("  按上面每条的「→ 修复」照做即可。")
    lines.append("-" * 68)
    return "\n".join(lines), ok_all


def main():
    ap = argparse.ArgumentParser(
        description="cp2k-aimd skill 环境自检（新手第一步跑这个）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n  python scripts/doctor.py\n  python scripts/doctor.py --json\n",
    )
    ap.add_argument("--json", action="store_true", help="输出 JSON（给 agent 用）")
    ap.add_argument("--quiet", action="store_true", help="只输出问题项（CI 用）")
    args = ap.parse_args()

    groups = collect()

    if args.json:
        flat = [it for _, items in groups for it in items]
        payload = {
            "python": sys.version.split()[0],
            "core_ok": all(it["ok"] for it in flat if it["required"]),
            "groups": [{"title": t, "checks": items} for t, items in groups],
            "fixes": [it["fix"] for it in flat if not it["ok"] and it["fix"]],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["core_ok"] else 1

    if args.quiet:
        flat = [it for _, items in groups for it in items]
        bad = [it for it in flat if not it["ok"] and it["required"]]
        for it in bad:
            print(f"[FAIL] {it['label']}: {it['detail']}")
            if it["fix"]:
                print(f"       → {it['fix']}")
        return 0 if not bad else 1

    text, ok_all = render_text(groups)
    print(text)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
