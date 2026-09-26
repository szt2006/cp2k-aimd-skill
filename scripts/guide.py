#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guide.py —— CP2K 计算项目的「阶段向导」

它不是自动化工作流，而是一个"会陪你走完整项目"的辅助：
  - list              列出项目全生命周期的所有阶段
  - show <stage>      展开某个阶段的完整指引（目标/该做的/决策点/坑/命令/产出/完成判据）
  - scan <dir>        扫描你的项目目录，根据已有文件推断"你卡在哪、下一步该做什么"
  - next <dir>        只给出下一步行动（scan 的精简版）

设计原则：每个阶段都告诉你"现在该做什么、为什么、用什么命令、做完长什么样"，
而不是替你盲跑。阶段的顺序与 SKILL.md 的闭环一致。
"""

import argparse
import glob
import os
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


# ---------------------------------------------------------------------------
# 阶段模型（数据驱动；顺序 = 项目推进顺序）
# 每个阶段字段：
#   key        英文键
#   title      中文标题（含序号）
#   goal       目标
#   enter      进入条件
#   actions    该做的具体事（清单）
#   decisions  决策点 + 指引
#   pitfalls   常见坑
#   commands   对应的 skill 命令（引用 gen_inp / recommend / postprocess / diagnose）
#   outputs    应产出的文件/结果
#   done       完成判据
#   next       下一步阶段 key
#   # 以下供 scan 使用：
#   evidence   该阶段"已完成"的文件/输出信号（glob 列表或 .out 关键字）
# ---------------------------------------------------------------------------

STAGES = [
    {
        "key": "define",
        "title": "① 立项与问题定义",
        "goal": "把科学问题翻译成可计算的任务：要算什么量、用什么 RUN_TYPE、什么化学环境。",
        "enter": "任何新项目的起点。",
        "actions": [
            "明确科学问题：吸附能？反应能垒？扩散系数？IR 谱？电荷转移？表面重构？",
            "选定任务类型 → GLOBAL RUN_TYPE：单点(ENERGY_FORCE)/几何(GEO_OPT)/晶胞(CELL_OPT)/动力学(MD)/过渡态(BAND=NEB 或 VIBRATIONAL_ANALYSIS)/增强采样(MD+&METADYN)。",
            "判断化学环境：气相分子 / 表面 slab / 块体 / 溶液（溶液需 PACKMOL 建盒，本 skill 不生成）。",
            "粗估体系规模（原子数）→ 决定能否上杂化泛函（>50 原子基本要 ADMM）。",
        ],
        "decisions": [
            "静态优化 vs AIMD：表面反应、有限温效应、扩散——这些必须有限温动力学，静态优化会漏掉。",
            "是否需要反应路径：有初末态→NEB；有连续构型变化→元动力学（选 CV）。",
        ],
        "pitfalls": [
            "任务类型选错导致白算（如用 GEO_OPT 看表面反应，实际需要 AIMD）。",
            "忽视有限温效应，用 0 K 优化结构外推有限温结论。",
        ],
        "commands": [
            "python recommend.py --elements <...> --goal <energy|geo_opt|md|ts> --periodic <none|xy|xyz>   # 先用它梳理方法",
        ],
        "outputs": ["一句话任务定义", "目标物理量清单", "初步的 RUN_TYPE 选择"],
        "done": "你能用一句话说清：体系是什么、要算什么量、用什么计算类型。",
        "next": "build",
        "evidence": [],
    },
    {
        "key": "build",
        "title": "② 体系构建（初始结构）",
        "goal": "得到干净、合理、无重叠的初始结构（坐标 + 晶胞）。",
        "enter": "任务类型已定。",
        "actions": [
            "获取初始结构：实验 CIF / Materials Project / 自己搭建 / PACKMOL（溶液盒本 skill 不生成，需自备）。",
            "表面 slab：切表面、加真空层（一般 ≥15 Å，避免镜像相互作用）、固定底层、判断终止面。",
            "块体：确认晶格常数、准备加 k 点。",
            "吸附体系：把吸附质放到合理初位（不要原子重叠），多试几个吸附位点初猜。",
        ],
        "decisions": [
            "真空层厚度（≥15 Å 一般安全；大体系可减）。",
            "固定哪些原子（slab 底层通常固定 2 层）。",
            "表面超胞大小（避免吸附质与镜像相互作用）。",
        ],
        "pitfalls": [
            "真空层不足 → 镜像相互作用污染结果。",
            "底层未固定 → 优化时整块 slab 漂移。",
            "初始结构原子重叠 → SCF/几何优化发散或得到怪结构。",
        ],
        "commands": [
            "python gen_inp.py --type <...> --topology POSCAR.cif --topology-format cif   # 从 CIF 读结构",
            "python gen_inp.py --type <...> --xyz init.xyz                                # 或从 xyz 读",
        ],
        "outputs": ["干净的初始结构文件（.xyz / .cif）"],
        "done": "结构无重叠、真空层/晶胞合理、吸附质初位合理。",
        "next": "decide",
        "evidence": ["*.cif", "*.xyz"],
    },
    {
        "key": "decide",
        "title": "③ 计算方法与参数决策（安全起点）",
        "goal": "选定泛函/基组/赝势/自旋/色散/k点/SMEAR/CUTOFF，得到可跑的“安全起点”。",
        "enter": "初始结构就绪。",
        "actions": [
            "跑 recommend.py 得到逐项推荐 + 理由 + 可直接执行的 gen_inp 命令。",
            "逐项确认：泛函阶梯、是否 UKS（开壳层）、是否 DFT-D3（弱作用/层间）、是否 k 点（块体/金属）、是否 SMEAR（金属/窄带隙）、是否 DFT+U（含 d/f 电子过渡金属）。",
            "确认赝势/基组（轻元素 GTH-PADE、过渡金属 GTH-PBE，已按元素查好 q）。",
        ],
        "decisions": [
            "泛函阶梯：PBE（默认，筛选/结构）→ TPSS/SCAN（吸附/表面反应更准，~1.5-2x）→ HSE06/B3LYP（反应能/带隙最准，必须 +ADMM）。",
            "是否 DFT+U：含 Fe/Ti/Co/Ni/Mn/Cu/Cr/Ce 等 d 电子 TM 的氧化物/硫化物——几乎必加，否则电子结构错。",
            "是否 SMEAR：任何金属/窄带隙体系必加 FERMI_DIRAC。",
        ],
        "pitfalls": [
            "金属不加 SMEAR → SCF 死活不收敛。",
            "TM 氧化物不加 DFT+U → 能带/d 带中心错。",
            "大体系直接 HSE06（不带 ADMM）→ 计算成本上天。",
        ],
        "commands": [
            "python recommend.py --elements Au O --goal geo_opt --periodic xy --multiplicity 3 --vdw auto --accuracy balanced",
            "# recommend 对含 d 电子 TM 会自动建议 DFT+U，并用 --kinds 'Fe:...:U=3' 发射 &DFT_PLUS_U",
        ],
        "outputs": ["推荐参数表", "可直接执行的 gen_inp.py 命令"],
        "done": "你认可了推荐参数，并能直接生成输入。",
        "next": "converge",
        "evidence": ["*.inp"],
    },
    {
        "key": "converge",
        "title": "④ 收敛性测试",
        "goal": "确认 CUTOFF / REL_CUTOFF / k 点密度 / SMEAR 宽度已足够（结果不再随参数明显变化）。",
        "enter": "参数已定，正式大算之前。",
        "actions": [
            "CUTOFF 扫描（300→400→500 Ry），看能量变化 < 1 meV/atom 即收敛。",
            "块体：k 点密度扫描（4³→6³→8³ Monkhorst-Pack）。",
            "金属：SMEAR 宽度扫描（100→300→500 K），确认带隙/能量稳定。",
            "REL_CUTOFF 一般 60 足够，不必扫。",
        ],
        "decisions": [
            "选“性价比最高”的收敛参数，不是无限大（成本 × 精度权衡）。",
        ],
        "pitfalls": [
            "跳过收敛测试 → 结果不可信、与他人不可比。",
            "CUTOFF 太低 → 能量漂移、几何/频率错。",
        ],
        "commands": [
            "python gen_inp.py ... --cutoff 300   # 跑一遍取能量",
            "python gen_inp.py ... --cutoff 400   # 再跑",
            "python parse_output.py cp2k.out       # 取能量做收敛曲线",
        ],
        "outputs": ["收敛曲线（能量 vs CUTOFF / k 点）", "最终采用的收敛参数"],
        "done": "能量随 CUTOFF/k 点变化 < 1 meV/atom，参数锁定。",
        "next": "optimize",
        "evidence": [],
    },
    {
        "key": "optimize",
        "title": "⑤ 几何/晶胞优化",
        "goal": "得到能量最低、合理的结构（局域极小点）。",
        "enter": "收敛参数已定。",
        "actions": [
            "分子/表面用 GEO_OPT；块体/高压用 CELL_OPT。",
            "检查收敛：MAX_FORCE 低于阈值、几何变化趋稳、无虚频（用 VIBRATIONAL_ANALYSIS 验证极小点）。",
            "吸附体系：确认吸附质没飞走、键长合理、没跑到别的位点。",
            "多初位/爬过渡态确认不是错误极小（尤其表面反应）。",
        ],
        "decisions": [
            "OPTIMIZER：块体 BFGS（默认）、slab/缺陷 LBFGS 或 CG。",
            "是否 CELL_OPT（块体/相变/高压必做；表面 slab 一般不优化晶胞）。",
            "固定哪些原子（slab 底层）。",
        ],
        "pitfalls": [
            "未收敛就拿结构用 → 后续全错。",
            "优化到错误极小点（需多初位/过渡态确认）。",
            "虚频未检查 → 以为极小点其实是鞍点。",
        ],
        "commands": [
            "python gen_inp.py --type geo_opt [--optimizer lbfgs] [--fixed-atoms '1..54']",
            "python gen_inp.py --type cell_opt",
            "python diagnose.py cp2k.out      # 看几何是否收敛",
        ],
        "outputs": ["优化后结构（坐标）", "优化能量", "收敛报告"],
        "done": "MAX_FORCE 达标、几何稳定、无虚频（或虚频已解释）。",
        "next": "static",
        "evidence": ["*GEO_OPT*", "*geo_opt*", "REACH", "GEOMETRY"],
    },
    {
        "key": "static",
        "title": "⑥ 静态计算与电子结构性质",
        "goal": "在优化结构上算电子结构性质，直接回答科学问题。",
        "enter": "优化结构可信。",
        "actions": [
            "在优化结构上跑单点，开 --properties。",
            "PDOS：看 d 带中心、带隙、元素/轨道贡献（催化关键）。",
            "布居分析：MULLIKEN/LOWDIN/HIRSHFELD 看电荷转移、键极性。",
            "BADER（需 cube + bader 二进制）、cube（电荷密度/ELF）看成键/孤对。",
            "含 DFT+U 体系：确认自旋态/磁矩正确（看 .out 的原子磁矩）。",
        ],
        "decisions": [
            "用哪个性质回答你的问题：吸附强度→d 带中心/电荷转移；成键→ELF/cube；离子性→Bader。",
        ],
        "pitfalls": [
            "在没优化的结构上算性质 → 结论无意义。",
            "PDOS 费米能级定错 → 能级对齐错（postprocess.py pdos 自动探测费米面）。",
        ],
        "commands": [
            "python gen_inp.py --type static --properties pdos charges cube [--ldos-list '1..26']",
            "python postprocess.py pdos prefix=<out>     # 画 PDOS",
            "python postprocess.py bader                 # 需 cube + bader",
        ],
        "outputs": ["PDOS 图", "电荷/布居表", "cube 文件（密度/ELF）", "Bader 电荷"],
        "done": "拿到回答科学问题所需的性质数据。",
        "next": "dynamics",
        "evidence": ["*.pdos", "*E_DENSITY_CUBE*", "ACF.dat"],
    },
    {
        "key": "dynamics",
        "title": "⑦ 分子动力学（AIMD / MD）",
        "goal": "在有限温下观察体系真实行为：是否反应、如何扩散、结构如何演化。",
        "enter": "优化结构可信；AIMD 一般用人力可承受的泛函（PBE/TPSS，很少上杂化）。",
        "actions": [
            "选系综（NVT 常用 / NPT 看体积涨落）、恒温器（CSVR/Nose/LANGEVIN，表面催化 LANGEVIN 更稳）。",
            "TIMESTEP 0.5 fs（含 H/O 的一般安全），STEPS 足够采样（数千~数十万）。",
            "分平衡段 + 采样段；开 --restart-freq 续算；打印轨迹 + 速度（默认开 &VELOCITIES）。",
            "跑后检查能量/温度漂移（diagnose）。",
        ],
        "decisions": [
            "温度、恒温器、是否 NPT、步长（重元素/快振动可减到 0.5 仍安全）。",
            "采样长度：扩散需足够长（MSD 线性区）；反应需足够覆盖反应事件。",
        ],
        "pitfalls": [
            "TIMESTEP 太大 → 体系爆炸。",
            "未平衡就采样 → 统计偏了。",
            "温度/能量漂移 → 步长过大或未收敛（看 diagnose）。",
        ],
        "commands": [
            "python gen_inp.py --type aimd_md --thermostat langevin --ensemble nvt --restart-freq 1000 --steps 50000",
            "python diagnose.py cp2k.out      # 看温度/能量漂移",
        ],
        "outputs": ["*-pos-1.xyz 轨迹", "*-vel-1.xyz 速度", "*.out（能量/温度）"],
        "done": "轨迹足够长、温度/能量平稳、覆盖你要的现象。",
        "next": "postproc",
        "evidence": ["*-pos-1.xyz", "*-vel-1.xyz"],
    },
    {
        "key": "react",
        "title": "⑧ 反应路径（NEB / 元动力学）",
        "goal": "算反应能垒（NEB）或自由能面（元动力学 FES）。",
        "enter": "已知初态+末态（NEB）或选好 CV（元动力学）。",
        "actions": [
            "NEB：CI-NEB，初末态都优化好，中间副本插值，K_SPRING 0.02-0.08；收敛后验证过渡态（VIBRATIONAL_ANALYSIS：有且仅有 1 个虚频）。",
            "元动力学：选 CV（DISTANCE 已支持；COORDINATION 需手加 &COLVAR）、墙约束、NT_HILLS；后用 CP2K graph 重建 FES。",
        ],
        "decisions": [
            "NEB vs 元动力学：离散已知路径→NEB；连续 CV、探索未知路径→元动力学。",
            "CV 选择（元动力学最关键，选错得假 FES）。",
        ],
        "pitfalls": [
            "初末态未优化 → 能垒错。",
            "NEB 收敛判据太松 → 过渡态不准。",
            "元动力学 graph 的 -ndim 必须 = 真实 CV 数，否则 FES 重建错误。",
        ],
        "commands": [
            "python gen_inp.py --type neb --xyz-replicas ./0.xyz ... --optimize-band DIIS --k-spring 0.05",
            "python gen_inp.py --type metadyn [--topology ...]",
            "python postprocess.py fes     # 重建并画 FES",
        ],
        "outputs": ["能垒曲线（NEB）", "FES 图（元动力学）"],
        "done": "拿到能垒/自由能面，过渡态虚频验证通过。",
        "next": "postproc",
        "evidence": ["HILLS", "fes.dat", "*METADYN*"],
    },
    {
        "key": "postproc",
        "title": "⑨ 后处理与动力学分析",
        "goal": "从轨迹/输出算出物理量：RDF / MSD / 扩散 / VACF / IR / 键角 / PDOS / Bader / FES。",
        "enter": "有轨迹 / .out / .pdos / cube / restart。",
        "actions": [
            "结构：rdf（径向分布）、cn（配位数）、bond/angle（键长/角分布）。",
            "动力学：msd → diffusion（Einstein，给 Å²/ps 与 cm²/s）；vacf → ir/power（红外/振动态密度）。",
            "电子：pdos（d 带中心）、bader（电荷）。",
            "自由能：fes（元动力学 FES 出图）。",
        ],
        "decisions": [
            "按科学问题选量：扩散→MSD；振动/IR→VACF；局域结构→RDF/CN。",
        ],
        "pitfalls": [
            "MSD 没做 PBC 解包裹 → 错误（postprocess 已处理）。",
            "RDF 没给晶胞 → 归一化错（--cell 或自动从 .out 解析）。",
            "IR 无速度文件 → 用位置差分近似，需知悉其局限（高频段偏差）。",
        ],
        "commands": [
            "python postprocess.py rdf prefix=<out> --pairs 'O O'",
            "python postprocess.py msd prefix=<out>   &&   python postprocess.py diffusion prefix=<out>",
            "python postprocess.py vacf prefix=<out>  &&   python postprocess.py ir prefix=<out>",
        ],
        "outputs": [".png 图", ".csv 数据"],
        "done": "拿到回答问题所需的分析量，并出图。",
        "next": "diagnose",
        "evidence": ["*.png", "*_rdf*", "*_msd*", "*_vacf*", "*_pdos*"],
    },
    {
        "key": "diagnose",
        "title": "⑩ 结果判读与诊断",
        "goal": "判断结果可信、发现异常、决定下一步（收工 or 回去调参重算）。",
        "enter": "有 .out / 分析图。",
        "actions": [
            "diagnose.py 自动看 SCF/几何/能量漂移/虚频/ABORT，给“改哪行”建议。",
            "对照 references/decide.md 的结果判读对照表，确认计算是否合理。",
            "问自己：收敛了吗？物理上合理吗？和文献/化学直觉一致吗？",
        ],
        "decisions": [
            "结果可信 → 进入 report。",
            "未收敛/异常 → 回到 optimize/static/dynamics 调参重算（闭环迭代）。",
        ],
        "pitfalls": [
            "忽视警告、把未收敛当结果。",
            "只看能量不看结构/性质是否合理。",
        ],
        "commands": [
            "python diagnose.py cp2k.out",
            "python parse_output.py cp2k.out",
        ],
        "outputs": ["健康报告（收敛/异常/建议）"],
        "done": "结果经诊断可信，或明确了要改什么重算。",
        "next": "report",
        "evidence": ["*_diag*", "*diagnosis*"],
    },
    {
        "key": "report",
        "title": "⑪ 总结与报告",
        "goal": "汇总数据、回答科学问题、形成可交付/可发表结论。",
        "enter": "结果经诊断可信。",
        "actions": [
            "整理能量/结构/谱图/电荷，回答立项时的问题。",
            "复查方法描述是否完整（泛函/基组/参数/U值/k点/温度）。",
            "出最终图（postprocess 已生成的 png/csv 直接引用）。",
        ],
        "decisions": [
            "结论是否回答了科学问题；是否需要补充计算。",
        ],
        "pitfalls": [
            "方法描述不全 → 别人无法复现。",
            "只给图不给误差/收敛信息。",
        ],
        "commands": [
            "python postprocess.py <子命令>   # 复出最终图",
        ],
        "outputs": ["报告 / 图 / 数据表", "方法学段落"],
        "done": "形成回答科学问题的结论，方法可复现。",
        "next": "define",
        "evidence": ["*.pdf", "*report*"],
    },
    {
        "key": "resume",
        "title": "↻ 续算（从检查点恢复被中断/杀掉的计算）",
        "goal": "把被 kill / 超时 / 宕机中断的计算，从最近一次写盘的检查点接上继续跑，而不是从头重算、也不是当成已完成去后处理。",
        "enter": "目录里有 <prefix>-1.restart（几何/MD/热浴/速度都在里面），但 .out 未见正常结束标记（无 PROGRAM ENDED）。",
        "actions": [
            "先判断为什么断、末步是否健康：grep -iE 'PROGRAM ENDED|not converged|ABORT|SCF run NOT converged' cp2k.out | tail —— CP2K 即使某离子步 SCF 不收敛也会继续下一步（与 Gaussian 不同），续算前要知悉末步状态。",
            "定位最新检查点：<prefix>-1.restart 是完整可跑的输入（含坐标/速度/步数/热浴）；历史检查点在 <prefix>-1.restart.bak-* 或 RESTART_HISTORY/ 下。注意：从最后写盘的检查点续，不是被杀掉的精确那一步。",
            "接上续算：在输入里加 &EXT_RESTART / RESTART_FILE_NAME <prefix>-1.restart / &END —— 最省事的做法是直接把 <prefix>-1.restart 当输入文件提交。",
            "（可选）波函数续算省 SCF：&DFT 里 SCF_GUESS RESTART + WFN_RESTART_FILE_NAME ./<prefix>-RESTART.wfn（注意是 &DFT 关键字，不在 &SCF；文件缺失会自动退化 ATOMIC GUESS，非致命）。",
            "MD 续算：EXT_RESTART 自动接上步数/速度/热浴；&MD STEPS 是‘总步数目标’而非‘再跑多少步’，按需调大后再提交。",
        ],
        "decisions": [
            "从 -1.restart（最新）续，还是退回某个 .bak 历史检查点：末步不健康（SCF 崩/结构畸变）就回退上一个检查点。",
            "要不要顺带 WFN_RESTART：想省 SCF 迭代就带；若中断后结构会大改，收益有限。",
        ],
        "pitfalls": [
            "续算是从‘最后写盘的检查点’接上，不是被中断的精确步——两次检查点之间的步会丢失/重跑（这也是为什么长任务要 --restart-freq）。",
            "WFN_RESTART_FILE_NAME 放错节（应在 &DFT，不在 &SCF）→ 不生效，白等 SCF。",
            "&MD STEPS 写成‘增量步数’ → 若小于已完成步数，续算会立刻结束。",
            "直接覆盖旧输出/轨迹文件 → 轨迹被截断或追加错乱；建议确认 APPEND 行为或换新目录保存续算段。",
            "末步 SCF 未收敛就盲目续 → 误差累积（CP2K 不会像 Gaussian 那样停下来）。",
        ],
        "commands": [
            "python guide.py scan <dir>                                             # 识别检查点与末步状态",
            "grep -iE 'PROGRAM ENDED|not converged|ABORT' cp2k.out | tail          # 判断为何中断、末步是否健康",
            "python gen_inp.py --type <...> --scf-guess RESTART --wfn-restart ./<prefix>-RESTART.wfn   # 生成带波函数续算的输入",
            "# 或最省事：直接提交 <prefix>-1.restart 作为输入；细节见 references/run.md「续算(RESTART)」节",
        ],
        "outputs": ["含 &EXT_RESTART 的续算 .inp（或直接复用 <prefix>-1.restart）"],
        "done": "计算从检查点接上并继续推进（步数/几何在原基础上前进，非从头）。",
        "next": "postproc",
        "evidence": ["*-1.restart", "*.restart"],
    },
]

STAGE_BY_KEY = {s["key"]: s for s in STAGES}
STAGE_ORDER = [s["key"] for s in STAGES]


# ---------------------------------------------------------------------------
# 输出格式（纯文本，ANSI 简单着色）
# ---------------------------------------------------------------------------
def _c(text, code):
    return "\033[{}m{}\033[0m".format(code, text)


def _bold(t):
    return _c(t, "1")


def _green(t):
    return _c(t, "32")


def _yellow(t):
    return _c(t, "33")


def _cyan(t):
    return _c(t, "36")


def _bullet_list(items, indent="  "):
    return "\n".join("{}- {}".format(indent, x) for x in items)


# ---------------------------------------------------------------------------
# subcommand: list
# ---------------------------------------------------------------------------
def _stage_payload(s):
    """把阶段字典转成可 JSON 序列化的结构。"""
    return {
        "key": s["key"],
        "title": s["title"],
        "goal": s["goal"],
        "enter": s["enter"],
        "actions": s["actions"],
        "decisions": s["decisions"],
        "pitfalls": s["pitfalls"],
        "commands": s["commands"],
        "outputs": s["outputs"],
        "done": s["done"],
        "next": s["next"],
        "next_title": STAGE_BY_KEY.get(s["next"], {}).get("title", ""),
    }


def cmd_list(args):
    n_main = len([s for s in STAGES if s.get("key") != "resume"])
    n_resume = len(STAGES) - n_main
    if getattr(args, "json", False):
        import json
        print(json.dumps({
            "ok": True,
            "n_main": n_main,
            "n_resume": n_resume,
            "stages": [_stage_payload(s) for s in STAGES],
        }, ensure_ascii=False, indent=2))
        return 0
    print(_bold("CP2K 项目全生命周期阶段") + "（从立项到报告，共 {} 个主线阶段{}）\n".format(
        n_main, " + {} 个续算分支".format(n_resume) if n_resume else ""))
    for i, s in enumerate(STAGES, 1):
        nxt = STAGE_BY_KEY.get(s["next"], {}).get("title", "—")
        print("  {}. {}  {}".format(i, _cyan(s["title"]), _yellow("→ 下一步: " + nxt)))
    print("\n用法：")
    print("  python guide.py show <stage>   展开某阶段完整指引")
    print("  python guide.py scan <dir>     扫描项目目录，告诉下一步该做什么")
    print("  python guide.py next <dir>     只给下一步行动")
    return 0


# ---------------------------------------------------------------------------
# subcommand: show
# ---------------------------------------------------------------------------
def cmd_show(args):
    s = STAGE_BY_KEY.get(args.stage)
    if not s:
        if getattr(args, "json", False):
            import json
            print(json.dumps({
                "ok": False,
                "error": "未知阶段 '{}'".format(args.stage),
                "available": list(STAGE_ORDER),
            }, ensure_ascii=False, indent=2))
            return 1
        print("未知阶段 '{}'。可用：{}".format(args.stage, ", ".join(STAGE_ORDER)))
        print("\n提示：先跑 `python guide.py list` 看全部阶段及其含义。")
        return 1
    if getattr(args, "json", False):
        import json
        print(json.dumps({"ok": True, "stage": _stage_payload(s)},
                         ensure_ascii=False, indent=2))
        return 0
    print("\n" + _bold("═" * 64))
    print(_bold(s["title"]))
    print(_bold("═" * 64))
    print("\n" + _bold("目标") + "\n  " + s["goal"])
    print("\n" + _bold("进入条件") + "\n  " + s["enter"])
    print("\n" + _bold("该做的事") + "\n" + _bullet_list(s["actions"]))
    print("\n" + _bold("决策点（带指引）") + "\n" + _bullet_list(s["decisions"]))
    print("\n" + _bold(_yellow("常见坑")) + "\n" + _bullet_list(s["pitfalls"]))
    print("\n" + _bold("可参考的命令（由你决定是否执行）") + "\n" + _bullet_list(s["commands"]))
    print("\n" + _bold("应产出的文件/结果") + "\n" + _bullet_list(s["outputs"]))
    print("\n" + _bold(_green("完成判据")) + "\n  " + s["done"])
    nxt = STAGE_BY_KEY.get(s["next"])
    if nxt:
        print("\n" + _bold("下一步") + " → " + _cyan(nxt["title"]))
    print()
    return 0


# ---------------------------------------------------------------------------
# scan: 扫描目录，推断阶段
# ---------------------------------------------------------------------------
def _scan_dir(path):
    """返回信号字典 + 分类文件列表"""
    if not os.path.isdir(path):
        return None
    files = []
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)):
            files.append(f)
    names = " ".join(files)

    # 读所有 .out 的内容（可能有多个，取第一个非空）
    out_text = ""
    out_files = [f for f in files if f.endswith(".out")]
    for f in out_files:
        try:
            with open(os.path.join(path, f), "r", encoding="utf-8", errors="ignore") as fh:
                out_text += fh.read()
        except Exception:
            pass

    signals = {
        "inp": [f for f in files if f.endswith(".inp")],
        "out": out_files,
        "out_text": out_text,
        "traj": [f for f in files if "-pos-1.xyz" in f],
        "vel": [f for f in files if "-vel-1.xyz" in f],
        "pdos": [f for f in files if f.endswith(".pdos")],
        "cube": [f for f in files if "CUBE" in f.upper() or f.endswith(".cube")],
        "acf": [f for f in files if f.upper() == "ACF.DAT"],
        "hills": [f for f in files if f.upper() == "HILLS"],
        "fes": [f for f in files if "fes" in f.lower() and f.endswith(".dat")],
        "metadyn": [f for f in files if "METADYN" in f.upper()],
        "wfn": [f for f in files if "RESTART.wfn" in f or f.upper().endswith(".WFN")],
        "restart": [f for f in files if f.endswith(".restart") or f.endswith(".restart.bak")
                    or "-1.restart" in f or ".restart.bak-" in f],
        "pp_png": [f for f in files if f.endswith(".png")],
        "pp_csv": [f for f in files if f.endswith(".csv")],
        "cif": [f for f in files if f.lower().endswith(".cif")],
        "xyz": [f for f in files if f.lower().endswith(".xyz") and "-pos-1" not in f and "-vel-1" not in f],
    }

    # 从 .out 文本推断发生了什么
    ot = out_text.upper()
    signals["out_md"] = "ENSEMBLE" in ot and ("MD" in ot or "MOLECULAR DYNAMICS" in ot or "STEP" in ot)
    signals["out_geo"] = "GEO_OPT" in ot or "GEOMETRY OPTIMIZATION" in ot or "CELL_OPT" in ot
    # 几何收敛标记
    signals["geo_converged"] = bool(re.search(r"REACH.*TOLERANCE|GEOMETRY OPTIMIZATION.*COMPLETE|CONVERGED", ot))
    # 正常结束标记（用于区分“跑完”与“被中断/杀掉”）
    signals["program_ended"] = ("PROGRAM ENDED" in ot or "PROGRAM STOPPED" in ot)
    # 轨迹帧数（粗略：pos-1.xyz 行数 / (natoms+2)）
    return signals, files


def _detect_stage(signals):
    """根据信号推断当前阶段 key。返回 (current_key, evidence_notes)"""
    s = signals

    # 是否已发生计算（.out / 轨迹 / 性质产物 / restart 检查点是最强信号，优先于此前的 .inp）
    has_run = (s["out"] or s["traj"] or s["pdos"] or s["cube"]
               or s["acf"] or s["hills"] or s["fes"] or s["metadyn"] or s.get("restart"))

    if not has_run:
        # 还没跑过：看有没有输入或结构
        if s["inp"]:
            return "decide", ["已生成输入 {} 但未运行。下一步：校验 + 提交计算（见 references/run.md）。".format(
                ", ".join(s["inp"])[:80])]
        if s["cif"] or s["xyz"]:
            return "decide", ["检测到初始结构文件（{}），但还没有 .inp —— 你可能已构建好结构，下一步是参数决策与生成输入。".format(
                ", ".join(s["cif"] + s["xyz"])[:80])]
        return "define", ["目录里没有任何 CP2K 文件（无 .inp / .out / 结构）。从立项与构建开始。"]

    # 已跑过，按产物推断阶段
    # —— 续算优先：有 restart 检查点，但计算未正常结束（无 PROGRAM ENDED）→ 像是被 kill/超时/宕机中断
    if s.get("restart") and not s.get("program_ended"):
        note = ["检测到 restart 检查点（{}），但 .out {}——计算像是被中断/杀掉，而非正常跑完。".format(
            ", ".join(s["restart"])[:60],
            "未见正常结束标记（无 PROGRAM ENDED）" if s["out"] else "缺失或为空")]
        note.append("下一步不是后处理，而是用 &EXT_RESTART 从检查点续算；续前先 grep 末步收敛情况。")
        return "resume", note

    if s["traj"] or s["out_md"]:
        return "postproc", ["检测到 AIMD/MD 轨迹（{}）。计算已跑，下一步做后处理分析。".format(
            ", ".join(s["traj"])[:60])]

    if s["hills"] or s["fes"] or s["metadyn"]:
        return "postproc", ["检测到元动力学产物（HILLS / fes.dat / restart）。下一步：重建并分析 FES。"]

    if s["pdos"] or s["cube"] or s["acf"]:
        return "postproc", ["检测到电子结构性质产物（pdos/cube/ACF.dat）。可继续后处理或进入诊断。"]

    if s["out_geo"]:
        if s["geo_converged"]:
            return "static", ["检测到几何/晶胞优化且已收敛（.out 含收敛标记）。下一步：在优化结构上算电子结构性质，或进入后处理。"]
        return "optimize", ["检测到几何/晶胞优化但未见明确收敛标记。先用 diagnose.py 确认是否收敛；未收敛则继续优化或调参。"]

    # 有 .out 但无法归类为上述 → 可能是静态单点
    return "diagnose", ["检测到 .out（{}）但无法明确归类。建议先跑 diagnose.py 判读健康度，再决定下一步。".format(
        ", ".join(s["out"])[:60])]


def _render_scan(path, brief=False):
    res = _scan_dir(path)
    if res is None:
        print("目录不存在或无法读取：{}".format(path))
        return 1
    signals, files = res
    if not files:
        print("目录为空：{}".format(path))
        return 0
    current, note = _detect_stage(signals)
    s = STAGE_BY_KEY[current]

    print("\n" + _bold("扫描目录：") + path)
    print(_bold("已有文件（{} 个）：".format(len(files))) + " " + ", ".join(files)[:200])
    print("\n" + _bold(_yellow("推断当前阶段：")) + _cyan(s["title"]))
    for n in note:
        print("  · " + n)

    if brief:
        print("\n" + _bold(_green("下一步行动：")))
        print(_bullet_list(s["actions"][:4]))
        print(_bold("对应命令："))
        print(_bullet_list(s["commands"][:3]))
        return 0

    # 完整报告
    print("\n" + _bold("当前阶段完整指引："))
    print("  " + _bold("目标") + " " + s["goal"])
    print("  " + _bold("该做的事："))
    print(_bullet_list(s["actions"]))
    print("  " + _bold(_yellow("注意的坑：")))
    print(_bullet_list(s["pitfalls"]))
    print("  " + _bold("可参考的命令："))
    print(_bullet_list(s["commands"]))
    print("  " + _bold(_green("完成判据：")) + s["done"])
    nxt = STAGE_BY_KEY.get(s["next"])
    if nxt:
        print("  " + _bold("完成后进入：") + _cyan(nxt["title"]))
    return 0


def cmd_scan(args):
    if getattr(args, "json", False):
        return _render_scan_json(args.dir, brief=False)
    return _render_scan(args.dir, brief=False)


def cmd_next(args):
    if getattr(args, "json", False):
        return _render_scan_json(args.dir, brief=True)
    return _render_scan(args.dir, brief=True)


def _render_scan_json(path, brief=False):
    import json
    res = _scan_dir(path)
    if res is None:
        print(json.dumps({"ok": False, "dir": path,
                          "error": "目录不存在或无法读取"},
                         ensure_ascii=False, indent=2))
        return 1
    signals, files = res
    if not files:
        print(json.dumps({"ok": True, "dir": path, "files": [],
                          "stage": None, "note": ["目录为空"]},
                         ensure_ascii=False, indent=2))
        return 0
    current, note = _detect_stage(signals)
    s = STAGE_BY_KEY[current]
    payload = {
        "ok": True,
        "dir": path,
        "files": files,
        "stage": current,
        "stage_title": s["title"],
        "note": note,
        "actions": s["actions"] if not brief else s["actions"][:4],
        "commands": s["commands"] if not brief else s["commands"][:3],
    }
    if not brief:
        payload["stage_detail"] = _stage_payload(s)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser():
    ap = argparse.ArgumentParser(
        description="CP2K 计算项目阶段向导：告诉你在项目的每个阶段该做什么。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--json", action="store_true",
                    help="输出 JSON（给 agent 用）")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("list", help="列出所有阶段")

    p_show = sub.add_parser("show", help="展开某阶段的完整指引")
    p_show.add_argument("stage", help="阶段 key: " + ", ".join(STAGE_ORDER))

    p_scan = sub.add_parser("scan", help="扫描项目目录，推断当前阶段与下一步")
    p_scan.add_argument("dir", help="项目目录路径")

    p_next = sub.add_parser("next", help="只给出下一步行动")
    p_next.add_argument("dir", help="项目目录路径")

    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    if not args.cmd or args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "show":
        return cmd_show(args)
    if args.cmd == "scan":
        return cmd_scan(args)
    if args.cmd == "next":
        return cmd_next(args)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
