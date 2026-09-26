# gen_inp.py 进阶开关全集（催化计算常用）

> **这是 SKILL.md 的配套参考**：SKILL.md 只保留主流程与最常用开关，
> 完整的进阶能力（泛函阶梯 / ADMM / Properties / SCF 工具箱 / MD / 逐原子 KIND /
> NEB / 元动力学 / QM-MM）全部收在本文件，避免入口层过长。
>
> 读法：先看 §0 快速定位，再跳到对应小节。所有开关都由 gen_inp.py 生成，
> **不必手改模板**。每条都对照 CP2K 2026.1 官方 `cp2k_input.xml` 校验过。

---

## 0. 快速定位

| 我要做什么 | 看哪节 | 核心开关 |
|---|---|---|
| 提高泛函精度（PBE → Meta-GGA → 杂化） | §1 泛函阶梯 | `--functional TPSS/SCAN/HSE06/B3LYP` |
| 杂化太贵，要降本 | §2 ADMM | `--admm` |
| 要 DOS/PDOS/应力/Wannier/cube 等输出 | §3 Properties | `--properties ...` |
| SCF 不收敛，要调混合/OT/阈值 | §4 SCF 工具箱 | `--mixing-method` / `--ot-minimizer` / `--eps-scf` |
| MD 要换恒温器 / 系综 / 续算 / 按时限收尾 | §5 MD 增强 | `--thermostat` / `--ensemble` / `--restart-freq` / `--walltime` |
| 自旋 / 色散 / 固定原子 / 表面偶极 / k 点 | §6 其余进阶 | `--multiplicity` / `--dispersion` / `--fixed-atoms` |
| 强关联过渡金属要 DFT+U | §7 逐原子 KIND | `--kinds "Fe:...:U=3"` |
| 算过渡态（NEB） | §8 NEB | `--xyz-replicas` / `--optimize-band` |
| 算自由能面（元动力学） | §9 元动力学 | `--well-tempered` / `--metadyn-ww` / `--plumed` |
| 多尺度 QM/MM | §10 QM/MM | `--type qmmm` |

---

## §1 泛函阶梯

- **GGA**：`--functional PADE/PBE`（默认；结构优化/筛选性价比最高）。
- **Meta-GGA**：`--functional TPSS` / `SCAN` —— 精度介于 PBE 和杂化之间。对吸附能、弱作用、表面反应比 PBE 明显更准，价格仅 ~1.5-2x PBE。**推荐作为 PBE→HSE06 的中间台阶**。
- **杂化泛函**：`--functional HSE06` / `B3LYP` → 生成 `&HF` 块（反应能/带隙最准）。**务必加 `--admm`**（见 §2），否则大体系上天价。

## §2 ADMM 杂化降本

- **`--admm`** → 自动生成 `&AUXILIARY_DENSITY_MATRIX_METHOD ADMM` 块。
  - 用 cFIT/FIT 辅助基组计算精确交换部分，**成本降低 3-5x**。
  - 对 >50 原子的杂化计算几乎是必须的；精度损失通常 <0.01 eV。
  - recommend.py 对 HSE06/B3LYP 默认推荐开启。

## §3 Properties 输出

> **放置规则（已对照官方 cp2k_input.xml 核对）**：CP2K **没有** `&PROPERTIES` 容器块能直接吃 DOS/PDOS/STRESS/DIPOLE。
> 这些打印项必须落到正确的 `&PRINT` 子节：
> - `dos` / `pdos` / `cube` / `band` → **`&DFT &PRINT`**（`&DOS` / `&PDOS` / `&E_DENSITY_CUBE` / `&BAND_STRUCTURE`）。
> - `stress` → **`&FORCE_EVAL &PRINT`**（`&STRESS_TENSOR`）。
> - `wannier` → **`&DFT &LOCALIZE &PRINT`**（`&WANNIER_CENTERS`）。
> - `dipole`（偶极矩）是 **MM/MIXED 专属**，Quickstep DFT 不发射，故 `--properties` 不接 `dipole`。

- **`--properties dos pdos stress band cube wannier mulliken lowdin hirshfeld charges mo elf vhartree moments`** → 全部落 `&DFT &PRINT`（除 stress 在 `&FORCE_EVAL &PRINT`、wannier 在 `&DFT &LOCALIZE`）。
  - `pdos`：投影态密度（金属/半导体必做；看 d-band center、元素贡献）；`&EACH QS_SCF 1` 每 SCF 打印。加 `--ldos-list "1..26"` 可进一步发射 `&PDOS &LDOS LIST <原子>` 做逐原子投影（范围 `a..b` 会自动展开为显式原子号，兼容官方解析器）。`--pdos-nlumo N`（默认 1；nico 用 30 打印全部空轨道）、`--pdos-nhomo N` 控制投影的轨道窗口。
  - **输出风格**：`--print-style SILENT` 让 `mulliken`/`lowdin`/`hirshfeld` 以 `&NAME SILENT` + `FILENAME <名>` 安静输出（复刻 nico 写法）；默认 `ON`（不写 FILENAME）。`--cube-stride "1 1 1"` 设置所有 cube 的 `STRIDE`：**默认 `5 5 5` 是本 skill 的历史默认值，既不是 CP2K 官方默认（`2 2 2`）也不是讲义用法（`1 1 1`）**——`5 5 5` 等于每 5 个格点取 1 个（抽掉 ~99% 的格点），画 ELF/静电势时"有棱有角"；`1 1 1` 最平滑但文件大（格点数 ×125），`2 2 2` 与官方对齐。**要看图就显式写 `--cube-stride "1 1 1"`**。
  - `band`：能带结构（需配合 `&BAND_STRUCTURE &KPOINT_SET`）。
  - `stress`：应力张量（CELL_OPT / 压强计算）。**注意它与 `--stress-tensor` 是两件事**：`--properties stress` 只发 `&FORCE_EVAL/&PRINT/&STRESS_TENSOR`（**打印**），`--stress-tensor analytical|numerical` 发 `&FORCE_EVAL/STRESS_TENSOR`（**算不算、怎么算**）。官方默认是 `STRESS_TENSOR NONE`；`--type cell_opt` 现在默认发 `ANALYTICAL`。
  - `cube`：电子密度 cube 文件（可视化电荷分布）。
  - `mulliken` / `lowdin` / `hirshfeld`：三种布居/分电荷分析（电荷转移、键极性、Bader 前处理）。
  - `charges`：一次性发射 `mulliken` + `lowdin` + `hirshfeld`。
  - `mo`：`&MO_CUBES`（NHOMO/NLUMO，分子轨道 cube 可视化）。
  - `elf`：`&ELF_CUBE`（电子局域函数，看成键/孤对）。**注意 CP2K 段名为单数 `ELF_CUBE`**。
  - `vhartree`：`&V_HARTREE_CUBE`（Hartree 势 cube）。**段名单数 `V_HARTREE_CUBE`**。
  - `moments`：`&MOMENTS`（电/磁多极矩）。
  - `wannier`：Wannier 中心。发射 `&DFT &LOCALIZE METHOD CRAZY` + `&PRINT &WANNIER_CENTERS`，并带上 TRAVIS 需要的三件套：**`IONS+CENTERS`**（官方默认 F；不开它 Wannier 中心**不与原子核写在同一个文件里**，`X` 行拿不到）、**`FILENAME wannier.xyz`**、以及 `&EACH`（MD 家族用 **`MD 1`**，逐 MD 步输出；static/geo_opt/vib 用 `QS_SCF 10`）。⇒ `--properties wannier` 的产物可直接喂 `postprocess.py travis`。

## §4 SCF 收敛工具箱

- **混合方法**：`--mixing-method broyden`（默认）/ `pulay`（金属推荐）/ `multisecant`（极难收敛）。`--mixing-alpha`（默认 0.4；nico 用 0.1）、`--mixing-beta`（BROYDEN 残差混合，nico 用 1.5；默认不发射）、`--mixing-nbroyden`（默认 8）。
  > 注：`FULL_ALL` **不是** `&MIXING` 的合法 `METHOD`（`cp2k_input.xml` 中 `&MIXING` 仅 BROYDEN_MIXING / PULAY_MIXING / MULTISECANT_MIXING）；旧资料里的 `FULL_ALL` 写法在官方解析器中报错，已废弃。
- **SCF 路线（OT 还是对角化）**：`--scf-route auto`（默认）/ `ot` / `diag`。
  - `auto`：**不传 `--ot-minimizer` ⇒ 对角化**（`&DIAGONALIZATION`，历史默认行为）；**传了 `--ot-minimizer` ⇒ 走 `&OT`**。
  - `ot`：强制 `&OT`；没给 `--ot-minimizer` 时用官方默认 `CG`。
  - `diag`：强制对角化（会忽略 `--ot-minimizer`，并在 stderr 说明）。
- **OT 优化器**：`--ot-minimizer diis|cg|broyden|sd`（**不传 = 不发 `&OT`**，走对角化）。**只要显式给值就发 `&OT` + `MINIMIZER <值>`** —— 包括 `diis`。官方 `&OT MINIMIZER` 默认是 **CG**；`DIIS/CG/BROYDEN/SD` 都合法。
  - 配套旋钮：`--ot-preconditioner full_all|full_single_inverse|full_single|full_kinetic|full_s_inverse|none`（**默认仍发 `FULL_SINGLE_INVERSE`；CP2K 官方默认是 `FULL_KINETIC`**）、`--ot-linesearch none|2pnt|3pnt|gold`（默认不发 ⇒ CP2K 用 `2PNT`）。
  - 讲师建议的"AIMD 前先测 CG vs DIIS"现在可以真的测了：`--ot-minimizer cg` vs `--ot-minimizer diis`（两者都发 `&OT`）。
  > 注：`LBFGS` **不是** `&OT` 的合法 `MINIMIZER`（`&OT` 仅 DIIS / CG / BROYDEN / SD）；`LBFGS` 是 `&GEO_OPT` 的 `OPTIMIZER`，二者不要混淆。
- **QS 精度**：`--qs-eps 1e-12`（数值精度不够时调高）。
- **MGRID 截断能**：`--cutoff N`（默认模板 300；金属 350–500）、`--rel-cutoff N`（默认 60）。直接改 `&MGRID CUTOFF/REL_CUTOFF`。
- **SCF 收敛阈值/步数**：`--eps-scf 1.0E-6`（默认 1.0E-7）、`--max-scf 500`（默认 300）。
- **SCF 收敛辅助关键字**：`--eps-diis 0.05`（DIIS 截断，nico 用）、`--added-mos 500`（金属/展宽额外 MO，nico 用）、`--cholesky INVERSE`（重叠矩阵 Cholesky；默认不发射，nico 用 INVERSE）、`--diagonalization-eps-adapt 0.01`（自适应 DIIS 阈值；仅在含 `&DIAGONALIZATION` 的模板发射，nico 用）。
- **续算 / 初猜**：`--scf-guess ATOMIC`（默认）/ `RESTART`（从既有波函数续算）+ `--wfn-restart ./cp2k-RESTART.wfn`（发射 `&DFT WFN_RESTART_FILE_NAME`；注意此关键字属于 `&DFT` 而非 `&SCF`）。

## §5 MD 增强

- **恒温器选择**：`--thermostat csvr`（默认）/ `nose` / `langevin`（表面催化推荐；自动映射为稳健的 `AD_LANGEVIN`）。
  > **`--ensemble nve` 时不发 `&THERMOSTAT`**：NVE 是微正则系综（官方原文 "constant energy (microcanonical)"，N、V、E 恒定），**按定义不控温**；`&THERMOSTAT/TYPE` 的官方说明是"用于**恒温系综**的热浴"⇒ NVE 下热浴不生效。此前模板的两行 token（`ENSEMBLE __ENSEMBLE__` + `__THERMOSTAT_BLOCK__`）会一起发射，得到"看起来配了热浴、实际完全不控温"的假象；现在 gen_inp 会省略该段并在 stderr 说明，`validate_inp.py` 对"`ENSEMBLE NVE` + `&THERMOSTAT` 并存"报 warning。要控温请用 `--ensemble nvt`（默认）/ `npt`。
  > 同理 `--type metadyn` 的模板把 `ENSEMBLE NVT` 与 CSVR 热浴**写死在模板里**，`--ensemble` 对 metadyn 不生效（gen_inp 会在 stderr 说明）。
- **系综扩展**：`--ensemble npt`（自动加 BAROSTAT，等压等温系综）。
- **续算支持**：`--restart-freq N`（每 N 步写 RESTART 文件；长 AIMD 必开）。
- **按时限干净收尾**：`--walltime <秒>` → `&GLOBAL WALLTIME`。**给的值要比队列时限略小**
  （如 24 h 限制用 `--walltime 82800`，即 23 h）。CP2K 会在**被批处理系统杀掉之前**主动停手，
  留下可用的 restart 文件；不给就被 `SIGKILL`，这一段轨迹与波函数全丢。
  官方教程把"**批处理时限**"列为重启的**第一大成因**（`T09 P9` 原文 "for a clean job ending
  and restart"；另见 `T07 P14` / `T08 P18`）。**长 AIMD 应当 `--walltime` 与 `--restart-freq` 一起给。**

## §6 其余进阶能力

- **自旋极化（开壳层）**：`--multiplicity N`（O₂→3、自由基→2）→ 自动 `UKS`+`MULTIPLICITY`+`WF_INTERPOLATION ASPC`。
- **色散**：`--dispersion` → `&VDW_POTENTIAL` DFT-D3（弱吸附/层间必备，需 `dftd3.dat`）。
- **固定原子**：`--fixed-atoms "1..54 289..324"` → `&CONSTRAINT &FIXED_ATOMS`，冻结 slab 底层。
- **GAPW 全电子**：`--gapw` → `&QS METHOD GAPW`（核区 EFG/超精细/NMR 必备；仍用 GTH 赝势+常规轨道基组，仅切换核心密度重构，已校验合法）。配合 `--properties efg hyperfine` 开核区性质。
- **几何约束（SHAKE）**：`--constraint-g3x3 "1 2 3" --g3x3-distances "1.0 1.5 2.0"` → `&CONSTRAINT &G3X3`（3 原子/3 距离约束）；`--constraint-hbonds --hbond-atom-type O --hbond-targets "0.96 1.0"` → `&CONSTRAINT &HBONDS`（X-H 键 SHAKE）。均经官方解析器校验。COLLECTIVE(`&COLVAR`约束) 因 2026.1 schema 未建模 `&DEFINE_COLVAR`，仍由顾问手动指导。
- **非周期/表面**：`--periodic none`（孤立分子→WAVELET + **自动补 `&TOPOLOGY/&CENTER_COORDINATES`**）/ `xy`（表面 slab，z 非周期）。
  > 🔴 居中那两行不是装饰：WAVELET 求解器要求「单胞边界处电子密度为 0」（官方 T24 §3.4），
  > 分子横跨边界会**静默算错**——实测能量差 12 Ha、|ΣF| 达 24.7 a.u.，而 CP2K 不报错。
  > 详见 `decide.md §5`。
- **表面偶极修正**：`--surface-dipole`（可选 `--dipole-dir Z` / `--dipole-pos 0.5` / `--dipole-switch 0.3`）→ `&DFT SURFACE_DIPOLE_CORRECTION T`，用于吸附质单侧或两端终止不对称 slab，恢复真空区平整势、加速 SCF 收敛（仅 `PERIODIC xy`/`x?` 有意义）。
- **k 点**：`--kpoints "6 6 6"`（块体金属）/ `"4 4 1"`（表面）→ `&KPOINTS MONKHORST-PACK`。
- **收敛辅助**：`--outer-scf`（OT 难收敛）、`--smear`（金属）、`--print-forces`（输出原子力）、`--charge N`。
- **振动分析**：`--type vib` → `RUN_TYPE VIBRATIONAL_ANALYSIS`（确认极小点/过渡态、求 IR）。**固定原子算频率时必须多开并行结构**：`NPROC_REP` 取小、结构数（= 总核数 / `NPROC_REP`）取大，否则频率不可信（例：56 核写 `--nproc-rep 7` ⇒ 8 个并行结构）。`--type vib` + `--fixed-atoms` 时 gen_inp 会在 stderr 复述这条。
  > 模板 `vib.inp` 里两行容易看错的默认值（**模板本身保持原样以免改变已有生成物**，口径记在这里）：
  > - `DX 0.01`：有限位移步长，单位是 **bohr**（官方默认 0.01 bohr ≈ 0.0053 Å）。
  > - `FULLY_PERIODIC T`：T = **不**从 Hessian 里清理转动（表面/周期性体系要这样）；F = 清除平动+转动（气相分子用，才能得到 3N−6 个真振动）。
  > - **输出个数**：固定原子时 CP2K 仍会打印 **3N 个**频率值并全部列为结果（3 个自由原子 → 9 个）；真正的分子内振动只有 3N−6 个（→ 3 个）。气相分子配 `FULLY_PERIODIC F` 才会只给 3N−6 个。
- **优化器选择**：`--optimizer bfgs`（默认，块体）/ `lbfgs` / `cg`（slab/缺陷常用；自动发射 `&LBFGS`/`&CG` 子节与 `&LINE_SEARCH`）。`cell_opt` 默认 `cg`；`geo_opt` 默认 `bfgs`。覆盖庚子例子里的 LBFGS/CG 写法。
- **应力张量计算方式**：`--stress-tensor analytical` / `numerical` → 在 `&FORCE_EVAL` 层发射 `STRESS_TENSOR` 关键字（控制"如何算"应力；与 `--properties stress` 仅"打印"应力区分开）。覆盖 cu-kpoint 例子的 `STRESS_TENSOR ANALYTICAL`。
  > **`--type cell_opt` 现在默认发 `STRESS_TENSOR ANALYTICAL`**：官方 `&FORCE_EVAL/STRESS_TENSOR` 默认是 `NONE`，而 CELL_OPT **靠应力/压力驱动**（官方 §4.2 的 CELL_OPT 示例第一行就写了它）——没有它晶胞优化拿不到更新方向。显式写 `--stress-tensor numerical` 可覆盖成数值应力。
- **晶胞方向约束（保真空层）**：`--cell-opt-constraint z`（取值 `none|x|y|z|xy|xz|yz`）→ `&MOTION/&CELL_OPT CONSTRAINT Z`，**只弛豫物理上有意义的晶胞方向**。二维材料/表面 slab 建议随手带上（`--type cell_opt --periodic xy` 时 gen_inp 会在 stderr 提醒）。注意：它与原子约束 `--fixed-atoms`（`&MOTION/&CONSTRAINT/&FIXED_ATOMS`）**不是一回事**。
- **晶胞对称性**：`--cell-symmetry cubic|hexagonal|tetragonal|orthorhombic|monoclinic|triclinic|rhombohedral|…` → `&SUBSYS/&CELL SYMMETRY <值>`。**模板里的 `KEEP_SYMMETRY T` 必须配它才有意义**（官方 Note：初始对称性必须在 `&CELL` 里指定；`&CELL/SYMMETRY` 默认 `NONE`）。不给该开关时 `KEEP_SYMMETRY` 是空转，`gen_inp.py` 会在 stderr 提醒、`validate_inp.py` 也会 warning。
  > `cell_opt` **不需要**再加一个空的 `&GEO_OPT` 段：官方 `&CELL_OPT/TYPE` 默认 `DIRECT_CELL_OPT`，含义就是"原子与晶胞**同时**优化"（`TYPE GEO_OPT` 那种"先优化原子、再优化晶胞"的交替方案才要求同时定义 `&GEO_OPT`，而且 `TYPE` 在 CP2K 2026.2 已被移除）。
- **多元素**：`--elem Au O --basis DZVP-MOLOPT-SR-GTH DZVP-GTH-PADE --potential GTH-PBE-q11 GTH-PADE-q6`（逐元素 &KIND）。
- **从文件读结构（TOPOLOGY）**：`--topology POSCAR.cif --topology-format cif`（也支持 xyz / pdb / extxyz）→ 发射 `&SUBSYS &TOPOLOGY COORD_FILE_NAME <file> COORD_FILE_FORMAT <fmt>`，替代 `&COORD`。覆盖 cu-kpoint / nico / LiGePS / al2o3-slab 等从 CIF/POSCAR 读结构的例子（与 `--xyz`/`--coord` 互斥）。
- **坐标走 `@INCLUDE`（讲师主推写法）**：`--coord-include coord.inc` → 发射 `&COORD` + `@INCLUDE 'coord.inc'` + `&END COORD`，坐标本体留在外挂文件里（CP2K 前处理器在 `&COORD` 内照样展开）。**该文件必须是"去掉 xyz 前两行"的纯坐标行**；路径相对 `.inp` 所在目录解析。`validate_inp.py` 会递归展开被 include 的文件（缺文件会报 error，不会静默通过）。
- **输出 PDB 轨迹**：`--trajectory-format pdb`（取值 `xmol|xyz|pdb|dcd|atomic|dcd_aligned_cell`）→ `&MOTION/&PRINT/&TRAJECTORY FORMAT PDB`（模板已有 `&TRAJECTORY` 就加一行；没有就新建 `&PRINT` 段 + `&EACH MD 1`）。官方默认是 **XMOL**（不含晶胞）；**晶胞在变的场景（cell_opt / NPT AIMD）建议 `pdb`**，否则轨迹里看不到盒子。
- **氘代换步长**：`--deuterate` → 把所有 H 的 `&KIND MASS` 设成 2（已显式写 `mass=` 的条目不覆盖）。O–H 3300 cm⁻¹ → O–D ~2500 cm⁻¹，含氢体系 `--timestep` 可从 1.0 fs 放宽到 ~1.2 fs（仍建议先做小步数能量守恒测试）。`--timestep > 1` 且体系含 H 而未氘代时，gen_inp 会在 stderr 提醒。

## §7 逐原子 KIND 控制（DFT+U / 逐原子自旋 / 同位素质量）

- **`--kinds`**（覆盖 `--elem/--basis/--potential`，精细控制每个 `&KIND`）：
  格式 `NAME:ELEMENT:BASIS:POTENTIAL` 加可选 `U=<eV>` `mag=<f>` `mass=<f>` `L=<int>` `noramp`。
  - `NAME` 可与 `ELEMENT` 不同（同一元素的不同自旋/氧化位点，如 `Fe` / `Fe2` / `Fe3` 均 `ELEMENT Fe`）。
  - 只给 3 段 `NAME:BASIS:POTENTIAL` 时，`NAME` 同时作为 `ELEMENT`。
  - `U=<eV>` → 自动发射 `&DFT_PLUS_U`（`U_MINUS_J [eV]`、`L` 默认 2、带 ramping 收敛辅助），并把 `PLUS_U_METHOD` 注入 `&DFT`（默认 MULLIKEN，可用 `--plus-u-method` 改 LOWDIN/MARZARI/DUDEI）。强关联过渡金属氧化物（Fe₃O₄、TiO₂ 等）常用。
  - `mag=<f>` → 逐原子 `MAGNETIZATION`（不同原子不同自旋态，如 Fe₃O₄ 的 +5/+4/−5 三种自旋）。
    > **`L` 的口径**：gen_inp.py **发射** `L 2`（d 壳层）；**CP2K 官方默认 `L = -1`**，所以手写输入卡时 d 电子必须自己写 `L 2`、f 电子写 `L 3`（可用 `L=<int>` 覆盖）。
    > **`U_RAMPING` 的单位**：`&DFT_PLUS_U` 里 `U_MINUS_J` 与 `U_RAMPING` 的**默认单位都是 hartree**。凡以 eV 思考的数都要写成 `U_MINUS_J [eV] <值>`（gen_inp 自动带的 `[eV]` 就是这个作用），否则 `0.1` 会被当成 0.1 hartree ≈ 2.72 eV。
  - `mass=<f>` → 逐原子 `MASS`（同位素或人为质量，如 Au 用 19.7 加速动力学）。
  - `noramp` → 去掉 `U_RAMPING` 系列（Au-TiO₂ 的 Ti 写法）；默认带 ramping（Fe₃O₄ 写法）。
  - 与 `--admm` 同时用时，每个 `&KIND` 自动加 `BASIS_SET AUX_FIT`。
  - 例：`--kinds "Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=5.0:U=3" "Fe2:Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=4.0:U=3" "Au:DZVP-MOLOPT-SR-GTH:GTH-PBE-q11:mass=19.7"`

## §8 NEB 进阶选项（--type neb）

- **多副本外部读取**：`--xyz-replicas ./0.xyz ./1.xyz ... ./N.xyz` → 每个文件发射一个 `&REPLICA COORD_FILE_NAME <file>`，`NUMBER_OF_REPLICA` 自动设为文件数（覆盖 al2o3/neb 从 `./0.xyz..` 读副本的写法）。与内联 `--xyz-init`/`--xyz-final` 互斥（内联只产生首末两帧）。
- **带点链优化方式**：`--optimize-band MD`（默认，发射 `&OPTIMIZE_BAND OPT_TYPE MD` + `&MD` 退火块）/ `DIIS`（发射 `OPT_TYPE DIIS`，配合 `--optimize-end-points F` 固定端点，即 al2o3/neb 写法）。
- **帧对齐 / 旋转**：`--align-frames T|F`（默认 T）/ `--rotate-frames T|F`（默认 F）→ `&BAND ALIGN_FRAMES` / `ROTATE_FRAMES`。空位迁移等"不想被对齐扰动路径"的情形设 F。
- **spring 常数 / 诊断输出**：`--k-spring 0.08`（默认 0.02；一般 0.02~0.08）。**单位是原子单位 hartree/bohr²**（官方 XML 对该关键字不标注单位 ⇒ CP2K 内部原子单位），不要按 eV/Å² 理解。`--program-run-info`（发射 `&BAND &PROGRAM_RUN_INFO ON`）、`--convergence-info`（发射 `&BAND &CONVERGENCE_INFO ON`）。
- **收敛判据**：`--neb-max-force`（默认 `0.0006`）、`--neb-rms-force`（默认 `0.0003`）→ `&BAND/&CONVERGENCE_CONTROL`。
  > 这三个值的关系要说清：**CP2K 官方默认是 `MAX_FORCE 4.5E-4` / `RMS_FORCE 3.0E-4`**；本 skill 的模板刻意用 `6.0E-4` —— 与 `geo_opt.inp` 的 `MAX_FORCE 6.0E-4` **同档**，目的是让"结构优化 / 过渡态 / 频率"三件套用同一把尺子（三件套的 `&FORCE_EVAL` 也必须不变），这样能垒与虚频才可比。讲者经验里也有人放宽到 `1E-3`。要跟官方默认对齐就 `--neb-max-force 4.5E-4`。
  > 注意 `&BAND/&CONVERGENCE_CONTROL` 与 `&GEO_OPT`/`&CELL_OPT` 的 `MAX_FORCE` 是**两套独立关键字**（本开关只改前者）。
- 示例（复刻 al2o3/neb）：`--type neb --xyz-replicas ./0.xyz ./1.xyz ./2.xyz ./3.xyz ./4.xyz ./5.xyz --optimize-band DIIS --optimize-end-points F --align-frames F --rotate-frames F --program-run-info --convergence-info --band-type CI-NEB --nproc-rep 28 --k-spring 0.08`

## §9 元动力学进阶选项（--type metadyn，对应 decide.md §17）

- **退火/温标**：`--well-tempered`（发射 `WELL_TEMPERED T`）+ `--delta-t 1500`（偏置温度 DELTA_T [K]，如 1500）+ 可选 `--wtgamma <γ>`（或用 WTGAMMA 替代 DELTA_T）。退火元动力学让山随时间变扁、收敛更稳。
- **山高**：`--metadyn-ww 0.05`（发射 `WW`，hill 高度，hartree；默认 0.1；越大山越疏、自由能面越平滑）。
- **扩展拉格朗日**：`--lagrange`（发射 `LAGRANGE T`，CV 带质量被动力学传播，适合有质量/转动的 CV）。
- **多 walker**：`--multi-walker`（发射 `&MULTIPLE_WALKERS`，协作式元动力学加速填面）。
- **PLUMED 驱动**：`--plumed` + `--plumed-file plumed.dat`（发射 `USE_PLUMED T` + `PLUMED_INPUT_FILE`，用 plumed 定义 CV 与偏置，CP2K 当执行器）。
- 示例：`--type metadyn --project surf --elem Au O --well-tempered --delta-t 1500 --metadyn-ww 0.05 --lagrange --multi-walker`
- 模板默认 `DO_HILLS` + `NT_HILLS 50` 已撒山；CV 用 `&SUBSYS &COLVAR` 定义、`&METAVAR` 引用（模板给的是占位 ATOMS 1 2 / 1 3，需按你的体系改成真实原子号与 CV 数）。

## §10 QM/MM（--type qmmm，半经验 PM6 做 QM 区）
- **结构**：`METHOD MIXED` + `&MULTIPLE_FORCE_EVALS FORCE_EVAL_ORDER 2 3 MULTIPLE_SUBSYS T`，耦合两个子 `&FORCE_EVAL`：① `METHOD FIST`（MM，经典力场）；② `METHOD Quickstep` 且 `&QS METHOD PM6`（QM，半经验，无需基组/赝势）。`&MIXED MIXING_TYPE GENMIX` 用 `MIXING_FUNCTION E1+E2` 把两区能量相加；`&MAPPING` 用 `&FRAGMENT 1`(QM 原子区间) / `&FRAGMENT 2`(MM 原子区间) 定义分区。
- **参数**：
  - `--qm-elem C H O` / `--mm-elem Cu`（QM 区元素 / MM 区元素）。
  - `--qm-method PM6`（默认；也支持 PM3 / AM1 / RM1 / MNDO）。
  - `--qm-atoms "1 50"` / `--mm-atoms "51 2000"`（FRAGMENT 区间，必填真实值）。
  - `--topology ./s`（全系统坐标，MIXED + FIST 两个 SUBSYS 共用）/ `--qm-topology ./f`（QM 片段坐标，Quickstep SUBSYS 用）。
  - `--qmmm-run-type MD`（默认；用 `GEO_OPT` 可松弛 QM 区）/ `--group-partition "2 6"`（各子 eval 的 MPI 核数）。
- **重要**：FIST 的 `&NONBONDED` 当前只生成占位骨架（每个 MM 元素的 `&LENNARD-JONES` 自对，EPSILON=0），**必须先填入真实力场参数**（GENPOT / EAM / Buckingham）与 `&FRAGMENT` 原子区间、坐标文件才能跑物理合理的 QM/MM。COORD 用 `COORD_FILE_FORMAT`（官方解析器仅认这个，比例子里的旧 `COORDINATE` 更通用）。
