# H 层精读 06 · 基组与赝势（T20）＋ CP2K 使用入门（T24）

> **精读范围**：`txt/T20_ling_basis_pseudo.txt`（**34 页全文**）、`txt/T24_cp2k_intro.txt`（**19 页全文**），
> 逐页读完，无抽样。引用格式 `T20 P12` = 该 txt 里 `========== PAGE 12 ==========` 那一页。
>
> **材料身份**
> - **T20**《Optimisation of Basis Sets and Pseudopotentials》，Sanliang Ling（University College London），
>   **4th CP2K Tutorial, 31 Aug – 4 Sep 2015, Zurich**（`T20 P1`）——**官方 workshop 教材**，幻灯片型。
> - **T24**《CP2K 入门教程》，赵亚帆（yafanzhao@163.com / zevan.zhao@gmail.com）（`T24 P1`），
>   中文正文型教材，原始文件名标"**强烈推荐**"。**版本锚点：正文下载的是 CP2K 2.5.1 源码**（`T24 P2`），
>   编译环境写 Debian testing / 内核 3.17 / ifort 12.0.3 / openmpi 1.6.5"目前最新 1.8.3"（`T24 P2`）⇒ 成稿约 2014 年。
>
> **抽取假象提醒**（H 层 README §5）：pdfplumber 对两端对齐排版会丢词间空格、并会把**双栏幻灯片的两栏文本交错串行**。
> 本文档遇到明显的列错位一律**照抄 + 标注**（见 §7），不做"顺手的纠正"。
>
> **冲突裁决**：按 `h_tutorials/README.md` §1 与 `AGENTS.md` §5——H 层与 A–F 冲突时**先用 G 层裁定**；
> G 层没写的实操阈值以 H 层教材原文为准并标出处。本文档所有"冲突"均给页码证据。

---

## 1. 这两份材料教什么

| | **T20 · 基组与赝势优化** | **T24 · CP2K 使用入门** |
|---|---|---|
| 出处 | 4th CP2K Tutorial (Zurich, 2015) 官方 workshop | 中文个人教程（非官方），成稿约 2014 / CP2K 2.5.1 时代 |
| 体裁 | 幻灯片 34 页，**公式与流程图为图**，文字量少 | 正文 19 页，**输入片段密集**，几乎每节都给可抄的 `&SECTION` |
| 教什么 | ① 基组的数学构造（GTO/收缩/极化/弥散）②命名法与"质量对应表"③**MOLOPT 基组是怎么被优化出来的**（OPTIMIZE_BASIS 全流程）④BSSE 的 CP2K 做法 ⑤**GTH 赝势的解析形式与文件格式**⑥**赝势是怎么被优化出来的**（ATOM 全流程） | ①**装什么、怎么装**②**卡住时去哪问**③各种 `RUN_TYPE` 的输入模板④**影响精度的参数逐项**（晶胞/CUTOFF/基组/泛函/EPS_SCF/OT vs 对角化/EPS_DEFAULT）⑤非周期、多重度、NEB、频率的实操写法 |
| 不教什么 | 不讲"某元素该用哪个 q"的选择清单（只讲怎么自己造）；不讲 CP2K 输入语法全貌 | 不讲原理推导；**不做基组/赝势的取舍分析**（只有一句"一般 DZVP 就足够了" `T24 P9`） |
| 对 skill 的价值 | **唯一一份把"MOLOPT 与 GTH 从哪来"讲透的教材**——补齐 G 层"只登记标题、未收教材"的空档 | 提供一份**独立于庚子计算课程**的上手路径 + 若干可交叉验证/需纠偏的数值口径 |

**一句话**：T20 回答"**你手里这套基组/赝势是怎么被造出来、凭什么信它**"；T24 回答"**我什么都没有的时候，怎么从零把 CP2K 跑起来**"。

---

## 2. 逐节要点（带页码）

### 2.1 T20（34 页）

#### 2.1.1 背景与基组基础（P1–P7）

| 页 | 要点 |
|---|---|
| **P1** | 标题/作者/场合：*Optimisation of Basis Sets and Pseudopotentials*，Sanliang Ling (UCL)，4th CP2K Tutorial，2015-08-31 – 09-04，Zurich |
| **P2** | **CP2K 的两条电子结构路线**：`GPW`（Gaussian and plane waves）= **GTH 赝势** + **价电子**的高斯基组；`GAPW`（Gaussian and augmented plane waves）= **all electron calculations**。→ 全文的顶层分野 |
| **P3** | LCAO：分子轨道 = MO 系数 × 原子轨道（基函数）之和。（Jensen, *Introduction to Computational Chemistry*, Wiley (2007)） |
| **P4** | GTO：归一化常数 + 指数（**决定轨道宽度**）；`l_x + l_y + l_z` 之和决定轨道类型——**0=s、1=p、2=d、3=f** |
| **P5** | 收缩基组（contracted basis set）：由**收缩系数**（"to be optimised"）把若干原高斯线性组合 |
| **P6** | **极化函数**：角动量**高于价轨道**的基函数；**第一层极化函数最重要**；**H–Be 加 p 函数、B–Ca 加 d 函数**；作用是给基组增加柔性、更好描述成键 |
| **P7** | **弥散函数**：**指数很小**的基函数；更好描述波函数"尾巴"；对**弱束缚电子（阴离子、激发态）**与**气相分子**重要 |

> P3–P7 全部引自 Jensen 教材，属"教科书常识页"；**对 CP2K 决策没有直接增量**，但 P6/P7 是后文 SR 基组取舍的物理基础。

#### 2.1.2 GPW/GAPW 各自的基组 + 文件落点（P8–P9）

| 页 | 要点（**文件名照抄**） |
|---|---|
| **P8** | **GAPW 用全电子基组**：Pople 型（如 `6-31G*`）、相关一致基组（如 `aug-cc-pVDZ`）"and more"；见 `$CP2K/cp2k/data` 的 **`ALL_BASIS_SETS`** 与 **`EMSL_BASIS_SETS`**；更多全电子基组可从 **EMSL Basis Set Exchange**（`https://bse.pnl.gov/bse/portal`）取。**GAPW 必须在 `&KIND` 段里定义 potential**——见 `$CP2K/cp2k/data/POTENTIAL`，**选 "ALL" potential** |
| **P9** | **GPW 用基组**：**MOLOPT**（"basis sets optimised from **molecular** calculations"，见 **`BASIS_MOLOPT`**）；**固体用 `DZVP-MOLOPT-SR-GTH`**（`SR` = **shorter range**，即**更少、从而更不弥散**的原函数）；**务必检查基组收敛（DZVP/TZVP/…）**；**production run 不要用 `SZV`**；配 GTH 赝势的更多基组见 **`BASIS_ZIJLSTRA`** 与 **`GTH_BASIS_SETS`**；所有基组文件都在 `$CP2K/cp2k/data` |

#### 2.1.3 基组是怎么被"设计"和"造"出来的（P10–P23）

| 页 | 要点 |
|---|---|
| **P10** | **基组构造的 5 条标准**：①成本/精度折中；②**可系统改进的路线**（SZV/DZVP/TZVP/TZV2P/…）；③**同一个基组要在各种化学环境都表现良好**（从孤立分子到固体）；④要导向**良态（well conditioned）重叠矩阵**（线性标度计算的前提）；⑤**条件数 = 重叠矩阵最大本征值/最小本征值之比**。（VandeVondele & Hutter, *J. Chem. Phys.*, **127**, 114105 (2007)） |
| **P11** | **MOLOPT ↔ 全电子(Pople/NWCHEM) 质量对应表** + **SZV/DZVP/TZVP/TZV2P 的定义**（见 §3.1.1 与 §4.8）。出处标注 *Matthias Krack, 1st CP2K Tutorial, Zurich, 2009* |
| **P12** | **MOLOPT 基组文件格式**（以 `H DZVP-MOLOPT-GTH DZVP-MOLOPT-GTH-q1` 为例）逐字段标注：**element / basis set name / "number of valence electrons in pseudo" / "number of CGTO contraction coefficients" / 各 set 的组成行 / Gaussian exponents / s-function / p-function 系数列**。→ 照抄见 §4.2 |
| **P13** | **基组优化要事先定的 5 件事**：高斯指数个数（**优化前就要定**）、每个角动量的基函数个数、**训练分子的选择（决定可迁移性）**、优化策略（不同基组**是否同时优化**）、**条件数在优化目标里的权重** |
| **P14** | **训练分子怎么选**：由**不同元素、不同配位环境**构成的**小分子**；每个分子**最好只含两种元素**（其中含目标元素）；好的小分子来源（**带优化好的几何**）见 **Ahlrichs et al., *Phys. Chem. Chem. Phys.*, 7, 3297 (2005)** 的 **Supporting Information** |
| **P15** | **MOLOPT 的目标函数由这些量构成**：收缩系数、指数、目标函数、待优化的基组、训练分子、**总能量**、**条件数**。（VandeVondele & Hutter, *J. Chem. Phys.*, **127**, 114105 (2007)） |
| **P16** | **用 `OPTIMIZE_BASIS` 做基组优化的四步**：①选**参考（完备）基组** → ②**用参考基组做精确的分子计算** → ③**选定待拟合基组的形式** → ④**最小化目标函数** `Ω(α, c) = Δρ_i^{B,M}(α, c) + γ·ln κ(α, c)`。页脚注明：**developed by Dr Florian Schiffmann** |
| **P17** | **参考（完备）基组从哪来**：查 **`GTH-def2-QZVP`** 与 **`aug-GTH-def2-QZVP`**，收在 **`$CP2K/cp2k/data/BASIS_ADMM`**；或**用 `ATOM` 码生成未收缩基组**（见 Marcella 的 slides 与 `$CP2K/cp2k/tests/ATOM` 里的例子）。**分子计算的三条要求**：所有元素都用参考基组；**避免同核双原子分子**；**用平衡几何（即先做 `GEO_OPT`）** |
| **P18** | `ATOM` 生成 Na 未收缩基组的**完整输入**（`RUN_TYPE BASIS_OPTIMIZATION`、`CORE 1s2`、`MAX_ANGULAR_MOMENTUM 1`、`NUM_GTO 6 6`、`POTENTIAL_NAME GTH-PBE-q9`、`&POWELL ACCURACY 1.e-8 STEP_SIZE 1.0`）→ 照抄见 §4.4 |
| **P19** | 仅图（"Generate uncontracted basis set with ATOM" 的结果截图），文本无可抽取内容 |
| **P20** | `ATOM` 输出的 **Na 完备基组（CBS）**：8 个 set，每个头行为 `2 0 2 1 1 1 1`，指数依次 `23.51400109 / 11.54276369 / 4.98513381 / 2.06401264 / 0.83224580 / 0.31900235 / 0.06577574 / 0.02386738`，每行系数 `1.0 1.0 1.0`（**完全未收缩**） |
| **P21** | **怎样从 BSE 造一个 CP2K 格式的参考基组（`H GTH-def2-QZVP`）**：去 `https://bse.pnl.gov/bse/portal`，选 'H' 元素与 'Def2-QZVP' 基组，用 **'Gaussian 94' 格式**导出；左栏是转换后的 **CP2K 格式**（`H GTH-def2-QZVP`，**12 个 set**），右栏是 BSE 原始 Gaussian-94 文本；页面上写 **"(use exponents between 0.05~20 only)"** |
| **P22** | **`OPTIMIZE_BASIS` 的输入结构**（`PROJECT optbas` / `PROGRAM_NAME OPTIMIZE_BASIS` / `BASIS_TEMPLATE_FILE` / `BASIS_WORK_FILE` / `BASIS_OUTPUT_FILE Ti_FIT10` / 注释掉的 `USE_CONDITION_NUMBER Y` 与 `CONDITION_WEIGHT 0.0005` / `&TRAINING_FILES DIRECTORY ../ticl4 INPUT_FILE_NAME ticl4.inp` / `&FIT_KIND Ti BASIS_SET FIT10 INITIAL_DEGREES_OF_FREEDOM EXPONENTS` / `&CONSTRAIN_EXPONENTS BOUNDARIES 0.1 20 USE_EXP -1 -1`）+ **拟合出的 `Ti FIT10` 基组（10 个 set：4 s + 3 p + 3 d）**；页脚注 **`(Ti electron configuration: [Ne] 3s2 3p6 4s2 3d2)`** 与 **`(see $CP2K/cp2k/tests/QS/regtest-optbas)`** → 照抄见 §4.5 |
| **P23** | 仅图（优化过程截图） |

#### 2.1.4 BSSE（P24）

| 页 | 要点（**输入片段照抄见 §4.6**） |
|---|---|
| **P24** | ①**MOLOPT 基组是"不完备"的**（incomplete）⇒ 有 BSSE；②**用 Boys and Bernardi 的 counterpoise 方案**做 BSSE 校正——CP2K 里就是 `RUN_TYPE BSSE` + `&FORCE_EVAL &BSSE` 里两个 `&FRAGMENT LIST`；③对**结合能**之类的计算有用；④**用更大的基组来减小 BSSE**；⑤手动路径是 `&KIND` 里写 **`GHOST`**（例中 `&KIND H_ghost` 配 `BASIS_SET DZVP-MOLOPT-SR-GTH`）。文献：**Boys & Bernardi, *Mol. Phys.*, 19, 553 (1970)**；算例：`$CP2K/cp2k/tests/QS/regtest-gpw-3` |

#### 2.1.5 GTH 赝势：解析形式、文件格式、可用范围、怎么做（P25–P32）

| 页 | 要点 |
|---|---|
| **P25** | **GTH 赝势的局域部分**解析形式：**离子电荷误差函数（error function）长程项** + **短程项** + 系数；**`r_loc` = 高斯离子电荷分布的宽度**。（Krack, *Theor. Chem. Acc.*, 114, 145 (2005)）公式本体在图中，未抽取 |
| **P26** | **非局域部分**：系数、**高斯型投影子（Gaussian-type projectors）**、归一化常数、球谐函数、半径。（同上文献） |
| **P27** | **GTH 赝势文件的字段语义**（以 Ti 为例）：`Ti GTH-PBE-q12 GTH-PBE` → `4 6 2`（**"Number of valence electrons in each shell (s/p/d)"**）→ `r_loc` + 势函数个数 + 系数 → 每个 `l`（s/p/d）一组 `r_l` + **"number of non-local projectors"** + 系数。→ 照抄见 §4.3 |
| **P28** | **GTH 赝势的可用范围（按泛函）**：**LDA (PADE)：H–Rn（含镧系）**；**PBE：H–Rn（不含镧系）**；**PBEsol：H–Kr（+ a few selected）**；**BP：H–Kr（+ a few selected）**；**HCTH：a few selected elements**；**NLCC 赝势：a few selected elements**。文件都在 `$CP2K/cp2k/data`，见 **`POTENTIAL`**、**`GTH_POTENTIALS`**、**`NLCC_POTENTIALS`**。（Matthias Krack, 1st CP2K Tutorial, Zurich, 2009） |
| **P29** | **赝势优化流程**：①用**选定的 DFT 泛函**做**全电子**计算 → ②选定赝势的拟合形式 → ③**最小化全电子原子与赝原子在原子球内的本征值与电荷之差** → ④质量检查（quality check）。（Hutter et al., *Phys. Rev. B*, **58**, 3641 (1998)） |
| **P30** | **用 `ATOM` 优化 O 的赝势（泛函 PBE0）的完整输入**：`RUN_TYPE PSEUDOPOTENTIAL_OPTIMIZATION`、`ELECTRON_CONFIGURATION [He] 2s2 2p4`、`CORE [He]`、`MAX_ANGULAR_MOMENTUM 2`、`COULOMB_INTEGRALS ANALYTIC`、`EXCHANGE_INTEGRALS ANALYTIC`、`RELATIVISTIC DKH(2)`、`&XC_FUNCTIONAL PBE0`、`EPS_SCF 1.e-10`、`&AE_BASIS / &PP_BASIS BASIS_TYPE GEOMETRICAL_GTO`、`POTENTIAL_NAME GTH-PBE-q6`、`&POWELL ACCURACY 1.e-10 STEP_SIZE 0.5 WEIGHT_PSIR0 0.1`；算例 `$CP2K/cp2k/tests/ATOM/regtest-pseudo` → 照抄见 §4.4 |
| **P31** | 仅图（赝势优化结果截图） |
| **P32** | **用独立的 `ATOM` 码优化赝势**：查 **`README_quick_GTH`（在 `$CP2K/potentials`）**；更多细节见 Dr Matthias Krack 的 slides；**质量检查有更多选项** |

#### 2.1.6 结语与延伸阅读（P33–P34）

| 页 | 要点 |
|---|---|
| **P33** | **三条工程纪律**：①**自己造基组/赝势之前，先读原始文献**；②优化出来的基组/赝势**要在生产运行前做大量测试、并与参考值比较**；③CP2K 用到的所有数据文件可从 `http://sourceforge.net/p/cp2k/code/HEAD/tree/trunk/cp2k/data/` 下载（**URL 已过时**，见 §7-13） |
| **P34** | 延伸阅读两篇（CECAM 链接）：Krack《Accuracy and Efficiency》、Mohamed《Basis Sets and Pseudo-Potentials》 |

---

### 2.2 T24（19 页）

#### 2.2.1 装机与求助（P1–P5）

| 页 | 要点 |
|---|---|
| **P1** | ①CP2K 定位："可以用多种方法对固体、液体、分子以及生物体系进行计算……DFT（高斯+平面波混合）、经典力场、半经验、DFTB"；**最大优势是计算速度很快**；②**三条安装路线**：(a) 发行版软件源预编译——Debian / Fedora / Ubuntu 三个包搜索页；(b) **官网预编译可执行文件**（`sourceforge.net/projects/cp2k/files/precompiled/`）——"**运行比较可靠**，缺点是用了**没有优化过的 blas / lapack 库，计算速度比较慢**"；(c) **源码编译**——好处是能用 **MKL** 等更快的数学库，**"使用 Intel 编译器以及 MKL 数学库编译的 CP2K 执行速度是预编译版本的 3 倍左右"** |
| **P2** | **源码编译步骤（Intel 路线）**：参考 `www.cp2k.org/howto:compile`；环境 = Debian testing / i5-4210M / 内核 3.17-1-amd64；先用 apt 装数学库（`libxc1 libxc-dev libint-dev libint1 libelpa-dev libelpa0 libopenblas-base libopenblas-dev libfftw3-3 libfftw3-bin libfftw3-dev libfftw3-mpi3 openmpi-bin gcc gfortran g++`；装 `-dev` 包以获得静态链接库；GNU 编译器 4.9.1、openmpi 1.6.5；Intel Fortran 环境 `composerxe-2011.3.174`（ifort 12.0.3），装到 `/opt/intel`；`source /opt/intel/bin/compilervars.sh intel64`；自编 openmpi（`./configure --prefix=/opt/openmpi-1.6.5 F77=ifort FC=ifort`）；下载 **CP2K 2.5.1** 源码，改 `arch/Linux-x86-64-intel.popt`：`FC/LD = /opt/openmpi-1.6.5/bin/mpif90`、`INTEL_MKL = /opt/intel/mkl`、`DFLAGS = -D__INTEL -D__FFTSG -D__parallel -D__BLACS -D__SCALAPACK -D__FFTW3 -D__LIBINT`、`FCFLAGS = ... -O2 -xHost -heap-arrays 64 -funroll-loops -fpp -free` |
| **P3** | 续 P2 的 arch 文件：`LIBS = -L$(MKL_LIB) -lmkl_blas95_lp64 -lmkl_lapack95_lp64 -lmkl_scalapack_lp64 -lmkl_intel_lp64 -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -lmkl_blacs_openmpi_lp64 -lfftw3 -lpthread -lderiv -lint -lstdc++`；**关键切换规则：用 intelmpi 就把 blacs 设成 `-lmkl_blacs_intelmpi_lp64`，用 openmpi 设成 `-lmkl_blacs_openmpi_lp64`**；对 4 个文件（`graphcon.o / et_coupling.o / qs_vxc_atom.o / hfx_screening_methods.o`）单独降到 `FCFLAGS2`（`-O1`）编译；`make –j 4 ARCH=Linux-x86-64-intel VERSION=popt`；**"视 CPU 性能，一般 15 分钟左右"** 得 `exe/Linux-x86-64-intel/cp2k.popt`；**GNU+MKL+ELPA 路线**：改 `arch/Linux-x86-64-gfortran_mkl_elpa.popt`（`DFLAGS` 含 `-D__GFORTRAN ... -D__LIBXC2 -D__FFTW3 -D__ELPA`，`LIBS` 含 `-lmkl_gf_lp64 ... -lxc -lelpa`），`make -j 4 ARCH=Linux-x86-64-gfortran_mkl_elpa VERSION=popt` |
| **P4** | 续 P3：`exe/Linux-x86-64-gfortran_mkl_elpa/cp2k.popt`；**实测结论："使用 gfortran 和 intel 编译器编译的 CP2K 可执行文件运行速度相当，后者稍微快一点点"**（因为两者都用了 MKL）。**获取帮助的 5 条途径**（§2.1–2.5）：CP2K Google Group（"这里是最好的获得帮助的地方"、开发者亲自回复）、CP2K 官方教程（`www.cp2k.org/tutorials`、`/events`）、官方手册（`manual.cp2k.org/trunk/`）、**源码包中的测试文件**、相关文献（`manual.cp2k.org/trunk/references.html`）。**本轮最有价值的一条使用告诫**：**"CP2K 的官方手册实际上并不是'手册'，因为这个网站只是解释了各种关键词的含义以及设置，并没有教你如何使用 CP2K"**；**"手册本身是从 CP2K 的源码直接生成的，只要下载了源码就可以在本地生成"** |
| **P5** | **`tests/` 的正确用法**：源码 `tests` 目录含各种方法的输入文件；**"这些输入文件并不是最适合计算的，其中测参数设置没有经过优化"**，但**给了我们了解输入文件结构的途径**；**"学会使用 grep 命令……`grep –iR keyword tests/` 来查看使用了该关键词的测试输入文件"**；**"tests 目录中的输入文件主要是用来测试程序运行的正常与否，往往使用了不合理的参数，用户需要参考手册等其他资料自行进行调整"** |

#### 2.2.2 功能与"影响精度的各种参数"（P5–P10）

| 页 | 要点 |
|---|---|
| **P5** | `RUN_TYPE` 七种（原文）：`BAND`（band 方法做最低能量路径 MEP 与过渡态搜索，常用 CI-NEB、IT-NEB）、`CELL_OPT`（晶胞参数优化）、`ENERGY`（"对于 DFT 来说，就是一个 SCF 计算"）、`ENERGY_FORCE`（能量 + 每个原子的梯度/受力）、`GEO_OPT`（`MINIMIZATION` 优化到极小点 / `TRANSITION_STATE` 用 **Dimer 方法**优化到过渡态）、`MD`（**基于第一原理的分子动力学模拟是 CP2K 的一大优势**，也支持力场与 DFTB）、`VIBRATIONAL_ANALYSIS`（频率，可算部分原子的 `INVOLVED_ATOMS`，也可算某频率范围内的 `MODE_SELECTIVE`） |
| **P6** | ⚠️ 原文此处**又编了一个 "3.1"**（与 P5 的 3.1 重号）。内容：**3.1.1 晶胞大小**——**"CP2K 只支持 Gamma 点的计算，没有 K 点。因此，计算中必须使用足够大的晶胞。如果晶胞太小，部分基组函数就会超过晶胞的边界，导致重叠矩阵求逆过程出现问题，计算就会不可靠。不能直接使用 VASP 中的小晶胞来进行 CP2K 的计算。"**（抽取文本此处有整段重复叠字，是排版强调的假象）**3.1.2 `CUTOFF` 与 `REL_CUTOFF`**——网格从粗到细分 **4 个级别**；`CUTOFF` 控制整体最高精度，`REL_CUTOFF` 控制**有多少网格点落到最精细的级别**；`CUTOFF` **默认 280 Ry**，但有些原子要 500 Ry 甚至更高；**"对包含 Na，N，O，F，Ne，Ni，Ga 等元素的计算，需要设置高达 1000 Ry 的 CUTOFF 来确保计算精度"**，含这些元素要额外小心；`REL_CUTOFF` **默认 50 Ry**，**一般设到 60 Ry 精度就足够了**；另有 **`USE_FINER_GRID`** 等参数用于提高网格精细程度 |
| **P7–P8** | **3.1.3 基组和泛函**：**"CP2K 中可以使用的泛函很多，但并非每个基组都为相应的泛函进行了优化"**；常用泛函 **LDA(PADE)、BLYP、PBE**，"在 CP2K 的 tests 目录中有相应的优化基组"；也可用 **B3LYP、HSE** 等杂化泛函，可用 **DFT-D3** 色散校正。给出 **B3LYP 完整输入**（`&DFT BASIS_SET_FILE_NAME ./BASIS_MOLOPT` / `POTENTIAL_FILE_NAME ./POTENTIAL` / `&SCF SCF_GUESS ATOMIC EPS_SCF 1.0E-6 MAX_SCF 50 &OUTER_SCF MAX_SCF 10` / `&OT PRECONDITIONER FULL_SINGLE_INVERSE MINIMIZER DIIS N_DIIS 7` / `&QS METHOD GAPW EPS_DEFAULT 1.0E-12 EPS_PGF_ORB 1.0E-32 EPS_FILTER_MATRIX 0.0E+0` / `&MGRID COMMENSURATE CUTOFF 300` / `&POISSON POISSON_SOLVER MULTIPOLE PERIODIC NONE &MULTIPOLE RCUT 40` / 手写 B3LYP 的 `&LYP SCALE_C 0.81` `&BECKE88 SCALE_X 0.72` `&VWN FUNCTIONAL_TYPE VWN3 SCALE_C 0.19` `&XALPHA SCALE_X 0.08` + `&HF FRACTION 0.20` / `&XC_GRID XC_SMOOTH_RHO NN10 XC_DERIV SPLINE2_SMOOTH`）与 **HSE 输入**（`&XWPBE SCALE_X -0.25 SCALE_X0 1.0 OMEGA 0.11` + `&PBE SCALE_X 0.0 SCALE_C 1.0`；`&HF EPS_SCHWARZ 1.0E-10 MAX_MEMORY 10 FRACTION 0.25 SCREENING_TYPE SHORTRANGE OMEGA 0.11`） |
| **P9** | 续 3.1.3：**"基组的大小也有很多种，如 SZ，DZVP 以及 TZVP。一般计算中使用 DZVP 基组就足够了。"**（注意原文写 **`SZ`** 而非 `SZV`）**3.1.4 SCF 收敛精度**：一般测试性计算 `1E-5` 就可得相对准确结果；较高精度 `1E-6`；**频率等精度要求更高的计算 `1E-7`**。**3.1.5 收敛算法的选择**：两种——**OT（轨道变换）** 与 **DIAG（对角化）**；**带隙大的半导体/绝缘体推荐 OT**（收敛快）；**HOMO-LUMO 带隙很小或几乎没有的金属体系建议用对角化 + smear**；给出 **Rh(1 1 1) 表面**输入（`SCF_GUESS RESTART`、`EPS_SCF 5.0E-7`、`MAX_SCF 500`、**`ADDED_MOS 500`**、`CHOLESKY INVERSE`、`&SMEAR ON METHOD FERMI_DIRAC ELECTRONIC_TEMPERATURE [K] 300`、`&DIAGONALIZATION ALGORITHM STANDARD`、`&MIXING METHOD BROYDEN_MIXING ALPHA 0.1 BETA 1.5 NBROYDEN 8`）；**"注意使用对角化方法必须使用 `ADDED_MOS` 关键词。另外，设置正确的 MIXING 方案也是加速收敛的关键。"**；**"即使是对于非金属体系，有时候对角化方法也会比 OT 算法速度更快。所以，在进行大规模的计算之前最好进行充分的测试。"** |
| **P10** | 续 3.1.5：**OT 的优化算法**——常用 **CG、DIIS、BROYDEN**；**CG 最稳定**（一般计算都可用），**DIIS 快但不够稳定**，**两者都有问题时试 BROYDEN**；给 BROYDEN 输入（`&OT T MINIMIZER BROYDEN N_HISTORY_VEC 4 BROYDEN_BETA 6.9999999999999996E-01 BROYDEN_SIGMA 1.4999999999999999E-01 LINESEARCH 2PNT PRECONDITIONER FULL_SINGLE_INVERSE`）。**3.1.6 `EPS_DEFAULT`**：QS 部分默认 `1.0E-10`；**Google Group 建议高精度计算要设到 `1.0E-14`**；给出**联动表**（照抄）：`EPS_CORE_CHARGE` = 核电荷映射精度，默认 **`EPS_DEFAULT/100.0`**；`EPS_GVG_RSPACE` = 实空间 KS 矩阵元积分精度，默认 **`SQRT(EPS_DEFAULT)`**；`EPS_PGF_ORB` = 重叠矩阵元精度，默认 **`SQRT(EPS_DEFAULT)`**；`EPS_KG_ORB` = 使用 Kim-Gordon 方法时的精度，默认 **`SQRT(EPS_DEFAULT)`** |

#### 2.2.3 各任务的输入模板（P10–P19）

| 页 | 要点 |
|---|---|
| **P10–P11** | **3.2 能量计算**：`RUN_TYPE ENERGY`；要梯度则 `ENERGY_FORCE`。**3.2.1 `OUTER_SCF`**：给输入（`EPS_SCF 1.0E-6 SCF_GUESS RESTART MAX_SCF 100 &OT T PRECONDITIONER FULL_ALL MINIMIZER DIIS LINESEARCH 3PNT &OUTER_SCF ON MAX_SCF 5 EPS_SCF 5.0E-6`）；**语义解释**："计算过程中，如果 SCF 经过 100 次优化依然没有收敛，则进入 `OUTER_SCF` 过程，对前一次的波函数进行调整，重新进行 SCF 迭代。每次 `OUTER_SCF` 中优化的次数依然是 100 次，最多可以进行 5 次 `OUTER_SCF`。所以，最多可以进行 500 次 SCF 计算。"**3.2.2 输出每个原子上的受力**：`&FORCE_EVAL &PRINT &FORCES ON Filename ForceFileName`；不设文件名则打到 out 文件；给出输出格式样例（`ATOMIC FORCES in [a.u.]` / `# Atom Kind Element X Y Z` / 每行原子受力 / **`SUM OF ATOMIC FORCES`**） |
| **P12** | **3.3 几何优化**：`RUN_TYPE GEO_OPT`；两种——能量极小化（默认）与 **Dimer 过渡态**。**3.3.1** 极小化输入（`&GEO_OPT TYPE MINIMIZATION MAX_ITER 400 OPTIMIZER LBFGS MAX_FORCE 4.0E-4`）；**"几何优化有三种算法，分别是 CG、BFGS 和 LBFGS。其中，CG 算法是最稳定的算法，但计算速度相对较慢；BFGS 算法效率最高，计算中需要对 Hessian 矩阵进行对角化，如果初始结构不合理，BFGS 算法容易出问题；LBFGS 算法效率和 BFGS 类似，同时稳定性也很好。对于一般的几何优化，推荐使用 LBFGS 算法。"**；固定原子用 `&MOTION &CONSTRAINT &FIXED_ATOMS LIST 1 2 3 4 / LIST 12 .. 43 / LIST 76..91`（**原文演示了 `1 2 3 4`、`12 .. 43`、`76..91` 三种 LIST 写法**） |
| **P12–P13** | **3.3.2 Dimer 过渡态**：`&GEO_OPT TYPE TRANSITION_STATE MAX_ITER 400 OPTIMIZER CG` + `&CG &LINE_SEARCH TYPE 2PNT` + `&TRANSITION_STATE METHOD DIMER &DIMER DR 0.01 ANGLE_TOLERANCE [deg] 4.0 INTERPOLATE_GRADIENT &ROT_OPT OPTIMIZER CG MAX_ITER 10 MAX_DR 3.0E-3 MAX_FORCE 4.5E-4`；**"使用 dimer 方法进行过渡态搜索计算时，只能使用 CG 优化算法，不能用 BFGS 或者 LBFGS。"**；**可手工给定初始 Dimer Vector**（指向过渡态方向，提高搜索效率；不给则程序随机设定初值）；文献 **Henkelman & Jónsson, *J. Chem. Phys.*, 111(15), 7010-7022 (1999)** |
| **P13–P14** | **3.4 非周期性体系**：`&POISSON PERIODIC none POISSON_SOLVER wavelet`（原文小写）；若用 MT 则 `&POISSON PERIODIC NONE POISSON_SOLVER MT &MT ALPHA 7.0 REL_CUTOFF 1.2`；**"对于周期性计算，`POISSON_SOLVER` 设置为 PERIODIC；对于非周期性计算，可以设置为 MT 或者 WAVELET，两者略有不同。如果设置为 MT，要保证计算使用的单胞体积足够大，至少是电荷密度的两倍。如果设置为 WAVELET，不需要设置非常大的单胞，但分子必须处于单胞的中心，确保单胞的边界处电子密度为 0。"**；**"可以使用 `TOPOLOGY` 参数来强制将分子置于单胞的中心"**（`&TOPOLOGY &CENTER_COORDINATES`）；**`&CELL` 的周期性也要设为 `NONE`**（`ABC 20.0 20.0 20.0` + `PERIODIC NONE`） |
| **P14–P15** | **3.5 晶胞参数优化**：`RUN_TYPE CELL_OPT` + `&MOTION &CELL_OPT TYPE GEO_OPT OPTIMIZER CG MAX_ITER 200 EXTERNAL_PRESSURE 1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0 PRESSURE_TOLERANCE 0.1 KEEP_ANGLES KEEP_SYMMETRY` + `&CG &LINE_SEARCH TYPE 2PNT`；**"在 `FORCE_EVAL` 部分需要设置 `STRESS_TENSOR` 的计算方法为 `ANALYTICAL`"**；晶胞有特定对称性可在 `&CELL` 加 `SYMMETRY`；算例 `tests/QS/regtest-gpw-4/cell-1.inp` |
| **P15–P16** | **3.6 多重度计算**：必须是**自旋非限制**（`LSD` 或 `UKS`）；两种方案——手写 **`MUTIPLICITY`**（原文如此拼写，"最为简单可靠"）或自动猜测 **`RELAX_MULTIPLICITY`**（输入里写作 **`RELAX_MULTIP`** 并取值 `0.001`）；给完整输入（`&DFT LSD ... &MGRID CUTOFF 300 &QS EPS_DEFAULT 1.0E-14 WF_INTERPOLATION ASPC EXTRAPOLATION_ORDER 3 &SCF ADDED_MOS 50 50 EPS_SCF 5.0E-7 SCF_GUESS RESTART MAX_SCF 200 CHOLESKY INVERSE &DIAGONALIZATION ALGORITHM STANDARD &MIXING BROYDEN_MIXING ALPHA 0.1 BETA 1.5 NBROYDEN 8 &OUTER_SCF ON MAX_SCF 5 EPS_SCF 1.0E-6`）；**4 条使用注意（照抄）**：①**必须自旋非限制（UKS/LSD）**；②**必须用对角化，不能用 OT**，因此**也必须用 `ADDED_MOS`**；③**不能用 SMEAR**；④**`RELAX_MULTIP` 设为大于 0 就开启自旋优化模式，值越大自旋翻转发生概率越大**。结论：**"尽管这种方法看似很诱人，但在使用中很受限制。"** |
| **P16–P17** | **3.7 NEB**：`RUN_TYPE BAND` + `&MOTION &BAND NPROC_REP 32 BAND_TYPE IT-NEB NUMBER_OF_REPLICA 6 K_SPRING 0.02 &CONVERGENCE_CONTROL MAX_DR 0.01 MAX_FORCE 0.001 RMS_DR 0.02 RMS_FORCE 0.0005 ROTATE_FRAMES F &CI_NEB NSTEPS_IT 5 &OPTIMIZE_BAND OPT_TYPE MD OPTIMIZE_END_POINTS T &MD TIMESTEP 0.5 TEMPERATURE 500.0 MAX_STEPS 300 &VEL_CONTROL ANNEALING 0.99 PROJ_VELOCITY_VERLET T` + 6 个 `&REPLICA COORD_FILE_NAME ./1.xyz …`）。**关键词解释表（照抄要点）**：`NPROC_REP` = 每个 REPLICA 使用的 CPU 数；**`BAND_TYPE` 有 `IT-NEB`、`CI-NEB`、`B-NEB`、`D-NEB`、`EB`、`SM` 等多种，推荐 IT-NEB 与 CI-NEB**；`NUMBER_OF_REPLICA` = 总镜像数（越多越准），**CPU 总数 = `NUMBER_OF_REPLICA` × `NPROC_REP`**（本例 32×6=192）；`K_SPRING` — **越大收敛越快但不准、越小收敛越慢但更准**；**"在初步计算中，可以将 `K_SPRING` 设置为 0.08 左右，然后再放松至 0.02 以获得精确结果"** |
| **P18** | **3.8 振动频率分析**：`RUN_TYPE VIBRATIONAL_ANALYSIS` + `&VIBRATIONAL_ANALYSIS DX 0.01 INTENSITIES F NPROC_REP 128 FULLY_PERIODIC T`；**"CP2K 计算频率使用的是数值算法，即对每个原子向 +x, -x, +y, -y, +z, -z 6 个方向分别进行移动……所以，如果有 N 个原子要进行移动，总共要进行 6N+1 次 SCF 收敛计算。"**；关键词表：`DX` 位移步长、`INTENSITIES` 是否算红外强度（设 T 需在 DFT 部分算偶极矩，关键词 **`MOMENTS`**）、`NPROC_REP`、**`FULLY_PERIODIC T` = 避免从 Hessian 矩阵中消除转动模式；开启后对 N 个原子会算出 `3N-3` 个频率，其中包含 3 个转动自由度**；算部分原子频率两条路：`CONSTRAINT` 固定不动的原子，或 **`MODE_SELECTIVE`**（给输入 `&MODE_SELECTIVE ATOMS 82 83 INITIAL_GUESS ATOMIC EPS_NORM 1.0E-5 EPS_MAX_VAL 1.0E-6 &INVOLVED_ATOMS INVOLVED_ATOMS 82 83`）；**REPLICA 数算法 `NREP = 总 CPU 数目 / NPROC_REP`；"如果只使用一个 REPLICA，使用 MODE_SELECTIVE 算法计算频率时，就会只跟踪一个频率，无法得到正确的结果。"** |
| **P19** | **虚频问题（T24 的收尾，也是全文信息量最高的一页）**：**"使用 CP2K 程序计算一个优化好的结构式的频率时，也常会出现多个虚频。这并非是几何优化出现了问题，而是 CP2K 计算使用 GTH 赝势时存在的一个问题。"** 给出 **4 种解决方案（照抄）**：①**使用 NLCC 赝势**（给 arXiv:1212.6011 链接）——**"不过，NLCC 赝势很不完整，只有 B-Cl 的元素有，且只提供了 PBE 泛函的赝势。"**；②**增大 `CUTOFF`，使用 600 Ry 以上**；③**在 `XC_GRID` 部分使用平滑参数 `SMOOTING`（原文拼写）——"不推荐使用"**；④**在 `XC_GRID` 部分使用 `USE_FINER_GRID`**——加上后 **XC 部分格点的精度提高为 `4*CUTOFF`** |

---

## 3. 核心逻辑链（重点）

### 3.1 基组

#### 3.1.1 SZV / DZVP / TZVP / TZV2P 命名法的含义

**T20 P11 原文定义（照抄）**：

- **`SZV`：single-zeta valence**，即**每个轨道一个收缩函数**
- **`DZVP`：double-zeta valence**，即**每个轨道两个收缩函数**，**外加一组 `l = l_max + 1` 的极化函数**
- **`TZVP` / `TZV2P`：triple-zeta valence**，即**每个轨道三个收缩函数**，**外加一 / 两组 `l = l_max + 1` 的极化函数**

**T20 P6 补充了"为什么要极化"**：极化函数是**角动量高于价轨道**的基函数；**第一层极化函数最重要**（H–Be 加 p、B–Ca 加 d）；作用是增加柔性、更好描述成键。
**T20 P7 补充了"另一类函数"**：**弥散函数（小指数）** 描述波函数尾部，对**阴离子/激发态与气相分子**重要——这正是 `SR` 变体要砍掉的东西。

**质量对应关系（T20 P11 表，照抄；原表把 MOLOPT 列与"CP2K All-electron (Gaussian/NWCHEM)"列并排）**：

| MOLOPT（GPW 用） | CP2K 全电子 / Gaussian / NWCHEM（GAPW 用） |
|---|---|
| `SZV` | `STO-3G` |
| `DZVP` | `6-31G*` |
| `TZVP` | `6-311G*` |
| `TZV2P` | `6-311G(2df, 2pd)` |

> ⚠️ **这是"质量档位对应"，不是"同一个基组可以互换"**。T20 表格同页还有 `H-Rn` 与 `limited availability` 两处浮动文字（归属见 §7-2）。
>
> G 层 `23_dft_subpages_full.md` 已记"`SZV`、`DZVP`、`TZVP`、`TZV2P`、`QZVPP` 表示递增的基组质量"，
> **但没有任何一层记过这张与 Pople/NWCHEM 的对应表** → 属本层增量（§5-N6）。

#### 3.1.2 `MOLOPT` 的来历

**T20 给出一条完整的"出身链"，这是其他层完全没有的：**

1. **定位**：MOLOPT = "basis sets optimised from **molecular** calculations"（`T20 P9`），文件是 `BASIS_MOLOPT`。
2. **为什么要专门优化**：基组必须同时满足（`T20 P10`）：成本/精度折中、**可系统改进**（SZV→DZVP→TZVP→TZV2P）、**跨化学环境可迁移**（孤立分子→固体都要能用）、**导向良态重叠矩阵**（线性标度的前提）。
   **"条件数 = 重叠矩阵最大本征值 / 最小本征值之比"**（`T20 P10`）——这是 CP2K 独有的基组设计指标，G/E 层都没有。
3. **优化出来的量是什么**：**高斯指数**（个数在优化前就定死）+ **收缩系数** + 极化函数组数（`T20 P13`、`T20 P15`）。
4. **目标函数**（`T20 P15`、`T20 P16`）：`Ω(α, c) = Δρ_i^{B,M}(α, c) + γ·ln κ(α, c)`，即**"拟合密度差 + 条件数惩罚项"**——由 **Dr Florian Schiffmann** 开发。
   ⇒ 这条式子解释了为什么 MOLOPT 基组**天生不与"密度"以外的东西挂钩**：它是拿"参考完备基组算出来的分子密度"当靶子拟合的。
5. **优化流程**（`T20 P16`、`T20 P17`、`T20 P22`）：
   ① 选**参考（完备）基组**：`GTH-def2-QZVP` / `aug-GTH-def2-QZVP`（收在 `$CP2K/cp2k/data/BASIS_ADMM`），或用 **`ATOM` 码**自己生成未收缩基组（`T20 P17`、`T20 P18`、`T20 P20`）
   ② 用参考基组做**精确分子计算**（所有元素都用参考基组；**避免同核双原子分子**；**用平衡几何，即先 `GEO_OPT`**）
   ③ 选待拟合基组的形式（`&FIT_KIND` + `INITIAL_DEGREES_OF_FREEDOM`）
   ④ 用 `OPTIMIZE_BASIS` 最小化目标函数（`&OPTIMIZATION MAX_FUN`、`&CONSTRAIN_EXPONENTS BOUNDARIES 0.1 20 USE_EXP -1 -1`）
6. **训练集从哪来**（`T20 P14`）：**小分子**、**不同元素 + 不同配位环境**、**每个分子最好只含两种元素（含目标元素）**；现成小分子（带优化几何）见 **Ahlrichs et al., PCCP 7, 3297 (2005) 的 SI**。
7. **文献**：`T20 P10` 与 `T20 P15` 两处都把 MOLOPT 挂在 **VandeVondele & Hutter, *J. Chem. Phys.*, 127, 114105 (2007)** 上。
   ⇒ **这与 F 层 `playbook.md` 对 E 层（`L3 P42` 把 MOLOPT 归给 PRB 54, 1703 (1996)）的纠错完全一致**，构成独立第二证据（§6-1）。

> **对"能不能信 MOLOPT"的实践含义**：MOLOPT 的靶子是**分子密度**，所以它在分子/团簇里最舒服；把同一套基组用于**金属固体**（尤其带 d/f 的过渡金属、镧系）时，**它没有针对固体优化过**——这就是 T20 要额外强调"检查基组收敛"、并推荐固体用 `SR` 变体的原因。

#### 3.1.3 `SR` 的来历与取舍

**T20 只给了一句话，但这句话是全部依据**（`T20 P9`）：

> "**`DZVP-MOLOPT-SR-GTH` for solids（`SR` denotes shorter range, i.e. less and thus less diffuse primitives）**"

拆开就是三步逻辑：

1. **`SR` = shorter range**；实现方式 = **原函数更少（less primitives）**，因此**更不弥散（less diffuse）**；
2. **用途指向固体（solids）**：周期性体系里，弥散函数会**跨胞重叠**、把重叠矩阵推向病态（回扣 `T20 P10` 的条件数标准），还直接抬高平面波/网格成本；
3. **代价**：砍掉弥散 = 牺牲波函数尾部 = **牺牲阴离子/弱束缚/气相分子那部分精度**（回扣 `T20 P7`）。

**与既有层的口径对照**：G 层 `23_dft_subpages_full.md` 已写"`SR` = 短程 MOLOPT 变体，更不弥散，在目标性质不需要弥散函数时对大型凝聚相体系常更高效"；E 层给的是**量化代价**（BSSE 增大 ~50%、提速 2–3 倍）。T20 **不给数字，只给理由**——正好补上"为什么"这一环（§5-N7 之外的逻辑补强）。

#### 3.1.4 为什么不能跨程序搬基组

**T20 没有一节叫这个名字，但全文把理由分散在三处，合起来是完整链条：**

| # | 理由 | T20 依据 |
|---|---|---|
| 1 | **基组的"价电子范围"与赝势绑死** | `T20 P2`：GPW 的高斯基组**只描述价电子**（"Gaussian basis sets for **valence** electrons"）；`T20 P12` 把基组名后缀 `-q1` 直接标注为 **"number of valence electrons in pseudo"**。搬去一个需要全电子（或不同芯定义）的程序，**基组根本没有芯区函数** |
| 2 | **指数与收缩系数是为特定参考密度拟合的** | `T20 P15`/`P16`：拟合靶子是**参考基组算出的分子密度**；换环境/换芯定义后靶子变了，参数不再最优 |
| 3 | **条件数/良态重叠矩阵是 CP2K 特有的硬约束** | `T20 P10`：太弥散或太陡的指数会让 `S` 病态；别的程序的通用基组没按这个标准筛过 |
| 4 | **"质量对应"不等于"同一个基组"** | `T20 P11`：`DZVP ≈ 6-31G*` 只是**档位类比**；把 `DZVP-MOLOPT-GTH` 原样搬到 Gaussian 是把一个"为 GTH 赝势 + 分子密度拟合"的基组当成 Pople 基组用 |
| 5 | **真要搬，必须经过一次"重新适配"** | `T20 P21` 演示了完整过程：从 BSE 取 **'Gaussian 94' 格式** → 转成 CP2K 的 set/指数/系数结构 → **按 `(use exponents between 0.05~20 only)` 过滤指数**（过陡的属于芯区、已被赝势吸收；过弥散的带来病态风险）→ 才成为可用的**参考**基组。⇒ 跨程序流动的合法形态是"**指数来源 + 重新适配**"，不是"**原样搬运**" |

**反方向同理**：`T20 P8` 指出全电子基组（Pople 型、相关一致型）要用于 GAPW 时，**必须在 `&KIND` 里明确 `POTENTIAL ALL`**——即"换了基组类型就必须同时换赝势设置"。

#### 3.1.5 基组与赝势必须配套的理由

1. **算法层面**：GPW 的定义就是 **GTH 赝势 + 价电子高斯基组**（`T20 P2`）。赝势负责芯，基组负责价，**两者共同定义"什么被显式处理"**。
2. **命名层面**：赝势叫 `GTH-PBE-q6`，基组叫 `DZVP-MOLOPT-GTH-q6`——**同一个 `q6` 是它们配对的显式契约**（`T20 P12` 把 `q1` 标为 "number of valence electrons in pseudo"；`T20 P27` 把 `q12` 标为 "Number of valence electrons"）。G 层 `14_basis_and_potentials.md` §3.4 有官方同义表述（**只写指针**）。
3. **泛函层面**：赝势**按泛函分族生成**（`T20 P28`：LDA(PADE)/PBE/PBEsol/BP/HCTH…），基组**也按泛函优化**——`T24 P6` 明确"**并非每个基组都为相应的泛函进行了优化**"，`T20 P9` 要求"**always check the basis set convergence**"。⇒ 三者（基组 / 赝势 / 泛函族）是**一个绑定组**。
4. **可验证层面**：`T20 P29` 说明赝势的质量标准是"**在全电子原子与赝原子的原子球内，本征值与电荷之差最小**"——**如果基组与赝势不配套，这个"赝原子"根本没被定义**，误差无从谈起。

### 3.2 赝势

#### 3.2.1 GTH 赝势的结构（`T20 P25`–`P27`）

- **局域部分**（`T20 P25`）：**离子电荷的误差函数长程项** + **短程项** + 系数；**`r_loc` = 高斯离子电荷分布的宽度**。
- **非局域部分**（`T20 P26`）：**高斯型投影子（Gaussian-type projectors）** + 系数 + 归一化常数 + 球谐函数 + 半径。
- **文件格式**（`T20 P27`，照抄见 §4.3）：`元素名` + `GTH-<XC>-qN` + 泛函族名；下一行 `4 6 2` = **"Number of valence electrons in each shell (s/p/d)"`；随后是 `r_loc` 行与每个 `l` 的投影子块（`r_l` + **"number of non-local projectors"** + 系数）。
- **可核对的一致性**：`Ti` 的 `4 6 2` ⇒ 4+6+2 = **12** = `GTH-PBE-q12` 的 q 值；而 `T20 P22` 页脚自己写了 Ti 的电子组态 **`[Ne] 3s2 3p6 4s2 3d2`** ⇒ s 壳 3s²+4s²=4、p 壳 3p⁶=6、d 壳 3d²=2。**两处完全对上**。（此项为本文档按文档内证据做的核对，已标注。）

#### 3.2.2 价电子数 q 怎么选

**T20 直接给的（可引用）**：

- `q` 的语义 = **显式处理的价电子数**（`T20 P12` 的 `-q1` 标签、`T20 P27` 的 `Number of valence electrons`）；
- **q 由"哪些壳层算价电子"决定，就写在赝势文件第二行**（`T20 P27` 的 `4 6 2`）；
- **T20 文档内出现的三个 q 实例**（照抄）：`GTH-PBE-q9` for **Na**（`T20 P18`，同时写 `CORE 1s2` ⇒ Na 的 2s2p 被算作价）、`GTH-PBE-q6` for **O**（`T20 P30`，同时写 `CORE [He]`、`ELECTRON_CONFIGURATION [He] 2s2 2p4`）、`GTH-PBE-q12` for **Ti**（`T20 P27`，`CORE` 未写但 `4 6 2` 反推为 `[Ne]` 芯）；
- **q 的可用组合由官方数据文件决定**：清单查 G 层 `14_basis_and_potentials.md` §4.2（**本轮不重复**）；T20 只给"按泛函的元素覆盖范围"（`T20 P28`，见 §2.1.5）。

**"大核 vs 小核"的取舍**——**诚实标注**：

> ⚠️ **T20 全文没有写"大核 / 小核"这段取舍文字**。G 层 `14_basis_and_potentials.md` §3.8 第 4 条记录了官方的一致性检查要求
> （"For heavy elements, decide whether a **large-core, medium-core, small-core, or all-electron** description is appropriate
> for the property of interest"），**但官方也只说"要判断"，没给判据**。
> 下面 ①②③ 是**本文档由 T20 的格式与实例推出的**（标注为推断，不是教材原文）；④ 是 T20 原文。

- ① **q 小 ⇒ 大核**：芯电子被赝势吸收，显式电子少、便宜、网格好收敛；代价是**"半芯态"（如 3s3p、4f、5d）被埋进赝势**，而这些态在化学/谱学里常常是主角。
- ② **q 大 ⇒ 小核**：把半芯态提升为价电子（Ti 的 `3s2 3p6` 就是被显式处理的：`4 6 2` 里 s=4 含 3s²、p=6 就是 3p⁶），代价是电子数、基组尺寸、`CUTOFF` 都要上去。
- ③ **T20 的教学立场是"你可以自己造一套"**：`P16`–`P22` 整套 `ATOM` + `OPTIMIZE_BASIS` 流程，就是"当现成的 q/基组组合不满足需要时，自己拟合一对配套的基组+赝势"。这**暗示了 q 的选择标准是"目标性质需要哪些态参与"**，而不是照抄别人的 q。
- ④ **T20 原文能直接支持的一条硬约束**：`P28` 说 **PBE 只到 H–Rn 且不含镧系**、**LDA(PADE) 才含镧系**（照抄见 §2.1.5）。⇒ 对镧系体系，**用 PBE + GTH 这条路本身就受限**，这不是"选大核小核"能解决的（**该条与 G 层并列见 §6-10**）。

#### 3.2.3 赝势与全电子 / GAPW 的关系

`T20 P2` 一句话定了分野，`T20 P8` 给了落点：

| 路线 | 电子处理 | 基组 | 赝势设置 | 文件/条目 |
|---|---|---|---|---|
| **GPW** | 价电子显式 + 芯被赝势吸收 | 价电子高斯基组（`MOLOPT` 等） | `GTH-<XC>-qN` | `POTENTIAL` / `GTH_POTENTIALS` |
| **GAPW** | **all electron** | **全电子基组**（Pople `6-31G*`、相关一致 `aug-cc-pVDZ` …） | **`POTENTIAL ALL`**（写在 `&KIND` 里） | `ALL_BASIS_SETS` / `EMSL_BASIS_SETS` / `POTENTIAL` 里的 "ALL" |

**逻辑后果（这是本轮最值得写进决策库的一条）**：
"**q 怎么选**"**只在 GPW 路径上有意义**；一旦目标是全电子（如芯能级谱），问题就从"选哪个 q"变成"**换 GAPW + `POTENTIAL ALL` + 全电子基组**"，
而且**必须整套换**（`T20 P8` 明确 "Potential needs to be defined in `&KIND` section **for GAPW calculations**"）。
G 层 `14_basis_and_potentials.md` §3.7 有官方同义三件套表述（**只写指针**）；`21_xray_spectroscopy_full.md` 已有"被激发原子必须用全电子基组"的实例（**只写指针**）。

#### 3.2.4 赝势也是"人造的"，而且按泛函造

`T20 P28`（覆盖范围）+ `T20 P29`（优化流程）合起来说明：

- 赝势**不是唯一真值**，而是**"选定泛函下的拟合产物"**：先用该泛函做全电子计算，再让赝原子的**本征值与原子球内电荷**去逼近全电子结果；
- 所以 **泛函换了，赝势严格来说也该换**（`T24 P6` 从另一侧说了同一件事："并非每个基组都为相应的泛函进行了优化"）；
- 所以 **`q` 与基组后缀必须形成闭环**（§3.1.5）；
- 所以 **"赝势质量"是可检查的**：`T20 P32` 指向 `$CP2K/potentials/README_quick_GTH`，并说独立 `ATOM` 码"**质量检查有更多选项**"。

### 3.3 T24 讲的"上手路径"——提炼成新手可执行清单

> 下面每条都能指到 T24 页码。"【推断】"标记的是本文档为了让清单可执行而补的连接动作，不是 T24 原文。

#### 阶段 0 · 装（`T24 P1`–`P4`）

- [ ] **先试最省事的路**：发行版软件源预编译（Debian / Fedora / Ubuntu）或官网预编译二进制（`sourceforge.net/projects/cp2k/files/precompiled/`）——**"运行比较可靠"**，代价是慢（`T24 P1`）。
- [ ] **要速度再自编**：准备 **Intel 编译器 + MKL**（或 GNU + MKL + ELPA），改 `arch/` 文件，`make -j 4 ARCH=... VERSION=popt`，**约 15 分钟**出 `cp2k.popt`（`T24 P2`–`P3`）。
  **T24 自报的收益**：Intel+MKL 版 ≈ 预编译版的 **3 倍**（`T24 P1`）；而 GNU+MKL 版与 Intel 版**基本持平**（`T24 P4`）。
  【推断】⇒ 新手**先跑通再优化**：先用预编译版验证流程，自编留到有稳定机时需求时再做。
  【提醒】T24 的 arch-file/`make` 流程是**旧版 CP2K 的做法**；现代 CP2K 用 CMake / toolchain 脚本，见 G 层 `09_build_libraries.md`（**指针**，且 §6-5 记录了"预编译版是否慢 3 倍"的口径冲突）。

#### 阶段 1 · 找资料的正确姿势（`T24 P4`–`P5`）

- [ ] **手册的定位**：`manual.cp2k.org` **"实际上并不是手册……只是解释了各种关键词的含义以及设置，并没有教你如何使用 CP2K"**；它是**从源码生成的**，所以**本地也生成得出来**（`T24 P4`）。
  【推断】⇒ 用法：**遇到"这个关键词什么意思/默认值多少"→ 查手册**；遇到"我该怎么组织一次计算"→ 查官方 tutorial / howto（H 层）。
- [ ] **`tests/` 的定位**：`grep –iR <keyword> tests/` 是**学新关键词的最快路径**，但 **"往往使用了不合理的参数"**，**只用来学输入结构、参数要自己按手册调整**（`T24 P5`）。
- [ ] **卡住时**：CP2K Google Group（"这里是最好的获得帮助的地方"，开发者亲自回复）（`T24 P4`）。
  【推断】⇒ 国内环境按 E 层/B 层的替代方案（列在 `playbook.md`）。

#### 阶段 2 · 第一次计算（最小闭环）

- [ ] **第一步只做 `RUN_TYPE ENERGY`**（"对于 DFT 来说，就是一个 SCF 计算"）（`T24 P5`）。
- [ ] **建胞先看尺寸**：CP2K 用 Γ 点，**胞必须足够大**——"如果晶胞太小，部分基组函数就会超过晶胞的边界，导致重叠矩阵求逆过程出现问题，计算就会不可靠"；**"不能直接使用 VASP 中的小晶胞"**（`T24 P6`）。
- [ ] **定网格**：`CUTOFF`（默认 **280 Ry**；含 Na/N/O/F/Ne/Ni/Ga 要 **1000 Ry** 才够）+ `REL_CUTOFF`（原文默认 **50 Ry**，**设 60 Ry 一般就够**）（`T24 P6`）。
- [ ] **定基组/泛函**：常用 **LDA(PADE) / BLYP / PBE**（tests 里有相应优化基组）；**"一般计算中使用 DZVP 基组就足够了"**（`T24 P7`–`P9`）。
- [ ] **定 SCF 路线**：**有带隙（半导体/绝缘体）→ OT**；**金属/近零带隙 → 对角化 + `SMEAR`**，且**必须 `ADDED_MOS`**、**MIXING 是加速收敛的关键**（`T24 P9`）。
- [ ] **定阈值**：`EPS_SCF` —— 试算 `1E-5`、常规 `1E-6`、**频率类 `1E-7`**（`T24 P9`）；`EPS_DEFAULT` 默认 `1E-10`，**高精度按 Google Group 建议设 `1E-14`**（`T24 P10`）。
- [ ] **给收敛兜底**：`&OUTER_SCF ON`（"最多 5 次外圈 × 每次 100 步 SCF"）（`T24 P11`）。

#### 阶段 3 · "跑通了"的判据（从 T24 各节可提取的验证动作）

- [ ] **能量 + 受力**：把 `RUN_TYPE` 设成 `ENERGY_FORCE`，在 `&FORCE_EVAL &PRINT &FORCES` 里打印；**T24 给了输出该长什么样**（`ATOMIC FORCES in [a.u.]` 表头 + `SUM OF ATOMIC FORCES` 行）——**能对上这个格式 = 真的跑起来了**（`T24 P11`）。
- [ ] **几何优化收敛**：`&GEO_OPT TYPE MINIMIZATION`，看 `MAX_FORCE`（示例 `4.0E-4`）等判据是否达标（`T24 P12`）。
- [ ] **非周期体系**：`PERIODIC NONE` 要**同时**写在 `&POISSON` 和 `&CELL` 两处，并配 `POISSON_SOLVER WAVELET`（+ `TOPOLOGY CENTER_COORDINATES` 把分子居中）或 `MT`（`T24 P13`–`P14`）。
- [ ] **晶胞优化**：`RUN_TYPE CELL_OPT` 必须配 `FORCE_EVAL` 的 `STRESS_TENSOR ANALYTICAL`（`T24 P14`–`P15`）。
- [ ] **频率**：算完先数虚频；**同时记住 T24 的告警**——"优化好的结构算频率**常出现多个虚频**，这并非几何优化出问题，而是 **GTH 赝势下的已知问题**"，处置见 P19 的 4 条（§6-8/§6-9）。

#### 阶段 4 · 新手最容易踩的 4 个坑（T24 明写的）

1. **把 VASP 的小晶胞搬过来**（`T24 P6`）。
2. **对角化忘了 `ADDED_MOS`**（`T24 P9`）。
3. **开 `RELAX_MULTIPLICITY` 却还想用 OT / SMEAR**——四个限制里两条直接冲突（`T24 P15`–`P16`）。
4. **以为 tests 里的参数可以直接投产**（`T24 P5`）。

---

## 4. 可执行要点（输入片段 / 命名规则 / 查文件的方法，照抄）

### 4.1 "查文件"的方法清单（全部出自 T20）

| 想查什么 | 去哪 | 出处 |
|---|---|---|
| 全电子基组（GAPW 用） | `$CP2K/cp2k/data` 的 **`ALL_BASIS_SETS`**、**`EMSL_BASIS_SETS`**；更多去 EMSL BSE（`https://bse.pnl.gov/bse/portal`） | `T20 P8` |
| GAPW 的"全电子"赝势条目 | `$CP2K/cp2k/data/POTENTIAL`，**选 "ALL" potential** | `T20 P8` |
| GPW 的分子优化基组 | **`BASIS_MOLOPT`**（固体用 `*-SR-*`） | `T20 P9` |
| 配 GTH 赝势的其它基组 | **`BASIS_ZIJLSTRA`**、**`GTH_BASIS_SETS`** | `T20 P9` |
| 基组/赝势总目录 | `$CP2K/cp2k/data` | `T20 P9`、`P28` |
| 赝势（按泛函） | `$CP2K/cp2k/data` 的 **`POTENTIAL`**、**`GTH_POTENTIALS`**、**`NLCC_POTENTIALS`** | `T20 P28` |
| **参考（完备）基组**（做基组拟合的靶子） | **`$CP2K/cp2k/data/BASIS_ADMM`** 里的 **`GTH-def2-QZVP`**、**`aug-GTH-def2-QZVP`** | `T20 P17` |
| `ATOM` 码的示例 | `$CP2K/cp2k/tests/ATOM` | `T20 P17` |
| 未收缩基组/赝势优化的算例 | `$CP2K/cp2k/tests/ATOM/regtest-pseudo` | `T20 P30` |
| `OPTIMIZE_BASIS` 的算例 | `$CP2K/cp2k/tests/QS/regtest-optbas` | `T20 P22` |
| BSSE 的算例 | `$CP2K/cp2k/tests/QS/regtest-gpw-3` | `T20 P24` |
| 从零做 GTH 赝势的快速指南 | **`$CP2K/potentials/README_quick_GTH`** | `T20 P32` |
| 训练分子（带优化几何） | Ahlrichs et al., *PCCP* **7**, 3297 (2005) 的 Supporting Information | `T20 P14` |

> 【对照 G 层】G 层 `14_basis_and_potentials.md` §5 记的官方工具是 **cp2k-basis / Basis Set Exchange / GTH 参数下载页**；
> T20 补的是**安装目录内的文件级路径**（`data/` 与 `tests/` 与 `potentials/`），两者互补。

### 4.2 MOLOPT 基组文件格式（`T20 P12`，**照抄**）

```
element        basis set name      number of valence electrons in pseudo
H              DZVP-MOLOPT-GTH     DZVP-MOLOPT-GTH-q1
1                                  number of CGTO contraction coefficients
2  0  1  7  2  1
   11.478000339908    0.0249162432   -0.0125124214    0.0245109182
    3.700758562763    0.0798254900   -0.0564490711    0.0581407941
    1.446884268432    0.1288626753    0.0112426847    0.4447094985
    0.716814589696    0.3794488946   -0.4185875483    0.6462079731
    0.247918564176    0.3245524326    0.5903632167    0.8033850182
    0.066918004004    0.0371481214    0.4387031330    0.8929712087
    0.021708243634   -0.0011251955   -0.0596931713    0.1201013165
Gaussian exponents | s-function | p-function
```

**同页给出的字段标签（照抄，按 `2 0 1 7 2 1` 六个数从左到右）**：

| 位置 | T20 标签 |
|---|---|
| 1 | **principle quantum number**（原文拼写） |
| 2 | **minimum angular momentum quantum number** |
| 3 | **maximum angular momentum quantum number** |
| 4 | **number of Gaussian exponents** |
| 5 | **number of s-function** |
| 6 | **number of p-function** |

**列语义**：一行 = `Gaussian exponent` + `n_s` 个 s 收缩系数 + `n_p` 个 p 收缩系数（例中 `7 2 1` ⇒ 每行 1 + 2 + 1 = **4 个数**，与照抄的行完全一致）。

**一致性核对（本文档所做，标注为核对）**：
- 对照 **`T20 P20` 的 Na CBS**：头行 `2 0 2 1 1 1 1` —— 7 个数，因为 `l_max = 2` ⇒ 需要 `n_s n_p n_d` 三个收缩数（`4 + (l_max − l_min + 1) = 7`）。
  ⇒ 与 G 层 `14_basis_and_potentials.md` §2.3 官方解释的 6 字段版（`3 0 1 4 2 2`，`l_max = 1`）**同构**。
- 对照 **`T20 P22` 的 Ti FIT10**：头行标 **10 个 set**，正文恰好是 **4 s（`1 0 0 1 1`）+ 3 p（`1 1 1 1 1`）+ 3 d（`1 2 2 1 1`）= 10** ✔
- 对照 **`T20 P21` 的 `H GTH-def2-QZVP`**：头行标 **12 个 set**，正文恰好是 **6 s + 3 p + 2 d + 1 f = 12** ✔

> ⚠️ `T20 P12` 首字段值为 **2**，而 H 的主量子数应为 1；且抽取文本里有一行孤立的 `1  number of CGTO contraction coefficients`。
> 疑为抽取把"set 数"行与 set 头行合并/错位 → 见 §7-1（**G 层官方说明"CP2K 忽略该数字"，故不影响使用**）。

### 4.3 GTH 赝势文件格式（`T20 P27`，**照抄**）

```
Element   Name                Number of valence electrons
Ti        GTH-PBE-q12         GTH-PBE
4  6  2
                              Number of valence electrons in each shell (s/p/d)

r_loc
0.38000000     2      8.71144218    -0.70028677
r_s
0.33777078     2      2.57526386     3.69297065    -4.76760461
r_p
0.24253135     2     -4.63054123     8.87087502   -10.49616087
r_d
0.24331694     1     -9.40665268
        ↑                    ↑
number of potential        coefficients
functions / non-local projectors
```

**字段标签（照抄）**：`Element`、`Name`、`Number of valence electrons`、**`Number of valence electrons in each shell (s/p/d)`**、`r_loc`、
**`number of non-local projectors`**、`number of potential functions`、`coefficients`。

**一致性核对（本文档所做）**：`4 6 2` ⇒ 12 = `q12`；与 `T20 P22` 页脚自注的 Ti 组态 `[Ne] 3s2 3p6 4s2 3d2` 逐壳对上（s=4、p=6、d=2）。
且三个非局域块的投影子数 `2 / 2 / 1` 与 `r_s / r_p / r_d` 三个通道一一对应。

### 4.4 `ATOM` 码做基组/赝势优化（`T20 P18`、`P30`，**照抄**）

**(a) 生成 Na 的未收缩基组（`T20 P18`）**

```
&GLOBAL
  PROJECT Na
  PROGRAM_NAME ATOM
&END GLOBAL
&ATOM
  ELEMENT Na
  RUN_TYPE BASIS_OPTIMIZATION
  ELECTRON_CONFIGURATION CORE 2s2 2p6 3s1
  CORE 1s2
  MAX_ANGULAR_MOMENTUM 1
  &METHOD
    METHOD_TYPE KOHN-SHAM
    &XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL
    &END XC
  &END METHOD
  &OPTIMIZATION
    EPS_SCF 1.e-8
  &END OPTIMIZATION
  &PP_BASIS
    NUM_GTO 6 6
    S_EXPONENTS 7.92602574 5.92602574 1.59655262 0.71279902 0.28969807 4.00675308
    P_EXPONENTS 7.92602574 5.92602574 1.59655262 0.71279902 0.28969807 4.00675308
  &END PP_BASIS
  &POTENTIAL
    PSEUDO_TYPE GTH
    POTENTIAL_FILE_NAME POTENTIAL
    POTENTIAL_NAME GTH-PBE-q9
  &END POTENTIAL
  &POWELL
    ACCURACY 1.e-8
    STEP_SIZE 1.0
  &END POWELL
&END ATOM
```
> 两处疑点（§7-3、§7-4）：`S/P_EXPONENTS` 末值不单调、`ELECTRON_CONFIGURATION CORE 2s2 ...` 疑为下一行 `CORE` 误并入，均疑为抽取错位，**照抄未改**。

**(b) 优化 O 的赝势（泛函 PBE0）（`T20 P30`）**

```
&GLOBAL
  PROGRAM_NAME ATOM
&END GLOBAL
&ATOM
  ELEMENT O
  RUN_TYPE PSEUDOPOTENTIAL_OPTIMIZATION
  ELECTRON_CONFIGURATION [He] 2s2 2p4
  CORE [He]
  MAX_ANGULAR_MOMENTUM 2
  COULOMB_INTEGRALS ANALYTIC
  EXCHANGE_INTEGRALS ANALYTIC
  &METHOD
    METHOD_TYPE KOHN-SHAM
    RELATIVISTIC DKH(2)
    &XC
      &XC_FUNCTIONAL PBE0
      &END XC_FUNCTIONAL
    &END XC
  &END METHOD
  &OPTIMIZATION
    EPS_SCF 1.e-10
  &END OPTIMIZATION
  &PRINT
    &BASIS_SET
    &END
  &END
  &AE_BASIS
    BASIS_TYPE GEOMETRICAL_GTO
  &END AE_BASIS
  &PP_BASIS
    BASIS_TYPE GEOMETRICAL_GTO
  &END PP_BASIS
  &POTENTIAL
    PSEUDO_TYPE GTH
    POTENTIAL_FILE_NAME POTENTIAL
    POTENTIAL_NAME GTH-PBE-q6
  &END POTENTIAL
  &POWELL
    ACCURACY 1.e-10
    STEP_SIZE 0.5
    WEIGHT_PSIR0 0.1
  &END POWELL
&END ATOM
```

### 4.5 `OPTIMIZE_BASIS` 拟合基组（`T20 P22`，**照抄**）

```
&GLOBAL
  PROJECT optbas
  PROGRAM_NAME OPTIMIZE_BASIS
  PRINT_LEVEL HIGH
&END GLOBAL
&OPTIMIZE_BASIS
  BASIS_TEMPLATE_FILE BASIS_SET_TEMPLATE
  BASIS_WORK_FILE WORK_BASIS_STRUCTURE
  BASIS_OUTPUT_FILE Ti_FIT10
# USE_CONDITION_NUMBER Y
# CONDITION_WEIGHT 0.0005
  WRITE_FREQUENCY 10
  &OPTIMIZATION
    MAX_FUN 50000
  &END OPTIMIZATION
  &TRAINING_FILES
    DIRECTORY ../ticl4
    INPUT_FILE_NAME ticl4.inp
  &END TRAINING_FILES
  &FIT_KIND Ti
    BASIS_SET FIT10
    INITIAL_DEGREES_OF_FREEDOM EXPONENTS
    &CONSTRAIN_EXPONENTS
      BOUNDARIES 0.1 20
      USE_EXP -1 -1
    &END CONSTRAIN_EXPONENTS
  &END FIT_KIND
&END OPTIMIZE_BASIS
```

**同页给出的拟合结果 `Ti FIT10`（10 个 set，指数照抄）**：

| 组 | set 头行 | 指数 |
|---|---|---|
| s-functions | `1 0 0 1 1` | `0.10001966`、`1.06186104`、`0.40963197`、`4.39901876` |
| p-functions | `1 1 1 1 1` | `0.52985233`、`1.57394040`、`11.83843422` |
| d-functions | `1 2 2 1 1` | `0.25675246`、`1.02358115`、`4.21355677` |

> 对照 `T20 P17` 的三条要求，本例的训练体系是 **TiCl₄**（`&TRAINING_FILES DIRECTORY ../ticl4`），
> 符合"**避免同核双原子分子**"（TiCl₄ 是 Ti+Cl 两种元素）；`&CONSTRAIN_EXPONENTS BOUNDARIES 0.1 20`
> 是"指数窗口"（与 `T20 P21` 的 `0.05~20` 口径不同，见 §7-6）。

### 4.6 BSSE（`T20 P24`，**照抄骨架**）

```
&GLOBAL
  PROJECT_NAME project
  RUN_TYPE BSSE
&END GLOBAL
…
&FORCE_EVAL
  …
  &BSSE
    &FRAGMENT
      LIST 1..272
    &END FRAGMENT
    &FRAGMENT
      LIST 273..368
    &END FRAGMENT
  &END BSSE
  …
  SCF_GUESS ATOMIC
  …
  &KIND H_ghost
    BASIS_SET DZVP-MOLOPT-SR-GTH
    GHOST
  &END KIND
  …
```

> G 层 `18_posthf_semiempirical_and_xray.md` §2.9 已记官方**两种方案**（自动 `FORCE_EVAL/BSSE`、手动 `KIND/GHOST`）→ **只写指针**；
> 本文档保留的增量是**这段可直接抄的骨架**与 `LIST` 的**起止区间写法**（`1..272` / `273..368`）。

### 4.7 T24 中最值得抄的片段（既有层缺或写法不同的）

**(a) 非周期体系三件套（`T24 P13`–`P14`）**

```
&POISSON
  PERIODIC none
  POISSON_SOLVER wavelet
&END POISSON
```
或
```
&POISSON
  PERIODIC NONE
  POISSON_SOLVER MT
  &MT
    ALPHA 7.0
    REL_CUTOFF 1.2
  &END MT
&END POISSON
```
```
&TOPOLOGY
  &CENTER_COORDINATES
  &END CENTER_COORDINATES
&END TOPOLOGY
```
```
&CELL
  ABC 20.0 20.0 20.0
  PERIODIC NONE
&END CELL
```

**(b) 只把分子居中 → 用 `MODE_SELECTIVE` 算局部频率（`T24 P18`）**

```
&VIBRATIONAL_ANALYSIS
  NPROC_REP 16
  DX 0.01
  INTENSITIES T
  &MODE_SELECTIVE
    ATOMS 82 83
    INITIAL_GUESS ATOMIC
    EPS_NORM 1.0E-5
    EPS_MAX_VAL 1.0E-6
    &INVOLVED_ATOMS
      INVOLVED_ATOMS 82 83
    &END INVOLVED_ATOMS
  &END &MODE_SELECTIVE
&END VIBRATIONAL_ANALYSIS
```
> 配套算式（原文）：**`NREP = 总 CPU 数目 / NPROC_REP`**；**只有一个 REPLICA 时 `MODE_SELECTIVE` 只跟踪一个频率，结果不正确**。

**(c) NEB 关键词速查（`T24 P17`，照抄，此表比既有层多出若干枚举）**

| 关键词 | 示例值 | T24 的解释 |
|---|---|---|
| `NPROC_REP` | `32` | 每个 REPLICA 使用的 CPU 数目 |
| `BAND_TYPE` | `IT-NEB` | **有 `IT-NEB`、`CI-NEB`、`B-NEB`、`D-NEB`、`EB`、`SM` 等多种；推荐 `IT-NEB` 与 `CI-NEB`** |
| `NUMBER_OF_REPLICA` | `6` | 镜像总数；越多越准；**CPU 总数 = `NUMBER_OF_REPLICA` × `NPROC_REP`**（本例 32×6=192） |
| `K_SPRING` | `0.02` | 越大收敛越快但不准、越小越慢但准；**初步计算设 `0.08` 左右，再放松至 `0.02`** |

**(d) 自动多重度（`T24 P15`–`P16`，**照抄其 4 条限制**）**

必须 `LSD`/`UKS`；必须对角化（**不能用 OT**）hence 必须 `ADDED_MOS`；**不能 `SMEAR`**；`RELAX_MULTIP > 0` 即开启自旋优化，**值越大自旋翻转概率越大**。
输入里该关键词写作 **`RELAX_MULTIP 0.001`**。

**(e) 能量+受力跑通判据（`T24 P11`，照抄输出格式）**

```
ATOMIC FORCES in [a.u.]
# Atom Kind Element  X  Y  Z
1  1  O   0.08722700 -0.04704030  0.08194080
2  2  H  -0.07829459  0.00721899 -0.00996929
3  2  H  -0.01049003  0.03981616 -0.06774948
SUM OF ATOMIC FORCES  -0.00155761 -0.00000516  0.00422203  0.00450019
```

### 4.8 命名规则速查（全部照抄 T20/T24，未做"凭记忆的纠正"）

| 记号 | 来源页 | 原文含义 |
|---|---|---|
| `SZV` | `T20 P9`、`P11` | single-zeta valence（每轨道 **1** 个收缩函数）；**production run 不要用** |
| `DZVP` | `T20 P11` | double-zeta valence（每轨道 **2** 个收缩函数 + **1** 组 `l = l_max + 1` 极化） |
| `TZVP` / `TZV2P` | `T20 P11` | triple-zeta valence（每轨道 **3** 个收缩函数 + **1 / 2** 组极化） |
| `MOLOPT` | `T20 P9` | "basis sets optimised from **molecular** calculations"，文件 `BASIS_MOLOPT` |
| `SR` | `T20 P9` | **shorter range**，即 **less and thus less diffuse primitives**；**for solids** |
| `-qN`（基组名后缀） | `T20 P12` | **number of valence electrons in pseudo** |
| `GTH-PBE-qN` | `T20 P27` | `qN` = **Number of valence electrons**；下一行 `x y z` = 各壳层（s/p/d）价电子数 |
| `GTH` | `T20 P25`–`P28` | Goedecker-Teter-Hutter 赝势；局域项含 `r_loc`（高斯离子电荷分布宽度） |
| `SZ`（T24 的写法） | `T24 P9` | T24 写的是 **`SZ`** 而非 `SZV`；T20 与 G 层一律作 `SZV` — 见 §7-11 |
| `DZVP-MOLOPT-SR-GTH` | `T20 P9`、`P24` | 固体/大体系最常用的 GPW 基组名（照抄） |
| `DZVP-MOLOPT-GTH` | `T20 P12` | H 的示例基组名（照抄） |
| `GTH-def2-QZVP` / `aug-GTH-def2-QZVP` | `T20 P17`、`P21` | 用作基组拟合的**参考（完备）基组**，收在 `BASIS_ADMM` |

---

## 5. 【新】相对既有 A–G 层的增量（先 grep 确认）

> **确认方式**：对本仓库 `references/**/*.md` 做 ripgrep（关键词：`OPTIMIZE_BASIS`、`BASIS_ADMM`、`def2-QZVP`、
> `Ahlrichs`、`GEOMETRICAL_GTO`、`WEIGHT_PSIR0`、`DKH`、`STO-3G`、`6-31G`、`6-311G(2df`、`RUN_TYPE BSSE`、`&BSSE`、`GHOST`、
> `condition number`/`条件数`、`EPS_GVG_RSPACE`、`RELAX_MULTIPLICITY`、`USE_FINER_GRID`、`POISSON_SOLVER`、`LBFGS`、`DIMER` 等）。
> **判定规则**：命中即视为已覆盖 → **只写指针**；未命中或只有"标题级登记" → 记为增量。

### 5.1 只写指针（G 层/他层已覆盖，本文档不重复）

| 内容 | 去哪儿 |
|---|---|
| BASIS_SET 文件格式逐行/逐字段官方解释、基函数总数公式、第 1 个数字被 CP2K 忽略 | G `14_basis_and_potentials.md` §2 |
| `qN` 含义 + 基组后缀必须匹配 | G `14_basis_and_potentials.md` §3.4 |
| `POTENTIAL` **关键字** vs `POTENTIAL` **段** | G `14_basis_and_potentials.md` §3.3 |
| 赝势必须与泛函族匹配（官方原文） | G `14_basis_and_potentials.md` §3.5 |
| CP2K 自带 5 个赝势库文件的分工 + UZH 协议优先 | G `14_basis_and_potentials.md` §3.6 |
| `POTENTIAL ALL` + `-ae` 基组 + GAPW 三件套 | G `14_basis_and_potentials.md` §3.7 |
| 基组/赝势一致性检查 4 条（含大核/小核判断要求） | G `14_basis_and_potentials.md` §3.8 |
| **GTH 完整元素→qN 清单** | G `14_basis_and_potentials.md` §4.2（**本轮绝不重复**） |
| GTH 三篇原始文献 | G `14_basis_and_potentials.md` §4.3 |
| BSSE 的**自动/手动两种官方方案** | G `18_posthf_semiempirical_and_xray.md` §2.9 |
| `SZV/DZVP/TZVP/TZV2P` 质量递增、`MOLOPT`/`SR` 语义 | G `23_dft_subpages_full.md`；B 层 `course_learned.md`；E 层 `learn_L3.md` |
| BSSE 的**量化数值**（DZVP ≈5 kcal/mol、SR 增大 ~50%） | A 层 `decide.md §28.2`、F 层 `playbook.md`（**本文档不复述数字**） |
| CUTOFF / REL_CUTOFF 收敛流程 | G `03_scf_convergence.md` §2 |
| OT vs 对角化、`ADDED_MOS`、`&SMEAR` | G `02_dft_methods.md` §3；A 层 `decide.md §22` |
| `OUTER_SCF` 机制 | G `03_scf_convergence.md` §1.4；G `23_dft_subpages_full.md` |
| `POISSON_SOLVER` 选择原则 | G `23_dft_subpages_full.md`；G `00_map.md` |
| `RUN_TYPE` **完整 29 项枚举** | G `01_global_and_units.md` §3（T24 只列 7 项） |
| B3LYP / HSE 输入骨架 | D 层 `sections.md` |
| Dimer 过渡态输入骨架 | D 层 `sections.md`；A 层 `decide.md §17` |
| 频率有限位移 6N+1、虚频判据（0/1/多个、≥100 cm⁻¹） | A 层 `decide.md §23`；F 层 `playbook.md` |
| `FULLY_PERIODIC` / `MODE_SELECTIVE` / `INVOLVED_ATOMS` 关键字存在性 | G `20_input_reference_tree.md`；A 层 `decide.md §23` |
| `&ATOM` 段树（`&AE_BASIS`/`&PP_BASIS`/`&POWELL`/`&POTENTIAL`） | G `20_input_reference_tree.md`（**只有树，无语义** → 语义属增量 N4） |
| 编译/工具链 | G `09_build_libraries.md`；B 层 `course_learned.md §3.1` |
| `LBFGS`/`BFGS`/`CG` 官方默认值与 LBFGS 专属判据 | G `05_optimization.md` §6.2/§7.4/§7.5 |
| k 点、单 Γ 点要求边长 ≥10 Å | G `02_dft_methods.md` §4；A 层 `decide.md §5.2` |

### 5.2 真增量

| # | 增量 | 出处 | 既有层核对结果 | 建议落点 |
|---|---|---|---|---|
| **N1** | **`OPTIMIZE_BASIS` 完整工作流**：四步法 + 目标函数 `Ω = Δρ + γ·ln κ` + 可调的 5 个设计自由度 + 训练分子准则 + 完整输入 | `T20 P13`–`P17`、`P22` | 全库只有 G 层 `01_global_and_units.md` 一行"`OPTIMIZE_BASIS` — A tool to create a MOLOPT or ADMM basis…"与 G 层 `20_input_reference_tree.md` 的段树；**没有任何一层写过流程/目标函数** | 可写入 A 层基组节或 F 层；**这是本层最硬的增量** |
| **N2** | **训练分子的选择准则 + 文献**（小分子、两种元素、不同配位环境；Ahlrichs *PCCP* **7**, 3297 (2005) SI） | `T20 P14` | grep `Ahlrichs` 只命中 G 层 `21`/`23` 的**基组名**（`Ahlrichs-pVDZ` 等），**无训练分子语境** | 与 N1 同处 |
| **N3** | **参考（完备）基组 = `GTH-def2-QZVP` / `aug-GTH-def2-QZVP`，位置 `$CP2K/cp2k/data/BASIS_ADMM`** | `T20 P17` | 全库 `BASIS_ADMM` 只出现在 **ADMM 辅助基**语境（G `02`/`18`/`21`/`23`）；`def2-QZVP` 只在 G `21` 出现且是 RI 辅助基（Zn 的 `def2-QZVP-RIFIT`）。**"拿 BASIS_ADMM 里的 QZVP 当拟合靶子"这一用途是新的** | A 层基组节 |
| **N4** | **`ATOM` 码的两种 `RUN_TYPE` 完整输入**（`BASIS_OPTIMIZATION` / `PSEUDOPOTENTIAL_OPTIMIZATION`）+ `$CP2K/potentials/README_quick_GTH` | `T20 P18`、`P30`、`P32` | grep `GEOMETRICAL_GTO`/`WEIGHT_PSIR0`/`DKH`/`PSEUDOPOTENTIAL_OPTIMIZATION` **零命中**；G 层只有段名树 | 可单列一节"自造基组/赝势"；**注意这是专家路线，不是新手路线**（与 `T20 P33` 的告诫一致） |
| **N5** | **BSE(Gaussian 94) → CP2K 格式转换法 + 指数窗口 `0.05~20`** | `T20 P21` | grep `STO-3G`/`6-31G`/`6-311G(2df` **零命中**；G 层只记"官方也接受从 BSE 取基组"（一句） | A 层/F 层；**这是"跨程序搬基组"的唯一可执行范例** |
| **N6** | **MOLOPT ↔ Pople/NWCHEM 质量对应表**（`SZV↔STO-3G`、`DZVP↔6-31G*`、`TZVP↔6-311G*`、`TZV2P↔6-311G(2df, 2pd)`） | `T20 P11` | 三层都只记"递增质量"，**无对应表** | A 层基组节（**务必标注"质量档位对应，非可互换"**） |
| **N7** | **基组设计的第 4 条标准：良态重叠矩阵 + 条件数定义**（= 最大/最小本征值之比） | `T20 P10` | `条件数`/`condition number` 只命中 G `23`（LRI 的病态与 `MAX_CONDITION_NUM`）——**语境不同**（LRI 辅助基 vs 基组设计准则） | A 层基组节；与 G `23` 的 LRI 条目互链 |
| **N8** | **GTH 赝势文件字段语义**（各壳层价电子数 `4 6 2`、`r_loc`、每通道投影子数） | `T20 P27` | G `14` §3.3 只给了**重启文件里展开的数值块**，**没有字段语义** | G 层可回填；A 层给指针 |
| **N9** | **GTH 赝势按泛函的"元素覆盖范围"**（LDA(PADE) H–Rn 含镧系 / PBE H–Rn **不含镧系** / PBEsol·BP H–Kr / HCTH·NLCC 少数） | `T20 P28` | G `14` §4.1 只列**可选泛函名**，§4.2 只给**元素→qN**，**没有"哪个泛函覆盖到哪个元素"** | G 层回填或 A 层（见 §6-10 的并列说明） |
| **N10** | **赝势优化的判据与流程**（全电子 vs 赝原子在原子球内的**本征值 + 电荷**差最小；含 PBE0 例子） | `T20 P29`、`P30` | 零命中 | 与 N4 同处 |
| **N11** | **BSSE 的可抄骨架**（`RUN_TYPE BSSE` + `&BSSE/&FRAGMENT LIST a..b` + `KIND H_ghost`/`GHOST`）+ "MOLOPT 不完备"的定性归因 | `T20 P24` | G `18` §2.9 有方案、无骨架；E 层 `course_notes.md` 已澄清"讲师从未把 `&BSSE` 作为校正方案给出" | A 层 §28 或 F 层；与 G `18` §2.9 互链 |
| **N12** | **工程纪律**：自造基组/赝势前先读原文；**生产前做大量测试并与参考值比对** | `T20 P33` | 零命中（G 层无此"过程性劝告"） | F 层"方法学纪律" |
| **N13** | **T24 的整体"上手路径"**（装 → 求助 → 首个能量计算 → 验证判据） | `T24 P1`–`P5`、`P9`–`P12` | B 层 `course_learned.md §3.1` 覆盖**编译**，A/F/D 层覆盖**单个任务写法**；**"零基础从装到跑通"的端到端清单没有** | 可直接并入 `AGENTS.md` §3 / `USAGE.md`，或 `guide.py` 的 `define` 阶段文案 |
| **N14** | **"手册不是教程、tests 参数不可投产"这两条资料使用告诫** | `T24 P4`、`P5` | G `13_input_syntax_and_print.md` 讲"用 `cp2k --html` 拿与二进制一致的文档"；**"tests 参数不合理"这条与 E 层说法冲突**（见 §6-6） | F 层；同时更新 E 层口径 |
| **N15** | **非周期 POISSON 的 `MT` / `WAVELET` 判据**（MT：单胞体积要够大，原文"至少是电荷密度的两倍"；WAVELET：分子必须居中、边界电子密度为 0）+ `TOPOLOGY CENTER_COORDINATES` 配套写法 | `T24 P13`–`P14` | G `23` 只说"从预期周期性与边界条件选择 `POISSON_SOLVER`"，`00_map.md` 提 `CENTER_COORDINATES` 但**无 MT/WAVELET 判据**；A 层 `decide.md §5` 给"`PERIODIC NONE` + `POISSON WAVELET`"的一行结论，**无判据** | A 层 §5 / F 层（**MT 那句量纲可疑，见 §7-8**） |
| **N16** | **GTH 赝势导致虚频的解释与 4 种处置**（NLCC / CUTOFF ≥600 / `XC_GRID` 平滑（不推荐）/ `USE_FINER_GRID`（XC 精度 → `4*CUTOFF`）） | `T24 P19` | 全库虚频条目都是"判据 + 收敛阈值自救"（A 层 §23.1、F 层），**没有"GTH 赝势数值问题"这一归因，也没有这 4 条处方** | A 层 §23.1 补"第二条归因"；见 §6-8/§6-9 |
| **N17** | **`EPS_DEFAULT` 联动 4 参数的默认值表** | `T24 P10` | G 层只对 `EPS_PGF_ORB = √EPS_DEFAULT` 有官方出处（`08_errors_and_faq.md` §3.8.4）；其余三条 G 层无记录；且 D 层 `sections.md` 有一条**冲突**（§6-3） | 先查 Input Reference 裁定，再回填 G/D 层 |
| **N18** | **自动多重度的 4 条操作限制**（必须 LSD/UKS、必须对角化、必须 `ADDED_MOS`、不能 `SMEAR`、`RELAX_MULTIP` 值越大翻转概率越大） | `T24 P15`–`P16` | A 层 `decide.md`/F 层已有"不建议开、会禁用 OT"的**结论**；**这 4 条可执行限制是新的** | A 层 §22 / F 层 |
| **N19** | **`BAND_TYPE` 更多枚举**：`IT-NEB`、`CI-NEB`、**`B-NEB`、`D-NEB`、`EB`、`SM`** | `T24 P17` | A/F/D 层都只写 `IT-NEB`/`CI-NEB`/`SM`；G 层明确"不编造 NEB 内容" | 需查官方 Input Reference 后回填（**由 G 层裁决**） |
| **N20** | **`MODE_SELECTIVE` 的完整输入 + `NREP = 总 CPU / NPROC_REP` + "单 REPLICA 会只跟踪一个频率"的坑** | `T24 P18` | A 层只记 `&INVOLVED_ATOMS 82 83` 的存在 | A 层 §23 / F 层 |
| **N21** | **`FULLY_PERIODIC T` 的量化语义**：N 原子体系给 **`3N−3`** 个频率（含 3 个转动自由度） | `T24 P18` | A 层只记"不从 Hessian 清除刚体转动" | A 层 §23（一句补充） |
| **N22** | **旧版 arch-file 编译实操**（MKL 库链接组合、`-lmkl_blacs_intelmpi_lp64` vs `openmpi_lp64` 的切换规则、15 分钟出 `cp2k.popt`） | `T24 P2`–`P4` | G `09_build_libraries.md` 是现代 CMake/toolchain；**arch-file 流程已过时** | **只作历史参考**，不入决策库（§6-5、§7-10） |
| **N23** | **元素相关 CUTOFF 清单（第二份独立样本）**：Na、N、O、F、Ne、Ni、Ga 需 ~1000 Ry | `T24 P6` | E 层样本是 F、O、Fe、Co、Ni、Cu、Na（`MAPPING.md` 行 320）。**两份清单不完全重合 → 互相印证"确有若干元素需 ~1000 Ry"**，具体元素名单需并列 | A 层 `decide.md §4`（并列两个来源） |

---

## 6. 与既有层的冲突 / 纠错（给页码证据）

| # | 冲突点 | H 层（T20/T24）口径 | 既有层口径 | 处置建议 |
|---|---|---|---|---|
| **1** | **MOLOPT 的文献归属** | `T20 P10`、`P15` 都把 MOLOPT 挂在 **VandeVondele & Hutter, *J. Chem. Phys.*, 127, 114105 (2007)** | F 层 `playbook.md` 已纠错：E 层 `learn_L3.md` 的 `L3 P42` 误把 MOLOPT 归给 *Phys. Rev. B* 54, 1703 (1996)（那是 GTH 赝势论文）；`L3 P15` 写对了 | ✅ **H 层独立印证 F 层的纠错**（第二证据）。建议在 E 层纠错处加注"官方 workshop `T20 P10/P15` 亦作 JCP 127, 114105 (2007)" |
| **2** | **"CP2K 只支持 Gamma 点，没有 K 点"** | `T24 P6` 原文 | G 层 `02_dft_methods.md` §4 有完整 `&KPOINTS` 用法；G 层 `11_version_changelog.md` §4.1 记 **3.0（2015）引入基础 k 点功能**；G 层 `08_errors_and_faq.md` **§3.11**（`faq:common_mistakes` 第 3 条）明确把"CP2K 没有 k 点采样"标为 **2020 年的旧表述、已不成立**，**§3.10** 记官方已把 k 点 FAQ 改成跳转页 | ⚠️ **以 G 层为准**。T24 成稿于 CP2K **2.5.1**（`T24 P2`），该表述**在其年代成立**。**但 T24 同段的实操推论仍有效**——"晶胞必须足够大"、"不能直接用 VASP 的小晶胞"与 A 层 `decide.md §5.2`（单 Γ 点要求边长 ≥10 Å）一致 → **可作独立佐证引用** |
| **3** | **`EPS_DEFAULT` 联动表里 `/100` 归谁** ✅ **已定案** | `T24 P10`：`EPS_CORE_CHARGE` = **`EPS_DEFAULT/100.0`**；`EPS_GVG_RSPACE` = **`SQRT(EPS_DEFAULT)`**；`EPS_PGF_ORB` = `SQRT(EPS_DEFAULT)`；`EPS_KG_ORB` = `SQRT(EPS_DEFAULT)` | D 层 `sections.md`：**"`EPS_PGF_ORB`（≈√EPS_DEFAULT）、`EPS_GVG_RSPACE`（≈EPS_DEFAULT/100）"** —— 把 `/100` 记到了 `EPS_GVG_RSPACE` 上；G 层只裁定 `EPS_PGF_ORB` = √EPS_DEFAULT（`08_errors_and_faq.md` §3.8.4） | ✅ **T24 对，D 层错。** 已用官方 `cp2k_input.xml` 定案（`python _kw_probe.py FORCE_EVAL/DFT/QS/EPS_CORE_CHARGE`）：<br>`EPS_CORE_CHARGE` 官方原文 **"Overrides EPS_DEFAULT/100.0 value"**；<br>`EPS_GVG_RSPACE` 与 `EPS_PGF_ORB` 官方原文均为 **"Overrides SQRT(EPS_DEFAULT) value"**。<br>→ `/100` **只属于 `EPS_CORE_CHARGE`**；D 层 `sections.md` 已于本轮更正并附更正记录 |
| **4** | **几何优化的推荐算法** | `T24 P12`：**"对于一般的几何优化，推荐使用 LBFGS 算法"**（理由：效率与 BFGS 类似、稳定性好） | B 层 `course_learned.md`：`BFGS`（**默认**，中等体系）/ `LBFGS`（**一两千原子的超大体系**）/ `CG`（小体系或 BFGS 不稳时）；G 层 `05_optimization.md`：`OPTIMIZER` **默认 `BFGS`** | ⚠️ **默认值以 G 层为准（`BFGS`）**；T24 的"一般推荐 LBFGS"是**另一套经验口径**，可作 F 层的备选建议并列，不要覆盖默认值说明 |
| **5** | **预编译版到底慢多少** | `T24 P1`：预编译版用"**没有优化过的 blas / lapack**"，自编（Intel+MKL）**快 3 倍左右**；`T24 P4`：GNU+MKL 与 Intel+MKL **速度相当** | G 层 `10_features_resources.md`：官方页写 **"precompiled single node, optimised CP2K versions for Linux"**（即官方自称已优化）；E 层（`playbook.md`）：官方预编译 `ssmp` 实测比 `popt` **慢 30–50%** | ⚠️ **三方口径不同**（3× / 官方"optimised" / 30–50%）。方向一致（**自编更快**），**倍数不可混用**。建议 F 层并列三条并标注各自出处与年代 |
| **6** | **`tests/` 里的参数能不能用** | `T24 P4`/`P5`：**"这些输入文件并不是最适合计算的，其中测参数设置没有经过优化"**、**"往往使用了不合理的参数，用户需要参考手册等其他资料自行进行调整"** | E 层 `learn_L3.md`：源码 `tests/` 有 ~3000 个测试输入，**"参数为优化过的最佳推荐，但未必最优"** | ⚠️ **直接冲突**（"未经优化/不合理" vs "优化过的最佳推荐"）。G 层无裁定。**建议采用 T24 的更保守口径**（对新手更安全），并在 E 层该行加注"H 层 `T24 P4–P5` 给出相反告诫" |
| **7** | **NLCC 赝势覆盖范围** | `T24 P19`：**"只有 B-Cl 的元素有，且只提供了 PBE 泛函的赝势"** | G 层 `14_basis_and_potentials.md` §3.6：`NLCC_POTENTIALS` 只写 **"contain more specialized potentials"**；T20 `P28`：**"a few selected elements"** | ⚠️ **三方不一致，且 T24 的具体范围无出处**。建议：以 G 层"更专用的势"为口径，T24 的 B–Cl 作为**待核实的待办**（查 `$CP2K/cp2k/data/NLCC_POTENTIALS` 实际内容） |
| **8** | **虚频问题的成因** | `T24 P19`：多个虚频**"并非是几何优化出现了问题，而是 CP2K 计算使用 GTH 赝势时存在的一个问题"** | A 层 `decide.md §23.1`：多个虚频 ⇒ **"过渡态搜得不准"**，常见原因是**收敛阈值设得太宽**；处方是收紧 `EPS_SCF` | ⚠️ **两种归因，不是简单对错**：A 层是"方法/收敛"归因，T24 是"赝势数值"归因。**建议 A 层 §23.1 增列"第二条归因（GTH 赝势数值噪音）"+ T24 P19 的 4 条处方**，形成两级排查：先收紧 `EPS_SCF` → 仍不行再看 `USE_FINER_GRID`/NLCC |
| **9** | **处置虚频的 CUTOFF 阈值** | `T24 P19` 方案②：**"增大 `CUTOFF`，使用 600 Ry 以上"** | E 层/B 层性价比档 **CUTOFF 400–500**（讲师口径 400–500 靠相对能量抵消误差）；G 层 `03_scf_convergence.md` §2 的方法论是**自己扫收敛** | ⚠️ **并列，不取单方**。T24 的 600 Ry 是"为压赝势数值噪音"的专门处方，与"常规生产取 400–500"不矛盾但**代价高一个档**。建议标注为"**针对性处方，需先确认虚频确由数值噪音引起**" |
| **10** | **哪里查赝势/基组"覆盖到哪个元素"** | `T20 P28`：按泛函给覆盖范围（含 **PBE 不含镧系**） | G 层 `14_basis_and_potentials.md` §4.1 只列泛函名（**含 T20 未提的 `BLYP`、`OLYP`**），§4.2 给元素→qN 但**不标泛函** | ⚠️ **不能直接交叉核对**（粒度不同）。建议 G 层补一列 / 加一行备注"哪些 qN 属哪个泛函族"，并注明 T20 P28 的口径 |
| **11** | **1998 年那篇赝势文献的署名** | `T20 P29` 写作 **"Hutter et al., *Phys. Rev. B*, 58, 3641 (1998)"** | G 层 `14_basis_and_potentials.md` §4.3 与 `12_authority_sources.md`：**Hartwigsen, Goedecker, Hutter**, *Phys. Rev. B* **58**, 3641–3662 (1998) | ⚠️ T20 的署名不完整 → **以 G 层为准**（G 层有官方索引页出处）。引用时写全三位作者 |
| **12** | **`SR` 基组的代价** | `T20 P9` 只给**理由**（shorter range ⇒ less diffuse ⇒ 给固体用），**不给数字** | E 层/B 层给**数字**：BSSE 增大 ~50%、提速 2–3 倍 | ✅ **互补，不冲突**。建议 A 层 `§28.2` 把"为什么（T20 P9）"与"多大代价（E 层）"分句写清 |
| **13** | **`BAND_TYPE` 的合法枚举** | `T24 P17`：`IT-NEB`、`CI-NEB`、**`B-NEB`、`D-NEB`、`EB`、`SM`** | A/F/D 层只写 `IT-NEB`/`CI-NEB`/`SM`；G 层明确"不编造 NEB 内容" | ⚠️ **需查官方 Input Reference 后由 G 层登记**。在未核实前，A 层保持现有三种，T24 的六种作为**待核实项**（§7-12） |

---

## 7. 存疑

> **本轮查证方式（15 条全部重查）**：① 用 PyMuPDF（`fitz`）把**争议页整页渲染成 PNG 再看**——
> 文本层看不到的花括号、箭头、页脚公式、终端截图，一望即知；② 用官方 `cp2k_input.xml`（`python _kw_probe.py ...`）定段归属/默认值/枚举；
> ③ 直接**下载官方数据与测试文件**对原文（`BASIS_MOLOPT`、`BASIS_ADMM`、`tests/ATOM/**`）；
> ④ 用 G 层（`references/official/`）与真实 `.out` 作旁证。**凡推翻原文猜测的，一律附「更正记录」。**

1. **`T20 P12` 六字段首值 = `2`（H）** → ✅ **已定案：两行没被合并，`2` 也不是错值——官方文件里 H 就写 `2`，且该字段不参与计算。**
   - **结论**：`1` 与 `2 0 1 7 2 1` 是**上下两行**（不是 pdfplumber 合并/错位）：`1` = **nset**（该基组含几个"指数集"）；`2 0 1 7 2 1` = 该 set 的组成行 `n lmin lmax nexp nshell(lmin) nshell(lmax)`。
   - **依据 1（页图）**：`fitz` 渲染 T20 P12 → `1` 单独一行、右侧箭头写的是 **"number of CGTO"**（**不是**"number of CGTO contraction coefficients"，后者是标在系数列上方的另一个标注）；`2 0 1 7 2 1` 是另一行，六条箭头分别指向 principal quantum number / minimum angular momentum quantum number / maximum angular momentum quantum number / number of Gaussian exponents / number of s-function / number of p-function。
   - **依据 2（官方基组文件自带格式说明）**：`https://raw.githubusercontent.com/cp2k/cp2k/master/data/BASIS_MOLOPT`（本轮下载后逐行查看第 39–73 行）：文件头 `# Basis set format:` 写明 `# nset : Number of exponent sets`、**`# n : Principle quantum number (only for orbital label printing)`**，随后 `H DZVP-MOLOPT-GTH DZVP-MOLOPT-GTH-q1` 条目逐字为 ` 1` / ` 2 0 1 7 2 1` / 7 行指数与系数——与 T20 P12 完全一致（含 `0.021708243634`）。
   - **依据 3（G 层）**：`references/official/14_basis_and_potentials.md:83` 已记官方原文 "**CP2K ignores this number.** It is merely present for compatibility reasons and documentation." ⇒ 即便它是 2 也不影响任何计算。
   - **更正记录**：原文两处猜测都要撤：① "若按同页标签它是 principal quantum number，H 应为 1" —— **官方文件里 H 就是 2**（该字段只用于轨道标签打印）；② "疑为 pdfplumber 把'set 数'行与 set 头行合并/错位" —— **不存在合并**，渲染页图可见两行分开、标注各异。

2. **`T20 P11` 的 `H-Rn` 与 `limited availability` 归属不明** → ✅ **已定案：两个标注都指向 CP2K（左）列，不是"全电子列可用性有限"。**
   - **结论**：`H-Rn` 的蓝色花括号**只括住 SZV / DZVP 两行**；`limited availability` 的花括号**括住 TZVP / TZV2P 两行**；两个括号都画在**表格左侧**，即限定的是**左列（CP2K / MOLOPT）**。
   - **依据**：`fitz` 渲染 T20 P11 页图（2304×1728，括号与行边界一目了然）。
   - **更正记录**：原文的"合理猜测"是"`H-Rn` = MOLOPT 覆盖 H–Rn ＋ `limited availability` = 全电子 Pople 列有限可用"——**后半错**：括号在左列侧，`limited availability` 说的是 **SZV/DZVP 之外的 TZVP/TZV2P 只有有限元素**。引用时请按"**SZV/DZVP 覆盖广；TZVP/TZV2P 仅少数元素**"来写。
   - **量化核对（官方 `BASIS_MOLOPT`，本轮下载后按名字计数）**：`SZV-MOLOPT-SR-GTH` 与 `DZVP-MOLOPT-SR-GTH` 各 **72** 个元素条目（文件头自述这些 SR 组覆盖 "most of the periodic table"）；而 `TZVP-MOLOPT-GTH` / `TZV2P-MOLOPT-GTH` / `TZV2PX-MOLOPT-GTH` 各只有 **9** 个（`H C N O F Si P S Cl`）⇒ **"覆盖广" vs "only 9 个元素" 与该页两个花括号的方向完全一致**（`H-Rn` 是宽覆盖的近似说法：严格说 72 个元素、并非真的到 Rn；这一点画图者没有精确标注）。
   - 说明：这是 G 层未收录的页内信息，只能靠**渲染页图**定案（文本层顺序被打乱）。

3. **`T20 P18` 的 `S_EXPONENTS`/`P_EXPONENTS` 末值不单调** → ⚠️ **未能确证，已排除以下可能**：① 不是抽取假象——`fitz` 渲染 T20 P18 页图与文本层**逐字一致**（两行都是 `7.92602574 5.92602574 1.59655262 0.71279902 0.28969807 4.00675308`）；② 不是"多列串行/排版换行"——页图上就是一行六个数；③ "S 与 P 完全相同"**不是异常**。
   **相关事实（本轮查到的）**：① 官方算例里 S/P（乃至 D）三行**本来就相同**且降序：`tests/ATOM/regtest-2/Ru_basis.inp`（`https://raw.githubusercontent.com/cp2k/cp2k/master/tests/ATOM/regtest-2/Ru_basis.inp`）`S_EXPONENTS`/`P_EXPONENTS`/`D_EXPONENTS` 三行数值完全一样；② 紧接的 T20 P19 是**同一个 Na 例子**（标题相同、同为 `NUM_GTO 6 6`）的 ATOM 输出截图，其 `s Exponents:` 打印顺序为 `3.37371675 / 1.19458113 / 21.63024049 / 0.39968861 / 8.84460076 / 0.04267359`（排序后是 `21.63 / 8.84 / 3.37 / 1.19 / 0.3997 / 0.0427`）——**输出本身就不按大小排序**，说明这套「指数列表的书写顺序」并不承载排序语义；③ 若把 P18 的六个数改排成降序，恰好得到 `7.926… > 5.926… > 4.00675308 > 1.59655262 > 0.71279902 > 0.28969807`（**完全单调**）⇒ 最可能是**第 6 个值被挪到了行尾**（幻灯片编辑时的错位），而不是"真的以 0.2897 之后接 4.0068"。
   **仍不确定的是**：原件到底是"4.00675308 排第 3 位"，还是"本有第 6 个更小指数、被 4.00675308 顶替"。
   **要确证需要**：2015 年那次 Na 基组优化所用的**原始输入文件**（对应 `$CP2K/cp2k/tests/ATOM/**` 的算例，或 Ling 的原始 .pptx）。2026 年的 CP2K 仓库里 `tests/ATOM/` 只剩 `regtest-1/2/libxc/pseudo`，没有这份 Na 例子，故本轮无法闭环。

4. **`T20 P18` 的 `ELECTRON_CONFIGURATION CORE 2s2 2p6 3s1`** → ✅ **已定案：这不是笔误，是 CP2K `ATOM` 的合法写法，官方回归测试里就在用。**
   - **结论**：`ELECTRON_CONFIGURATION` 后面**可以**直接跟字面量 `CORE`，表示"这里给的是价（赝）组态"，核心电子另由独立的 `CORE` 关键字给出；P18 的 `ELECTRON_CONFIGURATION CORE 2s2 2p6 3s1` + `CORE 1s2`（Na，`GTH-PBE-q9`）因此是**同型合法写法**。
   - **依据**：官方回归测试 `tests/ATOM/regtest-2/Ru_basis.inp`（`https://raw.githubusercontent.com/cp2k/cp2k/master/tests/ATOM/regtest-2/Ru_basis.inp`）逐字为
     ```
     CORE [Kr]
     ELECTRON_CONFIGURATION CORE 4d7 5s1
     ```
     —— 与本页写法同型（"CORE + 价组态"）。
   - **更正记录**：原文猜"P18 的 `CORE` 疑为**从下一行 `CORE 1s2` 误并入**"——**错**，官方算例里 `ELECTRON_CONFIGURATION` 行内本就有 `CORE` 字面量。**照抄 P18 无风险，不必改。**
   - **顺带定案（同页对照）**：T20 P30 的 O 例（`ELECTRON_CONFIGURATION [He] 2s2 2p4` + 独立一行 `CORE [He]`）与官方 `tests/ATOM/regtest-pseudo/O-PBE0-q6.inp`（`https://raw.githubusercontent.com/cp2k/cp2k/master/tests/ATOM/regtest-pseudo/O-PBE0-q6.inp`）**逐字一致**（P30 只是省略了 `&GTH_POTENTIAL` 数值块等）⇒ P30 是官方算例的直接摘录。另：`_kw_probe.py --find ELECTRON_CONFIGURATION` 给 `ATOM` 段说明 "Specifies the electron configuration. Optional the multiplicity (m) and a core state [XX] can be declared"，`--find CORE` 给 `ATOM/CORE` 的用法 `CORE 1s2 … or CORE [Ne] or CORE none for 0 electron cores`。

5. **`T20 P21` 的 `(use exponents between 0.05~20 only)` 作用对象不明** → ✅ **已定案：该规则作用于"从 BSE 搬来的那些 set"；首组不受它约束（有官方文件反证）。**
   - **结论**：T20 P21 左栏就是 `BASIS_ADMM` 里 `H GTH-def2-QZVP` 的**真实内容**；0.05~20 的窗口**只作用在从 BSE(Gaussian-94) 派生的 11 个未收缩 set 上**，不作用于第 1 个（收缩）set。
   - **依据**：`https://raw.githubusercontent.com/cp2k/cp2k/master/data/BASIS_ADMM`（本轮下载后查看）：`H GTH-def2-QZVP` 条目逐字 = `12`（set 数）/ `2 0 0 7 1` / 7 个指数与系数（`11.478000339908 0.024916243200` … `0.021708243634 -0.001125195500`，与 T20 P21 左栏逐字相同；其指数与首个 s 系数也和 T20 P12 的 `H DZVP-MOLOPT-GTH` 首组相同——P12 那组因为 `lmin..lmax = 0..1` 而多两列收缩系数）/ 之后 11 个单指数 set（`6.50959430 / 1.84124550 / 0.59853725 / 0.21397624 / 0.08031629 / 2.29200000 / 0.83800000 / 0.29200000 / 2.06200000 / 0.66200000 / 1.39700000`）。
     被丢弃的 BSE 指数正是两个 **>20** 的 `190.6916900`、`28.6055320`；保留的 11 个全部 **≥ 0.08031629**；而首组里的 `0.021708243634` **明显 < 0.05 却保留了** ⇒ 规则显然没有作用于首组。**原文的"似只作用于由 BSE 派生的未收缩 set"这一推论成立，并可升级为定案。**
   - **仍不确定（小，不影响上条）**：为什么首组直接采用与 `H SZV-MOLOPT-GTH` 完全相同的指数/系数——文件本身如此，官方未写理由。

6. **指数窗口两处不一致（`0.05~20` vs `0.1 20`）** → ✅ **已定案：不是笔误，是两个不同阶段的两套阈值。**
   - **结论**：`0.05~20`（T20 P21）是**手工从 BSE 造参考基组**时的取舍窗口；`0.1 20`（T20 P22）是 `OPTIMIZE_BASIS` 输入里 **`&FIT_KIND &CONSTRAIN_EXPONENTS BOUNDARIES` 这个关键字**的值——一个是"人在编辑器里筛数"，一个是"程序内的优化约束"，不可能同源。
   - **依据 1（官方 XML）**：`python _kw_probe.py OPTIMIZE_BASIS/FIT_KIND/CONSTRAIN_EXPONENTS/BOUNDARIES` → "Defines the boundaries to which the optimization is restricted. First value is the lower bound, second value is the upper bound."
   - **依据 2（页图 + 产物自洽）**：`fitz` 渲染 T20 P22 → `&CONSTRAIN_EXPONENTS / BOUNDARIES 0.1 20 / USE_EXP -1 -1` 确实在 `&FIT_KIND Ti` 内；同页拟合产物 `Ti FIT10` 的 10 个指数（`s: 0.10001966 / 1.06186104 / 0.40963197 / 4.39901876`；`p: 0.52985233 / 1.57394040 / 11.83843422`；`d: 0.25675246 / 1.02358115 / 4.21355677`）**全部落在 [0.1, 20]**（最小 0.10001966 恰好贴住下界）⇒ 该约束确实在起作用。
   - **仍不确定（小）**：为什么造参考基组放宽到 0.05 而拟合收紧到 0.1——讲义未解释；这只影响"为什么"，不影响"两者是两件事"的判定。

7. **`T20 P25`/`P26` 的公式出处（Krack 2005 vs Goedecker 1996）** → ✅ **已定案：公式已可核对；引 Krack 2005 描述该解析形式可以接受，但"形式"的原始出处是 Goedecker 1996。**
   - **公式已复原**（原文说"在图片中、抽取文本里没有"——**渲染页图即可读**，现照抄如下）：
     - P25（**局域部分**）：`V_loc^PP(r) = −(Z_eff/r)·erf(α^PP r) + Σ_{i=1..4} C_i^PP (√2·α^PP r)^{2i−2} exp[−(α^PP r)²]`，其中 `α^PP = 1/(√2·r_loc^PP)`；标注：ionic charge / error function / long-ranged term / short-ranged term / coefficients / Local part；页脚注 "`r_loc`: range of Gaussian ionic charge distribution"，引用 "Krack, Theor. Chem. Acc., 114, 145 (2005)"。
     - P26（**非局域部分**）：`V_nl^PP(r,r′) = Σ_{lm} Σ_{ij} ⟨r|p_i^{lm}⟩ h_ij^l ⟨p_j^{lm}|r′⟩`，`⟨r|p_i^{lm}⟩ = N_i^l Y^{lm}(r̂) r^{l+2i−2} exp[−(1/2)(r/r_l)²]`；标注：Non-local part / coefficients / Gaussian-type projectors / normalisation constant / spherical harmonics / radius；同样引用 Krack 2005。
   - **文献关系（依 G 层）**：`references/official/14_basis_and_potentials.md:414-416` 已登记三篇并给出各自定位——**S. Goedecker, M. Teter, J. Hutter, PRB 54, 1703 (1996)** = "GTH 方法原始文献"（即该分离式双空间解析形式）；**Hartwigsen, Goedecker, Hutter, PRB 58, 3641 (1998)** = H→Rn；**M. Krack, Theor. Chem. Acc. 114, 145 (2005)** = "H 到 Kr，针对 GGA 优化"。⇒ **"形式"归 Goedecker 1996（+1998 的相对论扩展），Krack 2005 是面向 GGA 的重参数化**，所以 T20 在公式页引用 Krack 2005 属于"**引了参数化文献、未引原始形式出处**"——**不算错，但不完整**；正式引用请按 G 层三篇写全（"形式"引 Goedecker 1996，元素覆盖与 GGA 参数化引 Krack 2005）。

8. **`T24 P13` 的 MT 判据量纲可疑** → ⚠️ **未能确证（原句确为原文，非抽取丢词）；同时修正页码。**
   - **更正记录（页码）**：该句在 **`T24 P14`**，不在 P13（P13 是 `&TRANSITION_STATE/&DIMER` 与 `&POISSON PERIODIC none` 的开头）。§5.2 N15 的"`T24 P13`–`P14`"作为区间引用无误，但本条原写 `T24 P13` 应改为 **`T24 P14`**。§6 未动。
   - **已定案部分**：`fitz` 渲染 T24 P14 → 原句逐字为"**如果设置为 MT，要保证计算使用的单胞体积足够大，至少是电荷密度的两倍。**" ⇒ **不是抽取丢词**，是原文表述；"体积 vs 密度"量纲确实不成立。
   - **相关事实（官方 XML）**：`python _kw_probe.py --section FORCE_EVAL/DFT/POISSON` → `POISSON_SOLVER`（默认 `PERIODIC`，合法值 `PERIODIC|ANALYTIC|MT|MULTIPOLE|WAVELET|IMPLICIT`）、`PERIODIC`（默认 `XYZ`）与 `&MT`/`&WAVELET`/`&MULTIPOLE`/`&EWALD`/`&IMPLICIT`；`&MT` 段只有 `ALPHA`（默认 7.0）与 `REL_CUTOFF`（默认 2.0）两项 ⇒ **官方 XML 里没有"单胞要多大"这类判据**，所以无法用官方来源替作者补全原意。
   - **仍不确定的是**：作者原意到底是"单胞尺寸至少是体系尺寸的两倍"还是"单胞体积至少是分子所占体积的两倍"（或第三义）。
   - **要确证需要**：作者的原始 Word/源文件（不可得）；或 CP2K 官方针对 MT 求解器的等价要求（`&MT` 段说明、Mail list 中 Krack/Martyna 的答复）。
   - **可用的替代判据（不必等定案）**：同页 WAVELET 的那条判据是**明确且可执行**的——"分子必须处于单胞的中心，确保单胞的边界处电子密度为 0"（配 `&TOPOLOGY &CENTER_COORDINATES`）；用 MT 时按"单胞显著大于体系 + 结果对盒长收敛"来把握，别把"两倍"当硬数字。

9. **`T24 P19` 的 `SMOOTING` 拼写与 `USE_FINER_GRID` 归属** → ✅ **已定案（除"4×CUTOFF"这一个系数）。**
   - **`SMOOTING`**：`python _kw_probe.py --find SMOOTING` → **`=== 全库搜关键字 'SMOOTING'：0 处 ===`**。（`SMOOTHING` 这个拼法**存在**，但它是 `MOTION/BAND/STRING_METHOD` 的关键字——"Smoothing parameter for the reparametrization of the frames"，默认 0.2——**与 XC 网格毫无关系**，所以 P19 的 `SMOOTING` 不能"改个拼法"了事。）`&XC &XC_GRID` 里真正可用的平滑关键字是 **`XC_SMOOTH_RHO`**（默认 `NONE`，枚举 `NONE|NN50|NN10|SPLINE2|NN6|SPLINE3|NN4`，官方用法串 `xc_smooth_rho nn10`）⇒ P19 方案③"在 `XC_GRID` 部分使用平滑参数"应写成 **`XC_SMOOTH_RHO NN10`**，这也正是 P8 已经用过、且 G 层 `21_xray_spectroscopy_full.md` 用过（`NN50`）的同一个关键字。**原文 `SMOOTING` 属拼写/记忆错误。**
   - **`USE_FINER_GRID`**：`python _kw_probe.py --find USE_FINER_GRID` → 7 处，全部在 `.../XC/XC_GRID`（含 `FORCE_EVAL/DFT/XC/XC_GRID`），`DEFAULT_VALUE : F`，说明 "Uses a finer grid only to calculate the xc" ⇒ **P19 的段归属（`XC_GRID`）正确**；`T24 P6` 把它列在 CUTOFF/REL_CUTOFF 小节只是叙述编排（它不是 `&MGRID` 关键字）。
   - **仍未确证（小）**："加上这个参数后，XC 部分的格点精度提高为 **4×CUTOFF**"这个系数**官方 XML 里没有**（说明只到 "uses a finer grid"）。要确证需读源码（`src/input_cp2k_xc.F` 的定义处与 finer-grid 网格构造逻辑）；本轮两次尝试下载 CP2K 源码文件均因网络超时未完成，故**不声明该系数成立**。
   - **别混淆（原文已有，保留）**：`XC_SMOOTH_RHO NN10`（P8）与 `NN50`（G 层示例）是同一族参数的取值差异，与 `USE_FINER_GRID` 是两回事。

10. **T24 的版本时效性** → ✅ **已定案：可收窄到 2014-02-26 ~ 2014-12-22 之间。**
    - **依据（G 层版本沿革）**：`references/official/11_version_changelog.md:49` = "**2.5 | February 26, 2014**"、`:48` = "**2.6 | December 22, 2014**"。正文锚定 **CP2K 2.5.1**（`T24 P2`）⇒ 晚于 2.5 发布；正文提到 openmpi"目前最新 1.8.3"与内核 3.17（均为 2014 年秋）却**未提 2.6** ⇒ 成稿落在 **2014-02-26 之后、2014-12-22 之前**，与原文"≈2014 年"一致但更精确。
    - **保留告诫（原结论不变）**：文中一切"默认值/推荐值"（`REL_CUTOFF 50`、`CUTOFF 280`、LBFGS 推荐、编译流程、NEB 枚举）仍须以 G 层现行手册复核后使用——本轮的复核结果见 §7-12 与 §6。

11. **T24 的 `SZ` 写法** → ✅ **已定案：现行 CP2K 基组名是 `SZV`，没有 `SZ-` 条目。**
    - **依据**：下载官方 `https://raw.githubusercontent.com/cp2k/cp2k/master/data/BASIS_MOLOPT`（本地 1741 行）后统计：`Select-String '\bSZ-'` = **0 处**；`SZV-` 存在且成族，例如第 61 行 `H SZV-MOLOPT-GTH SZV-MOLOPT-GTH-q1`、第 496 行 `H SZV-MOLOPT-SR-GTH SZV-MOLOPT-SR-GTH-q1`，全文件同时定义 `SZV / DZVP / TZVP / TZV2P / TZV2PX`（以及各自的 `-SR` 变体）⇒ **`SZ` 是 T24 的简写/笔误**，T20 P9 与 G 层写 `SZV` 是对的。

12. **`T24 P17` 的 NEB 枚举（`B-NEB`/`D-NEB`/`EB`/`SM`）无第二来源** → ✅ **已定案：六个枚举全部存在，T24 P17 正确。**
    - **依据（官方 `cp2k_input.xml` 原文）**：`MOTION/BAND/BAND_TYPE` 节点写着 `<USAGE>BAND_TYPE (B-NEB|IT-NEB|CI-NEB|D-NEB|SM|EB)</USAGE>`、`<DEFAULT_VALUE>IT-NEB</DEFAULT_VALUE>`、`LOCATION input_cp2k_neb.F:91`，六个 ITEM 各有说明（Bisection / Improved tangent / Climbing image / Doubly nudged / String Method / Elastic band (Hamiltonian formulation)）；`python _kw_probe.py MOTION/BAND/BAND_TYPE` 给默认值 `IT-NEB`。
    - **处置**：§6-13 与 §5.2 N19 的"待核实"可以解除——**A/F/D 层只列三种属于"不全"，T24 的六种不是编造**；建议由 G 层 `20_input_reference_tree.md` 登记六个枚举与默认值。

13. **T20 的下载/延伸阅读 URL 全部过时** → ✅ **已定案：给出本轮实测可用的入口；CECAM 两条不声明可用。**
    - **实测可用**：
      - T20 讲义本体（现在仍在 cp2k.org）：`https://www.cp2k.org/_media/events:2015_cecam_tutorial:ling_basis_pseudo.pdf` —— HTTP 200，**730,711 字节，与本地 `【基组和赝势-庚子计算整理】ling_basis_pseudo.pdf` 逐字节相同**（`curl` 下载比对）。
      - 基组/势数据文件：`https://github.com/cp2k/cp2k/tree/master/data` —— 实测 `https://raw.githubusercontent.com/cp2k/cp2k/master/data/BASIS_MOLOPT` 与 `.../BASIS_ADMM` 均可下载（本轮就是这么核 P12/P21 的）。
      - 势文件仓库：`https://github.com/cp2k/cp2k-data`（API 200；但注意其根目录只有 `LICENSE`/`README.md`/`potentials/`）。
    - **更正记录**：原文说"请改用 G 层 `_sources.md` / GitHub `cp2k-data` 的链接"——**`cp2k-data` 只有势文件，没有基组文件**（实测其根目录只有 `LICENSE`/`README.md`/`potentials/`，`potentials/` 下是 `GTH_rev`/`Goedecker`/`MM_potentials`）；基组在 `cp2k/cp2k` 的 `data/` 下。另：T20 P33 的 `sourceforge.net/p/cp2k/code/HEAD/tree/trunk/cp2k/data/` 是 SourceForge 时代的历史镜像，**本轮未实测其可用性**（网络超时），不作为推荐入口。
    - **未验证**：P34 的两条 CECAM 链接 `http://www.cecam.org/upload/talk/presentation_3002.pdf`（Krack, Accuracy and Efficiency）与 `..._2994.pdf`（Mohamed, Basis Sets and Pseudo-Potentials）本轮实测只返回 **302 重定向**，未能确认重定向后的可用内容 ⇒ **不写"可用"**。需要这两份时，建议从 `https://www.cp2k.org/` 的 events / media 区按作者与标题检索（Ling 同系列讲义已在那里，见上）。

14. **T20 的三页"纯图页"（`P19`、`P23`、`P31`）内容不可复原** → ✅ **已定案：不是不可复原——渲染 PDF 页即可读全（都是终端截图）。**
    - **依据**：`fitz` 渲染 T20 P19/P23/P31（2304×1728）后逐页可读：
      - **P19**（`ATOM` 生成 Na 未收缩基组的结果）：`Orbital energies` 三行 `1 0 2.000 −2.092687 (−56.944917 eV)` / `2 0 1.000 −0.098547 (−2.681599)` / `1 1 6.000 −1.047513 (−28.504279)`；`POWELL| Number of function evaluations 273`；`POWELL| Final value of function −47.1609800227`；`Optimized Basis` → `s Exponents` 与 `p Exponents` 各 6 个（`3.37371675 / 1.19458113 / 21.63024049 / 0.39968861 / 8.84460076 / 0.04267359`，**注意打印顺序并非降序**，见 §7-3）；底部还有一段 shell 记录 `grep "Final" Na.out.*`（Na.out.4…9 的 Final value 从 `−47.0387118701` 收敛到 `−47.1649267320`）。
      - **P23**（`OPTIMIZE_BASIS` 迭代日志）：`BASOPT| Information at iteration number: 390` 与 `400`，每个训练集一行 `Rho difference | Condition num. | Time`（如训练集 1 `0.36863360E-02 | 0.46570176E+02 | 2.804`，训练集 3 `0.39469184E-02 | 0.97623037E+02 | 1.586`），`BASOPT| Total residuum value: −.14866668E+02`。
      - **P31**（赝势优化质量检查）：`POWELL| Final errors of target values`，列 `L N Occupation Eigenvalue [eV] dE [eV] dCharge`（共 7 行，如 `0 1 2.00 −26.0500594476 0.000072[0] −0.000034[3]`），外加 3 行 `s-states N= 1/2/3  Wavefunction at r=0:`。
    - **结论**：三页**内容可复原**；但复原出来的是**软件输出截图**，不含讲义正文信息，因此对"复现/决策"没有额外帮助——原告诫"如需图中数据须回 PDF"**可以改成"回 PDF 渲染页图（或直接照上面抄）"**。

15. **`T20 P11` 的"对应表"是否可用于定性论证** → ✅ **本来就不是"存疑"，是引用纪律；本轮补一条与本页 §7-2 的更正联动。**
    - **为什么不是问题**：P11 的标题就是 "MOLOPT basis set"，表头是 `CP2K | All-electron (Gaussian/NWCHEM)`，页脚注只解释 CP2K 侧命名（`SZV`/`DZVP`/`TZVP`/`TZV2P` 的 ζ 与极化含义）——它**本来就是"质量档位类比"**，不是"同一基组"。原文的告诫（必带"档位对应，非同一基组"限定语）**保留**。
    - **本轮补正**：这张表的两个浮标注（`H-Rn` / `limited availability`）归属已由图定案（见 §7-2），引用时**不要再说"limited availability 指全电子列"**；正确写法是"**SZV/DZVP 一族覆盖面广（SR 变体各 72 个元素），TZVP/TZV2P 只有 9 个元素（H C N O F Si P S Cl）**"。

---

## 附 · 与工作流工具的挂点（供 A/F 层与脚本联动时参考）

| 本层新增知识 | 可挂到哪里 |
|---|---|
| N1–N3（怎么造基组、训练集、参考基组） | `references/playbook.md` 新增"自造基组/赝势"节；`guide.py show decide` 的"超出内置库时怎么办"分支 |
| N6（MOLOPT ↔ Pople 对应表） | `references/decide.md` 基组节；`recommend.py` 在用户点名 Pople 基组时给出"对应档位"提示 |
| N9（赝势按泛函的元素覆盖） | `recommend.py` 的赝势选择校验（**若能核实**：镧系 + PBE + GTH = 不可用，须换 LDA(PADE) 或 UZH） |
| N15（MT/WAVELET 判据） | `gen_inp.py` 非周期模板的注释；`validate_inp.py` 可加"`PERIODIC NONE` 未配 `POISSON_SOLVER`"的告警 |
| N16（GTH 虚频 4 处方） | `diagnose.py` 的虚频分支：先建议收紧 `EPS_SCF`（A 层），再加"仍不行 → `USE_FINER_GRID`"（H 层） |
| N17（EPS_DEFAULT 联动） | **核实后**写入 `validate_inp.py`/`recommend.py` 的精度联动提示 |
| N13（上手路径） | `AGENTS.md` §3 与 `USAGE.md` 的"零基础路径"；`doctor.py` 输出里的下一步建议 |
