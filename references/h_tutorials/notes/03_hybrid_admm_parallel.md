# H 层精读笔记 03 — 杂化泛函 / ADMM（T05）＋ 自动化 / Input Magic / 性能（T06）

> **覆盖**：`txt/T05_hybrid_admm_watkins.txt`（43 页）、`txt/T06_parallel_input_mueller.txt`（42 页）。
> **引用约定**：`T05 P31` = 该 txt 里的 `========== PAGE 31 ==========`（= PDF 第 31 页；幻灯片页脚编号与 PDF 页码不同，本笔记一律用 PDF 页码）。
> **抽取复核**：这两份 PDF 用 `pdfplumber.extract_text(x_tolerance=1.5, y_tolerance=2)` **重抽过一遍**，
> 词间空格已还原（`txt/` 里的粘连是已知假象）。逐页比对过：**无整页文本丢失**；
> T05 P33–P40（TiO₂ 极化子）与 T06 的分隔页确实"字少图多"，不是抽取失败。
> **边界**：G 层（`references/official/`）已写的（官方默认值/关键字语义/官方 FAQ 原文）本笔记**只写指针**，不重复。

**一句话结论**：
- **T05** 是"**为什么杂化贵 → CP2K 用什么把成本压到可跑 → 代价是多少（带具体积分数与带隙数字）**"的完整成本链教材，是 A/G 层 ADMM 条目的**原始出处与量化补强**。
- **T06 的实际内容与文件名不符**：PDF 标题页写的是 **"CP2K: Automation, Scripting, Testing"**（T06 P1），
  **全篇没有并行层次（MPI/OpenMP/`GROUP_PARTITION`）的讲解**；它教的是**输入生成/预处理/批量提交/构建验证/基组验证/性能判读**。
  "Parallelization" 只出现在文件名里。见 §6 纠错 1。

---

## 1. 这两份材料教什么

### T05《Hybrid Functionals, ADMM》— Matt Watkins（Univ. of Lincoln），Ghent workshop 2019-03-12（43 页）

作者自己声明：**"these slides are basically his reformatted"**（T05 P43）——本讲义基本是
**Sanliang Ling（Nottingham）**幻灯片的重新排版，所以它代表的是 CP2K 开发圈内部的"标准讲法"。

教学弧线（五段）：

| 段 | 页 | 教什么 |
|---|---|---|
| ① 动机 | T05 P2–P6 | 杂化是什么、为什么值得上（热化学 MAE、带隙 MAE 的**定量**对照表） |
| ② **成本阶梯** | T05 P7–P15 | HFX 的 4 中心 ERI 为什么 O(N⁴)，CP2K 用**置换对称 / Schwarz 筛选 / 密度矩阵筛选**三级把它压到 O(N)；再把库仑势分四类（全局 / 距离分离 / 截断 / 截断+长程修正），各自对应哪族泛函、哪个关键字、什么坑 |
| ③ **ADMM 原理与实现** | T05 P16–P22 | 辅助密度矩阵的公式推导（ADMM1 链式法则）、三种辅助密度矩阵构造法、ADMM 力的实现状态、校正泛函选择 |
| ④ **辅助基组与实操** | T05 P23–P32 | ADMM 基命名学（FIT3 系 / FIT10–13）、7 条通用提醒、**两个带积分数与带隙的成本-精度对照表**、完整输入骨架、**输出里 `HFX_MEM_INFO` 怎么读** |
| ⑤ 案例与展望 | T05 P33–P43 | TiO₂ 极化子（~1000 原子杂化）、ADMM 用作嵌入、Jacob's Ladder 之外的 MP2/RPA/GW |

**这份材料最稀缺的东西 = 数字**：T05 P26/P27 给出"杂化 vs ADMM 各花多少积分、带隙差多少 eV"，
T05 P31 给出一份真实输出的 ERI 内存账（21290 MiB / 压缩因子 8.14）。

### T06《Parallelization, Automatization, Input Magic》— Tiziano Müller（UZH），UGent workshop 2019-03-11~13（42 页）

**PDF 内标题为 "CP2K: Automation, Scripting, Testing"**（T06 P1）。两栏大纲（T06 P2）＝九块：

安装（toolchain/Spack）→ 验证（make test / dashboard）→ 可复现（`-c`/`-e`/输出捕获/归档）→
输入生成（GUI / 脚本 / 结构格式）→ **CP2K 预处理器（@INCLUDE/@SET/@IF/@PRINT）** →
"Run" 自动化（Farming / AiiDA / 调度器）→ 集成（Phonopy / PyRETIS / i-PI）→
**基组验证（Deltatest）** → **性能优化（TIMING 读法 + 优化准则）**。

教学弧线：**"一个人怎么把成百上千个 CP2K 作业可靠地跑出来、验证出来、并且说清用的基组靠不靠得住"**。
它不讲并行度调优，讲的是**工程化**——这恰好是 A–F 层（决策/实战）与 G 层（官方参考）之间的空白。

---

## 2. 逐节要点（带页码）

### 2.1 T05 逐页

| 页 | 要点（原文口径） |
|---|---|
| T05 P1 | 封面：Matt Watkins，School of Mathematics and Physics, University of Lincoln；`12/03/2019`；来源 `mattatlincoln.github.io/talks/GhentWorkshop/` |
| T05 P2 | **什么是杂化**（Global Hybrid functionals）："mixing non-local Hartree-Fock exchange with semi-local DFT exchange"，`E_XC = αE_X^HFX[ψ_i] + (1−α)E_X^DFT[ρ] + E_C^DFT[ρ]` |
| T05 P3 | **为什么需要杂化（实践动机）**：改善热化学（原子化能、生成焓）；改善晶格常数、表面能、电离势、**带隙**；对**局域态与关联态**给出定性正确的描述 |
| T05 P4 | 理论动机：adiabatic connection；单电子能级的**不连续**（图，无正文） |
| T05 P5 | **原子化能 MAE (G2) / eV**：SVWN **5.2**、LSD(SVWN5) **3.6**、PBE **0.73**、BLYP **0.31**、B3LYP **0.13**、PBE0 **0.21**（Scuseria et al., JCP 110, 5029 (1999)） |
| T05 P6 | **带隙 MAE / eV**（LSDA / PBE / TPSS / HSE）：ME −1.14 / −1.13 / −0.98 / **−0.17**；MAE 1.14 / 1.13 / 0.98 / **0.17**；rms 1.24 / 1.25 / 1.12 / **0.34**；Max(+) −/−/−/0.32；Max(−) −2.30 / −2.88 / −2.66 / −0.72（Scuseria et al., JCP 123, 174101 (2005)） |
| T05 P7 | **CP2K 里的定位**：GGA 是**电子密度**的泛函 `E[ρ]=Ts+J+E_XC[ρ]+∫vρ`；杂化是**密度＋双粒子密度矩阵（轨道）**的泛函；同一 `E_XC` 公式（Guidon, Hutter, VandeVondele, JCTC 6, 2348 (2010)） |
| T05 P8 | **HFX 能量**：`E_X^HFX[P] = −½ Σ P_μσ P_νσ (μν\|λσ)`，`P_μν = Σ_i C_μi C_νi = CCᵀ`；4 中心双电子积分（ERI）"naively scaling **O(N⁴)**" |
| T05 P9 | **置换对称**：`(μν\|λσ)=(νμ\|λσ)=(νμ\|σλ)=(μν\|σλ)=(λσ\|μν)=…`（8 重）⇒ `O(N⁴) → (1/8)O(N⁴)`（Guidon et al., JCP 128, 214104 (2008)） |
| T05 P10 | **积分筛选：Schwarz 不等式** `\|(μν\|λσ)\| ≤ \|(μν\|μν)\|^½ \|(λσ\|λσ)\|^½` ⇒ `(1/8)O(N⁴) → O(N²)`；对应关键字 **`EPS_SCHWARZ`**（`&HF &SCREENING`） |
| T05 P11 | **密度矩阵筛选** `P_max × \|(μν\|μν)\|^½\|(λσ\|λσ)\|^½ ≤ ε_Schwarz`，`P_max = max{\|P_μλ\|,\|P_μσ\|,\|P_νλ\|,\|P_νσ\|}` ⇒ "finally **linear scaling O(N²)→O(N)**"；关键字 **`SCREEN_ON_INITIAL_P`**。补充：`P_max` 是最大密度矩阵元；**通常用上一 SCF 步的密度矩阵做下一步的筛选**，"use **pre-converged GGA density matrix**"；"**very useful for DFT molecular dynamics simulations using hybrid functionals**" |
| T05 P12 | 相互作用势 ①：标准库仑 `g(r)=1/r` → **global hybrid**；`&INTERACTION_POTENTIAL / POTENTIAL_TYPE`。注：气相好算；**周期性体系受可积奇点困扰，k 点求和的收敛需要专门方法** |
| T05 P13 | ② **距离分离** `g(r)=erfc(ωr)/r + erf(ωr)/r` → HSE06 等。两个关键提醒：**"If omega is not large enough very large cells might be needed for HSE calculations at the Γ point"**；**"Costs are very different from plane-wave implementations – HSE is not typically cheaper than PBE0"** |
| T05 P14 | ③ **截断库仑** `g(r₁₂)=1/r₁₂ (r₁₂≤R_c) else 0` → **PBE0-TC** 族；`R_c` 由 **`CUTOFF_RADIUS`** 指定；"Truncation is mainly for solid-state environments and avoids numerical problems with point global hybrid calculations"；**"R_C must be smaller than half the smallest cell dimension"** |
| T05 P15 | ④ 截断＋**长程修正**（补回截断丢掉的交换能）→ **PBE0-TC-LRC** 族；对应 `&XC_FUNCTIONAL &PBE_HOLE_T_C_LR` 子段（Guidon et al., JCTC 5, 3010 (2008)） |
| T05 P16 | **ADMM 的出发点**：`E[ρ]=Ts+J+E_XC[ρ,P]+∫vρ`；引入辅助密度矩阵 `P̂ ≈ P`，则 `E_X^HFX[P] = E_X^HFX[P̂] + (E_X^HFX[P] − E_X^HFX[P̂]) ≈ E_X^HFX[P̂] + (E_X^DFT[P] − E_X^DFT[P̂])`（**把"主-辅差"用 GGA 交换来估**） |
| T05 P17 | **ADMM 仍是 KS 理论**：`E_total = E[P] + Ẽ[P̂]`；`K_total = ∂E/∂P + ∂Ẽ[P̂]/∂P = K + (∂Ẽ/∂P̂)(∂P̂/∂P)`（链式法则），自洽求解 `K_total C = S C ε`。括注 **"Simplest case given here, ADMM1"** |
| T05 P18 | 辅助密度矩阵构造 **①（无约束）**：找 `Ĉ` 使**主/辅基下占据波函数的平方差最小** `Σ_i∫(ψ_j−ψ̂_j)²dr`；对应 **`ADMM_PURIFICATION_METHOD NONE`** |
| T05 P19 | 构造 **②（正交归一半数约束）**：同上目标函数 + 拉格朗日乘子项 `Σ_kl Λ_kl(∫ψ̂_kψ̂_l dr − δ_kl)`；Λ 是强制正交归一的乘子矩阵；对应 **`ADMM_PURIFICATION_METHOD MO_DIAG`** |
| T05 P20 | 构造 **③（总电荷约束）**：`W = Σ_i⟨(i−ĩ)²⟩ + λ(Q − Σ_i⟨ĩ²⟩)`；对应关键字 **`EXCH_SCALING_MODEL`**（Merlot et al., JCP 141, 094101 (2014)） |
| T05 P21 | **ADMM 力**：`dE/dR = dE[P]/dR + dẼ[P̂]/dR`，`P̂C = AC`，`Û = dẼ[P̂]/dĈ = K̂Ĉ`，最终 `dẼ[P̂]/dR = Û[CΛ^{−1/2}] + Û[ACΛ^{−1/2}]`（ab 分量）。**"Forces for MO_Diag and non-purified ADMM implemented"**；**"Linear algebra can get expensive for larger systems (reason for contracted auxiliary basis sets)"** ← 这解释了为什么要有 cFIT 系列 |
| T05 P22 | **交换校正泛函可换**：`E_X^DFT` 可以是 **B88 / PBE / OPTX / KT3X**；关键字 **`EXCH_CORRECTION_FUNC`** |
| T05 P23 | **ADMM 基组（主族）**：最初只有 H–Cl、按原子计算优化。命名：**FIT3**＝每个价轨道 3 个高斯指数；**cFIT3**＝FIT3 的收缩；**pFIT3**＝FIT3＋极化函数；**cpFIT3**＝cFIT3＋极化；**aug-FIT3 / aug-cFIT3 / aug-pFIT3 / aug-cpFIT3**＝再加一个"弥散"函数。文件：`$CP2K/cp2k/data/BASIS_ADMM` |
| T05 P24 | **ADMM 基组（过渡金属）**：非收缩 **FIT10 = 4s+3p+3d**；**FIT11 = 4s+3p+3d+1f**；**FIT12 = 4s+3p+4d+1f**；**FIT13 = 4s+4p+4d+1f**；收缩版 **cFIT10/cFIT11/cFIT12/cFIT13**（**double-ζ 质量**）。注：**主族元素的 ADMM 基名字略有不同，且通常第一个 ADMM 基不含极化函数**；文件 `$CP2K/cp2k/data/BASIS_ADMM_MOLOPT`（Ling & Slater, unpublished） |
| T05 P25 | **一般性提醒（7 条，逐字）**：① Always check the convergence of **CUTOFF**；② Always check the convergence of **properties**（如晶格参数、带隙）w.r.t. **supercell sizes**；③ **Always start from pre-converged GGA (e.g. PBE) wavefunction and geometry**；④ Always check the convergence of **primary and ADMM basis sets** —— start from a small basis and gradually increase the size；⑤ **ADMM has only been implemented for use with GPW**；⑥ **Only ADMM1 will work with some other functionality (smearing, TDDFPT)** |
| T05 P26 | **例：金刚石带隙**（表，逐字）：PBE(PBS) — / 4.17 eV；PBE(ABS) — / 4.37；**PBE0(PBS) 40,787,850,778,591 / 6.07**；**PBE0(ABS) 23,561,509,497 / 6.25**；**PBE0 ADMM1 24,816,897,009 / 6.03**；**PBE0 ADMM2 24,795,460,638 / 6.02**（Guidon 2010）。⇒ ADMM1/2 的积分数与 "ABS" 同量级（~2.4×10¹⁰），带隙 6.02–6.03 vs 全精度 6.07/6.25 —— **误差 ~0.05 eV 量级换取一个数量级以上的积分削减**（PBS 列数字异常，见 §7） |
| T05 P27 | **例：硅带隙**（表，逐字）。上半（固定 **cFIT3** ADMM 基，3×3×3 超胞 216 原子）：截断半径 **0.2 nm → 1.16 eV / 77,799,946,176**；**0.4 → 1.54 / 154,325,979,000**；**0.6 → 1.71 / 265,868,148,312**；**0.8 → 1.78 / 422,457,823,080**。下半（固定 **8 Å 截断半径**，3×3×3 超胞 216 原子）：**cFIT3 → 1.16 / 422,457,823,080**；**FIT3 → 1.80 / 424,426,850,352**；**pFIT3 → 1.98 / 1,447,428,361,680**；**Ref. (VASP) 1.93**（Ling & Slater unpublished；Paier et al., JCP 124, 154709 (2006)） |
| T05 P28 | **泛函定义**：`E_XC^PBE0−TC−LRC = aE_X^HF,TC(R_c) + aE_X^PBE,LRC(R_c) + (1−a)E_X^PBE + E_C^PBE`；`E_XC^HSE = aE_X^HF,SR(ω) + (1−a)E_X^PBE,SR(ω) + E_X^PBE,LR(ω) + E_C^PBE`。**"'Empirical' parameters: a, R_c and ω"**；并吐槽 **"note the 0 in PBE0 stands for 0 empirical parameters…"**（即 PBE0-TC-LRC / HSE 都已引入经验参数） |
| T05 P29 | **ADMM 计算输入骨架**（逐字）：`BASIS_SET_FILE_NAME ./BASIS_MOLOPT` **＋ `BASIS_SET_FILE_NAME ./BASIS_ADMM`**（两行）、`WFN_RESTART_FILE_NAME ${project}-RESTART.wfn`、`&SCF SCF_GUESS RESTART`、`&AUXILIARY_DENSITY_MATRIX_METHOD METHOD BASIS_PROJECTION / ADMM_PURIFICATION_METHOD MO_DIAG`。注：**"The syntax for the AUX basis set changed (after 4.1?) before that it would be AUX_FIT_BASIS_SET ***"** |
| T05 P30 | **PBE0-TC-LRC vs HSE 输入对照**（完整 &XC 段，见 §4.1）。检索自 `$CP2K/cp2k/tests/QS/regtest-admm-1/2/3/4` |
| T05 P31 | **输出解读**：`HFX_MEM_INFO\| Est. max. program size before HFX [MiB]: 563`；随后是 `*** WARNING in hfx_energy_potential.F:600 :: The Kohn Sham matrix is not 100% occupied … Try to decrease EPS_PGF_ORB and EPS_FILTER_MATRIX in the QS section … https://www.cp2k.org/faq:hfx_eps_warning ***`；再往下逐行：cart. primitive ERI's calculated **218,851,035,670**；sph. ERI's calculated **152,193,561,473**；stored in-core **22,711,518,963**；stored on disk **0**；calculated on the fly **0**；**Total memory consumption ERI's RAM [MiB]: 21290**；**Whereof max-vals [MiB]: 1516**；**Total compression factor ERI's RAM: 8.14**；disk 0 / 0.00；**Size of density/Fock matrix [MiB]: 764**；**Size of buffers [MiB]: 118**。页脚结论：**"Number of sph. ERI's calculated on the fly: should ideally be zero. We want to keep ERIs in memory during the SCF loop."** |
| T05 P32 | **额外提醒**：ERI 及其解析导数由 **Libint** 计算（见 `$CP2K/cp2k/INSTALL`）；**大体系杂化吃内存 → 增大 `MAX_MEMORY` 或用更多 MPI 进程**；**"Note MAX_MEMORY is the memory per MPI process for ERIs, you must leave space for operating system and rest of the CP2K calculation."**；**极大杂化算例请用混合 MPI/OpenMP 版（`cp2k.psmp`）** |
| T05 P33 | 案例：**"TiO₂ is everyone's favourite material – hybrid calculations with ~1000 atoms and good basis sets using CP2K"**（Yim et al., PRL 117, 116402 (2016)） |
| T05 P34–P40 | TiO₂ 极化子（Elmaslmane et al., JCTC 2018, 14, 3740）：**7 页几乎全图、文字只有标题/图注**（T05 P33 的"~1000 原子"是本段的量级依据） |
| T05 P41 | **Fun and games**：ADMM 不只是杂化的近似 —— 还可用作**嵌入**（"smaller basis sets / no basis sets on some atoms"）；Ling et al., JPCC 117, 5075 (2013)（MgO on Ag(001)） |
| T05 P42 | **Up Jacob's Ladder**：用**未占据**轨道信息可构造更高级泛函（double hybrid、RPA）；练习链接 `cp2k.org/exercises:2017_uzh_cp2k-tutorial:hybrid`；**纠正**：**"The syntax for the AUX basis set changed, use `BASIS_SET AUX_FIT cFIT3` instead of `AUX_FIT_BASIS_SET ***` in the example."**；CP2K 还实现了 MP2 / RPA / GW（附练习链接） |
| T05 P43 | 致谢：**本讲义基本是 Sanliang Ling（Nottingham）幻灯片的重新排版**；Ling 的讲义另有色散校正泛函的细节（`cp2k-uk-stfc-june-2018-sanliang-ling.pdf`） |

### 2.2 T06 逐页

| 页 | 要点 |
|---|---|
| T06 P1 | 标题 **"CP2K: Automation, Scripting, Testing"**；Tiziano Müller，`tiziano.mueller@chem.uzh.ch`，Dept. of Chemistry UZH；CP2K Workshop @ UGent，**11.–13. March 2019** |
| T06 P2 | **大纲（两栏拼版）**：Full Input generation: GUIs｜Preparations / Full Input generation: Scripting｜Installation / **CP2K Preprocessor**｜Verification / **"Run" Automation**｜Reproducibility / Batch Processing｜Syntax-Checking & Input-Debugging / Workflows｜Archival / Integration: Phonopy, PyRETIS, i-PI｜Input Generation / Basis Set Verification｜Structure-only: Supported formats / **Performance Optimisation** |
| T06 P3 | 分隔页：Preparations |
| T06 P4 | **toolchain 编译**：`git clone --recursive https://github.com/cp2k/cp2k.git` → `cd cp2k/tools/toolchain` → `./install_cp2k_toolchain.sh`。默认用**系统编译器/链接器/MPI**（"MPI is detected and it appears to be OpenMPI"、"nvcc not found, disabling CUDA by default"）；**"Compiling with 8 processes"**；生成 `local.sopt/sdbg/ssmp` arch 文件；自动配置 **libxc、libint、libxsmm、ELPA、SIRIUS**；支持 Linux & macOS。收尾：`cp install/arch/* → cp2k/arch/`；`source .../install/setup`；**`make -j 8 ARCH=local VERSION="sopt sdbg ssmp popt pdbg psmp"`** |
| T06 P5 | toolchain 配置：`--install-all` 装全部；`--help` 看更多选项。**"Fortran requires .mod files and code built with same compiler!"**；重新配置后**建议手工清理 `build/`、`install/`**；查 `cp2k.org/dev:compiler_support` |
| T06 P6 | **Spack 编译**：`git clone .../spack.git` → `. ./share/spack/setup-env.sh` → `spack install cp2k` → `spack load cp2k`。卖点：科学软件包管理器；需要 Python；**自动检测并复用已有编译器**；递归构建全部前置依赖；**"Installs CP2K and the arch-file used to build it"** |
| T06 P7 | `spack info cp2k`（示例版本 6.1）。**variants 表（逐字）**：`blas [openblas]`（openblas/mkl/accelerate）、**`elpa [off]`**、**`libxc [on]`**、`mpi [on]`、**`openmp [off]`**、`pexsi [off]`、`plumed [off]`、`smm [libxsmm]`（libxsmm/libsmm/blas） |
| T06 P8 | 定位 arch 文件：`spack find -p cp2k` → 在 `.../.spack/archived-files/arch/` 下拿到 `linux-…-gcc.popt`；**"Use Spack arch-file for custom build of CP2K with Spack-installed libraries"**。注意：**默认 Spack 构建除编译器与链接器外的所有依赖；要用系统 MPI 需额外配置** |
| T06 P9 | **验证构建**：`make VERSION=sopt ARCH=local test`。示例输出：`Number of FAILED tests 0 / WRONG 0 / CORRECT 3031 / NEW 0 / Total 3031`，`Summary: correct: 3031 / 3031; 6min`，`Status: OK`，`Regtest took 379.00 seconds`，`Thu Feb 28 15:33:59 CET 2019`。**"Automatically skips unavailable features"**（示例：`Skipping QS/regtest-cdft-hirshfeld-2 : missing required feature : parallel / mpiranks>1`）；多平台结果看 `dashboard.cp2k.org` |
| T06 P10 | 分隔页：Reproducibility |
| T06 P11 | **输入调试与输出捕获**：`cp2k -c your.inp` —— **"Basic issues are found"、"Complex tests only at full runtime"**；技巧：**"Use low cutoffs, limit SCF cycles to get a full check (MAX_SCF, MAX_STEPS, …)"**。输出捕获：`cp2k your.inp \|& tee your.out`；**`cp2k your.inp -o your.out`（production run）**；**"Leave error output handling to batch-system if possible"** |
| T06 P12 | **数据归档**：**`cp2k -e your.inp`** —— **"Full-input: includes current default settings & resolved preprocessor variables"**、**"Can also be used for debugging complex inputs and parsing errors"**。其它产物：`POTENTIAL`、`BASIS_SET`、结构文件（`.xyz`、`.pdb`…）、力场/色散校正参数/DFTB 文件；**`proj-1.restart`（a full input file）**、`proj-pos-1.xyz`（MD/GEO_OPT 轨迹）、`proj-1.ener`（MD 能量、温度…）、`proj-1.cell`（CELL_OPT、NPT MD 的晶胞参数）、`proj-RESTART.wfn`、**`proj-RESTART.kp`**（重启用轨道） |
| T06 P13 | 分隔页：Input Generation |
| T06 P14 | **只给结构的格式**：XYZ（**仅坐标**）、PDB、CIF、**G96/G87（GROMACS）**、**PSF/UPSF（CHARMM）**、**CRD（AMBER）**、**XTL**。注：**"*.restart files have coordinates integrated as &COORD section"** |
| T06 P15 | **Avogadro**：1.x 插件 `github.com/brhr-iwao/libavogadro1cp2k`；2.x 插件 `github.com/svedruziclab/avogadrolibs-cp2k` |
| T06 P16 | **Chimera**：菜单驱动＋可视化；**TETR 做前处理**（几何搭建、**超胞、表面、团簇**）；**LEV00 做分析**（电荷/自旋密度可视化、DOS、声子、IR 谱）；＝ TETR+LEV00 Plugin for Chimera |
| T06 P17 | **PYCP2K**：Python DSL，**关键字与 CP2K 输入文件一一对应**；与 ASE 集成；基于 Python 自动补全引擎。关键能力：**`calc.parse("template.in")` 可以解析一个既有输入文件**（＝Python 侧的模板机制）、`calc.mpi_n_processes = 2`、`create_cell/create_coord` 从 ASE 原子对象生成 `&CELL/&COORD`。示例值：`Eps_default 1.0E-10`、`MGRID Ngrids 4 / Cutoff 300 / Rel_cutoff 60`、`XC_FUNCTIONAL PADE`、`Scf_guess ATOMIC`、`Eps_scf 1.0E-7`、`Max_scf 300`、`DIAGONALIZATION STANDARD`、`MIXING BROYDEN_MIXING / Alpha 0.4 / Nbroyden 8`、`KIND Basis DZVP-GTH-PADE / Potential GTH-PADE-q4`；最后 `calc.write_input_file()` / `calc.run()` |
| T06 P18 | **Python ASE**：强结构搭建工具；**可把已有输入文件片段与结构合并（templating）**；**"Uses cp2k_shell to run CP2K continuously → minimal overhead"**；**可在远端机器上启动 CP2K**。示例：用 `inp="""&FORCE_EVAL &MM &FORCEFIELD &SPLINE …"""` 跑 `force_eval_method="Fist"`；Ar fcc 解析应力 vs 数值应力互验（`calculate_numerical_stress(a, 1e-5)`）；`MDMin(UnitCellFilter(a), dt=0.01).run(fmax=1e-3)` 优化晶胞；用 **Niggli 张量**校验最小化晶胞 |
| T06 P19 | **CP2K 内置输入预处理器（逐字）**：`@INCLUDE 'filename.inc'` 内容在此处插入，**路径相对当前工作目录**；`@SET VAR value` **（重新）定义变量**；`${VAR}` 或 `$VAR` 展开；**`@IF …/@ENDIF` 条件，支持 `==` 与 `/=`（字典序比较）；值为 `0` 或空白判为 FALSE，其它一律 TRUE**；**`@PRINT …` 预处理时打印给定文本** |
| T06 P20 | **预处理器的用法（高吞吐工程布局）**：`HOME/HighThroughputProject/` 下 `base.inp`（内含 `@INCLUDE 'settings.inp'`）+ `structure1/ structure2/ structure3/`，每个子目录各有 `settings.inp` 与 `structure.xyz`；**"start CP2K in this directory"（在 structure2 里启动）**，**"inclusion relative to CWD"**；**settings.inp 里可以再放 `@SET`、其它 `@INCLUDE`，甚至完整的段/关键字** |
| T06 P21 | 分隔页："Run" Automation |
| T06 P22 | **自动化分层图**（六个框）：Shell Scripts｜**Batch Processing（CP2K Farming）**｜Python Scripts｜**AiiDA、atomate**｜Scheduler assisted｜Workflows |
| T06 P23 | **批处理：CP2K Farming（逐字配方）**：`&GLOBAL PROJECT OldMacDonald / PROGRAM FARMING / RUN_TYPE NONE`；`&FARMING NGROUPS 2 ! number of parallel jobs`、**`MASTER_SLAVE ! for load balancing`**、**`GROUP_SIZE 42 ! number of processors per group, default: 8`**；`&JOB JOB_ID 1 ! optional, required for dependencies / DIRECTORY dir-1 / INPUT_FILE_NAME water.inp / OUTPUT_FILE_NAME water.out`；第二个 `&JOB DEPENDENCIES 1 / DIRECTORY dir-2 / INPUT_FILE_NAME water.inp / OUTPUT_FILE_NAME more_water.out`。旁注：**"Jobs are run inside the same CP2K process"、"MPI gets initialized once → reduced startup time"、"Useful for many small jobs"** |
| T06 P24 | **Workflows: AiiDA**：Python 的 **Automated Interactive Infrastructure and Database**；**强数据溯源（Data Provenance）**；PostgreSQL 数据库＋文件仓库；Python 之上的工作流引擎；插件架构（**CP2K 插件**、高斯基组与赝势插件，更多见 AiiDA Plugin Registry）；Jupyter Notebook 集成；与 **MaterialsCloud** 开放科学平台集成 |
| T06 P25 | **AiiDA 例**：`Code.get_from_string("cp2k").new_calc()`；`calc.label`；`ase.build.molecule('H2O')` → `atoms.center(vacuum=2.0)` → `StructureData(ase=atoms)` → `calc.use_structure(...)`；`ParameterData(dict={'FORCE_EVAL':{'METHOD':'Quickstep','DFT':{'QS':{'EPS_DEFAULT':1.0e-12}}}})`；`calc.set_max_wallclock_seconds(3*60)`；**`calc.set_resources({"num_machines": 4})`**；`calc.set_computer(Computer.get("skitty"))`；`calc.store_all()` → `calc.submit()`。附图："AiiDA Data Provenance Graph" |
| T06 P26 | 分隔页：Integration: Phonopy, PyRETIS, i-PI |
| T06 P27 | **Phonopy**：Python；**基于文件的接口**——解析并生成代码输入（**带原子位移的 CP2K 输入**）；**只需要"已平衡且对称化"的晶体结构**；用**超胞方法**；后处理可产 **DOS、pDOS、热性质、声子能带结构** |
| T06 P28 | **PyRETIS**：Python；**TIS（Transition Interface Sampling）与 RETIS（Replica Exchange TIS）**；**可把 CP2K 当 MD 步的积分器**；产出**穿越概率 / 速率常数** |
| T06 P29 | **i-PI**：通用力引擎；聚焦**路径积分分子动力学**；**与力引擎通过 socket（网络套接字）通信**；还有大量其它方法；产出 MD 轨迹 |
| T06 P30 | 分隔页：Basis Set Verification |
| T06 P31 | **基组验证·挑战①**：引用 **"For GTOs, a triple-ζ quality basis has mean errors of ~10 kcal/mol in total energies, while chemical accuracy is almost reached for a quintuple-ζ basis..."**（Stig Rune Jensen et al., J. Phys. Chem. Lett. 8.7 (2017) 1449–1457）→ 提问 **"Do we really need larger basis sets?"** |
| T06 P32 | **挑战②**：引用 **"We show that by choosing Gaussian basis sets optimized for density functional theory, basis set methods are capable of achieving accuracy comparable to that from the multiwavelet approach..."**（Frank Jensen, J. Phys. Chem. A 121.32 (2017) 6104–6107）→ 回答 **"Not necessarily, just use the right one."** |
| T06 P33 | **Deltatest（Δ-gauge）方法**：度量＝**两条 V/E 曲线的差**，`Δ(a,b) = sqrt( ∫_{0.94V₀}^{1.06V₀} (E_b(V)−E_a(V))² dV / (0.12 V₀) )`；**40+ 种"方法"、71 种元素（H–Rn 元素晶体）**；**DFT、PBE 泛函**；**以全电子计算为参考**（Lejaeghere et al., Science 351, aad3000 (2016)；Crit. Rev. Solid State 39.1 (2014) 1–24） |
| T06 P34 | **Deltatest 结果（CP2K MOLOPT）**：三张图 —— ① **CP2K 的 DZVP-SR / TZVP-SR / TZV2P-SR / TZV2PX-SR vs Abinit**；② 同上但**非 SR** 版本 vs Abinit（横轴 H C N O F Si P S Cl Cu Br）；③ **CP2K vs WIEN2k** 与 **Abinit, GTH-PBE vs WIEN2k**；图中标注 **"↑ non-SR MOLOPT basis sets"** |
| T06 P35 | 同上，放大版＋**"larger Basis Set"** 箭头：**DZVP → TZVP → TZV2P → TZV2PX 偏差系统性下降** |
| T06 P36 | **结论与展望（逐字要点）**：MOLOPT 基组**适合固体计算**；**"Larger-ζ MOLOPT basis sets systematically improve results"**；**"Basis set related errors in same order as pseudization error"**；**"For some elements: basis set inadvertently compensates pseudopotential error"**；完整数据与工作流将发表在 `materialscloud.org` 的 Discovery 区；**全电子 Peintinger 基组的测试在进行中**；更多基准即将发布 |
| T06 P37 | 分隔页：Performance Optimisation |
| T06 P38 | **CP2K TIMING 示例（表头逐字）**：`SUBROUTINE / CALLS / ASD / SELF TIME (MAXIMUM, AVERAGE) / TOTAL TIME (MAXIMUM, AVERAGE)`；`CP2K 1 1.0 0.847 0.890 2709.628 2709.629`（总时长 ≈ **2710 s**）。代表行：`fft3d_ps` **18285** 次、ASD **12.3**、selftime max **615.774**/avg **642.063**、totaltime max 1002.533/avg 1028.016；`mp_waitany` **141448** 次、ASD 10.7、selftime **140.483/179.715**；`pw_scatter_p` 8402、ASD 13.3、168.017/174.224；`mp_alltoall_z22v` 18285、ASD 14.3、173.031/**215.341**；`calculate_rho_elec` 1262、ASD 6.0、19.360/**65.700**。旁注词表：`pw`=Planewave、`fft`=Fast Fourier Transformation、`mp`=Message Passing (MPI)、`qs`=Quickstep、`scf`=Self-consistent field、**`ASD` = measure for how deeply nested a function is**、**`SELF TIME` = time spent in routine and not separately timed subroutines** |
| T06 P39 | **时间分析准则（4 条，逐字）**：① **"Check that I/O routines are < 50% of total runtime"** → 记住 **Amdahl 定律：scaling flattens eventually**；→ **"Do you really need to write so much/often?"**；→ **"Are you running in the right directory?"**；② **"Compare Average and Maximum values"** → 差异大 = **"nodes are waiting for single rank to finish"**；③ **"Check settings for respective sections"** → **"Are you using the right algorithms?"** |
| T06 P40 | **一般准则**：**"Optimization starts with you: Biggest gains by proper setup"** —— ① **Cell size**；② **SCF settings, preconditioner**；③ **Choice of basis set**；④ **ADMM**；**"No universal recipe, check scaling of your system"**；**"Run a small number of MD or GEO_OPT steps"**；**"Turn off outer-SCF, keep inner-SCF fixed"**；自己编译时：**用厂商提供的 BLAS/LAPACK/FFTW3**、**构建并使用 libxsmm、ELPA**；`CUDA support available, improvements are coming` |
| T06 P41 | **求助渠道**：`cp2k.org`（Exercises、Lecture Slides）｜`manual.cp2k.org`（Input File reference）｜**`<CP2K-SOURCE>/tests`（Minimal Working Examples）**｜Google Group｜GitHub issue tracker |
| T06 P42 | Thank you |

---

## 3. 核心逻辑链（重点）

### 3.1 杂化泛函：为什么比 GGA 贵那么多

**逻辑链（T05 P7→P11，五步，每一步都有页码）**

1. **贵在公式本身**（T05 P8）：GGA 的 `E_XC` 只是密度的泛函；杂化多了 `αE_X^HFX[ψ_i]`，这一项写成 ERI 形式
   `E_X^HFX[P] = −½ Σ_{λσμν} P_μσ P_νσ (μν|λσ)` —— **四个基函数指标耦合在一起**，朴素标度 **O(N⁴)**。
2. **第一次降价：置换对称**（T05 P9）：ERI 的 8 重置换对称 ⇒ 只需算 1/8，`O(N⁴) → (1/8)O(N⁴)`。**只省常数，不改标度。**
3. **第二次降价：Schwarz 不等式筛选**（T05 P10）：`|(μν|λσ)| ≤ |(μν|μν)|^½|(λσ|λσ)|^½`，
   把"积分上界小于阈值"的四元组整块丢掉 ⇒ **`O(N²)`**。开关：`&HF &SCREENING EPS_SCHWARZ`。
4. **第三次降价：密度矩阵筛选**（T05 P11）：`P_max × [Schwarz 上界] ≤ ε` ⇒ **线性标度 O(N)**。
   关键在 `P_max` 从哪来 —— 讲义明确：**用上一步 SCF 的密度矩阵，最好用"预收敛的 GGA 密度矩阵"**。
   这直接推出 T05 P25 的第③条操作建议：**先跑 PBE 收敛波函数与几何，再开杂化**（`SCF_GUESS RESTART` + `WFN_RESTART_FILE_NAME`，T05 P29）。
5. **还有两条"不改标度但极重要"的成本因素**：
   - **周期性**（T05 P12–P14）：`1/r` 在 PBC 下有可积奇点，k 点求和收敛慢；**截断库仑（PBE0-TC）就是为了在固体里绕开这个问题**，代价是丢掉长程交换（T05 P15 用 LRC 补）。
   - **基组质量**（T05 P32 与 P8 的 ERI 定义）：HFX 的成本随基函数数四次方涨，**弥散/高角动量/强收缩基组最贵** —— 这正是 ADMM 存在的理由（T05 P16、P21 末句）。

**一句话**：`O(N⁴) → N⁴/8 → O(N²) → O(N)`，**前两步是"算法常数"，第三步（密度矩阵筛选）才真正把杂化在凝聚相里变成线性标度**，
而"用预收敛 GGA 密度矩阵"既是效率手段也是精度前提。

### 3.2 什么时候值得上杂化（教材给的定量依据）

| 目标 | 依据（页） | 数值 |
|---|---|---|
| 分子热化学（原子化能） | T05 P5 | PBE **0.73** → B3LYP **0.13** / PBE0 **0.21** eV（MAE，G2 集） |
| **带隙 / 半导体** | T05 P6 | PBE **1.13** → **HSE 0.17** eV（MAE）；rms 1.25 → **0.34** |
| 局域/关联态（极化子、缺陷） | T05 P3、P33–P40 | 定性正确性；教材用 TiO₂ 极化子（~1000 原子）做示范 |
| 成本量级 | T05 P8–P11、P26/P27 | 见 §3.1 与下表 |

**成本-精度实测（T05 P26，金刚石）**：

| 方法 | 积分数 | 带隙 [eV] |
|---|---|---|
| PBE (PBS) | — | 4.17 |
| PBE (ABS) | — | 4.37 |
| PBE0 (PBS) | 40,787,850,778,591 ⚠️ | 6.07 |
| PBE0 (ABS) | 23,561,509,497 | 6.25 |
| **PBE0 ADMM1** | **24,816,897,009** | **6.03** |
| **PBE0 ADMM2** | **24,795,460,638** | **6.02** |

⇒ ADMM 与 "ABS" 同一量级（~2.4×10¹⁰ 个积分），**带隙与全精度差 0.04–0.22 eV**，
却把积分从 10¹³ 量级拉到 10¹⁰ 量级（**PBS 列的位数看着异常，但已查证数字无误**，
详见 §7 第 1 条：原论文 Table 6 逐字如此，且论文自述 ADMM 比 PBS 省 **3 个数量级**）。

**两把"调成本"的旋钮（T05 P27，硅 3×3×3 / 216 原子，PBE0-TC-LRC）**：

- **旋钮 A：截断半径**（固定 cFIT3）0.2 → 0.4 → 0.6 → **0.8 nm（= 8 Å）**：
  带隙 1.16 → 1.54 → 1.71 → **1.78 eV**，积分数 7.78×10¹⁰ → 1.54×10¹¹ → 2.66×10¹¹ → **4.22×10¹¹**。
  ⇒ **R_c 越大越准也越贵，且 0.8 nm 仍未收敛到 VASP 的 1.93 eV**。
- **旋钮 B：ADMM 辅助基**（固定 8 Å）：cFIT3 → FIT3 → pFIT3：
  积分数 4.22×10¹¹ → 4.24×10¹¹ → **1.45×10¹²**（pFIT3 贵 3.4 倍）；
  带隙 **1.78 → 1.80 → 1.98**，参考 VASP **1.93** ⇒ **pFIT3 最接近参考**。
  > ⚠️ **更正记录（原写 `cFIT3 1.16 ⚠️`）**：该 `1.16` 是 **T05（2019 Ghent 版）下表的转录错误**，
  > **原值是 `1.78`**。依据：更早的同一份讲义 **Ling 2015 CECAM（`ling_hybrids.pdf`）第 15 页**，
  > 该行写 `cFIT3` 带隙 **1.78**、积分数 **422457823080** —— 与本节旋钮 A 的 0.8 nm 行**逐位相同**，
  > 两处本就是**同一组数据**（同为 8 Å / 3×3×3 / 216 atoms）。原表因此**不是**"两表设置不同"，
  > 而是**转录时抄错了一格**。详见 §7 第 2 条（含页码与原文出处）。

**因此"什么时候值得上杂化"的教材逻辑是**：
① 目标是带隙/局域态/热化学精度（T05 P3、P5、P6）；
② 上之前先把**几何与波函数用 GGA 收敛好**（T05 P25③、P11）；
③ **CUTOFF 与超胞尺寸先各自收敛**（T05 P25①②）——因为杂化的带隙对 R_c 与超胞都很敏感（T05 P27）；
④ **主基组与 ADMM 辅助基都要各自收敛**，从小基组往大试（T05 P25④、P27 的 FIT3→pFIT3）。

### 3.3 ADMM：辅助基组的角色、取舍、怎么选、坑

**角色（T05 P16–P17）**：HFX 的昂贵项是 `E_X^HFX[P]`。ADMM 把它拆成
`E_X^HFX[P̂]`（**在更小的辅助基上算 4 中心积分**）＋ `E_X^DFT[P] − E_X^DFT[P̂]`（**用 GGA 交换补主/辅差**）。
形式上仍是 KS 理论（T05 P17 的链式法则 → `K_total C = SCε`），所以它可以无缝塞进既有 HFX 代码，甚至线性标度实现里。

**精度-速度取舍的"物理旋钮"是辅助基组的大小**：
- 辅助基越小 → `E_X^HFX[P̂]` 越便宜，但"主/辅差"越大、GGA 校正要补的越多 → 精度越差（T05 P27：cFIT3 的带隙偏离参考最远）；
- 辅助基越大 → 越准但越贵（T05 P27：pFIT3 的积分数是 cFIT3 的 3.4 倍，带隙反而最接近参考）；
- **T05 P21 末句给出机制层面的原因**："Linear algebra can get expensive for larger systems (**reason for contracted auxiliary basis sets**)" ⇒ **cFIT 系（收缩）存在的意义就是省线性代数**，而不是省积分。

**怎么选辅助基（教材给的选择学，T05 P23–P24）**：

| 元素范围 | 家族 | 命名逻辑 | 文件 |
|---|---|---|---|
| 主族（最初 H–Cl） | **FIT3 / cFIT3 / pFIT3 / cpFIT3 / aug-…** | FIT3＝每价轨道 3 个高斯指数；c＝收缩；p＝+极化；aug＝+弥散 | `data/BASIS_ADMM` |
| 过渡金属 | **FIT10–FIT13 / cFIT10–cFIT13** | FIT10 = 4s+3p+3d；FIT11 = +1f；FIT12 = 4s+3p+4d+1f；FIT13 = 4s+4p+4d+1f；**c 版是 double-ζ 质量** | `data/BASIS_ADMM_MOLOPT` |

两条命名学提醒（T05 P24）：**主族元素的 ADMM 基名字与过渡金属"略有不同"**；**通常"第一个" ADMM 基不含极化函数**（所以别把第一个当最准的用）。
选择流程（T05 P25④＋T05 P27）：**从小基组开始，逐步加大**，并用参考值（或无 ADMM 的小体系）核对。

**输入三件套（T05 P29，逐字）**：
1. 两个基组文件：`BASIS_SET_FILE_NAME ./BASIS_MOLOPT` ＋ `BASIS_SET_FILE_NAME ./BASIS_ADMM`；
2. 每个 `&KIND` 上的 `BASIS_SET AUX_FIT <辅助基名>`（语法见 §6 纠错 4）；
3. `&AUXILIARY_DENSITY_MATRIX_METHOD METHOD BASIS_PROJECTION` + `ADMM_PURIFICATION_METHOD MO_DIAG`（或 `NONE`），以及 `&XC` 里的杂化泛函与 `&HF` 段。

**已知的坑（教材明列，T05 P21/P25/P31/P32）**
1. **`P̂` 的纯化方式会改变 KS 矩阵本征值的含义** —— MO_DIAG 的力已实现，但大体系线性代数会变贵（T05 P21）。
2. **ADMM 只实现于 GPW**；**只有 ADMM1 能与 smearing / TDDFPT 等其它功能共用**（T05 P25⑤⑥）→ 版本敏感，见 §6。
3. **必须查 CUTOFF 收敛、超胞收敛、主基组＋辅助基收敛**（T05 P25①②④）——ADMM 不是"免检"开关。
4. **必须从预收敛的 GGA 波函数/几何出发**（T05 P25③）。
5. **输出警告要看**：`hfx_energy_potential.F:600` 的 "Kohn Sham matrix is not 100% occupied"，指引减小 `EPS_PGF_ORB` 与 `EPS_FILTER_MATRIX`（T05 P31）。**该警告的完整官方解读在 G 层 `08_errors_and_faq.md` §3.8.4，此处只给"教材里它出现在哪一行输出"的位置。**
6. **ERI 内存账要会读**（T05 P31）：先看 `Est. max. program size before HFX [MiB]`，再看
   `Total memory consumption ERI's RAM`（示例 **21290 MiB**）、`Whereof max-vals`（**1516 MiB**）、
   `Total compression factor ERI's RAM`（**8.14**）、`Size of density/Fock matrix`（**764 MiB**）、`Size of buffers`（**118 MiB**）；
   **`calculated on the fly` 理想上必须为 0** —— 非零说明 ERI 没能在 SCF 循环里常驻内存。
7. **`MAX_MEMORY` 是"每个 MPI 进程"的 ERI 内存额度**，必须给操作系统和 CP2K 其余部分留空间（T05 P32）。

### 3.4 并行与 Input Magic（T06 实际教的东西）

> ⚠️ **先纠一个预期**：本 PDF **没有** MPI/OpenMP/`GROUP_PARTITION` 的并行层次讲解（见 §6 纠错 1）。
> 它教的"并行"是**任务级并行（同一进程里跑多组作业）**与**时序判读**；"Input Magic"＝**内置预处理器的模板化**。

**A. 并行层次（教材实际给出的三层）**

| 层 | 机制 | 教材出处 | 适用 |
|---|---|---|---|
| **进程内多作业** | **CP2K Farming**：`PROGRAM FARMING` + `RUN_TYPE NONE`，`NGROUPS`（并行作业数）/`GROUP_SIZE`（**每组处理器数，默认 8**）/`MASTER_SLAVE`（负载均衡）/`&JOB`（可加 `DEPENDENCIES` 串依赖） | T06 P23 | **大量小作业**：MPI 只初始化一次、作业在同一进程内跑 ⇒ 启动开销被摊掉 |
| **作业级调度** | Shell 脚本 / Python 脚本 / **AiiDA / atomate** / **Scheduler assisted**（PBS/Slurm 之类） | T06 P22、P24–P25 | 成百上千个独立算例、需要溯源与重跑 |
| **构建级选择** | toolchain 的 `VERSION="sopt sdbg ssmp popt pdbg psmp"`；Spack 的 `mpi [on]` / `openmp [off]` variants；缺 feature 的测试会被自动跳过（`parallel`、`mpiranks>1`） | T06 P4、P7、P9 | **"什么设置配什么机器"在 T06 里只有这一层**：单机串行 sopt/ssmp、MPI 用 popt/psmp、调试用 sdbg/pdbg；**T05 P32 补一句："极大杂化算例用 `cp2k.psmp`"** |

**B. `@SET/@INCLUDE` 模板机制与"输入魔法"（T06 P19–P20，本节是 H 层增量最高的部分之一）**

- 指令全集（T06 P19）：`@INCLUDE` / `@SET` / `${VAR}` 或 `$VAR` / **`@IF…@ENDIF`（`==`、`/=`，**0 或空白 = FALSE，其它 = TRUE**）** / **`@PRINT`**。
- **`@INCLUDE` 的路径相对"当前工作目录"**，不是相对被包含文件所在目录 —— 这一点决定了整套目录布局：
  ```
  HighThroughputProject/
  ├── base.inp                 @INCLUDE 'settings.inp'
  ├── structure1/{settings.inp, structure.xyz}
  ├── structure2/{settings.inp, structure.xyz}   ← 在这里启动 CP2K
  └── structure3/{settings.inp, structure.xyz}
  ```
  **同一份 `base.inp`＋每目录一份 `settings.inp` ⇒ 一次提交跑遍所有结构**（T06 P20）。
- **`settings.inp` 里可以再放 `@SET`、再 `@INCLUDE`，甚至完整的段/关键字**（T06 P20）⇒ 模板可以分层：全局参数 → 体系参数 → 结构文件。
- 于是"输入魔法"的三件套就是：**`@SET` 参数化路径/阈值 + `@INCLUDE` 外挂坐标与参数 + `@IF` 按体系切换分支**；
  `@PRINT` 用来在预处理阶段打印实际生效的文本（调试模板时确认变量展开成了什么）。
- **`cp2k -e your.inp`** 是这套机制的安全网：导出**含当前默认值＋已解析预处理变量**的完整输入（T06 P12）——
  **模板越复杂，越应该先 `-e` 看一眼实际生成的东西**。

**C. 性能判读链（T06 P38–P40）**
`跑一次 → 读 TIMING 表（CALLS/ASD/SELFTIME/TOTALTIME）→ ① I/O 是否 < 50% ② Average vs Maximum 差多大 ③ 算法/段设置对不对 → 再回去改设置`；
设置优先级（T06 P40）：**胞大小 → SCF/预条件 → 基组 → ADMM**；
"没有万能配方"，**用少量 MD/GEO_OPT 步做标度测试**，并把 **outer-SCF 关掉、inner-SCF 固定**（否则每次自洽步数不同，测不出可比时间）。

---

## 4. 可执行要点（照抄可运行）

> ⚠️ 以下均照抄教材原文（含其缺行/口径问题，已在括号里标注）。
> **T05 P30 的代码块在 PDF 文本层里没有 `FRACTION` 行** —— 已查清：**不是"少一行"，而是从
> `&END INTERACTION_POTENTIAL` 起**两栏都被整段裁掉**（含 `&MEMORY` / `MAX_MEMORY` / `EPS_STORAGE_SCALING` / **`FRACTION 0.25`** / 三个 `&END`）。
> **原件（Ling 2015 CECAM `ling_hybrids.pdf` P29）写有 `FRACTION 0.25`。**
> ⚠️ **不补会算错**：官方 `FORCE_EVAL/DFT/XC/HF/FRACTION` 的**默认值是 `1.0`**（=100% HFX），
> 漏写就变成纯 HFX 而不是 PBE0-TC-LRC。**照抄时必须自己补上 `FRACTION 0.25`**。详见 §7 第 4 条。
> （原"去 `tests/QS/regtest-admm-1/2/3/4` 取完整输入"的建议也已失效：那两个算例现在不在那些目录里。）

### 4.1 ADMM 计算输入骨架（T05 P29，逐字）

```
&DFT
  …
  BASIS_SET_FILE_NAME ./BASIS_MOLOPT
  BASIS_SET_FILE_NAME ./BASIS_ADMM
  WFN_RESTART_FILE_NAME ${project}-RESTART.wfn
  ...
  &SCF
    ...
    SCF_GUESS RESTART
    ...
  &END SCF
  &AUXILIARY_DENSITY_MATRIX_METHOD
    METHOD BASIS_PROJECTION
    ADMM_PURIFICATION_METHOD MO_DIAG
  &END AUXILIARY_DENSITY_MATRIX_METHOD
  ...
  &XC
    ...
  &END XC
&END DFT
```
每个 `&KIND` 还要加辅助基：**`BASIS_SET AUX_FIT cFIT3`**（T05 P42 明确纠正为这个写法）。

### 4.2 PBE0-TC-LRC（T05 P30 左栏，逐字）

```
&XC
  &XC_FUNCTIONAL
    &PBE
      SCALE_X 0.75
      SCALE_C 1.0
    &END PBE
    &PBE_HOLE_T_C_LR
      CUTOFF_RADIUS 2.0
      SCALE_X 0.25
    &END PBE_HOLE_T_C_LR
  &END XC_FUNCTIONAL
  &HF
    &SCREENING
      EPS_SCHWARZ 1.0E-6
      SCREEN_ON_INITIAL_P FALSE
    &END SCREENING
    &INTERACTION_POTENTIAL
      POTENTIAL_TYPE TRUNCATED
      CUTOFF_RADIUS 2.0
      T_C_G_DATA ./t_c_g.dat
    &END INTERACTION_POTENTIAL
  &END HF
&END XC
```

### 4.3 HSE（T05 P30 右栏，逐字）

```
&XC
  &XC_FUNCTIONAL
    &PBE
      SCALE_X 0.0
      SCALE_C 1.0
    &END PBE
    &XWPBE
      SCALE_X -0.25
      SCALE_X0 1.0
      OMEGA 0.11
    &END XWPBE
  &END XC_FUNCTIONAL
  &HF
    &SCREENING
      EPS_SCHWARZ 1.0E-6
      SCREEN_ON_INITIAL_P FALSE
    &END SCREENING
    &INTERACTION_POTENTIAL
      POTENTIAL_TYPE SHORTRANGE
      OMEGA 0.11
    &END INTERACTION_POTENTIAL
  &END HF
&END XC
```

**这两段里的具体数字（可直接引用，出处 T05 P30）**：
`SCALE_X 0.75` / `SCALE_X 0.25`（PBE0-TC-LRC）、`CUTOFF_RADIUS 2.0`、`T_C_G_DATA ./t_c_g.dat`、
`POTENTIAL_TYPE TRUNCATED`、`SCALE_X 0.0` / `SCALE_X -0.25` / `SCALE_X0 1.0` / `OMEGA 0.11`（HSE）、
`POTENTIAL_TYPE SHORTRANGE`、`EPS_SCHWARZ 1.0E-6`、`SCREEN_ON_INITIAL_P FALSE`。

### 4.4 CP2K Farming 批处理配方（T06 P23，逐字）

```
&GLOBAL
  PROJECT OldMacDonald
  PROGRAM FARMING
  RUN_TYPE NONE
&END GLOBAL
&FARMING
  NGROUPS 2            ! number of parallel jobs
  MASTER_SLAVE         ! for load balancing
  GROUP_SIZE 42        ! number of processors per group, default: 8
  &JOB
    JOB_ID 1           ! optional, required for dependencies
    DIRECTORY dir-1
    INPUT_FILE_NAME water.inp
    OUTPUT_FILE_NAME water.out
  &END JOB
  &JOB
    DEPENDENCIES 1
    DIRECTORY dir-2
    INPUT_FILE_NAME water.inp
    OUTPUT_FILE_NAME more_water.out
  &END JOB
  [...]
&END FARMING
```
要点：**`RUN_TYPE NONE` + `PROGRAM FARMING`**；作业跑在**同一个 CP2K 进程**里，**MPI 只初始化一次**（省启动时间）；**适合大量小作业**（T06 P23）。

### 4.5 预处理器模板（T06 P19–P20）

```
@SET DATAPATH /path/to/cp2k/data
@IF ${METHOD} == PBE
  ...
@ENDIF
@INCLUDE 'settings.inp'
@PRINT now preprocessing ${PROJECT}
```
- `@INCLUDE` 路径**相对当前工作目录** ⇒ 在哪个目录启动 CP2K，就包含哪个目录的 `settings.inp`。
- `@IF` 只支持 `==` 与 `/=`（**字典序**比较）；**值 `0` 或空白 = FALSE，其它 = TRUE**。
- `settings.inp` 里可以再写 `@SET` / `@INCLUDE` / 完整段与关键字。

### 4.6 命令行与调试（T06 P11–P12）

| 命令 | 用途（教材原话要点） |
|---|---|
| `cp2k -c your.inp` | **语法/输入检查**：只抓基础问题；复杂问题要真跑才暴露。配合**低截断 + 限制 `MAX_SCF`/`MAX_STEPS`** 才拿到完整检查 |
| `cp2k your.inp -o your.out` | **生产运行**（输出进文件） |
| `cp2k your.inp \|& tee your.out` | 同时看屏＋存档（`\|&` 同时捕获 stderr） |
| **`cp2k -e your.inp`** | **导出"完整输入"**：含当前默认设置 ＋ **已解析的预处理变量**；**调试复杂输入与解析错误的首选** |
| 错误输出 | **"Leave error output handling to batch-system if possible"** |

### 4.7 构建与验证（T06 P4–P9）

```bash
# toolchain
git clone --recursive https://github.com/cp2k/cp2k.git
cd cp2k/tools/toolchain
./install_cp2k_toolchain.sh              # 或 --install-all；--help 看选项
cp /data/cp2k/tools/toolchain/install/arch/*  /data/cp2k/cp2k/arch/
source /data/cp2k/tools/toolchain/install/setup
cd cp2k/
make -j 8 ARCH=local VERSION="sopt sdbg ssmp popt pdbg psmp"

# Spack
git clone https://github.com/spack/spack.git
. ./share/spack/setup-env.sh
spack install cp2k
spack load cp2k
spack find -p cp2k        # → .spack/archived-files/arch/…popt，可拿来做自定义编译

# 验证构建
make VERSION=sopt ARCH=local test
```

### 4.8 性能检查清单（T06 P39–P40）

1. **I/O 例程 < 总运行时间的 50%**（否则先减少输出频率/量，或换运行目录）。
2. **比较 TIMING 表的 Average 与 Maximum**：差得大 ⇒ 有节点在等单个 rank。
3. 检查各段设置是否用了正确的算法。
4. 优化顺序：**胞大小 → SCF 设置/预条件 → 基组 → ADMM**；**没有万能配方**。
5. 标度测试：**跑少量 MD 或 GEO_OPT 步**，**关 outer-SCF、固定 inner-SCF**。
6. 自编译：厂商 BLAS/LAPACK/FFTW3 + **libxsmm** + **ELPA**。

### 4.9 值得抄下来的数字（教材给的实操量）

| 数字 | 含义 | 出处 |
|---|---|---|
| `GROUP_SIZE` **默认 8** | Farming 每组默认处理器数（示例用 42） | T06 P23 |
| I/O **< 50%** | 总运行时间的 I/O 占比红线 | T06 P39 |
| **3031 测试 / 6 min / regtest 379 s** | toolchain 构建自检的规模量级（示例机） | T06 P9 |
| **0.94 V₀ – 1.06 V₀** | Deltatest 的积分体积窗口（Δ-gauge 定义） | T06 P33 |
| **71 元素 / 40+ 方法** | Deltatest 覆盖范围 | T06 P33 |
| **~10 kcal/mol** | 三重-ζ 高斯基组总能平均误差（五重-ζ 才近化学精度） | T06 P31（引 Jensen 2017） |
| **EPS_SCHWARZ 1.0E-6** | T05 示例（PBE0-TC-LRC 与 HSE）用的筛选阈值 | T05 P30 |
| **CUTOFF_RADIUS 2.0** | T05 示例输入里的截断半径（注意 T05 P27 表用的是 nm：0.2–0.8 nm = 2–8 Å） | T05 P30 / T05 P27 |
| **21290 MiB / 8.14× / 1516 MiB / 764 MiB / 118 MiB** | 真实输出的 ERI RAM、压缩因子、max-vals、密度-Fock 矩阵、缓冲区 | T05 P31 |
| **~1000 原子** | 教材示范的杂化可行规模（TiO₂） | T05 P33 |

---

## 5. 【新】相对既有 A–G 层的增量（先 grep 确认）

> 方法：grep 范围为 **A–G 层**（`references/**/*.md`：G 层 27 个官方文件 + A–F 各层 + E 层讲义/字幕），
> 必要时做**全仓库** grep（`D:\cp2k-aimd\cp2k-aimd-v1.2`）以判定某个词是否**只在 H 层出现**；
> `h_tutorials/txt/`（本次教材正本）与 `h_tutorials/notes/`（本笔记自身）不计入"既有层"。
> 表中"零命中"＝在上述范围内**没有任何一处**写过该内容。

| # | 增量 | 出处 | grep 结论（A–G 层现状） |
|---|---|---|---|
| 1 | **HFX 成本阶梯**：`O(N⁴) → (1/8)O(N⁴) → O(N²) → O(N)`，以及两级筛选的关键字挂钩（`EPS_SCHWARZ`、`SCREEN_ON_INITIAL_P`）与"用预收敛 GGA 密度矩阵" | T05 P8–P11 | A 层 `decide.md:222` 只写"精确交换积分是 O(N^4) 瓶颈"一句；**没有 1/8 置换对称、没有 Schwarz/密度矩阵两级降标度、没有 `SCREEN_ON_INITIAL_P` 的用法语义** |
| 2 | **杂化的成本-精度数值表**（金刚石：积分数 vs 带隙；硅：R_c 与 ADMM 基的二维对照） | T05 P26–P27 | A–G 层 grep 无同类数字；G 层 `19_performance_gpu_community.md:122` 只有"约为局域 DFT 的 **100 倍**"这一句定性量级 |
| 3 | **ADMM 三种辅助密度矩阵构造**（NONE / MO_DIAG / `EXCH_SCALING_MODEL` 电荷约束）的公式与文献（Merlot 2014） | T05 P18–P20 | G 层 `02_dft_methods.md` §6.5 只给 `ADMM_TYPE` 快捷名；`EXCH_SCALING_MODEL` 仅在 `15_optical_and_xray.md:138,272` 作为 `NONE` 出现，**无任何解释** |
| 4 | **ADMM 基命名学**：FIT3/cFIT3/pFIT3/cpFIT3/aug-*；过渡金属 **FIT10=4s+3p+3d / FIT11=+1f / FIT12=4s+3p+4d+1f / FIT13=4s+4p+4d+1f**，c 版为 double-ζ | T05 P23–P24 | G 层只登记文件名（`02`/`14`/`18`），**没有任何一族基组的成分表**；D 层 `manual_notes.md:86` 只有 `AUX_FIT_BASIS_SET` 关键字名 |
| 5 | **ADMM 的两条实现限制**：仅 GPW；只有 ADMM1 兼容 smearing/TDDFPT | T05 P25 | A–G 层 grep 无对应条目（且与版本变更冲突，见 §6） |
| 6 | **`HFX_MEM_INFO` 输出块的逐行读法**（含 "on the fly 应理想为 0"） | T05 P31 | A–G 层 grep `HFX_MEM_INFO` **零命中**（该输出块从未被记录过） |
| 7 | **`MAX_MEMORY` 是"每 MPI 进程的 ERI 内存"**，必须给 OS 与其余计算留空间 | T05 P32 | G `08_errors_and_faq.md:136` 只说"内存上限取决于 MPI 进程数与 `MAX_MEMORY`（MB）"，**未点明"per MPI process"与"要留余量"** |
| 8 | **`&FARMING` 可跑配方 + `&JOB` 关键字（`JOB_ID`/`DIRECTORY`/`INPUT_FILE_NAME`/`OUTPUT_FILE_NAME`/`DEPENDENCIES`）+ `MASTER_SLAVE`** + "同一进程内跑、MPI 只初始化一次" | T06 P23 | G `20_input_reference_tree.md:138-144` 只有 `&FARMING` 段说明与 10 个直接关键字清单（`&FARMING/JOB` 的 5 个关键字**未列名**）；**`MASTER_SLAVE` 在 G 的清单里没有**，全仓库 grep `MASTER_SLAVE` 仅 T06 命中（G/D 层均无） |
| 9 | **预处理器 `@IF/@ENDIF`（`==`/`/=`、0/空白=FALSE）与 `@PRINT`**，以及"`@INCLUDE` 相对 CWD"推出的**多目录高通量工程布局** | T06 P19–P20 | A–G 层只有 `@SET`/`@INCLUDE`（E 层 `learn_L3.md:98-100`、F 层 `playbook.md:342`）；**`@IF`/`@PRINT` 全无**，也没有这套目录布局 |
| 10 | **`cp2k -c`（语法检查，配低截断+限步数）与 `cp2k -e`（导出含默认值与已解析变量的完整输入）** | T06 P11–P12 | A–G 层 grep `cp2k -c` / `-e your.inp` **零命中**；F 层只有 vim 语法高亮当检查器（`playbook.md:531`）；H 层 T07 P3 / T08 P4 讲的是 `-i/-o/--check/--version/--html-manual`（写法不同，可互补） |
| 11 | **TIMING 表的列语义（CALLS/ASD/SELFTIME/TOTALTIME，"ASD＝函数嵌套深度"）＋ 4 条判读准则（I/O<50%、Amdahl、Max vs Avg 看负载不均、算法是否选对）** | T06 P38–P39 | A–G 只有"先看输出末尾的 timing report"的定性指引（G `08_errors_and_faq.md:378`）；**grep `Amdahl`/`ASD`/`SELFTIME` 在 A–G 层零命中** |
| 12 | **Deltatest（Δ-gauge）方法与 MOLOPT 结论**：固体用 MOLOPT；**更大 ζ 系统性改善**；**基组误差与赝化误差同量级**；**某些元素基组误差会"意外补偿"赝势误差**；文献出处（Lejaeghere Science 2016） | T06 P31–P36 | A–G 层 grep **`Deltatest` 零命中**；E 层有 BSSE 的 kcal/mol 定量（`learn_L3.md:464` 等），**但那是 BSSE，不是 Δ-gauge 固体基准** |
| 13 | **只给结构的格式清单**：XYZ（仅坐标）/PDB/CIF/**G96-G87(GROMACS)**/**PSF-UPSF(CHARMM)**/**CRD(AMBER)**/XTL；且 **restart 文件的坐标就是 `&COORD` 段** | T06 P14 | A–G/D 层只覆盖 `COORD_FILE_FORMAT XYZ` 与 `&TOPOLOGY` 的 XYZ/CIF/PDB/XTL（E 层 `learn_L3.md:506`、`MAPPING.md:337`）；**GROMACS/CHARMM/AMBER 结构格式未列** |
| 14 | **与生态工具的"接口机制"**：PYCP2K 的 DSL 与 **`calc.parse("template.in")`**；ASE **用 `cp2k_shell` 常驻**（minimal overhead，可远端启动）；Phonopy **文件接口 + 只需平衡对称化结构**；PyRETIS 把 CP2K 当积分器；i-PI **socket** | T06 P17–P18、P27–P29 | G `00_map.md:74-96` 与 `10_features_resources.md` **只有标题/链接清单**；`24_official_exercises.md:455+` 只有 i-PI 的 socket 配置。**PYCP2K/ASE/Phonopy/PyRETIS 的接口机制 A–G 无** |
| 15 | **AiiDA 最小可跑代码片段**（`ParameterData` 里的 `EPS_DEFAULT 1.0e-12`、`set_max_wallclock_seconds(3*60)`、`set_resources({"num_machines": 4})`）＋ **atomate 作为并列工作流框架** | T06 P22、P24–P25 | G `00_map.md:74` 只登记 AiiDA 标题与 dashboard 集成测试；**全仓库 grep `atomate` 仅 T06 命中** |
| 16 | **"用 `make test` 验证构建"**（自动跳过不可用 feature、看 dashboard）＋ **`spack find -p cp2k` 取出 Spack 的 arch 文件**＋Spack variants 表（`elpa[off]`/`openmp[off]`/`libxc[on]`/`smm[libxsmm]`） | T06 P4–P9 | G `19_performance_gpu_community.md` §6 有 Spack 安装与 `+cuda`，`09_build_libraries.md` 有 toolchain；**"跑 regtest 验证构建"与"从 Spack 取 arch 文件"是增量** |
| 17 | **`cp2k -e` 与归档产物的对照清单**（`proj-1.restart`＝a full input file、`proj-RESTART.kp` 单列） | T06 P12 | G `07_restarting.md`/`05_optimization.md` 已很完整（含 `.kp` 与 `BACKUP_COPIES`）⇒ **本条基本重复，只保留"`-e` 导出全量输入"这一新点**，其余指向 G |

---

## 6. 与既有层的冲突 / 纠错（给页码证据）

1. **【最重要】H 层 README 对 T06 的主题描述与教材内容不符。**
   `h_tutorials/README.md` §3 原写 T06 = "**并行 / 自动化 / Input Magic**"，而 PDF 标题页是 **"CP2K: Automation, Scripting, Testing"**（T06 P1），
   全篇 42 页**没有任何 MPI/OpenMP/`GROUP_PARTITION` 的并行层次讲解**；
   唯一的并行内容是 **Farming 的进程内多作业**（T06 P23）、**构建变体**（T06 P4/P7/P9）、**TIMING 负载不均判读**（T06 P38–P39）。
   ⇒ 建议把 T06 主题改为"**自动化 / 脚本化 / 测试与性能判读**"，避免下游按"并行教材"去查它。
   （"Parallelization" 一词只存在于源文件名里。）

2. **"ADMM has only been implemented for use with GPW"（T05 P25）在现行版本已不成立。**
   G 层版本变更里明确记录 **"GAPW 下启用 ADMM（#2729）"**（`11_version_changelog.md:223`）与
   **"TDDFT/线性响应：GAPW/GAPW_XC 与 ADMM/GAPW 选项（#2200）"**（同文件 242 行）。
   ⇒ T05 是 2019 年的口径（PDF 日期 `12/03/2019`，T05 P1）；**引用这条必须加版本限定**，以 G 层为准。

3. **"Only ADMM1 will work with some other functionality (smearing, TDDFPT)"（T05 P25）与 G 层推荐的"ADMM2"存在张力。**
   G 层 `02_dft_methods.md` §6.5 / `23_dft_subpages_full.md`:1065 明确 **"`ADMM2` 通常是超出基态杂化 DFT 的工作流中支持最广的变体"**；
   而 G 层多处官方示例用的是 `ADMM_PURIFICATION_METHOD NONE`（例如 `15_optical_and_xray.md:140`、
   `21_xray_spectroscopy_full.md:585` —— 后者注释 **"This is the simplest ADMM scheme and has proven to work well"**）。
   ⇒ 存在**三个不同口径**：T05(2019) 说"只有 ADMM1 兼容扩展功能"、G 层权威页说"ADMM2 支持最广"、官方示例大量使用 `NONE`。
   **不要凭 T05 一句话断定"必须 ADMM1"**；按目标性质在 G 层的官方示例里找同场景的写法。

4. **辅助基语法：`AUX_FIT_BASIS_SET ***` 已过时。**
   T05 P29 注："The syntax for the AUX basis set changed (after 4.1?) before that it would be **AUX_FIT_BASIS_SET \*\*\***"；
   T05 P42 再次明确："**use `BASIS_SET AUX_FIT cFIT3` instead of `AUX_FIT_BASIS_SET ***`** in the example."
   而 **D 层 `manual_notes.md:86` 仍把 `AUX_FIT_BASIS_SET` 列为现行 `&KIND` 关键字**（只把 `AUX_BASIS_SET`/`RI_AUX_BASIS_SET` 标为 `[REMOVED]`），
   H 层 T15（2016 夏校练习，`T15_ex2016_hfx.txt:150`）也用 `AUX_FIT_BASIS_SET cFIT3`。
   ⇒ **两套写法在文献/教材里并存，必须标注版本**；教材给出的现行写法是 **`BASIS_SET AUX_FIT <name>`**（T05 P42）。

5. **`EPS_SCHWARZ` 的"教材值"不唯一，别当默认值抄。**
   T05 P30 用 **`1.0E-6`**（取自 `tests/QS/regtest-admm-*`）；C 层 `sections.md:72` 写 **`1e-10`** 并配 `MAX_MEMORY 100`；
   G 层官方示例里 `21_xray_spectroscopy_full.md:622` 用 **`1.0E-6`**、`18_posthf_semiempirical_and_xray.md:528` 用 **`1.0E-10`** 且另有 `EPS_SCHWARZ_FORCES 1.0E-5`。
   ⇒ **`EPS_SCHWARZ` 随体系/目的而变（1e-6 ~ 1e-10），没有单一推荐值**；引用时务必带出处页码。

6. **单位口径提醒：T05 P27 的表用 nm，T05 P30 的输入用 CP2K 默认长度单位（Å）。**
   表注写 **"8 Å cutoff radius"** 与表头 **0.8 nm** 一致（T05 P27），而输入里写 `CUTOFF_RADIUS 2.0`（T05 P30）。
   ⇒ 跨页比较时先换算，别把"2.0"当成"2 nm"。

7. **教材原文笔误（`txt/` 只读不改，在此登记）**：T05 P8 "Mulliken **motation**"（应为 notation）；
   T05 P14 "the snappily **titles** PBE0-TC family"（应为 titled）；T05 P19 "**indempotent**"（应为 idempotent）；
   T05 P13 "plane-wave **implementions**"；T05 P28 引文作者 "**Scuceria**"（应为 Scuseria）。
   这些在两版抽取里都一致出现，判为幻灯片原文笔误。

---

## 7. 存疑

> **本轮查证方式（8 条全部重查）**：① 用 PyMuPDF（`fitz`）把**争议页整页/区域渲染成 PNG 再看**——
> 文本层看不到的图例、花括号、被裁代码、纯图页截图，一望即知（脚本在 `_scratch/`，交付前已删）；
> ② 用官方 `cp2k_input.xml`（`python _kw_probe.py ...`）定关键字的段归属、默认值、枚举；
> ③ 到 cp2k.org 取**同一份讲义的其它版本**（Ling 2015 CECAM 版、Ling 2018 UK 版）交叉比对原文；
> ④ 用真实 `cp2k.out`（`study/庚子计算整理…/【庚子计算整理】cu100-h2o-opt…/cu100-h2o-opt/cp2k.out`，CP2K 6.1）当"输出到底长什么样"的地面真值。
> **形态约定**：`✅ 已定案` 给依据；`⚠️ 未能确证` 给"已排除什么 + 仍缺什么 + 要什么才能确证"。
> **凡本轮推翻了原文猜测/说法的，一律附「更正记录」**（本项目约定：更正要留痕）。

1. **T05 P26 金刚石表的 PBS 列位数异常** → ✅ **已定案：数字无误；原文的"常识"判据（ADMM 约省一个数量级）用错了基线。**
   - **结论**：`PBE0 (PBS) 40 787 850 778 591`（≈4.08×10¹³）是**原论文的原值**，不是抽取时的数字分组假象。
   - **依据 1（页图逐字）**：`fitz` 渲染 T05 P26 → 页面**字面**就是 `40, 787, 850, 778, 591`（五组，前四组带逗号；末组 `591` 无逗号，且字宽与同表 `009`/`638` 一致）⇒ 不是抽取时的"数字分组"假象。
   - **依据 2（原论文 Table 6）**：Guidon, Hutter, VandeVondele, *J. Chem. Theory Comput.* **6**, 2348 (2010)，DOI `https://doi.org/10.1021/ct1002225`（本轮读到的全文镜像：`https://datapdf.com/auxiliary-density-matrix-methods-for-hartreeafock-exchange460fd6866b75b52a86f76684115715c356241.html`）Table 6 逐字为
     `PBE0 (PBS) 40 787 850 778 591 6.07` / `PBE0 (ABS) 23 561 509 497 6.25` / `PBE0 ADMM1 24 816 897 009 6.03` / `PBE0 ADMM2 24 795 460 638 6.02`，表注写明 **3×3×3 超胞、Γ 点**，`PBS` = primary basis set、`ABS` = auxiliary basis set，`ADMM1` = purified、`ADMM2` = non-purified wavefunction fitting。
   - **依据 3（论文自述的削减倍数）**：同文正文原句 **"The ADMM calculations are by 3 orders of magnitude more efficient than the reference PBE0 run."** —— 4.08×10¹³ ÷ 2.48×10¹⁰ ≈ **1.6×10³**，正是"三个数量级"。
   - **依据 4（作者本人的旁证）**：Ling 2018 UK 讲义（`https://www.cp2k.org/_media/events:2018_summer_school:cp2k-uk-stfc-june-2018-sanliang-ling.pdf` 第 42 页）同一张表，`40 787 850 778 591` 被**手工圈出**（椭圆标注），并多一行注记 **"3x3x3 supercell"**。
   - **更正记录**：原文写"PBS 列比它们大 ~1700 倍，与'ADMM 通常带来约一个数量级削减'的常识不符 ⇒ 此列数字…需回原论文核对"。**错在两处**：① 基线选错——ABS（2.36×10¹⁰）只是"同一辅助基但不做 ADMM 校正"的参照，本来就该与 ADMM 同量级；真正的对照是 **PBS**，ADMM 相对 PBS 省 ≈1645 倍（论文自述 3 个数量级）；② 因而"PBS 列异常"这一怀疑不成立。现已回原论文核对完毕。

2. **T05 P27 两张表在 cFIT3 上互相矛盾** → ✅ **已定案：下表 `cFIT3 1.16` 是 2019 版的转录错误，原值是 `1.78`。**
   - **结论**：同一算例（cFIT3 + 8 Å + 3×3×3 / 216 原子）的带隙应为 **1.78 eV**，与积分数 `422 457 823 080`、与上表 0.8 nm 行完全自洽。
   - **依据（更早的同一份讲义）**：Ling 2015 CECAM ADMM 讲义 `https://www.cp2k.org/_media/events:2015_user_meeting:cp2k-uk-2015-ling.pdf` **第 15 页**（本轮下载后用 pdfplumber 抽取 + `fitz` 渲染页图双重确认）：
     - 上表表头是 **"Cutoff radius (Å)"**，四行 `2 / 4 / 6 / 8 → 1.16 / 1.54 / 1.71 / 1.78`，积分数 `77799946176 / 154325979000 / 265868148312 / 422457823080`；
     - 下表（表注 "PBE0-TC-LRC with 8 Å cutoff radius, 3x3x3 supercell, 216 atoms"）为 **`cFIT3 1.78 / 422457823080`**、`FIT3 1.80 / 424426850352`、`pFIT3 1.98 / 1447428361680`、`Ref. (VASP) 1.93 (indirect)`。
   - **页图旁注（可作正文补充）**：`R_C ≤ L/2`；"**Polarisation function is important for covalent solids!**"。
   - **更正记录**：原文列了两种可能，其中 ② "两表 cFIT3 的实际设置不同（超胞或基组不同）" **可排除**——两处积分数**逐位相同**，且 2015 原版明写两表同为 "8 Å / 3×3×3 / 216 atoms"；① 成立，并可进一步定位：错的是 **2019 Ghent/Watkins 版**（`cFIT3` 行被误写成 0.2 nm 行的 1.16），**不是** 2015 版。⇒ 原文"不要把 cFIT3 + 8 Å → 1.16 当收敛结果引用"的告诫**正确**，但原因要说清是**2019 版抄错**。
   - **对应的 §3.2 表内 ⚠️ 标记**：本轮按边界要求**未改动 §1–§6**，该表仍保留 `1.16 ⚠️` 与"见 §6/§7"的指针；**以本条为准**。

3. **T05 P33–P40（TiO₂ 极化子）7 页几乎全是图** → ✅ **已定案：不是抽取失败，但页内确实没有任何计算参数。**
   - **依据**：`fitz` 渲染 T05 P33/P34/P36/P38/P40 → 逐页都是整幅图像（STM 图、DFT 自旋密度图、极化子结构图），图内文字可辨：P34 有 `Empty states / Filled states`、`Dimer / 'cross-dumbbell' trimer / 'mushroom' trimers / Tetramer`、比例尺 `1 nm`、页底图注 `Yim et al, Phys. Rev. Lett. 117, 116402 (2016)`；P38 有 `TiO2-Polarons`、`Anatase / Rutile`、`Electron / Hole`。
   - **结论**：① "字少图多"属实，**不是抽取失败**；② 这些页（含图内标注）**不含基组 / CUTOFF / k 点 / 超胞尺寸等任何可复现参数** ⇒ 原告诫成立：**要复现该规模必须回原文献**（Yim PRL 2016；Elmaslmane JCTC 2018）；"~1000 原子"仍只有 T05 P33 正文这一个来源。
   - **补充**：图形内容本身可复原（渲染页图即可），所以不必再说"内容不可复原"；但复原出来的是**图**，不是参数。

4. **T05 P30 的代码块缺 `&HF FRACTION`** → ✅ **已定案：不是"少一行"，而是两栏都被从 `&END INTERACTION_POTENTIAL` 起整段裁掉；原件写有 `FRACTION 0.25`。**
   - **结论**：T05 P30 两栏代码都停在左栏 `T_C_G_DATA ./t_c_g.dat` / 右栏 `OMEGA 0.11`，其后的 **`&END INTERACTION_POTENTIAL`、`&MEMORY`(`MAX_MEMORY 2400`/`EPS_STORAGE_SCALING 0.1`)、`&END MEMORY`、`FRACTION 0.25`、`&END HF`、`&END XC` 一并丢失**（两栏裁在同一行 → 典型的版面裁剪，不是作者有意省略某一行）。
   - **依据 1（页图）**：`fitz` 渲染 T05 P30 确认两栏底边齐平截断。
   - **依据 2（T05 P43 指认的来源讲义原文含 `FRACTION 0.25`）**：
     - `https://www.cp2k.org/_media/events:2015_cecam_tutorial:ling_hybrids.pdf` **第 29 页**：`… &END INTERACTION_POTENTIAL / &MEMORY / MAX_MEMORY 2400 / EPS_STORAGE_SCALING 0.1 / &END MEMORY / **FRACTION 0.25** / &END HF / &END XC`（两栏各一行，PBE0-TC-LRC 与 HSE06 都是 0.25）；
     - `https://www.cp2k.org/_media/events:2018_summer_school:cp2k-uk-stfc-june-2018-sanliang-ling.pdf` **第 37 页**同段同值；
     - `https://www.cp2k.org/_media/events:2015_user_meeting:cp2k-uk-2015-ling.pdf` 第 13 页亦同。
   - **依据 3（为什么必须补）**：`python _kw_probe.py FORCE_EVAL/DFT/XC/HF/FRACTION` → `DEFAULT_VALUE : 1.00000000E+000`（"The fraction of Hartree-Fock to add to the total energy."）⇒ **漏写 `FRACTION` 不是无关紧要，而是把 25% HFX 变成 100% HFX**。
   - **照抄建议（更新）**：补的行要放在 `&END INTERACTION_POTENTIAL`（及 `&MEMORY` 块）**之后、`&END HF` 之前**——原件就是这个顺序；其余行照抄 T05 P30 即可。
   - **附带更正（实用）**：T05 P30/P42 与 `§4.1` 都建议"直接去 `tests/QS/regtest-admm-1/2/3/4` 取完整输入"——**这两个目录现在不装这两个算例了**：查 GitHub API（`https://api.github.com/repos/cp2k/cp2k/contents/tests/QS/regtest-admm-1`…`-4`）可见 `regtest-admm-1..4` 里是 `CH3-BP-*.inp` / `CH4-BP-*.inp` / `H2O-admm-*.inp` / `2H2O-BLOCKED-PURIFY-*.inp` 等（**BP 泛函的 ADMM 测试**），没有 PBE0-TC-LRC / HSE06 的输入。要"完整输入"请按上一条**自己补 FRACTION**，或去 `tests/QS/regtest-hfx*` / `regtest-hfx-periodic` 找同类写法。

5. **T06 P38 的 TIMING 表头列数与数据列数对不上** → ✅ **已定案：这不是幻灯片排版错位，而是 CP2K 自身 TIMING 表头的固有缺陷；幻灯片忠实复制了真实输出。**
   - **依据 1（真实 CP2K 6.1 输出）**：`cu100-h2o-opt/cp2k.out:19125-19127` 逐字为
     ```
      SUBROUTINE                       CALLS  ASD         SELF TIME        TOTAL TIME
                                     MAXIMUM       AVERAGE  MAXIMUM  AVERAGE  MAXIMUM
      CP2K                                 1  1.0     0.01     0.01 16003.69 16003.88
     ```
     第二行表头确有 **5 个** `MAXIMUM/AVERAGE` 标签，而数据只有 **4 个**时间列（SELF MAX/AVG + TOTAL MAX/AVG）。
   - **依据 2（页图）**：`fitz` 渲染 T06 P38 并把表头区域放大 12× → 幻灯片上确实是 `MAXIMUM  AVERAGE  MAXIMUM  AVERAGE  MAXIMUM`，与文本层一致（不是抽取多出来的词）。
   - **更正记录**：原文判定"属**幻灯片表格排版与文本层错位**"——**归因错误**。真实 CP2K 输出（至少 6.1）第二行表头就多一个 `MAXIMUM`；因此**读表规则不变**（按"名字 + CALLS + ASD + selftime(max/avg) + totaltime(max/avg)"理解），但**不要再把它记成幻灯片的问题**，也不要指望换个路径重抽就能对齐。

6. **T06 的"什么设置配什么机器"信息严重不足** → ✅ **已定案（就这两份教材而言）：不是我们读漏，是教材确实只给到"构建变体 + 两个量"这一层。**
   - **依据**：对 `txt/T05_hybrid_admm_watkins.txt` + `txt/T06_parallel_input_mueller.txt`（43+42 页）按 `core|CPU|memory|node|MPI rank|thread` 全检索，**一共只有 7 行命中**，且全是定性的：`HFX_MEM_INFO` 的内存账 4 行（T05 第 633/636/639/644 行）、`MAX_MEMORY`/`more MPI processes`/`memory per MPI process for ERIs` 2 行（第 654–655 行）、"nodes are waiting for single rank to finish" 1 行（T06 第 800 行）。**没有任何核数配比、每核内存、节点拓扑、"多少原子配多少核"的数字。**
   - **这两份材料里仅有的可量化依据（已用官方 XML 复核）**：
     - `python _kw_probe.py FARMING/GROUP_SIZE` → `DEFAULT_VALUE : 8`（"Gives the preferred size of a working group…"）⇒ T06 P23 的"default: 8"**正确**；同段 `python _kw_probe.py --section FARMING` 还列出 `MASTER_SLAVE`（logical，默认 `F`）、`NGROUPS`、`STRIDE`、`GROUP_PARTITION`、`MAX_JOBS_PER_GROUP 65535`、`CYCLE`、`WAIT_TIME 0.5`、`DO_RESTART` 等（G 层清单未列全，可回填）。
     - `python _kw_probe.py FORCE_EVAL/DFT/XC/HF/MEMORY` → `MAX_MEMORY` 默认 **512**（[MiB]，"maximum amount of memory to be consumed by the full HFX module"）、`EPS_STORAGE_SCALING` 默认 1.0、`STORAGE_LOCATION` 默认 `.`、`MAX_DISK_SPACE` 默认 0、`TREAT_FORCES_IN_CORE` 默认 F。
   - **注意边界**：这只说明"**教材给不了**"，不等于"CP2K 社区没有这类经验"；需要核数/内存配比时应另找来源（G 层性能页、邮件列表、`cp2k.org` 的 HPC 资料），不要指望 T05/T06。

7. **"Γ 点大晶胞"与"HSE 不比 PBE0 便宜"（T05 P13）的可迁移性未验证** → ⚠️ **未能确证，已排除以下可能**：① G 层 `references/official/`（27 个 .md）全文检索 `HSE` / `omega` / `OMEGA` **没有任何对应表述**（命中的是 `COHSEX`、等离子体频率 ω 等无关内容）⇒ 不能拿 G 层为它背书，也不能说 G 层否定了它；② 也**不是** Watkins 改写走样——同两句在 Ling 自己的 Ghent 2019 正本里就有（`https://www.cp2k.org/_media/events:2019_ghent:admm.pdf`，43 页，与 T05 逐页对应）。
   **相关事实（本轮查到的）**：CP2K 邮件列表 2026-04 的一条开发者回复只说到 "**HSE06 is generally more expensive than PBE**"（比 PBE 贵），**没有**支持或否定"不比 PBE0 便宜"（`https://lists.cp2k.org/archives/cp2k-user/2026-April/022244.html`）。
   **仍不确定的是**：① 在 CP2K 里 HSE06 相对 PBE0(-TC-LRC) 的实际成本比（同体系同基组）；② ω 取多小就必须放大 Γ 点超胞。
   **要确证需要**：**一台能跑凝聚相杂化的机器**——对同一体系（例如 T05 P27 的 Si 3×3×3 / 216 原子）分别跑 PBE0-TC-LRC 与 HSE06，比较输出里 `HFX_MEM_INFO| Number of cart. primitive ERI's calculated` 与 TIMING 总时长；再做 ω（0.11 → 0.2/0.3）与超胞尺寸的二维扫描看带隙收敛。本轮只有讲义文本，没有这种算力环境。

8. **T06 P34/P35 的图例只能部分还原** → ✅ **已定案：图例可以完全还原**（渲染页图即可）；但"具体 Δ 值不要引用"的告诫仍然有效。
   - **依据**：`fitz` 渲染 T06 P34/P35 → 图例逐项可读：`CP2K, DZVP vs Abinit`（蓝圆点线）、`CP2K, TZVP vs Abinit`（橙三角）、`CP2K, TZV2P vs Abinit`（绿星）、`CP2K, TZV2PX vs Abinit`（红方）+ `Abinit`（浅蓝柱）；左图同族但为 SR 版（`CP2K: DZVP-SR vs Abinit` …），右图旁注 `↑ non-SR MOLOPT basis sets`，下图是 `CP2K vs. WIEN2k` 与 `Abinit, GTH-PBE vs WIEN2k`（柱）。P35 是放大版：y 轴 0–30，横轴 `H C N O F Si P S Cl Cu Br`（11 元素），并有 `larger Basis Set` 虚线箭头贯穿 DZVP→TZVP→TZV2P→TZV2PX。
   - **结论**：原文"图例文字在文本层是乱序"是**文本层**现象（`CCCCAb PPPP 2222in…`），渲染后完全可读；**但**图里的 Δ 数值只有折线，目测精度约 ±0.5（y 轴量程 0–30）⇒ **仍只引用 T06 P36 的四条文字结论，不要引用具体 Δ 值**。
