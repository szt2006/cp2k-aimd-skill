# 18 · 后 HF 方法、半经验方法与 X 射线谱（官方）

> 来源：
> - https://manual.cp2k.org/trunk/methods/post_hartree_fock/index.html
> - https://manual.cp2k.org/trunk/methods/post_hartree_fock/preliminaries.html
> - https://manual.cp2k.org/trunk/methods/post_hartree_fock/mp2.html
> - https://manual.cp2k.org/trunk/methods/post_hartree_fock/rpa.html
> - https://manual.cp2k.org/trunk/methods/post_hartree_fock/low-scaling.html
> - https://manual.cp2k.org/trunk/methods/semiempiricals/index.html
> - https://manual.cp2k.org/trunk/methods/semiempiricals/xtb.html
> - https://manual.cp2k.org/trunk/methods/semiempiricals/dftb.html
> - https://manual.cp2k.org/trunk/methods/properties/index.html
> - https://manual.cp2k.org/trunk/methods/properties/optical/index.html
> - https://manual.cp2k.org/trunk/methods/properties/optical/rtbse.html
> - https://manual.cp2k.org/trunk/methods/properties/optical/vibronicspec.html
> - https://manual.cp2k.org/trunk/methods/properties/x-ray/index.html
> - https://manual.cp2k.org/trunk/methods/properties/infrared.html
> 抓取日期：2026-09-08
> 标注规则：`[默认]` = 官方默认值；`[官方推荐]` = 官方明确建议；`[示例]` = 官方示例原样；`[G层提示]` = 本层基于官方原文给出的使用提示（非官方原文）

---

## 0. 本文件补什么

| 主题 | 此前状态 | 本文件 |
|---|---|---|
| 后 HF（MP2 / RPA / SOS-MP2） | G 层仅有零散提及 | **§1–§3 完整** |
| **BSSE（基组叠加误差）** | 仅"经验级警示，来源待核对" | **§2 找到官方原文，来源确证** |
| 低标度后 HF | 无 | **§4 完整**（含 2 个完整输入） |
| 半经验（xTB / DFTB） | 无 | **§5 完整**（含 4 个完整输入） |
| X 射线谱 4 页 | 无 | **§6 页面清单 + 状态** |
| RTBSE / vibronic | 无 | **§7 完整** |
| 红外/Raman/NMR | 占位页 | **§8 状态确认** |

> **本文件最重要的更正**：BSSE 在 CP2K 官方手册中有明文记载（`preliminaries.html` §Basis Set Superposition Error）。此前 G 层标注为"仅作经验级警示、来源待核对"，现升级为**官方事实**。

---

## 1. 后 HF 章节结构与总体定位（官方）

官方 `post_hartree_fock/index.html` 原文：

> Post-Hartree-Fock methods in CP2K add wavefunction-based correlation, quasiparticle, or response corrections **on top of a converged reference calculation**. The reference is usually Hartree-Fock, a hybrid functional, or semilocal DFT, depending on the target method and property.

页面清单：

| 页面 | 状态 |
|---|---|
| Preliminaries | **正文完整**（本文件 §2） |
| Møller–Plesset Perturbation Theory（MP2） | **正文完整**（本文件 §3.1） |
| RPA and Laplace-Transformed SOS-MP2 | **正文完整**（本文件 §3.2） |
| Low-scaling post Hartree-Fock | **正文完整**（本文件 §4） |

官方生产建议原文：

> For production work, **converge the reference calculation first**, then check basis-set size, auxiliary basis or auto-generated RI basis settings, quadrature parameters, and memory distribution.

`[G层提示]` 顺序不能颠倒：**先收敛参考态**，再谈后 HF。这是官方明确的 workflow。

---

## 2. Preliminaries：后 HF 的五步准备（官方，含 BSSE）

### 2.1 两类基组（官方）

官方原文：

> Because of the different building blocks, we have to distinguish at least two kinds of basis sets: the **primary basis set (PBS)** to represent the orbital functions and the **RI basis set** to expand products of PBS functions into a set of auxiliary functions.

RI 近似（官方公式）：

```
(ia|jb) = Σ_PQ (ia|P) (P|Q)^(-1) (Q|jb)
```

官方补充：在 PBS 与 RI 基组之上，**HF 的 ADMM 近似可能引入第三类基组**。

### 2.2 步骤 1：选择主基组（官方）

官方原文：

> Because of the slow convergence of the calculated properties from post-Hartree-Fock calculations with respect to the size of the PBS, post-Hartree-Fock methods demand for **larger PBSs than ordinary hybrid DFT or HF calculations**.

官方推荐（`[官方推荐]`）：

| 情形 | 官方建议 |
|---|---|
| 无外推方案 | 至少 **triple-zeta（cc-TZ）** 或 **augmented double-zeta（aug-cc-DZ）** 质量 |
| 有外推方案 | 每种元素需要**两个不同大小**的基组 |
| 非增广 DZ 基组 | **应避免**（结果通常不够收敛，无法用于外推） |

外推公式（官方）：

```
E(X) = A + B / X³
```

X = 2, 3, 4 分别对应 DZ、TZ、QZ。

可用基组文件（官方）：`BASIS_RI_cc-TZ`、`BASIS_ccGRB`（在 data 目录）。

### 2.3 步骤 2：选择 RI 基组（官方）

用 `BASIS_SET RI_AUX` 指定。官方给三条路径：

| 路径 | 说明 |
|---|---|
| ① 用现成的 | `BASIS_RI_cc-TZ` 文件含**少数主族元素**的 RI 基组；缺失元素查文献 |
| ② 自己优化 | 推荐在需要大量计算时使用，可显著降低成本。见 `OPT_RI_BASIS` 与 regtest 套件 `QS/regtest-ri-opt` |
| ③ 自动生成 | 其它情况 CP2K 可自动生成（`AUTO_BASIS RI_AUX`）。精度尚可，但**大小约为优化基组的 2 倍** |

### 2.4 步骤 3：赝势（官方）

> Pseudopotentials should **reflect the underlying hybrid or HF calculation** used to determine orbitals and orbital energies.

`[G层提示]` 即：参考态用的是 PBE0，赝势就应选对应的 `GTH-PBE0-q*`，不能混用 PBE 赝势。

### 2.5 步骤 4：预优化参考轨道（官方，重要）

官方原文：

> It is recommended to **restart the orbital calculation step from preoptimized HF or hybrid orbitals**. This reduces computational costs because **DFT and HF calculations do not perform well in case of the large number of CPU cores required for post-Hartree-Fock methods**.

`[G层提示]` 实践含义：后 HF 要开很多核，但 SCF 在大核数下效率差。所以**先用少量核把 SCF 跑收敛、存 wfn，再用大量核跑后 HF**。示例见 §3.3 的 `WFN_RESTART_FILE_NAME`。

### 2.6 步骤 5：积分方法（官方，含限制表）

用 `INTEGRALS` 段配置。官方原文解释：

> Because most densities occurring in the formalisms of the post-Hartree-Fock methods have a **zero net-charge**, such that the Coulomb operator does not need to be truncated it is required by HF. CP2K has its own integration routines for post-Hartree-Fock methods exploiting this circumstance.

`ERI_METHOD` 三种取值及官方限制（**重要**）：

| 方法 | 全称 | 官方限制 |
|---|---|---|
| `GPW` | Gaussian-Plane-Wave | **完全支持** |
| `MME` | Minimax-Ewald | **不实现应力张量**；**不支持短程算符**（截断 Coulomb、erfc-Coulomb 等） |
| `OS` | Obara-Saika | **仅低标度方法实现梯度**；**不支持自动生成的 RI 基组** |

GPW 的 CUTOFF 官方建议：

> the primary cutoff parameter can be **chosen much smaller (150-300 Ry)** than usual.

### 2.7 通用输入骨架（官方原文）

```fortran
&WF_CORRELATION
  # Determine the available memory
  MEMORY 1000
  # Determines the size of sub groups used in most methods
  # The lower the number, the less communication but the more memory (only relevant for very large systems)
  GROUP_SIZE 1
  &INTEGRALS
    # Here, we show the setup with the GPW integration
    ERI_METHOD GPW
    # Tune the accuracy and performance of the integral calculation step (default is usually sufficient)
    SIZE_LATTICE_SUM 5
    &WFC_GPW
      # Set it as large as necessary and as small as possible (check energies)
      CUTOFF 200
      REL_CUTOFF 50
    &END
    # Only necessary for special functionals
    &INTERACTION_POTENTIAL
    &END
    # Relevant only if low-scaling methods or a potential operator without short-range contributions is requested
    &RI
      # Set up the RI metric
      &RI_METRIC
      &END
    &END
  &END
  # Set the section corresponding to the requested method (mixtures of different methods are not possible)
  &<NAME_OF_METHOD>
    <OPTIONS_TO_CONFIGURE_METHOD>
  &END
&END
```

官方警告：

> mixtures of different methods are **not possible**

### 2.8 梯度计算（官方）

官方原文：

> Gradient calculations are available for **RI-MP2, RI-RPA and RI-SOS-MP2** calculations.

- 低标度实现 → 看 `LOW_SCALING/CPHF`
- 否则 → 看 `CANONICAL_GRADIENTS`

官方 `CANONICAL_GRADIENTS` 骨架：

```fortran
&CANONICAL_GRADIENTS
  # This threshold switches to explicit contractions for almost degenerate orbital pairs (excluding diagonal elements)
  EPS_CANONICAL 1.0E-6
  # Try to turn it on, but it may crash in the execution step
  FREE_HFX_BUFFER .FALSE.
  &CPHF
    # This threshold is to be optimized (lower values increase accuracy but require more time)
    EPS_CONV 1.0E-6
    MAX_ITER 20
  &END
&END
```

### 2.9 ★ BSSE：官方明文记载（来源确证）

官方 `preliminaries.html` 原文（完整）：

> **Basis Set Superposition Error (BSSE)**
>
> Energy calculations using post-Hartree-Fock methods suffer from **severe basis set superposition error (BSSE)**. In CP2K, this is **enhanced by the many different basis sets in use**. Check the `BSSE` section for further information on the automatic setup of BSSE calculations and the `GHOST` for the manual setup of BSSE calculations.

#### 关键点（G 层提炼）

| 要点 | 内容 |
|---|---|
| 适用范围 | **后 HF 方法**（MP2、RPA、SOS-MP2 等）的能量计算 |
| 严重程度 | 官方用词 **severe**（严重） |
| CP2K 特有放大因素 | 用了**多种不同基组**（主基组 + RI 基组 + ADMM 辅助基组），使 BSSE 更严重 |
| 自动方案 | `FORCE_EVAL/BSSE` 段 |
| 手动方案 | `FORCE_EVAL/SUBSYS/KIND` 的 `GHOST` 关键字 |

#### 与既有 A 层经验的关系

A 层此前的结论是"BSSE 高斯基组高估吸附能"，但当时标注为**经验级、来源待核对**（PDF/字幕全文零命中）。

**本轮结论**：
- ✅ 官方手册**确实记载了 BSSE**，来源确证，可升级为官方事实
- ⚠️ 但官方原文说的是"**后 HF 方法**"的 BSSE，**并未**直接说"高斯基组高估吸附能"
- `[G层提示]` 因此正确的表述是：**官方确认后 HF 计算存在严重 BSSE，且 CP2K 因多基组并用而加剧**；"高斯基组高估吸附能"这一具体论断在官方页面中**未找到直接对应**，仍应作为经验级结论对待。两者不矛盾，但不能互相代替。

---

## 3. MP2 与 RPA（官方）

### 3.1 MP2（官方）

MP2 能量公式（官方）：

```
E^(2) = −Σ_ijab (ia|jb) [ 2(ia|jb) − (ib|ja) ] / ( ε_a + ε_b − ε_i − ε_j )
```

官方实现方式：GPW 方法，见 DelBen2012、DelBen2013。CP2K 也实现双杂化泛函。

#### 三种实现对比（官方）

| 实现 | 可用参考态 | 梯度（核力/应力） | 相对成本 | 备注 |
|---|---|---|---|---|
| **Canonical**（`DIRECT_CANONICAL`） | GPW **和** GAPW | ❌ 无解析梯度 | **最贵** | 允许 core-corrections |
| **GPW-based**（`MP2_GPW`） | **仅 GPW** | ❌ 无解析梯度 | 比 canonical 便宜 | DelBen2012 |
| **RI-based**（`RI_MP2`） | GPW（GAPW 参考态不可） | ✅ GPW 积分下有解析梯度 | **最便宜** | DelBen2013、DelBen2015b |

RI 的限制（官方）：
- MME 积分**不支持应力张量**
- Obara-Saika 积分**不实现任何梯度**

#### 泛型标度关键字（官方）

`SCALE_S`（singlet 缩放）与 `SCALE_T`（triplet 缩放），**三种实现通用**。

#### 官方输入示例

Canonical：

```fortran
&WF_CORRELATION
  # See prelimaries
  MEMORY    1200
  NUMBER_PROC  1
  # Only if not the Coulomb potential is required
  &INTEGRALS
  &END
  &MP2
    METHOD DIRECT_CANONICAL
  &END
&END
```

GPW-based：

```fortran
&WF_CORRELATION
  # See prelimaries
  MEMORY    1200
  NUMBER_PROC  1
  # Only if not the Coulomb potential is required
  &INTEGRALS
    &WFC_GPW
      # To be optimized
      CUTOFF 200
      REL_CUTOFF 50
    &END
  &END
  &MP2
    METHOD MP2_GPW
  &END
&END
```

RI-based：

```fortran
&WF_CORRELATION
  # See prelimaries
  MEMORY    1200
  NUMBER_PROC  1
  # Only if not the Coulomb potential is required
  &INTEGRALS
    &WFC_GPW
      # To be optimized
      CUTOFF 200
      REL_CUTOFF 50
    &END
  &END
  &RI_MP2
    # Larger block sizes require more memory but reduce communication, -1 (default) let CP2K choose it
    BLOCK_SIZE 2
    # This keyword determines how many copies of the rank-three tensor are kept in the memory of all CPUs. Large number of groups increase the memory demands but reduce communication (default: -1, automatic determination)
    NUMBER_INTEGRATION_GROUPS 2
  &END
&END
```

#### 性能考虑（官方）

> MP2-calculations are generally very expensive for large systems due to their **quintical scaling** with respect to the number of atoms. Thus, for larger systems, one should switch to the cheaper **RPA or SOS-MP2** methods.

官方补充：CP2K 用局部矩阵乘法做收缩，若链接了 **SpLA** 库可加速；在没有 GPU 加速 DGEMM 的情况下可实现 GPU 加速。

#### 简并轨道对的陷阱（官方）

官方原文：

> A few more words are required regarding systems with **many degenerate occupied orbital pairs** as they are found in structures with **many symmetry-equivalent atoms**. In that case, non-diagonal elements of the density matrix of almost degenerate occupied-orbital pairs have to be calculated explicitly for numerical reason. This is **significantly more expensive** than for non-degenerate orbital pairs.

调参关键字：`EPS_CANONICAL`。

`[G层提示]` 高对称晶体（如简单氧化物、金属）做 MP2 梯度时要预期这一步显著变慢。

### 3.2 RPA 与 LT-RI-SOS-MP2（官方）

#### 公式（官方）

直接 RI-RPA（dRPA）：

```
E_RI-dRPA = −(1/4π) ∫ dω Tr( log(1+Q(ω)) − Q(ω) )
Q_RS(ω) = 2 Σ_ia B_iaR (ε_a−ε_i) / [ (ε_a−ε_i)² + ω² ] B_iaS
```

拉普拉斯变换 SOS-MP2（LT-RI-SOS-MP2）：

```
E_LT-RI-SOS-MP2 = −∫_0^∞ dτ Tr( Q̄(τ)² )
Q̄_RS(τ) = Σ_ia B_iaR exp( −(ε_a−ε_i) τ ) B_iaS
```

官方：积分**数值求解**；双杂化泛函可用。

#### 两种实现（官方）

| 实现 | 标度 |
|---|---|
| 四标度（quartic） | 本文件 §3.2 重点 |
| 低标度（cubic，sub-cubic） | 见 §4 |

缩放关键字：RPA 用 `SCALE_RPA`；LT-RI-SOS-MP2 用 `SCALE_S`。

#### 积分方案（官方，重要）

| 方案 | 所需积分点 |
|---|---|
| **Clenshaw-Curtis** | **30–40** 个 |
| **Minimax** | **6–8** 个 |

官方警告：

> Minimax quadrature rules have to be **preoptimized** such that **not all possible numbers of quadrature points are available**.

`[G层提示]` Minimax 点数少但只能取预设值，不能随意指定任意整数。

#### 与精确交换的组合（官方）

> RPA correlation energies are usually combined with **exact exchange** energies. In CP2K, this is available by activating the `HF` section which is setup like an ordinary HF section.

#### Beyond-RPA 方案（官方）

| 方案 | 全称 | 启用方式 |
|---|---|---|
| **RSE** | Renormalized Screened Exchange | `RSE` 关键字（**仅对非 HF 参考态有意义**） |
| **AXK** | Approximate Exchange Kernel | `EXCHANGE_CORRECTION` 段 |
| **SOSEX** | Second-Order Screened EXchange | `EXCHANGE_CORRECTION` 段 |

官方 RPA 段示例：

```fortran
  &RI_RPA
    # Choose it as large as necessary and as small as possible
    QUADRATURE_POINTS 6
    # Choose it as large as possible (must be a divisor of the number of quadrature points and the number of processes)
    # -1 is default and let CP2K decide on that value
    # Larger values increase the memory demands but reduce communication
    NUM_INTEG_GROUPS -1
    # The RSE correction is only relevant for a non-HF reference
    RSE .TRUE.
    # Exchange corrections may be quite costly
    &EXCHANGE_CORRECTION [NONE|AXK|SOSEX]
      # The Hartree-Fock-based implementation scales better for larger systems but introduces more noise
      USE_HFX_IMPLEMENTATION F
      # This parameter is ignored if USE_HFX_IMPLEMENTATION is set to T
      # Larger values improve performance but increase the memory demands
      BLOCK_SIZE 16
    &END
  &END
```

#### RPA 梯度（官方）

> Analytical gradients are **only available for RPA calculations using a minimax grid**, but **not for the beyond-RPA methods**（RSE, AXK, SOSEX）.

两个附加关键字（官方）：

| 关键字 | 作用 |
|---|---|
| `DOT_PRODUCT_BLKSIZE` | 沿辅助指标拆分收缩以改善数值稳定性。**默认关闭** |
| `MAX_PARALLEL_COMM` | 非阻塞通信的并行通道数。更大值允许更多重叠但增加内存。**超过 3 通常没必要** |

#### LT-RI-SOS-MP2（官方）

官方原文：

> CP2K implements two quadrature schemes only the **Minimax** scheme requiring usually **6-8 quadrature points**.

输入更简单：

```fortran
  &RI_SOS_MP2
    # Works similar than in RPA
    NUM_INTEG_GROUPS -1
    # Larger values improve the accuracy but increase the costs
    QUADRATURE_POINTS 6
  &END
```

梯度：可用，类似 RI-MP2 / RI-RPA。同样用 `EPS_CANONICAL`。

官方对 `EPS_CANONICAL` 的说明：

> Larger values improve the numerical accuracy but increase the computational costs significantly because CP2K assumes that the number of relevant pairs is negligible.

#### 性能考虑（官方）

- 四标度 RI-RPA / RI-SOS-MP2 随原子数**四次方**增长
- 依赖并行矩阵乘法 → 可用 **COSMA** 降低成本，若 COSMA 配置了 GPU 可加速
- HF 可用 **ADMM** 加速，**推荐在基组很弥散时使用**
- RSE 修正复用与 HF 交换能相同的 HF 段
- AXK / SOSEX 成本取决于实现：
  - **HF-based 实现**：大体系更便宜；性能取决于每进程组的可用内存（`GROUP_SIZE`、`MAX_MEMORY`）；对超大体系成本变得**可忽略**
  - **非 HF 实现**：依赖 SpLA 加速的局部矩阵乘法；大体系下成为瓶颈，但**数值噪声更小**

### 3.3 RI-MP2 梯度完整输入（官方，含 ADMM）

官方原文示例（水分子，HF + ADMM 加速 + RI-MP2 梯度）：

```fortran
&GLOBAL
  PRINT_LEVEL LOW
  PROJECT example
  RUN_TYPE FORCE_EVAL
&END GLOBAL

&FORCE_EVAL
  METHOD Quickstep
  &DFT
    # This file contains basis sets for common elements (H, C, N, O; for F, Al, Cl, Si, P, S only TZ basis sets)
    BASIS_SET_FILE_NAME BASIS_RI_cc-TZ
    BASIS_SET_FILE_NAME BASIS_ADMM
    POTENTIAL_FILE_NAME POTENTIAL
    # Plug in your preconverged wfn file here
    WFN_RESTART_FILE_NAME ./example_HF.wfn
    # Use if no RI basis set is available (possible values: SMALL, MEDIUM, LARGE, HUGE)
    AUTO_BASIS RI_AUX LARGE

    &AUXILIARY_DENSITY_MATRIX_METHOD
      # Purification is not implemented
      ADMM_PURIFICATION_METHOD NONE
      # Try different options (check with reference values or use the default)
      EXCH_CORRECTION_FUNC PBEX
      # other methods are not implemented
      METHOD BASIS_PROJECTION
    &END AUXILIARY_DENSITY_MATRIX_METHOD
    &MGRID
      # Adjust as usual
      CUTOFF 600
      REL_CUTOFF 50
    &END MGRID
    &POISSON
      PERIODIC XYZ
      POISSON_SOLVER WAVELET
    &END POISSON
    &QS
      # Choose as tight as necessary
      EPS_DEFAULT 1.0E-10
      METHOD GPW
    &END QS
    &SCF
      # Choose as tight as necessary
      EPS_SCF 1.0E-8
      MAX_SCF 100
      SCF_GUESS RESTART
    &END SCF
    &XC
      &HF
        FRACTION 1.0000000
        &INTERACTION_POTENTIAL
          # Adjust the cutoff radius according to your cell
          CUTOFF_RADIUS 1.5
          POTENTIAL_TYPE TRUNCATED
          T_C_G_DATA t_c_g.dat
        &END INTERACTION_POTENTIAL
        &SCREENING
          # Tune these parameters
          EPS_SCHWARZ 1.0E-10
          EPS_SCHWARZ_FORCES 1.0E-5
          SCREEN_ON_INITIAL_P .FALSE.
        &END SCREENING
      &END HF
      &WF_CORRELATION
        MEMORY 500
        NUMBER_PROC 1
        &CANONICAL_GRADIENTS
          # The default is usually good enough
          EPS_CANONICAL 1E-6
          # This is the option which should always work
          # Try to set it to .TRUE. (may segfault)
          FREE_HFX_BUFFER .FALSE.
          &CPHF
            # Choose as tight as necessary
            EPS_CONV 1.0E-6
            # Smaller values of EPS_CONV may require more iterations
            MAX_ITER 10
          &END CPHF
        &END CANONICAL_GRADIENTS
        &INTEGRALS
          &WFC_GPW
            # Adjust these parameters to your needs of accuracy
            CUTOFF 200
            EPS_FILTER 1.0E-12
            EPS_GRID 1.0E-8
            REL_CUTOFF 50
          &END WFC_GPW
        &END INTEGRALS
        &RI_MP2
          # Determine an automatic block size, if memory is low, set it to 1
          BLOCK_SIZE -1
        &END RI_MP2
      &END WF_CORRELATION
      &XC_FUNCTIONAL NONE
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &PRINT
    &FORCES
    &END FORCES
  &END PRINT
  &SUBSYS
    # Adjust cell information and coordinations as necessary
    &CELL
      ABC [angstrom] 5.0 5.0 5.0
      PERIODIC XYZ
    &END CELL
    &COORD
      O       0.000000    0.000000    -0.211000
      H       0.000000   -0.844000     0.495000
      H       0.000000    0.744000     0.495000
    &END COORD
    &KIND H
      # orbital and RI basis set should match
      BASIS_SET cc-TZ
      BASIS_SET RI_AUX RI_TZ
      # Use the largest affordable one
      BASIS_SET AUX_FIT cpFIT3
      POTENTIAL GTH-HF-q1
    &END KIND
    &KIND O
      BASIS_SET cc-TZ
      BASIS_SET RI_AUX RI_TZ
      BASIS_SET AUX_FIT cpFIT3
      POTENTIAL GTH-HF-q6
    &END KIND
    &TOPOLOGY
      &CENTER_COORDINATES
      &END CENTER_COORDINATES
    &END TOPOLOGY
  &END SUBSYS
&END FORCE_EVAL
```

官方注释要点（照录）：

| 注释 | 含义 |
|---|---|
| `BASIS_SET_FILE_NAME BASIS_RI_cc-TZ` | 常见元素（H,C,N,O；F,Al,Cl,Si,P,S 只有 TZ 基组） |
| `AUTO_BASIS RI_AUX LARGE` | 无现成 RI 基组时用；可选 SMALL/MEDIUM/LARGE/HUGE |
| `ADMM_PURIFICATION_METHOD NONE` | **纯化未实现** |
| `EXCH_CORRECTION_FUNC PBEX` | 试不同选项或用默认 |
| `METHOD BASIS_PROJECTION` | **其它方法未实现** |
| `FREE_HFX_BUFFER .FALSE.` | "这是总能工作的选项"；设 `.TRUE.` 可能段错误 |
| `BLOCK_SIZE -1` | 自动；内存紧张时设 1 |
| `BASIS_SET RI_AUX RI_TZ` | **轨道基组与 RI 基组应当匹配** |
| `BASIS_SET AUX_FIT cpFIT3` | 用能负担的最大者 |
| `POTENTIAL GTH-HF-q1/q6` | 赝势须与 HF 参考态一致 |

`[G层提示]` 注意 `T_C_G_DATA t_c_g.dat`——周期性 HFX 需要截断 Coulomb 的数据文件。

---

## 4. 低标度后 HF（官方）

### 4.1 定位（官方，重要）

官方原文：

> While these low-scaling methods have more favorable scaling than their standard implementations (**sub-cubic vs quartic**), they suffer from a **heavy prefactor**. Therefore, they are only interesting for **large to very large systems (hundreds of atoms)**, and will still consume a lot of resources. For smaller system, the **standard MP2 and RPA implementations are recommended** (they also have gradients implemented).

`[G层提示]` 这是明确的选型红线：**小体系不要用低标度**，prefactor 太重，反而更慢。

### 4.2 理论要点（官方）

- 所有方程在**原子轨道（AO）基**中表述
- 用 **RI 技术 + 短程度规** + **数值拉普拉斯变换**
- 短程度规增加三中心 RI 积分 `(μσ⌊P)` 的稀疏性 → 稀疏张量收缩更高效
- **最短可能的 RI 度规是 overlap**
- 官方推荐：稀疏体系（如水）用**截断 Coulomb，截断半径 1.5–2.0 Å**；稠密固体用 overlap 通常足够
- 三中心和两中心 RI ERI 用 **libint** 解析计算
- 两中心势 ERI `(Q|R)` 用 **GPW 数值**计算（因为 1/r 是长程）

### 4.3 拉普拉斯变换与积分点（官方）

> A numerical Laplace transform is used to reduce the scaling of the method. The integral is replaced by a weighted sum over a few grid points, placed according to the **MINIMAX** algorithm. Typically, using **6-8 points** is enough. CP2K can go up to **20 points**, although more points do **not necessarily** increase accuracy (and sometimes bring **numerical instability**).

官方警告：

> The MINIMAX quadrature depends on the **band gap** of the system and the **total spread of the SCF eigenvalues**. If the selected number of grid points is inappropriate, a **warning is issued**.

`[G层提示]` 看到 MINIMAX 相关警告要重视——说明积分点数与体系的带隙/本征值分布不匹配。

### 4.4 官方示例 1：SOS-MP2 液态水 MD（完整输入）

官方说明：3 步 MD，32 个水分子，用 RI-MP2 优化的 cc-TZ 与 RI_TZ 基组。

```fortran
&GLOBAL
  PROJECT water32
  RUN_TYPE MD
  PRINT_LEVEL MEDIUM
&END GLOBAL
&MOTION
  &MD
    STEPS 3
  &END MD
&END MOTION
&FORCE_EVAL
  &DFT
    !cc-TZ: RI-MP2 optimized basis sets
    BASIS_SET_FILE_NAME BASIS_RI_cc-TZ
    POTENTIAL_FILE_NAME POTENTIAL
    SORT_BASIS EXP

    &MGRID
      CUTOFF 600
      REL_CUTOFF 50
      NGRIDS 5
    &END MGRID

    &SCF
      SCF_GUESS RESTART
      EPS_SCF 1.0E-6
      MAX_SCF 40
    &END SCF

    &XC
      &XC_FUNCTIONAL NONE
      &END XC_FUNCTIONAL
      &HF
        FRACTION 1.0
        &INTERACTION_POTENTIAL
          !TC potential with cutoff < L/2 for periodic HFX
          POTENTIAL_TYPE TRUNCATED
          CUTOFF_RADIUS 4.5
        &END INTERACTION_POTENTIAL
        &MEMORY
          !maximum memory allocated to HFX ERI storage, per MPI rank
          !the optimal number depends on the specifics of the computer
          MAX_MEMORY 4000
        &END MEMORY
      &END HF
      &WF_CORRELATION
        !explicit opposite-spin scaling
        SCALE_S 1.3
        &RI_SOS_MP2
          !MINIMAX quadrature by default
          QUADRATURE_POINTS 6
        &END RI_SOS_MP2
        !Enabling low-scaling
        &LOW_SCALING
          MEMORY_CUT 3
        &END LOW_SCALING
        &RI
          &RI_METRIC
            !Short range RI metric for SOS-MP2
            POTENTIAL_TYPE TRUNCATED
            CUTOFF_RADIUS 1.5
          &END RI_METRIC
        &END RI
        &INTEGRALS
          ERI_METHOD GPW
          &WFC_GPW
            !Safe yet faster than default values
            CUTOFF 200
            REL_CUTOFF 40
          &END  WFC_GPW
        &END INTEGRALS
      &END WF_CORRELATION
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 9.8528 9.8528 9.8528
    &END CELL
    &TOPOLOGY
      COORD_FILE_FORMAT XYZ
      COORD_FILE_NAME ./H2O-32.xyz
    &END TOPOLOGY
    &KIND H
      BASIS_SET cc-DZ
      BASIS_SET RI_AUX RI_DZ
      POTENTIAL GTH-HF
    &END KIND
    &KIND O
      BASIS_SET cc-DZ
      BASIS_SET RI_AUX RI_DZ
      POTENTIAL GTH-HF
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

官方说明要点：

| 要点 | 官方原文/说明 |
|---|---|
| 短程 RI 度规 | 用截断 Coulomb，半径 **1.5–2.0 Å** 更安全；水的 overlap 度规**精度不够** |
| 周期性 HFX | 必须用截断 Coulomb 作 HFX 势，**截断半径 < L/2**。示例中的 4.5 Å "somewhat small"，更大水盒子更好 |
| 预优化 RI 基组 | "Whenever available, one should use pre-optimized RI basis sets for better performance"；自动生成精度可以但**更大、效率更低** |
| `SCALE_S 1.3` | 显式 opposite-spin 缩放 |

### 4.5 官方示例 2：RPA 体相 TiO₂ 晶胞优化（完整输入）

官方说明：RPA@PBE0 的 2 步晶胞优化，72 个原子。用 **ADMM2** 加速 HF。

```fortran
&GLOBAL
  PROJECT TiO2
  RUN_TYPE CELL_OPT
  PRINT_LEVEL MEDIUM
&END GLOBAL
&MOTION
  &CELL_OPT
    MAX_ITER 2
  &END CELL_OPT
&END MOTION
&FORCE_EVAL
  STRESS_TENSOR ANALYTICAL
  &DFT
    BASIS_SET_FILE_NAME BASIS_ccGRB_UZH
    BASIS_SET_FILE_NAME BASIS_ADMM_UZH
    POTENTIAL_FILE_NAME POTENTIAL_UZH
    SORT_BASIS EXP
    !automatically generated RI basis set
    AUTO_BASIS RI_AUX SMALL

    !enabling the ADMM2 approximation
    &AUXILIARY_DENSITY_MATRIX_METHOD
      METHOD BASIS_PROJECTION
      ADMM_PURIFICATION_METHOD NONE
      EXCH_CORRECTION_FUNC PBEX
    &END AUXILIARY_DENSITY_MATRIX_METHOD

    &MGRID
      CUTOFF 600
      REL_CUTOFF 50
      NGRIDS 5
    &END MGRID

    &SCF
      EPS_SCF 1.0E-6
      MAX_SCF 20
      &OT
        PRECONDITIONER FULL_ALL
        MINIMIZER DIIS
      &END OT
      &OUTER_SCF
        MAX_SCF 5
        EPS_SCF 1.0E-6
      &END OUTER_SCF
    &END SCF

    &XC
      &XC_FUNCTIONAL
        &PBE
          SCALE_X 0.75
        &END PBE
      &END XC_FUNCTIONAL
      &HF
        FRACTION 0.25
        !always use a short range potential < L/2 in periodic HFX
        &INTERACTION_POTENTIAL
          POTENTIAL_TYPE TRUNCATED
          CUTOFF_RADIUS 4.5
        &END INTERACTION_POTENTIAL
        &MEMORY
          !maximum memory allocated to HFX ERI storage, per MPI rank
          !the optimal number depends on the specifics of the computer
          MAX_MEMORY 4000
        &END MEMORY
      &END HF
      &WF_CORRELATION
        &RI_RPA
          MINIMAX_QUADRATURE
          QUADRATURE_POINTS 6
          !calculate EXX with ADMM, using the same HF section as in SCF
          !so that the integrals can be resued without recomputing
          ADMM
          &HF
            FRACTION 1.0
            &INTERACTION_POTENTIAL
              POTENTIAL_TYPE TRUNCATED
              CUTOFF_RADIUS 4.5
            &END INTERACTION_POTENTIAL
          &END HF
        &END RI_RPA
        !enabling low-scaling
        &LOW_SCALING
          MEMORY_CUT 3
        &END LOW_SCALING
        &RI
          !overlap RI metric is appropriate for dense systems
          &RI_METRIC
            POTENTIAL_TYPE IDENTITY
          &END RI_METRIC
        &END RI
        &INTEGRALS
          ERI_METHOD GPW
          !Safe yet faster than default values
          &WFC_GPW
            CUTOFF 200
            REL_CUTOFF 40
          &END WFC_GPW
        &END INTEGRALS
      &END WF_CORRELATION
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 9.330 9.330 9.107
    &END CELL
    &TOPOLOGY
      COORD_FILE_FORMAT XYZ
      COORD_FILE_NAME ./TiO2.xyz
    &END TOPOLOGY
    &KIND Ti
      BASIS_SET ccGRB-D-q12
      BASIS_SET AUX_FIT admm-dz-q12
      POTENTIAL GTH-PBE0-q12
    &END KIND
    &KIND O
      BASIS_SET ccGRB-D-q6
      BASIS_SET AUX_FIT admm-dz-q6
      POTENTIAL GTH-PBE0-q6
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

#### RPA@PBE0 的执行顺序（官方解释，重要）

官方原文：

> In RPA@PBE0, the SCF is first converged at the **PBE0** level of theory. Then, the RPA correlation energy is computed using the **PBE0 orbitals and eigenvalues**, and finally, the PBE0 exchange-correlation energy is **replaced by the exact exchange energy (EXX)** calculated with the same orbitals.

即三步：
1. PBE0 级别收敛 SCF
2. 用 PBE0 轨道与本征值算 RPA 相关能
3. 用相同轨道算 EXX，**替换** PBE0 的 XC 能

官方优化技巧：

> If taken to be the same as the SCF (except for `FRACTION` and `MEMORY`), the stored ERIs **can be reused and rescaled** instead of recomputed, thus saving precious computational time.

`[G层提示]` 这是为什么示例里 `&HF` 段**出现两次**（一次给 SCF，一次给 RPA）。保持两段一致（除 `FRACTION`/`MEMORY`）可复用积分。

官方其他说明：
- `ADMM` 关键字在 RPA 段中指定 EXX 用 ADMM 近似
- `MINIMAX_QUADRATURE` 显式请求，是效率上的必要步骤——**默认网格是 Clenshaw-Curtis，同样精度需要更多积分点**
- 稠密体系用 **overlap 度规**（`POTENTIAL_TYPE IDENTITY`）

### 4.6 低标度后 HF 的关键参数（官方，重要）

| 参数 | 位置 | 官方说明 |
|---|---|---|
| `SORT_BASIS` | DFT 段 | **应设为 `EXP`**。按指数排序基函数 → 增加稀疏性 → 提升性能 |
| `EPS_FILTER` | `LOW_SCALING` 段 | 稀疏张量收缩的块稀疏阈值，**安全默认 `1.0×10⁻⁹`**。放宽可显著加速，**不建议高于 `1.0×10⁻⁸`** |
| `MEMORY_CUT` | `LOW_SCALING` 段 | 影响大张量收缩的批处理策略。默认 **5**。**注意 `MEMORY_CUT 3` 不等于总内存除以 3**（初始/最终张量及计算其余部分的数据不受影响）。更高值降低内存占用但有性能开销 |
| RI METRIC | `RI/RI_METRIC` 段 | 周期计算中**对性能至关重要**。更短程的度规通常更高效；更长程的（如 1.5 Å 截断的 TC）可能更准确 |

### 4.7 官方文件位置

官方原文给出的示例文件：
`https://github.com/cp2k/cp2k-examples/tree/master/post_hartree_fock`

---

## 5. 半经验方法（官方）

### 5.1 章节结构

| 页面 | 状态 |
|---|---|
| Extended Tight Binding（xTB） | **正文完整**（§5.2） |
| Density Functional Tight Binding（DFTB） | **占位页** |

官方 DFTB 页原文：

> Unfortunately, nobody has gotten around to writing this page yet :-(

### 5.2 GFN-xTB（官方）

#### 实现途径（官方）

| 实现 | 可用方法 |
|---|---|
| **CP2K 原生** | GFN0-xTB、GFN1-xTB |
| **tblite 库** | GFN1-xTB、IPEA1-xTB、GFN2-xTB |

引用：Grimme2017（GFN1）、Bannwarth2019（GFN2）、Katbashev2025、Alizadeh2026（tblite 集成）。

#### 能量分解（官方公式）

GFN1-xTB：

```
E_GFN1-xTB = E_EL + E_IES + E_REP + E_DISP + E_XB
```

GFN2-xTB（用各向异性静电 AES 替代/补充各向同性）：

```
E_GFN2-xTB = E_EL + E_AES + E_REP + E_DISP
```

各项官方说明：

| 项 | 内容 |
|---|---|
| `E_EL` | 电子能：基于零阶哈密顿 h⁰、价分子轨道 Ψᵢ、占据数 nᵢ，以及分数占据带来的电子温度×熵项 |
| `E_IES` | 各向同性静电：二阶自洽项 + 三阶对角项（Mulliken 电荷 qA 的三次修正） |
| `E_AES` | 各向异性静电：含原子偶极矩 μA 与四极矩 θA；相互作用张量含**短程阻尼函数 f** |
| `E_REP` | 排斥：原子对势，含有效核电荷与参数 kf、α |
| `E_DISP` | 色散：GFN1 用 **D3 + BJ 阻尼**；GFN2 用 **D4 + 自洽电荷** |
| `E_XB` | 卤键修正（元素特定） |

#### 原生实现关键字（官方）

| 关键字 | 作用 |
|---|---|
| `CHECK_ATOMIC_CHARGES` | 检查三次电荷对角贡献的数值稳定性 |
| `USE_HALOGEN_CORRECTION` | 开关卤键修正 `E_XB`，**默认包含** |
| `DO_NONBONDED` | 加入通用修正势以校正键/原子特定相互作用 |
| `PARAMETER` | 修改 xTB 参数 |
| `DO_EWALD` | 周期性边界条件需开启。**从 CP2K 2026.2 起周期度直接取自晶胞定义，此关键字已废弃** |

官方原文：

> The additional keywords `COULOMB_INTERACTION`, `COULOMB_LR` and `TB3_INTERACTION` are **for debugging purposes only** and it is recommended to use the default options here.

#### tblite 实现（官方）

`METHOD` 可选值：

| 值 | 方法 |
|---|---|
| `GFN1` | GFN1-xTB |
| `GFN2` | GFN2-xTB |
| `IPEA1` | IPEA1-xTB（GFN1 的变体） |
| `PARAM` | 从 `PARAM` 指定的文件读取参数（格式遵循 tblite 规范） |

启用方式（官方）：

> set the `METHOD` keyword to `xTB` and the `GFN_TYPE` in the `XTB` block to `tblite`.

官方示例：

```fortran
&QS
  METHOD xTB
  &XTB
    GFN_TYPE TBLITE
    SCC_MIXER AUTO
    &TBLITE
      METHOD GFN2
      ACCURACY 1.0
    &END TBLITE
  &END XTB
&END QS
```

`ACCURACY`：控制 tblite 电子混合器的收敛阈值，**值越小收敛越紧**。

#### 官方示例 1：GFN2-xTB 冰 Ih 单点（含 k 点）

```fortran
&GLOBAL
  PRINT_LEVEL LOW
  PROJECT ice_Ih_GFN2_k333
  RUN_TYPE ENERGY
&END GLOBAL

&FORCE_EVAL
  METHOD Quickstep
  &DFT
    &QS
      EPS_DEFAULT 1.0E-12
      METHOD xTB
      &XTB
        GFN_TYPE TBLITE
        &TBLITE
          METHOD GFN2
          ACCURACY 0.1
        &END TBLITE
      &END XTB
    &END QS
    &KPOINTS
      SCHEME MACDONALD 3 3 3 0.0 0.0 0.0
      FULL_GRID T
    &END KPOINTS
    &SCF
      EPS_SCF 1.0E-9
      MAX_SCF 300
      SCF_GUESS MOPAC
      &MIXING
        METHOD DIRECT_P_MIXING
        ALPHA 0.2
      &END MIXING
      &PRINT
        &RESTART OFF
        &END RESTART
      &END PRINT
    &END SCF
  &END DFT
  &SUBSYS
    &CELL
      PERIODIC XYZ
      A 7.678093000000 0.000000000000 0.000000000000
      B 3.839046000000 6.649423000000 0.000000000000
      C 0.000000000000 0.000000000000 7.234567000000
    &END CELL
    &COORD
      SCALED
      H   0.000007000000  0.334718000000  0.199799000000
      ...（共 36 个原子，此处从略，完整坐标见官方页面）
    &END COORD
  &END SUBSYS
&END FORCE_EVAL
```

官方说明：

> Please note that **k-points are fully supported for tblite in CP2K**.

#### 官方示例 2：spGFN2-xTB 开壳层（三重态 O₂）

官方说明：

> In case of open-shell calculations, a spin-polarization term can be enabled with the `LSD` keyword in CP2K. In this case, tblite **automatically allows the usage of spGFN2-xTB**.

```fortran
&FORCE_EVAL
  &DFT
    LSD
    MULTIPLICITY 3
    &QS
      EPS_DEFAULT 1.00E-12
      METHOD xTB
      &XTB
        GFN_TYPE TBLITE
        SCC_MIXER TBLITE
        &TBLITE
          METHOD GFN2
        &END TBLITE
      &END XTB
    &END QS
    &SCF
      ADDED_MOS 1 3
      EPS_SCF 1.e-10
      MAX_SCF 200
      SCF_GUESS MOPAC
      &PRINT
        &RESTART OFF
        &END RESTART
      &END PRINT
    &END SCF
  &END DFT
  &SUBSYS
    &CELL
      ABC 20.0 20.0 20.0
      PERIODIC NONE
    &END CELL
    &COORD
      O     0.000000    0.000000    0.000000
      O     1.208000    0.000000    0.000000
    &END COORD
  &END SUBSYS
&END FORCE_EVAL
```

`[G层提示]` 开壳层要同时给 `LSD`、`MULTIPLICITY 3`、`ADDED_MOS 1 3`（给未占据轨道）。

#### 官方示例 3：原生 GFN1-xTB 单点

```fortran
&GLOBAL
  RUN_TYPE  ENERGY
  PROJECT_NAME xtb
  PRINT_LEVEL  MEDIUM
  PREFERRED_DIAG_LIBRARY SL
&END GLOBAL
&FORCE_EVAL
 METHOD QS
&DFT
  &QS
   METHOD XTB
   &XTB
    CHECK_ATOMIC_CHARGES F    ! Keyword to check if Mulliken charges are physically reasonable
    DO_EWALD  T               ! Ewald summation is required for periodic structures
    USE_HALOGEN_CORRECTION T  ! Element-specific correction for halogen interactions (Cl, Br) with (O, N)
   &END XTB
  &END QS
  &SCF
   SCF_GUESS RESTART
   MAX_SCF 50
   EPS_SCF 1.E-6
   &OT ON
     PRECONDITIONER FULL_SINGLE_INVERSE
     MINIMIZER DIIS
   &END
   &OUTER_SCF
     MAX_SCF 200
     EPS_SCF 1.E-6
   &END OUTER_SCF
  &END SCF
 &END DFT
  &SUBSYS
    &TOPOLOGY
      COORD_FILE_FORMAT  xyz
      COORD_FILE_NAME  input.xyz
      CONNECTIVITY OFF
      &CENTER_COORDINATES
      &END CENTER_COORDINATES
     &END TOPOLOGY
    &CELL
      ABC  21.64 21.64 21.64
      ALPHA_BETA_GAMMA 90.0 90.0 90.0
      PERIODIC XYZ
    &END CELL
  &END SUBSYS
&END FORCE_EVAL
```

#### 原生实现的官方输出（可用于核对）

```
 xTB| Parameter file                                              xTB_parameters
 xTB| Basis expansion STO-NG                                                   6
 xTB| Basis expansion STO-NG for Hydrogen                                      4
 xTB| Halogen interaction potential                                            F
 xTB| Halogen interaction potential cutoff radius                         20.000
 xTB| Nonbonded interactions                                                   F
 xTB| D3 Dispersion: Parameter                                         dftd3.dat
 xTB| Huckel constants ks kp kd                        1.850     2.250     2.000
 xTB| Huckel constants ksp k2sh                                  2.080     2.850
 xTB| Mataga-Nishimoto exponent                                            2.000
 xTB| Repulsion potential exponent                                         1.500
 xTB| Coordination number scaling kcn(s) kcn(p) kc     0.006    -0.003    -0.005
 xTB| Electronegativity scaling                                           -0.007
 xTB| Halogen potential scaling kxr kx2                          1.300     0.440
```

能量分解输出（官方示例）：

```
  Core Hamiltonian energy:                                   -962.45147378153547
  Repulsive potential energy:                                   8.84897617161771
  Electronic energy:                                            0.76461561909348
  DFTB3 3rd order energy:                                       0.33228335538302
  Dispersion energy:                                           -0.76618599817727
  Total energy:                                              -953.27178463361872
```

`[G层提示]` 注意输出里出现 `DFTB3 3rd order energy`——这是三阶对角项（`E_IES` 中的 `ΓA qA³` 项）。

#### 官方示例 4：通用非键修正势

官方说明：势函数形式可自由选择，用 `FUNCTION` 指定；变量用 `VARIABLES`，参数用 `PARAMETERS`。段可**重复多次**，实现成对的元素特定修正势。**该选项实现了解析梯度**。

```fortran
   &XTB
    CHECK_ATOMIC_CHARGES F
    DO_EWALD  T
    USE_HALOGEN_CORRECTION T
    DO_NONBONDED T               ! Possible option to include a generic non-bonded potential
     &NONBONDED                  ! Specification of the potential, keyword can be repeated
      &GENPOT
       ATOMS Kr Br
       FUNCTION Aparam*exp(-Bparam*r)-Cparam/r**8  ! Potential formula has to be specified
       PARAMETERS Aparam Bparam Cparam             ! Parameters included in the formula above
       VALUES 70.0 1.0 0.0                         ! Explicit values for the parameters
       VARIABLES r
       RCUT 40.5
      &END GENPOT
     &END NONBONDED
   &END XTB
```

官方重要警告：

> Note that the generic nonbonding potential correction is **CP2K specific** and thus the so-obtained energy **differs from the original GFN1-xTB method**.

即：用了 `NONBOND` 修正后，能量不再等同于标准 GFN1-xTB，公式为：

```
E_GFN1-xTB+NONBOND = E_GFN1-xTB + E_NONBOND
```

参数修改途径（官方）：
- 加 `PARAMETER` 段并用对应关键字指定调整后的值
- 或给出修改后参数文件的路径：`PARAM_FILE_PATH` + `PARAM_FILE_NAME`

---

## 6. X 射线谱（官方页面清单）

`methods/properties/x-ray/index.html` 列出 4 个子页：

| 页面 | URL | 状态 |
|---|---|---|
| X-Ray Absorption from ΔSCF | `x-ray/delta-scf.html` | **未采集**（已登记缺口） |
| X-Ray Absorption from TDDFT | `x-ray/tddft.html` | **未采集**（已登记缺口） |
| X-Ray Absorption from RTP and δ-Kick perturbation | `x-ray/delta-kick.html` | **未采集**（已登记缺口） |
| X-Ray Ab-Initio Correction Scheme | `x-ray/correction_scheme.html` | **未采集**（已登记缺口） |

`[G层提示]` 四条路径对应四种 X 射线吸收谱计算方案：
1. **ΔSCF**：约束占据的差分自洽场
2. **TDDFT**：线性响应
3. **RTP + δ-Kick**：实时间传播 + 脉冲扰动（与 §7 的 RTBSE 同属实时间框架）
4. **Ab-Initio Correction Scheme**：从头算修正方案

---

## 7. RTBSE 与振动耦合（官方）

### 7.1 实时间 Bethe-Salpeter 传播（RTBSE）

**引用**：Marek2025。

官方原文：

> Instead of solving the Casida equation in the linear response regime, an explicit time-integration of the equation of motion of electrons can be carried out to determine the excitation frequencies. In the real-time Bethe-Salpeter propagation (RTBSE) method, the equation of motion is the **von Neumann equation** for the single particle density matrix ρ̂ with an effective Hamiltonian Ĥ.

```
dρ̂/dt = −i [ Ĥ(t), ρ̂(t) ]
```

#### 与 TDDFT 的关键区别（官方）

> Instead of using TDDFT functionals, the **COHSEX approximation to the self-energy** is employed to calculate the time dependent behaviour of the density matrix [Attaccalite2011].

**前置要求**（官方）：

> This requires a **previous determination of the screened Coulomb potential**, done via the bandstructure **GW** calculation.

`[G层提示]` RTBSE **必须先做 GW 计算**（`FORCE_EVAL/PROPERTIES/BANDSTRUCTURE/GW`）得到屏蔽库仑势。

#### 时间步进方案（官方）

```
ρ̂(t+Δt) = e^(−iĤ(t+Δt)Δt/2) e^(−iĤ(t)Δt/2) ρ̂(t) e^(iĤ(t)Δt/2) e^(iĤ(t+Δt)Δt/2)
```

官方称之为 **enforced time reversal scheme**（ETRS）[Castro2004]。

有效哈密顿量（官方）：

```
Ĥ(t) = ĥ_G0W0 + Û(t) + V̂_Hartree[ρ̂(t)] − V̂_Hartree[ρ̂₀] + Σ̂_COHSEX[ρ̂(t)] − Σ̂_COHSEX[ρ̂₀]
```

其中 ρ̂₀ 是 GW 分子轨道确定的密度矩阵，Û(t) 是外加场。

#### 激发方案（官方）

官方原文：

> Without the external field Û(t), the density matrix only rotates in phase but does not produce any measurable dynamics.

两种激发：
1. **实时间脉冲**：Û(t) 按某个有限时变场 E⃗(t) 的形式
2. **无穷尖锐的 δ 脉冲**：极限 E⃗(t) → I e⃗ δ(t)，I 为脉冲强度，e⃗ 为方向

#### 可观测量（官方）

电偶极矩：

```
μᵢ(t) = Tr( ρ̂(t) (x̂ᵢ − x_{i,CC}) )
```

电极化率（与光吸收谱相关）：

```
αᵢⱼ(ω) = μᵢ(ω) / Eⱼ(ω)
```

阻尼因子 γ 用于稳定傅里叶变换 [Müller2020]：

```
μᵢ(ω) = ∫_0^T dt e^(−γt) e^(iωt) μᵢ(t) = ∫_0^T dt e^(i(ω+iγ)t) μᵢ(t)
```

官方：对实场做 FT 时，这会在振荡频率处给出 **Lorentzian 峰**，出现在相应极化率张量元的**虚部**。

#### 运行方式（官方）

| 设置 | 说明 |
|---|---|
| `RTBSE` 段 | 包含该段即启动 RTBSE 运行；`SECTION_PARAMETERS` 可把 TDDFT 方法作为**调试方法** |
| `TIMESTEP` / `STEPS` | 控制每步大小与总传播时间。**更小的 TIMESTEP 提高可捕获的最大能量 ω**；**更大的总时间（STEPS）提高能量分辨率（更小的 Δω）** |
| 各向同性 | 气相/各向同性极化率需**跑 3 次**计算以确定极化率张量的迹 |

#### ETRS 精度（官方）

| 关键字 | 说明 |
|---|---|
| `EPS_ITER` | 控制 ETRS 循环自洽精度。**更小阈值（更高精度）→ 传播更稳定**，但可能需要更小的时间步/更多自洽迭代 |
| `MAX_ITER` | 单时间步最大自洽迭代数，超过则中断并报不收敛 |

官方警告：

> If the propagation is converging poorly (**>50 ETRS iterations**), smaller `TIMESTEP` may stabilize the propagation.

官方状态输出示例：

```
 RTBSE| Simulation step         Convergence     Electron number  ETRS Iterations
 RTBSE|               0     0.55891101E-008     0.16000000E+002                5
 RTBSE| Simulation step         Convergence     Electron number  ETRS Iterations
 RTBSE|               1     0.31847656E-008     0.16000000E+002                5
 RTBSE| Simulation step         Convergence     Electron number  ETRS Iterations
 RTBSE|               2     0.38793291E-008     0.16000000E+002                5
```

#### 指数化方法（官方）

`MAT_EXP` 关键字：

| 方法 | 适用范围 | 说明 |
|---|---|---|
| `BCH` | TDDFT **和** RTBSE | 用 Baker-Campbell-Hausdorff 展开的对易子级数计算矩阵指数效应 |
| `EXACT` | **仅 RTBSE** | 对角化瞬时哈密顿量，精确求指数 |

对非精确方法：
- `EXP_ACCURACY`：指数级数截断阈值
- `MAX_ITER`：最大迭代数，超过则停止并报不收敛

#### 激发方式（官方）

- 实时间脉冲 → `EFIELD` 段
- δ 脉冲 → `APPLY_DELTA_PULSE` + `DELTA_PULSE_DIRECTION`（e⃗ 向量）+ `DELTA_PULSE_SCALE`（I，**原子单位**）

官方警告：

> Note that the definition of the vector is **different** from the definition used in the TDDFT method.

官方输出：

```
 RTBSE| Applying delta puls
 RTBSE| Delta pulse elements (a.u.) :   -0.1000E-003  -0.0000E+000  -0.0000E+000
 RTBSE| Metric difference after delta kick                       0.61399576E-004
```

官方警告：

> If this metric difference is **approaching 1.0**, the ETRS cycle might have trouble converging - we recommend **reducing** the `DELTA_PULSE_SCALE`.

#### 打印可观测量（官方）

| 打印段 | 内容 |
|---|---|
| `DENSITY_MATRIX` | 每个时间步把 MO 基下的密度矩阵元写入文件 |
| `FIELD` | 每个时间步施加的电场元；默认文件名含 `FIELD` |
| `MOMENTS` | 每个时间步的电偶极矩元。默认**实部与虚部都打印到标准输出**；指定文件名时实/虚分量存到**不同文件** |
| `MOMENTS_FT` | 偶极矩时间序列的傅里叶变换；默认文件名含 `MOMENTS_FT` |
| `POLARIZABILITY` | 极化率的傅里叶变换元。可指定元；未指定时会做合理猜测；默认文件名含 `POLARIZABILITY` |
| `RESTART` | 控制重启文件名。产生**三个文件**：最后收敛时间步的瞬时密度矩阵的实部与虚部（二进制）+ 一个 `info` 文件（存最后时间步索引） |

官方关于重启的重要提示：

> note that for RT-BSE calculations, the `EACH` section should have `MD` keyword set to **1** to enable restarts at arbitrary number of iteration steps, **default is 20**

官方续跑机制：

> When `RESTART`, `MOMENTS` and `FIELD` are saved into files, one can **continue running the calculation in the same directory for longer time without rerunning the already calculated time steps**. Note that total length of the propagation time controls the energy/frequency precision, while timestep size controls the energy/frequency range.

傅里叶变换的时间中心与阻尼（官方）：

- `START_TIME`：设置傅里叶变换中心到给定时间 t₀
- `DAMPING`：控制 γ

```
f(ω) = ∫ dt e^(i(ω+iγ)t) f(t+t₀)
```

#### Padé 插值（官方）

用途：对 `MOMENTS_FT` 与 `POLARIZABILITY` 的傅里叶变换结果做 Padé 插值，**提高能量空间的点密度**（否则受总传播时间限制，`Δω ≈ 2π/T`）。

实现：接口到 **GreenX 库**（analytic continuation 组件）[Mattiat2018]。需要编译时开 **`-DCP2K_USE_GREENX=ON`**。

`PADE` 段的参数（**该段的存在即触发插值**）：

| 参数 | 含义 |
|---|---|
| `E_MIN` | 插值的能量区间起点 |
| `E_MAX` | 插值的能量区间终点 |
| `E_STEP` | 要求的插值分辨率（更小的 `E_STEP` → 更多插值点） |
| `FIT_E_MIN` | 拟合插值参数所用能量区间的起点 |
| `FIT_E_MAX` | 拟合插值参数所用能量区间的终点 |

#### 官方完整输入示例

```fortran
&REAL_TIME_PROPAGATION
    &RTBSE ! Start the RTBSE method
    &END RTBSE
    EPS_ITER 1.0E-8 ! Check convergence
    MAT_EXP BCH
    EXP_ACCURACY 1.0E-14 ! Less than EPS_ITER
    INITIAL_WFN RT_RESTART
    APPLY_DELTA_PULSE
    DELTA_PULSE_DIRECTION 1 0 0
    DELTA_PULSE_SCALE 0.0001 ! Small
    &FT
        &PADE
            E_MIN [eV] 0.0
            E_MAX [eV] 100.0
            E_STEP [eV] 0.02
            FIT_E_MIN [eV] 0.0
            FIT_E_MAX [eV] 300.0
        &END PADE
    &END FT
    &PRINT
        &MOMENTS
            FILENAME MOMENTS
        &END MOMENTS
        &MOMENTS_FT
            FILENAME MOMENTS-FT
        &END MOMENTS_FT
        &FIELD
            FILENAME FIELD
        &END FIELD
        &POLARIZABILITY
            FILENAME POLARIZABILITY
            ELEMENT 1 1
            ELEMENT 2 2 ! print two different elements of tensor
        &END POLARIZABILITY
        &RESTART
            &EACH
                MD 1
            &END EACH
        &END RESTART
    &END PRINT
&END REAL_TIME_PROPAGATION
```

官方：完整示例输入在 `cp2k-examples` 仓库。

### 7.2 光学谱中的振动耦合效应（vibronic）

官方页面 `optical/vibronicspec.html` 给出的示例是 **SO₂ 分子**。

#### 官方方法（吸收谱与激发态受力一次算完）

官方原文：

> The absorption spectrum and excited-state forces can be calculated in a **single run**. For this, we will change the `RUN_TYPE` to `ENERGY_FORCE`, **remove the `VIBRATIONAL_ANALYSIS` section** from the input above, and add the `PROPERTIES` section below to `FORCE_EVAL`.

```fortran
&PROPERTIES
  &TDDFPT
    NSTATES 10
    CONVERGENCE [eV] 1.0e-5
    ADMM_KERNEL_CORRECTION_SYMMETRIC
    &PRINT
      &FORCES
        THRESHOLD 0.01
      &END
    &END PRINT
  &END TDDFPT
&END PROPERTIES
```

`[G层提示]` 三个关键点：
1. `RUN_TYPE ENERGY_FORCE`（不是 `ENERGY`）
2. **移除** `VIBRATIONAL_ANALYSIS` 段
3. 新增 `TDDFPT/PRINT/FORCES` 且设 `THRESHOLD 0.01`

官方页只给出了 "### 2. Absorption spectrum and excited-state forces" 这一节，说明这是系列步骤中的第 2 步（第 1 步在官方页面未完整抓取到）。

### 7.3 光吸收谱的理论定位（官方 optical 索引页）

官方给出 Casida 方程（TDDFT 与 GW/BSE 共用形式）：

```
( A  B ) ( X⁽ⁿ⁾ )       ( 1   0  ) ( X⁽ⁿ⁾ )
( B  A ) ( Y⁽ⁿ⁾ ) = Ω⁽ⁿ⁾ ( 0  −1  ) ( Y⁽ⁿ⁾ )
```

A、B 矩阵的差别（官方）：

| 方法 | A 矩阵 | B 矩阵 |
|---|---|---|
| **TDDFT**（单重态） | `(ε_a^DFT − ε_i^DFT) δ_ij δ_ab + 2v_ia,jb + ⟨ia|f_xc(Ω⁽ⁿ⁾)|jb⟩` | `2v_ia,bj + ⟨ia|f_xc(Ω⁽ⁿ⁾)|jb⟩` |
| **GW/BSE** | `(ε_a^GW − ε_i^GW) δ_ij δ_ab + 2v_ia,jb − W_ij,ab` | `2v_ia,bj − W_ib,aj` |

#### 官方选型建议（重要）

| 体系 | 推荐方法 | 原因（官方） |
|---|---|---|
| 分子 | TDDFT（ALDA 或杂化泛函如 PBE0） | 计算量小、方便 |
| 电荷转移激发 | **需范围分离杂化泛函** | 激发电子在分子内显著距离转移时 ALDA 不够 |
| **金属** | ALDA 常给出好的激发能 | — |
| **半导体/绝缘体** | **GW/BSE** | ALDA 的 xc 核**未充分包含电子-空穴对的库仑相互作用（激子）**；GW/BSE 通过屏蔽库仑 `W_ij,ab` 计入电子-空穴吸引 |

官方推荐读物：C. A. Ullrich, *Time-Dependent Density-Functional Theory - Concepts and Applications*。

`[G层提示]` 这张表是选型的关键判据：**别拿 TDDFT+ALDA 算半导体/绝缘体的激子**。

---

## 8. 其它 Properties 页面状态（官方）

| 页面 | 状态 |
|---|---|
| Infrared Spectroscopy | **占位页** |
| Raman Spectroscopy | **占位页** |
| Nuclear Magnetic Resonance | **占位页** |
| STM images | 已有（见 `15_optical_and_xray.md`） |

官方红外页原文：

> Unfortunately no one has gotten around to writing this page yet :-(
>
> In the meantime, the following links might be helpful:
> - https://brehm-research.de/spectroscopy
> - https://www.cp2k.org/exercises:2018_ethz_mmm:infrared_2018

`[G层提示]` 红外/Raman/NMR 三页**至今无官方正文**。红外只有第三方链接与官方练习页。这与 `06_properties.md` §1.2 的登记一致。

---

## 9. 交叉索引

| 本文件主题 | 关联文件 | 关系 |
|---|---|---|
| **BSSE 官方出处** | A 层 `decide.md` §28 | A 层 BSSE 结论升级为官方事实；但"高斯基组高估吸附能"仍为经验级 |
| 后 HF 参考态收敛 | `03_scf_convergence.md` | 官方要求"先收敛参考态" |
| ADMM 与辅助基组 | `02_dft_methods.md`、`14_basis_and_potentials.md` | ADMM 引入第三类基组，加剧 BSSE |
| 赝势与参考态一致 | `14_basis_and_potentials.md` | `POTENTIAL GTH-HF-q1/q6` 须与 HF 参考态匹配 |
| 基组文件 | `14_basis_and_potentials.md` | `BASIS_RI_cc-TZ`、`BASIS_ccGRB`、`BASIS_ADMM` |
| 周期性 HFX 截断 Coulomb | `02_dft_methods.md` | 截断半径 < L/2，`T_C_G_DATA` |
| xTB 与 DFTB | `02_dft_methods.md`（方法族） | 半经验属 Quickstep 的 `QS/METHOD xTB` |
| k 点 | `02_dft_methods.md` | tblite 支持 k 点 |
| 光学谱 / TDDFT / BSE | `15_optical_and_xray.md` | 本文件 §7 补 RTBSE/vibronic/Casida 选型表 |
| 实时间传播 | `15_optical_and_xray.md` | RTBSE 属 `REAL_TIME_PROPAGATION` 段 |
| 振动分析 | `06_properties.md` | vibronic 示例中移除 `VIBRATIONAL_ANALYSIS` |
| GreenX 库 | `09_build_libraries.md` | Padé 插值需 `-DCP2K_USE_GREENX=ON` |
| COSMA / SpLA / libint | `09_build_libraries.md` | RPA/MP2 的加速依赖这些库 |

---

## 10. 本文件登记的新缺口（诚实标注）

| 缺口 | 说明 |
|---|---|
| X 射线谱 4 个子页正文 | `x-ray/delta-scf.html`、`tddft.html`、`delta-kick.html`、`correction_scheme.html` 均未采集 |
| DFTB 页面 | 官方占位页 |
| 红外 / Raman / NMR 页面 | 官方占位页 |
| vibronic 示例第 1 步 | 官方页只给出第 2 步，第 1 步未完整获取 |
| NEWTON-X 场景 B | 见 `17_constrained_dynamics_and_paths.md` |
| `GROUP_SIZE` / `MAX_MEMORY` 的调优细节 | 官方仅给出定性说明，未给具体数值建议 |
