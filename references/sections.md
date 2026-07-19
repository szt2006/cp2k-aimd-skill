# CP2K SECTION 速查（基于庚子计算讲义）

CP2K 输入是层级化的 SECTION/END SECTION 结构。下面的层级与常用关键字按使用频率排列。

## 顶层结构
```
&GLOBAL            # 全局控制：PROJECT, RUN_TYPE, PRINT_LEVEL
&FORCE_EVAL        # 一个或多个：定义能量/力怎么算（DFT/FIST/MIXED）
&MIXED             # 仅 QM/MM 时用
&MOTION            # 优化/动力学/过渡态/约束
&EXT_RESTART       # 续算
```

## &GLOBAL
| 关键字 | 说明 | 常用值 |
|---|---|---|
| PROJECT | 输出文件前缀 | 任意字符串 |
| RUN_TYPE | 计算类型 | ENERGY / ENERGY_FORCE / GEO_OPT / CELL_OPT / MD / BAND |
| PRINT_LEVEL | 输出详细度 | LOW（优化）/ MEDIUM（MD）|
| WALLTIME | 墙钟时间限制 | 如 7200（秒）|

## &FORCE_EVAL
| 关键字 | 说明 | 常用值 |
|---|---|---|
| METHOD | 能量方法 | Quickstep（DFT）/ FIST（力场）/ MIXED（QM/MM）|
| STRESS_TENSOR | 应力张量 | None（不优化晶胞时）/ ANALYTICAL |
| &DFT | DFT 参数块 | 见下 |
| &SUBSYS | 结构块 | 见下 |
| &PRINT | 打印控制 | &FORCES, &PDOS, &E_DENSITY_CUBE, &WANNIER_CENTERS |

### &FORCE_EVAL/&DFT
- `BASIS_SET_FILE_NAME BASIS_SET` —— 基组库（cp2k/data）。
- `POTENTIAL_FILE_NAME GTH_POTENTIALS` —— 赝势库。
- `&MGRID` —— 网格：`NGRIDS 4`, `CUTOFF 300`（Ry，金属 350–500）, `REL_CUTOFF 60`（Ry）。重元素调大 CUTOFF（gen_inp：`--cutoff` / `--rel-cutoff`）。
- `&XC / &XC_FUNCTIONAL PADE` —— 泛函（=PBE）。加 `&VDW_POTENTIAL` 可做色散校正。
- `&SCF`：
  - `SCF_GUESS ATOMIC` / RESTART（RESTART 需 `--wfn-restart <file>` 发射 `&DFT WFN_RESTART_FILE_NAME`）
  - `EPS_SCF 1.0E-7`, `MAX_SCF 300`（gen_inp：`--eps-scf` / `--max-scf`）
  - `EPS_DIIS 0.05`, `ADDED_MOS 500`（金属/展宽加额外 MO）, `CHOLESKY INVERSE`（gen_inp：`--eps-diis` / `--added-mos` / `--cholesky`）
  - `&MIXING METHOD BROYDEN_MIXING ALPHA 0.4 BETA 1.5 NBROYDEN 8`（gen_inp：`--mixing-alpha/beta/nbroyden`）
  - `&OT MINIMIZER DIIS PRECONDITIONER FULL_SINGLE_INVERSE` —— OT 求解器（默认开）
  - `&SMEAR METHOD FERMI_DIRAC ELECTRONIC_TEMPERATURE [K] 300` —— 金属/窄带隙必加
  - `&DIAGONALIZATION ALGORITHM STANDARD` + `EPS_ADAPT 0.01` —— 传统对角化（非 OT 时用；gen_inp：`--diagonalization-eps-adapt`）
- `&POISSON` —— 周期体系 `PERIODIC xyz`；表面/团簇用 `WAVELET` 或 `MT`（Martyna-Tuckerman）。
- `&PRINT &PDOS` —— 投影态密度（见 postprocess.md）。

### &FORCE_EVAL/&SUBSYS
- `&KIND <名称>`：`ELEMENT`, `BASIS_SET`（如 `DZVP-GTH-PADE` / `DZVP-MOLOPT-SR-GTH`）, `POTENTIAL`（如 `GTH-PADE-q4` / `GTH-PBE-q11`）, 可选 `MASS` / `MAGNETIZATION`。
  - **多元素体系：每种元素一个 &KIND 块。**
  - **同一元素的不同自旋/氧化位点**可用不同 `&KIND` 名称但同一 `ELEMENT`（如 `Fe` / `Fe2` / `Fe3`，均 `ELEMENT Fe`），配合逐原子 `MAGNETIZATION` 设不同自旋。
  - **DFT+U**：在 `&KIND` 内加 `&DFT_PLUS_U`（关键字 `L`、`U_MINUS_J [eV]`、`U_RAMPING`、`EPS_U_RAMPING`、`INIT_U_RAMPING_EACH_SCF`）；并在 `&DFT` 层设 `PLUS_U_METHOD`（MULLIKEN / LOWDIN / MARZARI / DUDEI）。强关联过渡金属氧化物（Fe3O4、TiO2 等）常用。
  - 用 `gen_inp.py --kinds "NAME:ELEMENT:BASIS:POTENTIAL:U=<eV>:mag=<f>:mass=<f>:L=<int>:noramp"` 一步生成上述所有逐原子控制。
- `&CELL`：`A/B/C` 三个晶格向量（每行 3 个数）。
- `&COORD`：逐行 `元素 x y z`。或用 `&TOPOLOGY COORD_FILE_NAME xxx.xyz COORD_FILE_FORMAT XYZ`。

## &MOTION
- `&GEO_OPT`：`OPTIMIZER BFGS`（或 CG/LBFGS）, `MAX_ITER 400`, `MAX_FORCE 6.0E-4`, `MAX_DR 0.003`, `RMS_FORCE 0.0003`, `RMS_DR 0.0015`。
- `&CELL_OPT`：`EXTERNAL_PRESSURE 1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0`, `KEEP_ANGLES T`, `KEEP_SYMMETRY T`, `OPTIMIZER CG`。
- `&MD`：`ENSEMBLE NVT/NVE/NPT_F`, `STEPS`, `TIMESTEP 0.5`（fs）, `TEMPERATURE`, `&THERMOSTAT`（NOSE / CSVR）。
- `&BAND`：`NEB`, `NUMBER_OF_REPLICA`, `BAND_TYPE CI-NEB`, 内嵌多个 `&REPLICA`（按出现顺序编号，**无** `i` 参数）`&COORD ... &END COORD` 或 `COORD_FILE_NAME <file>`（首末两帧必填，中间由 CP2K 插值）。另含 `K_SPRING`(spring 常数 0.02~0.08)、`NPROC_REP N`(每副本 MPI 数)、`ALIGN_FRAMES T/F`、`ROTATE_FRAMES T/F`、`&CI_NEB`、`&OPTIMIZE_BAND`、`&PROGRAM_RUN_INFO`、`&CONVERGENCE_INFO`。
- `&CONSTRAINT / &FIXED_ATOMS`：`LIST 1..54 289..324` 固定原子序号。
- `&PRINT`：在 MOTION 下控制轨迹/速度/重启：`&TRAJECTORY &EACH MD 1`, `&VELOCITIES &EACH MD 1`, `&RESTART_HISTORY &EACH MD 500`, `&RESTART BACKUP_COPIES 3`。

## &FREE_ENERGY / &METADYN（元动力学）
- `&METADYN DO_HILLS NT_HILLS 50`
- `&METAVAR SCALE 0.3 COLVAR n` —— 每个集体变量一个
- `&COLVAR` —— 定义集体变量（如 `&DISTANCE ATOMS i j`）；METAVAR 的 COLVAR 序号对应这里
- `&WALL TYPE QUADRATIC POSITION [angstrom] K [kcalmol] 40.0 DIRECTION WALL_PLUS/WALL_MINUS`

## 进阶 SECTION（来自《CP2K使用入门》）
- **自旋极化**：`&DFT UKS` + `MULTIPLICITY N`（N=2S+1；O₂→3，单电子自由基→2）。开壳层务必加 `WF_INTERPOLATION ASPC` + `EXTRAPOLATION_ORDER 3` 加速 SCF。`LSD` 是另一种（限制自旋）写法；分子/表面常用 `UKS`。
- **杂化泛函**：`&XC &XC_FUNCTIONAL` 内放 `&XWPBE`（HSE06：SCALE_X -0.25, SCALE_X0 1.0, OMEGA 0.11）+ `&PBE`（SCALE_X 0.0, SCALE_C 1.0），并加 `&HF FRACTION 0.25 SCREENING_TYPE SHORTRANGE OMEGA 0.11 &SCREENING EPS_SCHWARZ 1e-10 &MEMORY MAX_MEMORY 100`。B3LYP 用 `&LYP`(SCALE_C 0.81)+`&BECKE88`(SCALE_X 0.72)+`&VWN`(FUNCTIONAL_TYPE VWN3, SCALE_C 0.19)+`&XALPHA`(SCALE_X 0.08) + `&HF FRACTION 0.20`。杂化泛函贵，建议 `EPS_SCF 1e-6`、加 `&OUTER_SCF`。
- **色散**：`&XC &VDW_POTENTIAL POTENTIAL_TYPE PAIR_POTENTIAL &PAIR_POTENTIAL TYPE DFTD3 REFERENCE_FUNCTIONAL PBE R_CUTOFF [angstrom] 12`，并把 `dftd3.dat` 放到运行目录。
- **约束/固定原子**：`&MOTION &CONSTRAINT &FIXED_ATOMS LIST 1..54 289..324 &END` —— 冻结 slab 底层或远场。LIST 区间写法 `a..b`，多段空格分开。
- **非周期 POISSON**：孤立分子/团簇用 `&POISSON PERIODIC NONE POISSON_SOLVER WAVELET`（或 MT）。此时 `&CELL` 给一个大盒子（如 20×20×20 Å）包住分子即可。
- **振动分析**：`&GLOBAL RUN_TYPE VIBRATIONAL_ANALYSIS` + `&MOTION &VIBRATIONAL_ANALYSIS DX 0.01 INTENSITIES T NPROC_REP 8 FULLY_PERIODIC T`。有限差分求 Hessian；`MODE_SELECTIVE` 可只对指定原子（如 `&INVOLVED_ATOMS 82 83`）做局域振动。
- **OUTER_SCF**：`&SCF &OUTER_SCF ON MAX_SCF 5 EPS_SCF 5e-6 &END` —— OT 不收敛时的外层循环，常与 `SCF_GUESS RESTART` 配合。
- **打印原子力**：`&GLOBAL &PRINT &FORCES ON &END` 把每步原子力写进 .out（关键词 `ATOMIC FORCES in [a.u.]`）。
- **QS EPS_DEFAULT**：`&DFT &QS EPS_DEFAULT 1e-10`（默认 1e-10，精度不够调到 1e-12~1e-14）；相关 `EPS_CORE_CHARGE`、`EPS_PGF_ORB`（≈√EPS_DEFAULT）、`EPS_GVG_RSPACE`（≈EPS_DEFAULT/100）。
- **NEB 进阶**：`&BAND K_SPRING 0.02`（spring 常数，一般 0.02~0.08）、`NPROC_REP N`（每副本 MPI 数，总核数 = N×副本数）、`BAND_TYPE IT-NEB/CI-NEB`、`&CI_NEB NSTEPS_IT 5`、`&OPTIMIZE_BAND OPT_TYPE MD &MD TIMESTEP 0.5 TEMPERATURE 500 MAX_STEPS 300 &VEL_CONTROL ANNEALING 0.99`。
  - **多副本外部读取**：`&REPLICA COORD_FILE_NAME <file>`（每个副本一个文件，如 al2o3/neb 的 `./0.xyz .. ./5.xyz`）；`NUMBER_OF_REPLICA` 等于文件数。内联则写 `&REPLICA &COORD ... &END COORD`。
  - **端点固定 DIIS**：`&OPTIMIZE_BAND OPT_TYPE DIIS OPTIMIZE_END_POINTS F &END OPTIMIZE_BAND`（al2o3/neb 写法，不松弛端点；无需 `&DIIS` 子节）。
  - **帧对齐/旋转**：`ALIGN_FRAMES T/F`（默认 T，优化前先把每帧对齐）、`ROTATE_FRAMES T/F`（默认 F，把帧旋转到最佳重叠——旋转型反应坐标需要）。
  - **诊断输出**：`&PROGRAM_RUN_INFO ON`（每副本运行信息）、`&CONVERGENCE_INFO ON`（带收敛信息）。
- **Dimer 过渡态**：`&MOTION &GEO_OPT TYPE TRANSITION_STATE OPTIMIZER CG MAX_FORCE 4.5e-4 &CG &LINE_SEARCH TYPE 2PNT &END &TRANSITION_STATE METHOD DIMER &DIMER DR 0.01 ANGLE_TOLERANCE [deg] 4.0 &ROT_OPT OPTIMIZER CG MAX_ITER 10 &CG &LINE_SEARCH TYPE 2PNT &END &END &END` —— 只需初态，自动找鞍点（适合只知初态、不知路径的反应）。
- **QM/MM（METHOD MIXED）**：顶层 `&MULTIPLE_FORCE_EVALS FORCE_EVAL_ORDER 2 3 MULTIPLE_SUBSYS T`；然后三个 `&FORCE_EVAL`：① `METHOD MIXED`（`&MIXED MIXING_TYPE GENMIX GROUP_PARTITION 2 6 &GENERIC MIXING_FUNCTION E1+E2 VARIABLES E1 E2 &MAPPING &FORCE_EVAL_MIXED &FRAGMENT 1 <QM原子> &FRAGMENT 2 <MM原子> &FORCE_EVAL 1 DEFINE_FRAGMENTS 1 2 &FORCE_EVAL 2 DEFINE_FRAGMENTS 1`）；② `METHOD FIST`（`&MM &FORCEFIELD &SPLINE &CHARGE ATOM X / CHARGE 0.0 &NONBONDED &LENNARD-JONES atoms X X ... / &EAM / &GENPOT &POISSON &EWALD`）；③ `METHOD Quickstep` 且 `&DFT &QS METHOD PM6 &SE &COULOMB CUTOFF [angstrom] 20.0 &EXCHANGE CUTOFF [angstrom] 20.0 &POISSON PERIODIC NONE WAVELET`。
  - QM 区用 PM6 半经验（`QS METHOD PM6`，无需 BASIS_SET/POTENTIAL）；MM 区用 FIST 经典力场，其 `&NONBONDED` 需真实参数（GENPOT/EAM/Buckingham），本项目模板只生成占位骨架。
  - 坐标：`&TOPOLOGY COORD_FILE_FORMAT xyz`（官方解析器认 `COORD_FILE_FORMAT`，不认旧别名 `COORDINATE`）；全系统与 QM 片段各用一份坐标文件。

## 常用可执行文件
- `cp2k.popt` —— MPI 并行（最常用）
- `cp2k.ssmp` —— OpenMP
- `cp2k.psmp` —— MPI + OpenMP
- 运行前先 `source` 编译时的 toolchain 环境（见 run.md）。
