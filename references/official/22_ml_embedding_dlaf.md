# 22 · 机器学习势、嵌入方法与 DLA-Future（官方）

> 来源：
> - https://manual.cp2k.org/trunk/methods/machine_learning/nequip.html
> - https://manual.cp2k.org/trunk/methods/machine_learning/mace.html
> - https://manual.cp2k.org/trunk/methods/machine_learning/nnp.html
> - https://manual.cp2k.org/trunk/methods/machine_learning/pao-ml.html
> - https://manual.cp2k.org/trunk/methods/machine_learning/ace.html
> - https://manual.cp2k.org/trunk/methods/embedding/kim-gordon.html
> - https://manual.cp2k.org/trunk/technologies/eigensolvers/dlaf.html
> 抓取日期：2026-09-09
> 标注规则：`[默认]` = 官方 Input Reference 默认值；`[官方推荐]` = 官方正文明确推荐；`[示例]` = 官方示例取值；`[G层提示]` = G 层整理性说明（非官方原话）。

---

## 0. 本文件补什么

`16_qmmm_embedding_ml.md` 只覆盖了 DeePMD 为主的 ML 势概览。本文件补齐：

- **5 个 ML 势页面**（NequIP/Allegro、MACE、NNP、PAO-ML、ACE）
- **Kim-Gordon 密度嵌入**（理论 + 教程）
- **DLA-Future 分布式线性代数**（编译 + 输入 + 调参）

---

## 1. NequIP 与 Allegro（`nequip.html`）

### 1.1 定位

- NequIP / Allegro 是**深度等变神经网络**原子间势框架。
- **CP2K 接口兼容 NequIP ≥ 0.7.0** 训练并编译的模型，与 LAMMPS 的
  `pair_nequip_allegro`（v0.7.0）集成**一致**。
- 相关文献：Batzner2022、Musaelian2023、Tan2025。

### 1.2 输入（官方原文）

CP2K 中推理**已统一**，完全通过 `&NONBONDED` 力场参数里的 **`&NEQUIP`** 段配置：

```fortran
&FORCEFIELD
  &NONBONDED
    &NEQUIP
      MODEL_TYPE  NEQUIP # possible choices are NEQUIP or ALLEGRO
      ATOMS H O
      POT_FILE_NAME NequIP/waterscan-neq0.16.nequip.pth
      UNIT_ENERGY eV
      UNIT_FORCES eV*angstrom^-1
      UNIT_LENGTH angstrom
    &END NEQUIP
  &END NONBONDED
&END FORCEFIELD
```

| 关键字 | 说明 |
|---|---|
| `MODEL_TYPE` | 载入模型的架构（`NEQUIP` 或 `ALLEGRO`） |
| `ATOMS` | 元素/种类列表 |
| `POT_FILE_NAME` | NequIP/Allegro 模型路径 |
| `UNIT_*` | **显式定义模型内部长度、能量、力的单位** |

> **官方提示**：完整生产级 MD 示例输入在回归测试目录：
> `tests/Fist/regtest-nequip/water-bulk.inp`、`tests/Fist/regtest-allegro/water-bulk.inp`。

### 1.3 编译要求

- 运行 NequIP/Allegro **需要带 LibTorch 编译 CP2K**。
- **支持的 LibTorch 版本：2.4–2.7**。
- CPU 二进制：工具链加 **`--with-libtorch`** 即可。
- GPU 加速：要么从源码编译 LibTorch，要么从 PyTorch 下载 CUDA 预编译库并把路径传给工具链脚本：

```
./install_cp2k_toolchain.sh --with-libtorch=
```

> **[G层提示]** 官方这里写的是 `--with-libtorch=`（等号后留空），
> 实际用法应是把路径写在等号后。已登记为官方页面表述不完整，见 `_sources.md` §4.6。

### 1.4 验证与可复现性（官方）

- **与 LAMMPS 对比**：官方已核实本实现**数值上复现** LAMMPS `pair_nequip_allegro` 插件的结果。
- **数据**：训练数据集、`data/NequIP` 与 `data/Allegro` 中的模型文件、输入脚本、
  以及验证用的 parity 图都在 Zenodo：**doi:10.5281/zenodo.18848354**。

### 1.5 参考资源（官方列出）

| 资源 | 位置 |
|---|---|
| 高性能升级 | 论文 Tan2025；代码 `github.com/mir-group/pair_nequip_allegro` |
| Allegro | 论文 Musaelian2023；代码 `github.com/mir-group/allegro` |
| NequIP | 论文 Batzner2022；代码 `github.com/mir-group/nequip` |
| e3nn | <https://e3nn.org>；doi:10.5281/zenodo.7430260 |

---

## 2. MACE（`mace.html`）

### 2.1 定位

- MACE 用**高阶等变消息传递神经网络**构建原子间势；方法见 Batatia et al. (2022)。
- **官方注意**：运行 MACE **需要带 LibTorch 支持的 CP2K 构建**。
- 与 NequIP/Allegro 接口类似，CP2K 通过**通用 LibTorch 接口**跑 MACE：
  训练好的模型**一次性导出为自包含 TorchScript 文件（`.pth`）**，CP2K 运行时载入并求值。
  **模拟过程中不涉及 Python 解释器。**

### 2.2 导出 MACE 模型（官方）

用辅助脚本 `cp2k/tools/mace/create_cp2k_model.py` 把训练好的 `.model` 包装并编译为 CP2K 可载入的 TorchScript：

```
python create_cp2k_model.py my_mace.model --dtype float64
# -> writes my_mace.model-cp2k.pth
```

- 转换**只需在有 `torch` 和 `mace` 的机器上做一次**。
- 生成的 `*.pth` 与 NequIP 接口**用同样的张量与元数据格式**：
  - 输入：`pos`、`edge_index`、`edge_cell_shift`、`cell`、`atom_types`
  - 输出：`atomic_energy`、`forces`、`virial`
  - 内嵌元数据：`num_types`、`r_max`、`type_names`、`model_dtype`（CP2K 读取它们来构建邻居图）
- **导出用的 `torch` 版本必须与链接进 CP2K 的 LibTorch 版本兼容。**

### 2.3 输入（官方原文）

通过 `&NONBONDED` 力场参数里的 **`&MACE`** 段配置：

```fortran
&FORCEFIELD
  &NONBONDED
    &MACE
      ATOMS Cu
      POT_FILE_NAME MACE/my_mace.model-cp2k.pth
    &END MACE
  &END NONBONDED
&END FORCEFIELD
```

| 关键字 | 说明 |
|---|---|
| `ATOMS` | 元素/种类列表；**到模型类型列表的映射必须与 `&COORDS`/`&TOPOLOGY` 中的坐标一致** |
| `POT_FILE_NAME` | 导出的 MACE 模型路径 |

> **官方重要说明**：MACE 是**消息传递模型，感受野非局域**。
> 与 NequIP 一样，该接口在**每个 MPI rank 上求值整个体系**，
> 再把能量、力、位力**除以 rank 数**。

### 2.4 参考资源

- MACE：论文 Batatia2022；代码 `github.com/ACEsuit/mace`
- e3nn：<https://e3nn.org>

---

## 3. 神经网络势 NNP（`nnp.html`）

### 3.1 定位

- CP2K 支持 **Behler-Parrinello 高维神经网络势（HDNNP）**，
  以**原子中心对称函数（ACSF）**为描述符。
- NNP 可驱动任何走 `FORCE_EVAL` 的 CP2K 运行：
  单点能 → 几何优化 → 分子动力学 → 自由能方法的偏置 MD → **模型委员会外推诊断**。
- **同一条 NNP 路径也支撑路径积分模拟中的氦溶剂相互作用。**
- 实现读取用 **n2p2 格式**训练的网络（`input.nn`、`scaling.data`、`weights.<element>.data`）。

### 3.2 输入（官方原文）

在 `&FORCE_EVAL` 里用 **`METHOD NNP`** 选择。网络文件与一个或多个模型定义在 **`&NNP`** 下配置。

最小委员会 NNP MD 输入：

```fortran
&FORCE_EVAL
  METHOD NNP
  &NNP
    NNP_INPUT_FILE_NAME nnp-1/input.nn
    SCALE_FILE_NAME     nnp-1/scaling.data
    &MODEL
      WEIGHTS nnp-1/weights
    &END MODEL
    &MODEL
      WEIGHTS nnp-2/weights
    &END MODEL
    ! ... up to 8 typical for committee error bars ...
  &END NNP
  &SUBSYS
    &CELL
      ABC [angstrom] 12.42 12.42 12.42
    &END CELL
    &COORD
      ! ...
    &END COORD
  &END SUBSYS
&END FORCE_EVAL
```

> **官方提示**：覆盖 NVT、NPT、偏置 MD 和重启的完整示例在 `tests/NNP/regtest-1/`；
> 路径积分氦-溶质耦合示例见 `tests/Pimd/regtest-2/water_in_helium_nnp.inp`。
> **委员会成员典型取 8 个**以得到误差棒。

### 3.3 调参（官方）

**ACSF 样条网格**：

- **默认 `RAD_SPLINE_N 8192`**，是按**径向截断约 12 bohr** 校准的。
- 截断显著更大或精度要求更严的模型，可能需要更大的值。
- **三次 Hermite 的值残差标度为 O(1/n⁴)，力（导数）残差为 O(1/n³)**；
  默认网格下两者在 12 bohr 截断时都接近机器精度
  （**值误差 ~1e-14，力误差 ~1e-10**）；
  **随截断增大，力项是约束瓶颈**。

**Verlet skin**：

- 元胞列表邻居搜索用 Verlet skin，只有当原子在两次力求值之间漂移超过 **`skin/2`** 时才重建链。
- **默认自动选择 `MIN(0.5 bohr, 0.1 * cutoff)`**。
- 长时间稳定轨迹可以调大以减少重建频率，代价是每个原子的邻居列表更大：

```fortran
&NNP
  ! ...
  VERLET_SKIN [bohr] 1.0
&END NNP
```

- 这相当于 LAMMPS 的 `neighbor <skin> bin` 命令。
- **负值（默认）选择自动启发式**；**有用的上界约在最小垂直胞宽的一半**。

### 3.4 并行

- NNP 同时支持 **MPI 与 OpenMP**。
- **MPI 在 rank 间分配原子**；**OpenMP 在每个 rank 内并行化逐原子描述符与力的循环**。

### 3.5 参考

<https://www.cp2k.org/tools:aml>、<https://doi.org/10.1063/5.0160326>、
Behler2007、Behler2011、Schran2020、Schran2020b。

---

## 4. PAO-ML（`pao-ml.html`）

### 4.1 定位

- **PAO-ML = Polarized Atomic Orbitals from Machine Learning**。
- 用机器学习生成**几何自适应的紧凑基组**，并提供**精确的离子力**。
- 可作为传统基组的**近乎即插即用的替代**来加速标准 DFT 计算。
- 方法类似基于最小基组的半经验模型，但**精度更好且参数化准自动**。
- **官方警告（原文）**：方法**仍处于早期阶段——请谨慎使用**。详见 Schuett2018。

### 4.2 五步流程（官方）

#### Step 1：获取训练结构

- 对每个结构，变分 PAO 基组通过**显式优化**确定。
- 训练结构应**远小于目标体系**，但要**足够大以包含大体系的所有"结构基元（motifs）"**。
- 液体：跑一个小盒子的 MD 是获取结构的好办法。

#### Step 2：在**主基组**里算参考数据

- 选一个主基组，如 `DZVP-MOLOPT-GTH`，做完整的 **`LS_SCF`** 优化。
- **同时开启 `RESTART_WRITE` 保存最终密度矩阵**——它能显著加速下一步。

#### Step 3：为训练结构优化 PAO 基组

- 为每个原子种类选 `PAO_BASIS_SIZE`。
- **最小基组就能得到不错的结果**；略大于最小的 PAO 基组可显著提高精度，
  但**更难优化也难机器学习**。

PAO 设置大部分在 `&PAO` 段：

```fortran
&PAO
  EPS_PAO    1.0E-7                    ! convergence threshold of PAO optimization
  MAX_PAO    10000                     ! minimal PAO basis usually converge withing 2000 steps.

  MAX_CYCLES 500                       ! tunning parameter for PAO optimization scheme
  MIXING     0.5                       ! tunning parameter for PAO optimization scheme
  PREOPT_DM_FILE primay_basis.dm       ! restart DM from primary basis for great speedup

  LINPOT_REGULARIZATION_DELTA 1E-6     !!!! Critical parameter for accuracy vs learnability trade-off !!!!

  LINPOT_REGULARIZATION_STRENGTH 1E-3  ! rather insensitive parameter, 1e-3 works usually
  REGULARIZATION 1.0E-3                ! rather insensitive parameter, 1e-3 works usually

  PRECONDITION YES                     ! not important, don't touch
  LINPOT_PRECONDITION_DELTA 0.01       ! not important, don't touch
  LINPOT_INITGUESS_DELTA 1E+10         ! not important, don't touch

  &PRINT
    &RESTART
      BACKUP_COPIES 1                  ! write restart files, just in case
    &END RESTART
  &END PRINT
&END PAO
```

各原子种类的设置在 `&KIND` 段：

```fortran
&KIND H
  PAO_BASIS_SIZE 1    ! set this to at least the minimal basis size
  &PAO_POTENTIAL
    MAXL 4            ! 4 works usually
    BETA 2.0          ! 2 work usually, but is worth exploring in case of accuracy or learnability issues.
  &END PAO_POTENTIAL
&END KIND
```

**调优 PAO 优化（官方）**：

- 找最优 PAO 基是个复杂的极小化问题，因为**旋转矩阵 U 与 KS 矩阵 H 必须自洽优化**。
- 为加速，**KS 矩阵只偶尔更新**，大部分时间花在优化 U 上。这个交替方案由两个参数控制：
  - **`MAX_CYCLES`**：重算 H 的频率。
  - **`MIXING`**：U 优化过程中的过冲阻尼。

**进度追踪（官方）**：看以 `PAO| step` 开头的行：

```
             step-num             energy          conv-crit. step-length   time
 PAO| step   1121                 -186.164843303  0.227E-06  0.120E+01     1.440
```

| 列 | 含义（官方） |
|---|---|
| step-num | 能量求值次数，即**探测过的 U 矩阵个数**。用 `ADAPT`ive 线搜索时增长间隔会变。**达到 `MAX_PAO` 时优化被提前终止。** |
| energy | 被优化的量。**只含总能量的一阶项**，即 \(Tr[HP]\)，但**变分极小值相同**。还含各正则化项贡献。 |
| conv-crit. | 梯度范数按体系大小归一化。与 `EPS_PAO` 比较决定是否收敛。**在更新 KS 矩阵后的两步内达到该判据，整体优化即终止。** |
| step-length | 线搜索结果，**应为 1 量级**。若在优化末尾开始异常波动，说明进一步优化被数值精度（如 `EPS_FILTER`、`EPS_SCF`）阻碍。 |
| time | 该优化步耗时（秒）。会随线搜索步数变化。 |

#### Step 4：优化机器学习超参数

- 大体系模拟时，PAO-ML 从训练数据推断新的 PAO 基组。
- 用了两个启发式：**描述符**与**推理算法**。
- **目前只实现了一个简单描述符和高斯过程**；官方指出**这部分有很好的未来研究机会**。
- 要得到好的学习结果，需为每个应用**仔细调少量超参数**：
  当前实现包括 **`GP_SCALE`** 以及描述符的 **`BETA`** 和 **`SCREENING`**。
- **超参数优化没有梯度**，故必须用**无导数方法**（如 Powell 的方法）。
  一个通用实现是 **scriptmini** 工具。
- **好的优化判据**：训练集上相对主基组的能量差**方差**；也可比较原子力。
- 尽管没有梯度，**该优化相当快**，因为只在小的 PAO 基组里算。

#### Step 5：用 PAO-ML 跑模拟

大部分设置在新的 `&PAO/&MACHINE_LEARNING` 段：

```fortran
&PAO
  MAX_PAO 0                  ! use PAO basis as predicted by ML, required for correct forces
  PENALTY_STRENGTH 0.0       ! disable penalty, required for correct forces

  &MACHINE_LEARNING
    GP_SCALE 0.46            !!! critical tuning parameter - depends also on descriptor settings !!!
    GP_NOISE_VAR 0.0001      ! insensitive parameter

    METHOD GAUSSIAN_PROCESS  ! only implemented method - opportunity for future research
    DESCRIPTOR OVERLAP       ! only implemented method - opportunity for future research
    PRIOR MEAN               ! try once ZERO - makes usually no difference
    TOLERANCE 1000.0         ! disable check for max variance of GP prediction

    &TRAINING_SET
          ../training/Frame0000/calc_pao_ref-1_0.pao
          ../training/Frame0100/calc_pao_ref-1_0.pao
          ../training/Frame0200/calc_pao_ref-1_0.pao
          ! add more ...
    &END TRAINING_SET
  &END MACHINE_LEARNING
&END PAO
```

> **官方关键提示**：`MAX_PAO 0`（用 ML 预测的 PAO 基组）与 `PENALTY_STRENGTH 0.0`（关闭惩罚）
> **都是"力正确"的必要条件**。

各原子种类设置仍在 `&KIND` 段：

```fortran
&KIND H
  PAO_BASIS_SIZE 1      ! use same settings as for training
  &PAO_POTENTIAL
    MAXL 4              ! use same settings as for training
    BETA 2.0            ! use same settings as for training
  &END PAO_POTENTIAL

  &PAO_DESCRIPTOR
     BETA   0.16        !!! important ML hyper-parameter !!!
     SCREENING 0.66     !!! important ML hyper-parameter !!!
     WEIGHT 1.0         ! usually not needed when BETA and SCREENING are choose properly
  &END PAO_DESCRIPTOR
&END KIND
```

> **官方提示**：Step 5 的 `PAO_BASIS_SIZE`、`MAXL`、`BETA` **必须与训练时一致**。

### 4.3 精度 vs 可学习性（官方）

- 在 Step 3 优化 PAO 参考数据时，**必须权衡精度与可学习性**。
- **可学习性好 = 相似结构给出相似的 PAO 参数**，即 PAO 参数应**平滑依赖原子位置**。
- 官方给的一套设置通常能得到好结果；**若后续机器学习步骤出问题，这里可能是罪魁祸首**。
- **目前还没有简单方法评估可学习性。** 一种做法是沿某个反应坐标（如二聚体解离）构造一组结构，
  把 `.pao` 文件里 `Xblock` 的数值对反应坐标作图。
- **对可学习性最关键的参数：`LINPOT_REGULARIZATION_DELTA` 与势的 `BETA`。**

---

## 5. ACE（`ace.html`）

### 5.1 定位

- **原子团簇展开（Atomic Cluster Expansion）**是局域原子环境的**完备描述符**。
- 引入 ACE 的非线性函数即得原子间势，**精度可与最先进的机器学习势媲美**。

### 5.2 输入

> **官方标注：`Input Section` 下的正文写作 "TODO"**（即该段尚未写完）。

推理通过 **`&ACE`** 段进行：

```fortran
&ACE
  ATOMS O H
  POT_FILE_NAME ./sample.yaml
&END ACE
```

- `sample.yaml` 指**用 ACE 部署的模型**。
- 完整示例输入见回归测试 `H2O-64_ACE_MD.inp`。

| 关键字 | 说明 |
|---|---|
| `ATOMS` | 要用 ACE 处理的元素/种类列表 |
| `POT_FILE_NAME` | 特定 ACE 拟合的文件名 |

### 5.3 编译

- 运行 ACE **需要带 ACE 库编译 CP2K**。
- CP2K 二进制：工具链加 **`--with-ace`**，会从 ACE GitHub release 下载并编译。
- **存在 CUDA 环境时启用 GPU 支持。**

### 5.4 参考

ACE 论文 Drautz2019、Lysogorskiy2021、Bochkarev2024；代码 `github.com/ICAMS/lammps-user-pace`。

---

## 6. Kim-Gordon 密度嵌入（`kim-gordon.html`）

### 6.1 理论（官方）

基于**密度嵌入**。先引入密度嵌入方法的**减法方案定义**：

\[
 E_{tot} = E_{HK}[\rho_{tot}] - \sum_{A}E_{HK}[\rho_{A}] + \sum_{A}E_{KS}[\rho_{A}] 
\]

- 总电子密度 \(\rho_{tot} = \sum_{A}\rho_{A}\) 是所有子系统 \(A\) 的密度之和。
- \(E_{HK}\)、\(E_{KS}\) 分别是 Hohenberg-Kohn 与 Kohn-Sham 泛函。

\[
E_{HK}[\rho] = T_{HK}[\rho] + E_{ext}^{HK}[\rho] + \frac{1}{2} \int\int \frac{\rho(r)\rho(r')}{r-r'}drdr' + E_{XC}[\rho] \\
E_{KS}[P] = T_{S}[P] + E_{ext}[P] + \frac{1}{2} \int\int \frac{\rho(r)\rho(r')}{r-r'}drdr' + E_{XC}[\rho]
\]

其中 \(P\) 是体系的约化单粒子密度矩阵。

**关键限制**：HK 能量中的外势泛函**对密度必须是线性的**：

\[ E_{ext}^{HK}[\rho_{tot}] = \sum_{A}E_{ext}^{HK}[\rho_{A}] \]

记经典库仑项为 \(E_{hxc}[\rho]\)，定义**非可加动能**：

\[ T_{nadd}[\rho,{\rho_{A}}] = T_{HK}[\rho]-\sum_{A}T_{HK}[\rho_{A}] \]

得：

\[ E_{tot}[{P_{A}}] =\sum_{A}(T_{S}[P_{A}] + E_{ext}[P_{A}]) + E_{hxc}[\rho] + T_{nadd}[{P_{A}}] \]

**为避免对每个子系统积分动能泛函**，可应用**原子势近似**。对局域势：

\[
T_{nadd} = T_{S}[\rho]-\sum_{A}T_{S}[\rho_{A}] =
\int\rho\mu[\rho]dr - \sum_{a}\int\rho_{A}\mu[\rho_{A}]dr =
\sum_{a}\int\rho_{A}(\mu[\rho]-\mu[\rho_{A}])dr
\]

对泛函 \(\mu[\rho]\) 做**线性化近似**：

\[
\mu[\rho]-\mu[\rho_{A}] \sim \sum_{B\neq A} \frac{\partial \mu[\rho_{A}]}{\partial \rho} \rho_{B} = \mu'[\rho_{A}] \\
T_{nadd} = \sum_{A}T_{S}\sum_{B\neq A}\int\mu'[\rho_{A}]\rho_{A}\rho_{B}dr
\]

对导数泛函再做**原子贡献近似**：

\[ E \mu'[\rho_{A}]\rho_{A} = V^{K}[\rho_{A}] \sim \sum_{a \in A}V_{a}^{K}(R_{a}) \]

利用**典型动能泛函正比于 \(\rho^{5/3}\)** 这一事实，得到最终原子局域势模型：

\[ V_{a}^{K}(R_{a}) = N_{a}\rho_{a}^{2/3} \]

其中 \(\rho_{a}\) 是模型原子密度。**这种局域势有助于加速底层嵌入计算。**

### 6.2 教程（官方）

- **把总体系划分为子系统是关键**。为此需要指定"**最小单元**"，在 `&TOPOLOGY` 段中定义。

```fortran
  &SUBSYS
    &CELL
      ABC 9.8528 9.8528 9.8528
    &END CELL
    &COORD
 O   2.28039789       9.14653873       5.08869600       1
 H   1.76201904       9.82042885       5.52845383       1
 H   3.09598708       9.10708809       5.58818579       1
 O   1.25170302       2.40626097       7.76990795       2
 H  0.554129004       2.98263407       8.08202362       2
 H   1.77125704       2.95477891       7.18218088       2
 O   1.59630203       6.92012787      0.656695008       3
 H   2.11214805       6.12632084      0.798135996       3
 H   1.77638900       7.46326399       1.42402995       3
 ...
    &END COORD
    &TOPOLOGY
      CONN_FILE_FORMAT USER
    &END
```

> **官方说明**：该策略**基于 `&COORD` 段的第四列**。
> 此时代码能通过 **`COLORING_METHOD`** 找到"最小单元"的最佳组合以简化计算。

- **另一条建议**：用**线性标度 DFT** 跑 KG 计算，把 `&SCF` 段替换为 `&LS_SCF`：

```fortran
&LS_SCF
  MAX_SCF     40
  EPS_FILTER  1.0E-6
  EPS_SCF     1.0E-7
  MU         -0.1
  PURIFICATION_METHOD TRS4
&END
```

> 这会加速计算，**体系维度增大时尤其明显**。

- **官方注意（原文）**：**所有关键字也必须在 `&QS` 段里激活**：

```fortran
&QS
  LS_SCF
  KG_METHOD
  ...
&END QS
```

---

## 7. DLA-Future（`dlaf.html`）

### 7.1 定位

- DLA-Future 是用 pika 提供的 **C++26 `std::execution`** 库实现的**分布式线性代数库**。
- 提供 **ScaLAPACK 风格的 Fortran 接口**（DLA-Future-Fortran），
  可**作为 ScaLAPACK 的即插即用替代**（ScaLAPACK 参数的子集，例如没有 workspace 参数）。

### 7.2 依赖与安装

- 有若干依赖，**官方通过 Spack 包管理器分发，这是推荐的安装方式**。
- DLA-Future 的 Spack 包列出了所有必需和可选依赖。

### 7.3 CMake 选项

```cmake
-DCP2K_USE_DLAF=ON
```

### 7.4 输入文件用法

**特征值求解**——用 `PREFERRED_DIAG_LIBRARY` 关键字选择：

```fortran
&GLOBAL
  PREFERRED_DIAG_LIBRARY DLAF
  DLAF_NEIGVEC_MIN 1024
  [...]
&END GLOBAL
```

- **`DLAF_NEIGVEC_MIN`**：改用 DLA-Future 而非 ScaLAPACK 的**最小矩阵尺寸**。
- **官方提示**：DLA-Future **针对 GPU 上的大矩阵优化**，
  **对小矩阵或 CPU 矩阵可能比 ScaLAPACK 更慢**。

**Cholesky 分解**——用 `PREFERRED_CHOLESKY_LIBRARY`：

```fortran
&GLOBAL
  PREFERRED_CHOLESKY_LIBRARY DLAF
  DLAF_CHOLESKY_N_MIN 1024
  [...]
&END GLOBAL
```

- **`DLAF_CHOLESKY_N_MIN`** 含义同上。

**块大小（官方）**：

- **CP2K 的默认块大小对 DLA-Future 可能不是最优的。**
- DLA-Future 受益于更大的块，但**最优块大小取决于具体的 CP2K 计算**。
- 通过以下关键字调整：

```fortran
&GLOBAL
  [...]
  &FM
    FORCE_BLOCK_SIZE .TRUE.
    NCOL_BLOCKS 1024
    NCOL_BLOCKS 1024
    [...]
  &END FM
&END GLOBAL
```

> **[G层提示]** 官方页面这里 **`NCOL_BLOCKS` 写了两遍**（第二行应为 `NROW_BLOCKS`）。
> 照录原文并登记到 `_sources.md` §4.6，**不擅自改官方原文**。

### 7.5 环境变量与 pika

- DLA-Future 构建在 **pika** 之上。pika 是基于 C++26 `std::execution` 的 C++ 库
  （见 P2300 提案），提供**用户级线程的 CPU 运行时**，以及与 CUDA/HIP 和 MPI 的集成。
- **pika 的行为可通过命令行选项或环境变量控制**；线程数与线程绑定请参考 pika 文档。

---

## 8. 与 G 层其它文件的关系

| 相关文件 | 关系 |
|---|---|
| `16_qmmm_embedding_ml.md` | QM/MM 与 DeePMD 等 ML 势概览；本文件补齐其余 ML 框架与 KG/DLAF |
| `09_build_libraries.md` | LibTorch / ACE 库的编译（本文件补 `--with-libtorch`、`--with-ace`） |
| `19_performance_gpu_community.md` | GPU、Spack、特征求解器；DLAF 是特征求解器之一 |
| `20_input_reference_tree.md` | `&NNP`、`&ACE`、`&NEQUIP`、`&MACE`、`&PAO`、`&LS_SCF`、`&FM` 在段树中的位置 |
| `_sources.md` | 采集总表与缺口清单 |

---

## 9. 缺口与已知问题登记（如实）

| 项 | 状态 |
|---|---|
| `ace.html` 的 `Input Section` 正文 | **官方标注 "TODO"**，尚未写完 |
| `nequip.html` 的 `--with-libtorch=` 用法 | 官方等号后留空，**表述不完整**，已登记 |
| `dlaf.html` 的 `NCOL_BLOCKS` 重复 | 官方笔误（应为 `NROW_BLOCKS`），已登记 |
| ML 各页的图/表 | 未采集 |
| `kim-gordon.html` 的 `COLORING_METHOD` 细节 | 官方未展开，指向 Input Reference |
| PAO-ML 的 `scriptmini` 工具 | 官方仅提及名称，**未采集本体** |
| NequIP/MACE/ACE 的模型文件与数据集 | 指向 Zenodo / GitHub，**未下载** |
| `methods/embedding/` 下其它子页 | 本文件只采了 `kim-gordon.html`；如有其它子页待查 |
