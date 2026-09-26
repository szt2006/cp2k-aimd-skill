# 21 · X 射线谱四页完整正文（官方）

> 来源：
> - https://manual.cp2k.org/trunk/methods/properties/x-ray/index.html
> - https://manual.cp2k.org/trunk/methods/properties/x-ray/delta-scf.html
> - https://manual.cp2k.org/trunk/methods/properties/x-ray/tddft.html
> - https://manual.cp2k.org/trunk/methods/properties/x-ray/delta-kick.html
> - https://manual.cp2k.org/trunk/methods/properties/x-ray/correction_scheme.html
> 抓取日期：2026-09-09
> 标注规则：`[默认]` = 官方 Input Reference 默认值；`[官方推荐]` = 官方正文明确推荐；`[示例]` = 官方示例取值；`[G层提示]` = G 层整理性说明（非官方原话）。

---

## 0. 本文件补什么

上一轮 `15_optical_and_xray.md` 只列了 X 射线谱的**页面清单**（4 个子页 + 1 个索引），
**没有正文**。本文件把 4 个子页的**完整内容**落地：理论、完整示例输入、输出文件格式、
调参建议、FAQ 逐条。

四页分工：

| 页面 | 方法 | 一句话定位 |
|---|---|---|
| `delta-scf.html` | ΔSCF / TP-HH | 最"手工"的路线：全电子 + 手动芯空穴，用来**定标** |
| `tddft.html` | **XAS_TDP**（LR-TDDFT） | 主力方法：芯-价分离 + 突变近似 + 芯特异 RI，可算大体系/周期性 |
| `delta-kick.html` | RT-TDDFT + δ 脉冲 | 实时传播，一次传播拿整段谱（需按轴跑 3 次） |
| `correction_scheme.html` | **GW2X** | 修 XAS_TDP 的**绝对能量偏移**，对标实验 |

> **[G层提示]** 选型速记：**要便宜 → XAS_TDP；要绝对能量准 → XAS_TDP + GW2X；**
> **要全谱一次拿 → δ-kick；要对照某个具体跃迁能 → ΔSCF 定标。**
> 三者不是替代关系，`delta-kick` 页本身就明确建议先用 XAS_TDP 确定跃迁能量再设时间步。

---

## 1. ΔSCF 路线（`delta-scf.html`）

### 1.1 流程总览

官方分 4 部分：

| Part | 内容 |
|---|---|
| 1 | 优化几何（MgO / MgS） |
| 2 | XAS 计算（`&XAS` 段，`METHOD TP_HH`） |
| 3 | ΔSCF 计算（`METHOD DSCF`）——拿**首个跃迁的精确能量** |
| 4 | 换基组做收敛性测试 |

> **[G层提示]** 官方原文说明：几何优化**不需要**全电子计算，用 GTH 赝势即可；
> 到 XAS 阶段才切到 **GAPW + 全电子基组**（`POTENTIAL ALL`）。

### 1.2 Part 1：几何优化（MgO，官方输入原文）

```fortran
&GLOBAL
  PROJECT_NAME MgO
  RUN_TYPE GEO_OPT
  PRINT_LEVEL LOW
  FLUSH_SHOULD_FLUSH .TRUE.
&END GLOBAL

&MOTION
  &GEO_OPT
    TYPE MINIMIZATION
    OPTIMIZER BFGS
    MAX_ITER 200
  &END GEO_OPT
&END MOTION

&FORCE_EVAL
  METHOD QS
  STRESS_TENSOR ANALYTICAL

&DFT
    ! in the geometry optimization there is no need to run an all-electron calculation, so we are
    ! going to make use of the GTH pseudopotentials for the core electrons.
    BASIS_SET_FILE_NAME  GTH_BASIS_SETS
    POTENTIAL_FILE_NAME  GTH_POTENTIALS

&MGRID
      NGRIDS 5
      CUTOFF 400
      REL_CUTOFF 60
    &END MGRID

&QS
      METHOD GPW ! to optimize the geometry the GPW method will be used
    &END QS

&SCF
      MAX_SCF 200
      EPS_SCF 1.0E-6
      SCF_GUESS ATOMIC

&OT
        MINIMIZER DIIS
        PRECONDITIONER FULL_ALL
      &END OT
    &END SCF

&XC
      &XC_FUNCTIONAL PBE  ! PBE exchange-correlation functional
      &END XC_FUNCTIONAL

&XC_GRID
         XC_SMOOTH_RHO NN50
         XC_DERIV NN50_SMOOTH
      &END XC_GRID
   &END XC
  &END DFT

&SUBSYS
    &COORD
      O     3.010000   1.737824   1.228827
      Mg    0.000000   0.000000   0.000000
    &END COORD

&CELL
      PERIODIC XYZ  ! we are considering the system periodic in the three directions
      ALPHA_BETA_GAMMA 60 60 60
      ABC 3.010 3.010 3.010
    &END CELL

&KIND Mg
      ELEMENT Mg
      BASIS_SET DZVP-GTH
      POTENTIAL GTH-PBE-q10
    &END KIND

&KIND O
      ELEMENT O
      BASIS_SET DZVP-GTH
      POTENTIAL GTH-PBE-q6
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

**官方注意事项（原文要点）**：

- 两原子体系不必单独写 `.xyz`，直接写 `&COORD` 即可。
- **别忘了把 `GTH_POTENTIALS` 和 `GTH_BASIS_SETS` 放进工作目录**。
- 收敛判定：输出文件里搜横幅 `*** GEOMETRY OPTIMIZATION COMPLETED ***`。
- 最终坐标在 `MgO-pos-1.xyz`；CP2K 会打印**每一步**的坐标（用索引 `i` 标出，在原子数下面一行），
  **要用最后一次迭代的位置**。
- 末尾检查警告横幅：`The number of warnings for this run is : 0`。
  非 0 就在输出里搜 warning 消息。
- MgS 同理，只是把 `ELEMENT` 换成 S；官方提醒**要检查 `GTH_BASIS_SET` 与 `GTH_POTENTIALS`
  里不同原子的名字是否一致**。

### 1.3 Part 2：XAS 计算（官方输入原文）

```fortran
&GLOBAL
  PROJECT_NAME MgX ! TASK: change X to O or S
  RUN_TYPE ENERGY
  PRINT_LEVEL LOW
  FLUSH_SHOULD_FLUSH .TRUE.
&END GLOBAL

&FORCE_EVAL
  METHOD QS

&DFT
    !where to find all-electron basis sets and potentials
    BASIS_SET_FILE_NAME  EMSL_BASIS_SETS
    POTENTIAL_FILE_NAME  POTENTIAL
    UKS

&MGRID
      NGRIDS 5
      CUTOFF 400
      REL_CUTOFF 60
    &END MGRID

&QS
      METHOD GAPW ! using GAPW for all-electron calculations
      EXTRAPOLATION ASPC
      EXTRAPOLATION_ORDER 3
      MAP_CONSISTENT
      EPS_DEFAULT 1.0E-10
      ! algorithm to construct the atomic radial grid for GAPW
      QUADRATURE   GC_LOG
      ! parameters needed for the GAPW method, look at the manual for more details
      EPSFIT       1.E-4 ! precision to give the extension of a hard gaussian
      EPSISO       1.0E-12
      EPSRHO0      1.E-8
      LMAXN0       4
      LMAXN1       6
      ALPHA0_H     10 ! Exponent for hard compensation charge
    &END QS

&SCF
      MAX_SCF 50
      EPS_SCF 1.0E-5
      SCF_GUESS ATOMIC
      ADDED_MOS 8

&MIXING
         METHOD BROYDEN_MIXING
         ALPHA 0.5
      &END MIXING

&END SCF

&XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL

&XC_GRID
         XC_SMOOTH_RHO NN50
         XC_DERIV NN50_SMOOTH
      &END XC_GRID

&VDW_POTENTIAL
        POTENTIAL_TYPE PAIR_POTENTIAL
        &PAIR_POTENTIAL
          PARAMETER_FILE_NAME dftd3.dat
          TYPE DFTD3
          REFERENCE_FUNCTIONAL PBE
          R_CUTOFF [angstrom] 16
        &END PAIR_POTENTIAL
      &END VDW_POTENTIAL
    &END XC

&XAS
      RESTART .FALSE.
      METHOD TP_HH ! transition potential half core hole
      DIPOLE_FORM VELOCITY
      STATE_TYPE 1s ! excitation from 1s orbital (K-edge calculation)
      ATOMS_LIST 1 2 ! calculate absorption for 1st and 2nd atoms in the &COORD subsection
      ADDED_MOS 8

&SCF
         EPS_SCF 1.0E-5
         MAX_SCF 200

&MIXING
            METHOD BROYDEN_MIXING
            ALPHA 0.5
         &END MIXING

&SMEAR
           ELECTRONIC_TEMPERATURE [K] 300
           METHOD FERMI_DIRAC
         &END SMEAR
      &END SCF

&LOCALIZE
      &END LOCALIZE

&PRINT
         &PROGRAM_RUN_INFO
         &END PROGRAM_RUN_INFO

&RESTART
             FILENAME ./MgX ! TASK: change X to O or S
             &EACH
               XAS_SCF 20
             &END EACH
             ADD_LAST NUMERIC
         &END RESTART

&XAS_SPECTRUM
           FILENAME ./MgX ! TASK: change X to O or S
         &END XAS_SPECTRUM

&XES_SPECTRUM
           FILENAME ./MgX ! TASK: change X to O or S
         &END XES_SPECTRUM
      &END PRINT
    &END XAS
  &END DFT

&SUBSYS
    &COORD
      X   x(X)   y(X)   z(X)
      Mg  x(Mg)  y(Mg)  z(Mg)
    &END COORD

&CELL
      PERIODIC XYZ
      ALPHA_BETA_GAMMA 60 60 60
      ABC A B C
    &END CELL

&KIND Mg
      ELEMENT Mg
      BASIS_SET Ahlrichs-pVDZ
      POTENTIAL ALL ! all-electron calculations
      LEBEDEV_GRID 80
      RADIAL_GRID 200
    &END KIND

&KIND X ! TASK: change X to O or S
      ELEMENT X ! TASK: change X to O or S
      BASIS_SET Ahlrichs-pVDZ
      POTENTIAL ALL ! all-electron calculations
      LEBEDEV_GRID 80
      RADIAL_GRID 200
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

**官方说明要点**：

- `METHOD TP_HH` = **transition potential half core hole**（半芯空穴过渡势）。
- `DIPOLE_FORM VELOCITY` = 速度规范。
- `STATE_TYPE 1s` = K 边；`ATOMS_LIST 1 2` 按 `&COORD` 里的**顺序**索引。
- 从几何优化拿最终坐标，**去掉 `SCALED`**（因为用笛卡尔坐标）。
- 这一步比几何优化慢；**若 SCF 不收敛，增大 `MAX_SCF`**。
- 输出：`MgS-xas_at1_st1.spectrum` 与 `MgS-xas_at2_st1.spectrum`
  （`at1` 对应输入里第 1 个原子，`at2` 对应第 2 个）。

**谱文件格式（官方原文照录）**：

```
  Absorption spectrum for atom      1, index of excited core MO is     2, # of lines      9
    11    531.57449433      0.00000000      0.00000019     -0.00000002      0.00000000   0.00000
    12    549.96927153      0.31337224      0.18092555      0.12793369      0.14730324   0.00000
    13    550.01480014     -0.22208298      0.24828653      0.19285978      0.14816194   0.00000
    14    550.01480014     -0.00815280      0.23149701     -0.30741602      0.14816194   0.00000
    15    574.27304606     -0.84466734      0.95907128      0.71266966      2.14117868   0.00000
    16    574.27304607     -0.01626535      0.86344807     -1.18125846      2.14117868   0.00000
    17    574.27591527      1.19525241      0.69008026      0.48796033    2.14294438   0.00000
    18    694.86428215      0.00000000     -0.00000010     -0.00000012      0.00000000   0.00000
```

列含义（官方原文）：

| 列 | 含义 |
|---|---|
| 1 | KS 虚态索引 |
| 2 | 能量（**eV**） |
| 3、4、5 | 投影到 x、y、z 的强度 |
| 6 | **吸收强度的模（我们关心的量）** |

**谱线卷积**：官方要求下载 `{{exercises:2019_conexs_newcastle:lib_tools.zip}}` 解压到输出目录，
然后运行 `./get_average_spectrum.sh`，得到 `spectrum.inp` 与 `spectrum.out`
（前者与 `.spectrum` 内容相同，后者是卷积后的吸收谱）。
想换第二个原子就把脚本里 `at1` 改成 `at2`。

> **[G层提示]** 官方提到 `S_K-edge.inp` 只需画**第 2 和第 6 列**。

### 1.4 Part 3：ΔSCF 计算

**唯一改动**：把 `&XAS` 里的 `METHOD` 从 `TP_HH` 改成

```fortran
      METHOD DSCF
```

跑完后在输出里搜：

```
Ionization potential of the excited atom:                  -92.73815588900608
```

- 单位 **Hartree**，乘 **27.211** 转 eV。
- 这就是**首个跃迁的能量**，用它把吸收谱**刚性平移**对齐。

### 1.5 Part 4：换基组测试（官方建议的 4 个）

- `pc-0`（较小基组）
- `pob-TZVP`（固体计算用基组）
- `DZVP-all`
- `Ahlrichs-def2-SVP`

**官方警告（原文）**：本练习为了在小机器/有限时间上跑，用了**简单基组**；
**生产计算必须认真做基组、XC 泛函等的收敛性测试**才能得到可靠谱。

---

## 2. XAS_TDP 路线（`tddft.html`）★主力方法

### 2.1 方法定位与引用

- CP2K 里方法名 **`XAS_TDP`**，基于**线性响应 TDDFT**。
- 依赖**芯能级特异近似**，可高效处理大体系与周期性体系。
- **K 边和 L 边都支持**。
- 细节见 **Bussy2021**；**若使用请引用该论文**（官方明确要求）。

### 2.2 三个芯特异近似（官方理论小结）

| 近似 | 内容 | 收益 |
|---|---|---|
| **芯-价分离**（core-valence separation） | 芯态与价态能量、局域性差异大，耦合弱，故**忽略来自价态的激发** | 大幅缩小空间 |
| **突变近似**（sudden approximation） | 激发芯电子时**忽略芯区之外电子的弛豫** | 可**逐个**处理激发，对角化若干小矩阵比对角化一个大矩阵标度更好 |
| **芯特异 RI** | 因前两条，所需四中心二电子积分**都涉及被激发的芯态** | 只需**以被激发原子为中心**的 RI 基 |

库仑积分近似：

\[
  (pI|Jq) \approx \sum_{\mu, \nu} \ (pI|\mu) \ (\mu|\nu)^{-1} \ (\nu|Jq)
\]

- `p,q` 为原子轨道（GTO），`I,J` 为芯轨道。
- 非零积分要求 `p,I` 与 `q,J` 有重叠；`I,J` 局域在同一原子，故 RI 基只需该原子上的 GTO。
- **K 边**只有一个芯态，`I=J`；**L 边** `I,J` 张成三个简并 `2p` 态。

XC 核（kernel）的 RI 方案：

\[
(pI|f_{xc}|Jq) \approx \sum_{\kappa, \lambda, \mu, \nu, } \ (pI|\kappa) \ (\kappa|\lambda)^{-1} \ (\lambda|f_{xc}|\mu) \ (\mu|\nu)^{-1} (\nu|Jq)
\]

密度投影：

\[
n(\mathbf{r}) \approx \sum_\nu d_\nu \ \chi_\nu(\mathbf{r})
\]

> **官方警告**：若附近有**重原子**，其芯态可能描述不好（GTO 只在自己中心才"尖锐"），
> 投影质量会下降。解决办法：**给近邻用赝势**，或**把它们的 RI 基函数加进投影**。

**成立前提（官方强调）**：要激发的芯态必须能在 KS 轨道中识别出来，
**必须有强 `1s`/`2s`/`2p` 特征且充分局域**，否则结果错误。

### 2.3 输入段与外部参数

- 参数在 `&FORCE_EVAL/&DFT/&XAS_TDP`。
- **外部必须配合设置**：
  - `RUN_TYPE` = `ENERGY`
  - `&QS/&METHOD` = `GAPW`（GAPW + 全电子基组才能准确描述芯态）
- 最重要的关键字/子段：

| 名称 | 作用 |
|---|---|
| `DONOR_STATES` | 定义**激发哪个芯态**、在哪找 |
| `KERNEL` | 定义 XC 泛函与精确交换（杂化 TDDFT） |
| `GRID` | 定义 XC 核积分网格 \((\lambda|f_{xc}|\mu)\) |

> **官方原话**：其它关键字的默认值原则上都够用。
> **第一个前提是基态计算质量要好。**

### 2.4 示例 1：CO₂ 分子（K 边，官方输入原文）

```fortran
&GLOBAL
  PROJECT CO2
  RUN_TYPE ENERGY
&END GLOBAL

&FORCE_EVAL
  &DFT
    BASIS_SET_FILE_NAME EMSL_BASIS_SETS
    POTENTIAL_FILE_NAME POTENTIAL
    AUTO_BASIS RI_XAS MEDIUM              ! size of automatically generated RI basis

    &MGRID
      CUTOFF 500
      REL_CUTOFF 40
      NGRIDS 5
    &END MGRID

    &QS
      METHOD GAPW                         ! It is necesary to use the GAPW method for
    &END QS                               ! accurate description of core states

    &POISSON
      PERIODIC NONE
      PSOLVER MT
    &END

    &SCF
      EPS_SCF 1.0E-8
      MAX_SCF 30
    &END SCF

    &XC
      &XC_FUNCTIONAL
         &HYB_GGA_XC_BHandHLYP
         &END
      &END XC_FUNCTIONAL
      &HF
         FRACTION 0.5                    ! BHandHLYP functional requires 50% exact exchange
      &END HF
    &END XC

    &XAS_TDP
      &DONOR_STATES
         DEFINE_EXCITED BY_INDEX         ! We look for states by atom index:
         ATOM_LIST 1 2                   ! we want to excite atoms 1 and 2
         STATE_TYPES 1s 1s               ! from their 1s core state.
         N_SEARCH 3                      ! The 3 lowest energy MOs need to be searched (C1s, O1s, O1s)
         LOCALIZE                        ! States need to be actively localized because O atoms are
      &END DONOR_STATES                  ! equivalent under symmetry

      GRID C 250 500                     ! Integration grid dimensions for C and O excited atoms
      GRID O 250 500                     ! there are 250 angular points (Lebedev grid) and 500
                                         ! radial points

      &KERNEL
         RI_REGION 2.0                   ! Include RI basis elements from atoms within a 2.0 Ang
                                         ! sphere radius around the excited atom for the density projection
         &XC_FUNCTIONAL
            &HYB_GGA_XC_BHandHLYP
            &END
         &END XC_FUNCTIONAL
         &EXACT_EXCHANGE
            FRACTION 0.5                 ! Definition of the functional for the TDDFT kernel
         &END EXACT_EXCHANGE             ! Here (and usually) taken to be the same as the ground state
      &END KERNEL
    &END XAS_TDP

  &END DFT
  &SUBSYS
    &CELL
      ABC 10.0 10.0 10.0
      PERIODIC NONE
    &END CELL
    &COORD
      C 5.00 5.00 5.00
      O 5.00 5.00 6.16
      O 5.00 5.00 3.84
    &END COORD
    &KIND C
      BASIS_SET 6-311G**                ! Using all-electron basis sets and potential is necessary
      POTENTIAL ALL                     ! for the correct description of core states
    &END KIND
    &KIND O
      BASIS_SET 6-311G**
      POTENTIAL ALL
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

**官方逐点解释**：

- `DONOR_STATES`：按**原子索引**定义激发原子（`ATOM_LIST 1 2`），
  激发发生在 C 的 1s 和**其中一个** O 的 1s。
  两个 O 对称等价，**不必两个都算**。
- `KERNEL/RI_REGION 2.0`：把 2.0 Å 球半径内原子的 RI 基函数加入密度投影，
  **对 C 尤其重要**（周围有两个较重的 O）。
  **若 O 用了赝势，则不需要 `RI_REGION`**。

**输出中的芯态识别报告（官方原文照录）**：

```
# Start of calculations for donor state of type 1s for atom   1 of kind C

    The following localized MO(s) have been associated with the donor state(s)
    based on the overlap with the components of a minimal STO basis:
                                             Spin   MO index     overlap(sum)
                                                1          3          1.00113

    The next best overlap for spin 1 is 0.00000 for MO with index    1

    Mulliken population analysis retricted to the associated MO(s) yields:
                                                  Spin  MO index     charge
                                                     1         3      1.002
```

> **官方判据**：**overlap 与 Mulliken 电荷都应尽量接近 1.0**。
> 这说明选中的分子轨道类型正确（此处投影到 C 1s 的 STO 上）且充分局域（该 MO 上有一个完整电子在该原子上）。
> 数值偏低说明芯能级识别出问题，**解决办法：增大 `N_SEARCH`，和/或在对称等价原子情况下用 `LOCALIZE`**。

谱信息在单独文件 `CO2.spectrum`，按每个被激发芯能级列出**激发能 + 振子强度**。

### 2.5 示例 2：NaAlO₂（K 边，周期性，官方输入原文）

```fortran
&GLOBAL
   PROJECT  sodal
   RUN_TYPE ENERGY
   PRINT_LEVEL LOW
&END GLOBAL

&FORCE_EVAL
   METHOD QS
   &DFT
      BASIS_SET_FILE_NAME  BASIS_ADMM
      ! the pcseg-n and admm-n basis set families can be downloaded at https://www.basissetexchange.org
      BASIS_SET_FILE_NAME  BASIS_PCSEG
      BASIS_SET_FILE_NAME  BASIS_MOLOPT
      POTENTIAL_FILE_NAME  POTENTIAL
      AUTO_BASIS RI_XAS MEDIUM

      &QS
         METHOD GAPW                         ! GAPW is necessary for core states
      &END QS

      &AUXILIARY_DENSITY_MATRIX_METHOD       ! The ADMM methog greatly accelerated the ground state calculation
         ADMM_PURIFICATION_METHOD NONE       ! This is the simplest ADMM scheme and has proven to work well
      &END AUXILIARY_DENSITY_MATRIX_METHOD

      &SCF
         MAX_SCF    30
         EPS_SCF    1.0E-06

         &OT
           MINIMIZER DIIS
           PRECONDITIONER FULL_ALL
         &END OT
         &OUTER_SCF
            MAX_SCF    6
            EPS_SCF    1.0E-06
         &END
      &END SCF

      &MGRID
         CUTOFF 400
         REL_CUTOFF 40
         NGRIDS 5
      &END

      &XC
         &XC_FUNCTIONAL PBE               ! This is the PBEh functional with 45% HFX
            &PBE                          ! Large fraction of HFX are ususally needed for XAS LR-TDDFT
               SCALE_X 0.55
            &END
         &END XC_FUNCTIONAL

         &HF
            FRACTION 0.45
            &INTERACTION_POTENTIAL
               POTENTIAL_TYPE TRUNCATED   ! The tuncated Coulomb potential has to be used in PBCs
               CUTOFF_RADIUS 5.0          ! with a cutoff radius lower than half the cell size
            &END INTERACTION_POTENTIAL
            &SCREENING
               EPS_SCHWARZ 1.0E-6         ! Screening HFX integrals boosts performance
            &END SCREENING
         &END HF
      &END XC

      &XAS_TDP
         &DONOR_STATES
            DEFINE_EXCITED BY_KIND        ! We define the excited atoms by kind, which is named Alx here
            KIND_LIST Alx                 ! There is only one Alx atom in the coordinates since all Al
            STATE_TYPES 1s                ! atoms are equivalent under symmetry. The Alx atom is the only
            N_SEARCH 1                    ! one decribed at all-electron level, which is why we use
         &END DONOR_STATES                ! N_SEARCH = 1. There is also no need to LOCALIZE

         TAMM_DANCOFF                     ! TDA is turned on by default, but we make it explicit here
         GRID Alx 150 300
         ENERGY_RANGE 20.0                ! This means that we onluy solve for excitation energies that are
                                          ! up to 20.0 eV above the first energy
         &OT_SOLVER
            MINIMIZER DIIS                ! The iterative OT solver is typically more efficient than
            EPS_ITER 1.0E-4               ! full diagonalization for large systems
         &END OT_SOLVER

         &KERNEL
            &XC_FUNCTIONAL PBE
               &PBE
                  SCALE_X 0.55
               &END
            &END XC_FUNCTIONAL

            &EXACT_EXCHANGE
               OPERATOR TRUNCATED
               RANGE  5.0
               SCALE 0.45
            &END EXACT_EXCHANGE
         &END KERNEL
      &END XAS_TDP
   &END DFT

   &SUBSYS
      &CELL
         ABC 10.467947   10.651128   14.393541
      &END CELL
      &TOPOLOGY
         COORD_FILE_NAME sodal.xyz
         COORD_FILE_FORMAT xyz
      &END TOPOLOGY
    &KIND O
      BASIS_SET DZVP-MOLOPT-SR-GTH
      BASIS_SET AUX_FIT FIT3
      POTENTIAL GTH-PBE
    &END KIND
    &KIND Na
      ELEMENT Na
      BASIS_SET DZVP-MOLOPT-SR-GTH
      BASIS_SET AUX_FIT FIT3
      POTENTIAL GTH-PBE
    &END
    &KIND Al
      BASIS_SET DZVP-MOLOPT-SR-GTH
      BASIS_SET AUX_FIT FIT3
      POTENTIAL GTH-PBE
    &END
    &KIND Alx                          ! All atoms but the single Alx are described using pseudopotentials
      ELEMENT Al                       ! This greatly reduces the number of basis function and the cost of
      BASIS_SET pcseg-2                ! the calculation in general. AUX_FIT basis sets are for ADMM
      BASIS_SET AUX_FIT admm-2
      POTENTIAL ALL
    &END
   &END SUBSYS
&END FORCE_EVAL
```

**官方要点**：

- **只把 1 个原子（被激发的 Alx）用全电子处理**，其余全用赝势——极大降低基函数数与总成本。
- 用 **ADMM** 大幅加速基态 HFX 计算。
- 用 **OT 迭代求解器**：只算 20.0 eV 范围内的少数本征值，标度远好于全对角化。
- `RI_REGION` **缺省即 0**；因为被激发 Al 的邻居都用赝势，**不需要额外 RI 基做密度投影**。
- 该输入对应 Bussy2021 图 4；**规模大得多，20–30 核需数小时**（主要耗时在 SCF 收敛）。

### 2.6 示例 3：TiCl₄（L 边 + 自旋轨道耦合，官方输入原文）

```fortran
&GLOBAL
  PROJECT TiCl4
  PRINT_LEVEL LOW
  RUN_TYPE ENERGY
&END GLOBAL
&FORCE_EVAL
  &DFT
    BASIS_SET_FILE_NAME  BASIS_DEF2-TZVPD
    POTENTIAL_FILE_NAME  POTENTIAL
    AUTO_BASIS RI_XAS    LARGE

    &POISSON
      PERIODIC NONE
      PSOLVER MT
    &END POISSON
    &QS
      METHOD GAPW
    &END QS

    &MGRID
      CUTOFF 800
      REL_CUTOFF 50
      NGRIDS 5
    &END

    &SCF
      EPS_SCF 1.0E-8
      MAX_SCF 200
      &MIXING
         METHOD BROYDEN_MIXING
         ALPHA 0.2
         BETA 1.5
         NBROYDEN 8
      &END MIXING
    &END SCF

    &XC
      &XC_FUNCTIONAL
         &HYB_GGA_XC_B3LYP
         &END
      &END XC_FUNCTIONAL
      &HF
         FRACTION 0.2
      &END HF
    &END XC

    &XAS_TDP
      &DONOR_STATES
         DEFINE_EXCITED BY_KIND
         KIND_LIST Ti
         STATE_TYPES 2p             ! 2p core state for L-edge
      &END DONOR_STATES             ! No need to LOCALIZE since only one Ti atom

      TAMM_DANCOFF FALSE            ! TDA is on by default, get full TDDFT like this
      DIPOLE_FORM LENGTH

      GRID Ti 500 1000              ! This is a fairly dense grid

      EXCITATIONS RCS_SINGLET       ! For SOC calculations in closed-shell system, these 3 keywords
      EXCITATIONS RCS_TRIPLET       ! are required. Singlet and triplet excitation are coupled together
      SOC                           ! with the SOC hamiltonian

      &KERNEL
         RI_REGION 5.0              ! To get the best possible density projection
      &XC_FUNCTIONAL
         &HYB_GGA_XC_B3LYP
         &END
      &END XC_FUNCTIONAL
         &EXACT_EXCHANGE
            FRACTION 0.2
         &END EXACT_EXCHANGE
      &END KERNEL
    &END XAS_TDP

  &END DFT
  &SUBSYS
    &KIND Cl
      BASIS_SET def2-TZVPD
      POTENTIAL ALL
      RADIAL_GRID 80                ! The GAPW grids are also used to evaluate the SOC operator
      LEBEDEV_GRID 120              ! it is good practice to use sligthly larger ones than the default
    &END KIND
    &KIND Ti
      BASIS_SET def2-TZVPD
      POTENTIAL ALL
      RADIAL_GRID 80
      LEBEDEV_GRID 120
    &END KIND
    &CELL
      ABC 10.0 10.0 10.0
      PERIODIC NONE
    &END CELL
    &TOPOLOGY
      COORD_FILE_FORMAT XYZ
      COORD_FILE_NAME TiCl4.xyz
      &CENTER_COORDINATES
      &END CENTER_COORDINATES
    &END TOPOLOGY
  &END SUBSYS
&END FORCE_EVAL
```

**官方要点**：

- `STATE_TYPES 2p` → **L 边**。
- **SOC 的处理方式**：用 **ZORA SOC Hamiltonian** 把**单重态与三重态激发耦合**在一起，
  故需要同时给 `EXCITATIONS RCS_SINGLET`、`EXCITATIONS RCS_TRIPLET` 和 `SOC`。
- `RADIAL_GRID 80` / `LEBEDEV_GRID 120`：**GAPW 网格也用于计算 SOC 算符，官方建议略大于默认值**。
- 该计算是基准性质的，故 `GRID`、`CUTOFF` 都取得较大。对应 Bussy2021 图 1a，**4 核约 10 分钟**。

**L 边的输出特征（官方原文）**：芯态识别给出的 overlap **大于 1**，
原因是 `2p` 态简并——候选 KS 轨道投影到 2px/2py/2pz 三个 STO 上，
为避免贡献相消而取**绝对重叠之和**。

```
  # Start of calculations for donor state of type 2p for atom   1 of kind Ti

    The following canonical MO(s) have been associated with the donor state(s)
    based on the overlap with the components of a minimal STO basis:
                                             Spin   MO index     overlap(sum)
                                                1          7          1.36751
                                                1          8          1.36751
                                                1          9          0.99786

    The next best overlap for spin 1 is 0.06653 for MO with index   27

    Mulliken population analysis retricted to the associated MO(s) yields:
                                                  Spin  MO index     charge
                                                     1         7      1.000
                                                     1         8      1.000
                                                     1         9      1.000
```

### 2.7 XAS_TDP 官方 FAQ（逐条照录要点）

**Q1：用什么泛函和基组？**

- **高 HF 交换比例的杂化泛函**在芯谱表现好；本实现中 **PBEh(α=0.45)** 与 **BHandHLYP** 有成功案例。
- **周期性边界下必须用截断库仑算符**（截断半径 **< 半胞长**）。
- 被激发原子**必须用全电子基组**；其它原子可用 **MOLOPT 基组 + 赝势**。
- 存在芯特异基组如 **pcX-n**、**cc-pCVXZ**，但**小分子基组收敛研究表明并非必需**。
- **pcseg-n 基组好用**，因为自带配套 ADMM 基。

**Q2：怎么让计算更准？**

- 第一要务是**基态计算要好**——任何改善 SCF 的改动都会反映到 LR-TDDFT 质量上。
- `EPS_FILTER` 与 `EPS_PGF_XAS` 用于筛选，**调低更慢但更准**。
- 增大 `GRID` 维度改善 XC 核数值积分质量。**角点上限 974**；径向点无上限但太大会影响性能。
  **官方建议 `GRID C 250 500` 通常足够**。
- 增大 `KERNEL/RI_REGION` 让密度投影更准；**应与更密的 `GRID` 配合**。
- RI 基默认自动生成，质量由 `&DFT/AUTO_BASIS` 控制；默认 `MEDIUM`，
  可提到 **`AUTO_BASIS RI_XAS LARGE/HUGE`**；也可提供外部 RI 基组。

**Q3：怎么让计算更快？**

- 大体系**推荐用 OT 迭代求解器**替代默认全对角化，改善标度。
- **TDA 默认开启**，一般认为质量与全 TDDFT 相当但便宜得多——**确认它是开的**。
- 大体系**强烈推荐 ADMM**（基态 HFX 是主要瓶颈）。
- **所有非激发原子都建议用赝势**（全电子基组偏大）。
- 若被激发原子的全电子基没有配套 ADMM 基，可**用全基组作为 `AUX_FIT`**；
  若该基组很弥散，**去掉最弥散的元素可能有益**。
- 代码同时有 MPI 与 OMP 并行，加核在一定程度上加速。

**Q4：怎么画 `*.spectrum` 的谱？**

- 每个 donor state 一个 `*.spectrum` 文件，含激发能 + 振子强度 → **棒状谱**，
  需用**高斯或洛伦兹函数人工展宽**才能对标实验。
- **L 边 SOC 计算会给出单重态、三重态和 SOC 三套激发结果**。
- **再次强调：XAS LR-TDDFT 谱准确但能量轴通常偏移，必须做刚性平移才能对标实验。**

**Q5：结果不对/不合理怎么办？**

两个主要原因：

1. **没找到/没识别出正确的芯态**。看 `XAS_TDP` 输出部分的 Mulliken 布居分析与 STO 重叠，
   **两者都应接近 1.0**。若不是，增大 `DONOR_STATES/N_SEARCH` 扫描更多 KS 轨道；
   若有多个对称等价原子，**务必用 `DONOR_STATES/LOCALIZE`**。
2. **XC 核 \((\lambda|f_{xc}|\mu)\) 数值积分不够准**。增大 `GRID` 密度、增大 `RI_REGION`、
   和/或提高自动生成 RI 基的质量。**用外部 RI 基也可能有帮助**，
   因为自动生成方案可能失败（官方举例：**Zn 的 def2-QZVP → 用 def2-QZVP-RIFIT**）。

最后：**算出的谱需要刚性平移才能对标实验。**

---

## 3. δ-kick 路线（`delta-kick.html`）

### 3.1 定位

- 用**实时 TDDFT（RTP）** + **δ-kick 方法**计算吸收电子谱。
- 对应线性响应路线见 `tddft.html`（即 XAS_TDP）。
- 沿 RTP 传播**采样含时偶极矩**，再**傅里叶变换**得到频域吸收谱。

### 3.2 理论要点（官方）

**响应理论**：微扰区、线性阶，含时响应在 Fourier 空间可分解——
给定频率的响应正比于同频率的扰动。诱导偶极矩 \(\mu^\omega\) 等于
极化率矩阵 \(\alpha(\omega,\omega)\) 与扰动电场 \(F^\omega\) 的乘积：

\[
\mu^\omega = \alpha(\omega, \omega) \cdot F^\omega
\]

- **LR-TDDFT**：计算特定频率 \(\omega\) 的电场激发的激发态及跃迁偶极矩，再推极化率。
- **实时方法**：在模拟开始时用**一个瞬时脉冲（含所有频率）激发所有可能跃迁**，
  然后传播受扰波函数并记录含时诱导偶极矩的涨落，最后由诱导偶极矩推出任意频率的极化率张量。

**δ-kick 扰动**：先做基态电子结构（如 DFT），再用瞬时电场扰动：

\[
F(t) = F^0 \delta(t)
\]

用**极窄高斯包络的常电场**可得相同结果。该场在 \(t=0^-\) 扰动基态波函数，
随后用数值积分含时薛定谔方程实时传播。

频域中场幅度：

\[
F^\omega = \frac{F^0}{2 \pi} \int_{-\infty}^{+ \infty} \delta(t) e^{i \omega t} dt = \frac{F^0}{2 \pi}
\]

**所有频率上的幅度都是 \(F^0/2\pi\)** —— 瞬时扰动确实包含所有频率。

\[
\mu^\omega = \frac{1}{2 \pi} \alpha(\omega, \omega)  F^0
\]

因此：

\[
\text{Re} \left[ \alpha(\omega, \omega) \right]  = 2 \pi \frac{\text{Re} \left[ \mu^\omega \right] }{F^0} \\
\text{Im} \left[ \alpha(\omega, \omega) \right] = 2 \pi \frac{\text{Im}  \left[ \mu^\omega \right] }{F^0}
\]

> 若频率远离共振，Fourier 空间中偶极矩幅度可能非常小；**原则上一次 RTP 跑就能提取整段谱**。
> 但芯激发到价激发的整段谱非常宽，**为了数值效率，传播参数通常只聚焦于谱的某一特定部分**。

**吸收谱**：线性响应假设下，极化率的实部/虚部决定响应性质——
**共振处有虚部，离共振时纯实部**。

**一次实时传播只能得到极化率张量的三个分量**：例如沿 \(x\) 施 δ-kick 得到
\(\alpha_{xx}\)、\(\alpha_{yx}\)、\(\alpha_{zx}\)（分别对应在 x、y、z 做 Fourier 变换）。
**要拿到完整张量需要跑 3 次 RTP，每个笛卡尔轴一次。**

与实验对比时常假设体系在空间所有取向上平均，则吸收谱：

\[
I(\omega)  \propto \sum_{i=x,y,z} \text{Im} \left[ \alpha_{ii}(\omega, \omega) \right]
\]

### 3.3 官方示例输入（CO 气相，沿垂直于 CO 键方向 δ-kick）

```fortran
&GLOBAL
  PROJECT RTP
  RUN_TYPE RT_PROPAGATION
&END GLOBAL

&MOTION
  &MD
    ENSEMBLE NVE
    STEPS 50000
    TIMESTEP [fs] 0.00078
    TEMPERATURE [K] 0.0
  &END MD
&END MOTION

&FORCE_EVAL
  METHOD QS
  &DFT
    &REAL_TIME_PROPAGATION
      APPLY_DELTA_PULSE .TRUE.
      DELTA_PULSE_DIRECTION 1 0 0
      DELTA_PULSE_SCALE 0.001
      MAX_ITER 100
      MAT_EXP ARNOLDI
      EPS_ITER 1.0E-11
      INITIAL_WFN SCF_WFN
      PERIODIC .FALSE.
    &END REAL_TIME_PROPAGATION
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
      SCF_GUESS RESTART
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
    &PRINT
      &MULLIKEN OFF
      &END MULLIKEN
      &HIRSHFELD OFF
      &END HIRSHFELD
      &MOMENTS
       PERIODIC .FALSE.
         FILENAME =dipole
         COMMON_ITERATION_LEVELS 100000
         &EACH
            MD 1
         &END EACH
      &END MOMENTS
    &END PRINT
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

> 官方说明：该输入是 **DFT/PBEh 级别**，用 **GAPW**，密度在全电子 **pcseg-2** 基组中展开。

### 3.4 时间步怎么选（官方规则）

- 时间步要**适配感兴趣频率**；是"分辨最高频率"与"采样时长足够"之间的折中。
- **经验规则：时间步应比最高待分辨频率对应周期小约一个数量级。**
- 例：O 1s 芯激发的 K 边约 **530 eV**，对应周期 **0.0078 fs**。
- 据 LR-TDDFT（XAS_TDP）计算，首个跃迁在 **529 eV**，振子强度 **0.044 a.u.**。
  对 δ-kick 来说，诱导偶极矩应含约 529 eV 的振荡分量，
  故 `TIMESTEP` 设为最大频率的十分之一，即 **`[fs] 0.00078`**，
  这样最快振荡由约 **10 个传播步**采样。
- 总时长由最大步数决定，此处官方正文写 **500000** 步
  （**[G层提示]** 但官方示例输入里 `STEPS` 写的是 **50000**，两处不一致，已登记到 `_sources.md` §4.6）。
- **采样越长，谱越平滑尖锐**（峰位分辨率更高）。
  **没有永远有效的规则**决定传播要多长，因为涨落强烈依赖体系；
  **务必检查谱对进一步延长采样是否收敛**。

### 3.5 场参数（官方）

- **幅度**：典型值 \(10^{-3}\)；依赖体系。
  **最佳做法是跑多个不同幅度做收敛检查**——线性区内响应应随场幅度加倍而加倍。
  **场太弱时数值噪声可能占主导。** 对孤立 CO，\(10^{-3}\) 是好值。
- **官方警告（原文）**：**CP2K 中实际施加的扰动并不是 `DELTA_PULSE_SCALE`，它依赖胞尺寸。**
  对应的幅度值会写在输出文件的 **RTP 初始化部分**。
- **偏振方向**决定最可能触发哪些激发态（选择定则）。
  本例 529 eV 跃迁**垂直于 CO 键**，故场偏振沿 \(x\)（或 \(y\)）：
  `DELTA_PULSE_DIRECTION 1 0 0`、`DELTA_PULSE_SCALE 0.001`。

### 3.6 规范选择（官方）

| 体系 | `PERIODIC` | 规范 | 说明 |
|---|---|---|---|
| 孤立体系 | `.FALSE.` | **length gauge**（长度规范） | 位置与电场算符耦合，**可用于所有微扰阶** |
| 凝聚相体系 | `.TRUE.` | **velocity gauge**（速度规范） | 需做含矢量势的规范变换，**只在一阶施加微扰** |

---

## 4. GW2X 修正方案（`correction_scheme.html`）★对标实验的关键

### 4.1 为什么需要

XAS LR-TDDFT 结果**需要刚性平移**才能对标实验，原因是：

- **自相互作用误差**
- **芯空穴产生时缺少轨道弛豫**

官方为此开发了 **ab-initio 修正方案**，理论与基准见 **Bussy2021b**（**使用请引用**）。

### 4.2 理论要点（官方）

XAS LR-TDDFT 给出的是相对基态 KS 轨道能差的激发能：

\[
\omega = \varepsilon_a - \varepsilon_I + \Delta_{xc},
\]

- \(\varepsilon_a\)：虚 MO 轨道能；\(\varepsilon_I\)：donor 芯 MO 能量。
- Koopmans 条件下，这些能量被解释为电子亲和能与电离势（IP）。
- **但 DFT 预测绝对轨道本征值很差**；又因 \(|\varepsilon_I| >> |\varepsilon_a|\)，
  若把 DFT 的 \(\varepsilon_I\) 换成**准确的 IP**，激发能预期会大幅改善。

IP 可用**二阶电子传播子方程**精确计算：

\[
\text{IP}_I = -\varepsilon_I - \frac{1}{2} \sum_{ajk}\frac{|\langle Ia||jk\rangle|^2}{-\text{IP}_I + \varepsilon_a -\varepsilon_j -\varepsilon_k} - \frac{1}{2}\sum_{abj}\frac{|\langle Ij||ab\rangle|^2}{-\text{IP}_I + \varepsilon_j - \varepsilon_a - \varepsilon_b}
\]

- \(a,b\)：虚 HF 旋轨道；\(j,k\)：占据 HF 旋轨道。
- 该理论的 DFT 推广称 **GW2X**（Shigeta2001）：
  计算**广义 Fock 矩阵**，并**分别旋转占据与虚 DFT 轨道**使其成为**赝正则**。
- 或用广义 Fock 矩阵的**对角元**近似轨道能（省去轨道旋转）——称 **GW2X\*** 方法。

### 4.3 `&GW2X` 段与关键字（官方）

- 参数在 **`&FORCE_EVAL/&DFT/&XAS_TDP/&GW2X`**。
- **GW2X 只能配合杂化泛函（或全 HF）**——否则算广义 Fock 矩阵所需的机制不存在。
- **参数很少，通常加一个空的 `&GW2X` 子段就够。**

| 关键字 | 作用 |
|---|---|
| `EPS_GW2X` | 电子传播子方程 Newton-Raphson 迭代的收敛阈值 |
| `MAX_GW2X_ITER` | 最大迭代次数 |
| `PSEUDO_CANONICAL` | 控制跑原始 GW2X 还是简化版 GW2X\*（**默认原始 GW2X 开启**） |
| `C_SS`、`C_OS` | 缩放同自旋/反自旋分量（类似 SOS- 与 SCS-MP2） |
| `XPS_ONLY` | 若设置，**只算芯 IP，跳过 XAS LR-TDDFT** |

### 4.4 示例 1：OCS（L 边 + SOC，官方输入原文）

```fortran
&GLOBAL
  PROJECT OCS
  PRINT_LEVEL MEDIUM
  RUN_TYPE ENERGY
&END GLOBAL
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME BASIS_GW2X
    POTENTIAL_FILE_NAME POTENTIAL
    AUTO_BASIS RI_XAS MEDIUM

    &MGRID
      CUTOFF 800
      REL_CUTOFF 50
      NGRIDS 5
    &END MGRID
    &QS
      METHOD GAPW
    &END QS

    &POISSON
      PERIODIC NONE
      PSOLVER MT
    &END

    &SCF
      EPS_SCF 1.0E-8
      MAX_SCF 50
    &END SCF

    &XC
      &XC_FUNCTIONAL                ! The PBEh(45%) functional
        &GGA_C_PBE
        &END
        &GGA_X_PBE
          SCALE 0.55
        &END
      &END XC_FUNCTIONAL

      &HF
         FRACTION 0.45
      &END HF
    &END XC

    &XAS_TDP
      &DONOR_STATES
         DEFINE_EXCITED BY_KIND
         KIND_LIST S
         STATE_TYPES 2p          ! Need to look for the S 2p states within the 7 MOs with lowest energy;
         N_SEARCH 7              ! one S 1s, one S 2s, three S 2s , one C 1s and one O 1s
         LOCALIZE                ! Localization is required
      &END DONOR_STATES

      EXCITATIONS RCS_SINGLET
      EXCITATIONS RCS_TRIPLET
      SOC

      GRID S  300 500

      N_EXCITED 150
      TAMM_DANCOFF

      &GW2X                      ! This is the only difference in the input file with respect to a
      &END GW2X                  ! standard XAS_TDP calculation (defaults parameters are used)

      &KERNEL
         RI_REGION 3.0
         &XC_FUNCTIONAL
            &GGA_C_PBE
            &END
            &GGA_X_PBE
              SCALE 0.55
            &END
         &END XC_FUNCTIONAL
         &EXACT_EXCHANGE
            FRACTION 0.45
         &END EXACT_EXCHANGE
      &END KERNEL

    &END XAS_TDP
  &END DFT
  &SUBSYS
    &CELL
      ABC 10.0 10.0 10.0
      PERIODIC NONE
    &END CELL
    &COORD
      C         5.0000000209        4.9999999724        5.2021372095
      O         5.0000000094        5.0000000290        6.3579624316
      S         5.0000000207        5.0000000007        3.6399034216
    &END COORD
    &KIND C
      BASIS_SET aug-pcX-2
      POTENTIAL ALL
    &END KIND
    &KIND O
      BASIS_SET aug-pcX-2
      POTENTIAL ALL
    &END KIND
    &KIND S
      BASIS_SET aug-pcX-2
      POTENTIAL ALL
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

**官方说明**：

- 与标准 XAS LR-TDDFT 输入**唯一区别就是加了 `&GW2X` 子段**。
- 此处只用默认参数，即**原始 GW2X 方案，收敛阈值 0.01 eV**。
- 用了**芯特异全电子 `aug-pcX-2` 基组**（三重 zeta 质量）。
- 该输入对应 Bussy2021b 表 II 的一个条目，但**参数更宽松**（为了让教程便宜易跑，4 核约 2 分钟）。

**输出（官方原文照录）**：

```
    - GW2X correction for donor MO with spin  1 and MO index    5:
                             iteration                convergence (eV)
                                     1                       10.047536
                                     2                        1.237503
                                     3                        0.014416
                                     4                       -0.000000

      Final GW2X shift for this donor MO (eV):   1.927146

    - GW2X correction for donor MO with spin  1 and MO index    6:
                             iteration                convergence (eV)
                                     1                        6.197650
                                     2                        4.963008
                                     3                        0.241838
                                     4                        0.000439

      Final GW2X shift for this donor MO (eV):   1.907648

    - GW2X correction for donor MO with spin  1 and MO index    7:
                             iteration                convergence (eV)
                                     1                        6.197650
                                     2                        4.963008
                                     3                        0.241838
                                     4                        0.000439

      Final GW2X shift for this donor MO (eV):   1.907648

    Calculations done:

    First singlet XAS excitation energy (eV):                165.014087
    First triplet XAS excitation energy (eV):                164.681850
    First SOC XAS excitation energy (eV):                    164.396537

    Ionization potentials for XPS (GW2X + SOC):              170.602279
                                                             169.457339
                                                             169.367465
```

**官方解读**：

- 每个 S 2p 的修正都打印出来。
- **修正相当于相对标准 XAS LR-TDDFT 平移 1.9 eV**，首个单重态激发能变为 **164.4 eV**（L₃ 边）。
- **与实验符合到 0.1 eV 以内**，明显优于 XAS LR-TDDFT。
- **芯 IP（含 SOC 效应）也给出，可直接用于生成 XPS 谱。**
- **`OCS.spectrum` 文件的内容直接就是修正后的谱。**

### 4.5 示例 2：固体 NH₃（K 边，周期性，官方输入原文）

```fortran
&GLOBAL
  PROJECT NH3
  RUN_TYPE ENERGY
  PRINT_LEVEL MEDIUM
&END GLOBAL
&FORCE_EVAL
  METHOD QS
  &DFT
    BASIS_SET_FILE_NAME BASIS_GW2X
    BASIS_SET_FILE_NAME BASIS_ADMM
    BASIS_SET_FILE_NAME BASIS_MOLOPT
    POTENTIAL_FILE_NAME POTENTIAL
    AUTO_BASIS RI_XAS MEDIUM

    &QS
      METHOD GAPW
    &END QS

    &MGRID
      CUTOFF 600
      REL_CUTOFF 50
      NGRIDS 5
    &END MGRID

    &SCF
      SCF_GUESS RESTART
      EPS_SCF 1.0E-8
      MAX_SCF 30

      &OT
         MINIMIZER CG
         PRECONDITIONER FULL_ALL
      &END OT

      &OUTER_SCF
         MAX_SCF 6
         EPS_SCF 1.0E-8
      &END OUTER_SCF

    &END SCF

    &AUXILIARY_DENSITY_MATRIX_METHOD
      ADMM_PURIFICATION_METHOD NONE
    &END AUXILIARY_DENSITY_MATRIX_METHOD

    &XC
      &XC_FUNCTIONAL
         &GGA_X_PBE
            SCALE 0.55
         &END
         &GGA_C_PBE
         &END
      &END XC_FUNCTIONAL
      &HF
         FRACTION 0.45
         &INTERACTION_POTENTIAL
            POTENTIAL_TYPE TRUNCATED
            CUTOFF_RADIUS 5.0
         &END INTERACTION_POTENTIAL
      &END HF
    &END XC

    &XAS_TDP
      &DONOR_STATES
         DEFINE_EXCITED BY_KIND
         KIND_LIST Nx
         STATE_TYPES 1s
         N_SEARCH 1
         LOCALIZE
      &END DONOR_STATES

      TAMM_DANCOFF
      GRID Nx 300 500
      E_RANGE 30.0

      &GW2X
      &END

      &KERNEL
         &XC_FUNCTIONAL
            &GGA_X_PBE
               SCALE 0.55
            &END
            &GGA_C_PBE
            &END
         &END XC_FUNCTIONAL
         &EXACT_EXCHANGE
            OPERATOR TRUNCATED
            CUTOFF_RADIUS 5.0
            FRACTION 0.45
         &END EXACT_EXCHANGE
      &END KERNEL

    &END XAS_TDP
  &END DFT
  &SUBSYS
    &CELL
      ABC   10.016118  10.016118  10.016118
    &END CELL
    &TOPOLOGY
      COORD_FILE_FORMAT XYZ
      COORD_FILE_NAME NH3.xyz
    &END TOPOLOGY
    &KIND H
      BASIS_SET DZVP-MOLOPT-SR-GTH
      BASIS_SET AUX_FIT FIT3
      POTENTIAL GTH-PBE
    &END KIND
    &KIND N
      BASIS_SET DZVP-MOLOPT-SR-GTH
      BASIS_SET AUX_FIT FIT3
      POTENTIAL GTH-PBE
    &END KIND
    &KIND Nx
      ELEMENT N
      BASIS_SET aug-pcseg-2
      BASIS_SET AUX_FIT aug-admm-2
      POTENTIAL ALL
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

**官方说明**：

- 与标准 XAS-LRTDDFT 输入**唯一区别是 `&GW2X` 子段**。
- 对应 Bussy2021b 图 3a。此处 GW2X 修正为**蓝移 3.7 eV**，谱与实验吻合极好。
- 该例**很重（24 核约 45 分钟）**。

### 4.6 GW2X 官方 FAQ（逐条）

**Q1：怎么让 GW2X 更快？**

- GW2X 修正**随体系 MO 数立方标度**，故**减少 MO 数是关键**。
- 因为只有被激发原子需要准确的芯区描述，**其它原子全用赝势**——只保留价态，大幅减少 MO 数。
- 固体 NH₃ 例中所有 N 对称等价，对 XAS 谱贡献相同，
  故**只把一个 N 用全电子处理**，其余 N 和 H 都用赝势。
- 同时用 **ADMM**，大幅降低底层杂化 DFT 计算以及 GW2X 所需广义 Fock 矩阵的求值成本。

**Q2：为什么周期性体系拿不到绝对芯 IP？**

- 非周期边界条件下，势在远处为零。
- **周期性情况下零点定义不清**，所有 KS 本征值被一个未知常数整体平移。
- 因此它们的绝对值和算出的 IP **不能物理解释**。
- **但修正方案依赖的是差 \(|\varepsilon_a-\varepsilon_I|\)，该平移会抵消。**

**Q3：为什么需要 `LOCALIZE`？**

- 为高效求 \(\langle Ia || jk \rangle\) 型反对称积分，用与 XAS_TDP 相同的**局域 RI 方案**，
  因此芯态 \(I\) 需在空间上局域。
- 但原始 GW2X 方案所需的赝正则轨道旋转**可能破坏这种局域性**（若体系中有其它等价原子）。
- 为防止这一点，**旋转和后续 IP 计算会忽略其它原子上的所有芯态**。
- 由于不同原子的芯态相互作用很弱，影响可忽略。
- **但重要的是把 `LOCALIZE` 的值保持到最小**，确保只忽略芯态。

---

## 5. 四页对比与选型表

| 维度 | ΔSCF | XAS_TDP | δ-kick | GW2X（配 XAS_TDP） |
|---|---|---|---|---|
| 方法类型 | ΔSCF / TP-HH | LR-TDDFT | RT-TDDFT | 电子传播子修正 |
| 关键段 | `&XAS` | `&XAS_TDP` | `&REAL_TIME_PROPAGATION` | `&XAS_TDP/&GW2X` |
| 基态要求 | GAPW + 全电子 | GAPW + 全电子（激发原子） | GAPW + 全电子 | 同 XAS_TDP + **杂化泛函** |
| K 边 / L 边 | K（`STATE_TYPE 1s`） | 都支持（`STATE_TYPES 1s`/`2p`） | 都支持 | 都支持 |
| SOC | 未涉及 | `SOC` + 双 `EXCITATIONS` | 未涉及 | `SOC` + 双 `EXCITATIONS` |
| 周期性 | 支持 | 支持（**截断库仑，半径 < 半胞长**） | 支持（**速度规范**） | 支持（同上） |
| 绝对能量 | **DSCF 给出首跃迁能量** | **偏移，需刚性平移** | 偏移 | **GW2X 修正后对标实验（0.1 eV）** |
| 计算量 | 中 | 中（大体系用 OT + ADMM） | 大（需长传播） | **立方标度，较重** |
| 官方推荐泛函 | PBE（示例） | **PBEh(α=0.45) / BHandHLYP** | PBEh(α=0.45)（示例） | **同 XAS_TDP** |
| 谱文件 | `*-xas_at*_st*.spectrum` | `*.spectrum` | 需自己 FT 偶极矩 | `*.spectrum`（已修正） |

> **[G层提示]** 一个反复出现的官方告诫：**XAS LR-TDDFT 谱的能量轴是偏移的，
> 必须刚性平移才能对标实验**。这不是 bug，是自相互作用误差 + 缺轨道弛豫导致的系统性偏移。
> **要免去手动平移，就用 GW2X。**

---

## 6. 与 G 层其它文件的关系

| 相关文件 | 关系 |
|---|---|
| `15_optical_and_xray.md` | 光学谱（TDDFT/GW-BSE/RT-TDDFT）与 X 射线谱**页面清单**；本文件是其 X 射线分支的正文 |
| `13_input_syntax_and_print.md` | `&PRINT` 与 printkey 机制（本文件多处用到 `&PRINT` 子段） |
| `14_basis_and_potentials.md` | 全电子基组与 `POTENTIAL ALL` 的选法 |
| `18_posthf_semiempirical_and_xray.md` | `&BSSE`、RTBSE；本文件与其中 RTBSE 页同属"谱学"族 |
| `20_input_reference_tree.md` | `&XAS_TDP`、`&GW2X`、`&REAL_TIME_PROPAGATION` 在段树中的位置 |
| `_sources.md` | 采集总表与缺口清单 |

---

## 7. 缺口与已知问题登记（如实）

| 项 | 状态 |
|---|---|
| `delta-scf` 页的 `lib_tools.zip` / `get_average_spectrum.sh` | 官方页面通过 DokuWiki 宏 `{{exercises:...}}` 引用，**未采集脚本本体** |
| 四页的图片/图注 | 未采集（WebFetch 无法取图） |
| `delta-kick` 页**步数矛盾** | 正文写 **500000** 步，示例输入写 **STEPS 50000**。已登记到 `_sources.md` §4.6 |
| `delta-kick` 页外部脚本 "here" 链接 | 未采集 |
| Bussy2021 / Bussy2021b 论文正文 | 仅官方引用，**未采集论文**（L1 级，非 L0） |
| `XAS_TDP` 与 `&XAS` 全部关键字的默认值 | 未逐条抄录，见 `20_input_reference_tree.md` 索引后按 URL 查 |
