# 19 · 性能基准、加速器、社区与开发（官方）

> 来源：
> - https://www.cp2k.org/performance
> - https://www.cp2k.org/performance:systems
> - https://dashboard.cp2k.org/
> - https://manual.cp2k.org/trunk/technologies/accelerators/index.html
> - https://manual.cp2k.org/trunk/technologies/accelerators/cuda.html
> - https://manual.cp2k.org/trunk/technologies/accelerators/hip.html
> - https://manual.cp2k.org/trunk/technologies/eigensolvers/index.html
> - https://manual.cp2k.org/trunk/technologies/libraries.html
> - https://manual.cp2k.org/trunk/development/onboarding.html
> - https://manual.cp2k.org/trunk/getting-started/build-with-spack.html
> - https://manual.cp2k.org/trunk/getting-started/troubleshooting.html
> 抓取日期：2026-09-08
> 标注规则：`[默认]` = 官方默认值；`[官方推荐]` = 官方明确建议；`[示例]` = 官方示例原样；`[G层提示]` = 本层基于官方原文给出的使用提示（非官方原文）

---

## 0. 本文件补什么

| 主题 | 此前状态 | 本文件 |
|---|---|---|
| 官方 benchmark suite（5 项） | 无 | **§1 完整** |
| 测试机器规格 | 无 | **§2 完整** |
| dashboard 回归测试平台 | 仅知道网址 | **§3 完整** |
| CUDA / HIP 编译选项 | 部分 | **§4 完整（逐条）** |
| 特征求解器 | 一句 | **§5** |
| Spack 安装 | 仅提及 | **§6 完整** |
| 库的详细配置要求 | 部分 | **§7 补充** |
| 参与开发流程 | 无 | **§8 完整** |

---

## 1. 官方基准测试套件（官方 performance 页）

### 1.1 目的（官方原文）

> The purpose of the CP2K benchmark suite is to provide performance which can be used to **guide users towards the best configuration** (e.g. machine, number of MPI processors, number of OpenMP threads) for a particular problem, and give a good estimation for the parallel performance of the code for different types of method.

共 5 项基准：

| 编号 | 名称 | 类型 |
|---|---|---|
| 1 | `H2O-64` | AIMD / DFT |
| 2 | `Fayalite-FIST` | 经典力场 MD（FIST） |
| 3 | `LiH-HFX` | 杂化泛函单点（GAPW + HFX） |
| 4 | `H2O-DFT-LS` | 线性标度 DFT 单点 |
| 5 | `H2O-64-RI-MP2` | RI-MP2 单点 |

官方邀请：

> We encourage you to contribute benchmark results from your own local cluster or HPC system - just run the inputs and add timings in the relevant sections below. Python scripts for generating the scaling graphs are provided `tools/benchmark_plots/`.

联系人：Iain Bethune (ibethune@epcc.ed.ac.uk)

### 1.2 结果解读注意事项（官方，重要）

| 要点 | 官方原文 |
|---|---|
| 报告内容 | "the total time for the calculation against the number of compute nodes used" |
| **不可直接比较** | "Each benchmark uses a different system, so the results are **not directly comparable**." |
| 混合模式 | "The mixed mode MPI/OpenMP version of CP2K is used to measure performance (there is negligible overhead from running this version with 1 thread per process compared to the pure MPI code)." |
| 线程绑定 | "all reasonable combinations of MPI processes and OpenMP threads were tested, subject to keeping each processes' threads within a **single NUMA region**" |
| NUMA 实例 | "on ARCHER, 6 cores share a single NUMA region, so **no more than 6 threads per process** were used as the resulting performance would be very poor" |
| 报告口径 | "From these combinations, the **best** run time and number of threads per process is reported." |
| 计费 | "As most HPC systems charge by the node, **full nodes** were utilised at all times." |

`[G层提示]` 关键实践结论：**每个进程的线程数不要超过单个 NUMA 域的核数**。这是官方实测经验。

### 1.3 五项基准详情

#### ① H2O-64

| 项目 | 内容 |
|---|---|
| 方法 | 玻恩-奥本海默 AIMD，Quickstep DFT |
| 设置 | TZV2P 基组、平面波截断 **280 Ry**、**LDA** 交换关联 |
| 初猜 | 由经典平衡构型生成，电子密度初猜基于原子轨道 |
| 体系 | **64 个水分子（192 原子，512 电子）**，12.4 Å³ 盒子 |
| MD 步数 | **10 步** |
| 文件位置 | `benchmarks/QS/`（随 CP2K 源码分发） |

官方结果（最佳配置）：

| 机器 | 架构 | 日期 | Git Commit | 最快时间 (s) | 配置 |
|---|---|---|---|---|---|
| HECToR | Cray XE6 | 21/01/2014 | 82b8204 | 39.066 | 512 核，2 OMP 线程/MPI 任务 |
| ARCHER | Cray XC30 | 08/01/2014 | 292a983 | 18.11 | 576 核，1 OMP 线程/MPI 任务 |
| Magnus | Cray XC40 | 22/10/2014 | 27eacee | 17.275 | 384 核，1 OMP 线程/MPI 任务 |
| Piz Daint | Cray XC30 | 12/05/2015 | f439118 | 19.885 | 192 核，1 OMP 线程/MPI 任务，无 GPU |
| Cirrus | SGI ICE XA | 24/11/2016 | 989a92c | 15.560 | 1152 核，9 OMP 线程/MPI 任务 |
| Noctua | Cray CS500 | 25/09/2019 | 9f58d81 | 13.3 | 640 核，10 OMP 线程/MPI 任务 |

#### ② Fayalite-FIST

| 项目 | 内容 |
|---|---|
| 方法 | NPT 系综 300 K，1000 时间步短 MD |
| 体系 | **28000 原子**，103 超胞，每胞 28 原子铁橄榄石 Fe₂SiO₄ |
| 势 | 经典势（Morse + 硬核排斥项，**5.5 Å 截断**）+ SPME 长程静电 |
| 官方说明 | "While CP2K does support classical potentials via the Frontiers In Simulation Technology (FIST) module, this is **not a typical calculation for CP2K** but is included to give an impression of the performance difference between machines for the **MM part of a QM/MM calculation**." |
| 文件位置 | `benchmarks/Fist/` |

官方结果：

| 机器 | 架构 | 日期 | Git Commit | 最快时间 (s) | 配置 |
|---|---|---|---|---|---|
| HECToR | Cray XE6 | 21/01/2014 | 82b8204 | 403.928 | 2048 核，4 OMP 线程/MPI 任务 |
| ARCHER | Cray XC30 | 09/01/2014 | 292a983 | 197.117 | 576 核，6 OMP 线程/MPI 任务 |
| Magnus | Cray XC40 | 06/11/2014 | 27eacee | 150.493 | 768 核，6 OMP 线程/MPI 任务 |
| Piz Daint | Cray XC30 | 12/05/2015 | f439118 | 207.972 | 512 核，2 OMP 线程/MPI 任务，无 GPU |
| Cirrus | SGI ICE XA | 24/11/2016 | 989a92c | 166.192 | 576 核，2 OMP 线程/MPI 任务 |
| Noctua | Cray CS500 | 25/09/2019 | 9f58d81 | 119.820 | 2560 核，10 OMP 线程/MPI 任务 |

#### ③ LiH-HFX

| 项目 | 内容 |
|---|---|
| 方法 | Quickstep **GAPW** + 杂化 Hartree-Fock 交换，单点能 |
| 体系 | **216 原子** LiH 晶体，432 电子，12.3 Å³ 盒子 |
| 成本量级 | "These types of calculations are generally around **one hundred times** the computational cost of a standard local DFT calculation, although this can be reduced using the **Auxiliary Density Matrix Method (ADMM)**." |
| OpenMP 的作用 | "Using OpenMP is of particular benefit here as the HFX implementation requires a large amount of memory to store partial integrals. By using several threads, fewer MPI processes share the available memory on the node and thus enough memory is available to **avoid recomputing any integrals on-the-fly**, improving performance." |
| 文件位置 | `benchmarks/QS_LiH_HFX/` |

官方结果：

| 机器 | 架构 | 日期 | Git Commit | 最快时间 (s) | 配置 |
|---|---|---|---|---|---|
| HECToR | Cray XE6 | 21/01/2014 | 82b8204 (*) | 121.362 | 65536 核，8 OMP 线程/MPI 任务 |
| ARCHER | Cray XC30 | 09/01/2014 | 292a983 (*) | 51.172 | 49152 核，6 OMP 线程/MPI 任务 |
| Magnus | Cray XC40 | 10/11/2014 | 27eacee (*) | 62.075 | 24576 核，4 OMP 线程/MPI 任务 |
| Piz Daint | Cray XC30 | 12/05/2015 | f439118 | 66.051 | 32768 核，4 OMP 线程/MPI 任务，无 GPU |
| Cirrus | SGI ICE XA | 24/11/2016 | 989a92c | 483.676 | 2016 核，6 OMP 线程/MPI 任务 |

官方脚注（**重要**）：

> (*) Prior to r14945, a **bug resulted in an underestimation of the number of ERIs which should be computed** (by roughly 50% for this benchmark). Therefore these results **cannot be compared directly** with later ones.

`[G层提示]` 带 (*) 的数据是**有 bug 的历史数据**，只能纵向看同机趋势，不能与后续版本横向比。

#### ④ H2O-DFT-LS（线性标度）

| 项目 | 内容 |
|---|---|
| 方法 | 线性标度 DFT 单点能 |
| 体系 | **6144 原子**，39 Å³ 盒子（2048 个水分子） |
| 设置 | LDA 泛函，DZVP MOLOPT 基组，**300 Ry 截断** |
| 官方说明 | "For large systems the linear-scaling approach for solving Self-Consistent-Field equations will be much cheaper computationally than using standard DFT and **allows scaling up to 1 million atoms for simple systems**." |
| 机理 | "The linear scaling cost results from the fact that the algorithm is based on an **iteration on the density matrix**. The **cubically-scaling orthogonalisation step of standard Quickstep DFT using OT is avoided** and the key operation is sparse matrix-matrix multiplications, which have a number of non-zero entries that scale linearly with system size. These are implemented efficiently in the **DBCSR** library." |
| 文件位置 | `benchmarks/QS_DM_LS/H2O-dft-ls.inp`（问题规模由参数 `NREP` 调节） |

官方结果：

| 机器 | 架构 | 日期 | Git Commit | 最快时间 (s) | 配置 |
|---|---|---|---|---|---|
| HECToR | Cray XE6 | 16/01/2014 | 82b8204 | 98.256 | 65536 核，8 OMP 线程/MPI 任务 |
| ARCHER | Cray XC30 | 08/01/2014 | 292a983 | 28.476 | 49152 核，4 OMP 线程/MPI 任务 |
| Magnus | Cray XC40 | 03/12/2014 | 27eacee | 30.921 | 24576 核，2 OMP 线程/MPI 任务 |
| Piz Daint | Cray XC30 | 12/05/2015 | f439118 | 27.900 | 32768 核，2 OMP 线程/MPI 任务，无 GPU |
| Cirrus | SGI ICE XA | 24/11/2016 | 989a92c | 543.032 | 2016 核，2 OMP 线程/MPI 任务 |
| Noctua | Cray CS500 | 25/09/2019 | 9f58d81 | 37.730 | 10240 核，10 OMP 线程/MPI 任务 |

`[G层提示]` 官方明确：线性标度**避免了 OT 的三次标度正交化步骤**，核心是稀疏矩阵乘法（DBCSR）。这与 A 层"OT vs 对角化"的讨论互补——线性标度是第三条路。

#### ⑤ H2O-64-RI-MP2

| 项目 | 内容 |
|---|---|
| 方法 | RI 近似的二阶 Møller-Plesset 微扰论单点能 |
| 体系 | 64 个水分子，12.4 Å³ 盒子（**与 H2O-64 完全相同的体系**） |
| 成本量级 | "around **100 times** more computationally demanding than standard DFT calculations" |
| 文件位置 | `benchmarks/QS_mp2_rpa/64-H2O/` |

官方结果：

| 机器 | 架构 | 日期 | Git Commit | 最快时间 (s) | 配置 |
|---|---|---|---|---|---|
| HECToR | Cray XE6 | 13/01/2014 | 82b8204 | 141.633 | 49152 核，8 OMP 线程/MPI 任务 |
| ARCHER | Cray XC30 | 09/01/2014 | 292a983 | 83.945 | 36864 核，4 OMP 线程/MPI 任务 |
| Magnus | Cray XC40 | 04/11/2014 | 27eacee | 63.891 | 24576 核，6 OMP 线程/MPI 任务 |
| Piz Daint | Cray XC30 | 12/05/2015 | f439118 | 48.15 | 32768 核，8 OMP 线程/MPI 任务，无 GPU |
| Cirrus | SGI ICE XA | 24/11/2016 | 989a92c | 303.571 | 2016 核，1 OMP 线程/MPI 任务 |
| Noctua | Cray CS500 | 25/09/2019 | 9f58d81 | 82.571 | 10240 核，2 OMP 线程/MPI 任务 |

---

## 2. 测试机器规格（官方 performance:systems）

### 2.1 Cray 系统

| 名称 | 架构 | 处理器 | 频率 (GHz) | 节点数 | 核/节点 | 峰值 (TFlop/s) | GFlop/s/节点 | 年份 |
|---|---|---|---|---|---|---|---|---|
| HECToR Phase 3 | Cray XE6 | AMD Opteron 6276 "Interlagos" 16 核 | 2.3 | 2816 | 32 | 829.03 | 294.4 | 2011 |
| ARCHER Phase 1 | Cray XC30 | Intel Xeon E5-2697 v2 "Ivy-Bridge" 12 核 | 2.7 | 3008 | 24 | 1559.35 | 518.4 | 2013 |
| Magnus | Cray XC40 | Intel Xeon E5-2690 v3 "Haswell" 12 核 | 2.6 | 1488 | 24 | 1485.6 | 998.4 | 2014 |
| Piz Daint | Cray XC30 | Intel Xeon E5-2670 "Sandy-Bridge" 8 核 + NVIDIA Tesla K20X GPU | 2.6 | 5272 | 8 + 1 GPU | 7787 | 166.4 (CPU) + 1311 (GPU) | 2015 |
| Noctua | Cray CS500 | Intel Xeon Gold 6148 "Skylake-SP" 20 核 | 2.4 | 272 | 40 | 761.6 | 2800 | 2018 |

### 2.2 附加系统

| 名称 | 架构 | 处理器 | 频率 (GHz) | 节点数 | 核/节点 | 峰值 (TFlop/s) | GFlop/s/节点 | 年份 |
|---|---|---|---|---|---|---|---|---|
| Cirrus | SGI ICE XA | Intel Xeon E5-2695 v4 "Broadwell" 18 核 | 2.1 | 56 | 36 | 67.7 | 1209.6 | 2016 |

`[G层提示]` 这些数据**最新到 2019 年**，官方页最后修改日期为 2020/11/10（由 rschade 修改）。用于相对比较可以，**不要用来估计当前硬件的绝对性能**。

---

## 3. CP2K Dashboard（官方回归测试平台）

网址：`https://dashboard.cp2k.org/`

### 3.1 它是什么（G 层定位）

官方 onboarding 页明确引用：

> You will be notified if any of the tests on our **Dashboard** breaks.

即 dashboard 是 CP2K 的**官方持续集成与回归测试状态面板**，属官方渠道（L0/L2）。

### 3.2 面板内容

- **Recent Commits**：最近提交（含作者、git hash、时间）
- **More...** 下的三类链接：`Test Coverage`、`Discontinued Tests`、`Supported compilers`
- 测试矩阵：按 Name / Host / Status / Commit / Summary / Last OK 列出

### 3.3 抓取时的实际状态（2026-09-08，仅作示例）

| 测试项 | Host | 状态 | Summary |
|---|---|---|---|
| CSCS Daint (psmp) | Alps Daint (CSCS) | OK | correct: 6221 / 6221; 3min |
| CSCS Daint (psmp, H100) | Alps Daint (CSCS) | **FAILED** | correct: 6244 / 6245; failed: 1 |
| CSCS Eiger (ssmp) | Alps Eiger (CSCS) | OK | correct: 6131 / 6131; 4min |
| CSCS Eiger (psmp) | Alps Eiger (CSCS) | OK | correct: 6221 / 6221; 7min |
| Precommit | GCP | OK | Found 9325, skipped 0, checked 9325, and failed 0 files |
| Coding conventions | GCP | OK | Found 0 issues (250 suppressed) |
| Current Toolchain (psmp) | GCP | OK | correct: 6220 / 6220; 27min |
| Ubuntu, GCC 9–16 (ssmp) | GCP | OK | correct: 4613 / 4613; 8–13min |
| Minimal build | GCP | **FAILED** | correct: 3340 / 3388; wrong: 33; failed: 15 |
| Coverage | GCP | OK | correct: 6220 / 6220; 21min |
| Manual generation | GCP | OK | Manual generation works fine |
| Doxygen generation | GCP | OK | Doxygen generation works fine |
| ASE Calculator | GCP | OK | ASE commit 5881b77 works fine |
| AiiDA-CP2K Plugin | GCP | **FAILED** | Something is wrong with aiida-cp2k commit c6b973e |
| i-Pi | GCP | OK | i-Pi commit 2a4611c works fine |
| Phonopy | GCP | OK | Phonopy commit 6683c73 works fine |
| Gromacs QM/MM | GCP | OK | Gromacs commit 1210900 works fine |
| Performance OpenMP | GCP | OK | Performance test took 45 minutes |
| Performance CUDA Volta | GCP | OK | Performance test took 42 minutes |
| ARM64 | GCP | OK | correct: 6070 / 6070; 45min |
| macOS on Apple M1 (psmp) | MacStadium | **FAILED** | correct: 6220 / 6221; wrong: 1 |
| Spack (ssmp, CUDA P100) | GCP | **FAILED** | correct: 6138 / 6143; wrong: 5 |
| HIP ROCm build (psmp) | GCP | **FAILED** | Docker build had non-zero exit status |
| Intel oneAPI (ssmp, ifx) | GCP | **FAILED** | correct: 4153 / 4188; wrong: 2; failed: 33 |
| Intel oneAPI (psmp, ifort) | GCP | **FAILED** | correct: 6056 / 6058; wrong: 2 |
| Address Sanitizer | GCP | **FAILED** | correct: 6186 / 6188; failed: 2 |

`[G层提示]` 这些是**瞬时快照**，只用于说明面板能看什么。判断某版本是否可靠时，应**实时查 dashboard**，不要引用本文件的快照数字。

### 3.4 从面板能读出的有用信息（G 层提炼）

| 信息 | 用途 |
|---|---|
| 回归测试规模 | 约 **6200** 个测试用例（psmp），约 4600（Ubuntu ssmp） |
| 支持编译器 | GCC 9–16、Intel oneAPI（ifx/ifort）、以及各类 toolchain |
| 第三方生态测试 | ASE、AiiDA、i-Pi、Phonopy、GROMACS QM/MM —— 说明这些是**官方跟踪的生态接口** |
| 性能测试 | OpenMP 与 CUDA Volta 各有独立性能回归（约 42–45 分钟） |
| 平台覆盖 | CSCS Alps（Daint/Eiger，含 H100）、ARM64、macOS Apple M1 |

---

## 4. 加速器：CUDA 与 HIP（官方，逐条）

### 4.1 索引页

官方 `technologies/accelerators/index.html` 仅列两页：CUDA、HIP / ROCm。

### 4.2 CUDA（官方全文）

| 选项 | 说明 |
|---|---|
| `-DCP2K_USE_ACCEL=CUDA` | 通用启用 NVIDIA GPU 支持 |
| `-DCMAKE_CUDA_ARCHITECTURES` | 指定 CUDA compute capability，例如 `100` 对应 B200 |
| `-DCP2K_WITH_GPU` | **已废弃**的选择器，仍可用，取值：K20X、K40、K80、P100、V100、A100、H100、B200、GB10、A40 |
| `-DCP2K_USE_NVHPC=ON` | 用 NVHPC kit 构建时 |
| `-DCP2K_WITH_GPU_PROFILING` | 开启 NVIDIA Tools Extensions；需要链接 `-lnvToolsExt` |
| BLAS/ScaLAPACK | 链接能加速大 DGEMM 的库（如 `libsci_acc`） |
| `-DCP2K_ENABLE_GRID_GPU=OFF` | 关闭 grid 库的 GPU 后端 |
| `-DCP2K_ENABLE_DBM_GPU=OFF` | 关闭稀疏张量库的 GPU 后端 |
| `-DCP2K_ENABLE_PW_GPU=OFF` | 关闭 FFT 及相关 gather/scatter 的 GPU 后端 |
| `-DCP2K_DBCSR_USE_CPU_ONLY=ON` | 关闭 DBCSR 的 GPU 后端 |

`[G层提示]` 注意**四个可独立关闭的 GPU 后端**：grid、DBM（稀疏张量）、PW（FFT）、DBCSR。排查 GPU 问题时可以逐个关掉定位。

### 4.3 HIP / ROCm（官方全文）

官方说明：

> The code for the HIP based grid backend was developed and tested on **Mi100** but should work out of the box on NVIDIA hardware as well.

| 选项 | 说明 |
|---|---|
| `-DCP2K_USE_ACCEL=HIP` | 通用启用 AMD GPU 支持 |
| `-DCP2K_ENABLE_GRID_GPU=OFF` | 关闭 grid 库的 GPU 后端 |
| `-DCP2K_ENABLE_DBM_GPU=OFF` | 关闭稀疏张量库的 GPU 后端 |
| `-DCP2K_ENABLE_PW_GPU=OFF` | 关闭 FFT 及相关操作的 GPU 后端 |
| `-DCP2K_DBCSR_USE_CPU_ONLY=ON` | 关闭 DBCSR 的 GPU 后端 |
| `-DCP2K_USE_UNIFIED_MEMORY=ON` | 启用统一内存支持（**实验性**，仅支持 **Mi250X 及以上**） |
| `-DCP2K_WITH_GPU=Mi50, Mi60, Mi100, Mi250, Mi300` | 架构取值 |

官方支持的架构（含 gfx 代号）：

| GPU | gfx 代号 |
|---|---|
| Mi300(A,X) | gfx1103 |
| Mi250 | gfx90a |
| Mi100 | gfx908 |
| Mi50 | gfx906 |

官方补充：

> The HIP backend for the grid library **supports NVIDIA hardware as well**. It uses the same code and can be used to **validate the backend** in case only NVIDIA hardware is available.

| 选项 | 说明 |
|---|---|
| `-DCP2K_WITH_GPU_PROFILING` | 开启 AMD ROC TX 与 Tracer 库；需要链接 `-lroctx64 -lroctracer64` |

官方参考：`https://rocm.docs.amd.com/en/latest/`

`[G层提示]` 原文有两处笔误照录：`-DCP2K_WITH_GPU==Mi50...`（双等号）与 "AMD ROC TX and Tracer libray"（拼写）。使用时应按 `-DCP2K_WITH_GPU=...` 单等号形式。

---

## 5. 特征求解器（官方）

官方 `technologies/eigensolvers/index.html` 全文：

> CP2K integrates multiple libraries for the solution of eigenvalue problems. **ScaLAPACK is a mandatory dependency when using MPI**, but GPU-accelerated libraries are optionally available.

页面仅列 `DLAF` 一个子页（`eigensolvers/dlaf.html`），**未采集**。

`[G层提示]` 结合 `08_errors_and_faq.md` §2.1.3：若 CP2K 用 ELPA 构建，它是默认对角化库；把 `PREFERRED_DIAG_LIBRARY` 设为 `SCALAPACK` 可能绕过某些 bug（官方指向 github issue #4484）。

---

## 6. 用 Spack 构建（官方）

### 6.1 基础流程（官方）

```bash
spack install cp2k
spack load cp2k
```

官方提示：

> If it is the first time you use Spack, you might have to run `spack compiler find` to setup the compilers.

`spack load cp2k` 会把相应目录加入 `PATH` 与 `MANPATH`。

### 6.2 变体（variants，官方）

```bash
spack install cp2k +libint +libxc
```

语法：`+VARIANT` 启用布尔变体，`~VARIANT` 禁用，`VARIANT=VALUE` 用于非布尔变体。

官方说明：

> More importantly, it takes care of building the **appropriate versions** of `libint` and `libxc` to work with CP2K (Fortran support, …).

### 6.3 版本（官方）

```bash
spack install cp2k@2023.2
spack install cp2k@2023.2 +libint +libxc +dlaf +sirius +cosma +spglib lmax=6 
```

官方把 `cp2k@2023.2 +libint +libxc +dlaf +sirius +cosma +spglib lmax=6` 称为一个 **spec**。

`[G层提示]` 注意 `lmax=6` 这种**非布尔变体**的写法（`VARIANT=VALUE`）。

### 6.4 CUDA 与 ROCm 支持（官方）

```bash
spack install cp2k +cuda cuda_arch=80
spack install cp2k +rocm amdgpu_target=gfx90a
```

官方提示：

> Spack is designed to support the installation of different versions of the same software, therefore there is no problem with running both commands above. However, `spack load cp2k` will **no longer work**, you will need to be a bit more specific: `spack load cp2k +cuda`

### 6.5 依赖管理（官方）

依赖用 `^` 指定：

```bash
spack install cp2k +cuda cuda_arch=80 ^dbcsr ~cuda
spack install cp2k ^intel-oneapi-mkl +cluster
```

官方说明：

> `+cluster` is a variant of the Intel oneAPI Spack package enabling cluster support (ScaLAPACK, BLACS, …).

### 6.6 开发者工作流（官方）

```bash
spack install --only=dependencies CP2K_SPEC
spack build-env CP2K_SPEC -- bash
```

官方说明：先用 Spack 装依赖，然后手动构建 CP2K。

### 6.7 Spack 与 Docker 容器（官方）

```bash
./tools/docker/spack_cache_start.sh
```

启动本地 **MinIO** 服务器作为 Spack 包缓存；`spack_cache_stop.sh` 停止。

```bash
podman build -f tools/docker/Dockerfile.test_spack -t cp2k_test_spack --shm-size=1G --network=host .
```

不用缓存时：

```bash
podman build -f tools/docker/Dockerfile.test_spack -t cp2k_test_spack --shm-size=1G --build-arg SPACK_CACHE="" .
```

---

## 7. 库的补充配置要求（官方 libraries 页，本文件补充）

> `09_build_libraries.md` 已列 30 个库。本节补录其中的**详细配置要求**（此前未展开的部分）。

### 7.1 DBCSR（必需）

- 独立库，维护于 `cp2k/dbcsr` 仓库
- 文档：`https://cp2k.github.io/dbcsr/develop/index.html`
- **MPI 配置必须一致**：CP2K 的 MPI 构建（`psmp`/`pdbg`）要求 DBCSR 用 `-DUSE_MPI=ON` 构建，若 `mpi_f08` 可用再加 `-DUSE_MPI_F08=ON`；串行构建（`ssmp`/`sdbg`）要求 DBCSR 用 `-DUSE_MPI=OFF`

### 7.2 LIBINT（HFX 的 ERI）

- 开：`-DCP2K_USE_LIBINT2=ON`
- 官方推荐用 toolchain 或 Spack 获取兼容构建
- CP2K 官方下载服务器提供**已配置好的 Libint 源码包**
- 手工构建必须：提供 ERI（`--enable-eri=1`）、用 Libint 默认排序、导出 CMake package、含 Fortran 接口（`libint_f.mod`）
- 官方警告：**更高的最大角动量**会增加编译时间，静态构建时还会显著增大二进制体积
- 官方警告：除非必要，**避免用大量调试信息编译 Libint**，会大幅增大库体积

### 7.3 LIBXS

- C 库，原为 LIBXSMM 的一部分
- **使用 CP2K 的 OpenCL 后端时必需**
- 开：`-DCP2K_USE_LIBXS=ON`

### 7.4 LIBXSTREAM

- GPU offload 的加速器后端库
- 配置 `-DCP2K_USE_ACCEL=OPENCL` 时**自动要求**，**没有单独的 `CP2K_USE_LIBXSTREAM` 选项**
- OpenCL 构建同时需要 LIBXS
- 手工构建需让 CMake 能发现 LIBXSTREAM 与 OpenCL 开发文件（如通过 `CMAKE_PREFIX_PATH`）

### 7.5 LIBXSMM

- 开：`-DCP2K_USE_LIBXSMM=ON`，**仅在 `-DCP2K_USE_LIBXS=ON` 时有效**
- LIBXS 与 LIBXSMM 的集成通过 `libxs_jit.F`（由 LIBXS 提供，由 DBCSR 与 CP2K 编译）
- 可与 CUDA 和 HIP 后端一起使用

### 7.6 LIBXC

- 最新版：`https://gitlab.com/libxc/libxc/-/releases`
- 开：`-DCP2K_USE_LIBXC=ON`
- 官方说明：CP2K 用**三阶导数但不使用四阶导数**，因此可用 `cmake .. -DDISABLE_KXC=OFF <其他 LIBXC 配置标志>`
- `DFT/XC/XC_FUNCTIONAL` 输入参考中同时列出 LIBXC 泛函与内建泛函

### 7.7 PLUMED

- 开：`-DCP2K_USE_PLUMED=ON`（需 PLUMED 2.x）
- 完整说明：`https://cp2k.org/howto:install_with_plumed`

### 7.8 spglib

- 开：`-DCP2K_USE_SPGLIB=ON`

### 7.9 SIRIUS

- **需要 MPI 构建**
- 开：`-DCP2K_USE_SIRIUS=ON`
- 依赖栈通常含 HDF5、SpFFT、SPLA、eigensolver 库；**推荐通过 Spack 构建**以启用全部特性
- **重要**：`PW_DFT` 的输入参考**由 SIRIUS 自己提供**，因此**未用 SIRIUS 构建的 CP2K 二进制导出的 `.xml` 中不含该段**
- 相关选项：`CP2K_USE_LIBVDWXC`、`CP2K_USE_SIRIUS_DFTD3`、`CP2K_USE_SIRIUS_DFTD4`、`CP2K_USE_SIRIUS_NLCG`、`CP2K_USE_SIRIUS_VCSQNM`

### 7.10 Torch（LibTorch）

- CP2K 用它做 **NequIP 和 MACE 接口**以及 **GauXC Skala 模型**
- 开：`-DCP2K_USE_LIBTORCH=ON`
- GPU 加速：选与可用后端/硬件兼容的 LibTorch 发行版（NVIDIA 用 CUDA，AMD 用 ROCm）
- 官方警告（Caution）：

> Note that currently pre-built libtorch bundle (up to **2.12.1**) is **not compatible** with CP2K's external oneMKL linking stack. If you build CP2K with MKL and want to enable libtorch, you may need to **build it by yourself**.

### 7.11 SPLA

- SIRIUS 的硬依赖，也可独立使用
- 提供 blas gemm 族的通用接口并 offload 到 GPU（**CUDA 与 ROCm 都支持**）
- **需要 MPI 构建**，开：`-DCP2K_USE_SPLA=ON`
- 要 offload 合格的 `dgemm`，另加 `-DCP2K_USE_SPLA_GEMM_OFFLOADING=ON` 并启用 CUDA 或 HIP
- SPLA 必须带 Fortran 接口与 GPU 后端构建
- **运行时**由 SPLA 决定单个操作是否适合 offload

### 7.12 DFTD4

- 提供 "Generally Applicable Atomic-Charge Dependent London Dispersion Correction"
- 官方要求：**用 CMake 构建的 dftd4 包，而非 Meson 构建的**（Meson 导出 CMake 配置的能力尚未进入发行版）
- 官方版本说明：**CP2K 2026.2 是最后一个提供到版本 3 的旧版 DFTD4 接口的发行版**；因开发中的兼容性问题，这些接口已在 PR #5641 中移除
- DFTD4 也是 TBLITE 包的一部分
- 开：`-DCP2K_USE_DFTD4=ON`

### 7.13 TREXIO

- 开：`-DCP2K_USE_TREXIO=ON`，**需要 HDF5**

### 7.14 LibFCI

- 为 CP2K 的 active-space 计算提供 full-CI 求解器
- 开：`-DCP2K_USE_LIBFCI=ON`

### 7.15 GREENX

- 为 RPA、GW、Laplace-MP2 等 GreenX 方法提供功能
- 开：`-DCP2K_USE_GREENX=ON`
- **也是 RTBSE 的 Padé 插值所必需**（见 `18_posthf_semiempirical_and_xray.md` §7.1）

### 7.16 HDF5

- 开：`-DCP2K_USE_HDF5=ON`
- **SIRIUS 与 TREXIO 的硬依赖**；也可单独用于 active space 模块的 QCSchema 文件读写

---

## 8. 参与 CP2K 开发（官方 onboarding）

### 8.1 官方态度（原文）

> CP2K invites the community to contribute to its development! Documentation improvements, bug fixes, performance enhancements, portability issues, new features, new methods … you are encouraged to contribute so that the community as a whole can benefit.
>
> CP2K is a large project, there is no way to study the full code, and start when that is done! **Start working on small patches first**, that are easy to code, to test and to integrate. Small patches are easier to review and thus will be more quickly merged to the Git master branch.

官方：`./CONTRIBUTING.md` 是指向本页的软链接。

### 8.2 准备补丁（官方步骤）

```bash
# 1. 在 GitHub 上 Fork https://github.com/cp2k/cp2k
# 2. 克隆你的 fork
git clone --recursive https://github.com/YOURNAME/cp2k.git
cd cp2k
# 3. 新建分支
git checkout -b my-new-feature
# 4. 改代码
# 5. 添加新文件与改动
git add ...
# 6. 提交
git commit
# 7. 首次推送（远程分支同名）
git push -u origin my-new-feature
# 8. 继续工作，重复 6、7
# 9. 后续推送
git push
# 10. 在 GitHub 界面创建 pull request
```

官方说明：

> Even as a member of the development team you will **not** be able to push directly to the `master` branch. This is by intention and we would like to ask you to send changes as Pull Requests instead.

提交需遵循 Contribution Guidelines（`https://github.com/cp2k/cp2k/wiki/Contribution-Guidelines`）。

### 8.3 更新与 rebase（官方）

```bash
# 一次性告知本地仓库远程地址
git remote add upstream https://github.com/cp2k/cp2k.git
# 确保在正确的分支
git checkout master
# 把当前分支 rebase 到 cp2k/cp2k 的 master 之上
git pull --rebase upstream master

# 把带补丁的分支更新到新的 master
git checkout my-new-feature
git rebase master
# 冲突时解决；迷路了可以中止
git rebase --abort
# 对已推送过的分支 rebase 后必须强推
git push --force
```

### 8.4 提交补丁前的检查清单（官方，重要）

官方原文："Following these guidelines will avoid common mistakes and make it easier to integrate patches. It usually takes **less than one hour**."

| 步骤 | 内容 |
|---|---|
| 1 | `./make_pretty.sh` 自动格式化代码（变量） |
| 2 | 编译代码 |
| 3 | 准备并添加适合回归测试的测试用例（能快速跑过所有新代码路径） |
| 4 | 手工运行这些测试用例；**用 bounds checking 与 valgrind** 检查未定义变量或内存泄漏 |
| 5 | 跑完整回归测试套件，确保新用例正确且不影响其它测试 |

关注要点（官方）：

- 新文件（含测试）是否可见？按需 `git add`
- 新测试目录是否注册在 `tests/TEST_DIRS`？
- 是否只改了预期要改的文件和代码？按需 `git revert`
- 代码中是否残留 stray write 语句或调试信息？
- 所有新代码是否充分文档化与解释？
- 输入关键字是否描述清楚？
- 是否把恰当的引用加进了 bibliography？

若有任一步骤需要改代码，回到第一步。

### 8.5 PR 与 CI（官方）

- 在 `https://github.com/YOURNAME/cp2k` 创建 PR
- 查看 PR 状态：`https://github.com/cp2k/cp2k/pulls`
- 官方用 `git rebase` 保持 **Git history 线性**，最终 PR 中**不能有 merge commits**
- PR 触发 CP2K CI 检查约定、兼容性与正确性
  - 成功 → 由 CP2K 管理员合并
  - 失败 → 看 CI 日志、在分支上修复、再次 commit/push。CI 会自动重跑（**无需关闭 PR**）
- 管理员可能启动额外测试
- 若 dashboard 上任何测试因你的 PR 而失败，会收到通知；提交新 PR 修复

### 8.6 加入团队（官方，权限分级）

首个 PR 被接受并合并后，会收到加入 `cp2k-developers` 团队的邀请，获得 **triage** 访问权限：

- 对 issue 与 PR 应用或取消 assignee、标签、类型、里程碑
- 关闭或重开他人的 issue 与 PR，包括把 issue 转为 discussion 并锁定原 issue，但**不能**合并 PR 到 master
- 在 PR 中评论 `/cp2kci {item}` 触发 CP2K-CI 测试

按个案，愿意承担更多责任的活跃开发者可申请加入 `cp2k-core-developers` 团队，获得 **write** 访问权限：

- 合并 PR 到 master
- 批准 PR，或请求/应用对 PR 的改动
- 编辑、隐藏或删除他人的 issue 与 PR 评论
- 重命名 issue、置顶 issue
- 创建、编辑或删除标签与里程碑
- 为代码某部分定义或成为 code owner（相关 PR 会收到通知并自动请求评审，需明确批准才能合并）

协助入口：`cp2k-admins` 团队任一成员。

---

## 9. 官方故障排查页（补充到 08）

> `08_errors_and_faq.md` 已完整覆盖 `getting-started/troubleshooting.html`。本节补录两处此前未单列的内容。

### 9.1 输入/输出的基础回顾（官方）

三种标准流：`stdin`（读数据，fd 0）、`stdout`（写数据，fd 1）、`stderr`（写错误，fd 2）。

三种典型启动命令：

```bash
# 1. -o 指定 stdout 文件，错误信息到屏幕
mpirun -np 2 -x OMP_NUM_THREADS=1 cp2k.psmp -i project.inp -o project.out

# 2. 1> 重定向 stdout，2>&1 让 stderr 也进同一文件
mpirun -np 2 -x OMP_NUM_THREADS=1 cp2k.psmp -i project.inp 1>project.out 2>&1

# 3. 管道给 tee，同时打印到屏幕与文件
mpirun -np 2 -x OMP_NUM_THREADS=1 cp2k.psmp -i project.inp | tee project.out
```

队列系统：Slurm 用 `--output=<filename>` 与 `--error=<filename>` 给 `srun`。

`FILENAME` 的默认值：官方手册写为字符串 `__STD_OUT__`，即"屏幕或标准记录器"。

### 9.2 多副本任务的日志陷阱（官方，重要）

官方原文：

> Note that certain types of tasks like **vibrational analysis, nudged elastic band, swarm, farming**, …, have ***multiple*** output logs depending on the replica and parallelization in use; sometimes the single primary log (specified by `-o`) may **not be as informative or primitive** as the secondary logs (automatically generated per replica under the working directory) and it is necessary to locate the exact issue(s) from the latter. This applies to warnings and errors too, which in addition are typically issued on the **first MPI rank of each replica**.

`[G层提示]` 振动分析、NEB、swarm、farming 出错时，**别只盯主日志**，要去工作目录找每个副本的次级日志，且优先看每个副本的 rank 0。

---

## 10. 交叉索引

| 本文件主题 | 关联文件 | 关系 |
|---|---|---|
| 性能基准 / NUMA 线程绑定 | A 层 `decide.md` | 线程数不超过单 NUMA 域核数 |
| 线性标度 DFT | A 层 `decide.md`（OT vs 对角化） | 线性标度是第三条路，避免 OT 的三次标度正交化 |
| HFX 与 ADMM | `02_dft_methods.md`、`18_posthf_semiempirical_and_xray.md` | LiH-HFX 基准、ADMM 加速 |
| GPU 后端 | `09_build_libraries.md` §5 | 本文件 §4 补全逐条选项 |
| 库配置细节 | `09_build_libraries.md` §3 | 本文件 §7 补全配置要求 |
| Spack 构建 | `09_build_libraries.md` | 本文件 §6 完整流程 |
| 特征求解器 / ELPA 卡死 | `08_errors_and_faq.md` §2.1.3 | `PREFERRED_DIAG_LIBRARY SCALAPACK` 绕过 bug |
| 多副本日志 | `08_errors_and_faq.md` §1.4 | 本文件 §9.2 补充官方原文 |
| 后 HF 性能（quintic / quartic） | `18_posthf_semiempirical_and_xray.md` | MP2 五标度、RPA 四标度/亚三次 |
| 版本与 changelog | `11_version_changelog.md` | 版本策略、DFTD4 接口移除等 |
| 引用规范 | `10_features_resources.md` | 参与开发时的 bibliography 要求 |

---

## 11. 本文件登记的新缺口（诚实标注）

| 缺口 | 说明 |
|---|---|
| DLAF 页面 | `technologies/eigensolvers/dlaf.html` 未采集 |
| benchmark 最新数据 | 官方页最后更新 2020-11-10，2019 年后无新机器数据 |
| dashboard 的 Test Coverage / Discontinued Tests / Supported compilers 子页 | 未单独采集 |
| `tools/benchmark_plots/` 脚本用法 | 官方仅提及，未展开 |
| 各库的版本兼容矩阵 | 官方分散在各库页面，未集中给出 |
