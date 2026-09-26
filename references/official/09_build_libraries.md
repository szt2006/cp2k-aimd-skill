# 09 · 安装、外部库与加速器

> **来源**：
> - <https://manual.cp2k.org/trunk/getting-started/installation.html>（安装总览）
> - <https://manual.cp2k.org/trunk/technologies/libraries.html>（外部库，30 个）
> - <https://manual.cp2k.org/trunk/technologies/accelerators/index.html> + `cuda.html` + `hip.html`
> - <https://manual.cp2k.org/trunk/technologies/eigensolvers/index.html>
> - <https://www.cp2k.org/howto>（安装类 HowTo 清单）
> - 相关 FAQ 3 条（CPU 扩展、libsmm、toolchain 非零退出码）
> **抓取日期**：2026-09-08
> **本文件定位**：G 层（官方权威层）。只写官方说了什么。本机实测的编译经验见 F 层 `playbook.md`。

---

## 1. 安装前必须想清楚的 6 个问题（官方 checklist）

官方原文把安装前的考量列成 6 项，并明确标注哪些是"**（assumed）**"（即官方文档默认的前提）。

### 1.1 目标机器是什么操作系统？

| 系统 | 官方描述 |
|---|---|
| **Linux**（assumed） | the workhorse for high-performance computing, a majority of compiling and regression tests are hosted in some Linux distribution |
| **Darwin**（macOS） | MacOS on Apple Silicon M1 is also regularly tested, and installation methods based on **Spack or Homebrew** are recommended |
| **Windows** | for lightweight beginner experiments, the **Windows Subsystem for Linux (WSL)** or any other virtual machine platforms can provide a Linux environment on Windows |

> **重要**：官方对 Windows 的定位是"**lightweight beginner experiments**"，且推荐 **WSL 或虚拟机**提供 Linux 环境。**没有原生 Windows 构建的官方路径。**

### 1.2 有没有 root / sudo 权限？

| 情况 | 官方说明 |
|---|---|
| **有** | proceed with caution, especially if the privilege means that actions may disrupt the environment for other users and softwares |
| **没有**（assumed） | it is **totally fine** to install as a normal user in a convenient directory with read and write permission as well as sufficient disk space |

### 1.3 有没有网络连接？

| 情况 | 官方说明 |
|---|---|
| **有**（assumed） | new packages will be downloaded automatically to prepare dependencies; however, **once ready, running CP2K itself does not require internet connection** |
| **没有** | 离线安装：在别处下载全部包 → 传到目标目录 → **校验文件完整性**（如 `sha256sum`） |

### 1.4 有没有 module 系统？

官方解释：Module 系统（如 LMod、Environment Module）可加载/卸载模块以控制运行时环境变量与路径而不冲突；用 `module avail`、`module show` 等命令查看。

| 情况 | 官方说明 |
|---|---|
| **有** | 推荐事先检查可用性与兼容性，并激活相关模块用于安装与运行；**避免同一包多份副本**，且能利用针对该机器定制的优化，**特别是硬件相关的 libfabric 与 MPI 配置** |
| **没有**（assumed） | 用默认配置从头准备 |

### 1.5 机器有没有不同类型的节点？

官方举例：login node（低负载任务如编译）vs compute node（重负载计算）。关键是**程序环境与硬件规格是否一致**。

| 情况 | 官方说明 |
|---|---|
| **有** | 异构计算、不同 CPU 架构与指令集需**特别小心优化目标**；一个环境中生效的环境变量与路径，可能需要在另一个环境中通过提交脚本显式激活 |
| **没有**（assumed） | 针对**本机 CPU** 优化是合适的，环境设置更简单 |

### 1.6 有没有工作站级 GPU？

官方定义：

> A "workstation GPU" or "professional GPU" focuses on the **double-precision float-point arithmetic** and is suitable for scientific computing, in contrast to a "gaming GPU" or "consumer GPU" with less optimized double-precision performance.

| 情况 | 官方说明 |
|---|---|
| **有** | 部分 eigensolver、accelerator 与其他库已就绪或正在开发 GPU 加速，用于 CP2K 量子化学计算中的矩阵运算；**注意 CP2K 的要求不同于基于分子力学的其它 MD 代码** |
| **没有**（assumed） | 纯 CPU 构建总是可行的，且**在没有 GPU 时不必然更慢** |

---

## 2. 官方安装说明入口

官方 installation 页的 `Instructions` 节**只有链接**（无正文），软链接 `./INSTALL.md` 指向该页。

| 资源 | 链接 |
|---|---|
| 如何编译 CP2K | <https://github.com/cp2k/cp2k/blob/master/INSTALL.md> |
| CP2K 官方手册安装页 | <https://manual.cp2k.org/trunk/getting-started/installation.html> |

### 2.1 官网安装类 HowTo 清单（完整）

| HowTo | 链接 |
|---|---|
| How to Compile CP2K | `github.com/cp2k/cp2k/blob/master/INSTALL.md` |
| How to Compile CP2K with CUDA Support | `cp2k.org/howto:compile_with_cuda` |
| How to Compile and Install CP2K with PLUMED | `cp2k.org/howto:install_with_plumed` |
| How to Compile and Install CP2K on Windows with Cygwin | `cp2k.org/howto:compile_on_windows_with_cygwin` |
| How to Compile CP2K on Windows | `cp2k.org/howto:compile_on_windows` |
| How to Compile CP2K on macOS | `cp2k.org/howto:compile_on_macos` |
| How to Compile CP2K on CRAY XC40/50 at CSCS | `cp2k.org/howto:compile_on_cray_cscs` |
| How to build and run CP2K containers | `cp2k.org/howto:build_and_run_cp2k_containers` |

---

## 3. 外部库完整清单（30 个，官方 `libraries.html`）

### 3.1 必需库（3 个）

#### ① BLAS and LAPACK（required, base functionality）

官方原文要点：

> Using vendor-provided libraries can make a **very significant difference (up to 100%, e.g., ACML, MKL, ESSL)**, **not all optimized libraries are bug free**. Use the latest versions available, use the interfaces matching your compiler, and download all patches!

**可用实现**：

| 来源 | 链接 |
|---|---|
| Netlib BLAS | <http://www.netlib.org/blas/> |
| Netlib LAPACK | <http://www.netlib.org/lapack/> |
| Netlib LAPACK-dev | <http://www.netlib.org/lapack-dev/> |
| OpenBLAS | <http://www.openblas.net> |
| ATLAS | <http://math-atlas.sourceforge.net> |
| GotoBLAS2 | <https://www.tacc.utexas.edu/research-development/tacc-software/gotoblas2> |

**线程安全要求（重要）**：

> Please note that the BLAS/LAPACK implementation used by CP2K needs to be **thread-safe (OpenMP)**. Examples are the sequential or thread variant of the Intel MKL, the Cray libsci, the OpenBLAS OpenMP variant and the reference BLAS/LAPACK packages.

| 可用（线程安全） | 说明 |
|---|---|
| Intel MKL 的 sequential 或 thread 变体 | ✅ |
| Cray libsci | ✅ |
| OpenBLAS OpenMP 变体 | ✅ |
| 参考版 BLAS/LAPACK | ✅ |

**CMake 自动检测**：

> Usually the CMake step of CP2K will auto-detect the type of BLAS and SCALAPACK and then use the right configuration to ensure the code is thread-safe; however, **if detection is ambiguous**, `-DCP2K_BLAS_VENDOR=MKL` and `-DCP2K_SCALAPACK_VENDOR=MKL` can be used for a oneMKL installation.

**macOS**：BLAS/LAPACK 可由 OpenBLAS 或 Apple Accelerate framework 提供。

#### ② DBCSR（required, block-sparse matrix operations）

> DBCSR is a standalone library for block-sparse matrix operations. It is maintained at the cp2k/dbcsr repository.

| 资源 | 链接 |
|---|---|
| 仓库 | <https://github.com/cp2k/dbcsr> |
| 官网 | <https://www.cp2k.org/dbcsr> |
| 文档 | <https://cp2k.github.io/dbcsr/develop/index.html> |

**官方硬约束（MPI 配置必须一致）**：

> The MPI configuration should be **consistent** between CP2K and DBCSR. For a MPI build (`psmp`/`pdbg`) of CP2K, DBCSR must also have been built with MPI support using the CMake flag `-DUSE_MPI=ON`, and `-DUSE_MPI_F08=ON` if `mpi_f08` is available. Likewise, a serial build (`ssmp`/`sdbg`) of CP2K must use a DBCSR configured with `-DUSE_MPI=OFF`.

| CP2K 构建 | DBCSR 配置 |
|---|---|
| `psmp` / `pdbg`（MPI） | `-DUSE_MPI=ON`（若有 `mpi_f08` 则加 `-DUSE_MPI_F08=ON`） |
| `ssmp` / `sdbg`（串行） | `-DUSE_MPI=OFF` |

> CP2K 通过 toolchain 或 Spack 构建准备 DBCSR，CMake 配置时会自动找到。

#### ③ MPI and ScaLAPACK（required for MPI parallel builds）

> MPI (version 3 or later) and SCALAPACK are needed for parallel code.

**Warning（官方）**：

> Note that the **MPI installation must match the used Fortran compiler**.

**免费实现**：

| 实现 | 链接 |
|---|---|
| MPICH | <https://www.mpich.org/> |
| OpenMPI | <http://www.open-mpi.org/> |

**Hint（官方）**：

> When building MPICH with GCC 10, the `-fallow-argument-mismatch` compiler flag may be needed.

**Note（Open MPI 进程绑定，重要）**：

> Open MPI applies process binding by default. This can affect hybrid MPI+OpenMP runs because the launcher **does not infer the number of OpenMP threads required by each MPI rank**. A binding that is appropriate for an MPI-only calculation can therefore leave each rank with too few CPUs for its OpenMP threads.

**官方处置**：

| 动作 | 命令 |
|---|---|
| 查看映射与绑定 | `mpirun --display map,bind ...` |
| 禁用绑定 | `--bind-to none` |
| 显式分配每 rank 核数 | `--map-by slot:PE=<OMP_NUM_THREADS> --bind-to core` |

**版本要求**：

| 要求 | 官方措辞 |
|---|---|
| MPI 版本 | **MPI version 3 或更高**；不支持 MPI 2.0 等旧版 |
| `mpi_f08` 模块 | 可用时传 `-DCP2K_USE_MPI_F08=ON` |
| **从 2027.1 起** | CP2K 要求 MPI 实现提供 **`MPI_THREAD_MULTIPLE`** |

**2027.1 的 `MPI_THREAD_MULTIPLE` 细节（官方原文）**：

> The standalone executables request this level when initializing MPI and stop if it is unavailable. When CP2K is used as a library in an application that initializes MPI externally, the application must call `MPI_Init_thread` requesting `MPI_THREAD_MULTIPLE`; initialization through `MPI_Init` or with a lower thread-support level is insufficient.

**ScaLAPACK**：见 <http://www.netlib.org/scalapack/>；可作为 AOCL（AMD）或 oneMKL（Intel）的一部分，官方推荐在对应机器上使用。

### 3.2 性能关键库（强烈推荐）

#### ④ FFTW（improved performance of FFTs）

> FFTW can be used to improve FFT speed on a wide range of architectures. **It is strongly recommended to install and use FFTW3.**

| 项 | 说明 |
|---|---|
| 版本 | FFTW 3.X，CMake 传 `-DCP2K_USE_FFTW3=ON` |
| 下载 | <http://www.fftw.org> |
| MKL 自带 FFTW | 若有 MKL 但仍想用独立 FFTW3，传 `-DCP2K_USE_FFTW3_WITH_MKL=ON` |

**Warning（官方）**：

> Note that **FFTW must know the Fortran compiler you will use in order to install properly** (e.g., `export F77=gfortran` before configure if you intend to use gfortran).

**OpenMP 接口（重要）**：

> Since CP2K is OpenMP parallelized, CP2K enables the **FFTW3 OpenMP interface by default** (`-DCP2K_ENABLE_FFTW3_OPENMP_SUPPORT=ON`); the FFTW installation must therefore provide `libfftw3_omp`. The alternative threads interface can be selected with `-DCP2K_ENABLE_FFTW3_THREADS_SUPPORT=ON`, which requires `libfftw3_threads`.

| 接口 | CMake 默认 | 需要的库 |
|---|---|---|
| OpenMP 接口 | **默认 ON** | `libfftw3_omp` |
| threads 接口 | 可选 `-DCP2K_ENABLE_FFTW3_THREADS_SUPPORT=ON` | `libfftw3_threads` |

**Important（官方）**：

> Support for FFTW is required for some features, especially systems with **very large block sizes/grid sizes**. **A future release of CP2K may make FFTW a hard dependency.** Please consider CP2K to be compiled with support for FFTW.

#### ⑤ LIBINT（ERI calculation for HFX）

> Libint2 provides the electron-repulsion integrals required for **Hartree–Fock exchange** and related methods.

| 项 | 说明 |
|---|---|
| CMake | `-DCP2K_USE_LIBINT2=ON` |
| 推荐获取方式 | CP2K toolchain 或 Spack |
| 手动构建要求 | 必须提供 ERI（`--enable-eri=1`）、采用 Libint 默认排序、导出 CMake package、包含 Fortran 接口（`libint_f.mod`） |
| 官方警告 | 更高的最大角动量会增加 CP2K 编译时间，**静态构建尤其增大二进制体积**；避免用大量调试信息编译 Libint |

### 3.3 矩阵运算与 GPU 后端库

#### ⑥ LIBXS（improved performance for matrix multiplication）

> LIBXS is a C library for memory operations, numerics, synchronization, and more.

| 项 | 说明 |
|---|---|
| 文档 | <https://libxs.readthedocs.io/> |
| 源码 | <https://github.com/hfp/libxs> |
| CMake | `-DCP2K_USE_LIBXS=ON` |
| **硬约束** | **使用 CP2K 的 OpenCL 后端时必需** |

#### ⑦ LIBXSTREAM（OpenCL offload runtime）

> LIBXSTREAM provides the stream and memory-management layer used by CP2K's OpenCL offload backend.

| 项 | 说明 |
|---|---|
| 文档 | <https://libxstream.readthedocs.io/> |
| 源码 | <https://github.com/hfp/libxstream> |
| CMake | **无独立 `CP2K_USE_LIBXSTREAM` 选项**；配置 OpenCL 加速（`-DCP2K_USE_ACCEL=OPENCL`）时**自动需要** |
| 附加要求 | OpenCL 构建也需 LIBXS；手动构建时需让 LIBXSTREAM 与 OpenCL 开发文件对 CMake 可见（如 `CMAKE_PREFIX_PATH`） |

#### ⑧ LIBXSMM（JIT-kernel provider of libXS）

> LIBXSMM is a library for specialized dense and sparse matrix operations that provides just-in-time kernels (JIT-kernels) for LibXS.

| 项 | 说明 |
|---|---|
| 文档 | <https://libxsmm.readthedocs.io/> |
| 源码 | <https://github.com/libxsmm/libxsmm/> |
| CMake | `-DCP2K_USE_LIBXSMM=ON`，**仅在同时传 `-DCP2K_USE_LIBXS=ON` 时有效** |
| 集成方式 | 通过 LIBXS 提供、由 DBCSR 与 CP2K 编译的 `libxs_jit.F` |
| 后端 | 可用于 CUDA 与 HIP 两种后端 |

#### ⑨ COSMA（Distributed Communication-Optimal Matrix-Matrix Multiplication Algorithm）

> COSMA is an alternative for the `pdgemm` routine included in ScaLAPACK. The library supports both CPU and GPUs.

| 项 | 说明 |
|---|---|
| CMake | `-DCP2K_USE_COSMA=ON` |
| 源码 | <https://github.com/eth-cscs/COSMA> |

#### ⑩ SPLA（Matrix-matrix multiplication offloading on GPU）

> The SPLA library is a **hard dependency of SIRIUS** but can also be used as a standalone library.

| 项 | 说明 |
|---|---|
| CMake | `-DCP2K_USE_SPLA=ON` |
| 额外 offload | `-DCP2K_USE_SPLA_GEMM_OFFLOADING=ON` + 启用 CUDA 或 HIP |
| 要求 | **需要 MPI 构建**；SPLA 必须用其 Fortran 接口和 GPU 后端构建 |
| 后端 | CUDA 与 ROCm（HIP） |
| 运行时行为 | SPLA 在运行时决定单个操作是否适合 offload |

### 3.4 泛函与 XC 相关库

#### ⑪ LIBXC（wider choice of xc functionals）

| 项 | 说明 |
|---|---|
| 文档 | <https://libxc.gitlab.io> |
| 下载 | <https://gitlab.com/libxc/libxc/-/releases> |
| CMake | `-DCP2K_USE_LIBXC=ON` |
| **重要配置** | CP2K 用三阶导数、**不用四阶导数**，所以 LIBXC 可配置为 `cmake .. -DDISABLE_KXC=OFF <other LIBXC configuration flags>` |
| 泛函清单 | 见 CP2K input reference 的 `DFT/XC/XC_FUNCTIONAL` 段（LIBXC 泛函与内置泛函一并列出） |

#### ⑫ GauXC（xc integration library）

> GauXC can be used to evaluate selected exchange-correlation functionals through an external integrator.

| 项 | 说明 |
|---|---|
| CMake | `-DCP2K_USE_GAUXC=ON` |
| 依赖 | Skala 支持需要 Libtorch |
| MPI 要求 | **MPI 版 CP2K 需要带 MPI 支持的 GauXC 安装** |
| BLAS 兼容性 | TorchScript 模型的 libtorch 必须与 CP2K 的 BLAS 和 OpenMP 运行时兼容；预构建 libtorch 通常自带 oneMKL；**CP2K 的 LP64 OpenBLAS 构建**为解决冲突的 grouped SGEMM/DGEMM 符号提供兼容路径，其他混合 BLAS 接口需要一致构建的数值栈 |
| 文档 | `manual.cp2k.org/trunk/methods/dft/gauxc.html` |

#### ⑬ libGint（GPU 上的 HFX）

> libGint — A library for the calculation of the Hartree Fock exchange on GPUs

**输入文件改动（官方原文）**：

```
&FORCE_EVAL
  &DFT
    &XC
      &HF
        HFX_LIBRARY libGint
      &END HF
      &MEMORY
        MAX_MEMORY X
      &END MEMORY
    &END XC
  &END DFT
&END FORCE_EVAL
```

| 项 | 说明 |
|---|---|
| CMake | `-DCP2K_USE_LIBGINT=ON` |

### 3.5 低标度与后 HF 方法库

#### ⑭ PEXSI（low scaling SCF method）

> The Pole EXpansion and Selected Inversion (PEXSI) method requires an MPI build and a compatible PEXSI CMake package. PEXSI itself depends on a sparse-direct-solver and graph-partitioning stack, typically **SuperLU_DIST together with ParMETIS or PT-Scotch**.

| 项 | 说明 |
|---|---|
| CMake | `-DCP2K_USE_PEXSI=ON` |
| 推荐获取 | **Spack 是最方便的受支持途径** |
| **官方限制** | **不支持通过 toolchain 安装 PEXSI** |

#### ⑮ GREENX（GreenX methods such as RPA, GW, and Laplace-MP2）

| 项 | 说明 |
|---|---|
| CMake | `-DCP2K_USE_GREENX=ON` |
| 源码 | <https://github.com/nomad-coe/greenX> |
| 文档 | <https://nomad-coe.github.io/greenX/> |

#### ⑯ LibFCI（full-CI active-space solver）

> LibFCI is an external library providing a full-CI solver for CP2K active-space calculations.

| 项 | 说明 |
|---|---|
| CMake | `-DCP2K_USE_LIBFCI=ON` |
| 源码 | <https://github.com/DCM-Uni-Paderborn/libfci> |

### 3.6 色散校正与半经验方法

#### ⑰ DFTD4（dispersion correction）

> DFTD4 provides the Generally Applicable Atomic-Charge Dependent London Dispersion Correction.

| 项 | 说明 |
|---|---|
| 官网 | <https://www.chemie.uni-bonn.de/grimme/de/software/dft-d4> |
| 源码 | <https://github.com/dftd4/dftd4> |
| CMake | `-DCP2K_USE_DFTD4=ON` |
| **官方要求** | **请用 CMake 构建的 dftd4 包**，而非 Meson 构建的（Meson 导出 CMake 配置的能力尚未包含在任何发布版本中） |
| **版本变更** | **CP2K 2026.2 将是最后一个保留对 DFTD4 legacy 版本（低至第 3 版）接口的版本**；这些接口已在 PR #5641 中移除 |
| 附注 | DFTD4 也包含在 TBLITE 包中 |

> **这是 G 层记录"色散校正"官方信息的权威来源之一**——因为手册 `methods/dft/vdw.html` 返回 404（见 `02_dft_methods.md` §11）。

#### ⑱ TBLITE（semiempirical method）

> TBLITE is a lightweight tight-binding framework that provides the **GFN2-xTB** method.

| 项 | 说明 |
|---|---|
| 源码 | <https://github.com/tblite/tblite> |
| 文档 | <https://tblite.readthedocs.io> |
| CMake | `-DCP2K_USE_TBLITE=ON` |
| **官方要求** | **始终使用 CMake 构建的 tblite 包**，而非 Meson 构建的 |
| **依赖简化** | 从源码 CMake 构建 tblite 也会安装 DFT-D4 与 s-dftd3，因此**启用 tblite 时无需单独安装 DFTD4**；s-dftd3 还为额外的 XC 泛函提供参数 |

### 3.7 机器学习势库

#### ⑲ Torch（PyTorch C++ library）

> LibTorch is the C++ distribution of PyTorch. CP2K uses it for the **NequIP and MACE interfaces** and for GauXC Skala models.

| 项 | 说明 |
|---|---|
| 下载 | PyTorch 安装页 |
| CMake | `-DCP2K_USE_LIBTORCH=ON` |
| GPU 加速 | 选择与可用后端和硬件兼容的 LibTorch 发行版（NVIDIA GPU 用 CUDA，支持的 AMD GPU 用 ROCm） |

**Caution（官方，重要）**：

> Note that currently **pre-built libtorch bundle (up to 2.12.1) is not compatible with CP2K's external oneMKL linking stack**. If you build CP2K with MKL and want to enable libtorch, you may need to build it by yourself.

#### ⑳ DeePMD-kit（wider range of interaction potentials）

> DeePMD-kit provides Deep Potential models.

| 项 | 说明 |
|---|---|
| CMake | `-DCP2K_USE_DEEPMD=ON` |
| C 接口下载 | <https://docs.deepmodeling.com/projects/deepmd/en/master/install/install-from-c-library.html> |
| 源码 | <https://github.com/deepmodeling/deepmd-kit> |

#### ㉑ ACE（atomic cluster expansion ML potentials）

> Atomic cluster expansion potentials from ML-PACE for accurate and transferable interatomic potentials.

| 项 | 说明 |
|---|---|
| CMake | `-DCP2K_USE_ACE=ON` |
| 源码 | <https://github.com/ICAMS/lammps-user-pace> |
| **构建特点** | 用 cmake/make 编译，**没有 install 步骤**；只需确保 CP2K 构建过程链接三个库（`libpace`、`libyaml-cpp-pace`、`libcnpy`），并需要访问 `ML-PACE/ace`、`ML-PACE/ace-evaluator` 与 `yaml-cpp/include` |

### 3.8 增强采样与多尺度

#### ㉒ PLUMED（enables various enhanced sampling methods）

> PLUMED is a plugin library for enhanced sampling and free energy algorithms in molecular dynamics.

| 项 | 说明 |
|---|---|
| 官网 | <https://www.plumed.org/> |
| 源码 | <https://github.com/plumed/plumed2> |
| CMake | `-DCP2K_USE_PLUMED=ON`（PLUMED 2.x） |
| 完整说明 | <https://cp2k.org/howto:install_with_plumed> |

#### ㉓ MIMIC（multiscale simulations）

> MiMiC — Multiscale simulation framework

| 项 | 说明 |
|---|---|
| 接口库 | MCL，<https://gitlab.com/mimic-project/> |
| 官网 | <https://mimic-project.org> |
| CMake | `-DCP2K_USE_MIMIC=ON` |

### 3.9 平面波与电子输运

#### ㉔ SIRIUS（plane wave calculations）

> SIRIUS is a domain specific library for electronic structure calculations with plane wave method.

| 项 | 说明 |
|---|---|
| 源码 | <https://github.com/electronic-structure/SIRIUS> |
| CMake | `-DCP2K_USE_SIRIUS=ON`，**需要 MPI 构建** |
| 依赖栈 | 通常含 HDF5、SpFFT、SPLA、eigensolver 库；**推荐通过 Spack 构建**以启用全部特性 |
| **重要行为** | `PW_DFT` 输入参考**由 SIRIUS 自身生成**，因此**未启用 SIRIUS 编译的 CP2K 二进制所 dump 的 `.xml` 中不会有该部分** |
| 相关子选项 | `-DCP2K_USE_LIBVDWXC=ON`（SIRIUS 构建提供 libvdwxc 支持时）<br>`-DCP2K_USE_SIRIUS_DFTD3=ON`（SIRIUS 用 DFT-D3 构建时）<br>`-DCP2K_USE_SIRIUS_DFTD4=ON`（SIRIUS 用 DFT-D4 构建时）<br>`-DCP2K_USE_SIRIUS_NLCG=ON`（SIRIUS 用 NLCG 构建时）<br>`-DCP2K_USE_SIRIUS_VCSQNM=ON`（SIRIUS 用变胞弛豫支持构建时） |
| 构建选项文档 | <https://electronic-structure.github.io/SIRIUS-doc/> |

#### ㉕ libsmeagol（electron transport calculation with current-induced forces）

> libsmeagol is an external library to compute electron transport properties using Non-Equilibrium Green Functions (NEGF) method.

| 项 | 说明 |
|---|---|
| 源码 | <https://github.com/StefanoSanvitoGroup/libsmeagol> |
| CMake | `-DCP2K_USE_LIBSMEAGOL=ON` |
| **限制** | 依赖 MPI 库，**只能与 MPI 并行 CP2K 二进制链接** |
| 安装产物 | 创建目录 `$(LIBSMEAGOL_DIR)/lib` 与 `$(LIBGRPP_DIR)/obj` |

### 3.10 对称性、格式与输出

#### ㉖ spglib（crystal symmetries tools）

| 项 | 说明 |
|---|---|
| 文档 | <https://spglib.readthedocs.io/> |
| 源码 | <https://github.com/spglib/spglib> |
| CMake | `-DCP2K_USE_SPGLIB=ON` |

#### ㉗ TREXIO（unified computational chemistry format）

| 项 | 说明 |
|---|---|
| 源码 | <https://github.com/trex-coe/trexio> |
| 文档 | <https://trex-coe.github.io/trexio/index.html> |
| CMake | `-DCP2K_USE_TREXIO=ON` |
| 依赖 | **需要 HDF5** |

#### ㉘ openPMD（structured output）

| 项 | 说明 |
|---|---|
| 源码 | <https://github.com/openPMD/openPMD-api/> |
| 文档 | <https://openpmd-api.readthedocs.io> |
| CMake | `-DCP2K_USE_OPENPMD=ON` |
| **官方限制** | **CMake 是启用 openPMD 的唯一受支持方式**；在 DFLAGS 中用 `-D__OPENPMD` **可能可用也可能不可用** |
| 版本要求 | openPMD-api **≥ 0.16.1**（由 `OPENPMDAPI_VERSION_GE` 判定） |
| MPI 要求 | openPMD-api **必须针对 MPI 构建**（由 `openPMD_HAVE_MPI` 判定） |

#### ㉙ HDF5

| 项 | 说明 |
|---|---|
| CMake | `-DCP2K_USE_HDF5=ON` |
| 用途 | **SIRIUS 与 TREXIO 的硬依赖**；也可单独用于 active space 模块中 QCSchema 文件的读写 |

#### ㉚ LibVori（Voronoi Integration for Electrostatic Properties from Electron Density）

> LibVori is a library which enables the calculation of electrostatic properties (charge, dipole vector, quadrupole tensor, etc.) via integration of the total electron density in the Voronoi cell of each atom.

| 项 | 说明 |
|---|---|
| 官网 | <https://brehm-research.de/libvori> |
| CMake | `-DCP2K_USE_VORI=ON` |
| 附加功能 | 支持 **BQB 格式**压缩轨迹，见 <https://brehm-research.de/bqb>；用 `bqbtool` 检查 BQB 文件 |

---

## 4. CMake 标志速查表（官方全集）

| 库 / 组件 | 必需性 | CMake 标志 |
|---|---|---|
| BLAS / LAPACK | **必需**（基础功能） | `-DCP2K_BLAS_VENDOR=MKL`、`-DCP2K_SCALAPACK_VENDOR=MKL`（检测不明确时） |
| DBCSR | **必需**（硬依赖） | `-DUSE_MPI=ON`、`-DUSE_MPI_F08=ON`、`-DUSE_MPI=OFF` |
| MPI / ScaLAPACK | **MPI 并行构建必需** | `-DCP2K_USE_MPI_F08=ON` |
| FFTW | **强烈推荐** | `-DCP2K_USE_FFTW3=ON`、`-DCP2K_USE_FFTW3_WITH_MKL=ON`、`-DCP2K_ENABLE_FFTW3_OPENMP_SUPPORT=ON`（默认）、`-DCP2K_ENABLE_FFTW3_THREADS_SUPPORT=ON` |
| LIBINT | ERI / HFX | `-DCP2K_USE_LIBINT2=ON` |
| LIBXS | 矩阵乘性能（OpenCL 必需） | `-DCP2K_USE_LIBXS=ON` |
| LIBXSTREAM | OpenCL offload runtime | **无独立选项**；由 `-DCP2K_USE_ACCEL=OPENCL` 自动启用 |
| LIBXSMM | JIT kernel | `-DCP2K_USE_LIBXSMM=ON`（依赖 `-DCP2K_USE_LIBXS=ON`） |
| LIBXC | 更多 XC 泛函 | `-DCP2K_USE_LIBXC=ON`；LIBXC 自身配置 `-DDISABLE_KXC=OFF` |
| GauXC | XC 积分 | `-DCP2K_USE_GAUXC=ON` |
| PEXSI | 低标度 SCF | `-DCP2K_USE_PEXSI=ON` |
| PLUMED | 增强采样 | `-DCP2K_USE_PLUMED=ON` |
| spglib | 晶体对称性 | `-DCP2K_USE_SPGLIB=ON` |
| SIRIUS | 平面波 | `-DCP2K_USE_SIRIUS=ON` + 5 个 `SIRIUS_*` 子选项 |
| COSMA | pdgemm 替代 | `-DCP2K_USE_COSMA=ON` |
| LibVori | Voronoi 静电性质 / BQB | `-DCP2K_USE_VORI=ON` |
| Torch (LibTorch) | NequIP / MACE / GauXC Skala | `-DCP2K_USE_LIBTORCH=ON` |
| SPLA | GPU gemm offload | `-DCP2K_USE_SPLA=ON`、`-DCP2K_USE_SPLA_GEMM_OFFLOADING=ON` |
| DeePMD-kit | Deep Potential | `-DCP2K_USE_DEEPMD=ON` |
| ACE | ML-PACE 势 | `-DCP2K_USE_ACE=ON` |
| DFTD4 | 色散校正 | `-DCP2K_USE_DFTD4=ON` |
| libsmeagol | NEGF 电子输运 | `-DCP2K_USE_LIBSMEAGOL=ON` |
| TREXIO | 统一格式（需 HDF5） | `-DCP2K_USE_TREXIO=ON` |
| LibFCI | full-CI 活性空间 | `-DCP2K_USE_LIBFCI=ON` |
| GREENX | RPA / GW / Laplace-MP2 | `-DCP2K_USE_GREENX=ON` |
| TBLITE | GFN2-xTB | `-DCP2K_USE_TBLITE=ON` |
| openPMD | 结构化输出（≥0.16.1，需 MPI） | `-DCP2K_USE_OPENPMD=ON` |
| HDF5 | SIRIUS/TREXIO 硬依赖，QCSchema | `-DCP2K_USE_HDF5=ON` |
| MIMIC (MCL) | 多尺度模拟 | `-DCP2K_USE_MIMIC=ON` |
| libGint | GPU 上的 HFX | `-DCP2K_USE_LIBGINT=ON` |

---

## 5. 加速器（Accelerators）

### 5.1 官方索引页

`technologies/accelerators/index.html` **只有两个链接**（无正文）：

- [CUDA](https://manual.cp2k.org/trunk/technologies/accelerators/cuda.html)
- [HIP / ROCm](https://manual.cp2k.org/trunk/technologies/accelerators/hip.html)

### 5.2 CUDA（官方全文）

| 项 | CMake / 说明 |
|---|---|
| 启用 NVIDIA GPU 支持 | `-DCP2K_USE_ACCEL=CUDA` |
| 指定 CUDA compute capability | `-DCMAKE_CUDA_ARCHITECTURES`，例如 B200 用 `100` |
| **已弃用的选择器** | `-DCP2K_WITH_GPU`，可用值：**K20X, K40, K80, P100, V100, A100, H100, B200, GB10, A40** |
| 用 NVHPC kit 构建 | `-DCP2K_USE_NVHPC=ON` |
| 开启 NVIDIA Tools Extensions | `-DCP2K_WITH_GPU_PROFILING`，**需要链接 `-lnvToolsExt`** |
| 加速大 DGEMM 的 BLAS/ScaLAPACK | 例如 `libsci_acc` |
| 关闭 grid 库 GPU 后端 | `-DCP2K_ENABLE_GRID_GPU=OFF` |
| 关闭稀疏张量库 GPU 后端 | `-DCP2K_ENABLE_DBM_GPU=OFF` |
| 关闭 FFT 及 gather/scatter 的 GPU 后端 | `-DCP2K_ENABLE_PW_GPU=OFF` |
| 关闭 DBCSR 的 GPU 后端 | `-DCP2K_DBCSR_USE_CPU_ONLY=ON` |

### 5.3 HIP / ROCm（官方全文）

> The code for the HIP based grid backend was developed and tested on **Mi100** but should work out of the box on NVIDIA hardware as well.

| 项 | CMake / 说明 |
|---|---|
| 启用 AMD GPU 支持 | `-DCP2K_USE_ACCEL=HIP` |
| 关闭 grid 库 GPU 后端 | `-DCP2K_ENABLE_GRID_GPU=OFF` |
| 关闭稀疏张量库 GPU 后端 | `-DCP2K_ENABLE_DBM_GPU=OFF` |
| 关闭 FFT 及 gather/scatter 的 GPU 后端 | `-DCP2K_ENABLE_PW_GPU=OFF` |
| 关闭 DBCSR 的 GPU 后端 | `-DCP2K_DBCSR_USE_CPU_ONLY=ON` |
| 启用统一内存 | `-DCP2K_USE_UNIFIED_MEMORY=ON`（**experimental and only supports Mi250X and above**） |
| 指定架构 | `-DCP2K_WITH_GPU==Mi50, Mi60, Mi100, Mi250, Mi300`；支持 Mi300(A,X) (gfx1103)、Mi250 (gfx90a)、Mi100 (gfx908)、Mi50 (gfx906) |
| 开启 ROC Tracer | `-DCP2K_WITH_GPU_PROFILING`，**需要链接 `-lroctx64 -lroctracer64`** |
| ROCm 文档 | <https://rocm.docs.amd.com/en/latest/> |

> **官方附注**：HIP 后端 grid 库**也支持 NVIDIA 硬件**——用同一套代码，可用于在只有 NVIDIA 硬件时验证该后端。

---

## 6. 特征求解器（Eigensolvers）

官方 `technologies/eigensolvers/index.html` **全文只有一句**：

> CP2K integrates multiple libraries for the solution of eigenvalue problems. **ScaLAPACK is a mandatory dependency when using MPI**, but GPU-accelerated libraries are optionally available.

| 结论 | 说明 |
|---|---|
| ScaLAPACK | **MPI 时的强制依赖** |
| GPU 加速的特征求解库 | 可选 |

> **官方缺口**：该页**没有列出**各特征求解库的具体名称、CMake 开关或默认选择。用户若需 `PREFERRED_DIAG_LIBRARY` 的可选值，请查 Input Reference（`&GLOBAL` 段）。

> 关联：`08_errors_and_faq.md` §2.1.3 提到 ELPA 是默认对角化库，可用 `PREFERRED_DIAG_LIBRARY SCALAPACK` 规避某些 bug。

---

## 7. 编译相关 FAQ（3 条）

### 7.1 CPU 扩展未被充分利用的 HINT（faq:hint_insufficiently_exploiting_cpu_extensions）

**官方报错原文**：

```
HINT in environment.F:804 The compiler target flags used to build this 
binary are insufficiently exploiting the extensions which are available 
for this CPU model.
```

**官方解释**：

> This means that the CPU running this CP2K executables has additional instructions (like `AVX`, etc.) which could be exploited to make small areas of the code run faster, but the compiler did not build the necessary code to do so when this CP2K executable was compiled from source.

**官方给出的排查清单**：

| 情形 | 官方说明 |
|---|---|
| 用发行版或官方预编译的可执行文件 | **唯一办法是自己从源码构建** |
| 已用 `-march=native` 或 `-xHost` 但仍见 HINT | 说明**构建 CP2K 的机器的指令集比运行 CP2K 的机器小**；必须改用**针对目标架构的具体标志**（查编译器文档），而不是自动检测。**代价是最终可执行文件可能不再能在构建机上运行，只能在目标机上运行** |
| **Intel Compiler** | 据其文档，**默认只启用 SSE2**；查文档确定目标 CPU 该加哪些标志，或在本机即目标机时加 `-xHost` |
| **GNU Compiler** | GNU 编译器**默认（与优化级别无关）最多只发 SSE2 指令**；用合适的 `-march=…` 或（构建机=目标机时）`-march=native` |
| 第三方库 | **同样的规则适用于 CP2K 使用的第三方库** |

### 7.2 构建 libsmm 时"Argument list too long"（faq:libsmm_arguments_too_long）

**官方报错原文**：

```
make: execvp: /bin/sh: Argument list too long
```

**官方解释**：

> The libsmm build process involves compiling many small (versions of) matrix multiplication kernels and testing them. For some shells / settings, the makefile may generate lists of arguments that are too long… **This most likely occurs if you are building the library interactively (i.e. not through a batch system).**

**官方 workaround**（用"batch / workload manager"选项 + 空提交命令）：

```
./generate -c config/linux.intel -j 100 -w none -t 24 tiny1
```

| 选项 | 官方说明 |
|---|---|
| `-w none` | 使用空提交命令 |
| `-j 100` | 把构建拆成 100 个独立阶段 |
| 处置 | **增大 `-j` 的值直到不再出现该错误** |

### 7.3 toolchain 脚本非零退出码（faq:toolchain_non_zero_exit_code_detected）

**官方报错示例**：

```
[...]
binutils-2.30.tar.gz: OK
Checksum of binutils-2.30.tar.gz Ok
Installing from scratch into /tmp/cp2k/tools/toolchain/install/binutils-2.30
ERROR: (/tmp/cp2k/tools/toolchain/scripts/install_binutils.sh, line 16) Non-zero exit code detected.
```

**官方 Solution**：

> Check for the detailed error message in one of the `*.log` files in `tools/toolchain/build/<THE_FAILED_PACKAGE>`.

**找全部日志的命令**：

```
cd your/cp2k/code/location
find tools/toolchain -iname "*.log"
```

> 对 binutils 的例子，应在 `/tmp/cp2k/tools/toolchain/build/binutils-2.30/` 下的 `configure.log`、`make.log` 或 `install.log` 中找到更详细的错误消息。

---

## 8. 官方页面缺口与版本敏感项

| 项 | 状态 | 处置 |
|---|---|---|
| `installation.html` 的 Instructions 节 | **只有链接，无正文** | 见 §2 |
| `accelerators/index.html` | **只有 2 个链接，无正文** | 见 §5.1 |
| `eigensolvers/index.html` | **只有一句话，无具体库清单** | 见 §6 |
| `faq:cuda_support` | 仅跳转 | 见 §5.2 |
| `faq:contribute` / `faq:usagestats` / `faq:name` / `faq:doing_io` | 非编译相关，未收录 | 需要时回查官网 |
| toolchain 与 Spack 的完整用法 | **官方在本层所抓页面中未展开** | 见 `github.com/cp2k/cp2k/blob/master/INSTALL.md` |
| MPI `MPI_THREAD_MULTIPLE` 要求 | **2027.1 起** | 见 §3.1 ③、`11_version_changelog.md` |
| DFTD4 legacy 接口 | **2026.2 是最后一个版本** | 见 §3.6 ⑰、`11_version_changelog.md` |
| libtorch ≤ 2.12.1 与 oneMKL 不兼容 | 官方 Caution | 见 §3.7 ⑲ |
| openPMD-api ≥ 0.16.1 | 官方硬要求 | 见 §3.10 ㉘ |

---

## → 交叉索引

| 本文件内容 | 关联 A/F 层条目 | 关联 G 层文件 |
|---|---|---|
| 编译安装与本机工具链 | F 层 `playbook.md`（本机编译经验） | — |
| `psmp` / `ssmp` / `pdbg` / `sdbg` 四种构建 | — | `01_global_and_units.md`（运行命令） |
| MPI vs OpenMP 配比 | — | `08_errors_and_faq.md` §3.12 |
| DFTD4 与色散校正 | A 层 decide.md 色散校正相关 | `02_dft_methods.md` §11 |
| PLUMED 与增强采样 | A 层 decide.md 元动力学相关 | `02_dft_methods.md`（方法索引） |
| SIRIUS 与平面波 | — | `02_dft_methods.md` §1（GPW/GAPW） |
| `PREFERRED_DIAG_LIBRARY` / ELPA | — | `08_errors_and_faq.md` §2.1.3 |
| spglib 与对称性 | — | `02_dft_methods.md` §4 |
| LibTorch / MACE / NequIP / DeePMD / ACE | — | `10_features_resources.md`（功能清单） |
| HDF5 / TREXIO / openPMD / LibVori | — | `10_features_resources.md`（功能清单） |
