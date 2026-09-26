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


def _num(tok):
    """CP2K 数字偶用 Fortran 风格 D 指数（如 1.2D+01），float() 不认，统一换 E。"""
    return float(tok.replace("D", "E").replace("d", "e"))


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
        "sum_force": None,
        "energies": [],
        "has_kpoints": False,
        "has_smear": False,
        "imag_freqs": [],
        "md_steps": 0,
        # --- 作业是否跑完（新增；既有键一个都没动）---
        "program_ended": 0,
        "bad_termination": 0,
        "exit_code": None,
        "md_steps_requested": None,
        "md_steps_done": 0,
        "completion_pct": None,
        "run_status": "unknown",
        # --- MD 温度/系综/守恒量漂移（新增；既有键一个都没动）---
        "temp_target": None,       # MD| Temperature [K]  回显的目标温度
        "ensemble": None,          # NVT / NVE / NPT ...
        "thermostat": None,        # Nose-Hoover-Chains / CSVR / ...
        "temps": [],               # 每 MD 步瞬时温度 [K]
        "temps_avg": [],           # CP2K 自带滑动平均温度 [K]
        "drift_per_atom": [],      # ENERGY DRIFT PER ATOM [K] 瞬时
        "drift_per_atom_avg": [],  # ENERGY DRIFT PER ATOM [K] 滑动平均
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
        if "Max. force" in ln or "Max. gradient" in ln:
            m = re.search(r"[-+]?\d+\.\d+(?:[edED][-+]?\d+)?", ln)
            if m:
                res["max_force_last"] = float(m.group(0))
        # 🔴 **原子力之和 ΣF**：孤立体系的**牛顿第三定律判据**。
        # CP2K 每步都打印 `SUM OF ATOMIC FORCES  fx  fy  fz  |ΣF|`。
        # 为什么值得单独盯它（2026-10 真机实测血泪）：`POISSON_SOLVER WAVELET`
        # 有一个硬前提——**分子必须居于单胞中心**（官方 T24 §3.4：确保单胞边界处
        # 电子密度为 0）。违反了它，CP2K **不报任何错、SCF 照常"收敛"**，
        # 但结果是错的：实测同一水分子
        #     偏心 ⇒ E = −29.225 Ha，**|ΣF| = 24.72 a.u.**，O 上的力 23 a.u.
        #     居中 ⇒ E = −17.120 Ha，|ΣF| = 0.0005 a.u.  ✅ 与 ANALYTIC/MT 一致
        # 也就是说 **ΣF≠0 是这类"静默错误"唯一可见的症状**，而它就在输出里。
        if "SUM OF ATOMIC FORCES" in ln:
            nums = re.findall(r"[-+]?\d+\.\d+(?:[eEdD][-+]?\d+)?", ln)
            if len(nums) >= 4:
                try:
                    res["sum_force"] = float(nums[3])
                except ValueError:
                    pass
        # ⚠️ 能量行**跨版本换过写法**，两种都要认（2026-10 真机实测发现）：
        #     旧版（如课程那批 5.x/6.x）:  ENERGY| Total FORCE_EVAL ( QS ) energy (a.u.):  -29.06...
        #     CP2K 2022.1            :  ENERGY| Total FORCE_EVAL ( QS ) energy [a.u.]:  -29.06...
        # 早先只写死了 **圆括号** 的 "energy (a.u.)"，于是在 2022.1 的输出上**一个都匹配不到**
        # ⇒ `res["energies"]` 恒为空 ⇒ **整条「AIMD 能量漂移」诊断静默失效**
        # （同一份文件 `parse_output.py` 却能数出 19 个能量，因为它的正则对格式不敏感）。
        # 现在改成与 parse_output.py 同源的**格式无关**写法：认 `ENERGY| Total FORCE_EVAL … :  <数>`。
        if "ENERGY|" in ln and "Total FORCE_EVAL" in ln:
            m = re.search(r":\s*([-+]?\d+\.\d+(?:[eEdD][-+]?\d+)?)\s*$", ln)
            if m:
                res["energies"].append(_num(m.group(1)))
        if "k-points" in ln.lower() or "KPOINTS" in ln:
            res["has_kpoints"] = True
        if "FERMI_DIRAC" in ln or "SMEAR" in ln:
            res["has_smear"] = True

        # ---- 作业是否跑完：正常收尾 / 被 kill / 未知 ----
        if "PROGRAM ENDED AT" in ln or "PROGRAM ENDED" in ln:
            res["program_ended"] += 1
        if "BAD TERMINATION OF ONE OF YOUR APPLICATION PROCESSES" in ln:
            res["bad_termination"] += 1
        # 'EXIT CODE: 15'（MPI 收尾块）——允许任意空白，真实 .out 里是
        # '=   EXIT CODE: 15'。只认**收尾块**里的那一行，避免误吃别的文本。
        mex = re.search(r"\bEXIT CODE\s*:\s*(-?\d+)", ln)
        if mex:
            res["exit_code"] = int(mex.group(1))
        # 请求步数：CP2K 在 'MD| Molecular Dynamics Protocol' 里回显
        #   ' MD| Number of Time Steps        5000'          （旧版）
        #   ' MD_PAR| Number of time steps        20'        （2022.1，小写 + 换前缀）
        # 少认一种 ⇒ 完成度算不出来、"作业被 kill" 的处方会退化成"无法计算"。
        mreq = re.search(r"Number of [Tt]ime [Ss]teps\s+(\d+)", ln)
        if mreq:
            res["md_steps_requested"] = int(mreq.group(1))
        # 实际步数：旧版每步一行 ' STEP NUMBER  =  2534'
        mst = re.search(r"^\s*STEP NUMBER\s*=\s*(\d+)\s*$", ln)
        if mst:
            res["md_steps_done"] = max(res["md_steps_done"], int(mst.group(1)))
        else:
            # CP2K 2022.1 把它挪进 MD 块并改了措辞：' MD| Step number   1'
            # （少了它，`_is_md` 判据会失效 ⇒ 能量漂移检查**静默不跑**）
            mst2 = re.search(r"^\s*MD\|\s*Step number\s+(\d+)\s*$", ln)
            if mst2:
                res["md_steps_done"] = max(res["md_steps_done"], int(mst2.group(1)))
        if "MD step" in ln or "STEP" in ln and "ENSEMBLE" in ln:
            # rough MD step counter
            pass

        # ---- MD 系综 / 恒温器 / 目标温度（.out 头部回显）----
        # ⚠️ **跨版本换过前缀与措辞**（2026-10 真机实测发现，与能量行 `(a.u.)`→`[a.u.]`
        # 是同一类问题）。两种都要认，否则温度层会**一个数都取不到却不报错**：
        #     旧版（课程那批）              CP2K 2022.1
        #     MD| Ensemble Type   NVT       MD_PAR| Ensemble type            NVT
        #     MD| Temperature [K] 300.00    MD_PAR| Temperature [K]        300.000000
        #     THERMOSTAT| Type of thermostat  ...（同）
        _two = (r"([-+]?\d+(?:\.\d+)?(?:[eEdD][-+]?\d+)?)"
                r"\s+([-+]?\d+(?:\.\d+)?(?:[eEdD][-+]?\d+)?)")
        men = re.search(r"MD\|\s*Ensemble Type\s+(\S+)", ln)
        if men:
            res["ensemble"] = men.group(1)
        else:
            men3 = re.search(r"MD_PAR\|\s*Ensemble type\s+(\S+)", ln)
            if men3:
                res["ensemble"] = men3.group(1)
            elif res["ensemble"] is None:
                # 兜底：MD 步分隔块里的 ' ENSEMBLE TYPE =  NVT'
                men2 = re.search(r"ENSEMBLE TYPE\s*=\s*(\S+)", ln)
                if men2:
                    res["ensemble"] = men2.group(1)
        mth = re.search(r"THERMOSTAT\|\s*Type of thermostat\s+(.+?)\s*$", ln)
        if mth:
            res["thermostat"] = mth.group(1)
        # 🔴 顺序很关键：**先**判"两列的每步行"，**再**判"单值的目标温度回显"。
        # 否则 2022.1 的 `MD| Temperature [K]  349.34  349.34` 会被单值正则
        # 吃成"目标温度 = 349.34"，进而报出**假的**"温度偏离目标"告警。
        mtp2 = re.match(r"\s*MD\|\s*Temperature \[K\]\s+" + _two + r"\s*$", ln)
        if mtp2:
            res["temps"].append(_num(mtp2.group(1)))
            res["temps_avg"].append(_num(mtp2.group(2)))
        else:
            # 注意：只认 'MD| Temperature [K]' / 'MD_PAR| Temperature [K]'，
            # 不吃 'MD| Temperature tolerance [K]'（'[K]' 紧跟 Temperature），
            # 也不吃 'Electronic temperature [K]:'（小写且格式不同）。
            mtg = re.search(r"(?:MD\||MD_PAR\||MD_INI\||MD_VEL\|)\s*Temperature \[K\]"
                            r"\s+([-+]?\d+\.\d+)", ln)
            if mtg and res["temp_target"] is None:
                res["temp_target"] = float(mtg.group(1))

        # ---- 每 MD 步（旧版格式）：' TEMPERATURE [K] = <瞬时> <滑动平均>' ----
        # 只认等号 + 两个数：这样 ' INITIAL TEMPERATURE[K] = 300.000'（无空格、
        # 单列）与 'Electronic temperature [K]:'（小写）都不会被误吃。
        mtp = re.match(r"\s*TEMPERATURE \[K\]\s*=\s*" + _two, ln)
        if mtp:
            res["temps"].append(_num(mtp.group(1)))
            res["temps_avg"].append(_num(mtp.group(2)))
        # ---- 每 MD 步（2022.1）：' MD| Energy drift per atom [K] <瞬时> <平均>' ----
        mdp = re.match(r"\s*ENERGY DRIFT PER ATOM \[K\]\s*=\s*" + _two, ln)
        if not mdp:
            mdp = re.match(r"\s*MD\|\s*Energy drift per atom \[K\]\s+" + _two, ln)
        if mdp:
            res["drift_per_atom"].append(_num(mdp.group(1)))
            res["drift_per_atom_avg"].append(_num(mdp.group(2)))
        # imaginary frequency: CP2K prints negative cm^-1 for unstable modes.
        # handle "Frequency (cm^-1)   -123.45" (same line) and
        # "  1   -123.45   ..." (mode-number + value, multi-line CP2K format).
        mf = re.search(r"Frequency.*?(-?\d+\.\d+)", ln)
        if mf and float(mf.group(1)) < 0:
            res["imag_freqs"].append(float(mf.group(1)))
        mm = re.match(r"\s*\d+\s+(-?\d+\.\d+)", ln)
        if mm and float(mm.group(1)) < 0:
            res["imag_freqs"].append(float(mm.group(1)))

    # ---- 作业状态判定：正常结束 / 被 kill / 未知 ----
    killed = bool(res["bad_termination"]) or (
        res["exit_code"] is not None and res["exit_code"] != 0)
    if killed:
        res["run_status"] = "killed"
    elif res["program_ended"] and res["exit_code"] is None:
        res["run_status"] = "normal"
    elif res["program_ended"] and res["exit_code"] == 0:
        res["run_status"] = "normal"
    else:
        res["run_status"] = "unknown"

    if res["md_steps_requested"] and res["md_steps_done"]:
        res["completion_pct"] = 100.0 * res["md_steps_done"] / res["md_steps_requested"]
    return res


def job_status_finding(res):
    """作业是否跑完 —— 单独一条 finding（正常结束 / 被 kill / 未知）。

    为什么要有这一条：最容易误判的一类就是**作业被队列 kill 掉**。真实
    aimd `.out` 里没有 `PROGRAM ENDED`、尾部是 `EXIT CODE: 15` + `BAD
    TERMINATION OF ONE OF YOUR APPLICATION PROCESSES`，输入请求 5000 步、
    实际只跑到 2534 步（50.68%）—— 而早先的 diagnose 只报"SCF 未收敛 6 次"，
    半个字都没提作业被 kill，用户会以为算完了。
    """
    status = res.get("run_status", "unknown")
    n_done = res.get("md_steps_done") or 0
    n_req = res.get("md_steps_requested")
    pct = res.get("completion_pct")
    if pct is not None:
        progress = "实际跑到第 {} 步 / 请求 {} 步（完成度 {:.2f}%）".format(
            n_done, n_req, pct)
    elif n_done:
        progress = "实际跑到第 {} 步（.out 里没有回显请求步数，无法算完成度）".format(n_done)
    else:
        progress = "未检测到逐步 MD 记录（非 MD 作业，或输出被截断）"

    if status == "killed":
        why = []
        if res.get("bad_termination"):
            why.append("出现 {} 次 'BAD TERMINATION OF ONE OF YOUR APPLICATION "
                       "PROCESSES'".format(res["bad_termination"]))
        if res.get("exit_code") is not None:
            why.append("'EXIT CODE: {}'".format(res["exit_code"]))
        sug = (
            "**作业没有跑完，是被 kill 掉的**（"
            + ("；".join(why) if why else "检测到非 0 退出码") + "）。\n"
            "  " + progress + "\n"
            "  CP2K 自己没打印 'PROGRAM ENDED'，所以这不是正常收尾 —— 别把它当算完的结果用。\n"
            "  处方（按顺序做）：\n"
            "  ① 给 &GLOBAL 加 WALLTIME —— 取值比队列时限略小（如队列 24 h 就写 "
            "WALLTIME 82800 秒），让 CP2K 在批处理系统杀它之前**自己干净收尾**并写出重启文件：\n"
            "       gen_inp.py --walltime 82800 ...\n"
            "  ② 开 &RESTART_HISTORY（模板 &PRINT 下），按需设频率：\n"
            "       gen_inp.py --restart-freq 500 ...\n"
            "  ③ 确认重启文件真的落盘了（PROJECT-RESTART.wfn / PROJECT-1.restart，"
            "以及 -1.restart 的历史副本）；**没有重启文件就只能从头重算**。\n"
            "  ④ 续算：&GLOBAL 加 EXT_RESTART + &EXT_RESTART RESTART_FILE_NAME "
            "<PROJECT>-1.restart（SCF_GUESS RESTART），从断点接着跑剩余步数。\n"
            "  ⑤ 若经常被杀，同时考虑减小 TIMESTEP / 降 CUTOFF / 开 --smear 提高每步速度。"
        )
        return ("ERROR", "作业被 kill（未正常结束）", sug)
    if status == "normal":
        return (
            "INFO",
            "作业正常结束（PROGRAM ENDED）。",
            "{}。可以进入后处理：postprocess.py rdf/msd/diffusion …".format(progress),
        )
    return (
        "INFO",
        "作业结束状态未知（既没有 'PROGRAM ENDED'，也没有 'BAD TERMINATION' / "
        "非 0 'EXIT CODE'）。",
        "{}。常见原因：作业**仍在运行**（.out 正在被写）、输出被截断、或日志被裁剪过。"
        "请确认进程是否还活着；若已死，按「被 kill」的处方加 WALLTIME + "
        "RESTART_HISTORY 重跑。".format(progress),
    )


def diagnose(res, verbose=False):
    findings = []  # list of (severity, msg, suggestion)

    job_finding = job_status_finding(res)

    if res["fatal"]:
        findings.append((
            "ERROR",
            "计算被 ABORT：{}".format(res["fatal"][0][:120]),
            "先解决致命错误（通常是语法/内存/文件缺失），再谈收敛。看 ABORT 上方报错。",
        ))
        findings.append(job_finding)
        return findings  # 致命错误优先

    findings.append(job_finding)

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

    # ---- 🔴 原子力之和 ΣF ≠ 0：静默物理错误的**唯一可见症状** ----
    # 阈值 0.05 a.u.：实测合法算例落在 0.0002~0.0020，而"坏"的算例是 23~25，
    # 中间有三个数量级的安全带，不会误报。
    if res["sum_force"] is not None and abs(res["sum_force"]) > 0.05:
        findings.append((
            "WARN",
            "原子力之和 |ΣF| = {:.3f} a.u. —— **孤立体系必须为 0**（牛顿第三定律）。".format(
                abs(res["sum_force"])),
            "这几乎总意味着**静电能解错了**，而不是精度问题。最典型的成因：\n"
            "  ① **`POISSON_SOLVER WAVELET` 而分子没居中** —— 它要求「单胞边界处电子密度为 0」\n"
            "     （官方 T24 §3.4），分子横跨边界就会给出全错的力与能量。\n"
            "     修法：加 `&SUBSYS/&TOPOLOGY/&CENTER_COORDINATES`，或把坐标平移到盒子中心；\n"
            "     也可改用 `POISSON_SOLVER ANALYTIC` / `MT`。\n"
            "  ② 检查 `&CELL`/`&POISSON` 的 `PERIODIC` 是否与体系一致；\n"
            "  ③ 若体系本就有外场/约束（如 `&EFIELD`），ΣF 可以不为 0 —— 那种情况忽略本条。",
        ))
    # ⚠️ 作用域很重要（2026-10 真机实测踩到）：像 `VIBRATIONAL_ANALYSIS` 这类任务，
    # 每个能量来自**不同的位移构型**，能量本来就该不同 —— 把它们当"漂移"是**假阳性**。
    # 所以先判"这到底是不是一条 MD 轨迹"：
    #   * `md_steps_done > 0`（真的出现 STEP NUMBER）⇒ 是 MD，判漂移；
    #   * 否则若有多个能量 ⇒ 只报 INFO，并说明这些能量为什么不该比较。
    if len(res["energies"]) >= 3:
        emin, emax = min(res["energies"]), max(res["energies"])
        span = emax - emin
        rel = (span / emin) if abs(emin) > 1e-6 else None
        _is_md = res["md_steps_done"] > 0
        if _is_md and rel is not None and abs(rel) > 0.01:
            findings.append((
                "WARN",
                "能量跨度 {:.4f} a.u.（相对 {:.2%}），疑似 AIMD 能量漂移。".format(
                    span, span / emin),
                "建议：① 减小 TIMESTEP（模板 &MD TIMESTEP 0.5→0.25 fs）；② 查 NOSE "
                "thermostat TIMECON；③ 金属确认 --smear 已开；④ 看守恒量是否漂移。",
            ))
        elif _is_md and verbose:
            findings.append((
                "INFO",
                "能量跨度 {:.2e} a.u.，基本稳定。".format(span),
                "无需调整。",
            ))
        elif not _is_md:
            findings.append((
                "INFO",
                "{0} 个能量记录，跨度 {1:.4f} a.u. —— **这不是 MD 轨迹**（未见 STEP NUMBER），"
                "各能量来自不同构型（如频率分析的逐个位移、几何优化的逐帧），"
                "**跨度大是正常的，不能当能量漂移看**。".format(len(res["energies"]), span),
                "要判 AIMD 能量漂移请对着**同一条 MD 轨迹**的 .out/.ener 看；"
                "或直接看 CP2K 自报的 `ENERGY DRIFT PER ATOM [K]`。",
            ))

    # ---- 温度漂移 / 失控 / 恒温器耦合（MD）----
    # 阈值用真实算例标定：NVT Nose-Hoover 目标 300 K 跑 2534 步，
    # 瞬时温度 179–370 K（峰值 1.23×目标）、末段平均 290.8 K（偏 3.1%）、
    # 守恒量漂移 0.80 K/原子 —— 三项都不该报 WARN。
    if res["temps"]:
        tgt = res["temp_target"]
        tmax = max(res["temps"])
        tmin = min(res["temps"])
        t_end = res["temps_avg"][-1]
        ens = (res["ensemble"] or "?").upper()
        therm = res["thermostat"] or "（.out 未回显）"

        if tgt and tmax > 1.5 * tgt:
            findings.append((
                "WARN",
                "温度失控：最高瞬时温度 {:.1f} K，超过目标 {:.0f} K 的 1.5 倍"
                "（系综 {}，恒温器 {}）。".format(tmax, tgt, ens, therm),
                "处方：① 先把 TIMESTEP 减半（0.5→0.25 fs）重跑；"
                "② 恒温器 TIMECON 过长会压不住，缩到 20–50 fs；"
                "③ 确认初始结构已预优化（未优化结构会瞬间放热）；"
                "④ 同步看下方「守恒量漂移」是否一起变差。",
            ))
        elif tgt and abs(t_end - tgt) > 0.2 * tgt:
            findings.append((
                "WARN",
                "平均温度 {:.1f} K 偏离目标 {:.0f} K 达 {:.1%}"
                "（系综 {}，恒温器 {}）。".format(
                    t_end, tgt, abs(t_end - tgt) / tgt, ens, therm),
                "处方：NVT 下平均温度应收敛到目标。偏离 >20% 通常是"
                "① 步数太少还没平衡（丢掉前 20% 平衡段再统计平均值）；"
                "② 恒温器 TIMECON 太长（耦合太弱）；"
                "③ 系综其实是 NVE（NVE 不控温，温度本来就会漂）。",
            ))
        elif verbose:
            findings.append((
                "INFO",
                "温度：瞬时 {:.1f}–{:.1f} K，末段平均 {:.1f} K（目标 {}）。".format(
                    tmin, tmax, t_end,
                    "{:.0f} K".format(tgt) if tgt else "未回显"),
                "系综 {}，恒温器 {}。".format(ens, therm),
            ))

        # CP2K 自报的守恒量漂移 —— AIMD 最硬的健康指标，不用自己估。
        if res["drift_per_atom_avg"]:
            d = res["drift_per_atom_avg"][-1]
            if abs(d) > 10.0:
                findings.append((
                    "WARN",
                    "守恒量漂移 {:.2f} K/原子（CP2K 自报 ENERGY DRIFT PER ATOM "
                    "的滑动平均）。".format(d),
                    "处方：>10 K/原子说明积分不稳：① 减小 TIMESTEP；"
                    "② 收紧 SCF（EPS_SCF 1e-6）；③ 确认 &QS EPS_DEFAULT 未被放宽；"
                    "④ 金属体系确认 SMEAR 已开。",
                ))
            elif abs(d) > 1.0 or verbose:
                findings.append((
                    "INFO",
                    "守恒量漂移 {:.2f} K/原子（滑动平均），在可接受范围。".format(d),
                    ">10 K/原子才需要动手；<1 K/原子是健康水平。",
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
    ap.add_argument("--json", action="store_true", help="输出 JSON（给 agent 用）")
    args = ap.parse_args()

    try:
        text = open(args.out, encoding="utf-8", errors="replace").read()
    except FileNotFoundError:
        if args.json:
            import json
            print(json.dumps({"ok": False, "file": args.out,
                              "error": "找不到文件"},
                             ensure_ascii=False, indent=2))
            sys.exit(1)
        print("\n[ERROR] 找不到文件: {}".format(args.out), file=sys.stderr)
        print("  请检查路径；诊断需要 CP2K 的 .out 输出文件。", file=sys.stderr)
        print("  如果还没跑过 CP2K，先照 examples/01_si_bulk_static/ 跑通一个最小例子。",
              file=sys.stderr)
        sys.exit(1)
    except IsADirectoryError:
        print("\n[ERROR] 给的是目录，不是 .out 文件: {}".format(args.out),
              file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print("\n[ERROR] 无权限读取: {}".format(args.out), file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print("\n[ERROR] 无法读取 {}: {}".format(args.out, e), file=sys.stderr)
        sys.exit(1)

    res = parse(text)
    findings = diagnose(res, verbose=args.verbose)

    if args.json:
        import json
        print(json.dumps({
            "ok": True,
            "file": args.out,
            "findings": [{"severity": s, "message": m, "suggestion": sug}
                         for s, m, sug in findings],
            "stats": {
                "scf_converged": res["scf_converged"],
                "scf_not_converged": res["scf_not_converged"],
                "reached_max_scf": res["reached_max_scf"],
                "geo_done": res["geo_done"],
                "geo_not": res["geo_not"],
                "max_force_last": res["max_force_last"],
                "n_energies": len(res["energies"]),
                "has_kpoints": res["has_kpoints"],
                "has_smear": res["has_smear"],
                "n_imag_freqs": len(res["imag_freqs"]),
                # --- 新增（既有键一个都没删/没改名）---
                "run_status": res["run_status"],
                "program_ended": res["program_ended"],
                "bad_termination": res["bad_termination"],
                "exit_code": res["exit_code"],
                "md_steps_requested": res["md_steps_requested"],
                "md_steps_done": res["md_steps_done"],
                "completion_pct": res["completion_pct"],
                # --- MD 温度层（新增）---
                "ensemble": res["ensemble"],
                "thermostat": res["thermostat"],
                "temperature_target": res["temp_target"],
                "temperature_max": (max(res["temps"]) if res["temps"] else None),
                "temperature_final_avg": (res["temps_avg"][-1]
                                          if res["temps_avg"] else None),
                "energy_drift_per_atom_avg": (res["drift_per_atom_avg"][-1]
                                              if res["drift_per_atom_avg"] else None),
            },
        }, ensure_ascii=False, indent=2))
        return

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
        print("  末步最大力/梯度: {:.4e} a.u./bohr".format(res["max_force_last"]))
    print("  能量采样点: {} 个".format(len(res["energies"])))
    print("  含 k 点: {} / 含 SMEAR: {}".format(res["has_kpoints"], res["has_smear"]))
    print("  虚频: {} 个".format(len(res["imag_freqs"])))
    # ---- MD 温度层（系综 / 恒温器 / 温度漂移 / 守恒量漂移）----
    if res["temps"]:
        _tgt = ("{:.1f} K".format(res["temp_target"])
                if res["temp_target"] is not None else "未回显")
        print("  MD 温度: 瞬时 {:.1f}–{:.1f} K | 末段平均 {:.1f} K | 目标 {}".format(
            min(res["temps"]), max(res["temps"]), res["temps_avg"][-1], _tgt))
        print("    系综: {} | 恒温器: {}".format(
            res["ensemble"] or "未回显", res["thermostat"] or "未回显"))
    if res["drift_per_atom_avg"]:
        print("  守恒量漂移: {:.3f} K/原子（滑动平均，CP2K 自报）".format(
            res["drift_per_atom_avg"][-1]))
    # ---- 作业是否跑完（三种状态分开报）----
    _status_zh = {"normal": "正常结束", "killed": "被 kill", "unknown": "未知"}
    print("  作业状态: {}".format(_status_zh.get(res["run_status"], "未知")))
    print("    PROGRAM ENDED: {} 次 | BAD TERMINATION: {} 次 | EXIT CODE: {}".format(
        res["program_ended"], res["bad_termination"],
        res["exit_code"] if res["exit_code"] is not None else "（无）"))
    if res["md_steps_requested"] is not None or res["md_steps_done"]:
        _pct = ("{:.2f}%".format(res["completion_pct"])
                if res["completion_pct"] is not None else "无法计算（.out 未回显请求步数）")
        print("    MD 步数: 实际 {} / 请求 {} | 完成度 {}".format(
            res["md_steps_done"],
            res["md_steps_requested"] if res["md_steps_requested"] is not None else "?",
            _pct))


if __name__ == "__main__":
    main()
