# 11 · 版本时间线与不兼容变更

> **来源**：<https://manual.cp2k.org/trunk/changelog.html>
> **抓取日期**：2026-09-08
> **抓取范围**：2.0（2009）– 2027.1（开发中）全部版本条目
> **本文件定位**：G 层（官方权威层）。用于**升级前排查**与**解释版本相关行为差异**。

---

## 0. 为什么这一层必须记录版本

CP2K 迭代快，**默认行为会变**。两个已在本 skill 中反复出现的关键例子：

| 变更 | 影响 | 出处 |
|---|---|---|
| **2024.1 起 SCF 不收敛默认 ABORT** | 旧脚本"跑完不报错"的假设失效 | 见 §3 与 `03_scf_convergence.md` |
| **2026.2 移除 `&MOTION/&CELL_OPT/TYPE`** | 旧输入文件直接报错 | 见 §2.3 |
| **2027.1 起要求 `MPI_THREAD_MULTIPLE`** | 旧 MPI 环境可能无法启动 | 见 §2.1、`09_build_libraries.md` §3.1 |

**使用原则**：排查"为什么同样的输入在不同机器上行为不同"时，**第一步先确认两边 CP2K 版本**。

---

## 1. 版本时间线总表

| 版本 | 发布日期 | 类型 |
|---|---|---|
| **2027.1** | 开发中（Under Development） | 开发版 |
| **2026.2** | July 15, 2026 | 正式版 |
| **2026.1** | January 6, 2026 | 正式版 |
| **2025.2** | July 23, 2025 | 正式版 |
| **2025.1** | January 1, 2025 | 正式版 |
| **2024.3** | September 9, 2024 | **小版本**（修复 PW 环境 MD 停滞） |
| **2024.2** | August 6, 2024 | 正式版 |
| **2024.1** | January 3, 2024 | 正式版（**Sphinx 手册上线**） |
| **2023.2** | July 28, 2023 | 正式版 |
| **2023.1** | January 1, 2023 | 正式版 |
| **2022.2** | October 4, 2022 | **小版本**（修 Spglib URL） |
| **2022.1** | July 8, 2022 | 正式版 |
| **9.1** | December 31, 2021 | 正式版 |
| **8.2** | May 28, 2021 | 正式版 |
| **8.1** | December 30, 2020 | 正式版 |
| **7.1** | December 24, 2019 | 正式版（**SVN → Git**） |
| **6.1** | June 11, 2018 | 正式版 |
| **5.1** | October 24, 2017 | 正式版 |
| **4.1** | October 5, 2016 | 正式版 |
| **3.0** | December 22, 2015 | 正式版 |
| **2.6** | December 22, 2014 | 正式版 |
| **2.5** | February 26, 2014 | 正式版 |
| **2.4** | June 13, 2013 | 正式版 |
| **2.3** | Sept 03, 2012 | 官方页面**无变更记录** |
| **2.2** | Oct 23, 2011 | 官方页面**无变更记录** |
| **2.1** | Oct 6, 2010 | 官方页面**无变更记录** |
| **2.0** | Sep 8, 2009 | 官方页面**无变更记录** |

> **命名规则变化**：2023.1 及之前用 `X.Y`（如 9.1、8.2）；**2024.1 起改为 `YYYY.N`**（如 2024.1、2026.2）。跨这个分界做版本比较时注意。

---

## 2. 不兼容变更汇总（Breaking Changes）

> **这是本文件最有价值的部分。** 官方从 **2024.1** 起才明确设置 `Breaking Changes` 章节；2023.2 及更早的变更条目未分节。

### 2.1 2027.1（开发中）

| # | 官方变更 | 影响 |
|---|---|---|
| 1 | **Require `MPI_THREAD_MULTIPLE` for all MPI builds**（PR #5811、#5817） | 独立可执行文件在初始化 MPI 时请求该级别，**不可用则停止**；作为库被外部调用时，应用必须用 `MPI_Init_thread` 请求 `MPI_THREAD_MULTIPLE` |
| 2 | **Drop compatibility of old DFT-D4 API**（PR #5641） | 旧版 DFTD4（低至 v3）接口不再可用 |
| 3 | Rename the RI-RS GW keyword `CUTOFF_RADIUS_RI_RS` to `CUTOFF_RADIUS_RL_RI`（PR #5621） | 旧关键字名失效 |
| 4 | Remove the deprecated `USE_PREV_RHO_R` wavefunction-extrapolation alias（PR #5666） | 用 `USE_PREV_RHO_R` 的输入失效 |
| 5 | Remove the `SPLINE3_NOPBC` multigrid interpolator（PR #5719） | 用该插值器的输入失效 |

**2027.1 新功能（供对照）**：

- MACE 机器学习势接口（经 LibTorch，PR #5580）
- GFN1/2-xTB 原生自旋极化（PR #5611）
- 非周期 RI-RS GW 改进（自动/分布式分解、流式面板、稀疏控制、独立实空间截断，PR #5621）
- 线性化实时 BSE 传播 + 开壳层支持（PR #5627）
- **张量形式 DFT+U+J** 与 U、J 的自洽最小追踪线性响应计算（PR #5631、#5638）
- **CELL_OPT 保留显式给定的晶胞取向**，并对晶胞度规应用 `KEEP_SPACE_GROUP`（PR #5648）
- NNP CPU 扩展性改进（缓存 cell lists + OpenMP，新增 `RAD_SPLINE_N` 与 `VERLET_SKIN` 控制，PR #5295）
- GauXC 对象缓存 + SKALA 多 GPU、默认启用 routed atom chunks、复合 GAPW 密度（PR #5340、#5644、#5670、#5675）
- Floquet-Bloch 并行化 + 有限温度占据谱权重与中心区能带输出（PR #5642）
- **`POTENTIAL_FILE_NAME` 可重复**，以搜索多个赝势文件（PR #5649）
- 电矩的紧凑轨迹输出（PR #5650）
- 原子极化张量计算支持 meta-GGA（含 DCDR，PR #5658）
- DFTB 与 xTB 的 Gaussian 静电 QM/MM 耦合（PR #5731）
- **GAPW 复合密度下的约束 DFT**（PR #5730）

**2027.1 修复**：HOMO 与最低分数占据轨道索引初始化（#5616）；UZH 基组文件 Na、Ca 条目错标修正（#5633）；半胞边界的周期镜像选择稳定化（#5646）；分布矩阵的分子矩求和（#5680）；四次元动力学墙能量（#5687）；ELPA 核选择与回退信息（#5700）；GauXC 能量与梯度中的 RKS 密度归一化（#5740）。

### 2.2 2026.2（July 15, 2026）

| # | 官方变更 | 影响 |
|---|---|---|
| 1 | **Remove `&MOTION/&CELL_OPT/TYPE`; cell optimizations now always use `DIRECT_CELL_OPT`**（PR #5257） | **旧输入的 `TYPE` 关键字会导致报错** |
| 2 | Drop support for **GCC 8**（PR #5290） | 编译环境要求提高 |
| 3 | **Refactor DOS/PDOS input section**（PR #5326） | **DOS/PDOS 输入段结构变了**，旧输入需改 |
| 4 | Remove obsolete **Cython Python bindings**（PR #5541） | Python 绑定方式变更 |
| 5 | **Remove `EVAL_ENERGY_FORCES` and `EVAL_FORCES` keywords in favor of `EVAL` under `&MOTION/&MD/&REFTRAJ`**（PR #5401） | 旧关键字失效 |
| 6 | **An implementation of the FFTW3 interface may be turned into a hard dependency in a later release.**（PR #5454） | 官方建议现在就编入 FFTW3/MKL/AOCL 等 |

**2026.2 新功能（重点）**：

| 主题 | 官方条目 |
|---|---|
| **k 点相关** | DFT+U with k-points for Mulliken methods（#4855）；Energy Correction Harris functional with k-points（#5031）；Lowdin population analysis for k-points（#5045）；Wavefunction extrapolation for k-point（#4884 等）；**K-point symmetry reduction**（#5123 等） |
| **外推** | GExt wavefunction extrapolation（#5043、#5229） |
| **HFX** | Adaptively Compressed Exchange (ACE) option to the HFX/ADMM ground-state path（#5238）；HFX 短程势截断半径输入关键字（#4945） |
| **SCF** | Alternative smearing methods（#4958） |
| **PIMD** | Brownian chain molecular dynamics (BCMD) propagator for path integrals（#5247） |
| **输出** | DOS/PDOS 展宽输出与 k 点投影（#5287、#5299）；NEB 相对能量图与最终结构输出（#5382）；优化最终结构输出为 CIF 与 EXTXYZ（#5118、#5140）；质量加权前的 Hessian 输出（#5395） |
| **几何** | Dimer 通过读取 molden 文件初始化（#5312）；**固定体积的晶胞优化**（#5086） |
| **巨正则 SCF** | 恒定电势（功函）巨正则 SCF 用于 3d 周期 slab（#5467）；平面反电荷模型（#5064）；新的 Pulay 混合（#5407） |
| **MD** | 按热区分别重标温度的 per-thermal-region 函数（独立于恒温器，#5002） |
| **溶剂化** | Solvent aware SCCS（#5495） |
| **EXTXYZ** | 从 EXTXYZ 解析晶胞信息（初始几何 + reftraj 每帧，#4960、#5401）；reftraj 计算前对每帧坐标做 wrapping（#5479） |
| **优化器** | L-BFGS 优化器打印控制关键字（#5274） |

**2026.2 新库**：openPMD 输出（含科学元数据，PR #4058 等）；GauXC/Skala 模型（#5084）；LibFCI 活性空间求解器（#5167）；重新集成 LIBXS / LIBXSTREAM / LIBXSMM（#5343）；libGint（CUDA 加速 HFX，#5446）。

### 2.3 2026.1（January 6, 2026）

| # | 官方变更 | 影响 |
|---|---|---|
| 1 | **Remove Makefile**（PR #4618） | **只能 CMake 构建** |
| 2 | **Remove QUIP**（PR #4616） | QUIP 势接口移除 |
| 3 | Some remaining issues with Intel compilers and CMake（PR #4550） | 官方自述遗留问题 |

**2026.1 新功能（重点）**：

- 新基组 **`BASIS_AUG_MOLOPT` 与 `BASIS_RI_AUG_MOLOPT`（全电子）**（#4354）
- Active Space：ERI 的新长程截断势（#4357）
- **CNEO-DFT 能量与力**（#4403、#4420）
- Sternheimer BSE（第一版含 W 矩阵，#4445）
- **SF-TDDFT 实现**（#4446）
- PAO-ML：迁移到 **NequIP** 框架（#4461）
- GAPW DC-DFT + EC EXTERNAL（#4502）
- NEGF：提取电极矩阵哈密顿量的新方法（#4520、#4636）
- RT-TDDFT + RT-BSE：傅里叶变换输出（#4527）
- RIXS：开壳层（#4533）
- **MiMiC 多尺度模拟框架接口**（#4546）
- TDDFPT 的受限空间激发（#4560、#4588）
- 振动光谱后处理工具（#4581）
- **轨迹的扩展 XYZ 格式**（#4601）
- `MO_CUBES` 段的 `MAX_FILE_SIZE_MB` 关键字（#4603）
- k 点计算的矩（moments）实现（#4621）
- OT 的占据轨道本征值更好获取（#4364）

### 2.4 2025.2（July 23, 2025）

| # | 官方变更 | 影响 |
|---|---|---|
| 1 | **Remove old TDDFPT code**（PR #4066） | 旧 TDDFPT 输入失效 |
| 2 | **Restore old format for writing forces to .xyz files**（PR #4294） | **格式回退**（注意方向） |
| 3 | **RTBSE: Input structure changed**（PR #3918） | RTBSE 输入段结构变更 |

**2025.2 新功能**：TDDFPT 激子描述符（#3847）；xTB 的 Efield（#3883）；**GFN-xTB**（#4005 等）；从/向 trexio 文件读写外能导数（#4009、#4074）；赝势新增三价与四价锕系的 5f-in-core（#4068）与 ccECP（#3940）；RTBSE Padé FT 精修（#4115）；HP-DFT 模块与回归测试（#4138）；**打印空间群选项**（#4271）；SIRIUS DFTD3/DFTD4 支持（#4277）；数值微分的原子极化张量（#4287）；RI-HFXk 改进（#4291）；**RIXS 模块**（#4315）。

**2025.2 新库**：DLA-Future 集成改进（#4169、#4269）；升级到 DeePMD 3.1.0 并切换 PyTorch 后端（#3893、#4310）；GRPP 变为内部依赖（#3966）；greenX 库接口（#4078）；ACE 支持（#4182）。

### 2.5 2025.1（January 1, 2025）

| # | 官方变更 | 影响 |
|---|---|---|
| 1 | Weighting of RSMD colvar is modified for the case of `subsystem = list`（PR #3818） | 该场景下权重变了 |

**2025.1 新功能**：BSE 光学谱、BSE@evGW(0) 等（#3628 等）；实时 Bethe-Salpeter 传播（#3691）；**Harris 与 EHT 方法（含 LS 求解器）**（#3665、#3780、#3790）；AO 基下打印 Wannier 态系数（#3683、#3687）；线性响应的 Z-matrix 形式与 `EVERY_N_STEP` 关键字（#3689、#3692）；RPA 基 SIGMA 泛函（#3695）；基于 KS 轨道的外能表达式响应力框架（#3721）；PAO 从等变 PyTorch 模型预测（#3738）；**gfn0-xTB 与并行 DFT-D4**（#3765、#3679、#3685）；展宽占据 TDA（#3829）；GW 新增 `SIZE_LATTICE_SUM` 与 `KPOINTS_W`（#3833）。

**2025.1 新库**：SMEAGOL（NEGF 电子输运，#3716）；**cuSOLVERMp** 广义特征求解器（#3787）；**DLA-Future** 广义与复数特征求解器（#3799、#3813、#3819）；TREXIO 文件格式写入（#3792）。

### 2.6 2024.3（September 9, 2024）——小版本

> This is a minor release to fix an issue with the PW environment that can lead to **stalls during MD**（<https://github.com/cp2k/cp2k/issues/3661>）.
>
> Since this only affects **MPI jobs**, the `ssmp` binaries from the previous 2024.2 release are still up-to-date.

| 要点 | 说明 |
|---|---|
| 修复 | PW 环境导致 **MD 停滞** |
| 影响范围 | **仅 MPI 作业** |
| 结论 | 2024.2 的 `ssmp` 二进制仍然适用 |

> **注意**：`08_errors_and_faq.md` §2.1.5 提到"优化与 NEB 会莫名卡住"，本条正是官方修复 MD 停滞的记录之一。

### 2.7 2024.2（August 6, 2024）

| # | 官方变更 | 影响 |
|---|---|---|
| 1 | **Increase ScaLAPACK default block size to 64**（PR #3184） | 默认值变化 |
| 2 | **Remove `BROYDEN_MIXING_NEW` option**（PR #3346） | 旧关键字失效 |
| 3 | Remove `KP_RI_EXTENSION_FACTOR` keyword（PR #3223） | 旧关键字失效 |
| 4 | **Mark support for QUIP and PEXSI as deprecated**（PR #3600） | 弃用警告 |

**2024.2 新功能**：手册 methods 节新增**大量页面**；ECP 核梯度（#3210）；新基组（#3266 等）；TDA Kernel 方法（#3273）；**分子的 Bethe-Salpeter 方程**（#3308、#3329）；NequIP & Allegro 的应力预测（#3428、#3445）；**小胞全 k 点的 GW**（#3448 等）；G0W0 的 Hedin shift（#3533）；**i-PI 服务器功能**（#3420）；K 点对称性基础设施（#3482）。

**2024.2 新库**：DeePMD-kit 机器学习（#3145）；**DFTD4 库色散校正**（#3501）；**OpenCL 的 GPU 支持**（#3321 等）。

### 2.8 2024.1（January 3, 2024）★

| # | 官方变更 | 影响 |
|---|---|---|
| 1 | **Abort run by default on SCF convergence failure**（PR #3148） | **最重要的一条**：SCF 不收敛不再静默继续 |
| 2 | Remove `SINGLE_PRECISION_MATRICES` keyword（#3096、#3140） | 旧关键字失效 |
| 3 | Drop support for **NDEBUG**（#3172） | 编译选项变化 |
| 4 | Production docker files moved to new repository（#3083） | Docker 镜像位置变更 |
| 5 | MD: Refactor `REFTRAJ` / `EVAL_ENERGY_FORCES` keyword（#2981） | 关键字重构 |
| 6 | **Drop CMake option `CP2K_BUILD_DBCSR`**（#3044） | CMake 选项失效 |

**2024.1 新功能**：**Docs: Launch Sphinx-based manual**（#2883）——即 `manual.cp2k.org` 上线；TDDFPT 的赝势、GAPW、GPW 与力（#2895 等）；**k 点的 RI-HFX（含梯度与 ADMM）**（#2998）；ADMM 输入快捷方式（#3118）；短程 DFT 嵌入中的长程量子计算（WF）（#2924）；活性空间用半变换积分做 ERI（#3082）；开壳层周期 GW（#2920 等）；G0W0/SOC 的能带、PDOS、局域带隙（#2994、#3130）；NNP 的 Helium-Solute 相互作用（#3043）；EMD 的时变场（#3081）。

**2024.1 新库**：DLA-Future 特征求解器实验支持（#3143）；libgrpp 库（ECP 计算，#3147）。

### 2.9 2023.2（July 28, 2023）

> 官方此版本**未设 Breaking Changes 章节**，变更条目平铺。

| 类别 | 条目 |
|---|---|
| GW | 周期开壳层、自旋轨道耦合导致的电子态劈裂（#2639、#2831） |
| 赝势 | 新增含自旋轨道耦合（SOC）参数的 GTH 赝势数据库文件（#2848） |
| RTP | TD 场速度规范与 TD-MO 投影（#2623、#2744）；线性密度 delta kick 与重启（#2543）；GAPW 下启用 ADMM（#2729） |
| APT/AAT | 速度形式下 APT 与 AAT 的 NVPT 实现（#2568、#2561） |
| 其它 | Intrinsic Atomic Orbitals（#2707） |
| 机器学习 | PyTorch 接口、Nequip 与 Allegro 模型（#2420、#2528、#2722） |
| **k 点** | **DIIS/Diag. 求解器实现**（#2721） |
| TDDFPT | SOC 吸收（#2859）；GAPW 三重态激发能与力（#2837、#2861） |
| EC | 参考与 DC 计算均启用 HFX-ADMM 的 DC-DFT（#2780） |
| 晶胞 | 新增晶胞对称性 `HEXAGONAL_GAMMA_120`（#2758） |
| 网格 | 重命名后端，**默认改为 `CPU`**（#2772、#2775、#2778）；大基组的 GPU 加速（#2787、#2793） |
| 特征求解 | NVIDIA cuSOLVERMp 实验支持（#2860） |
| 测试 | `--smoketest` 选项（#2501） |
| MPI | MPI Fortran 2008 绑定支持（#2486） |
| 容器 | Apptainer/Singularity 容器支持 |

> **重要**：**2023.2 起 k 点有 DIIS/Diag. 求解器**——这是 `02_dft_methods.md` §4 中 k 点方法演进的关键节点。

### 2.10 2023.1（January 1, 2023）

- SOS-MP2 与 RPA 的梯度（含基准，#2208 等）
- TDDFT/线性响应：GAPW/GAPW_XC 与 ADMM/GAPW 选项（#2200）
- TDDFT：激发态力作为性质（#2363）
- RI-RPA：ADMM RI-RPA 的 XC 校正（#2216）
- RTP：速度规范与磁 delta pulse（#2343）
- GW：自动外推 k 点网格（#2229）
- xTB：vdW 选项（#2431）；修复电子能量对 `EPS_DEFAULT` 的依赖（#2287）
- 振动分析：**Raman 强度**（#2263）
- 新赝势与基组
- 改进 NewtonX 接口（#2443）
- Fist：LAMMPS 风格表格化配对势（#2313）
- EC：变分密度校正 DFT（DC-DFT，#2322）
- 更新活性空间接口（#2346）
- Helium：补齐 xyz 输出格式（#2432）
- SIRIUS：libvdwxc 支持（#2270）
- ELPA：修复 GPU 上的块大小问题（#2407）
- **Drop Support for MPI 2.0**（#2438）★
- 新增实验性 CMake 构建系统（#2364）★
- 修复 ARM64 回归测试（#1855）
- 开始用 Address Sanitizer 测试（#2306）
- 开始在 macOS Apple M1 上测试（MacStadium 赞助）

### 2.11 2022.2（October 4, 2022）——小版本

> Minor release to fix the outdated url for Spglib in the toolchain（#2262）.

### 2.12 2022.1（July 8, 2022）

- 张量运算迁移到新稀疏矩阵库 **DBM**（#1863）
- PW 的 HIP 支持（#1864）
- **Drop support for GCC 5**（#1878）
- GAPW Voronoi 积分（#1919）
- 移除弃用的 `LIBXC` 与 `KE_LIBXC` 段（#1921）★
- ADMM 交换势的 LibXC 等价物（#1972）
- metaGGA 泛函支持改进（#1974）
- mp2 模块用 SPLA offload GPU 上的 dgemm（#1951）
- TDDFT：用跃迁电荷指纹跟踪态（#1991）
- 绝对坐标冻结原子的恒压器（#2000）
- 修复 COSMA 链接（#2021）
- 迁移到集中式 `__OFFLOAD_CUDA/HIP` 标志（#2027）
- 低标度 SOS-Laplace MP2 力（#2031）
- 基组优化代码重构（#2068）
- GW 自能的 k 点（#2073）
- CDFT：基于 Hirshfeld 分割的力（#2111）
- RPA：低标度梯度（#2131）
- MP2：更多求解器（#2142）
- GW：交换自能的 4 中心 Hartree-Fock 与 ADMM（#2145）
- 为 Newton-X 打印振动模式（#2146）
- 部分占据的 Wannier 态（#2154）
- Voronoi 积分：缓解对称结构问题，更多诊断输出（#2171）
- TDDFPT 能量支持 GAPW_XC（#2178）

### 2.13 9.1（December 31, 2021）

- 修复 macOS 构建（#1316）
- 新增 **NEWTONX 接口**（#1794）
- 新增 **Gromacs QM/MM 支持**
- DBCSR 的 HIP 与 OpenCL 实验支持
- 性能关键新代码采用 **BSD3 许可**（#1632）
- 新增 **GAL21 力场**（#1579）
- **Upgrade to `MPI_THREAD_SERIALIZED`**（#1564）★ —— 注意 2027.1 将升级到 `MPI_THREAD_MULTIPLE`
- 新赝势与基组（#1547、#1551）
- MO 系数对核坐标的解析导数（#1706）
- RI-HFX 的力（#1688）
- TDDFT 的力（#1670、#1759）
- 周期 GW 的正则化 RI（#1776）
- PINT 的逐 bead 约束（#1734）
- NNP 的解析应力张量（#1783）
- xTB 的 ghost 粒子与 tip scan（#1578）
- MP2 基双杂化的力与应力张量（#1647）
- 回归测试脚本改写为 Python（#1548）

### 2.14 8.2（May 28, 2021）

- 加速网格核，尤其非正交 CPU 与 GPU 上的积分
- 升级到 COSMA 2.5（#1303）
- **新增 ARM64 支持** ★
- **Drop support for GCC 6**（#1203）
- 升级到 **LibXC 5** 并统一其输入（#1304 等）
- xTB/DFTB：带 efield 的应力张量
- Motion：空间群对称性
- 修复多 GPU（一致设置活动设备，#814）
- 修复 MOLDEN 输出（#1335）
- XAS_TDP：修复开壳层 SOC 的 bug（#1304）
- PINT：修复 PINT-RPMD 重启的守恒量（#1290）
- **ELPA：为保险起见默认只对大型矩阵使用**（#1444）★
- libvori：增强的 `.voronoi` 文件格式更好支持 TRAVIS

> **`08_errors_and_faq.md` §2.1.3 提到"若用 ELPA 构建则是默认对角化库"**——本条（8.2，2021）说明官方对 ELPA 的使用范围做过限制调整，是版本敏感项。

### 2.15 8.1（December 30, 2020）

- 修复影响 GPU 上 ADMM 的 bug（#893）
- 修复影响 Amber 二面角的 bug（#984）
- **Drop support for Python 2 and non-OpenMP builds** ★
- 新增 GRRM17 与 SCINE 接口
- 新增 **COSMA** 支持
- 新增电子密度的 **Voronoi 积分**支持
- 新增压缩 **BQB** 格式输出
- 单电子积分的 OpenMP 重构与加速
- 极化率的响应码：有限差分调试、杂化泛函、ADMM
- **基于 Kohn-Sham 密度的 Harris 泛函**
- TDDFPT 代码重构，新增 sTDA kernel、xTB/sTDA 方法
- **NNP：Behler-Parrinello 神经网络势**
- XAS_TDP：新增 OT 求解器并改进性能
- mGGA：新增应力张量并修 bug（#1116）
- QMMM：基准测试并用 OpenMP 加速 GEEP
- LS：基于子矩阵方法的符号计算
- ALMO：信赖域方法
- **RI-HFX：Hartree-Fock 交换的分辨率恒等式**
- RPA/GW/MP2：低标度实现的若干优化与重构
- **CUDA：collocate 与 integrate 网格操作的 GPU 加速（实验性）**

### 2.16 7.1（December 24, 2019）

- **SIRIUS**：含 GPU 支持的平面波模块
- xTB：紧束缚模块
- RPA / GW / MP2：迁移到 DBCSR 张量
- **HELIUM**：新的 canonical worm 算法
- XAS_TDP：线性响应 TDDFT 的 X 射线吸收谱模拟
- NEGF：接触特定的温度、正确的 shift 与 scale 因子
- S-ALMO：重大重构，新增大量选项
- CDFT：清理与修 bug
- PW FFT 的 FPGA 接口
- 更新库：DBCSR、ELPA、libint、libxc、libxsmm
- `cp2k_shell` 并入主程序，用 `-s` 或 `--shell` 调用
- **开发从 SVN 迁移到 Git** ★

### 2.17 6.1（June 11, 2018）

- 投影算符绝热化（POD）方法
- CP2K 可基于电子结构库 **SIRIUS** 用 CPU 和 GPU 做平面波计算
- DBCSR 纳入 NVIDIA P100 kernels
- 更新 toolchain
- 防止小矩阵/大核数下 ELPA 对角化崩溃
- 用 MPI I/O 更快读写 cube 文件
- 基于 Docker 的测试

### 2.18 5.1（October 24, 2017）

- 基于 DBCSR 的稀疏张量框架
- 标志 `__ELPA2` 与 `__ELPA3` 移除，改用 `-D__ELPA=YYYYMM` 指定库版本 ★
- **约束 DFT**（CDFT 与 MIXED_CDFT）
- 立方标度 GW
- GW + 镜像电荷计算分子在金属表面的电子能级
- 约束晶胞优化（`MOTION/CELL_OPT/CONSTRAINT`）

### 2.19 4.1（October 5, 2016）

- Maximum Overlap Method（MOM）
- Modified Atomic Orbitals（MAO）分析
- 改进的 toolchain，安装更简单
- 改进开发工具：prettifier、API 文档
- 改进编码规范
- 更多集体变量
- OMEN 输运改进
- `libcp2k.h` 接口（C/C++ 头文件）
- Remote Memory Access（RMA）
- 若干性能改进与 bug 修复
- 镧系元素的 **GTH-PBE 赝势**
- 机器学习极化原子轨道（PAO-ML）
- 立方标度 RPA
- 周期 ERI 的快速方法（减少 QM/MM 镜像电荷校正开销）
- **Drop support for PLUMED 1.3（现在需要 PLUMED 2.x）** ★
- 改进的线性标度（LS）DFT MD（curvy steps）
- TDDFT 支持杂化泛函

### 2.20 3.0（December 22, 2015）

- 路径积分代码改进，使用 PIGLET 恒温器
- 规避 ifort 特性导致经典 MD 中 1-4 相互作用被错误忽略
- 非限制情形的 MP2 梯度
- EMD 的电流输出
- 恒定 E/D 模拟
- 基于 RMA 的 DBCSR
- 改进可移植性（xlf90）
- **G0W0 与本征值自洽 GW**
- 改进测试：make target `test` 现在会回归测试
- **GGA DFT 的基础 k 点功能** ★
- 半经验运行的更快 TRS4
- **PEXSI 库接口** ★
- **PLUMED 2.0 接口**
- ELPA2015 接口
- Filtered Basis 方法
- 更多优化 CUDA kernels
- 与量子输运代码 OMEN 耦合
- 隐式 Poisson 求解器（含介电与不同边界条件）
- LS SCF 启用 Rho 混合
- LRIGPW 方法加速
- ASE Python 工具包支持
- 更新 toolchain
- 规避 CUDA cufft 7.0 的已知问题
- 极化原子轨道
- RESP 原子电荷拟合的 REPEAT 变体
- 简化错误处理
- Intel libxsmm 支持

> **k 点历史起点**：**3.0（2015）引入"GGA DFT 的基础 k 点功能"**，2.6（2014）已有"K-points（部分方法的局部实现）"。这解释了为什么 2020 年的 FAQ 会写"CP2K 没有 k 点采样"——那是更早期状态的遗留表述。

### 2.21 2.6（December 22, 2014）

- 用 DBCSR 乘法例程实现全矩阵乘的 GPU 加速
- 带 HFX 与 ADMM NONE 的 RTP 与 EMD
- 改进 `FULL_SINGLE_INVERSE` 预条件器与大体系的线性标度 `PRECOND_SOLVER INVERSE_UPDATE`
- 自洽连续溶剂化（**SCCS**）模型
- **K-points（部分方法的局部实现）**
- 改进线性标度例程
- 改进 RPA 频率积分方法
- QUIP 多体势
- LRI 基组优化
- 完整 Fortran 2003 合规
- 各类 bug 修复、重构与加速
- 生产级参数集（基组、赝势等）
- 文件发现机制（编译标志 `-D__DATA_DIR` 或环境变量 `$CP2K_DATA_DIR`）★
- 新构建系统，用 makedep.py 替换 makedepf90
- 开始把代码拆成有明确依赖关系的子目录（包）
- DBCSR CUDA kernels 的自动调优框架与众多已优化 kernel 参数
- DFTB 的 QM/MM
- **LRIGPW**
- Hirshfeld 布居分析
- 基于 DM 与电荷约束投影的 ADMM

> **`$CP2K_DATA_DIR` 的官方来源**：本条给出了数据目录发现机制的引入版本。

### 2.22 2.5（February 26, 2014）

- MP2 梯度与应力
- emacs / vim 输入语法高亮插件
- SCF 后线性响应，含 Raman
- Cray 的能量使用框架
- RI-MP2 辅助基组优化
- 几何的全局优化
- SCP 紧束缚
- 原子块的相对论校正
- **CUDA 启用的 DBCSR**
- 改进 OMP 并行
- Tree Monte Carlo：MC 的额外并行
- ALMO：分子体系的线性标度
- 移除内部 ELPA，改为外部库 ★
- 集成分子基组优化
- Langevin 动力学区域
- 对齐晶胞的 DCD dump 选项
- 大量 bug 修复

### 2.23 2.4（June 13, 2013）

- **GPW-MP2 & RPA**
- 自适应 QM/MM
- 非局域 vdW 泛函、PBEsol
- 集成基组优化
- 非线性核校正赝势支持
- 更多线性标度算法与性质
- 可使用镜像电荷
- 周期 RESP 电荷
- **PLUMED 支持**
- **ELPA 特征求解器支持**
- **libxc 支持**
- 改进 ifort/MKL 支持
- Cray Gemini 的进程拓扑映射

### 2.24 2.3 / 2.2 / 2.1 / 2.0

官方页面**无变更记录内容**（仅有版本号与日期）。

---

## 3. 关键不兼容项专题汇总

> 按"会影响输入文件能否运行"分类，方便升级前逐条自查。

### 3.1 已移除的输入关键字 / 段

| 版本 | 移除项 | 替代 |
|---|---|---|
| 2027.1 | `CUTOFF_RADIUS_RI_RS`（RI-RS GW） | 改为 `CUTOFF_RADIUS_RL_RI` |
| 2027.1 | `USE_PREV_RHO_R`（波函数外推别名） | — |
| 2027.1 | `SPLINE3_NOPBC` 多重网格插值器 | — |
| 2026.2 | `&MOTION/&CELL_OPT/TYPE` | 始终 `DIRECT_CELL_OPT` |
| 2026.2 | `EVAL_ENERGY_FORCES`、`EVAL_FORCES` | `&MOTION/&MD/&REFTRAJ` 下的 `EVAL` |
| 2024.2 | `BROYDEN_MIXING_NEW` | — |
| 2024.2 | `KP_RI_EXTENSION_FACTOR` | — |
| 2024.1 | `SINGLE_PRECISION_MATRICES` | — |
| 2022.1 | `&LIBXC` 与 `&KE_LIBXC` 段 | 用 `&XC_FUNCTIONAL` |

### 3.2 输入结构重构

| 版本 | 变更 |
|---|---|
| 2026.2 | **DOS/PDOS 输入段重构** |
| 2025.2 | RTBSE 输入结构变更 |
| 2024.1 | `REFTRAJ` / `EVAL_ENERGY_FORCES` 关键字重构 |

### 3.3 默认行为变更

| 版本 | 变更 | 影响 |
|---|---|---|
| **2024.1** | **SCF 不收敛默认 ABORT** | 旧脚本"不报错即成功"的假设失效 |
| 2024.2 | ScaLAPACK 默认块大小增至 64 | 性能/内存特征变化 |
| 2023.2 | 网格后端默认改为 `CPU` | GPU 需显式启用 |
| 2025.1 | `subsystem = list` 时 RSMD colvar 加权方式变更 | 数值结果变化 |

### 3.4 编译 / 环境要求提升

| 版本 | 变更 |
|---|---|
| 2027.1 | **要求 `MPI_THREAD_MULTIPLE`** |
| 2026.2 | 停止支持 GCC 8；FFTW3 未来可能成为硬依赖 |
| 2026.1 | **移除 Makefile（只能 CMake）**；移除 QUIP |
| 2024.1 | 停止支持 NDEBUG；移除 CMake 选项 `CP2K_BUILD_DBCSR` |
| 2022.1 | 停止支持 GCC 5 |
| 8.2 | 停止支持 GCC 6；新增 ARM64 支持 |
| 8.1 | **停止支持 Python 2 与非 OpenMP 构建** |
| 4.1 | 停止支持 PLUMED 1.3 |
| 2023.1 | 停止支持 MPI 2.0 |

### 3.5 库 / 依赖变更

| 版本 | 变更 |
|---|---|
| 2027.1 | 移除旧 DFT-D4 API 兼容 |
| 2026.2 | 移除过时 Cython Python 绑定；新增 openPMD、GauXC/Skala、LibFCI、LIBXS/XSTREAM/XSMM、libGint |
| 2026.1 | 移除 QUIP |
| 2025.2 | 移除旧 TDDFPT 代码；DeePMD 升级到 3.1.0（PyTorch 后端）；GRPP 变内部依赖；新增 SMEAGOL、cuSOLVERMp、DLA-Future、TREXIO |
| 2024.2 | QUIP 与 PEXSI 标记为 deprecated；新增 DeePMD-kit、DFTD4、OpenCL GPU |
| 2024.1 | 新增 DLA-Future 实验支持、libgrpp |
| 2023.2 | 网格后端重命名 |
| 2022.1 | 张量运算迁移到 DBM |
| 9.1 | DBCSR 支持 HIP/OpenCL（实验） |
| 8.2 | 升级到 LibXC 5 |
| 8.1 | 新增 COSMA、Voronoi 积分、BQB 格式 |
| 7.1 | 更新 DBCSR、ELPA、libint、libxc、libxsmm |
| 5.1 | 移除 `__ELPA2` / `__ELPA3`，改用 `-D__ELPA=YYYYMM` |
| 2.5 | 移除内部 ELPA，改用外部库 |

---

## 4. 版本相关的功能引入时间线（按主题）

### 4.1 k 点

| 版本 | 进展 |
|---|---|
| 2.6（2014） | K-points（部分方法的局部实现） |
| 3.0（2015） | **GGA DFT 的基础 k 点功能** |
| 2022.1 | GW 自能的 k 点 |
| 2023.2 | **DIIS/Diag. 求解器** |
| 2024.1 | **k 点的 RI-HFX（含梯度与 ADMM）** |
| 2024.2 | 小胞全 k 点的 GW；K 点对称性基础设施 |
| 2026.2 | **DFT+U with k-points**；**Harris 泛函 with k-points**；Lowdin 布居分析；波函数外推；**k 点对称性约化**；DOS/PDOS 的 k 点投影；矩 |

### 4.2 HFX / 杂化泛函

| 版本 | 进展 |
|---|---|
| 8.1（2020） | **RI-HFX**（分辨率恒等式） |
| 9.1（2021） | RI-HFX 的力 |
| 2022.1 | GW 交换自能的 4 中心 HF 与 ADMM |
| 2024.1 | k 点的 RI-HFX |
| 2026.2 | **ACE（自适应压缩交换）加入 HFX/ADMM 基态路径**；HFX 短程势截断半径关键字 |
| 2026.2 | libGint（CUDA 加速 HFX） |

### 4.3 机器学习势

| 版本 | 进展 |
|---|---|
| 2023.2 | PyTorch 接口、**Nequip 与 Allegro 模型** |
| 2024.1 | NNP 的 Helium-Solute 相互作用 |
| 2024.2 | **DeePMD-kit**；NequIP & Allegro 应力预测 |
| 2025.1 | PAO 从等变 PyTorch 模型预测 |
| 2025.2 | DeePMD 升级到 3.1.0（PyTorch 后端）；**ACE 支持** |
| 2026.1 | PAO-ML 迁移到 NequIP 框架 |
| 2026.2 | **GauXC/Skala 模型** |
| 2027.1 | **MACE 接口**（经 LibTorch） |

### 4.4 DFT+U

| 版本 | 进展 |
|---|---|
| 2026.2 | **DFT+U with k-points for Mulliken methods** |
| 2027.1 | **张量形式 DFT+U+J**；U、J 的自洽最小追踪线性响应计算 |

> **注意**：`02_dft_methods.md` §8 记录的 DFT+U 官方 HowTo 中 `PLUS_U_METHOD Mulliken` 是当前主流做法。2027.1 将新增**张量形式**与**自洽 U/J**，属开发版功能。

### 4.5 分子动力学

| 版本 | 进展 |
|---|---|
| 2024.3 | 修复 PW 环境导致 MD 停滞（仅 MPI） |
| 2024.1 | EMD 的时变场 |
| 2026.1 | — |
| 2026.2 | 按热区重标温度（独立于恒温器）；BCMD 路径积分传播器；固定体积晶胞优化 |
| 2027.1 | Floquet-Bloch 并行化 |

### 4.6 优化

| 版本 | 进展 |
|---|---|
| 2024.1 | — |
| 2026.1 | 修复 GEO_OPT 中 CG 的 3PNT 线搜索（#4665） |
| 2026.2 | **固定体积晶胞优化**；L-BFGS 打印控制关键字；优化最终结构输出为 CIF/EXTXYZ；Dimer 通过 molden 初始化 |
| 2027.1 | **CELL_OPT 保留显式晶胞取向**；对晶胞度规应用 `KEEP_SPACE_GROUP` |

### 4.7 巨正则 SCF

| 版本 | 进展 |
|---|---|
| 2026.2 | 恒定电势（功函）巨正则 SCF 用于 3d 周期 slab；平面反电荷模型；新的 Pulay 混合 |

---

## 5. 使用建议（G 层给的操作性提示）

| 场景 | 建议动作 |
|---|---|
| 拿到别人给的输入文件跑不动 | 先查文件里是否用了 §3.1 已移除的关键字 |
| 同一输入在两台机器结果不同 | 先确认 CP2K 版本是否一致（`cp2k -v` 或输出文件头） |
| SCF 不收敛导致作业失败 | 这是 **2024.1 起**的默认行为，不是 bug；见 `03_scf_convergence.md` |
| 想用 k 点 | 确认版本 ≥ 2023.2（DIIS/Diag. 求解器） |
| 想用 k 点的 DFT+U | 需要 **2026.2 或更新** |
| 编译报 GCC 版本错误 | 见 §3.4 的编译器支持下限表 |
| 用 Makefile 编译 | **2026.1 起已移除**，必须用 CMake |
| MPI 环境启动即停止 | 检查是否为 2027.1+ 且 MPI 不提供 `MPI_THREAD_MULTIPLE` |
| 升级后 DOS/PDOS 输入报错 | 2026.2 重构了该段 |
| 升级后 `&CELL_OPT TYPE` 报错 | 2026.2 移除了该关键字 |

---

## 6. 官方页面缺口

| 项 | 状态 |
|---|---|
| 2.3 / 2.2 / 2.1 / 2.0 | 官方页面**无变更记录** |
| 2023.2 及更早版本的 Breaking Changes 分节 | 官方**未设**该章节，需自行从条目判断 |
| 每个变更的**完整关键字对照表** | 官方无此表，需查各版本 PR 与 Input Reference |
| 版本兼容性矩阵（输入文件跨版本） | 官方无 |

---

## → 交叉索引

| 本文件内容 | 关联 A/F 层条目 | 关联 G 层文件 |
|---|---|---|
| 2024.1 SCF 不收敛默认 ABORT | A 层 decide.md、F 层 `playbook.md` | `03_scf_convergence.md` §1.1 |
| 2026.2 移除 `CELL_OPT/TYPE` | F 层 `playbook.md` 晶胞优化 | `05_optimization.md` |
| k 点演进时间线 | A 层 decide.md k 点节 | `02_dft_methods.md` §4、`07_restarting.md` §2 |
| DFT+U 演进 | A 层 decide.md DFT+U 节 | `02_dft_methods.md` §8 |
| 外推方法演进（GExt / ASPC） | — | `04_sampling_md.md` |
| FFTW3 可能成为硬依赖 | — | `09_build_libraries.md` §3.2 ④ |
| MPI 版本与 `MPI_THREAD_MULTIPLE` | — | `09_build_libraries.md` §3.1 ③ |
| DFT-D4 API 变更 | — | `09_build_libraries.md` §3.6 ⑰ |
| 网格后端默认 CPU | — | `09_build_libraries.md` §5 |
| ELPA 默认使用范围 | — | `08_errors_and_faq.md` §2.1.3 |
| 新库引入（openPMD / TREXIO / libGint 等） | — | `09_build_libraries.md` §3 |
| 新功能清单（features 页滞后） | — | `10_features_resources.md` §2、§7 |
