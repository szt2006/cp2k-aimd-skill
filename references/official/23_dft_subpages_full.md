# 23 · DFT 子页正文补遗（官方）

> 来源：
> - https://manual.cp2k.org/trunk/methods/dft/cneo.html
> - https://manual.cp2k.org/trunk/methods/dft/gauxc.html
> - https://manual.cp2k.org/trunk/methods/dft/electrostatics/index.html
> - https://manual.cp2k.org/trunk/methods/dft/hartree-fock/index.html
> - https://manual.cp2k.org/trunk/methods/dft/hartree-fock/admm.html
> - https://manual.cp2k.org/trunk/methods/dft/hartree-fock/ri_gamma.html
> - https://manual.cp2k.org/trunk/methods/dft/hartree-fock/ri_kpoints.html
> - https://manual.cp2k.org/trunk/methods/dft/local_ri.html
> - https://manual.cp2k.org/trunk/methods/dft/gpw.html
> - https://manual.cp2k.org/trunk/methods/dft/gapw.html
> - https://manual.cp2k.org/trunk/methods/dft/basis_sets.html
> - https://manual.cp2k.org/trunk/methods/dft/pseudopotentials.html
> - https://manual.cp2k.org/trunk/methods/dft/k-points.html
> - https://manual.cp2k.org/trunk/methods/dft/orbital_transformation.html
> - https://manual.cp2k.org/trunk/methods/dft/convergence.html
> - https://manual.cp2k.org/trunk/methods/dft/cutoff.html
> - https://manual.cp2k.org/trunk/methods/dft/constrained.html
> - https://manual.cp2k.org/trunk/methods/dft/linear_scaling.html
> 抓取日期：2026-09-09
> 标注规则：`[默认]` = 官方 Input Reference 默认值；`[官方推荐]` = 官方正文明确推荐；`[示例]` = 官方示例取值；`[G层提示]` = G 层整理性说明（非官方原话）。

---

## 0. 本文件补什么

`02_dft_methods.md` 已覆盖 GPW/GAPW 原理、赝势、OT、k 点、LRIGPW、HFX-ADMM、CDFT、DFT+U 的**主体**。
但官方 DFT 章节（`methods/dft/`）下还有若干子页，其**正文**此前只有"被提及"而无内容。本文件补齐：

| 子页 | `02` 中状态 | 本文件处理 |
|---|---|---|
| `cneo.html` | 仅 1 次提及 | **§1 全新**：CNEO-DFT 完整理论 + 输入 + 适用场景 |
| `gauxc.html` | 0 次 | **§2 全新**：外部 XC 积分器 + Skala 机器学习泛函 |
| `electrostatics/index.html` | 0 次 | **§3 全新**：泊松求解器选型 + 带电体系 + 真空收敛 |
| `hartree-fock/ri_gamma.html` | 0 次 | **§4.1 全新**：RI-HFX（Γ 点） |
| `hartree-fock/ri_kpoints.html` | 0 次 | **§4.2 全新**：RI-HFXk（k 点） |
| `hartree-fock/admm.html` | 已覆盖 | §4.3 只补**补充要点**（避免重复） |
| `local_ri.html` | 已覆盖 | §5 只补**官方"何时用"判据**（避免重复） |
| `gpw.html` / `gapw.html` | 已覆盖 | §6 只补**流程图与官方结论**（避免重复） |
| `basis_sets.html` | 部分覆盖 | §7 补**命名体系 + UZH 协议推荐** |
| `pseudopotentials.html` | 已覆盖 | §7.4 补**关键字 vs 段**的官方长示例 |
| `k-points.html` | 已覆盖 | 不重复，见 `02_dft_methods.md` §4 |
| `orbital_transformation.html` | 已覆盖 | §8 补**官方关键区分表述** |
| `convergence.html` | 已覆盖 | §9 补**`EXTERNAL_DENSITY` 初始猜测 + 重启链条** |
| `cutoff.html` | 已覆盖 | 不重复，见 `03_scf_convergence.md` 第二部分 |
| `constrained.html` | 已覆盖 | 不重复，见 `02_dft_methods.md` §7 |
| `linear_scaling.html` | 占位页 | §10 登记 |

> **[G层提示]** 本文件是**补遗**，不是独立体系。查 DFT 方法请先看 `02_dft_methods.md`，
> 本文件只提供 `02` 未覆盖的正文。凡与 `02` 冲突处，以官方原文为准并回标 `02`。

---

## 1. CNEO-DFT（约束核-电子轨道 DFT）

> 来源页：`methods/dft/cneo.html`

### 1.1 是什么（官方原文）

**Constrained nuclear-electronic orbital DFT (CNEO-DFT)** 把**部分或全部原子核当作量子力学处理**，
同时**保持明确定义的分子几何/晶体结构**。

做法：对量子核施加**位置约束**，产生**有效势能面**，该势能面**包含核量子效应**，
尤其是量子离域带来的**零点能**。

**关键结论（官方原文）**：在这个有效势能面上，**可以照常做几何优化、振动分析、经典分子动力学**，
用来**替代传统的 Born–Oppenheimer 势能面**。

### 1.2 理论（官方）

能量泛函同时依赖电子密度 ρ^e(r) 与核密度 ρ_I^n(r)：

```
E[ρ^e, {ρ_I^n}] = T_s^e[ρ^e] + Σ_I T_s^{n,I}[ρ_I^n]
                  + ∫dr V_ext(r) [ρ^e(r) − Σ_I Z_I ρ_I^n(r)]
                  + E_H[ρ^e, {ρ_I^n}] + E_xc^e[ρ^e] + E_c[ρ^e, {ρ_I^n}]
```

**位置约束**（对每个量子核 I）：

```
⟨r⟩_I = ∫ r ρ_I^n(r) dr = R_I
```

其中 `R_I` 是对应经典分子/晶体几何的位置期望值。

该约束通过**拉格朗日乘子 f_I** 施加在 CNEO 核 Kohn–Sham 方程中：

```
[ −1/(2M_I) ∇² + v_eff^{n,I} + f_I · (r − R_I) ] φ_i^{n,I} = ε_i^{n,I} φ_i^{n,I}
```

**官方解释**：在每个核几何处自洽求解，得到 CNEO 有效能量面上的一个点，
可解释为**约束最小化能量面（constrained minimized energy surface, CMES）**。
CMES 理论框架为"在这些有效能量面上做动力学传播"提供了理论依据。

**解析梯度**：CNEO 能量对**量子核位置期望值**以及**经典核位置**的解析梯度，
提供几何优化、振动分析、分子动力学所需的**力**。

> **[G层提示]** 这句话是 CNEO 能被当作"普通 CP2K 任务"跑的**根本原因**——
> 它提供了解析力，所以 `RUN_TYPE GEO_OPT` / `VIBRATIONAL_ANALYSIS` / `MD` 全部可用。

### 1.3 怎么用（官方逐步）

#### 前置条件

- 含量子核的原子**必须用 GAPW**。
- 官方要求用户**先熟悉 CP2K 里的 GAPW 设置**。

#### 基本输入结构

除电子基组文件外，**还需指定核基组文件**。官方以 `NUCLEAR_BASIS_SETS`（PB 系列质子基组）为例：

```fortran
&DFT
  BASIS_SET_FILE_NAME NUCLEAR_BASIS_SETS  ! Nuclear basis
  &QS
    METHOD GAPW               ! GAPW is required for CNEO
  &END QS
&END DFT
```

官方说明：**也可以提供自定义核基函数的其它基组文件**。

#### 定义量子核

把原子的 `POTENTIAL` 设为 `CNEO`，即**对该原子启用 CNEO-DFT**。
这些原子**同时需要电子基组与核基组**：

- **电子基组**必须是**全电子**的——为了正确描述**核区**的电子-核相互作用；
- **核基函数**描述量子核轨道。

```fortran
&KIND H
  BASIS_SET Ahlrichs-def2-TZVP   ! All-electron electronic basis
  BASIS_SET NUC PB4-D            ! Nuclear basis
  POTENTIAL CNEO                 ! This enables CNEO-DFT calculation
&END KIND
```

> **[G层提示]** 注意 `BASIS_SET NUC <名字>` 的**双参数形式**：第一个参数是**基组角色**（`NUC` = 核基组），
> 第二个才是基组名。这与 `BASIS_SET ORB ...` / `BASIS_SET AUX_FIT ...` / `BASIS_SET RI_HFX ...` 同构。

#### 经典核

经典核用**标准设置**（赝势或全电子）。官方说明：
**只有含量子核的原子才严格要求 GAPW**，因此经典核原子**可以跳过 GAPW**，用 `GPW_TYPE .TRUE.`。

#### 核基组

`NUCLEAR_BASIS_SETS` 提供 PB 系列质子基组（PB4-D 到 PB6-H），
并**额外含两个缩放指数版本**作为"非质子量子核"的示例：

| 基组 | 官方说明 |
|---|---|
| **PB4-D** ~ **PB6-H** | 为质子优化的基函数（含球谐） |
| **PB4-D_D** | PB4-D 的**缩放指数**版本，用于氘 |
| **PB4-D_Mu** | PB4-D 的**缩放指数**版本，用于μ子（muonium，**仅用于测试目的**） |

**官方明确的限制**：
- 除 `PB4-D` 外**没有提供其它基组的缩放版本**；
- 用户若想用它们研究氘，可**手动按 √(m_deuteron/m_proton) 缩放指数**；
- 但官方提醒：**这种简单修改可能不是最优的**；
- 对**一般质量与电荷**的量子核，**基组开发仍非常有限**，用户可能需**自行构造基函数**（例如 even-tempered 基组）。

#### 质量指定

对氢原子，程序**自动假定 ¹H 同位素**并使用相应核质量（质子质量 1.007825 u **减去电子质量**）。

对同位素或其它量子核，**显式指定中性原子质量**：

```fortran
&KIND H
  BASIS_SET Ahlrichs-def2-TZVP
  BASIS_SET NUC PB4-D_D          ! Nuclear basis suitable for the mass
  POTENTIAL CNEO
  MASS 2.01410177811             ! Neutral deuterium atom mass
&END KIND
```

**官方明确的两条**：
1. 程序**自动减去电子质量**得到核质量；
2. 对**氢以外的元素**，用**纯同位素质量**，不要用平均原子质量。

**官方诚实的边界声明**：
- 电子-核相互作用的**平均场处理**主要**在氢体系上做过基准测试**；
- 虽有无关联的**初步全量子研究**存在；
- **缺乏优化的核基组**是另一个可能的问题。

#### k 点采样

- **电子自由度**支持标准 k 点采样（用于扩展体系）。
- **k 点采样只影响电子子系统**；量子核由于**高度局域化的图像**，
  **仍由局域基函数描述，与 k 点网格无关**。

### 1.4 什么时候用（官方）

**含氢体系**，且**质子量子效应显著影响分子性质**时。官方列出的关键应用：

| 应用 | 官方说明 |
|---|---|
| **振动光谱** | 改善频率预测，捕获量子核运动带来的**非谐贡献** |
| **同位素效应研究** | 理解核质量变化（H/D）如何通过**零点能与量子离域**改变分子性质 |
| **表面化学** | 涉及吸附、扩散、转移过程，核量子效应改变热力学与动力学行为 |
| **反应动力学** | 零点能与核**浅势垒隧穿**影响势垒高度与反应速率 |

### 1.5 参考文献（官方给出）

| 编号 | DOI |
|---|---|
| [1] | https://doi.org/10.1063/1.5143371 |
| [2] | https://doi.org/10.1021/acs.jpclett.2c02905 |
| [3] | https://doi.org/10.1063/5.0009233 |
| [4] | https://doi.org/10.1063/5.0243086 |
| [5] | https://doi.org/10.1063/5.0014001 |

> **[G层提示]** 本页**没有给出完整的可运行输入示例**，只有代码片段。
> 想跑请以 `data/NUCLEAR_BASIS_SETS` 与官方 regtest 为准。

---

## 2. GauXC（外部 XC 积分器 + Skala 模型）

> 来源页：`methods/dft/gauxc.html`

### 2.1 是什么（官方原文）

**GauXC 为 Quickstep 提供外部交换-关联（XC）积分器**。
它可以通过 `GAUXC` 段求值**选定的传统泛函**以及 **GauXC Skala 模型**。

**官方明确的两条路径**：

| 路径 | 官方说明 |
|---|---|
| **默认：分子求积路径**（molecular-quadrature） | 通过 GauXC 的**原子中心分子网格**求 XC 贡献。**主要面向孤立体系计算** |
| **实验性：原生网格路径**（`NATIVE_GRID T`） | 从 **CP2K 的 GPW 实空间网格**求值 **SKALA TorchScript 模型**。**支持范围不同，应与分子求积路径分开看待** |

### 2.2 基本输入

GauXC 在 `XC_FUNCTIONAL` 段里被选为**唯一的 XC 泛函**。

**选传统泛函**：

```fortran
&XC
  &XC_FUNCTIONAL
    &GAUXC
      FUNCTIONAL PBE
    &END GAUXC
  &END XC_FUNCTIONAL
&END XC
```

**选 Skala 模型**：`MODEL` 非 `NONE` 即选择 GauXC Skala 模型。
模型可以是 `.fun` 文件或**已安装的模型名**。此时底层泛函**可选，默认为 `PBE`**：

```fortran
&XC
  &XC_FUNCTIONAL
    &GAUXC
      MODEL path/to/model.fun
    &END GAUXC
  &END XC_FUNCTIONAL
&END XC
```

**官方明确**：`.fun` 格式与可用模型检查点**由 GauXC 而非 CP2K 定义**。`.fun` 文件用 **TorchScript 序列化**。

官方 Skala 1.1 Rev1 检查点可用 `huggingface_hub` 的 `hf` 命令下载：

```bash
hf download microsoft/skala-1.1 skala-1.1-rev1.fun --local-dir .
hf download microsoft/skala-1.1 skala-1.1-rev1-cuda.fun --local-dir .
```

- 用 `MODEL ./skala-1.1-rev1.fun` **显式选择**下载的检查点；
- 或者把 `GAUXC_SKALA_MODEL` 指向 **CPU 检查点**，并用 `MODEL SKALA` 做**主机执行**；
- 对 `INT_EXECUTION_SPACE DEVICE`，把 `GAUXC_SKALA_CUDA_MODEL` 指向 **CUDA 检查点**；
- CP2K 会**回退到 `GAUXC_SKALA_MODEL`**（为了兼容"该变量已指向设备兼容检查点"的既有配置）；
  **CPU 检查点本身不是设备兼容的**。
- **官方安全提醒**：模型接口与可用检查点请查阅 GauXC/Skala 模型文档，**`.fun` 文件只从可信来源获取**。

**网格默认值（官方）**：分子求积 Skala 路径默认 `GRID SUPERFINE` 与 `PRUNING_SCHEME UNPRUNED`（除非显式给出）。
**官方建议**：这些设置**推荐用于力检查**；更粗的网格属于**精度设置，应针对目标计算做收敛**。

### 2.3 分子求积路径（默认）

- 是**孤立 Quickstep 计算**的既有接口，**在其支持范围内**包含能量、XC 势、核梯度计算。

#### 周期性参考计算

**官方强调**：周期输入**不是**紧凑周期性 GauXC 实现。
若想在周期输入里把分子路径当作**孤立胞参考计算**用，**必须显式设** `PERIODIC_REFERENCE T`：

```fortran
&GAUXC
  PERIODIC_REFERENCE T
&END GAUXC
```

**该参考路径同时受限于全部三条**：

- `PERIODIC XYZ`；
- **Gamma 点**计算且**只有一个 AO 镜像**；
- `METHOD GPW` 配 **GTH 赝势**。

**官方明确警告**：它用的是**分子求积**，**不得用来验证紧凑周期材料**。
周期性邻胞 AO 块、k 点、紧凑胞求积、周期应力张量**都需要专门的周期性 GauXC 接口**。

#### Skala 运行时控制

| 关键字 | 官方说明 |
|---|---|
| `MODEL_ATOM_CHUNK_SIZE` | 控制**按原子分块的 Torch 推断**。正值 = 每块原子数；零 = 禁用分块；**默认** = 让 GauXC 或 `GAUXC_ONEDFT_ATOM_CHUNK_SIZE` 环境变量决定 |
| `SKALA_RUNTIME` | MPI 计算中控制 **Skala 能量与势求值用的通信子**。`AUTO` = 闭壳层用**力求值通信子**，开壳层用**rank 局部复制运行时** |
| `MODEL_GRADIENT_RUNTIME` | **默认**为**保守的复制运行时**，用于核梯度。**只有** GauXC 安装支持**分布式 Skala 梯度**时才选 `MPI` |

#### GAPW 密度表示（官方，技术核心）

**官方明确**：传统 GauXC 配 `METHOD GAPW` **需要全电子势**。
Skala 模型**额外支持赝势 GAPW**。`PSEUDOPOTENTIAL_GAPW_REPRESENTATION` 显式选择其密度表示：

| 取值 | 官方说明 |
|---|---|
| `DIRECT_VALENCE` | **[默认]** 在**直接价密度**上求值模型；是 GTH/ECP kind 的**GPW 式路线**，**与 kind 的 `GPW_TYPE` 设置无关** |
| `PAW_ONE_CENTER` | 把密度、密度梯度、动能密度重构为 **smooth + hard − soft**，然后再做 Skala 求值。**在这个求和之后形成非线性特征**，保留了 smooth/hard/soft 三个自旋梯度分量之间的**全部 15 个两两交叉项**；其中 **14 个是相对 smooth-density 基线的额外项**。同样构造**也保留非局域耦合** |
| `PAW_ONE_CENTER_SPLIT` | 保留**遗留的"分别求值 smooth 与 hard−soft 能量"**作为**显式诊断**。该表达式对**半局域 GAPW XC 是精确的**，但对**非局域 Skala 模型不是数学恒等式** |
| `CP2K_DEFAULT` | 恢复由既有的 `GPW_TYPE`、基组、`FORCE_PAW` kind 设置**隐含的表示** |

**适用范围（官方）**：该选择器**只适用于赝势 GAPW kind**。
- 全电子 `METHOD GAPW` **保持其全电子 AO 密度表示**；
- `METHOD GAPW_XC` 在相应单中心重构**之前**选择 CP2K 的 `rho_xc` 密度；
- **混合全电子/赝势体系用同一个选择器、无需额外输入**：全电子 kind 贡献其单中心原始场，
  每个赝势 kind 遵循 `DIRECT_VALENCE`、`PAW_ONE_CENTER` 或遗留的 `CP2K_DEFAULT` 规则。

**两个易混关键字（官方明确区分）**：
- `NATIVE_GRID_GAPW_DENSITY_PARTITION` 控制**遗留的单中心诊断**；**默认 `HARD_MINUS_SOFT`**，
  遵循 CP2K 的 GAPW XC 构造。`HARD_ONLY`、`SOFT_ONLY`、`NONE` 是**诊断选项**。
- 名字相似的 `NATIVE_GRID_ATOM_PARTITION` 控制**原生网格的原子划分**，
  **不影响 GauXC 分子求积**。

**网格继承（官方）**：单中心表示**继承 kind 相关的 `RADIAL_GRID`、`LEBEDEV_GRID`、`HARD_EXP_RADIUS` 控制**；
**官方警告**：**已确立的更紧设置不应为 Skala 计算而降低**。

**电子数守恒（官方，重要）**：
- 重构表达式**在密度表示层面守恒电子数**；
- 其在**有限径向/Lebedev 求积**上的数值积分**保留常规分子网格误差**，随 kind 相关网格设置收敛；
- **CP2K 不对密度做重标定**以强制数值积分精确——因为**密度相关的重标定会改变 Skala 泛函**，
  并需要**额外的 VXC、力、维里导数**；
- `NATIVE_GRID_DIAGNOSTICS T` 打印**原子复合电子积分**用于收敛检查。

**力与维里（官方）**：
- 分子 Skala 力**对 GAPW 与 GAPW_XC 情形可用**；
- 直接分子 GauXC 路线通过**配置好的 GauXC 梯度路径**求 XC 核梯度；
- `PAW_ONE_CENTER` 表示则**解析地传播 Skala 特征伴随**，穿过 CP2K 的
  **smooth-field 插值 → 单中心重构 → 原子划分 → NLCC 中心坐标**；
- `MOLECULAR_VIRIAL` 是**由核梯度构造的有限体系诊断**，**不是周期应力张量**。

**NLCC 限制（官方，重要）**：
- **直接分子 GauXC 求值配 NLCC 赝势不受支持**——因为 GauXC **不接收冻结芯密度及其导数**；
- **分子赝势 GAPW 配 `PAW_ONE_CENTER` 是另一条受支持的路线**：
  CP2K 在**同一个原子中心复合求积**上求 NLCC 密度与梯度，**在 Skala 构造特征之前**把它们
  加入重构的原始场，并**解析地微分芯与网格中心坐标**；
- **动能密度保持仅价电子（valence-only）**。
- **官方明确不支持清单**：非局域 `VDW_POTENTIAL` 校正、更高阶 XC 导数响应与 kernel 性质、
  实时传播。

### 2.4 实验性原生网格 SKALA 路径

`NATIVE_GRID T` **绕过 GauXC 的分子求积**，从 **CP2K 的 GPW 实空间网格**求值 SKALA TorchScript 模型。
官方定位：**能量、XC 势、核梯度/应力计算的实验性路径，只用一个 GAUXC 泛函**。
**与分子路径不同**，它**可以覆盖选定的孤立与周期性 GPW/GAPW 计算，包括 k 点密度矩阵**。

最小原生网格输入：

```fortran
&XC
  &XC_FUNCTIONAL
    &GAUXC
      MODEL SKALA
      NATIVE_GRID T
      NATIVE_GRID_DIAGNOSTICS T
    &END GAUXC
  &END XC_FUNCTIONAL
&END XC
```

`NATIVE_GRID_DIAGNOSTICS T` 打印**传给 Torch 的特征块的电子数、自旋矩、网格权重之和**。
**官方建议**：在**验证模型或周期设置**时很有用。

#### CPU / CUDA / MPI

- 原生网格实现**同时支持 CPU 与 CUDA TorchScript 求值，包括 k 点计算**。
- CUDA 求值**显式选择**：

```fortran
&GAUXC
  NATIVE_GRID T
  NATIVE_GRID_USE_CUDA T
  NATIVE_GRID_CUDA_DEVICE -1
&END GAUXC
```

- `NATIVE_GRID_CUDA_DEVICE` **负值**把 **MPI 局部 rank 分配到可见 CUDA 设备**；**非负值**显式选择该可见设备。
- **CPU k 点计算需要兼容的 LibTorch/BLAS 运行时**（见 §2.6）。
- `NATIVE_GRID_ATOM_CHUNKS T` 在 MPI 计算中**按原子块分配模型求值**，**可降低 CUDA 峰值内存**；
  `NATIVE_GRID_ATOM_CHUNK_MAX_ROWS` 进一步限制**单次 Torch 调用处理的填充原子网格行数**。
  官方解释：这考虑了**不等原子网格尺寸所要求的矩形填充**；**原子块从不被拆分**，
  所以**单个块可以超过该限制**。
- 对 `ATOM_COMPOSITE`，拆分遵循 **Skala 的独立原子维度**，因此**也用于解析力与应力求值**；
  **完整的输入伴随在 CP2K 施加插值、划分、单中心导数之前被累积**。
- 对分子 `PAW_ONE_CENTER` 表示：**每个 rank 只组装自己拥有的原子**，
  径向 hard/soft 场**按 kind 复制一次**用于跨原子重叠。**每个活跃 rank 求值其完整的局部原子块**，
  rank 局部 Skala 能量**求和**。**特征伴随留在拥有它的 rank 上**，
  而 **smooth 平面波插值伴随全局求和**。官方说明：**Skala 1.1 通过其非局域层保留独立原子维度，
  所以这个分解是精确的**。CUDA + 自动设备选择时，**MPI 局部 rank 在各自可见 GPU 上执行其原子块**。

#### 原子与 GAPW 密度划分

- `NATIVE_GRID_ATOM_PARTITION` 把**原生网格行**分配给**原子特征块**。
  - `SMOOTH`（**[默认]**）用**可微的 Becke 式划分**；
  - `HARD` 把每个点分配给**最近的周期原子**，**用于遗留的能量/VXC 检查**；
  - **力与应力计算内部使用 smooth 划分**，因为**划分权重的导数会贡献到 Skala 响应**。
- `NATIVE_GRID_GAPW_DENSITY_PARTITION` **独立于**该空间原子划分，
  它选择 **PAW 式 `METHOD GAPW` / `METHOD GAPW_XC` 计算的单中心原始场项**。
  - `HARD_MINUS_SOFT`（**[默认]**）在**单次非线性 Skala 求值之前**把
    hard−soft 密度、密度梯度、动能密度加到 smooth 场；
  - `HARD_ONLY`、`SOFT_ONLY`、`NONE` 是**诊断变体**；
  - `DIRECT_VALENCE` **不论 `GPW_TYPE` 都用价密度路线**；
  - 遗留的 `CP2K_DEFAULT` 表示**可能从 kind 设置推断**该路线。
- `NATIVE_GRID_LAYOUT` 选择**组合原始场在哪个网格上形成**：
  - `ATOM_COMPOSITE`（**[默认]**）把 smooth 场**插值到 GAPW 径向/Lebedev 网格**，
    在那里**加上 hard−soft 场**，然后构造非线性 Skala 特征。在周期胞中，
    **对所有原子镜像的 Becke 式划分**负责**外能量求积**；**只对目标原子自镜像的单独划分**
    定义其**完整周期描述子域**，从而**避免非局域描述子在不同原子边界处被截断**。
  - `COMMON_GRID` 在**规则网格**上重构相同场，**保留为 cutoff 敏感的诊断参考**。
  - **官方实测结论**：在**匹配 cutoff** 时，完整原子块**既显著更接近对应的非周期原子复合极限，
    又比在一个全局周期网格上解析所有 hard−soft 细节便宜得多**。
  - **该选择器不改变物理密度表示**：全电子 GAPW、赝势 `DIRECT_VALENCE`、
    赝势 `PAW_ONE_CENTER` 在两种布局上**各自保持语义**；**也不影响分子 GauXC 求积**。
  - **官方明确警告**：分子 GauXC `DIRECT_VALENCE` 与原生 `PAW_ONE_CENTER` 是**不同的赝势密度表示**；
    **周期与非周期原子复合计算之间的一致，并不意味着与直接 AO 价结果相等**。
  - 混合全电子/赝势 GAPW kind **用同一输入语法**。`ATOM_COMPOSITE` 构造每个目标原子块，
    **只为需要它们的 kind 加 hard−soft 原始场**，并施加**匹配的按 kind 伴随**。
    `COMMON_GRID` 诊断**不提供这种混合按 kind 重构**，因此**对混合芯表示不可用**。
  - **有限全电子单中心表示误差可独立收敛**：通过 `DFT%QS%GAPW_1C_BASIS` 与 kind 的径向/Lebedev 网格。
    例如**要求苛刻的分子交叉检验**可用 `EXT_VERY_LARGE` 配 **200 径向 + 590 Lebedev 点**。
    **官方说明这些设置不自动施加**，因为**成本很大且所需求积依赖元素与目标精度**。

#### 当前范围（官方）

原生网格路径为下列情形提供**能量、VXC、核力、解析应力**：

- 规则网格 GPW 配 **GTH/ECP 赝势**；
- **全电子 GAPW**；
- 赝势 GAPW（`GPW_TYPE` 或 PAW 式单中心校正）；
- **`ATOM_COMPOSITE` 上的混合全电子/赝势 GAPW**；
- `METHOD GAPW_XC`。

NLCC **对原生规则网格表示与赝势 GAPW `PAW_ONE_CENTER` 都支持**。
周期 `PAW_ONE_CENTER` **默认用原子中心复合后端**；其平滑格点镜像划分、原生网格插值、
周期镜像、单中心场**为核力与应变做了一致微分**。

**NLCC 的官方技术细节（重要）**：
- 对原生网格 NLCC，CP2K **在实空间与倒空间都把冻结芯密度加到每个自旋密度**，然后再构造 Skala 特征；
- 在分子原子复合路线中，**同一芯场在划分后的径向/Lebedev 行上解析求值**；
- 模型**在组合的价+芯原始场上求值一次**，保留**密度/芯与梯度交叉项**；
- **官方原文强调**：**NLCC 增强 ρ 与 ∇ρ，而 τ 保持仅价电子**；
- 官方说明：这遵循 CP2K 的**类 meta-GGA 的 NLCC 约定**，但**与全电子冻结芯表示不完全相同**，
  因为**没有提供芯动能密度**。因此**NLCC 对"与全电子参考一致性"的影响必须针对目标化学做验证，
  而不能假定它系统性地有益**。

**k 点密度矩阵**用 CP2K 标准权重与对称约化。**已测试范围**包括：
**仅反演约化、完整 K290 约化、SPGLIB 约化**，用于 GPW/GTH、全电子 GAPW、
以及配 GTH/ECP 赝势的 PAW 式 GAPW。

**官方明确的范围外清单**：**ROKS、ADMM、非 k 点多镜像计算**仍**在当前范围之外**。

**官方结论**：因为这是**实验性接口**，**在生产使用前应针对所选模型与体系验证能量、力、应力**。

### 2.5 故障排查（官方）

| 现象 / 手段 | 官方说明 |
|---|---|
| `CP2K_GAUXC_STATUS_STDERR=1` | 把 GauXC 状态消息**镜像到标准错误**。当启动器或 CI 系统在外部库失败后**不保留 CP2K 输出文件**时有用 |
| TorchScript 模型运行时 | **需要与 CP2K 的 BLAS、ScaLAPACK、OpenMP 运行时兼容的 LibTorch 安装**。预构建 LibTorch 发行版可能**捆绑 oneMKL 符号**，其**分组 SGEMM/DGEMM 接口与同名 OpenBLAS 入口点不兼容**。对 **LP64 OpenBLAS** 构建，CP2K **通过标准 CBLAS 接口展开这些分组操作**。其它混合 BLAS 接口**仍需要一致构建的数值栈** |
| **官方明确禁止的做法** | **不要**为了绕过问题把 oneMKL **预加载进链接 OpenBLAS 的 CP2K**——**被插入的复 BLAS 符号会破坏 ScaLAPACK k 点路径** |
| `OUTPUT_PATH` | 把 GauXC 分子与基组诊断**写到已存在的目录**。**要求 GauXC 编译时带 HDF5 支持** |

### 2.6 参见

官方 `See Also`：Libraries、Gaussian Plane Wave、Gaussian Augmented Plane Waves。

> **[G层提示]** GauXC 页面是 G 层采到的**信息密度最高的页面之一**，但**没有给出完整的可运行输入**。
> 实际使用请以 CP2K 官方 regtest 与 GauXC 文档为准。**Skala 是微软发布的机器学习 XC 泛函**，
> 属于"用 ML 模型替代解析泛函"的路线，与 `22_ml_embedding_dlaf.md` 里的 ML **势**不同层次。

---

## 3. 静电与泊松求解器（Electrostatics and Poisson Solvers）

> 来源页：`methods/dft/electrostatics/index.html`

### 3.1 核心立场（官方原文）

**官方开篇定性**：静电边界条件**是物理模型的一部分，不只是数值设置**。
它们决定**哪些周期镜像相互作用**、**带电计算是否需要补偿电荷**、
以及**哪些总能量差是有意义的**。**官方要求**：**在收敛胞尺寸之前就显式设置它们**。

> **[G层提示]** 这句话值得单独记住：**"边界条件是物理，不是数值"**。
> 凡是 slab / 带电体系 / 隐式溶剂的计算，先定边界条件，再谈收敛。

### 3.2 两个必须区分的周期性设置（官方）

| 设置 | 官方说明 |
|---|---|
| `CELL/PERIODIC` | 控制**原子体系**的周期性，**包括几何与配对表（pair lists）** |
| `POISSON/PERIODIC` | 选择**静电格林函数**的周期方向 |

**官方要求**：二者**通常应描述同一个物理体系**。
CP2K **允许不同取值**（因为某些专门工作流需要），但**不匹配会让计算的不同部分使用不同的镜像**。
**官方明确禁止**：**不要仅仅为了在真空方向压制相互作用而使用不匹配**。

**IMPLICIT 求解器的独立关键字（官方强调）**：
广义 `IMPLICIT` 求解器有**额外的、独立的** `BOUNDARY_CONDITIONS` 关键字。
**其默认是 `PERIODIC`**，所以 **`POISSON_SOLVER IMPLICIT` 不会仅仅因为 `POISSON/PERIODIC` 被设为
`X`、`XY` 或其它降低的周期性就变成 1D 或 2D 求解器**。
**需要非周期、混合或介电边界条件时，必须显式配置 `IMPLICIT` 子段。**

**官方示例（slab，x/y 周期）**：

```fortran
&SUBSYS
  &CELL
    ABC 10.0 10.0 20.0
    PERIODIC XY
  &END CELL
  # ...
&END SUBSYS

&DFT
  &POISSON
    PERIODIC XY
    POISSON_SOLVER ANALYTIC
  &END POISSON
  # ...
&END DFT
```

### 3.3 求解器总览（官方表）

**官方指引**：**从预期的周期性与边界条件来选择 `POISSON_SOLVER`**。
**Input Reference 是当前支持组合的权威列表**。

| 求解器 | 支持周期性 | 官方主要考虑 |
|---|---|---|
| `PERIODIC` | 3D | 标准**全周期倒空间解** |
| `ANALYTIC` | 0D, 1D, 2D | 解析倒空间格林函数；**收敛可能很慢** |
| `MT` | 0D, 2D | **Martyna–Tuckerman 镜像解耦**。**胞必须至少是完整电子密度范围的两倍** |
| `MULTIPOLE` | 0D | 用**原子中心高斯**拟合总电荷以解耦周期镜像 |
| `WAVELET` | 0D, 2D, 3D | **密度必须在非周期胞面处衰减到零** |
| `IMPLICIT` | 广义 0D–3D | 支持周期、Neumann、混合 Dirichlet/周期条件与**空间变化的介电**。**必须显式配置其边界条件** |

**官方警告（重要）**：**当电子密度延伸到超过胞的一半时，`MT` 可能返回完全错误的结果。**
**相关范围包括弥散密度尾部，而不只是核坐标。**

**官方选型建议**：

| 体系 | 官方建议 |
|---|---|
| 孤立、局域的分子或团簇 | `MT`、`WAVELET` 或 `MULTIPOLE` 是常见 0D 选择；`ANALYTIC` 与 `IMPLICIT` 提供更多选项 |
| slab | **通常需要真正的 2D 求解器，或显式构造的混合边界条件** |
| 线（wire） | 用**支持 1D 周期性**的求解器 |
| 全周期体相 | 通常用 `PERIODIC` |

### 3.4 带净电荷的体系（官方，最易踩坑处）

**官方原文**：**非中性周期胞的静电能在没有额外约定时是未定义的**。

**3D `PERIODIC` 求解器下 CP2K 的约定**：
- 使用**均匀补偿背景**；
- **省略奇异的零倒空间分量**；
- 因此**电子密度、离子电荷、背景共同构成一个静电问题**；
  **单独的电子-背景或离子-背景能量没有独立意义**。

**有限尺寸误差（官方）**：
- 增大胞体积会**降低背景密度**，但也**改变与周期镜像的相互作用**；
- 因此**带电 3D 计算有一个依赖胞尺寸与胞形状的有限尺寸误差，通常只按代数方式衰减**；
- **CP2K 不会仅从 `CHARGE` 推断一个通用的物理校正**；
- **官方要求**：**只在使用了相同边界条件与势零点约定的计算之间比较能量**，
  或者施加**适合物理模型的校正**。

**0D 与部分周期体系的差别（官方）**：
- **孤立 0D 求解器**可以给局域带电团簇一个**有限能量**而无需周期背景，**只要密度被包含在数值胞内**；
- **部分周期体系不同**：**单位长度或单位面积的净电荷会产生长程场**。
  **没有显式反电荷、电极、电解质或其它补偿模型时**，
  **带电 1D 线或 2D slab 的能量通常没有与真空无关的孤立极限**；
  **此时增大真空可能改变报告的能量，而不是使其收敛**。

**官方重要提示（原文级）**：
**不同泊松求解器给出的总能量对带电体系不自动在同一参考上。**
静电势的**常数平移对中性胞无关紧要，但会改变净电荷非零胞所被赋予的能量**。
因此**求解器之间的一致本身并不是有效的正确性检验**。

**官方关于模型的立场**：隐式溶剂、平面反电荷、电极模型**可以使带电界面成为一个定义良好的物理问题**，
但它们**描述的是不同的体系**。
**应从实验或热力学边界条件来选择这类模型，而不是当作事后施加的数值校正**。

### 3.5 收敛真空与胞尺寸（官方流程）

**官方要求：用保持物理模型的收敛序列**：

1. **先选定**周期方向、泊松求解器、电荷补偿模型、势参考。
2. **`CUTOFF` 与 `REL_CUTOFF` 分开收敛**。
3. **0D 体系：放大每个非周期方向。slab 或 wire：只放大非周期方向。**
   **保持结构居中**，**保持基组、泛函、SCF 阈值、周期胞矢量不变**。
4. **记录相对于最大胞的能量差，以及力，并在相关时记录平面平均势与电荷密度。**
   **检查密度在每个求解器所要求的非周期边界处都可忽略。**
5. **如果 FFT 网格变化可能与真空尺寸趋势混淆，就在更高的网格 cutoff 重复。**

**官方判据**：
- 对**中性局域体系**，一旦镜像相互作用、密度截断、网格变化**都低于目标精度**，总能量**应达到平台**；
- 对**带电 3D 超胞**，**在均匀背景约定下分析有限尺寸趋势**；
- 对**带电 1D 或 2D 体系**，**在静电模型包含物理所需的补偿之前，
  不要把缺乏平台解释为数值失败**。

**官方最后一个警告**：**弥散基函数可能产生集中在真空中的态，尤其是带电表面。**
**在加真空或弥散函数时检查轨道与密度**——否则**改变胞可能同时改变电子态与其静电有限尺寸误差**。

### 3.6 参考文献（官方给出）

Martyna1999、Blöchl1995、Genovese2006、Genovese2007、BaniHashemian2016。

---

## 4. Hartree-Fock 交换：RI 与 ADMM

> 来源页：`methods/dft/hartree-fock/index.html`（导航）、`.../admm.html`、`.../ri_gamma.html`、`.../ri_kpoints.html`

### 4.0 官方导航结构

`methods/dft/hartree-fock/` 下三个子页：

- **HFX with ADMM**（`admm.html`）
- **HFX-RI for Γ-Point (non-periodic)**（`ri_gamma.html`）
- **HFX-RI with k-Points**（`ri_kpoints.html`）

**官方开篇定性**：RI 技术在 CP2K 中**为多种方法实现，每次略有不同的风味**。
**HFX 有两个不同的 RI 实现**：一个用于 **k 点采样**，一个用于 **Γ 点计算**。

### 4.1 RI-HFX（Γ 点，非周期）

**实现文献**：Bussy2023。

#### 应用领域（官方）

**官方明确**：CP2K 的 RI-HFX 实现**对使用大基组的分子、以及小/中等尺寸固体**证明特别高效。
**对大型稀疏周期体系（如水），原始 4 中心 HFX 实现更高效。**

**官方补充**：
- **ADMM 可与 RI-HFX 无缝配合使用**；
- **核力与应力张量可用**。

#### 理论要点（官方）

Γ 点下，精确交换对 KS 矩阵的贡献由**密度矩阵与 2 电子 4 中心电子排斥积分（ERI）收缩**得到：

```
K_μν = P_σλ Σ_{a,b,c} (μ⁰ σ^a | ν^b λ^{a+c})
```

- AO 指标**隐式求和**（爱因斯坦约定）；
- `a, b, c` 对应**模拟胞的周期镜像**；
- **周期镜像求和可以一次做完**，得到**单个 4 中心量** (μσ|νλ)；
- **非周期边界条件下的分子**：`a = b = c = 0`。

**RI 近似**下用 2 中心与 3 中心 ERI 代替：

```
K_μν = P_σλ [ (μσ⌊P) (P⌊Q)^{-1} (Q|R) (R⌊S)^{-1} (S⌊νλ) ]
```

- `P, Q, R, S` 是**构成全局 RI 基的 GTO**，**理想上覆盖所有可能 AO 乘积的空间**；
- `⌊` 表示 **RI 度量**，**通常取比 HFX 势更短程**；
- **最短程的 RI 度量是重叠**，得到**著名的 RI-SVS 近似**。

**代价特性（官方，重要）**：
- 用 RI-HFX 时，**计算瓶颈从"算 4 中心 2 电子 ERI"转移到"稀疏张量收缩"**；
- **通常 RI-HFX 内存占用更低，且有 GPU 加速**；
- **但其渐近标度是 ~O(N³)，而 4 中心 HFX 是线性的**；
- **因此 RI-HFX 更适合较小的稠密体系与分子。**

#### 例 1：分子（甘氨酸，HF/cc-pVQZ）

官方设置：**Hartree-Fock 级别**的甘氨酸**几何优化**，基组 **cc-pVQZ**（取自 basissetexchange）。
**RI 基组在 KIND 段以 `RI_HFX` 引用，本示例由用户显式提供**。
官方说明：**16 CPU 上每个几何优化步约 70 秒**。

**官方的三条 take-home messages**：

1. **如果存在优化过的 RI 基组（如本例的 `cc-pVQZ-JKFIT`），应使用它们以提高效率。**
   它们**比自动生成的对应物更小，尽管有时不够精确**。
2. **非周期计算中，对 HFX 势与 RI 度量都使用 1/r 默认库仑相互作用。**
   **短程 RI 度量引入稀疏性并降低 (μσ⌊P) 的计算成本，而这在 PBC 中才真正有用。**
3. **本特定示例中，RI-HFX 比原始 4 中心实现高效得多。**
   可以**注释掉 `HF/RI` 段**跑同一输入做演示对比。

**官方完整输入（原样）**：

```fortran
&GLOBAL
  PROJECT glycine
  PRINT_LEVEL MEDIUM
  RUN_TYPE GEO_OPT
&END GLOBAL
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME BASIS_cc-pVQZ
    POTENTIAL_FILE_NAME POTENTIAL
    !Sort basis function accoring to their exponent for more sparsity
    SORT_BASIS EXP

    &MGRID
      CUTOFF 500
      REL_CUTOFF 50
      NGRIDS 5
    &END MGRID

    &QS
      !all-electron calculations require GAPW
      METHOD GAPW
    &END QS

    &POISSON
      !non-periodic calculation for this molecule
      PERIODIC NONE
      PSOLVER WAVELET
    &END

    &SCF
      EPS_SCF 1.0E-6
      MAX_SCF 50
      &END SCF
    &XC
      &XC_FUNCTIONAL NONE
      &END XC_FUNCTIONAL
      &HF
        !Pure RI Hartree-Fock calculation using only defaults:
        ! -HFX potential is the 1/r Coulomb interaction
        ! -RI metric is also the 1/r Coulomb interaction
        ! -Default accuracy parameters (good in most cases)
        &RI
        &END RI
      &END HF
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 10.0 10.0 10.0
      PERIODIC NONE
    &END CELL
    &COORD
      C -0.04879702 -0.00000000 1.40419128
      N -1.35021542 0.00000000 2.04225544
      C -0.04354337 0.00000000 -0.12235209
      O -1.02422569 -0.00000000 -0.83489570
      O 1.22983691 0.00000000 -0.61028238
      H 1.14837668 -0.00000000 -1.58391528
      H 0.53209836 -0.87421885 1.73662058
      H 0.53209836 0.87421885 1.73662058
      H -1.88873390 0.81280508 1.74087629
      H -1.88873390 -0.81280508 1.7408762
    &END COORD
    &TOPOLOGY
      !Always a good idea to put the molecule in the middle of the simulation cell in non-PBCs
      &CENTER_COORDINATES
      &END CENTER_COORDINATES
    &END TOPOLOGY
    &KIND C
      BASIS_SET cc-pVQZ
      BASIS_SET RI_HFX cc-pVQZ-JKFIT
      POTENTIAL ALL
    &END KIND
   &KIND O
      BASIS_SET cc-pVQZ
      BASIS_SET RI_HFX cc-pVQZ-JKFIT
      POTENTIAL ALL
    &END KIND
    &KIND N
      BASIS_SET cc-pVQZ
      BASIS_SET RI_HFX cc-pVQZ-JKFIT
      POTENTIAL ALL
    &END KIND
    &KIND H
      BASIS_SET cc-pVQZ
      BASIS_SET RI_HFX cc-pVQZ-JKFIT
      POTENTIAL ALL
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

**官方在这段输入里体现的要点**：
- `SORT_BASIS EXP`：**按指数排序基函数以获得更好的稀疏性**；
- `METHOD GAPW`：**全电子计算需要 GAPW**（因为 `POTENTIAL ALL`）；
- `PSOLVER WAVELET` + `PERIODIC NONE`：非周期分子；
- `&XC_FUNCTIONAL NONE` + `&HF/&RI`：**纯 RI Hartree-Fock**；
- `&CENTER_COORDINATES`：**非 PBC 中把分子放到胞中心总是好主意**；
- `BASIS_SET RI_HFX cc-pVQZ-JKFIT`：**显式指定 RI 基组**。

#### 例 2：固体（64 原子 Si，ADMM-PBE0）

**官方说明**：本例用 **ADMM-PBE0 级别**计算 **64 原子体硅胞**的能量。
**因为不存在与 `admm-dzp` 对应的预优化 RI 基组，RI 基组是即时生成的（on the fly）**。
这里 PBE0 的 **25% 精确交换分数**被计算。

> **[G层提示]** 官方对例 2 的正文在此处**截断于该句**（页面原文如此），
> 未给出完整输入。**缺口已登记于 §11。**

### 4.2 RI-HFXk（k 点）

**实现文献**：Bussy2024。

#### 应用领域（官方）

**官方明确**：带 k 点采样的 RI-HFX（**RI-HFXk**）**针对小单胞与稠密 k 点网格的模拟做了优化**。
它**比等价的 Γ 点超胞计算高效得多**。

#### 理论要点（官方）

k 点采样下，给定 k 点处精确交换对 KS 矩阵的贡献：

```
K_μν^k = Σ_k' P_σλ^{k'} (μ^k σ^{k'} | ν^k λ^{k'})
```

**官方说明**：CP2K 中**大多数 k 空间矩阵都通过其实空间对应物的傅里叶变换得到**，
精确交换矩阵也是如此：

```
K_μν^k = Σ_R e^{i k·R} K^R_μν
```

其中 `R` 是**模拟胞周期镜像的平移矢量**。实空间矩阵：

```
K^b_μν = Σ_{a,c} P_σλ^c (μ⁰ σ^a | ν^b λ^{a+c})
```

**官方特别指出**：**在 Γ 点计算中只有一个 k 点（k = 0）**，
导致**所有 c 的密度矩阵相同**，于是**可以把它移出求和**，
就**恢复了前面 Γ 点的公式**。

**RI-HFXk 的实空间精确交换矩阵用"局域、原子特异的 RI 基"计算**：

```
K^b_{μi,νj} = Σ_{a,c} P^c_{σλ}
              (μ⁰_i σ^a ⌊ P⁰_i) (P⁰_i ⌊ R⁰_i)^{-1} (R⁰_i | S^b_j)
              (S^b_j ⌊ Q^b_j)^{-1} (Q^b_j ⌊ ν^b_j λ^{a+c})
```

- 指标 `i, j` 指**原子**；
- `K^b_{μi,νj}` 对应**周期镜像 b 的矩阵中 i、j 原子块**里的 μ、ν AO 对；
- **原子 i 在参考胞中的局域 RI 基 {P⁰_i}**，由**以原子 i 为中心、半径 R_max 的球内所有原子的 RI 基元素**组成；
- **`R_max` 是体系中最弥散 AO 的范围**；
- 官方说明：更多细节见**已接受、尚未发表的论文**。

**代价特性（官方，重要）**：
- **因为构造实空间交换矩阵是计算中最昂贵的部分，该方法的成本与 k 点网格无关（常数）**；
- **当 k 点数目变高（~1000）时，标度变为线性**，因为**必须在每个 k 点对角化一个矩阵**；
- **ADMM 可与 RI-HFXk 无缝配合使用**。

#### 例：石墨烯能带（ADMM-PBE0）

**官方设置**：
- 用 `pob-TZVP-rev2` 基组，**因为它不弥散，因此高效**；
- **官方补充**：更弥散的基组（如 CP2K 随附的 `ccGRB` 家族）**似乎产生更稳健的结果**；
- ADMM 辅助基组用**较低质量的 `pob-DZVP-rev2`**。

**流程（官方）**：
1. 先用**稠密通用 k 点网格**收敛 SCF。本例用 **19×19×1 Monkhorst–Pack**；
   **官方指出**：狄拉克锥所在的特殊点 K **不显式在网格中**——
   这**允许更简单的计算**（体系被当作半导体处理），
   但**网格足够稠密以致物理被很好捕获**。
2. SCF 收敛后，**实空间 KS 矩阵集合 F^b_μν 被反傅里叶变换**到输入中指定的 k 点路径上的 F^k_μν；
3. **对角化**，用其本征值作为能带能量；
4. **可用 `cp2k_bs2csv` 把 CP2K 输出转成更易处理的 CSV 文件**。

**官方给的关键参数说明**：
- `EPS_PGF_ORB` 设为 **1.0×10⁻⁶**：**该参数控制 AO 的范围，因此决定局域原子特异 RI 基的范围**。
  **这个值带来特别高的精度**；**默认 1.0×10⁻⁵ 通常足够**。
- **HFX 势选为截断库仑算符（Truncated Coulomb），截断半径 R_C = 5.0 Å**。
  **对所有周期 HFX 计算，都需要有限程势。**
  **k 点情形下，半径 R_C 的球必须能装进 BvK 超胞**
  （**等价于 Γ 点计算中的 L/2 要求**）。**不满足要求会发警告**。
  **理想截断半径依赖体系，应仔细测试。实践中大多数计算从 R_C = 6.0 Å 起收敛。**
- **输入中未指定 RI 度量**。**默认对 HFX 势与 RI 度量用同一个算符**
  （本例为 TC 配 R_C = 5.0 Å）。
  **与 Γ 点计算相反，用更长程的 RI 度量在 RI-HFXk 中不会显著影响速度，同时保证尽可能好的精度。**
- **像大多数 HFX 计算一样，从收敛的 PBE 波函数重启可加速 SCF 收敛。**
  **注意 k 点重启文件中转储的是实空间密度矩阵。**
  **然而 HFX 计算比 PBE 需要多得多的镜像**，因为**精确交换是非局域的**。
  **在初始 PBE 计算中用非常紧的 `EPS_PGF_ORB`（如 1.0×10⁻¹²）会在那里也产生很多镜像。**
- **计时（官方）**：从 PBE 波函数重启时 32 CPU 约 5 分钟，否则 10 分钟。

**官方完整输入（节选，含关键段）**：

```fortran
&GLOBAL
  PROJECT graphene_kp
  RUN_TYPE ENERGY
&END GLOBAL
&FORCE_EVAL
  &DFT
    BASIS_SET_FILE_NAME BASIS_pob
    POTENTIAL_FILE_NAME POTENTIAL
    SORT_BASIS EXP
    AUTO_BASIS RI_HFX MEDIUM
    !restarting from a converged PBE calculation lead to less SCF steps
    WFN_RESTART_FILE_NAME graphene_pbe-RESTART.kp

    !Turning on the ADMM approximation
    &AUXILIARY_DENSITY_MATRIX_METHOD
      ADMM_TYPE ADMMS
    &END AUXILIARY_DENSITY_MATRIX_METHOD

    &QS
      !sometimes necessary when running small systems with a lot of CPUs
      PW_GRID_BLOCKED FALSE
      METHOD GAPW
      !needs to be the same value as that in RI%EPS_PGF_ORB
      EPS_PGF_ORB 1.0E-6
    &END  QS

    &MGRID
      CUTOFF 600
      REL_CUTOFF 60
      NGRIDS 5
    &END MGRID

    &SCF
      EPS_SCF 1.0E-06
      MAX_SCF 50
      !typically need lower threshold to start DIIS with k-points
      EPS_DIIS 0.05
      SCF_GUESS RESTART
    &END SCF

    &XC
      &XC_FUNCTIONAL
        &PBE
          SCALE_X 0.75
        &END
      &END XC_FUNCTIONAL
      &HF
        FRACTION 0.25
        &RI
          KP_NGROUPS 16
          !using a smaller than default EPS_PGF_ORB allows for a
          !more accurate calculation with a larger local RI basis
          EPS_PGF_ORB 1.0E-6
          &PRINT
            !prints an estimate of required memory per MPI rank
            KP_RI_MEMORY_ESTIMATE
            !prints a progress bar for the current SCF step
            KP_RI_PROGRESS_BAR
          &END PRINT
        &END RI
        &INTERACTION_POTENTIAL
          !Always use a limited ranged potential in PBCs
          POTENTIAL_TYPE TRUNCATED
          CUTOFF_RADIUS 5.0
```

**官方在注释里给出的关键提示（原文）**：
- `PW_GRID_BLOCKED FALSE`：**在小体系上跑很多 CPU 时有时是必要的**；
- `EPS_PGF_ORB` **必须与 `RI%EPS_PGF_ORB` 取相同值**；
- `EPS_DIIS 0.05`：**带 k 点时通常需要更低的阈值来启动 DIIS**；
- `KP_NGROUPS 16`：**k 点 RI 的组数**；
- `KP_RI_MEMORY_ESTIMATE`：**打印每个 MPI rank 所需内存的估计**；
- `KP_RI_PROGRESS_BAR`：**打印当前 SCF 步的进度条**；
- `POTENTIAL_TYPE TRUNCATED` + `CUTOFF_RADIUS 5.0`：**在 PBC 中总是用有限程势**。

> **[G层提示]** 页面正文在 `CUTOFF_RADIUS 5.0` 之后**截断**（HTML 页面的代码块如此），
> 后续的 `&INTERACTION_POTENTIAL` 闭合、`&KIND`、`&SUBSYS`、k 点网格设置**未在页面给出**。
> **缺口已登记于 §11。**

#### RI-HFX vs RI-HFXk 对照（G 层归纳）

| 维度 | RI-HFX（Γ 点） | RI-HFXk（k 点） |
|---|---|---|
| 文献 | Bussy2023 | Bussy2024 |
| 适用 | **大基组分子、小/中尺寸固体** | **小单胞 + 稠密 k 点网格** |
| 不适用 | 大型稀疏周期体系（用水举例，4 中心更好） | — |
| 成本标度 | ~O(N³) | **与 k 点网格无关**；k 点 ~1000 后变线性 |
| RI 基 | **全局 RI 基** | **局域、原子特异 RI 基**（半径 R_max = 最弥散 AO 范围） |
| RI 度量 | **非周期用 1/r 默认**；短程度量在 PBC 才有用 | **默认与 HFX 势同一算符**；更长程不显著影响速度 |
| 势要求 | 非周期用 1/r | **必须有限程势**；R_C 球须装进 BvK 超胞；多数从 R_C = 6.0 Å 起收敛 |
| 内存 / GPU | 内存占用更低，GPU 加速 | — |
| ADMM | **可无缝配合** | **可无缝配合** |
| 力 / 应力 | **核力与应力张量可用** | — |

### 4.3 ADMM 补充要点（`02_dft_methods.md` §6 之外的官方内容）

**官方对 ADMM 的定位（原文）**：ADMM **通过把密度矩阵从主轨道基投影到更小的辅助基**，
**降低杂化 DFT 中 Hartree-Fock 交换的成本**。
CP2K **在辅助基中求值精确交换，并为"主基与辅助基交换描述之差"加一个校正项**。

**官方明确**：ADMM **在精确交换是瓶颈时最有用，尤其是配更大或更弥散高斯基组时**。
**常用于杂化 DFT**；**ADMM2 变体也被若干复用精确交换机制的后 SCF 方法支持**。

#### 基本设置三要素（官方）

1. **杂化泛函或其它求值 HFX 的设置**；
2. **每个原子 kind 的辅助基组**，用 `BASIS_SET AUX_FIT` 指定；
3. **`AUXILIARY_DENSITY_MATRIX_METHOD` 段**，选择 ADMM 变体与校正泛函。

官方示例：

```fortran
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

#### 选辅助基（官方，补充）

- 辅助基应**为主基家族和预期精度而选**；
- **MOLOPT 式计算**：`BASIS_ADMM_MOLOPT` 家族提供紧凑辅助基；
- **较新的 UZH 基组集**含 `BASIS_ADMM_UZH` 及相关基组文件，用于 **correlation consistent 设置**；
- **全电子计算**可用**全电子辅助基组**（如果有）。

**官方关键定性**：**辅助基是近似的一部分**。
**太小的辅助基会使交换校正变大并降低精度；太大则回吐的加速变少。**
**官方要求**：**生产工作中至少测试一个更大的辅助基，或与不用 ADMM 的更小参考体系对比。**

#### 选变体（官方，补充）

- `ADMM_TYPE` 是**快捷方式**，**一致地设置投影、纯化、缩放选项**；
- `ADMM1` 与 `ADMM2` 是**原始变体**；`ADMMS`、`ADMMP`、`ADMMQ` **使用后来引入的额外模型**；
- **官方推荐**：**`ADMM2` 通常是"超越基态杂化 DFT 的工作流"中最广泛支持的变体**；
- `EXCH_CORRECTION_FUNC` 选择 **ADMM 校正所用的交换泛函**，
  **应与主 XC 设置的交换部分一致选择**；**`PBEX` 是 PBE 基杂化计算的常见选择**。

#### 实践检查（官方 4 条）

- **保持与不用 ADMM 时相同的主基与势收敛检查**；
- **检查对辅助基大小的敏感性**；
- **对小型代表性体系，把总能、力或目标性质与不用 ADMM 的参考对比**；
- **记住 ADMM 加速交换计算，但不替代主高斯基、实空间网格或 SCF 阈值的收敛。**

**参考文献（官方 See Also）**：Guidon2009、Guidon2010、Merlot2014、Iannuzzi2026。

---

## 5. LRIGPW 补充：官方"何时用"判据

> 来源页：`methods/dft/local_ri.html`（`02_dft_methods.md` §5 已覆盖原理与用法，此处只补官方判据）

**官方明确的前提**：**LRIGPW 只有在"实空间网格上的操作（密度的 collocation 与势的积分）
在计时中占主导"时才有益。**

**官方给出的反面判据（重要）**：
- **金属体系通常不是这种情况**——因为**KS 矩阵的对角化对计算成本贡献很大**；
- **LRIGPW 对凝聚相体系（液体、分子晶体等）高效**。

**官方明确列出"可获得特别大加速"的三种情形**：

1. **非正交胞（non-orthorhombic cells）**；
2. **大的网格 cutoff**；
3. **很多 SCF 步**。

**官方进一步说明**：
- **用 LRI，SCF 步被加速，因此单点计算获益最大**；
- **对分子动力学，波函数可以从上一步外推，SCF 收敛很快**。
  **这种情况下也能获得加速，取决于网格 cutoff 与体系**；
- **官方警告**：**LRIGPW 比标准 GPW 方案有更高的内存需求**。
  **这在 HPC 平台上通常不是问题，但可能限制在较小集群上的使用。**

**官方示例输入**：`lrigpw_example.inp`（Ice XV）。

**参考文献**：Golze2017b（LRIGPW 综合描述）、Golze2017。

---

## 6. GPW / GAPW 补充：官方流程图与结论

> 来源页：`methods/dft/gpw.html`、`methods/dft/gapw.html`（`02_dft_methods.md` §1 已覆盖，此处只补官方原文级表述）

### 6.1 GPW 的官方核心表述

**官方原文**：CP2K 中的**主基由高斯型轨道（GTO）函数构成**。
为利用 **FFT 算法高效求解泊松方程**，**电子密度必须先从 GTO 表示转移到规则网格**——
这称为 **collocation**。求解泊松方程后，**得到的静电势必须再转回 GTO 基**——这称为 **integration**。

**官方对方法本质的定性（原文）**：
**这种在高斯与平面波表示之间"机会主义式"的切换，就是 GPW 方法的核心思想。**

**官方流程图（原样）**：

```
el. Density (Gaussian Basis)
    -- Collocate -->  el. Density (Regular Grid)
    -- FFT -->        el. Density (Plane Waves)
    -- Poisson Solver --> el. Potenial (Plane Waves)
    -- FFT-1 -->      el. Potenial (Regular Grid)
    -- Integrate -->  el. Potenial (Gaussian Basis)
```

**官方 See Also**：`https://www.cp2k.org/gpw`、`https://www.cp2k.org/quickstep`、Lippert1997、Kühne2020。

### 6.2 GAPW 的官方核心表述

**官方原文**：GAPW **扩展了 GPW，使全电子计算和非常小芯赝势的计算在 CP2K 中变得可行**。
**核心思想**：**把密度的平滑部分留在常规 GPW 网格上，而用原子中心贡献处理核附近快速变化的密度**。

**官方适用场景**：**芯电子密度重要时**——例如**全电子计算、芯能级光谱、磁性质、
以及某些小芯赝势设置**。

**官方明确结论**：**对标准的仅价电子赝势 DFT 计算，GPW 通常更简单更快。**

**官方示例（全电子 GAPW）**：

```fortran
&KIND O
  BASIS_SET SVP-MOLOPT-GGA-ae
  POTENTIAL ALL
  LEBEDEV_GRID 110
  RADIAL_GRID 80
&END KIND
```

**官方说明**：完整测试过的水分子示例为 **`gapw_h2o.inp`**；
它**故意做得很小，意在作为起点而非生产级基准**。

**GAPW 精度参数（官方逐个）**：

| 关键字 | 官方描述 |
|---|---|
| `EPSFIT` | 控制**高斯指数如何拆分为 hard 与 soft 部分**。**降低它会把更硬的函数纳入 soft density，通常需要更大的 `CUTOFF`** |
| `EPSRHO0` | 控制 **hard compensation density 贡献所用的范围** |
| `EPSSVD` | 控制 **projector matrices 的奇异值分解容差** |

> **[G层提示]** `02_dft_methods.md` §1.2 已把这三个参数连同 `LEBEDEV_GRID`/`RADIAL_GRID`
> 和实践指引（检查电子计数、按需收紧、提高 CUTOFF、不需要时优先 GPW）整理为表，此处不重复。

---

## 7. 基组与赝势补充

> 来源页：`methods/dft/basis_sets.html`、`methods/dft/pseudopotentials.html`
> （`14_basis_and_potentials.md` 已覆盖文件格式、GTH 元素清单等，此处只补官方新表述）

### 7.1 基组页的官方关键立场

**官方原文（重要，与纯平面波代码的对比）**：
在 CP2K 的 Quickstep 模块中，**KS 轨道用原子中心高斯基函数展开**。
**这与纯平面波代码不同**：
**增大实空间网格 `CUTOFF` 会改善密度与势的辅助平面波表示，
但它本身并不会达到完备基组极限。**
**官方要求**：**为系统收敛，高斯基质量与网格参数必须一起考虑。**

> **[G层提示]** 这条是**基组收敛与 CUTOFF 收敛必须分开做**的根本原因。
> 结合 `03_scf_convergence.md` 的 CUTOFF 收敛教程，就构成完整的收敛策略。

**基组文件查找位置（官方）**：`BASIS_SET_FILE_NAME` 列出的文件，
**CP2K 在当前目录与配置的 CP2K 数据目录中搜索**。

**官方基础示例**：

```fortran
&FORCE_EVAL
  &DFT
    BASIS_SET_FILE_NAME BASIS_MOLOPT
  &END DFT
  &SUBSYS
    &KIND O
      BASIS_SET DZVP-MOLOPT-GTH
    &END KIND
    &KIND H
      BASIS_SET DZVP-MOLOPT-GTH
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

### 7.2 基组命名的官方解读

**官方说明**：许多 CP2K 基组**在名字里编码了用途**：

| 名字片段 | 官方说明 |
|---|---|
| `SZV`、`DZVP`、`TZVP`、`TZV2P`、`QZVPP` | **表示递增的基组质量** |
| `MOLOPT` | **分子优化**的高斯基组，**常与 GPW 配合使用** |
| `SR` | **短程 MOLOPT 变体**。**更不弥散**，在**目标性质不需要弥散函数**时，**对大型凝聚相体系常更高效** |
| `GTH` | **为 GTH 赝势计算设计**的基组 |
| `q1`、`q4`、`q6` 等后缀 | 表示**匹配的赝势所代表的价电子数** |
| `ae` | **全电子基组**，**常与 GAPW 方法、`POTENTIAL ALL` 一起用** |

### 7.3 基组与赝势的配对（官方，含新推荐）

**官方要求**：**生产计算请使用被设计为一起工作的基组与赝势。**

**官方举例**：
- 氧的 `DZVP-MOLOPT-GTH` **通常与 `GTH-PBE-q6` 配对**（PBE 计算）；
- **UZH 协议基组**（`BASIS_MOLOPT_UZH`）**与 `POTENTIAL_UZH` 中的对应条目配对**。

**官方明确的新推荐（重要）**：
**对新的 GPW 生产输入，在可用的地方，这些 UZH 协议配对是首选的起点**；
**较旧的 MOLOPT/GTH 库对兼容性和与既有输入对比仍然有用**。

**官方补充**：**同一个 `BASIS_MOLOPT_UZH` 文件也含全电子 MOLOPT 基组**，用于 GAPW 模拟，
例如 **`SVP-MOLOPT-GGA-ae`、`TZVPP-MOLOPT-GGA-ae`、`QZVPP-MOLOPT-GGA-ae`**，
**配 `POTENTIAL ALL` 使用**。

### 7.4 `BASIS_SET` 的角色参数（官方）

**官方说明**：`BASIS_SET` **可以携带一个可选的基组类型**。**不带显式类型时，CP2K 使用主轨道基**：

```fortran
&KIND O
  BASIS_SET ORB DZVP-MOLOPT-GTH
&END KIND
```

> **[G层提示]** 与 §1.3 的 `BASIS_SET NUC ...`、§4 的 `BASIS_SET RI_HFX ...`、
> §4.3 的 `BASIS_SET AUX_FIT ...` 一起看，这就是 CP2K 的**基组角色体系**：
> `ORB`（默认主基）/ `NUC`（核基）/ `RI_HFX`（HFX 的 RI 基）/ `AUX_FIT`（ADMM 辅助基）/
> `LRI_BASIS_SET`（LRIGPW 辅助基，注意它是**独立关键字**而非角色参数）。

### 7.5 赝势页的官方补充：关键字 vs 段

**官方明确警告**：**不要把 `POTENTIAL` *关键字*与同名的 `POTENTIAL` *段*混淆**——
**二者都定义赝势**。区别是：
**关键字接受势的类型与名字**；**段接受内部格式的完整规范与数据**。

**官方说明**：**像上面那样只指定关键字，对大多数实际用途就足够了。**
**好奇的话**：CP2K 会**解析用户输入并以更啰嗦但等价的新语法组合重启文件**
（见 `MOTION/PRINT/RESTART`），**这样的重启文件可以一窥关键字与段两种用法**：

```fortran
     &KIND "O"
       POTENTIAL "GTH-PBE-q6"
       &POTENTIAL
         2 4
           2.4455430000000000E-001 2 -1.6667214800000000E+001  2.4873113199999999E+000
         2
           2.2095592000000000E-001 1  1.8337458110000000E+001
           2.1133246999999999E-001 0
         # Potential name: GTH-PBE-Q6 for element symbol: O
         # Potential read from the potential filename: GTH_POTENTIALS
       &END POTENTIAL
     &END KIND
     &KIND "H"
       POTENTIAL "GTH-PBE-q1"
       &POTENTIAL
         1
           2.0000000000000001E-001 2 -4.1789004399999996E+000  7.2446330999999997E-001
         0
         # Potential name: GTH-PBE-Q1 for element symbol: H
         # Potential read from the potential filename: GTH_POTENTIALS
       &END POTENTIAL
     &END KIND
```

**官方再次强调**：`GTH-PBE-q6` 里的后缀 `q6` 意味着**显式处理 6 个价电子**；
**所选基组应匹配该价组态**；**氧的常用基组可在全名中用同样后缀**（如 `DZVP-MOLOPT-GTH-q6`）。

**官方最后的提醒**：**若在内置数据文件中发现某些赝势没有对应基组、或反之，请咨询开发者。**

---

## 8. OT 的官方关键区分（补充）

> 来源页：`methods/dft/orbital_transformation.html`（`02_dft_methods.md` §3 已覆盖，此处只补官方区分表述）

**官方原文**：OT **在保持正交归一的轨道子空间的同时最小化电子能量**。
**它避免了完整对角化，对大型绝缘体系常常高效。**
CP2K **也支持复数 k 点轨道、分数占据，以及有限温自由能最小化配 OT**。

**官方明确的"两个相关但不同"的段**：

| 段 | 官方说明 |
|---|---|
| `&SCF%OT` | **直接的 SCF 方法**。轨道、以及（被请求时）其旋转与辅助能量是**优化变量** |
| `&SCF%DIAGONALIZATION%OT` | **固定 Kohn–Sham 矩阵的迭代本征求解器**。外围的对角化 SCF 路径负责**指派占据、构造密度、做密度混合** |

**官方强调（重要）**：**这个区分对金属计算很重要，因为只有直接 OT 需要显式的旋转与辅助能量变量。**

**官方对固定占据的说明**：**常规直接 OT 设置适用于占据子空间与虚空间分离、且占据保持固定的情形。**

```fortran
&SCF
  &OT
    ALGORITHM STRICT
    MINIMIZER CG
    PRECONDITIONER FULL_SINGLE_INVERSE
  &END OT
&END SCF
```

- `STRICT` 是**默认算法**；`CG` 是**默认且通常稳健的最小化器**；
- **官方对预条件子的立场**：预条件子控制优化的轨道部分。
  **其适用性与成本取决于体系、基组与电子结构方法；
  因此应针对目标计算做测试，而不是仅凭一个名义上的等级来选。**

**官方关于 k 点**：**同一个直接 OT 形式支持复数、加权的 k 点集，包括对称约化网格。**
**官方要求**：**为每个目标性质收敛 k 点网格，并用等价的全网格验证实验性原子对称约化**。

**官方对分数占据与金属的说明**：
**在有限电子温度下，直接 OT 最小化固定电子数的自由能泛函。**
**它优化轨道子空间，连同该子空间内部的旋转，以及决定占据的辅助轨道能量。**

```fortran
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

**官方明确**：`ROTATION` **使占据列的旋转变分**。
**当能量在这类旋转下不变时（含分数占据情形），这是必需的。**

> **[G层提示]** 与 `02_dft_methods.md` §3.1「两个不同的 OT」对照阅读；
> 官方在 `orbital_transformation.html` 与 `convergence.html` 两页对 OT 的表述**互相补充**，
> 前者讲**段与变量的语义**，后者讲**收敛算法与 `OUTER_SCF` 机制**。

---

## 9. SCF 收敛补充：`EXTERNAL_DENSITY` 初始猜测与重启链条

> 来源页：`methods/dft/convergence.html`（`03_scf_convergence.md` 已覆盖主体，此处只补官方新增内容）

### 9.1 `SCF_GUESS EXTERNAL_DENSITY`（官方，新机制）

**官方说明**：**对自旋限制的 GPW 计算，可以用实空间网格上的标量电子密度直接初始化第一个
Kohn–Sham 哈密顿量**。做法是：

- 设 `SCF_GUESS EXTERNAL_DENSITY`；
- 用 `EXTERNAL_DENSITY_FILE_NAME` 提供**高斯 cube 文件**；
- **cube 网格必须与 CP2K 最细的网格一致**。

**官方机制说明（重要）**：
**CP2K 只消费这个密度一次**；**在第一次求解步之后，普通 SCF 过程生成并混合它自己的 AO 密度矩阵**。
**这避免了"把标量密度拟合到 AO 密度矩阵"这个病态问题。**

**官方明确的限制清单**：
- **当前实现支持半局域 GPW 计算**；
- **不支持**：含动能密度泛函（kinetic-energy-density functionals）、DFT+U、`DRHO_BY_COLLOCATION`；
- **精确交换仍需要 AO 密度矩阵**；
- **该猜测独立于、且不能与 `HARRIS_METHOD` 或面向 ZMP 的 `DFT%EXTERNAL_DENSITY` 段组合使用。**

### 9.2 重启链条（官方，高价值清单）

**官方立场**：**如果某个初步的廉价计算能收敛，从波函数重启对走向高级、昂贵的计算是强烈推荐的。**

**官方给出的六条链条**：

1. 用 **2-zeta `DZVP-MOLOPT-SR-GTH`** 基组做 gamma-only 计算后，
   用 **3-zeta `TZVP-MOLOPT-SR-GTH`** 基组重启另一个 gamma-only 计算
   （**注意二者应使用同一赝势**）；
2. 用**纯 GGA 泛函 PBE** 之后，重启一个**杂化泛函 PBE0** 计算
   （**这也会让 `SCREEN_ON_INITIAL_P` 变得合理**）；
3. 普通计算之后，重启一个带**特殊外部环境**（如周期电场或隐式溶剂模型）的计算；
4. **单点能求值之后，重启一个几何或晶胞优化任务**，然后再**重启一个振动分析任务**；
5. **基态计算之后，用 `WFN_MIX` 操纵 MO 系数并重启一个激发态计算**；
6. ……

**官方注意（格式陷阱，重要）**：
**波函数重启文件的格式与后缀在 gamma-only 形式与 k 点采样方案之间不同**：
- **前者通常是 `<project>-RESTART.wfn`**；
- **后者通常是 `<project>-RESTART.kp`**；
- **它们不能为重启目的互换。**

**官方新增（版本相关）**：
**从 CP2K 2026.2 起**，可以**用 `DFT/ENERGY_CORRECTION` 段下的 Harris 泛函做能量校正**，
**从而从一个 gamma-only 计算产生 `<project>-RESTART.kp`**。

### 9.3 官方关于"更贵的参数反而更快"的表述

**官方原文（值得记住）**：
**某些控制 Quickstep 精度的参数，如 `EPS_DEFAULT`、`CUTOFF`、`REL_CUTOFF`，
在选择得"尽可能好"时也能帮助收敛。**
**总时间成本不一定会随参数偏向更精确、更昂贵而增加**：
**即使每个 SCF 迭代耗时更长，达到收敛所需的总迭代数仍可能减少。**

**官方关于 k 点的补充**：
**更高数目或密度的 k 点对布里渊区采样也可能有益**，
**特别是当胞很小（对应长的倒空间格矢量）且体系是电子导体或半导体时**。
**针对目标性质的 k 点收敛测试，不必从"低到让 SCF 都无法收敛"开始。**

### 9.4 算法相关：官方对两种算法的分开考察

**官方说明**：**目前收敛判据不考虑能量的绝对变化**，
**且对角化算法的收敛与 OT 算法的收敛不同**。因此**下面分别考察两者**。

**对角化路径（官方）**：
- 标准对角化算法由 `DIAGONALIZATION` 段激活，**完全支持混合与 smearing 技术**；
- `MIXING` 段的 `METHOD` 支持若干方法。**默认保守的 `DIRECT_P_MIXING`** 可换成
  **`BROYDEN_MIXING`、`PULAY_MIXING`、`KERKER_MIXING`** 等；
- 分数占据（smearing）由 `SMEAR` 段启用，**对带隙很小或没有带隙、以及强静态相关的体系非常有用**；
- `METHOD` 的可能值包括**费米-狄拉克分布**与**若干展宽方法（如高斯展宽）**；
- **官方提醒**：**为费米-狄拉克 smearing 抬高 `ELECTRONIC_TEMPERATURE` 能处理困难体系，
  但需要外推到 0 才能得到与不用 smearing 可比的结果**；
  **同样，高斯展宽应把宽度 `SIGMA` 系统性地降到 0**；
- **官方补充**：**有些算法只与均匀占据兼容**。

**OT 路径（官方）**：
- OT 由 `OT` 段激活。**最重要的设置**是 `ALGORITHM`、`LINESEARCH`、`MINIMIZER`、`PRECONDITIONER`；
- `OUTER_SCF` 段控制**更新 OT 预条件子的外循环**。
  **更新 KS 矩阵的常规循环现在是内循环**：
  **若满足 `SCF/MAX_SCF` 而未满足 `SCF/EPS_SCF`，程序离开内循环，
  把 OT 预条件子更新为外循环的一次迭代，然后开始另一个内循环。**
- **官方具体建议（数值）**：
  **这种情况下 `SCF/MAX_SCF` 可降到约 16 到 32**，
  **以便以适当的频率调用预条件子生成器，平衡时间成本与收敛行为**；
  **把 `SCF/OUTER_SCF/MAX_SCF` 设为约 8 到 16 对大多数情形足够。**

> **[G层提示]** `03_scf_convergence.md` §1.4 已覆盖 `OUTER_SCF` 机制；
> 此处补的是**官方给出的具体数值区间（16–32 / 8–16）**与**算法分述的原文结构**。

---

## 10. 占位页登记

| 页面 | 官方状态 |
|---|---|
| `methods/dft/linear_scaling.html` | **占位页**。官方原文：**"Unfortunately no one has gotten around to writing this page yet :-("**。官方只给两个链接：VandeVondele2012、`https://www.cp2k.org/exercises:2017_ethz_mmm:ls_scf` |

> **[G层提示]** 线性标度 DFT 在 `02_dft_methods.md` §9 已登记为占位页；
> 本文件补充**官方给出的两个可用链接**，便于用户直接找 LS-SCF 教程。

---

## 11. 缺口登记（如实，不编造）

| 缺口 | 说明 |
|---|---|
| **RI-HFX 固体例（64 原子 Si）输入** | 官方 `ri_gamma.html` 的例 2 正文**在"PBE0 的 25% 精确交换分数被计算"一句后截断**，未给出完整输入。**需从官方 example file bundle 获取** |
| **RI-HFXk 输入尾部** | 官方 `ri_kpoints.html` 的输入**在 `CUTOFF_RADIUS 5.0` 后截断**（代码块未闭合），`&KIND`、`&SUBSYS`、k 点网格设置未在页面给出 |
| **`lib_tools.zip` / example bundle** | 官方多页提供 `lib_tools.zip` 与 example 打包下载，**G 层未采**（二进制，且非文档正文） |
| **官方图片 / 流程图原始 SVG** | `gpw.html` 的 block-beta 流程图在 HTML 中以 mermaid 类语法存在，**G 层已转录为文字链式表示**，未保留原图 |
| **GauXC 完整可运行输入** | 官方页**只有片段**，无完整输入；实际使用需查 regtest |
| **CNEO 完整可运行输入** | 官方页**只有片段**，无完整输入 |
| **`constrained.html` 正文** | `02_dft_methods.md` §7 已覆盖 CDFT 主体（含 Becke/Hirshfeld/MIXED_CDFT 与 Zn 二聚体、水二聚体算例），**本文件不重复**。若需逐字原文，请直接查官方页 |
| **`k-points.html` 正文** | `02_dft_methods.md` §4 已完整覆盖（含时间反演约化、空间群约化、对称后端、移动几何体、验证排查） |
| **`cutoff.html` 教程脚本** | `03_scf_convergence.md` 第二部分已覆盖原理与实测数据；本文件只补了官方模板输入的 `&MGRID`/`&SCF` 片段 |

---

## 12. 交叉索引

| 需求 | 去哪 |
|---|---|
| GPW/GAPW 原理、赝势主体、OT、k 点、LRIGPW、ADMM、CDFT、DFT+U | `02_dft_methods.md` |
| SCF 收敛排查、CUTOFF/REL_CUTOFF 收敛教程 | `03_scf_convergence.md` |
| 基组文件格式、GTH 完整元素清单、基组/赝势一致性检查 | `14_basis_and_potentials.md` |
| 量子核 / CNEO 与核基组 | **本文件 §1** |
| 外部 XC 积分器 / Skala 机器学习泛函 | **本文件 §2**；构建见 `09_build_libraries.md` |
| 泊松求解器选型、带电体系、真空收敛 | **本文件 §3**；周期性另见 `20_input_reference_tree.md` |
| RI-HFX / RI-HFXk | **本文件 §4** |
| ML 势（NequIP/MACE/NNP/PAO-ML/ACE）、Kim-Gordon、DLA-Future | `22_ml_embedding_dlaf.md` |
| X 射线谱（ΔSCF / XAS_TDP / δ-kick / GW2X） | `21_xray_spectroscopy_full.md` |
| Input Reference 完整段树与关键字计数 | `20_input_reference_tree.md` |
| 官方资料权威性分级 | `12_authority_sources.md` |
| 编译与库依赖（含 GauXC / LibTorch / DLA-Future） | `09_build_libraries.md` |
