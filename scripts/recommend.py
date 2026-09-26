#!/usr/bin/env python3
"""CP2K 参数推荐引擎 —— skill 的"思考层"第一部分。

给定体系描述（元素 / 周期 / 电荷 / 自旋 / 目标 / 精度 / 是否吸附），输出：
  1) 推荐的泛函 / 基组 / 赝势 / 自旋 / 色散 / k 点 / SMEAR / CUTOFF 等参数；
  2) 每一项选择的"理由"（为什么这样选）；
  3) 一个"从 0 到收敛"的起步阶梯（sanity → 生产 → 精修）；
  4) 一条可直接执行的 gen_inp.py 命令（已按元素逐个填好基组/赝势/q）。

设计哲学：默认值只是"安全起点假设"，不是定律。本脚本把一位资深计算化学家对
新体系的判断过程固化成可执行的启发式规则；具体取舍仍由使用者带判断确认。

注意：脚本依赖你给出的体系描述。它不能"理解"一个全新分子的电子结构，
只能根据元素组成、周期性、目标等信息做有理由的推荐。

Usage:
  python recommend.py --elements Au O --goal geo_opt --periodic xy \
      --multiplicity 3 --vdw auto --accuracy balanced

  # 输出可直接执行的 gen_inp.py 命令；加 --json 可导出结构化结果。
"""
import argparse
import json
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

# ---------------------------------------------------------------------------
# 元素知识表
#   sym -> (is_metal, default_basis, default_potential(q), note)
#   is_metal: 需要 GTH-PBE/MOLOPT（过渡金属、镧锕系、后过渡 Tl/Pb/Bi）
#   其余主族/轻元素用 GTH-PADE/DZVP-GTH-PADE
#   q = GTH 赝势价电子数（常用值；不确定时令 q=None，提示用户核对）
# ---------------------------------------------------------------------------
METAL_BASIS = "DZVP-MOLOPT-SR-GTH"
METAL_POT = "GTH-PBE"
LIGHT_BASIS = "DZVP-GTH-PADE"
LIGHT_POT = "GTH-PADE"

# (is_metal, q_for_GTH-PADE_or_GTH-PBE, note)
ELEMENTS = {
    # 轻元素 / 主族（GTH-PADE）
    "H":  (False, 1,  "轻元素"),
    "He": (False, 2,  ""),
    "Li": (False, 1,  ""),
    "Be": (False, 2,  ""),
    "B":  (False, 3,  ""),
    "C":  (False, 4,  "有机/碳材料"),
    "N":  (False, 5,  "含氮官能团/氮化物"),
    "O":  (False, 6,  "氧化物/含氧吸附"),
    "F":  (False, 7,  ""),
    "Ne": (False, 8,  ""),
    "Na": (False, 1,  ""),
    "Mg": (False, 2,  ""),
    "Al": (False, 3,  ""),
    "Si": (False, 4,  "半导体/硅"),
    "P":  (False, 5,  ""),
    "S":  (False, 6,  "含硫"),
    "Cl": (False, 7,  "卤素"),
    "Ar": (False, 8,  ""),
    "K":  (False, 1,  ""),
    "Ca": (False, 2,  ""),
    "Ga": (False, 13, "重主族，精度要求高时可用 MOLOPT"),
    "Ge": (False, 4,  "重主族"),
    "As": (False, 5,  ""),
    "Se": (False, 6,  ""),
    "Br": (False, 7,  "卤素"),
    "Kr": (False, 8,  ""),
    # 过渡金属 / 镧锕系 / 后过渡（GTH-PBE / MOLOPT）
    "Sc": (True, 11, "3d"), "Ti": (True, 12, "3d"), "V":  (True, 13, "3d"),
    "Cr": (True, 6,  "3d（常用 q6；高自旋可 q14）"),
    "Mn": (True, 7,  "3d"),
    "Fe": (True, 16, "3d 磁性，常需 UKS"),
    "Co": (True, 17, "3d 磁性"),
    "Ni": (True, 18, "3d 磁性"),
    "Cu": (True, 11, "3d"), "Zn": (True, 12, "3d"),
    "Y":  (True, 11, "4d"), "Zr": (True, 12, "4d"), "Nb": (True, 13, "4d"),
    "Mo": (True, 6,  "4d"), "Tc": (True, 7,  "4d"), "Ru": (True, 16, "4d 贵金属"),
    "Rh": (True, 17, "4d 贵金属"), "Pd": (True, 10, "4d 贵金属"),
    "Ag": (True, 11, "4d"), "Cd": (True, 12, "4d"),
    "Hf": (True, 12, "5d"), "Ta": (True, 13, "5d"), "W":  (True, 14, "5d"),
    "Re": (True, 7,  "5d"), "Os": (True, 16, "5d 贵金属"),
    "Ir": (True, 17, "5d 贵金属"), "Pt": (True, 10, "5d 贵金属"),
    "Au": (True, 11, "5d 贵金属，催化常用"),
    "Hg": (True, 12, "5d"),
    "Tl": (True, 13, "后过渡"), "Pb": (True, 14, "后过渡"),
    "Bi": (True, 15, "后过渡"),
    # 镧系（示例，常用 MOLOPT + 高 q）
    "La": (True, 11, "镧系"), "Ce": (True, 12, "镧系"), "Gd": (True, 15, "镧系"),
    "Lu": (True, 11, "镧系"),
}

# 常见"磁性"元素（大概率需要自旋极化 UKS）
MAGNETIC = {"Fe", "Co", "Ni", "Mn", "Cr", "V", "Ti", "Ru", "Os", "Rh", "Ir",
            "Cu", "Pd", "Pt", "Gd", "Ce", "La"}

# 含这些元素的体系几乎一定有弱作用（分子/吸附/层间），默认开 DFT-D3
VDW_ELEMENTS = {"H", "C", "N", "O", "F", "S", "Cl", "P", "Br", "I",
                "Se", "As", "B", "Si"}  # 出现非纯金属体系时即建议 D3

# 常见强关联过渡金属：建议 DFT+U 的起始 U_MINUS_J(eV)（PBE+U / Dudarev 惯例）。
# 仅是起步值，必须用文献或线性响应法标定；不同材料/泛函差异很大。
PLUS_U_DEFAULTS = {
    "Ti": (4.0, "3d 局域化"), "V": (4.0, "3d"), "Cr": (3.5, "3d"),
    "Mn": (4.0, "3d"), "Fe": (4.0, "3d 磁性"), "Co": (3.5, "3d"),
    "Ni": (6.0, "3d"), "Cu": (5.0, "3d"),
    "La": (6.0, "4f"), "Ce": (5.0, "4f"),
}
# 与强关联金属形成氧化物/硫化物等局域化体系时，DFT+U 尤其必要
CORRELATOR_ANIONS = {"O", "S", "Se", "Te", "P", "As"}


def el_info(sym):
    sym = sym.strip().title()
    if sym not in ELEMENTS:
        return None
    is_metal, q, note = ELEMENTS[sym]
    if is_metal:
        basis = METAL_BASIS
        pot = "{}-q{}".format(METAL_POT, q) if q else "{} (q?)".format(METAL_POT)
    else:
        basis = LIGHT_BASIS
        pot = "{}-q{}".format(LIGHT_POT, q) if q else "{} (q?)".format(LIGHT_POT)
    return {"sym": sym, "is_metal": is_metal, "q": q, "basis": basis,
            "pot": pot, "note": note}


def recommend(args):
    """Return a dict with the full recommendation + reasoning + ladder + command."""
    elems = [e.strip().title() for e in args.elements]
    infos = [el_info(e) for e in elems]
    unknown = [e for e, i in zip(elems, infos) if i is None]
    infos = [i for i in infos if i]
    if not infos:
        sys.exit("ERROR: 无法识别任何元素: {}".format(", ".join(args.elements)))

    metals = [i for i in infos if i["is_metal"]]
    has_metal = bool(metals)
    any_magnetic = any(i["sym"] in MAGNETIC for i in infos)

    reasoning = []
    rec = {"elements": elems}

    # ---- 泛函 ----
    func = args.functional
    if func is None:
        func = "PADE"  # = PBE，性价比首选
        reasoning.append(
            "泛函: 默认 PBE(=PADE) 做结构优化/筛选 —— 便宜、对结构/力学量可靠。"
            "若目标是反应能、吸附能、能带隙，建议最后用 HSE06/B3LYP 精修（见阶梯）。"
        )
    else:
        meta_gga = func in ("TPSS", "SCAN")
        is_hybrid = func in ("HSE06", "B3LYP")
        if meta_gga:
            reasoning.append(
                "泛函: {} 是 Meta-GGA 泛函，精度介于 PBE 和 HSE06 之间。".format(func) +
                "对表面吸附能、分子间作用力、弱化学键的描述优于 PBE，"
                "价格只比 PBE 贵约 1.5-2x（vs HSE06 的 5-20x）。"
                "适合需要'比 PBE 好但不想上杂化'的场景。"
            )
        elif is_hybrid:
            reasoning.append(
                "泛函: {} 为杂化泛函，含精确交换，反应能/带隙更准，".format(func) +
                "但贵 5-20x。建议加 --admm（降本 3-5x）+ --outer-scf（助收敛）。"
            )
        else:
            reasoning.append(
                "泛函: 按你的指定用 {}（PBE/PADE 是 GGA 泛函，性价比最高）。".format(func)
            )
    rec["functional"] = func
    outer_scf = (func in ("HSE06", "B3LYP"))

    # ---- 基组 / 赝势（逐元素）----
    basis_list, pot_list = [], []
    for i in infos:
        basis_list.append(i["basis"])
        pot_list.append(i["pot"])
        tag = "过渡金属" if i["is_metal"] else "轻/主族元素"
        reasoning.append(
            "基组/赝势 [{} {}]: {} / {}  (q={}{})".format(
                tag, i["sym"], i["basis"], i["pot"], i["q"],
                "，注意核对价电子数" if i["q"] is None else "")
        )
    rec["basis"] = basis_list
    rec["potential"] = pot_list

    # ---- 自旋 ----
    mult = args.multiplicity
    if mult and mult > 0:
        reasoning.append(
            "自旋: --multiplicity {} → 开 UKS（限制/非限制自旋极化）。"
            "开壳层（O₂、自由基、多数吸附态）必须开。".format(mult)
        )
    elif any_magnetic:
        reasoning.append(
            "自旋: 体系含磁性元素({})，大概率需要自旋极化。若未指定多重度，"
            "建议先试 UKS：铁磁 Fe 体相 → --multiplicity 3；其他按磁矩/磁序定。"
            "（本推荐未强制开启，请据磁态判断）".format(
                "/".join(sorted({i["sym"] for i in infos if i["sym"] in MAGNETIC})))
        )
        mult = 0
    else:
        reasoning.append("自旋: 闭壳层，默认不开 UKS（--multiplicity 0）。")
    rec["multiplicity"] = mult

    # ---- 色散 DFT-D3 ----
    if args.vdw == "yes" or (args.vdw == "auto" and (set(elems) & VDW_ELEMENTS)):
        vdw = True
        reasoning.append(
            "色散: 开 DFT-D3（&VDW_POTENTIAL）。体系含分子/吸附质/层状结构，"
            "弱作用显著影响几何与能量；D3 便宜且风险低。需把 dftd3.dat 放运行目录。"
        )
    else:
        vdw = False
        reasoning.append("色散: 暂不开 DFT-D3（纯金属块体/离子晶体，弱作用贡献小）。")
    rec["vdw"] = vdw

    # ---- 周期性 / POISSON / k 点 ----
    periodic = args.periodic
    if periodic == "none":
        reasoning.append(
            "周期: 非周期（孤立分子/团簇）→ POISSON WAVELET，给大盒子包住分子即可。"
        )
        kpoints = None
    else:
        reasoning.append(
            "周期: {}。表面 slab 用 xy（z 非周期）；块体用 xyz。".format(periodic)
        )
        if has_metal:
            if periodic == "xy":
                kpoints = "4 4 1"
            else:
                kpoints = "6 6 6" if args.accuracy != "fast" else "3 3 3"
            reasoning.append(
                "k 点: 含金属，费米面需采样 → KPOINTS MONKHORST-PACK {}。"
                "绝缘体可用 GAMMA 单点，但金属必须多 k 点否则能带/能量错误。".format(kpoints)
            )
        else:
            kpoints = None
            reasoning.append(
                "k 点: 非金属块体/表面，GAMMA 中心点通常够用；若后续发现能带相关量异常再加。"
            )
    rec["periodic"] = periodic
    rec["kpoints"] = kpoints

    # ---- SMEAR（金属）----
    if has_metal and periodic != "none":
        smear = True
        reasoning.append(
            "SMEAR: 金属/窄带隙 → 开 FERMI_DIRAC 300K，避免 SCF 在费米面附近抖动不收敛。"
            "同时自动配 SCF 精细调参：提高 CUTOFF、MAX_SCF 500、EPS_SCF 1e-6、"
            "EPS_DIIS 0.05、ADDED_MOS 500、CHOLESKY INVERSE、"
            "BROYDEN(ALPHA 0.1 / BETA 1.5 / NBROYDEN 8)、DIAGONALIZATION EPS_ADAPT 0.01"
            "（复刻 nico 等金属体系经验设置，确保收敛）。续算可加 --scf-guess RESTART "
            "--wfn-restart ./cp2k-RESTART.wfn。"
        )
    else:
        smear = False
        if args.smear:
            smear = True
            reasoning.append("SMEAR: 按你的指定强制开启。")
    rec["smear"] = smear

    # ---- CUTOFF ----
    if has_metal:
        cutoff = 500 if args.accuracy == "accurate" else 400
    elif any(i["sym"] in {"Ga", "Ge", "As", "Se", "Br", "Tl", "Pb", "Bi"} for i in infos):
        cutoff = 400 if args.accuracy == "accurate" else 350
    else:
        cutoff = 400 if args.accuracy == "accurate" else 300
    reasoning.append(
        "CUTOFF: {} Ry（{}精度）。重元素/金属需更高截断；收敛后可测 CUTOFF 收敛性再定。".format(
            cutoff, args.accuracy)
    )
    rec["cutoff"] = cutoff


    # ---- ADMM (hybrid functionals) ----
    use_admm = func in ("HSE06", "B3LYP")
    rec["admm"] = use_admm
    if use_admm:
        reasoning.append(
            "ADMM: 杂化泛函自动推荐开启 --admm（辅助密度矩阵法）。"
            "ADMM 用 cFIT 辅助基组计算精确交换部分，成本降低 3-5x，"
            "对 >50 原子的体系几乎是必须的。精度损失通常 <0.01 eV。"
        )

    # ---- Properties output ----
    props = []
    goal = args.goal
    # Recommend PDOS for surface/catalysis systems
    if goal in ("energy", "geo_opt", "cell_opt") and has_metal:
        props.append("pdos")
        reasoning.append(
            "Properties: 推荐 --properties pdos（投影态密度）。"
            "金属/半导体体系的电子结构分析几乎总需要 PDOS：看 d-band center、"
            "费米面附近态密度、元素贡献分解。"
        )
    # Recommend BAND for bulk semiconductors/metals
    if goal == "energy" and periodic != "none" and not any_magnetic:
        # Only suggest band structure for non-magnetic bulk
        pass  # Don't auto-add; user can request
    if args.properties:
        props = list(args.properties)
        reasoning.append("Properties: 按你的指定添加 {}。".format(" ".join(props)))
    rec["properties"] = props

    # ---- Thermostat (MD only) ----
    if goal == "md":
        ens = args.ensemble or "nvt"
        rec["ensemble"] = ens
        if ens == "nve":
            # NVE = 微正则（N/V/E 恒定）——**按定义不控温**，&THERMOSTAT 不起作用。
            # 这条必须显式讲：CP2K 的 &MD ENSEMBLE **官方默认就是 NVE**，
            # 所以"忘了写系综"会静默变成不控温的跑法。
            rec["thermostat"] = None
            _msg = ("恒温器: 系综选了 **NVE**（微正则，N/V/E 恒定）—— 按定义**没有恒温器**，"
                    "写 &THERMOSTAT 也不起作用；温度会自由漂移。NVE 只适合做能量守恒/"
                    "守恒量检查，要控温请用 --ensemble nvt。"
                    "（注意 CP2K 的 &MD ENSEMBLE **官方默认就是 NVE**，不写系综 = 不控温。）")
            if args.thermostat:
                _msg += " 你显式给的 --thermostat {} 在 NVE 下会被忽略。".format(args.thermostat)
            reasoning.append(_msg)
        else:
            thermo = args.thermostat or "csvr"
            if has_metal and thermo == "csvr":
                thermo = "langevin"
                reasoning.append(
                    "恒温器: MD 含金属表面 -> 推荐 Langevin 恒温器（--thermostat langevin）。"
                    "Langevin 对表面催化体系温度控制更稳定；CSVR/Nose 在金属表面易过热。"
                )
            else:
                reasoning.append(
                    "恒温器: {} ({} 系综)。".format(
                        thermo.upper(),
                        {"nve": "微正则", "nvt": "正则", "npt": "等压等温"}.get(ens, "NVT")
                    )
                )
            rec["thermostat"] = thermo

        # ---- TIMESTEP：原先**完全不推荐**，而它恰恰是 AIMD 最有后果的参数 ----
        # 口径与 gen_inp.py --timestep 的帮助文本严格一致（模板默认 0.5 fs）：
        #   「AIMD 一般 0.5–1.0 fs；超过 ~2 fs 要检查能量守恒/漂移」，
        #   「含氢体系 O–H 振动周期约 10 fs，经验上限 1/10（1 fs）、常态 1/20（0.5 fs）」。
        _has_h = any(i["sym"] == "H" for i in infos)
        if args.timestep is not None:
            ts = args.timestep
            reasoning.append(
                "TIMESTEP: 按你的指定 {} fs（gen_inp.py --timestep {}）。".format(ts, ts))
        elif _has_h:
            ts = 0.5
            reasoning.append(
                "TIMESTEP: 含氢 -> 0.5 fs。含氢体系有最快的振动（O–H 周期约 10 fs，"
                "3300 cm^-1），经验上限是周期的 1/10（1 fs）、文献常态是 1/20（0.5 fs）。"
                "要放宽到 >1 fs 必须先 --deuterate（O–D 降到约 2500 cm^-1）"
                "或先做能量守恒测试。"
            )
        else:
            ts = 1.0
            reasoning.append(
                "TIMESTEP: 不含氢（没有最快的 X–H 振动）-> 可放宽到 1.0 fs。"
                "AIMD 一般取 0.5–1.0 fs；重原子慢振动体系（如 TiO2）生产上见过 2 fs，"
                "但**必须**先确认守恒量不漂（用 diagnose.py 看 ENERGY DRIFT PER ATOM）。"
            )
        rec["timestep"] = ts
    if outer_scf:
        reasoning.append("OUTER_SCF: 杂化泛函难收敛 → 自动加 --outer-scf。")

    # ---- DFT+U (strongly correlated TM) ----
    plus_u = False
    kind_specs = []
    u_elems = [i for i in infos if i["sym"] in PLUS_U_DEFAULTS]
    has_correlator = bool(CORRELATOR_ANIONS & set(elems))
    if u_elems and goal in ("energy", "geo_opt", "cell_opt", "md") and not use_admm:
        if args.plus_u == "yes" or (args.plus_u == "auto" and has_correlator):
            plus_u = True
            rec["plus_u"] = {i["sym"]: PLUS_U_DEFAULTS[i["sym"]][0] for i in u_elems}
            reasoning.append(
                "DFT+U: 体系含强关联过渡金属({})且为氧化物/硫属化物等局域化体系，"
                "其 d/f 轨道高度局域，纯 PBE 会错误离域（金属性/磁矩失真）。"
                "建议对每个相关元素加 U（&DFT_PLUS_U），由 gen_inp.py --kinds 发射；"
                "PLUS_U_METHOD MULLIKEN 自动注入 &DFT。起点 U_MINUS_J(eV): {}。"
                "注意：U 必须用文献值或线性响应法标定，这里只是起步值"
                "（不同元素位点若自旋不同，再手动给各 &KIND 加 mag=）。".format(
                    "/".join(sorted(rec["plus_u"])),
                    ", ".join("{}={}".format(k, v) for k, v in rec["plus_u"].items()))
            )
            for i in infos:
                spec = "{}:{}:{}".format(i["sym"], i["basis"], i["pot"])
                if i["sym"] in PLUS_U_DEFAULTS:
                    spec += ":U={}".format(PLUS_U_DEFAULTS[i["sym"]][0])
                kind_specs.append(spec)
    rec["plus_u_on"] = plus_u
    rec["kinds"] = kind_specs

    # ---- 起步阶梯 ----
    ladder = build_ladder(elems, args.goal, func, has_metal, vdw, any_magnetic, cutoff, kpoints)

    # ---- 生成命令 ----
    # MD 的恒温器/系综/步长必须一路带到命令里，否则"理由"与"命令"会不一致。
    _md = None
    if goal == "md":
        _md = {"thermostat": rec.get("thermostat"),
               "ensemble": rec.get("ensemble"),
               "timestep": rec.get("timestep")}
    cmd = build_command(args, elems, basis_list, pot_list, func, mult, vdw,
                         periodic, kpoints, smear, outer_scf, cutoff,
                         plus_u, kind_specs, _md)

    rec["ladder"] = ladder
    rec["command"] = cmd
    rec["unknown_elements"] = unknown
    rec["reasoning"] = reasoning
    return rec


def build_ladder(elems, goal, func, has_metal, vdw, any_magnetic, cutoff, kpoints):
    """给出一个'从 0 到收敛'的渐进式计算计划。"""
    goal_cn = {
        "energy": "单点能", "geo_opt": "几何优化", "cell_opt": "晶胞优化",
        "md": "AIMD/分子动力学", "neb": "NEB 过渡态", "vib": "振动分析",
        "ts": "过渡态(Dimer)",
    }.get(goal, goal)
    L = []
    L.append("【起步阶梯 · 目标={}】".format(goal_cn))
    L.append("  ① 结构 sanity（最便宜）: 用上面推荐命令先跑一次；"
             "大 slab 先 --fixed-atoms 冻底层，只放对吸附质/表层，快速看是否报错/崩。"
             "重点确认：SCF 能收敛、初始力方向合理、没 NaN。")
    L.append("  ② 生产级优化: 确认 sanity 后，收紧 CUTOFF 到 {} Ry，"
             "MAX_FORCE 6e-4，按需要开 --dispersion/--multiplicity；"
             "金属加 --smear{}。得到可信的平衡结构/能量。".format(
                 cutoff, " + KPOINTS {}".format(kpoints) if kpoints else ""))
    if func in ("HSE06", "B3LYP"):
        L.append("  ③ 精修(已选杂化泛函): 在 PBE 优化结构上做 {} 单点能，"
                 "拿准确反应能/吸附能/带隙。".format(func))
    else:
        L.append("  ③ 精修(可选): 在优化结构上用 --functional HSE06 做单点能，"
                 "校正反应能/带隙；或 --type vib 确认是极小点(无虚频)还是过渡态(唯一虚频)。")
    if goal in ("neb", "ts"):
        L.append("  ③' 过渡态: NEB 收敛后看反应能垒；或用 Dimer 法（只需初态）交叉验证鞍点。")
    L.append("  ④ 收尾: 用 parse_output.py 取能量/力/收敛，用 diagnose.py 看是否要调参；"
             "后处理见 postprocess.md（IR/PDOS/轨迹/电荷）。")
    return L


def build_command(args, elems, basis_list, pot_list, func, mult, vdw,
                  periodic, kpoints, smear, outer_scf, cutoff,
                  plus_u=False, kind_specs=None, md=None):
    """拼出一条可直接执行的 gen_inp.py 命令。

    当 plus_u 触发时，用 --kinds 取代 --elem/--basis/--potential（逐原子 &KIND
    同时携带 DFT+U 的 U= 设定），否则保持逐元素三参数写法。

    `md` 是 MD 分支**解析后**的推荐值 {thermostat, ensemble, timestep}。
    必须传进来：早先这三项只出现在"选择理由"里、从不进入命令，于是
    **建议说"推荐 Langevin"，生成的命令却会用 gen_inp.py 的默认 csvr**
    —— 建议与实际输入静默不一致。默认值（csvr / nvt）仍不写，保持命令干净。
    """
    parts = ["python gen_inp.py"]
    # 目标 -> gen_inp.py 的 --type（goal 用领域名，type 用 gen_inp.py 枚举）
    _type_map = {"energy": "static", "md": "aimd_md", "ts": "geo_opt"}
    _ptype = _type_map.get(args.goal, args.goal)
    parts.append("--type {}".format(_ptype))
    parts.append("--project {}".format(args.project))
    if plus_u and kind_specs:
        parts.append("--kinds " + " ".join('"{}"'.format(s) for s in kind_specs))
        parts.append("--plus-u-method MULLIKEN")
    else:
        parts.append("--elem " + " ".join(elems))
        parts.append("--basis " + " ".join(basis_list))
        parts.append("--potential " + " ".join(pot_list))
    if func != "PADE":
        parts.append("--functional {}".format(func))
    if mult and mult > 0:
        parts.append("--multiplicity {}".format(mult))
    if vdw:
        parts.append("--dispersion")
    if periodic != "xyz":
        parts.append("--periodic {}".format(periodic))
    if kpoints:
        parts.append('--kpoints "{}"'.format(kpoints))
    if smear:
        parts.append("--smear")
    if outer_scf:
        parts.append("--outer-scf")
    if args.charge:
        parts.append("--charge {}".format(args.charge))
    if args.fixed_atoms:
        parts.append('--fixed-atoms "{}"'.format(args.fixed_atoms))
    parts.append("--cell " + " ".join(str(x) for x in args.cell))
    # ---- 金属体系 SCF 精细调参（复刻 nico 等经验设置，保证收敛）----
    if smear:
        parts.append("--cutoff {}".format(cutoff))
        parts.append("--eps-scf 1.0E-6")
        parts.append("--max-scf 500")
        parts.append("--eps-diis 0.05")
        parts.append("--added-mos 500")
        parts.append("--cholesky INVERSE")
        parts.append("--mixing-alpha 0.1")
        parts.append("--mixing-beta 1.5")
        parts.append("--mixing-nbroyden 8")
        parts.append("--diagonalization-eps-adapt 0.01")
    # ---- MD 三件套：恒温器 / 系综 / TIMESTEP（默认值不写，保持命令干净）----
    if md:
        if md.get("thermostat") and md["thermostat"] != "csvr":
            parts.append("--thermostat {}".format(md["thermostat"]))
        if md.get("ensemble") and md["ensemble"] != "nvt":
            parts.append("--ensemble {}".format(md["ensemble"]))
        if md.get("timestep") is not None:
            parts.append("--timestep {}".format(md["timestep"]))
    # 坐标：NEB 用 --xyz-init/--xyz-final 或 --xyz-replicas，其余用 --xyz
    if args.goal == "neb":
        if args.xyz_replicas:
            parts.append("--xyz-replicas " + " ".join(args.xyz_replicas))
        else:
            if args.xyz_init:
                parts.append("--xyz-init {}".format(args.xyz_init))
            if args.xyz_final:
                parts.append("--xyz-final {}".format(args.xyz_final))
        # NEB 进阶开关
        if args.optimize_band != "MD":
            parts.append("--optimize-band {}".format(args.optimize_band))
        if args.optimize_end_points != "T":
            parts.append("--optimize-end-points {}".format(args.optimize_end_points))
        if args.align_frames != "T":
            parts.append("--align-frames {}".format(args.align_frames))
        if args.rotate_frames != "F":
            parts.append("--rotate-frames {}".format(args.rotate_frames))
        if abs(args.k_spring - 0.02) > 1e-9:
            parts.append("--k-spring {}".format(args.k_spring))
        if args.program_run_info:
            parts.append("--program-run-info")
        if args.convergence_info:
            parts.append("--convergence-info")
    elif args.xyz:
        parts.append("--xyz {}".format(args.xyz))
    else:
        parts.append("--xyz <结构.xyz>")
    parts.append("-o {}.inp".format(args.project))
    return " \\\n  ".join(parts)


def recommend_qmmm(args):
    """QM/MM (METHOD MIXED) 专用推荐：构造 --type qmmm 命令 + 理由 + 起步阶梯。

    不进入普通 DFT 推荐路径（PM6 半经验无需基组/赝势，FIST 也无基组）。
    力场参数与 FRAGMENT 原子区间/坐标文件是占位 TODO，用户必须按真实体系填充。
    """
    qm = list(args.qm_elem or ["C", "H", "O"])
    mm = list(args.mm_elem or ["Cu"])
    parts = ["python gen_inp.py"]
    parts.append("--type qmmm")
    parts.append("--project {}".format(args.project))
    parts.append("--qm-elem " + " ".join(qm))
    parts.append("--mm-elem " + " ".join(mm))
    parts.append("--qm-method PM6")
    parts.append('--qm-atoms "1 50"')       # TODO: 按实际 QM 原子区间填
    parts.append('--mm-atoms "51 2000"')    # TODO: 按实际 MM 原子区间填
    parts.append("--topology TODO_full_structure.xyz")
    parts.append("--qm-topology TODO_qm_fragment.xyz")
    parts.append("--qmmm-run-type MD")
    parts.append('--group-partition "2 6"')
    cmd = " \\\n  ".join(parts)
    reasoning = [
        "QM/MM 用 METHOD MIXED 把 QM（Quickstep + QS METHOD PM6 半经验）与 MM"
        "（FIST 经典力场）两套力场耦合，适合大体系里只把感兴趣的区域做量子计算。",
        "QM 区（{}）用 PM6 半经验（自带 Slater 参数，无需基组/赝势）；MM 区（{}）用 "
        "FIST 力场。".format(" ".join(qm), " ".join(mm)),
        "PM6 适合有机/生物/溶液体系；含强关联金属或需要精度的区域不建议用半经验。",
        "FIST 的 &NONBONDED 目前是占位骨架（LENNARD-JONES 自对，EPSILON=0），必须先填入"
        "真实力场参数（GENPOT / EAM / Buckingham）才能跑物理合理的 MM。",
        "&MIXED &MAPPING 的 FRAGMENT 1/2 原子区间，以及 COORD 文件（全系统 ./s + QM 片段"
        " ./f）都需要按实际体系把 TODO 替换掉。",
    ]
    ladder = [
        "【起步阶梯 · 目标=QM/MM (MD/NEB)】",
        "  ① 先把 QM 片段单独用 PM6 跑通（--type static/geo_opt），确认半经验参数可用、SCF 收敛。",
        "  ② 准备全系统坐标 ./s 与 QM 片段坐标 ./f；填好 FIST 力场参数与 FRAGMENT 原子区间。",
        "  ③ 用下面命令生成 QM/MM 输入，validate_inp.py 校验后提交；先用少量步数 MD 看耦合是否正常。",
        "  ④ 收尾：parse_output.py + diagnose.py；若要做 QM/MM 过渡态，再单独配 --type neb 路径。",
    ]
    return {
        "elements": qm + mm,
        "functional": "PM6(SE)",
        "basis": ["(PM6 半经验)"], "potential": ["(无)"],
        "multiplicity": 1, "vdw": False, "plus_u_on": False, "plus_u": {},
        "periodic": "—", "kpoints": None, "smear": False, "cutoff": "—",
        "reasoning": reasoning, "ladder": ladder, "command": cmd,
        "unknown_elements": [],
    }


def main():
    ap = argparse.ArgumentParser(
        description="CP2K 参数推荐引擎：根据体系描述给出有理由的参数推荐与生成命令。")
    ap.add_argument("--elements", nargs="+", required=True,
                    help="元素组成，如 --elements Au O")
    ap.add_argument("--goal", default="geo_opt",
                    choices=["energy", "geo_opt", "cell_opt", "md", "neb", "vib", "ts", "qmmm"],
                    help="计算目标（映射到 --type）。ts=过渡态 Dimer 法。qmmm=QM/MM(MIXED+PM6)。")
    ap.add_argument("--periodic", default="xyz",
                    choices=["xyz", "xy", "none"],
                    help="周期性：块体 xyz / 表面 slab xy / 孤立分子 none")
    ap.add_argument("--charge", type=int, default=0, help="体系总电荷")
    ap.add_argument("--multiplicity", type=int, default=0,
                    help="自旋多重度；>0 开 UKS。不填则由脚本按磁性提示。")
    ap.add_argument("--functional", default=None,
                    choices=["PADE", "PBE", "TPSS", "SCAN", "HSE06", "B3LYP"],
                    help="泛函；默认 None→PBE。可显式指定杂化泛函。")
    ap.add_argument("--vdw", default="auto", choices=["auto", "yes", "no"],
                    help="DFT-D3 色散；auto=含分子/吸附质时自动开")
    ap.add_argument("--plus-u", default="auto", choices=["auto", "yes", "no"],
                    help="DFT+U 强关联修正；auto=含强关联 TM 且为氧化物/硫属化物时自动推荐")
    ap.add_argument("--smear", action="store_true",
                    help="强制开 SMEAR（金属默认会开）")
    ap.add_argument("--accuracy", default="balanced",
                    choices=["fast", "balanced", "accurate"],
                    help="精度档：影响 CUTOFF / k 点密度")
    ap.add_argument("--fixed-atoms", default="",
                    help="冻结原子列表（slab 冻底层），如 '1..54'")
    ap.add_argument("--project", default="cp2k", help="输出项目名")
    ap.add_argument("--cell", nargs=9, type=float,
                    default=[10.0, 0, 0, 0, 10.0, 0, 0, 0, 10.0],
                    metavar="A1..C3", help="晶格向量（占位，实际按结构填）")
    ap.add_argument("--xyz", default="", help="坐标文件（非 NEB）")
    ap.add_argument("--xyz-init", default="", help="NEB 初态 xyz")
    ap.add_argument("--xyz-final", default="", help="NEB 末态 xyz")
    # ---- QM/MM（仅 --goal qmmm 生效）----
    ap.add_argument("--qm-elem", nargs="+", default=None,
                    help="QM 区元素，如 --qm-elem C H O（用 Quickstep + QS METHOD PM6 半经验）")
    ap.add_argument("--mm-elem", nargs="+", default=None,
                    help="MM 区元素，如 --mm-elem Cu（用 FIST 经典力场）")
    # ---- NEB 进阶（仅 --goal neb 生效）----
    ap.add_argument("--xyz-replicas", nargs="+", default=None,
                    help="NEB 多副本外部 xyz：./0.xyz ./1.xyz ... ./N.xyz（每个→"
                         "&REPLICA COORD_FILE_NAME；NUMBER_OF_REPLICA 自动=文件数）")
    ap.add_argument("--optimize-band", default="MD",
                    choices=["MD", "DIIS"], help="&OPTIMIZE_BAND OPT_TYPE（DIIS 配 --optimize-end-points F 固定端点）")
    ap.add_argument("--optimize-end-points", default="T",
                    choices=["T", "F"], help="&OPTIMIZE_BAND OPTIMIZE_END_POINTS")
    ap.add_argument("--align-frames", default="T", choices=["T", "F"],
                    help="&BAND ALIGN_FRAMES")
    ap.add_argument("--rotate-frames", default="F", choices=["T", "F"],
                    help="&BAND ROTATE_FRAMES")
    ap.add_argument("--k-spring", type=float, default=0.02,
                    help="&BAND K_SPRING（相邻 replica 间的弹簧常数）。官方默认 0.02，"
                         "**官方 XML 不标单位 ⇒ 按 CP2K 内部原子单位 hartree/bohr²**"
                         "（早先这里写 eV/angstrom^2 是错的）。粗算常取 0.08/0.1")
    ap.add_argument("--program-run-info", action="store_true",
                    help="&BAND &PROGRAM_RUN_INFO ON")
    ap.add_argument("--convergence-info", action="store_true",
                    help="&BAND &CONVERGENCE_INFO ON")
    ap.add_argument("--properties", nargs="+",
                    help="Properties: dos pdos stress band cube wannier (dipole 为 MM/MIXED 专属，DFT 不发射)")
    ap.add_argument("--thermostat", default=None,
                    choices=["csvr", "nose", "langevin"],
                    help="MD thermostat (default: auto-recommend)")
    ap.add_argument("--ensemble", default="nvt",
                    choices=["nve", "nvt", "npt"],
                    help="MD ensemble (default: nvt)")
    ap.add_argument("--timestep", type=float, default=None,
                    help="&MD TIMESTEP [fs]；不给则按体系推荐"
                         "（含氢 0.5、不含氢 1.0）。口径同 gen_inp.py --timestep")
    ap.add_argument("--json", action="store_true", help="导出 JSON 结果")
    args = ap.parse_args()

    if args.goal == "qmmm":
        rec = recommend_qmmm(args)
        qm = list(args.qm_elem or ["C", "H", "O"])
        mm = list(args.mm_elem or ["Cu"])
        print("=" * 64)
        print("CP2K 参数推荐（思考层 · QM/MM）")
        print("体系元素(QM+MM): {}".format(" ".join(rec["elements"])))
        print("=" * 64)
        print("\n--- 推荐方案 ---")
        print("  QM 区 : {} (Quickstep + QS METHOD PM6 半经验)".format(" ".join(qm)))
        print("  MM 区 : {} (FIST 经典力场)".format(" ".join(mm)))
        print("  RUN_TYPE: MD（QM/MM 常用；也可 GEO_OPT 松弛 QM 区）")
        print("\n--- 选择理由 ---")
        for r in rec["reasoning"]:
            print("  • " + r)
        print("\n" + "\n".join(rec["ladder"]))
        print("\n--- 生成命令（可直接执行）---")
        print(rec["command"])
        print("\n（注意：FIST 力场参数、FRAGMENT 原子区间、坐标文件均为占位 TODO，"
              "必须先填真实值再提交。）")
        return

    rec = recommend(args)

    if args.json:
        print(json.dumps(rec, indent=2, ensure_ascii=False))
        return

    print("=" * 64)
    print("CP2K 参数推荐（思考层）")
    print("体系元素: {}".format(" ".join(rec["elements"])))
    if rec.get("unknown_elements"):
        print("⚠ 未能识别的元素（请手动核对基组/赝势）: {}"
              .format(", ".join(rec["unknown_elements"])))
    print("=" * 64)
    print("\n--- 推荐参数 ---")
    print("  泛函      : {}".format(rec["functional"]))
    print("  基组/赝势 :")
    for b, p in zip(rec["basis"], rec["potential"]):
        print("      {} / {}".format(b, p))
    print("  自旋      : {}".format(rec["multiplicity"] or "关(闭壳层)"))
    print("  DFT-D3    : {}".format("开" if rec["vdw"] else "关"))
    print("  DFT+U     : {}".format(
        "开 (元素: {})".format(", ".join("{}={}".format(k, v)
            for k, v in rec.get("plus_u", {}).items())) if rec.get("plus_u_on") else "关"))
    print("  周期性    : {}".format(rec["periodic"]))
    print("  k 点      : {}".format(rec["kpoints"] or "GAMMA(默认)"))
    print("  SMEAR     : {}".format("开" if rec["smear"] else "关"))
    print("  CUTOFF    : {} Ry".format(rec["cutoff"]))
    print("\n--- 选择理由 ---")
    for r in rec["reasoning"]:
        print("  • " + r)
    print("\n" + "\n".join(rec["ladder"]))
    print("\n--- 生成命令（可直接执行，再跑 validate_inp.py）---")
    print(rec["command"])
    print("\n（然后用 scripts/validate_inp.py 校验，提交后 scripts/parse_output.py "
          "+ diagnose.py 看结果、决定下一步。）")


if __name__ == "__main__":
    main()
