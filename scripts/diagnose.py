#!/usr/bin/env python3
"""CP2K 输出诊断引擎 —— skill 的"思考层"第二部分（结果判读闭环）。

读一个 .out，识别常见"算得不对 / 没收敛 / 该调参"的信号，并给出
**具体的下一步改哪一行**（对应 gen_inp.py 开关或模板关键字）。

覆盖的信号：
  - SCF 不收敛（最多迭代/未收敛）→ 加 --outer-scf / --smear / 换 MIXING / RESTART
  - 几何优化未达收敛 → 增 MAX_ITER / 换 LBFGS / 先 CELL_OPT / 放宽 MAX_FORCE
  - 残余力仍偏大 → 收紧 MAX_FORCE
  - 金属体系却没开 SMEAR（k 点 + SCF 难收敛）→ --smear
  - AIMD 能量漂移 → 减 TIMESTEP / 查 thermostat / 开 SMEAR
  - 振动分析虚频 → 极小点 vs 过渡态的判断
  - GPW 病态 / 截断过低警告 → 增 CUTOFF
  - 致命 ABORT / 收集 WARNING 列表

Usage:
  python diagnose.py cp2k.out
  python diagnose.py cp2k.out --verbose
"""
import argparse
import re
import sys


def parse(out_text):
    lines = out_text.splitlines()
    res = {
        "fatal": [],
        "warnings": [],
        "scf_converged": 0,
        "scf_not_converged": 0,
        "reached_max_scf": 0,
        "geo_done": 0,
        "geo_not": 0,
        "max_force_last": None,
        "energies": [],
        "has_kpoints": False,
        "has_smear": False,
        "imag_freqs": [],
        "md_steps": 0,
    }
    for ln in lines:
        if "ABORT" in ln or "FATAL" in ln:
            res["fatal"].append(ln.strip())
        if "WARNING" in ln:
            res["warnings"].append(ln.strip())
        if "SCF run converged" in ln:
            res["scf_converged"] += 1
        if "SCF run NOT converged" in ln:
            res["scf_not_converged"] += 1
        if "Reached maximum number of SCF iterations" in ln:
            res["reached_max_scf"] += 1
        if "GEOMETRY OPTIMIZATION COMPLETE" in ln:
            res["geo_done"] += 1
        if "GEOMETRY OPTIMIZATION NOT" in ln or "OPTIMIZATION NOT converged" in ln:
            res["geo_not"] += 1
        if "Max. force" in ln:
            m = re.search(r"[-+]?\d+\.\d+(?:[edED][-+]?\d+)?", ln)
            if m:
                res["max_force_last"] = float(m.group(0))
        if "Total FORCE_EVAL" in ln and "energy (a.u.)" in ln:
            m = re.search(r"[-+]?\d+\.\d+(?:[edED][-+]?\d+)?\s*$", ln)
            if m:
                res["energies"].append(float(m.group(0)))
        if "k-points" in ln.lower() or "KPOINTS" in ln:
            res["has_kpoints"] = True
        if "FERMI_DIRAC" in ln or "SMEAR" in ln:
            res["has_smear"] = True
        if "MD step" in ln or "STEP" in ln and "ENSEMBLE" in ln:
            # rough MD step counter
            pass
        # imaginary frequency: CP2K prints negative cm^-1 for unstable modes.
        # handle "Frequency (cm^-1)   -123.45" (same line) and
        # "  1   -123.45   ..." (mode-number + value, multi-line CP2K format).
        mf = re.search(r"Frequency.*?(-?\d+\.\d+)", ln)
        if mf and float(mf.group(1)) < 0:
            res["imag_freqs"].append(float(mf.group(1)))
        mm = re.match(r"\s*\d+\s+(-?\d+\.\d+)", ln)
        if mm and float(mm.group(1)) < 0:
            res["imag_freqs"].append(float(mm.group(1)))
    return res


def diagnose(res, verbose=False):
    findings = []  # list of (severity, msg, suggestion)

    if res["fatal"]:
        findings.append((
            "ERROR",
            "计算被 ABORT：{}".format(res["fatal"][0][:120]),
            "先解决致命错误（通常是语法/内存/文件缺失），再谈收敛。看 ABORT 上方报错。",
        ))
        return findings  # 致命错误优先

    # ---- SCF ----
    if res["scf_not_converged"] or res["reached_max_scf"]:
        sug = ("SCF 未收敛（出现 {} 次未收敛 / {} 次达最大迭代）。建议：\n"
               "  ① 加 --outer-scf（外层循环，帮 OT 跳出）；\n"
               "  ② 若是金属/窄带隙，加 --smear（FERMI_DIRAC 300K）；\n"
               "  ③ 增大 MAX_SCF（模板 &SCF MAX_SCF 300→500），换 --mixing-method pulay 或 multisecant（注意 FULL_ALL 不是合法 &MIXING METHOD）；\n"
               "  ④ 续算用 SCF_GUESS RESTART（EXT_RESTART）。"
               ).format(res["scf_not_converged"], res["reached_max_scf"])
        findings.append(("WARN", "SCF 未收敛", sug))
    elif res["scf_converged"] == 0 and res["energies"]:
        findings.append((
            "INFO",
            "未发现明确的 SCF 收敛/未收敛标志，但有能量输出。",
            "若后续步数很多，建议确认 SCF 真收敛（grep 'SCF run converged'）。",
        ))

    # ---- 金属未开 SMEAR ----
    if res["has_kpoints"] and not res["has_smear"] and (
            res["scf_not_converged"] or res["reached_max_scf"]):
        findings.append((
            "WARN",
            "含 k 点且 SCF 难收敛，但未检测到 SMEAR。",
            "金属/窄带隙体系强烈建议 --smear（FERMI_DIRAC 300K），否则费米面附近 SCF 抖动不收敛。",
        ))

    # ---- 几何优化 ----
    if res["geo_not"]:
        sug = ("几何优化未达收敛。建议：\n"
               "  ① 增大 MAX_ITER（模板 &GEO_OPT MAX_ITER 400→800）；\n"
               "  ② 若力在振荡，换 OPTIMIZER LBFGS；\n"
               "  ③ 检查初始结构是否合理，必要时先 CELL_OPT；\n"
               "  ④ 可暂放宽 MAX_FORCE 到 1e-3 先得大致结构。")
        findings.append(("WARN", "几何优化未收敛", sug))
    elif res["geo_done"] and res["max_force_last"] is not None:
        if res["max_force_last"] > 1.0e-3:
            findings.append((
                "INFO",
                "已收敛但最后最大力 {:.2e} a.u./bohr（>1e-3）。".format(res["max_force_last"]),
                "对多数性质够用；若要更精确（如频率/吸附能），收紧 MAX_FORCE 到 6e-4 重算。",
            ))

    # ---- 能量漂移（MD / 多次 SCF 能量）----
    if len(res["energies"]) >= 3:
        emin, emax = min(res["energies"]), max(res["energies"])
        span = emax - emin
        if abs(emin) > 1e-6 and abs(span / emin) > 0.01:
            findings.append((
                "WARN",
                "能量跨度 {:.4f} a.u.（相对 {:.2%}），疑似 AIMD 能量漂移。".format(
                    span, span / emin),
                "建议：① 减小 TIMESTEP（模板 &MD TIMESTEP 0.5→0.25 fs）；② 查 NOSE "
                "thermostat TIMECON；③ 金属确认 --smear 已开；④ 看守恒量是否漂移。",
            ))
        elif verbose:
            findings.append((
                "INFO",
                "能量跨度 {:.2e} a.u.，基本稳定。".format(span),
                "无需调整。",
            ))

    # ---- 虚频 ----
    if res["imag_freqs"]:
        n = len(res["imag_freqs"])
        if n == 1:
            findings.append((
                "INFO",
                "振动分析有 1 个虚频（{} cm^-1）。".format(res["imag_freqs"][0]),
                "若目标是过渡态：唯一虚频符合预期（鞍点）。若目标是极小点：说明非极小点，"
                "沿虚频模式 distort 后再优化。",
            ))
        else:
            findings.append((
                "WARN",
                "振动分析有 {} 个虚频（最小 {} cm^-1）。".format(n, min(res["imag_freqs"])),
                "若目标是极小点：结构非极小点。沿每个虚频模式依次 distort 后重新优化，"
                "直到无虚频；或用 Dimer 法直接找鞍点。",
            ))

    # ---- GPW 病态 / 截断 ----
    if any("numerically ill-conditioned" in w or "Rho_numerically" in w for w in res["warnings"]):
        findings.append((
            "WARN",
            "检测到 GPW 数值病态警告。",
            "建议增大 CUTOFF（模板 &MGRID CUTOFF，金属/重元素 400–600 Ry），"
            "或调 &QS EPS_DEFAULT。",
        ))

    # ---- WARNING 汇总 ----
    if res["warnings"]:
        if verbose:
            findings.append((
                "INFO",
                "共 {} 条 WARNING，列前 5：".format(len(res["warnings"])),
                "\n".join("  - " + w[:160] for w in res["warnings"][:5]),
            ))
        else:
            findings.append((
                "INFO",
                "检测到 {} 条 WARNING（加 --verbose 查看）。".format(len(res["warnings"])),
                "一般可忽略，但涉及 'ill-conditioned' / 'not converged' 需处理。",
            ))

    if not findings:
        findings.append((
            "INFO",
            "未检测到明显问题。",
            "若能量/力已合理，可进入后处理（postprocess.md）或精修（HSE06/vib）。",
        ))
    return findings


def main():
    ap = argparse.ArgumentParser(description="Diagnose a CP2K .out and suggest fixes.")
    ap.add_argument("out", help="CP2K 输出文件 .out")
    ap.add_argument("--verbose", action="store_true", help="显示 WARNING 明细与能量统计")
    args = ap.parse_args()

    try:
        text = open(args.out).read()
    except OSError as e:
        sys.exit("ERROR: 无法读取 {}: {}".format(args.out, e))

    res = parse(text)
    findings = diagnose(res, verbose=args.verbose)

    print("=" * 64)
    print("CP2K 输出诊断（思考层 · 结果判读）")
    print("文件: {}".format(args.out))
    print("=" * 64)
    for sev, msg, sug in findings:
        icon = {"ERROR": "✖", "WARN": "⚠", "INFO": "·"}.get(sev, "·")
        print("\n{} [{}] {}".format(icon, sev, msg))
        print("  → " + sug.replace("\n", "\n    "))
    print("\n--- 统计量 ---")
    print("  SCF 收敛 {} / 未收敛 {} / 达最大迭代 {}".format(
        res["scf_converged"], res["scf_not_converged"], res["reached_max_scf"]))
    print("  几何优化完成 {} / 未收敛 {}".format(res["geo_done"], res["geo_not"]))
    if res["max_force_last"] is not None:
        print("  末步最大力: {:.4e} a.u./bohr".format(res["max_force_last"]))
    print("  能量采样点: {} 个".format(len(res["energies"])))
    print("  含 k 点: {} / 含 SMEAR: {}".format(res["has_kpoints"], res["has_smear"]))
    print("  虚频: {} 个".format(len(res["imag_freqs"])))


if __name__ == "__main__":
    main()
