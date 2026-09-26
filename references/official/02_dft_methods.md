# 02 · DFT 方法论（官方）

> **来源**：
> - <https://www.cp2k.org/quickstep>
> - <https://www.cp2k.org/features>
> - <https://manual.cp2k.org/trunk/methods/dft/index.html>
> - <https://manual.cp2k.org/trunk/methods/dft/gpw.html>
> - <https://manual.cp2k.org/trunk/methods/dft/gapw.html>
> - <https://manual.cp2k.org/trunk/methods/dft/pseudopotentials.html>
> - <https://manual.cp2k.org/trunk/methods/dft/orbital_transformation.html>
> - <https://manual.cp2k.org/trunk/methods/dft/k-points.html>
> - <https://manual.cp2k.org/trunk/methods/dft/local_ri.html>
> - <https://manual.cp2k.org/trunk/methods/dft/hartree-fock/index.html>
> - <https://manual.cp2k.org/trunk/methods/dft/hartree-fock/admm.html>
> - <https://manual.cp2k.org/trunk/methods/dft/constrained.html>
> - <https://manual.cp2k.org/trunk/methods/dft/linear_scaling.html>（占位页）
> - <https://www.cp2k.org/howto:dft_u>
> **抓取日期**：2026-09-08

---

## 1. Quickstep 与 GPW/GAPW 原理

### 1.1 GPW（Gaussian Plane Wave）

官方描述（`methods/dft/gpw.html`）：

- CP2K 的**主基组**由 Gaussian Type Orbital（GTO）函数构成。
- 为利用高效的 FFT 算法求解 Poisson 方程，电子密度必须先从 GTO 表示**转移到规则网格**，这一步称为 **collocation**。
- 求解 Poisson 方程后，得到的静电势必须**转回 GTO 基组**，这一步称为 **integration**。
- 这种在 Gaussian 与 plane wave 表示之间**"机会主义"地切换**，是 **Gaussian and Plane Waves (GPW)** 方法的核心思想。

官方关联页面：`www.cp2k.org/gpw`、`www.cp2k.org/quickstep`；参考文献 Kühne2020。

### 1.2 GAPW（Gaussian Augmented Plane Waves）

官方描述（`methods/dft/gapw.html`）：

- GAPW **扩展了 GPW**，使**全电子计算**和使用**非常小芯赝势**的计算在 CP2K 中变得可行。
- 核心思想：把密度的**平滑部分**留在常规 GPW 网格上，而把**核附近快速变化的密度**用**原子中心贡献**处理。

**适用场景（官方原文）**：
- 全电子计算（all-electron calculations）
- 芯能级光谱（core-level spectroscopy）
- 磁性质（magnetic properties）
- 某些小芯赝势设置（some small-core pseudopotential setups）

**官方明确结论**：对**标准仅价电子赝势 DFT 计算，GPW 通常更简单更快**。

**激活方式**：

```
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    &QS
      METHOD GAPW
    &END QS
  &END DFT
&END FORCE_EVAL
```

全电子 GAPW 还需要全电子基组与 `POTENTIAL ALL`：

```
&KIND O
  BASIS_SET SVP-MOLOPT-GGA-ae
  POTENTIAL ALL
  LEBEDEV_GRID 110
  RADIAL_GRID 80
&END KIND
```

官方提供一个完整测试过的水分子示例：`gapw_h2o.inp`（官方说明：**故意做得很小，只作为起点，不是生产级基准**）。

**GAPW 精度参数（官方）**：

| 关键字 | 官方描述 |
|---|---|
| `EPSFIT` | 控制高斯指数如何拆分为 hard 与 soft 部分。**降低它会将更硬的函数纳入 soft density，通常需要更大的 `CUTOFF`** |
| `EPSRHO0` | 控制 hard compensation density 贡献所用的范围 |
| `EPSSVD` | 控制 projector matrices 的奇异值分解容差 |
| `LEBEDEV_GRID` / `RADIAL_GRID` | **按 kind 设置**原子中心积分网格。提高这些值可改善电子计数和依赖近核密度的性质精度，但**也增加成本** |

**官方实践指引**：
- 为 `POTENTIAL ALL` 使用全电子基组，或为所选小芯赝势使用专门设计的基组。
- **检查 SCF 收敛后 CP2K 打印的电子计数**——它是 hard/soft density 拆分质量的有用诊断。
- `EPSFIT`、`EPSRHO0`、`EPSSVD` 与原子网格**只按目标性质所需的程度收紧**。
- 当更硬的高斯指数被纳入 soft density 时，**提高 `CUTOFF`**。
- **不需要全电子或近核精度时优先用 GPW**。

参考文献：Lippert1999、Krack2000、Iannuzzi2026。

### 1.3 DFT 章节导航（官方 `methods/dft/index.html`）

官方 DFT 章节包含以下子页：

`gpw` / `gapw` / `hartree-fock`（含 `admm`、`ri_gamma`、`ri_kpoints`）/ `pseudopotentials` / `k-points` / `orbital_transformation` / `convergence` / `cutoff` / `local_ri` / `constrained` / `cneo` / `linear_scaling` / `gauxc`

---

## 2. 赝势（Pseudopotentials）

> 来源：<https://manual.cp2k.org/trunk/methods/dft/pseudopotentials.html>

### 2.1 基本概念（官方）

- 大多数 GPW 计算使用**模守恒 Goedecker-Teter-Hutter（GTH）赝势**。
- 赝势把化学上不活跃的芯电子从显式电子问题中移除，通过有效势表示它们对价电子的影响。这**减少了电子数**，并**避免了否则需要极细网格的极硬芯密度**。

### 2.2 输入写法（官方示例）

```
&FORCE_EVAL
  &DFT
    POTENTIAL_FILE_NAME GTH_POTENTIALS
  &END DFT
  &SUBSYS
    &KIND O
      POTENTIAL GTH-PBE-q6
    &END KIND
    &KIND H
      POTENTIAL GTH-PBE-q1
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

**官方重要提醒**：不要把 `POTENTIAL` **关键字**与同名的 `POTENTIAL` **段**混淆。
- 关键字：取势的类型与名称；
- 段：取内部格式的完整规范与数据。
- **仅指定关键字就足以应付大多数实际使用**（官方原文）。

### 2.3 后缀含义与配套基组（官方）

- `GTH-PBE-q6` 中的后缀 `q6` 表示**有 6 个价电子被显式处理**。
- **所选基组应匹配这个价电子构型**；对氧，可用全名中带相同后缀的常见基组如 `DZVP-MOLOPT-GTH-q6`。
- 若在内置数据文件中发现某些赝势没有对应基组、或反之，**请咨询开发者**。

### 2.4 如何选择赝势（官方）

1. **使用与计算所用交换-相关泛函族相匹配的赝势**。例如 `GTH-PBE-q6` 是氧的 PBE 计算的天然选择。
2. 混合泛函族在某些探索性工作中可以接受，但**不是通向高精度的系统性路线**（官方原文）。

**CP2K 数据目录中的赝势库（官方列表）**：

| 库 | 官方说明 |
|---|---|
| `GTH_POTENTIALS` | 含广泛使用的 GTH 势，用于常见 GPW 计算 |
| `POTENTIAL_UZH` | 含 **UZH 协议** GTH 势，设计为与匹配的 UZH 基组一起使用 |
| `NLCC_POTENTIALS`、`GTH_SOC_POTENTIALS` | 含更专用的势 |
| `ECP_POTENTIALS` | 含用于高斯积分计算的**有效芯势** |

**官方推荐**：
> For new GPW production inputs, **prefer a matching UZH protocol pair from `POTENTIAL_UZH` and `BASIS_MOLOPT_UZH`** when it is available for the element and functional family. The older `GTH_POTENTIALS` library remains important for **reproducing established calculations** and for cases where a matching UZH setup is not available.

**全电子计算**：

```
&KIND O
  BASIS_SET SVP-MOLOPT-GGA-ae
  POTENTIAL ALL
&END KIND
```

需配合**全电子基组**与 **GAPW 方法**。

### 2.5 官方一致性检查清单

- 基组与赝势应能在 `DFT` 段中指定的文件里找到；
- 赝势的价电荷应与基组后缀匹配（当使用后缀时）；
- 交换-相关泛函应与赝势族一致；
- 对重元素，要决定**大芯 / 中芯 / 小芯 / 全电子**描述哪一种适合目标性质。

### 2.6 官方参考链接

- <https://en.wikipedia.org/wiki/Pseudopotential>
- <https://cp2k.org/static/potentials/>
- <https://www.cp2k.org/tools:cp2k-basis>
- 文献：Goedecker1996、Hartwigsen1998、Krack2005、Iannuzzi2026

---

## 3. 轨道变换 OT（Orbital Transformation）

> 来源：<https://manual.cp2k.org/trunk/methods/dft/orbital_transformation.html>

### 3.1 两个不同的 OT（官方强调的关键区分）

官方明确指出**两个输入段暴露相关但不同的算法**：

| 输入段 | 性质 | 官方描述 |
|---|---|---|
| `&SCF%OT` | **直接 SCF 方法** | 轨道、以及（被请求时）它们的旋转和辅助能量是优化变量 |
| `&SCF%DIAGONALIZATION%OT` | **固定 Kohn–Sham 矩阵的迭代本征求解器** | 外围对角化 SCF 路径负责分配占据、构造密度、执行密度混合 |

> 官方原文：The distinction is important for metallic calculations because **only direct OT needs explicit rotation and auxiliary-energy variables**.

### 3.2 固定占据的常规直接 OT（官方示例）

```
&SCF
  &OT
    ALGORITHM STRICT
    MINIMIZER CG
    PRECONDITIONER FULL_SINGLE_INVERSE
  &END OT
&END SCF
```

官方说明：
- `STRICT` 是**默认算法**；`CG` 是**默认、通常稳健的 minimizer**。
- **preconditioner 控制轨道部分的优化**。其适用性与成本取决于体系、基组和电子结构方法；**因此应针对目标计算测试，而不是仅根据名义上的层级来选**（官方原文）。

**k 点支持（官方）**：
- 同一直接 OT 公式支持**复数、带权重的 k 点集**，包括对称约化的网格。
- 官方要求：**对每个目标性质收敛 k 点网格**，并**用等效的完整网格验证实验性的原子对称约化**。

### 3.3 分数占据与金属（官方示例）

在有限电子温度下，直接 OT 最小化**固定电子数的自由能泛函**。它优化轨道子空间，同时优化该子空间内的旋转和决定占据的辅助轨道能量。

```
&SCF
  ADDED_MOS AUTO
  &SMEAR ON
    METHOD FERMI_DIRAC
    ELECTRONIC_TEMPERATURE 500
  &END SMEAR
  &OT
    ALGORITHM STRICT
    MINIMIZER CG
    PRECONDITIONER FULL_ALL
    ROTATION
    ENERGIES
    OCCUPATION_PRECONDITIONER
  &END OT
&END SCF
```

**关键字语义（官方）**：

| 关键字 | 官方说明 |
|---|---|
| `ROTATION` | 使**占据列旋转**变分。**当能量在该类旋转下不变时必需，包括分数占据的情形** |
| `ENERGIES` | 添加**辅助能量变量**，以便与自由能泛函一致地优化占据。**带 smearing 的直接 OT 应同时使用 `ROTATION` 与 `ENERGIES`** |
| `OCCUPATION_PRECONDITIONER` | 在轨道度规上增补耦合的、固定电子数的占据响应。**它是可选的，并且是与独立选择的 `PRECONDITIONER` 组合使用，而不是替代它**。可改善困难的金属响应模式，但其对收敛的影响**仍取决于体系** |

### 3.4 虚态缓冲（Virtual-state buffer）

官方说明：
- **Smearing 需要足够的虚态来容纳部分占据的尾部。**
- 固定的正整数 `ADDED_MOS` 值：每自旋通道增加那么多状态；
- `ADDED_MOS -1`：请求原子轨道基组中所有可用状态；
- `ADDED_MOS AUTO`：为有限温度 k 点 OT 选择初始缓冲，并在**最高可用能带仍有明显占据时增长它**。**若原子轨道基组耗尽，它会带诊断信息停止。**

> 官方警告：`AUTO` 消除了大部分手动试错，**但它无法创造基组之外的状态**。因此关于最高能带占据的警告，需要检查基组、电子温度或 smearing 宽度、以及物理电子数，**而不是仅仅无限增加一个任意整数**。

### 3.5 Smearing 分布（官方）

直接有限温度 OT 支持：`FERMI_DIRAC`、`GAUSSIAN`、`METHFESSEL_PAXTON`、`MARZARI_VANDERBILT`。

- `FERMI_DIRAC` 有**直接的热力学解释**：被优化的量是**固定电子数下的 Helmholtz 自由能**，用一个共同的化学势来在所有自旋与 k 点通道上强制该电子数。
- 对其它分布，CP2K 使用它们对应的**广义自由能校正**。应遵循 `&SMEAR` 中关于**力与应力**的解释与外推指引。

**k 点与 Gamma-only（官方）**：
- 省略 `&KPOINTS` 使用**天然的 Gamma-only 实现**。
- 一般的 k 点网格使用**复轨道**与**归一化的不可约点权重**。
- **两种情况下，决定收敛的都是所报告的自由能目标，而不是仅未校正的势能。**

### 3.6 OT 作为迭代本征求解器（官方示例）

```
&SCF
  ADDED_MOS AUTO
  &SMEAR ON
    METHOD FERMI_DIRAC
    ELECTRONIC_TEMPERATURE 500
  &END SMEAR
  &DIAGONALIZATION ON
    ALGORITHM OT
    &OT
      ALGORITHM STRICT
      MINIMIZER CG
      PRECONDITIONER FULL_ALL
    &END OT
  &END DIAGONALIZATION
  &MIXING
    METHOD BROYDEN_MIXING
  &END MIXING
&END SCF
```

官方说明：
- 这里 OT **只求解固定哈密顿量的本征空间问题**。父 SCF 驱动器对该本征空间做规范化、分配占据、构造密度、并应用所选密度混合。
- **因此 `DIAGONALIZATION%OT` 不使用 `ROTATION`、`ENERGIES`、`OCCUPATION_PRECONDITIONER` 或 `NONDIAG_ENERGY`；设置它们不会使它们变成额外的本征求解器变量。**
- 当**稳健的密度混合比避免所有对角化式的外层迭代更重要**时，这条路径有用。
- **即使两个计算使用相同的内部 OT 算法、minimizer 和 preconditioner，它在数学上也与同时进行的直接 OT 不完全相同。**

### 3.7 官方"新金属计算"实用检查（5 条）

1. **为目标性质收敛基组、cutoff、k 点网格与 smearing 参数。**
2. **确认第一和最高可用能带没有携带意外的部分占据。**
3. **在不同 MPI 布局之间比较自由能、电子数、化学势与自旋矩。**
4. **至少用一个代表性结果与常规对角化加密度混合比较。**
5. **把步数当作性能指标，而不是两个方法找到同一电子态的证据。**

> 官方总结：自由能、熵贡献与外推能量服务于不同目的。**smearing 下的力与应力是所记录的自由能泛函的导数；在验证有限差分或比较结构时，应使用匹配的量。**

---

## 4. k 点采样（K-Points）

> 来源：<https://manual.cp2k.org/trunk/methods/dft/k-points.html>

### 4.1 为什么需要 k 点（官方）

- 对周期体系，Bloch 定理用倒空间中的晶体动量 k 标记单电子态。电子密度、总能量、占据等量都包含对布里渊区的积分。
- CP2K 用**有限个 k 点的加权求和**替代该积分，其中 w_k 是归一化的 k 点权重。
- **Gamma-only 计算只采样 k=0**。它通常适合**孤立体系、大超胞、或布里渊区足够小的其它情形**。**更小的原胞、金属、以及能带强色散的体系通常需要收敛的 k 点网格。**

### 4.2 `&KPOINTS` 段的性质（官方强调）

- `&KPOINTS` 描述的是**SCF 计算期间所用的采样**，而**不是**通过选定高对称点的后处理路径。
- **省略 `&KPOINTS`** 给出常规的 Gamma-only 计算（`SCHEME NONE`）。
- **`SCHEME GAMMA`** 则显式创建一个 Gamma 处的一点 k 点集。**在多数情况下物理采样相同，但两个输入使用不同的实现路径。**
- **复波函数是 k 点计算的默认**；实波函数仅对 Gamma 和 Bloch 相位可表示为实数的特殊 k 点有效。**一般网格或原子 k 点对称约化必须使用复波函数。**

### 4.3 功能兼容性表（官方，重要）

| 功能 | 兼容性与限制 |
|---|---|
| 标准对角化 | **Supported.** |
| 轨道变换（OT） | **Supported.** 见 Orbital Transformation |
| 原子对称约化 | **Experimental.** 必须用等效的未约化计算验证 |
| WFN 外推 | **Supported.** |
| 其它对角化方法 | **Unsupported.** No k-point path available. |
| 杂化泛函 | **Supported via RI-HFXk.** |
| DFT+U | **Limited.** Mulliken populations only. |
| SCCS | **Not validated.** Use with caution. |
| 约束 DFT（CDFT） | **Unsupported.** No k-point path available. |
| TDDFPT | **Limited.** Independent-particle response only（`KERNEL NONE`） |
| XAS 与 RIXS | **Unsupported.** No k-point path available. |
| 线性响应 / DFPT | **Unsupported.** No k-point path available. |
| GW | **Support with separate workflow.** Does not rely on `DFT%KPOINTS`. |
| 周期性电场 | **Unsupported.** Requires OT first. |
| 活性空间计算 | **Unsupported.** Only `SCHEME NONE` and `SCHEME GAMMA` available. |

**官方对"为什么不支持"的解释**（原文要点）：
- 可能是 CP2K 代码实现尚不存在、不完整或未验证；
- **也可能是底层理论与算法本身还没有更新到 k 点版本**（相对于孤立、非周期形式化）。
- 后者情况下，给现有方法做新颖的 k 点推广**值得发表学术论文，需要认真的合作与投入**。因此官方**强烈建议**在提出此类功能请求时，**提供其它软件中 k 点形式化的参考实现**。

> 官方警告：**一次成功的计算本身并不能证明某个功能–k 点组合对特定体系或性质是可靠的。** 对新工作流，应**收敛 k 点网格**，并在适当处**与等效的实空间超胞计算比较**。

### 4.4 选择与收敛网格（官方）

- 经验规则可提供有用起点，但**可靠结果需要针对具体体系与性质收敛 k 点网格**。
- **总能量、力、应力、金属占据、态密度、带边可能以不同速率收敛。** 应**增加网格密度直到相关量不再以所需精度变化**。
- **对 slab、wires 等低维体系，只采样周期性方向，非周期或真空方向通常用 1 个 k 点。**
- **扩大实空间超胞会缩小布里渊区，可降低所需 k 点密度，但本身并不能消除有限尺寸效应。**

> **Important**（官方）：**Electronic smearing and DOS broadening do not replace k-point convergence.** In particular, a smooth DOS obtained from a sparse mesh may still be physically unconverged.

- **常规能带结构**：先在适当的积分网格上收敛 SCF，然后用 `&BAND_STRUCTURE` 和 `&KPOINT_SET` 定义路径。

### 4.5 采样方案（官方）

`SCHEME` 选择方案。**规则网格默认按完整网格求值：只有在显式启用 `SYMMETRY` 时才请求原子对称约化。**

#### Gamma-only

省略 `&KPOINTS` 即为常规 Gamma-only：

```
&DFT
  ...
&END DFT
```

需要 k 点计算路径时，可显式请求 Gamma 点集：

```
&DFT
  &KPOINTS
    SCHEME GAMMA
  &END KPOINTS
&END DFT
```

#### Monkhorst–Pack

```
&DFT
  &KPOINTS
    SCHEME MONKHORST-PACK 6 6 6
  &END KPOINTS
&END DFT
```

三个整数指定沿倒格矢的网格维度。用 `GAMMA_CENTERED` 生成 Gamma 中心变体：

```
&KPOINTS
  SCHEME MONKHORST-PACK 6 6 6
  GAMMA_CENTERED T
&END KPOINTS
```

官方说明：Gamma centering 支持 Monkhorst–Pack 网格。**当使用偶数个细分且要求网格包含 Gamma 点时最有用。**

#### MacDonald

同时指定网格维度与显式位移：

```
&KPOINTS
  SCHEME MACDONALD 4 4 4 0.25 0.25 0.25
&END KPOINTS
```

前三个值定义网格维度，后三个定义位移。

#### 显式 k 点集

```
&KPOINTS
  SCHEME GENERAL
  KPOINT 0.0 0.0 0.0 1.0
  KPOINT 0.5 0.0 0.0 1.0
&END KPOINTS
```

- 每个 `KPOINT` 行含三个坐标与一个权重。**CP2K 内部会对提供的权重做归一化。**
- 默认 `UNITS` 为 `B_VECTOR`，即坐标以倒格矢坐标表示。也可用 `CART_BOHR` 或 `CART_ANGSTROM` 选笛卡尔坐标；其单位分别是 **2π/Bohr** 与 **2π/Å**。

> **Note**（官方）：`SCHEME GENERAL` 定义的是 **SCF 计算的积分集**，**不是**高对称能带路径的常用接口。后者用 `&DFT%PRINT%BAND_STRUCTURE`。

#### k 点并行

`PARALLEL_GROUP_SIZE` 控制 k 点计算中 MPI 进程如何分组。其值是**分配给一个 k 点组的 MPI 进程数**。
- **组大小必须整除总 MPI 进程数，且得到的组数必须整除 k 点个数。**
- 默认 `-1` 选择最小的有效每进程组大小；`0` 为每个 k 点使用所有进程；正值请求该确切组大小。
- **该设置是并行化选择，不改变物理 k 点网格。**

### 4.6 k 点对称约化（官方）

对规则 Monkhorst–Pack 与 MacDonald 网格，CP2K 区分**两级** k 点约化：

1. **k 空间反演（时间反演）约化**：配对 k 与 −k，**对规则网格默认使用**；
2. **原子（空间群）对称约化**：使用将当前周期结构映射到自身的额外操作。

`SYMMETRY` 关键字控制**第二级**。**它默认关闭；这并不禁用规则网格的默认时间反演约化。**

#### 时间反演约化

对规则 Monkhorst–Pack 或 MacDonald 网格，CP2K 通常合并反演相关的 k 与 −k 点。这是 `SYMMETRY F`（默认）与 `FULL_GRID F`（默认）同时使用时的标准约化路径：

```
&KPOINTS
  SCHEME MONKHORST-PACK 8 8 8
&END KPOINTS
```

也可用 `INVERSION_SYMMETRY_ONLY` 显式请求。**当共享输入模板中存在 `SYMMETRY T`、但只想要时间反演约化时有用**：

```
&KPOINTS
  SCHEME MONKHORST-PACK 8 8 8
  SYMMETRY T
  INVERSION_SYMMETRY_ONLY T
&END KPOINTS
```

`SCHEME GENERAL` 默认保留所提供列表。**当为显式列表请求仅反演约化时，每个 k/−k 对必须以相等权重出现。**

要显式计算规则网格的每个点，禁用原子对称并请求完整网格：

```
&KPOINTS
  SCHEME MONKHORST-PACK 8 8 8
  SYMMETRY F
  FULL_GRID T
&END KPOINTS
```

> **Note**（官方）：对 Monkhorst–Pack 与 MacDonald 网格，`FULL_GRID T` 与 `SYMMETRY T` 一起会**禁用原子对称约化但保留 k 空间反演（时间反演）约化**。要得到严格的完整网格参考计算，**同时使用 `SYMMETRY F` 与 `FULL_GRID T`**。

#### 原子（空间群）对称约化

> **Warning**（官方）：**Atomic k-point symmetry reduction is experimental.** 在生产使用前，**必须用等效的完整网格计算验证能量、力、应力及任何其它目标性质**。

用 `SYMMETRY T` 启用：

```
&KPOINTS
  SCHEME MONKHORST-PACK 8 8 8
  SYMMETRY T
  WAVEFUNCTIONS COMPLEX
&END KPOINTS
```

这会**结合默认的时间反演约化与额外的原子对称操作**。**对带非平凡 Bloch 相位的一般原子对称操作，需要复波函数。**

**兼容的采样集**：
- 原子对称约化适用于规则 Monkhorst–Pack 与 MacDonald 网格。
- 也可用于 `SCHEME GENERAL`，**前提是所有显式权重相等，且完整集合在每一个被请求的对称操作下闭合**。
- **非均匀的 `GENERAL` 列表（包括能带路径）应保持 `SYMMETRY F`。**

**晶胞要求**：
- 对规则 Monkhorst–Pack 与 MacDonald 网格，**完整原子约化目前要求晶胞矩阵采用 CP2K 标准的下三角约定**。
- 若对非正交晶胞或该约定之外的晶胞矩阵请求完整原子约化，**CP2K 会警告并回退到 `INVERSION_SYMMETRY_ONLY`**。
- **通过 `ABC` 与 `ALPHA_BETA_GAMMA` 定义晶胞，或读取合适的 CIF 结构，可让 CP2K 从与取向无关的晶格参数构造标准晶胞取向。**

**对称后端**：
- **K290 是既定的默认后端。**
- 可选的 `SPGLIB` 后端使用 spglib 返回的对称操作，包括分数平移：

```
&KPOINTS
  SCHEME MONKHORST-PACK 8 8 8
  SYMMETRY T
  SYMMETRY_BACKEND SPGLIB
  WAVEFUNCTIONS COMPLEX
&END KPOINTS
```

- 该选项**要求 CP2K 用 spglib 构建**。若指定了 `SYMMETRY_BACKEND` 而省略 `SYMMETRY_REDUCTION_METHOD`，约化方法会跟随所选后端。
- `SYMMETRY_REDUCTION_METHOD SPGLIB` 与 `SYMMETRY_BACKEND K290` 一起是**比较模式**：SPGLIB 提出 k 点轨道，K290 操作用于实际变换。**主要用于验证与开发，而非默认生产设置。**

**移动的几何**：
- 对 `GEO_OPT`、`CELL_OPT`、MD 及相关计算，CP2K **从当前晶胞与坐标确定原子 k 点对称性**，而不是假设初始操作仍然有效。
- **不可约 k 点集因此可能随几何演化而变化。**
- **`SCHEME GENERAL` 列表必须在每一步都保持对称闭合，否则被拒绝。**
- 当几何或晶胞优化意图保持完整空间群时，使用相关的 `KEEP_SPACE_GROUP` 设置。对 `CELL_OPT`，另见关于 `KEEP_SYMMETRY` 的讨论。

**验证与排查**：
- 对每个新体系或工作流，把原子对称约化计算与严格的完整网格参考比较：

```
&KPOINTS
  SCHEME MONKHORST-PACK 8 8 8
  SYMMETRY F
  FULL_GRID T
  WAVEFUNCTIONS COMPLEX
&END KPOINTS
```

- `&DFT%PRINT%KPOINTS` 打印 k 点信息，**用于检查生成的集合**。
- 进一步诊断：使用 `VERBOSE`，必要时调整 `EPS_SYMMETRY`。
- `DEBUG_FULL_KPOINT_SYMMETRY` 用于**专家级有限差分调试**。

### 4.7 相关输出与工作流（官方）

- **DOS/PDOS 通常需要比几何优化更密的网格。**
- **k 点 MO 输出**：`.mokp` 记录 k 点 MO 输出。**Molden 输出对 k 点计算不可用。**
- **HFX-RI with k-Points**：含能带结构示例。
- **Wannier90 接口**：experimental，含从 SCF k 点网格导出与对称约化 SCF 网格的处理。
- 几何与晶胞优化与实验性原子 k 点对称的交互见上文。

---

## 5. 局域分辨率恒等 LRIGPW

> 来源：<https://manual.cp2k.org/trunk/methods/dft/local_ri.html>

### 5.1 原理（官方）

- 在 GPW 中，**实空间网格上总密度的描述通常是计算上最昂贵的部分**。
- 引入**局域分辨率恒等（LRI）**方法后，可**保留 GPW 的线性标度，同时降低网格操作的 prefactor**。组合方法 LRIGPW 见 Golze2017b。
- 在 LRIGPW 中，原子对密度 ρ_AB 由**以原子 A 为中心的拟合函数集 {f_iA(r)} 与以原子 B 为中心的拟合函数集 {f_jB(r)}** 展开近似。
- 拟合函数**也是高斯型函数**，作为**辅助基组**提供。

### 5.2 使用方法（官方示例）

```
&QS
  METHOD LRIGPW
  &LRIGPW
     LRI_OVERLAP_MATRIX INVERSE
     SHG_LRI_INTEGRALS
  &END
&END QS
```

LRIGPW **额外需要一个辅助基组**作为输入：

```
&DFT
   BASIS_SET_FILE_NAME BASIS_LRIGPW_AUXMOLOPT
   BASIS_SET_FILE_NAME BASIS_MOLOPT
   ...
&END DFT
&SUBSYS
   &KIND O
     BASIS_SET DZVP-MOLOPT-GTH
     POTENTIAL GTH-PBE-q6
     LRI_BASIS_SET LRI-DZVP-MOLOPT-GTH-MEDIUM
   &END KIND
   ...
&END SUBSYS
```

**辅助基组说明（官方）**：
- 辅助基组可用于 MOLOPT 基组。**所有辅助基组都是由简单几何级数生成的，无需进一步优化。**
- 基组有不同尺寸：**`MEDIUM` 与 `LARGE`**。**使用大的辅助基组精度改善，但计算开销增加。**

### 5.3 关键坑：重叠矩阵病态（官方）

- **LRI 辅助基组通常相当大，导致重叠矩阵可能病态**（Golze2017b 式 (10)）。**因此该矩阵的求逆可能数值不稳定。**
- **若 SCF 不收敛，把 `LRI_OVERLAP_MATRIX` 设为 `AUTOSELECT`。** 此时会识别出条件数极大的原子对，**对这些对计算伪逆而非常规逆**。条件数阈值由 `MAX_CONDITION_NUM` 给出。

### 5.4 积分方案（官方）

- LRI 积分（Golze2017b 式 (31)-(34)）在 **SCF 之前**计算。
- **传统使用的 Obara-Saika 方案在这里计算量过大**，因此采用**基于 solid harmonic Gaussians（SHG）的更高效积分方案**，由 `SHG_LRI_INTEGRALS` 调用。

### 5.5 什么时候用（官方，重要）

> LRIGPW **只在实空间网格操作（即密度的 collocation 与势的 integration）主导计时时**才有益。

- **对金属体系通常不是这种情况**，因为 Kohn-Sham 矩阵对角化对计算成本贡献很大。
- **LRIGPW 对凝聚相体系高效**，如液体、分子晶体等。

**尤其大的加速可获得于**：
- **非正交晶胞（non-orthorhombic cells）**
- **大的网格 cutoff**
- **很多 SCF 步**

**补充说明（官方）**：
- 用 LRI，**SCF 步被加速，因此单点计算获益最大**。
- 对 MD，波函数可从上一帧外推、SCF 快速收敛；**这种情况下也能获得加速，取决于网格 cutoff 与体系**。
- **LRIGPW 的内存需求高于标准 GPW 方案。** 这在 HPC 平台上通常不是问题，**但可能限制在较小集群上的使用**。

官方示例输入：`lrigpw_example.inp`（Ice XV）。

---

## 6. Hartree-Fock 交换与 ADMM

> 来源：`methods/dft/hartree-fock/index.html`、`hartree-fock/admm.html`

### 6.1 HFX 章节结构（官方）

- **HFX with ADMM** — 辅助密度矩阵法
- **HFX-RI for Γ-Point (non-periodic)** — Γ 点 HFX-RI
- **HFX-RI with k-Points** — k 点 HFX-RI

### 6.2 ADMM 原理（官方）

- **辅助密度矩阵法（ADMM）通过把密度矩阵从主轨道基组投影到更小的辅助基组，降低杂化 DFT 中 Hartree-Fock 交换的成本。**
- CP2K **在辅助基组中求值精确交换，并为**主交换描述与辅助交换描述之间的差异**添加一个校正项**。
- **ADMM 在精确交换是瓶颈时最有用，尤其是在较大或更弥散的高斯基组下。**
- 它**常用于杂化 DFT**，且 **ADMM2 变体也被若干复用精确交换机制的后 SCF 方法支持**。

### 6.3 基本设置（官方示例）

ADMM 计算需要三样东西：
1. 杂化泛函或其它求值 HF 交换的设置；
2. 每个原子 kind 的辅助基组，用 `BASIS_SET AUX_FIT` 指定；
3. 一个 `AUXILIARY_DENSITY_MATRIX_METHOD` 段，选择 ADMM 变体与校正泛函。

```
&DFT
  BASIS_SET_FILE_NAME BASIS_MOLOPT_UZH
  BASIS_SET_FILE_NAME BASIS_ADMM_UZH
  POTENTIAL_FILE_NAME POTENTIAL_UZH
  &AUXILIARY_DENSITY_MATRIX_METHOD
    ADMM_TYPE ADMMS
    EXCH_CORRECTION_FUNC PBEX
  &END AUXILIARY_DENSITY_MATRIX_METHOD
  &XC
    &XC_FUNCTIONAL PBE
    &END XC_FUNCTIONAL
    &HF
      FRACTION 0.25
    &END HF
  &END XC
&END DFT

&SUBSYS
  &KIND O
    BASIS_SET ccGRB-D-q6
    BASIS_SET AUX_FIT admm-dz-q6
    POTENTIAL GTH-HYB-q6
  &END KIND
&END SUBSYS
```

### 6.4 选择辅助基组（官方）

- 辅助基组应**为主基组族与预期精度选择**。
- 对 MOLOPT 式计算，**`BASIS_ADMM_MOLOPT` 族提供紧凑的辅助基组**。
- 较新的 UZH 基组集合包含 **`BASIS_ADMM_UZH`** 及用于相关一致设置的相关基组文件。
- **全电子计算可用全电子辅助基组（当有提供时）。**

> 官方警告：**辅助基组是近似的一部分。太小的辅助基组会使交换校正变大并降低精度；太大的辅助基组则返还较少的加速。** 对生产工作，**至少测试一个更大的辅助基组，或与一个没有 ADMM 的较小参考体系比较**。

### 6.5 选择 ADMM 变体（官方）

- `ADMM_TYPE` 是一个**快捷方式**，一致地设置投影、纯化与标度选项。
- **`ADMM1` 与 `ADMM2` 是原始变体**，而 **`ADMMS`、`ADMMP`、`ADMMQ` 使用后来引入的额外模型**。
- **`ADMM2` 通常是超出基态杂化 DFT 的工作流中支持最广的变体。**
- `EXCH_CORRECTION_FUNC` 选择用于 ADMM 校正的交换泛函。**应与主交换-相关设置中的交换部分一致地选择**；`PBEX` 是 PBE 基杂化计算的常见选择。

### 6.6 官方实践检查（ADMM）

- **保持与不使用 ADMM 时相同的主基组与势收敛检查；**
- **检查对辅助基组尺寸的敏感性；**
- **对一个小的代表性体系，把总能量、力或目标性质与非 ADMM 参考比较；**
- **记住 ADMM 加速的是交换计算，但不替代主高斯基组、实空间网格或 SCF 阈值的收敛。**

参考文献：Guidon2009、Guidon2010、Merlot2014、Iannuzzi2026。

---

## 7. 约束 DFT（CDFT）

> 来源：<https://manual.cp2k.org/trunk/methods/dft/constrained.html>

### 7.1 CDFT 是什么（官方）

- CDFT 是**构造电荷和/或自旋局域化态**的工具。
- 前置要求：**不需要任何 CDFT 经验，但建议先充分理解如何使用 CP2K/QS 运行普通 DFT 模拟。**

**典型应用（官方列表）**：
- 研究**电荷转移**现象并计算**电子耦合**（例如使用 Marcus 理论方法）；
- 修正由**自相互作用误差**引起的**虚假电荷离域**；
- **参数化模型哈密顿量**（例如 Heisenberg 自旋哈密顿量）。

### 7.2 核心公式（官方原文）

在 Kohn-Sham 能量泛函 E_KS 上增加额外的**约束势**即可生成电荷/自旋局域化态：

```
E_CDFT[ρ,λ→] = max_λ→ min_ρ ( E_KS[ρ] + Σ_c λ_c [ Σ_{i=↑,↓} ∫ w_ci(r) ρ_i(r) dr − N_c ] )
```

其中：
- **λ→ = [λ_1, λ_2, ⋯]^T** 是**约束拉格朗日乘子**（约束势强度）；
- **w_i(r)** 是**原子中心权重函数**；
- **N_c** 是**约束的目标值**；
- 一次 CDFT 模拟中可包含**多个约束**。

**权重函数构造**：

```
w_i(r) = ( Σ_{j∈C} c_j P_j(r) ) / ( Σ_{j∈N} P_j(r) )
```

- **c_j** 是**原子系数**，决定每个原子如何被纳入约束；
- **P_j** 是 **cell function（胞函数）**，根据某种布居分析方法确定原子 j 所占据的体积；
- **N** 是系统中**所有原子**的集合。

**约束类型（按权重函数约定）**：

| 类型 | 权重约定 |
|---|---|
| **电荷密度约束**（ρ↑+ρ↓） | `w↑ = w↓ = w` |
| **磁化密度约束**（ρ↑−ρ↓） | `w↑ = −w↓ = w` |
| **自旋特定约束**（ρ↑/↓） | `w↑/↓ = w, w↓/↑ = 0` |

**CP2K 中可用 Becke 和 Hirshfeld 两种空间划分方案**作为约束权重函数。

**力项（MD / 几何优化）**：

```
F_c,i = −λ_c ∫ ( ∂w(r)/∂R_i ) ρ(r) dr
```

### 7.3 求解方式与 SCF 循环（官方）

- CDFT 能量表达式采用**两层（two-tiered）方法**自洽求解：**外层循环优化约束，内层循环收敛电子结构**。
- **实践中，将 CDFT 与 OT 方法结合需要三个 SCF 循环**（因为 OT 有它自己的外层循环用于重置 OT 预条件子）。
- 约束满足条件：当 `c→(λ→) = 0→` 时所有约束都被满足。因此 λ→ 可通过**最小化约束误差 max|c→(λ→)|** 来优化，直到最大元素降到阈值 **ε** 以下。**优化 λ 使用求根算法。**
- **Newton/准牛顿迭代**：`λ→_n = λ→_{n−1} − α J_n^{-1} c→(λ→_{n−1})`，其中 **α ∈ (0,1]** 是步长，**J^{-1}** 是逆 Jacobian。**步长 α 可固定，也可用回溯线搜索优化。**
- **Jacobian 近似**：用有限差分，例如一阶前向差分 `J_ij ≈ ( c→_i(λ→ + δ→_j) − c→_i(λ→) ) / |δ→_j|`。

### 7.4 典型输入（官方示例，含注释）

```
&QS
  ...
  ! CDFT loop settings
  ! Please note that prior to CP2K version 7.0,
  ! Becke constraints were separate from the CDFT section
  &CDFT
    TYPE_OF_CONSTRAINT BECKE
    ! Compute CDFT charges?
    ATOMIC_CHARGES  TRUE
    ! Constraint strength and target values
    ! Give one value per constraint
    STRENGTH        ${BECKE_STR}
    TARGET          ${BECKE_TARGET}
    ! Constraint definitions, each repetition defines a new constraint
    &ATOM_GROUP
      ATOMS 1
      COEFF 1
      CONSTRAINT_TYPE CHARGE
    &END ATOM_GROUP
    ! No constraint applied but calculate charges
    &DUMMY_ATOMS
      ATOMS 2
    &END DUMMY_ATOMS
    ! CDFT convergence and optimizer settings
    &OUTER_SCF ON
      TYPE CDFT_CONSTRAINT
      EXTRAPOLATION_ORDER 2
      MAX_SCF 10
      ! Convergence threshold
      EPS_SCF 1.0E-3
      ! Optimizer selection:
      ! Now Newton's method with backtracking line search
      OPTIMIZER NEWTON_LS
      ! Optimizer (initial) step size
      STEP_SIZE -1.0
      ! Note that the section CDFT_OPT exists in CP2K version >= 6.1
      ! Remove section for CP2K version 5.1 (keywords are unchanged)
      &CDFT_OPT ON
        ! Line search settings
        MAX_LS 5
        CONTINUE_LS
        FACTOR_LS 0.5
        ! Finite difference settings for Jacobian matrix
        JACOBIAN_STEP 1.0E-2
        JACOBIAN_FREQ 1 1
        JACOBIAN_TYPE FD1
        JACOBIAN_RESTART FALSE
      &END CDFT_OPT
    &END
    ! Settigs specific to Becke constraints
    &BECKE_CONSTRAINT
      ...
    &END BECKE_CONSTRAINT
    ! Print information about CDFT calculation
    &PROGRAM_RUN_INFO ON
      &EACH
        QS_SCF 1
      &END EACH
      COMMON_ITERATION_LEVELS 2
      ADD_LAST NUMERIC
      FILENAME ./${NAME}
    &END PROGRAM_RUN_INFO
  &END CDFT
&END QS
```

**官方说明：这些参数选择应适合大多数系统。**

**关键关键字（官方）**：

| 关键字 | 官方说明 |
|---|---|
| `TYPE_OF_CONSTRAINT` | 选择约束类型（示例 `BECKE`） |
| `ATOMIC_CHARGES` | 是否计算 CDFT 电荷 |
| `ATOM_GROUP` 段 | 定义实际约束，**每次重复该段就定义一个新约束** |
| `ATOMS` / `COEFF` / `CONSTRAINT_TYPE` | 选择约束原子 / 原子系数（**通常所有系数都设为 +1**，混合 +1 与 −1 系数会将约束定义为两组原子之差）/ 选择约束类型 |
| `TARGET` | **约束目标值应为约束原子上期望的价电子数**；若使用两组原子间的相对约束，则需适当乘以原子系数 |
| `STRENGTH` | 初始约束强度 λ→ |
| `DUMMY_ATOMS` | 不施加约束但计算电荷 |
| `FRAGMENT_CONSTRAINT` | 基于碎片的约束，目标值由孤立碎片密度的叠加计算得到 |
| `OUTER_SCF` | 定义 CDFT SCF 循环设置 |
| `EPS_SCF`（CDFT 内） | 定义 CDFT 约束收敛阈值 ε |
| `OPTIMIZER` | 选择 CDFT 优化器。**推荐大多数应用使用 Newton 或准牛顿优化器（Broyden 方法）** |
| `STEP_SIZE` | 优化器（初始）步长 |
| `CDFT_OPT` 段 | **CP2K >= 6.1 才有**；CP2K 5.1 请移除该段（关键字不变） |

**优化器选择建议（官方）**：
- **Newton 或准牛顿优化器（Broyden 方法）推荐用于大多数应用。**
- **单约束的 MD 模拟可能受益于使用 bisect 优化器**（二分法），因为它**避免构建 Jacobian 矩阵**——当每个 MD 步总时间中相当一部分花在构建 Jacobian 上时尤其有用。
- **Jacobian 重建频率 `JACOBIAN_FREQ` 可以在每个 MD 步和每个 CDFT SCF 步的基础上控制。**
- **Broyden 优化器需要更少的 Jacobian 重建**（矩阵每次迭代做 rank-one 更新），**但该方法关于重建频率的稳定性需要仔细研究**。

### 7.5 Becke 约束（官方）

- **Becke 密度划分方法可被视为一种平滑的 Voronoi 方案。**
- Voronoi 划分中，每个原子占据的体积是"比其他任何原子都更接近该原子"的实空间网格点集合。
- **Becke cell function P_i 叠加在 Voronoi 图之上，在 Voronoi 多面体边界上从 1 平滑衰减到 0。使用平滑的密度划分函数可改善模拟的数值稳定性。**

> **问题与补救**：Voronoi 及 Becke 划分方法**对每种元素同等对待**，这在大多数系统中会导致**非物理的部分电荷**。例如，**Becke 方案预测水中氧带正电、氢带负电**。补救方法：在划分时考虑**原子半径**，由 `ADJUST_SIZE` 激活，原子半径由 `ATOMIC_RADII` 定义。**原子半径应设置为反映所模拟系统的值，例如共价分子使用加成共价半径，离子化合物使用 Shannon 离子半径。**

**算法实现与计算成本（官方）**：
- Becke 密度划分涉及**在每个实空间网格点 r 上遍历每对原子排列 {R_i, R_j}, j ≠ i**。
- 这导致**对系统尺寸（单元格大小和平面波截断）以及系统内原子数的糟糕扩展性**，**对溶剂化系统模拟尤为麻烦**。
- **计算成本可显著降低**：只有约束涉及原子在截断距离 R_cutoff（`CUTOFF_TYPE`）内的网格点才真正需要考虑。**其它网格点可用约束原子中心的球状高斯函数高效筛选，由 `CAVITY_CONFINE` 激活**，并由其他形如 `CAVITY_*` 的关键字控制。

**Becke 约束示例（官方）**：

```
&CDFT
  ...
  &BECKE_CONSTRAINT
    ! Take atomic radii into account?
    ADJUST_SIZE     FALSE
    ATOMIC_RADII    0.63 0.32
    ! Cutoff scheme
    CUTOFF_TYPE     ELEMENT
    ELEMENT_CUTOFF  6.0
    ! Perform Becke partitioning only within the space
    ! spanned by constraint atom centered spherical Gaussians
    ! (reduces cost for solvated systems)
    CAVITY_CONFINE  TRUE
    CAVITY_SHAPE    VDW
    EPS_CAVITY      1.0E-7
    IN_MEMORY       TRUE
    SHOULD_SKIP     TRUE
&END CDFT
```

> **官方建议**：这组参数选择应对大多数系统合理，除了**系统相关的原子半径和约束定义**。**减小划分截断可能对溶剂化系统 MD 模拟有用，但在开始生产模拟前必须进行大量测试。**

### 7.6 Hirshfeld 约束（官方）

- **Hirshfeld 约束在大系统中比 Becke 约束构造更便宜**，因为它们**本质上只是球状高斯函数的加权和**。
- `SHAPE_FUNCTION` 与 `GAUSSIAN_SHAPE` 定义对系统施加哪种类型的 Hirshfeld 约束。
- **`SHAPE_FUNCTION` 接受两个值：`Gaussian` 或 `Density`。**
  - **`Gaussian`**：每个原子的 CDFT 权重函数是**单个高斯函数**，其半径由 `GAUSSIAN_SHAPE` 控制。**默认使用表格化共价半径作为高斯半径**，也可选 van der Waals 半径或自定义半径。
  - **`Density`**：原子权重函数由**孤立原子密度**构造，并展开为多个球状高斯函数。**该选择避免了引入任何经验参数，且通常提供比 Becke 或基于高斯函数的 Hirshfeld 电荷划分更稳健的原子电荷描述。**
- **Hirshfeld 约束模拟需要 CP2K 7.0 或更高版本。**

### 7.7 混合 CDFT（MIXED_CDFT）

- **混合 CDFT 计算通过 `MIXED FORCE_EVAL` 段激活**：把 `MIXING_TYPE` 设为 `MIXED_CDFT`，并提供适当的 `MIXED_CDFT` 输入段。
- **参与混合 CDFT 计算的各个 CDFT 态应对应同一系统中电荷和/或自旋的不同局域化。**
- **约束定义不必在所有态中完全相同（即用相同原子集定义），只要约束数目相同即可。**
- **CDFT 态作为它们各自的 `FORCE_EVAL` 段包含进来。**

> **强烈建议（官方）**：先在单独模拟中收敛各 CDFT 态，然后将这些模拟的 `FORCE_EVAL` 段复制粘贴到混合 CDFT 输入文件，并把混合 CDFT 方法用作**后处理分析工具**。收敛的波函数和约束强度 λ→ 应作为重启量提供给混合 CDFT 计算。**强烈鼓励使用模板和 CP2K 的 `@include`、`@set` 指令**来保持混合 CDFT 输入整洁。

**正交化方法（官方）**：
- **旋转 CDFT 态到权重矩阵 W 的本征态**：**只有一个约束且该约束在所有 CDFT 态中定义完全相同**的系统默认行为；否则不适用。
- **Löwdin 对称正交化** `H = S^{−1/2} H' S^{−1/2}`：**有多个约束的系统默认行为**，且**始终可用关键字 `LOWDIN` 激活**。
- **波函数重叠方法**：基态 Kohn-Sham 解表示为 CDFT 态的线性组合，见关键字 `WFN_OVERLAP`。

**`NGROUPS` 与并行（官方）**：
- `NGROUPS 1`：两个 CDFT 态**顺序**处理，使用全部 N 个 MPI 进程。**如果各 CDFT 态约束定义相同，CDFT 权重函数及其梯度会从一态复制到另一态**（因为构造这些项在大系统中可能很昂贵）。
- `NGROUPS` 设为 2 或更大：**每个 CDFT 态用 N/Ngroups 个处理器并行求解**。**很可能减少墙钟时间，但代价是更多计算资源。** 注意此时权重函数及其梯度对每个态**单独计算**，**对大型溶剂化系统可能代价很高**。
- `PARALLEL_BUILD`（`NGROUPS 2` 时可用）：**CDFT 权重函数和梯度先在 N 个 MPI 进程上并行构建，随后复制到两个大小为 N/2 的 MPI 处理器组上并行求解 CDFT 态。该运行模式限于两个 CDFT 态、一个定义完全相同的总电荷密度约束。** 这是**高级特性**，**应仅在可能时与 `DLB` 动态负载均衡配合使用**。

**官方算例结果（供对照）**：
- Zn 阳离子二聚体电子耦合：rotation 与 Löwdin 两种正交化方法**都给出 5.67 mHa**，与更昂贵的 CASSCF/MRCI+Q 的 **5.49 mHa** 估计一致。
- 水二聚体电荷转移能参考值：**1.7 mHa**（PBE0/def-QZVP/CDFT，不同代码与约束）。

---

## 8. DFT+U（官方 HowTo）

> 来源：<https://www.cp2k.org/howto:dft_u>（页面最后修改 2023-11-23）

### 8.1 为什么需要 DFT+U（官方原文）

> Plain density functional theory (DFT) calculations based on the local density approximation (LDA) or the generalised gradient approximation (GGA) **usually fail to describe strongly correlated system properly**. LDA and GGA often **incorrectly predict a metallic ground state** for systems like **FeO, CoO or UO2**. A possible remedy for this deficit is the addition of a **Hubbard U correction** which is known as **DFT+U** (or also LDA+U or GGA+U) approximation.

### 8.2 官方完整算例：立方 FeO 的 EOS 计算

- 体系：立方 FeO（空间群 #225，wüstite），用 **2x2x2 晶胞**以计入沿 [111] 的反铁磁有序。
- 关键设置（从官方完整输入中提取）：

```
&GLOBAL
  PRINT_LEVEL low
  PROJECT ${project}
  RUN_TYPE ${run_type}     ! energy_force
  WALLTIME 1800
&END GLOBAL

&FORCE_EVAL
  METHOD Quickstep
  &DFT
    LSD
    PLUS_U_METHOD Mulliken
    BASIS_SET_FILE_NAME BASIS_MOLOPT
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    &MGRID
      CUTOFF 600.0
      REL_CUTOFF 60.0
    &END MGRID
    &QS
      EPS_DEFAULT 1.0E-12
    &END QS
    &SCF
      EPS_SCF 3.0E-7
      MAX_SCF 21
      SCF_GUESS restart
      &OT on
        MINIMIZER CG
        PRECONDITIONER FULL_SINGLE_INVERSE
        STEPSIZE 0.1
      &END OT
      &OUTER_SCF on
        EPS_SCF 3.0E-7
        MAX_SCF 20
      &END OUTER_SCF
      ...
    &END SCF
    &XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC ${a} ${b} ${c}
      &CELL_REF
        ABC ${a_ref} ${b_ref} ${c_ref}
      &END CELL_REF
    &END CELL
    ...
    &KIND Fe_a
      BASIS_SET DZVP-MOLOPT-SR-GTH-q16
      POTENTIAL GTH-PBE-q16
      # Fe(2+): 3d6 (alpha, spin up)
      &BS on
        &ALPHA
          N    4   3
          L    0   2
          NEL -2   4
        &END ALPHA
        &BETA
          N    4   3
          L    0   2
          NEL -2  -4
        &END BETA
      &END BS
      &DFT_PLUS_U on
        L 2
        U_MINUS_J [eV] ${U_Fe}
      &END DFT_PLUS_U
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

**关键要点（官方）**：
- **`PLUS_U_METHOD Mulliken`** 在 `&DFT` 中设置。
- **`&DFT_PLUS_U` 按 kind 设置**，含 `L 2`（d 电子）与 `U_MINUS_J [eV] ${U_Fe}`。
- 需要 **`LSD`（= UKS）** 与 **`&BS`（broken symmetry）** 设置初始占据，以构造反铁磁序。
- **`&CELL_REF` 设为比优化过程预期上界更大的尺寸**（这是变胞优化的官方建议，见 `05_optimization.md`）。

### 8.3 U 值来源（官方）

> The suggested Hubbard Ueff value of **1.9 eV** for iron using CP2K has been retrieved from the work of **Kéri et al., ES&T 51, 10585-10594 (2017)**.

即官方明确说明：**U 值应从文献获取**，而不是自己拍。

### 8.4 官方给出的 FeO EOS 总能量数据（CP2K 2023.2）

```
# a [Angstrom]  Total energy [Hartree]
  8.385257      -4466.80963727
  8.444310      -4466.85496007
  8.502549      -4466.88640521
  8.560000      -4466.90536056
  8.616690      -4466.91306948
  8.672644      -4466.91064762
  8.727886      -4466.89906783
  8.782436      -4466.87923722
  8.836318      -4466.85199239
  8.889550      -4466.81806793
```

### 8.5 官方关于 EOS 扫描的实操建议

> It is recommended to **start with a cell size close to the assumed minimum** and to **employ the wavefunction restart files consecutively for the larger and smaller cell sizes** to avoid a convergence to different states for compressed and enlarged cells.

即：**从一个接近预期最小值的晶胞开始，然后向更大和更小的晶胞连续复用波函数重启文件**，以避免压缩和膨胀晶胞收敛到不同状态。

---

## 9. 线性标度 DFT（官方占位页）

> 来源：<https://manual.cp2k.org/trunk/methods/dft/linear_scaling.html>

官方本页**无正文**：

> Unfortunately no one has gotten around to writing this page yet :-(

官方仅给出两条外链：
- 文献 VandeVondele2012
- `https://www.cp2k.org/exercises:2017_ethz_mmm:ls_scf`

**G 层不编造内容**。线性标度相关的输入关键字（`LS_SCF` 等）应查官方 Input Reference；实操经验见 A/F 层。

---

## 10. 交叉索引

| 主题 | G 层 | A/F 层 |
|---|---|---|
| CUTOFF / REL_CUTOFF 收敛 | `03_scf_convergence.md` §3 | A `decide.md`；F `playbook.md` §0 |
| SCF 收敛（含 OT / 对角化选择） | `03_scf_convergence.md` | A；F §1 |
| DFT+U 是否必加 | 本文 §8 | A `decide.md` §28（强关联 TM 必加） |
| BSSE | 官方 acronyms 有 BSSE 词条 | A §28（高斯基组高估吸附能）；F |
| 色散校正 | 本文 §11 | A；F |
| 功能是否支持 k 点 | 本文 §4.3 兼容性表 | — |
| 官方功能全清单（能不能算 X） | `10_features_resources.md` | — |

---

## 11. 色散校正与非局域 vdW（官方缺口说明）

官方手册 **`methods/dft/vdw.html` 返回 404**，即当前手册没有独立的色散校正方法页。

可从官方其它位置获得的权威信息：

**官方功能清单（`www.cp2k.org/features`）明确列出**：
- **DFT-D2 / DFT-D3** 色散校正
- **非局域 vdW 泛函**：`B88-vdW`、`PBE-vdW`、`B97X-D`

**官方库依赖页（`technologies/libraries.html`）明确列出**：
- **DFTD4** — Generally Applicable Atomic-Charge Dependent London Dispersion Correction
  - CMake 开关 `-DCP2K_USE_DFTD4=ON`
  - **重要限制**：目前 CP2K **请使用 CMake 构建的 dftd4 包，而非 Meson 构建的包**
  - **CP2K 2026.2 将是最后一个带有 legacy DFTD4 代码（低至版本 3）接口的发行版**；这些接口已在 PR #5641 中被移除
  - DFTD4 **也包含在 TBLITE 包中**
- **SIRIUS 的 DFT-D3 / DFT-D4 支持**：`-DCP2K_USE_SIRIUS_DFTD3=ON`、`-DCP2K_USE_SIRIUS_DFTD4=ON`

**输入关键字**：应查官方 Input Reference 的 `FORCE_EVAL/DFT/XC/VDW_POTENTIAL` 段（G 层未抓取该 Input Reference 页面，属于已知缺口，见 `_sources.md`）。

**F 层经验（不在 G 层，仅指向）**：BSSE 与吸附能高估的经验性警示见 A 层 `decide.md` §28 与 F 层 `playbook.md`。
