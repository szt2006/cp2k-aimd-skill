# 07 · QM/MM 三份教材精读（T21 / T22 / T23）

> **溯源层**：`txt/T21_qmmm_basic.txt`（28 页）、`txt/T22_qmmm_2d_embedding.txt`（23 页）、
> `txt/T23_qmmm_aimd_approaches.txt`（86 页），合计 **137 页**，逐页读完。
> 引用格式：`T21 P16` = `T21_qmmm_basic.txt` 里 `========== PAGE 16 ==========` 之后的内容。
>
> **抽取假象说明**（`README.md` §5）：pdfplumber 对两端对齐排版**丢词间空格**，且幻灯片里
> **代码块常被排成左右两栏而互相串行**（T22 P10–P12、T21 P12/P14 最明显）。
> 本笔记里凡是"两栏串行"的片段，都用 `<-- 原文两栏串行` 标注，语义按左右两栏分别还原，
> **不把串行当成原文错误**。T23 另有 114 个 `\x00` 字节（`~NUL~`）——那是 `½`、`≪`、`√` 等
> 数学符号的抽取残渣（集中在 P10/P24/P45/P57 的公式里），**不是原文缺陷**。

---

## 1. 这三份材料教什么

| 编号 | 一句话 | 讲授者 / 场合 |
|---|---|---|
| **T21** | **CP2K 里 QM/MM 的"填空式"基本用法**——从 CP2K 输入语法、`@INCLUDE`/`@SET`/`@IF` 预处理器，一路到 `&QMMM` 的 `&CELL`/`&QM_KIND`/`&LINK`，把五段（`&FORCE_EVAL`/`&GLOBAL`/`&MOTION`/`&EXT_RESTART`）拼成一份能跑的 QM/MM 输入 | Pablo Campomanes，CECAM QM/MM School（T21 P1） |
| **T22** | **CP2K 独有的 2D 嵌入（embedded cluster / island / sandwich 三型）及其在分子薄膜上的完整生产流程**——`&MM_KIND RADIUS`、`&PERIODIC`、边界势，以及如何验证嵌入没坏 | D. Z. Gao, M. B. Watkins, F. Federici-Canova, A. L. Shluger，UCL（T22 P1） |
| **T23** | **CP2K QM/MM 的"驱动级"方法学**：力学/静电/极化嵌入的能量分解、静电耦合三档（全 MM 盒 / 球截断 / 多极）、GEEP 高斯展开加速、PBC 下的解耦-再耦合、镜像电荷（IC-QM/MM），最后落到带电氧空位迁移（NEB）与分子/水在金属表面的生产算例 | Marcella Iannuzzi（UZH）+ Teodoro Laino（IBM Zurich），CP2K UK Workshop 2014, Imperial College（T23 P1） |

### 三者的层次关系

```
T21 基础用法（怎么把 QM/MM 输入写出来：五段结构 + &QMMM 三大块）
        ↓  会写了以后，"QM 盒/MM 盒是两个盒子"这件事在 2D 体系上怎么落地
T22 2D 嵌入（在 T21 语法之上加三样东西：&MM_KIND RADIUS、&PERIODIC、边界势；
              并给出 2D 体系专用的验证清单）
        ↓  再往下问"为什么这么写、代价从哪来、PBC 怎么办、怎么加速"
T23 AIMD 中的方法学（把 QM/MM 能量拆成 E_QM + E_MM + E_int；
              QM/MM 做 AIMD 时每一步都要重算 QM 区被 MM 环境极化的静电项，
              于是有 GEEP / 多极 / 球截断三条加速路线 + PBC 下的解耦-再耦合）
```

**一句话**：T21 教**语法**，T22 教**一类体系的完整套路**，T23 教**背后的方法与性能**。
T23 的标题虽叫 "in ab initio molecular dynamics"，但**它自己并没有单独开一节讲"QM 区在动力学中怎么随时间变化"**——
它讲的是**让 QM/MM 在动力学里跑得动的方法学**（GEEP 把 QM/MM 静电项从"占 60–80% 时间"压下去，T23 P29/P50/P66）。
这一点在第 3.4 节和 §7 会明确区分"教材真讲了什么"与"没讲什么"。

---

## 2. 逐节要点（带页码）

### 2.1 T21《Basic Usage of QM/MM in CP2K》（28 页）

| 页 | 要点 |
|---|---|
| P1 | 标题页；作者 Pablo Campomanes，CECAM QM/MM School："Hybrid Quantum Mechanics / Molecular Mechanics (QM/MM) Approaches to Biochemistry and Beyond" |
| P2 | **CP2K 通用输入语法**：`&SECTION … &END SECTION`；**块可以任意打乱顺序（shuffling is allowed, sort them as you like）**；注释用 `#` 或 `!`；单位用 `[UNIT]`；长行用 `\` 续行 |
| P3 | 预处理器 `@INCLUDE <filename.inc>`：文件内容被插入并解析，**用来避免输入文件过长**（例：`@INCLUDE 'xyz.inc'`） |
| P4 | `@SET VAR <value>` + `${VAR}` 替换：**同一个值在多处出现时只改一处** |
| P5 | `@IF … @ENDIF` 条件块：表达式为 `.false.` 时跳过；**一份输入文件保留多套运行配置**（例：`@IF (${RUN_TYPE} == EQUIL) EPS_DEFAULT 1.0E-10`） |
| P6 | **CP2K QM/MM 框架是模块化的**：QM 与 MM **on an equal footing（Quickstep + FIST）**；三块 = QM part（DFT）/ Interface region（QM/MM 相互作用 + 耦合项）/ MM part（经典力场 + 环境效应） |
| P7, P8 | **输入文件四大段**：`&FORCE_EVAL`（体系描述 + 算能量/力的参数）、`&GLOBAL`（做什么类型的模拟 + 全局参数）、`&MOTION`（MD 系综及其参数）、`&EXT_RESTART`（从外部文件重启）。P7/P8 内容相同（同一张幻灯片的重复页） |
| P9, P10 | **`&FORCE_EVAL` 的 QM/MM 骨架**：`METHOD QMMM` 激活 QM/MM 模块；并列 `&DFT`（`@INCLUDE 'force_eval_qm.inc'`）、`&MM`（`@INCLUDE 'force_eval_mm.inc'`）、`&QMMM`（耦合）、`&SUBSYS`（坐标/拓扑/胞）。P9/P10 重复 |
| P11 | `&DFT` 里要说清**QM 区的电荷与自旋**：`CHARGE 1`（**默认 CHARGE=0**）、`MULTIPLICITY 3`（**默认 MULTIPLICITY=1**）、`UKS`（要求自旋极化计算）；文件类 `BASIS_SET_FILE_NAME` / `POTENTIAL_FILE_NAME` / `WFN_RESTART_FILE_NAME`；`&QS METHOD GPW (or DFTB/PM6/…)`；`&XC &XC_FUNCTIONAL PBE (or BLYP/B3LYP/…)` |
| P12 | `&MGRID CUTOFF 320`（密度截断，Ry；**等价于 CPMD 波函数截断 80 Ry**）；`&SCF EPS_SCF 1.0E-6` / `MAX_SCF 50` / `SCF_GUESS ATOMIC (or RESTART if job cont)`；`&PRINT &MULLIKEN (or LOWDIN) FILENAME … &EACH MD 20`；其他可打印：`MO_CUBES`（分子轨道）、`DENS_CUBE`（总电子或自旋密度） |
| P13 | 骨架页重复（`&QMMM` 位置） |
| P14 | **MM 部分**：先给经典力场势能公式（键/角/二面角 + 12-6 LJ + 库仑）；`&MM &FORCEFIELD PARM_FILE_NAME parm.pot` / `PARMTYPE CHM (or G96/AMBER/…)` / `VDW_SCALE14 0.5` / `EI_SCALE14 0.8333333`；`&POISSON POISSON_SOLVER PERIODIC` / `PERIODIC XYZ` + `&EWALD EWALD_TYPE SPME (or EWALD/PME/…)`；注明 `&POISSON` 段是"控制长程静电的参数" |
| P15 | 骨架页重复 |
| **P16** | **`&QMMM` 核心三件套**：`USE_GEEP_LIB 9`（"# of gaussians to be used in the expansion of elect. potential"）、`ECOUPL GAUSS (or NONE/MULTIPOLE/…)`（"type of QM/MM elect. coupling"）、`&CELL !QM box size ABC [angstrom] 25.0 25.0 25.0`、`&QM_KIND C / MM_INDEX 1 5`、`&QM_KIND H / MM_INDEX 2 3 4 6 7 8`，注明"**indexes following MM numbering**" |
| P17 | 同 P16 内容 + 标注图（数字 1–8 是原子编号）；**关键结论句**："**If covalent bonds between QM and MM regions -> LINK atoms must be added**" |
| **P18** | **`&LINK` 唯一示例**：`&LINK / LINK_TYPE IMOMM (H-capping) / QM_INDEX 5 / MM_INDEX 8 / &END LINK`，并附示意图（1 到 8 的键被切断，5 在 QM 侧、8 在 MM 侧） |
| P19 | 骨架页重复 |
| P20 | `&SUBSYS` 的 **MM 盒**：`&CELL ABC [angstrom] 80.0 75.0 95.0` / `PERIODIC XYZ (directions where to apply PBC)`；`&TOPOLOGY COORD_FILE_NAME sys.pdb` / `COORD_FILE_FORMAT PDB (or XYZ/G96/…)` / `CONN_FILE_NAME sys.psf` / `CONN_FILE_FORMAT PSF (or AMBER/G96/…)` |
| P21 | `&KIND O/C/H` 的 **QM 基组与赝势**：`BASIS_SET DZVP-GTH-PBE`、`POTENTIAL GTH-PBE-q6`（O）/ `GTH-PBE-q4`（C）/ `GTH-PBE-q1`（H）；注明可在 CP2K 发行版里找不同的基组/赝势文件 |
| P22 | 四大段重复 |
| P23 | `&GLOBAL`：`PRINT_LEVEL MEDIUM (or SILENT/LOW/HIGH/…)`、`PROJECT_NAME MY_PROJECT`、`RUN_TYPE ENERGY_FORCE (or GEO_OPT/MD/…)`、`WALLTIME 86400`；**`touch EXIT` / `touch EXIT_MD` 可优雅停止** |
| P24 | 四大段重复 |
| **P25** | `&MOTION &MD`：`ENSEMBLE NVT (or NVE/NPT/…)`、`STEPS 5000`、`TIMESTEP 0.5`、`TEMPERATURE 298`；`&THERMOSTAT TYPE CSVR (or NOSE/…)` + `&CSVR TIMECON [fs] 50.`；另有 `&CONSTRAINT` 段位 |
| P26 | 四大段重复 |
| P27 | `&EXT_RESTART`：`RESTART_FILE_NAME NAME-1.restart`、`RESTART_DEFAULT FALSE`、`RESTART_POS TRUE`、`RESTART_VEL TRUE`、`RESTART_THERMOSTAT TRUE`、`RESTART_AVERAGES FALSE`、`RESTART_COUNTERS FALSE`；**"WFN is read if activated in &FORCE_EVAL"**（波函数重启是在 `&FORCE_EVAL` 里开的） |
| P28 | **I/O 清单**：`cp2k.popt –i NAME.inp –o NAME.out`（扩展名任意）；可选输入 = `POTENTIAL`/`BASIS_SET`/拓扑坐标力场参数/`@INCLUDE` 文件；标准输出 = `NAME.out`（**log，不会被覆盖**）、`NAME-1.restart`、`NAME-1.ener`（能量/温度/守恒量）、`NAME-1.dcd`（MD 轨迹或 GEO_OPT 步）、`NAME-1.cell`（NPT/CELL_OPT 才有）、`NAME-RESTART.wfn` |

> **T21 的性质**：它是**"输入填空课"**，不是"方法课"。**全文没有出现**"mechanical / electrostatic / polarized embedding"
> 这套术语，也没有讲**QM 区该选多大**、**MM 区净电荷怎么中和**（后者见 G 层 §2.8）。

### 2.2 T22《QM/MM 2D Embedding and Applications》（23 页）

| 页 | 要点 |
|---|---|
| P1 | 标题页；David Z. Gao, Matthew B. Watkins, Filippo Federici-Canova, Alexander L. Shluger，UCL 物理与天文系 |
| P2 | 大纲：QM/MM 引论（Embedded Cluster / **Embedded Island** / **Embedded Sandwich** 三型）→ CP2K 实现 → 分子薄膜应用（实验背景/应用/常见挑战）→ 结论 |
| P3 | **为什么要 QM+MM**：QM 管电子效应，MM 管更大环境，**降低计算成本**；"整体系用从头算算太贵" + "只有一部分体系含关键相互作用" |
| P4 | **Island 模型**（MM 区包住 QM 区，有限体系） |
| **P5** | **Sandwich 模型**："Periodic in 2 Dimensions: The **Infinite Sandwich Model**"——QM 层被上下 MM 夹住，**QM 只在 2 个方向周期** |
| **P6** | **CP2K 用的是加和式（additive）QM/MM**："Total energy is just the QM part + MM part + interaction between them!"；同时注明"**There is also subtractive QM/MM… which is a bit different… (also in CP2K)**"。三项定义：MM 原子的位置与电荷 / QM 体系的总电子+核电荷密度 / QM-MM 之间的 van der Waals |
| P7 | 应用背景文献：Amrous et al., *Advanced Materials Interfaces*, 2014, 1, 1400414（自组装薄膜形貌的分子设计与调控） |
| P8 | 体系：分子（锚定 CN 官能团 / 可互换基团 / π-π 堆叠的环 / 提供柔性的烃臂） + **KCl(001)** 衬底（易解理、易得、杂质少；简单立方；台阶边简单；绝缘体，同时有锚定位点和排斥位点） |
| **P9** | **QM/MM 分工**：2D 单层膜用 **2D Sandwich Embedding**；**分子-表面相互作用用 DFT**，**次表面 KCl 原子用经典力场** |
| **P10** | `&FORCE_EVAL METHOD QMMM (QMMM/FIST/QS)` + `@include QS.inc` + `&MM (&FORCEFIELD &CHARGE &NONBONDED &WILLIAMS &POISSON &EWALD)`：K/Cl 电荷 ±1.0；`&WILLIAMS` 三种配对（Cl-Cl、K-K、K-Cl）带 `A [eV]` / `B [angstrom^-1]` / `C [eV*angstrom^6]` / `RCUT [angstrom] 3.0`；`&EWALD EWALD_TYPE spme ALPHA .44 GMAX 40`。**该页两栏串行严重**，详见 §4.1 还原版 |
| **P11** | **`&QMMM` 的 2D 专属内容**：`&CELL (Size of QS Cell) ABC 12.6 15.0 12.6 PERIODIC XZ`；`&MM_KIND K RADIUS 1.52` / `&MM_KIND Cl RADIUS 1.67`（**注释写明 RADIUS 是 "Width of MM Gaussians"**）；`ECOUPL GAUSS (Use GEEP)` + `USE_GEEP_LIB 6` + `NOCOMPATIBILITY`（注释："**should be treated as parameters**"）；`&QM_KIND K MM_INDEX 25..32 41..48` / `&QM_KIND Cl MM_INDEX 17..24 33..40` + `NOCENTER F` / `NOCENTER0 F`；`&PERIODIC (Apply periodic potential) &MULTIPOLE OFF`（注释："**QM multipole coupling**"、"**use if XY of MM box =/= QM box**"） |
| **P12** | `&SUBSYS` 的 **整个体系胞**：`&CELL ABC 12.6 50 12.6 PERIODIC XZ`；`&TOPOLOGY COORD_FILE_NAME kcl.xyz / COORD_FILE_FORMAT XYZ`；`&GENERATE &ISOLATED_ATOMS LIST 1..48`（注释："**Ignores bonds, dihedrals...**"）；`&GLOBAL PRINT_LEVEL MEDIUM / PROJECT_NAME KCl / RUN_TYPE GEO_OPT / FLUSH_SHOULD_FLUSH`；`&MOTION &GEO_OPT OPTIMIZER LBFGS` + `&CONSTRAINT &FIXED_ATOMS LIST 1..16 / EXCLUDE_MM .FALSE. / EXCLUDE_QM .TRUE.`（**固定底层 KCl，且把 QM 原子排除在约束外**）；`&KIND K BASIS_SET DZVP-MOLOPT-SR-GTH / POTENTIAL GTH-PBE-q9`、`&KIND Cl BASIS_SET DZVP-MOLOPT-GTH / POTENTIAL GTH-PBE-q7` |
| **P13** | **Step 1：分别选定 QM 与 MM 两套表示**。QM 侧 = GPW（VandeVondele et al., *Comput. Phys. Commun.* 2005, 167, 103）+ **GGA/PBE + MOLOPT**（VandeVondele & Hutter, *J. Chem. Phys.* 2007, 127, 114105）+ **DFT-D2 色散修正**（Grimme, *J. Comput. Chem.* 2006, 27, 1787）。MM 侧 = KCl(001) 的**已发表对势**（Catlow, Diller, Norgett, *J. Phys. C* 1977, 10, 1395），**注明"Fixed Shells to Cores!"**（壳层固定到核心）。已算性质：Mulliken 与 Bader 分析**显示无电荷转移**；主要相互作用在 **CN 与表面阳离子之间**；**吸附能 3.1 eV**；DFT 配方给出的 **KCl  homo/lumo gap = 5.2 eV（实验 7.6 eV）** |
| P14 | 电子性质：KCl(001) 上的 CDB（一维电荷密度），Gao/Federici Canova/Watkins/Shluger, *J. Comput. Chem.* 2014 (Submitted) |
| **P15** | **Step 2：评估 QM/MM 模型**。三条：① 比较各套表示的**已知物理性质**；② 比较 DFT 体系与 QM/MM 体系的**电子结构**；③ **检查嵌入相关的常见问题**。"QM/MM indeed seems to work…" |
| P16 | 同上，QM/MM 下的电子结构（图） |
| **P17** | **常见问题之一：电子泄漏（Electron Leakage）**。示出 2D 嵌入的真空区/QM 原子/MM 原子分区图；"In previous embedded cluster studies charge leakage was an issue: **Examine the electron density plots of the system**；**Less of a problem in ionic materials, looks OK here!**" |
| **P18** | **常见问题之二：边界势（Border Potentials）**。"QM atoms interact with MM atoms at the border…**May not be properly represented using the standard force field**；**Additive corrective potential may be added to improve the model**"。起因 A = **QM 区与 MM 区晶格常数不同**；起因 B = 边界处更复杂的相互作用（**共价键等**）。**针对起因 A 的解法三步**：① 把原子固定到想要的位置；② **优化一组附加的加和性对势**；③ **理想情况下边界原子上的力应降到 0** |
| **P19** | **边界势的输入实现**：在 `&MM &FORCEFIELD &NONBONDED` 下用 `&WILLIAMS` 正常对数 + **新增 `KZ`/`ClZ` 两条 `&CHARGE`（注释："border KCl"）**，并用一组 `RCUT [angstrom] 5.0` 的 `&WILLIAMS` 对（KZ-Cl、KZ-KZ、ClZ-ClZ 等）覆盖边界配对；注明"如果你要 KCl(001) 块体的边界势、或要脚本做这件事，**直接问我要**" |
| P20 | 周期单层结构：① 研究各种可能的单层构型（**用实验图案的周期性做约束**；**对映体（分子翻转）给出简并的图案**；这些构型下**每分子吸附能升到 3.4 eV**）；② 模拟 AFM 图像；③ 解释实验结果 |
| **P21** | **给分子造力场**：CHARMM（Brooks et al., *J. Comput. Chem.* 2009, 30, 1545-1614）；四步 = **① 用 QM/MM 生成拟合数据 → ② 遗传算法同时拟合大量变量 → ③ 评估力场 → ④ 研究体系中的动力学**。KCl(001) 的经典表示仍用 Catlow 1977 |
| P22 | "Molecular Dynamics… a quick example!"（幻灯片只有标题，**内容在图里**） |
| **P23** | 结论 + 出处。**"QM/MM can greatly reduce cost if: ① Only some interactions are critical；② MM potentials are available."** 三步总纲：**选 QM/MM 参数 → 测电子与物理性质 → 检查常见失效模式**。附两个链接：`cp2k.org/exercises:2014_uzh_molsim:index`（Marcella Iannuzzi）、`archer.ac.uk/training/course-material/2014/08/CP2K/Slides/QMMM.pdf` |

### 2.3 T23《QM/MM approaches in ab initio molecular dynamics》（86 页）

**结构与篇幅分布**（页码即 `PAGE N`）：P1–P8 概览 / P9–P14 MM 与减式 QM/MM / P15–P24 加和式与静电方案 /
P25–P29 GEEP 原理 / P30–P50 多格子框架（**P36–P43 为纯动画页，文本为空**）/ P51–P52 输入示例 /
P53–P64 PBC 扩展 / P65 周期输入示例 / P66–P67 GEEP 总结与误差来源 / P68–P72 全周期与解耦-再耦合 /
P73–P79 应用：带电氧空位 NEB / **P80–P86 附录：IC-QM/MM 论文抽页**（含 P85–P86 的水/Pt(111) 薄膜）。

| 页 | 要点 |
|---|---|
| P1 | 标题页；Marcella Iannuzzi（University of Zurich）+ Teodoro Laino（IBM Zurich Research Laboratory），**CP2K UK Workshop 2014, 27-28 August, Imperial College, London** |
| P2 | 大纲：QM/MM 方法概览 → 可用的 QM/MM **静电方案** → **GEEP：CP2K 的 QM/MM 驱动** → 应用：**SiO₂ 中的带电氧空位** |
| P3 | 2013 年诺贝尔化学奖：Karplus / Levitt / Warshel，"Development of Multiscale Models of Complex Chemical Systems" |
| **P4** | **加和式势能面**：`V(R) = V_QM(R) + V_MM(R) + V_int(R)`；"把体系分成 QM 与 MM 两部分，**把要处理的电子单列出来**"；"Find solutions to many technical problems." |
| **P5** | **四个必须做的选择**（本层最重要的一页，见 §3.1）：QM 管电子重排 / MM 高效纳入更宽的环境 / **① 选 QM 方法（semi empirical, DFT, QC）② 选力场 ③ 分割方式 ④ 边界的处理** |
| P6 | 规模动机：**738,000 原子 - 50 纳米**（P. D. Blood & G. A. Voth, *PNAS* 103, 2006, 15068-15072），用于 docking 的配体结合亲和力、自由能模拟、复杂生物分子结构 |
| P7 | **一页 Biochemistry 综述抽页**（van der Kamp & Mulholland, *Biochemistry* 2013, 52, 2708-2728）：QM/MM 用 QM 算活性位电子结构、用更简单的 MM 纳入酶环境；**方法谱从"便宜到可用于 MD"到"高精度电子结构"**；并提到 EVB（经验价键）路线 |
| **P8** | **自适应 QM 区**：0.11 million atoms、**5 QM regions: effects of O implantation into Si**、**adaptive QM regions**、simoX 技术（Yoshio Tanaka, AIST；Aiichiro Nakano, USC）。**这是全套 137 页里唯一出现"adaptive QM regions"字样的地方，只有标题与配图，无方法细节** |
| P9 | MM 环境 = 多体展开 `U(R^N) = ΣU₁(R_i) + ΣΣU₂(R_i,R_j) + ΣΣΣU₃(R_i,R_j,R_k) + …` |
| P10 | **经验力场的典型形式**（含 `~NUL~` = `½`）：键伸缩 `k_i/2 (l−l₀)²`、角弯曲 `k_j/2 (θ−θ₀)²`、扭转 `V_n/2 (1+cos(nφ−δ))`、`4ε_ij[(σ_ij/r_ij)^12 − (σ_ij/r_ij)^6]`、库仑 `q_iq_j/(4πε₀r_ij)`；参数集 `(k₀,l₀); (k₀,θ₀); (V_s,φ_s); (ε,σ); q`；页脚标 **7/64**。小节标题含"Parameterization and Transferability""Reducing the Complexity" |
| P11 | **拓扑文件长什么样**：CHARMM 的丙氨酸 `RESI ALA 0.00` 条目全展开（`ATOM` / `BOND` / `DOUBLE` / `IMPR` / `DONOR` / `ACCEPTOR` / `IC`），并逐条解释 `RESI`/`GROUP`/`ATOM`/`BOND` 的含义；**注意 "GROUP = 一组共享电子密度的原子，带整数电荷"** |
| **P12** | **纯 MM 的 CP2K 输入**（`METHOD FIST` + `&MM &FORCEFIELD PARM_FILE_NAME acn.pot / PARMTYPE CHM / &CHARGE 四条 / &POISSON &EWALD EWALD_TYPE SPME ALPHA .44 GMAX 32 O_SPLINE 6` + `&SUBSYS &CELL ABC 27.0 27.0 27.0` + `&TOPOLOGY CONNECTIVITY PSF / CONN_FILE_NAME acn_topology.psf / COORD_FILE_NAME acn_topology.pdb / COORDINATE pdb` + `STRESS_TENSOR ANALYTICAL`）。**两栏串行**，还原版见 §4.2 |
| **P13** | **减式（subtractive）QM/MM**：`E_total = E_MM,tot + E_QM(QM) − E_MM(QM)`；并给出**代价**："**MM FF also for active region!**"（活性区也要用 MM 力场算一遍）、"**QM density not polarised**"（QM 密度不被极化） |
| **P14** | **减式方案的完整输入**（本层唯一的 `&MULTIPLE_FORCE_EVALS` 完整片段）：`FORCE_EVAL_ORDER 1 2 3 4`；`METHOD MIXED` + `&MIXED MIXING_TYPE GENMIX` / `VARIABLES X Y Z` / `MIXING_FUNCTION X+Y-Z`；四个 `&FORCE_EVAL` 分别对应 MM/MM/QM；注释明确 `# X: Energy force_eval 2 / # Y: Energy force_eval 3 / # Z: Energy force_eval 4`（**三个能量来自第 2/3/4 个 FORCE_EVAL**）。**两栏串行**，还原版见 §4.3 |
| **P15** | **加和式（additive）QM/MM**：`E_total = E_MM,tot + E_QM(QM) + E_QM/MM`，其中 `E_QM/MM = E_el + E_vdw + E_b`。四条判语："**Electrostatic coupling is the most involved term!**" / "**Mechanical embedding possible!**" / "**Linked atom scheme!**" / "**vdW might need ad hoc parameterisation**" |
| P16 | 大纲页（进入"可用的静电方案"） |
| **P17** | **静电方案之一：在定义 QM 盒的同一个格子上**——`Cost ≈ N_MM * P1`（**随 MM 原子数线性增长，最贵**） |
| **P18** | **静电方案之二：Spherical Cutoff（球截断）**——`Cost ≈ N_c * P1`（只算球内 `N_c` 个 MM 原子） |
| **P19** | **静电方案之三：Multi-pole（多极展开）**——MM 盒的展开；文献 A. Laio, J. VandeVondele, U. Rothlisberger, *J. Chem. Phys.* 116, 2002, 6941 |
| P20 | 大纲页（进入 GEEP） |
| P21 | "QM/MM" 过渡页 |
| **P22** | **加和式能量分解的正式写法**：`E_TOT(R_QM,R_MM) = E_QM(R_QM) + E_MM(R_MM) + E_QM/MM(R_QM,R_MM)`；`E_QM/MM(R_QM,R_MM) = Σ_MM q_MM ∫ n(r)/|r−R_MM| dr + u_vdW(R_QM,R_MM)`；图上标 **QM,MM** 的求和 |
| P23 | 为什么需要新方法："**Gaussians / Plane Waves**"——QM 用高斯基、MM 电荷要在平面波网格上表示 |
| **P24** | **高斯电荷分布**：`n(r,R_MM) = (r_c,MM/√π)³ e^(−(r−R_MM/r_c,MM)²)`，对应势 `v_MM(r,R_MM) = Erf(|r−R_MM|/r_c,MM)/|r−R_MM|`。**两个目的（原文）**："**prevent spill out problem!**"（防止电子溢出 QM 区）、"**accelerate calculations of electrostatics**" |
| **P25** | **GEEP = Gaussian Expansion of the QM/MM Electrostatic Potential**（Laino, Mohamed, Laio, Parrinello, *J. Chem. Theory Comput.* 1, 2005, 1176-1184）。抽页原文三句最关键：① 在 QM/MM 里"**MM charges have been Gaussian smeared as a means to repair the broken covalent bonds at the QM/MM boundaries**"；② **本文不处理"QM/MM 区被共价键跨越"的问题**，而是利用抹高斯"prevent the spill-out problem and to accelerate the calculation"；③ 直接算 eq 2 的代价是 **N_u × N_MM**（`N_u` ≈ 10⁶ 网格点，`N_MM` ≥ 10⁴ 经典原子）——"**a brute force computation of the integral in eq 2 is impractical**" |
| P25–P26 | 分解式：平滑库仑势写成 **N_g 个高斯函数之和 + 残差函数 R_low**；`G_cut ≈ 1.0` 时残差已够平滑，而 `V_a` 需要 `G_cut ≈ 3.0` ⇒ **残差可以用比 V 大一数量级间距的网格来映射**（"grids of different spacing can be used"）。P25/P26 内容有大量重复（同一篇论文的两页被连续抽了两次） |
| P27 | **多格子框架**：`N_{i+1} = 8 N_i`（Laino et al. 2005） |
| P28 | 多格子框架：**interpolate / restrict** 交替 + **Cubic Splines** |
| **P29** | **在 QM 盒里做 collocation**：`E_QM/MM(R_QM,R_MM) = ∫ n(r,R_QM) V_QM/MM(r,R_MM) dr`，势落在**最细的 QM 网格**上，`V_QM/MM(r,R_MM) = Σ_MM v_i(r,R_MM)`；标注"**optimal!**"、"**grid levels!**"、**"60-80% of time"**（这一步占 60–80% 的时间） |
| P30–P35 | QM 盒示意 + **compact Gaussian functions**（6 页，文本几乎只有标题） |
| **P36–P43** | **纯动画页，抽取文本为空**（8 页）。内容不可考，只能从上下文判断是 GEEP 多格子插值/限制过程的动画 |
| P44 | `Scaling ~ N_c³` |
| **P45–P49** | 实空间插值：**"interpolation from coarsest to finest!"**，`V_QM/MM(r,R_MM) = Σ_{i=coarse}^{fine} (Π_{k=i}^{fine} I_{k−1}) V_i^QM/MM(r,R_MM)`（5 页重复同一公式） |
| **P50** | 静电势插值：**"20-40% of time"**（插值占 20–40% 的时间）——与 P29 的 60–80% 合起来就是 GEEP 优化的预算依据 |
| **P51** | **GEEP 的完整 QM/MM 输入示例**（本笔记 §4.4 逐字抄录）：`&QMMM &CELL ABC 6.0 6.0 6.0 / USE_GEEP_LIB 9 / ECOUPL GAUSS / &MM_KIND H RADIUS 0.44 / &MM_KIND O RADIUS 0.78 / &QM_KIND H MM_INDEX 8 9 / &QM_KIND O MM_INDEX 7`；配套 `&MM`、`&DFT`、`&SUBSYS &CELL ABC 15.0 15.0 15.0 / &TOPOLOGY COORD_FILE_NAME sys.pdb / COORDINATE pdb`。**注意：QM 盒 6 Å、MM 盒 15 Å，两个盒子大小不同**（与 T22 P11 注释"use if XY of MM box =/= QM box"呼应） |
| P52–P53 | **扩展到 PBC**：用 Ewald 求和方案，分**倒空间**与**实空间**两部分 |
| P54 | **QM/MM fully periodic**（QM 与 MM 都在三个方向周期；Laino et al., *J. Chem. Theory Comput.* 2(5), 2006, 1370-1378） |
| **P55–P57** | **总静电能的背景电荷处理**：`n(r) = n_QM(r) + n_MM(r) ± n_B`（**background charge**），并给出四项分解 `E_TOT`、`E_MM`、`E_QM`、`E_QM/MM`，每项都用 `(n + n_B)` 的形式（即**带电体系在 PBC 下必须有均匀背景电荷**，QM/MM 每一项都要一致地减掉它） |
| P58 | MM/MM fully periodic |
| P59 | QM/MM fully periodic（QM 只占一格） |
| P60–P61 | **GEEP with PBC**：粗网格上"**smooth!**"（最粗网格） |
| **P62** | **QM/MM 实空间项**：`V_rs^QM/MM(r,R_MM) = Σ_{L<L_cut} Σ_g A_g exp(−|r−R_MM+L|²/G_g²) − (√π³/…)` |
| P63–P64 | **QM/MM 倒空间项**：**"low cutoff function! only few k vectors needed"**（残差函数的傅里叶变换支撑很小，倒空间求和只需少量 k 向量） |
| **P65** | **周期 GEEP 的完整输入示例**（§4.5 逐字抄录）：`&QMMM &CELL ABC 17.320500 ×3 / ECOUPL GAUSS / USE_GEEP_LIB 6 / &MM_KIND NA RADIUS 1.5875316249000 / &MM_KIND CL RADIUS 1.5875316249000 / &PERIODIC GMAX 0.5 / &MULTIPOLE EWALD_PRECISION 0.00000001 / RCUT 8.0 / NGRIDS 20 20 20 / ANALYTICAL_GTERM`。**这页把 GEEP（`ECOUPL GAUSS`）与多极/周期（`&PERIODIC &MULTIPOLE`）放在同一份输入里，说明二者是叠加而非互斥** |
| **P66** | **GEEP 总结**：加速因子 ≈ `(N_f/N_c)³ = 2^(3(N_grid−1))`；**通常用 3–4 级网格，对应加速 64–512 倍 ≈ 100 倍**（比朴素 collocation 快两个数量级；插值与限制的时间可忽略）；倒空间只需少量点；**"Small computational overhead between the fully periodic and non-periodic"**（全周期与非周期之间的额外开销很小） |
| **P67** | **误差来源三条**：① **网格层截断应与被映射高斯的截断匹配（约每线方向 20–25 个点）**；② **三次样条插值的误差**；③ **粗网格层的截断应与长程函数的截断相当** |
| P68–P69 | QM fully periodic（QM 占满全胞） |
| **P70–P71** | **De-coupling and re-coupling（解耦与再耦合）**：全 QM 周期体系 ↔ 单 QM 区 + MM 环境（Laino et al., *JCTC* 2(5), 2006） |
| **P72** | **Bloechl 方案**：在 g 空间对总密度做**密度拟合** `ñ(r,R_QM) = Σ q_QM g_QM(r,R_QM)`；目标"**Reproduce the correct Long-Range electrostatics!**"；构造 `Q_l = ∫ dr r^l (n(r,R_QM) − ñ(r,R_QM))`，**最小化** `W = ∫ dr r²(n − ñ)²`；"**Decoupling and Recoupling using these charges**"。文献 P. E. Bloechl, *J. Chem. Phys.* 103(17), 1995, 7422-7428 + Laino et al. 2006 |
| **P73–P75** | **应用：带电氧空位（Charged OV）在二氧化硅中的迁移**（T. Laino, D. Donadio, I-Feng W. Kuo, *Phys. Rev. B*, 2007）；三页逐步展示"dimer!"、**deloc. el.（离域电子）**、`E'` 中心、`δ`/`δ₁` 电荷态（P74 是 P73 加了 `E'₁`、`δ₁`，P75 再加 `E*`） |
| P76–P77 | 空白页（只有页眉栏，图不可抽取） |
| P78–P79 | **NEB: Minimum Energy Path**（同一文献） |
| **P80** | 附录开始：**Image Charge & QM/MM**——"QM molecule + EAM metal"，例子 **nitrobenzene/Au(111)**；文献 Siepmann & Sprik, *JCP* 102 (1995) + Golze, Iannuzzi, Passerone, Hutter, *JCTC* (2013)；并给出该论文的**算法段落**：IC 系数可用**预处理共轭梯度（preconditioned-CG）**迭代求解，每次迭代只要 **两次 FFT + N_IC 次数值积分**；**"the Gaussian elimination scheme is always the method of choice for single point calculations. The preconditioned-CG is used for geometry optimizations and MD simulations."**（**单点用高斯消元，几何优化与 MD 用预条件 CG**）；MD/优化可以**复用同一个矩阵 T 作为预条件子若干步再更新**。测试体系共 **5 个吸附物-金属体系**：benzene / nitrobenzene / thymine / guanine on Au(111) + water on Pt(111)（含 water dimer 与 12 分子团簇）；金属衬底为**四层 slab，三个方向都加 PBC** |
| P81–P82 | IC 公式：`ρ_IC(r) = Σ_I^{met} C_I exp(−α|r−R_met^I|²)`；**恒定电势条件** `V_H(r) + V_IC(r) = ∫[ρ(r')+ρ_IC(r')]/|r−r'| dr' = V_0`；"**IC induce polarization, solved selfconsistently**" |
| **P83** | IC 的线性方程组与 CG 迭代；**唯一可调参数 α 的判据**："**For values of α larger than 3.0 Å⁻², neither the total energy nor the image charge distribution show a significant dependency on α. However, drastic changes are found for smaller values.**"；α 太小 ⇒ 高斯过宽 ⇒ 电荷在金属里均匀分布 ⇒ **非物理结果（技术伪影）**；α 极大也不推荐。另有：**由于"infinite slab"的宏观极限，IC 电荷之和应趋于零**；"**the finite sum of the image charges does not correspond to a physical charge since the image charges are merely a computational tool to impose the correct behavior of the electrostatic potential within the metal**"；吸附构型：nitrobenzene/thymine/guanine 在 Au(111) 上 `d_metal ≈ 3.1 Å`，benzene 在 fcc 三重空位 `d = 3.0 Å` |
| **P84** | **H₂O 团簇在 Pt(111)**（QM=H₂O，Pt 用 EAM，H₂O-Pt 用 **Siepmann-Sprik + IC**）：Table 3 给的数（kJ/mol）——1H₂O：E_int 41.6→44.2（IC）对比 full DFT 44.9；2H₂O：40.9→43.7 对比 50.6；12H₂O：36.4→42.8 对比 44.2。**"The deviation is less than 4.0 kJ/mol for all water systems."**；12H₂O 单分子偶极矩可比气相（**1.85 Debye**）大 **0.7 Debye**（H 键所致）；PBE 预测体相水平均偶极矩 **3.10–3.27 Debye**；IC 极化再额外增强最多 **0.3 Debye** |
| **P85** | 液态水/Pt(111) 薄膜：蜂窝排列，**70% on-top 位被占据**；水膜按密度振荡分 **4 层**；**距离表面 >10 Å 后密度趋近体相水**；液-真空界面密度趋于零 |
| P86 | 四层水的 O-O / O-H 径向分布函数与每分子 H 键数分布；**第 2、3 层的 RDF 与文献 DFT-PBE 体相水相似**；第 4 层峰高显著更小（真空界面配位减少）；**水-金属层与水-真空层的峰位相同** |

---

## 3. 核心逻辑链

### 3.0 总能量怎么分解 —— 先分清"加和式"与"减式"

| 方案 | 公式 | 教材出处 | 教材给的评价 |
|---|---|---|---|
| **加和式 additive** | `E_TOT = E_MM,tot + E_QM(QM) + E_QM/MM`，`E_QM/MM = E_el + E_vdw + E_b` | T23 P4, P15, P22；T22 P6 | **CP2K 走的是这条**（T22 P6 明确）。"Electrostatic coupling is the most involved term!" |
| **减式 subtractive** | `E_total = E_MM,tot + E_QM(QM) − E_MM(QM)` | T23 P13, P14 | 代价：**活性区也要用 MM 力场算一遍**；**QM 密度不被极化** |

> **为什么先讲这个**：三份材料里只有 T22 P6 用一句话点到"CP2K 也有减式"，T23 P13–P14 才给公式和输入。
> 而"该选哪种"的判断，**两页合起来才是完整的**：默认加和式（因为 CP2K 的 `&QMMM`
> 就是加和式的实现）；只有当你**已经有覆盖活性区的 MM 参数**、且**不在乎 QM 密度被环境极化**时，减式才划算。

---

### 3.1 三种嵌入方式：力学 / 静电 / 极化

> **前置提醒**：**"mechanical / electrostatic / polarized embedding" 这套术语在 T21、T22、T23 里都没有出现**。
> 教材用的是**关键字**和**物理量**的说法。下表把教材原文的说法与标准术语对上，并**逐格标出处**——
> 凡是教材没讲的格子，写"教材未讲"，不替它补。

| | **力学嵌入（mechanical）** | **静电嵌入（electrostatic）** | **极化嵌入（polarized / IC）** |
|---|---|---|---|
| 教材对应说法 | "**Mechanical embedding possible!**"（T23 P15）；QM 只与 MM 点电荷相互作用、**无极化**（G 层 `16_…` §2.5 有官方原文，本层只写指针） | "**Electrostatic coupling is the most involved term!**"（T23 P15）；QM 被 MM 环境极化 | "**IC induce polarization, solved selfconsistently**"（T23 P81/P82） |
| **物理假设** | QM 区**不被** MM 区极化；MM 只提供几何约束/范德华环境 | MM 的**固定点电荷**进入 QM 的单电子哈密顿量 ⇒ **QM 波函数被 MM 静电场极化**；MM 不被 QM 反向极化（**单向**） | MM（金属）中**诱导出镜像电荷**，与 QM 密度**自洽求解** ⇒ **双向**：既是 MM 极化 QM，也是 QM 极化 MM（金属屏蔽） |
| **关键公式/实现** | 教材未给公式 | `H_μν^QM/MM = −Σ_a q_a ∫ φ_μ(r) φ_ν(r)/|r−r_a| dr`（高斯基，T23 P25）；或"改外部势 + 在网格节点上 coloc 上 MM 的贡献"（平面波基，T23 P25） | `ρ_IC(r) = Σ_I C_I exp(−α|r−R_I|²)`，`V_H(r) + V_IC(r) = V_0`（T23 P81/P82） |
| **CP2K 关键字** | 教材只给概念，未给该档关键字 | `ECOUPL GAUSS`（GEEP，QM 用 DFT 时）——T21 P16、T22 P11、T23 P51/P65。其它档：`ECOUPL NONE` / `ECOUPL MULTIPOLE`（**枚举出处仅 T21 P16**，G 层给的 `E_COUPL COULOMB`/`NONE` 见 §6） | `&QMMM &IMAGE_CHARGE MM_ATOM_LIST … EXT_POTENTIAL …`（G 层 `16_…` §4.3 已采全，**本层只写指针**）；T23 P80–P86 给的是原理与性能，**没给 CP2K 输入** |
| **代价** | 最低 | **"60-80% of time"（T23 P29）**——GEEP 之前，QM/MM 静电积分的 collocation 就占 60–80% 机时；朴素做法代价 `N_u × N_MM`（10⁶ 网格点 × 10⁴ MM 原子）"impractical"（T23 P25） | 单点：高斯消元解线性方程组；MD/几何优化：预条件 CG，每次迭代 **2 次 FFT + N_IC 次数值积分**（T23 P80）；**矩阵 T 可复用若干步再更新** |
| **加速路线** | — | ① 同格子 `Cost ≈ N_MM × P1`（T23 P17，最贵）② **球截断** `Cost ≈ N_c × P1`（T23 P18）③ **多极展开**（T23 P19）④ **GEEP 多格子**：3–4 级网格 ⇒ **64–512 倍 ≈ 100 倍**（T23 P66） | `IMAGE_MATRIX_METHOD GPW/MME`、`DETERM_COEFF CALC_MATRIX/ITERATIVE`（G 层 `16_…` §4.5 已采全） |
| **适用面（教材原话/例子）** | 教材未给适用面判据 | 主战场：**酶（Biochemistry 2013 综述，T23 P7）**、**水/Pt(111)（T23 P84）**、**带电氧空位/SiO₂（T23 P73–P75）**、**KCl(001) 上的分子膜（T22）** | **吸附物-金属**：benzene / nitrobenzene / thymine / guanine on Au(111)、water on Pt(111)（T23 P80、P84） |

#### 教材怎么解释"该选哪种"

**T23 P5 把选择拆成四个必须回答的问题**（这是三份材料里最接近"决策树"的一页）：

> QM: modelling of electronic rearrangements! / MM: efficient inclusion of wider environment!
> **Choice of QM method (semi empirical, DFT, QC)!**
> **Choice of the force field!**
> **Partitioning and treatment of the boundary**

注意它**没有**把"选哪种嵌入"单列为第 5 问——因为在 CP2K 的实现里，
**"嵌入方式"被折叠进了"边界怎么处理"（第 4 问）和"静电方案怎么选"（T23 P17–P19 三档代价）**。
这是本层与 G 层 `16_…` §2.5 的**视角差异**：G 层从**关键字枚举**角度讲三档，
T23 从**代价标度**（`N_MM·P1` vs `N_c·P1` vs 多极）角度讲三档。

**教材实际给出的"该选哪种"判据（逐条有页）**：

1. **"QM/MM can greatly reduce cost if: ① Only some interactions are critical；② MM potentials are available."**（T22 P23）
   —— 这是**能不能用 QM/MM** 的前置判据，不是嵌入方式判据。**两条都不满足就别上 QM/MM**。
2. **能不能避开边界**：G 层的 chorismate mutase 例子（"催化是静电方式、不形成共价键"⇒ 不需要 link atom）是本层的**隐含最佳情形**；T23 P15 则明确"**Linked atom scheme!**"是加和式的组成部分之一。
3. **要不要金属屏蔽** ⇒ 要，就用 IC-QM/MM（T23 P80）；纯分子/离子环境 ⇒ 普通静电嵌入就够。
4. **QM 方法是什么**：T21 P16 把 `ECOUPL GAUSS` 和 `USE_GEEP_LIB` 放在一起 ⇒ **GEEP 是 DFT 路线**（T23 P23–P25 全是高斯基 + 平面波网格）；若 QM 用半经验，G 层 `16_…` §2.5 给的官方说明是 `E_COUPL COULOMB`。
5. **MM 盒与 QM 盒是不是一样大**：不一样时，T22 P11 的 `&PERIODIC &MULTIPOLE` 注释就是为你写的（"use if XY of MM box =/= QM box"）。

**教材没讲的**（§7 存疑会重复）：三档嵌入各自**什么时候会失效**、**极化嵌入的额外代价量级**、
**力学嵌入在什么情况下还算合理**——这三份材料都没有判断句。

---

### 3.2 边界处理：link atom / `&LINK` / 边界电荷中和

> 这一节是任务里点名的重点，但**必须先把三层材料的覆盖度说清楚**，否则会误以为 T21–T23 讲全了。

#### (a) 覆盖度真相表

| 边界问题 | T21 | T22 | T23 | 真正讲全的地方 |
|---|---|---|---|---|
| **什么情况下必须加 link atom** | ✅ **P17 一句话**："If covalent bonds between QM and MM regions -> LINK atoms must be added" | ❌ 未讲 | ⚠️ P15 只列 "**Linked atom scheme!**"；P25 论文抽页**明确声明"本文不处理 QM/MM 区被共价键跨越的问题"** | T21 P17 |
| **`&LINK` 语法** | ✅ **P18**：`LINK_TYPE IMOMM` / `QM_INDEX` / `MM_INDEX` | ❌ | ❌ | T21 P18 + G 层 `16_…` §2.7 |
| **link atom 怎么定位 / 力怎么分摊** | ❌ | ❌ | ❌ | **三份都没讲**（G 层也只说"用 IMOMM 方法做连接"） |
| **切哪根键** | ❌ | ❌ | ❌ | G 层 `16_…` §2.7 官方规则（切最"无聊"的脂肪族 C-C，避免强极化键） |
| **边界电荷怎么中和** | ❌ | ❌ | ❌ | **G 层 `16_…` §2.8 独家**（MM 区残留 −0.0362，分摊到 6 个主链原子） |
| **电子溢出（spill-out）** | ❌ | ✅ **P17 电子泄漏**：查电子密度图；**离子材料里问题较小** | ✅ **P24**：高斯基抹平 MM 电荷就是为了"prevent spill out problem"；**P25**：抹高斯是"repair the broken covalent bonds at the QM/MM boundaries"的手段 | T22 P17 + T23 P24/P25 |
| **边界势（border potential）** | ❌ | ✅ **P18–P19 完整**（起因 A/B + 三步解法 + 输入实现） | ❌ | T22 P18–P19 |
| **PBC 下的背景电荷** | ❌ | ❌ | ✅ **P55–P57**：`n(r) = n_QM + n_MM ± n_B`，四项能量全部用 `(n+n_B)` 一致处理 | T23 P55–P57 |

#### (b) 为什么这是 QM/MM 最容易出错的地方 —— 教材自身给出的理由（逐条溯源）

1. **能量分解里，边界项没有任何"天然"定义。** 加和式 `E_TOT = E_MM,tot + E_QM(QM) + E_QM/MM`（T23 P4/P15/P22）
   里的 `E_QM/MM` 是一个**人为加进去的项**，它没有唯一的定义；而减式（T23 P13）里
   `−E_MM(QM)` 那一项要求"**活性区也要被 MM 力场描述一遍**"——**同一个原子在两种描述之间切换，边界处的电荷/参数不一致就会在这里露出来**。
2. **共价键被切断是"物理上不存在"的操作。** T23 P25 的论文原文只说抹高斯是为了
   "**repair the broken covalent bonds at the QM/MM boundaries**"，并**明确声明本文不处理这个问题**——
   换句话说：**CP2K 的 GEEP 只是用抹高斯把断键处的静电做平滑，它不"修复"断键本身**。
   T21 P18 那句"必须加 LINK atoms"才是真正的补丁，而 T21 只给了一个 `LINK_TYPE IMOMM (H-capping)` 的示例。
3. **QM 区被 MM 环境极化后，QM 的电子密度会往边界外"漏"（spill-out）。** T23 P24 把
   `n(r,R_MM) = (r_c/√π)³ e^(−(…)²)` 和 `v = Erf(|r−R|/r_c)/|r−R|` 两个式子直接标为
   "**prevent spill out problem!**" + "**accelerate calculations of electrostatics**"——
   **注意这句话的作用域**：它是从文献里抽出来的，原文语境是"**我们不再处理断键，而是靠抹高斯来防止溢出**"。
   T22 P17 给了**检查手段**（看电子密度图）并给了**经验判断**（离子材料里问题较小）。
4. **边界处两套描述不一致会留下虚假的力。** T22 P18 的解法③把判据写得很硬：
   "**Forces on border atoms should reach 0 ideally**"——**边界原子上的力不为零 = 模型没调好**。
   而 T22 P18 列的起因 A（**QM 区与 MM 区晶格常数不同**）说明这类不一致**不需要共价键就能发生**。
5. **PBC + 带电体系会引入背景电荷，而 QM/MM 的四项能量必须一致地处理它。** T23 P55–P57：
   `n(r) = n_QM(r) + n_MM(r) ± n_B`，`E_TOT / E_MM / E_QM / E_QM/MM` 四项**每一项**都写成
   `(n + n_B)(n' + n_B)` 的形式。**只处理其中几项 ⇒ 边界/背景的误差直接进总能量**。

#### (c) T22 给的"边界势"三步处方（**本层独有的可操作内容**，T22 P18–P19）

```
起因 A：QM 区与 MM 区的晶格常数不同
起因 B：边界处更复杂的相互作用（共价键等）

解法（针对起因 A）：
  1. Fix the atoms to the desired positions          （先把原子固定到目标位置）
  2. Optimize an additional set of additive pair potentials  （再优化一组附加的加和性对势）
  3. Forces on border atoms should reach 0 ideally    （边界原子的力应降到 0）
```

**实现方式（T22 P19）**：在 `&MM &FORCEFIELD &NONBONDED` 里**沿用 `&WILLIAMS` 形式**，
但**给边界原子单独造一套原子类型（`KZ` / `ClZ`，注释写着 "border KCl"）**，
它们的 `RCUT [angstrom]` 从 3.0 放大到 **5.0**，然后覆盖边界相关的所有配对。
原文还留了一句"如果你要 KCl(001) 块体的边界势、或要现成脚本，**直接问我要**"
——这句话本身是个提示：**这类势是逐体系手工拟合的，没有通用值**。

#### (d) 一个必须指出的"层间张力"

- T23 P25（Laino 2005 原文）：**"In contrast here, we do not address the issue of treating QM/MM regions crossed by a covalent bond"**
  —— CP2K 的 GEEP 论文**主动回避**了断键问题。
- T21 P17：**"If covalent bonds between QM and MM regions -> LINK atoms must be added"**
  —— 教材告诉你**必须**加。
- T22 整份**没有一个字**提 link atom，它的体系（KCl(001) 上的分子膜）走的是"**离子衬底 + 完整分子**"的路线，
  所以它把全部注意力放在**边界势**而不是**连接原子**上。

**合起来才是完整判断**：`&LINK` 解决"**共价断键**"，**边界势**解决"**离子/异质界面上的对势不匹配**"，
**抹高斯（GEEP）** 只解决"**断键处的静电平滑与溢出抑制**"。**三者不是替代关系，各管一段**——
教材从没在一页里把这三者并列过，这是本笔记的归纳（依据：T21 P17、T22 P18–P19、T23 P24–P25）。

---

### 3.3 QM 区怎么选、QM 区大小与成本的权衡、半经验 vs DFT

#### (a) QM 区怎么在 CP2K 里"选"—— 用 MM 编号的 `MM_INDEX`

T21 P16 的注释写得最直白：`MM_INDEX 1 5`（**indexes following MM numbering**）。
即 **QM 区是用 MM 体系的原子编号来指定的**。三份材料的写法汇总：

| 写法 | 出处 | 形式 |
|---|---|---|
| 逐一列举 | T21 P16–P18 | `&QM_KIND C` + `MM_INDEX 1 5` |
| **区间简写 `..`** | T22 P11 | `&QM_KIND K MM_INDEX 25..32 41..48` |
| 水分子示例 | T23 P51 | `&QM_KIND O MM_INDEX 7` / `&QM_KIND H MM_INDEX 8 9` |
| 蛋白质残基示例 | G 层 `16_…` §2.4 | `&QM_KIND O MM_INDEX 5668 5669 …`（指针） |

**注意 `&QMMM &CELL` 是"QM 盒"而不是整个模拟胞**：T21 P16 注释 `&CELL !QM box size ABC [angstrom] 25.0 25.0 25.0`；
T23 P51 里 **QM 盒 6.0 Å、MM 盒 15.0 Å**；T22 P11 里 **QM 盒 `12.6 15.0 12.6`、整个体系胞 `12.6 50 12.6`**（z 方向留真空）。
**QM 盒不是 QM 区的定义者**——定义者是 `&QM_KIND` 的 `MM_INDEX`；`&CELL` 是**放 QM 波函数/网格的盒子**。

#### (b) QM 区大小与成本的权衡 —— 教材给的是"标度"，不是"经验半径"

三份材料**都没有**给出"QM 区半径应取 5 Å / 10 Å"这类数值。它们给的是**代价怎么长**：

| 环节 | 标度 | 出处 |
|---|---|---|
| 朴素静电积分（直算） | `N_u × N_MM`（10⁶ × 10⁴）"**impractical**" | T23 P25 |
| 同格子静电 | `Cost ≈ N_MM × P1`（**线性于 MM 原子数**） | T23 P17 |
| 球截断静电 | `Cost ≈ N_c × P1`（只算球内 `N_c` 个） | T23 P18 |
| 增大多格子层数 | `Scaling ~ N_c³` | T23 P44 |
| **GEEP 加速因子** | `(N_f/N_c)³ = 2^(3(N_grid−1))`；3–4 级 ⇒ **64–512 ≈ 100×** | T23 P66 |
| GEEP 时间预算 | collocation **60–80%**；插值 **20–40%** | T23 P29 / P50 |
| IC-QM/MM（若用 IC） | 单点：解线性方程组（高斯消元）；**MD/优化：预条件 CG，每次 2 次 FFT + N_IC 次数值积分**；T 可复用 | T23 P80 |

**能读出的唯一"大小权衡"判据**（要小心，这是教材的间接表述）：
- QM 区变大 ⇒ `N_MM` 变小但 QM 的 SCF 变贵，同时**边界变长** ⇒ 边界势/连接原子的问题面变大（T22 P18 "QM atoms interact with MM atoms at the border"）。
- QM 区变小 ⇒ spill-out 风险上升（T23 P24 把"防止溢出"和"加速静电"并列成高斯抹平的两个目的），T22 P17 把"**看电子密度图**"列为必做检查。
- **教材给的唯一硬性验收动作**：T22 P18 第 3 步 —— **边界原子的力应降到 0**；T22 P15 的三条评估流程（比物理性质、比电子结构、查常见失效）。

#### (c) 半经验（PM6 等）与 DFT 做 QM 区的取舍

**教材原文出处**：

| 出处 | 原文/要点 |
|---|---|
| T21 P11 | `&QS METHOD GPW (or **DFTB/PM6/…**)` —— **半经验方法挂在 `&QS METHOD` 上**，与 GPW 并列 |
| T21 P16 | `ECOUPL GAUSS (or NONE/MULTIPOLE/…)` + `USE_GEEP_LIB 9` —— **`ECOUPL GAUSS`/`USE_GEEP_LIB` 与 GPW 网格路线绑在一起**（T23 P23–P29 全是高斯基 + 平面波网格的 collocation） |
| T23 P5 | "**Choice of QM method (semi empirical, DFT, QC)!**" —— 只列为**必须做的选择之一**，**没有给取舍判据** |
| T23 P7（Biochemistry 综述抽页） | 方法谱"**from cheaper and more approximate methods, which can be used for molecular dynamics simulations, to highly accurate electronic structure methods**" —— **唯一一句把"能不能跑 MD"与"方法便宜程度"挂钩的话** |
| G 层 `24_official_exercises.md` §1.3 / §1.2 | 官方 QM/MM NEB 练习用 **PM6** 做 56 原子分子、EAM 做 2900 原子 Cu 衬底；官方另一处明确"练习用 PM6 只是便宜，准确表征反应要用 DFT 或更高"（**指针**） |

**结论（教材可支撑的版本）**：
1. **半经验 = 便宜到能跑动力学**（T23 P7）；DFT = 精度上限，但**QM/MM 静电项要上 GEEP 才能在动力学里承受**（T23 P29/P66）。
2. **换了 QM 方法，静电耦合关键字也要跟着换**：`ECOUPL GAUSS`/`USE_GEEP_LIB` 是 DFT/GPW 路线的加速器（T23 P23–P29、P51、P65）；
   G 层给的官方写法是半经验配 `E_COUPL COULOMB`（**指针**：`16_qmmm_embedding_ml.md` §2.5）。
   **这两条不冲突但也不能混用**——见 §6 的纠错条目。
3. 三份材料**都没有**做"PM6 vs DFT 的 QM/MM 结果对比"。

---

### 3.4 AIMD 语境下的特殊问题

> **先说结论：这份 86 页的 T23，标题里有 "in ab initio molecular dynamics"，
> 但它没有一节专门讲"QM 区在动力学中如何定义/如何随时间变化"。**
> "水分子进出 QM 区怎么办（自适应缓冲）"**在这 137 页里没有任何方法内容**。
> 下面把"教材真讲了什么"和"教材没讲什么"分开列，避免下游误用。

#### (a) 教材**真讲了**的 AIMD 相关方法学（都可指页）

| 主题 | 内容 | 页 |
|---|---|---|
| **为什么 QM/MM 做 AIMD 会卡** | QM/MM 静电项的 collocation 占 **60–80%** 机时（P29），插值占 **20–40%**（P50）；朴素直算 `N_u×N_MM` "impractical"（P25）。**每一步 MD 都要重算一次**——这才是 GEEP 存在的理由 | T23 P25/P29/P50 |
| **让动力学跑得动的加速** | GEEP 多格子（3–4 级 ⇒ ≈100×，P66）；球截断（P18）；多极（P19）；PBC 下额外开销很小（P66） | T23 P17–P19, P66 |
| **PBC 下的静电** | Ewald 分实空间/倒空间（P52–P53）；**带电体系必须有背景电荷** `±n_B`，且 `E_TOT/E_MM/E_QM/E_QM/MM` 四项一致处理（P55–P57）；残差函数倒空间只需少量 k 向量（P63–P64） | T23 P52–P57, P62–P64 |
| **从"全 QM 周期"到"单 QM 区"** | **De-coupling and re-coupling**（P70–P71）+ **Bloechl 密度拟合**给解耦/再耦合用的电荷（P72） | T23 P70–P72 |
| **周期性怎么落到 2D 体系** | **Sandwich 模型："Periodic in 2 Dimensions: The Infinite Sandwich Model"**（T22 P5）；输入上是 `&QMMM &CELL … PERIODIC XZ` 与整个体系胞 `PERIODIC XZ`（T22 P11–P12） | T22 P5, P11–P12 |
| **生产规模的 MD 算例** | ① **SiO₂ 中带电氧空位的迁移**（P73–P75）+ **NEB 最小能量路径**（P78–P79）；② **水/Pt(111) 薄膜的 MD 快照、分层密度、RDF、H 键分布**（P85–P86）；③ **12 个水分子的团簇**偶极矩分析（P84） | T23 P73–P79, P84–P86 |
| **动力学/优化专用的算法选择** | IC-QM/MM："**Gaussian elimination … always the method of choice for single point calculations. The preconditioned-CG is used for geometry optimizations and MD simulations.**"；**矩阵 T 可复用若干步再更新** | T23 P80 |
| **输入侧的动力学骨架** | `&MOTION &MD ENSEMBLE NVT STEPS 5000 TIMESTEP 0.5 TEMPERATURE 298` + `&THERMOSTAT TYPE CSVR &CSVR TIMECON [fs] 50.`；`&GLOBAL RUN_TYPE MD`；`touch EXIT_MD` 优雅停止；`&EXT_RESTART RESTART_POS/VEL/THERMOSTAT TRUE`；每个 MD 步 `&PRINT &EACH MD 20` 打印 Mulliken | T21 P23/P25/P27/P12 |

#### (b) 教材**没讲**的（**必须如实标注为缺口**）

| 问题 | 状态 | 页证据 |
|---|---|---|
| **QM 区在动力学中如何定义 / 如何随时间变化** | **没有方法内容**。三份材料的 `&QM_KIND` 都是**静态列表**（T21 P16–P18 / T22 P11 / T23 P51），**没有任何一处**给出"随时间更新 QM 区"的语法或流程 | T21 P16, T22 P11, T23 P51 |
| **水分子进出 QM 区 / 自适应缓冲（adaptive buffer）** | **137 页里"adaptive QM regions"只出现一次，且只是标题**：T23 P8 "0.11 million atoms! 5 QM regions: effects of O implantation into Si! **adaptive QM regions** / simoX technology"（Yoshio Tanaka AIST & Aiichiro Nakano USC）——**无方法、无输入、无判据** | T23 P8（唯一出处） |
| **QM/MM 与 metadynamics / 增强采样** | 三份材料**均未提及** | — |
| **QM/MM 断键/成键反应在 QM 区内的处理** | 三份均未给判据；T23 P7 的综述抽页只提到"可以研究过渡态结构" | T23 P7 |

> **旁证（E 层，非本层结论，只作交叉指路）**：E 层 `pdf_text/learn_L2.md` 第 178/249/503 行提到
> 庚子课程讲过 "**adaptive buffered QM/MM**" 与用其模拟 Criegee 反应（*JACS* 2016, 138(35), 11164-9）。
> **那是 E 层（第三方培训）的内容，H 层的 T21–T23 没有覆盖**。若下游要写"自适应缓冲"，
> 必须回 E 层取原文，**不能从本笔记推**。

---

## 4. 可执行要点（输入片段照抄）

> **抄录原则**：`txt/` 原文里代码块被 pdfplumber 按版面重排过，**同一段输入的字面顺序常与原文不同**。
> 下面凡涉及"两栏串行"的片段，按**语义还原块结构**（缩进、块配对），
> **关键字名、关键字大小写、参数值一律照抄原文**；被还原的部分在注释里标明原文行号。

### 4.1 T22 P10：2D 嵌入的 MM 部分（`&FORCE_EVAL METHOD QMMM` + `&MM`）

原文行 108–131（**两栏串行**）。还原后的块结构：

```
&FORCE_EVAL
  METHOD QMMM                      # (QMMM/FIST/QS)
  @include QS.inc                  # (The usual DFT stuff!)
  &MM                              # (This is from @include MM.inc)
    &FORCEFIELD
      &CHARGE
        ATOM K
          CHARGE 1.0
        &END CHARGE
        ATOM Cl
          CHARGE -1.0
        &END CHARGE
      &END CHARGE
      &NONBONDED
        &WILLIAMS
          atoms K Cl
          A [eV]            4117.9
          B [angstrom^-1]   3.2808
          C [eV*angstrom^6] 0.0
          RCUT [angstrom]   3.0
        &END WILLIAMS
        &WILLIAMS
          atoms Cl Cl
          A [eV]            1227.2
          B [angstrom^-1]   3.1114
          C [eV*angstrom^6] 124.0
          RCUT [angstrom]   3.0
        &END WILLIAMS
        &WILLIAMS
          atoms K K
          A [eV]            3796.9
          B [angstrom^-1]   3.84172
          C [eV*angstrom^6] 124.0
          RCUT [angstrom]   3.0
        &END WILLIAMS
      &END NONBONDED
    &END FORCEFIELD
    &POISSON                        # (POISSON section in the MM part)
      &EWALD
        EWALD_TYPE spme
        ALPHA .44
        GMAX 40
      &END EWALD
    &END POISSON
  &END MM
```

> ⚠️ **原文里有两处 `&CHARGE` 的嵌套写法**（`&FORCEFIELD &CHARGE … &END CHARGE / ATOM Cl / CHARGE -1.0 / &END CHARGE / &END CHARGE`），
> 看上去是"每个原子一个 `&CHARGE` 子块，外面再套一层 `&CHARGE`"。**照抄原文，但落地时要按 G 层/手册核对**——
> 本层只负责如实记录教材写了什么（§7 存疑第 4 条）。
> 另注意原文 `&WILLIAMS` 里用的是**小写 `atoms`**，而 §4.6 的边界势片段里是**大写 `atoms`**——原文如此，未统一。

### 4.2 T23 P12：纯 MM 输入（作 QM/MM 的 MM 半边参考）

原文行 317–351（**两栏串行**）。行号对照：319/321/326/329-333/335-347/349 = 左栏（`&MM` 路径），
322-325/327-328/330-345 交错 = 右栏（`&SUBSYS`/`&POISSON` 路径）。

```
&FORCE_EVAL
  !
  METHOD FIST
  !
  &MM
    &FORCEFIELD
      PARM_FILE_NAME acn.pot
      PARMTYPE CHM
      &CHARGE
        ATOM CT
        CHARGE -0.479
      &END CHARGE
      !
      &CHARGE
        ATOM YC
        CHARGE 0.481
      &END CHARGE
      &CHARGE
        ATOM YN
        CHARGE -0.532
      &END CHARGE
      &CHARGE
        ATOM HC
        CHARGE 0.177
      &END CHARGE
    &END FORCEFIELD
    !
  &END MM
  !
  &POISSON
    &EWALD
      EWALD_TYPE SPME
      ALPHA .44
      GMAX 32
      O_SPLINE 6
    &END EWALD
  &END POISSON
  &SUBSYS
    &CELL
      ABC 27.0 27.0 27.0
    &END CELL
    &TOPOLOGY
      CONNECTIVITY PSF
      CONN_FILE_NAME acn_topology.psf
      COORD_FILE_NAME acn_topology.pdb
      COORDINATE pdb
    &END TOPOLOGY
  &END SUBSYS
  STRESS_TENSOR ANALYTICAL
  !
&END FORCE_EVAL
```

> **注意 `O_SPLINE 6`**：T21 P14 与 T23 P12 的 `&EWALD` 里都有这一项（T21 的 P14 只列了 `EWALD_TYPE SPME`，未列 `O_SPLINE`）——
> **T23 P12 是三份材料里唯一给出 `O_SPLINE 6` 的地方**（T22 P10 只给 `EWALD_TYPE spme / ALPHA .44 / GMAX 40`）。
> 也在 `STRESS_TENSOR ANALYTICAL` 出现在 `&FORCE_EVAL` 层级（**不是** 在 `&MM` 里）——原文如此。

### 4.3 T23 P14：减式 QM/MM 的 **`&MULTIPLE_FORCE_EVALS` 完整片段**（本层最稀缺的一块）

原文行 371–405（**两栏串行**，实际是"左：`&MULTIPLE_FORCE_EVALS` + `&FORCE_EVAL METHOD MIXED`；右：第 2/3/4 个 `&FORCE_EVAL`"）。
**这是本层相对 G 层的最大增量之一**：G 层 `18_restarting.md` L647 与 `20_input_reference_tree.md` L60/L196 只登记了
`&MIXED`/`&MAPPING` 的存在，`24_official_exercises.md` §1.3 给的是官方练习的 `E1+E2` 变体；
**T23 P14 给的是 `X+Y-Z` 的减式变体**（含 `FORCE_EVAL_ORDER 1 2 3 4` 与三个注释映射）。

```
&MULTIPLE_FORCE_EVALS
  FORCE_EVAL_ORDER 1 2 3 4
&END MULTIPLE_FORCE_EVALS
!
&FORCE_EVAL
  METHOD MIXED
  &MIXED
    MIXING_TYPE GENMIX
    # X: Energy force_eval 2
    # Y: Energy force_eval 3
    # Z: Energy force_eval 4
    MIXING_FUNCTION X+Y-Z
    VARIABLES X Y Z
    &GENERIC
    &END GENERIC
  &END MIXED
  &SUBSYS
    &TOPOLOGY
      CONNECTIVITY PSF
      CONN_FILE_NAME topo.psf
      COORD_FILE_NAME totsys.xyz
    &END TOPOLOGY
    &CELL
      ABC 19.729 19.729 19.729
    &END CELL
  &END SUBSYS
&END FORCE_EVAL
!
&FORCE_EVAL
  METHOD FIST
  &MM
    ……
  &END MM
  &SUBSYS
    &TOPOLOGY
      CONNECTIVITY PSF
      CONN_FILE_NAME topo.psf
      COORD_FILE_NAME totsys.xyz
    &END TOPOLOGY
    &CELL
      ABC 19.729 19.729 19.729
    &END CELL
  &END SUBSYS
&END FORCE_EVAL
!
&FORCE_EVAL
  METHOD FIST
  &MM
    ……
  &END MM
  &SUBSYS
    &TOPOLOGY
      CONNECTIVITY PSF
      CONN_FILE_NAME qmtopo.psf
      COORD_FILE_NAME qmsys.xyz
    &END TOPOLOGY
    &CELL
      ABC 19.729 19.729 19.729
    &END CELL
  &END SUBSYS
&END FORCE_EVAL
!
&FORCE_EVAL
  METHOD QS
  &DFT
    ……
  &END DFT
  &SUBSYS
    &TOPOLOGY
      CONNECTIVITY PSF
      CONN_FILE_NAME qmtopo.psf
      COORD_FILE_NAME qmsys.xyz
    &END TOPOLOGY
    &CELL
      ABC 19.729 19.729 19.729
    &END CELL
  &END SUBSYS
&END FORCE_EVAL
```

> **读法（原文注释直译）**：`X` = 第 2 个 `force_eval` 的能量（**整个体系用 MM**），
> `Y` = 第 3 个（**QM 区用 MM**），`Z` = 第 4 个（**QM 区用 QS**），`MIXING_FUNCTION X+Y-Z`
> 正好是减式 `E_MM,tot + E_MM(QM) − E_QM(QM)` 的**符号约定**（注意与 T23 P13 的公式写法
> `E_MM,tot + E_QM(QM) − E_MM(QM)` **符号相反**，因为这里 `Z` 是 QM、`Y` 是 QM 区的 MM）。
> **`&CELL ABC` 三段相同（19.729³）**，但**拓扑不同**（`topo.psf`+`totsys.xyz` vs `qmtopo.psf`+`qmsys.xyz`）。

### 4.4 T23 P51：**GEEP 的 `&QMMM` 完整示例**（照抄原文块序）

原文行 955–992（两栏串行：左 = `&QMMM`+`&MM`+`&DFT`+`&MM_KIND`+`&SUBSYS`，右 = 各行值）。
**还原后**：

```
&QMMM
  &CELL
    ABC 6.0 6.0 6.0
  &END CELL
  USE_GEEP_LIB 9
  ECOUPL GAUSS
  !
  &MM_KIND H
    RADIUS 0.44
  &END MM_KIND
  &MM_KIND O
    RADIUS 0.78
  &END MM_KIND
  !
  &QM_KIND H
    MM_INDEX 8 9
  &END QM_KIND
  &QM_KIND O
    MM_INDEX 7
  &END QM_KIND
  !
&END QMMM
!
&MM
  ……
&END MM
!
&DFT
  ……
&END DFT
!
&SUBSYS
  &CELL
    ABC 15.0 15.0 15.0
  &END CELL
  !
  &TOPOLOGY
    COORD_FILE_NAME sys.pdb
    COORDINATE pdb
  &END TOPOLOGY
&END SUBSYS
```

> **两个数字要记牢**：**QM 盒 6.0 Å** vs **MM 盒 15.0 Å**（`&QMMM &CELL` 与 `&SUBSYS &CELL`）。
> `RADIUS 0.44`(H) / `RADIUS 0.78`(O) 是 **MM 高斯宽度**（T22 P11 注释 "Width of MM Gaussians"）。

### 4.5 T23 P65：**周期性 GEEP 的 `&QMMM` 完整片段**（照抄）

原文行 1157–1182，**未被两栏串行破坏**，可直接照抄：

```
&QMMM
  &CELL
    ABC 17.320500 17.320500 17.320500
  &END CELL
  !
  ECOUPL GAUSS
  USE_GEEP_LIB 6
  !
  &MM_KIND NA
    RADIUS 1.5875316249000
  &END MM_KIND
  &MM_KIND CL
    RADIUS 1.5875316249000
  &END MM_KIND
  !
  &PERIODIC
    GMAX 0.5
    &MULTIPOLE
      EWALD_PRECISION 0.00000001
      RCUT 8.0
      NGRIDS 20 20 20
      ANALYTICAL_GTERM
    &END MULTIPOLE
  &END PERIODIC
  !
&END QMMM
```

> ⚠️ **关键字大小写照抄原文**：这里是 **`&MM_KIND NA` / `&MM_KIND CL`**（大写），
> 而 T22 P11 是 `&MM_KIND K` / `&MM_KIND Cl`（元素名混合大小写）。
> **两者都是教材原文**，落地时以 G 层/手册的元素名规范为准（§7 存疑第 5 条）。

### 4.6 T22 P19：**边界势的输入实现**（照抄原文块结构）

原文行 300–333（**两栏串行**）。还原后：

```
&MM
  &POISSON
    &EWALD
      EWALD_TYPE spme
      ALPHA .44
      GMAX 40
    &END EWALD
  &END POISSON
  &FORCEFIELD                       # (the normal sets of potentials)
    &CHARGE
      ATOM K
      CHARGE 1.0
    &END CHARGE
    &CHARGE
      ATOM Cl
      CHARGE -1.0
    &END CHARGE
    &CHARGE                         # (border KCl)
      ATOM KZ
      CHARGE 1.0
    &END CHARGE
    &CHARGE
      ATOM ClZ
      CHARGE -1.0
    &END CHARGE
    &NONBONDED
      &WILLIAMS
        atoms K ClZ
        A [eV]            4117.9
        B [angstrom^-1]   3.2808
        C [eV*angstrom^6] 0.0
        RCUT [angstrom]   5.0
      &END WILLIAMS
      &WILLIAMS
        atoms KZ Cl
        A [eV]            4117.9
        B [angstrom^-1]   3.2808
        C [eV*angstrom^6] 0.0
        RCUT [angstrom]   5.0
      &END WILLIAMS
      &WILLIAMS
        atoms KZ KZ                  # (all other possible pairings)
        A [eV]            4117.9
        B [angstrom^-1]   3.2808
        C [eV*angstrom^6] 0.0
        RCUT [angstrom]   5.0
      &END WILLIAMS
      &WILLIAMS
        atoms ClZ ClZ
        A [eV]            4117.9
        B [angstrom^-1]   3.2808
        C [eV*angstrom^6] 0.0
        RCUT [angstrom]   5.0
      &END WILLIAMS
    &END NONBONDED
  &END FORCEFIELD
&END MM
```

> **关键差异一目了然**：`RCUT` 从体相的 **3.0** 放宽到 **5.0**，并引入 **`KZ` / `ClZ` 两个新原子类型**。
> 原文注释只有三句："the normal sets of potentials" / "(border KCl)" / "(all other possible pairings)"，
> 以及页脚"如果你需要 KCl(001) 块体的边界势或脚本，直接问我要"。
> **参数值（4117.9 / 3.2808 / 0.0）原文里边界势与体相 K-Cl 相同**——照抄，不做解释。

### 4.7 T22 P11 + P12：2D 嵌入的 `&QMMM` 与体系设置（合并照抄）

```
&QMMM
  &CELL                       # (Size of QS Cell)
    ABC 12.6 15.0 12.6
    PERIODIC XZ
  &END CELL
  &MM_KIND K                  # (Width of MM Gaussians)
    RADIUS 1.52
  &END MM_KIND
  &MM_KIND Cl
    RADIUS 1.67
  &END MM_KIND
  ECOUPL GAUSS                # (Use GEEP)
  #should be treated as parameters
  NOCOMPATIBILITY
  USE_GEEP_LIB 6
  NOCENTER F                  # ← 更正：与上面三行**同级**（&QMMM 的直接关键字），不在 &QM_KIND 里
  NOCENTER0 F
  &QM_KIND K
    MM_INDEX 25..32 41..48
  &END QM_KIND
  &QM_KIND Cl
    MM_INDEX 17..24 33..40
  &END QM_KIND
  &PERIODIC                   # (Apply periodic potential)
    &MULTIPOLE OFF            # QM multipole coupling
                              # use if XY of MM box =/= QM box
    &END MULTIPOLE
  &END PERIODIC
&END QMMM
```

```
&SUBSYS
  &CELL                       # (Size of Entire System)
    ABC 12.6 50 12.6
    PERIODIC XZ
  &END CELL
  &TOPOLOGY
    COORD_FILE_NAME kcl.xyz
    COORD_FILE_FORMAT XYZ
    &GENERATE
      &ISOLATED_ATOMS         # (Ignores bonds, dihedrals...)
        LIST 1..48
      &END ISOLATED_ATOMS
    &END GENERATE
  &END TOPOLOGY
  &KIND K
    ELEMENT K
    BASIS_SET DZVP-MOLOPT-SR-GTH
    POTENTIAL GTH-PBE-q9
  &END KIND
  &KIND Cl
    ELEMENT Cl
    BASIS_SET DZVP-MOLOPT-GTH
    POTENTIAL GTH-PBE-q7
  &END KIND
&END SUBSYS
```

```
&GLOBAL
  PRINT_LEVEL MEDIUM
  PROJECT_NAME KCl
  RUN_TYPE GEO_OPT
  FLUSH_SHOULD_FLUSH
&END GLOBAL

&MOTION
  &GEO_OPT
    OPTIMIZER LBFGS
  &END GEO_OPT
  &CONSTRAINT
    &FIXED_ATOMS
      LIST 1..16
      EXCLUDE_MM .FALSE.
      EXCLUDE_QM .TRUE.
    &END FIXED_ATOMS
  &END CONSTRAINT
&END MOTION
```

> ⚠️ **`&GLOBAL` 的 `FLUSH_SHOULD_FLUSH`** 是 T22 P12 独有的关键字（T21 的 `&GLOBAL` 段没有，T23 也没给）。
> ⚠️ **`NOCENTER F` / `NOCENTER0 F` 的归属——已更正（原来放在 `&QM_KIND K` 里，是错的）**：
> 按 x 中分**重抽源 PDF 第 11 页**后，这两行与 `ECOUPL GAUSS` / `NOCOMPATIBILITY` / `USE_GEEP_LIB 6`
> **同级缩进**，是 **`&QMMM` 的直接关键字**；CP2K **2.4** 手册的 `&QMMM` 关键字表也把它们列在 `&QMMM` 下
> （<https://manual.cp2k.org/cp2k-2_4-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html>）。原来那个"在 `MM_INDEX` 前后各一行"的
> 顺序，是文本层把 **`&CELL` 右栏插进 `&QMMM` 左栏**造成的**假嵌套**。
> 语义与现代化改写见 **§7 第 11 条**（`NOCENTER`/`NOCENTER0` 在 CP2K 2.6 起被
> `CENTER` / `CENTER_TYPE` / `CENTER_GRID` 取代，**trunk 里已不存在**）。

### 4.8 T21 P16/P18：最小可用的 `&QMMM` + `&LINK`（照抄）

```
&QMMM
  USE_GEEP_LIB 9        # of gaussians to be used in the expansion of elect. potential
  ECOUPL GAUSS          # (or NONE/MULTIPOLE/…); type of QM/MM elect. coupling
  &CELL                 # !QM box size
    ABC [angstrom] 25.0 25.0 25.0
  &END CELL
  &QM_KIND C
    MM_INDEX 1 5        # (indexes following MM numbering)
  &END QM_KIND
  &QM_KIND H
    MM_INDEX 2 3 4 6 7
  &END QM_KIND
  &LINK
    LINK_TYPE IMOMM     # (H-capping)
    QM_INDEX 5
    MM_INDEX 8
  &END LINK
&END QMMM
```

> **`QM_INDEX` 在前、`MM_INDEX` 在后**（T21 P18 原文行 384–385）。
> ⚠️ **G 层 `16_qmmm_embedding_ml.md` §2.7 的官方示例顺序相反**（`MM_INDEX 1411` → `QM_INDEX 1413` → `LINK_TYPE IMOMM`）。
> **两者都是原文**；关键字段落的顺序在 CP2K 里通常无关（T21 P2："shuffling is allowed"），但**落地时应以 G 层为准**。
> 另：T21 P16/P17 的 `&QM_KIND H` 是 `MM_INDEX 2 3 4 6 7 8`（**6 个**索引），**P18 变成 `MM_INDEX 2 3 4 6 7`（5 个）**——
> 差别正是**原子 8 从 QM 挪到 MM**，而 `&LINK` 的 `QM_INDEX 5 / MM_INDEX 8` 正好**成对地补上这次挪动**
> （P17 那句"If covalent bonds between QM and MM regions -> LINK atoms must be added"对应的就是这一步）。
> **可确认的事实**：P16/P17 的 QM 原子集 = {C:1,5} ∪ {H:2,3,4,6,7,8}；P18 的 QM 原子集 = {C:1,5} ∪ {H:2,3,4,6,7}，
> 且 P18 声明的连接是 **QM 侧 5 ↔ MM 侧 8**。至于 5 与 8 在真实分子图里是否直接成键，
> 原文只给示意图（P17/P18 的数字标注图），**文本层无法确认**（见 §7 存疑 13）。
>
> ⚠️ 由此产生一个**必须注意的细节**：P18 的 `MM_INDEX 8` 是**两种含义**——`&QM_KIND` 里的
> `MM_INDEX` 指"哪些 MM 编号的原子进 QM 区"，`&LINK` 里的 `MM_INDEX` 指"连接键的 MM 侧原子"。
> **同名不同义**，抄输入时不要混。

### 4.9 T21 P25/P23/P27：AIMD 骨架（照抄）

```
&GLOBAL
  PRINT_LEVEL MEDIUM        # (or SILENT/LOW/HIGH/…)
  PROJECT_NAME MY_PROJECT
  RUN_TYPE MD               # (原文给的是 ENERGY_FORCE (or GEO_OPT/MD/…))
  WALLTIME 86400
&END GLOBAL

&MOTION
  &MD                       # (or GEO_OPT/MC/…)
    ENSEMBLE NVT            # (or NVE/NPT/…)
    STEPS 5000
    TIMESTEP 0.5
    TEMPERATURE 298
    &THERMOSTAT
      TYPE CSVR             # (or NOSE/…)
      &CSVR
        TIMECON [fs] 50.
      &END CSVR
    &END THERMOSTAT
    &CONSTRAINT
      ...
    &END CONSTRAINT
  &END MD
&END MOTION

&EXT_RESTART
  RESTART_FILE_NAME NAME-1.restart
  RESTART_DEFAULT FALSE
  RESTART_POS TRUE
  RESTART_VEL TRUE
  RESTART_THERMOSTAT TRUE
  RESTART_AVERAGES FALSE
  RESTART_COUNTERS FALSE
  ...
&END EXT_RESTART
```

> `touch EXIT` / `touch EXIT_MD`：**优雅停止**（T21 P23）。
> "**WFN is read if activated in &FORCE_EVAL**"（T21 P27）——**波函数重启的开关在 `&FORCE_EVAL` 里，不在 `&EXT_RESTART` 里**。
> `&QM_KIND` / `&LINK` 是**静态的**：`&EXT_RESTART` 段里**没有任何**与 QM 区相关的重启项（T21 P27 全列）。

### 4.10 加速与误差控制的"数"（来自 T23，可直接当工作预算）

| 项 | 值 | 页 |
|---|---|---|
| GEEP 常用网格层数 | **3–4 级** | T23 P66 |
| GEEP 加速因子 | `2^(3(N_grid−1))` ⇒ 64–512 ≈ **100×** | T23 P66 |
| collocation 占 QM/MM 时间 | **60–80%** | T23 P29 |
| 插值占 QM/MM 时间 | **20–40%** | T23 P50 |
| 误差来源① 网格层截断 | **每线方向 20–25 个点** | T23 P67 |
| 误差来源② | 三次样条插值误差 | T23 P67 |
| 误差来源③ 粗网格截断 | 应与**长程函数的截断**相当 | T23 P67 |
| 多极（`&MULTIPOLE`）示例参数 | `EWALD_PRECISION 1e-8` / `RCUT 8.0` / `NGRIDS 20 20 20` | T23 P65 |
| IC 高斯宽度 α 收敛判据 | **α > 3.0 Å⁻² 后能量与梯度不再显著依赖 α** | T23 P83 |
| IC 水/Pt 精度 | 所有水体系偏差 **< 4.0 kJ/mol** | T23 P84 |

---

## 5. 【新】相对既有 A–G 层的增量

> **先 grep 确认过的结论**（命令与命中位置见下）。G 层 `16_qmmm_embedding_ml.md` 已有的内容**只写指针**。

**grep 覆盖检查**（对本轮新知识的关键字，在 `references/official/`、`references/decide.md`、
`references/playbook.md`、`references/course_learned.md`、`references/course_notes.md`、
`references/manual_notes.md`、`references/sections.md`、`references/pdf_text/` 全查）：

| 关键字 | 既有层命中 | 结论 |
|---|---|---|
| `MM_KIND` | 仅 `official/06_properties.md` L146（**列为"G 层未抓取的缺口"**）、`official/20_input_reference_tree.md` L202/L295（**只列段名**）、`decide.md` L687 未列 | **新增**：T22 P11 给 `RADIUS` 实例值、T23 P51/P65 给第二/第三组值 |
| `USE_GEEP_LIB` | `official/16_…` L148（**只提"GEEP 可用"**）、`decide.md` **§25.3**（原 L687；说"内置 GEEP 库免手备"） | **新增**：**逐页扫描确认 4 处实值**——T21 P16/P17 `USE_GEEP_LIB 9`；T22 P11 `USE_GEEP_LIB 6`；T23 P51 `USE_GEEP_LIB 9`；T23 P65 `USE_GEEP_LIB 6` |
| `ECOUPL` | `official/16_…` L148 用的是 **`E_COUPL`**（COULOMB/NONE/GEEP）；`official/06_properties.md` L146 与 `20_input_reference_tree.md` 把 **`ECOUPL`** 列为缺口关键字；`decide.md` L687 列 **GAUSS/SPLINE/NONE** | **新增 + 纠错**：教材一致用 **`ECOUPL`**（无下划线，**逐页扫描 5 处**：T21 P16/P17、T22 P11、T23 P51/P65），枚举为 **`GAUSS` / `NONE` / `MULTIPOLE`**（**枚举出处唯一：T21 P16/P17**）；**`SPLINE` 在 T21–T23 三份材料里 0 命中**（见 §6） |
| `&PERIODIC`（在 `&QMMM` 下） | `official/20_input_reference_tree.md` L202/L295 **只列段名** | **新增**：T22 P11 `&PERIODIC &MULTIPOLE OFF` 与"**use if XY of MM box =/= QM box**"的用途注释；T23 P65 `&PERIODIC GMAX 0.5` + `&MULTIPOLE` 五个参数 |
| `NOCOMPATIBILITY` / `NOCENTER` / `NOCENTER0` | **全库 0 命中** | **完全新增**（T22 P11） |
| `&MULTIPLE_FORCE_EVALS` 的**减式**（`X+Y-Z`） | `official/24_official_exercises.md` §1.3 给的是**加式** `E1+E2`（DFT+EAM，`&MAPPING &FORCE_EVAL_MIXED &FRAGMENT`）；`18_restarting.md` L647 是 `&MIXED_CDFT`（CDFT）；`20_input_reference_tree.md` L60 只列段名 | **新增**：T23 P14 给 `FORCE_EVAL_ORDER 1 2 3 4` + `MIXING_TYPE GENMIX` + `MIXING_FUNCTION X+Y-Z` + `VARIABLES X Y Z` 的**减式完整四 `&FORCE_EVAL` 结构**（**注意：T23 的减式片段里没有 `&MAPPING`**——`&MAPPING` 只在 G 层 `24_official_exercises.md` §1.3 的加式例子里出现） |
| **球截断 / 多极 / 同格子三档静电方案的代价标度** | **全库 0 命中** | **完全新增**（T23 P17/P18/P19） |
| **GEEP 的加速因子、时间预算（60–80% / 20–40%）、三条误差来源（20–25 点/线方向）** | **全库 0 命中** | **完全新增**（T23 P29/P50/P66/P67） |
| **PBC 下带电 QM/MM 的背景电荷 `±n_B` 与四项能量一致处理** | **全库 0 命中** | **完全新增**（T23 P55–P57） |
| **De-coupling / re-coupling + Bloechl 密度拟合给解耦电荷** | **全库 0 命中** | **完全新增**（T23 P70–P72） |
| **2D 嵌入三型（cluster / island / sandwich）与 "Infinite Sandwich Model"** | `official/16_…` §5 讲的是 `embedding/` 目录下的 **Kim-Gordon / Quantum Embedding**，**不是** 2D sandwich | **完全新增**（T22 P4/P5/P9） |
| **边界势（border potential）的三步处方与 `KZ`/`ClZ` 实现** | **全库 0 命中** | **完全新增**（T22 P18/P19） |
| **电子泄漏（spill-out）的检查手段与"离子材料里问题较小"的经验判断** | 全库仅在 T23 P24/P25 的原始论文语境出现 | **完全新增**（T22 P17 + T23 P24/P25） |
| **QM/MM 里的 MM 高斯抹平同时承担"防溢出"和"修断键"两个角色** | 全库 0 命中 | **完全新增**（T23 P24/P25 原文） |
| **`T21` 的"QM 盒 ≠ 体系盒"三组实测尺寸**（25³ / 6³ vs 15³ / 12.6×15×12.6 vs 12.6×50×12.6） | 全库 0 命中 | **完全新增**（T21 P16、T23 P51、T22 P11–P12） |
| **IC-QM/MM 的"单点用高斯消元、MD/优化用预条件 CG"分工 + 矩阵 T 复用** | `official/16_…` §4.5 只讲 `DETERM_COEFF CALC_MATRIX / ITERATIVE` 的**选择建议**，未讲**为什么** | **新增（机理层）**：T23 P80 给出理由（CG 每次迭代 = 2 次 FFT + N_IC 次数值积分；T 可复用若干步） |
| **IC 的 α > 3.0 Å⁻² 判据、α 太小的物理原因、IC 电荷和不为零的解释** | `official/16_…` §4.5 已含"α > 3.0 Å⁻² 后不依赖 α"（**指针即可**），但**"α 太小 ⇒ 高斯过宽 ⇒ 电荷均匀分布 ⇒ 技术伪影"**的机理与**"IC 电荷和不是物理电荷"**的澄清 | **新增（机理层）**：T23 P83 |
| **水/Pt(111) 与 5 个吸附物-金属体系的定量表（E_int / E_ads / 偶极矩）** | 全库 0 命中 | **完全新增**（T23 P84、P85–P86） |
| **"QM/MM 能省成本"的两条前置判据 + 三步总纲** | 全库 0 命中（`decide.md` L689 给的是"何时用"，措辞不同） | **新增**：T22 P23 |
| **`&ISOLATED_ATOMS` / `&GENERATE` / `FLUSH_SHOULD_FLUSH` / `OPTIMIZER LBFGS` 在 QM/MM 输入里的用法** | `&ISOLATED_ATOMS` 在 `official/20_input_reference_tree.md` 的 `&TOPOLOGY` 子段里可能登记，但**未与 QM/MM 关联** | **新增（组合用法）**：T22 P12 |
| **`&CONSTRAINT &FIXED_ATOMS` 的 `EXCLUDE_MM` / `EXCLUDE_QM`** | 全库 0 命中 | **完全新增**（T22 P12） |
| **`O_SPLINE 6`（`&EWALD` 内）** | 全库 0 命中 | **完全新增**（T23 P12） |

**只写指针（G 层已有，本层不重复）**：
- `E_COUPL COULOMB`（静电嵌入）/ `E_COUPL NONE`（力学嵌入）/ `E_COUPL GEEP` 的**官方定义** → `official/16_qmmm_embedding_ml.md` §2.5
- `&LINK MM_INDEX/QM_INDEX/LINK_TYPE IMOMM` 的**官方示例与切键规则** → 同上 §2.7
- **MM 区残留电荷中和的完整算法与数值**（−0.0362 / 6 个主链原子） → 同上 §2.8
- **AMBER `HO`/`HG` 氢缺 LJ 参数会导致模拟崩溃** → 同上 §2.6
- **IC-QM/MM 的全部输入关键字**（`&IMAGE_CHARGE` / `MM_ATOM_LIST` / `EXT_POTENTIAL` / `WIDTH` / `IMAGE_MATRIX_METHOD` / `DETERM_COEFF` / `RESTART_IMAGE_MATRIX` / `IMAGE_CHARGE_INFO`） → 同上 §4.3–4.7
- **`&MULTIPLE_FORCE_EVALS` + `&MIXED` + `&MAPPING` 的官方加式 NEB 例子**（DFT+EAM，2900 原子 Cu） → `official/24_official_exercises.md` §1.3
- **`&FORCE_EVAL/QMMM` 的子段全清单（12 个）** → `official/20_input_reference_tree.md` L202/L295
- **`RESTART_QMMM` 关键字** → `official/20_input_reference_tree.md` L112（**T21 P27 的 `&EXT_RESTART` 清单里没有它**——教材是 2014 年的）

---

## 6. 与既有层的冲突 / 纠错（带页码证据）

> **裁决原则**（`h_tutorials/README.md` §1）：H 与 A–F 冲突时**先用 G 层裁定**；
> 若属"G 层没写、只有教材讲了"的，以教材原文为准。
> 下面每条都注明**是"真冲突"还是"互补"**。

### 冲突 1（**真冲突 · 关键字拼写**）：`E_COUPL` vs `ECOUPL`

| 层 | 写法 | 位置 |
|---|---|---|
| **G 层** | **`E_COUPL`** | `official/16_qmmm_embedding_ml.md` L148、L150（表格表头） |
| **A 层** | **`E_COUPL`** | `decide.md` **§25.3**（原行号为 L687，本节改写后行号已变，故改引节号） |
| **G 层（缺口登记）** | 把 **`ECOUPL`**（无下划线）列为"应查官方 Input Reference"的缺口关键字 | `official/06_properties.md` L146；`official/20_input_reference_tree.md` 相关段 |
| **H 层（教材）** | **`ECOUPL`**（无下划线），**逐页扫描 5 处，全部一致** | **T21 P16**、**T21 P17**、**T22 P11**、**T23 P51**、**T23 P65** |

**判定**：**这是"G 层自己登记过的缺口"**——`06_properties.md` L146 明确写了"`&QMMM`、`&QM_KIND`、`&MM_KIND`、**`ECOUPL`**…**G 层未抓取该页面**"。
现在 H 层给的是**四页一致的 `ECOUPL`**，而 `16_…` §2.5 的 `E_COUPL` 来自**另一条官方路径**（AM1 教程页）。
**处置建议**：**不要在本轮改 G 层**；在 A 层 `decide.md` **§25.3** 加一句"两种拼写在不同官方页面出现，以手册 `&QMMM` 页为准"，
并**登记为待核**（本笔记 §7 存疑第 1 条）。**H 层照抄 `ECOUPL`，不改成 `E_COUPL`。**

> ✅ **2026-10-06 补记（本条已在 §7 定案）**：`ECOUPL` **不是待核项** ——
> `python _kw_probe.py --find ECOUPL` 查实 **`E_COUPL` 是默认名，`ECOUPL` 与
> `QMMM_COUPLING` 是官方别名**（CP2K 源码 `src/input_cp2k_qmmm.F` 的
> `variants=s2a("QMMM_COUPLING", "ECOUPL")`；手册 `&QMMM` 页亦标 *Aliases*）。
> 两种拼写**都合法**，不是"两个官方页面口径冲突"。H 层照抄 `ECOUPL` 正确；
> 推荐写默认名 `E_COUPL`。

### 冲突 2（**真冲突 · 枚举值**）：`SPLINE` 是否存在

| 层 | 枚举 | 位置 |
|---|---|---|
| **A 层** | **`E_COUPL` 选 …（`GAUSS` GEEP 高斯展开 / **`SPLINE`** / `NONE`）** | `decide.md` **§25.3**（原 L687） |
| **H 层（教材）** | **`ECOUPL GAUSS (or NONE/MULTIPOLE/…)`** | **T21 P16** |

**grep 证据**：`SPLINE` 在 T21/T22/T23 三份材料里：T21 命中 0 次；
T22 命中 0 次；T23 命中 0 次（T23 P12 的 `O_SPLINE 6` 是 `&EWALD` 的关键字，**不是 `ECOUPL` 的枚举值**）。

**判定**：**A 层的 `SPLINE` 在本层 137 页里没有任何佐证**；且经官方 XML 定案，
**`SPLINE` 从来就不是 `E_COUPL` 的合法取值**（`<ENUMERATION strict="yes">`，
五值枚举；跨 2.4/2.6/3.0/6.1/trunk **五个手册版本**核对均无 `SPLINE`）。

> ✅ **2026-10-06 补记（已处置）**：原"处置建议"写的是"改成与教材一致的
> **`GAUSS` / `NONE` / `MULTIPOLE`**" —— ⚠️ **这个建议本身也不对**：
> `MULTIPOLE` **不是** `E_COUPL` 的枚举值（本笔记 §7 第 3 条已证明它是
> `&QMMM/&PERIODIC` 下的**独立子段**；教材 T21 P16 那句括号里把几样东西并列了，
> 不能照抄进枚举）。
> **正确处置（已执行）**：A 层 `decide.md` §25.3 改为**五值枚举表**
> `NONE`（默认，机械耦合）/ `COULOMB`（解析 1/r，**GPW/GAPW 下不可用**）/
> `GAUSS`（GEEP 高斯展开 `Erf(r/rc)/r`）/ `S-WAVE` / `POINT_CHARGE`，
> 删去 `SPLINE` 并附更正记录。**`SPLINE` 是 `&MM/&FORCEFIELD/&SPLINE` 的段名，两回事。**

### 冲突 3（**互补，非冲突**）：`&QMMM &LINK` 的关键字顺序

- G 层 `16_…` §2.7：`MM_INDEX 1411` → `QM_INDEX 1413` → `LINK_TYPE IMOMM`
- H 层 T21 P18：`LINK_TYPE IMOMM` → `QM_INDEX 5` → `MM_INDEX 8`

**判定**：T21 P2 自己说了"**shuffling is allowed, sort them as you like**"，CP2K 的块/关键字顺序本就不敏感。
**不是冲突**，但**落地照抄时应以 G 层顺序为准**（官方页面更新）。

### 冲突 4（**真冲突 · 方法可用性**）：GEEP 是不是"DFT 专属"

| 层 | 说法 |
|---|---|
| **G 层** `16_…` L148 | "**In DFT calculations, the highly efficient GEEP method can be used as well.**" —— 读起来像"GEEP 只在 DFT 里可用" |
| **H 层** | `ECOUPL GAUSS` / `USE_GEEP_LIB` 在教材里**从未被限定为 DFT 专属**（T21 P16 与 `&QS METHOD` 分开列；T23 P51 的 `&DFT` 用 `……` 省略） |

**判定**：G 层那句话是**官方教程里的语境描述**（那篇教程用 AM1，所以说"在 DFT 里也可以用 GEEP"），
不是"GEEP 只支持 DFT"的排他声明。但 **T23 P23–P29 的 GEEP 推导全程假设高斯基 + 平面波网格（即 GPW/DFT 路线）**。
**处置建议**：保留 G 层原话，在 A 层补一句"GEEP 的加速推导基于 GPW 网格（T23 P23–P29），
半经验路线的静电耦合官方教程用 `E_COUPL COULOMB`"。

### 纠错 5：A 层对 `&QMMM` 子段的描述不完整

- `decide.md` **§25.3**（原 L687）只提 `&LINK &IMOMM`，**未提** `&MM_KIND`（`RADIUS` 高斯宽度）、`&PERIODIC`（`GMAX`/`&MULTIPOLE`）、`&CELL`（QM 盒）。
- G 层 `20_input_reference_tree.md` L202/L295 **已给全 12 个子段**（`&CELL`/`&FORCEFIELD`/`&FORCE_MIXING`/`&IMAGE_CHARGE`/`&INTERPOLATOR`/`&LINK`/`&MM_KIND`/`&PERIODIC`/`&PRINT`/`&QM_KIND`/`&WALLS`），**但只有段名**。
- **H 层增量**：给出 `&MM_KIND`（`RADIUS` 实值）、`&PERIODIC`（`GMAX` + `&MULTIPOLE` 五参数）、`&CELL`（三组实测尺寸）的**可用实例**（T21 P16、T22 P11、T23 P51/P65）。

### 纠错 6：**T23 的标题与内容有落差**（必须写下来，否则下游会误引）

T23 标题 = "QM/MM approaches **in ab initio molecular dynamics**"，但：
- 全文**没有**"QM 区如何随时间定义/更新"的任何内容（`&QM_KIND` 三处出现全是静态列表：T23 P51、T21 P16、T22 P11）；
- **"adaptive QM regions" 只在 T23 P8 出现一次，且只是幻灯片标题 + 配图**；
- **"水分子进出 QM 区"零命中**；
- 与"动力学"真正相关的只有：GEEP/PBC 的性能方法学（P25–P66）、IC-QM/MM 的算法分工（P80）、
  以及两个生产应用（SiO₂ 氧空位迁移 + NEB，P73–P79；水/Pt(111) 薄膜 MD，P84–P86）。

**处置建议**：下游若看到"H 层有 86 页 AIMD QM/MM"，**不要**据此断言"自适应缓冲已覆盖"。
若需要"自适应缓冲 QM/MM"，走 **E 层**（`pdf_text/learn_L2.md` L178/L249/L503，第三方课程）并标注来源层。

### 纠错 7：T23 P13/P14 的减式公式**符号与输入不一致**

- P13 公式：`E_total = E_MM,tot + E_QM(QM) − E_MM(QM)`
- P14 输入：`MIXING_FUNCTION X+Y-Z`，注释 `# X: Energy force_eval 2 / # Y: Energy force_eval 3 / # Z: Energy force_eval 4`，
  而第 4 个 `&FORCE_EVAL` 是 `METHOD QS`（**QM**），第 3 个是 `METHOD FIST`（**MM**）。
- ⇒ 输入实现的是 `E_MM,tot + E_MM(QM) − E_QM(QM)`，**与 P13 公式的加减号相反**。

**判定**：P13 是**印在幻灯片上的公式**，P14 是**实际输入**。按"实际输入优先"，
减式在 CP2K 里的实现是 `X(全 MM) + Y(QM 区的 MM) − Z(QM 区的 QM)`。
**这是教材内部的不一致，本笔记按输入为准记录**（T23 P13 vs P14）。

### 纠错 8：T23 P25 的原文声明与 T21 P17 的教材口径**表面矛盾**

- T23 P25（Laino 2005 原文抽页）："**In contrast here, we do not address the issue of treating QM/MM regions crossed by a covalent bond**"
- T21 P17："**If covalent bonds between QM and MM regions -> LINK atoms must be added**"

**判定**：**不是矛盾**——P25 是论文作者说明"GEEP 这篇论文不管断键"，T21 是教你怎么用 `&LINK` 去管。
**但这句话非常重要**：它意味着**用了 GEEP 不等于处理了断键**。下游若把"用了 `ECOUPL GAUSS`"当成"边界已搞定"，
就会踩坑。**这条建议写进 F 层 `playbook.md`。**

---

## 7. 存疑

> 本节 14 条原为"存疑"。本轮**逐条查证**。查证手段（按优先级）：
> **本地官方 `cp2k_input.xml`**（`python _kw_probe.py --find / --section`）→ **重抽源 PDF**
> （`pdfplumber` 按 x 中分栏 + `PyMuPDF` 渲染成图，**只读源 PDF**）→ **官方手册与 CP2K/GitHub 源码（给 URL）**。
> **凡结论推翻原文猜测者，一律附「更正记录」留痕。**

1. **`E_COUPL` vs `ECOUPL` 的真值**
   - ✅ **已定案：`E_COUPL` 是**默认名**，`ECOUPL` 是**官方别名（alias）**；两者都合法**，另有别名 `QMMM_COUPLING`。
   - **依据**：
     · `python _kw_probe.py --find ECOUPL` → `FORCE_EVAL/QMMM`，输出
       `默认名 E_COUPL | 别名 QMMM_COUPLING, ECOUPL`，`DEFAULT_VALUE : NONE`。
     · cp2k_input.xml 原文：`<NAME type="default">E_COUPL</NAME>` + `<NAME type="alias">QMMM_COUPLING</NAME>`
       + `<NAME type="alias">ECOUPL</NAME>`。
     · CP2K 源码 `src/input_cp2k_qmmm.F` 行 95–98：
       `CALL keyword_create(keyword, __LOCATION__, name="E_COUPL", & variants=s2a("QMMM_COUPLING", "ECOUPL"), …)`。
     · 官方手册：<https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/QMMM.html> →
       `E_COUPL` 条目标明 **Aliases: QMMM_COUPLING, ECOUPL**，`Usage: E_COUPL GAUSS`。
   - **⇒ 原"本轮无法裁定…登记为待核"已裁定**：**H 层照抄 `ECOUPL` 不必改**（合法别名），
     **G 层的 `E_COUPL` 是默认名**；A/F 层写哪个都能跑，**推荐写默认名 `E_COUPL`**。

2. **`ECOUPL SPLINE` 是否存在**
   - ✅ **已定案：不存在。`E_COUPL` 的合法取值只有 `NONE` / `COULOMB` / `GAUSS` / `S-WAVE` / `POINT_CHARGE`。**
   - **依据（本层可复现）**：
     · cp2k_input.xml 原文是 **`<ENUMERATION strict="yes">`**（`strict="yes"` ⇒ 枚举外的值不合法），五条 `ITEM`：
       `NONE`（Mechanical coupling）/ `COULOMB`（analytical 1/r，**not available for GPW/GAPW**）/
       `GAUSS`（fast gaussian expansion，GEEP 用的就是它）/ `S-WAVE` / `POINT_CHARGE`（QM-derived point charges）。
     · 源码同一处：`enum_c_vals=s2a("NONE", "COULOMB", "GAUSS", "S-WAVE", "POINT_CHARGE")`。
     · 官方手册同页 **Valid values** 五项，与上完全一致。
   - **跨版本核对（已做）**：CP2K **2.4 / 2.6 / 3.0 / 6.1 / trunk** 五个版本的手册 `&QMMM` 页枚举**完全一致**，
     **都没有 `SPLINE`、也都没有 `MULTIPOLE`**：
     <https://manual.cp2k.org/cp2k-2_4-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html> 、
     <https://manual.cp2k.org/cp2k-2_6-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html> 、
     <https://manual.cp2k.org/cp2k-3_0-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html> 、
     <https://manual.cp2k.org/cp2k-6_1-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html>
   - **更正记录**：A 层 `decide.md` **§25.3**（原 L687）把 `E_COUPL` 的枚举写成 `GAUSS` / **`SPLINE`** / `NONE`
     —— **`SPLINE` 是错的**（2.4→trunk 全无），且**漏了 `COULOMB` / `S-WAVE` / `POINT_CHARGE`**，
     同时把 `MULTIPOLE`（见下条）误当枚举值。**建议改成五值枚举。**
     （原文对 T23 P12 的 `O_SPLINE 6` 属 `&EWALD` 关键字的判断**是对的**，与本条无关。）

3. **`&ECOUPL` 与 `&PERIODIC &MULTIPOLE` 的关系**
   - ✅ **已定案：**不存在 `&ECOUPL` 段**；`MULTIPOLE` **不是** `E_COUPL` 的枚举值，
     `&PERIODIC`（含 `&MULTIPOLE`）是 `&QMMM` 下**独立的子段**，管"QM 周期镜像的解耦"。
     ⇒ **T23 P65 的读法是"叠加"：主方案由 `E_COUPL GAUSS` 定，`&PERIODIC &MULTIPOLE` 是周期修正。**
   - **依据**：
     · `python _kw_probe.py --section FORCE_EVAL/QMMM` 的子段表 =
       `&FORCE_MIXING &QM_KIND &MM_KIND &CELL &PERIODIC &LINK &INTERPOLATOR &FORCEFIELD &WALLS &IMAGE_CHARGE &PRINT`
       —— **没有 `&ECOUPL`**（所以 T21 P16 把 `MULTIPOLE` 与 `NONE` 并列成 `ECOUPL` 的枚举是**注释写混了**）。
     · `python _kw_probe.py --find MULTIPOLE` → **关键字层面 0 命中**；它只作为**段名**出现在
       `FORCE_EVAL/QMMM/PERIODIC/MULTIPOLE`，其子关键字是
       `RCUT`（angstrom）/ `EWALD_PRECISION`（hartree，默认 1e-6）/ `ANALYTICAL_GTERM`（默认 F）/ `NGRIDS`（默认 50³）
       + `&INTERPOLATOR` / `&CHECK_SPLINE` / `&PROGRAM_RUN_INFO`。
     · `FORCE_EVAL/QMMM/PERIODIC` 的官方描述（cp2k_input.xml 原文）：
       "This section is used to set up the **decoupling of QM periodic images with the use of density derived
       atomic point charges**. **Switched on by default even if not explicitly given. Can be switched off if
       e.g. QM and MM box are of the same size.**"
       —— 与 T22 P11 行 163 的注释 `#use if XY of MM box =/= QM box` **逐字对应**。
     · T22 P11 那两行原文（行 159–161）是 `&MULTIPOLE OFF` + `#QM multipole coupling`：**`OFF` 就是"关掉"**，
       正因为该例里 QM 盒与 MM 盒不同才要显式关（默认是开的）。
   - **落地写法**：`E_COUPL GAUSS`（要 GEEP 时）+ 需要时另加 `&PERIODIC / &MULTIPOLE … / &END PERIODIC`；
     **不存在 `E_COUPL MULTIPOLE`**。

4. **T22 P10 的 `&CHARGE` 嵌套写法**
   - ✅ **已定案：是**两栏串行**造成的假象。原文实际是**两个平级的 `&CHARGE` 块、每块一个原子**。**
   - **依据**：按 x 中分重抽源 PDF 第 10 页（`pdfplumber` 逐页 `crop` 左/右半栏），**左栏**完整给出块序：
     `&FORCE_EVAL / METHOD QMMM / &MM / &FORCEFIELD / &CHARGE / ATOM K / CHARGE 1.0 / &END CHARGE /
     &CHARGE / ATOM Cl / CHARGE -1.0 / &END CHARGE / &NONBONDED / …`
     ⇒ **没有外层 `&CHARGE`**，"两层 `&END CHARGE` 夹着两个原子"是文本层把右栏插进左栏造成的。
   - 旁证（官方输入参考）：`python _kw_probe.py --section FORCE_EVAL/MM/FORCEFIELD/CHARGE` → 子关键字只有
     `ATOM`（"Defines the atomic kind of the charge."）与 `CHARGE`（"Defines the charge of the MM atom in
     electron charge unit."）；`&CHARGE` 是 `&FORCEFIELD` 的子段（`--section FORCE_EVAL/MM/FORCEFIELD` 列出
     `&SPLINE &NONBONDED &NONBONDED14 &CHARGE &CHARGES &SHELL &BOND …`）。
   - **更正记录**：笔记 §4.1 照抄的 `&CHARGE` 块序**要按"左右两栏拆开"重读**（本次已按实际嵌套在 §4.1 旁加注）。

5. **`&MM_KIND NA` / `&MM_KIND CL`（大写）vs `&MM_KIND K` / `&MM_KIND Cl`（混合）**
   - ⚠️ **未能确证，已排除以下可能**：
     ① 这**不是**"关键字大小写写错"的问题——`&MM_KIND <元素符号>` 是**带标签的段**，
        段名 `MM_KIND` 与子关键字 `RADIUS`/`CORR_RADIUS` 的匹配与大小写无关
        （`python _kw_probe.py` 本身就是按 `.upper()` 比对才命中这些名字的）；
     ② 这**不是**"某个元素名不合法"——T23 P65 的 `NA`/`CL` 来自体相 NaCl（`ABC 17.3205 Å` 立方 + `&MULTIPOLE`），
        T22 P11 的 `K`/`Cl` 来自 KCl(001)；**两处都是各自体系里正确的元素**。
   - **仍不确定的是**：CP2K 对**段标签里的元素符号**是否做大小写折叠（即 `&MM_KIND CL` 与 `&MM_KIND Cl`
     是否等价）。本轮**没有**找到官方对"section label 匹配是否大小写敏感"的明文，也没有 CP2K 二进制可实测。
   - **要确证需要**：① 官方 Input Reference 关于 section label 匹配规则的说明；或
     ② 用 `CL`/`Cl` 各跑一次最小 QM/MM 输入比对（本机无 CP2K 环境，本层做不到）。
   - **已查到的事实**：两处原文并存（T23 P65 全大写、T22 P11 混合）；`&MM_KIND` 的子关键字是
     `RADIUS`（默认 `0.8` angstrom，注释是 "Width of MM Gaussians"）与 `CORR_RADIUS`。
     **⇒ 落地时统一写元素的标准大小写（`Na`/`Cl`/`K`），不要照抄全大写。**

6. **T23 P36–P43 共 8 页抽取文本为空**
   - ✅ **已定案：不是抽取失败——这 8 页在 PDF 里**根本没有文字对象**（纯图形/动画页）；而且**渲染可读**。**
   - **依据（逐页统计，`PyMuPDF` + `pdfplumber` 双工具）**：
     | 页 | chars | images | lines | rects | curves | contents |
     |---|---|---|---|---|---|---|
     | P36 | 0 | 2 | 0 | 65 | 4 | 5280 B |
     | P37 | 0 | 2 | 0 | 65 | 9 | 6320 B |
     | P38 | 0 | 2 | 0 | 65 | 54 | 21370 B |
     | P39 | 0 | 3 | 0 | 65 | 4 | 5337 B |
     | P40 | 0 | 3 | 0 | 17 | 0 | 2215 B |
     | P41 | 0 | 3 | 0 | 18 | 26 | 10197 B |
     | P42 | 0 | 3 | 0 | 19 | 52 | 18154 B |
     | P43 | 0 | 3 | 0 | 20 | 78 | 26159 B |
     三种抽参（默认 / `x_tolerance=1.5` / `layout=True`）在这 8 页**都返回空串** ⇒ **无文字可抽**，与参数无关。
   - **"这 8 页不是同一页"**：渲染到像素后两两比较，**P40–P43 两两有 25.7% 的像素不同**，
     且 `curves` 数**单调递增 0→26→52→78** ⇒ 是**同一张多格子图逐帧画出来的动画**（P36–P39 是另一组，65 个矩形）。
   - **内容可考（本轮已渲染读出）**：把 **P40 渲染成 PNG 看**，画面 = **4×4 的网格方块** + 右侧一张标题为
     **"Long Range Part"** 的曲线图（x 轴 0–10，y 轴 0–0.5）⇒ 正是 GEEP **多格子（coarse→fine）**那一套。
   - **更正记录**：原文写"（纯动画页）…**无法从文本层获取**。若下游需要，**必须回 PDF**"——
     "无法从文本层获取/必须回 PDF"**对**；但应补两点：① 这 8 页是**两组**（P36–P39 与 P40–P43），
     **不是同一页重复 8 次**；② 它们带 **2–3 张位图 + 17–65 个矢量矩形**，**用 `PyMuPDF` 渲染即可读**，
     不是"不可考"。

7. **T23 P76–P77 只有页眉栏、无内容**
   - ✅ **已定案（并在原文基础上补出图里是什么）**。
   - **依据**：`chars = 57`（就是顶部导航栏 `QMMM:overview / QMMM Schemes / GEEP / Application: cOVD / Conclusion`）、
     `images = 2 / 3`、`lines = 1`、`rects = 1`；渲染后：
     · **P76** = 一整块 **SiO₂ 超胞**（黄 Si / 红 O 线框，`Application: cOVD` 高亮在导航栏里）；
     · **P77** = 上=同一超胞渲染；下=放大到 **QM 团簇嵌在 MM 线框里**（2 个红球 = O、3 个黄球 = Si 高亮）。
   - **⇒ 原文"按上下文应属'带电氧空位'应用的中间结果图"判断正确**；且这两页**渲染可读**，
     不是"不可考"——只是**没有数值/输入**。

8. **T22 P22 "Molecular Dynamics… a quick example!" 只有标题**
   - ✅ **已定案（"本层无货"成立，但"内容不可考"应改写）**。
   - **依据**：该页 `chars = 37`（仅标题一行）、`images = 2`、`lines = 0`；渲染后是一张
     **分子单层膜吸附在离子衬底上的 MD 快照**（青/红/蓝球为有机分子，灰白为衬底晶格，与 T22 正文的
     KCl(001)+CDB 体系一致）。
   - **⇒ 结论**：**图是一张 MD 快照，可渲染查看，但图里没有任何数值、参数或输入卡**。
     原文"若下游要 2D 嵌入的 MD 示例，**本层无货**"**成立**；"内容在图里"应改成"**图是一张无参数的快照**"。

9. **重复页统计**
   - ⚠️→✅ **部分更正：T21 的清单完全正确；T23 的页码清单是错的，数字只是巧合。**
   - **依据（两层判据都做了）**：
     ① **文本层**（按 `PAGE N` 切页 + 去空白归一化后逐页比对）：
        · **T21 有 2 组**：`P7/P8/P22/P24/P26`（5 页，归一化后 415 字符全同）与
          `P9/P10/P13/P15/P19`（5 页，297 字符全同）⇒ **冗余 8 页**，
          **与原文列的 `T21 P7/P8`、`T21 P9/P10`、`T21 P13/P15/P19`、`T21 P22/P24/P26` 完全一致**。
        · **T23 有 8 组**：`P2/P16/P20`、`P30/P31`、`P32/P33/P34/P35`、`P36…P43`（全空）、
          `P45/P46`、`P47/P48/P49`、`P76/P77`、`P78/P79` ⇒ **非空冗余 11 页 + 空页冗余 7 页 = 18 页**。
     ② **像素层**（渲染后逐像素比）：`T21 P7…P26` 那一组两两 **5.5–6.8% 像素**不同、
        `T21 P9…P19` 那一组仅 **0.5–0.6%** 不同 ⇒ 是"**同一张幻灯片同一版式反复出现**（文字全同、图形/高亮不同）"，
        **不是逐字节相同的页**；T23 里**逐字节完全相同**的只有 **`P78/P79`（像素差 0.00%）**，
        而 `P45` vs `P46` 差 **14.3%**、`P47` vs `P48` 差 **2.2%**、`P76` vs `P77` 差 **43.9%**。
   - **更正记录**：原文写"T23 **P25/P26**、**P45–P49**、**P81/P82** 也存在大量重复…统计'有效页数'时应扣除：
     T21 约 **−8 页**，T23 约 **−12 页**"。
     · **`T21` 的 `−8 页` 与它列的四组页号：正确**（本轮实测冗余正好 8 页）。
     · **`T23` 的三组页号：错**——`P25/P26` 与 `P81/P82` **文本不同、像素也不同，不是重复页**；
       `P45–P49` 实际是**两组**（`P45/P46` 与 `P47/P48/P49`）且像素确有差异。
     · `T23` 的真实重复组见上；**`−12 页`这个数字**恰好接近"非空冗余 11 页"，属**巧合**，不是从上述页号得来的。

10. **QM 区该多大 / 该放哪些残基**
    - ⚠️ **未能确证（原文判断成立；本轮补上"查过哪些地方、都缺什么"）。**
    - **已排除以下可能**：
      ① **官方 manual 的 QM/MM 正文页只讲"切在哪"，不讲"切多大"**——
         `methods/qm_mm/builtin.html`（官方 AM1 + 精氨酸教程）给的是
         "cut across the most boring aliphatic C-C bond"、"definitely avoid cutting across heavily polarized
         bonds"（本例切 **Cα–Cβ**）以及"把残基移入 QM 区后 MM 区残留净电荷如何中和"的流程，
         **全篇没有 QM 区尺寸/收敛判据**；
      ② **G 层 `16_qmmm_embedding_ml.md` §2.7 同样只有切键规则**（"切最无聊的脂肪族 C-C 键"），
         属于**切在哪**，不是**切多大**；
      ③ **三份教材（T21/T22/T23）都没有判据**：T22 P23 只给前置条件"Only part of the system contains
         critical interactions!"，T22 P15/P18 给的是**事后验收**（比物理性质、比电子结构、边界力趋零），
         T23 全篇是算法与性能。
    - **仍不确定的是**：**QM 区尺寸的定量判据**——多大才够、要不要做"QM 区尺寸收敛测试"、按什么量判定收敛。
    - **要确证需要**：官方或权威 QM/MM 方法学文献里关于 "QM region size convergence" 的可操作规则
      （本轮在 cp2k.org / manual.cp2k.org 上没有找到）。
    - **已查到的相关事实**：官方给的收敛/健康信号是**边界力趋零**与**电子密度溢出（spill-out）检查**，
      属**事后验收**而非先验尺寸——这一点与 D 层 `playbook.md`/笔记 §3.2、§3.3(b) 的口径一致。

11. **`NOCOMPATIBILITY` / `NOCENTER` / `NOCENTER0` 的含义**
    - ✅ **已定案（含一条重要的版本更正与一条嵌套更正）。**
    - **`NOCOMPATIBILITY`**（`&QMMM` 级，logical，**默认 `F`**）：官方描述原文
      "This keyword **disables the compatibility** of QM/MM potential between **CPMD and CP2K** implementations.
      The compatibility is achieved using an MM potential of the form:
      `Erf[x/rc]/x + (1/rc − 2/(pi^1/2·rc))·Exp[−(x/rc)²]`.
      **This keyword has effect only selecting GAUSS E_COUPLING type.**"
      ⇒ 它是"**关掉** CP2K 与 CPMD 之间的势兼容"（**默认是开的**），**只在 `E_COUPL GAUSS` 下有效**；
      这也解释了 T22 P11 行 149 的注释 `#should be treated as parameters`（该页是 KCl/2D 嵌入的自研势）。
      依据：`python _kw_probe.py FORCE_EVAL/QMMM/NOCOMPATIBILITY`；
      <https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/QMMM.html>。
    - **`NOCENTER` / `NOCENTER0`：教程没错，是**版本**问题。**
      · **trunk 里已不存在**：`python _kw_probe.py --find NOCENTER` / `--find NOCENTER0` **各 0 命中**；
        trunk 手册的 `&QMMM` 关键字表里也没有它们。
      · **但 CP2K 2.4 确实有**，而且在 **`&QMMM` 级**（与 `E_COUPL`/`NOCOMPATIBILITY`/`USE_GEEP_LIB`/`TYP_CENTER` 并列）：
        官方原文（<https://manual.cp2k.org/cp2k-2_4-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html>）：
        - `NOCENTER`（logical，默认 `.FALSE.`）："This keyword disables the automatic centering of the qm
          system every MD step. **It centers the system only for the first step.**"
        - `NOCENTER0`（logical，默认 `.FALSE.`）："This keyword disables the automatic centering of the qm
          system every MD step **even for the first step**."
        - `TYP_CENTER`（关键字，默认 `NONE`，取值 `GRID`/`NONE`）："specifies how the QM system is centered
          with respect to the QM box during MD."（`GRID` = "centering is performed in units of the grid spacing"）
        T22 是 2014 年的片子（CP2K 2.4/2.5 时代）⇒ 用的是这套**旧关键字**。
      · **现代等价写法**（CP2K 2.6 起替换，`--find` 各版本手册已核）：
        `NOCENTER F` + `NOCENTER0 F`（= 每步都居中）= **`CENTER EVERY_STEP`**；
        `NOCENTER T`（= 只首步居中）= **`CENTER SETUP_ONLY`**；
        `NOCENTER0 T`（= 从不居中）= **`CENTER NEVER`**；
        `TYP_CENTER GRID` = **`CENTER_GRID T`**。配套还有 `CENTER_TYPE`
        （enum `MAX_MINUS_MIN` | `PBC_AWARE_MAX_MINUS_MIN`，默认前者）。
    - **更正记录（两处）**：
      ① 原文"直觉上 `NOCENTER`/`NOCENTER0` 与'**高斯中心是否放在 MM 原子位置**'有关，但本层无证据，不做推测"
         —— **直觉方向错了**：它们管的是"**QM 体系是否每步自动居中到 QM 盒里**"（居中算法），
         **与高斯基中心无关**；而且现在**有证据**了（2.4 手册原文见上）。
      ② 笔记 §4.7 把 `NOCENTER F` / `NOCENTER0 F` 排进了 **`&QM_KIND K` 内部**，并特意加了一个 ⚠️ 说明
         "原文是 `NOCENTER F` 在 `MM_INDEX` 之前、`NOCENTER0 F` 在 `MM_INDEX` 之后…此处按原文保留该顺序"
         —— **错**。按 x 中分重抽源 PDF 第 11 页后，这两行与 `ECOUPL GAUSS` / `NOCOMPATIBILITY` /
         `USE_GEEP_LIB 6` **同级缩进**，是 **`&QMMM` 的直接关键字**；2.4 手册的关键字表也把它们列在 `&QMMM` 下。
         **§4.7 已按此更正**（原来那两行是文本层把 `&CELL` 右栏插进 `&QMMM` 左栏造成的假嵌套）。

12. **T23 P2 大纲里的 "GEEP: CP2K QM/MM driver"**
    - ✅ **已定案：**"driver" 是概念说法；输入里**没有独立的 GEEP 段**。**
    - **依据**：
      · `python _kw_probe.py --section FORCE_EVAL/QMMM` 的子段表**没有 `&GEEP`**；
        `python _kw_probe.py --find GEEP` 与 `--find GEEP_LIB` **各 0 命中**。
      · GEEP 的官方全称是 **Gaussian Expansion of the Electrostatic Potential**
        （<https://manual.cp2k.org/trunk/acronyms.html>；G 层 `10_features_resources.md` 已登记同一展开）。
      · 输入里它就是"**一档耦合方式 + 一个整数**"：
        `E_COUPL GAUSS`（别名 `ECOUPL GAUSS`）+ `USE_GEEP_LIB <2..15>`
        （`python _kw_probe.py FORCE_EVAL/QMMM/USE_GEEP_LIB` → 默认 `0`，描述 "enables the use of the internal
        GEEP library to generate the gaussian expansion of the MM potential. Using this keyword there's no need
        to provide the MM_POTENTIAL_FILENAME. It expects a number from 2 to 15"）；
        配套 `MM_POTENTIAL_FILE_NAME`（默认 `MM_POTENTIAL`）、`EPS_MM_RSPACE`（默认 1e-10，
        "affects only the GAUSS E_COUPLING"）、以及网格机器 `&QMMM/&PERIODIC/&INTERPOLATOR`
        （`KIND` 默认 `SPLINE3_NOPBC`、`EPS_X`/`EPS_R` 默认 1e-10、`MAX_ITER` 默认 100）。
    - **⇒ 落地建议**：**不要去找 `&GEEP` 段**；T23 P2 那句"driver"应按"**CP2K 内建的高斯展开库（GEEP library）**"理解。

13. **T21 P18 里原子 5 与原子 8 是否直接成键**
    - ✅ **已定案：**是直接成键**（乙烷的 C5–H8 键），这正是被 `&LINK` 切断并用 H 封端的那根键。**
    - **依据（三条互证）**：
      ① **渲染读图**：把 `Basic Usage of QMMM in CP2K.pdf` 第 18 页的分子图放大渲染后，体系是**乙烷 C₂H₆**；
         图中 **`1` = 左侧碳、`5`（蓝）= 右侧碳、`8`（红）= 右碳上的一个氢**；
      ② **输入自洽**：T21 P18 的 `&QM_KIND C MM_INDEX 1 5` + `&QM_KIND H MM_INDEX 2 3 4 6 7`
         ⇒ QM 集 = {C1, C5, H2, H3, H4, H6, H7}，**`8` 号是唯一的 MM 原子**；
         而 T21 P17 的枚举 `&QM_KIND H MM_INDEX 2 3 4 6 7 8` 表明 **H8 属于 C5 那一组 ⇒ H8 与 C5 相连**；
      ③ **语义自洽**：`&LINK / LINK_TYPE IMOMM / QM_INDEX 5 / MM_INDEX 8` 后紧跟注释 `(H-capping)`
         —— `&LINK` 就是为**跨 QM/MM 边界的共价键**设的（T21 P17 原话："If covalent bonds between QM and
         MM regions -> LINK atoms must be added"），只有 C5–H8 **直接成键**这条读法能让 `&LINK` 有意义。
    - **更正记录**：原文"**`&LINK` 的语义要求两侧原子成键，但这对原子在图里是否相邻，本层无法从文本证实。
      待核（回 PDF 看图）**"——**已回图，证实相邻**；本条由"待核"改为已定案。

14. **`ECOUPL` 的出现次数已逐页核对**
    - ✅ **已定案：原文的"5 处 / `E_COUPL` 0 处"完全正确。**
    - **依据（复扫结果）**：按 `PAGE N` 切页 + 空白归一化 + **词边界正则** `(?<![A-Z_])ECOUPL(?![A-Z_])` 重扫：
      **T21 命中 2 处（P16、P17）**、**T22 命中 1 处（P11）**、**T23 命中 2 处（P51、P65）**，
      **合计 5 处，全部写作 `ECOUPL`**；**`E_COUPL` 在三份材料里 0 命中**。
    - **⚠️ 方法学补充（重要）**：**必须加词边界**。不加词边界、只做"去空白 + 大写 + 子串计数"会得到
      **假阳性**：`Decoupling` / `Recoupling`（T23 P72 行 30 `Decoupling and Recoupling using these charges`）
      与 `MULTIPOLE COUPLING`（T22 P11 行 26 `#QM multipole coupling`）里都含 `ECOUPL` 子串——
      本层第一次扫就因此误得 **T22 = 2 处、T23 = 4 处**（合计 8 处）的错误计数，加词边界后回到 5 处。
    - 原文关于 **PowerShell `Select-String` 扫 `txt/` 会得 `ECOUPL=0` 假阴性**（UTF-8 vs ANSI）的提醒
      **仍然有效**；核验请用 `grep` 工具或 Python 以 UTF-8 读。

---

## 附：本笔记可直接支撑的下游动作

| 下游需要 | 用本笔记的哪几节 |
|---|---|
| 写一份能跑的 QM/MM 输入 | §4.1（MM 半边）、§4.4/§4.5（`&QMMM` 两种）、§4.8（最小 `&QMMM`+`&LINK`）、§4.9（AIMD 骨架） |
| 判断该不该上 QM/MM | §3.1（两条前置判据，T22 P23）+ T23 P5 四问 |
| 判断该用哪档静电耦合 | §3.1（三档代价标度表，T23 P17–P19）+ §5 的 `ECOUPL` 枚举纠错 |
| 排查"嵌入坏了" | §3.2（T22 P15/P17/P18 检查清单）、§3.3(b)（QM 区大小 ↔ spill-out） |
| 2D 表面/薄膜体系 | §4.7（T22 P11–P12 全套）+ §3.2(c)（边界势三步） |
| 减式 QM/MM / 多 `FORCE_EVAL` | §4.3（**本层独有**） |
| 让 QM/MM 动力学跑得动 | §4.10（GEEP 网格层数、误差来源、时间预算） |
| 金属表面吸附（IC-QM/MM） | §5 的指针 → G 层 `16_…` §4；机理与性能 → 本笔记 T23 P80–P86 行 |
| 找"自适应 QM 区 / 水进出 QM 区" | **本层无货** → §6 纠错 6 → E 层 `pdf_text/learn_L2.md` |
