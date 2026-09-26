# 17 · 约束动力学、路径优化与表面跳跃（官方）

> 来源：
> - https://manual.cp2k.org/trunk/methods/sampling/constrained_dynamics.html
> - https://manual.cp2k.org/trunk/methods/optimization/nudged_elastic_band.html
> - https://manual.cp2k.org/trunk/methods/sampling/newton-x.html
> - https://manual.cp2k.org/trunk/methods/sampling/index.html
> - https://manual.cp2k.org/trunk/methods/optimization/index.html
> 抓取日期：2026-09-08
> 标注规则：`[默认]` = 官方默认值；`[官方推荐]` = 官方明确建议；`[示例]` = 官方示例原样；`[G层提示]` = 本层基于官方原文给出的使用提示（非官方原文）

---

## 0. 本文件补什么

`05_optimization.md` 已覆盖几何/晶胞优化（`geometry_and_cell_opt.html`）。本文件补三块此前 G 层完全缺失的内容：

| 主题 | 官方页面 | 状态 |
|---|---|---|
| 约束分子动力学 + 蓝月系综 | `sampling/constrained_dynamics.html` | **正文完整**（含公式与引用） |
| NEB（Nudged Elastic Band） | `optimization/nudged_elastic_band.html` | **占位页**，只给 4 个练习链接 |
| 表面跳跃（NEWTON-X 接口） | `sampling/newton-x.html` | **正文完整**（含完整输入文件） |

> 关键更正：**NEB 至今没有官方正文页**。上一轮 `05_optimization.md` §13 已登记为占位页，本文件补充其指出的 4 个官方练习链接（见 §3）。

---

## 1. 约束分子动力学：机制与输入（官方）

### 1.1 基本机制

官方原文：

> CP2K can constrain a collective variable (CV) during molecular dynamics with `MOTION/CONSTRAINT/COLLECTIVE`. The CV is defined in `FORCE_EVAL/SUBSYS/COLVAR`, and `COLVAR` in the constraint section selects it **by input order**. Use `INTERMOLECULAR` for a CV whose atoms are not all in the same molecular object.

三条要点（官方原文提炼）：

| 要点 | 说明 |
|---|---|
| CV 定义位置 | `FORCE_EVAL/SUBSYS/COLVAR` |
| 选择方式 | `MOTION/CONSTRAINT/COLLECTIVE` 里的 `COLVAR` 关键字**按输入顺序**索引（第 1 个 COLVAR 就是 1） |
| 跨分子 | 若 CV 的原子不属于同一个 molecular object，必须加 `INTERMOLECULAR TRUE` |

### 1.2 固定距离窗口（官方示例原文）

```fortran
&FORCE_EVAL
  ...
  &SUBSYS
    ...
    &COLVAR
      &DISTANCE
        ATOMS 1 2
      &END DISTANCE
    &END COLVAR
  &END SUBSYS
&END FORCE_EVAL

&MOTION
  &CONSTRAINT
    &COLLECTIVE
      COLVAR 1
      INTERMOLECULAR TRUE
      TARGET [angstrom] 2.0
    &END COLLECTIVE
    &LAGRANGE_MULTIPLIERS ON
      FILENAME constraint_force
      COMMON_ITERATION_LEVELS 1
    &END LAGRANGE_MULTIPLIERS
  &END CONSTRAINT
  &MD
    ...
  &END MD
&END MOTION
```

> `[G层提示]` 这是"固定窗口"（fixed window）模式：`TARGET` 是一个常数，用于**平衡态约束热力学积分（TI）**的单个窗口。

---

## 2. 拉格朗日乘子输出（官方，关键）

`LAGRANGE_MULTIPLIERS` 在每个 velocity-Verlet 步写**两条**记录：

| 记录名 | 含义 | 用途 |
|---|---|---|
| `Shake Lagrangian Multipliers` | 位置约束乘子 | **与构型约束力、约束热力学积分（TI）相关的值** |
| `Rattle Lagrangian Multipliers` | 速度约束乘子 | 强制约束的时间导数；**不是第二份构型力采样** |

### 2.1 单位陷阱（官方原文，重要）

官方原文：

> The values are raw CP2K internal quantities; specifying `TARGET` in another unit does **not** convert the printed multipliers. A distance constraint therefore produces a multiplier in **hartree/bohr**, while an angular constraint uses the corresponding internal angular unit.

`[G层提示]` 这是极容易踩的坑：你在 `TARGET` 里写了 `[angstrom] 2.0`，但输出的乘子仍然是 **hartree/bohr**。角度约束同理，用内部角度单位。后处理时必须自己换算。

### 2.2 文件内的排序（官方）

文件包含**所有**激活约束的乘子，顺序为：

1. 先分子内约束（intramolecular），再分子间约束（intermolecular）
2. 每组内部顺序：collective-variable 约束 → 3-by-3 约束 → 4-by-6 约束

---

## 3. NEB（官方占位页 + 练习线索）

官方 `optimization/nudged_elastic_band.html` 原文：

> Unfortunately, nobody has gotten around to writing this page yet :-(
>
> In the meantime, the following links might be helpful:
> - https://www.cp2k.org/exercises:common:neb
> - https://www.cp2k.org/exercises:2018_uzh_cmest:path_optimization_neb
> - https://www.cp2k.org/exercises:2017_ethz_mmm:nudged_elastic_band
> - https://www.cp2k.org/exercises:2015_cecam_tutorial:neb

`[G层提示]` NEB 的官方知识只在**练习页**里，不在手册正文。这四条链接是唯一官方入口。注意 `exercises:2015_cecam_tutorial:neb` 同时出现在 B 层课程综合里（庚子计算 NEB 流程），两者可互相印证。

> **★ 已补齐（2026-09-09）**：这 4 条链接（以及另外 3 条同主题练习，共 **7 页**）的**完整正文**
> 已采集落盘到 **`24_official_exercises.md` §1**，含：
> `common:neb`（最小可跑 NEB 完整输入 + 输出解读）、
> `2015_cecam_tutorial:neb`（**`MULTIPLE_FORCE_EVALS` QM/MM 混合力场做 NEB**，2900+ 原子体系）、
> `2014_ethz_mmm:nudged_elastic_band`（IT-NEB + `&CONSTRAINT` + 中间点引导三条硬规则）、
> `2016_uzh_cmest:path_optimization_neb`（乙烷构象，官方给 4 个 xyz）等。
> **本文件 §3 的空白登记已由 24 号文件填补。**

---

## 4. 蓝月系综校正（官方，本文件核心）

### 4.1 为什么需要校正

官方原文：

> Constrained molecular dynamics generally produces **biased** statistical distributions. The blue-moon ensemble average is used to correct these biased outputs and retrieve the statistical properties corresponding to **unconstrained** molecular-dynamics conditions. The printed SHAKE multiplier is **not, in general, a complete blue-moon estimator**.

`[G层提示]` 换句话说：直接对 `Shake Lagrangian Multipliers` 求平均，得到的不是真正的自由能梯度，除非满足特定条件（见 §4.4）。

### 4.2 自由能梯度公式（官方原文）

对单一约束反应坐标 ξ：

```
dA/dξ = ⟨ Z^(-1/2) ( -λ + k_B T G ) ⟩_ξ / ⟨ Z^(-1/2) ⟩_ξ
```

其中：
- `k_B` 玻尔兹曼常数，`T` 温度
- `⟨⋯⟩_ξ` 表示在反应坐标 ξ(r₁,…,r_N) 下的 MD 时间平均
- `Z` 是**标量质量度规**（scalar mass metric）

### 4.3 质量度规 Z 的定义（官方原文）

```
Z = Σ_i (1/m_i) |∇_i ξ|²
```

官方约定：约束力为 `−λ∇ξ`，因此自由能梯度包含 `Z^(-1/2)` 重加权，对一般坐标还多一项**度规导数项（G）**。

### 4.4 CP2K 当前只写 λ，不做完整校正（官方原文，关键）

官方原文：

> CP2K currently writes λ but does **not** evaluate or print the complete corrected blue-moon estimator. The required metric terms therefore have to be evaluated **during postprocessing** for the chosen reaction coordinate.

官方给出的参考文献：

> Komeiji, *Chem-Bio Informatics Journal* **7**, 12 (2007), DOI `10.1273/cbij.7.12` —— 给出通用表达式与两种常见坐标的显式算法。

`[G层提示]` 这与既有 A 层结论一致：**CP2K 只输出 λ，完整蓝月校正必须自己做后处理**。现在有了官方出处（本页 + Komeiji2007），可以把这个结论从"经验"升级为"官方事实"。

### 4.5 两种坐标的具体化简（官方，可直接用）

#### （1）两原子距离 ξ = |r_i − r_j|

```
Z = m_i^(-1) + m_j^(-1)   （常数）
```

- Z 是常数 → 度规导数项为 0
- 重加权因子 `Z^(-1/2)` 在分子分母中**约掉**
- 于是自由能梯度化简为 **`−⟨λ⟩_ξ`**

> 官方原文："Here Z is constant and the metric-derivative term is zero. The reweighting cancels, so the free-energy gradient reduces to −⟨λ⟩_ξ with the sign convention above."

`[G层提示]` **这是唯一可以"直接平均 λ"的情形**。也是最常用的情形（键长、吸附距离）。

#### （2）三原子距离差 ξ = |r_i − r_j| − |r_k − r_j|

```
Z = m_i^(-1) + m_k^(-1) + 2 m_j^(-1) (1 − ρ_ij · ρ_kj)
```

- 度规导数项仍为 0
- 但 Z **依赖瞬时角度**（`ρ_ij`、`ρ_kj` 是单位向量）
- 自由能梯度为：

```
dA/dξ = ⟨ Z^(-1/2) (−λ) ⟩_ξ / ⟨ Z^(-1/2) ⟩_ξ
```

> 官方原文警告："This simplification applies to this specific three-atom coordinate. It **must not be assumed** for an arbitrary `COMBINE_COLVAR`, coordination number, or multiple simultaneous constraints."

`[G层提示]` 三原子距离差常用于质子转移（供体-H···受体）。此时**必须按瞬时构型算 Z 再加权**，不能简单平均 λ。

### 4.6 蓝月校正决策表（G 层提炼）

| 你的反应坐标 | 能否直接平均 λ？ | 需要做什么 |
|---|---|---|
| 两原子距离 | ✅ 可以 | 直接 `−⟨λ⟩` |
| 三原子距离差 | ❌ 不可以 | 每帧算 Z，按 `Z^(-1/2)` 加权 |
| `COMBINE_COLVAR` | ❌ 不可假定 | 需查 Komeiji2007 通用式 |
| 配位数（coordination number） | ❌ 不可假定 | 同上 |
| 多个同时约束 | ❌ 不可假定 | 同上，且耦合项复杂 |

---

## 5. 固定窗口 vs 移动约束（官方）

### 5.1 平衡态约束热力学积分（fixed windows）

官方原文流程：

> For equilibrium constrained thermodynamic integration, run **independently equilibrated trajectories at a series of fixed `TARGET` values**, calculate the corrected free-energy gradient in every window, and integrate it over the reaction coordinate.

官方要求检查的五项：

1. 采样长度（sampling length）
2. 关联时间（correlation time）
3. 窗口间距（window spacing）
4. 积分方向（integration direction）
5. 单位换算（unit conversion）

`[G层提示]` 窗口间距过大会导致积分误差；方向不同可能暴露滞后（hysteresis）。建议正反两向各跑一遍看是否闭合。

### 5.2 移动约束 / 慢生长（moving constraints）

官方原文：

> `TARGET_GROWTH` instead changes `TARGET` **linearly by `TARGET_GROWTH × TIMESTEP` at every MD step**, optionally stopping at `TARGET_LIMIT`.

即：

```
TARGET(t) = TARGET(0) + TARGET_GROWTH × TIMESTEP × step
```

当 TARGET 达到 `TARGET_LIMIT` 时停止变化。

#### 官方示例原文

```fortran
&FORCE_EVAL
  ...
  &SUBSYS
    ...
    &COLVAR
      &DISTANCE
        ATOMS 1 2
      &END DISTANCE
    &END COLVAR
  &END SUBSYS
&END FORCE_EVAL

&MOTION
  &CONSTRAINT
    &COLLECTIVE
      COLVAR 1
      INTERMOLECULAR TRUE
      TARGET [angstrom] 2.0
      TARGET_GROWTH [angstrom*fs^-1] 0.0008
      TARGET_LIMIT [angstrom] 3.0
    &END COLLECTIVE
    &LAGRANGE_MULTIPLIERS ON
      FILENAME constraint_force
      COMMON_ITERATION_LEVELS 1
    &END LAGRANGE_MULTIPLIERS
  &END CONSTRAINT
  &MD
    ...
  &END MD
&END MOTION
```

注意 `TARGET_GROWTH` 的单位写法：**`[angstrom*fs^-1]`**（每飞秒多少埃），与 `TIMESTEP` 相乘。

### 5.3 官方对慢生长的警告（重要）

官方原文：

> CP2K does **not** integrate the work or turn the resulting trajectory into an equilibrium free-energy profile automatically. A finite pulling rate can cause **lag, dissipation, and direction-dependent hysteresis**, so such a trajectory must be analysed with a method appropriate to the intended nonequilibrium protocol.

### 5.4 Jarzynski 恒等式（官方原文）

在 ξ 变化无穷小的极限下，不可逆功 W 描述初末态之间的能量变化。慢生长得到的功能与自由能变化 ΔA 通过 Jarzynski 恒等式联系：

```
exp( −ΔA / (k_B T) ) = ⟨ exp( −W / (k_B T) ) ⟩
```

`[G层提示]` 官方只给出恒等式本身，**没有**给出 CP2K 侧计算 W 的工具。W 需要由 λ 与约束轨迹自行积分（`W = ∫ λ dξ` 类形式），属于后处理范畴。

---

## 6. 表面跳跃与 NEWTON-X 接口（官方）

### 6.1 定位

官方原文：

> This is a short tutorial on how to use the CP2K-NEWTONX interface to a) generate initial conditions to compute photoabsorption spectra and b) to run non-adiabatic dynamics simulations using orbital derivative couplings.

更完整的 NEWTON-X 教程（含 CP2K 接口规格说明）在 NEWTON-X 官网：
`https://newtonx.org/documentation-tutorials/`

### 6.2 理论要点（官方）

CP2K 提供激发能 Ω_M 与激发态本征矢 X_M，基于 Tamm-Dancoff 本征方程：

```
A X_M = Ω_M S X_M
```

其中 S 为原子轨道重叠矩阵，F 为 Kohn-Sham 矩阵，K 为核（含 Coulomb/交换/XC 贡献），C 为分子轨道系数。

激发态梯度：构造变分拉格朗日量，对核坐标 R 求导（与 TDDFT 页一致）。

### 6.3 传播与跳跃（官方公式）

核按经典方式在势能面上传播：

```
R(t+Δt) = R(t) + v(t)Δt + ½ a(t)Δt²
v(t+Δt) = v(t) + ½ [a(t) + a(t+Δt)]Δt
a(t) = −(1/m) ∇Ω_M(R(t))
```

总波函数系数 c_M(t) 通过 Tully 表面跳跃获得，跳跃概率：

```
P_{M→N} = max[ 0, −2Δt / |c_M|² · Re( c_M c_N* ) σ_MN ]
```

### 6.4 非绝热耦合 σ_MN 的两种来源（官方，含引用要求）

| 方式 | 说明 | 官方要求引用 |
|---|---|---|
| 半经验模型 **Baeck-An** | — | Barbatti et al., *Open Research Europe* **1**, 49 (2021), DOI `10.12688/openreseurope.13624.1` |
| 数值时间导数耦合 **OD**（orbital time derivative） | 由 CP2K 提供 MO 重叠矩阵 S(t−Δt,t) | Ryabinkin et al., *J. Phys. Chem. Lett.* **6**, 4200 (2015), DOI `10.1021/acs.jpclett.5b02062`；Barbatti et al., *Molecules* **21**, 1603 (2016), DOI `10.3390/molecules21111603` |

`[G层提示]` 用到 NEWTON-X 接口时，**必须**按上表引用相应方法论文。这是官方明确的引用要求。

### 6.5 必需的打印设置（官方）

要让 NEWTON-X 读到 CP2K 输出，必须加三个 print：

| 打印段 | 作用 |
|---|---|
| `FORCE_EVAL/PRINT/FORCES` | 打印激发态受力 |
| `TDDFPT/PRINT/NAMD_PRINT` + `PRINT_PHASES` | 打印激发态本征矢（MO 格式）及相位 |
| `VIBRATIONAL_ANALYSIS/PRINT/NAMD_PRINT` | 打印简正模（用于生成初始条件） |

官方附加要求：

> cartesian coordinates have to be provided in terms of the external file `coord.cp2k` and that the number of atoms has to be specified in the CP2K input file in the `SUBSYS` section.

即坐标**必须**用外部文件 `coord.cp2k`（配合 `@include`），且在 `&TOPOLOGY` 里写明 `NATOMS`。

### 6.6 场景 A：初始条件与光吸收谱（官方完整输入）

#### （1）激发态计算输入（官方原文）

```fortran
&GLOBAL
  PROJECT excited_states_for_h2o 
  RUN_TYPE ENERGY
  PREFERRED_DIAG_LIBRARY SL
  PRINT_LEVEL medium
&END GLOBAL
&FORCE_EVAL
  &PRINT                      # print statement for ground-state or excited-state forces
    &FORCES
    &END FORCES
  &END PRINT
  METHOD Quickstep
  &PROPERTIES
    &TDDFPT                    # TDDFPT input section to compute 10 excited states
      &DIPOLE_MOMENTS
        DIPOLE_FORM LENGTH
      &END DIPOLE_MOMENTS
      KERNEL FULL
      NSTATES 10
      MAX_ITER   100
      MAX_KV 20
      CONVERGENCE [eV] 1.0e-5
      RKS_TRIPLETS F
      &PRINT                     # NAMD print section to print excited-state eigenvectors
        &NAMD_PRINT
          PRINT_VIRTUALS T
          PRINT_PHASES T
        &END NAMD_PRINT
      &END PRINT
    &END TDDFPT
  &END PROPERTIES
  &DFT
    &QS
      METHOD GAPW
      EPS_DEFAULT 1.0E-17
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
    POTENTIAL_FILE_NAME POTENTIAL
    BASIS_SET_FILE_NAME EMSL_BASIS_SETS
    &MGRID
      CUTOFF 1000
      REL_CUTOFF 100
      NGRIDS 5
    &END MGRID
    &POISSON
      PERIODIC NONE
      PSOLVER MT
    &END
    &XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 8.0 8.0 8.0
      PERIODIC NONE
    &END CELL
                                    # Coordinates are provided externally for the interface
    &COORD
      @include coord.cp2k
    &END COORD
    &TOPOLOGY
      &CENTER_COORDINATES T
      &END
      NATOMS 3                       # specifying number of atoms for NEWTONX
      CONNECTIVITY OFF
    &END TOPOLOGY
    &KIND H
      BASIS_SET 6-311Gxx
      POTENTIAL ALL
    &END KIND
    &KIND O
      BASIS_SET 6-311Gxx
      POTENTIAL ALL
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

> 注意：官方此示例用 `POTENTIAL ALL`（全电子，配合 GAPW），并用 `EMSL_BASIS_SETS` + `6-311Gxx`。目的是与全电子分子程序（如 Turbomole）对比。

#### （2）简正模计算输入（官方原文）

```fortran
&GLOBAL
  PROJECT normal_modes_for_h2o
  RUN_TYPE VIBRATIONAL_ANALYSIS      #computing normal modes to generate initial conditions
  PREFERRED_DIAG_LIBRARY SL
  PRINT_LEVEL medium
&END GLOBAL
&FORCE_EVAL
  &PRINT
    &FORCES
    &END FORCES
  &END PRINT
  METHOD Quickstep
  &DFT
    &QS
      METHOD GAPW                   # GAPW enables comparison with all-electron molecular program codes like Turbomole
      EPS_DEFAULT 1.0E-17
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
    POTENTIAL_FILE_NAME POTENTIAL
    BASIS_SET_FILE_NAME EMSL_BASIS_SETS
    &MGRID
      CUTOFF 1000
      REL_CUTOFF 100
      NGRIDS 5
    &END MGRID
    &POISSON
      PERIODIC NONE
      PSOLVER MT
    &END
    &XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 8.0 8.0 8.0
      PERIODIC NONE
    &END CELL
                                    # coordinates must be provided as external file for NEWTONX
    &COORD
      @include coord.cp2k
    &END COORD
    &TOPOLOGY
      &CENTER_COORDINATES T
      &END
      NATOMS 3
      CONNECTIVITY OFF
    &END TOPOLOGY
    &KIND H
      BASIS_SET 6-311Gxx
      POTENTIAL ALL
    &END KIND
    &KIND O
      BASIS_SET 6-311Gxx
      POTENTIAL ALL
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
&VIBRATIONAL_ANALYSIS
  &PRINT
    &NAMD_PRINT                      # keyword to enable printing of cartesian normal modes
    &END NAMD_PRINT
  &END PRINT
  DX 0.001
&END VIBRATIONAL_ANALYSIS
```

#### （3）NEWTON-X 侧文件（官方）

`cp2k.par`（指定可执行文件与并行设置）：

```
 parallel = 16
 exec = cp2k.psmp
```

`initqp_input` 关键设置：

- `file_nmodes = normal_modes_for_h2o-VIBRATIONS-1.eig`（上一步频率计算产出的简正模文件）
- `iprog = 10`（**指定电子结构程序为 CP2K**）

官方完整示例：

```fortran
&dat
 nact = 2
 iprog = 10
 numat = 3
 npoints = 500
 file_geom = geom
 file_nmodes = normal_modes_for_h2o-VIBRATIONS-1.eig
 anh_f = 1
 rescale = n
 temp = 0
 ics_flg = n
 chk_e = 1
 nis = 1
 nfs = 11
 kvert = 1
 de = 100
 prog = 14
 iseed = 0
 lvprt = 1
/
```

目录要求：激发态计算放在子目录 `JOB_AD` 中，需 `cp2k.inp`、`cp2k.par`、`coord.cp2k`。

然后执行 NEWTON-X 的 `initcond.pl` 生成初始条件，输出 `final_output_XXX`（每个态一个），含几何与速度。

官方输出示例（初始条件）：

```
 Initial condition =     1
 Geometry in COLUMBUS and NX input format:
 o     8.0    5.00630777    5.00000001    4.46399957   15.99491464
 h     1.0    6.37684065    5.00000128    5.50815661    1.00782504
 h     1.0    3.52303474    5.00000149    5.58297278    1.00782504
 Velocity in NX input format:
   -0.000089112    0.000000000   -0.000020915
    0.000417197    0.000000002    0.000694479
    0.000997296    0.000000013   -0.000362483
 Epot of initial state (eV):    0.0865  Epot of final state (eV):     19.0799
 Vertical excitation (eV):     18.9935  Is Ev in the required range? YES
 Ekin of initial state (eV):    0.0479  Etot of initial state (eV):    0.1343
 Oscillator strength:           0.1221
 State:                         10
```

最后用 `nxinp` 脚本算出展宽的吸收谱，输出 `cross-section.dat`。

### 6.7 场景 B：非绝热动力学

官方页在 "B) Non-adiabatic dynamics using orbital determinant derivatives" 处**内容截断**（页面本身如此，抓取到的正文到此结束）。

`[G层提示]` 场景 B 的完整步骤需到 NEWTON-X 官网教程查阅，官方 CP2K 手册未给出。已登记为缺口。

---

## 7. 采样与优化章节的完整页面清单（官方）

### 7.1 Sampling 章节

| 页面 | 状态 |
|---|---|
| Molecular Dynamics | 已有（见 `04_sampling_md.md`） |
| **Constrained molecular dynamics** | **本文件 §1–§5** |
| **Surface Hopping with NEWTON-X** | **本文件 §6** |
| Real-Time Propagation and Ehrenfest MD | 已有（见 `15_optical_and_xray.md`） |

### 7.2 Optimization 章节

| 页面 | 状态 |
|---|---|
| Geometry and cell optimization | 已有（见 `05_optimization.md`） |
| **Nudged Elastic Band** | **占位页**（本文件 §3） |

---

## 8. 交叉索引

| 本文件主题 | 关联文件 | 关系 |
|---|---|---|
| 约束 MD / 蓝月系综 | A 层 `decide.md` | A 层有"CP2K 只写 λ"的经验结论；本文件补官方出处与公式 |
| NEB 练习链接 | B 层 `course_learned.md` | 庚子计算 NEB 流程；`exercises:2015_cecam_tutorial:neb` 为同一官方来源 |
| 约束 MD 输入语法 | `13_input_syntax_and_print.md` | `&COLVAR` / `&COLLECTIVE` 段写法、单位方括号 |
| 拉格朗日乘子输出控制 | `13_input_syntax_and_print.md` | `COMMON_ITERATION_LEVELS` / `FILENAME` 机制 |
| TDDFPT 输入细节 | `15_optical_and_xray.md` | NEWTON-X 的 TDDFPT 段与 NAMD_PRINT 依赖该文件的 TDDFT 内容 |
| 简正模 / 振动分析 | `06_properties.md` | 初始条件生成依赖 `RUN_TYPE VIBRATIONAL_ANALYSIS` |
| 优化器与收敛 | `05_optimization.md` | NEB 与优化器设置共享 `OPTIMIZER`/`OPT_TYPE` |
| 几何优化卡住 | `08_errors_and_faq.md`、`19_posthf_and_troubleshooting.md` | 官方 troubleshooting 提到优化/NEB 可能卡住，建议调 `OPTIMIZER`/`OPT_TYPE` |

---

## 9. 本文件登记的新缺口（诚实标注）

| 缺口 | 说明 |
|---|---|
| NEWTON-X 场景 B 正文 | 官方页在 "B)" 处截断，需查 NEWTON-X 官网 |
| NEB 手册正文 | 官方明确为占位页，只有 4 条练习链接 |
| Jarzynski 侧 W 的计算工具 | 官方只给恒等式，未提供 CP2K 侧计算 W 的手段 |
| 蓝月通用式实现 | 需按 Komeiji2007 自行实现；CP2K 不含 |
