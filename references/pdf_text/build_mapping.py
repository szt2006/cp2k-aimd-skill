#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 `MAPPING.md` —— 讲义页码 ↔ 字幕行号 的严格对应表。

为什么需要它
------------
课程资料是**两种不同组织方式**：
  * 讲义 = 5 个**按主题切分**的 PPT deck（共 425 页），**不是按天**；
  * 字幕 = 5 天**按天录制**的录音转写（6 个文件，共 22133 行）。

两者**多对多**，按编号硬对必然出错。旧版 `course_survey.md §1` 只有一句
"对应 5 天的 PPT 讲义"，而它 §2 的"每天讲什么"是**抽样**得出的——这正是
"BSSE 被误归到第 4 天"的根源。

本脚本把对应关系**逐段固化**：PDF 侧的页 → 主题索引写死在下面（内容取自
`learn_L1..L5.md` 的逐页小节标题），字幕侧的分段表从 6 份精读报告里
**逐字拼接**（不重打，避免转录错）。改报告后重跑本脚本即可刷新。

用法
----
    python build_mapping.py            # 重新生成 MAPPING.md
    python build_mapping.py --check    # 只校验分段表是否连续、是否覆盖全文

依赖：无（纯标准库）。字幕分段报告来自精读流程，缺失时脚本会明确报缺。
"""
import argparse
import os
import re
import sys

# --- 控制台编码兼容层（中文 Windows/GBK 下输出 ✓ ⑪ ⚠ 等符号不再抛异常）---
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

HERE = os.path.dirname(os.path.abspath(__file__))
# 精读报告所在目录（课程资料工作区，不属于 skill 仓库）
REPORT_DIR = os.environ.get("CP2K_EXTRACT_DIR",
                            r"D:\cp2k-aimd\study\_extract")

# 字幕文件 → (精读报告, 总行数, 天次说明)
SUBTITLES = [
    ("S1.1.txt", "S1_1.md", 2857, "第 1 天（上）：课程总览 + AIMD 基础 + VASP 跑 AIMD"),
    ("S1.2.txt", "S1_2.md", 1532, "第 1 天（下）：作业提交 + INCAR 全参数 + 后处理/出图"),
    ("S2.txt", "S2.md", 4546, "第 2 天：AIMD 后处理全套 + CP2K 简介/优缺点/编译 + 建模八类"),
    ("S3.txt", "S3.md", 4142, "第 3 天：CP2K 输入参数全集（对应讲义 L3）"),
    ("S4.txt", "S4.md", 4537, "第 4 天：NEB/频率/表面/团簇/基组赝势/DFT+U/磁性/QM-MM（**讲义无对应**）"),
    ("S5.txt", "S5.md", 4519, "第 5 天：振动光谱 TRAVIS + 电子结构分析 + 自由能面三法"),
]

# 讲义侧页 → 主题索引（取自 learn_L1..L5.md 的逐页小节标题，逐页无遗漏）
PDF_INDEX = [
    ("L1.txt", 83, "AIMD 基本原理 + VASP 做 AIMD + AIMD 后处理", [
        ("P1", "版权声明"),
        ("P2", "五天课程大纲（9/26–9/30，本文件是理解全部错位的总钥匙）"),
        ("P3", "从头上分子动力学 AIMD · 主讲人刘锦程（四大块：基本原理/计算练习/后处理/自由能面）"),
        ("P4–P7", "势能面特殊点 / 驻点·极小点·过渡态公式 / IRC 内禀反应坐标"),
        ("P8–P11", "电子步与离子步 / 单点能 / 结构优化 / 过渡态搜索 / 分子动力学模拟"),
        ("P12", "结构优化 vs MD（占位页）"),
        ("P13", "AIMD 计算基本流程"),
        ("P14–P18", "相空间 / 宏观量统计平均 / 常见系综 / NVE 总能"),
        ("P18–P20", "牛顿运动方程 / 速度形式 Verlet 算法 / AIMD 关键参数"),
        ("P21–P22", "时间步长选择：总则 + 经验准则"),
        ("P23", "参数测试（CP2K vs VASP 对照）"),
        ("P24–P26", "AIMD 重复性问题（混沌 / 100 条模拟统计，JACS 2016）"),
        ("P27", "**Energy drift 与 EPS_SCF 关系**（1E-4 严重 / 1E-5 300 ps 后明显 / 1E-6·1E-7 几乎没有）"),
        ("P28–P29", "**周期性边界条件 PBC**（盒子边长须大于原子间作用范围，避免与自身镜像作用）"),
        ("P30", "动能与温度公式"),
        ("P31–P37", "控温技术全谱：总论 / Maxwell–Boltzmann / 退火 / 速度调节法 / Andersen / Nosé–Hoover"),
        ("P38–P41", "水盒子建模（MS Amorphous Cell）+ CP2K 平衡态任务提交文件清单"),
        ("P42–P44", "**VASP 做 AIMD 参数详解**：NSW/POTIM；**SMASS 控系综**（P43）；**MDALGO 控热浴**（P44）"),
        ("P45–P48", "AIMD 平衡态模拟一般步骤 / INCAR 模板 / 其他参数注意事项"),
        ("P49–P50", "案例文献解析（从文献 computational method 还原参数）"),
        ("P51–P82", "**AIMD 后处理分析**：VMD 轨迹查看与命令 / 键长键角二面角 / 势能涨落 / "
                     "RDF / VACF / 红外 / MSD / 扩散系数 / Arrhenius 能垒 / 多帧显示"),
    ]),
    ("L2.txt", 69, "CP2K 简介 + 编译 + 复杂模型建模", [
        ("P1–P2", "版权 / CP2K 简介封面（主讲人刘锦程）"),
        ("P3", "程序定位图（速度 / 力场尺度 / 黑科技 / 后 HF / 精度）"),
        ("P4–P15", "**编译方法**：方法对比表（P7）+ toolchain 法详细步骤（P8–P15）"),
        ("P22–P30", "CP2K 经典文章（作 AIMD 应用示例）"),
        ("P31", "学习资源"),
        ("P32–P33", "**优缺点（四大缺点清单，P33 明文含 BSSE）**"),
        ("P37–P41", "表面 terminal 与悬挂键"),
        ("P42–P49", "Wood 表面标记法 / 晶格矢量旋转（R30、√3×√3）/ 魔角石墨烯"),
        ("P50–P56", "异质结建模"),
        ("P57–P59", "画论文示意图"),
        ("P60–P64", "固-液界面 / MS Amorphous Cell"),
        ("P65–P68", "Packmol"),
    ]),
    ("L3.txt", 156, "CP2K 计算流程 + 输入参数全集（最核心的一份）", [
        ("P2–P3", "CP2K 计算流程封面 + 全流程图（输入/赝势/基组/坐标 → 计算 → 输出 → 分析）"),
        ("P24–P32", "**SCF**：通用参数（P24）/ 对角化（P25–P29）/ OT（P30–P32）/ 两者对比表（P30）"),
        ("P35–P36", "`&KIND`（元素 / 基组 / 赝势 / 磁性）"),
        ("P38–P43", "**基组详解**：SZV/DZVP/TZVP 命名（P39）、**BSSE 定义（P40）**、"
                    "**DZVP BSSE ≈5 kcal/mol≈0.22 eV（P41）**、**MOLOPT 与 SR 取舍 + 文献数据（P42）**"),
        ("P44", "赝势 POTENTIAL 详解"),
        ("P45–P46", "CELL 晶胞"),
        ("P46–P49", "COORD 与坐标读入"),
        ("P145", "有用教程链接"),
        ("P150–P154", "KIND 补充"),
    ]),
    ("L4.txt", 64, "振动光谱 TRAVIS + 电子结构分析", [
        ("P1", "版权声明"),
        ("P2–P8", "**TRAVIS 计算红外 IR 振动光谱**：是什么 / 安装 / CP2K 输出 Wannier 中心 / "
                  "wannier.xyz 格式 / 运行 / 绘图 / 替代方案（直接输出偶极）"),
        ("P9–P10", "电荷密度 cube / 自旋电荷密度"),
        ("P11–P16", "**电荷密度差分**：两种算法 / CO-Ni(100) 练习 / 显示控制 / 平面平均"),
        ("P17–P24", "**原子电荷**：定义与种类 / Bader / 原子盆 / 计算命令 / 练习 / 着色 / Löwdin·Hirshfeld·Mulliken"),
        ("P25–P26", "态密度 PDOS：关键字 + 画 DOS"),
        ("P27–P32", "电子结构分析案例"),
        ("P33–P41", "**电子局域函数 ELF**：定义与应用 / 数学 / 案例 / CP2K 计算"),
        ("P42–P43", "分子轨道 MO cube"),
        ("P44–P56", "**静电势 ESP / 功函数**：定义 / N₂ 静电势 / 功函数定义与公式 / "
                    "VASP 算功函数 / CP2K 算 / 异质结分析 / 负载团簇电子流向 / 分子表面 ESP / vdW 表面 / VESTA 练习"),
        ("P57–P60", "空页"),
        ("P61–P63", "计算警告：EMAX_SPLINE 太小 / RESTART wfn 不存在 / OT 收敛技巧"),
        ("P64", "版权声明"),
    ]),
    ("L5.txt", 53, "AIMD 模拟自由能势能面（三法）", [
        ("P1–P2", "版权 / 封面（方法一 PMF-Blue moon、方法二 Slow-growth、方法三 Metadynamics）"),
        ("P3–P6", "为什么用 AIMD 算 FES / 稀有事件 / 正则系综 / 限制性 constrained AIMD"),
        ("P7–P8", "**PMF 数学原理**"),
        ("P9", "collective variables 集体变量"),
        ("P10–P12", "PMF 文献案例"),
        ("P13–P15", "**VASP 限制性 AIMD 文件 ICONST**（注意：约束靠 ICONST，不是 MDALGO）"),
        ("P16–P21", "实例：H₂CO₃ 碳酸分解自由能面（PMF 法）"),
        ("P22–P25", "**方法二 Slow-growth（讲师推荐）**"),
        ("P26–P27", "**方法三 Metadynamics 原理**"),
        ("P28–P30", "metadynamics 文献案例"),
        ("P31", "Metadynamics INCAR（VASP）"),
        ("P32–P35", "实例：N₂ 解离吸附自由能垒"),
        ("P36", "输出文件 HILLSPOT"),
        ("P37–P38", "CV 震荡判据"),
        ("P39", "技巧：CV 选取"),
        ("P40–P42", "技巧：峰高 / 峰宽 / 重启 / 维度"),
        ("P43–P46", "练习：CP2K + QM/MM"),
        ("P47–P48", "**CP2K Metadynamics 定义 CV** + `&MOTION &FREE_ENERGY &METAVAR` 输入"),
        ("P49–P51", "CP2K 输出文件与绘图"),
        ("P52", "设置 WW（峰高）与 SCALE（峰宽）"),
        ("P53", "版权声明"),
    ]),
]

# 讲义 ↔ 字幕 的对应锚点（已核实，逐条给出双语行号/页码）
ANCHORS = [
    ("AIMD 基本流程与系综", "L1 P13–P18", "S1.1 全线", "字幕是讲师口述展开，讲义是公式骨架"),
    ("势能面/驻点/过渡态定义", "L1 P4–P7", "S1.1 731–1024 附近", "字幕另补了 DFT 理论回顾"),
    ("时间步长选择", "L1 P21–P22", "S1.1 1450–1600",
     "字幕给「最快振动周期 1/10 上限、1/20 常规」的推导"),
    ("Energy drift 与 EPS_SCF", "**L1 P27**", "S1.2 相关段",
     "讲义给三档定性判据：严重 / 300 ps 后明显 / 几乎没有"),
    ("周期性边界条件 PBC", "**L1 P28–P29**", "S1.1 2017–2150",
     "字幕补了晶胞三档经验与扩胞代价量化"),
    ("控温技术全谱", "L1 P31–P37", "S1.1 2296–2445", "字幕是热浴四法对比"),
    ("VASP AIMD：SMASS", "**L1 P43**", "S1.2 252–301",
     "−3=NVE；−1=NVT 速度调节法（退火专用）；≥0=Nosé–Hoover"),
    ("VASP AIMD：MDALGO", "**L1 P44**", "S1.2 385–396",
     "0=NVE；1=Andersen；2=Nosé–Hoover；3=Langevin"),
    ("AIMD 后处理：RDF", "L1 P63–P68", "S2 263–632",
     "字幕补「配位数必须球面积分」「必须用正交晶胞」"),
    ("AIMD 后处理：VACF/vDOS", "L1 P69–P72", "S2 633–971",
     "VASPKIT 727/728 取代旧脚本；vDOS 不等于红外谱"),
    ("AIMD 后处理：MSD/扩散", "L1 P75–P81", "S2 1058–1656",
     "多参考帧「先平方再平均」；D=斜率/6（二维用 /4）"),
    ("CP2K 优缺点四点清单", "**L2 P32–P33**", "**S2 2869–3019**",
     "讲义给骨架，字幕给对策与量化阈值（Γ 点需晶胞 ≥10 Å 等）"),
    ("**BSSE（基组重叠误差）**", "**L2 P33 + L3 P40–P42**",
     "**S2 2971–3007 / 4494–4529；S3 140–169 / 2211–2349**",
     "旧版误归第 4 天并判「零命中」，已更正；权威量化出处是 L3 P41–P42"),
    ("CP2K 编译与部署", "L2 P4–P15", "S2 1853–2123",
     "字幕补预编译版兼容判据（glibc 2.17 / Intel 2018.0.0）"),
    ("建模：表面/异质结/固液/团簇", "L2 P37–P68", "**S2 3062–4546**（近 1500 行）",
     "字幕是主体，讲义是骨架"),
    ("CP2K 输入参数全集", "L3 全线（156 页）", "S3 全线", "字幕逐段讲，与讲义一一对应"),
    ("SCF：OT vs 对角化", "L3 P24–P32", "S3 相关段",
     "字幕补「导体 OT 不可用」「k 点只对角化能加」"),
    ("k 点功能不完善", "L2 P33", "**S2 2919–2970；S3 4030–4053**",
     "字幕补：7.1 无对称性约化，VASP 用户会低估一个量级机时"),
    ("几何优化 / 晶胞优化", "L3 相应页", "S3 相关段",
     "字幕补 CELL_OPT 推荐 CG、CONSTRAINT Z 防真空层消失"),
    ("NEB / 过渡态", "L3 含 NEB 章节", "**S4 336–824**",
     "字幕是主战场：CP2K 可逐点分批算、coord.inc、K_SPRING 0.08/0.1"),
    ("频率计算", "L3 含频率章节", "**S4 1003–1625**",
     "字幕补虚频 ≥100 波数判据、cp2k_frequency.pl、末帧 tail -125"),
    ("DFT+U / 磁性", "L3 相应页", "S4 相关段 + S1.2 DFT+U 段",
     "不加 U 会定性错误；&KIND 自定义标签拆二/三价铁"),
    ("DFT-D3 色散", "L3 相应页", "**S4 4101–4198**",
     "dftd3.dat 必须复制到计算目录；截断半径 15 Å 与盒子尺寸耦合"),
    ("QM/MM", "L5 P43–P46", "S4 QM-MM 段 + S5 相关段", "讲义有练习，字幕有讲解"),
    ("振动光谱 TRAVIS", "**L4 P2–P8**", "**S5 8–265**",
     "讲义给操作；字幕给「为什么用 TRAVIS」（VASP 只能算 vDOS）"),
    ("电子结构：ELF/PDOS/电荷差分/原子电荷/功函数", "**L4 P9–P56**", "**S5 266–2201**",
     "字幕给 VESTA 操作与判读（黄=增、蓝青=减；B − C − D）"),
    ("自由能面 PMF/slow-growth/metadynamics", "**L5 P3–P52**", "**S5 2202–4519**",
     "讲义给原理与公式，字幕给 CV 选取、加墙与踩坑"),
]


# ---------------------------------------------------------------------------
# 已知的来源错误 → 生成时规范化（**必须放在生成器里**）
#
# 为什么不能只在 MAPPING.md 里手改：MAPPING.md 是**生成物**，`build()` 每次
# 都用 "w" 覆盖。精读报告在仓库外（`REPORT_DIR`），改报告只对当前这台机器有效；
# 把修正放在生成器里，任何人、任何来源目录重跑都不会把错误带回来。
#
# 每条修正都会在 stdout 报告「命中 / 未命中（源已是正确写法）/ 两侧都没找到」，
# 后两种都不会让生成静默失败。
# ---------------------------------------------------------------------------
REPORT_FIXES = [
    {
        "report": "S1_1.md",
        "wrong": "CO₂ 表面上",
        "right": "TiO₂ 表面上",
        "what": "`S1.1.txt` 分段表 `2017–2150` 行 —— Au₂₀ 负载团簇的**载体**"
                "（同一错字在源报告里共 3 处：§1 分段表 + 差分表 + 补充说明）",
        "why": [
            "旧值照抄了字幕的 **ASR 错字**：`S1.1.txt`:2073 逐字为"
            "「它模拟**二氧化碳**表面上金20团簇的一个这个，呃，负载的一个动态变化的一个过程」；"
            "同一段里 `AIMD`→`AAMD`、`晶胞`→`金包/精包`、`Au₂₀`→`歼20/精20`，"
            "是**纯语音转写**；**「二氧化钛（TiO₂）」被听成「二氧化碳（CO₂）」**"
            "（钛 tài / 碳 tàn 音近）。",
            "**CO₂ 是分子，根本不能充当「负载团簇的载体」** —— 旧值在化学上讲不通。",
            "讲义 `L1.txt` **PAGE 66**（第 969–973 行）原文：「完美的 **TiO₂** 表面上 Ti 和 Au "
            "没有化学键作用，但是在**有缺陷的 TiO₂** 表面上，Au₂₀ 金字塔结构坍塌，"
            "**形成 Ti-Au 化学键**。*J. Am. Chem. Soc.* **2013**, 135 (29), 10673-83.」"
            "—— 该文献即 *The Role of Reducible Oxide–Metal Cluster Charge Transfer in "
            "Catalytic Processes: New Insights on the Catalytic Mechanism of CO Oxidation "
            "on Au/TiO₂ from Ab Initio Molecular Dynamics*（doi 10.1021/ja402063v），"
            "正是 Au₂₀/TiO₂ 的 **AIMD** 论文，与「负载团簇的动态变化过程」完全对应。",
            "仓库自带真实算例同案：`references/h_tutorials/cases/TiO2-Au20_cp2k.inp`"
            "（TiO₂ + Au₂₀，`U_MINUS_J [eV] 13.6` 加在 Ti 上，与 `S4.txt`:2447–2448"
            "「对这个**钛**加了 13.6 个电子伏特」一致）。",
            "课程建模链条亦为 **TiO₂ 金红石 (110)**：切面 → 15 Å 真空层 → `Supercell` 5×3 → "
            "铅笔工具拉出 Au₂₀（讲义 `L2` P50；`S2.txt` 4402–4490）。",
        ],
        "rejected": "第二轮视频精读笔记（`videonotes/cp2k-1-1-AIMD第一讲-精读笔记` "
                    "L814–816 `[73:40–76:16]`、`videonotes/cp2k-2-…` L1634–1658）"
                    "据**同一句 ASR** 读成 **CeO₂**，属同一处 ASR 错误的**连带误推**，"
                    "本表不采用。同源更正记录另见 `course_learned.md` §1.8 与 §3.2 末条"
                    "（那两处也记录了 videonotes 的读法及其被否理由）。",
    },
]


APPLIED_FIXES = []      # [(fix, "applied"|"already"|"missing", n_replaced)]


# ---------------------------------------------------------------------------
# 「待判读」：**不改正文**，只在 §6 加提示
#
# 有些格子并没有抄错——报告忠实记录了课程画面/讲师原话——但**照字面读会得出
# 错误结论**。这类不能用 REPORT_FIXES 改字（改了就不忠实），也不该放着不管。
# 所以在 §6 里加一条带出处的提示，正文保持逐字。
# ---------------------------------------------------------------------------
REPORT_CAVEATS = [
    {
        "report": "S2.md",
        "anchor": "α-Al₂O₃ 识别为",
        "what": "`S2.txt` 分段表 `3098–3290` 行 —— VESTA 识别出的 α-Al₂O₃ 空间群",
        "note": [
            "该格写「VESTA 里加对称性会自动识别空间群（α-Al₂O₃ 识别为 **C2/m**）」。",
            "**这不是抄错**：课程画面/讲师口径确实是 `C2/m`（`S2.txt`:3263–3264"
            "「看到它对称性识别出来是这个空间群」），第二轮视频精读则读作 **R-3c**"
            "（`videonotes/cp2k-2-AIMD后处理与CP2K入门-精读笔记` L1234，把 ASR 的「CR-M」"
            "判为 R-3c）—— 同一画面两种读法。",
            "⚠️ **但晶体学事实是**：α-Al₂O₃（刚玉型）室温标准相属三方晶系、"
            "空间群 **`R-3c`（No. 167）**，`C2/m`（单斜，No. 12）与之不符。",
            "⇒ **处置（两说并列）**：**引用晶体学数据时用 `R-3c`**；"
            "**引述课程演示时**说「讲师现场 MS/VESTA 识别出的是 `C2/m`」。"
            "B 层同一处已按此口径写明（`references/course_learned.md` §3.2 末条附近）。",
            "要定案需要**回看该段录屏画面**，或核对 Materials Project `mp-1143`"
            "（该条目为 `R-3c`）。",
        ],
    },
]


def check_caveats():
    """核对每条「待判读」的锚点是否还在报告里（措辞变了要能发现）。"""
    out = []
    for cv in REPORT_CAVEATS:
        path = os.path.join(REPORT_DIR, cv["report"])
        found = False
        if os.path.isfile(path):
            txt = open(path, encoding="utf-8", errors="replace").read()
            found = cv["anchor"] in txt
        out.append((cv, found))
    return out


def apply_report_fixes(report, txt):
    """把 `REPORT_FIXES` 里属于本报告的修正应用到报告正文，并记录命中情况。

    记录 `n`（实际替换次数）而不是布尔值：万一将来源报告里出现**本该保留**的
    同形文字，次数会立刻偏离预期，从 stdout 就能看出来。
    """
    for fx in REPORT_FIXES:
        if fx["report"] != report:
            continue
        n = txt.count(fx["wrong"])
        if n:
            txt = txt.replace(fx["wrong"], fx["right"])
            APPLIED_FIXES.append((fx, "applied", n))
        elif fx["right"] in txt:
            APPLIED_FIXES.append((fx, "already", 0))
        else:
            APPLIED_FIXES.append((fx, "missing", 0))
    return txt


def render_corrections():
    """生成 `## 6. 更正记录` —— 随生成物一起输出，重跑不会丢。"""
    L = ["---\n", "## 6. 更正记录（生成物自带；修正写在 `build_mapping.py` 里）\n",
         "> 本文件由脚本生成，手改会在下次重跑时被覆盖。",
         "> 因此**凡是对来源报告的修正都登记在生成器 `REPORT_FIXES` 中**，",
         "> 并由本节把「改了什么、为什么」写进生成物，保证修正**可追溯、不会静默回退**。\n"]
    if not REPORT_FIXES:
        L.append("（无）\n")
        return L
    for i, fx in enumerate(REPORT_FIXES, 1):
        _hit = [t for f, t in
                [(f, (s, n)) for f, s, n in APPLIED_FIXES] if f is fx]
        status, n = (_hit[0] if _hit else ("not-run", 0))
        zh = {"applied": f"本次生成**已应用**（源报告仍是错的，替换 {n} 处）",
              "already": "本次生成**未触发**（源报告已是正确写法）",
              "missing": "⚠️ **两侧都没找到**——源报告措辞可能已变，请人工复核",
              "not-run": "本次生成未跑到该报告"}.get(status, status)
        L.append(f"### 更正 {i}：{fx['what']}\n")
        L.append(f"- 状态：{zh}")
        L.append(f"- `{fx['wrong']}` → **`{fx['right']}`**\n")
        L.append("- 依据：")
        for w in fx["why"]:
            L.append(f"  - {w}")
        L.append(f"- 未采用的另一读法：{fx['rejected']}\n")

    cavs = check_caveats()
    if cavs:
        L.append("### 待判读（**不改正文**，只加提示）\n")
        L.append("> 下列格子并非抄错——报告忠实记录了课程画面/讲师原话——")
        L.append("> 但**照字面读会得出错误结论**，故在此标注。正文保持逐字未动。\n")
        for i, (cv, found) in enumerate(cavs, 1):
            L.append(f"**{i}. {cv['what']}**\n")
            L.append("- 锚点核对：" + ("✅ 在报告中找到" if found
                                       else "⚠️ **锚点未在报告中找到**，措辞可能已变，请人工复核"))
            for n in cv["note"]:
                L.append(f"- {n}")
            L.append("")
    return L


def extract_section1(report):
    """从精读报告里取出 §1 主题分段表的 markdown 表格行。

    读进来先过一遍 `apply_report_fixes()` —— 精读报告在仓库外（课程资料工作区），
    某些错误是**照抄字幕 ASR 错字**造成的；若只在生成物里手改，重跑就被打回。
    所以修正在生成器里，且每次生成都报告"命中/未命中"，不让它静默变成空操作。
    """
    path = os.path.join(REPORT_DIR, report)
    if not os.path.isfile(path):
        return None
    txt = open(path, encoding="utf-8", errors="replace").read()
    txt = apply_report_fixes(report, txt)
    m = re.search(r"^##\s*1\.[^\n]*\n(.*?)^##\s*2\.", txt, re.S | re.M)
    if not m:
        return None
    rows = [ln.rstrip() for ln in m.group(1).splitlines()
            if ln.strip().startswith("|")]
    return rows or None


def parse_ranges(rows):
    """从表格行里抽出 (起, 止) 行号对，用于连续性校验。"""
    out = []
    for ln in rows:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if not cells:
            continue
        m = re.match(r"^(\d+)\s*[–\-~]\s*(\d+)$", cells[0])
        if m:
            out.append((int(m.group(1)), int(m.group(2))))
    return out


def check(ranges, total, name):
    """校验分段是否覆盖全文且无重叠。

    返回 (严重问题, 轻微提示)：
      * 严重 = 真有行号被两段同时覆盖（next.start < prev.end），或首尾没包住全文；
      * 轻微 = 相邻两段**共享一行**（next.start == prev.end）。
        这通常只是"闭区间写法"不一致（上一段把边界行含进去了，下一段又写了一遍），
        不影响定位，单独列出供人工判断，不算失败。
    """
    bad, minor = [], []
    if not ranges:
        return [f"{name}: 未解析到任何行号区间"], []
    if ranges[0][0] != 1:
        bad.append(f"{name}: 首段从第 {ranges[0][0]} 行开始，应为 1")
    if ranges[-1][1] != total:
        bad.append(f"{name}: 末段到第 {ranges[-1][1]} 行，应为 {total}")
    for i in range(1, len(ranges)):
        prev_end, start = ranges[i - 1][1], ranges[i][0]
        if start == prev_end:
            minor.append(f"{name}: 第 {i} 段与上一段共享第 {start} 行（闭区间写法）")
        elif start < prev_end:
            bad.append(f"{name}: 第 {i} 段起点 {start} 与上一段终点 {prev_end} "
                       f"**真重叠 {prev_end - start + 1} 行**")
    return bad, minor


def build(check_only=False):
    tables = {}
    problems = []
    minors = []
    for sfile, report, total, _desc in SUBTITLES:
        rows = extract_section1(report)
        if rows is None:
            problems.append(f"{report}: 未找到 §1 主题分段表（报告缺失或结构变了）")
            continue
        tables[sfile] = rows
        bad, minor = check(parse_ranges(rows), total, f"{report}({sfile})")
        problems.extend(bad)
        minors.extend(minor)

    # ---- 报告修正的命中情况：必须每次都报，不能静默变成空操作 ----
    for fx, status, n in APPLIED_FIXES:
        tag = {"applied": f"已应用（源报告仍错，替换 {n} 处）",
               "already": "未触发（源报告已是正确写法）",
               "missing": "⚠️ 两侧都没找到 —— 源报告措辞可能已变，请人工复核"
               }.get(status, status)
        print(f"· 修正[{fx['report']}] {fx['what'][:52]}…：{tag}")
        if status == "missing":
            problems.append(f"{fx['report']}: 报告修正未命中（`{fx['wrong']}` 与 "
                            f"`{fx['right']}` 都不在报告里）")

    if check_only:
        for m in minors:
            print("  · " + m)
        if problems:
            print("分段表校验发现问题：")
            for p in problems:
                print("  ✗ " + p)
            return 1
        print("分段表校验通过：6 份字幕均覆盖全文，无真重叠。"
              + (f"（另有 {len(minors)} 处共享边界行，属闭区间写法，不影响定位）"
                 if minors else ""))
        return 0

    L = []
    L.append("# 讲义 ↔ 字幕 严格对应表（MAPPING.md）\n")
    L.append("> 本文件由 `build_mapping.py` 生成（改精读报告后重跑即可刷新）。")
    L.append("> 定位：把课程资料的**两种组织方式**对应起来，使任何一句"
             "\"讲义 P X\"或\"字幕第 N 行\"都能互相定位。\n")
    L.append("**为什么要专门做对应表**：讲义是 **5 个按主题切分的 PPT deck（425 页），不是按天录的**；")
    L.append("字幕才是**按天**录的（5 天 6 文件 22133 行）。两者**多对多**，按编号硬对必然出错。")
    L.append("旧版 `course_survey.md` 只有一句\"对应 5 天的 PPT 讲义\"，而它\"每天讲什么\"是**抽样**得来的——")
    L.append("这正是 **BSSE 被误归到第 4 天、进而被判\"全文零命中、无法溯源\"**的根源。\n")
    L.append("---\n")

    L.append("## 1. 先记三条硬事实\n")
    L.append("1. **讲义编号 ≠ 天次**。`L1`=第 1 天；`L2`=CP2K 简介/编译/建模（第 2 天）；"
             "`L3`=参数全集（第 3 天）；**`L4`=第 5 天的电子结构**；**`L5`=第 5 天的自由能面**。")
    L.append("2. **第 4 天没有对应讲义**（NEB / 频率 / Au20 / QM-MM 只在字幕 `S4.txt` 里）。")
    L.append("3. **实际讲课进度比大纲慢半拍**：第 2 天补完了大纲第 1 天的后处理；第 3 天才讲大纲第 2 天的"
             "\"参数详解\"；第 4 天讲大纲第 3 天的过渡态 + 第 4 天的频率/DFT+U；第 5 天与大纲一致。"
             "大纲原文见 **`L1.txt` P2**。\n")

    L.append("---\n")
    L.append("## 2. 讲义（PDF）页 → 主题索引\n")
    for name, npages, topic, rows in PDF_INDEX:
        L.append(f"### `{name}`（{npages} 页）—— {topic}\n")
        L.append("| 页 | 主题 |")
        L.append("|---|---|")
        for pg, t in rows:
            L.append(f"| {pg} | {t} |")
        L.append("")

    L.append("---\n")
    L.append("## 3. 讲义 ↔ 字幕 对应锚点（已逐条核实）\n")
    L.append("| 主题 | 讲义 | 字幕 | 备注 |")
    L.append("|---|---|---|---|")
    for topic, pdf, sub, note in ANCHORS:
        L.append(f"| {topic} | {pdf} | {sub} | {note} |")
    L.append("")

    L.append("---\n")
    L.append("## 4. 字幕逐段主题表（覆盖全文，无空档）\n")
    L.append("> 行号可直接与 `S*.txt` 对照（字幕原文按 1:1 落库，**行号未变**）。\n")
    for sfile, report, total, desc in SUBTITLES:
        L.append(f"### `{sfile}` —— {desc}")
        L.append(f"（共 {total} 行；分段表来自精读报告 `{report}`）\n")
        rows = tables.get(sfile)
        if rows:
            L.extend(rows)
        else:
            L.append(f"> ⚠️ 缺分段表：未找到 `{report}` 的 §1。")
        L.append("")

    L.append("---\n")
    L.append("## 5. 怎么用这张表\n")
    L.append("- 要查**某个知识点的课程原文**：先在上表定位主题 → 拿到页码/行号 → 回 "
             "`L*.txt` / `S*.txt` 核对。")
    L.append("- 要判断**某说法是讲义有还是字幕独有**：看同一行的\"讲义\"与\"字幕\"两列是否都有内容。")
    L.append("- 引用规范：讲义写 `L3 P40–P42`；字幕写 `S2.txt:2971–3007`。")
    L.append("- **发现本表与原文不符时，以原文为准并回来修本表**（本表是索引，不是权威）。\n")

    L.extend(render_corrections())

    out = os.path.join(HERE, "MAPPING.md")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))
    print(f"WROTE {out}  ({len(L)} 行)")

    if minors:
        print(f"\n· {len(minors)} 处相邻段共享边界行（闭区间写法差异，不影响定位）：")
        for m in minors:
            print("  · " + m)
    if problems:
        print("\n⚠️ 分段表校验发现**真重叠/缺口**（已照常写出，但需人工复核）：")
        for p in problems:
            print("  ✗ " + p)
        return 1
    print("分段表校验通过：6 份字幕均覆盖全文，无真重叠。")
    return 0


def main():
    ap = argparse.ArgumentParser(description="生成/校验 讲义↔字幕 对应表")
    ap.add_argument("--check", action="store_true", help="只校验分段表，不写文件")
    args = ap.parse_args()
    return build(check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
