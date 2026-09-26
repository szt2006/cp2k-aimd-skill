# 05 · 优化：几何、晶胞、NEB（官方）

> **来源**：
> - <https://manual.cp2k.org/trunk/methods/optimization/index.html>
> - <https://manual.cp2k.org/trunk/methods/optimization/geometry_and_cell_opt.html>
> - <https://manual.cp2k.org/trunk/methods/optimization/nudged_elastic_band.html>（占位页）
> **抓取日期**：2026-09-08

---

## 1. 优化章节导航（官方）

- **Geometry and cell optimization**（本文 §2–§9）
- **Nudged Elastic Band**（**占位页**，见本文 §10）

---

## 2. 引言与总体对应关系（官方）

- **几何优化（geometry optimization）**：通过反复计算能量与受力，将原子向势能面上的驻点移动，从而弛豫原子位置。
- **常见用途**：① 去除初始结构中的人为受力；② 获得局部极小值；③ 为分子动力学或性质计算准备结构；④ 用特殊设置搜索过渡态。
- **晶胞优化（cell optimization）**：相关的变胞（variable-cell）问题——**原子位置与模拟晶胞一起弛豫**，使结构满足目标外压或应力条件。

**关键字对应**：

| 目标 | 关键字 | 控制段 |
|---|---|---|
| 固定晶胞几何优化 | `RUN_TYPE GEO_OPT` | `MOTION/GEO_OPT` |
| 晶胞体积/形状也需弛豫 | `RUN_TYPE CELL_OPT` | `MOTION/CELL_OPT` |

**共用关键字（官方）**：`OPTIMIZER`、`MAX_ITER`、`MAX_DR`、`RMS_DR`、`MAX_FORCE`、`RMS_FORCE` 在 `MOTION/GEO_OPT` 与 `MOTION/CELL_OPT` 中**含义相同**。

---

## 3. `GEO_OPT` 还是 `CELL_OPT`？（官方）

### 3.1 使用固定晶胞 `GEO_OPT` 的情形

当**晶格矢量已知、有意固定或与问题无关**时。典型场景：
- 大盒子中的分子与团簇；
- 具有固定基底或真空区的 **slabs（板层）**；
- 对已优化过的晶体晶胞进行计算；
- 只需内部原子坐标弛豫的工作流。

### 3.2 使用 `CELL_OPT` 的情形

当**平衡晶胞体积、形状、压力或残余应力本身就是问题的一部分**时。最常见于：
- 体相晶体（bulk crystals）；
- 应变的固体；
- 需要弛豫面内晶格常数的二维材料；
- 为固定晶胞分子动力学准备结构。

### 3.3 官方注意事项（Note）

- **优化不能替代有限温度下的压力采样**；若所需量是有限温度热平均，应使用合适系综的 MD 工作流。
- 对基于玻恩–奥本海默近似的常规电子结构方法（正是忽略核运动才使"势能面"概念成立），**优化中不涉及温度（核动能）**，被优化的能量**不包含**零点能与热校正（谐振或非谐振）。**因此"0 K 优化"的说法实为用词不当（misnomer）。**

---

## 4. 基本设置（官方示例）

### 4.1 固定晶胞优化

```
&GLOBAL
  PROJECT my_geo_opt
  RUN_TYPE GEO_OPT
&END GLOBAL

&FORCE_EVAL
  ! Define the method that provides energies and forces.
  ! This can be Quickstep DFT, a force field, a machine-learning potential, QM/MM, ...
&END FORCE_EVAL

&MOTION
  &GEO_OPT
    TYPE MINIMIZATION
    OPTIMIZER BFGS
    MAX_ITER  200
    MAX_DR    3.0E-03
    RMS_DR    1.5E-03
    MAX_FORCE 4.5E-04
    RMS_FORCE 3.0E-04
  &END GEO_OPT
&END MOTION
```

### 4.2 变胞优化

- 使用 `RUN_TYPE CELL_OPT` + `CELL_OPT` 块。
- **明确设置 `EXTERNAL_PRESSURE`（不要依赖默认值）**；再额外指定 `STRESS_TENSOR` 也是合理的。

```
&GLOBAL
  PROJECT my_cell_opt
  RUN_TYPE CELL_OPT
&END GLOBAL

&FORCE_EVAL
  ! Define the method that provides energies, forces, and stress.
  STRESS_TENSOR ANALYTICAL ! Compute full stress tensor analytically
&END FORCE_EVAL

&MOTION
  &CELL_OPT
    OPTIMIZER BFGS
    MAX_ITER  200
    EXTERNAL_PRESSURE 1.01325E+00
    PRESSURE_TOLERANCE 100.0
    MAX_DR    3.0E-03
    RMS_DR    1.5E-03
    MAX_FORCE 4.5E-04
    RMS_FORCE 3.0E-04
  &END CELL_OPT
&END MOTION
```

### 4.3 关于解析应力张量的注意（官方 Note）

- 解析应力张量的可用性**取决于能量/受力评估方法**。**部分电子结构方法只支持有限差分数值应力，每个优化迭代将耗时明显更多。**
- 可通过设置 `FORCE_EVAL/PRINT/STRESS_TENSOR` 检查输出中是否提到 numerical stress。

### 4.4 `GEO_OPT/TYPE`（官方）

`TYPE` 选择优化目标：
- **`MINIMIZATION`**：搜索局部极小值，**常规选择**；
- **`TRANSITION_STATE`**：启用过渡态搜索机制；需要 `MOTION/GEO_OPT/TRANSITION_STATE` 中的额外方法相关设置，**不能当作普通极小化处理**。

> **版本提醒**：`&MOTION/&CELL_OPT/TYPE` 在 **2026.2 被移除**，晶胞优化现在**始终使用 `DIRECT_CELL_OPT`**（见 `11_version_changelog.md`）。

### 4.5 `MAX_ITER` 与终止条件（官方）

- `MAX_ITER` 限制优化迭代数。**一次优化迭代可能需要多于一次受力评估**，取决于优化器与线搜索模式。
- 优化在下列**任一**情况发生时终止：
  1. 未达 `MAX_ITER` 前满足收敛判据；
  2. 达到 `MAX_ITER`（无论是否收敛）；
  3. **触发程序的外部控制**，例如达到 `WALLTIME` 指定的全局墙钟时间，或**在工作目录中发现了用户紧急创建的名为 `EXIT` 或 `EXIT_GEO` 的文件**。

---

## 5. 起始结构与晶胞（官方）

### 5.1 通用要求

- 从**化学与物理上合理**的结构开始。**严重的近距接触、非现实的配位环境或准备不当的晶胞，会导致受力不稳定、SCF 失败、非物理的原子位移，或难以恢复的优化器步长。**
- 官方举例：**"amorphous cell" 结构（随机堆积分子/原子）极难优化**，尤其当化学键被严重打乱时；同理，**来自高温 MD 的汽化或熔化状态、含大量断键的构型**也如此。

### 5.2 `CELL_OPT` 的初始晶胞

- 起始体积与形状应**足够接近预期结构与密度**，使压力与应力不被制备假象主导。
- 晶胞弛豫方向取决于外压。对**表面板层、二维/一维材料或含真空的系统，各向异性意味着真空方向不应弛豫**，除非物理上确有需要；**更好的做法是约束相应的晶胞分量，或在选定期望晶胞后使用固定晶胞优化**。
- **可能需要对不同真空尺寸做目标量的收敛性严格测试。**

### 5.3 可视化建议（官方）

- 在建模程序中显示结构与晶胞（**含盒子与近邻周期镜像**）非常有帮助：**在与周期性一致的方向上，盒子边界附近既不应出现大空隙，也不应出现原子拥挤团簇**；反之，**在非周期方向上充足的真空是消除跨界非期望相互作用的关键**。

### 5.4 极端手段：力缩放（官方）

- 作为**保留的极端措施**，`MAX_FORCE`（属于 `FORCE_EVAL/RESCALE_FORCES`）会触发一种机制，**人为将原子上的超大受力按幅值重新缩放**。
- **该设置仅用于粗糙的初始结构**；**一旦几何变得合理、受力接近收敛判据，在通向最终结果的生产运行中不应再使用。**

### 5.5 变胞优化的晶胞表示约定（官方 Note）

- `CELL_OPT` **期望采用"第一个矢量 A 沿 X 轴、第二个矢量 B 位于 XY 平面"的晶胞表示**。这是为了保证当前实现中晶胞矢量能正确响应外压而更新。
- 即便非传统矢量定义有时更"顺手"（例如面心立方晶格的原胞菱形胞），也**应对晶胞与原子坐标施加适当的线性变换以生成输入模型**。官方指向 GitHub issue 3384。

> **版本提醒**：**2027.1 起**，`CELL_OPT` 期间会保留显式给定的晶胞取向，并将 `KEEP_SPACE_GROUP` 应用于晶胞度量（cell metric）（#5648）。

---

## 6. 优化器选择（官方）

`OPTIMIZER` 关键字选择用于更新几何（`CELL_OPT` 时还更新晶胞）的算法。
**最有用的优化器专属控制是：准牛顿法的 trust radius，以及共轭梯度的 line-search 设置。**

### 6.1 `BFGS`（默认）

- **默认优化器**，通常对中小体系高效。构建近似 Hessian，起始结构合理时收敛快。
- **若优化步长过大、振荡或不稳定，`BFGS` 子节中的 `TRUST_RADIUS` 常是第一个需要减小的参数。** 更小的 trust radius 更保守；**过小会拖慢收敛**。
- **开启 `USE_MODEL_HESSIAN` 常可减少所需迭代次数。**

### 6.2 `LBFGS`

- 有限内存变体，**通常更适合大体系**（存储完整近似 Hessian 代价高）。
- 同样有 `TRUST_RADIUS` 控制。对困难弛豫有用，但对准备良好的大体系默认行为通常足够。

### 6.3 `CG`

- 稳健的共轭梯度极小化器。常作为以下情形的良好备选：**起始结构差、受力或应力有噪声、准牛顿步不稳定**。
- **每个 CG 优化步都包含沿搜索方向的一维线搜索，可能需要多次受力评估，因而比 `BFGS` 更贵。**

### 6.4 `CG` 的线搜索：`CG/LINE_SEARCH` 与 `TYPE`（官方）

| `TYPE` | 官方说明 |
|---|---|
| `2PNT` | **最便宜**，由两点外推。当受力评估平滑、优化路径表现良好时高效。最大线搜索步长可用 `MAX_ALLOWED_STEP` 限制 |
| `GOLD` | 黄金分割/Brent 式线搜索。**更贵但更稳健，是困难极小化的更安全默认**。初始 bracketing 步长由 `INITIAL_STEP` 控制；**对存在近距接触或早期步长不稳定的结构，可能需要减小该值** |
| `FIT` | 使用拟合的一维模型。**对数值噪声最稳健，但也最贵**，主要用于更便宜的线搜索表现很差的困难情形 |

### 6.5 优化不稳定时的排查顺序（官方，重要）

若优化出现非物理的大步长或不稳定：

```
1. 先检查起始结构/晶胞以及受力/应力质量；
2. 再考虑减小 BFGS/LBFGS 的 trust radius；
3. 约束有问题的晶胞自由度；
4. 切换到 CG；
5. 或先用较宽松设置做一次短时预备优化，然后再收紧收敛判据。
```

---

## 7. 收敛判据（官方）

### 7.1 关键字与单位

| 关键字 | 含义 | 单位 |
|---|---|---|
| `MAX_FORCE` | 最大受力 | **Hartree/Bohr** |
| `RMS_FORCE` | 受力均方根 | **Hartree/Bohr** |
| `MAX_DR` | 最大位移 | **Bohr** |
| `RMS_DR` | 位移均方根 | **Bohr** |
| `EXTERNAL_PRESSURE` | 目标压力（`CELL_OPT`） | **bar** |
| `PRESSURE_TOLERANCE` | 压力收敛容差（`CELL_OPT`） | **bar** |

### 7.2 变胞优化的典型收敛报告（官方原文）

由 `PROGRAM_RUN_INFO` 控制。**受力以梯度（gradient）形式报告。** 固定晶胞优化时，报告不提及压力，其余相同。

```
 OPT| **************************************************************************
 OPT| Step number                                                              1
 OPT| Optimization method                                                   BFGS
 OPT| Total energy [hartree]                                      -45.5348295392
 OPT| Internal pressure [bar]                                   47536.1640430316
 OPT| Effective energy change [hartree]                            -0.0002840779
 OPT| Predicted energy change [hartree]                            -0.0001679733
 OPT| Step size                                                     0.0105821341
 OPT| Trust radius                                                  0.3779452266
 OPT| Decrease in energy                                                     YES
 OPT|
 OPT| Maximum step size                                             0.0105821341
 OPT| Convergence limit for maximum step size                       0.0030000000
 OPT| Maximum step size is converged                                          NO
 OPT|
 OPT| RMS step size                                                 0.0033463738
 OPT| Convergence limit for RMS step size                           0.0015000000
 OPT| RMS step size is converged                                              NO
 OPT|
 OPT| Maximum gradient                                              0.0073208554
 OPT| Convergence limit for maximum gradient                        0.0004500000
 OPT| Maximum gradient is converged                                           NO
 OPT|
 OPT| RMS gradient                                                  0.0023150598
 OPT| Convergence limit for RMS gradient                            0.0003000000
 OPT| RMS gradient is converged                                               NO
 OPT|
 OPT| Pressure deviation [bar]                                  47535.1507930316
 OPT| Pressure tolerance [bar]                                    100.0000000000
 OPT| Pressure is converged                                                   NO
 OPT| **************************************************************************
```

> 该报告印证了官方示例的推荐取值：`MAX_DR = 3.0E-03`、`RMS_DR = 1.5E-03`、`MAX_FORCE = 4.5E-04`、`RMS_FORCE = 3.0E-04`、`PRESSURE_TOLERANCE = 100.0`。

### 7.3 充分条件 vs 必要条件（官方）

- 在 `MAX_ITER` 步内**满足所有判据**是优化收敛的**充分条件**。
- 对 `BFGS` 与 `CG` 优化器，这**也是必要条件**。
- **对 `LBFGS` 优化器，这不是必要条件**：LBFGS 有自己额外的一对判据 `WANTED_PROJ_GRADIENT` 与 `WANTED_REL_F_ERROR`，可能覆盖上述通用判据。

### 7.4 `LBFGS` 提前报告收敛的提示信息（官方原文）

```
 ************************************************
 * Specific L-BFGS convergence criteria         *
 * WANTED_PROJ_GRADIENT and WANTED_REL_F_ERROR  *
 * satisfied .... run CONVERGED!                *
 *                    * * *                     *
 * General convergence criteria on stepsize and *
 * gradients may or may not have been satisfied *
 * yet; if unsatisfactory, try tightening the   *
 * L-BFGS convergence criteria and restart run. *
 ************************************************
```

> 即：**即使一个或多个通用判据尚未满足，也可能看到上述消息。** 官方建议收紧判据或换用其他优化器并重启，直到满意收敛。

### 7.5 `LBFGS` 附加输出（官方）

- `LBFGS` 有自己的 `PRINT_LEVEL` 控制主输出的详细程度。
- 还会生成单独的 **`iterate.dat`** 文件，其中列 `projg` 与 `f` 可对照 `WANTED_PROJ_GRADIENT` 与 `WANTED_REL_F_ERROR` 判据检查。

```
   it   nf  nseg  nact  sub  itls  stepl    tstep     projg        f
    0    1     -     -   -     -     -        -     4.632D-02 -1.082D+00
    1    2     1     0  ---    0  1.0D+00  6.6D-02  5.016D-02 -1.087D+00
    ...
    9   15     1     0  con    0  1.0D+00  1.2D-02  7.569D-04 -1.152D+00
```

### 7.6 关于收敛的更多说明（官方，重要）

- 几何与晶胞优化通常试图降低能量，**但收敛由激活的受力、位移、压力判据决定，而非仅由总能量决定**。
- **中间步骤有时能量会升高。若所有激活的收敛判据都满足，最后一步出现极小的能量升高通常是可接受的。**
- **但在某些情况下，这可能意味着该结构不是真正的极小值；可通过振动分析检查，虚频揭示不稳定模式。**
- 一般来说，常规收敛判据可在**几十到几百次迭代**内满足。**默认 `MAX_ITER = 200` 大多足够，对困难情形（如大规模柔性结构）可提到约 300 ~ 400。**
- **时间成本估计**：先跑一次 `RUN_TYPE ENERGY_FORCE` 单点计算，将耗时乘以预期迭代数。
- **长时间优化监控建议**：**不要只盯着数值判据**；应下载几何（轨迹）文件，在可视化程序中偶尔观察结构与晶胞的演化，**一旦出问题及时终止程序**。

---

## 8. 约束、晶胞自由度与对称性（官方）

### 8.1 原子约束

定义于 `MOTION/CONSTRAINT`。常见例子是 `FIXED_ATOMS`，可固定选定的原子或笛卡尔分量：

```
&MOTION
  &CONSTRAINT
    &FIXED_ATOMS
      COMPONENTS_TO_FIX XYZ
      LIST 1 2 3
    &END FIXED_ATOMS
  &END CONSTRAINT
&END MOTION
```

- `COMPONENTS_TO_FIX` 选择要约束的笛卡尔分量；`LIST` 包含原子索引，**顺序与 `COORD` 中一致**。
- 用途举例：**固定板层底层、固定支撑结构的一部分，或施加化学上有意的限制**。

> **警告（官方）**：生产计算前务必检查约束——**意外的约束是"看起来已收敛但物理上错误"的常见原因**。例如**表面或微孔吸附（物理/化学吸附）模型中，基底应允许局部弛豫，而不是完全固定**，以反映基底（吸附剂）与吸附质之间真实的相互作用。

### 8.2 `CELL_OPT` 的晶胞自由度（官方）

| 关键字 | 官方作用 |
|---|---|
| `CONSTRAINT` | 固定选定的晶胞分量 |
| `KEEP_ANGLES` | 保持晶胞角不变 |
| `KEEP_VOLUME` | 固定体积的晶胞形状弛豫 |
| `KEEP_SYMMETRY` 或 `KEEP_SPACE_GROUP` | 对称性约束的晶胞优化 |

**对表面或层状系统，通常更好的做法是只弛豫物理上有意义的晶胞方向，而非让整个晶胞变化。**

### 8.3 对称性约束（官方）

- **只有在已知目标极小值确实保持该对称性时才应使用对称性约束**；否则会阻止结构弛豫到更低对称性的极小值。
- 周期性固定晶胞 `GEO_OPT` 参见 `GEO_OPT/KEEP_SPACE_GROUP` 及相关对称性关键字。

### 8.4 关于 `KEEP_SYMMETRY` 的注意（官方 Note）

- **`KEEP_SYMMETRY` 应始终与 `FORCE_EVAL/SUBSYS/CELL/SYMMETRY` 指定的晶胞对称性一起使用。**
- 这些关键字**只作用于变胞优化中的晶胞矢量及其梯度**；并且二者都**假定采用"A 沿 X 轴、B 在 XY 平面"的常规晶胞**。
- **为使用 `KEEP_SPACE_GROUP`，需要安装 `spglib` 库并链接到 CP2K 构建**，以检测并保持空间群。**通常 `KEEP_SPACE_GROUP` 与 `KEEP_SYMMETRY` 搭配使用。**

---

## 9. 优化中的电子结构设置（官方）

### 9.1 SCF 质量

- 每个优化步都需要一次电子结构计算，**力的质量取决于 SCF 收敛、网格设置、基组、赝势以及方法相关的阈值**。对 `CELL_OPT`，**应力张量与压力也必须足够精确**，以便可靠地更新晶胞。
- **不要混淆**：**每次迭代的 SCF 收敛 ≠ 优化过程中跨迭代的几何收敛**（步长、梯度、压力）。
- 优化由受力驱动，`CELL_OPT` 还额外由应力驱动，**而非仅由总能量驱动**。因此，**仅从最终静态能量测试来调整设置和参数可能不够**。
- **这些设置通常至少要**与**常规单点能量计算一样严格，且常常更严格**——因为噪声大或收敛不佳的受力与应力会拖慢优化、引起振荡、导致线搜索失败，或得到不可靠的结构/晶胞。
- 重要的 Quickstep 设置：**`CUTOFF`、`REL_CUTOFF`、`EPS_DEFAULT`、`EPS_SCF`**。

#### 关于网格的注意（官方，重要）

- **平面波与实空间网格的网格间距由 `CUTOFF` 设置和晶胞尺寸共同决定。**
- **变胞优化可能出现显著的晶胞变化，这会影响网格点数，并给能量、力、应力及其他性质引入人为的不连续，即使结构变化很小。**
- **为更好稳定性，建议在 `FORCE_EVAL/SUBSYS/CELL/CELL_REF` 中设置一个参考晶胞，其尺寸大于整个变胞优化过程中预期达到的上界，并保持其恒定**，从而使网格点数固定、能量变化更平滑。

### 9.2 外推（Extrapolation，官方）

- 相邻优化步通常彼此接近，因此**外推电子初始猜测可大幅减少 SCF 迭代次数**。相关关键字：`EXTRAPOLATION` 与 `EXTRAPOLATION_ORDER`。
- **`GEXT_PROJ` 适用时通常是首选**；**`ASPC` 也是强烈推荐、稳健的通用选项**。其它高阶方案如 `PS` 与 `GEXT_PROJ_QTR` 也值得考虑。
- 更简单的上一步猜测，尤其是 **`USE_PREV_WF`**，是偏好更保守初始猜测时的可靠后备；**需要全新初始猜测时可用 `USE_GUESS`**。
- **基于密度矩阵的猜测（如 `USE_PREV_P` 与 `LINEAR_P`）需要特别小心**，尤其当晶胞或近邻表变化时。**这对 `CELL_OPT` 尤其相关**，但在固定晶胞工作流中（重启后或大几何变化后）也可能出现。CP2K 可能打印类似警告：

```
*** WARNING in qs_wf_history_methods.F:849 :: Change in cell ***
*** neighborlist: might affect quality of initial guess      ***
```

> **官方指引**：这表示先前的密度矩阵可能无法提供高质量初始猜测。**若该警告与几何、晶胞、总能量、受力、应力或 SCF 行为的异常变化同时出现，应停止使用该基于密度矩阵的方法，改用更安全的替代方案。**

**关于外推适用版本的注意（官方）**：
- 外推方案的适用性**取决于版本**。例如，外推以前仅适用于 gamma-only 计算，**而 CP2K 最新版本已开始支持带完整 k 点采样的外推**。
- **然而，当 k 点被要求按对称性约化时，随几何更新而动态刷新 k 点对称性，可能使外推不可用并自动回退到 `USE_GUESS`。**

### 9.3 危险提示（官方原文）

> **Danger**：**要负责任，不要盲目忽略 SCF 收敛失败。**

- SCF 收敛的一般问题见 `03_scf_convergence.md`。
- **糟糕的 SCF 收敛会导致当前步的能量、受力、应力不可靠，从而给更新后的结构以及下一步外推的波函数引入误差。**
- **若优化过程中大多数或全部步骤的 SCF 循环都未能收敛，最终结果不可信。若忽视收敛失败，结构"爆炸（blowing up）"之类的异常行为就不应令人意外。**
- **一开始就准备好良好的起始结构，比用粗糙结构并指望随优化推进 SCF 循环变容易要可靠得多。** 可用起始结构的单点能量计算来试验能达成收敛的选项，并评估耗时。

---

## 10. 输出文件与重启（官方）

主输出文件包含优化进程与收敛检查。几何文件与重启文件按全局 `PROJECT_NAME`（或 `PROJECT`）以及 `MOTION/PRINT` 下的相关 printkey 命名。

| 文件 | 内容 | 控制关键字 |
|---|---|---|
| `project-pos-1.xyz` | 优化过程中访问过的几何序列 | `MOTION/PRINT/TRAJECTORY`（默认格式 XYZ 或 XMOL） |
| `project-FINAL-1_{iter}.cif` / `.xyz` | 最终结构的 CIF 与扩展 XYZ；`{iter}` 为达到收敛或触达 `MAX_ITER` 时的迭代数 | `MOTION/PRINT/FINAL_STRUCTURE` |
| `project-1.cell` | 优化过程中的晶胞矢量 | `MOTION/PRINT/CELL` |
| `project-1.stress` | 优化过程中的应力张量 | `MOTION/PRINT/STRESS` |
| `project-1.restart` | CP2K 重启输入，含最新几何、晶胞及相关设置 | `MOTION/PRINT/RESTART` |

> **关于 `project-pos-1.xyz` 的警示（官方）**：**原始 XYZ 规范不携带周期性**，且**并非所有可视化程序都能解析 XYZ 注释行中附加的晶胞信息**（如扩展 XYZ 规范）；**可能需要用 `FORMAT` 关键字切换到其它格式以便可视化**。

**关于备份**：当 `RESTART` 下的 `BACKUP_COPIES` 非零时，之前优化步的备份重启文件也会保留为 `project-1.restart.bak-*`。

### 10.1 直接重启（官方）

重启文件可直接作为新输入文件使用：

```
cp2k -i project-1.restart -o project-restart.out
```

- 也可使用 `EXT_RESTART` 段进行更精细的重启控制。
- **当优化未收敛、需要从最新结构开始新优化时，这些都很方便。**

### 10.2 波函数与 Hessian 重启

- 对昂贵的电子结构计算，波函数重启文件可降低续算或后续计算成本；参见 `07_restarting.md` 与 `FORCE_EVAL/DFT/SCF/PRINT/RESTART`。
- **对 BFGS 优化，活动优化驱动程序（driver）的 `BFGS` 子节提供 Hessian 重启选项。**

---

## 11. 官方实用检查清单（信任优化结果之前）

- [ ] 所有激活的受力与位移收敛判据均已满足；
- [ ] 对 `CELL_OPT`，压力判据已满足，且最终晶胞物理上合理；
- [ ] 优化后的晶胞与预期问题相符：`GEO_OPT` 用固定晶胞、`CELL_OPT` 用弛豫晶胞，并在需要处施加约束方向；
- [ ] **没有意外激活的约束、固定原子、晶胞约束或对称性限制**；
- [ ] 最后若干优化步的 SCF 过程可靠收敛；
- [ ] 最终结构与晶胞被一致地复用于后续计算。

---

## 12. 官方关键字与取值汇总表

| 关键字 / 选项 | 所属 | 取值 / 说明 |
|---|---|---|
| `RUN_TYPE` | `GLOBAL` | `GEO_OPT`（固定晶胞）、`CELL_OPT`（变胞）；另提及 `ENERGY_FORCE`（单点，用于预估时间） |
| `OPTIMIZER` | `GEO_OPT` / `CELL_OPT` | `BFGS`（默认）、`LBFGS`、`CG` |
| `TYPE` | `GEO_OPT` | `MINIMIZATION`（默认常规选择）、`TRANSITION_STATE`（需额外设置） |
| `MAX_ITER` | `GEO_OPT` / `CELL_OPT` | 示例 200；**默认 200 大多足够；困难情形可 300~400** |
| `MAX_DR` | `GEO_OPT` / `CELL_OPT` | 示例 `3.0E-03` Bohr |
| `RMS_DR` | `GEO_OPT` / `CELL_OPT` | 示例 `1.5E-03` Bohr |
| `MAX_FORCE` | `GEO_OPT` / `CELL_OPT` | 示例 `4.5E-04` Hartree/Bohr |
| `RMS_FORCE` | `GEO_OPT` / `CELL_OPT` | 示例 `3.0E-04` Hartree/Bohr |
| `EXTERNAL_PRESSURE` | `CELL_OPT` | 示例 `1.01325E+00` bar；**应显式设置，勿依赖默认** |
| `PRESSURE_TOLERANCE` | `CELL_OPT` | 示例 `100.0` bar |
| `STRESS_TENSOR` | `FORCE_EVAL` | 示例 `ANALYTICAL` |
| `TRUST_RADIUS` | `BFGS` / `LBFGS` 子节 | 优化不稳定时**首先减小**；过小则收敛慢 |
| `USE_MODEL_HESSIAN` | `BFGS` 子节 | 开启**常可减少迭代次数** |
| `CG/LINE_SEARCH/TYPE` | `CG` 子节 | `2PNT`（最便宜）、`GOLD`（更稳健、更安全默认）、`FIT`（最稳健也最贵） |
| `MAX_ALLOWED_STEP` | `LINE_SEARCH/2PNT` | 限制最大线搜索步长 |
| `INITIAL_STEP` | `LINE_SEARCH/GOLD` | 初始 bracketing 步长；近距接触/早期不稳定时可减小 |
| `WANTED_PROJ_GRADIENT` | `LBFGS` | LBFGS 专属判据之一 |
| `WANTED_REL_F_ERROR` | `LBFGS` | LBFGS 专属判据之一 |
| `PRINT_LEVEL` | `LBFGS` | 控制主输出详细程度 |
| `MAX_FORCE` | `FORCE_EVAL/RESCALE_FORCES` | 触发超大受力人为缩放；**仅**用于粗糙初始结构 |
| `WALLTIME` | `GLOBAL` | 达到墙钟时间会终止优化 |
| `EXIT` / `EXIT_GEO` | 工作目录文件 | 用户紧急终止标志 |
| `FIXED_ATOMS`、`COMPONENTS_TO_FIX`、`LIST` | `MOTION/CONSTRAINT` | 原子约束；`LIST` 索引顺序同 `COORD` |
| `CONSTRAINT`、`KEEP_ANGLES`、`KEEP_VOLUME`、`KEEP_SYMMETRY`、`KEEP_SPACE_GROUP` | `CELL_OPT` | 晶胞自由度控制 |
| `KEEP_SPACE_GROUP` | `GEO_OPT` | 周期性固定晶胞优化中的空间群保持 |
| `SYMMETRY` | `FORCE_EVAL/SUBSYS/CELL` | 与 `KEEP_SYMMETRY` 配合使用 |
| `spglib` | 外部库 | 使用 `KEEP_SPACE_GROUP` 需安装并链接 |
| `CUTOFF`、`REL_CUTOFF`、`EPS_DEFAULT`、`EPS_SCF` | `FORCE_EVAL/DFT/...` | **优化时通常需比单点更严格** |
| `CELL_REF` | `FORCE_EVAL/SUBSYS/CELL` | 变胞优化中固定网格点数的参考晶胞 |
| `EXTRAPOLATION`、`EXTRAPOLATION_ORDER` | `FORCE_EVAL/DFT/QS` | `GEXT_PROJ`、`ASPC`、`PS`、`GEXT_PROJ_QTR`、`USE_PREV_WF`、`USE_GUESS`、`USE_PREV_P`、`LINEAR_P` |
| `PRINT/STRESS_TENSOR` | `FORCE_EVAL` | 用于确认解析/数值应力 |
| `PROGRAM_RUN_INFO` | `GEO_OPT/PRINT`、`CELL_OPT/PRINT` | 控制收敛报告输出 |
| `TRAJECTORY`、`FINAL_STRUCTURE`、`CELL`、`STRESS`、`RESTART` | `MOTION/PRINT` | 输出文件控制 |
| `BACKUP_COPIES` | `MOTION/PRINT/RESTART` | 非零时保留 `project-1.restart.bak-*` |
| `EXT_RESTART` | 顶级 | 更精细的重启控制 |
| `RESTART` | `FORCE_EVAL/DFT/SCF/PRINT` | 波函数重启 |

> **官方本页未给出的项（避免误引）**：`OPT_TYPE`、`MAX_STEP`（仅在报告中以自然语言出现，对应关键字为 `MAX_DR`）、`DIIS`、`DIRECT_CELL_OPT` 及 `CELL_OPT/TYPE` 的取值枚举、`TRANSITION_STATE` 的具体子关键字与推荐值、以及除 `BFGS`（默认优化器）和 `MAX_ITER`（默认 200）之外的**各类关键字官方默认值**。

---

## 13. NEB（官方占位页）

> 来源：<https://manual.cp2k.org/trunk/methods/optimization/nudged_elastic_band.html>

官方本页**无正文**：

> Unfortunately, nobody has gotten around to writing this page yet :-(

官方给出的外链（**这是官方对 NEB 学习的唯一指引**）：

- <https://www.cp2k.org/exercises:common:neb>
- <https://www.cp2k.org/exercises:2018_uzh_cmest:path_optimization_neb>
- <https://www.cp2k.org/exercises:2017_ethz_mmm:nudged_elastic_band>
- <https://www.cp2k.org/exercises:2015_cecam_tutorial:neb>

**G 层不编造 NEB 内容。** NEB 的输入关键字（`&MOTION/&BAND`、`NUMBER_OF_REPLICA`、`K_SPRING`、`OPTIMIZE_BAND`、CI-NEB/D-NEB 等）应查官方 Input Reference；实操流程与踩坑见 A 层 `decide.md`、F 层 `playbook.md`。

**官方功能清单中对 NEB 的表述**（见 `10_features_resources.md`）：**NEB 四算法 B-NEB / IT-NEB / CI-NEB / D-NEB**。

**官方 changelog 中 NEB 相关变更**：
- **2026.2**：新增 **NEB 输出**，含相对能量图与最终结构（#5382）。

---

## 14. 交叉索引

| 主题 | G 层 | A/F 层 |
|---|---|---|
| 收敛判据数值 | 本文 §7.1、§12 | A `decide.md`；F `playbook.md` §0 |
| `MAX_ITER` 取值 | 本文 §7.6 | A；F |
| 优化不稳定的排查顺序 | 本文 §6.5 | F §1 |
| `CELL_REF` 与网格不连续 | 本文 §9.1 | F §1 |
| 外推选择 | 本文 §9.2；`04` §11 | A；F |
| 约束的隐藏陷阱（吸附模型） | 本文 §8.1 | A；F §4 |
| 优化重启 | 本文 §10；`07_restarting.md` | F §2 |
| NEB | 本文 §13（占位，仅有外链） | **A 层是 NEB 的主要来源**；F 层 |
