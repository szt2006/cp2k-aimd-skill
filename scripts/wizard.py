#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wizard.py —— 交互式向导（新手零参数生成第一个 .inp）

新手不用记任何参数：它用一问一答的方式问清"算什么体系、什么目标"，
然后**复用 recommend.py 的推理**给出参数，再**复用 gen_inp.py** 生成 .inp，
最后告诉你下一步该敲什么命令。

设计原则：
  - **不重复造轮子**：参数推理调 `recommend.py`，文件生成调 `gen_inp.py`，
    保证与 CLI 用法永远一致（单一真源）。
  - **零依赖**：纯标准库。
  - **可非交互**：`--yes` 全默认直通（给 agent / CI 用）；`--json` 输出结构化结果。
  - **每一步都能看懂**：打印推荐理由与产物路径，不做黑箱。

用法：
    python scripts/wizard.py                 # 交互问答
    python scripts/wizard.py --yes --out x.inp   # 全默认，直接生成
    python scripts/wizard.py --json          # 结构化输出（需配合 --yes）

退出码：0 = 成功；1 = 用户取消或参数错误；2 = 用法错误；3 = 依赖缺失。
"""

import argparse
import json
import os
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
RECOMMEND = os.path.join(HERE, "recommend.py")
GEN_INP = os.path.join(HERE, "gen_inp.py")

# 体系类型 → (periodic, goal, 说明)
SYSTEM_KINDS = [
    ("1", "分子 / 团簇（气相）", "none", "energy", "孤立分子、团簇、气相反应"),
    ("2", "表面吸附（slab）", "xy", "geo_opt", "金属/氧化物表面 + 吸附质"),
    ("3", "块体 / 晶体", "xyz", "cell_opt", "周期性晶体、晶格常数优化"),
    ("4", "表面 slab 几何优化", "xy", "geo_opt", "已切好表面的 slab 结构优化"),
    ("5", "分子动力学（AIMD）", "xyz", "md", "有限温动力学、扩散、熔体"),
    ("6", "过渡态（NEB）", "xyz", "neb", "反应路径、能垒"),
    ("7", "振动分析（频率）", "none", "vib", "IR 谱、确认极小点/鞍点"),
]

# 目标 → gen_inp --type
GOAL_TO_TYPE = {
    "energy": "static",
    "geo_opt": "geo_opt",
    "cell_opt": "cell_opt",
    "md": "aimd_md",
    "neb": "neb",
    "vib": "vib",
    "ts": "geo_opt",
    "qmmm": "qmmm",
}


def _die(msg, code=1):
    print(f"\n[取消] {msg}", file=sys.stderr)
    sys.exit(code)


def _ask(prompt, default=None, allow_empty=False):
    """提问并读取回答；EOF（管道输入结束）时用默认值或退出。"""
    suffix = f" [{default}]" if default else ""
    try:
        ans = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        if default is not None:
            print(f"{prompt}{suffix}: {default}  (非交互，用默认值)")
            return default
        _die("输入中断，且该项没有默认值。请改用 --yes 走默认流程，或在交互终端里运行。")
    if not ans:
        if default is not None:
            return default
        if allow_empty:
            return ""
        _die(f"「{prompt}」不能为空。")
    return ans


def _ask_choice(prompt, options, default=None):
    """options: [(key, label, ...)]，返回选中的 key。"""
    print(f"\n{prompt}")
    for opt in options:
        key, label = opt[0], opt[1]
        note = f"  —— {opt[4]}" if len(opt) > 4 and opt[4] else ""
        print(f"  {key}) {label}{note}")
    keys = [o[0] for o in options]
    while True:
        ans = _ask("请输入序号", default=default)
        if ans in keys:
            return ans
        print(f"  ✗ 「{ans}」不是有效选项，请从 {', '.join(keys)} 里选。")


def _ask_yesno(prompt, default="n"):
    ans = _ask(prompt + " (y/n)", default=default).lower()
    return ans in ("y", "yes", "是", "1", "t", "true")


def _run(cmd, label):
    """跑子命令，回传 (ok, stdout, stderr)。"""
    print(f"\n  → 执行：{' '.join(cmd)}")
    try:
        # 子进程（recommend.py / gen_inp.py）经 _console 统一输出 UTF-8，
        # 这里必须按 UTF-8 解码，否则在 GBK 环境下会乱码/报错。
        p = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
    except FileNotFoundError:
        return False, "", f"找不到 {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, "", "执行超时（120s）"
    if p.returncode != 0:
        return False, p.stdout, p.stderr
    return True, p.stdout, p.stderr


def run_recommend(elements, goal, periodic, mult, vdw, func=None, extra=None):
    cmd = [sys.executable, RECOMMEND, "--elements", *elements,
           "--goal", goal, "--periodic", periodic]
    if mult and mult != "1":
        cmd += ["--multiplicity", str(mult)]
    if vdw:
        cmd += ["--vdw", vdw]
    if func:
        cmd += ["--functional", func]
    if extra:
        cmd += extra
    return _run(cmd, "recommend")


def build_gen_cmd(elements, goal, out, basis=None, potential=None,
                  mult=None, dispersion=False, periodic="xyz",
                  smear=False, kpoints=None, fixed_atoms=None,
                  surface_dipole=False, functional=None, admm=False,
                  thermostat=None, ensemble=None, restart_freq=None,
                  kinds=None, xyz=None):
    typ = GOAL_TO_TYPE.get(goal, "static")
    cmd = [sys.executable, GEN_INP, "--type", typ,
           "--elem", *elements, "-o", out]
    if basis:
        cmd += ["--basis", *basis]
    if potential:
        cmd += ["--potential", *potential]
    if mult and str(mult) != "1":
        cmd += ["--multiplicity", str(mult)]
    if dispersion:
        cmd += ["--dispersion"]
    if periodic:
        cmd += ["--periodic", periodic]
    if smear:
        cmd += ["--smear"]
    if kpoints:
        cmd += ["--kpoints", kpoints]
    if fixed_atoms:
        cmd += ["--fixed-atoms", fixed_atoms]
    if surface_dipole:
        cmd += ["--surface-dipole"]
    if functional:
        cmd += ["--functional", functional]
    if admm:
        cmd += ["--admm"]
    if thermostat:
        cmd += ["--thermostat", thermostat]
    if ensemble:
        cmd += ["--ensemble", ensemble]
    if restart_freq:
        cmd += ["--restart-freq", str(restart_freq)]
    if kinds:
        cmd += ["--kinds", *kinds]
    if xyz:
        cmd += ["--xyz", xyz]
    return cmd


def _parse_recommend_basis(stdout):
    """从 recommend 输出里抓基组/赝势（两行形如 '      DZVP-... / GTH-...'）。"""
    basis, pot = [], []
    for line in stdout.splitlines():
        s = line.strip()
        if "/" in s and ("GTH" in s or "MOLOPT" in s or "PADE" in s):
            parts = [p.strip() for p in s.split("/")]
            if len(parts) == 2 and parts[0] and parts[1]:
                basis.append(parts[0])
                pot.append(parts[1])
    return basis or None, pot or None


def _parse_recommend_cmd(stdout):
    """从 recommend 输出的「生成命令」段抓出 --basis / --potential / --kpoints。

    这是旧版兼容路径；新版优先用 extract_gen_argv() 直接复用整条命令。
    """
    basis = pot = kpoints = None
    in_cmd = False
    for line in stdout.splitlines():
        if "生成命令" in line:
            in_cmd = True
            continue
        if not in_cmd:
            continue
        s = line.strip().rstrip("\\").strip()
        if s.startswith("--basis"):
            basis = s.split()[1:]
        elif s.startswith("--potential"):
            pot = s.split()[1:]
        elif s.startswith("--kpoints"):
            kpoints = " ".join(s.split()[1:]).strip('"')
    return basis, pot, kpoints


def extract_gen_argv(stdout):
    """把 recommend 输出的「生成命令」整段还原成 argv 列表（去掉 python gen_inp.py）。

    这样能**原样复用** recommend 的全部建议参数（含 --smear 的精细 SCF 调参、
    --cutoff/--eps-scf/--added-mos/--mixing-* 等），避免手工解析漏项。
    返回 None 表示没找到可用的命令段。
    """
    lines = stdout.splitlines()
    start = None
    for i, line in enumerate(lines):
        if "生成命令" in line:
            start = i + 1
            break
    if start is None:
        return None

    argv = []
    for line in lines[start:]:
        s = line.strip()
        if not s:
            break
        if s.startswith("（") or s.startswith("("):   # 命令段结束
            break
        s = s.rstrip("\\").strip()
        if not s or s.startswith("python "):          # 跳过 `python gen_inp.py`
            continue
        # 处理 --kpoints "4 4 1" 这类带引号的值：按 shlex 风格切
        argv.extend(_split_args(s))
    return argv or None


def _split_args(s):
    """按空格切分，但保留引号内的空格（如 --kpoints "4 4 1"）。"""
    out, cur, quote = [], "", None
    for ch in s:
        if quote:
            if ch == quote:
                quote = None
            else:
                cur += ch
        elif ch in "\"'":
            quote = ch
        elif ch.isspace():
            if cur:
                out.append(cur)
                cur = ""
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


# 带值的开关（删除时必须连值一起删）
#
# ⚠️ **这个集合必须覆盖 gen_inp.py 的每一个带值开关**（含 `nargs="+"`/`"*"` 的算多值，
# 见 MULTI_VALUE_FLAGS）。漏登记一个，wizard 拆命令行时就会把它的**值**当成独立 token
# （删开关时值残留、或反过来把值当开关）。
# 原先两份清单各自手工维护、**已经漂移**：实测漏了 27 个（`--timestep`/`--timecon`/
# `--steps`/`--walltime`/`--xyz-init`/`--xyz-final`/`--rotate-frames`/`--align-frames`/
# `--plus-u-method`/`--qs-eps`/`--print-style` … 多数在更早几轮就漏了）。
# 现在由 `_doc_consistency.py` 的第 11 条检查**从 argparse 实测**比对，不会再漂。
VALUE_FLAGS = {
    "--type", "--project", "--elem", "--basis", "--potential", "--charge",
    "--multiplicity", "--functional", "--periodic", "--kpoints", "--fixed-atoms",
    "--cutoff", "--rel-cutoff", "--eps-scf", "--max-scf", "--eps-diis",
    "--added-mos", "--cholesky", "--scf-guess", "--mixing-method",
    "--mixing-alpha", "--mixing-beta", "--mixing-nbroyden", "--ot-minimizer",
    "--diagonalization-eps-adapt", "--thermostat", "--ensemble", "--restart-freq",
    "--optimizer", "--kinds", "--cell", "--xyz", "--coord", "--topology",
    "--topology-format", "--output", "-o", "--wfn-restart", "--cube-stride",
    "--pdos-nhomo", "--pdos-nlumo", "--band-type", "--nproc-rep", "--delta-t",
    "--wtgamma", "--metadyn-ww", "--plumed-file", "--dipole-dir",
    "--dipole-pos", "--dipole-switch", "--constraint-g3x3",
    "--g3x3-distances", "--hbond-atom-type", "--hbond-targets",
    "--qm-elem", "--mm-elem", "--qm-method", "--qm-atoms", "--mm-atoms",
    "--qm-topology", "--qmmm-run-type", "--group-partition", "--k-spring",
    "--optimize-band", "--properties", "--stress-tensor",
    # --- 2026-10 补齐：从 gen_inp.py 的 argparse 实测出来的 27 个 ---
    "--align-frames", "--cell-opt-constraint", "--cell-symmetry",
    "--coord-include", "--diagonalization-algorithm", "--ldos-list",
    "--neb-max-force", "--neb-rms-force", "--nose-length", "--nose-mts",
    "--nose-yoshida", "--optimize-end-points", "--ot-linesearch",
    "--ot-preconditioner", "--plus-u-method", "--print-style", "--qs-eps",
    "--rotate-frames", "--scf-route", "--steps", "--temperature", "--timecon",
    "--timecon-unit",
    "--timestep", "--trajectory-format", "--walltime", "--xyz-final",
    "--xyz-init",
}
# 可重复出现、带多个值的开关
MULTI_VALUE_FLAGS = {
    "--elem", "--basis", "--potential", "--kinds", "--properties",
    "--qm-elem", "--mm-elem", "--xyz-replicas", "--fixed-atoms",
}


def _drop_flag(argv, flag):
    """从 argv 里移除某个开关；带值开关会连它的值一起删。"""
    if flag not in VALUE_FLAGS:
        return [a for a in argv if a != flag]
    out, skip = [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a == flag:
            skip = True
            continue
        out.append(a)
    return out


def interactive(args):
    print("=" * 68)
    print("  CP2K 输入文件向导（wizard.py）—— 不用记参数，问几个问题就行")
    print("=" * 68)
    print("\n随时按 Ctrl+C 退出。")

    # ---- 1. 体系类型 ----
    key = _ask_choice("① 你要算什么类型的体系？", SYSTEM_KINDS, default="2")
    kind = [k for k in SYSTEM_KINDS if k[0] == key][0]
    _, kind_label, periodic, goal, _ = kind

    # ---- 2. 元素 ----
    print("\n② 体系里有哪些元素？（元素符号，空格分隔，如：Au O）")
    print("   常见：Au/Cu/Pt 等过渡金属用 MOLOPT 基组；Si/O/C/H 等轻元素用 PADE。")
    while True:
        raw = _ask("元素列表", default="Si")
        elems = [e.capitalize() for e in raw.replace(",", " ").split() if e]
        if elems:
            break
        print("  ✗ 至少写一个元素。")
    print(f"   已选：{' '.join(elems)}")

    # ---- 3. 自旋 ----
    mult = "1"
    if _ask_yesno("\n③ 体系是开壳层吗？（有未成对电子：O₂、自由基、多数吸附态）", default="n"):
        while True:
            raw = _ask("   多重度 (2=单电子, 3=双电子, 4=三电子...)", default="3")
            if raw.isdigit() and int(raw) >= 1:
                mult = raw
                break
            print("  ✗ 请输入 >=1 的整数。")

    # ---- 4. 色散 ----
    vdw = "no"
    if periodic in ("xy", "xyz") and _ask_yesno(
            "\n④ 有弱相互作用吗？（吸附、层状材料、分子晶体、氢键）", default="y"):
        vdw = "auto"

    # ---- 5. 金属/SMEAR ----
    smear = False
    if _ask_yesno("\n⑤ 体系含金属或窄带隙半导体吗？（决定要不要 SMEAR + k 点）", default="n"):
        smear = True

    # ---- 6. 过渡态专项 ----
    xyz_replicas = None
    if goal == "neb":
        print("\n⑥ NEB 需要两个端点结构文件（.xyz）。")
        init = _ask("   起始结构文件路径", default="init.xyz")
        final = _ask("   终止结构文件路径", default="final.xyz")
        xyz_replicas = [init, final]

    # ---- 7. 结构文件 ----
    xyz = None
    if goal != "neb" and _ask_yesno(
            "\n⑦ 有现成的结构文件吗？（.xyz / POSCAR / .cif；没有就先留空，稍后手动填 &COORD）",
            default="n"):
        xyz = _ask("   结构文件路径", default="structure.xyz")

    # ---- 8. 输出文件名 ----
    default_out = f"{GOAL_TO_TYPE.get(goal, 'static')}.inp"
    out = _ask("\n⑧ 输出文件名", default=args.out or default_out)

    return {
        "kind_label": kind_label, "periodic": periodic, "goal": goal,
        "elements": elems, "mult": mult, "vdw": vdw, "smear": smear,
        "xyz_replicas": xyz_replicas, "xyz": xyz, "out": out,
    }


def main():
    ap = argparse.ArgumentParser(
        description="CP2K 输入文件交互式向导（新手零参数生成 .inp）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n  python scripts/wizard.py\n  python scripts/wizard.py --yes --out si.inp\n",
    )
    ap.add_argument("--yes", action="store_true",
                    help="非交互：全部用默认值（Si 块体静态计算）")
    ap.add_argument("--out", default=None, help="输出文件名")
    ap.add_argument("--json", action="store_true", help="输出 JSON 结果")
    args = ap.parse_args()

    for p in (RECOMMEND, GEN_INP):
        if not os.path.isfile(p):
            print(f"[ERROR] 缺少 {os.path.basename(p)}，仓库不完整。", file=sys.stderr)
            return 3

    if args.yes:
        cfg = {
            "kind_label": "块体 / 晶体", "periodic": "xyz", "goal": "energy",
            "elements": ["Si"], "mult": "1", "vdw": "no", "smear": False,
            "xyz_replicas": None, "xyz": None,
            "out": args.out or "static.inp",
        }
    else:
        try:
            cfg = interactive(args)
        except KeyboardInterrupt:
            print("\n\n已取消。", file=sys.stderr)
            return 1

    elems = cfg["elements"]
    goal = cfg["goal"]
    periodic = cfg["periodic"]
    mult = cfg["mult"]
    vdw = cfg["vdw"] if cfg["vdw"] != "no" else None

    # ---- 调 recommend 拿参数与理由 ----
    ok, stdout, stderr = run_recommend(elems, goal, periodic, mult, vdw)
    if not ok:
        print("\n[ERROR] recommend.py 失败：", file=sys.stderr)
        print(stderr or stdout, file=sys.stderr)
        return 1

    if not args.json:
        print("\n" + "-" * 68)
        print("【推荐参数与理由】（来自 recommend.py）")
        print("-" * 68)
        print(stdout.rstrip())

    # ---- 优先复用 recommend 给出的完整命令；否则回退到手工拼装 ----
    rec_argv = extract_gen_argv(stdout)
    if rec_argv:
        # 去掉 recommend 里的占位 --xyz <结构.xyz> 与 -o cp2k.inp，按用户选择替换
        cleaned = []
        skip_next = False
        for i, a in enumerate(rec_argv):
            if skip_next:
                skip_next = False
                continue
            if a in ("-o", "--output"):
                skip_next = True
                continue
            if a == "--xyz":
                skip_next = True
                continue
            if a == "--cell":
                # --cell 需要 9 个值；模板里没结构时也保留（用户可改）
                cleaned.append(a)
                continue
            cleaned.append(a)
        cmd = [sys.executable, GEN_INP] + cleaned + ["-o", cfg["out"]]
        if cfg["xyz"]:
            cmd += ["--xyz", cfg["xyz"]]
        # NEB 端点
        if cfg.get("xyz_replicas"):
            cmd = [x for x in cmd if x != "--xyz"]
            cmd += ["--xyz-replicas", *cfg["xyz_replicas"]]
        # 用户明确否定的项，移除 recommend 的相反建议
        if not cfg["smear"]:
            cmd = _drop_flag(cmd, "--smear")
        if cfg["vdw"] != "auto":
            cmd = _drop_flag(cmd, "--dispersion")
        if not cfg.get("mult") or str(cfg["mult"]) == "1":
            cmd = _drop_flag(cmd, "--multiplicity")
    else:
        basis, pot, kpoints = _parse_recommend_cmd(stdout)
        if not basis:
            basis, pot = _parse_recommend_basis(stdout)
        cmd = build_gen_cmd(
            elems, goal, cfg["out"],
            basis=basis, potential=pot, mult=mult,
            dispersion=(vdw == "auto"), periodic=periodic,
            smear=cfg["smear"], kpoints=kpoints,
            xyz=cfg["xyz"],
        )
        if cfg.get("xyz_replicas"):
            cmd += ["--xyz-replicas", *cfg["xyz_replicas"]]

    if not args.yes and not _ask_yesno("\n是否现在生成 .inp？", default="y"):
        print("\n已跳过生成。你可以手动执行上面的命令。")
        if args.json:
            print(json.dumps({"generated": False, "gen_cmd": cmd}, ensure_ascii=False, indent=2))
        return 0

    ok, g_out, g_err = _run(cmd, "gen_inp")
    if not ok:
        print("\n[ERROR] gen_inp.py 失败：", file=sys.stderr)
        print(g_err or g_out, file=sys.stderr)
        return 1

    out_path = cfg["out"]
    print(f"\n{'=' * 68}")
    print(f"  完成！已生成：{out_path}")
    print(f"{'=' * 68}")
    print("\n下一步：")
    print(f"  1) 校验语法：python scripts/validate_inp.py {out_path}")
    print(f"  2) 填入坐标（若 &COORD 里还是占位符）：打开 {out_path} 替换 __COORD__ 部分")
    print("  3) 提交计算：mpirun -n 4 cp2k.popt "
          f"{out_path} 1>cp2k.out 2>cp2k.err   （见 references/run.md）")
    print("  4) 跑完读结果：python scripts/parse_output.py cp2k.out")
    print("                 python scripts/diagnose.py cp2k.out")
    print("\n想知道每一步该注意什么：python scripts/guide.py show "
          f"{'optimize' if goal in ('geo_opt', 'cell_opt') else 'static' if goal == 'energy' else 'dynamics'}")

    if args.json:
        print(json.dumps({
            "generated": True,
            "out": out_path,
            "goal": goal,
            "elements": elems,
            "periodic": periodic,
            "gen_cmd": cmd,
            "next": [
                f"python scripts/validate_inp.py {out_path}",
                f"mpirun -n 4 cp2k.popt {out_path} 1>cp2k.out 2>cp2k.err",
                "python scripts/parse_output.py cp2k.out",
                "python scripts/diagnose.py cp2k.out",
            ],
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
