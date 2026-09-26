# 08 · 官方故障排查与 FAQ

> **来源**：
> - <https://manual.cp2k.org/trunk/getting-started/troubleshooting.html>（故障排查，全文）
> - <https://www.cp2k.org/faq> 及各 FAQ 子页（共 19 条，其中 **14 条已取正文**）
> **抓取日期**：2026-09-08（第一、二轮）；**2026-09-09 第三轮补入 §3.14–§3.17 四条 FAQ**
> **本文件定位**：G 层（官方权威层）。只写官方说了什么，不写经验性做法。经验性排错流程见 F 层 `playbook.md`。

---

## 0. 官方对"报错"的基本态度

官方 troubleshooting 页开头原文：

> True to any advanced computational task, encounters to warnings and errors can be frequent and inevitable when working with CP2K due to various reasons. Don't panic: this page analyzes a selected catalog of possible issues and provides hints on how to address them.
>
> This is a dynamic list attempting to cover more topics of interest; feel free to open requests for expansion, but please read first and bear in mind the recommendations about asking questions in the Foreward and FAQ. Moreover, here is a gentle reminder that **the normal termination of a computational task does not inherently guarantee scientifically meaningful, accurate, rigorous and publishable results.**

**官方最后一句是重点**：**正常结束 ≠ 结果有意义**。报错要排查，不报错也要验收。

---

## 1. 先搞清楚输入输出去哪了（Whereabouts of Input & Output）

官方在讲具体报错之前，先给了一段"基础知识回顾"。

### 1.1 三种标准流

| 流 | 文件描述符 | 用途 |
|---|---|---|
| `stdin` | 0 | 读数据 |
| `stdout` | 1 | 写数据 |
| `stderr` | 2 | 写错误消息 |

重定向用 `>` 或 `>>`，管道用 `|`。

### 1.2 官方给的三种典型启动命令

**① 常规 MPI 并行（`stdout` 进文件，`stderr` 在屏幕）**

```
mpirun -np 2 -x OMP_NUM_THREADS=1 cp2k.psmp -i project.inp -o project.out
```

**② 把 `stderr` 也并进同一个文件**

```
mpirun -np 2 -x OMP_NUM_THREADS=1 cp2k.psmp -i project.inp 1>project.out 2>&1
```

> 官方说明：`1>` 让 `project.out` 成为 `stdout`，`2>&1` 让它同时成为 `stderr`。

**③ 用 `tee` 同时看屏幕和存文件**

```
mpirun -np 2 -x OMP_NUM_THREADS=1 cp2k.psmp -i project.inp | tee project.out
```

> 官方说明：`stdout` 进 `tee`，屏幕和文件同时得到日志；`stderr` 仍在屏幕（未重定向）。

**④ 排队系统**

> If CP2K is launched by job scheduling systems in a queue, the `stdout` and `stderr` may be set up with its own configurations; for instance, the Slurm Workload Manager defines `--output=<filename>` and `--error=<filename>` options for the `srun` command.

### 1.3 `PRINT` 段决定"打印什么、打印到哪"

官方以 `FORCE_EVAL/PRINT/FORCES` 为例：

```
&FORCE_EVAL
  &PRINT
    &FORCES ON
    &END FORCES
  &END PRINT
&END FORCE_EVAL
```

| 要点 | 官方说明 |
|---|---|
| `&FORCES ON` | 打开 `ATOMIC FORCES` 输出 |
| `FILENAME` | 决定输出去哪 |
| 默认值 | 字符串 `__STD_OUT__`，意为"the screen or standard logger"，等价于 `stdout` |
| 设成别的 | 会创建单独文件 |

### 1.4 多副本任务的日志陷阱（重要）

官方原文：

> Note that certain types of tasks like vibrational analysis, nudged elastic band, swarm, farming, …, have ***multiple*** output logs depending on the replica and parallelization in use; sometimes the single primary log (specified by `-o` option above) may not be as informative or primitive as the secondary logs (automatically generated per replica under the working directory) and it is necessary to locate the exact issue(s) from the latter. This applies to warnings and errors too, which in addition are typically issued on **the first MPI rank of each replica**.

| 任务类型 | 日志数量 |
|---|---|
| 振动分析、NEB、swarm、farming 等 | **多个**（按 replica 生成） |

**两条官方提示**：

1. 主日志（`-o` 指定的）**不一定**是最有信息量的；**必须去工作目录下找各 replica 的次日志**。
2. 警告与错误**通常只打印在每个 replica 的第一个 MPI rank 上**。

---

## 2. 官方故障排查六类（Problems and Solutions）

### 2.1 程序卡住或被莫名杀掉

**官方原文标题**：Program is stuck or killed for unknown reason

#### 2.1.1 第一动作：确认是否真在跑

> When the program appears to freeze and stop updating any of the logs for outputs, check immediately whether it is still running with `ps aux` or `top`/`htop` commands or with the job scheduler.

#### 2.1.2 OOM（内存不足）

> An out-of-memory (OOM) error can occur if the memory allocation for the program fails to meet the actual requirement during execution. This may or may not have a clear-cut message due to uncertainty in the timing, but may be confirmed in a re-run with the `free` or `ps aux` commands monitoring the memory consumption.

**官方给的三条对策**：

| 对策 | 官方措辞 |
|---|---|
| 加内存 | 若可行 |
| **减少 MPI 进程数** | reducing the number of MPI parallel processes |
| **改用 MPI + OpenMP 混合**（`psmp` 构建） | switching to MPI + OpenMP hybrid parallelism for the `psmp` build can reduce the total memory consumption |

#### 2.1.3 ELPA 相关的卡死

> If CP2K is built with ELPA, it would be the default diagonalization library. Setting `PREFERRED_DIAG_LIBRARY` to `SCALAPACK` can probably circumvent some bugs like in github issue #4484.

| 现象 | 处置 |
|---|---|
| 用 ELPA 构建且卡住 | 把 `PREFERRED_DIAG_LIBRARY` 设为 `SCALAPACK` |

#### 2.1.4 杂化泛函的内存与耗时

官方原文：

> When running a hybrid DFT calculation, where it is well-known that the evaluation of ERI for Hartree-Fock exchange and the in-core storage tends to be very memory-intensive, the upper bound of memory requirement depends on the number of MPI parallel processes and the value of `MAX_MEMORY` in MB. **The first SCF cycle is usually very time-consuming due to the necessary initial evaluation of ERI, and so do not terminate the program too early as long as the memory is fine.**

| 要点 | 官方说明 |
|---|---|
| 内存上限取决于 | MPI 进程数 + `MAX_MEMORY`（单位 MB） |
| 第一个 SCF 循环 | **通常非常耗时**（首次 ERI 求值） |
| 处置 | **只要内存没问题，别过早终止程序** |

#### 2.1.5 优化 / NEB 卡住

> There are heavy tasks like optimization and nudged elastic band that have been reported to stuck for indeterminate time, which have rarely been reproduced reliably. In case it happens, chances are that adjusting the `OPTIMIZER` or `OPT_TYPE` can help, and utilizing the latest restart file to re-run the job until convergence is recommended.

| 官方处置 | 说明 |
|---|---|
| 调整 `OPTIMIZER` 或 `OPT_TYPE` | 可能有效 |
| **用最新重启文件重跑直到收敛** | 官方推荐 |

### 2.2 输出消息交错重复（MPI 没生效）

**官方原文标题**：Interleaved multiplicated output messages

**正常情况**（4 进程）：

```
mpirun -np 4 -x OMP_NUM_THREADS=1 cp2k.psmp -i project.inp -o project.out
```
```
 DBCSR| MPI: Number of processes                                               4
 DBCSR| OMP: Current number of threads                                         1
```

**异常情况**（同一消息出现 4 次）：

```
 DBCSR| MPI: Number of processes                                               1
 DBCSR| OMP: Current number of threads                                         1
```

> …along with many other interleaved and multiplicated lines like `PROGRAM STARTED AT {time}` and `PROGRAM PROCESS ID {pid}`, then CP2K is **not parallelized as intended**, but run as several independent processes that are all writing to a common output log in some indeterminate order.

**官方诊断结论**：

> This means that the environment is not configured properly and the active MPI library (as shown by `which mpirun`) is not the one that CP2K has been linked to (as shown by `ldd cp2k.psmp`).

| 检查项 | 命令/位置 |
|---|---|
| 当前生效的 MPI | `which mpirun` |
| CP2K 链接的 MPI | `ldd cp2k.psmp` |
| 两者不一致 → | 环境配置错误 |

**官方排查清单**：

> Check everything that determines the environment variables and paths, including but not limited to `~/.bashrc` and `/etc/profile` files, modules, and conda envs. If the CP2K is built from source with toolchain, do not forget to source the `cp2k_env` to load the dependencies as instructed.

- `~/.bashrc`、`/etc/profile`
- modules
- conda envs
- **源码构建时要 `source cp2k_env`**

### 2.3 输出里出现星号、NaN 或 Inf

**官方原文标题**：Asterisks, NaN or Inf in the output

#### 2.3.1 星号 `***` 的成因（Fortran 定宽格式）

官方举例：

> For example, the edit descriptor `F12.6` specifies a real float-type field with exactly 12 characters, including 6 for the fractional part and 1 for the decimal point (and 1 for the minus sign if negative), thus leaving only 5 places for the integer part; if the value to be printed is larger than 99999.999999 or smaller than -9999.999999, it would not fit in and a string of asterisks `************` would be shown instead.

**`F12.6` 的位宽分配**：

| 用途 | 字符数 |
|---|---|
| 小数部分 | 6 |
| 小数点 | 1 |
| 负号（若为负） | 1 |
| 整数部分 | 12 − 6 − 1 − 1 = **5** |
| 溢出阈值 | > 99999.999999 或 < −9999.999999 |

**官方的重要提醒**：

> Most of these field formats are designed with output layout, value precision and possible range in mind, so the presence of a string of asterisks in the place of numeric output **should invoke some doubts on the reliability of very large or very small numeric results, even if the calculation looks fine otherwise**.

> Note that there are some format specifications like the PDB file and the Gaussian cube file where the entries have some restricted fixed-width field formats for writing or reading, while others like the XYZ file are more lenient.

| 文件格式 | 定宽限制 |
|---|---|
| PDB | 有受限的定宽字段格式 |
| Gaussian cube | 有受限的定宽字段格式 |
| XYZ | 较宽松 |

#### 2.3.2 `NaN` / `Inf`

> Beyond that, abnormal values may be represented as `NaN` for "Not a Number" or `Inf` for Infinity, padded with whitespaces to satisfy the width of the edit descriptor. **Both of these marks in the output suggest that something numerically unstable has gone haywire and needs developer attention.**

| 标记 | 含义 | 官方判断 |
|---|---|---|
| `NaN` | Not a Number | 数值不稳定失控，需要开发者关注 |
| `Inf` | Infinity | 同上 |

### 2.4 输入解析类型错误

**官方原文标题**：A certain type object was expected, found something else

**报错格式**：

```
A (integer|floating point|string) type object was expected, found (end of line|<something>),
File: <filename>, Line: <line>, Column: <col>
```

**官方说明**：

> This kind of error arises from the parser of input files, and naturally is resolved by preparing or editing the file in accordance with the manual. Say, a structure input requiring XYZ format should not use CIF, and the XYZ file should have number of atoms on the first line, comments on the second line and each of the rest of (number of atoms) lines in a format of `element-symbol X-coordinate Y-coordinate Z-coordinate`.

**XYZ 格式的官方要求**：

| 行 | 内容 |
|---|---|
| 第 1 行 | 原子数 |
| 第 2 行 | 注释 |
| 其余 N 行 | `元素符号 X坐标 Y坐标 Z坐标` |

### 2.5 `CPASSERT failed`

**官方原文标题**：CPASSERT failed

> `CPASSERT` is one of the Error Handling mechanisms in CP2K intended for conditions that should hold most of the time, like some basic sanity checks for correct data types, matching matrix dimensions, or availability of essential elements for a certain routine. Therefore, `CPASSERT failed` is a minimal blanket statement for these unlikely events, **only indicating the code location at the lower right corner of the message box**.

| 要点 | 说明 |
|---|---|
| `CPASSERT` 用途 | 数据类型、矩阵维度、必要元素存在性等**基本健全性检查** |
| `CPASSERT failed` 信息量 | **极少**，只在消息框右下角给出代码位置 |
| 处置 | 若输入文件严格按文档写仍报错，**报告给开发者**并说明条件失败的情形 |

> The message may be revised for a clearer user-oriented phrasing upon reasonable request.

### 2.6 几何错误或 `EMAX_SPLINE` 太小

**官方原文标题**：GEOMETRY wrong or EMAX_SPLINE too small

> This error originates from closely contacting or outright overlapping atoms in the geometry that are detected while building a neighbor list. Although the keyword `EMAX_SPLINE` is for a Molecular Mechanics (MM) calculation with classical force fields, **this error does not necessarily come from a MM or QM/MM task** because neighbor lists are also widely used in quantum mechanics (QM).

| 要点 | 说明 |
|---|---|
| 根因 | 几何中原子**过近接触或直接重叠**，在构建邻接表时被检测到 |
| 关键字归属 | `EMAX_SPLINE` 属 MM，但**QM 也用邻接表**，所以 QM 也会报这个错 |

**官方给出的三类常见建模陷阱**（原文三条）：

| # | 官方原文 | 含义 |
|---|---|---|
| 1 | The file conversion procedure during structure preparation involve formats that do not record any information about periodicity or cell definition, or whose record is not yet universally recognized such as the extended XYZ specification | 结构准备时的格式转换**丢失周期性/晶胞信息**（如 extended XYZ 尚不被普遍识别） |
| 2 | The redefinition of cell vectors (most commonly by means of linear transformation) and the construction of surface slabs or supercells violate the original periodicity, or fail to deduplicate atoms sent to the same coordinate dictated by symmetry-equivalent positions | 重定义晶胞矢量（常见于线性变换）、构建表面 slab 或超胞时**破坏原有周期性**，或**未去重**对称等价位置的原子 |
| 3 | The structure contains crystallographic disorder where one site has more than one possible type of atom, and the fractional occupancy is not handled well when creating the model | 晶体学无序：一个位点有多种原子可能，**分数占据**在建模时未妥善处理 |

> 官方同时提醒：Always remember to inspect the input structure in a visualization program as said in the section Starting structure and cell.

### 2.7 SCF 收敛问题（官方指向另一页）

> `SCF run NOT converged` and `KS energy is an abnormal value (NaN/Inf)` are discussed separately on How to make a SCF run converge.

→ 见 G 层 `03_scf_convergence.md`。

### 2.8 消息里出现 LSD

**官方原文标题**：Messages mentioning LSD

> `LSD` is an alias for UKS in some error messages such as `Use the LSD option for an odd number of electrons` and `LSD: try to use a different multiplicity`. CHARGE and MULTIPLICITY options should be set correctly based on the chemistry to be modelled. **If the system is intended to be closed-shell, broken geometry like missing or duplicated hydrogen atoms may give rise to the errors.**

| 关键事实 | 说明 |
|---|---|
| `LSD` = `UKS` 的别名 | 出现在错误消息里 |
| 两条典型消息 | `Use the LSD option for an odd number of electrons` / `LSD: try to use a different multiplicity` |
| 处置 | `CHARGE` 与 `MULTIPLICITY` 按化学正确设置 |
| **反查** | 若体系本应闭壳，**缺氢/重复氢**等几何错误也会触发这类报错 |

---

## 3. 官方 FAQ 清单（19 条）

> **来源**：<https://www.cp2k.org/faq>（页面最后修改 2020/08/21）

### 3.1 全部条目

| # | 官方标题 | 链接 | 本层是否收录正文 |
|---|---|---|---|
| 1 | HINT: Compiler target flags insufficiently exploiting the extensions of this CPU model. | `faq:hint_insufficiently_exploiting_cpu_extensions` | 否（见 `09_build_libraries.md`） |
| 2 | How can I generate a new basis set? | `faq:new_basis_set` | ✅ §3.2 |
| 3 | How can I speedup my calculations? | `faq:speedup` | ✅ §3.3 |
| 4 | How can one contribute to CP2K? | `faq:contribute` | 否 |
| 5 | How can one guess a reasonable cutoff value? | `faq:cutoff` | ✅ §3.4 |
| 6 | How do I solve "CPASSERT failed" in cp_fm_cholesky.F? | `faq:cholesky_decomp_failed` | ✅ §3.5 |
| 7 | How do I solve the "Argument list too long" error when building libsmm? | `faq:libsmm_arguments_too_long` | 否（见 `09_build_libraries.md`） |
| 8 | How large is CP2K's user base? | `faq:usagestats` | 否 |
| 9 | How to choose the NGRIDS in &MGRID | `faq:ngrids` | ✅ §3.6 |
| 10 | How to cite CP2K | `faq:cite` | ✅ §3.7 |
| 11 | I received a warning message about the Kohn Sham matrix not 100% occupied when doing Hartree-Fock or hybrid calculations… | `faq:hfx_eps_warning` | ✅ §3.8（重要） |
| 12 | Into which spin channel do excess electrons go? | `faq:uks_convention` | ✅ §3.9 |
| 13 | kpoints | `faq:kpoints` | ✅ §3.10（**已过时**） |
| 14 | My simulation fails. Any ideas? | `faq:common_mistakes` | ✅ §3.11（**含过时内容**） |
| 15 | Non-zero exit code detected when using the CP2K toolchain script | `faq:toolchain_non_zero_exit_code_detected` | 否（见 `09_build_libraries.md`） |
| 16 | Should I use MPI or OpenMP or both? | `faq:mpi_vs_openmp` | ✅ §3.12 |
| 17 | What does the name CP2K stand for? | `faq:name` | 否 |
| 18 | What is the correct way to write information to the screen? | `faq:doing_io` | 否 |
| 19 | Which parts of CP2K are CUDA-accelerated? | `faq:cuda_support` | ✅ §3.13 |

### 3.2 如何生成新基组（faq:new_basis_set）

官方原文关键句：

> We have different options available to generate basis sets within CP2K. However, all of them also require a large part of manual invention. **There are no black box schemes.**

**三种方法**：

| 方法 | 官方描述 | 参考文件 |
|---|---|---|
| **Method 1** | Optimize the exponents of a Gaussian basis with the atomic code for a given reference state. 需选择每个 l 量子数的 Gaussian 数目、原子态…；计算收缩系数并按量化配方生成附加函数。可能需要补充原子计算无法给出的极化函数。 | `tests/ATOM/regtest-2/Ru*.inp` |
| **Method 2** | Just like Method 1 but calculate the contractions from an atomic response calculation. | `tests/ATOM/regtest-2/Ru_basis.inp` |
| **Method 3** | MOLOPT basis sets. This requires extensive calculations on test molecules. | `tests/QS/regtest-optbas` |

### 3.3 如何加速计算（faq:speedup）

官方把性能分成**两个层面**：物理层面与计算层面。

**物理参数（Physical parameters）**：

| # | 官方描述 |
|---|---|
| 1 | choosing the cheapest representation of your system that gives correct results e.g. choosing an appropriate basis set (Gaussian), and also an appropriately sized plane-wave expansion |
| 2 | SCF settings — choosing an appropriate convergence threshold, and diagonalization algorithm (**or use OT for non-metallic systems for much greater performance, with a good preconditioner**) |

**计算层面（Computational aspects）**：

| # | 官方描述 |
|---|---|
| 1 | 若用 MPI 并行，**先用缩短版问题做测试**，确定能有效使用多少 CPU 核。经验法则：typical settings 下合理扩展约到 `nprocs ≈ natoms` |
| 2 | 用高编译优化（如 `-O3`）与优化的 BLAS/LAPACK 库（如 MKL、GotoBLAS、ATLAS） |
| 3 | 构建可选的性能关键库 `libsmm`（`cp2k/tools/build_libsmm`）与 `libgrid`（`cp2k/tools/autotune_grid`） |

**官方最后一条建议**：

> Before going to far down any of these areas, take a look at the **timing report** which is printed at the end of your CP2K job output. This will give you some information about which parts of the code are taking the most time, and therefore where to invest your time tweaking to get the best performance.

即：**先看作业输出末尾的 timing report**，再决定优化方向。

### 3.4 如何猜一个合理的 CUTOFF（faq:cutoff）

官方原文（**"给没耐心的 CP2K 用户"**）：

> As a rule of thumb one can multiply the largest exponent of the Gaussian basis sets employed by **40** to obtain a reasonable guess for the cutoff value in **Rydberg**.

**官方举例**：

| 基组 | 最大指数 |
|---|---|
| 氧的 DZVP-MOLOPT-SR-GTH | 约 **10.4** |
| 氢的 DZVP-MOLOPT-SR-GTH | 约 **10.0** |
| → 推荐的起始 CUTOFF | **10 × 40 = 400 Ry** |

**官方给出的验收判据**：输出中

```
Total charge density on r-space grids:        0.0000000000
Total charge density g-space grids:           0.0000000000
```

> …in the CP2K output should be **smaller than 10⁻⁸**.

**如何让它每次都打印**：

```
&GLOBAL
 PRINT_LEVEL medium
 ...
&END GLOBAL
```

> The default is to print this information when the SCF iteration is converged which possibly might never happen with a too small cutoff value.

> **注意**：这与 G 层 `03_scf_convergence.md` 的 CUTOFF 收敛教程是同一主题的两处官方口径——FAQ 给"40 倍最大指数"的快速估计，收敛教程给系统的收敛流程。两处并不矛盾：FAQ 是起点，教程是精调。

### 3.5 `cp_fm_cholesky.F` 的 CPASSERT 失败（faq:cholesky_decomp_failed）

**典型报错**（官方注明行号以 CP2K 2.7 为准）：

```
 *******************************************************************************
 *   ___                                                                       *
 *  /   \                                                                      *
 * [ABORT]                                                                     *
 *  \___/                             CPASSERT failed                          *
 *    |                                                                        *
 *  O/|                                                                        *
 * /| |                                                                        *
 * / \                                                  fm/cp_fm_cholesky.F:94 *
 *******************************************************************************

 ===== Routine Calling Stack ===== 

           10 cp_fm_cholesky_decompose
            9 make_full_inverse_cholesky
            8 make_preconditioner
            7 prepare_preconditioner
            6 init_scf_loop
            5 scf_env_do_scf
            4 qs_energies
            3 qs_forces
            2 qs_mol_dyn_low
            1 CP2K
```

**官方诊断**：

> This says that CP2K failed to compute a Cholesky decomposition during the construction of the preconditioner for OT. Most likely, the **overlap matrix (S) has become singular** (or at least numerically close to singular).

**官方三条处置**：

| # | 官方原文 | 说明 |
|---|---|---|
| 1 | Try some of the other `PRECONDITIONER` options, which may prove to be more stable for your system | 换 `PRECONDITIONER` |
| 2 | Decrease the value of `EPS_DEFAULT` or `EPS_PGF_ORB`, to reduce the amount of numerical noise in the construction of S | 减小 `EPS_DEFAULT` / `EPS_PGF_ORB` |
| 3 | Check carefully that the Basis Set(s) chosen for your calculation are appropriate for the system. **If the basis set is over-complete this could result in a singular overlap matrix** — try switching to a smaller basis set | 基组过完备会导致 S 奇异 → 换更小的基组 |

### 3.6 如何选择 `&MGRID` 的 `NGRIDS`（faq:ngrids）

官方原文：

> The three inputs "CUTOFF", "NGRIDS", and "REL_CUTOFF" are important for accuracy and efficiency. The problem is that both, "accuracy and efficiency" depend on the combination of chosen values.

**官方给出的最优设置流程（两步）**：

**第 1 步：选足够高的 `REL_CUTOFF`**

> this is **system and basis set independent**. It determines the minimal cutoff used to bring a Gaussian function on the real space grid. High values mean high accuracy, low values faster execution.

**第 2 步：选 cutoff 与网格数，决定实空间网格**

官方举例：

> for your calculation, e.g. cutoff=400 ngrids=4
> grid1 = 400, grid2 = 200, grid3 = 100, grid4 = 50 (**not actual numbers**)

**官方给出的判据（关键不等式）**：

> The cutoff should be high enough to take on the Gaussian with the largest exponent, i.e. **exponent × REL_CUTOFF ≤ cutoff** (where exponent is for a product Gaussian)

**`NGRIDS` 的取舍**：

> If you choose more grids the mapping (Gaussian→Grid) is better but you have more overhead from more grids (mostly FFTs).

| `NGRIDS` 增大 | 效果 |
|---|---|
| 高斯→网格映射 | 更好 |
| 开销 | 更大（主要是 FFT） |

### 3.7 如何引用 CP2K（faq:cite）

> When performing calculations with CP2K, you will find a "R E F E R E N C E S" section in the output. This section lists the scientific articles that describe the specific modules and methods used in the calculation.
>
> When using CP2K as part of a scientific publication, the CP2K developer team kindly asks you to acknowledge their work by citing the articles in the "R E F E R E N C E S" section.
>
> Sometimes, you may need to cite CP2K in contexts where a detailed list of references is not appropriate (for example, as part of a list of quantum chemistry or solid state physics software packages). In this case, we recommend citing the latest relevant CP2K review. **As of May 2020, this is [10.1063/5.0007045](https://dx.doi.org/10.1063/5.0007045)**.

| 场景 | 引用方式 |
|---|---|
| 正常论文 | 引用输出中 `R E F E R E N C E S` 段列出的文章 |
| 软件清单等不宜列详单的场合 | 引用最新的 CP2K review（截至 2020-05 为 DOI `10.1063/5.0007045`） |

> **注意**：`10.1063/5.0007045` 是官方页面在 2020 年给出的"最新 review"。G 层原样保留该版本信息，不替换为更新的综述——若需更新，应回查官网当前状态。

### 3.8 KS 矩阵未 100% 占据的警告（faq:hfx_eps_warning）★

这是 FAQ 中**技术含量最高、最容易误判**的一条，官方 2023.2 起有更新。

#### 3.8.1 官方警告原文

```
The Kohn Sham matrix is not 100% occupied. 
This may result in incorrect Hartree-Fock results. 
Setting MIN_PAIR_LIST_RADIUS to -1 in the QS section 
ensures a fully occupied KS matrix. 
```

#### 3.8.2 官方首要处置（2023.2 起）

> **Since version 2023.2** The occupancy of the Kohn-Sham matrix depends on whether atomic pairs are neighbours. Two atoms are considered neighbours if their basis functions (Gaussians) are overlapping, which is controlled through the `EPS_PFG_ORB` keyword. In large cells, the KS matrix can be sparse because atomic pairs can be further apart. **Setting the `MIN_PAIR_LIST_RADIUS` to -1 makes sure all atomic pairs within the unit cell are considered neighbours**, therefore ensuring a full KS matrix. **This is considerably more efficient than reducing `EPS_PFG_ORB` to unreasonably small numbers.**

| 方案 | 官方评价 |
|---|---|
| `MIN_PAIR_LIST_RADIUS -1` | **效率高得多**（2023.2 起的首选） |
| 把 `EPS_PGF_ORB` 减到不合理的极小值 | 不推荐 |

> **原文拼写**：官方页面同时出现 `EPS_PFG_ORB`（两处）与 `EPS_PGF_ORB`（多处）。正确的关键字名是 **`EPS_PGF_ORB`**，`EPS_PFG_ORB` 是官方笔误。G 层保留原文但在此标注。

#### 3.8.3 为什么会出这个警告（官方机理）

> In a normal DFT (LSDA/GGA) calculation, the sparsity of the Kohn Sham (KS) matrix is the same as the overlap matrix… the density matrix and Kohn Sham matrix are stored using the same sparse pattern as the overlap matrix. This makes the calculation efficient… and the accuracy of the calculation as well as the electron density function are unaffected.
>
> For Hartree Fock exchange calculations, however, this is no longer the case. The sparsity of the KS matrix is no longer that of the overlap matrix. For the HF exchange term, we need all non-zero blocks of the density matrix and not only those that matched with the overlap. This contributes to more non-zero elements in the KS matrix.
>
> Due to anything outside the sparsity pattern of the KS matrix—which is based on that of the overlap matrix—is not stored, the Hartree Fock code performs a screening of the HF exchange terms based on the sparsity pattern of KS, and has to *assume* that if a block is not present in the KS matrix then the HF exchange contribution to the block is also zero. **This is not always true**, depending on the property of the density matrix. Therefore, when the code detects that non-zero contributions of the HF exchange terms are being screened out, it produces the above warning message.

**机理链条**：

```
普通 DFT（LSDA/GGA）：KS 矩阵稀疏模式 = 重叠矩阵稀疏模式 → 安全
         ↓
HF 交换：KS 矩阵稀疏模式 ≠ 重叠矩阵稀疏模式（需要密度矩阵的全部非零块）
         ↓
KS 矩阵外的块不存储 → HF 代码按 KS 稀疏模式筛选
         ↓
代码"假设"：KS 矩阵里没有的块，其 HF 交换贡献也是零
         ↓
但这个假设不总成立 → 检测到 HF 交换的非零贡献被筛掉 → 报警告
```

#### 3.8.4 `EPS_PGF_ORB` 与 `EPS_FILTER_MATRIX`

| 关键字 | 官方描述 | 默认值 |
|---|---|---|
| `EPS_PGF_ORB` | controls the sparse pattern of the overlap matrix. 绝对值小于 `EPS_PGF_ORB` 的元被当作零；整个原子块都小于 `EPS_PGF_ORB` 则该块不进入稀疏矩阵 | **`EPS_DEFAULT` 的平方根** |
| `EPS_FILTER_MATRIX` | 在 KS 矩阵已有重叠稀疏模式之上，若不为零，则把 KS 矩阵中**所有元绝对值都小于 `EPS_FILTER_MATRIX`** 的原子块移除 | **零**（即默认不做这层过滤） |

#### 3.8.5 看到警告该怎么办（官方原文）

> If `EPS_FILTER_MATRIX` is already zero, then setting `EPS_PGF_ORB` to a smaller value will eventually remove the warning message. If `EPS_FILTER_MATRIX` is not zero, then the first course of action is to reduce it.
>
> As usual with screening, the typical error you make is on the order of EPS, except the case when the calculation becomes unstable, which yields results that can be essentially unrelated to EPS (e.g. wrong by O(1)). **In practice, despite of the warning, if a calculation is stable it should be accurate up to the value of `EPS_PGF_ORB` or `EPS_FILTER_MATRIX`—whichever is larger.** You can always check by running a single point calculation with a smaller EPS value, and see if the difference in the total energy is in the order of magnitude as the larger of the EPS value you have tested.
>
> **The warning message is therefore more for the case when the calculation becomes unstable due to the forced screening of the HF exchange.** So if your calculation is unstable, and if you see this warning message, then `EPS_PGF_ORB` and `EPS_FILTER_MATRIX` are the first places to look.
>
> Note that by decreasing `EPS_PGF_ORB`, you will be making the overlap matrix more dense… This will increase your computational cost. However, for calculations with hybrid functionals the cost of HF exchange term usually dominates and hence the associated cost increase… may not be significant in comparison.

**官方给出的判断流程**：

| 情形 | 官方处置 |
|---|---|
| `EPS_FILTER_MATRIX` 已为 0 | 减小 `EPS_PGF_ORB` |
| `EPS_FILTER_MATRIX` 不为 0 | **首先减小它** |
| 计算稳定 + 有警告 | 精度约为 `EPS_PGF_ORB` 与 `EPS_FILTER_MATRIX` 中**较大者**的量级，可接受 |
| 计算不稳定 + 有警告 | `EPS_PGF_ORB` 与 `EPS_FILTER_MATRIX` 是**首要排查点** |
| 验证手段 | 用更小的 EPS 做单点，比较总能差是否与 EPS 量级一致 |

> **重要认知**：官方明确说"**尽管有警告，只要计算稳定，精度就在 EPS 量级**"。这个警告**不是**"结果一定错"，而是"筛掉了可能非零的 HF 交换贡献"。

### 3.9 多余电子进哪个自旋通道（faq:uks_convention）

**规则 1：Alpha ≥ Beta**

> The number of electrons in the alpha channel is greater or equal the number of electrons in the beta channel. It does not matter whether you charge your system by adding an electron (then you have n+1 electrons in channel alpha and n electrons in channel beta) or whether you charge it by taking out one electron (then you have n electrons in channel alpha and n-1 electrons in channel beta).

| 操作 | alpha 通道电子数 | beta 通道电子数 |
|---|---|---|
| 加一个电子（n+1） | n+1 | n |
| 减一个电子（n−1） | n | n−1 |

**规则 2：符号约定**

> In the output log file, the sign convention is such that alpha channel population is positive and beta channel population is negative. So if you have an atom with four spins up (+4, because up=alpha) and one spin down (-1, because down=beta), then your spin charge is **+3**.

| 通道 | 符号 |
|---|---|
| alpha（自旋向上） | 正 |
| beta（自旋向下） | 负 |

**规则 3：cube 文件**

> In the cube files for the spin density, you get the difference between alpha and beta channel, but the voxel data is signed. Following the point above on the sign convention, the value in the cube file is **alpha + beta** (spin up plus spin down) which is identical to the absolute value of the beta channel subtracted from the absolute value of the alpha channel.

| 量 | 表达式 |
|---|---|
| 自旋密度 cube 文件体素值 | `alpha + beta` = `|alpha| − |beta|` |

### 3.10 k 点 FAQ（faq:kpoints）——**官方内容已过时**

> **页面最后修改**：2026/06/23

官方原文**全部内容**：

> For up-to-date information about k-point sampling in CP2K see the following links:
>
> - <https://github.com/cp2k/cp2k/issues/4854>
> - <https://manual.cp2k.org/trunk/methods/dft/k-points.html>
> - <https://manual.cp2k.org/trunk/methods/dft/hartree-fock/ri_kpoints.html>

即**官方自己把这个 FAQ 页改成了指向别处的跳转页**。k 点采样请直接看 G 层 `02_dft_methods.md` §4。

### 3.11 "我的模拟失败了"（faq:common_mistakes）——**含过时内容**★

> **页面最后修改**：2020/08/21

**官方列出的四条常见错误**：

| # | 官方原文 | 说明 |
|---|---|---|
| 1 | `CUTOFF` not converged. **Anything below 200 is almost certainly too low.** Test the convergence explicitly. | CUTOFF 未收敛；**低于 200 几乎肯定太低** |
| 2 | SCF cycle not converged. | SCF 未收敛 |
| 3 | Cell too small. **Keep in mind that CP2K does *not* have k-point sampling.** | 胞太小；原文称"CP2K 没有 k 点采样" |
| 4 | atoms missing / wrong coordinates : visualize your geometry, including periodic images | 原子缺失/坐标错误；**可视化几何，包括周期镜像** |

> ⚠️ **官方过时内容标注**：
>
> 第 3 条中的 "**CP2K does *not* have k-point sampling**" 是 **2020 年的旧表述，已不成立**。CP2K 现在**有** k 点采样：
> - `02_dft_methods.md` §4 记录了 `&KPOINTS` 段的完整用法；
> - `07_restarting.md` §2 记录了 `.kp` 重启文件与 `FULL_GRID`；
> - 官方 `faq:kpoints`（2026-06 修改）已改为跳转页，指向 `methods/dft/k-points.html`；
> - 官方 changelog 记录了 k 点功能的引入与演进（见 `11_version_changelog.md`）。
>
> **G 层处置**：原文照录 + 明确标注过时。使用 k 点时**以 `02_dft_methods.md` 与 Input Reference 为准**。
>
> 其余三条（CUTOFF、SCF、几何检查）**仍然有效**。

### 3.12 该用 MPI 还是 OpenMP（faq:mpi_vs_openmp）

> The entire CP2K code is MPI parallelized. Some additional loops are also OpenMP parallelized. **You should therefore first take advantage of the MPI parallelization.** However, running one MPI-rank per CPU-core will probably lead to memory shortage.
>
> At this point, OpenMP threads can be used to utilized all CPU-cores without the large memory-footprint of a MPI-process.
>
> **The optimal ratio between MPI-ranks and OpenMP-threads depends on the kind of simulation you run. Do your own benchmarks! A ratio of two threads per rank is usually a good point to start.**

| 官方结论 | 说明 |
|---|---|
| CP2K 全部代码 MPI 并行 | 优先用 MPI |
| 部分循环额外 OpenMP 并行 | OpenMP 是补充 |
| 一核一 MPI rank → 可能内存不足 | 这是引入 OpenMP 的原因 |
| **最优 MPI:OpenMP 比取决于模拟类型** | 官方要求**自己做基准测试** |
| 官方起始建议 | **每 rank 两个线程** |

### 3.13 CUDA 加速范围（faq:cuda_support）

> Have a look at our [GPU page](https://www.cp2k.org/gpu) as well as [this howto](https://www.cp2k.org/howto:compile_with_cuda).

官方 FAQ 本身**只有跳转链接**，具体内容见 `09_build_libraries.md`。

### 3.14 如何为 CP2K 做贡献（faq:contribute）

> 来源：`https://www.cp2k.org/faq:contribute`（最后修改 2020/08/21）

官方把贡献方式分成**四类**：

#### （1）用 CP2K！

- **"促成伟大的科学是 CP2K 的主要目的。"** 用 CP2K 做高质量工作，并**向他人展示如何正确、高效地使用 CP2K**。
- **在出版物中给出所用程序的署名，并引用原始文献。** 这**有助于资助后续开发与维护代码**。
- **把工作的摘要加到官方 science 页**。

#### （2）贡献网站

- CP2K 网站**现在完全是一个 wiki**。**大多数页面任何人都可公开编辑，点右边的铅笔即可**。
- **创建新页面**：直接打开 URL（例如 `http://cp2k.org/my_new_page`）然后点铅笔。
- 所用软件叫 **DokuWiki**，**很容易学**，官方提供 playground 页练习。

#### （3）贡献参考手册

- 官方指出：`http://manual.cp2k.org/trunk/` 上的小 **`[Edit]` 链接**是一个**新功能**，
  **让每个人都能轻松为 CP2K 文档做贡献**。
- 链接通向一个**提交文字修改的表单**，**经过简短审查后修改会出现在官方 cp2k-manual 中**。
- 官方列举：
  - **发现错别字，请改正**；
  - **如果终于弄懂了某个关键字怎么工作，请澄清它的描述**；
  - **如果想做出真正的改变，写一个引言性质的章节描述**。

#### （4）贡献代码

- **CP2K 源代码是公开可用的。** 可以**跟进开发并发送 patch**。
- 官方说明**也为新开发者提供了一些有用信息**。

> **[G层提示]** 这条 FAQ 是**"G 层文档为什么能持续更新"的机制说明**——
> 手册的 `[Edit]` 表单意味着**官方手册本身是社区可编辑的**。
> 结合 `12_authority_sources.md` 的权威性分级：**`[Edit]` 提交的内容经官方审查后进入手册**，
> 因此**已发布的手册页属 L1 权威**，而**待审提交不是**。

### 3.15 CP2K 的用户规模（faq:usagestats）

> 来源：`https://www.cp2k.org/faq:usagestats`（最后修改 2020/08/21）

**官方原文（重要，解释"为什么没有用户数"）**：

> **使用 CP2K 没有注册要求**，代码以多种方式自由可用。
> **这使得收集准确的用量统计变得困难。**
> 为向资助机构提供反馈，我们**因此看方法论文的引用量，或者看网站访问量**。

官方给出的网站访问信息入口：**Main site**、**Manual site**、**Downloads**。

> **[G层提示]** 这条说明**CP2K 官方不存在"注册用户数"这个口径**。
> 需要引用 CP2K 影响力时，**用方法论文引用量或官方 Dashboard**（见 `19_performance_gpu_community.md` §3）。

### 3.16 CP2K 名字的来历（faq:name）

> 来源：`https://www.cp2k.org/faq:name`（最后修改 2020/08/21）

**官方原文（原样照录）**：

> The name is derived from the CPMD code and the original meaning was the
> CP (Car-Parrinello = ab initio MD) code for the new Millenium.
> **Never mind that we didn't implement the CP method.**

**G 层直译**：这个名字**源自 CPMD 代码**，原意是**"新千年的 CP（Car-Parrinello = ab initio MD）代码"**。
**别在意我们其实并没有实现 CP 方法。**

> **[G层提示]** 这是一条**常被误解的常识**：
> **CP2K 的名字里有 Car-Parrinello，但从未实现 CP 方法。**
> CP2K 的 AIMD 走的是 **Born–Oppenheimer 路线**（`RUN_TYPE MD` + 每步 SCF），
> **不是 CPMD 的 Car-Parrinello 扩展拉格朗日路线**。
> 与 `04_sampling_md.md` 对照阅读。

### 3.17 如何正确向屏幕写信息（faq:doing_io）

> 来源：`https://www.cp2k.org/faq:doing_io`（最后修改 2020/08/21）

**官方原文**：

> When writing output in cp2k, to the screen or a file, one should use a **printkey**.

**G 层直译**：在 CP2K 中写输出（**到屏幕或文件**）时，**应当使用 printkey**。

> **[G层提示]** printkey 的完整机制（迭代层级、`FILENAME`、`&PRINT` 段）见
> `13_input_syntax_and_print.md`。**这是给开发者/改源码者的规则**，
> 普通用户写输入只需在 `&PRINT` 段里选 printkey。

---

## 4. 官方页面的已知缺口与过时项

| 项 | 状态 | 处置 |
|---|---|---|
| FAQ 页面整体最后修改于 2020/08/21 | **多数条目未随版本更新** | 使用时注意版本坐标 |
| `faq:common_mistakes` 称"CP2K 没有 k 点采样" | **已过时** | 见 §3.11 标注 |
| `faq:kpoints` 已改为跳转页 | 官方主动废弃 | 指向 manual |
| `faq:cuda_support` 无正文 | 仅跳转 | 见 `09_build_libraries.md` |
| `faq:hint_insufficiently_exploiting_cpu_extensions` | 未取正文 | 见 `09_build_libraries.md` |
| `faq:libsmm_arguments_too_long` | 未取正文 | 见 `09_build_libraries.md` |
| `faq:toolchain_non_zero_exit_code_detected` | 未取正文 | 见 `09_build_libraries.md` |
| `faq:contribute` / `faq:usagestats` / `faq:name` / `faq:doing_io` | **已取正文**（2026-09-09） | 见 §3.14–§3.17 |

> **维护提示**：FAQ 是 DokuWiki 页面，正文可能随时被改动。若某条内容与 Input Reference 冲突，**以 Input Reference 为准**。

---

## → 交叉索引

| 本文件内容 | 关联 A/F 层条目 | 关联 G 层文件 |
|---|---|---|
| SCF 不收敛 | A 层 decide.md、F 层 playbook.md | `03_scf_convergence.md` |
| CUTOFF 的"40 倍最大指数"经验 | — | `03_scf_convergence.md`（系统收敛教程） |
| `NGRIDS` 与 `exponent × REL_CUTOFF ≤ cutoff` | — | `03_scf_convergence.md`、`01_global_and_units.md`（`&MGRID`） |
| `CPASSERT` in `cp_fm_cholesky.F` → OT 预条件器 | A 层 decide.md OT 节 | `02_dft_methods.md` §3 |
| HFX `EPS_PGF_ORB` 警告 | — | `02_dft_methods.md` §6（HFX/ADMM） |
| `LSD` = `UKS`、`CHARGE`/`MULTIPLICITY` | A 层 decide.md 自旋设置 | `01_global_and_units.md` |
| 几何错误 / 邻接表 | F 层 playbook.md 建模检查 | `02_dft_methods.md`、`05_optimization.md` |
| k 点过时表述 | — | `02_dft_methods.md` §4、`07_restarting.md` §2 |
| MPI vs OpenMP | — | `09_build_libraries.md` |
| 引用 CP2K | — | `10_features_resources.md` |
