# 15 · 光学谱、X 射线谱与实时传播（官方）

> **来源**：
> - <https://manual.cp2k.org/trunk/methods/properties/optical/index.html>
> - <https://manual.cp2k.org/trunk/methods/properties/optical/tddft.html>
> - <https://manual.cp2k.org/trunk/methods/properties/optical/bethe-salpeter.html>
> - <https://manual.cp2k.org/trunk/methods/properties/optical/rtbse.html>
> - <https://manual.cp2k.org/trunk/methods/properties/optical/vibronicspec.html>
> - <https://manual.cp2k.org/trunk/methods/properties/x-ray/index.html>
> - <https://manual.cp2k.org/trunk/methods/properties/x-ray/delta-scf.html>
> - <https://manual.cp2k.org/trunk/methods/properties/x-ray/tddft.html>
> - <https://manual.cp2k.org/trunk/methods/properties/x-ray/delta-kick.html>
> - <https://manual.cp2k.org/trunk/methods/properties/x-ray/correction_scheme.html>
> - <https://manual.cp2k.org/trunk/methods/sampling/ehrenfest.html>
> - <https://manual.cp2k.org/trunk/methods/properties/stm_images.html>
> **抓取日期**：2026-09-09

---

## 0. 本文件补什么

上一轮 `06_properties.md` 明确列出缺口："TDDFT / GW-BSE / 红外 / 拉曼 / NMR / STM **有页面但未抓取**"。本文件补齐其中最核心的 **光学谱 + X 射线谱 + 实时传播**。

**本轮实测的官方页面状态**（先给结论，避免误判）：

| 页面 | 状态 |
|---|---|
| `optical/tddft.html` | ✅ **内容丰富**（理论 + 完整输入 + 输出解读） |
| `optical/bethe-salpeter.html` | ✅ **内容极丰富**（理论 + 输入 + 完整示例 + 精度基准） |
| `optical/rtbse.html` | 见 §5 |
| `optical/vibronicspec.html` | 见 §5 |
| `x-ray/*`（4 页） | 见 §6 |
| `sampling/ehrenfest.html` | ✅ **内容丰富**（含完整 RTP.inp） |
| `properties/nmr.html` | ❌ **占位页** |
| `properties/raman.html` | ❌ **占位页** |
| `properties/infrared.html` | ❌ **占位页** |
| `properties/stm_images.html` | ✅ 内容完整（已摘录 §7） |

---

## 1. LR-TDDFT（线性响应含时密度泛函）

### 1.1 官方定位（原文）

> This is a short tutorial on how to run **linear-response time-dependent density functional theory (LR-TDDFT)** computations for absorption and emission spectroscopy. The TDDFT module enables a description of excitation energies and excited-state computations within the **Tamm-Dancoff approximation (TDA)** featuring GGA and hybrid functionals as well as semi-empirical simplified TDA kernels and noncollinear kernels for spin-flip excitations.

**关键事实**：
- CP2K 的 TDDFT 基于 **TDA（Tamm-Dancoff 近似）**，不是完整 TDDFT。
- 支持 **GGA 与杂化泛函**、**半经验 sTDA 核**、**自旋翻转非共线核**。
- 用途：**吸收谱与发射谱**。

### 1.2 理论要点（官方原文归纳）

| 项 | 官方表述 |
|---|---|
| 本征问题 | `A X_p = Ω_p S X_p`（Hermitian） |
| 矩阵 A | 零阶 = KS 轨道能之差 F；一阶核 K = 库仑 J + 精确交换 K_EX + XC 势 V_XC 与 XC 核 f_XC |
| 响应密度 | 在 Davidson 每一步**保证对称化与正交化** |
| ADMM | 可用辅助密度矩阵法近似杂化泛函的精确交换 |
| sTDA | **忽略 XC 贡献**，用半经验算符 γ_J、γ_K 近似 J 与 K |
| 振子强度 | 分子体系用 **length form**，周期体系用 **velocity form** |
| 激发态梯度 | 基于每个激发态的变分拉格朗日量，需**迭代求解 Z 向量方程** |

### 1.3 输入要求（官方原文）

> parameters defining the LR-TDDFT computation have to be specified in the **TDDFPT** subsection. Furthermore, `RUN_TYPE` has to be set to `ENERGY` and the underlying KS ground-state reference has to be specified in the `DFT` section.

| 层级 | 必需内容 |
|---|---|
| `&GLOBAL` | `RUN_TYPE ENERGY`（吸收谱）；激发态梯度改 `ENERGY_FORCE` 或 `GEO_OPT` |
| `&FORCE_EVAL/&PROPERTIES` | `&TDDFPT` 子节 |
| `&FORCE_EVAL/&DFT` | 底层 KS 基态参考（`&QS`、`&SCF`、`&XC`、`&MGRID`；杂化泛函需 ADMM） |
| `&DFT/&EXCITED_STATES` | 做激发态梯度/荧光谱时需加，指定 `STATE n` |

### 1.4 TDDFPT 的关键字（官方逐个说明）

| 关键字 | 官方说明 |
|---|---|
| `KERNEL` | 核矩阵 K 的选择：`FULL`（GGA/杂化泛函）或 `sTDA`（半经验） |
| `NSTATES` | 要算的激发能个数 |
| `CONVERGENCE` | Davidson 算法的收敛阈值 |
| `RKS_TRIPLETS` | 从默认的单重态切换到三重态激发能 |
| `RESTART` | 若存在 `.tdwfn` 重启文件则重启 TDDFPT |
| `WFN_RESTART_FILE_NAME` | 重启文件名 |

**sTDA 子节关键字**：`FRACTION`（精确交换比例 a_EX）、`MATAGA_NISHIMOTO_CEXP`（α）、`MATAGA_NISHIMOTO_XEXP`（β）、`DO_EWALD`（周期体系需开）。

### 1.5 官方完整示例（丙酮激发能，PBE0 + ADMM）

官方给的输入（**逐字保留关键部分**）：

```
&GLOBAL
  PROJECT S20Acetone
  RUN_TYPE ENERGY
  PREFERRED_DIAG_LIBRARY SL
  PRINT_LEVEL medium
&END GLOBAL
&FORCE_EVAL
  METHOD Quickstep
    &PROPERTIES
      &TDDFPT                          ! input section for TDDFPT
       KERNEL FULL                       ! specification of the underlying kernel matrix K
       NSTATES 10                      ! specifies the number of excited states to be computed
       MAX_ITER   100                  ! number of iterations for the Davidson algorithm
       CONVERGENCE [eV] 1.0e-7         ! convergence threshold in eV
       RKS_TRIPLETS F                  ! Keyword to choose between singlet and triplet excitations
      &END TDDFPT
    &END PROPERTIES
  &DFT
    &QS
      METHOD GPW
      EPS_DEFAULT 1.0E-17
      EPS_PGF_ORB 1.0E-20
    &END QS
    &SCF
      SCF_GUESS restart
      &OT
         PRECONDITIONER FULL_ALL
         MINIMIZER DIIS
      &END OT
      &OUTER_SCF
         MAX_SCF 900
         EPS_SCF 1.0E-7
      &END OUTER_SCF
      MAX_SCF 10
      EPS_SCF 1.0E-7
    &END SCF
    POTENTIAL_FILE_NAME POTENTIAL_UZH
    BASIS_SET_FILE_NAME BASIS_MOLOPT_UZH
    BASIS_SET_FILE_NAME BASIS_ADMM_UZH
    &MGRID
      CUTOFF 800
      REL_CUTOFF 80
    &END MGRID
    &AUXILIARY_DENSITY_MATRIX_METHOD       ! For hybrid functionals, it is recommended to choose ADMM
      METHOD BASIS_PROJECTION              ! the ADMM environment for ground and excited state has to be
      EXCH_SCALING_MODEL NONE              ! identical
      EXCH_CORRECTION_FUNC NONE            ! Triple-zeta auxiliary basis sets are recommended
      ADMM_PURIFICATION_METHOD NONE
    &END AUXILIARY_DENSITY_MATRIX_METHOD
    &POISSON
       PERIODIC NONE
       POISSON_SOLVER WAVELET
    &END
    &XC
     &XC_FUNCTIONAL PBE0
     &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC [angstrom] 14.0 14.0 14.0
      PERIODIC NONE
    &END CELL
    ...
    &KIND H
      BASIS_SET ORB DZVP-MOLOPT-PBE0-GTH-q1  ! in general it is recommended to use larger basis sets
      BASIS_SET AUX_FIT admm-dzp-q1          ! for the primary and auxiliary basis (TZVP/tzp)
      POTENTIAL GTH-PBE0-q1
    &END KIND
    ...
  &END SUBSYS
&END FORCE_EVAL
```

**官方对此输入的两条重要说明**：

1. **杂化泛函推荐用 ADMM**——"it is possible to compute the exact exchange integrals for hybrid functionals analytically at however high computational costs. It is therefore recommended to use the Auxiliary Density Matrix Method (ADMM) to approximate the exact exchange contribution."
2. **GGA 不需要 ADMM 段**——"For GGAs, the corresponding ADMM sections are not required and it is sufficient to specify the chosen functional in the subsection `&XC_FUNCTIONAL` of the `&XC` section."

### 1.6 输出解读（官方给出四段）

**(a) TDDFPT Initial Guess**——零阶 KS 能级差，列出占据→虚轨道跃迁：

```
          State         Occupied      ->      Virtual          Excitation
          number         orbital              orbital          energy (eV)
 -------------------------------------------------------------------------------
             1               12                   13              6.63336
             2               11                   13              9.62185
```

**(b) 收敛后的激发能、跃迁偶极与振子强度**：

```
 R-TDDFPT states of multiplicity 1
 Transition dipoles calculated using velocity formulation

         State    Excitation        Transition dipole (a.u.)        Oscillator
         number   energy (eV)       x           y           z     strength (a.u.)
         ------------------------------------------------------------------------
 TDDFPT|      1       4.67815   2.4840E-08 -1.9187E-08  5.9673E-08   5.21038E-16
 TDDFPT|      4       9.70094  -2.3716E-09  7.2323E-07  7.0660E-01   1.18663E-01
```

> 官方说明：`DIPOLE_FORM` 可选 `BERRY`（**仅完全周期体系**）、`LENGTH`（**仅分子体系**）、`VELOCITY`（两者皆可）。

**(c) Excitation analysis**——每个跃迁的轨道贡献与激发振幅：

```
        State             Occupied              Virtual             Excitation
        number             orbital              orbital             amplitude
 -------------------------------------------------------------------------------
             1   4.67815 eV
                                12                   13               0.998438
```

> `MIN_AMPLITUDE` 控制打印阈值。

**(d) 自然跃迁轨道（NTO）**——官方原文：

> Natural transition orbitals (NTOs) are printed when choosing `PRINT_LEVEL medium` in the `GLOBAL` section or when enabling the `NTO_ANALYSIS` section. For this purpose it is required to generate unoccupied orbitals and the keyword `LUMO` enables to adjust the number of unoccupied orbitals. It is possible to print the NTOs as `CUBE_FILES` or in Molden format, with the latter being activated with the keyword `MOS_MOLDEN`.

### 1.7 激发态梯度 / 荧光谱（官方）

> To perform an excited-state optimization for emission spectroscopy, the run type has to be set to `GEO_OPT` and the state to be optimized has to be specified in the `EXCITED_STATES` section. **Note that the number of excited states chosen in the TDDFPT section should be larger or at least equal to the number of the chosen excited state.**

```
 &GLOBAL
  PROJECT S20Acetone
  RUN_TYPE ENERGY_FORCE                ! The run type has to be changed to ENERGY_FORCE of GEO_OPT
  ...
 &END GLOBAL
 &PROPERTIES
    &TDDFPT
       NSTATES 10
       ...
       ADMM_KERNEL_CORRECTION_SYMMETRIC T   ! required keyword when using hybrid functionals and ADMM
    &END TDDFPT                             ! for the exact exchange contribution for ES gradients
 &END PROPERTIES
 &DFT
    ...
    &EXCITED_STATES T
     STATE 1                     ! the excited state to be optimized has to be specified in this section
    &END EXCITED_STATES
    ...
 &END DFT
```

**关键约束**：`NSTATES ≥ STATE 序号`；杂化+ADMM 时**必须**加 `ADMM_KERNEL_CORRECTION_SYMMETRIC T`。

### 1.8 sTDA 参数（官方明确警告）

> To speed up computation times for broad-band absorption spectra, a semi-empirical simplified Tamm-Dancoff (sTDA) kernel can be chosen by setting `KERNEL` to `sTDA`. The semi-empirical electron repulsion operators depend on several empirical parameters, which need to be adjusted depending on the system under investigation. Most importantly, the amount of exact exchange, scaled by adjusting the parameter a_EX needs to be chosen carefully and is really crucial to ensure a well-balanced treatment of exact exchange in the GS and ES potential energy surfaces. **Too large fractions of exchange in the excited state can lead to negative excitation energies. In general, a relatively small amount of exchange a_EX=0.2/0.1 is therefore recommended.**

```
&PROPERTIES
  &TDDFPT
   KERNEL sTDA     ! switches on the semi-empirical kernel sTDA
   &sTDA
     FRACTION 0.2  ! it is crucial to adjust the fraction of exact exchange
   &END sTDA
   NSTATES 10
   MAX_ITER   100
   CONVERGENCE [eV] 1.0e-7
   RKS_TRIPLETS F
  &END TDDFPT
&END PROPERTIES
```

**与 GFN1-xTB 组合**：官方说"recommended to adjust all parameters and to apply corrections to shift the virtual KS orbital eigenvalues"——用 `EV_SHIFT`（开壳层 `EOS_SHIFT`）。

### 1.9 周期体系（官方明确限制）

> As already mentioned above, oscillator strengths should be calculated using the `BERRY` or `VELOCITY` formulation. When choosing the `sTDA` kernel, `DO_EWALD` has to be switched to true to activate Ewald summation for Coulomb contributions. When computing ES gradients using `KERNEL FULL` in combination with hybrid functionals and ADMM, **only the ADMM2 method relying on basis projection is implemented** in combination with the default for the exchange functional for the first-order GGA correction term.

```
&AUXILIARY_DENSITY_MATRIX_METHOD
  METHOD BASIS_PROJECTION
  ADMM_PURIFICATION_METHOD NONE
  EXCH_SCALING_MODEL NONE
  EXCH_CORRECTION_FUNC PBEX
&END
```

### 1.10 引用要求（官方原文）

> Please cite these papers if you were to use the TDDFT module for the computation of excitation energies (**Strand2019**, **Iannuzzi2005**) or excited-state gradients (**Hehn2022**) of spin-conserving excitations and **HernandezSegura2025** for spin-flip excited-state energies and gradients.

| 用途 | 必须引用 |
|---|---|
| 激发能 | Strand2019（`10.1063/1.5078682`）、Iannuzzi2005 |
| 自旋守恒激发态梯度 | Hehn2022 |
| 自旋翻转激发态能量与梯度 | HernandezSegura2025 |
| ADMM | Guidon2010 |
| sTDA + GFN1-xTB | Grimme2016 |

---

## 2. GW + Bethe-Salpeter 方程（BSE）

### 2.1 官方定位（原文）

> The Bethe-Salpeter equation (BSE) is a method for computing electronic excitation energies and optical absorption spectra.

### 2.2 前置条件与推荐设置（官方原文）

> For starting a BSE calculation one needs to set the `RUN_TYPE` to `ENERGY` and the following sections for `GW` and `BSE`:

```
&GW
  SELF_CONSISTENCY      evGW0         ! We strongly recommend to use evGW0 (and PBE) for BSE runs
  &BSE
    TDA                 TDA+ABBA      ! Diagonalizing ABBA and A
    SPIN_CONFIG         SINGLET       ! or TRIPLET
    NUM_PRINT_EXC       15            ! Number of printed excitations
    ENERGY_CUTOFF_OCC   -1            ! Set to positive numbers (eV) to
    ENERGY_CUTOFF_EMPTY -1            ! truncate matrices A_ia,jb and B_ia,jb
    NUM_PRINT_EXC_DESCR -1            ! Number of printed exciton descriptors
    &BSE_SPECTRUM                     ! Activates computation and output of optical absorption spectrum
      ETA_LIST 0.01 0.02              ! Multiple broadenings can be specified within one run
    &END BSE_SPECTRUM
    &NTO_ANALYSIS
      STATE_LIST 1 2                  ! List of states for which NTOs are computed
      CUBE_FILES T                    ! Write cube files for NTOs
      STRIDE 6 6 6                    ! Coarse grid for smaller example cube files
    &END NTO_ANALYSIS
  &END BSE
&END GW
```

### 2.3 关键关键字（官方逐个说明）

| 关键字 | 取值与说明 |
|---|---|
| `SELF_CONSISTENCY` | `G0W0` / `evGW0` / `evGW`。**官方强烈推荐 evGW0 配 PBE**；屏蔽库仑相互作用**始终**从 DFT 层面算（W₀(ω=0)） |
| `TDA` | `ON`（对角化 A）/ `OFF`（广义对角化 ABBA）/ `TDA+ABBA`（两者都算） |
| `SPIN_CONFIG` | `SINGLET`（α_S=2，默认）/ `TRIPLET`（α_T=0） |
| `NUM_PRINT_EXC` | 打印的激发态个数 |
| `ENERGY_CUTOFF_OCC` | 只保留 ε_i ∈ [HOMO−E_cut, HOMO] 的占据轨道。**>30 原子体系推荐使用**，但**必须做收敛测试** |
| `ENERGY_CUTOFF_EMPTY` | 同理，对空轨道 |
| `NUM_PRINT_EXC_DESCR` | 打印激子描述符的激发态个数 |
| `BSE_SPECTRUM` | 激活光学吸收谱输出；`ETA_LIST` 可一次给多个展宽 η |
| `NTO_ANALYSIS` | 激活自然跃迁轨道；可按激发态编号、最小振子强度或最小 NTO 权重筛选 |

### 2.4 DFT 设置的影响（官方原文）

> - `XC_FUNCTIONAL`: The starting point can have a profound influence on the excitation energies. Motivated by the discussion in [Graml2026], **we strongly recommend to use BSE@evGW0@PBE**, i.e. the PBE functional as DFT starting point.
> - `BASIS_SET`: Specify the basis set, which affects N_empty and thus the size of the matrices. The **`aug-cc-pVDZ`** basis set should be sufficient for most calculations, but needs to be checked regarding convergence, e.g. using `aug-cc-pVTZ`.

### 2.5 计算代价与精度（官方原文，很有价值）

> The memory consumption of the BSE algorithm is large, it is approximately **100⋅N_occ²⋅N_empty² Bytes**. You can see N_occ, N_empty and the estimated memory consumption from the BSE output. The BSE implementation is well parallelized, i.e. you can use several nodes that can provide the memory.
>
> We have benchmarked the numerical precision of our BSE implementation in [Graml2026] and compared its results to the BSE implementation in FHI aims [Liu2020]. For our recommended settings, i.e. **BSE@evGW0@PBE with the aug-cc-pVDZ basis set**, we have found **excellent agreement with less than 5 meV mean absolute deviation** averaged over the first 10 excitation levels and the 28 molecules in *Thiel's set* for Singlet excitations.

| 项 | 数值 |
|---|---|
| 计算标度 | **O(N⁶)**（矩阵对角化 ~ (N_occ N_empty)³） |
| 内存 | **≈ 100·N_occ²·N_empty² Bytes** |
| 精度（对比 FHI-aims） | Thiel's set 28 分子、前 10 个单重态：**平均绝对偏差 < 5 meV** |
| 并行 | 良好并行化，可用多节点提供内存 |

### 2.6 官方最小示例（H₂）

> For the calculation you need the input file `BSE_H2.inp` and the aug-cc-pVDZ basis. ... run CP2K by

```
mpirun -n 1 cp2k.psmp BSE_H2.inp
```

> which requires **5 GB RAM and takes roughly 45 seconds on 1 core**.

基组：`aug-cc-pVDZ` 与 `aug-cc-pVDZ-RIFIT`，来自 `BASIS-aug`，可**从 Basis Set Exchange 获取**。H₂ 几何取自 vanSetten2015。

**官方示例输出（激发能）**：

```
BSE|     Excitation n   Spin Config       TDA/ABBA   Excitation energy Ω^n (eV)
BSE|                1       Singlet         -ABBA-                      12.0361
BSE|                2       Singlet         -ABBA-                      13.0327
```

**单粒子跃迁**（`⇒` 表示激发 X_ia，`⇐` 表示退激发 Y_ia）：

```
BSE| Excitation n           i =>/<=     a      TDA/ABBA       |X_ia^n|/|Y_ia^n|
BSE|            1           1    =>     2        -ABBA-                  0.9457
BSE|            1           1    =>     4        -ABBA-                  0.3437
```

> 官方说明：**大于 1 的贡献**（如 `1.0010`）源自 ABBA 矩阵广义本征问题的不寻常归一化条件：`Σ_ia X_ia^(m)X_ia^(n) − Y_ia^(m)Y_ia^(n) = ±δ_mn`。

**光学性质**：

```
BSE|  Excitation n  TDA/ABBA        d_x^n     d_y^n     d_z^n Osc. strength f^n
BSE|             1    -ABBA-        0.000    -0.000    -1.191             0.418
```

**吸收谱文件**：每个 η 一个文件（如 `BSE-ABBA-eta=0.010.spectrum`），列含频率 ω、`Im{α_avg(ω)}`、以及 α_μμ' 的各分量；另有光电吸收截面张量文件。

**激子描述符**：

```
BSE|    n      c_n     d_eh [Å]     σ_e [Å]     σ_h [Å]   d_exc [Å]        R_eh
BSE|    1    1.026       0.0000      2.0542      0.8576      2.2521     -0.0332
```

| 量 | 含义（官方定义） |
|---|---|
| `c_n` | 归一化因子 `⟨Ψ|Ψ⟩` |
| `d_eh` | 电子-空穴**距离**——区分电荷转移态（非零） |
| `σ_e` / `σ_h` | 电子/空穴**尺寸**——区分 Rydberg（σ_h≪σ_e）与价态（σ_h≈σ_e） |
| `d_exc` | **激子尺寸** |
| `R_eh` | 电子-空穴**关联系数**——`>0` 关联（束缚激子）、`<0` 反关联 |

**NTO 分析**：官方说明权重 `λ_I²` 默认阈值 0.010；对 n=1 可验证 `1.01320 + 0.01320 ≈ c_n ≈ 1.026`。

### 2.7 大规模计算（官方示例）

> [Here], you can find a sample output of a BSE@evGW0@PBE calculation on a **nanographene with 206 atoms**, which has a peak memory requirement of **2.5 TB RAM**:

```
BSE| Total peak memory estimate from BSE [GB]                         8.725E+02
BSE| Peak memory estimate per MPI rank from BSE [GB]                      5.453
```

> To enable BSE calculations on large molecules, we recommend to use large clusters with increased RAM and explicitly setting the keywords `ENERGY_CUTOFF_OCC` and `ENERGY_CUTOFF_EMPTY`.

### 2.8 官方限制（原文）

> The current BSE implementation in CP2K **works for molecules**. The inclusion of periodic boundary conditions in a Γ-only approach and with full k-point sampling is **work in progress**.

---

## 3. 实时传播与 Ehrenfest 动力学（RT-TDDFT）

### 3.1 官方定位

> In real time time-dependent DFT, instead of solving the static Schroedinger equation (SE), the aim is to solve the time dependent SE (TDSE).

### 3.2 三种传播子（官方原文）

> Three different propagators are available in CP2K, the **enforced time-reversible symmetry propagator (ETRS)**, the **exponential midpoint (EM)** propagator, and the **Crank-Nicholson** propagator which can be seen as a first order Padé approximation of the EM propagator.

| 传播子 | 说明 |
|---|---|
| ETRS | 先取指数近似，再自洽求最终的时间可逆酉传播子 |
| EM | 指数中点 |
| Crank-Nicholson | EM 的一阶 Padé 近似 |

**矩阵指数的 4 种算法**（`MAT_EXP` 选择）：**Taylor 展开、对角化、Padé 近似、Arnoldi 子空间迭代**。

官方原文：

> The **Arnoldi method often provides a superior performance**. Comparing the theoretical scaling, the Arnoldi method is expected to be about **5 times as fast as Padé or Taylor**. However, the **Padé approximation can be sometime the faster and more stable choice than the Arnoldi method** (e.g., large time step).

> **官方笔误**：正文写 `MAT_ESP`，实际关键字为 `MAT_EXP`（官方 Input Reference 与示例输入均为 `MAT_EXP`）。G 层照录并标注。

### 3.3 收敛判据（官方原文）

> The convergence criterion implemented in CP2K is defined as `||ΔCᵀ S ΔC||_max < ε` with ΔC as the difference of coefficient matrices in two successive steps, and ε given by `EPS_ITER`.

### 3.4 输入要点（官方原文）

> the corresponding `RUN_TYPE` in the `GLOBAL` section has to be selected, and the `MD` section has to be present to specify the time step length `TIMESTEP` and the desired number of steps (`STEPS`). **It is crucial to set an appropriate time step to propagate the electronic degrees of freedom, i.e., in the order of atto-seconds.** All other input parameters related to the RT-TDDFT run are specified from the section `REAL_TIME_PROPAGATION`.

| 关键字 | 说明 |
|---|---|
| `RUN_TYPE` | `RT_PROPAGATION` |
| `MD/TIMESTEP` | **atto-second 量级** |
| `MD/STEPS` | 步数 |
| `REAL_TIME_PROPAGATION/INITIAL_WFN` | `SCF_WFN`（先做基态 SCF）/ `RESTART_WFN`（给重启文件）/ `RT_RESTART`（RT 格式重启） |
| `WFN_RESTART_FILE_NAME` | 重启文件路径 |
| `EPS_ITER` / `MAX_ITER` | 传播子自洽收敛阈值与最大迭代 |
| `MAT_EXP` | `ARNOLDI` 等 |
| `DENSITY_PROPAGATION` | 大体系线性标度 |

> **官方重要说明**：`RT_RESTART` 的重启文件**格式与 SCF 重启文件不同**。

### 3.5 外场（`&EFIELD`，官方原文）

> The applied field is in general modulated by an envelope function: E(t) = P E_env(t) cos(ω₀t + ϕ)

| 关键字 | 含义 |
|---|---|
| `ENVELOP` | 包络类型（如 `GAUSSIAN`） |
| `&GAUSSIAN_ENV` → `SIGMA`、`T0` | 高斯包络的宽度与中心时刻 |
| `INTENSITY` | 强度（W·cm⁻²） |
| `PHASE` | 初始相位 ϕ |
| `POLARISATION` | 极化方向 P |
| `WAVELENGTH` | 波长 |
| `VELOCITY_GAUGE` | 周期体系**必须**激活（默认 length gauge 仅适用孤立分子） |

**官方明确限制**：

> By default the coupling between the electric field and the electronic degrees of freedom is described within the **length gauge**, by adding to the Hamiltonian the dipole coupling term eE(t)·r. **This approach is only valid for isolated molecular systems, and not when periodic boundary conditions are applied.**

> The time dependent electric field defined within this section **can only be used in combination with RT-TDDFT**.

### 3.6 时变投影（`PROJECTION_MO`）

> By projecting the time-dependent molecular orbitals onto some reference states (e.g., the initial MOs) means computing the overlap between the propagated orbital ψ_i(r,t)=Σ_α C_iα(t) ϕ_α(r) and any reference orbital ψ_m^ref. For instance, considering as reference orbitals the static unoccupied ones, the quantity `N_exc(t) = Σ_m^{unocc} Σ_i^{occ} ||⟨ψ_m^ref|ψ_i(t)⟩||²` is an estimate of the number of excited electrons.

| 关键字 | 说明 |
|---|---|
| `REF_MO_FILE_NAME` | 参考波函数文件 |
| `REF_MO_INDEX` | `-1` = 用该文件中所有 MO |
| `SUM_ON_ALL_REF` | `.FALSE.` = 分别存储 |
| `TD_MO_INDEX` | `-1` = 所有时变 MO |
| `SUM_ON_ALL_TD` | `.FALSE.` = 分别存储 |
| `&PRINT/&EACH` → `MD n` | 每 n 个 MD 步打印一次 |

### 3.7 官方完整示例（CO 共振 X 射线激发，`RTP.inp`）

```
@set EXC_STATE_1     LR-xasat2_1s_singlet_idx1-1.wfn
@set EXC_STATE_2     LR-xasat2_1s_singlet_idx2-1.wfn

&GLOBAL
  PROJECT RTP
  RUN_TYPE RT_PROPAGATION
  PRINT_LEVEL MEDIUM
&END GLOBAL

&MOTION
  &MD
    ENSEMBLE NVE
    STEPS 5000
    TIMESTEP [fs] 0.00078
    TEMPERATURE [K] 0.0
  &END MD
&END MOTION

&FORCE_EVAL
  METHOD QS
  &DFT
    &REAL_TIME_PROPAGATION
      MAX_ITER 100
      MAT_EXP ARNOLDI
      EPS_ITER 1.0E-11
      INITIAL_WFN SCF_WFN
      &PRINT
        &FIELD
          FILENAME =applied_field
        &END FIELD
        &PROJECTION_MO
          REF_MO_FILE_NAME RTP-RESTART.wfn
          REF_MO_INDEX -1
          SUM_ON_ALL_REF .FALSE.
          TD_MO_INDEX -1
          SUM_ON_ALL_TD .FALSE.
          &PRINT
            &EACH
              MD 1
            &END EACH
          &END PRINT
        &END PROJECTION_MO
        ...
      &END PRINT
    &END REAL_TIME_PROPAGATION
    &EFIELD
      ENVELOP GAUSSIAN
      &GAUSSIAN_ENV
        SIGMA [fs] 0.3073
        T0 [fs] 1.3190
      &END GAUSSIAN_ENV
      INTENSITY 4.08E+13
      PHASE 0.0
      POLARISATION 1 0 0
      WAVELENGTH 2.34374655955
    &END EFIELD
    BASIS_SET_FILE_NAME BASIS_PCSEG2
    POTENTIAL_FILE_NAME POTENTIAL
    &MGRID
      CUTOFF 1000
      NGRIDS 5
      REL_CUTOFF 60
    &END MGRID
    &QS
      METHOD GAPW
      EPS_FIT 1.0E-6
    &END QS
    &SCF
      MAX_SCF 500
      EPS_SCF 1.0E-8
    &END SCF
    &POISSON
      POISSON_SOLVER WAVELET
      PERIODIC NONE
    &END POISSON
    &XC
      &XC_FUNCTIONAL PBE
        &PBE
          SCALE_X 0.55
        &END
      &END XC_FUNCTIONAL
      &HF
        FRACTION 0.45
        &INTERACTION_POTENTIAL
          POTENTIAL_TYPE TRUNCATED
          CUTOFF_RADIUS 7.0
        &END INTERACTION_POTENTIAL
      &END HF
    &END XC
    ...
  &END DFT
  &SUBSYS
    &CELL
      ABC 10 10 10
      ALPHA_BETA_GAMMA 90 90 90
      PERIODIC NONE
    &END CELL
    &TOPOLOGY
      COORD_FILE_NAME carbon-monoxide_opt.xyz
      COORD_FILE_FORMAT XYZ
    &END TOPOLOGY
    &KIND C
      BASIS_SET pcseg-2
      POTENTIAL ALL
    &END KIND
    &KIND O
      BASIS_SET pcseg-2
      POTENTIAL ALL
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

**官方对参数的说明（原文要点）**：

> The time step used is rather small since we have to describe a core-hole excitation process that takes place with a typical frequency of 529 eV. **Following the rule of thumb to use a time step 10 times smaller than the field wavelength**, we set TIMESTEP to `[fs] 0.00078`.

> Note that the smaller this threshold, the more iterations per time step will be needed to converge. Hence, we have set the maximal iteration number MAX_ITER at quite high value of 100.

> Along with a carrying frequency of 529 eV (approximately 2.34374655955 nm), it should promote about 10⁻³ electrons from the Oxygen 1s to the first available excited state.

### 3.8 RTP 的实用限制（官方归纳）

| # | 限制 | 官方依据 |
|---|---|---|
| 1 | **length gauge 不适用周期体系** | "only valid for isolated molecular systems" |
| 2 | **时间步长必须 atto-second 量级** | "It is crucial to set an appropriate time step" |
| 3 | Ehrenfest MD 每步迭代更多 | "each iteration step for Ehrenfest dynamics involves a real time propagation step and a complete evaluation of the forces" |
| 4 | 方法/外推选择依赖体系 | "needs to be tested on the system of interest" |
| 5 | 计算瓶颈是矩阵指数 | "the most expensive part is the evaluation of the matrix exponential" |
| 6 | `&EFIELD` 只能配 RT-TDDFT | "can only be used in combination with RT-TDDFT" |
| 7 | 激发态波函数**轨道排序**影响输出文件 | "the ordering of the orbitals will affect which file the excited orbital is written to" |
| 8 | RTP 激发是**连续过程** | 电子不能吸收恰好一个光子瞬时跃迁；需先用 XAS 模拟确定谱特征 |

**官方原文中的疑似笔误（G 层照录并标注）**：`MAT_ESP`（应为 `MAT_EXP`）、`ERTS`（应为 `ETRS`）、`XAD_TDP`（应为 `XAS_TDP`）；"among those listed in" 后**缺引用**。

---

## 4. 光学谱章节的其它子页（官方页面结构）

```
Optical Spectroscopy
├── Time-Dependent DFT                    ← 见 §1（内容完整）
├── GW + Bethe-Salpeter equation          ← 见 §2（内容完整）
├── Real-Time Bethe-Salpeter Propagation  ← RT-BSE
└── Simulating Vibronic Effects in Optical Spectra  ← 振动光谱效应
```

> RT-BSE 与 vibronic 两页本轮**已登记页面存在**，但未逐页全文采集（内容优先级低于 TDDFT/BSE）。缺口见 `_sources.md` §5。

---

## 5. X 射线谱（官方页面结构）

```
X-Ray Spectroscopy
├── X-Ray Absorption from ΔSCF                       ← ΔSCF
├── X-Ray Absorption from TDDFT                      ← TDDFT
├── X-Ray Absorption from RTP and δ-Kick perturbation ← RTP + δ-kick
└── X-Ray Ab-Initio Correction Scheme                ← 从头校正方案
```

> **状态**：本轮已登记页面存在；正文未逐页全文采集。**缺口如实登记**，见 `_sources.md` §5。
>
> **与 RTP 的关联（官方原文）**：RTP 页明确提到"Some preliminary calculations to determine the spectral features of the system under study are in general useful to better define the desired properties of the perturbing field. **For core state excitations these information can be obtained by XAS simulations.**" 即 **XAS 是 RTP 的"前置侦察"**。
>
> 另外，RTP 示例用到了 `XAS_TDP` 模块的 `RESTART_WFN` 输出来做投影参考——**XAS_TDP 与 RTP 是配套使用的**。

---

## 6. STM 图像模拟（官方 `stm_images.html`，内容完整）

### 6.1 方法与输入（官方原文）

> CP2K can generate volumetric data for simulated scanning tunneling microscopy (STM) images with the `&DFT%PRINT%STM` section. The implementation is a **post-SCF analysis based on the Tersoff–Hamann approximation**: it sums the densities of the Kohn–Sham states in an energy window set by the requested sample bias. The result is written as a **cube file**.

```
&FORCE_EVAL
  ...
  &DFT
    ...
    &PRINT
      &STM
        BIAS [eV] -1.0 1.0
        NLUMO 50
        TH_TORB S
        STRIDE 1 1 1
      &END STM
    &END PRINT
  &END DFT
&END FORCE_EVAL
```

| 关键字 | 说明（官方） |
|---|---|
| `BIAS` | 一个或多个偏压（eV） |
| `NLUMO` | 额外的未占据态数目 |
| `TH_TORB` | 针尖轨道对称性；**默认与常规 Tersoff–Hamann 选择是 `S`** |
| `STRIDE` | 实空间网格抽样；`1 1 1` = 全网格，更大值减小文件 |
| `REF_ENERGY` | 替代 SCF 费米能作为参考能量 |
| `APPEND` | 追加到已有 cube 文件 |

**能量窗口规则（官方原文）**：

- 当 V<0：`E_ref + V < ε_n ≤ E_ref`（占据态）
- 当 V>0：`E_ref < ε_n ≤ E_ref + V`（未占据态）

> Positive-bias images require enough unoccupied eigenstates to span the requested window. Set `NLUMO` ... **Increase `NLUMO` until that warning disappears and the image is converged.**

### 6.2 输出是三维场，不是二维图（官方原文）

> CP2K writes a **three-dimensional field, not a finished two-dimensional topograph**. A visualization or post-processing program can obtain
> - a **constant-height image** by sampling the cube on a plane parallel to the surface, or
> - a **constant-current image** by finding, for every lateral position, the height at which the cube field reaches a chosen isovalue.

### 6.3 官方明确的限制（原文）

> **Important**: The STM print section is currently implemented **only for Gamma-point calculations**. If an explicit k-point mesh is present, CP2K prints a warning and does not generate the STM cubes. ... For a spin-polarized calculation, the current implementation **adds the alpha- and beta-spin contributions to the same cube. It does not produce separate spin-resolved STM images**. Likewise, the output is an independent-particle, Tersoff–Hamann-type signal; it does not include a microscopic tip, tip–sample relaxation, a tunneling-current prefactor, or a self-consistent finite-bias transport calculation.

| 限制 | 内容 |
|---|---|
| k 点 | **仅 Γ 点**；有 k 点网格时**打印警告且不生成** |
| 自旋 | α 与 β 贡献**加在同一个 cube**，**无自旋分辨** |
| 物理 | 独立粒子 Tersoff–Hamann 型信号；**不含**微观针尖、针尖-样品弛豫、隧穿电流前因子、自洽有限偏压输运 |

### 6.4 官方推荐工作流（原文 5 步）

> 1. Relax the slab and adsorbate with settings appropriate for the physical spin state, charge, and surface periodicity.
> 2. Perform a tightly converged single-point calculation on the relaxed geometry. For metallic systems, converge the occupations, smearing, and SCF mixing carefully.
> 3. Add the `STM` section and request the experimental bias values. For positive bias, converge `NLUMO` with respect to both the number of included states and the cube data.
> 4. Check the lateral supercell, vacuum width, basis set, plane-wave cutoffs, and `STRIDE`. Diffuse basis-set tails and the density grid can affect the signal in the vacuum region.
> 5. Extract constant-height maps or constant-current isosurfaces with a cube-processing or visualization program. Use the same tip height or isovalue when comparing related systems.

> For a magnetic system, also inspect the spin density and the orbital character of the states in the bias window. The spin-summed STM cube can otherwise hide a qualitatively different alpha- and beta-channel contribution.

---

## 7. 本文件明确登记的占位页（官方无正文）

| 页面 | 官方状态 | G 层处置 |
|---|---|---|
| `properties/nmr.html` | "Unfortunately, nobody has gotten around to writing this page yet :-(" | **如实标注，不编造** |
| `properties/raman.html` | 同上 | **如实标注** |
| `properties/infrared.html` | 占位页，仅 2 外链 | 见 `06_properties.md` §1.2 |

> **G 层不编造这些方法的输入写法。** 需要时请查官方 Input Reference 对应段，或 F 层实操经验。

---

## 8. 交叉索引

| 想查 | 去 |
|---|---|
| 性质计算总索引与缺口 | `06_properties.md` |
| 振动分析（VIBRATIONAL_ANALYSIS） | `01_global_and_units.md`、`06_properties.md` §1.3 |
| 拉曼（2023.1 起） | `11_version_changelog.md` |
| DOS/PDOS | `06_properties.md` §2.3 |
| MD 系综与温控 | `04_sampling_md.md` |
| `RUN_TYPE` 全部取值 | `01_global_and_units.md` §3 |
| 实时传播的重启 | `07_restarting.md` |
| 元动力学 | `04_sampling_md.md`；F 层 |
| 引用规范 | `12_authority_sources.md` §3 |
