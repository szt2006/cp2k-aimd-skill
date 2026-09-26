# 12 · CP2K 资料权威性分级与来源核实

> **来源**：
> - <https://github.com/cp2k/cp2k>（官方仓库 README 的 Links 节，是官方自己声明的"哪些渠道是官方的"）
> - <https://dashboard.cp2k.org/>（官方回归测试仪表盘）
> - <https://groups.google.com/group/cp2k>（官方邮件列表 / 论坛）
> - <https://pubs.aip.org/aip/jcp/article/152/19/194103/1931750>（官方参考论文）
> - <https://manual.cp2k.org/trunk/development/onboarding.html>（官方开发流程）
> **抓取日期**：2026-09-09

---

## 0. 本文件的作用

用户提问："查找 cp2k 相关的官方、权威资料，**先确认其官方、权威性**"。

本文件回答：**哪些来源算官方、哪些算权威、判定依据是什么**。
判定依据全部来自官方自我声明（GitHub README 的 Links 节 + 官网 + 手册），**不靠主观印象**。

> **G 层原则不变**：本文件只记录可核实的官方声明与客观事实，不写"我觉得这个网站挺权威"。

---

## 1. 权威性分级（4 级）

| 级别 | 定义 | 判定依据 | 用途 |
|---|---|---|---|
| **L0 官方一手** | 由 CP2K 项目自己发布、自己维护 | 官方仓库 README 的 Links 节列出，或官网/手册子域 | **可作为最终依据**；G 层只收这一级 |
| **L1 官方同行评审** | CP2K 核心开发者署名、经同行评审发表 | 作者含项目创建者/维护者；期刊为同行评审 | 引用与理论依据；方法细节的最终背书 |
| **L2 官方衍生/社区** | 官方账号运营、但内容由社区产生 | 官方 README 明确推荐作为求助渠道 | 定位线索、经验参考；**结论需回 L0 复核** |
| **L3 第三方** | 非 CP2K 项目发布 | — | 仅供参考，**不入 G 层** |

---

## 2. L0 官方一手来源（逐个核实）

### 2.1 官方站点清单（**依据：官方 GitHub README 的 Links 节原文**）

官方仓库 README 原文列出：

> - [CP2K.org](https://www.cp2k.org) for showcases of scientific work, tutorials, exercises, presentation slides, etc.
> - [The manual](https://manual.cp2k.org/) with descriptions of all the keywords for the CP2K input file
> - [The dashboard](https://dashboard.cp2k.org) to get an overview of the currently tested architectures
> - [The Google group](https://groups.google.com/group/cp2k) to get help if you could not find an answer in one of the previous links
> - [Acknowledgements](https://www.cp2k.org/funding) for list of institutions and grants that help to fund the development of CP2K

**这段是判定官方性的黄金依据**——官方自己列出了 5 个渠道。据此：

| # | 来源 | URL | 级别 | 官方自述定位 |
|---|---|---|---|---|
| 1 | 官网 | <https://www.cp2k.org> | **L0** | 科学工作展示、教程、练习、幻灯片 |
| 2 | 官方手册 | <https://manual.cp2k.org> | **L0** | 输入文件**所有关键字**的说明 |
| 3 | 官方仪表盘 | <https://dashboard.cp2k.org> | **L0** | 当前测试的架构概览 |
| 4 | 官方 Google Group | <https://groups.google.com/group/cp2k> | **L2** | 找不到答案时求助 |
| 5 | 资助致谢页 | <https://www.cp2k.org/funding> | **L0** | 资助机构与基金列表 |

### 2.2 官方代码与数据仓库（**依据：同一 README**）

README 的 Directory organization 节原文：

> - `src`: The source code
> - `data`: Simulation parameters e.g. basis sets and pseudopotentials
> - `docs`: The markdown source pages for documentations that is rendered as the manual
> - `tests`: Inputs for tests and regression tests
> - `tools`: Mixed collection of useful scripts related to CP2K
> - `benchmarks`: Inputs for benchmarks

| # | 来源 | URL | 级别 | 说明 |
|---|---|---|---|---|
| 6 | 主仓库 | <https://github.com/cp2k/cp2k> | **L0** | 源码、测试、工具、基准 |
| 7 | 数据仓库 | <https://github.com/cp2k/cp2k-data> | **L0** | 基组与赝势参数文件（**`data/` 的独立仓库**） |
| 8 | DBCSR 库 | <https://github.com/cp2k/dbcsr> | **L0** | 稀疏矩阵库，官方子项目 |
| 9 | 示例仓库 | <https://github.com/cp2k/cp2k-examples> | **L0** | 官方示例输入（如 BSE、image charges） |
| 10 | GTH 赝势索引 | <https://cp2k.org/static/potentials/> | **L0** | 官方托管的赝势下载页 |

> **重要**：`docs/` 目录是手册的 **Markdown 源**，手册由它渲染。因此"手册页面"与"仓库 docs 目录"同源，**互为印证**。

### 2.3 官方域名边界（避免把仿冒站当官方）

| 域名 | 是否官方 | 依据 |
|---|---|---|
| `cp2k.org` / `www.cp2k.org` | ✅ 官方 | README 列出 |
| `manual.cp2k.org` | ✅ 官方 | README 列出 |
| `dashboard.cp2k.org` | ✅ 官方 | README 列出 |
| `github.com/cp2k/*` | ✅ 官方 | 官方组织账号 |
| `groups.google.com/group/cp2k` | ✅ 官方指定 | README 列出 |
| 其它含 "cp2k" 的站点 | ❌ 非官方 | 未在官方 Links 中出现 |

---

## 3. L1 官方同行评审来源

### 3.1 CP2K 参考论文（标准引用）

| 项 | 内容 |
|---|---|
| 标题 | *CP2K: An electronic structure and molecular dynamics software package — Quickstep: Efficient and accurate electronic structure calculations* |
| 作者 | Thomas D. Kühne, Marcella Iannuzzi, Mauro Del Ben, Vladimir V. Rybkin, Patrick Seewald, Frederick Stein, Teodoro Laino, Rustam Z. Khaliullin, Ole Schütt, Florian Schiffmann, Dorothea Golze, Jan Wilhelm, Sergey Chulkov, Mohammad Hossein Bani-Hashemian, Valéry Weber, Urban Borštnik, Mathieu Taillefumier, Alice Shoshana Jakobovits, Alfio Lazzaro, Hans Pabst, Tiziano Müller, Robert Schade, Manuel Guidon, Samuel Andermatt, Nico Holmberg, Gregory K. Schenter, Anna Hehn, Augustin Bussy, Fabian Belleflamme, Gloria Tabacchi, Andreas Glöß, Michael Lass, Iain Bethune, Christopher J. Mundy, Christian Plessl, Matt Watkins, Joost VandeVondele, Matthias Krack, Jürg Hutter（**共 39 位**） |
| 期刊 | *The Journal of Chemical Physics* **152**, 194103 (2020) |
| DOI | `10.1063/5.0007045` |
| 类型 | Research Article；**Open Access**；**Editor's Pick** |
| 所属专题 | JCP Special Topic on Electronic Structure Software / Chemical Physics Software Collection |
| 收/审 | Received 2020-03-10；Accepted 2020-04-22 |

**权威性判定**：

1. **作者含项目创建者与主要维护者**——Jürg Hutter（苏黎世大学）、Thomas D. Kühne（Paderborn）、Matthias Krack（PSI）、Joost VandeVondele 等，即 CP2K 的核心团队。
2. **经同行评审**（Received/Accepted 日期明确，JCP 正式 Research Article）。
3. **被官方手册引用**——`methods/dft/index.html` 的 References 节列出 `Kühne2020`；TDDFT 页、BSE 页等亦引用手册 bibliography 中的条目。
4. **属官方专题集**（Electronic Structure Software）。

→ **判定：L1，可作为方法层面的权威背书。**

### 3.2 手册 bibliography 中的方法论文（L1）

官方手册维护统一参考文献库 `manual.cp2k.org/trunk/bibliography.html`，各方法页以 `[作者年份]` 引用。这些是**官方认可的方法出处**。

本轮新采集页面中出现的条目（示例）：

| 条目 | 用途 |
|---|---|
| `Kühne2020` | CP2K 总览（官方手册 DFT 页引用） |
| `Iannuzzi2026` | 官方手册 DFT / 赝势页引用（新） |
| `Strand2019` (`10.1063/1.5078682`) | TDDFT 实现 |
| `Hehn2022` | 激发态梯度（自旋守恒） |
| `HernandezSegura2025` | 自旋翻转激发态能量与梯度 |
| `Iannuzzi2005` | 早期 TDDFT 实现 |
| `Guidon2010` | ADMM |
| `Grimme2016` | sTDA / GFN1-xTB 参数 |
| `Graml2026` | BSE 理论与实现、精度基准 |
| `Golze2013` | Image-Charge QM/MM |
| `Goedecker1996` | GTH 赝势（Phys. Rev. B **54**, 1703 (1996)） |
| `Hartwigsen1998` | GTH 赝势 H→Rn（Phys. Rev. B **58**, 3641 (1998)） |
| `Krack2005` | H→Kr 的 GTH 优化版（Theor. Chem. Acc. **114**, 145 (2005)） |
| `Komeiji2007` (`10.1273/cbij.7.12`) | 蓝月亮系综度量项 |
| `vanSetten2015` | BSE 示例 H2 几何 |
| `Mewes2018` | 激子描述符定义 |
| `Liu2020` | FHI-aims 的 BSE 实现（对比基准） |

→ **判定：L1。方法细节的最终依据是手册正文 + 其 bibliography。**

### 3.3 官方引用的外部软件/文献（L3，但被官方背书）

官方页面会引用第三方工具与文献（如 `brehm-research.de/spectroscopy`、`github.com/grimme-lab/stda`）。这些**本身是 L3**，但因为是**官方页面主动给出的**，在本层标注为"官方指出的外部参考"，不作为最终依据。

---

## 4. L2 官方衍生 / 社区来源

### 4.1 官方 Google Group

| 项 | 内容 |
|---|---|
| 群组名 | `cp2k` |
| URL | <https://groups.google.com/group/cp2k> |
| 欢迎语 | "Welcome to the discussion forum on cp2k (<http://www.cp2k.org>)." |
| 官方地位 | **官方 README 明确列为求助渠道** |
| 规模 | 约 **6786 个讨论主题**（截至 2026-09-09 抓取时） |
| 活跃度 | 帖子日期连续（抓取时可见 7 月 30 日 – 9 月 7 日） |
| 参与者 | 含核心开发者（Jürg Hutter、Thomas Kühne、Frederick Stein、Johann Pototschnig 等） |

**权威性判定**：
- **官方性**：✅ 有——官方 README 列为官方求助渠道。
- **内容权威性**：⚠️ **不等同于手册**——帖子是个人答复，未经过文档审校。
- **正确用法**：**定位线索**（"我这个问题属于哪一类"）→ 然后回手册/源码复核。
- **错误用法**：把论坛答复当最终依据。

> 上一轮我曾在抓取时怀疑"页面没写 official support channel 所以不确定是否官方"——**这个疑问现在已被官方 README 的 Links 节解决**：README 明确把它列为官方渠道。此处更正记录。

### 4.2 官方仪表盘（L0，但定位特殊）

<https://dashboard.cp2k.org/> 是**官方回归测试结果**，不是文档。

| 项 | 内容 |
|---|---|
| 内容 | 每次提交在各平台上的回归测试通过情况（correct / wrong / failed 计数、耗时） |
| 覆盖平台（示例） | CSCS Daint (psmp / psmp,H100)、CSCS Eiger (ssmp/psmp)、Current Toolchain (pdbg/psmp/sdbg/ssmp)、Spack 多组合、Ubuntu GCC 9–16、macOS on Apple M1、CUDA P100/Volta、HIP ROCm、Intel oneAPI (ifx/ifort)、ARM64、Minimal build、Coverage、Address Sanitizer 等 |
| 集成测试 | ASE Calculator、AiiDA-CP2K Plugin、i-Pi、Phonopy、Gromacs QM/MM、Spack (GROMACS) |
| 另有页面 | Test Coverage、Discontinued Tests、Supported compilers |

**对使用者的价值**：
- 判断"某个平台/编译器组合是否被官方持续测试"——**装机前查它比问人可靠**。
- 看到某测试 FAILED 时，可对照 `Last OK` 提交判断是回归还是长期问题。

---

## 5. 判定方法（可复现）

要判断一个 CP2K 相关来源是否官方，按以下顺序：

```
1. 看域名/账号是否在官方 README Links 节 → 是则 L0/L2
2. 看是否 manual.cp2k.org 的子页 → L0
3. 看作者是否含 CP2K 核心开发者 且 经同行评审 → L1
4. 看是否被官方手册 bibliography 收录 → L1（官方认可的方法出处）
5. 都不满足 → L3，不入 G 层
```

**反例（不要被误导）**：

| 现象 | 结论 |
|---|---|
| 搜索引擎里某个"CP2K 教程"站 | 非官方（不在 Links 节） |
| 个人博客整理的"CP2K 关键字表" | L3；**关键字默认值一律回手册核对** |
| 论坛里某开发者的一句答复 | L2；可作线索，需回手册复核 |
| 论文里描述 CP2K 某功能 | L1 但可能对应旧版本；**版本行为以 changelog 为准** |

---

## 6. 本轮据此新增采集的来源（全部 L0/L1）

| 来源 | 级别 | 落点 |
|---|---|---|
| 官方 GitHub 主仓库 README | L0 | 本文件 §2 |
| 官方 GitHub 组织与子仓库（cp2k-data / dbcsr / cp2k-examples） | L0 | 本文件 §2.2、`14_basis_and_potentials.md` |
| 官方 dashboard | L0 | 本文件 §4.2、`18_performance_and_gpu.md` |
| 官方 Google Group | L2 | 本文件 §4.1、`19_community_and_development.md` |
| 官方开发流程 onboarding | L0 | `19_community_and_development.md` |
| Kühne2020 官方参考论文 | L1 | 本文件 §3.1 |
| 手册 bibliography 方法论文 | L1 | 各专题文件 |
| GTH 赝势官方索引页 | L0 | `14_basis_and_potentials.md` |
| 手册 `input_file` / `printkey` 页 | L0 | `13_input_syntax_and_print.md` |
| 手册 `basis_sets` / `pseudopotentials` 页 | L0 | `14_basis_and_potentials.md` |
| 手册 properties 各子页 | L0 | `15_optical_and_xray.md`、`06_properties.md` |
| 手册 QM/MM 各子页 | L0 | `16_qmmm_embedding_ml.md` |
| 手册 optimization 全文 | L0 | `17_optimization_advanced.md` |
| 手册 sampling 约束/Ehrenfest 页 | L0 | `17_optimization_advanced.md`、`15_optical_and_xray.md` |
| 手册 machine_learning 页 | L0 | `16_qmmm_embedding_ml.md` |
| 手册 development/onboarding 页 | L0 | `19_community_and_development.md` |

---

## 7. 交叉索引

| 想查 | 去 |
|---|---|
| 某个来源是否官方 | 本文件 §1–§4 |
| 官方渠道清单 | 本文件 §2.1 |
| 怎么引用 CP2K | 本文件 §3.1；`10_features_resources.md` §4 |
| 装机前查平台支持 | 本文件 §4.2；`18_performance_and_gpu.md` |
| 官方开发流程 | `19_community_and_development.md` |
| 未覆盖来源与缺口 | `_sources.md` |
