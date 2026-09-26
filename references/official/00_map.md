# 00 · 官网与官方手册内容地图

> **来源**：
> - <https://www.cp2k.org/>（DokuWiki 站，导航页 / HowTo / 教程 / 资源）
> - <https://manual.cp2k.org/trunk/>（Sphinx 手册，方法论 / 技术 / 输入参考）
> **抓取日期**：2026-09-08

---

## 1. 两个站点分工

| 站点 | 技术栈 | 内容定位 | 什么时候去 |
|---|---|---|---|
| `www.cp2k.org` | DokuWiki | 项目门户：概述、功能、HowTo、教程、文档、社区 | 找教程、找 HowTo、查"CP2K 能做什么"、查引用格式 |
| `manual.cp2k.org/trunk` | Sphinx | 官方手册：方法论详解、技术专题、**完整输入参考**、术语、单位、变更日志 | 查关键字语义与默认值、读方法论、查版本变更 |

**关键事实**：`www.cp2k.org/howto` 页面明确说明——**大多数 howto 已迁移到 `manual.cp2k.org`**。所以遇到 howto 列表里点不动的条目，优先去手册找。

---

## 2. www.cp2k.org 导航结构

| 路径 | 内容 | G 层落点 |
|---|---|---|
| `/` | 项目概述、能力摘要、引用要求、GPL 许可、无担保声明 | `10_features_resources.md` |
| `/features` | **完整功能清单**（DFT / AIMD / QM/MM / NEB / 半经验 / 经典 MD / 元动力学 …） | `10_features_resources.md` |
| `/quickstep` | Quickstep 模块原理（GPW/GAPW、OT、精度与效率、参考文献） | `02_dft_methods.md` |
| `/howto` | 全部 HowTo 清单（安装类 / 基础类 / 进阶类） | `00_map.md` §4 |
| `/docs` | Talks / Posters / Workshops / Technical Reports / Theses / Books | `10_features_resources.md` |
| `/exercises` | 历年培训课程练习集（2014–2025） | `00_map.md` §5 |
| `/faq` | FAQ 目录（19 条） | `08_errors_and_faq.md` |
| `/howto:dft_u` | DFT+U 完整教程（含 FeO EOS 算例与能量表） | `02_dft_methods.md` |
| `/howto:static_calculation` | 静态计算完整教程（Si bulk8 全输入 + 输出详解） | `01_global_and_units.md` / `03_scf_convergence.md` |
| `/periodicity` | **周期性约定**（胞 0→h 不中心化、`CENTER_COORDINATES`、两处周期性应一致） | **本文件 §2.1** |
| `/tools` | **23 个第三方工具 + GTH 势 + 3 个脚本仓库** | **本文件 §2.2** |
| `/science` | **79 个应用案例**（论文 + 期刊 + 作者） | **本文件 §2.3** |
| `/version_history` | **跳转页**（→ manual changelog） | **本文件 §2.4** |
| `/videos` | **跳转 YouTube 频道**（2020-08-29） | **本文件 §2.4** |
| `/tutorials` | **已改名 howto**，多数已移至 manual | **本文件 §2.4** |

### 2.1 `/periodicity`（周期性约定，官方全文）

> 来源：`https://www.cp2k.org/periodicity`（最后修改 2021/11/05）

**官方原文要点**：

- **CP2K 针对周期性计算做了优化，而且周期性是默认行为。** 不过仍可以做其它类型的计算。
- **★ 最重要的约定（官方强调）**：**胞按惯例从 0 到 h，而不是从 −h/2 到 h/2。**
  **因此若想把团簇放在胞中心，要放在 h/2 而不是 0。**
- **自动化做法**：用 `FORCE_EVAL/SUBSYS/TOPOLOGY/CENTER_COORDINATES`。
  **官方说明**：**对某些泊松求解器，这是被推荐的**，以确保**电子密度在胞的非周期面上为零**。
- **邻居列表的周期性**（因而也是高斯 collocation/integration 的周期性）
  由关键字 `FORCE_EVAL/SUBSYS/CELL#PERIODIC` 控制。
- **泊松求解器（静电）**在 `FORCE_EVAL/DFT/POISSON` 段中控制，
  用 `POISSON_SOLVER` 关键字选择。**官方提醒：并非所有求解器都支持所有周期性。**
- **泊松求解器的周期性**设在 `FORCE_EVAL/DFT/POISSON#PERIODIC`，
  **所选的泊松求解器应支持它**。
- **官方结论**：**大多数情况下，泊松求解器与子体系的周期性设置应当一致。**

> **[G层提示]** 这条与 `23_dft_subpages_full.md` §3 的官方新表述（"边界条件是物理模型的一部分，不只是数值设置"）
> **互相印证**：官网这页是**较早（2021）**的简短版本，手册那页是**较新的详细版本**。
> 两者不冲突，**以手册为准**；本页的"胞 0→h 不中心化"是手册未强调的**实操细节**，值得单独记住。

### 2.2 `/tools`（第三方工具清单，官方全文）

> 来源：`https://www.cp2k.org/tools`（最后修改 2023/11/10）

官方标题：**"Tools for simplifying your life with CP2K"**。

#### 与 CP2K 交互的第三方软件（23 项）

| # | 工具 | 说明 |
|---|---|---|
| 1 | **AiiDA** | Workflow and Provenance Engine |
| 2 | **AML** | Python Package |
| 3 | **Atomic Simulation Environment (ASE)** | 原子模拟环境 |
| 4 | **Basis Set Exchange** | 基组交换平台 |
| 5 | **cp2k-basis** | Browse Basis-sets and Pseudos |
| 6 | **Cubecruncher** | cube 文件处理 |
| 7 | **Gromacs QM/MM** | GROMACS 的 QM/MM 接口 |
| 8 | **GRRM** | Global Reaction Route Mapping |
| 9 | **i-PI** | a universal force engine |
| 10 | **Avogadro 1 输入生成器与输出可视化** | — |
| 11 | **Avogadro 2 输入生成器** | — |
| 12 | **Libra** | Quantum-Classical Non-Adiabatic Dynamics |
| 13 | **Phonopy** | 声子计算 |
| 14 | **GNU EMACS 插件** | 编辑器集成 |
| 15 | **Sublime Text 3 插件** | 编辑器集成 |
| 16 | **Vim 插件** | 编辑器集成 |
| 17 | **Pwtools** | pre- and postprocessing |
| 18 | **PYCP2K** | a python interface to CP2K |
| 19 | **PyRETIS** | rare events in Python |
| 20 | **SeeK-path** | the k-path finder and visualizer |
| 21 | **TAMkin** | A Package for Vibrational Analysis and Chemical Kinetics |
| 22 | **the NOMAD Repository** | 数据仓库 |
| 23 | **UCSF Chimera Plugins** | 用于 TETR 和 LEV00 |

#### 基组与势

- **Goedecker-Teter-Hutter (GTH) pseudopotential parameter sets**。

#### 来自 CP2K 用户与开发者的脚本仓库

- **Tiziano Müller 的简单 Python 脚本**：mangle/generate cp2k input/output。
- **Peter Mamonov 的 PyMOL `&QMMM` 段生成器**。
- **Guillaume Le Breton 的 Python 包**：读取含时 CP2K 输出，为实时分析提供工具。

> **[G层提示]** 与 `12_authority_sources.md` / `19_performance_gpu_community.md` 对照：
> 该页是**官方认定的第三方生态清单**，但**第三方工具本身不是官方资料**（权威性分级为 L3 或更低）。

### 2.3 `/science`（79 个应用案例，官方全文）

> 来源：`https://www.cp2k.org/science`

官方按**主题**组织，每项给出**论文标题 + 期刊 + 年份 +（部分）作者**。共 **79 个案例**。

**最新案例（2025–2026）**：

| 主题 | 期刊 / 年份 |
|---|---|
| Optical Detection of Exchange Physics | The Journal of Physical Chemistry Letters **2026** |
| **Support for Skala through GauXC** | **arXiv**（并给出手册链接） |
| XAS for Single Molecule-Magnet | The Journal of Physical Chemistry Letters **2025** |
| Design of STM Tips for Spin-State Modulation | Nano Micro Small **2025** |
| Transport in confined electrolytes | The Journal of Chemical Physics **2025** |

**代表性主题（按年份）**：

| 主题 | 期刊 / 年份 |
|---|---|
| Charge Transfer to Solvent | Nature Communications 2024 |
| Core-hole Clock Spectroscopy | PCCP 2024 |
| HCOOH-Saturated TiO₂ | JPCL 2023 |
| Nanoconfined Water | Nature 2022 |
| Solvated Electron | Angewandte Chemie 2022 |
| Electrochemical Interfaces | PNAS 2022 |
| Single Atom Electrocatalyst | Nature Communications 2022 |
| Solvated Electron in Methanol | Chemical Science 2022 |
| Osmotic Transport in Nanofluidics | ACS Nano 2021 |
| Solvated Electrons | Nature Comm. 2021 |
| Nuclear Quantum Effects at Metal Interfaces | — |

> **[G层提示]** `/science` 是**官方为"用 CP2K 做了什么"做的展示页**，
> 也是 `faq:contribute` 中"把工作摘要加到 science 页"的**投稿目标**。
> **它同时是官方证据链的一环**：`Support for Skala through GauXC` 案例直接印证了
> `23_dft_subpages_full.md` §2 的 GauXC 内容属于**已在产出科学结果的官方功能**。

### 2.4 三个跳转/改名页（官方现状）

| 页面 | 官方原文 / 状态 |
|---|---|
| `/version_history` | **"This page has been moved to https://manual.cp2k.org/trunk/changelog.html"**（最后修改 2026/07/15）。**G 层内容见 `11_version_changelog.md`** |
| `/videos` | **"For videos please go to our Youtube channel."**（最后修改 2020/08/29） |
| `/tutorials` | 页面标题已变为 **howto**；正文首句：**"Most howtos have been moved to https://manual.cp2k.org."** 完整清单见 §4 |

> **[G层提示]** 这三页**本身无技术内容**，但**它们的"跳转"状态本身是信息**：
> 说明官方把**版本历史、教程、视频**分别迁到了 manual / howto / YouTube。
> 查这些主题时**不要停在官网原页**。


---

## 3. manual.cp2k.org 导航结构

### 3.1 Getting Started

| 页面 | 内容 | G 层落点 |
|---|---|---|
| `getting-started/installation.html` | 安装前 6 项考虑清单（OS / root / 联网 / module / 异构节点 / 工作站 GPU） | `09_build_libraries.md` |
| `getting-started/first-calculation.html` | h2o 单点能完整示例；4 个可执行文件含义；结果检查 | `01_global_and_units.md` |
| `getting-started/troubleshooting.html` | **故障排查**：I/O 基础 + 六类问题 | `08_errors_and_faq.md` |

### 3.2 Methods（方法论）

```
Methods
├── DFT
│   ├── gpw                     ← 高斯平面波
│   ├── gapw                    ← 高斯增广平面波（全电子）
│   ├── hartree-fock/
│   │   ├── admm                ← 辅助密度矩阵法
│   │   ├── ri_gamma            ← Γ 点 HFX-RI
│   │   └── ri_kpoints          ← k 点 HFX-RI
│   ├── pseudopotentials        ← 赝势
│   ├── k-points                ← k 点采样（含功能兼容表）
│   ├── orbital_transformation  ← OT 方法
│   ├── convergence             ← SCF 收敛
│   ├── cutoff                  ← CUTOFF/REL_CUTOFF 收敛
│   ├── local_ri                ← LRIGPW
│   ├── constrained             ← CDFT（含 CDFT-CI）
│   ├── cneo                    ← CNEO-DFT
│   ├── linear_scaling          ← 线性标度（占位页）
│   └── gauxc                   ← 外部 XC 积分器
├── Post-HF
├── Semi-Empiricals
├── Machine Learning
├── Embedding
│   ├── kim-gordon
│   └── qm_qm                   ← 量子嵌入（占位页）
├── QM/MM
├── Sampling
│   ├── molecular_dynamics      ← MD（含系综/温控/压控/平衡）
│   ├── constrained_dynamics
│   ├── newton-x
│   └── ehrenfest
├── Optimization
│   ├── geometry_and_cell_opt   ← 几何/晶胞优化
│   └── nudged_elastic_band     ← NEB（占位页）
├── Electronic-structure Analysis
│   └── population/             ← 布居分析、RESP
├── Properties
│   ├── optical/                ← TDDFT / BSE / RTBSE / 振动光谱
│   ├── x-ray/                  ← ΔSCF / TDDFT / δ-kick / 校正方案
│   ├── infrared                ← 红外（占位页）
│   ├── raman
│   ├── nmr
│   └── stm_images
└── Restarting                  ← 重启（波函数/MD/NEB/CDFT）
```

### 3.3 Technologies

| 页面 | 内容 | G 层落点 |
|---|---|---|
| `technologies/eigensolvers/index.html` | 本征求解器总览（ScaLAPACK 为 MPI 必需；GPU 库可选） | `09_build_libraries.md` |
| `technologies/eigensolvers/dlaf.html` | DLA-Future | `09_build_libraries.md` |
| `technologies/accelerators/index.html` | CUDA / HIP-ROCm | `09_build_libraries.md` |
| `technologies/accelerators/opencl.html` | OpenCL 后端 | `09_build_libraries.md` |
| `technologies/libraries.html` | **30 个外部库**的依赖关系与 CMake 开关 | `09_build_libraries.md` |

### 3.4 References

| 页面 | 内容 | G 层落点 |
|---|---|---|
| `CP2K_INPUT.html` | 完整输入参考（所有 SECTION 与关键字） | 分散在各专题文件 |
| `bibliography.html` | 参考文献库 | `10_features_resources.md` |
| `acronyms.html` | 缩写表（约 130 条） | `10_features_resources.md` |
| `units.html` | 单位表 | `01_global_and_units.md` |

### 3.5 其它

| 页面 | 内容 | G 层落点 |
|---|---|---|
| `changelog.html` | 版本变更日志（2.0 – 2027.1） | `11_version_changelog.md` |
| `versions.html` | 旧版手册入口（2026.2 / 8.2 / 8.1 / 7.1 / 2.6） | `11_version_changelog.md` |

---

## 4. www.cp2k.org/howto 完整清单

官方注明：**大多数 howto 已迁移到 manual.cp2k.org**。以下为原清单（保留原分类）。

### 4.1 安装 / 编译类（8 项）

| HowTo | 说明 |
|---|---|
| `howto:install_with_plumed` | 与 PLUMED 一起编译 |
| `howto:cuda` | CUDA 加速构建 |
| `howto:cygwin` | Cygwin 下构建 |
| `howto:windows` | Windows 下构建 |
| `howto:macos` | macOS 下构建 |
| `howto:cray` | CRAY 平台构建 |
| `howto:container` | 容器化部署 |
| `howto:toolchain` | CP2K toolchain 脚本 |

### 4.2 基础类（5 项）

| HowTo | 说明 |
|---|---|
| `howto:static_calculation` | 静态单点能 + 力（Si bulk8 完整算例） |
| `howto:converging_cutoff` | CUTOFF / REL_CUTOFF 收敛 |
| `howto:dft_u` | DFT+U（FeO EOS 完整算例） |
| `howto:restart` | 重启 |
| `howto:kpoints` | k 点 |

### 4.3 进阶类（6 项）

| HowTo | 说明 |
|---|---|
| `howto:pgo` | 全局优化（PGO） |
| `howto:stm` | STM 图像模拟 |
| `howto:cp2k_omen` | 与 OMEN 量子输运代码耦合 |
| `howto:shifter` | Shifter 容器 |
| `howto:cp2k-basis` | 基组工具 |
| `howto:libsmm_arguments_too_long` | libsmm 构建报错处理 |

---

## 5. www.cp2k.org/exercises 教程索引（2014–2025）

> **★ 已完整采集（2026-09-09）**：本节只是**索引级**概览。
> 全部 **21 个课程命名空间 / 248 个子页**（其中 **239 页有正文**，约 170 万字符）
> 已采集落盘到 **`24_official_exercises.md`**，含 NEB 完整输入、AIMD/系综/SGCP/i-PI、
> EOS/PDOS/能带/电荷密度差/功函数、以及全部 239 页的清单。

官方说明：这是**历年培训课程用过的练习集**。

| 年份 | 课程 | 主办 |
|---|---|---|
| 2025 | Computational Methods in Crystallography | CECAM, EPFL |
| 2021 | Statistical Mechanics and Molecular Simulations | UZH |
| 2020 | Statistical Mechanics and Molecular Simulations | UZH |
| 2020 | International Winter School on Electronic Structure Calculations | UPB, PC2 |
| 2019 | Statistical Mechanics and Molecular Simulations | UZH |
| 2019 | Introduction to CP2K | Ghent University |
| 2019 | CONEXS Summer School | Newcastle University |
| 2018 | CP2K User Tutorial: "Computational Spectroscopy" | UPB, PC2 |
| 2018 | Molecular and Materials Modelling | ETHZ |
| 2018 | Statistical Mechanics and Molecular Simulations | UZH |
| 2018 | CP2K-UK Summer School | UoL, STFC |
| 2018 | CHE437 Condensed Matter Electronic Structure Theory | UZH |
| 2017 | Molecular and Materials Modelling | ETHZ |
| 2017 | Statistical Mechanics and Molecular Simulations | UZH |
| 2017 | CP2K User Tutorial: "Advanced ab-initio MD methods" | UZH |
| 2017 | CHE437 Condensed Matter Electronic Structure Theory | UZH |
| 2016 | CP2K Summer School 2016 | KCL |
| 2016 | Molecular and Materials Modelling | ETHZ |
| 2016 | CHE437 Condensed Matter Electronic Structure Theory | UZH |
| 2015 | CECAM 4th CP2K Tutorial | CECAM-ETHZ |
| 2015 | Molecular Simulations | UZH |
| 2015 | Molecular and Materials Modelling | ETHZ |
| 2015 | A one day introduction to CP2K | PITT |
| 2014 | Molecular and Materials Modelling | ETHZ |
| 2014 | Molecular Simulations | UZH |

### 5.1 与 NEB 直接相关的官方练习（官方在 NEB 占位页列出）

> **正文已采集** → `24_official_exercises.md` §1（7 页完整输入）。

- `exercises:common:neb`
- `exercises:2018_uzh_cmest:path_optimization_neb`
- `exercises:2017_ethz_mmm:nudged_elastic_band`
- `exercises:2015_cecam_tutorial:neb`

### 5.2 其它官方在占位页给出的高价值外链

| 主题 | 外链 |
|---|---|
| 线性标度 DFT | `exercises:2017_ethz_mmm:ls_scf` |
| 红外光谱 | `exercises:2018_ethz_mmm:infrared_2018` |
| 光谱学通用 | <https://brehm-research.de/spectroscopy> |
| 量子嵌入 | `_media/events:2017_dev_meeting/rybkin_cp2kdev-meeting_zurich2017-7.pdf` |

---

## 6. 官方明确的"从哪学起"路径

综合官方各页面的指引，一条稳妥的入门路径是：

```
1. manual.cp2k.org/trunk/getting-started/installation.html   → 环境准备
2. manual.cp2k.org/trunk/getting-started/first-calculation.html → 跑通第一个算例（h2o 单点）
3. www.cp2k.org/howto:static_calculation                      → 完整输入结构讲解（Si bulk8）
4. manual.cp2k.org/trunk/methods/dft/cutoff.html              → 收敛自己的 CUTOFF/REL_CUTOFF
5. manual.cp2k.org/trunk/methods/dft/convergence.html         → 学会让 SCF 收敛
6. 按研究方向选：sampling/molecular_dynamics 或 optimization/geometry_and_cell_opt
7. 需要性质 → manual.cp2k.org/trunk/methods/properties/
8. 报错 → manual.cp2k.org/trunk/getting-started/troubleshooting.html
```

官方在 `first-calculation.html` 末尾给出了 "Next Steps" 指引，方向与本表一致。

---

## 7. 交叉索引

| 想查 | 去 |
|---|---|
| 关键字默认值 | `01_global_and_units.md`（GLOBAL 部分）、`02`–`07` 各专题 |
| 能不能算某类体系/性质 | `10_features_resources.md`（官方功能全清单） |
| 某报错什么意思 | `08_errors_and_faq.md` |
| 某版本改了什么 | `11_version_changelog.md` |
| 官方没写的内容 | `_sources.md` 缺口清单 → 转 A/F 层 |
| 实战调参经验 | F 层 `../playbook.md` |
| 讲师口径与硬规则 | A 层 `../decide.md` |
