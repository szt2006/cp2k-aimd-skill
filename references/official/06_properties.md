# 06 · 性质计算与电子结构分析（官方）

> **来源**：
> - <https://manual.cp2k.org/trunk/methods/properties/index.html>
> - <https://manual.cp2k.org/trunk/methods/electronic_structure/index.html>
> - <https://manual.cp2k.org/trunk/methods/embedding/index.html>
> - <https://manual.cp2k.org/trunk/methods/properties/infrared.html>（占位页）
> - <https://manual.cp2k.org/trunk/methods/embedding/qm_qm.html>（占位页）
> **抓取日期**：2026-09-08

---

## 0. 本文件的诚实说明

官方手册的**性质计算与电子结构分析章节目前非常不完整**：

- `properties/index.html` 只给出**子页面链接树**，没有正文；
- `properties/infrared.html` 是**占位页**（只有 2 条外链）；
- `electronic_structure/index.html` 只有一段引言 + 子页面链接；
- `embedding/qm_qm.html` 是**占位页**（只有 1 条外链）。

因此本文件的内容以**官方页面结构 + 官方功能清单**为主，**不编造方法细节**。缺什么，如实标注。

---

## 1. Properties（性质计算）官方页面结构

```
Properties
├── Optical Spectroscopy
│   ├── Time-Dependent DFT                    ← TDDFT
│   ├── GW + Bethe-Salpeter equation          ← GW-BSE
│   ├── Real-Time Bethe-Salpeter Propagation  ← RT-BSE
│   └── Simulating Vibronic Effects in Optical Spectra  ← 振动光谱效应
├── X-Ray Spectroscopy
│   ├── X-Ray Absorption from ΔSCF
│   ├── X-Ray Absorption from TDDFT
│   ├── X-Ray Absorption from RTP and δ-Kick perturbation
│   └── X-Ray Ab-Initio Correction Scheme
├── Infrared Spectroscopy        ← 占位页（无正文）
├── Raman Spectroscopy           ← 拉曼
├── Nuclear Magnetic Resonance   ← NMR
└── STM images                   ← STM 图像
```

### 1.1 官方功能清单中对这些性质的对应表述

| 性质 | 官方 `features` 页表述 |
|---|---|
| TDDFPT | 列在 DFT 能力中 |
| GW | 列在 DFT 能力中 |
| Bethe-Salpeter | 列在 DFT 能力中 |
| STM | `www.cp2k.org/howto:stm`（HowTo 进阶类） |
| 振动分析 | `RUN_TYPE VIBRATIONAL_ANALYSIS`（`01_global_and_units.md` §3） |
| 拉曼 | **2023.1 起加入拉曼强度**（changelog #2263） |
| NMR | 官方 acronyms 有 NMR 词条 |

### 1.2 红外光谱（占位页说明）

官方本页无正文，仅给出：

- <https://brehm-research.de/spectroscopy>
- <https://www.cp2k.org/exercises:2018_ethz_mmm:infrared_2018>

**G 层不编造红外流程。** 相关关键字（`&VIBRATIONAL_ANALYSIS`、`&MOTION/&MD` 的 IR 输出等）应查官方 Input Reference；实操经验见 F 层 `playbook.md` 与 `references/postprocess.md`。

### 1.3 振动分析的官方版本变更（changelog 中与振动相关的条目）

| 版本 | 变更 |
|---|---|
| 2026.2 | 修订后的振动分析打印中新增**质量加权前的 Hessian 输出**（#5395） |
| 2026.1 | **振动光谱（vibronic spectroscopy）**后处理工具（#4581）；修复振动分析中的力常数（#4427） |
| 2023.1 | 振动分析：**拉曼强度**（#2263） |

**虚频判断**：官方在 `05_optimization.md` §7.6 明确写道——**中间步能量上升可能意味着该结构不是真正的极小值；可通过振动分析检查，虚频揭示不稳定模式**。这是官方对"用振动分析验证极小值"的明确表述。

---

## 2. Electronic-structure Analysis（电子结构分析）

### 2.1 官方引言（原文要点）

> This section collects documentation for analyzing the electronic structure obtained from CP2K calculations. These analyses are typically based on **Kohn-Sham eigenvalues, occupations, wavefunctions, orbital projections, or related post-SCF quantities**, and are used to interpret **band edges, frontier orbitals, metallicity, defect states, orbital character**, and related electronic-structure features.

### 2.2 官方页面结构（本页可见部分）

```
Electronic-structure Analysis
└── Population and atomic charges
    └── RESP Charges
```

> 官方本页**仅列出这一个子页**（Population and atomic charges → RESP Charges）。这是一个明显的缺口——DOS/PDOS、Bader、COOP、STM 等在 `properties` 或 `howto` 下，而非本页。

### 2.3 官方功能清单中与电子结构分析相关的项

从 `www.cp2k.org/features` 与 changelog 提取：

| 功能 | 官方来源 |
|---|---|
| **DOS / PDOS** | features 页列出；2026.2 新增**带展宽输出和 k 点投影的 DOS/PDOS**（#5287、#5299）；2026.2 **重构 DOS/PDOS 输入段**（#5326，**不兼容变更**） |
| **Bader 电荷** | features 页列出（DDAPC 等布居分析） |
| **Mulliken / Löwdin 布居** | 2026.2 新增 k 点的 **Löwdin 布居分析**（#5045）；DFT+U 的 k 点支持**仅 Mulliken 方法**（#4855） |
| **Hirshfeld 布居** | 2.6 起加入（changelog） |
| **RESP 电荷** | 官方电子结构分析页有子页；2.4 起支持周期 RESP 电荷；3.0 起有 REPEAT 变体 |
| **Voronoi 积分** | LibVori（`09_build_libraries.md` §16）；2.2.1 起 GAPW Voronoi 积分（#1919） |
| **COOP / 晶体轨道** | 官方 acronyms 有 COLVAR 等；具体见 Input Reference |
| **STM 图像** | `howto:stm` |
| **Wannier 态** | 2025.1 在 AO 基组中打印 Wannier 态系数（#3683、#3687）；Wannier90 接口（experimental） |
| **k 点 MO 输出 `.mokp`** | `k-points.html` 明确：**Molden 输出对 k 点计算不可用** |
| **能带结构** | 通过 `&DFT%PRINT%BAND_STRUCTURE` 与 `&BAND_STRUCTURE`/`&KPOINT_SET` 定义路径 |
| **molecular moments / 分子矩** | 2026.2 实现 k 点计算的矩（#4621）；2027.1 修复分布式矩阵上的分子矩求和（#5680） |
| **APT / AAT / DCDR** | 2025.2 通过数值微分计算原子极化张量（#4287）；2027.1 支持在 APT 计算中用 DCDR 处理 meta-GGA（#5658） |

**官方关于 DOS 与 k 点的重要提醒**（来自 `k-points.html`）：

> **Electronic smearing and DOS broadening do not replace k-point convergence.** In particular, a smooth DOS obtained from a sparse mesh may still be physically unconverged.

> **DOS/PDOS 通常需要比几何优化更密的网格。**

---

## 3. Embedding（嵌入）与 QM/MM

### 3.1 官方页面结构

```
Embedding
├── Kim-Gordon
└── Quantum Embedding Theories   ← 占位页（无正文）
```

### 3.2 QM/MM

- **官方手册的 QM/MM 章节不在 `methods/embedding` 下**，而是在 `Methods` 下的 **QM/MM** 项。
- 官方功能清单（`features`）对 QM/MM 的表述：**实空间多重网格 / 线性标度 / 自适应 QM/MM**。
- 官方 changelog 中的 QM/MM 相关条目：
  - 2.4：**自适应 QM/MM**
  - 2.6：**DFTB 的 QM/MM**
  - 8.1：QMMM 添加基准测试，并用 OpenMP 加速 **GEEP**
  - 9.1：**Gromacs QM/MM 支持**
  - 2027.1：为 **DFTB 与 xTB 添加高斯静电 QM/MM 耦合**（#5731）
  - 2027.1：启用带 **GAPW 复合密度的 CDFT**（#5730）
- 官方 acronyms：`QMMM` = Quantum Mechanics / Molecular Mechanics；`GEEP` = Gaussian Expansion of the Electrostatic Potential；`IMOMM` = Integrated Molecular Orbital Molecular Mechanics method。

**QM/MM 的具体输入关键字**（`&QMMM`、`&QM_KIND`、`&MM_KIND`、`ECOUPL`、`EMBED`、`PERIODIC` 等）**应查官方 Input Reference**；G 层未抓取该页面，属于已知缺口。

### 3.3 其它嵌入/多尺度框架

| 框架 | 官方来源 |
|---|---|
| **MiMiC** | 多尺度模拟框架，通过 MCL 库实现；CMake 开关 `-DCP2K_USE_MIMIC=ON`；`RUN_TYPE MIMIC` |
| **Kim-Gordon** | `methods/embedding/kim-gordon.html` |
| **i-PI** | `RUN_TYPE DRIVER`（i-PI driver mode）；2024.2 加入 i-PI 服务端功能 |
| **libsmeagol / NEGF** | 电子输运；`RUN_TYPE NEGF`；`-DCP2K_USE_LIBSMEAGOL=ON` |

---

## 4. 官方对本文件内容的缺口清单（必须如实告知用户）

| 主题 | 官方状态 | 建议替代 |
|---|---|---|
| 红外光谱流程 | 占位页，仅 2 外链 | F 层 `playbook.md`；`references/postprocess.md`；官网 exercises |
| 拉曼光谱 | 有页面，本次未抓取 | 重新抓取 `properties/raman.html` |
| NMR | 有页面，本次未抓取 | 重新抓取 `properties/nmr.html` |
| STM 图像 | 有页面 + `howto:stm` | 重新抓取 |
| DOS/PDOS 输入写法 | 官方分散在 Input Reference，本页未展开 | 抓取 `CP2K_INPUT/FORCE_EVAL/DFT/PRINT/DOS.html` 等 |
| Bader 电荷 | 官方 Input Reference 有段，本页未展开 | 抓取 Input Reference |
| QM/MM 输入关键字 | 官方手册 QM/MM 页本次未抓取 | 抓取 `methods/qm_mm/` |
| 量子嵌入理论 | 占位页，仅 1 外链 | 官方 PDF：`_media/events:2017_dev_meeting/rybkin_cp2kdev-meeting_zurich2017-7.pdf` |
| 色散校正（vdW） | `methods/dft/vdw.html` **404** | `02_dft_methods.md` §11 |
| 线性标度 DFT | 占位页 | `02_dft_methods.md` §9 |
| NEB | 占位页 | `05_optimization.md` §13；A/F 层 |

**维护约定**：这些缺口补抓后，覆盖对应章节并在 `_sources.md` 更新。

---

## 5. 交叉索引

| 主题 | G 层 | A/F 层 |
|---|---|---|
| RDF / MSD / 扩散 / VACF 后处理 | —（官方 MD 页未展开） | **F 层是主要来源**；`references/postprocess.md`；脚本 `scripts/postprocess.py` |
| IR / 振动 | 本文 §1.2、§1.3（缺口） | F 层；`references/postprocess.md` |
| DOS / PDOS | 本文 §2.3 | F 层；脚本 |
| Bader | 本文 §2.3 | F 层 |
| 自由能面 / 元动力学 | 官方 features 提及 well-tempered metadynamics | A 层；F 层 |
| k 点功能兼容性（哪些性质支持 k 点） | `02_dft_methods.md` §4.3 | — |
