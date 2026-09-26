# H 层精读 04 · CP2K 输入与运行基础（T07 / T08 / T09 / T18）

> **精读范围**（逐页读完，无抽样）：
> - `references/h_tutorials/txt/T07_cp2k_basics.txt` —— 14 页，《Running CP2K Calculations — Basics》
> - `references/h_tutorials/txt/T08_running2018.txt` —— 22 页，《Running CP2K calculations》2018（Iain Bethune）
> - `references/h_tutorials/txt/T09_cp2k3_input.txt` —— 26 页，《CP2K — Basic tutorial to CP2K calculations》（Sébastien Le Roux，`cp2k-3.pdf`）
> - `references/h_tutorials/txt/T18_exercises_all.txt` —— 6 页，《CP2K Exercises — Practical Exercises》
>
> **页码约定**：本文所有 `T** P**` 均指抽取文本里的 `========== PAGE N ==========` 标记，即 **PDF 物理页**。
> T09 是 LaTeX 排版，PDF 页码与文内印刷页码差 6（例：`T09 P11` = 文内 "5"，即 Tab. 1.2 所在页）；引用时两者都给。
>
> **抽取假象提醒**：pdfplumber 对两端对齐排版丢词间空格（如 `Fordetailsseereferences`、`thevariable "MD_STEPS"isdeclared`），
> 本文按语义还原；**不把丢空格当原文错误**。T08 有一页（P17 "Overview of an output file"）在原 PDF 里就是一张**纯截图**，
> 抽取后只剩 `…`，无法据其复原内容——本文不猜。
>
> **与 G 层的分工**：输入语法 8 条规则、`&PRINT`/printkey 四控制项（段参数/`EACH`/`ADD_LAST`/`COMMON_ITERATION_LEVELS`）、
> `FILENAME` 四种写法已由 G 层 `references/official/13_input_syntax_and_print.md` §2–§3 系统整理，
> **本文只写指针，不重复**（见 §5）；本文补的是 G 层没有的**前处理命令（`@SET`/`@INCLUDE`/`@IF`）实操细节、
> 文件级工程组织、可执行文件与命令行、输出文件命名族、以及"照抄级"最小输入**。

---

## 1. 这四份材料各教什么（各一句话）

| 材料 | 一句话 |
|---|---|
| **T07**《CP2K Input Basics》（14 页） | 极简幻灯片：CP2K 四个可执行文件与命令行、输入文件"段套段 + 注释 + 单位"基本语法、`GLOBAL`/`FORCE_EVAL`/`MOTION` 三段骨架、基组/赝势必须匹配、`PRINT_LEVEL`/print-key 控输出、重启（`-i PROJECT-1.restart` + `SCF_GUESS RESTART`）。 |
| **T08**《Running CP2K calculations》2018（22 页） | 与 T07 **同一套幻灯片的加长版**：正文（P3–P18）逐页等价于 T07 并**把 `&DFT`/`&SUBSYS` 的完整输入块和真实文件名写全**（`GTH_BASIS_SETS`/`POTENTIAL`、`TZV2P-GTH`/`GTH-PADE-q6`），后半 P19–P21 是 T07 完全没有的**"怎么造输入"工具链**（vim/emacs 插件、ASE、PyCP2K、Chimera/TETR/LEV00、Avogadro）。 |
| **T09**《CP2K 输入文件》= `cp2k-3.pdf`（26 页） | 一份**完整小册子**（不是幻灯片）：把输入文件当"类命令解释器"讲透——变量 `@SET` 的 3 条指令硬规则、`@INCLUDE` 递归嵌套、`@IF/@ENDIF` 条件段、`&SECTION`/`&END SECTION` 层级与"三段顺序无所谓"，然后给出 `FORCE_EVAL`/`SCF`/`SUBSYS`/`MOTION`（几何优化 / MD / 通用模板）/`EXT_RESTART` 的**逐表输入**，最后第 2 章给出**一套 9 文件的生产级工程组织**与主输入 `System.inp` 全文。 |
| **T18**《官方练习汇总》（6 页） | **确实只是一份练习清单/索引**：6 页里没有任何输入、参数或教学正文，只有 **20 个** `www.cp2k.org` URL（分 Beginners / Intermediate / Extended 三档）＋ 性能基准页链接；对写输入**零直接增量**，价值在于"想练什么 → 去哪一页"。<br>〔更正：原写"16 个"，实测 `T18_exercises_all.txt` 里 URL 共 **20** 个、去重后仍 20，全部指向 cp2k.org；见 §7.2 Q9〕 |

**T07 与 T08 的关系（实测）**：T07 是同一场 material 的**删节版**，14 页内容与 T08 P2–P18 一一对应；
T07 唯一"多出"的信息只有 P10 多点了一句"**separable dual-space** pseudopotentials"（T08 P13 只写 GTH）。

---

## 2. 逐节要点（带页码）

### 2.1 T07（14 页）

| 页 | 要点 |
|---|---|
| P1 | 目录：How to run / Input File / Basic Structure / Method and System / Simulation Protocol / Basis Sets and PPs / Output / Controlling the Output / Output Structure / Restarting。 |
| P2 | **四个可执行文件**：`sopt` 串行、`ssmp` 单进程 + 多处理器（OpenMP）、`popt` 并行（MPI）、`psmp` 并行（MPI）+ 多处理器（OpenMP）。获取途径：官网 download、Linux 发行版包管理、源码（GitHub，含开发版）、`materialscloud.org → WORK → QuantumMobile`、以及**计算中心预装**。 |
| P3 | 命令行：`cp2k.sopt -i input_file -o output_file`；**默认输出到标准输出**；**输出到文件是 append（原文 `Output to file appends (!!)`）**；**不写 `-i` 时最后一个参数就是输入文件**。其他选项：`-version`、`-check input_file`、`-html-manual`、`-help`。 |
| P4 | 一次运行的典型文件：输入（必需，如 `H2O-32.inp`，**文件名与扩展名任意**）；可选输入（默认在 `cp2k/data`）：`POTENTIAL`（赝势库）、`BASIS_SET`（基组库）、结构文件（psf/xyz/crd…）；输出：`PROJECT-1.restart`（可直接拿去续算的输入）、`PROJECT-pos-1.xyz`（MD 或 GEO_OPT 轨迹）、`PROJECT-1.ener`（MD 能量/温度/守恒量）、`PROJECT-1.cell`（晶胞参数）、`PROJECT-RESTART.wfn`（轨道，续算用）。 |
| P5 | 语法骨架：手册 <http://manual.cp2k.org> 或 `-html-manual`；**13 个（可选）顶层段**；`&BEGIN section_name [params]` … `&END [section_name]`；关键字三种形态 `KEYWORD value` / `KEYWORD [ON\|OFF] [YES\|NO] [TRUE\|FALSE] …` / 只写 `KEYWORD`；**段可嵌套段与关键字**。 |
| P6 | 前处理：`@INCLUDE 'filename'` 引入文件文本；`@SET VAR value` 定义变量；`@VAR` 替换为变量值；`@IF / @ENDIF` 简单逻辑；`or #` 作注释。**单位**：数值有默认单位（查手册）；要换单位就**手写** `ABC [nm] 100 100 100`（或 `bohr`，**默认 angstrom**）、`EMAX_SPLINE [eV] 50`（或 `Ry`，**默认 hartree**）；也支持组合如 `[hartree*bohr^-2]`。 |
| P7 | `&GLOBAL`（必需）：`PROJECT H2O-32`、`RUN_TYPE MD`、`PRINT_LEVEL HIGH`、子段 `&TIMINGS / THRESHOLD 0.000001 / &END`、`WALLTIME 3600`，`&END GLOBAL`。 |
| P8 | `&FORCE_EVAL`（必需）：`METHOD QS`（或 FIST、QMMM…）+ `&DFT … &END DFT` + `&SUBSYS … &END SUBSYS`；职责 = **定义"用什么方法"与"什么体系"**（原子坐标与晶胞）。 |
| P9 | `&MOTION`：`&MD / ENSEMBLE NVE / STEPS 10 / TIMESTEP 0.5 / TEMPERATURE 300.0 / &END MD`；用来控制 **MD、几何优化、NEB、Monte Carlo**。 |
| P10 | 赝势/基组：CP2K 用 **separable dual-space** 赝势；库在 `cp2k/data` 或 GitHub；`POTENTIAL`=`GTH_POTENTIALS`（覆盖多元素、按 XC 泛函优化：LDA(PADE)/PBE/BLYP…）；`BASIS_SET`=`GTH_BASIS_SET`、`BASIS_MOLOPT`（收缩高斯，多种质量/大小）；**必须保证基组与赝势匹配（电子数与泛函）**；每个库文件头部有文档与引用。 |
| P11 | 输出控制：`&GLOBAL` 的 `PRINT_LEVEL` ∈ `SILENT / LOW / MEDIUM(默认) / HIGH / DEBUG`；`HIGH` 信息更多、并**在并行作业里产生 per-process 日志**；**长 MD（如经典 MD）建议 `LOW`**；细粒度靠 print-key——**大多数输入段里都有 `&PRINT` 子段**，其下再按物理量分子段。 |
| P12 | 例：`&MOTION` 的 `&PRINT` 内含 `&CELL`、`&FORCES`、`&TRAJECTORY`、`&VELOCITIES`…；每个子段有"从哪个打印级别开始输出"的参数与默认值——**`&TRAJECTORY` 默认 `LOW`，`&VELOCITIES` 默认 `HIGH`**。 |
| P13 | 打印频率用 `&EACH` 子段，例：`&PRINT / &CELL / &EACH / MD 100 / &END EACH / &END CELL / &END PRINT`；**文件名、文件格式等也在各自的 `&PRINT` 段里控制**。 |
| P14 | 重启场景：硬件故障、批处理时限、不收敛、需要更多 MD 采样…；**CP2K 会 dump 一个可直接重跑的 restart 输入文件**：`cp2k.sopt -i PROJECT-1.restart`；**MD 步号连续编号**；**存储所有状态量（含扩展系统）**；用 `SCF_GUESS RESTART`。 |

### 2.2 T08（22 页）

| 页 | 要点 |
|---|---|
| P1–P2 | 作者 Iain Bethune（STFC）；目录比 T07 多两项："**The How – FORCE_EVAL**"、"**The What – MOTION**"（这对命名比 T07 的 Method/System + Simulation Protocol 更好记）。 |
| P3 | 同 T07 P2（四个二进制）。 |
| P4 | 同 T07 P3，但选项写作双横线：`--version`、`--check input_file`、`--html-manual`、`--help`（**注意：T07 写单横线，T08 写双横线，见 §7 存疑**）。 |
| P5 | 同 T07 P4，多一句 `PROJECT-1.cell` 的用途限定："**cell parameters for NPT MD or CELL_OPT**"。 |
| P6 | 同 T07 P5（13 个可选顶层段、`&BEGIN`/`&END`、关键字三形态、可嵌套）。 |
| P7 | 同 T07 P6，但注释写成 **`! or # – comments`**（T07 只写了 `#`）；变量替换写成 **`$VAR`**（**无花括号**）。 |
| P8 | 同 T07 P7（`&GLOBAL` 全文，含 `&TIMINGS/THRESHOLD` 与 `WALLTIME 3600`）。 |
| P9 | 同 T07 P8（`&FORCE_EVAL` 骨架）。 |
| P10 | **`&DFT` 的完整可抄块**（T07 完全没有）：`BASIS_SET_FILE_NAME GTH_BASIS_SETS`、`POTENTIAL_FILE_NAME POTENTIAL`；`&MGRID CUTOFF 280 REL_CUTOFF 30`（注 "Parameters for the realspace multi-grids"）；`&QS EPS_DEFAULT 1.0E-12 / WF_INTERPOLATION PS / EXTRAPOLATION_ORDER 3`；`&SCF SCF_GUESS ATOMIC` + `&OT ON / MINIMIZER DIIS` + `&PRINT / &RESTART OFF`；`&XC / &XC_FUNCTIONAL Pade`（注 "Exchange-Correlation Functional (LDA)"）。 |
| P11 | **`&SUBSYS` 完整块**：`&CELL ABC 9.8528 9.8528 9.8528`（注释 `# 32 H2O (TIP5P,1bar,300K) a = 9.8528`）；`&COORD` 逐原子 `O x y z`，页边注 **"Could also `@include` an external file or parse other formats via `&TOPOLOGY / COORD_FILE_NAME`"**；`&KIND H` / `&KIND O` 各给 `BASIS_SET TZV2P-GTH` + `POTENTIAL GTH-PADE-q1`/`-q6`，页边注 "Definitions of atomic kinds / Could specify charge, mass …"。 |
| P12 | 同 T07 P9（`&MOTION/&MD`），多一句 "Also used to control Geometry Optimisation, NEB, Monte Carlo, …"。 |
| P13 | 基组/赝势：明确 **Goedecker-Teter-Hutter 分离型赝势**；库地址给到 `http://sourceforge.net/p/cp2k/code/HEAD/tree/trunk/cp2k/data`；其余同 T07 P10。 |
| P14–P16 | 输出控制，同 T07 P11–P13。 |
| P17 | "Overview of an output file" —— **原 PDF 是截图**，抽取文本只剩 `…`，不可复原。 |
| P18 | 重启，同 T07 P14。 |
| P19 | **输入工具①编辑器插件**：`https://www.cp2k.org/tools:vim`、`https://www.cp2k.org/tools:emacs`；能力：语法高亮、缩进、**段落的显示/隐藏**、关键字补全。 |
| P20 | **输入工具②Python 接口**：ASE（<https://wiki.fysik.dtu.dk/ase/>，全功能原子模拟环境，体系搭建/分析/可视化，支持含 CP2K 在内的多代码）；PyCP2K（<https://github.com/SINGROUP/pycp2k>，**面向对象封装，结构跟随 CP2K 输入格式**，即 `GLOBAL%RUN_TYPE` ↔ `GLOBAL.Run_type`；支持自动补全；可借 ASE 执行）。 |
| P21 | **输入工具③GUI**：UCSF Chimera 插件（<https://github.com/gpsgibb/tetr_lev00_Chimera_plugin>，菜单驱动 + 可视化；**TETR** 搭几何：超胞/表面/团簇；**LEV00** 分析：电荷/自旋密度、DOS、声子、IR 谱）；Avogadro 1 已支持 CP2K（<https://github.com/brhr-iwao/libavogadro1cp2k>），Avogadro 2 实验性支持（<https://github.com/infuniri/avogadrolibs-cp2k>）。 |
| P22 | "Questions?" |

### 2.3 T09（26 页；文内印刷页码 = PDF 页 − 6）

**前置**：P1 封面（作者 Sébastien Le Roux，IPCMS/Strasbourg，链接 `http://cp2k.berlios.de/`）；
P2/P4/P6/P20/P24 为整页空白图形页；P3 目录；P5 List of Tables（Tab. 1.1–1.12 + Tab. 2.1）；
P25 参考文献（Lippert/Hutter/Parrinello *Mol. Phys.* **92**(3):477–487 (1997)；VandeVondele/Hutter *J. Chem. Phys.* **118**(10):4365–4369 (2003)；Blöchl *Phys. Rev. B* **50**(24):17953–17979 (1994)）；P26 排版说明。

| 页（PDF / 文内） | 要点 |
|---|---|
| P7 / 1 | §1.1 方法总览：CP2K 是 Fortran95 程序，能算 MM/QMMM/QM/MC/MD…，本册**只覆盖第一性原理**（单点、几何优化、尤其 MD）。**FPMD-CP2K 是 Born–Oppenheimer 分子动力学**；DFT 用**混合高斯 + 平面波（GPW）**：波函数用高斯展开，密度在网格上计算（PAW-like）。大体系标度 **O(N²M)**，M=基函数数目，N=分子轨道数。**输入格式是 CPMD-like 的 section 体系** `&SECTION … &END SECTION`；FPMD 输入由 **3 个必需段**组成：`GLOBAL`、`FORCE_EVAL`、`MOTION`；**这三段的出现顺序无关紧要**。 |
| P8 / 2 | §1.2 变量与 include：输入系统是"**命令解释器**"式的，允许定义变量、命令、用 include 文件。变量 `@SET MD_STEPS 5000` 后用 `${MD_STEPS}` 引用；**声明必须且只能由 3 个指令组成：`@SET`、变量名、变量值；该行上任何其它参数都会被当成变量值的一部分** —— 原文反例 `@SET MD_DT 1.5 ! Integration time step in fs => Bad` vs 正例 `@SET MD_DT 1.5 => Good`；并强调"**在 CP2K 输入系统里这是文本变量（即文件名）的通则，所以指定文件名时不要在同一行加注释**"。`@INCLUDE 'file.inc'` 插入文件；**include 文件里还能再有 `@INCLUDE`，所以输入结构会变得相当复杂**。语法可用 **`cp2k -c input.inp`** 测试（原文 `]$ cp2k -c input.inp`），**该命令递归作用于所有 include 文件**。 |
| P9 / 3 | §1.3 `&GLOBAL`：`PROJECT My_system`、`RUN_TYPE My_calculation`、`PRINT_LEVEL MEDIUM`、`WALLTIME My_cpu_time`。逐条：`PROJECT`=工程名；**`RUN_TYPE` 取值：MD（分子动力学）、GEO_OPT（几何优化）、ENERGY_FORCE（单点）**；`PRINT_LEVEL`=输出量，**标准信息用 `LOW`**；**`WALLTIME`=CPU 时间的内部上限（秒），用于干净地结束作业并重启**。再用 `@SET` 变量化：`@SET SYSNAME liquid-Ge2Se3` / `RTYPE MD` / `CPUTIME 36000`，`&GLOBAL` 里写 `${SYSNAME}`/`${RTYPE}`/`${CPUTIME}`——**目的是产出更通用的输入文件**。 |
| P10 / 4 | §1.4 开头 + **Tab. 1.1**（`FORCE_EVAL` 用的变量声明）：`@SET RESTART FALSE`、`BASISFILE`、`PSEUDOFILE`、`WAVEFILE`、`CUTOFF 300`、`GRIDS 5`、`SCF_NCYCLES 500`、`SCF_OCYCLES 100`、`SCF_CONV 1E-6`，以及**条件化**：`@IF ( ${RESTART} == TRUE ) @SET SCF_GUESS RESTART @ENDIF` / `@IF ( ${RESTART} == FALSE ) @SET SCF_GUESS ATOMIC @ENDIF`；`SCF_MINI CG`（SCF 最小化算法：BROYDEN、CG 或 DIIS）、`FUNCTIONAL BLYP`、`OUT_STEPS 1`。前置约定：注释用蓝字（**可保留在输入文件里**＝CP2K 注释）、变量用绿字、include 文件用粗体。 |
| P11 / 5 | **Tab. 1.2** 第一性原理型 `&FORCE_EVAL` 全文：`&PRINT/&FORCES/&END/&END`（打印力）；`METHOD Quickstep`（注：第一性原理计算的方法**总是** Quickstep，即 CP2K 展开波函数所用方法名）；`&DFT` 内 `BASIS_SET_FILE_NAME ${BASISFILE}`、`POTENTIAL_FILE_NAME ${PSEUDOFILE}`、`@IF ( ${RESTART} == TRUE ) WFN_RESTART_FILE_NAME ${WAVEFILE} @ENDIF`；`&MGRID CUTOFF ${CUTOFF} ! => Cutoff of the finest grid level` + `NGRIDS ${GRIDS} ! => Number of multigrids to use, default = 4`；`&QS METHOD GPW ! => This is the default value`、`EPS_DEFAULT 1.0E-12 ! => Default value is 1.0E-10`、`MAP_CONSISTENT TRUE`、`EXTRAPOLATION ASPC ! => Recommend for MD, PS otherwise`、`EXTRAPOLATION_ORDER 3 ! => 4 can be better but increases CPU time`；SCF 与 SUBSYS **用 include 插入**：`@INCLUDE 'scf.inc'`、`@INCLUDE 'subsys.inc'`；`&XC/&XC_FUNCTIONAL ${FUNCTIONAL}/&END XC_FUNCTIONAL/&END XC`。 |
| P12 / 6 | **Tab. 1.3** `scf.inc`：`MAX_SCF ${SCF_NCYCLES}`、`EPS_SCF ${SCF_CONV}`、`SCF_GUESS ${SCF_GUESS}`（初猜：初算 `ATOMIC`，续算 `RESTART`）；`&OT ON / MINIMIZER ${SCF_MINI} / PRECONDITIONER FULL_ALL / ENERGY_GAP 0.001` —— **明确警告：OT 需要 HOMO–LUMO 能隙，因此只对绝缘体有效**；`PRECONDITIONER FULL_ALL` 是"最有效的态选择性预条件，基于对角化"；`ENERGY_GAP`（a.u.）是给 `FULL_ALL` 用的**能隙低估**；`&OUTER_SCF MAX_SCF ${SCF_OCYCLES} / EPS_SCF ${SCF_CONV}` —— 若前 `SCF_NCYCLES` 步没收敛，**可在更新预条件后继续更多圈**（此例 500 × 100 圈）。`&PRINT/&RESTART`：`LOG_PRINT_KEY T`（写重启文件时在屏上提示）、`&EACH QS_SCF 0`（**SCF 循环中从不写重启文件**）/ `MD ${OUT_STEPS}`（每 N 个 MD 步写一次）、`ADD_LAST NUMERIC`。 |
| P13 / 7 | **Tab. 1.4** `subsys.inc`：`&CELL ABC [angstrom] 15.28 15.28 15.28`（模拟盒参数）、`PERIODIC XYZ`；`&TOPOLOGY COORDINATE XYZ`（**注：从 XYZ 文件读坐标时永远是笛卡尔坐标且单位为 angstrom**）、`COORD_FILE_NAME GeSe.xyz`；逐元素 `&KIND Ge/Se` + `BASIS_SET SZV-MOLOPT-SR-GTH`（注：**"非常棘手的段，务必彻底测试以确保用对了基组"**）+ `POTENTIAL GTH-BLYP-q4`/`-q6`（注：**CP2K 赝势有 GTH、ALL、KG 三族；`GTH-BLYP-q4` 这个精确字符串出现在赝势文件里、位于元素名之前**）。§1.5 开头：**只要计算中原子会动，就必须写 `MOTION`**。 |
| P14 / 8 | §1.5.1 几何优化：**Tab. 1.5** 变量（`RTYPE GEO_OPT`、`GEO_MINI CG`、`GEO_MAXS 10000`、`OUT_FORM XYZ`、`OUT_UNIT angstrom`、`OUT_STEPS 1`）；**Tab. 1.6** `&MOTION/&GEO_OPT MINIMIZER ${GEO_MINI} MAX_ITER ${GEO_MAXS}` + `&PRINT` 下 `&RESTART`（`LOG_PRINT_KEY T`、`&EACH GEO_OPT ${OUT_STEPS}`、`ADD_LAST NUMERIC`）与 `&TRAJECTORY`（`LOG_PRINT_KEY T`、**`FORMAT ${OUT_FORM}`、`UNIT ${OUT_UNIT}`**、`&EACH GEO_OPT ${OUT_STEPS}`、`ADD_LAST NUMERIC`）。 |
| P15 / 9 | §1.5.2 MD：**Tab. 1.7** 变量（`RTYPE MD`、`MD_ENS NVT`、`MD_STEPS 10000`、`MD_DT 2.0`、`MD_TEMP 300`、`OUT_FORM XYZ`、`OUT_UNIT angstrom`、`OUT_STEPS 1`）——**`TIMESTEP` 的单位是 fs**。 |
| P16 / 10 | **Tab. 1.8** `&MOTION/&MD`：`ENSEMBLE ${MD_ENS}`、`STEPS`、`TIMESTEP`、`TEMPERATURE`，并用 `@IF ( ${MD_ENS} == NVT )` 包住 `&THERMOSTAT TYPE NOSE / REGION GLOBAL / &NOSE TIMECON 50. / LENGTH 3 / YOSHIDA 3 / MTS 2`；`&PRINT` 下并列 `&RESTART`、`&TRAJECTORY`、`&VELOCITIES` 三个子段，各自 `&EACH MD ${OUT_STEPS}`（**`&VELOCITIES` 必须像 `&TRAJECTORY` 一样显式写，才会每步出速度文件**）。 |
| P17 / 11 | §1.5.3 通用 MOTION：**Tab. 1.9** 把几何优化 + MD + 输出三组变量合并声明。 |
| P18 / 12 | **Tab. 1.10** 通用模板：`&${RTYPE}`（**段名本身用变量！**）+ `@IF ( ${RTYPE} == MD )` … `@ENDIF` / `@IF ( ${RTYPE} == GEO_OPT )` … `@ENDIF` + `&END ${RTYPE}`；`&PRINT` 里 `&EACH ${RTYPE} ${OUT_STEPS}`（**`EACH` 的键也是变量**）；`&VELOCITIES` 只在 MD 分支里出现。 |
| P19 / 13 | §1.6 重启：**Tab. 1.11** 变量（`RTYPE MD`、`RESTART TRUE`、`RESTARTFILE My_restart_file`、`MD_ENS NVT`）；**Tab. 1.12** `&EXT_RESTART ON / RESTART_DEFAULT F / RESTART_FILE_NAME ${RESTARTFILE} / RESTART_POS T / RESTART_COUNTERS T`，条件追加 `RESTART_VEL T`（MD）与 `RESTART_THERMOSTAT T`（NVT）——**注意这里的逻辑值用的是 `T`/`F` 而不是 TRUE/FALSE**。 |
| P21 / 15 | §2.1 **工程组织（9 个文件）**：`System.inp`（主输入，含 `GLOBAL` 与 `EXT_RESTART`）、`forces.inc`（FORCE_EVAL）、`scf.inc`（SCF）、`subsys.inc`（SUBSYS）、`motion.inc`（MOTION）、`restart.inc`（EXT_RESTART）、`system.xyz`（XYZ angstrom 笛卡尔坐标）、`BASIS_SETS`、`PSEUDO_POT`。其中 `system.xyz` 由用户定义，`BASIS_SETS`/`PSEUDO_POT` **随 CP2K 分发**；`forces.inc`/`scf.inc`/`subsys.inc`/`motion.inc`/`restart.inc` **严格等同 Tab. 1.2 / 1.3 / 1.4 / 1.10 / 1.12**。**主输入文件集中放全部变量定义 + 两个小段（GLOBAL、EXT_RESTART）**。 |
| P22–P23 / 16–17 | §2.2 **Tab. 2.1 `System.inp` 全文**：先是 6 组 `@SET`（General / Files / DFT / Geometry optimization / MD / Output，共 ~30 个变量，含 `@SET BASISFILE BASIS_SETS`、`@SET PSEUDOFILE PSEUDO_POT`）；然后 `&GLOBAL PROJECT ${SYSNAME} / RUN_TYPE ${RTYPE} / PRINT_LEVEL MEDIUM / WALLTIME ${CPUTIME} / &END GLOBAL`；然后按顺序 `@IF ( ${RESTART} == TRUE ) @INCLUDE 'restart.inc' @ENDIF`、`@INCLUDE 'forces.inc'`、`@IF ( ${RTYPE} /= ENERGY_FORCE ) @INCLUDE 'motion.inc' @ENDIF`。**即：单点计算（`ENERGY_FORCE`）不需要 MOTION；`EXT_RESTART` 只在续算时需要。** 末句："还有很多关键字可用于高级参数化，详见 CP2K 用户手册"。 |
| P25 / 19 | 参考文献（见上"前置"）。 |

### 2.4 T18（6 页）——确实是练习清单

| 页 | 内容（**只有链接，无正文**） |
|---|---|
| P1 | 练习都在网上：<https://www.cp2k.org/events:2019_cp2k_workshop_ghent:index>；按兴趣选范围。 |
| P2 | **Beginner 'HowTo'**：单点能量与力（<https://www.cp2k.org/howto:static_calculation>）；**CUTOFF / REL_CUTOFF 收敛**（`/howto:converging_cutoff`、`/events:2018_summer_school:converging_cutoff`）；**玩 SCF 设置**（`/events:2018_summer_school:scf_setup`）；几何优化（`/howto:geometry_optimisation`）。 |
| P3 | **Intermediate**：NaCl 团簇的几何与晶胞优化（2016 summer school `geometry_and_cell_optimization`）；局域泛函表面科学（`exercises:2016_summer_school:gga`）；**液态水 AIMD**（`…:aimd`）；杂化泛函与色散校正（`…:hfx`）。 |
| P4 | **Intermediate（续）**：线性标度 DFT（`exercises:2015_pitt:ls`）；电子相关 MP2 与 RPA（`…:mp2`）；**用 GEEP 做 QM/MM**（`exercises:2016_summer_school:qmmm`）；激发态（`…:excited`）。 |
| P5 | **Extended**：元动力学（`exercises:2015_cecam_tutorial:mtd1`）；水中尿素的 QM/MM（`…:urea`）；金属表面吸附 NEB（`…:neb`）；蛋白质力场（`…:forcefields`）；`VIBRATIONAL_ANALYSIS`、NMR、X-Ray、DFT+U（`www.cp2k.org/`）。 |
| P6 | **Scaling / 性能测试**：基准体系在 <https://www.cp2k.org/performance>；建议实验：体系尺寸与精度参数对性能的影响；性能"tweaks"要**问专家**。 |

> **T18 的用法**：它是一张**主题 → URL 路由表**。G 层 `24_official_exercises.md`（248 页官方练习集逐页采集）已经把这些页的正文收进去了，所以本文对 T18 只做**索引登记**，不复述任何练习内容。

---

## 3. 核心逻辑链（重点）

### 3.1 CP2K 输入文件的组织逻辑

**为什么是"段套段"？——因为整个输入系统被设计成一个"命令解释器"。**
T09 P8 原话把这一点说得很直白：`The CP2K input system is "command interpreter"-like system, thus it allows to define variables, commands and use include files.`
推论是：输入文件是**给解释器顺序执行的一串指令**，其中 `&NAME` 是"进入名为 NAME 的节点"，`&END [NAME]` 是"离开当前节点"。
所以它天生是**树**而不是表。

**① 层级：`&` 是入栈，`&END` 是出栈。**

- 顶层段（T07 P5 / T08 P6：**13 个可选顶层段**）——一次计算只用其中几个；`GLOBAL`、`FORCE_EVAL`、`MOTION` 是最常用的三个（T09 P7 称 FPMD 计算的"**3 个必需段**"）。
- 段内可以**同时**放关键字和子段（T07 P5 "Sections may contain others sections and keywords"；T08 P6 同）。
  例：`&FORCE_EVAL` 里既有 `METHOD Quickstep`（关键字）又有 `&DFT` / `&SUBSYS`（子段）——T08 P9。
- **`&END` 后面的段名可写可不写**（T07 P5 / T08 P6 的语法写的是 `&END [section_name]`，方括号＝可选）。
  T07 P7 的 `&GLOBAL` 示例里 `&TIMINGS` 只写 `&END`，而 `&GLOBAL` 写 `&END GLOBAL` —— 同一份材料里两种写法混用，证明两者都合法。
  **工程建议（H 层归纳）**：多层嵌套时**始终写 `&END 段名`**，否则漏一个 `&END` 极难定位；这正是 T08 P19 推荐编辑器插件的原因——插件能"show/hide sections"，配对错了一眼可见。
- **段的最高层不缩进也合法**，缩进纯属可读性；T09 的全部表格、T08 P10–P11 都用缩进表达层级。

**② 关键字与段同名时怎么区分？——看行首有没有 `&`。**

这是"命令解释器"设计带来的唯一歧义点，材料里给出了判据（T07 P5 + T08 P10 的实际用法）：

| 写法 | 语义 |
|---|---|
| `&SCF` / `&MGRID` / `&OT` / `&PRINT` | **进入段**（入栈），后面直到匹配 `&END` 的内容都属于它 |
| `SCF_GUESS ATOMIC` / `CUTOFF 280` / `MINIMIZER DIIS` | **关键字赋值**（当前栈顶段的属性） |

真正的同名冲突发生在 `&OT ON` 这种写法上：`OT` 既是段名，又带一个默认参数（T08 P10 写 `&OT ON`，T09 P12 写 `&OT ON`），
这里的 `ON` **不是关键字而是段参数**。G 层 `13_input_syntax_and_print.md` §2.1 已把段默认参数（`&OT`＝开、`&OT FALSE`＝关＝不写该段）讲透，**此处只给指针**。
**正确的心智模型**：`&X [param]` = 打开节点 X 并顺手把它的"总开关"设成 param；`&X` 不带 param = 用该段的默认参数。

**③ 顺序自由，但语义耦合。**

- `GLOBAL` / `FORCE_EVAL` / `MOTION` **出现顺序无所谓**（T09 P7 明确：`The order of appearance of these sections does not matter.`）。
- 但**关键字之间会互相牵制**，这才是真正的约束：
  - `&GLOBAL/RUN_TYPE` 与 `&MOTION` 的子段必须对上——`RUN_TYPE MD` 要有 `&MOTION/&MD`，`RUN_TYPE GEO_OPT` 要有 `&MOTION/&GEO_OPT`（T07 P7+P9、T08 P8+P12 的例子就是配对的）。
  - **单点计算不需要 MOTION**：T09 Tab. 2.1（P23）用 `@IF ( ${RTYPE} /= ENERGY_FORCE ) @INCLUDE 'motion.inc' @ENDIF` 把这一点写成了条件。
  - `FORCE_EVAL` 内部：`METHOD` 决定下面该有哪个子段（`Quickstep`→`&DFT`，`FIST`→`&MM`，`QMMM`→`&QMMM`）——T07 P8 / T08 P9 的 `METHOD QS (or FIST, QMMM …)`。
  - `&KIND` 的 `BASIS_SET`/`POTENTIAL` 必须与 `&DFT` 里 load 的库文件匹配（见 §3.2 的第 4 块）。
- **变量让"顺序自由"变得有用**：T09 P9 用 `@SET RTYPE MD` + `RUN_TYPE ${RTYPE}`，改一行就整体换计算类型；T09 Tab. 1.10（P18）甚至把**段名**写成 `&${RTYPE}`、把 **`&EACH` 的键**也写成 `${RTYPE}`。

**④ 单位怎么写？——"关键字 值"的中间插一个方括号。**

T07 P6 / T08 P7 给的规则是：

```
ABC [nm] 100 100 100          # 或 bohr；默认 angstrom
EMAX_SPLINE [eV] 50           # 或 Ry；默认 hartree
                              # 组合单位：[hartree*bohr^-2]
```

三层含义：
1. **每个数值都有默认单位**，查手册（`Numerical entries have a default unit (see manual)`）。所以**不写单位也能跑**，但你必须知道它默认是什么。
2. **想换单位就在值和关键字之间手写 `[unit]`**——位置是**紧跟关键字、在数值之前**。
3. **组合单位用 `*` 和 `^-n` 拼**，如 `[hartree*bohr^-2]`。

材料里出现的默认单位锚点（可直接当速查表）：

| 量 | 出现位置 | 默认单位 | 显式写法示例 |
|---|---|---|---|
| 晶胞参数 | T07 P6 / T08 P7 | **angstrom**（可 `bohr`、`nm`） | `ABC [nm] 100 100 100`；T09 Tab. 1.4 写 `ABC [angstrom] 15.28 15.28 15.28` |
| `EMAX_SPLINE` | T07 P6 / T08 P7 | **hartree**（可 `eV`、`Ry`） | `EMAX_SPLINE [eV] 50` |
| XYZ 坐标 | T09 Tab. 1.4（P13） | **angstrom、笛卡尔**（原文：从 XYZ 读坐标"永远是笛卡尔且 angstrom"） | — |
| MD 时间步 | T09 Tab. 1.7（P15） | **fs** | — |
| `WALLTIME` | T09 §1.3（P9） | **秒** | — |
| 能量间隙 `ENERGY_GAP` | T09 Tab. 1.3（P12） | **a.u.** | — |

> 方括号内不能有空格、`#`/`!` 都是注释符、长短写大小写不敏感 —— 这些由 G 层 `13_input_syntax_and_print.md` §2 的官方 8 条规则覆盖，**本文不重复**；本节只补"默认单位是什么"和"组合单位怎么写"。

**⑤ 注释怎么写？——三种，且有一条"陷阱式"限制。**

| 写法 | 出处 | 说明 |
|---|---|---|
| `# 注释到行尾` | T07 P6；T08 P11 示例（`# 32 H2O (TIP5P,1bar,300K) a = 9.8528`） | 与 G 层官方一致 |
| `! 注释到行尾` | T08 P7（`! or # – comments`）；T09 全篇表格都用 `!` | 与 G 层官方一致 |
| 段名后/关键字后**行内**注释 | T09 Tab. 1.4（`&KIND Ge ! => For each species we create a KIND section`）、T08 P10 | 合法，常用 |

**陷阱（T09 P8 明确）**：`@SET` 所在行**没有注释**。
`@SET MD_DT 1.5 ! Integration time step in fs` 会让变量值变成 `1.5 ! Integration time step in fs`。
原文并且把这条上升为通则：**"在 CP2K 输入系统里这是文本变量的通则，即文件名——指定文件名时不要在同一行加注释"**。
→ 实操含义：`BASIS_SET_FILE_NAME BASIS_MOLOPT  # 基组库` 这种写法**可能被当成文件名的一部分**。**别在文件名行写注释。**

### 3.2 一次计算的最短闭环：从"我要算什么"到"能跑的 .inp"

把四份材料拼起来，最短闭环是 **6 块**。每块都给"最小充分设置"（低于这个就跑不起来或跑出来没意义）。

```
① 我要算什么      → &GLOBAL/RUN_TYPE                      （T07 P7, T09 P9）
② 输出叫什么      → &GLOBAL/PROJECT                        （T07 P7, T09 P9）
③ 体系长什么样    → &FORCE_EVAL/&SUBSYS/&CELL + &COORD + &KIND
                                                          （T08 P11, T09 P13）
④ 用什么方法算    → &FORCE_EVAL/METHOD Quickstep
                     └ &DFT: BASIS_SET_FILE_NAME + POTENTIAL_FILE_NAME
                              + &MGRID(CUTOFF, REL_CUTOFF) + &QS + &SCF + &XC
                                                          （T08 P10, T09 P11–P12）
⑤ 原子动不动      → &MOTION（不动就不写）                   （T07 P9, T09 P23）
⑥ 跑完怎么接着跑  → &GLOBAL/WALLTIME + &PRINT/&RESTART      （T09 P9, P12, P16）
```

逐块的最小充分设置：

| # | 块 | 最小充分设置 | 依据 |
|---|---|---|---|
| ① | 运行类型 | `RUN_TYPE` ∈ {`ENERGY_FORCE` 单点, `GEO_OPT` 优化, `MD` 动力学}（T09 只列这三个；现代版还有 `ENERGY`）。**`RUN_TYPE` 决定后面要不要写 `&MOTION`** | T09 P9 三条 + Tab. 2.1 P23 |
| ② | 工程名 | `PROJECT <名字>`：**所有自动生成文件的共同前缀**；续算必须沿用同一名字 | T07 P7 / T09 P9 / G 层 `01` |
| ③ | 体系 | `&SUBSYS` 下 **必须有** `&CELL`（或 `&TOPOLOGY`）**和** `&COORD`，**每个元素一个 `&KIND`**；`&KIND` 至少要 `BASIS_SET` + `POTENTIAL`（`ELEMENT` 可选，T09 P13 只用段名区分元素） | T08 P11, T09 P13 |
| ④ | 方法 | `METHOD Quickstep`（DFT 只有它）→ `&DFT`：**两个库文件名**（`BASIS_SET_FILE_NAME`、`POTENTIAL_FILE_NAME`）+ `&MGRID CUTOFF/REL_CUTOFF` + `&XC/&XC_FUNCTIONAL` + `&SCF`（`SCF_GUESS` + `EPS_SCF` + `MAX_SCF`） | T08 P10, T09 P11–P12 |
| ⑤ | 原子动不动 | 不动 → **整个 `&MOTION` 不写**；动 → `&MOTION/&MD ENSEMBLE+STEPS+TIMESTEP+TEMPERATURE` 或 `&MOTION/&GEO_OPT MINIMIZER+MAX_ITER` | T09 Tab. 1.6/1.8/2.1 |
| ⑥ | 可续算性 | `&GLOBAL WALLTIME <秒>`（**内部时限→干净结束并写出 restart**）+ `&MOTION/&PRINT/&RESTART`（`LOG_PRINT_KEY T` + `&EACH MD n`），并在重跑时设 `SCF_GUESS RESTART` | T09 P9 / P12 / P16 / P19，T07 P14 |

**④ 里最容易错的一环：基组与赝势的"三重匹配"**（这是材料反复强调、且 skill 最容易踩的地方）：

1. **名称字符串要能对上库文件里的条目**：T09 P13 注明 `GTH-BLYP-q4` 这个"精确字符串"**出现在赝势文件里、位于元素名之前**；若写成 `GTH-PADE-q4` 就得去 PADE 那一段找。
2. **泛函要一致**：库里的赝势是**按 XC 泛函分别优化**的（LDA(PADE) / PBE / BLYP…）——T07 P10 / T08 P13。用 PBE 泛函却配 `GTH-PADE-*` 是典型的"能跑但没意义"。
3. **电子数要一致**：`-q6` 是 6 价电子（T08 P11 的 O 用 `GTH-PADE-q6`、H 用 `-q1`；T09 P13 的 Ge/Se 用 `-q4`/`-q6`）。基组与赝势的价电子数必须对上。
4. **基组族要与库文件对应**：`DZVP-GTH-PADE` 活在 `BASIS_SET` 里，`DZVP-MOLOPT-GTH`/`SZV-MOLOPT-SR-GTH` 活在 `BASIS_MOLOPT` 里（T08 P10/P11/P13 用前者，T09 P13 用后者）。**load 了哪个库，就只能选那个库里的名字。**
5. **文档就在文件头上**：T07 P10 / T08 P13 都说"每个库文件开头有说明和参考文献"——不确定时直接打开 `cp2k/data/BASIS_MOLOPT` 看注释。

**⑤ 的一个语法要点**：`&MOTION` 写成 `&MD`/`&GEO_OPT` 的子段形式，**不是**顶层 `&MD`。T07 P9 / T08 P12 都是 `&MOTION / &MD … &END MD / &END MOTION`。

**⑥ 的一个顺序要点**：`&PRINT` 挂在**它所属的那个段**下面——控制 MD 轨迹/速度/重启的 `&PRINT` 在 `&MOTION` 下（T09 Tab. 1.8 P16）；控制 SCF 重启的 `&PRINT` 在 `&SCF` 下（T09 Tab. 1.3 P12）。**两者不是同一个 `&PRINT`。**

### 3.3 运行方式：串行/并行、重定向、`PROJECT` 与输出文件名

**① 四个二进制 = 两种并行的四种组合**（T07 P2 / T08 P3）：

| 二进制 | 并行方式 | 什么时候用 |
|---|---|---|
| `cp2k.sopt` | 串行（optimised） | 单核；小体系；调试/教学 |
| `cp2k.ssmp` | 单进程 + 对称多处理（OpenMP） | 单节点多核、不想起 MPI |
| `cp2k.popt` | 并行（MPI，optimised） | **集群常规选择**（skill 的 `run.md` 也这么定） |
| `cp2k.psmp` | MPI + OpenMP | 混合并行；内存吃紧时（skill `course_learned.md` §多核对比） |

> ⚠️ 版本差：现代 CP2K（G 层 `01_global_and_units.md` §，及官网 first-calculation 页）的**发布版命名是 `psmp / pdbg / ssmp / sdbg`**，`sopt/popt` 属于旧命名。**用 `ls exe/*/` 确认你手上到底有哪几个**，别照抄文件名。

**② 三种起法**（材料原文，照抄）：

```bash
# 串行 / 单进程，显式指定输入输出（T07 P3 / T08 P4 / T09 P8）
cp2k.sopt -i input_file -o output_file

# 输入文件作为最后一个参数（T07 P3 / T08 P4：Input file is the last argument）
cp2k.sopt input_file

# 续算：restart 文件本身就是一份完整输入（T07 P14 / T08 P18）
cp2k.sopt -i PROJECT-1.restart

# 语法自检（T09 P8）：递归检查所有 @INCLUDE
cp2k -c input.inp
```

> 并行启动的完整写法（`mpirun -n N cp2k.popt …`）在 T07/T08/T09 这三份材料里**没有给**；
> skill 的 `references/run.md` 与 G 层 `08_errors_and_faq.md` §已有（`mpirun -np N -x OMP_NUM_THREADS=1 cp2k.psmp -i p.inp -o p.out`）。**本处只给指针。**

**③ 输出重定向——三层，别搞混**：

| 方式 | 行为 | 出处 |
|---|---|---|
| 不写 `-o` | 输出**到标准输出**（屏幕上） | T07 P3 / T08 P4（`By default, output goes to the standard output`） |
| 写 `-o output_file` | 输出**写到文件**；原文警告 **`Output to file appends (!!)`（是追加，不是覆盖）** | T07 P3 / T08 P4 |
| shell 重定向 `1> cp2k.out 2> cp2k.err` | 把 stdout/stderr 分开 | 不在本四份材料内；见 skill `run.md` / G 层 `08_errors_and_faq.md` |

> **"appends" 这一条要当真**（本文把它标为**待复核**，见 §7）：如果属实，重复提交同一个作业会把两次输出堆在同一个 `.out` 里，
> 后续 `grep PROGRAM ENDED` / `parse_output.py` 会读到旧结果。**保守做法：提交前删掉或改名旧 `.out`**，或者干脆用 `1> cp2k.out`（shell 重定向默认截断）。

**④ `PROJECT` 决定文件名——命名规律**（T07 P4 / T08 P5）：

一次运行产生的文件名族 = **`PROJECT` + 后缀 + 编号 + 扩展名**：

| 文件 | 内容 | 出处 |
|---|---|---|
| `PROJECT-1.restart` | **可直接重跑的输入文件**（含坐标、速度、计数器、扩展系统状态） | T07 P4/P14，T08 P5/P18 |
| `PROJECT-pos-1.xyz` | MD 或 GEO_OPT 的**轨迹** | T07 P4，T08 P5 |
| `PROJECT-1.ener` | MD 的**能量、温度、守恒量（cons. Q）** | T07 P4，T08 P5 |
| `PROJECT-1.cell` | **晶胞参数**（NPT MD 或 CELL_OPT 才有意义） | T07 P4，T08 P5（明确限定） |
| `PROJECT-RESTART.wfn` | **轨道**（续算用；注意这个**没有 `-1`**） | T07 P4，T08 P5 |

**推论（H 层归纳）**：
- 文件名里的 `-1` 是**运行序号**：`-i PROJECT-1.restart` 重跑后会产生 `PROJECT-2.*`——这就是 T07 P14 说的 "**Continuous numbering of MD steps**" 的来源与用途。
- **`PROJECT-1.restart` 与 `PROJECT-RESTART.wfn` 是两种不同粒度的续算**：前者恢复**整个运行状态**（T07 P14："Stores all state variables (incl. extended system)"），后者只提供**波函数初猜**（T07 P4，配合 `SCF_GUESS RESTART`）。
- 因为文件名由 `PROJECT` 派生，**同一目录下不同作业务必用不同 `PROJECT`**，否则文件互相覆盖；反之，**续算必须保持 `PROJECT` 不变**（G 层 `07_restarting.md` §4.4 的官方硬约束与此一致）。

**⑤ 输出信息的"总闸"与"分闸"**（T07 P11–P13 / T08 P14–P16）：

- **总闸**：`&GLOBAL/PRINT_LEVEL` ∈ `SILENT / LOW / MEDIUM(默认) / HIGH / DEBUG`。
  - `HIGH` 信息更多，且**在并行作业里产生 per-process 日志**（进程一多，日志量爆炸）。
  - **长 MD（尤其经典 MD）建议 `LOW`**。
- **分闸**：**大多数段内都有 `&PRINT`**，其下逐物理量分子段（`&CELL` / `&FORCES` / `&TRAJECTORY` / `&VELOCITIES` …）。
  - **每个子段自带"从哪个打印级别开始输出"的默认值**：`&TRAJECTORY` 默认 `LOW`，`&VELOCITIES` 默认 `HIGH`。
    → 所以 **`PRINT_LEVEL MEDIUM` 时轨迹会写、速度不会写**；要速度就得把 `&PRINT_LEVEL` 提到 `HIGH`，或显式写 `&VELOCITIES`。
  - **频率**用 `&EACH`：`&PRINT / &CELL / &EACH / MD 100 / &END EACH / &END CELL`。
  - **文件名与格式**也在各自 `&PRINT` 段里控制（G 层 `13` §3.2 有 `FILENAME` 四种写法的官方细则，此处只给指针）。

---

## 4. 可执行要点（照抄）

### 4.1 最小可运行输入（完全照抄材料，仅拼接）

材料本身把输入拆在 T07 P7/P8/P9 与 T08 P8/P10/P11/P12 多页；下例是**按下标出处逐行拼接的完整文件**。
坐标部分：**T08 P11 原文只印了 5 行坐标 + `...`**（3 行 `O` 逐字照抄，另两行 `O`/3 行 `H` 中 `H` 三行是**按该页示意补的占位**）——
**要真跑请换成完整 32 个水分子的坐标**（32 × 3 = 96 行）。

```none
&GLOBAL                              ! T07 P7 / T08 P8
  PROJECT H2O-32
  RUN_TYPE MD
  PRINT_LEVEL HIGH
  &TIMINGS
    THRESHOLD 0.000001
  &END
  WALLTIME 3600
&END GLOBAL

&FORCE_EVAL                          ! T08 P9
  METHOD QS                          ! T07 P8: METHOD QS (or FIST, QMMM ...)
  &DFT                               ! T08 P10
    BASIS_SET_FILE_NAME GTH_BASIS_SETS
    POTENTIAL_FILE_NAME POTENTIAL
    &MGRID
      CUTOFF 280                     ! Parameters for the realspace multi-grids
      REL_CUTOFF 30
    &END MGRID
    &QS
      EPS_DEFAULT 1.0E-12
      WF_INTERPOLATION PS
      EXTRAPOLATION_ORDER 3
    &END QS
    &SCF                             ! Control of SCF procedure
      SCF_GUESS ATOMIC
      &OT ON
        MINIMIZER DIIS
      &END OT
      &PRINT
        &RESTART OFF
        &END
      &END
    &END SCF
    &XC                              ! Exchange-Correlation Functional (LDA)
      &XC_FUNCTIONAL Pade
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS                            ! T08 P11
    &CELL
      ABC 9.8528 9.8528 9.8528       ! # 32 H2O (TIP5P,1bar,300K) a = 9.8528
    &END CELL
    &COORD                           ! 仅示例：完整 32 个水分子请自行补齐
      O 2.280398 9.146539 5.088696
      O 1.251703 2.406261 7.769908
      O 1.596302 6.920128 0.656695
      H 0.837635 8.186808 8.987268
      H 8.314696 10.115534 2.212519
      H 8.687134 8.667252 2.448452
    &END COORD
    &KIND H
      BASIS_SET TZV2P-GTH
      POTENTIAL GTH-PADE-q1
    &END KIND
    &KIND O
      BASIS_SET TZV2P-GTH
      POTENTIAL GTH-PADE-q6
    &END KIND
  &END SUBSYS
&END FORCE_EVAL

&MOTION                              ! T07 P9 / T08 P12
  &MD
    ENSEMBLE NVE
    STEPS 10
    TIMESTEP 0.5
    TEMPERATURE 300.0
  &END MD
&END MOTION
```

> 说明：`&END` 后面留空（`&TIMINGS`、内层 `&PRINT`）是 T07 P7 的原文写法；`&END GLOBAL`、`&END DFT`、`&END SUBSYS` 等带段名也是原文写法。两种都合法（§3.1 ①）。
> **实跑 `validate_inp.py` 的结果（本轮已验证，2 个警告、0 个错误、exit 0）**：
> ```
> [warn] L5: unknown section '&TIMINGS' (possible typo? known: MIXING, KPOINTS, KIND)
> [warn] L12: METHOD 'QS' not a known value
> RESULT: OK (2 warning(s))
> ```
> → 两条都不是教材的错，而是 skill 侧的覆盖面问题：①`&GLOBAL/TIMINGS` 是**官方段**（G 层 `20_input_reference_tree.md` §2 有 `&GLOBAL/TIMINGS`），只是不在 `validate_inp.py` 的 `KNOWN_SECTIONS` 白名单里；②`METHOD QS` 是 T07 P8 的原文写法（`METHOD QS (or FIST, QMMM …)`），`Quickstep` 的合法缩写，但 `VALID_METHODS` 只收了全称（`validate_inp.py:107`）。**这两条值得作为独立小修**（加白名单项 + 加别名）。

### 4.2 命令行照抄

```bash
# ← T07 P3 / T08 P4 / T09 P8（原文逐字）
cp2k.sopt -i input_file -o output_file
cp2k.sopt -version
cp2k.sopt -check input_file
cp2k.sopt -html-manual
cp2k.sopt -help

# ← T09 P8：语法自检（递归检查 include）
cp2k -c input.inp

# ← T07 P14 / T08 P18：直接从 restart 文件续算
cp2k.sopt -i PROJECT-1.restart
```

### 4.3 T09 的"生产级工程组织"（9 文件，照抄 Tab. 2.1 骨架）

```
System.inp      主输入：全部 @SET 变量 + &GLOBAL + (续算时) EXT_RESTART
forces.inc      @INCLUDE 进来：&FORCE_EVAL ...
scf.inc         @INCLUDE 进来：&SCF ...（嵌在 FORCE_EVAL/&DFT 里）
subsys.inc      @INCLUDE 进来：&SUBSYS ...（嵌在 FORCE_EVAL 里）
motion.inc      @INCLUDE 进来：&MOTION ...（通用模板，&${RTYPE}）
restart.inc     @INCLUDE 进来：&EXT_RESTART ...
system.xyz      原子坐标（XYZ，angstrom，笛卡尔）
BASIS_SETS      基组库     ← 随 CP2K 分发
PSEUDO_POT      赝势库     ← 随 CP2K 分发
```

主输入骨架（Tab. 2.1 结构，`@SET` 明细从略）：

```none
@SET SYSNAME My_system
@SET RTYPE MD
@SET CPUTIME 36000
@SET RESTART FALSE
@SET BASISFILE BASIS_SETS
@SET PSEUDOFILE PSEUDO_POT
...（其余 ~20 个 @SET：CUTOFF / GRIDS / SCF_* / FUNCTIONAL / GEO_* / MD_* / OUT_*）

&GLOBAL
  PROJECT ${SYSNAME}
  RUN_TYPE ${RTYPE}
  PRINT_LEVEL MEDIUM
  WALLTIME ${CPUTIME}
&END GLOBAL

@IF ( ${RESTART} == TRUE )
  @INCLUDE 'restart.inc'
@ENDIF

@INCLUDE 'forces.inc'

@IF ( ${RTYPE} /= ENERGY_FORCE )
  @INCLUDE 'motion.inc'
@ENDIF
```

### 4.4 三条"写输入时立刻能省事"的规则（全部来自 T09 P8）

1. **`@SET` 行只能有三个东西**：`@SET`、变量名、值。多一个 token 就变成值的一部分。
2. **文件名行绝不加注释**（同一条规则的通则化形式）。
3. **写完先 `cp2k -c input.inp`**——它递归检查所有 `@INCLUDE`，能在提交前抓出语法错误。

---

## 5. 【新】相对既有 A–G 层的增量（先 grep 确认）

**grep 命令与结果**（工作目录 `D:\cp2k-aimd\cp2k-aimd-v1.2`）：

| 检索式 | 命中 | 结论 |
|---|---|---|
| `@SET\|@INCLUDE\|@IF\|&EXT_RESTART\|RUN_TYPE ENERGY_FORCE\|WALLTIME` over `*.md` | 51 处 | `@SET/@INCLUDE` 只有 4 处实质提及：`playbook.md:342`（`@SET DATAPATH`）、`course_learned.md:674`、`learn_L3.md:98/100`、`MAPPING.md:329/334` —— **全部只讲"用 `@SET` 写基组路径"这一件事**；`@IF` 在整个 A–G 层**零命中** |
| `-html-manual\|--html\|--xml\|xml2htm` | `official/13` 4 处 | G 层讲的是 `cp2k --html`/`--xml`；**`-html-manual` / `--html-manual` 这个写法零命中** |
| `cp2k -c\|--check` | 只有 `build_mapping.py --check` | **`cp2k -c`（输入语法自检）在 A–G 层零命中** |
| `top.level\|顶层面\|13 个\|顶层段` | `official/20` 等 | G 层记 **14 个顶层段**；材料写 **13** |
| 输出文件清单（`.ener\|pos-1.xyz\|PROJECT-RESTART`） | `course_learned.md` 有 `cp2k-1.energy` 等 | **`PROJECT-1.ener` / `PROJECT-1.cell` / `PROJECT-RESTART.wfn` 这一族命名在 G 层零命中** |

### 5.1 新增（G/E 层没有，或只有一句话）

| # | 增量内容 | 出处 | 为什么现在才补得上 |
|---|---|---|---|
| **H04-1** | **`@SET` 的"3 条指令"硬规则 + 行内注释污染变量值 + 文件名行禁注释** | T09 P8 | A–G 层只把 `@SET` 当"写路径的语法糖"，**没有任何一处说这条规则**；这是新手最常见的隐形错误（基组文件名被注释尾巴污染 → "找不到文件"）。 |
| **H04-2** | **`@IF ( ${VAR} == X ) … @ENDIF` 条件段；`${VAR}` 还能放进 `&段名` 和 `&EACH` 的键里** | T09 P10/P11/P18/P23 | `@IF` 在 A–G 层**零命中**。"一套输入同时管 MD/GEO_OPT/单点"的写法完全缺失。 |
| **H04-3** | **`&EXT_RESTART` 不写 `RESTART_FILE_NAME` 也能用**——直接把 `cp2k.sopt -i PROJECT-1.restart` 当输入提交 | T07 P14 / T08 P18 | G 层 `07_restarting.md` 只讲"输入里写 `&EXT_RESTART` + `RESTART_FILE_NAME`"；**"restart 文件本身就是完整输入，可以直接 `-i`"这一招在 G 层零命中**，是断点续算最省事的一条路径。 |
| **H04-4** | **`cp2k -c input.inp` 做输入语法自检，且递归检查所有 `@INCLUDE`** | T09 P8 | A–G 层零命中；与 skill 自己的 `validate_inp.py` 是两条互补的检查路径（前者是 CP2K 真解析器）。 |
| **H04-5** | **`-i`/`-o` 之外的四个实用选项 `-version` / `-check` / `-html-manual` / `-help`** | T07 P3 / T08 P4 | G 层只有 `--html`/`--xml`；`-version`/`-check`/`-help` 零命中。 |
| **H04-6** | **"输出到文件是 append"这一行为警告** | T07 P3 / T08 P4 | A–G 层零命中（skill `run.md` 用的是 shell 重定向，语义不同）。 |
| **H04-7** | **一次运行的输出文件命名族**：`PROJECT-1.restart` / `PROJECT-pos-1.xyz` / `PROJECT-1.ener` / `PROJECT-1.cell` / `PROJECT-RESTART.wfn` | T07 P4 / T08 P5 | G 层只零散提到 `.wfn`/`.kp`；**`-1.ener`、`-1.cell`、`-pos-1.xyz` 的"-1 是运行序号"这层含义**首次明确。 |
| **H04-8** | **"可选输入文件默认在 `cp2k/data`"** | T07 P4 / T08 P5 | 补充了"库文件从哪来"的一环（skill `sections.md` 写过"（cp2k/data）"，但没说"不写路径时 CP2K 会去那儿找"）。 |
| **H04-9** | **单点计算不需要 `&MOTION`**（`@IF ( ${RTYPE} /= ENERGY_FORCE )`） | T09 P23 | A–G 层没有把"`RUN_TYPE` → 是否要 `&MOTION`"这条判据写清楚（skill 的 `validate_inp.py` 有等价逻辑，但**知识库文档里没写**）。 |
| **H04-10** | **`&PRINT` 的挂载位置：控制 SCF 的 `&PRINT` 在 `&SCF` 下，控制轨迹/速度的 `&PRINT` 在 `&MOTION` 下** | T09 Tab. 1.3（P12）vs Tab. 1.8（P16） | G 层 `13` 讲了 printkey 机制，但没给"MD 场景下两个 `&PRINT` 各挂哪儿"的对照。 |
| **H04-11** | **`&TRAJECTORY` 默认 `LOW`、`&VELOCITIES` 默认 `HIGH`** → `PRINT_LEVEL MEDIUM` 时只有轨迹没速度 | T07 P12 / T08 P15 | G 层没有这两个默认级别（它讲的是"段参数"语义）。这解释了"为什么我没写 `&VELOCITIES` 就没有速度文件"。 |
| **H04-12** | **`&OT` 只对绝缘体有效；`PRECONDITIONER FULL_ALL` + `ENERGY_GAP` 的搭配含义；`&OUTER_SCF` 的 500×100 圈机制** | T09 Tab. 1.3（P12） | G 层 `02`/`03` 有 OT/OUTER_SCF 的参数表，但**"OT 需要 HOMO–LUMO 能隙 → 只对绝缘体"这条物理判据**与"`ENERGY_GAP` 是给 `FULL_ALL` 用的能隙低估"这层关系，A–G 层表述不如这里集中。 |
| **H04-13** | **`&TOPOLOGY COORDINATE XYZ` = 从 XYZ 读坐标永远是笛卡尔 + angstrom** | T09 P13 | 明确了"XYZ 文件里单位不可改"这一限制（G 层未明确）。 |
| **H04-14** | **`&KIND` 的 `POTENTIAL` 字符串必须与赝势文件里的条目"精确一致"、位于元素名之前** | T09 P13 | 把"基组-赝势匹配"从"注意事项"落成"字符串规则"。 |
| **H04-15** | **9 文件工程组织约定**（主输入只放变量 + 两个小段，其余全 `@INCLUDE`） | T09 §2.1（P21） | A–G 层没有"多文件工程"的落地约定。 |
| **H04-16** | **输入构建工具链**：vim/emacs 插件（含官网 URL）、ASE、PyCP2K（`GLOBAL%RUN_TYPE` ↔ `GLOBAL.Run_type`）、Chimera TETR/LEV00、Avogadro 1/2 | T08 P19–P21 | A–G 层零命中（`playbook.md` 只提了一句 `cp2k.vim` 要装好，没给 URL 与能力）。 |
| **H04-17** | **官方练习的"三档难度路由表"**（Beginner 4 条 / Intermediate 8 条 / Extended 4 条 + 性能页） | T18 P2–P6 | 是"想练什么去哪一页"的索引；正文仍在 G 层 `24_official_exercises.md`。 |

### 5.2 只写指针（G 层已写，本文不重复）

| 内容 | 去哪 |
|---|---|
| 输入语法 8 条规则（段/嵌套/大小写/#与!/单位方括号/续行 `\`/逻辑值三态/段默认参数） | `references/official/13_input_syntax_and_print.md` §2 |
| printkey 四控制项：段参数、`EACH`（从右往左匹配）、`ADD_LAST`、`COMMON_ITERATION_LEVELS` | 同上 §3.2 |
| `FILENAME` 四种写法（`STD_OUT` / `filename` / `./filename` / `=filename`）与危险提示 | 同上 §3.2(5) |
| 迭代层级（`1_4_5` = 第 4 个 MD 步的第 5 个 SCF 步） | 同上 §3.1 |
| `cp2k --html` / `--xml` 生成与二进制版本一致的文档 | 同上 §4 |
| `&GLOBAL` 全部关键字与默认值（`PROJECT_NAME` 别名 `PROJECT`、`RUN_TYPE` 默认 `ENERGY_FORCE`、`PRINT_LEVEL` 默认 `MEDIUM`、`WALLTIME` 两种写法、`ECHO_INPUT`…） | `references/official/01_global_and_units.md` §2 |
| `&EXT_RESTART` 关键字全表、NEB/各场景续算对照表 | `references/official/07_restarting.md` §4–§5 |
| 四个可执行文件的完整对照（含 `pdbg`/`sdbg`）与 MPI 启动、三种标准流 | `references/official/01_global_and_units.md`、`08_errors_and_faq.md` §1 |
| 31 个官方练习的正文内容 | `references/official/24_official_exercises.md` |
| `mpirun -n N cp2k.popt …` 的集群/本地提交模板 | `references/run.md` |

---

## 6. 与既有层的冲突 / 纠错（含页码证据）

### 6.1 【必读】skill 的 `gen_inp.py` / 模板 与教材写法的出入（5 条）

> 逐条都用 grep + 实跑核对过。**注意层次**：这些不是"教材错了"，而是"skill 工具的行为与教材/现代官方写法不一致"。

#### ⚠️ C-1　`@SET` / `@IF` / `@INCLUDE` 一律不被 `validate_inp.py` 识别（**会给出假阳性**）

- **教材依据**：T09 P8 明确 `@SET`/`@INCLUDE`/`@IF` 是**CP2K 官方前处理语法**（且 T09 P8 给出 `cp2k -c` 官方自检命令），T09 P23 的 `System.inp` 通篇依赖它们。
- **skill 现状**：`scripts/gen_inp.py` **完全不发射** `@SET`/`@IF`/`@INCLUDE`（grep `@SET|@IF|@INCLUDE` → 0 命中）；`scripts/validate_inp.py` 只 strip `#` 注释、只认 `&`/关键字行，**没有前处理分支**。
- **实测证据**（本轮实跑，文件已删）：

  ```
  $ cat t09style.inp
  @SET SYSNAME My_system
  @SET RTYPE ENERGY_FORCE
  @SET CPUTIME 36000
  &GLOBAL
  PROJECT ${SYSNAME}
  RUN_TYPE ${RTYPE}
  PRINT_LEVEL MEDIUM
  WALLTIME ${CPUTIME}
  &END GLOBAL
  @INCLUDE 'forces.inc'

  $ python scripts/validate_inp.py t09style.inp
    [warn] L7: RUN_TYPE '${RTYPE}' not a known value
    [ERROR] missing required top-level section &FORCE_EVAL
    RESULT: 1 error(s), 1 warning(s)     ← exit 1
  ```

  → **T09 教材风格的正确输入被判 1 error + 1 warning（`@INCLUDE` 指向的段看不见）。**
- **建议**：`validate_inp.py` 增加一层"前处理感知"：识别 `@SET/@INCLUDE/@IF/@ENDIF/@ELSE`，遇到未解析的 `${VAR}` 就**跳过该值的一致性检查**而不是报 warn；`@INCLUDE '<file>'` 若文件存在则**递归校验**（与 CP2K 的 `-c` 对齐），不存在则降级为提示。

#### ⚠️ C-2　`validate_inp.py` 不认 `!` 注释（**CP2K 官方注释符**）

- **教材依据**：T08 P7 `! or # – comments`；T09 全篇用 `!`（如 Tab. 1.2 P11 `METHOD Quickstep` 前后的 `!` 大段注释）。
- **skill 现状**：`validate_inp.py:123-125`
  ```python
  def strip_comment(line):
      # CP2K comments start with '#'
      return line.split("#", 1)[0].rstrip()
  ```
  **只 strip `#`。**
- **实测证据**：

  **实测 A（行内注释落在关键字值上）** —— 输入用 `RUN_TYPE MD   ! must match MOTION`：

  ```
  $ python scripts/validate_inp.py t.inp
    [warn] L3: RUN_TYPE 'MD   ! MUST MATCH MOTION' not a known value
    RESULT: OK (1 warning(s))                 ← exit 0，但值被污染
  ```

  **实测 B（行内注释落在 `&END` 行上）** —— 输入用 `&END GLOBAL   ! global run control done`：

  ```
  $ python scripts/validate_inp.py t.inp
    [warn] L5: unknown section '&END' (possible typo? known: MD, KIND, EI)
    [ERROR] unclosed section '&GLOBAL' (opened at L1)
    [ERROR] unclosed section '&END' (opened at L5)
    [ERROR] missing required top-level section &FORCE_EVAL
    RESULT: 3 error(s), 1 warning(s)          ← exit 1，整个文件被判废
  ```

  → 根因：`END_RE = r"^\s*&END\s*(\w+)?\s*$"` 要求**行尾即结束**，带 `!` 注释后匹配失败，该行反而被 `SECTION_RE` 当成"新开一个名为 `END` 的段"。
  这是一个**完全合法**的 CP2K 输入被判 3 个 error。
- **建议**：`strip_comment` 改成按 `#` 与 `!` 中**先出现者**截断（注意别误伤含 `!` 的路径/引号内容——CP2K 里 `!` 在方括号单位与文件名字符串中也可能出现，稳妥做法是只在"行首非空白处或空白后"才认作注释起点），并各加一条自测用例（`RUN_TYPE MD !`、`&END GLOBAL !`）。

#### ⚠️ C-3　模板不带 `WALLTIME`——与教材"可续算"主线相悖

- **教材依据**：T09 §1.3（P9）逐条解释 `WALLTIME = internal limit for CPU time in seconds … for a clean job ending and restart`；T07 P7 / T08 P8 的 `&GLOBAL` 示例里 `WALLTIME 3600` 是**示例的一部分**；T07 P14 / T08 P18 把"批处理时限"列为重启的首要原因。
- **skill 现状**：`grep WALLTIME scripts/gen_inp.py` → **0 命中**；`references/templates/*.inp` 8 个模板**全都没有 `WALLTIME`**（已逐个核对 `static.inp` / `aimd_md.inp` / `geo_opt.inp` / `cell_opt.inp` / `neb.inp` / `metadyn.inp` / `vib.inp` / `qmmm.inp` 的 `&GLOBAL` 块）。
- **风险**：用户拿到生成的输入直接投到有墙钟上限的队列上，**超时被杀时可能来不及写出 restart**（教材的因果链正是"`WALLTIME` → 干净结束 → 可重启"）。
- **建议**：`gen_inp.py` 增加 `--walltime <秒|HH:MM:SS>`，**并在 `&GLOBAL` 里默认发出**（值可由用户/队列时限决定）；同时 `templates/*.inp` 加 `__WALLTIME__` 占位。

#### ⚠️ C-4　默认"基组族 ↔ 库文件"可能不配套

- **教材依据**：T08 P10/P11 用 `BASIS_SET_FILE_NAME GTH_BASIS_SETS` + `TZV2P-GTH`（老 GTH 族）；T09 P13 用 `SZV-MOLOPT-SR-GTH`（MOLOPT 族）；现代官网 first-calculation 页用 **`BASIS_SET_FILE_NAME BASIS_MOLOPT` + `DZVP-MOLOPT-GTH`**。
- **skill 现状**：
  - `templates/static.inp:10` 与 `templates/aimd_md.inp:10` 都是 `BASIS_SET_FILE_NAME BASIS_SET`；`gen_inp.py` 的 ADMM 辅助库逻辑（L382–L391）也按"主基组是否含 MOLOPT"来选 `BASIS_ADMM_MOLOPT`/`BASIS_ADMM`。
  - 但 `gen_inp.py:1132` 的 `--basis` 默认值是 `["DZVP-GTH-PADE"]`，而 `recommend.py:44` 对金属默认给 **`DZVP-MOLOPT-SR-GTH`**（L46 轻元素给 `DZVP-GTH-PADE`）。
- **冲突点**：选了 `DZVP-MOLOPT-SR-GTH` 却仍载入 `BASIS_SET`，**该基组条目在 `BASIS_SET` 里不存在**（MOLOPT 族在 `BASIS_MOLOPT`）。G 层 `01_global_and_units.md` §5.1 记载官方静态教程的库文件就叫 `BASIS_SET`——所以这不是"skill 写错"，而是**"模板写死了文件名，却没有随基组族联动"**。**而 `recommend.py` 正是这么推荐的**（`METAL_BASIS = "DZVP-MOLOPT-SR-GTH"` / `METAL_POT = "GTH-PBE"`，L44–L45；`LIGHT_BASIS = "DZVP-GTH-PADE"` → `BASIS_SET` 才配得上），即 **`recommend.py` 的输出与模板的 `BASIS_SET_FILE_NAME` 互相矛盾**。
- **建议**：`gen_inp.py` 按所选基组族自动决定 `BASIS_SET_FILE_NAME`（含 `MOLOPT` → `BASIS_MOLOPT`，否则 `BASIS_SET`），或至少 emit 一行注释提示"确认你的 `cp2k/data` 里这个文件叫什么"。

#### ⚠️ C-5　`&CELL` 的两种写法：模板用 3×3 矢量，教材用 `ABC`

- **教材依据**：T07 P6 的单位示例就是 `ABC [nm] 100 100 100`；T08 P11 用 `ABC 9.8528 9.8528 9.8528`；T09 Tab. 1.4（P13）用 `ABC [angstrom] 15.28 15.28 15.28`——**三份材料一致用 `ABC`**。
- **skill 现状**：`templates/*.inp` 全部用
  ```
  A __A1__ __A2__ __A3__
  B __B1__ __B2__ __B3__
  C __C1__ __C2__ __C3__
  ```
  这是 G 层官方静态教程（`01_global_and_units.md` §5.2）的写法——**两边都是官方写法，不构成错误**，但**教材读者会对不上号**。
- **建议**：不改代码；在 `sections.md` 的 `&CELL` 条目补一句"`A/B/C` 三矢量 ↔ `ABC` + `ALPHA/BETA/GAMMA` 两种等价写法"（`MAPPING.md:333` 已记录讲师也讲了两者，只是 skill 文档没写）。

### 6.2 材料之间 / 材料 与 G 层 的冲突（照实登记）

| # | 冲突 | 证据 | 处置 |
|---|---|---|---|
| **X-1** | **顶层段数目：13 vs 14** | T07 P5 / T08 P6：`Sections – 13 (optional) top level sections`；G 层 `20_input_reference_tree.md` §1：**14 个顶层段**（多出 `&MULTIPLE_FORCE_EVALS`，且它只有 2 个关键字、0 个子段） | **以 G 层为准（14）**；T07/T08 是 2018–2019 年的表述。这正是 `AGENTS.md` §5"G 层没写则以 H 层为准"的镜像情形——这条 G 层写了。 |
| **X-2** | **`&MOTION` 是"必需"还是"按需"** | T09 P7 把 `GLOBAL`/`FORCE_EVAL`/`MOTION` 并列为"**3 个必需段**"；但 T09 Tab. 2.1（P23）自己用 `@IF ( ${RTYPE} /= ENERGY_FORCE ) @INCLUDE 'motion.inc' @ENDIF` 把 `MOTION` 变成**条件性**的；P13 §1.5 开头又写"**只要原子会动就要求写 MOTION**" | **T09 内部前后不一致**。结论取"按需"：`RUN_TYPE ∈ {ENERGY_FORCE}` → 不需要；`{MD, GEO_OPT, CELL_OPT, BAND…}` → 必需。与 skill `validate_inp.py` 的 `MOTION_RUN_TYPES` 逻辑一致。 |
| **X-3** | **`$VAR` vs `${VAR}`** | T08 P7 写 `$VAR – replaced with variable value`（无花括号）；T09 P8/P9 全篇写 `${VAR}` | **写作 `${VAR}`**——T09 有 20+ 处实例、T08 只有目录式的 1 行；花括号形式也是 skill/庚子层在用的。把 T08 那一行当**排版省略花括号**处理（该页同一行还有 `@IF / @ENDIF` 缺参数，明显是提纲式写法）。 |
| **X-4** | **CLI 选项的横线数** | T07 P3 `cp2k.sopt -version` / `-check` / `-html-manual` / `-help`（单横线）；T08 P4 `--version` / `--check` / `--html-manual` / `--help`（双横线） | **同一场材料的两个版本自相矛盾**。G 层官方用 `--html` / `--xml`（`13` §4），现代官网用 `-i` / `-o`。**实践：两个都试，或先 `cp2k --help` 看它印什么。** |
| **X-5** | **基组库文件名代际差异** | T07 P10：`GTH_BASIS_SET`、`BASIS_MOLOPT`；T08 P10：`GTH_BASIS_SETS`、`POTENTIAL`；T09 P13：`SZV-MOLOPT-SR-GTH`（隐含 `BASIS_MOLOPT`）；G 层官方 2.4 期教程：`BASIS_SET`、`GTH_POTENTIALS`；现代官网：`BASIS_MOLOPT`、`GTH_POTENTIALS` | **老名字（`GTH_BASIS_SETS`/`POTENTIAL`/`BASIS_SET`）与 MOLOPT 基组混用会失败**。**唯一可靠办法：`ls $CP2K_DATA`（或 `cp2k/data/`）看实际文件名**，然后让 `BASIS_SET_FILE_NAME` 与 `&KIND/BASIS_SET` **同族**。skill `sections.md` 的 `BASIS_SET_FILE_NAME BASIS_SET` 建议同步加这条警示。 |
| **X-6** | **`.ener` vs `.energy`** | T07 P4 / T08 P5：`PROJECT-1.ener`（MD energies, temperature, cons. Q）；skill `course_learned.md:365/840` 记的是 `cp2k-1.energy` | **两个都存在过**（跨版本改名）。**处置：以自己跑完 `ls` 的实际文件名为准**；在 `postprocess.md` 的文件识别逻辑里两者都要认（若尚未都认，值得补）。 |
| **X-7** | **`-1` 后缀与运行序号** | T07 P4 的 `PROJECT-pos-1.xyz` / `PROJECT-1.ener` / `PROJECT-1.cell` **都有 `-1`**，而 `PROJECT-RESTART.wfn` **没有** | 不是冲突而是**两套命名**：带 `-1` 的是"随运行序号递增"的滚动输出；`RESTART.wfn` 是"固定名、被覆盖"的状态文件。**别把 `-1` 当固定后缀写死进脚本**——二次续算会变成 `-2`。 |
| **X-8** | **T09 印刷页码 = PDF 页 − 6** | T09 P11 页脚是 "5"，P23 页脚是 "17" | 引用 T09 时**必须带 PDF 页码**，否则与目录里的 §号对不上。本笔记统一用 `T09 P<PDF页>`。 |

### 6.3 材料里的过时项（供 skill 更新时取舍）

| 内容 | 出处 | 说明 |
|---|---|---|
| `cp2k.sopt` / `cp2k.popt` | T07 P2/P3、T08 P3/P4 | 现代发布版命名为 `psmp` / `pdbg` / `ssmp` / `sdbg`（G 层 `01`）。skill `run.md`/`sections.md` 用的 `popt` 在**自编译**场景仍常见，**保留但补一句"先 `ls exe/*/` 确认"**。 |
| `cp2k.berlios.de` | T09 P1、P25 | 早已迁移到 `cp2k.org`。 |
| `http://sourceforge.net/p/cp2k/code/HEAD/tree/trunk/cp2k/data` | T08 P13 | 现在是 GitHub。 |
| `materialscloud.org -> WORK -> QuantumMobile` | T07 P2 | 历史产物，登记即可。 |
| `cp2k -c input.inp` | T09 P8 | 现代写法是 `cp2k --check`（G 层未收录 `--check`；T07/T08 的 `-check` 与之呼应）。 |

---

## 7. 存疑（**已逐条查证**：6 条定案、3 条收窄）

> 本节在 2.7.6 之后做了一轮**逐条查证**。定案手段按优先级：官方 `cp2k_input.xml`
> （`_kw_probe.py` 直查）→ 重读/重抽教材原页 → 官方手册（给 URL）。
> 定案的写"结论 + 依据"；确实无法确证的**收窄**成"已排除什么 + 还缺什么"，
> 不硬编结论。**推翻原文猜测的条目附更正记录。**

### 7.1 ✅ 已定案（6 条）

| # | 存疑点 | **结论** | 依据 |
|---|---|---|---|
| **Q3** | 13 个顶层段具体是哪 13 个 | ✅ **当前（CP2K 9.0 官方 XML）是 14 个**，可逐个列名：`&ATOM` `&DEBUG` `&EXT_RESTART` `&FARMING` `&FORCE_EVAL` `&GLOBAL` `&MOTION` `&MULTIPLE_FORCE_EVALS` `&NEGF` `&OPTIMIZE_BASIS` `&OPTIMIZE_INPUT` `&SWARM` `&TEST` `&VIBRATIONAL_ANALYSIS`。与 G 层 `20_input_reference_tree.md` §2 的"14 个"一致。<br>教材说的"13"是 **CP2K ~6.x（2018–2019）时代**的数；**具体少哪一个无法确证**（需要当年 `manual.cp2k.org` 的 `CP2K_INPUT` 快照逐个数，本轮未取到）。<br>**实操结论**：不要依赖"几个段"这个计数，直接用上面这份名单（或跑 `python _kw_probe.py --section` 看真值）。 | 直读官方 XML 的顶层 `SECTION` 子元素：`ET.parse(cp2k_input.xml).getroot()` 的直接 `SECTION` 子节点共 **14** 个（脚本输出） |
| **Q4** | `EMAX_SPLINE [eV] 50` 出现在哪一段 | ✅ **在 `FORCE_EVAL/MM/FORCEFIELD/SPLINE`**，默认 `0.5`、单位 `hartree`，官方描述 *"Specify the maximum value of the potential up to which splines will be constructed"*。<br>**它不是 QS 的 `&KIND/&BASIS_SET` 关键字** —— 那是**经典 MM 力场**的样条势上限。<br>**更正记录**：本节原写"现代 CP2K 里它是 `&SUBSYS/&KIND/&BASIS_SET` 的 `EMAX_SPLINE`？材料未说明" —— **这个猜测是错的**。正确理解是：T07/T08 举这个例子只是为了演示"单位可以写在方括号里"，**与基组无关**；因此"不要把这条当任意段都能写单位的证据"这个告诫**依然成立**，而且更成立（它是 MM 段的关键字）。 | `python _kw_probe.py --find EMAX_SPLINE` → 全库仅 1 处：`FORCE_EVAL/MM/FORCEFIELD/SPLINE`，`DEFAULT_VALUE 5.0E-001`、`DEFAULT_UNIT hartree` |
| **Q5** | T09 的 `&CELL ABC [angstrom] … PERIODIC XYZ` 对非周期体系是否够 | ✅ **不够。非周期必须两个段都写**：`&CELL PERIODIC NONE` **和** `&DFT/&POISSON PERIODIC NONE` + 一个非周期求解器（如 `PSOLVER MT`）。官方现行文档的孤立分子算例两处都写了。<br>另：`POISSON_SOLVER` 有别名 `POISSON` / `PSOLVER`（三种写法等价）；`&CELL PERIODIC` 的默认是 `XYZ`。 | 官方手册 [Run a First Calculation](https://manual.cp2k.org/trunk/getting-started/first-calculation.html)：`&POISSON PERIODIC NONE / PSOLVER MT` 与 `&CELL ABC … PERIODIC NONE` 同时出现；`python _kw_probe.py --find POISSON_SOLVER` 给出别名 |
| **Q6** | T08 P17 "Overview of an output file" 的内容 | ✅ **确认该页本来就是截图，不是抽取失败**：该页只有 **40 个字符对象**（标题 `CP2K Output: Overview of an output file …`）+ **2 个图片对象** + 12 个矩形；用 `x_tolerance` = 默认 / 1.5 / 3.0 三种参数重抽，**同样只得 41 字符**（相邻 P16 有 234、P18 有 340）。<br>⇒ 正文以**位图**呈现，文本层里不存在；**正文内容不可从文本恢复**（要看只能看图或 OCR）。本笔记如实不猜。 | `pdfplumber` 对源 PDF 第 17 页：`chars=40`、`images=2`、三种 `x_tolerance` 均 41 字符（脚本输出） |
| **Q7** | `WF_INTERPOLATION PS` 与 `EXTRAPOLATION_ORDER 3` 的适用边界 | ✅ **`WF_INTERPOLATION` 不是另一个关键字，它是 `EXTRAPOLATION` 的别名**（官方 XML 里同一 `<KEYWORD>` 有三个 `<NAME>`：默认名 `EXTRAPOLATION`，别名 `INTERPOLATION`、**`WF_INTERPOLATION`**）。<br>默认值 **`ASPC`**；合法取值含 `PS` / `ASPC` / `LINEAR_PS` / `USE_PREV_P` / `FROZEN` …；官方描述原文：**"PS and ASPC are recommended"**。<br>⇒ **T08 的 `WF_INTERPOLATION PS` 不是笔误**，它是同一关键字的另一个（同样被官方推荐的）取值；T09 的"ASPC for MD, PS otherwise"是对**取哪个值**的细化建议，两者不矛盾。<br>**更正记录**：本节原写"`WF_INTERPOLATION` 与 `EXTRAPOLATION` 是**两个不同关键字**，T08 那行是否笔误待查" —— **两处都错了**：是同一个关键字的别名关系，且 `PS` 合法。 | `python _kw_probe.py --find WF_INTERPOLATION` → `FORCE_EVAL/DFT/QS`，`默认名 EXTRAPOLATION \| 别名 INTERPOLATION, WF_INTERPOLATION`，`DEFAULT_VALUE ASPC`；官方 XML 原文 `<NAME type="default">EXTRAPOLATION</NAME>` + `<NAME type="alias">WF_INTERPOLATION</NAME>` |
| **Q8** | `ENERGY_FORCE` 与 `ENERGY` 的关系 | ✅ **两者都是合法取值**，且 `GLOBAL/RUN_TYPE` 的**默认值就是 `ENERGY_FORCE`**。官方枚举（完整）：`NONE, ENERGY, ENERGY_FORCE, MD, GEO_OPT, MC, SPECTRA, DEBUG, BSSE, LR, PINT, VIBRATIONAL_ANALYSIS, BAND, CELL_OPT, WFN_OPT, WAVEFUNCTION_OPTIMIZATION, MOLECULAR_DYNAMICS, GEOMETRY_OPTIMIZATION, MONTECARLO, ELECTRONIC_SPECTRA, LINEAR_RESPONSE, NORMAL_MODES, RT_PROPAGATION, EHRENFEST_DYN, TAMC, TMC, DRIVER, NEGF`（后半是前半的**同义别名**，如 `GEOMETRY_OPTIMIZATION`≡`GEO_OPT`）。<br>另有一个**同名但不同段**的 `&ATOM/RUN_TYPE`（默认 `ENERGY`，枚举 `NONE/ENERGY/BASIS_OPTIMIZATION/PSEUDOPOTENTIAL_OPTIMIZATION`）—— **查关键字时必须带上段路径**，否则会看到"默认值 ENERGY"而误判。<br>**现行官方文档**的入门算例用 `RUN_TYPE ENERGY`。<br>⇒ 沿用原文结论：`ENERGY_FORCE` 是安全写法（也是默认值）；`ENERGY` 只算能量不算力。 | `python _kw_probe.py --find RUN_TYPE` → `/GLOBAL`（默认 `ENERGY_FORCE`）与 `/ATOM`（默认 `ENERGY`）两处；枚举来自 XML 的 `DATA_TYPE/ENUMERATION/ITEM/NAME`；[官方入门算例](https://manual.cp2k.org/trunk/getting-started/first-calculation.html) 用 `RUN_TYPE ENERGY` |

### 7.2 ⚠️ 已收窄（3 条：查清了边界，但确证需要本机 CP2K 二进制 / 逐条点链接）

| # | 存疑点 | **已排除 / 已确立的事实** | **仍不确定 & 要确证需要什么** |
|---|---|---|---|
| **Q1** | `-o file` 到底是 append 还是覆盖 | **两份材料独立一致地说 append**，且 T08 把 T07 的 `(!!)` 改成了 **`(beware!)`** —— 同一作者在 2018 版**重申并加强了**这个警告，不像笔误。现行官方文档给出 `cp2k.psmp -i h2o.inp -o h2o.out`，并说"想同时在屏幕上看就改用 `\| tee h2o.out`"，但**没有说明 append/覆盖语义**。 | **仍不确定**：现代二进制（2024+）是否仍是 append。<br>**要确证**：`cp2k.psmp -i t.inp -o t.out` 连跑两次，看 `t.out` 里有几份 `PROGRAM ENDED` —— 本机**没装 CP2K**，无法实测。<br>**实操**：skill 继续保留"**提交前清理旧 `.out`**"的建议（无论哪种语义都安全）。 |
| **Q2** | `-check` / `--check` / `-c` 三个写法的版本归属 | 三个写法**确实各自出现在三份材料里**：T07 P3 `-check`、T08 P4 `--check`、T09 P8 `-c`。三份材料年代不同（T07/T08 是 2016/2018 workshop，T09 面向 CP2K 3.0）。<br>现行官方手册的 "Run a First Calculation" 页**没有列出任何语法自检选项**（只列 `-i` / `-o`）。 | **仍不确定**：哪个写法对应哪个版本、现行二进制接受哪些。<br>**要确证**：对每个版本的二进制跑 `cp2k.X --help`（本机无二进制）。<br>**实操**：写脚本时**优先用 `cp2k -c`**（T09 是最贴近"输入系统"的教材），并在注释里注明"若报未知选项改用 `--check`"。本 skill 自己的 `validate_inp.py` + `_official_validate.py` 已能在提交前完成同类检查，**不依赖 CP2K 自检**。 |
| **Q9** | T18 的 URL 是否仍有效 | cp2k.org 做过 **wiki 迁移**（本轮实测 `cp2k.org/tools:command_line` 已成空页）。**实测 T18 全文共 20 个 URL（去重后仍是 20），全部指向 `cp2k.org`**，其中 17 个是旧 wiki 命名空间（`/exercises:2015_pitt:*`、`/exercises:2016_summer_school:*`、`/exercises:2015_cecam_tutorial:*`、`/howto:*`、`/events:*` 等），只有 3 个是较新的 `/`、`/performance`、`/events:2019_cp2k_workshop_ghent:index`。<br>**正文内容不受影响**：G 层 `24_official_exercises.md` 是**已抓取存档**，练习正文以它为准。 | **仍不确定**：20 个链接里具体哪些还活（旧 wiki 命名空间在迁移后**大概率整体失效**，但本轮未逐个点）。<br>**要确证**：逐个发请求（20 次；价值低——正文已存档）。<br>**实操**：引用 T18 时**只把它当索引**，正文一律引 G 层。 |

### 7.3 本轮用到的查证命令（可复现）

```bash
python _kw_probe.py --find EMAX_SPLINE        # Q4：全库搜关键字属于哪一段（含别名）
python _kw_probe.py --find WF_INTERPOLATION   # Q7：命中并显示"默认名 + 别名"
python _kw_probe.py --find RUN_TYPE           # Q8：同名的两处（/GLOBAL 与 /ATOM）
python _kw_probe.py --find POISSON_SOLVER     # Q5：别名 POISSON / PSOLVER
```
外部资料（Q5、Q8 用到）：[Run a First Calculation — CP2K documentation](https://manual.cp2k.org/trunk/getting-started/first-calculation.html)、
[Foreword and FAQ — CP2K documentation](https://manual.cp2k.org/trunk/getting-started/foreword-and-faq.html)
