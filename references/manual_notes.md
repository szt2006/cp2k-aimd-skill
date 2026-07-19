# 官方手册学习笔记（manual.cp2k.org/trunk，基于 CP2K 2026.1）

> 来源：https://manual.cp2k.org/trunk/index.html （Input Reference 由本地 `cp2k_input.xml` 等价生成，已存 `references/_manual_tree.txt`）
> 学习工具：`scripts/_manual_tree.py`（抽 SECTION 树）、`scripts/_manual_kw.py "路径"`（抽某 SECTION 关键字详情）
> 目标：把手册知识系统化，校验并扩充 `decide.md` / `sections.md` / `gen_inp.py` / `recommend.py`

---

## 批次 1（2026-07-14）：结构 + GLOBAL/FORCE_EVAL/DFT 顶层 + GPW + SCF 收敛

### 总结构
- 顶层 14 个 SECTION：ATOM, DEBUG, EXT_RESTART, FARMING, FORCE_EVAL, GLOBAL, MOTION, TEST, VIBRATIONAL_ANALYSIS, (其余见 `_manual_tree.txt`)。
- 全文约 7616 行 SECTION 树，关键字总量极大（数千）。需分批精读。

### GLOBAL（入口）
- `RUN_TYPE`：决定计算类型（ENERGY_FORCE / GEO_OPT / CELL_OPT / MD / BAND / VIBRATIONAL_ANALYSIS）。
- `PROGRAM_NAME`（默认 cp2k）、`PROJECT_NAME`（输出文件基名）、`PRINT_LEVEL`（输出详细度）、`WALLTIME`。
- 结论：与 skill 现有知识一致。

### FORCE_EVAL
- `METHOD`：Quickstep / FIST / MIXED / QS / ...（skill 用 `METHOD Quickstep` 正确）。
- `STRESS_TENSOR`：控制应力张量计算（在 `&FORCE_EVAL` 层，非 `&PRINT`——与 skill 现有认知一致）。
- 14 个子 SECTION：`EXTERNAL_POTENTIAL, RESCALE_FORCES, MIXED, EMBED, DFT, PW_DFT, MM, NNP, QMMM, EIP, BSSE, SUBSYS, PROPERTIES, PRINT`。

### DFT（顶层，18 关键字 + 29 子 SECTION）
- 顶层关键字：`UKS` / `ROKS` / `MULTIPLICITY` / `CHARGE` / `PLUS_U_METHOD` / `BASIS_SET_FILE_NAME` / `POTENTIAL_FILE_NAME` / `WFN_RESTART_FILE_NAME` / `AUTO_BASIS` / `SORT_BASIS`。
- ⚠️ **新发现缺口**：`SURFACE_DIPOLE_CORRECTION`（slab 不对称几何需开表面偶极修正）+ `SURF_DIP_DIR` / `SURF_DIP_POS` / `SURF_DIP_SWITCH`。**skill 当前 slab 指导未提及**，应补。
- 29 子 SECTION 含：`SCF, LS_SCF, ALMO_SCF, QS, MGRID, XC, RELATIVISTIC, SIC, POISSON, KPOINTS, AUXILIARY_DENSITY_MATRIX_METHOD(ADMM), LOCALIZE, PRINT, REAL_TIME_PROPAGATION, SCCS, TDDFPT, XAS, ...`

### GPW（方法章）
- GPW = Gaussian 型轨道(GTO) 基组 + 实空间网格解 Poisson（collocation/integration 在 GTO↔grid 间切换）。确认 skill 的「Quickstep=GPW」框架正确。
- GAPW：全电子 / 对核敏感计算（如核四极矩、XAS）。
- 新输入流程：先选一致的基组/赝势对 → 收敛 MGRID CUTOFF → 收敛 SCF。

### SCF 收敛（方法章 "How to make a SCF run converge"）
- **CP2K 2024.1 起**：超过 `MAX_SCF`（默认 50）未达 `EPS_SCF` 直接 **ABORT**；有时先报 `KS energy is NaN/Inf`。
- 对角化路径 `&MIXING METHOD`：`DIRECT_P_MIXING`(默认) → `BROYDEN_MIXING` / `PULAY_MIXING` / `KERKER_MIXING`。
- `&SMEAR`：`FERMI_DIRAC`(ELECTRONIC_TEMPERATURE，需外推至0) / `GAUSSIAN`(SIGMA，需降至0)；用于小/零带隙、强关联。
- OT 路径：`&OT` 的 `ALGORITHM`/`LINESEARCH`/`MINIMIZER`/`PRECONDITIONER`；用 `&OUTER_SCF` 更新预条件子；**内循环 MAX_SCF 16–32，外循环 MAX_SCF 8–16**。
- `SCF_GUESS RESTART` + `WFN_RESTART_FILE_NAME`：从廉价计算接力。
- `IGNORE_CONVERGENCE_FAILURE` 仅最后手段（会污染结果）。
- 注：`ADDED_MOS` / `CHOLESKY`（在 `&SCF &DIAGONALIZATION` 下）该页未展开，但 skill 已支持 `--added-mos` / `--cholesky`，需在对 `&DIAGONALIZATION` 段精读时二次核对。

### 待办（后续批次）
- [ ] 精读 `FORCE_EVAL/DFT/SCF`（MIXING/OT/DIAGONALIZATION/OUTER_SCF 细节）
- [ ] 精读 `FORCE_EVAL/DFT/XC`（XC_FUNCTIONAL 各泛函、MGGA、HF/ADMM、LIBXC 名）
- [ ] 精读 `FORCE_EVAL/DFT/MGRID`、`POISSON`、`KPOINTS`
- [ ] 精读 `FORCE_EVAL/DFT/PRINT`（DOS/PDOS/BAND/STRESS/E_DENSITY_CUBE 落点）
- [ ] 精读 `FORCE_EVAL/SUBSYS`（CELL/COORD/TOPOLOGY/KIND/COLVAR）
- [ ] 精读 `MOTION`（GEO_OPT/CELL_OPT/MD/BAND/METADYN/CONSTRAINT）
- [ ] 读 Methods 章：Post-HF(HSE06/B3LYP+ADMM)、Semi-Empirical(PM6)、ML、Embedding、QM-MM、Sampling、Optimization、Electronic-structure Analysis、Properties
- [ ] 读 Technologies：Eigensolvers、Accelerators、Libraries
- [ ] 补 skill 缺口：SURFACE_DIPOLE_CORRECTION；复核 ADDED_MOS/CHOLESKY 落点

---

## 批次 2（2026-07-14）：Input Reference 核心路径精读 + DFT 概念章

### SCF（FORCE_EVAL/DFT/SCF，19 关键字 + 7 子节）
- `MAX_SCF`（默认 50，2024.1 起超限未收敛直接 ABORT）、`EPS_SCF`、`SCF_GUESS`、`ADDED_MOS`、`CHOLESKY`、`LEVEL_SHIFT`、`MAX_DIIS`、`NOTCONV_STOPALL`。
- 子节：**OT / DIAGONALIZATION / OUTER_SCF / SMEAR / MIXING / MOM / PRINT**。
- **OT**：`MINIMIZER`(DIIS/CG/BROYDEN/SD)、`ALGORITHM`(STRICT/IRAC)、`SAFE_DIIS`、`N_HISTORY_VEC`、BROYDEN 系列（BETA/GAMMA/SIGMA/ADAPTIVE）。默认设置已高效稳健。
- **MIXING**：`METHOD`(BROYDEN/PULAY/KERKER/MULTISECANT)、`ALPHA`、`BETA`(Kerker 阻尼分母)、`NMIXING`、`N_SIMPLE_MIX`、`NBUFFER`、`PULAY_ALPHA/BETA`。
- **SMEAR**：`METHOD`(FERMI_DIRAC/GAUSSIAN)、`ELECTRONIC_TEMPERATURE`、`WINDOW_SIZE`、`FIXED_MAGNETIC_MOMENT`（强制自旋差，固定磁矩计算用）。
- **OUTER_SCF**：`TYPE`、`OPTIMIZER`、`MAX_SCF`、`EPS_SCF`、`DIIS_BUFFER_LENGTH`。OT 配合 OUTER_SCF 更新预条件子；内循环 MAX_SCF 16–32、外循环 8–16。

### XC（FORCE_EVAL/DFT/XC）
- 624 个子 SECTION（全部 LibXC 泛函名 + CP2K 内置：PBE/TPSS/SCAN/HSE06/B3LYP/BEEF…）。功能名体系确认：`XC_FUNCTIONAL PBE` / `TPSS` / `SCAN` / `XWPBE`+`PBE`+`HF`(HSE06) / `LYP`+`BECKE88`+`VWN`+`XALPHA`+`HF`(B3LYP)。
- `VDW_POTENTIAL`、`GCP_POTENTIAL`（DFT-D 类）、`HF`（精确交换，杂化用）、`ADMM` 校正。
- 子节：`XC_GRID`、`XC_FUNCTIONAL`、`HF`、`WF_CORRELATION`、`VDW_POTENTIAL`、`GCP_POTENTIAL`。

### MGRID / POISSON / KPOINTS
- **MGRID**：`CUTOFF`（最细网格截断）、`REL_CUTOFF`（高斯映射参考）、`NGRIDS`(默认4)、`PROGRESSION_FACTOR`(默认3.0)、`COMMENSURATE`、`MULTIGRID_CUTOFF`。
- **POISSON**：`POISSON_SOLVER`(MT/WAVELET/MULTIPOLE/EWALD/IMPLICIT)、`PERIODIC`（仅静电，与 CELL 的 PBC 区分）。
- **KPOINTS**：`SCHEME`(NONE/GAMMA/MONKHORST-PACK/MACDONALD/GENERAL)、`SYMMETRY`、`FULL_GRID`、`PARALLEL_GROUP_SIZE`、`WAVEFUNCTIONS`。

### QS / PRINT
- **QS**：`EPS_DEFAULT`（总开关，设所有 EPS_xxx 到该精度）、`FORCE_PAW`、`METHOD GAPW`（切全电子）、GAPW 专属 `EPSFIT/EPSRHO0/EPSSVD/EPSISO/EPSSVD`。
- **DFT/PRINT（51 子节）**：`DOS`、`PDOS`(COMPONENTS/NLUMO)、`BAND_STRUCTURE`(KPOINT_SET/ADDED_MOS)、`MO_CUBES`、`E_DENSITY_CUBE`、`TOT_DENSITY_CUBE`、`V_HARTREE_CUBE`、`STM`、`MULLIKEN`、`LOWDIN`、`HIRSHFELD`、`MOMENTS`、`EFIELD_CUBE`、`ELF_CUBE`、`ELECTRIC_FIELD_GRADIENT`、`HYPERFINE_COUPLING_TENSOR`、`WANNIER90`、`XRAY_DIFFRACTION_SPECTRUM`、`CHARGEMOL` 等。每个 print_key 都有 `EACH`/`FILENAME`/`ADD_LAST` 控制。

### SUBSYS / CELL / COORD / TOPOLOGY / KIND
- **SUBSYS**：`SEED`（Langevin 随机数）、子节 CELL/COORD/VELOCITY/KIND/TOPOLOGY/COLVAR/MULTIPOLES/SHELL_*。
- **CELL**：`A/B/C`（列向量）、`ABC`（正交晶格长度）、`ALPHA_BETA_GAMMA`、`PERIODIC`、`MULTIPLE_UNIT_CELL`（重复扩胞）、`SYMMETRY`、`CELL_FILE_NAME`。
- **COORD**：`UNIT`、`SCALED`（分数坐标）。
- **TOPOLOGY**：`COORD_FILE_NAME/FORMAT`、`USE_ELEMENT_AS_KIND`、`CONN_FILE_NAME`、MM 排除列表（经典力场用）。
- **KIND（32 关键字）**：`BASIS_SET`、`POTENTIAL`、`ELEMENT`、`MASS`、`MAGNETIZATION`、`ELEC_CONF`、`CORE_CORRECTION`、`LEBEDEV_GRID`/`RADIAL_GRID`（GAPW 用）、`AUX_FIT_BASIS_SET`（ADMM）。注意 `AUX_BASIS_SET`/`RI_AUX_BASIS_SET` 等已标记为 [REMOVED]。

### MOTION（13 子节）
- **GEO_OPT**：`TYPE`、`OPTIMIZER`(BFGS/CG/LBFGS)、`MAX_ITER`、`MAX_DR`/`MAX_FORCE`/`RMS_DR`/`RMS_FORCE`（收敛判据）、`KEEP_SPACE_GROUP`。子节 LBFGS/CG/BFGS/TRANSITION_STATE。
- **CELL_OPT**：同 GEO_OPT + `EXTERNAL_PRESSURE`、`KEEP_ANGLES`、`KEEP_SYMMETRY`、`TYPE`。
- **MD（19 关键字 + 14 子节）**：`ENSEMBLE`、`STEPS`、`TIMESTEP`、`TEMPERATURE`、`TEMP_TOL`、`ANNEALING`、`COMVEL_TOL`。子节 LANGEVIN/GLE/CSVR/NOSE/BAROSTAT/THERMOSTAT/RESPA。
- **FREE_ENERGY/METADYN**：`WW`(高斯高度，默认0.1)、`DO_HILLS`、`WELL_TEMPERED`、`DELTA_T`/`WTGAMMA`、`NT_HILLS`/`MIN_NT_HILLS`、`LAGRANGE`、`USE_PLUMED`。与 skill 模板一致。
- **BAND**（NEB）：`NUMBER_OF_REPLICA`、`BAND_TYPE`、`K_SPRING`、`CI_NEB`/`STRING_METHOD`、`ROTATE_FRAMES`/`ALIGN_FRAMES`。
- **CONSTRAINT**：`FIXED_ATOMS`/`COLLECTIVE`/`G3X3`/`HBONDS`/`COLVAR_RESTART`；`SHAKE_TOLERANCE`。

### GLOBAL
- 32 关键字：`RUN_TYPE`、`PROGRAM_NAME`、`PROJECT_NAME`、`PRINT_LEVEL`、`WALLTIME`、`BLACS_GRID`、`PREFERRED_DIAG_LIBRARY`(ELPA/SCALAPACK)、FFT 库选项。

### DFT 概念章（WebFetch）
- **GPW/GAPW**：GAPW 用于全电子/核敏感（NMR/EFG/超精细/XAS）；`&QS METHOD GAPW` + 全电子基组 + `POTENTIAL ALL` + 逐 KIND `LEBEDEV_GRID`/`RADIAL_GRID`；GAPW 专属 EPS 控制硬/软拆分；优先 GPW。
- **HF-ADMM**：`&AUXILIARY_DENSITY_MATRIX_METHOD` 选 `ADMM_TYPE ADMMS`/`ADMM2` 或显式 `METHOD BASIS_PROJECTION`+`ADMM_PURIFICATION_METHOD MO_DIAG`+`EXCH_CORRECTION_FUNC PBEX`；每 KIND `BASIS_SET AUX_FIT`；辅助基过小→校正大降精度，过大→提速少；ADMM 加速交换但**不替代**主基组/网格/SCF 收敛。
- **CUTOFF 收敛**：先固定 `REL_CUTOFF 60`（多数够），扫 `CUTOFF`（体相 Si 实测 250 Ry 即 <1e-8 Ha）；REL_CUTOFF 太低把高斯压到最粗网格→能量误差；仅增 CUTOFF 不增 REL 收敛变慢。
- **K-Points**：Gamma 够用于大超晶胞/绝缘体/孤立体系；金属/小原胞/强色散需收敛 MONKHORST-PACK 网格；**OT 不支持 k 点**（仅对角化）；杂化+k点走 RI-HFXk；DFT+U+k点仅 Mulliken；展宽不能替代 k 点收敛。

### 已内化的 skill 改动（批次 2）
1. **gen_inp.py**：新增 `--surface-dipole`(+`--dipole-dir/pos/switch`)，`surface_dipole_block()` 发射 `&DFT SURFACE_DIPOLE_CORRECTION T`+`SURF_DIP_DIR/POS/SWITCH`；4 个表面模板(geo_opt/static/aimd_md/cell_opt)加 `__SURFACE_DIPOLE_BLOCK__` token。→ 堵住批次1发现的 slab 缺口。
2. **decide.md**：
   - §5 加 **OT↔k点不兼容**警告 + k点收敛原则 + **不对称 slab 表面偶极修正**说明。
   - §6 加 `FIXED_MAGNETIC_MOMENT` 固定磁矩。
   - §7 重写：补 **REL_CUTOFF** 含义与官方收敛流程（先 REL=60 扫 CUTOFF，体相Si 250 Ry 够），修正起步值。
   - §11 ADMM 对照手册：术语对齐 `AUX_FIT`/`BASIS_ADMM_MOLOPT`/`ADMM_TYPE`，加实践检查。
   - §12 加可微调实战参数（ALPHA/NBROYDEN/Kerker BETA/SAFE_DIIS/N_HISTORY_VEC）。
   - 新增 **§15 GAPW**：何时需要、切换方式、skill 当前不支持一键 GAPW 的说明。
3. **校验**：`_validate_all.py` 仍 0 error/0 warning（23 cases，模板改动回归通过）。

### 待办（后续批次）
- [ ] Methods 章剩余：Semi-Empirical(PM6/xTB/DFTB)、QM-MM(MIXED/QMMM)、Embedding、Machine Learning、Linear Scaling、Constrained DFT、Optimization/Transition State 概念。
- [ ] DFT/PRINT 子节逐个精读（DOS/PDOS/BAND_STRUCTURE 已读，其余如 WANNIER90/MULLIKEN/LOWDIN/HIRSHFELD/EFG/超精细细节）。
- [ ] MOTION 子节精读：MD/THERMOSTAT 各恒温器参数、METADYN 完整、BAND/CI-NEB、CONSTRAINT 各类型。
- [ ] 把"后处理该看什么"与 DFT/PRINT 落点对齐（已在 §14 列了性质→后处理，可再细化）。
- [ ] 考虑 gen_inp 是否加 GAPW 开关（当前手动）。

---

## 批次 3（2026-07-14）：MOTION 子节精读 + Methods 概念章

### MOTION 结构（本地 xml 子树确认，13 子节）
GEO_OPT / CELL_OPT / SHELL_OPT / MD / DRIVER / FREE_ENERGY(→METADYN/UMBRELLA_INTEGRATION/ALCHEMICAL_CHANGE) / CONSTRAINT / FLEXIBLE_PARTITIONING / MC / TMC / PINT / BAND。

### MD（MOTION/MD，19 关键字 + 14 子节）
- **ENSEMBLE 严格枚举**（已从 xml 核对）：`NVE` `NVT` `NPT_I` `NPT_F` `NPE_F` `NPE_I` `MSST` `MSST_DAMPED` `HYDROSTATICSHOCK` `ISOKIN` `REFTRAJ` `LANGEVIN` `NVT_ADIABATIC`。**没有笼统 NPT**——必须 NPT_I(各向同性) 或 NPT_F(柔性)。
- 其它关键字：`STEPS`/`MAX_STEPS`/`TIMESTEP`/`TEMPERATURE`/`TEMP_TOL`(重缩放容差)/`COMVEL_TOL`(清质心漂移)/`ANGVEL_ZERO`(清角速度,非周期)/`ANNEALING`/`TEMPERATURE_ANNEALING`(退火)/`INITIALIZATION_METHOD`/`TEMP_KIND`+`SCALE_TEMP_KIND`(分 KIND 控温)。
- 子节：LANGEVIN(GAMMA/NOISY_GAMMA/SHADOW_GAMMA)、MSST、BAROSTAT(PRESSURE/TIMECON/TEMPERATURE/TEMP_TOL/VIRIAL，VIRIAL 仅 NPT_F 可屏蔽分量)、THERMOSTAT(NOSE: TIMECON/LENGTH/YOSHIDA/MTS；CSVR: TIMECON；GLE: S 矩阵；AD_LANGEVIN)、RESPA、SHELL、ADIABATIC_DYNAMICS、REFTRAJ(MSD)、AVERAGES、THERMAL_REGION、PRINT、CASCADE、INITIAL_VIBRATION。

### GEO_OPT / CELL_OPT / CONSTRAINT
- **GEO_OPT**：TYPE/OPTIMIZER(BFGS/CG/LBFGS)/MAX_ITER/MAX_DR/MAX_FORCE/RMS_DR/RMS_FORCE/STEP_START_VAL/KEEP_SPACE_GROUP(+EPS_SYMMETRY/SYMM_REDUCTION/SYMM_EXCLUDE_RANGE/SPGR_PRINT_ATOMS)。子节 LBFGS/CG/BFGS/TRANSITION_STATE(DIMER 二聚体法找 TS)。
- **CELL_OPT**：比 GEO_OPT 多 `TYPE`/`EXTERNAL_PRESSURE`(1 值或 9 分量)/`KEEP_ANGLES`/`KEEP_SYMMETRY`/`CONSTRAINT`(固定压强张量分量)/`PRESSURE_TOLERANCE`。零温/有限温结构优化找平衡胞；与 NPT 动力学系综不同。
- **CONSTRAINT**：SHAKE_TOLERANCE/ROLL_TOLERANCE/CONSTRAINT_INIT；子节 FIXED_ATOMS(冻结原子)/COLLECTIVE(基于 COLVAR)/G3X3/G4X6(几何约束)/HBONDS/VIRTUAL_SITE。

### FREE_ENERGY / METADYN（增强采样）
- `&FREE_ENERGY &METADYN`：WW(默认0.1)/DO_HILLS/WELL_TEMPERED+DELTA_T(或WTGAMMA)/NT_HILLS/MIN_NT_HILLS/MIN_DISP/LAGRANGE/USE_PLUMED+PLUMED_INPUT_FILE/HILL_TAIL_CUTOFF(P/Q_EXPONENT 尾截断)/SLOW_GROWTH/TEMPERATURE(拉格朗日 CV 温度)。子节 METAVAR(+WALL: REFLECTIVE/QUADRATIC/QUARTIC/GAUSSIAN)、MULTIPLE_WALKERS、PRINT(HILLS/COLVAR)。→ 与 skill FES 后处理一致。
- 另：UMBRELLA_INTEGRATION(伞形采样)、ALCHEMICAL_CHANGE(炼金自由能)。

### BAND（NEB 反应路径，MOTION/BAND，9 关键字 + 10 子节）
- NUMBER_OF_REPLICA/BAND_TYPE/POT_TYPE/K_SPRING/CI_NEB/STRING_METHOD/ROTATE_FRAMES/ALIGN_FRAMES/USE_COLVARS/NPROC_REP/PROC_DIST_TYPE。子节 OPTIMIZE_BAND/CI_NEB/STRING_METHOD/REPLICA(各镜像初构)。RUN_TYPE BAND。

### Methods 概念章（WebFetch）
- **Semi-Empirical / xTB**：`&DFT &QS METHOD XTB`+`&XTB`（原生 GFN0/GFN1，或 `GFN_TYPE TBLITE`+`&TBLITE METHOD GFN1/GFN2/IPEA1`）。支持 PBC(Ewald，2026.2+ 自动)、色散 D3(BJ)/D4。比 DFT 快 1–3 量级，覆盖主族+过渡金属；半经验精度，不可替 DFT 定量能垒。DFTB 页未写(`METHOD DFTB`+Slater–Koster 参数文件 mio-1-1/pbc-0-3/3ob/trans3d)。
- **QM/MM**：`METHOD QMMM`+`&QMMM`(`&QM_KIND MM_INDEX` 列 QM 原子；`E_COUPL COULOMB` 静电嵌入 / `NONE` 机械嵌入；`&LINK LINK_TYPE IMOMM` 处理断键边界)+`&MM`(Amber/CHARMS prmtop/psf 力场)。用户须给拓扑+力场文件。DFT 级耦合用 GEEP。适合酶/溶液大体系局部反应。
- **Machine Learning / NNP**：`METHOD NNP`+`&NNP POTENTIAL_FILE_NAME`(预训练势)；支持 NequIP/Allegro/DeePMD/ACE。推理级速度、近 DFT 精度但迁移性差。NNP 页未写(指向 cp2k.org/tools:aml)。
- **Embedding**：`&FORCE_EVAL &EMBED`（Kim-Gordon / QM-QM 量子嵌入）；大体系某碎片需高精度时比全 DFT 便宜、比 QM/MM 自洽。

### 已内化的 skill 改动（批次 3）
1. **decide.md**：
   - §13 重写（v3，手册核对）：补 MD **ENSEMBLE 完整严格枚举**（含 NPT_I/NPT_F 区分）、各恒温器**关键字落点**（LANGEVIN GAMMA / CSVR TIMECON / NOSE TIMECON+LENGTH+YOSHIDA+MTS / GLE / AD_LANGEVIN）、BAROSTAT（PRESSURE/TIMECON/VIRIAL 仅 NPT_F）、初始化关键字（COMVEL_TOL/ANGVEL_ZERO/ANNEALING）。
   - 新增 **§16 选什么计算引擎**：DFT vs xTB / DFTB / QM-MM / NNP / Embedding 判断树 + 各引擎 CP2K 入口（手动设，gen_inp 暂只发 DFT）。
   - 新增 **§17 增强采样与反应路径**：METADYN（WW/DO_HILLS/WELL_TEMPERED/NT_HILLS/LAGRANGE/USE_PLUMED + METAVAR/WALL）、BAND-CI-NEB（NUMBER_OF_REPLICA/K_SPRING/CI_NEB/STRING_METHOD）、CONSTRAINT（FIXED_ATOMS/COLLECTIVE/G3X3/HBONDS/SHAKE_TOLERANCE）。
   - 新增 **§18 CELL_OPT**：TYPE/EXTERNAL_PRESSURE/KEEP_ANGLES/KEEP_SYMMETRY/CONSTRAINT/PRESSURE_TOLERANCE，区分 CELL_OPT(结构优化) vs NPT(动力学系综)。
2. **SKILL.md**：摘要与 `read_when` 关键词补 xTB/DFTB/QM-MM/神经网络势/CELL_OPT/约束/系综/恒温器/自由能；摘要加方法选择+增强采样+CELL_OPT 顾问范围说明。

### 待办（后续批次）
- [ ] METADYN/BAND/CELL_OPT/CONSTRAINT 的输入生成：考虑给 gen_inp.py 加开关（如 `--free-energy`/`--band`/`--cell-opt`/`--constraint`），当前仅 GEO_OPT/CELL_OPT/STATIC/AIMD_MD 模板。
- [ ] DFT/PRINT 子节逐个精读（DOS/PDOS/BAND_STRUCTURE 已读；MULLIKEN/LOWDIN/HIRSHFELD/EFG/超精细/WANNIER90 细节）。
- [ ] Methods 剩余：Post-Hartree-Fock(HSE06/B3LYP 已在 §8/§11)、Optimization/Transition State 概念、Electronic-structure Analysis、Properties、Technologies(Eigensolvers/Accelerators)。
- [ ] 复核 ADDED_MOS/CHOLESKY 在 `&SCF &DIAGONALIZATION` 下的实际落点（手册 SCF 收敛页未展开，待精读 DIAGONALIZATION 子节）。
- [ ] DFTB / NNP 手册页待补，待官方补全后再二次核对引擎入口细节。

---

## 批次 4（2026-07-14）：DFT/PRINT 性质子节精读

### 来源
- 本地 `cp2k_input.xml`：`&DFT &PRINT` 共 **51 个子节**。用 `_manual_kw.py` 逐个抽 MULLIKEN/LOWDIN/HIRSHFELD/EFG(HIRSHFELD_FORCE 实际在 `&FORCE_EVAL &PRINT`)/HYPERFINE_COUPLING_TENSOR/WANNIER90/PDOS/MO_CUBES/STM/MOMENTS/E_DENSITY_CUBE/BAND_STRUCTURE/DOS。
- 通用 `&EACH` 子节：18 个迭代层级关键字（QS_SCF/GEO_OPT/CELL_OPT/MD/METADYNAMICS/PINT…），值=间隔步数（0/负=不打印）。所有 PRINT 开关的打印频率都由它控制。
- 概念章 `methods/properties`（含 Optical/X-Ray/IR/Raman/NMR/STM 子页，NMR 与 NEB 页尚未撰写）。

### 关键结论（已核对）
- **电荷分析优先级**：Hirshfeld(-I) > Lowdin > Mulliken。Mulliken 依赖基组、不基组收敛；HirshFELD `SELF_CONSISTENT T`=Hirshfeld-I（迭代，更准）。
- **EFG / HYPERFINE**：分别 `ELECTRIC_FIELD_GRADIENT` / `HYPERFINE_COUPLING_TENSOR`；核区量需 GAPW(§15) 才准。`HYPERFINE_COUPLING_TENSOR` 用 `INTERACTION_RADIUS`。
- **PDOS** 子节：`COMPONENTS`(按角动量拆)、`NLUMO`(加虚轨道)、`LDOS`/`R_LDOS`。**DOS**：`DELTA_E`(直方图间距)。**BAND_STRUCTURE** + `&KPOINT_SET`、`ADDED_MOS`。
- **STM**：`BIAS`(偏压)、`NLUMO`(正偏压需占+空)、`TH_TORB`(针尖轨道)。**MO_CUBES**：`NHOMO`/`NLUMO`/`STRIDE`/`WRITE_CUBE`。**cube 类**(E_DENSITY/TOT_DENSITY/V_HARTREE/V_XC/ELF)：`STRIDE` 降采样。
- **MOMENTS**：`PERIODIC`(Berry phase)、`REFERENCE`、`MAX_MOMENT`、`MAGNETIC`(仅非周期)。**WANNIER90**：实验性，`SEED_NAME`/`MP_GRID`/`WANNIER_FUNCTIONS`，需 Wannier90。**CHARGEMOL**：调 ChargedMol。

### 已内化
- decide.md **§14 重写为 v4**：完整的 DFT/PRINT 决策表（通用打印机制 + EACH 频率 + 每个性质的"科学问题/子节/关键关键字"），并标注核区量需 GAPW、HIRSHFELD_FORCE 位置。

---

## 批次 5（2026-07-14）：Methods 剩余章精读

### 来源（manual.cp2k.org/trunk）
- `methods/post_hartree_fock`（preliminaries/mp2/rpa/low-scaling）、`methods/optimization`（geometry_and_cell_opt / nudged_elastic_band）、`methods/electronic_structure`（molecular_orbitals/band/population/wannier90）、`methods/properties`（nmr 页为 stub）、`technologies/eigensolvers`、`technologies/accelerators`。

### 关键结论（已核对）
- **Post-HF**：入口 `&DFT &XC &WF_CORRELATION`。三种 MP2 实现：DIRECT_CANONICAL(最贵,无解析力) / MP2_GPW(需 `&INTEGRALS &WFC_GPW` CUTOFF/REL_CUTOFF) / RI_MP2(最便宜、有解析力；需 `BASIS_SET RI_AUX` 或 `AUTO_BASIS RI_AUX LARGE`；`BLOCK_SIZE`/`NUMBER_INTEGRATION_GROUPS`/`MEMORY`)。`SCALE_S`/`SCALE_T` 重标单/三重态（双杂化泛函用）。RPA/SOS-MP2：`&RI_RPA`/`&RI_SOS_MP2`，`QUADRATURE_POINTS`(Minimax 6–8/Clenshaw-Curtis 30–40)、`RSE`/`EXCHANGE_CORRECTION [NONE|AXK|SOSEX]`。HF 参考用 **ADMM**(`&AUXILIARY_DENSITY_MATRIX_METHOD METHOD BASIS_PROJECTION`)+`&HF FRACTION 1.0`+`&SCREENING`+`&INTERACTION_POTENTIAL`(截断库仑)。MP2~N⁵、RPA~N⁴，大体系用 RI/低标度；参考 wfn 先收敛(`WFN_RESTART_FILE_NAME`)。
- **NEB**：`RUN_TYPE BAND`；初/末态+中间镜像在 `&SUBSYS &COORD` 内**空行分隔**或用 `&REPLICA/COORD`；`NUMBER_OF_REPLICA`/`BAND_TYPE [CI-NEB|IT-NEB|SM]`/`K_SPRING`(0.05–0.2)/`CI_NEB`/`ALIGN_FRAMES`/`ROTATE_FRAMES`；`&OPTIMIZE_BAND`+`&DIIS`/`&MD`、`&CONVERGENCE_CONTROL`。过渡态另法 `&GEO_OPT &TRANSITION_STATE &DIMER`。初/末态须先各自 GEO_OPT。
- **Eigensolvers/Accelerators**：OT(不支持金属/k点/取MO) vs 对角化(Davidson/Felbermayr)；ELPA 加速大体系对角化；MP2/RPA 用 COSMA/SpLA 上 GPU；CUDa/HIP/OpenCL GPU 卸载 DBCSR/GRID/ACC；PSMP 混合并行。

### 已内化
- decide.md 新增 **§19 Post-HF**(MP2/RI-MP2/RPA/SOS-MP2 含 ADMM 加速，含具体关键字与取舍)、**§20 NEB/过渡态输入结构**(与 §17 互补：NEB 给初末态找路径/能垒，METADYN 不预设路径探自由能面)、**§21 计算技术**(OT/对角化/ELPA/GPU/PSMP)。
- SKILL.md 摘要补至 §21、触发词加 MP2/RPA/Post-HF/NEB/过渡态/EFG/超精细/Wannier/DOS/PDOS/STM/cube/Hirshfeld/GPU/并行；决库描述更新。

---

## 批次 6（2026-07-14）：gen_inp.py 元动力学进阶开关（闭合 §17）

### 现状核对
- 模板已含 metadyn / neb / vib / qmmm（7 类模板），`_validate_all.py` 24 用例含 metadyn_AuO / neb_Au / neb_al2o3_advanced / qmmm_pm6，全部 0 err/0 warn。CONSTRAINT 的 FIXED_ATOMS 已由 `--fixed-atoms` 发射。
- **缺口**：metadyn 模板的 `&METADYN` 块硬编码（仅 DO_HILLS/NT_HILLS/METAVAR），无 well-tempered/LAGRANGE/WW/PLUMED/MULTIPLE_WALKERS 开关——而这些正是 §17 描述的关键字。

### 改动
- `references/templates/metadyn.inp`：在 `&METADYN` 内加 `__METADYN_WW__` 与 `__METADYN_EXTRA__` 两个 token。
- `scripts/gen_inp.py`：新增 `metadyn_ww_block()` / `metadyn_extra_block()`；argparse 加 `--well-tempered`/`--delta-t`/`--wtgamma`/`--metadyn-ww`/`--lagrange`/`--multi-walker`/`--plumed`/`--plumed-file`；接入 repl dict。
- `_validate_all.py`：新增 `metadyn_adv` 用例（well-tempered+delta-t+ww+lagrange+multi-walker+plumed）。
- SKILL.md：新增「元动力学进阶选项」段；decide.md §17 过时说明改为"gen_inp 现已发射 metadyn/neb 与进阶开关"。

### 校验结果
- `_validate_all.py`：**24 cases 0 error / 0 warning**（含 metadyn_adv）。`_validate_postprocess.py`：ALL PASSED。

### 待办（收敛后可选）
- [x] gen_inp 发射 metadyn 进阶关键字（批次 6 完成）。
- [x] DFT/PRINT 子节精读（批次 4 完成）。
- [x] Methods 剩余章（批次 5 完成）。
- [x] 复核 ADDED_MOS/CHOLESKY 落点（批次 7 完成：**更正**——二者是 `&SCF` 顶层关键字，非 `&DIAGONALIZATION` 子节）。
- [ ] DFTB / NNP 手册页为 stub，待官方补全后二次核对引擎入口。
- [x] CONSTRAINT 的 G3X3/HBONDS 开关（批次 8 完成；COLLECTIVE 因 2026.1 schema 无 `&DEFINE_COLVAR` 仍手动）。
- [x] GAPW 一键开关（批次 8 完成：`--gapw` → `&QS METHOD GAPW`）。

---

## 批次 7（2026-07-14）：SCF 收敛核心子节精读（本地 cp2k_input.xml 逐字核对）

### 关键结论（对照 CP2K 2026.1 `cp2k_input.xml`）
- **ADDED_MOS / CHOLESKY 落点纠正**：二者是 `&SCF` **顶层**关键字，NOT `&SCF &DIAGONALIZATION`。
  - `CHOLESKY` 默认 `RESTORE`；枚举 `OFF/REDUCE/RESTORE/INVERSE/INVERSE_DBCSR`。
  - `ADDED_MOS` 默认 `0`；金属/开壳层/过渡态设数百。
  - `SCF_GUESS` 默认 `ATOMIC`；枚举 `ATOMIC/RESTART/RANDOM/CORE/HISTORY_RESTART/MOPAC/SPARSE/NONE`。
- **`&SCF &DIAGONALIZATION`**：`ALGORITHM` 枚举 = `STANDARD`(默认)/`OT`/`LANCZOS`/`DAVIDSON`/`FILTER_MATRIX`；另 `JACOBI_THRESHOLD/EPS_JACOBI/EPS_ADAPT/MAX_ITER/EPS_ITER`。无 ADDED_MOS/CHOLESKY。
- **`&SCF &MIXING`**：`METHOD` 枚举（默认 `DIRECT_P_MIXING`）= `NONE/KERKER_MIXING/PULAY_MIXING/BROYDEN_MIXING/BROYDEN_MIXING_NEW/MULTISECANT_MIXING`；`ALPHA` 默认 0.4、`BETA`(Kerker) 默认 0.5 bohr⁻¹、`NMIXING/N_SIMPLE_MIX/PULAY_ALPHA`。**仅对角化/线性标度生效，OT 不用**。
- **`&SCF &SMEAR`**：`METHOD` 默认 `ENERGY_WINDOW`；枚举 `FERMI_DIRAC`(配 `ELECTRONIC_TEMPERATURE [K] 300`)/`ENERGY_WINDOW`(配 `WINDOW_SIZE`)/`LIST`；`FIXED_MAGNETIC_MOMENT`(自旋约束)。
- **`&SCF &OUTER_SCF`**：`TYPE/OPTIMIZER/MAX_SCF`(默认10)/`EPS_SCF`/`DIIS_BUFFER_LENGTH`/`EXTRAPOLATION_ORDER`(MD 外推)。
- **`&SCF &OT`**：36 关键字，`MINIMIZER`(CG/DIIS/BROYDEN)/`SAFE_DIIS`/`N_HISTORY_VEC`/`BROYDEN_BETA` 等。
- **`&SCF &MOM`**（最大重叠法）：`MOM_TYPE/START_ITER/OCC_ALPHA/DEOCC_ALPHA/OCC_BETA/DEOCC_BETA/PROJ_FORMULA`，用于占轨锁定（激发态/过渡态）。
- **`&QS`**：`METHOD` 枚举含 `GPW`(默认)/`GAPW`/`GAPW_XC`；GAPW 是 PAW 式全电子，仍用 GTH 赝势+常规轨道基组。

### 改动
- decide.md §12：补 ADDED_MOS/CHOLESKY 落点纠正（指向 §22）。
- decide.md 新增 **§22 SCF 收敛全流程决策**（EPS_SCF/MAX_SCF/SCF_GUESS/ADDED_MOS/CHOLESKY/OT vs 对角化/MIXING/SMEAR/OUTER_SCF/MOM 关键字枚举与取舍 + 收敛决策速查）。
- SKILL.md 摘要/decide.md 索引更新至 §22。

## 批次 8（2026-07-14）：gen_inp 加 GAPW 一键 + CONSTRAINT 进阶（G3X3/HBONDS）

### 改动
- `scripts/gen_inp.py`：argparse 加 `--gapw`、`--constraint-g3x3`/`--g3x3-distances`、`--constraint-hbonds`/`--hbond-atom-type`/`--hbond-targets`；`qs_block()` 支持 `gapw`（`&QS METHOD GAPW`）；`constraint_block()` 扩展 G3X3/HBONDS（保留 FIXED_ATOMS）；repl dict 接入。
- 模板无需改（`__QS_BLOCK__`/`__CONSTRAINT_BLOCK__` token 已就位）。
- `_validate_all.py`：新增 `gapw_static_Si`/`gapw_geoopt_Fe`/`constraint_g3x3_water`/`constraint_hbonds_water` 4 用例。
- decide.md §15(GAPW) 修正"全电子基组+POTENTIAL ALL"误述为"GTH 赝势+常规基组，仅切 METHOD"；§17 补 G3X3/HBONDS 已支持说明；COLLECTIVE 因 schema 缺 `&DEFINE_COLVAR` 仍手动。
- SKILL.md：「其余进阶能力」补 GAPW 与 G3X3/HBONDS 开关。

### 校验结果
- `_validate_all.py`：**28 cases 0 error / 0 warning**（含 4 个新增）。`_validate_postprocess.py`：ALL PASSED。

---

## 批次 9–12（2026-07-14）：边缘子节全补（VIB/COLVAR-PLUMED/FORCEFIELD/DFTB-NNP-EIP-MIXED/XC-VDW）

用户要求"都补"——把之前清单里剩余的全部边缘子节补完。

### 精读来源（权威：本地 `cp2k_input.xml` 2026.1 + 概念章）
- **批次 9 · VIBRATIONAL_ANALYSIS**：顶层 `&VIBRATIONAL_ANALYSIS`（`RUN_TYPE VIBRATIONAL_ANALYSIS`），有限差分 Hessian。关键字 DX / NPROC_REP / FULLY_PERIODIC / INTENSITIES / THERMOCHEMISTRY / TC_TEMPERATURE / TC_PRESSURE；`&PRINT` 含 MOLDEN_VIB / CARTESIAN_EIGS / HESSIAN / ROTATIONAL_INFO。
- **批次 9 · COLVAR / PLUMED**：`&SUBSYS &COLVAR` 定义 28 种 CV（DISTANCE/ANGLE/TORSION/COORDINATION/RMSD/WC/QPARM/COMBINE_COLVAR/HYDRONIUM_* 等）；`&METAVAR COLVAR <idx>` 引用 + SCALE/WALL/LAMBDA。PLUMED 接口在 `&MOTION &FREE_ENERGY &METADYN`：`USE_PLUMED`(逻辑,默认 F) + `PLUMED_INPUT_FILE`(默认 ./plumed.dat)。
- **批次 10 · FORCEFIELD / QM-MM**：`&FORCE_EVAL &MM &FORCEFIELD`：PARMTYPE / PARM_FILE_NAME / VDW_SCALE14 / EI_SCALE14；`&POISSON &EWALD` 的 `EWALD_TYPE` 枚举 NONE/EWALD/PME/**SPME(推荐)**。键合 `&BOND/&BEND/&TORSION/&IMPROPER/&OPBEND`，非键 `&NONBONDED`(LENNARD-JONES/BUCKINGHAM/TERSOFF/EAM…)。QM/MM `&QMMM`：E_COUPL(GAUSS/SPLINE/NONE)。
- **批次 11 · 其它方法**：`&FORCE_EVAL &QS &DFTB`(`&PARAMETER` 选 SK 集：mio-1-1/pbc-0-3/ob2/3ob/trans3d)；`&QS &XTB`；`&FORCE_EVAL METHOD NNP`(NNP_INPUT_FILE_NAME n2p2/RuNNer + SCALE_FILE_NAME)；`METHOD EIP`(EIP_MODEL)；`METHOD MIXED`(`&MIXED` MIXING_TYPE/NGROUPS)。采样器 `&MOTION &TMC`(蒙特卡洛/热力学)、`&PILE`/`&PINT`(路径积分量子核)。
- **批次 12 · XC_FUNCTIONAL / VDW_POTENTIAL**：内置泛函名对照 xml（PADE/PBE/BP86/BLYP/TPSS/SCAN/PBE0/B3LYP/HSE06/BEEFVDW/LIBXC…）。`&DFT &XC &VDW_POTENTIAL`：`POTENTIAL_TYPE` + `&PAIR_POTENTIAL`(TYPE DFTD3/DFT-D3(BJ)，REFERENCE_FUNCTIONAL/SCALING/R_CUTOFF) + `&NON_LOCAL`(TYPE vdW-DF/vdW-DF2/optB88-vdW/rVV10，KERNEL_FILE_NAME/CUTOFF/PARAMETERS)。补全 §1 泛函写法与 §4 色散结构。

### 内化改动
- decide.md 新增 **§23 振动分析/声子/IR**（VIBRATIONAL_ANALYSIS 决策表）、**§24 COLVAR 与 PLUMED 接口**（28 种 CV + metadyn 接法 + USE_PLUMED）、**§25 经典力场 FORCEFIELD 与 QM/MM 衔接**（PARMTYPE/EWALD_TYPE/键合非键）、**§26 其它 FORCE_EVAL 方法（DFTB/NNP/EIP/MIXED）+ 采样器（TMC/PILE）**、**§27 XC_FUNCTIONAL 内置泛函清单 + VDW_POTENTIAL（PAIR_POTENTIAL/NON_LOCAL）**。
- SKILL.md：摘要扩至 §27、decide.md 索引扩至 §1–§27、触发词补振动/力场/NNP/EIP/MIXED/COLVAR/PLUMED/XC_FUNCTIONAL/vdW-DF/TMC/PILE。
- 确认 `gen_inp.py` 早已支持 `--type vib`（vib.inp 模板正确：`RUN_TYPE VIBRATIONAL_ANALYSIS` + `&VIBRATIONAL_ANALYSIS`）与 `--plumed`；DFTB/NNP/EIP/MIXED 等边缘引擎按 §26 顾问手动指导（不发射，符合"顾问非自动驾驶"定位）。

### 校验结果
- `_validate_all.py`：**28 cases 0 error / 0 warning**（文档改动无回归，vib/qmmm 用例已含）。`_validate_postprocess.py`：ALL PASSED。

### 覆盖状态（截至本批次）
cp2k-aimd 手册学习**已基本覆盖** CP2K 2026.1 Input Reference 核心路径 + Methods/Technologies/Properties 概念章 + 全部边缘子节（VIB/COLVAR/PLUMED/FORCEFIELD/DFTB/NNP/EIP/MIXED/TMC/PILE/XC/VDW）。唯一未二次核对项：DFTB/NNP 引擎入口的"官方概念章"仍是 stub（已从 xml + 既有知识内化，等官方补全可再复盘）。


