# 24 · 官方练习集（`www.cp2k.org/exercises`，官方正文）

> 来源：
> - <https://www.cp2k.org/exercises>（总索引，2014–2025）
> - <https://www.cp2k.org/exercises:common:index>（**官方现行维护的练习集**，2025/06/19 最后修改）
> - 21 个课程命名空间下的 **248 个子页**
> 抓取日期：2026-09-09
> 标注规则：`[官方原文]` = 官网正文；`[G层提示]` = G 层整理性说明（非官方原话）。

---

## 0. 本文件补什么（重要）

**这是 G 层最后一块、也是此前明确登记为"未采"的最大缺口。**

- `17_constrained_dynamics_and_paths.md` §3 曾如实登记：
  > NEB 的官方知识**只在练习页里，不在手册正文**。官方 `optimization/nudged_elastic_band.html` 是**占位页**（"Unfortunately, nobody has gotten around to writing this page yet :-("），只给 4 条练习链接。

  本文件把这 4 条链接（以及另外 3 条同主题练习）的**完整正文**采入。

- `_sources.md` §5.1 曾登记 `www.cp2k.org/exercises` 为**中优先级未采**。本轮完成。

**规模实测**：248 个子页中 **239 页有正文**，**9 页是官方空链接**（"This topic does not exist yet"），
累计正文 **约 170 万字符**。本文件不逐页抄录全文，而是：
1. **提炼全部有技术价值的"做法/参数/坑"**（§1–§5）；
2. **给出 239 页的完整清单**（§6，含标题与规模），供按需回溯。

---

## 1. NEB / 过渡态（最高价值：官方唯一入口）

### 1.1 为什么这块最关键

官方手册的 NEB 页是**占位页**，`&MOTION/&BAND` 只有 Input Reference 关键字表，
**没有任何教程**。练习页是**唯一**能学到"怎么跑 NEB"的官方来源。

### 1.2 `exercises:common:neb` — 最小可跑 NEB（推荐入门）

**官方给的完整两步流程**：

**第 1 步：先做两端几何优化**（`GEO_OPT`，PM6 半经验）

```text
&GLOBAL
  PRINT_LEVEL LOW
  PROJECT ch3cl
  RUN_TYPE GEO_OPT
&END GLOBAL
&MOTION
  &GEO_OPT
    MAX_FORCE 1.0E-4
    MAX_ITER 2000
    OPTIMIZER BFGS
    &BFGS
      TRUST_RADIUS [bohr] 0.1
    &END
  &END GEO_OPT
&END MOTION
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    CHARGE -1                  # 负离子
    &QS
      METHOD PM6
      &SE
      &END SE
    &END QS
    &SCF
      SCF_GUESS ATOMIC
      EPS_SCF 1.0E-5
      MAX_SCF 50
      &OUTER_SCF
        EPS_SCF 1.0E-7
        MAX_SCF 500
      &END
    &END SCF
    &POISSON
      PERIODIC NONE
      PSOLVER WAVELET
    &END
  &END DFT
  &SUBSYS
    &CELL
      ABC 10.0 10.0 10.0
      PERIODIC NONE
    &END CELL
    &COORD
      ...（S_N2 反应 Cl⁻ + CH₃Cl，6 原子）
    &END COORD
  &END SUBSYS
&END FORCE_EVAL
```

**第 2 步：NEB 本体**

```text
&GLOBAL
  PRINT_LEVEL LOW
  PROJECT ch3cl
  RUN_TYPE BAND
&END GLOBAL
&MOTION
  &BAND
    NUMBER_OF_REPLICA 10
    K_SPRING 0.05
    &OPTIMIZE_BAND
      OPT_TYPE DIIS
      &DIIS
        MAX_STEPS 1000
      &END
    &END
    BAND_TYPE CI-NEB
    &CI_NEB
      NSTEPS_IT  5          # 先走 5 步普通 NEB，再开 CI
    &END
    &REPLICA
      COORD_FILE_NAME init.xyz
    &END
    &REPLICA
      COORD_FILE_NAME final.xyz
    &END
    &PROGRAM_RUN_INFO
      INITIAL_CONFIGURATION_INFO
    &END
  &END BAND
&END MOTION
```

**官方给出的输出解读**（主输出里每步一段）：

```text
 BAND TYPE                     =                                          CI-NEB
 BAND TYPE OPTIMIZATION        =                                              SD
 STEP NUMBER                   =                                               1
 NUMBER OF NEB REPLICA         =                                              10
 DISTANCES REP =        0.252266        0.229810 ...
 ENERGIES [au] =      -24.815004      -24.813368 ...
 BAND TOTAL ENERGY [au]        =                             -248.08548199708440
```

> **[官方原文]** 这些段**对每个 replica 给出到相邻点的距离与其能量**；
> **最后一段对应收敛的 NEB 轨迹**。

**官方给的理论要点（S_N2 为例）**：

- 鞍点数学条件：① 梯度为零；② Hessian 有**负本征值**；③ **只有一个虚频**。
- `MEP`（最小能量路径）是 3N 维势能面上的一维路径，路径上每点在**垂直于路径方向上是极小**；
  MEP 至少经过一个鞍点，**最高鞍点的能量就是活化能峰**。
- 官方提醒：练习用 PM6 只是**便宜**，**准确表征反应要用 DFT 或更高**。

### 1.3 `exercises:2015_cecam_tutorial:neb` — **QM/MM 混合力场做 NEB**（最高级技巧）

**体系**：分子（56 原子）吸附在 Cu(111) 表面（约 2900 原子）；
分子用 DFT（练习里用 PM6），衬底用 EAM，二者通过模拟 vdW 与 Pauli 排斥的势耦合。
**问题**：算 CHP@Cu(111) → TBC 环化脱氢反应**最后一步（6→7）的活化能**。

**关键技巧：`MULTIPLE_FORCE_EVALS` 四段式结构**（官方原文说明）：

> ① 第一段定义如何把整个体系**划分为 DFT + EMPIRICAL 两部分**；
> ② 第二段定义 **EMPIRICAL 部分的力场**；
> ③ 第三段定义 **DFT 部分的参数**；
> ④ **第四段定义计算目标（GEO_OPT / NEB / MD …）**。

**第一段（划分片段）**：

```text
&MULTIPLE_FORCE_EVALS
  FORCE_EVAL_ORDER 2 3
  MULTIPLE_SUBSYS T
&END
&FORCE_EVAL
  METHOD MIXED
  &MIXED
    MIXING_TYPE GENMIX
    GROUP_PARTITION 1 1
    &GENERIC
      ERROR_LIMIT 1.0E-10
      MIXING_FUNCTION E1+E2
      VARIABLES E1 E2
    &END
    &MAPPING
      &FORCE_EVAL_MIXED
        &FRAGMENT 1
          1 56
        &END
        &FRAGMENT 2
          57 2936
        &END
      &END
      &FORCE_EVAL 1
        DEFINE_FRAGMENTS 1 2
      &END
      &FORCE_EVAL 2
        DEFINE_FRAGMENTS 1
      &END
    &END
  &END
  &SUBSYS
    &COLVAR
      &DISTANCE
        ATOMS 49 50
      &END
    &END
    &CELL
      ABC  40.764229 39.715716 70.
    &END CELL
    &TOPOLOGY
      COORD_FILE_NAME ./s.xyz
      COORDINATE XYZ
      CONNECTIVITY OFF
    &END TOPOLOGY
  &END SUBSYS
&END
```

**第二段（经验力场）**：Cu–Cu 用 **EAM**（`Files/CU.pot`）；
C–Cu / H–Cu 用 `A*exp(-av*r)+B*exp(-ac*r)-C/(r^6)`（含 Pauli 排斥）；
C–C / C–H / H–H 设 **`EPSILON 0.0`**（因为由 DFT 提供）。

```text
&FORCE_EVAL
  METHOD FIST
  &MM
    &FORCEFIELD
      &SPLINE
        EPS_SPLINE 1.0E-6
        EMAX_SPLINE 0.9
      &END
      &CHARGE
        ATOM Cu
        CHARGE 0.0
      &END CHARGE
      &NONBONDED
        &GENPOT
          atoms Cu C
          FUNCTION A*exp(-av*r)+B*exp(-ac*r)-C/(r^6)
          VARIABLES r
          PARAMETERS A av B ac C
          VALUES 4.13643 1.33747 115.82004 2.206825 75.40708524085266692113
          RCUT  15
        &END GENPOT
        &LENNARD-JONES
          atoms C H
          EPSILON 0.0
          SIGMA 3.166
          RCUT  15
        &END LENNARD-JONES
        &EAM
          atoms Cu Cu
          PARM_FILE_NAME ../../Files/CU.pot
        &END EAM
      &END NONBONDED
    &END FORCEFIELD
    &POISSON
      &EWALD
        EWALD_TYPE none
      &END EWALD
    &END POISSON
  &END
  &SUBSYS
    &CELL
      ABC  40.764229 39.715716 70.
    &END CELL
    &TOPOLOGY
      COORD_FILE_NAME ./s.xyz
      COORDINATE XYZ
      CONNECTIVITY OFF
    &END TOPOLOGY
  &END SUBSYS
&END
```

> **[G层提示]** 官方特别提示：**第三段的 DFT 计算里，模拟盒子要比整体体系小**
> （"the simulation cell here is reduced with comparison to the simulation cell of the whole system"）——
> 因为 DFT 只算 56 原子的分子。

### 1.4 `exercises:2014_ethz_mmm:nudged_elastic_band` — IT-NEB + 约束 + 中间点引导

**体系**：平面内 7 个 Ar 原子团簇，算把**原子 2 移到中心**的活化能。
**官方说明**：NEB 至少需要起始与终止构型，**外加一个中间构型猜测是好的做法**——
尤其当存在两条以上反应路径时，**加入想要的中间构型可以引导优化走你关心的那条路径**；
中间构型不是定论，会被 NEB 算法优化掉。

```text
&GLOBAL
   RUN_TYPE BAND
   PROJECT_NAME neb1
&END GLOBAL
&MOTION
  &CONSTRAINT               ! 2D 体系，固定所有原子的 z 坐标
   &FIXED_ATOMS
    COMPONENTS_TO_FIX Z
    LIST 1..7
   &END
  &END
  &BAND
   NPROC_REP 1              ! 每个 replica 用几个处理器
   BAND_TYPE IT-NEB
   NUMBER_OF_REPLICA 10
    &OPTIMIZE_BAND
      OPT_TYPE DIIS
      &DIIS
       MAX_STEPS 1000
       N_DIIS 3
      &END
    &END
    &REPLICA                ! 起始构型（必须是第一个）
     &COORD
       ...
      &END
    &END REPLICA
    &REPLICA                ! 中间构型（可选，用于引导）
     &COORD
       ...
      &END
    &END REPLICA
    &REPLICA                ! 终止构型（必须是最后一个）
     &COORD
       ...
      &END
    &END REPLICA
  &END BAND
&END MOTION
```

> **[G层提示]** 三条硬规则：
> ① **起始 `&REPLICA` 必须是输入里第一个**；② **终止 `&REPLICA` 必须是最后一个**；
> ③ `&OPTIMIZE_BAND` **是必需的，且官方说"should not be changed"**（照抄即可）。

### 1.5 `exercises:2016_uzh_cmest:path_optimization_neb` — 乙烷构象转变（给好 4 个 xyz）

**官方直接提供 4 个几何文件**：`ethane_1_opt.xyz`（i=12）、`ethane_s1.xyz`（i=76）、
`ethane_ts.xyz`（i=76）、`ethane_s2.xyz`（i=76），并说明前两个是上一题优化结果。
**教学点**：上一题的几何优化**卡在局部极小**，无法变成另一个更低的结构 —— 这正是 NEB 的用武之地。

### 1.6 其余 NEB 练习页

| 页面 | 要点 |
|---|---|
| `2017_ethz_mmm:lennard_jones_cluster_neb` | LJ 团簇的 NEB |
| `2017_ethz_mmm:nudged_elastic_band` | 同 1.4 主题（更新版） |
| `2018_uzh_cmest:path_optimization_neb` | 同 1.5 主题（更新版） |

> **[G层提示]** 官方 NEB 相关练习共 **7 页**（1 个 common + 6 个课程页），
> 全部为**可运行完整输入**。这填补了 `17_...` §3 登记的最大空白。

---

## 2. AIMD 与分子动力学（与 skill 定位最相关）

### 2.1 `exercises:common:aimd` — AIMD 理论与练习

**官方对 AIMD 的界定**：

> 用电子结构理论（如 DFT）**在线（on-the-fly）**获得力的有限温度 MD 模拟，称为 AIMD。

**官方对 BOMD 的表述**：

> 在 Born-Oppenheimer MD 中，通过最小化或对角化方法从电子结构理论求解能量或力。
> **每一步 MD，电子结构只依赖给定的固定核位置**，即电子与核不耦合，
> 因此电子结构问题可用**定态薛定谔方程**求解；核按经典力学或量子力学传播。

公式（官方原文）：

```text
M_I R̈_I = −∇_I min_{ψ0} { ⟨ψ0|H_e|ψ0⟩ }
E_0 ψ0 = H_e ψ0
```

> 基态能量可由任何变分方法（如 DFT）得到。**AIMD 最常用 BO 流程**，
> 即每步优化电子结构并积分核运动方程；该流程可通过**外推电子密度**显著加速。

**练习内容**：用 **PBE-D3** 泛函做液态水的 AIMD。
官方给出一篇参考："How good is DFT for water?"（Perspective）。

### 2.2 `exercises:common:sgcp` — **第二代 Car-Parrinello（SGCP）**（含完整参数表）

> **[官方原文]** 本练习做 SGCP MD，**请引用 Phys. Rev. Lett. 98, 066401**。

**官方给的三方对比表（完整照录）**：

| 特征 | CPMD | BOMD | SGCP |
|---|---|---|---|
| 每步是否做 SCF | 否 | 是 | **部分（predictor-corrector）** |
| 时间步长 | 小（~0.1 fs） | 大（~1 fs） | **大（~1–2 fs）** |
| 守恒量保持 | 优秀 | 合理 | **优秀** |
| 是否在 BO 面上 | 略高于 | 是 | **非常接近** |
| 小带隙体系 | 差 | 好 | **好** |

**ASPC 方法（Always Stable Predictor Corrector）**：

```text
预测子：C_p(t_n) = Σ_{m=1..K} (−1)^(m+1) · m · B_m · P_S(t_{n−m})
        B_m = Kolafa 预测系数；P_S = 投影到重叠矩阵 S
修正子：C(t_n) = ω·min[C_p(t_n)] + (1−ω)·C_p(t_n),  ω = K/(2K−1)
```

**Langevin 动力学与耗散补偿**：

```text
M_I R̈_I = F_BO − (γ_D + γ_L) Ṙ_I + Ξ_I
γ_D = ASPC 隐式摩擦；γ_L = Langevin 恒温器；Ξ_I = Langevin 随机噪声
```

**CP2K 参数设置表（官方照录）**：

| 参数 | 作用 | 官方注释 |
|---|---|---|
| `EXTRAPOLATION_ORDER` | 越高预测子越好 | 典型 1–4；**金属体系用 0 更稳定** |
| `MAX_SCF_HIST` | 控制 SCF 修正 | **≥2 有助于更平滑收敛** |
| `STEPSIZE` | 时间步（fs） | 依体系约 **0.5–2 fs** |
| `PRECONDITIONER` | 影响 SCF 收敛 | **`FULL_SINGLE_INVERSE` 略好** |
| `NOISY_GAMMA` (γ_D) | ASPC 耗散补偿 | 调节以控制 T 与能量的漂移 |
| `GAMMA` (γ_L) | Langevin 恒温器强度 | **设为 0 则只做耗散积分** |

输入片段：

```text
&FORCE_EVAL
  &DFT
     &QS
      EXTRAPOLATION ASPC
      EXTRAPOLATION_ORDER 0
     &END QS
  &END DFT
&END FORCE_EVAL
```

### 2.3 `exercises:common:ensemble` — 系综完整教程（LJ 流体，2 万字符）

**官方覆盖**：NVE / NVT / NPT 三种系综 + **径向分布函数 g(r)**。

**官方给出的关键物理约束（PBC 与截断）**：

> - 近邻像的相互作用需要 **`r_ij` 的截断值**；
> - **截断应小于模拟盒尺寸的一半，且大于 σ**。

**官方给出的 g(r) 定义**：

> 径向分布函数（对关联函数）描述**从一个参考粒子出发，密度如何随距离变化**。

### 2.4 `exercises:common:mtd` — 元动力学（TiO₂ 表面，1 万字符）

**体系**：金红石 (110) TiO₂ 表面上**甲酸与水**的动态平衡（DFT-BOMD）。

**官方给的关键实操**：

- **模型是全周期的**，自由水分子上方**必须留足够空间**避免与 z 方向镜像相互作用；
  官方**加了约 20 Å 真空**。
- 盒子：`ABC 19.659 17.806 33.110`，`ALPHA_BETA_GAMMA 90 90 90`，`PERIODIC XYZ`。
- **先做 10 ps、300 K 的短 MD 平衡**，观察吸附物是否重排。
- 然后**设置几个集体变量（CV）**用于 MTD。**官方强调：CV 必须仔细选择，
  必须能描述你关心的构型变化**；先研究所选 CV 的典型行为也很有用。

### 2.5 `exercises:common:i-pi` — CP2K + i-PI 联用（含超算脚本）

**官方说明**：i-PI 是**从头算路径积分分子动力学**的 Python 接口，
由 Python 服务端（只需 Python + NumPy，无需编译）传播（路径积分）核动力学，
外部代码作为客户端计算电子能量与力。

**引用要求**：用 i-PI 配 CP2K 需引用
*Comput. Phys. Commun.* **236** (2019) 214–223 与 *J. Chem. Phys.* **144**, 054111 (2016)。

**官方列出的已发表工作**：*J. Phys. Chem. Lett.* 2020, 11, 9, 3724–3730；
*PNAS* 116 (4) 1110–1115 (2019)；*Nature Communications* **12**, 766 (2021)。

**安装与启动**：

```bash
git clone https://github.com/i-pi/i-pi.git
source ${PATH_TO_IPI}/env.sh
i-pi input.xml > log &
```

> 官方说明：`i-pi/examples/` 里有大量输入示例，覆盖 NVE / NVT / NPT / PIMD / REMP 等方法。

**CP2K 侧（INET socket）**：

```text
&MOTION
   &DRIVER
      HOST host_address
      PORT port
   &END DRIVER
&END MOTION
```

```xml
<ffsocket mode='inet' name='driver'>
  <address>host_address</address>
  <port>port</port>
  <latency>0.01</latency>
  <timeout>5000</timeout>
</ffsocket>
```

**CP2K 侧（UNIX socket）**：加 `UNIX` 关键字，i-PI 侧 `mode='unix'`。

**超算脚本（官方给 Daint/CSCS 示例）**：

```bash
HOST=$(hostname)
source ~/i-pi/env.sh
if [ -e simulation.restart ]; then
   sed -i "s/address>[^<]*</address>$HOST</" simulation.restart
   i-pi simulation.restart  >> log.ipi 2>&1 &
else
   sed -i "s/address>[^<]*</address>$HOST</" input.xml
   i-pi input.xml &> log.ipi &
fi
sleep 5
sed -i "s/HOST.*/HOST $HOST/" cp2k.inp
srun cp2k.psmp -i cp2k.inp -o cp2k.out
wait
```

> **[G层提示]** 这个脚本解决了一个真实痛点：**i-PI 与 CP2K 要连同一个 host 名**，
> 超算上作业节点名是动态的，必须运行时把 `HOST` 替换进去。

---

## 3. 电子结构与性质计算（`exercises:common` 其余页）

### 3.1 `geo_opt` — 几何优化

- **官方对优化算法的定位**：CG、Quasi-Newton 及其变体 BFGS。
  **"这些方法都不保证找到全局极小"**；**BFGS 在初始猜测离极小不远时更高效**。
- 极小条件：① 梯度为零；② Hessian **全正**。
- 梯度即力：`f = −dE/dr`；Hessian：`d²E/dr²`。
- **官方强调：要用振动分析检查 Hessian 本征值；有负值说明不是极小**。

### 3.2 `eos` — 晶格常数优化（Birch–Murnaghan）

**官方给的做法**：虽然可以用 `CELL_OPT` 同时优化晶胞与几何，但这里**手工做**，
因为可以假设只有晶格常数变化。

**BM 状态方程（官方原文）**：

```text
E(V) = E_0 + (9 V_0 B_0 / 16) { [ (V_0/V)^(2/3) − 1 ]^3 B_1
                              + [ (V_0/V)^(2/3) − 1 ]^2 [ 6 − 4 (V_0/V)^(2/3) ] }
```

**官方给的操作参数**：晶格常数**分数取 0.90–1.10，步长 0.025**；
然后拟合 `E_0, V_0, B_0, B_1`，用新 `V_0` 定晶格常数并画图。

**官方示例输入（石墨烯，含收敛技巧）**：

```text
&GLOBAL
  PROJECT graphene
  RUN_TYPE ENERGY
  PRINT_LEVEL MEDIUM
&END GLOBAL
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME  BASIS_MOLOPT
    POTENTIAL_FILE_NAME  POTENTIAL
    &POISSON
      PERIODIC XYZ
    &END POISSON
    &SCF
      SCF_GUESS ATOMIC
      EPS_SCF 1.0E-6
      MAX_SCF 300
      ADDED_MOS 100
      CHOLESKY INVERSE
      &SMEAR ON
        METHOD FERMI_DIRAC
        ELECTRONIC_TEMPERATURE [K] 300
      &END SMEAR
      &DIAGONALIZATION
        ALGORITHM STANDARD
        EPS_ADAPT 0.01
      &END DIAGONALIZATION
      &MIXING
        METHOD BROYDEN_MIXING
        ALPHA 0.2
        BETA 1.5
        NBROYDEN 8
      &END MIXING
    &END SCF
    &XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
```

> **[G层提示]** 这套 `SMEAR + ADDED_MOS + BROYDEN_MIXING` 组合是官方反复使用的
> **金属/小带隙体系收敛配方**，与 `03_scf_convergence.md` 一致。

### 3.3 `pdos` / `bs` — 态密度与能带（WO₃）

**官方两条硬约束（`bs` 页）**：

> - **K 点采样只支持 GGA 泛函**。
> - **CP2K 不支持用高等级电子结构理论（如杂化泛函）做能带结构计算。**

**`bs` 与 `pdos` 的输入差异（官方原文）**：只需相对 PDOS 例子改几处 ——
加 `UKS`、`&QS EXTRAPOLATION USE_GUESS`（**k 点采样必需**）、`&KPOINTS`、`&PRINT/&BAND_STRUCTURE`。

```text
&KPOINTS
   SCHEME MONKHORST-PACK 3 3 3
   WAVEFUNCTIONS REAL
   SYMMETRY .FALSE.
   FULL_GRID .FALSE.
   PARALLEL_GROUP_SIZE -1
&END KPOINTS
&PRINT
   &BAND_STRUCTURE
      ADDED_MOS 2
      FILE_NAME WO3.bs
      &KPOINT_SET
         UNITS B_VECTOR
         SPECIAL_POINT ???   #GAMA
         SPECIAL_POINT ???   #X
         SPECIAL_POINT ???   #M
         SPECIAL_POINT ???   #GAMA
      &END
   &END
&END PRINT
```

> **[G层提示]** 官方示例里 `SPECIAL_POINT ???` 是**待填占位**（原文如此），
> 需要自己按晶格填高对称点坐标 —— 这正是 `SeeK-path`（见 `00_map.md` §2.2）的用途。

**PDOS 打印配置**：

```text
&PRINT
   &PDOS
      NLUMO -1          # 打印全部可用投影 DOS
      COMPONENTS        # 按量子数拆分密度
   &END
&END PRINT
```

### 3.4 `chg` — 电荷密度差（含 Cubecruncher）

**公式（官方原文）**：`Δρ = ρ_AB − ρ_A − ρ_B`，
需要 **AB / A / B 三次单点计算**打印电子密度或总密度。

```bash
cubecruncher.x -i AB.cube   -subtract A.cube -o AB_A.cube
cubecruncher.x -i AB_A.cube -subtract B.cube -o chg_dif.cube
```

**官方还给了含时版本**：`Δρ(t−t_0) = ρ(t) − ρ(t_0)`，

```bash
cubecruncher.x -i elec_dens_t.cube -subtract elec_dens_t0.cube -o diff_t-t0.cube
```

### 3.5 `wf` — 功函数

**定义（官方原文）**：功函数是把电子从固体（或表面）移到真空某点所需的**最小热力学功**；
**它不是体材料的特征，而是材料表面的性质**。

```text
W = −eφ − E_f
φ = 真空中的静电势；E_f = 表面费米能级
```

> 官方说明：这两个量可从 **PDOS** 与 **`V_HARTREE_CUBE`** 得到；
> 可用 **Cubecruncher** 沿法线方向算剖面。

### 3.6 `code_structure` — 输入文件结构（入门）

**官方原话**：每个段由 `&SECTION` 初始化、`&END SECTION` 结束；
段内可给该段的 `KEYWORD` 赋 `PARAMETER`。

```text
&SECTION
   KEYWORD PARAMETER
   &SUB_SECTION
      KEYWORD PARAMETER
   &END SUB_SECTION
&END SECTION
```

官方举例：`GLOBAL` 段里 `PROJECT H2O` 给出输出文件前缀，`RUN_TYPE ENERGY` 做单点能。

### 3.7 `vib` — 振动分析（**官方仅标题，无正文**）

> **[官方原文]** 该页只有标题 `Vibrational Analysis`，正文为空（最后修改 2022/09/08）。

### 3.8 `reading_list` — 官方推荐书单与论文

**Books（官方原列）**：

| 书 | 作者 |
|---|---|
| Modern Quantum Chemistry: Introduction to Advanced Electronic Structure Theory | Attila Szabo |
| Molecular Electronic-Structure Theory | Trygve Helgaker, Poul Jørgensen, Jeppe Olsen |
| Electronic Structure: Basic Theory and Practical Methods | Richard M. Martin |
| Understanding Molecular Simulation From Algorithms to Applications | Daan Frenkel, Berend Smit |
| Computer Simulation of Liquids: Second Edition | Michael P. Allen, Dominic J. Tildesley |
| Statistical Mechanics: Theory and Molecular Simulation | Mark E. Tuckerman |
| Ab Initio Molecular Dynamics Basic Theory and Advanced Methods | Dominik Marx, Jürg Hutter |
| Time-Dependent Density-Functional Theory: Concepts and Applications | Carsten A. Ullrich |

**Papers（官方原列，含 DOI）**：

| 主题 | 论文 |
|---|---|
| CPMD | *Unified Approach for Molecular Dynamics and Density-Functional Theory*，Car & Parrinello，DOI 10.1103/PhysRevLett.55.2471 |
| 元动力学 | *Escaping free-energy minima*，Laio & Parrinello，DOI 10.1073/pnas.202427399 |
| 实时方法 | *Real-Time Time-Dependent Electronic Structure Theory*，DOI 10.1021/acs.chemrev.0c00223；*Real-time TD electronic structure theory*，DOI 10.1002/wcms.1341 |
| GPW | *A hybrid Gaussian and plane wave density functional scheme*，DOI 10.1080/002689797170220 |
| GAPW | *The Gaussian and augmented-plane-wave density functional method for AIMD*，DOI 10.1007/s002140050523；*All-electron ab-initio molecular dynamics*，DOI 10.1039/B001167N |

> **[G层提示]** 这份书单是**官方为入门者开的最小阅读集**，
> 与 `12_authority_sources.md` 的权威性分级互补：这里给"学什么"，那里给"信什么"。

### 3.9 `useful_tools` — 官方推荐的外部工具（含建模教程链接）

| 类别 | 工具 |
|---|---|
| 晶体结构数据库 | Bilbao Crystallographic Server；Crystallography Open Database；Materials Project |
| 基组数据库 | Basis Set Exchange |
| 建模软件 | Avogadro；VESTA；VMD |
| 建模教程 | **Building slab using VESTA**；**Building slab using Avogadro** |
| 数据可视化 | Gnuplot；Matplotlib；Plotly |
| 报告写作 | Overleaf |

> **[G层提示]** 这两条**建 slab 的教程链接**正好补上 skill 的已知边界——
> "能从已有 CIF/xyz 读结构，但**不能从零生成初始结构**"。

---

## 4. 课程练习集中的高价值专题（2014–2025）

以下页面**不在 `common` 下**，但内容与 AIMD/性质计算高度相关，
且**多数含完整可运行输入**。挑出与 skill 定位最相关的：

### 4.1 自由能与增强采样

| 页面 | 主题 | 字符 |
|---|---|---|
| `2015_cecam_tutorial:mtd1` | 元动力学（第一部分） | 25,775 |
| `2014_ethz_mmm:nacl_free_energy` | NaCl 解离的自由能剖面 | 7,062 |
| `2017_ethz_mmm:replica_2017` | 副本交换 MD | 12,542 |
| `2018_ethz_mmm:re_2018` | 副本交换（2018 版） | 12,068 |
| `2018_ethz_mmm:pmf` | 平均力势 | — |
| `2018_ethz_mmm:h2o_md` | 水的 MD | — |
| `2014_ethz_mmm:alanine_dipeptide` | 丙氨酸二肽 Ramachandran 图 | 6,761 |

### 4.2 AIMD 与 MD

| 页面 | 主题 | 字符 |
|---|---|---|
| `2015_pitt:aimd` | **AIMD 完整练习** | 20,871 |
| `2014_ethz_mmm:nacl_md` / `2015_ethz_mmm:nacl_md` | 观察 NaCl 解离 | 18,171 / 18,581 |
| `2014_ethz_mmm:md_slab` / `2015_ethz_mmm:md_slab` | 热金 slab（Hot gold） | 3,229 |
| `2014_ethz_mmm:t_melting` | 铜的熔点测定 | 4,132 |
| `2016_ethz_mmm:t_melting` | LJ 体系熔点 | 7,482 |
| `2014_uzh_molsim:h2o_md` / `h2o_diff` / `h2o_ff` | 水的 MD / 扩散 / 力场 | — |

### 4.3 电子结构与光谱

| 页面 | 主题 | 字符 |
|---|---|---|
| `common:lr-tddft` | **XAS LR-TDDFT 完整教程**（**与 `21_...` 同源**，官方注明是 Bussy 文章的副本） | 34,389 |
| `2017_uzh_cp2k-tutorial:gw` | **GW 计算** | 15,270 |
| `2017_uzh_cp2k-tutorial:hybrid` | **杂化泛函** | 20,709 |
| `2017_uzh_cp2k-tutorial:gapw` | **GAPW 全电子** | 12,397 |
| `2017_uzh_cp2k-tutorial:wfc` | 波函数 | — |
| `2015_pitt:gga` / `hfx` / `mp2` / `ls` | GGA / HF 交换 / MP2 / 线性标度 | 19,969 / 14,288 / — / — |
| `2014_ethz_mmm:uv` | **TDDFT 吸收光谱** | 6,075 |
| `2014_ethz_mmm:tio2_gap` | **TiO₂ 带隙随 %HFX 变化** | 7,056 |
| `2014_ethz_mmm:ls_scf` | 线性标度 SCF | 4,476 |
| `2014_ethz_mmm:wannier` | 最大局域化 Wannier 函数 | 6,761 |
| `2018_ethz_mmm:infrared_2018` | **红外光谱** | — |
| `2014_ethz_mmm:infra_red` | 红外（**该页为空**） | 0 |

### 4.4 表面、吸附与 QM/MM

| 页面 | 主题 | 字符 |
|---|---|---|
| `2014_ethz_mmm:dye_tio` / `2015` / `2016` | **染料锚定 TiO₂**（最大单页） | 25,057 / 24,959 / 24,959 |
| `2017_ethz_mmm:c2h2_pdga` | **乙炔在 PdGa 上吸附** | 24,202 |
| `2018_ethz_mmm:adsorption_2018` | 吸附 | — |
| `2017_ethz_mmm:qmmm` / `2018_ethz_mmm:qmmm_2018` | **QM/MM** | — |
| `2014_ethz_mmm:surface_au` / `surface_cu` | Au / Cu 表面能 | 3,793 / 3,428 |
| `2014_ethz_mmm:simple_stm` / `2017_ethz_mmm:stm` | STM 图像 | 5,574 / — |
| `2016_uzh_cmest:defects_in_graphene` / `defects_in_silicon` | 石墨烯/硅缺陷 | 4,299 / — |

### 4.5 半经验与力场

| 页面 | 主题 | 字符 |
|---|---|---|
| `2015_cecam_tutorial:urea` | 尿素（半经验） | 16,575 |
| `2015_cecam_tutorial:forcefields` | 力场 | — |
| `2015_cecam_tutorial:basis_set_optimisation_using_optimize_basis` | **基组优化** | — |
| `2015_cecam_tutorial:geometry_and_cell_optimization` | 几何与晶胞优化 | — |
| `2014_uzh_molsim:h2o_ff` | 水的力场 | — |

### 4.6 2019–2025 年新课程

| 课程 | 主题 |
|---|---|
| `2019_conexs_newcastle:ex0`–`ex4` | 光谱学专题（EXAFS/XANES 等），5 页共 6.9 万字符 |
| `2019_uzh_acpc2` / `2020_uzh_acpc2` / `2021_uzh_acpc2` | 原子级计算物理化学（`ex01`–`ex03` + 安装/登录） |
| `2025_cp2k_crystallography:ex1`–`ex4` | **结晶学计算方法**（最新，CECAM/EPFL） |
| `2018_uzh_acpc2:l-j_flu` | LJ 流体（2.3 万字符） |

---

## 5. 官方空链接页（如实登记，不编造）

以下 **9 个页面在 `exercises:common:index` 里有链接，但实际不存在**
（官方原文："This topic does not exist yet"）：

| 页面 | 在索引中的归类 |
|---|---|
| `exercises:common:blue_moon` | Blue Moon Ensemble（蓝月系综） |
| `exercises:common:gga` | GGA, Meta-GGA and LIBXC |
| `exercises:common:hfx` | Hybrid Functional |
| `exercises:common:mlp` | Machine Learning Potential |
| `exercises:common:pimd` | Path-Integral Molecular Dynamics |
| `exercises:common:tddft` | Time-dependent DFT |
| `exercises:common:vdos` | Velocity Density of States from AIMD |
| `exercises:common:vdw` | van der Waals |
| `exercises:common:wavefun` | Wavefunction based Methods |

另有 **1 页只有标题、无正文**：

| 页面 | 状态 |
|---|---|
| `exercises:common:vib` | 只有标题 `Vibrational Analysis` |

> **[G层提示]** 这是**官方自身的缺口**（索引先建了、内容未写），
> 与 `_sources.md` §5.1 登记的原则一致：**如实登记，不编造**。
> 其中 `blue_moon`、`pimd`、`tddft` 的主题**在 `17_...`/`21_...` 手册页里已有正文覆盖**，
> 所以不影响知识完整性；`vdos`、`mlp` 的内容则分别在 `06_properties.md` 与 `22_...` 中。

---

## 6. 全部 239 个有内容页面的完整清单

> 按课程分组，组内按字符数降序。**字符数为正文纯文本长度**，可用来判断内容分量。
> 页面路径补全方式：`https://www.cp2k.org/exercises:` + 表中页面名。

### 2015_ethz_mmm  (27 页 / 179,315 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2015_ethz_mmm:dye_tio` | Dye anchoring to TiO$_2$ | 24959 |
| `2015_ethz_mmm:nacl_md` | Observe NaCl dissociation | 18581 |
| `2015_ethz_mmm:monte_carlo_ice` | Properties of Ice from Monte Carlo Simulations | 8528 |
| `2015_ethz_mmm:bs` | (无标题) | 8524 |
| `2015_ethz_mmm:benzene_dimer` | Binding Energy of the Benzene Dimer | 8253 |
| `2015_ethz_mmm:c2h2_bond_energy` | C2H2 and C2H4 bond energy | 7801 |
| `2015_ethz_mmm:nudged_elastic_band` | Nudged Elastic Band | 7497 |
| `2015_ethz_mmm:nacl_free_energy` | Free Energy Profile of NaCl Dissociation | 7062 |
| `2015_ethz_mmm:tio2_gap` | TiO$_2$ Band Gap as a function of %hfx | 7056 |
| `2015_ethz_mmm:alanine_dipeptide` | Ramachandran plot for Alanine Dipeptide | 6761 |
| `2015_ethz_mmm:wannier` | Maximally Localized Wannier Functions | 6761 |
| `2015_ethz_mmm:single_point_calculation` | Computation of the Lennard Jones curve | 6467 |
| `2015_ethz_mmm:uv` | Absorption spectroscopy with time-dependent density functional theory | 6075 |
| `2015_ethz_mmm:md_ala` | Molecular Dynamics simulation of a small molecule | 5690 |
| `2015_ethz_mmm:reaction_energy` | Reaction Energy | 5611 |
| `2015_ethz_mmm:simple_stm` | Simple STM images | 5574 |
| `2015_ethz_mmm:mo_ethene` | Molecular orbitals of Ethene | 5206 |
| `2015_ethz_mmm:ls_scf` | Linear Scaling Self Consistent Field Methods | 4476 |
| `2015_ethz_mmm:basis_sets` | Basis Sets | 4412 |
| `2015_ethz_mmm:t_melting` | Determination of the melting temperature of copper | 4132 |
| `2015_ethz_mmm:alanine_modify` | Modification of the dihedral parameters | 3996 |
| `2015_ethz_mmm:surface_au` | Calculation of surface energies of Au | 3793 |
| `2015_ethz_mmm:surface_cu` | Surface energies of Copper high-symmetry surfaces | 3428 |
| `2015_ethz_mmm:md_slab` | Hot gold | 3229 |
| `2015_ethz_mmm:hfx_h2ion` | Hartree-Fock exchange for the dihydrogen cation | 2852 |
| `2015_ethz_mmm:geometry_optimization` | Geometry Optimization | 2591 |
| `2015_ethz_mmm:infra_red` | (无标题) | 0 |

### 2016_ethz_mmm  (25 页 / 174,380 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2016_ethz_mmm:dye_tio` | Dye anchoring to TiO$_2$ | 24959 |
| `2016_ethz_mmm:nacl_md` | Observe NaCl dissociation | 18581 |
| `2016_ethz_mmm:bs` | (无标题) | 8944 |
| `2016_ethz_mmm:benzene_dimer` | Binding Energy of the Benzene Dimer | 8253 |
| `2016_ethz_mmm:c2h2_bond_energy` | C2H2 and C2H4 bond energy | 7801 |
| `2016_ethz_mmm:nudged_elastic_band` | Nudged Elastic Band | 7497 |
| `2016_ethz_mmm:t_melting` | Determination of the melting temperature of a LJ system | 7482 |
| `2016_ethz_mmm:nacl_free_energy` | Free Energy Profile of NaCl Dissociation | 7062 |
| `2016_ethz_mmm:tio2_gap` | TiO$_2$ Band Gap as a function of %hfx | 7061 |
| `2016_ethz_mmm:wannier` | Maximally Localized Wannier Functions | 6761 |
| `2016_ethz_mmm:alanine_dipeptide` | Ramachandran plot for Alanine Dipeptide | 6757 |
| `2016_ethz_mmm:single_point_calculation` | Computation of the Lennard Jones curve | 6562 |
| `2016_ethz_mmm:md_ala` | Molecular Dynamics simulation of a small molecule | 5797 |
| `2016_ethz_mmm:simple_stm` | Simple STM images | 5733 |
| `2016_ethz_mmm:reaction_energy` | Reaction Energy | 5611 |
| `2016_ethz_mmm:mo_ethene` | Molecular orbitals of Ethene | 5206 |
| `2016_ethz_mmm:ls_scf` | Linear Scaling Self Consistent Field Methods | 4495 |
| `2016_ethz_mmm:surface_au` | Calculation of surface energies of Au | 4423 |
| `2016_ethz_mmm:basis_sets` | Basis Sets | 4412 |
| `2016_ethz_mmm:infra_red` | Infrared spectroscopy with molecular dynamics | 4110 |
| `2016_ethz_mmm:surface_cu` | Surface energies of Copper high-symmetry surfaces | 4023 |
| `2016_ethz_mmm:alanine_modify` | Modification of the dihedral parameters | 3996 |
| `2016_ethz_mmm:md_slab` | Hot gold | 3408 |
| `2016_ethz_mmm:hfx_h2ion` | Hartree-Fock exchange for the dihydrogen cation | 2852 |
| `2016_ethz_mmm:geometry_optimization` | Geometry Optimization | 2594 |

### 2014_ethz_mmm  (27 页 / 167,546 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2014_ethz_mmm:dye_tio` | Dye anchoring to TiO$_2$ | 25057 |
| `2014_ethz_mmm:nacl_md` | Observer NaCl dissociation | 18171 |
| `2014_ethz_mmm:c2h2_bond_energy` | C2H2 and C2H4 bond energy | 8724 |
| `2014_ethz_mmm:bs` | (无标题) | 8524 |
| `2014_ethz_mmm:benzene_dimer` | Binding Energy of the Benzene Dimer | 8253 |
| `2014_ethz_mmm:monte_carlo_ice` | Properties of Ice from Monte Carlo Simulations | 7420 |
| `2014_ethz_mmm:nudged_elastic_band` | Nudged Elastic Band | 7246 |
| `2014_ethz_mmm:tio2_gap` | TiO$_2$ Band Gap as a function of %hfx | 7056 |
| `2014_ethz_mmm:wannier` | Maximally Localized Wannier Functions | 6761 |
| `2014_ethz_mmm:alanine_dipeptide` | Ramachandran plot for Alanine Dipeptide | 6175 |
| `2014_ethz_mmm:uv` | Absorption spectroscopy with time-dependent density functional theory | 6075 |
| `2014_ethz_mmm:mo_ethene` | Molecular orbitals of Ethene | 5617 |
| `2014_ethz_mmm:reaction_energy` | Reaction Energy | 5423 |
| `2014_ethz_mmm:nacl_free_energy` | Free Energy Profile of NaCl Dissociation | 5398 |
| `2014_ethz_mmm:single_point_calculation` | Computation of the Lennard Jones curve for two Ar atoms | 4871 |
| `2014_ethz_mmm:basis_sets` | Basis Sets | 4063 |
| `2014_ethz_mmm:simple_stm` | Simple STM images | 4013 |
| `2014_ethz_mmm:ls_scf` | Linear Scaling Self Consistent Field Methods | 4010 |
| `2014_ethz_mmm:infra_red` | Infrared spectroscopy with molecular dynamics | 3907 |
| `2014_ethz_mmm:t_melting` | Determination of the melting temperature of copper | 3803 |
| `2014_ethz_mmm:alanine_modify` | Modification of the dihedral parameters | 3078 |
| `2014_ethz_mmm:hfx_h2ion` | Hartree-Fock exchange for the dihydrogen cation | 2835 |
| `2014_ethz_mmm:surface_cu` | Surface energies of Copper high-symmetry surfaces | 2559 |
| `2014_ethz_mmm:md_ala` | Molecular Dynamics simulation of a small molecule | 2516 |
| `2014_ethz_mmm:geometry_optimization` | Geometry Optimization | 2431 |
| `2014_ethz_mmm:md_slab` | Hot gold | 2085 |
| `2014_ethz_mmm:surface_au` | Calculation of surface energies of Au | 1475 |

### common  (17 页 / 104,924 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `common:lr-tddft` | How to run XAS LR-TDDFT calculations | 34389 |
| `common:ensemble` | Ensembles (Lennard-Jones liquids) | 18918 |
| `common:mtd` | Metadynamics | 9750 |
| `common:bs` | Band structure of WO$_3$ Lattice | 7134 |
| `common:neb` | Nudged elastic band | 5268 |
| `common:geo_opt` | Geometry Optimization | 5072 |
| `common:pdos` | Projected density of states for WO$_3$ | 4432 |
| `common:reading_list` | (无标题) | 3658 |
| `common:sgcp` | (无标题) | 3306 |
| `common:eos` | (无标题) | 3291 |
| `common:i-pi` | (无标题) | 2922 |
| `common:aimd` | Ab-initio molecular dynamics | 2313 |
| `common:chg` | (无标题) | 1285 |
| `common:useful_tools` | (无标题) | 1188 |
| `common:wf` | (无标题) | 969 |
| `common:code_structure` | (无标题) | 825 |
| `common:vib` | Vibrational Analysis | 204 |

### 2017_ethz_mmm  (15 页 / 100,305 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2017_ethz_mmm:c2h2_pdga` | Adsorption of C2H2 on PdGa(111) | 24202 |
| `2017_ethz_mmm:replica_2017` | Replica exchange of the disordering of a cluster | 12542 |
| `2017_ethz_mmm:qmmm` | Validation of a KCl QMMM model | 7930 |
| `2017_ethz_mmm:bands_2` | (无标题) | 6783 |
| `2017_ethz_mmm:t_melting_2017` | Determination of the melting temperature of copper | 6064 |
| `2017_ethz_mmm:reaction_energy_2017` | Dehydration of ethanol | 5884 |
| `2017_ethz_mmm:pythonmd` | 38 atom Lennard-Jones cluster: molecular dynamics with python | 5606 |
| `2017_ethz_mmm:lennard_jones_cluster` | 38 atom Lennard-Jones cluster | 4959 |
| `2017_ethz_mmm:surface_cu` | Surface energies of Copper high-symmetry surfaces | 4723 |
| `2017_ethz_mmm:surface_au` | Calculation of surface energies of Au | 4617 |
| `2017_ethz_mmm:stm` | (无标题) | 4137 |
| `2017_ethz_mmm:mc_and_kmc_2` | Kinetic Monte Carlo simulations for the diffusion of molecules on a substrate | 3932 |
| `2017_ethz_mmm:mc_and_kmc` | Monte Carlo simulations for the estimation of molecule pair interatcion | 3440 |
| `2017_ethz_mmm:bands_1` | Crystallographic point groups, free electron model | 3061 |
| `2017_ethz_mmm:lennard_jones_cluster_neb` | 38 atom Lennard-Jones cluster: nudged elastic band | 2425 |

### 2018_ethz_mmm  (15 页 / 92,467 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2018_ethz_mmm:re_2018` | Replica exchange of the disordering of a cluster | 12068 |
| `2018_ethz_mmm:h2o_md` | Molecular dynamics of water | 11128 |
| `2018_ethz_mmm:qmmm_2018` | Validation of a KCl QMMM model | 8083 |
| `2018_ethz_mmm:c2h2_bond_energy_2018` | C2H2 and C2H4 bond energy | 7441 |
| `2018_ethz_mmm:bands_ii_2018` | (无标题) | 7221 |
| `2018_ethz_mmm:ethanol_2018` | Dehydration of ethanol | 5866 |
| `2018_ethz_mmm:lennard_jones_cluster_2018` | 38 atom Lennard-Jones cluster | 5471 |
| `2018_ethz_mmm:adsorption_2018` | Adsorption of acetylene on an intermetallic surface | 5361 |
| `2018_ethz_mmm:pmf` | Reproducing a PMF calculation for adsorption of an organic molecule on KCl | 5237 |
| `2018_ethz_mmm:stm_2018` | (无标题) | 5149 |
| `2018_ethz_mmm:bf3` | Molecular orbitals of Boron trifluoride | 4613 |
| `2018_ethz_mmm:infrared_2018` | Infrared spectroscopy with molecular dynamics | 4175 |
| `2018_ethz_mmm:kmc2018` | Kinetic Monte Carlo simulations for the diffusion of molecules on a substrate | 4016 |
| `2018_ethz_mmm:mc2018` | Monte Carlo simulations for the estimation of pair interactions | 3708 |
| `2018_ethz_mmm:bands_i_2018` | Crystallographic point groups, free electron model | 2930 |

### 2017_uzh_cmest  (15 页 / 91,150 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2017_uzh_cmest:pdos` | Projected density of states and Band structure for WO$_3$ | 11907 |
| `2017_uzh_cmest:login` | First Login | 10991 |
| `2017_uzh_cmest:path_optimization_neb` | Path optimization using NEB | 10226 |
| `2017_uzh_cmest:first_simulation_run` | Run your first simulation using CP2K | 10198 |
| `2017_uzh_cmest:geometry_optimization` | Electronic structure calculation using DFT | 6486 |
| `2017_uzh_cmest:electronic_structure_dft` | Electronic structure calculation using DFT | 5957 |
| `2017_uzh_cmest:basic_electronic_structure` | Basic electronic structure calculation | 5901 |
| `2017_uzh_cmest:phonon_calculation` | Phonon band structure calculation using CP2K and Phonopy | 5413 |
| `2017_uzh_cmest:stm` | Simulation of STM images for a graphene nanoribbon adsorbed on a metallic substrate | 5191 |
| `2017_uzh_cmest:adsorption` | Adsorption on Graphene | 5184 |
| `2017_uzh_cmest:calculation_pbc` | Calculations with Periodic Boundary Conditions | 3453 |
| `2017_uzh_cmest:defects_in_graphene` | Analyzing defects in graphene | 3389 |
| `2017_uzh_cmest:faq` | (无标题) | 3287 |
| `2017_uzh_cmest:defects_in_silicon` | Analyzing defects in bulk silicon | 2538 |
| `2017_uzh_cmest:rp` | (无标题) | 1029 |

### 2018_uzh_cmest  (14 页 / 85,801 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2018_uzh_cmest:pdos` | Projected density of states and Band structure for WO$_3$ | 11902 |
| `2018_uzh_cmest:first_simulation_run` | Run your first simulation using CP2K | 10198 |
| `2018_uzh_cmest:path_optimization_neb` | Path optimization using NEB | 9912 |
| `2018_uzh_cmest:login` | First Login | 9092 |
| `2018_uzh_cmest:geometry_optimization` | Electronic structure calculation using DFT | 6486 |
| `2018_uzh_cmest:electronic_structure_dft` | Electronic structure calculation using DFT | 6155 |
| `2018_uzh_cmest:basic_electronic_structure` | Basic electronic structure calculation | 5901 |
| `2018_uzh_cmest:stm` | Simulation of STM images for a graphene nanoribbon adsorbed on a metallic substrate | 5204 |
| `2018_uzh_cmest:phonon_calculation` | Phonon band structure calculation using CP2K and Phonopy | 5200 |
| `2018_uzh_cmest:adsorption` | Adsorption on Graphene | 5053 |
| `2018_uzh_cmest:calculation_pbc` | Calculations with Periodic Boundary Conditions | 3453 |
| `2018_uzh_cmest:faq` | (无标题) | 3287 |
| `2018_uzh_cmest:defects_in_silicon` | Analyzing defects in bulk silicon | 2929 |
| `2018_uzh_cmest:rp` | (无标题) | 1029 |

### 2016_uzh_cmest  (13 页 / 71,426 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2016_uzh_cmest:path_optimization_neb` | Path optimization using NEB | 10223 |
| `2016_uzh_cmest:first_simulation_run` | Run your first simulation using CP2K | 10198 |
| `2016_uzh_cmest:login` | First Login | 7907 |
| `2016_uzh_cmest:band_structure_calculation` | Getting the band structure of graphene | 6821 |
| `2016_uzh_cmest:geometry_optimization` | Electronic structure calculation using DFT | 6411 |
| `2016_uzh_cmest:electronic_structure_dft` | Electronic structure calculation using DFT | 5957 |
| `2016_uzh_cmest:basic_electronic_structure` | Basic electronic structure calculation | 5482 |
| `2016_uzh_cmest:defects_in_graphene` | Analyzing defects in graphene | 4299 |
| `2016_uzh_cmest:calculating_pdos` | Projected density of states for graphene and h-BN | 4057 |
| `2016_uzh_cmest:calculation_pbc` | Calculations with Periodic Boundary Conditions | 3376 |
| `2016_uzh_cmest:faq` | (无标题) | 2939 |
| `2016_uzh_cmest:defects_in_silicon` | Analyzing defects in bulk silicon | 2017 |
| `2016_uzh_cmest:bulk_modulus_calculation` | Calculating the bulk modulus of Silicon | 1739 |

### 2015_cecam_tutorial  (6 页 / 70,285 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2015_cecam_tutorial:mtd1` | Simple metadynamics simulation using the coordination numbers as variables | 25775 |
| `2015_cecam_tutorial:urea` | QM/MM study of UREA Zwitterion in water | 16575 |
| `2015_cecam_tutorial:neb` | Nanostructures and adsorption on metallic surfaces | 13715 |
| `2015_cecam_tutorial:geometry_and_cell_optimization` | Geometry optimization of NaCl clusters | 5124 |
| `2015_cecam_tutorial:forcefields` | (无标题) | 4874 |
| `2015_cecam_tutorial:basis_set_optimisation_using_optimize_basis` | Basis set optimisation using OPTIMIZE_BASIS | 4222 |

### 2019_conexs_newcastle  (5 页 / 68,908 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2019_conexs_newcastle:ex2` | Linear-response TDDFT for XAS in CP2K: the XAS_TDP method | 17662 |
| `2019_conexs_newcastle:ex4` | Liquid water: PDOS and Born-Oppenheimer MD | 15887 |
| `2019_conexs_newcastle:ex1` | The H$_2$O molecule: DFT basics | 15864 |
| `2019_conexs_newcastle:ex3` | MgS and MgO: Periodic systems and XAS | 14717 |
| `2019_conexs_newcastle:ex0` | Connecting to the HPC cluster | 4778 |

### 2015_pitt  (5 页 / 67,604 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2015_pitt:aimd` | Ab initio molecular dynamics | 20871 |
| `2015_pitt:gga` | GGA based surface science | 19969 |
| `2015_pitt:hfx` | Hartree-Fock exchange | 14288 |
| `2015_pitt:ls` | Linear Scaling Self Consistent Field Methods | 6496 |
| `2015_pitt:mp2` | MP2 and RPA | 5980 |

### 2017_uzh_cp2k-tutorial  (5 页 / 62,145 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2017_uzh_cp2k-tutorial:hybrid` | Hartree-Fock exchange | 20709 |
| `2017_uzh_cp2k-tutorial:gw` | GW method for computing electronic levels | 15270 |
| `2017_uzh_cp2k-tutorial:gapw` | Gaussian and Augmented Plane Wave Method | 12397 |
| `2017_uzh_cp2k-tutorial:wfc` | Required files | 8040 |
| `2017_uzh_cp2k-tutorial:login` | First Login | 5729 |

### 2019_uzh_acpc2  (5 页 / 56,974 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2019_uzh_acpc2:ex01` | Lennard-Jones liquids | 20017 |
| `2019_uzh_acpc2:login` | First Login | 10991 |
| `2019_uzh_acpc2:ex03` | Nudged elastic band and free energy calculations | 9042 |
| `2019_uzh_acpc2:installation` | Exercise 0 | 8942 |
| `2019_uzh_acpc2:ex02` | Molecular Solution | 7982 |

### 2021_uzh_acpc2  (5 页 / 55,151 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2021_uzh_acpc2:ex01` | Lennard-Jones liquids | 22191 |
| `2021_uzh_acpc2:ex03` | Nudged elastic band and free energy calculations | 9912 |
| `2021_uzh_acpc2:ex02` | Molecular Solution | 8598 |
| `2021_uzh_acpc2:installation` | (无标题) | 7355 |
| `2021_uzh_acpc2:login` | First Login | 7095 |

### 2018_uzh_acpc2  (4 页 / 50,750 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2018_uzh_acpc2:l-j_flu` | Lennard-Jones liquids | 23358 |
| `2018_uzh_acpc2:prot_fol` | Protein Folding in Solution | 10235 |
| `2018_uzh_acpc2:installation` | Exercise 0 | 9199 |
| `2018_uzh_acpc2:mol_sol` | Molecular Solution | 7958 |

### 2015_uzh_molsim  (12 页 / 49,786 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2015_uzh_molsim:chp_cu111` | QM/MM: Cyclohexaphenylene on Cu(111) | 9876 |
| `2015_uzh_molsim:h2o_ff` | Constructing a force field for the $\text{H}_2\text{O}$ molecule | 8728 |
| `2015_uzh_molsim:h2o_diff` | Diffusion constant, viscosity and size effects | 4672 |
| `2015_uzh_molsim:nacl_free_energy` | Profiles of potential energy and free energy | 4207 |
| `2015_uzh_molsim:nacl_md` | Free and constrained molecular dynamics | 3901 |
| `2015_uzh_molsim:gnuplot` | 2d plotting with Gnuplot | 3418 |
| `2015_uzh_molsim:ssh` | Working on remote computers with SSH | 3372 |
| `2015_uzh_molsim:h2o_md` | Molecular dynamics of liquid $\text{H}_2\text{O}$ | 3159 |
| `2015_uzh_molsim:vmd` | 3d visualization with VMD | 2788 |
| `2015_uzh_molsim:cp2k` | Running a simple example with CP2K | 2314 |
| `2015_uzh_molsim:alanine_dipeptide` | Potential energy surface of alanine dipeptide | 1831 |
| `2015_uzh_molsim:bash_terminal` | The bash terminal | 1520 |

### 2020_uzh_acpc2  (5 页 / 49,608 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2020_uzh_acpc2:ex01` | Lennard-Jones liquids | 20017 |
| `2020_uzh_acpc2:ex03` | Nudged elastic band and free energy calculations | 9042 |
| `2020_uzh_acpc2:ex02` | Molecular Solution | 7939 |
| `2020_uzh_acpc2:login` | First Login | 6680 |
| `2020_uzh_acpc2:installation` | (无标题) | 5930 |

### 2014_uzh_molsim  (11 页 / 48,025 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2014_uzh_molsim:chp_cu111` | QM/MM: Cyclohexaphenylene on Cu(111) | 9876 |
| `2014_uzh_molsim:h2o_ff` | Constructing a force field for the $\text{H}_2\text{O}$ molecule | 9632 |
| `2014_uzh_molsim:h2o_diff` | Diffusion constant, viscosity and size effects | 4672 |
| `2014_uzh_molsim:nacl_free_energy` | Profiles of potential energy and free energy | 4208 |
| `2014_uzh_molsim:nacl_md` | Free and constrained molecular dynamics | 4013 |
| `2014_uzh_molsim:gnuplot` | 2d plotting with Gnuplot | 3418 |
| `2014_uzh_molsim:h2o_md` | Molecular dynamics of liquid $\text{H}_2\text{O}$ | 3159 |
| `2014_uzh_molsim:ssh` | Working on remote computers with SSH | 2983 |
| `2014_uzh_molsim:vmd` | 3d visualization with VMD | 2788 |
| `2014_uzh_molsim:bash_terminal` | The bash terminal in MacOS X | 1664 |
| `2014_uzh_molsim:alanine_dipeptide` | Potential energy surface of alanine dipeptide | 1612 |

### 2017_uzh_acpc2  (4 页 / 39,718 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2017_uzh_acpc2:l-j_flu` | Lennard-Jones liquids | 19992 |
| `2017_uzh_acpc2:login` | First Login | 9527 |
| `2017_uzh_acpc2:mol_sol` | Molecular Solution | 6323 |
| `2017_uzh_acpc2:prot_fol` | Protein Folding in Solution | 3876 |

### 2025_cp2k_crystallography  (4 页 / 18,430 字符)

| 页面 | 标题 | 字符数 |
|---|---|---|
| `2025_cp2k_crystallography:ex1` | Exercise 1: Electronic energy of the L-alanine crystal | 11045 |
| `2025_cp2k_crystallography:ex3` | Exercise 3: Electronic band structure of monolayer MoS$_\text{2}$ | 4857 |
| `2025_cp2k_crystallography:ex2` | Exercise 2: Geometry optimization of the L-alanine crystal | 1297 |
| `2025_cp2k_crystallography:ex4` | Exercise 4: Molecular dynamics of water | 1231 |

> **注**：`2014_ethz_mmm` / `2015_ethz_mmm` / `2016_ethz_mmm` 是同一课程不同年份，内容高度重叠；
> `2017/2018/2019/2020/2021_uzh_acpc2` 同理。清单全部保留，便于按年份对照官方演进。

---

## 7. 与 G 层其它文件的关系

| 需求 | 去哪看 |
|---|---|
| NEB 怎么做（完整输入） | **本文件 §1**（官方唯一入口） |
| NEB 的 `&BAND` 关键字表 | `17_constrained_dynamics_and_paths.md` §3 |
| NEB 的实操经验（插点/off-by-one） | F 层 `playbook.md` §2.4 |
| AIMD 系综/温控/压控 | `04_sampling_md.md` |
| SGCP / CPMD 对比 | **本文件 §2.2** |
| i-PI 联用 | **本文件 §2.5**、`04_sampling_md.md` |
| 元动力学 / 蓝月 | `17_constrained_dynamics_and_paths.md`、**本文件 §2.4** |
| XAS LR-TDDFT | `21_xray_spectroscopy_full.md`（与 `common:lr-tddft` 同源） |
| 基组与赝势 | `14_basis_and_potentials.md` |
| 收敛配方（SMEAR/ADDED_MOS/混合） | `03_scf_convergence.md`、**本文件 §3.2** |
| 电荷密度差 / 功函数 / PDOS | `06_properties.md`、**本文件 §3.3–§3.5** |
| 建 slab 的图形化教程 | **本文件 §3.9**（VESTA / Avogadro） |

---

## 8. 仍未采集（如实登记）

- **本文件不逐页抄录 239 页全文**（约 170 万字符），只提炼高价值做法 + 给完整清单。
  需要某页全文时，按 `www.cp2k.org/exercises:<课程>:<页名>` 直接访问。
- **练习配套的下载文件未采**：如 `NEB.tar.xz`、`snapshot_MD-300K.xyz`、
  `Files/CU.pot`、各页 `*_media/` 下的输入/坐标/脚本打包。这些是**二进制或数据文件**，
  非文档正文（与 `_sources.md` §5.1 的登记原则一致）。
- **9 个官方空链接页 + `vib` 空正文页**：见 §5，属官方自身缺口。
