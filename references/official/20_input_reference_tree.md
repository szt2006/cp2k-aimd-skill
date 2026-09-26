# 20 · Input Reference 完整索引树（官方）

> 来源：
> - https://manual.cp2k.org/trunk/CP2K_INPUT.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/ATOM.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/EXT_RESTART.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/MULTIPLE_FORCE_EVALS.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/NEGF.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/SWARM.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/FARMING.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_BASIS.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_INPUT.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/TEST.html
> - https://manual.cp2k.org/trunk/CP2K_INPUT/DEBUG.html
> 抓取日期：2026-09-09；复核日期：2026-09-19（§8，`_kw_probe.py` 直查官方 `cp2k_input.xml`）
> 标注规则：`[默认]` = 官方 Input Reference 默认值；`[官方推荐]` = 官方正文明确推荐；`[示例]` = 官方示例取值；`[G层提示]` = G 层整理性说明（非官方原话）。

---

## 0. 本文件补什么

上一轮 G 层只覆盖了 `&GLOBAL` 的 38 个关键字和少量段，**Input Reference 的完整结构一直空白**。
本文件把 `manual.cp2k.org/trunk/CP2K_INPUT.html` 的**全部分层结构**（14 个顶层段 / 76 个第二层段 /
269 个第三层段，共 **359 个页面**）整理成可导航索引，并统计了各段的**直接关键字数量**（合计 **750 个**）。

> **[G层提示]** 本文件是**索引**，不是关键字默认值表。查某个关键字的具体默认值/类型/单位，
> 请按本文件给出的 URL 打开对应页面；G 层只在 `01_global_and_units.md` 逐条抄录了 `&GLOBAL` 的默认值。

## 1. 总览

| 项 | 数量 | 说明 |
|---|---|---|
| 顶层段 | **14** | `&GLOBAL`、`&FORCE_EVAL`、`&MOTION` 等 |
| 第二层段 | **76** | 顶层段的直接子段 |
| 第三层段 | **269** | 第二层段的子段（含少量更深层） |
| 页面总数 | **359** | 每个段一个页面 |
| 直接关键字合计 | **750** | 仅统计各段页面「Keywords」节列出的直接关键字 |

### 1.1 各顶层段规模（按直接关键字数排序）

| 顶层段 | 页面数 | 直接关键字 | 直接子段 | 用途 |
|---|---|---|---|---|
| `&MOTION` | 14 | 165 | 13 | MD / 几何优化 / 晶胞优化 / 约束 / 元动力学 / 路径（NEB） |
| `&TEST` | 11 | 120 | 10 | 库功能自检（编译后验证） |
| `&GLOBAL` | 10 | 99 | 9 | 全局运行参数（RUN_TYPE、打印、并行） |
| `&ATOM` | 9 | 85 | 8 | 原子级计算（孤立原子/伪原子，需 PROFILE） |
| `&FORCE_EVAL` | 15 | 54 | 14 | 能量与力：DFT/MM/QM-MM/NNP 等全部引擎 |
| `&NEGF` | 6 | 52 | 5 | 非平衡格林函数（输运） |
| `&EXT_RESTART` | 1 | 38 | 0 | 外部重启（从另一输入/文件续算） |
| `&OPTIMIZE_INPUT` | 5 | 35 | 4 | 输入参数自动优化 |
| `&OPTIMIZE_BASIS` | 6 | 30 | 5 | 基组自动优化（ADMM 类） |
| `&FARMING` | 4 | 27 | 3 | 批处理作业（多输入串跑） |
| `&DEBUG` | 2 | 17 | 1 | 调试与诊断输出 |
| `&VIBRATIONAL_ANALYSIS` | 3 | 16 | 2 | 简正模式 / 振动分析 / 声子 |
| `&SWARM` | 3 | 10 | 2 | 粒子群全局优化 |
| `&MULTIPLE_FORCE_EVALS` | 1 | 2 | 0 | 多 force_eval 并行（如 QM/MM 分区） |

> **[G层提示]** 页面数含顶层段自身，故 `FORCE_EVAL` 为 15 = 1（自身）+ 14（子段）。

## 2. 顶层段明细（含直接子段与直接关键字）

### `&GLOBAL`

> Section with general information on which kind of simulation to perform and parameters for the whole PROGRAM [Edit on GitHub]

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL.html>
- 直接子段（9）：`&DBCSR`、`&FM`、`&FM_DIAG_SETTINGS`、`&GRID`、`&PREFERRED_INTEGRAL_LIBRARY`、`&PRINT`、`&PROGRAM_RUN_INFO`、`&REFERENCES`、`&TIMINGS`
- 直接关键字（38）：`ALLTOALL_SGL`、`BLACS_GRID`、`BLACS_REPEATABLE`、`CALLGRAPH`、`CALLGRAPH_FILE_NAME`、`DIRECT_GENERALIZED_DIAGONALIZATION`、`DLAF_CHOLESKY_N_MIN`、`DLAF_NEIGVEC_MIN`、`ECHO_ALL_HOSTS`、`ECHO_INPUT`、`ELPA_COMPLEX_KERNEL`、`ELPA_KERNEL`、`ELPA_NEIGVEC_MIN`、`ELPA_ONE_STAGE`、`ELPA_PRINT`、`ELPA_QR`、`ENABLE_MPI_IO`、`EPS_CHECK_DIAG`、`FFTW_PLAN_TYPE`、`FFTW_WISDOM_FILE_NAME`、`FFT_POOL_SCRATCH_LIMIT`、`FLUSH_SHOULD_FLUSH`、`OUTPUT_FILE_NAME`、`PREFERRED_CHOLESKY_LIBRARY`、`PREFERRED_DGEMM_LIBRARY`、`PREFERRED_DIAG_LIBRARY`、`PREFERRED_FFT_LIBRARY`、`PRINT_LEVEL`、`PROGRAM_NAME`、`PROJECT_NAME`、`RUN_TYPE`、`SAVE_MEM`、`SEED`、`TRACE`、`TRACE_MASTER`、`TRACE_MAX`、`TRACE_ROUTINES`、`WALLTIME`

### `&FORCE_EVAL`

> Section can be repeated.

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL.html>
- 直接子段（14）：`&BSSE`、`&DFT`、`&EIP`、`&EMBED`、`&EXTERNAL_POTENTIAL`、`&MIXED`、`&MM`、`&NNP`、`&PRINT`、`&PROPERTIES`、`&PW_DFT`、`&QMMM`、`&RESCALE_FORCES`、`&SUBSYS`
- 直接关键字（2）：`METHOD`、`STRESS_TENSOR`

### `&MOTION`

> This section defines a set of tool connected with the motion of the nuclei. [Edit on GitHub]

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION.html>
- 直接子段（13）：`&BAND`、`&CELL_OPT`、`&CONSTRAINT`、`&DRIVER`、`&FLEXIBLE_PARTITIONING`、`&FREE_ENERGY`、`&GEO_OPT`、`&MC`、`&MD`、`&PINT`、`&PRINT`、`&SHELL_OPT`、`&TMC`
- 直接关键字（0）：（无，见子段）

### `&ATOM`

> Section handling input for atomic calculations (requires &GLOBAL%PROGRAM_NAME ATOM). [Edit on GitHub]

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/ATOM.html>
- 直接子段（8）：`&AE_BASIS`、`&METHOD`、`&OPTIMIZATION`、`&POTENTIAL`、`&POWELL`、`&PP_BASIS`、`&PRINT`、`&REFERENCE`
- 直接关键字（11）：`ATOMIC_NUMBER`、`CALCULATE_STATES`、`CORE`、`COULOMB_INTEGRALS`、`ELECTRON_CONFIGURATION`、`ELEMENT`、`EXCHANGE_INTEGRALS`、`GRID_POINTS_GH`、`MAX_ANGULAR_MOMENTUM`、`RUN_TYPE`、`USE_GAUSS_HERMITE`

### `&VIBRATIONAL_ANALYSIS`

> Section to setup parameters to perform a Normal Modes, vibrational, or phonon analysis. Vibrations are computed using finite differences, which implies a very tight (e.g. 1E-8) threshold is needed for EPS_SCF to get accurate low frequencies. The analysis assumes a stationary state (minimum or TS), i.e. tight geometry optimization (MAX_FORCE) is needed as well. [Edit on GitHub]

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html>
- 直接子段（2）：`&MODE_SELECTIVE`、`&PRINT`
- 直接关键字（8）：`DX`、`FULLY_PERIODIC`、`INTENSITIES`、`NPROC_REP`、`PROC_DIST_TYPE`、`TC_PRESSURE`、`TC_TEMPERATURE`、`THERMOCHEMISTRY`

### `&EXT_RESTART`

> Section for external restart, specifies an external input file where to take positions, etc. By default they are all set to TRUE [Edit on GitHub]

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/EXT_RESTART.html>
- 直接子段（0）：（无）
- 直接关键字（38）：`BINARY_RESTART_FILE_NAME`、`CUSTOM_PATH`、`RESTART_AVERAGES`、`RESTART_BAND`、`RESTART_BAROSTAT`、`RESTART_BAROSTAT_THERMOSTAT`、`RESTART_BSSE`、`RESTART_CELL`、`RESTART_CONSTRAINT`、`RESTART_CORE_POS`、`RESTART_CORE_VELOCITY`、`RESTART_COUNTERS`、`RESTART_DEFAULT`、`RESTART_DIMER`、`RESTART_FILE_NAME`、`RESTART_HELIUM_AVERAGES`、`RESTART_HELIUM_DENSITIES`、`RESTART_HELIUM_FORCE`、`RESTART_HELIUM_PERMUTATION`、`RESTART_HELIUM_POS`、`RESTART_HELIUM_RNG`、`RESTART_METADYNAMICS`、`RESTART_OPTIMIZE_INPUT_VARIABLES`、`RESTART_PINT_GLE`、`RESTART_PINT_NOSE`、`RESTART_PINT_POS`、`RESTART_PINT_VEL`、`RESTART_POS`、`RESTART_QMMM`、`RESTART_RANDOMG`、`RESTART_RTP`、`RESTART_SHELL_POS`、`RESTART_SHELL_THERMOSTAT`、`RESTART_SHELL_VELOCITY`、`RESTART_TEMPERATURE_ANNEALING`、`RESTART_THERMOSTAT`、`RESTART_VEL`、`RESTART_WALKERS`

### `&MULTIPLE_FORCE_EVALS`

> Describes how to handle multiple force_evals. [Edit on GitHub]

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/MULTIPLE_FORCE_EVALS.html>
- 直接子段（0）：（无）
- 直接关键字（2）：`FORCE_EVAL_ORDER`、`MULTIPLE_SUBSYS`

### `&NEGF`

> References: Rocha2006b, Papior2017

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/NEGF.html>
- 直接子段（5）：`&CONTACT`、`&MIXING`、`&PRINT`、`&SCATTERING_REGION`、`&SCF`
- 直接关键字（18）：`DELTA_NPOLES`、`DISABLE_CACHE`、`ENERGY_LBOUND`、`EPS_DENSITY`、`EPS_GEO`、`EPS_GREEN`、`EPS_SCF`、`ETA`、`GAMMA_KT`、`HOMO_LUMO_GAP`、`INTEGRATION_MAX_POINTS`、`INTEGRATION_METHOD`、`INTEGRATION_MIN_POINTS`、`MAX_SCF`、`NPROC_POINT`、`V_SHIFT`、`V_SHIFT_MAX_ITERS`、`V_SHIFT_OFFSET`

### `&SWARM`

> Section to control swarm runs. The swarm framework provides a common ground for master/worker algorithms. [Edit on GitHub]

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/SWARM.html>
- 直接子段（2）：`&GLOBAL_OPT`、`&PRINT`
- 直接关键字（4）：`BEHAVIOR`、`MAX_ITER`、`NUMBER_OF_WORKERS`、`REPLAY_COMMUNICATION_LOG`

### `&FARMING`

> Describes a farming job, in which multiple inputs are executed. The RUN_TYPE in the global section has to be set to NONE for FARMING. The different groups are executed in parallel. The jobs inside the same groups in series. [Edit on GitHub]

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/FARMING.html>
- 直接子段（3）：`&JOB`、`&PROGRAM_RUN_INFO`、`&RESTART`
- 直接关键字（10）：`CAPTAIN_MINION`、`CYCLE`、`DO_RESTART`、`GROUP_PARTITION`、`GROUP_SIZE`、`MAX_JOBS_PER_GROUP`、`NGROUPS`、`RESTART_FILE_NAME`、`STRIDE`、`WAIT_TIME`

### `&OPTIMIZE_BASIS`

> describes a basis optimization job, in which an ADMM like approach is used to find the best exponents and/or coefficients to match a given training set. [Edit on GitHub]

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_BASIS.html>
- 直接子段（5）：`&FIT_KIND`、`&FRONTIER_ORBITALS`、`&FRONTIER_ORBITAL_SCREENING`、`&OPTIMIZATION`、`&TRAINING_FILES`
- 直接关键字（9）：`BASIS_COMBINATIONS`、`BASIS_OUTPUT_FILE`、`BASIS_TEMPLATE_FILE`、`BASIS_WORK_FILE`、`CONDITION_WEIGHT`、`GROUP_PARTITION`、`RESIDUUM_WEIGHT`、`USE_CONDITION_NUMBER`、`WRITE_FREQUENCY`

### `&OPTIMIZE_INPUT`

> describes an input optimization job, in which parameters in input files get optimized. [Edit on GitHub]

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_INPUT.html>
- 直接子段（4）：`&FORCE_MATCHING`、`&HISTORY`、`&RESTART`、`&VARIABLE`
- 直接关键字（6）：`ACCURACY`、`ITER_START_VAL`、`MAX_FUN`、`METHOD`、`RANDOMIZE_VARIABLES`、`STEP_SIZE`

### `&TEST`

> Tests to perform on the supported libraries. [Edit on GitHub]

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/TEST.html>
- 直接子段（10）：`&CP_DBCSR`、`&CP_FM_GEMM`、`&DBM`、`&EIGENSOLVER`、`&ERI_MME_TEST`、`&GRID_INFORMATION`、`&PROGRAM_RUN_INFO`、`&PW_TRANSFER`、`&RS_PW_TRANSFER`、`&SHG_INTEGRALS_TEST`
- 直接关键字（10）：`CLEBSCH_GORDON`、`COPY`、`DGEMM`、`ERI`、`FFT`、`LEAST_SQ_FT`、`MATMUL`、`MEMORY`、`MINIMAX`、`MPI`

### `&DEBUG`

> Section to setup parameters for debug runs. [Edit on GitHub]

- 页面：<https://manual.cp2k.org/trunk/CP2K_INPUT/DEBUG.html>
- 直接子段（1）：`&PROGRAM_RUN_INFO`
- 直接关键字（11）：`CHECK_ATOM_FORCE`、`CHECK_DIPOLE_DIRS`、`DE`、`DEBUG_DIPOLE`、`DEBUG_FORCES`、`DEBUG_POLARIZABILITY`、`DEBUG_STRESS_TENSOR`、`DX`、`EPS_NO_ERROR_CHECK`、`MAX_RELATIVE_ERROR`、`STOP_ON_MISMATCH`

## 3. 第二层段索引（76 个）

| 第二层段 | 直接关键字 | 第三层子段 | 页面 |
|---|---|---|---|
| `&GLOBAL/DBCSR` | 13 | `&ACC`、`&TENSOR` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL/DBCSR.html) |
| `&GLOBAL/FM` | 4 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL/FM.html) |
| `&GLOBAL/FM_DIAG_SETTINGS` | 4 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL/FM_DIAG_SETTINGS.html) |
| `&GLOBAL/GRID` | 3 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL/GRID.html) |
| `&GLOBAL/PREFERRED_INTEGRAL_LIBRARY` | 2 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL/PREFERRED_INTEGRAL_LIBRARY.html) |
| `&GLOBAL/PRINT` | 12 | `&EACH` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL/PRINT.html) |
| `&GLOBAL/PROGRAM_RUN_INFO` | 6 | `&EACH` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL/PROGRAM_RUN_INFO.html) |
| `&GLOBAL/REFERENCES` | 6 | `&EACH` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL/REFERENCES.html) |
| `&GLOBAL/TIMINGS` | 11 | `&EACH` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL/TIMINGS.html) |
| `&FORCE_EVAL/BSSE` | 0 | `&CONFIGURATION`、`&FRAGMENT`、`&FRAGMENT_ENERGIES`、`&PRINT` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/BSSE.html) |
| `&FORCE_EVAL/DFT` | 19 | `&ACTIVE_SPACE`、`&ALMO_SCF`、`&AUXILIARY_DENSITY_MATRIX_METHOD`、`&DENSITY_FITTING`、`&EFIELD`、`&ENERGY_CORRECTION`、`&EXCITED_STATES`、`&EXTERNAL_DENSITY`、`&EXTERNAL_POTENTIAL`、`&EXTERNAL_VXC`、`&HAIRY_PROBES`、`&HARRIS_METHOD`、`&KG_METHOD`、`&KPOINTS`、`&KPOINT_SET`、`&LOCALIZE`、`&LOW_SPIN_ROKS`、`&LS_SCF`、`&MGRID`、`&PERIODIC_EFIELD`、`&PLANAR_AVERAGED_V_HARTREE`、`&PLANAR_COUNTER_CHARGE`、`&POISSON`、`&PRINT`、`&QS`、`&REAL_TIME_PROPAGATION`、`&RELATIVISTIC`、`&SCCS`、`&SCF`、`&SCRF`、`&SIC`、`&SMEAGOL`、`&TRANSPORT`、`&XAS`、`&XAS_TDP`、`&XC` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/DFT.html) |
| `&FORCE_EVAL/EIP` | 1 | `&PRINT` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/EIP.html) |
| `&FORCE_EVAL/EMBED` | 3 | `&MAPPING`、`&PRINT` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/EMBED.html) |
| `&FORCE_EVAL/EXTERNAL_POTENTIAL` | 7 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/EXTERNAL_POTENTIAL.html) |
| `&FORCE_EVAL/MIXED` | 3 | `&COUPLING`、`&GENERIC`、`&LINEAR`、`&MAPPING`、`&MIXED_CDFT`、`&PRINT`、`&RESTRAINT` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/MIXED.html) |
| `&FORCE_EVAL/MM` | 0 | `&FORCEFIELD`、`&NEIGHBOR_LISTS`、`&PERIODIC_EFIELD`、`&POISSON`、`&PRINT` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/MM.html) |
| `&FORCE_EVAL/NNP` | 4 | `&BIAS`、`&MODEL`、`&PRINT` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/NNP.html) |
| `&FORCE_EVAL/PRINT` | 0 | `&DISTRIBUTION`、`&DISTRIBUTION1D`、`&DISTRIBUTION2D`、`&FORCES`、`&GRID_INFORMATION`、`&GRRM`、`&PROGRAM_RUN_INFO`、`&SCINE`、`&STRESS_TENSOR`、`&TOTAL_NUMBERS` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/PRINT.html) |
| `&FORCE_EVAL/PROPERTIES` | 0 | `&ATOMIC`、`&BANDSTRUCTURE`、`&ET_COUPLING`、`&FIT_CHARGE`、`&KUBO_TRANSPORT`、`&LINRES`、`&RESP`、`&RIXS`、`&TDDFPT`、`&TIP_SCAN` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/PROPERTIES.html) |
| `&FORCE_EVAL/PW_DFT` | 1 | `&CONTROL`、`&ITERATIVE_SOLVER`、`&MIXER`、`&PARAMETERS`、`&PRINT`、`&SETTINGS` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/PW_DFT.html) |
| `&FORCE_EVAL/QMMM` | 12 | `&CELL`、`&FORCEFIELD`、`&FORCE_MIXING`、`&IMAGE_CHARGE`、`&INTERPOLATOR`、`&LINK`、`&MM_KIND`、`&PERIODIC`、`&PRINT`、`&QM_KIND`、`&WALLS` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/QMMM.html) |
| `&FORCE_EVAL/RESCALE_FORCES` | 1 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/RESCALE_FORCES.html) |
| `&FORCE_EVAL/SUBSYS` | 1 | `&CELL`、`&COLVAR`、`&COORD`、`&CORE_COORD`、`&CORE_VELOCITY`、`&KIND`、`&MULTIPOLES`、`&PRINT`、`&RNG_INIT`、`&SHELL_COORD`、`&SHELL_VELOCITY`、`&TOPOLOGY`、`&VELOCITY` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/SUBSYS.html) |
| `&MOTION/BAND` | 9 | `&BANNER`、`&CI_NEB`、`&CONVERGENCE_CONTROL`、`&CONVERGENCE_INFO`、`&ENERGY`、`&FINAL_BAND`、`&OPTIMIZE_BAND`、`&PROGRAM_RUN_INFO`、`&REPLICA`、`&REPLICA_INFO`、`&STRING_METHOD` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/BAND.html) |
| `&MOTION/CELL_OPT` | 19 | `&BFGS`、`&CG`、`&LBFGS`、`&PRINT` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/CELL_OPT.html) |
| `&MOTION/CONSTRAINT` | 4 | `&COLLECTIVE`、`&COLVAR_RESTART`、`&CONSTRAINT_INFO`、`&FIXED_ATOMS`、`&FIX_ATOM_RESTART`、`&G3X3`、`&G4X6`、`&HBONDS`、`&LAGRANGE_MULTIPLIERS`、`&VIRTUAL_SITE` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/CONSTRAINT.html) |
| `&MOTION/DRIVER` | 5 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/DRIVER.html) |
| `&MOTION/FLEXIBLE_PARTITIONING` | 9 | `&CONTROL`、`&WEIGHTS` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/FLEXIBLE_PARTITIONING.html) |
| `&MOTION/FREE_ENERGY` | 1 | `&ALCHEMICAL_CHANGE`、`&FREE_ENERGY_INFO`、`&METADYN`、`&UMBRELLA_INTEGRATION` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/FREE_ENERGY.html) |
| `&MOTION/GEO_OPT` | 14 | `&BFGS`、`&CG`、`&LBFGS`、`&PRINT`、`&TRANSITION_STATE` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/GEO_OPT.html) |
| `&MOTION/MC` | 26 | `&AVBMC`、`&MAX_DISPLACEMENTS`、`&MOVE_PROBABILITIES`、`&MOVE_UPDATES` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/MC.html) |
| `&MOTION/MD` | 19 | `&ADIABATIC_DYNAMICS`、`&AVERAGES`、`&BAROSTAT`、`&CASCADE`、`&INITIAL_VIBRATION`、`&LANGEVIN`、`&MSST`、`&PRINT`、`&REFTRAJ`、`&RESPA`、`&SHELL`、`&THERMAL_REGION`、`&THERMOSTAT`、`&VELOCITY_SOFTENING` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/MD.html) |
| `&MOTION/PINT` | 14 | `&BEADS`、`&GLE`、`&HELIUM`、`&INIT`、`&NORMALMODE`、`&NOSE`、`&PIGLET`、`&PILE`、`&PRINT`、`&QTB`、`&STAGING` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/PINT.html) |
| `&MOTION/PRINT` | 1 | `&CELL`、`&CORE_FORCES`、`&CORE_TRAJECTORY`、`&CORE_VELOCITIES`、`&FINAL_STRUCTURE`、`&FORCES`、`&FORCE_MIXING_LABELS`、`&MIXED_ENERGIES`、`&POLAR_MATRIX`、`&RESTART`、`&RESTART_HISTORY`、`&SHELL_FORCES`、`&SHELL_TRAJECTORY`、`&SHELL_VELOCITIES`、`&STRESS`、`&STRUCTURE_DATA`、`&TRAJECTORY`、`&TRANSLATION_VECTOR`、`&VELOCITIES` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/PRINT.html) |
| `&MOTION/SHELL_OPT` | 13 | `&BFGS`、`&CG`、`&LBFGS`、`&PRINT` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/SHELL_OPT.html) |
| `&MOTION/TMC` | 31 | `&MOVE_TYPE`、`&NMC_MOVES`、`&TMC_ANALYSIS`、`&TMC_ANALYSIS_FILES` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/TMC.html) |
| `&ATOM/AE_BASIS` | 19 | `&BASIS` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/ATOM/AE_BASIS.html) |
| `&ATOM/METHOD` | 2 | `&EXTERNAL_VXC`、`&XC`、`&ZMP` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/ATOM/METHOD.html) |
| `&ATOM/OPTIMIZATION` | 5 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/ATOM/OPTIMIZATION.html) |
| `&ATOM/POTENTIAL` | 5 | `&ECP`、`&GTH_POTENTIAL` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/ATOM/POTENTIAL.html) |
| `&ATOM/POWELL` | 22 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/ATOM/POWELL.html) |
| `&ATOM/PP_BASIS` | 19 | `&BASIS` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/ATOM/PP_BASIS.html) |
| `&ATOM/PRINT` | 0 | `&ADMM`、`&ANALYZE_BASIS`、`&BASIS_SET`、`&FIT_BASIS`、`&FIT_DENSITY`、`&FIT_KGPOT`、`&FIT_PSEUDO`、`&GEOMETRICAL_RESPONSE_BASIS`、`&METHOD_INFO`、`&ORBITALS`、`&POTENTIAL`、`&PROGRAM_BANNER`、`&RESPONSE_BASIS`、`&SCF_INFO`、`&SEPARABLE_GAUSSIAN_PSEUDO`、`&UPF_FILE` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/ATOM/PRINT.html) |
| `&ATOM/REFERENCE` | 2 | `&POTENTIAL` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/ATOM/REFERENCE.html) |
| `&VIBRATIONAL_ANALYSIS/MODE_SELECTIVE` | 8 | `&INVOLVED_ATOMS`、`&PRINT` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/VIBRATIONAL_ANALYSIS/MODE_SELECTIVE.html) |
| `&VIBRATIONAL_ANALYSIS/PRINT` | 0 | `&BANNER`、`&CARTESIAN_EIGS`、`&HESSIAN`、`&MOLDEN_VIB`、`&NAMD_PRINT`、`&PROGRAM_RUN_INFO`、`&ROTATIONAL_INFO` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/VIBRATIONAL_ANALYSIS/PRINT.html) |
| `&NEGF/CONTACT` | 6 | `&BULK_REGION`、`&PRINT`、`&RESTART`、`&SCREENING_REGION` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/NEGF/CONTACT.html) |
| `&NEGF/MIXING` | 23 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/NEGF/MIXING.html) |
| `&NEGF/PRINT` | 1 | `&DOS`、`&PROGRAM_RUN_INFO`、`&RESTART`、`&TRANSMISSION` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/NEGF/PRINT.html) |
| `&NEGF/SCATTERING_REGION` | 2 | `&RESTART` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/NEGF/SCATTERING_REGION.html) |
| `&NEGF/SCF` | 2 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/NEGF/SCF.html) |
| `&SWARM/GLOBAL_OPT` | 6 | `&HISTORY`、`&MINIMA_CRAWLING`、`&MINIMA_HOPPING`、`&PROGRESS_TRAJECTORY` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/SWARM/GLOBAL_OPT.html) |
| `&SWARM/PRINT` | 0 | `&COMMUNICATION_LOG`、`&MASTER_RUN_INFO`、`&WORKER_RUN_INFO` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/SWARM/PRINT.html) |
| `&FARMING/JOB` | 5 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FARMING/JOB.html) |
| `&FARMING/PROGRAM_RUN_INFO` | 6 | `&EACH` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FARMING/PROGRAM_RUN_INFO.html) |
| `&FARMING/RESTART` | 6 | `&EACH` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/FARMING/RESTART.html) |
| `&OPTIMIZE_BASIS/FIT_KIND` | 7 | `&CONSTRAIN_EXPONENTS`、`&DERIVED_BASIS_SETS` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_BASIS/FIT_KIND.html) |
| `&OPTIMIZE_BASIS/FRONTIER_ORBITALS` | 8 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_BASIS/FRONTIER_ORBITALS.html) |
| `&OPTIMIZE_BASIS/FRONTIER_ORBITAL_SCREENING` | 1 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_BASIS/FRONTIER_ORBITAL_SCREENING.html) |
| `&OPTIMIZE_BASIS/OPTIMIZATION` | 3 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_BASIS/OPTIMIZATION.html) |
| `&OPTIMIZE_BASIS/TRAINING_FILES` | 2 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_BASIS/TRAINING_FILES.html) |
| `&OPTIMIZE_INPUT/FORCE_MATCHING` | 13 | `&COMPARE_ENERGIES`、`&COMPARE_FORCES` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_INPUT/FORCE_MATCHING.html) |
| `&OPTIMIZE_INPUT/HISTORY` | 6 | `&EACH` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_INPUT/HISTORY.html) |
| `&OPTIMIZE_INPUT/RESTART` | 7 | `&EACH` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_INPUT/RESTART.html) |
| `&OPTIMIZE_INPUT/VARIABLE` | 3 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/OPTIMIZE_INPUT/VARIABLE.html) |
| `&TEST/CP_DBCSR` | 23 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/TEST/CP_DBCSR.html) |
| `&TEST/CP_FM_GEMM` | 11 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/TEST/CP_FM_GEMM.html) |
| `&TEST/DBM` | 17 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/TEST/DBM.html) |
| `&TEST/EIGENSOLVER` | 5 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/TEST/EIGENSOLVER.html) |
| `&TEST/ERI_MME_TEST` | 14 | `&ERI_MME` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/TEST/ERI_MME_TEST.html) |
| `&TEST/GRID_INFORMATION` | 6 | `&EACH` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/TEST/GRID_INFORMATION.html) |
| `&TEST/PROGRAM_RUN_INFO` | 6 | `&EACH` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/TEST/PROGRAM_RUN_INFO.html) |
| `&TEST/PW_TRANSFER` | 7 | — | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/TEST/PW_TRANSFER.html) |
| `&TEST/RS_PW_TRANSFER` | 4 | `&RS_GRID` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/TEST/RS_PW_TRANSFER.html) |
| `&TEST/SHG_INTEGRALS_TEST` | 17 | `&BASIS` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/TEST/SHG_INTEGRALS_TEST.html) |
| `&DEBUG/PROGRAM_RUN_INFO` | 6 | `&EACH` | [链接](https://manual.cp2k.org/trunk/CP2K_INPUT/DEBUG/PROGRAM_RUN_INFO.html) |

## 4. 第三层段清单（269 个，按父段分组）

> **[G层提示]** 第三层段多为打印/收敛/算法子选项，日常写输入很少直接用到；
> 需要时按父段 URL 拼路径访问，例如 `&MOTION/&MD/&THERMOSTAT` →
> <https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/MD/THERMOSTAT.html>

**`&GLOBAL/DBCSR`**（2）：`&ACC`、`&TENSOR`

**`&GLOBAL/PRINT`**（1）：`&EACH`

**`&GLOBAL/PROGRAM_RUN_INFO`**（1）：`&EACH`

**`&GLOBAL/REFERENCES`**（1）：`&EACH`

**`&GLOBAL/TIMINGS`**（1）：`&EACH`

**`&FORCE_EVAL/BSSE`**（4）：`&CONFIGURATION`、`&FRAGMENT`、`&FRAGMENT_ENERGIES`、`&PRINT`

**`&FORCE_EVAL/DFT`**（36）：`&ACTIVE_SPACE`、`&ALMO_SCF`、`&AUXILIARY_DENSITY_MATRIX_METHOD`、`&DENSITY_FITTING`、`&EFIELD`、`&ENERGY_CORRECTION`、`&EXCITED_STATES`、`&EXTERNAL_DENSITY`、`&EXTERNAL_POTENTIAL`、`&EXTERNAL_VXC`、`&HAIRY_PROBES`、`&HARRIS_METHOD`、`&KG_METHOD`、`&KPOINTS`、`&KPOINT_SET`、`&LOCALIZE`、`&LOW_SPIN_ROKS`、`&LS_SCF`、`&MGRID`、`&PERIODIC_EFIELD`、`&PLANAR_AVERAGED_V_HARTREE`、`&PLANAR_COUNTER_CHARGE`、`&POISSON`、`&PRINT`、`&QS`、`&REAL_TIME_PROPAGATION`、`&RELATIVISTIC`、`&SCCS`、`&SCF`、`&SCRF`、`&SIC`、`&SMEAGOL`、`&TRANSPORT`、`&XAS`、`&XAS_TDP`、`&XC`

**`&FORCE_EVAL/EIP`**（1）：`&PRINT`

**`&FORCE_EVAL/EMBED`**（2）：`&MAPPING`、`&PRINT`

**`&FORCE_EVAL/MIXED`**（7）：`&COUPLING`、`&GENERIC`、`&LINEAR`、`&MAPPING`、`&MIXED_CDFT`、`&PRINT`、`&RESTRAINT`

**`&FORCE_EVAL/MM`**（5）：`&FORCEFIELD`、`&NEIGHBOR_LISTS`、`&PERIODIC_EFIELD`、`&POISSON`、`&PRINT`

**`&FORCE_EVAL/NNP`**（3）：`&BIAS`、`&MODEL`、`&PRINT`

**`&FORCE_EVAL/PRINT`**（10）：`&DISTRIBUTION`、`&DISTRIBUTION1D`、`&DISTRIBUTION2D`、`&FORCES`、`&GRID_INFORMATION`、`&GRRM`、`&PROGRAM_RUN_INFO`、`&SCINE`、`&STRESS_TENSOR`、`&TOTAL_NUMBERS`

**`&FORCE_EVAL/PROPERTIES`**（10）：`&ATOMIC`、`&BANDSTRUCTURE`、`&ET_COUPLING`、`&FIT_CHARGE`、`&KUBO_TRANSPORT`、`&LINRES`、`&RESP`、`&RIXS`、`&TDDFPT`、`&TIP_SCAN`

**`&FORCE_EVAL/PW_DFT`**（6）：`&CONTROL`、`&ITERATIVE_SOLVER`、`&MIXER`、`&PARAMETERS`、`&PRINT`、`&SETTINGS`

**`&FORCE_EVAL/QMMM`**（11）：`&CELL`、`&FORCEFIELD`、`&FORCE_MIXING`、`&IMAGE_CHARGE`、`&INTERPOLATOR`、`&LINK`、`&MM_KIND`、`&PERIODIC`、`&PRINT`、`&QM_KIND`、`&WALLS`

**`&FORCE_EVAL/SUBSYS`**（13）：`&CELL`、`&COLVAR`、`&COORD`、`&CORE_COORD`、`&CORE_VELOCITY`、`&KIND`、`&MULTIPOLES`、`&PRINT`、`&RNG_INIT`、`&SHELL_COORD`、`&SHELL_VELOCITY`、`&TOPOLOGY`、`&VELOCITY`

**`&MOTION/BAND`**（11）：`&BANNER`、`&CI_NEB`、`&CONVERGENCE_CONTROL`、`&CONVERGENCE_INFO`、`&ENERGY`、`&FINAL_BAND`、`&OPTIMIZE_BAND`、`&PROGRAM_RUN_INFO`、`&REPLICA`、`&REPLICA_INFO`、`&STRING_METHOD`

**`&MOTION/CELL_OPT`**（4）：`&BFGS`、`&CG`、`&LBFGS`、`&PRINT`

**`&MOTION/CONSTRAINT`**（10）：`&COLLECTIVE`、`&COLVAR_RESTART`、`&CONSTRAINT_INFO`、`&FIXED_ATOMS`、`&FIX_ATOM_RESTART`、`&G3X3`、`&G4X6`、`&HBONDS`、`&LAGRANGE_MULTIPLIERS`、`&VIRTUAL_SITE`

**`&MOTION/FLEXIBLE_PARTITIONING`**（2）：`&CONTROL`、`&WEIGHTS`

**`&MOTION/FREE_ENERGY`**（4）：`&ALCHEMICAL_CHANGE`、`&FREE_ENERGY_INFO`、`&METADYN`、`&UMBRELLA_INTEGRATION`

**`&MOTION/GEO_OPT`**（5）：`&BFGS`、`&CG`、`&LBFGS`、`&PRINT`、`&TRANSITION_STATE`

**`&MOTION/MC`**（4）：`&AVBMC`、`&MAX_DISPLACEMENTS`、`&MOVE_PROBABILITIES`、`&MOVE_UPDATES`

**`&MOTION/MD`**（14）：`&ADIABATIC_DYNAMICS`、`&AVERAGES`、`&BAROSTAT`、`&CASCADE`、`&INITIAL_VIBRATION`、`&LANGEVIN`、`&MSST`、`&PRINT`、`&REFTRAJ`、`&RESPA`、`&SHELL`、`&THERMAL_REGION`、`&THERMOSTAT`、`&VELOCITY_SOFTENING`

**`&MOTION/PINT`**（11）：`&BEADS`、`&GLE`、`&HELIUM`、`&INIT`、`&NORMALMODE`、`&NOSE`、`&PIGLET`、`&PILE`、`&PRINT`、`&QTB`、`&STAGING`

**`&MOTION/PRINT`**（19）：`&CELL`、`&CORE_FORCES`、`&CORE_TRAJECTORY`、`&CORE_VELOCITIES`、`&FINAL_STRUCTURE`、`&FORCES`、`&FORCE_MIXING_LABELS`、`&MIXED_ENERGIES`、`&POLAR_MATRIX`、`&RESTART`、`&RESTART_HISTORY`、`&SHELL_FORCES`、`&SHELL_TRAJECTORY`、`&SHELL_VELOCITIES`、`&STRESS`、`&STRUCTURE_DATA`、`&TRAJECTORY`、`&TRANSLATION_VECTOR`、`&VELOCITIES`

**`&MOTION/SHELL_OPT`**（4）：`&BFGS`、`&CG`、`&LBFGS`、`&PRINT`

**`&MOTION/TMC`**（4）：`&MOVE_TYPE`、`&NMC_MOVES`、`&TMC_ANALYSIS`、`&TMC_ANALYSIS_FILES`

**`&ATOM/AE_BASIS`**（1）：`&BASIS`

**`&ATOM/METHOD`**（3）：`&EXTERNAL_VXC`、`&XC`、`&ZMP`

**`&ATOM/POTENTIAL`**（2）：`&ECP`、`&GTH_POTENTIAL`

**`&ATOM/PP_BASIS`**（1）：`&BASIS`

**`&ATOM/PRINT`**（16）：`&ADMM`、`&ANALYZE_BASIS`、`&BASIS_SET`、`&FIT_BASIS`、`&FIT_DENSITY`、`&FIT_KGPOT`、`&FIT_PSEUDO`、`&GEOMETRICAL_RESPONSE_BASIS`、`&METHOD_INFO`、`&ORBITALS`、`&POTENTIAL`、`&PROGRAM_BANNER`、`&RESPONSE_BASIS`、`&SCF_INFO`、`&SEPARABLE_GAUSSIAN_PSEUDO`、`&UPF_FILE`

**`&ATOM/REFERENCE`**（1）：`&POTENTIAL`

**`&VIBRATIONAL_ANALYSIS/MODE_SELECTIVE`**（2）：`&INVOLVED_ATOMS`、`&PRINT`

**`&VIBRATIONAL_ANALYSIS/PRINT`**（7）：`&BANNER`、`&CARTESIAN_EIGS`、`&HESSIAN`、`&MOLDEN_VIB`、`&NAMD_PRINT`、`&PROGRAM_RUN_INFO`、`&ROTATIONAL_INFO`

**`&NEGF/CONTACT`**（4）：`&BULK_REGION`、`&PRINT`、`&RESTART`、`&SCREENING_REGION`

**`&NEGF/PRINT`**（4）：`&DOS`、`&PROGRAM_RUN_INFO`、`&RESTART`、`&TRANSMISSION`

**`&NEGF/SCATTERING_REGION`**（1）：`&RESTART`

**`&SWARM/GLOBAL_OPT`**（4）：`&HISTORY`、`&MINIMA_CRAWLING`、`&MINIMA_HOPPING`、`&PROGRESS_TRAJECTORY`

**`&SWARM/PRINT`**（3）：`&COMMUNICATION_LOG`、`&MASTER_RUN_INFO`、`&WORKER_RUN_INFO`

**`&FARMING/PROGRAM_RUN_INFO`**（1）：`&EACH`

**`&FARMING/RESTART`**（1）：`&EACH`

**`&OPTIMIZE_BASIS/FIT_KIND`**（2）：`&CONSTRAIN_EXPONENTS`、`&DERIVED_BASIS_SETS`

**`&OPTIMIZE_INPUT/FORCE_MATCHING`**（2）：`&COMPARE_ENERGIES`、`&COMPARE_FORCES`

**`&OPTIMIZE_INPUT/HISTORY`**（1）：`&EACH`

**`&OPTIMIZE_INPUT/RESTART`**（1）：`&EACH`

**`&TEST/ERI_MME_TEST`**（1）：`&ERI_MME`

**`&TEST/GRID_INFORMATION`**（1）：`&EACH`

**`&TEST/PROGRAM_RUN_INFO`**（1）：`&EACH`

**`&TEST/RS_PW_TRANSFER`**（1）：`&RS_GRID`

**`&TEST/SHG_INTEGRALS_TEST`**（1）：`&BASIS`

**`&DEBUG/PROGRAM_RUN_INFO`**（1）：`&EACH`

## 5. 怎么用这棵树（实操路径）

| 你的问题 | 走哪条路 |
|---|---|
| "`&MD` 里能不能设温度梯度？" | §3 找 `MOTION/MD` → 打开页面看 Keywords |
| "`&DFT` 下面到底有哪些子段？" | §3 找 `FORCE_EVAL/DFT` → 36 个子段一览 |
| "打印受力该加在哪？" | `&MOTION/&PRINT/&FORCES` 或 `&FORCE_EVAL/&PRINT/&FORCES` |
| "NEB 怎么配？" | `&MOTION/&BAND`（11 个子段，含 `CI_NEB`、`OPTIMIZE_BAND`、`REPLICA`） |
| "约束动力学有哪些约束类型？" | `&MOTION/&CONSTRAINT`（10 个子段：`COLLECTIVE`、`FIXED_ATOMS`、`G3X3`、`G4X6`、`HBONDS`、`LAGRANGE_MULTIPLIERS`、`VIRTUAL_SITE` 等） |
| "元动力学怎么开？" | `&MOTION/&FREE_ENERGY/&METADYN`（`&WALL` 的落点与四种形式见 §8.2） |
| "QM/MM 的 QM 区怎么定义？" | `&FORCE_EVAL/&QMMM`（`QM_KIND`、`MM_KIND`、`LINK`、`IMAGE_CHARGE`、`FORCE_MIXING`） |
| "BSSE 怎么算？" | `&FORCE_EVAL/&BSSE`（4 个子段：`CONFIGURATION`、`FRAGMENT`、`FRAGMENT_ENERGIES`、`PRINT`） |
| "DFT+U 在哪？" | `&FORCE_EVAL/&SUBSYS/&KIND/&DFT_PLUS_U`（第 4 层，落在 `&KIND` 内；`&DFT` 层只放关键字 `PLUS_U_METHOD`。落点更正见 §8.1） |
| "想算 K 点" | `&FORCE_EVAL/&DFT/&KPOINTS` / `&KPOINT_SET` |
| "线性标度怎么做？" | `&FORCE_EVAL/&DFT/&LS_SCF` |
| "分子动力学系综/温控/压控" | `&MOTION/&MD` 下的 `&THERMOSTAT`、`&BAROSTAT`、`&LANGEVIN`、`&RESPA` |
| "路径积分 MD（NQE）" | `&MOTION/&PINT`（11 个子段，含 `BEADS`、`PILE`、`GLE`、`HELIUM`、`QTB`） |
| "振动分析 / 声子" | `&VIBRATIONAL_ANALYSIS`（2 个子段 + 8 个关键字） |
| "从别的输入续算" | `&EXT_RESTART`（38 个关键字，无子段） |
| "输运（NEGF）" | `&NEGF`（5 个子段：`CONTACT`、`MIXING`、`PRINT`、`SCATTERING_REGION`、`SCF`） |
| "批量跑多个输入" | `&FARMING`（`JOB`、`PROGRAM_RUN_INFO`、`RESTART`） |

> **[G层提示]** 一个高频坑：**同名段在不同父段下语义不同**。例如 `&PRINT/&FORCES` 在
> `&FORCE_EVAL`、`&MOTION`、`&MD` 下都存在，但打印的内容与触发时机不一样。写输入时务必写全路径。

> **官网其它页落点提示**：`/periodicity`（**胞 0→h 不中心化**、`CENTER_COORDINATES`、两处周期性应一致）、
> `/tools`（23 个第三方软件 + GTH 势 + 3 个脚本仓库）、`/science`（79 个应用案例）、
> `/version_history`·`/videos`·`/tutorials` 三页的跳转状态，均整理在 `00_map.md` §2.1–§2.4。

## 6. 与 G 层其它文件的关系

| 需求 | 去哪 |
|---|---|
| 查 `&GLOBAL` 关键字的**默认值** | `01_global_and_units.md`（已逐条抄录 38 个） |
| 查**段/关键字是否存在、父子关系** | 本文件 |
| 查**某方法的物理原理、推荐设置、完整示例** | `02`–`23` 各专题文件 |
| 查**报错含义** | `08_errors_and_faq.md` |
| 查**版本变更导致的关键字增删** | `11_version_changelog.md` |
| 查**官网导航页（周期性/工具/案例/跳转页）** | `00_map.md` §2 |

## 7. 缺口登记（如实）

| 项 | 状态 |
|---|---|
| 各段**关键字默认值/类型/单位** | **未逐条抄录**（750 个关键字 × 平均 6 个字段 ≈ 4500 条，体量过大）。需要时按 URL 查官方页面 |
| 第四层及更深段 | 未展开（第三层已覆盖 269 个，更深层多为叶子打印项）；**例外**：§8 按需补录了 `&DFT_PLUS_U`、`&WALL`、`R_CUTOFF` 三处落点 |
| 各段的 `Mentions`（该段关联的方法页） | 未采集 |
| `&TEST` 段 | 已索引但未展开正文（编译自检用，日常不用） |

> **[G层提示]** 若后续要补"关键字默认值表"，建议**按需增量**：优先 `&MOTION/&MD`、`&FORCE_EVAL/&DFT/&QS`、
> `&FORCE_EVAL/&SUBSYS/&CELL`、`&FORCE_EVAL/&SUBSYS/&KIND` 这四段，它们覆盖日常输入的绝大多数关键字。

---

## 8. 本轮复核补录与更正（`_kw_probe.py` 直查官方 `cp2k_input.xml`，2026-09-19）

> **复核方式**：`python _kw_probe.py --find <名称>`（全库搜该段/关键字出现在哪些路径）、
> `python _kw_probe.py --section <段路径>`（列出该段的直接子段/直接关键字及官方 `unit=`、`default=`）。
> `_kw_probe.py` 直读 cp2k-input-tools 自带的官方 `cp2k_input.xml`，与 §1 所列 manual.cp2k.org 抓取同源。
> §3/§4 只展开到第三层；本节只**按需补录**三处更深层落点与一处落点更正，仍不对全部关键字做默认值抄录（口径同 §7）。

### 8.1 `&DFT_PLUS_U` 的落点（更正 §5）

| 项 | 官方 XML 事实 | 复核命令 |
|---|---|---|
| **正确路径** | `&FORCE_EVAL/&SUBSYS/&KIND/&DFT_PLUS_U`（第 4 层，挂在 `&KIND` 内） | `--find DFT_PLUS_U` → 全库 **1 处**：`&FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U`（1 个子段、5 个关键字） |
| 直接关键字（5） | `INIT_U_RAMPING_EACH_SCF`（`default=F`）、`L`（`default=-1`）、`U_MINUS_J`（`unit=hartree`，`default=0.00000000E+000`）、`U_RAMPING`（`unit=hartree`，`default=0.00000000E+000`）、`EPS_U_RAMPING`（`default=1.00000000E-005`） | `--section FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U` |
| 直接子段（1） | `&ENFORCE_OCCUPATION` —— 其直接关键字：`NELEC`（`default=0.00000000E+000`）、`ORBITALS`（`default=0`）、`EPS_SCF`（`default=1.00000000E+030`）、`MAX_SCF`（`default=-1`）、`SMEAR`（`default=F`） | `--section FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U/ENFORCE_OCCUPATION` |
| 相关关键字在 `&DFT` 层 | `PLUS_U_METHOD`（`default=MULLIKEN`）是 `&FORCE_EVAL/&DFT` 的**直接关键字**，**不在** `&DFT_PLUS_U` 下 | `--find PLUS_U_METHOD` → `FORCE_EVAL/DFT` |

> **更正记录**：§5 原写 "`&FORCE_EVAL/&DFT/&QS/&DFT_PLUS_U`（第三层）"，**路径错误**——该路径在 XML 中不存在；
> `&DFT_PLUS_U` 既不在 `&DFT` 下、也不在 `&DFT/&QS` 下，全库唯一落点是 `&FORCE_EVAL/&SUBSYS/&KIND/&DFT_PLUS_U`（第 4 层）。
> 佐证（与官方口径一致的真实输入）：H 层算例 `references/h_tutorials/cases/TiO2-Au20_cp2k.inp` 第 121–129 行把 `&DFT_PLUS_U`（含 `U_MINUS_J [eV] 13.6`）写在 `&KIND Ti` 内。

> **[G层提示]** 以下名称在官方 `cp2k_input.xml` 中**全库 0 命中**，本文件不收录，写输入时也不要使用：
> `U_EFFECTIVE`（`--find U_EFFECTIVE` → 0 处）、`ATOMIC_ORBITALS`（`--find ATOMIC_ORBITALS` → 0 处）。
> `&DFT_PLUS_U` 下与占据/轨道相关的子段是 `&ENFORCE_OCCUPATION`（见上表）。

### 8.2 `&WALL`（元动力学墙）的落点与四种形式（补录）

`&WALL` 位于第 5 层，且挂在 **`&METAVAR`** 下（不直接挂在 `&METADYN` 下）：

| 层 | 路径 | 直接子项（`--section` 实测） |
|---|---|---|
| 4 | `&MOTION/&FREE_ENERGY/&METADYN/&METAVAR` | 关键字 `LAMBDA`（`unit=internal_cp2k`）、`MASS`（`unit=amu`）、`GAMMA`（`unit=fs^-1`）、`SCALE`（`unit=internal_cp2k`）、`COLVAR`；子段 `&WALL` |
| 5 | `&MOTION/&FREE_ENERGY/&METADYN/&METAVAR/&WALL` | 关键字 `TYPE`（`default=NONE`）、`POSITION`（`unit=internal_cp2k`）；子段 `&REFLECTIVE`、`&QUADRATIC`、`&QUARTIC`、`&GAUSSIAN` |

官方 XML 中 `&WALL` 的子段**恰为下列 4 个**，各自的直接关键字与 `unit=` 标注如下（照抄 XML）：

| 形式 | 直接关键字（`default=` / `unit=`） |
|---|---|
| `&REFLECTIVE` | `DIRECTION`（`default=WALL_PLUS`）；**无 `K`** |
| `&QUADRATIC` | `DIRECTION`（`default=WALL_PLUS`）、`K`（**`unit=hartree`**） |
| `&QUARTIC` | `DIRECTION`（`default=WALL_PLUS`）、`K`（**`unit=hartree`**） |
| `&GAUSSIAN` | `WW`（**`unit=hartree`**）、`SIGMA`（`unit=internal_cp2k`）；**无 `K`** |

> 复核命令：`--find WALL` → 全库 1 处：`&MOTION/FREE_ENERGY/METADYN/METAVAR/WALL`（4 个子段、2 个关键字）；
> `--section MOTION/FREE_ENERGY/METADYN/METAVAR/WALL` 与 `--section MOTION/FREE_ENERGY/METADYN/METAVAR/WALL/<形式>`。

> **[G层提示]** 上表 `unit=` 一律照抄官方 `cp2k_input.xml`，本文件只如实转写，不对取值口径另作判断。

### 8.3 `R_CUTOFF` 的落点（补录：不在 `&QS` 下）

| 项 | 官方 XML 事实 |
|---|---|
| 落点 | `&FORCE_EVAL/&DFT/&XC/&VDW_POTENTIAL/&PAIR_POTENTIAL`。`--find R_CUTOFF` 全库 **7 处**，全部以 `.../&XC/&VDW_POTENTIAL/&PAIR_POTENTIAL` 结尾（`&DFT/&KG_METHOD`、`&DFT/&ENERGY_CORRECTION`、`&DFT/&TDDFPT`、`&DFT/&XC`、`&PROPERTIES/&LINRES/&EPR/&PRINT/&G_TENSOR`、`&PROPERTIES/&TDDFPT`、`&ATOM/&METHOD` 下各一份） |
| 官方默认值 | `DEFAULT_VALUE : 1.05835442E+001`，`DEFAULT_UNIT : angstrom`（即 **10.5835442 Å**） |
| `DESCRIPTION` | `Range of potential. The cutoff will be 2 times this value` |
| 负向核对 | `&FORCE_EVAL/DFT/QS` 下**没有** `R_CUTOFF`：`--section FORCE_EVAL/DFT/QS/R_CUTOFF` → `未找到 R_CUTOFF（在 FORCE_EVAL/DFT/QS 下）`（exit 1） |

---

## 交叉索引

| 关联文件 | 关系 |
|---|---|
| `00_map.md` | 官网/手册地图；本文件是其"Input Reference"分支的展开 |
| `01_global_and_units.md` | `&GLOBAL` 的 38 个关键字默认值（本文件只列名） |
| `02_dft_methods.md` | `&FORCE_EVAL/&DFT` 下各方法的物理说明 |
| `04_sampling_md.md` | `&MOTION/&MD` 的系综与温控说明 |
| `05_optimization.md` | `&MOTION/&GEO_OPT`、`&CELL_OPT` 的算法说明 |
| `17_constrained_dynamics_and_paths.md` | `&MOTION/&CONSTRAINT`、`&BAND`、`&FREE_ENERGY` 的实操 |
| `18_posthf_semiempirical_and_xray.md` | `&FORCE_EVAL/&BSSE`、`&XAS_TDP`、`&GW2X` |
| `_sources.md` | 采集总表与缺口清单 |
