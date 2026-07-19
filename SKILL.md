---
title: "CP2K 计算助手（会思考的版本 v2）"
summary: "基于庚子计算《AIMD与CP2K讲义》(1-5)、《理论催化计算实战教学》番外篇、《CP2K使用入门》及 CP2K.inp 思维导图提炼。内置'思考层'：recommend.py 推理参数(泛函含Meta-GGA TPSS/SCAN/杂化HSE06/B3LYP+ADMM降本/基组/赝势/自旋/色散/k点/SMEAR/CUTOFF/Properties/恒温器)，diagnose.py 诊断输出，postprocess.py 后处理引擎(RDF/MSD/扩散/VACF/IR/PDOS/Bader/FES)。新增 guide.py 项目阶段向导：在立项→构建→决策→收敛→优化→静态→动力学→反应路径→后处理→诊断→报告的每个阶段告诉你该做什么，并 scan 目录推断当前进度——不是空跑的自动化工作流。decide.md 已扩展至 §28：方法选择(xTB/DFTB/QM-MM/NNP/EIP/Embedding 何时用)、增强采样与反应路径(METADYN/BAND-CI-NEB/CONSTRAINT/COLVAR/PLUMED)、CELL_OPT 晶胞弛豫、MD 系综/恒温器/恒压器关键字落点、Properties/PRINT 全套决策(EFG/超精细/Hirshfeld(-I)/Wannier/DOS/PDOS/STM/cube/MOMENTS 与通用 EACH 打印频率)、Post-HF 关联(MP2/RI-MP2/RPA/SOS-MP2 与 ADMM 加速)、NEB/过渡态输入结构、计算技术(OT/对角化/ELPA/GPU/PSMP)、**SCF 收敛全流程决策(§22：EPS_SCF/MAX_SCF/SCF_GUESS/ADDED_MOS/CHOLESKY 落点纠正、OT vs 对角化、MIXING/SMEAR/OUTER_SCF/MOM 关键字枚举与取舍)**、振动分析/声子/IR 谱(VIBRATIONAL_ANALYSIS)、经典力场 FORCEFIELD 与 QM/MM 衔接(EWALD_TYPE/ PARMTYPE)、其它 FORCE_EVAL 方法(DFTB/NNP/EIP/MIXED)+采样器(TMC/PILE)、**XC_FUNCTIONAL 内置泛函清单与 VDW_POTENTIAL 结构(PAIR_POTENTIAL/NON_LOCAL)**、**§28 庚子讲师实操硬规则(DFT+U 强关联 TM 必加 / BSSE 高斯基组高估吸附能 / OT vs 对角化经验)**；gen_inp.py 已支持 GAPW 一键(`--gapw`)、CONSTRAINT 进阶(`--constraint-g3x3`/`--constraint-hbonds`)、VIB 模板(`--type vib`)、metadyn 进阶(`--plumed` 等)（均对照 CP2K 2026.1 官方手册本地 cp2k_input.xml 与概念章核对，并经官方解析器校验）。"
agent_created: true
read_when:
  - 用户要做 CP2K 计算（几何优化、晶胞优化、AIMD/分子动力学、NEB 过渡态、元动力学、振动分析）
  - 用户问 CP2K 输入怎么写、该选哪些 SECTION、参数怎么定
  - 用户需要校验 .inp / 解析 .out / 判断 SCF 收敛 / 决定下一步调什么
  - 关键词：cp2k、Quickstep、GTH、AIMD、几何优化、晶胞优化、DFT、赝势、基组、NEB、过渡态、metadyn、自由能面、势能面、HSE06、TPSS、SCAN、ADMM、UKS、DFT-D3、PDOS、DOS、EFG、超精细、Wannier、STM、cube、Hirshfeld、电荷分析、MP2、RPA、Post-HF、LANGEVIN、xTB、DFTB、QM/MM、神经网络势、CELL_OPT、约束、系综、恒温器、GPU、并行、振动分析、声子、IR谱、VIBRATIONAL_ANALYSIS、力场、FORCEFIELD、NNP、EIP、MIXED、COLVAR、PLUMED、XC_FUNCTIONAL、vdW-DF、rVV10、TMC、路径积分、PILE
---

# CP2K 计算助手（会思考的版本）

本 skill 从「庚子计算」讲义体系中提炼了课题组的 CP2K 写法与参数约定。
**它的定位是"全过程的参谋 / 副驾"，不是"自动驾驶"**：每个阶段它只负责把该考虑的事、权衡、坑、判读指标讲清楚，并给出可选的命令；最终怎么选、跑不跑、改不改，**决定权在你**。

> **设计原则：顾问，而非自动驾驶**
> - 本 skill **不会**在后台替你把整个流程跑完、只丢一堆结果给你。
> - 它在**每个阶段**告诉你：目标是什么、该考虑哪些选择、各选项的取舍、该盯哪些指标判断好坏、常见坑在哪、你可以调用哪些工具（命令都是**给你、由你决定执行**的）。
> - "算完读结果 / 出图"只是**可选的工具能力**，不是必须自动发生的步骤；何时用、怎么解读，由你定。
> - 入口是先 `guide.py show <stage>` 看该阶段指导，做完用 `guide.py scan .` 确认进度、决定下一步——只读、不跑。
>
> **核心哲学**：计算化学是"具体问题具体分析、根据结果不断调整"的过程。
> 本 skill 把课题组约定当作**安全起点假设**，而真正的能力在两层"思考"脚本：
> - `recommend.py` —— 你拿一个新体系来"问"参数时，它根据元素/周期/目标/自旋等，推理出该用什么泛函、基组、赝势、色散、k 点、SMEAR、CUTOFF，并给一条起步阶梯（**你判断是否采纳**）。
> - `diagnose.py` —— 你跑完 cp2k 后拿来"读"结果时，它判断 SCF/几何/能量/虚频是否健康，并告诉你下一步可改哪一行（**你决定改不改**）。
>
> 默认值不是定律；`decide.md` 里写清了每项选择的理由，方便你带化学直觉做最终取舍。

---

## 项目阶段向导（总入口，避免"空跑工作流"）

本 skill **不是**一条会自动替你点"运行"的流水线，而是一个在每个阶段告诉你**该做什么**的辅助。
`scripts/guide.py` 是总导航：

```bash
python guide.py list                       # 看全 11 个阶段
python guide.py show optimize              # 展开"几何优化"阶段的完整指引
python guide.py scan /path/to/project      # 读你目录里的真实文件，推断卡在哪、下一步做什么
python guide.py next /path/to/project      # 只给下一步行动
```

`scan` / `next` 会读目录中的 `.inp` / `.out` / `*-pos-1.xyz` 轨迹 / `*.pdos` / `*.cube` / `ACF.dat` / `HILLS` / `fes.dat`，
据此判断你**已做完哪些阶段、当前在哪个阶段、下一步最该做什么**——这是它和"空壳工作流"的根本区别。
完整阶段模型与陪跑路径见 `references/workflow.md`。

> **11 阶段顺序**（即项目推进顺序）：
> ① 立项 → ② 构建 → ③ 参数决策 → ④ 收敛测试 → ⑤ 几何/晶胞优化 →
> ⑥ 静态/电子结构性质 → ⑦ 分子动力学(AIMD/MD) → ⑧ 反应路径(NEB/元动力学) →
> ⑨ 后处理分析 → ⑩ 结果诊断 → ⑪ 总结报告。
> 闭环不是直线的：⑩ 诊断常把你打回 ⑤/⑥/⑦ 调参重算，这正是"按结果不断调整"的常态。

---

## 可调用的工具箱（你按需取用，不是自动流水线）

下面这些脚本是**工具**，不是 skill 会自动替你跑的步骤。阶段向导 `guide.py show <stage>` 会在每个阶段告诉你：此时该考虑什么、要不要用到下面某个工具、用到时怎么判读结果。**你不一定要全用，也不必按顺序**——按你当前的需要取用。

```
① 问诊  →  recommend.py  你拿来"问"参数：给有理由的推荐 + 起步阶梯（你判断是否采纳）
② 生成  →  gen_inp.py    你决定生成时，按你的选择产出 .inp（多元素/进阶开关）
③ 解读  →  validate_inp.py（语法自检）/ parse_output.py（取能量/受力/收敛）/ diagnose.py（读 .out 给改哪行的建议）—— 都是你跑完 cp2k 后按需调用的"读结果"工具
④ 调整  →  你看 diagnose 的方向，自己决定改不改、改什么
⑤ 后处理 → postprocess.py 你想从轨迹里提取物理意义时，用来算 RDF/MSD/扩散/VACF/IR/PDOS 等并出图
```
（⑤ 是「跑完读结果」之后的下游分析：RDF/MSD/扩散/键长键角/PDOS/Bader/FES 等，
详见 references/postprocess.md。阶段向导的"后处理"阶段会提示你该看哪些量、怎么判断结果是否合理。）

### ① 问诊（推荐参数）
当用户描述一个新体系，先抽取关键信息（元素、周期、电荷、自旋、目标、是否吸附/弱作用），
跑 `recommend.py` 得到推荐与理由，再和用户确认后生成：

```bash
python recommend.py --elements Au O --goal geo_opt --periodic xy \
    --multiplicity 3 --vdw auto --accuracy balanced
```

它会输出：推荐泛函/基组/赝势（**已按元素逐个查好 q**）、自旋、色散、k 点、SMEAR、CUTOFF，
每条都带"为什么"，以及一个"从 0 到收敛"的阶梯，最后给出**可直接执行的 gen_inp.py 命令**。

### ② 生成（输入文件）
`gen_inp.py` 读 XYZ、填模板、支持多元素与全部进阶开关（详见下文"进阶能力"）。
`recommend.py` 产出的命令可直接用；也可手动加开关。

### ③ 解读（校验 + 解析 + 诊断）
```bash
python validate_inp.py out.inp        # 语法校验（零依赖）
# 提交: mpirun -n N cp2k.popt out.inp   (见 references/run.md)
python parse_output.py cp2k.out        # 取能量/受力/收敛
python diagnose.py cp2k.out            # 自动诊断问题并给改哪行的建议
```

### ④ 调整（迭代）
`diagnose.py` 给的是方向（如"加 --smear""减 TIMESTEP""换 OPTIMIZER CG/BFGS"），
按 `references/decide.md` 第 10 节的对照表落实，回到②再生成。
**这一步体现"根据结果不断调整"——是计算化学的常态。**

---

## 课题组默认约定（安全起点，可被推理覆盖）

以下来自讲义，是**默认起点**；recommend.py 在识别到金属/开壳层/吸附等情形时会覆盖它们。

- **方法**：`METHOD Quickstep`（平面波 GPW 的 DFT）。
- **泛函**：`&XC_FUNCTIONAL PADE`（即 PBE；二者等价）。
- **赝势 / 基组**（按元素二选一，详见 `decide.md`）：
  - 轻元素 / 半导体：`GTH-PADE` + `DZVP-GTH-PADE`（Si：`GTH-PADE-q4`）。
  - 过渡金属 / 较重元素：`GTH-PBE` + `DZVP-MOLOPT-SR-GTH`（如 Au：`GTH-PBE-q11`）。
- **网格**：`&MGRID` `NGRIDS 4`, `CUTOFF 300`（轻元素；金属 350–500）, `REL_CUTOFF 60`。
- **SCF**：`EPS_SCF 1e-7`, `MAX_SCF 300`, `SCF_GUESS ATOMIC`, `&MIXING BROYDEN_MIXING`, `&OT DIIS`。
  金属/窄带隙加 `&SMEAR FERMI_DIRAC 300K`。精细调参旋钮见下「SCF 收敛工具箱」。
- **几何优化**：`OPTIMIZER BFGS`, `MAX_ITER 400`, `MAX_FORCE 6e-4`, `MAX_DR 0.003`, `RMS_FORCE 3e-4`, `RMS_DR 1.5e-3`。
- **晶胞优化**：`&CELL_OPT` + `EXTERNAL_PRESSURE 1.0 0 0 0 0 1.0 0 0 0 1.0`, `KEEP_ANGLES T`, `KEEP_SYMMETRY T`, `OPTIMIZER CG`。
- **AIMD/MD**：`&MD ENSEMBLE NVT`, `STEPS 500000`, `TIMESTEP 0.5` fs, `TEMPERATURE 600`, `&THERMOSTAT NOSE TIMECON 1000`。
- **元动力学**：`&MD NVT` + `&FREE_ENERGY &METADYN DO_HILLS NT_HILLS 50`；集体变量 `&COLVAR`（每个 CV 一个 `&COLVAR`，置于 `&SUBSYS`）；`&METAVAR`（含 `&WALL` 约束，墙参数用 `TYPE`+`POSITION`）。NEB 的 `&REPLICA` **不加编号参数**（按出现顺序编号）。
- **NEB（过渡态）**：`RUN_TYPE BAND` + `&BAND BAND_TYPE CI-NEB NUMBER_OF_REPLICA N`（含 `K_SPRING`/`&CI_NEB`/`&OPTIMIZE_BAND`）。进阶开关见下文「NEB 进阶选项」。另可用 **Dimer 法**（`GEO_OPT TYPE TRANSITION_STATE OPTIMIZER CG` + `&TRANSITION_STATE METHOD DIMER`），只需初态。

## 进阶能力（催化计算常用，均由开关控制，不必手改模板）

### 泛函阶梯
- **GGA**：`--functional PADE/PBE`（默认；结构优化/筛选性价比最高）。
- **Meta-GGA**：`--functional TPSS` / `SCAN` —— 精度介于 PBE 和杂化之间。对吸附能、弱作用、表面反应比 PBE 明显更准，价格仅 ~1.5-2x PBE。**推荐作为 PBE→HSE06 的中间台阶**。
- **杂化泛函**：`--functional HSE06` / `B3LYP` → 生成 `&HF` 块（反应能/带隙最准）。**务必加 `--admm`**（见下），否则大体系上天价。

### ADMM 杂化降本（v2 新增）
- **`--admm`** → 自动生成 `&AUXILIARY_DENSITY_MATRIX_METHOD ADMM` 块。
  - 用 cFIT/FIT 辅助基组计算精确交换部分，**成本降低 3-5x**。
  - 对 >50 原子的杂化计算几乎是必须的；精度损失通常 <0.01 eV。
  - recommend.py 对 HSE06/B3LYP 默认推荐开启。

### Properties 输出（v2 新增）
> **放置规则（已对照官方 cp2k_input.xml 核对）**：CP2K **没有** `&PROPERTIES` 容器块能直接吃 DOS/PDOS/STRESS/DIPOLE。
> 这些打印项必须落到正确的 `&PRINT` 子节：
> - `dos` / `pdos` / `cube` / `band` → **`&DFT &PRINT`**（`&DOS` / `&PDOS` / `&E_DENSITY_CUBE` / `&BAND_STRUCTURE`）。
> - `stress` → **`&FORCE_EVAL &PRINT`**（`&STRESS_TENSOR`）。
> - `wannier` → **`&DFT &LOCALIZE &PRINT`**（`&WANNIER_CENTERS`）。
> - `dipole`（偶极矩）是 **MM/MIXED 专属**，Quickstep DFT 不发射，故 `--properties` 不接 `dipole`。

- **`--properties dos pdos stress band cube wannier mulliken lowdin hirshfeld charges mo elf vhartree moments`** → 全部落 `&DFT &PRINT`（除 stress 在 `&FORCE_EVAL &PRINT`、wannier 在 `&DFT &LOCALIZE`）。
  - `pdos`：投影态密度（金属/半导体必做；看 d-band center、元素贡献）；`&EACH QS_SCF 1` 每 SCF 打印。加 `--ldos-list "1..26"` 可进一步发射 `&PDOS &LDOS LIST <原子>` 做逐原子投影（范围 `a..b` 会自动展开为显式原子号，兼容官方解析器）。`--pdos-nlumo N`（默认 1；nico 用 30 打印全部空轨道）、`--pdos-nhomo N` 控制投影的轨道窗口。
  - **输出风格**：`--print-style SILENT` 让 `mulliken`/`lowdin`/`hirshfeld` 以 `&NAME SILENT` + `FILENAME <名>` 安静输出（复刻 nico 写法）；默认 `ON`（不写 FILENAME）。`--cube-stride "1 1 1"`（默认 `5 5 5`）设置所有 cube 的 `STRIDE`（nico 用 1 1 1，逐网格点）。
  - `band`：能带结构（需配合 `&BAND_STRUCTURE &KPOINT_SET`）。
  - `stress`：应力张量（CELL_OPT / 压强计算）。
  - `cube`：电子密度 cube 文件（可视化电荷分布）。
  - `mulliken` / `lowdin` / `hirshfeld`：三种布居/分电荷分析（电荷转移、键极性、Bader 前处理）。
  - `charges`：一次性发射 `mulliken` + `lowdin` + `hirshfeld`。
  - `mo`：`&MO_CUBES`（NHOMO/NLUMO，分子轨道 cube 可视化）。
  - `elf`：`&ELF_CUBE`（电子局域函数，看成键/孤对）。**注意 CP2K 段名为单数 `ELF_CUBE`**。
  - `vhartree`：`&V_HARTREE_CUBE`（Hartree 势 cube）。**段名单数 `V_HARTREE_CUBE`**。
  - `moments`：`&MOMENTS`（电/磁多极矩）。
  - `wannier`：Wannier 中心（需 `&LOCALIZE METHOD CRAZY`）。

### SCF 收敛工具箱（v2 增强）
- **混合方法**：`--mixing-method broyden`（默认）/ `pulay`（金属推荐）/ `multisecant`（极难收敛）。`--mixing-alpha`（默认 0.4；nico 用 0.1）、`--mixing-beta`（BROYDEN 残差混合，nico 用 1.5；默认不发射）、`--mixing-nbroyden`（默认 8）。
  > 注：`FULL_ALL` **不是** `&MIXING` 的合法 `METHOD`（`cp2k_input.xml` 中 `&MIXING` 仅 BROYDEN_MIXING / PULAY_MIXING / MULTISECANT_MIXING）；旧资料里的 `FULL_ALL` 写法在官方解析器中报错，已废弃。
- **OT 优化器**：`--ot-minimizer diis`（默认）/ `cg` / `broyden`（大体系或 DIIS 不收敛时换用）。
  > 注：`LBFGS` **不是** `&OT` 的合法 `MINIMIZER`（`&OT` 仅 DIIS / CG / BROYDEN / SD）；`LBFGS` 是 `&GEO_OPT` 的 `OPTIMIZER`，二者不要混淆。
- **QS 精度**：`--qs-eps 1e-12`（数值精度不够时调高）。
- **MGRID 截断能**：`--cutoff N`（默认模板 300；金属 350–500）、`--rel-cutoff N`（默认 60）。直接改 `&MGRID CUTOFF/REL_CUTOFF`。
- **SCF 收敛阈值/步数**：`--eps-scf 1.0E-6`（默认 1.0E-7）、`--max-scf 500`（默认 300）。
- **SCF 收敛辅助关键字**：`--eps-diis 0.05`（DIIS 截断，nico 用）、`--added-mos 500`（金属/展宽额外 MO，nico 用）、`--cholesky INVERSE`（重叠矩阵 Cholesky；默认不发射，nico 用 INVERSE）、`--diagonalization-eps-adapt 0.01`（自适应 DIIS 阈值；仅在含 `&DIAGONALIZATION` 的模板发射，nico 用）。
- **续算 / 初猜**：`--scf-guess ATOMIC`（默认）/ `RESTART`（从既有波函数续算）+ `--wfn-restart ./cp2k-RESTART.wfn`（发射 `&DFT WFN_RESTART_FILE_NAME`；注意此关键字属于 `&DFT` 而非 `&SCF`）。

### MD 增强（v2 新增）
- **恒温器选择**：`--thermostat csvr`（默认）/ `nose` / `langevin`（表面催化推荐；自动映射为稳健的 `AD_LANGEVIN`）。
- **系综扩展**：`--ensemble npt`（自动加 BAROSTAT，等压等温系综）。
- **续算支持**：`--restart-freq N`（每 N 步写 RESTART 文件；长 AIMD 必开）。

### 其余进阶能力
- **自旋极化（开壳层）**：`--multiplicity N`（O₂→3、自由基→2）→ 自动 `UKS`+`MULTIPLICITY`+`WF_INTERPOLATION ASPC`。
- **色散**：`--dispersion` → `&VDW_POTENTIAL` DFT-D3（弱吸附/层间必备，需 `dftd3.dat`）。
- **固定原子**：`--fixed-atoms "1..54 289..324"` → `&CONSTRAINT &FIXED_ATOMS`，冻结 slab 底层。
- **GAPW 全电子**：`--gapw` → `&QS METHOD GAPW`（核区 EFG/超精细/NMR 必备；仍用 GTH 赝势+常规轨道基组，仅切换核心密度重构，已校验合法）。配合 `--properties efg hyperfine` 开核区性质。
- **几何约束（SHAKE）**：`--constraint-g3x3 "1 2 3" --g3x3-distances "1.0 1.5 2.0"` → `&CONSTRAINT &G3X3`（3 原子/3 距离约束）；`--constraint-hbonds --hbond-atom-type O --hbond-targets "0.96 1.0"` → `&CONSTRAINT &HBONDS`（X-H 键 SHAKE）。均经官方解析器校验。COLLECTIVE(`&COLVAR`约束) 因 2026.1 schema 未建模 `&DEFINE_COLVAR`，仍由顾问手动指导。
- **非周期/表面**：`--periodic none`（孤立分子→WAVELET）/ `xy`（表面 slab，z 非周期）。
- **表面偶极修正**：`--surface-dipole`（可选 `--dipole-dir Z` / `--dipole-pos 0.5` / `--dipole-switch 0.3`）→ `&DFT SURFACE_DIPOLE_CORRECTION T`，用于吸附质单侧或两端终止不对称 slab，恢复真空区平整势、加速 SCF 收敛（仅 `PERIODIC xy`/`x?` 有意义）。
- **k 点**：`--kpoints "6 6 6"`（块体金属）/ `"4 4 1"`（表面）→ `&KPOINTS MONKHORST-PACK`。
- **收敛辅助**：`--outer-scf`（OT 难收敛）、`--smear`（金属）、`--print-forces`（输出原子力）、`--charge N`。
- **振动分析**：`--type vib` → `RUN_TYPE VIBRATIONAL_ANALYSIS`（确认极小点/过渡态、求 IR）。
- **优化器选择**：`--optimizer bfgs`（默认，块体）/ `lbfgs` / `cg`（slab/缺陷常用；自动发射 `&LBFGS`/`&CG` 子节与 `&LINE_SEARCH`）。`cell_opt` 默认 `cg`；`geo_opt` 默认 `bfgs`。覆盖庚子例子里的 LBFGS/CG 写法。
- **应力张量计算方式**：`--stress-tensor analytical`（比默认 numerical 更快）/ `numerical` → 在 `&FORCE_EVAL` 层发射 `STRESS_TENSOR` 关键字（控制"如何算"应力；与 `--properties stress` 仅"打印"应力区分开）。覆盖 cu-kpoint 例子的 `STRESS_TENSOR ANALYTICAL`。
- **多元素**：`--elem Au O --basis DZVP-MOLOPT-SR-GTH DZVP-GTH-PADE --potential GTH-PBE-q11 GTH-PADE-q6`（逐元素 &KIND）。
- **从文件读结构（TOPOLOGY）**：`--topology POSCAR.cif --topology-format cif`（也支持 xyz / pdb / extxyz）→ 发射 `&SUBSYS &TOPOLOGY COORD_FILE_NAME <file> COORD_FILE_FORMAT <fmt>`，替代 `&COORD`。覆盖 cu-kpoint / nico / LiGePS / al2o3-slab 等从 CIF/POSCAR 读结构的例子（与 `--xyz`/`--coord` 互斥）。

### 逐原子 KIND 控制（DFT+U / 逐原子自旋 / 同位素质量）
- **`--kinds`**（覆盖 `--elem/--basis/--potential`，精细控制每个 `&KIND`）：
  格式 `NAME:ELEMENT:BASIS:POTENTIAL` 加可选 `U=<eV>` `mag=<f>` `mass=<f>` `L=<int>` `noramp`。
  - `NAME` 可与 `ELEMENT` 不同（同一元素的不同自旋/氧化位点，如 `Fe` / `Fe2` / `Fe3` 均 `ELEMENT Fe`）。
  - 只给 3 段 `NAME:BASIS:POTENTIAL` 时，`NAME` 同时作为 `ELEMENT`。
  - `U=<eV>` → 自动发射 `&DFT_PLUS_U`（`U_MINUS_J [eV]`、`L` 默认 2、带 ramping 收敛辅助），并把 `PLUS_U_METHOD` 注入 `&DFT`（默认 MULLIKEN，可用 `--plus-u-method` 改 LOWDIN/MARZARI/DUDEI）。强关联过渡金属氧化物（Fe₃O₄、TiO₂ 等）常用。
  - `mag=<f>` → 逐原子 `MAGNETIZATION`（不同原子不同自旋态，如 Fe₃O₄ 的 +5/+4/−5 三种自旋）。
  - `mass=<f>` → 逐原子 `MASS`（同位素或人为质量，如 Au 用 19.7 加速动力学）。
  - `noramp` → 去掉 `U_RAMPING` 系列（Au-TiO₂ 的 Ti 写法）；默认带 ramping（Fe₃O₄ 写法）。
  - 与 `--admm` 同时用时，每个 `&KIND` 自动加 `BASIS_SET AUX_FIT`。
  - 例：`--kinds "Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=5.0:U=3" "Fe2:Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=4.0:U=3" "Au:DZVP-MOLOPT-SR-GTH:GTH-PBE-q11:mass=19.7"`

### NEB 进阶选项（--type neb）
- **多副本外部读取**：`--xyz-replicas ./0.xyz ./1.xyz ... ./N.xyz` → 每个文件发射一个 `&REPLICA COORD_FILE_NAME <file>`，`NUMBER_OF_REPLICA` 自动设为文件数（覆盖 al2o3/neb 从 `./0.xyz..` 读副本的写法）。与内联 `--xyz-init`/`--xyz-final` 互斥（内联只产生首末两帧）。
- **带点链优化方式**：`--optimize-band MD`（默认，发射 `&OPTIMIZE_BAND OPT_TYPE MD` + `&MD` 退火块）/ `DIIS`（发射 `OPT_TYPE DIIS`，配合 `--optimize-end-points F` 固定端点，即 al2o3/neb 写法）。
- **帧对齐 / 旋转**：`--align-frames T|F`（默认 T）/ `--rotate-frames T|F`（默认 F）→ `&BAND ALIGN_FRAMES` / `ROTATE_FRAMES`。空位迁移等"不想被对齐扰动路径"的情形设 F。
- **spring 常数 / 诊断输出**：`--k-spring 0.08`（默认 0.02；一般 0.02~0.08）、`--program-run-info`（发射 `&BAND &PROGRAM_RUN_INFO ON`）、`--convergence-info`（发射 `&BAND &CONVERGENCE_INFO ON`）。
- 示例（复刻 al2o3/neb）：`--type neb --xyz-replicas ./0.xyz ./1.xyz ./2.xyz ./3.xyz ./4.xyz ./5.xyz --optimize-band DIIS --optimize-end-points F --align-frames F --rotate-frames F --program-run-info --convergence-info --band-type CI-NEB --nproc-rep 28 --k-spring 0.08`

### 元动力学进阶选项（--type metadyn，对应 decide.md §17）
- **退火/温标**：`--well-tempered`（发射 `WELL_TEMPERED T`）+ `--delta-t 1500`（偏置温度 DELTA_T [K]，如 1500）+ 可选 `--wtgamma <γ>`（或用 WTGAMMA 替代 DELTA_T）。退火元动力学让山随时间变扁、收敛更稳。
- **山高**：`--metadyn-ww 0.05`（发射 `WW`，hill 高度，hartree；默认 0.1；越大山越疏、自由能面越平滑）。
- **扩展拉格朗日**：`--lagrange`（发射 `LAGRANGE T`，CV 带质量被动力学传播，适合有质量/转动的 CV）。
- **多 walker**：`--multi-walker`（发射 `&MULTIPLE_WALKERS`，协作式元动力学加速填面）。
- **PLUMED 驱动**：`--plumed` + `--plumed-file plumed.dat`（发射 `USE_PLUMED T` + `PLUMED_INPUT_FILE`，用 plumed 定义 CV 与偏置，CP2K 当执行器）。
- 模板默认 `DO_HILLS` + `NT_HILLS 50` 已撒山；CV 用 `&SUBSYS &COLVAR` 定义、`&METAVAR` 引用（模板给的是占位 ATOMS 1 2 / 1 3，需按你的体系改成真实原子号与 CV 数）。
- 示例：`--type metadyn --project surf --elem Au O --well-tempered --delta-t 1500 --metadyn-ww 0.05 --lagrange --multi-walker`

### QM/MM（--type qmmm，半经验 PM6 做 QM 区）
- **结构**：`METHOD MIXED` + `&MULTIPLE_FORCE_EVALS FORCE_EVAL_ORDER 2 3 MULTIPLE_SUBSYS T`，耦合两个子 `&FORCE_EVAL`：① `METHOD FIST`（MM，经典力场）；② `METHOD Quickstep` 且 `&QS METHOD PM6`（QM，半经验，无需基组/赝势）。`&MIXED MIXING_TYPE GENMIX` 用 `MIXING_FUNCTION E1+E2` 把两区能量相加；`&MAPPING` 用 `&FRAGMENT 1`(QM 原子区间) / `&FRAGMENT 2`(MM 原子区间) 定义分区。
- **参数**：
  - `--qm-elem C H O` / `--mm-elem Cu`（QM 区元素 / MM 区元素）。
  - `--qm-method PM6`（默认；也支持 PM3 / AM1 / RM1 / MNDO）。
  - `--qm-atoms "1 50"` / `--mm-atoms "51 2000"`（FRAGMENT 区间，必填真实值）。
  - `--topology ./s`（全系统坐标，MIXED + FIST 两个 SUBSYS 共用）/ `--qm-topology ./f`（QM 片段坐标，Quickstep SUBSYS 用）。
  - `--qmmm-run-type MD`（默认；用 `GEO_OPT` 可松弛 QM 区）/ `--group-partition "2 6"`（各子 eval 的 MPI 核数）。
- **重要**：FIST 的 `&NONBONDED` 当前只生成占位骨架（每个 MM 元素的 `&LENNARD-JONES` 自对，EPSILON=0），**必须先填入真实力场参数**（GENPOT / EAM / Buckingham）与 `&FRAGMENT` 原子区间、坐标文件才能跑物理合理的 QM/MM。COORD 用 `COORD_FILE_FORMAT`（官方解析器仅认这个，比例子里的旧 `COORDINATE` 更通用）。

### 后处理引擎（postprocess.py，闭环第 ⑤ 步，按需调用）
- **何时用（按需，非必须）**：当你想从跑完的轨迹 / `*.out` / `*.pdos` / `*.cube` / metadyn `restart` 里**提取物理意义**（如结构有序度、扩散快慢、振动频率、电子结构）时，这些是可选的分析工具。阶段向导的"后处理"阶段会提示你该看哪些量、怎么判断结果是否合理；具体跑不跑、跑哪些，**由你决定**。
- **核心层（纯 numpy + matplotlib，零外部依赖，全部已用合成数据校验通过）**：
  - `energy` 能量/温度曲线；`rdf` 径向分布函数 g(r)；`msd` 均方位移；`diffusion` 扩散系数 D(Einstein，给 Å²/ps 与 cm²/s)；
  - `bond` / `angle` / `dihedral` 内禀几何时间序列+分布；`pdos` 态密度/投影态密度(自动按元素分解、Gaussian 展宽)；`adf` 角分布函数；`cn` 配位数；`zprofile` 轴向密度剖面；
  - `vacf` 速度自相关；`ir` / `power` 红外/振动态密度(对 VACF 做 FFT，双横轴 cm⁻¹ 与 1/ps)。
- **桥接层（检测外部二进制，缺失时给指引不中断）**：`bader`(Bader 电荷，需 `bader`)；`fes`(元动力学自由能面，调 CP2K `graph` 工具重建 FES 并出 2D 等值线，注意 `-ndim` 必须填真实 CV 数)；`travis`(TRAVIS 谱学 IR/Raman/VCD/ROA，生成控制文件并运行)。
  - **衔接要点**：RDF/MSD/ADF 需晶胞(`--cell` 或自动从 `.out` 解析)；VACF/IR 用 AIMD 默认打印的速度轨迹 `*-vel-1.xyz`(`--vel`)，无速度时可用位置轨迹差分近似。所有子命令出 `.png` + `.csv`。详见 `references/postprocess.md`。

### 项目阶段向导（guide.py，总入口）
- **它解决什么**：你不需要记"一个 CP2K 项目从头到尾要经历什么"——`guide.py` 把全流程拆成 11 个阶段（立项→构建→决策→收敛→优化→静态→动力学→反应路径→后处理→诊断→报告），每个阶段告诉你目标、该做的清单、决策点（带指引）、常见坑、对应命令、完成判据、下一步。
- **`scan` 让它不是空壳**：`python guide.py scan /path/to/project` 读你目录里的 `.inp`/`.out`/轨迹/`*.pdos`/`*.cube`/`ACF.dat`/`HILLS`/`fes.dat`，推断"你卡在哪个阶段、下一步最该做什么"。例如：只有 `.inp` → 提示去提交；有收敛的 `GEO_OPT` `.out` → 提示去算电子结构性质；有 `*-pos-1.xyz` 轨迹 → 提示去做后处理。
- **怎么融入工作**：每个阶段先用 `guide.py show <stage>` 看该做什么，做完用 `guide.py scan .` 确认进度，再进下一阶段。完整说明见 `references/workflow.md`。

## 选 SECTION 决策树（引导一步步走）

1. **算什么？** → `GLOBAL / RUN_TYPE`：单点能 `ENERGY_FORCE`、几何 `GEO_OPT`、晶胞 `CELL_OPT`、动力学 `MD`、过渡态 `BAND`(NEB) 或 `VIBRATIONAL_ANALYSIS`、增强采样 `MD+&METADYN`；多尺度 `METHOD MIXED`(QM/MM)。
2. **什么方法？** → `FORCE_EVAL / METHOD`：平面波 DFT 用 `Quickstep`（绝大多数）；经典 `FIST`；QM/MM `MIXED`（QM 区用 Quickstep + QS METHOD PM6 半经验，MM 区用 FIST 力场）。
3. **DFT 子项** → `&DFT`：`&MGRID`、`&XC`（泛函 GGA/Meta-GGA/杂化+可选 `&ADMM`降本+`&VDW_POTENTIAL`）、`&SCF`（MIXING 方法选择/OT 优化器/`&SMEAR`/`&OUTER_SCF`）、`&POISSON`、`&KPOINTS`（金属）。
4. **Properties（v2 新增）** → 落点已按官方参考核对：`&DFT &PRINT`（`&DOS`/`&PDOS`/`&E_DENSITY_CUBE`/`&BAND_STRUCTURE` 电子结构分析）、`&FORCE_EVAL &PRINT`（`&STRESS_TENSOR` 应力/压强）、`&DFT &LOCALIZE &PRINT`（`&WANNIER_CENTERS`）。`DIPOLE` 为 MM/MIXED 专属，DFT 不发射。
5. **结构** → `&SUBSYS`：`&CELL`、`&COORD`/`&TOPOLOGY`、逐元素 `&KIND`（ELEMENT/BASIS_SET/POTENTIAL）。
6. **动力学/优化** → `&MOTION`：`&GEO_OPT`/`&CELL_OPT`/`&MD`（NVE/NVT/NPT + CSVR/Nose/LANGEVIN/GLE 恒温器）/`&BAND`/`&CONSTRAINT`(`&FIXED_ATOMS`)。长 MD 加 `&RESTART` 续算支持。
7. **输出** → `&PRINT`：轨迹、受力、PDOS/cube/RESTART。

## 知识来源层级与阅读顺序（给未来对话的导航）

本 skill 的知识是**分层**的，避免重复文件造成混乱。任何对话加载本 skill 后，按需按以下优先级取用：

| 层级 | 文件 | 角色 | 何时读 |
|---|---|---|---|
| **A 决策知识库（权威）** | `references/decide.md`（§1–§28） | 所有"该选什么 / 为什么 / 判读结果"的答案库，含 §28 庚子讲师实操硬规则 | 写输入、做方法选择、判读结果时**首选** |
| **B 课程综合（权威·主题式）** | `references/course_learned.md` | 庚子计算 5 份 PDF(425 页)+6 字幕**逐页无遗漏**内化，按主题重组的导航枢纽（含 PDF 独有公式/脚本/数值案例/坑） | 需要课程实战细节、NEB/电子结构/自由能面完整流程时 |
| **C 速查/摘要** | `references/course_notes.md`（87 行）<br>`references/course_survey.md`（100 行） | C 是课程实战精华速查；survey 是文件→天→主题映射+同音错字表 | 想快速看"经验要点"或"字幕同音错字对照"时 |
| **D 手册笔记** | `references/manual_notes.md`<br>`references/_manual_tree.txt`<br>`references/sections.md` | 官方手册的结构化笔记（SECTION 树/关键字） | 查某个 SECTION 的官方字段含义时 |
| **E 原始素材（溯源·勿改）** | `references/pdf_text/L1–L5.txt`（PDF 分页抽取）<br>`references/pdf_text/learn_L1–5.md`（逐页学习原始稿）<br>`references/pdf_text/extract_pdf.py` | **B 的来源**：A 层"无遗漏"的溯源依据。除非要修正 B，否则只读不改 | 当 B 疑似遗漏某页细节、需回查原始讲义时 |

> **关键约定**：
> - **B 是 C 的超集且已替代 C 的深度**——C 仅作"速查"，正经内容以 B/A 为准。
> - **E 是溯源层**：保留它是为了"全面、可核对"，日常不要直接读 E（冗长）；发现 B 有误时回 E 校正，再同步回 A/B。
> - 交叉引用已在 A、B、postprocess.md 之间打通（如 A §28 ↔ B 的 DFT+U 节）。
> - **新增/修正资料的标准流程见 `references/MAINTENANCE.md`（分层 SOP + 无遗漏审计清单）**。

## 文件索引
- `scripts/recommend.py` —— **思考层①**：体系描述 → 参数推荐（含 TPSS/SCAN Meta-GGA、ADMM 推荐、Properties 推荐、恒温器建议）+ 理由 + 起步阶梯 + 生成命令。
- `scripts/diagnose.py` —— **思考层③**：读 `.out` → 诊断问题 → 给改哪行的建议。
- `scripts/guide.py` —— **项目阶段向导（总入口）**：`list`/`show <stage>`/`scan <dir>`/`next <dir>`。每个阶段告诉你该做什么；`scan` 读你目录的真实文件推断当前进度与下一步，避免空跑工作流。
- `scripts/gen_inp.py` —— 由模板生成 `.inp`（多元素 + ADMM/Meta-GGA/Properties(布居/电荷/cube 进阶)/MIXING/OT/Thermostat/NPT + 逐原子 KIND(DFT+U/自旋/质量) + NEB 进阶(多副本读取/OPTIMIZE_BAND DIIS/ALIGN_ROTATE_FRAMES/PROGRAM_RUN_INFO/CONVERGENCE_INFO) + QM/MM(MIXED/FIST/Quickstep-PM6) 等全部进阶开关）。
- `scripts/validate_inp.py` —— 内置语法校验（零依赖；白名单含 ADMM/TPSS/SCAN/MGGA_X_SCAN 等新 SECTION）。
- `_validate_all.py` —— **权威校验 harness**：用 `cp2k-input-tools` 的 `CP2KInputParser`（对照官方 `cp2k_input.xml`）生成并解析 23 类特征输入，输出 error/warning（已处理 pint/fs 工具坑）。
- `_official_validate.py` —— 单文件权威校验（对单个 .inp 跑 `CP2KInputParser`，把 `fs` 误报降级为 NOTE）。
- `verify_out/*.inp` —— 7 个已通过权威校验的示例输入（HSE06/TPSS/SCAN/MD-NPT/PULAY/OT-CG/B3LYP）。
- `scripts/parse_output.py` —— 解析 `.out` 取能量/受力/收敛。
- `scripts/postprocess.py` —— **后处理引擎**（闭环第 ⑤ 步）：子命令 `energy / rdf / msd / diffusion / bond / angle / dihedral / pdos / adf / cn / zprofile / vacf / ir / power`（纯 numpy+matplotlib，零外部依赖）+ 桥接 `bader`(Bader 电荷) / `fes`(元动力学自由能面，调 CP2K graph) / `travis`(谱学)。详见 references/postprocess.md。
- `_validate_postprocess.py` —— 后处理端到端校验 harness（合成数据：随机气箱验 RDF/ADF/CN、已知 D 的布朗运动验 MSD/diffusion、阻尼振子验 VACF/IR 频谱峰值、伪造 .pdos 验绘图、2D 抛物线验 FES 出图），全子命令 0 error / 0 crash。
- `references/decide.md` —— **决策知识库（§1–§28）**：泛函阶梯(GGA→Meta-GGA→杂化)/基组/赝势/q 表/自旋/色散/k点/SMEAR/CUTOFF/ADMM/混合法/恒温器/Properties(PRINT 全套：EFG/超精细/Hirshfeld/Wannier/DOS/PDOS/STM/cube/MOMENTS)/方法选择(xTB/DFTB/QM-MM/NNP/Embedding)/增强采样与反应路径(NEB/元动力学/CONSTRAINT)/CELL_OPT/Post-HF(MP2/RPA)/NEB 输入结构/计算技术(OT/对角化/ELPA/GPU)/**SCF 收敛全流程决策(§22：EPS_SCF/MAX_SCF/SCF_GUESS/ADDED_MOS/CHOLESKY 落点纠正、OT vs 对角化、MIXING/SMEAR/OUTER_SCF/MOM 关键字枚举与取舍)**/振动分析(VIBRATIONAL_ANALYSIS：DX/INTENSITIES/THERMOCHEMISTRY/FULLY_PERIODIC)/经典力场(FORCEFIELD：PARMTYPE/PARM_FILE_NAME + EWALD_TYPE SPME)/其它 FORCE_EVAL 方法(DFTB/NNP/EIP/MIXED)+采样器(TMC/PILE 路径积分)/**XC_FUNCTIONAL 内置泛函清单(PADE/PBE/BP86/BLYP/TPSS/SCAN/PBE0/B3LYP/HSE06/BEEFVDW…)与 VDW_POTENTIAL(PAIR_POTENTIAL DFT-D3(BJ)/NON_LOCAL vdW-DF/rVV10)** 的选择理由 + 结果判读对照表。
- `references/sections.md` —— 各 SECTION 含义与推荐取值速查（含 PROPERTIES/ADMM/Meta-GGA 条目）。
- `references/workflow.md` —— **项目阶段向导总文档**：11 阶段完整指引（目标/该做的/决策点/坑/命令/完成判据）+ 陪跑路径 + 与其他脚本的关系。
- `references/templates/*.inp` —— static / geo_opt / cell_opt / aimd_md / metadyn / neb / vib 七类模板（均含 __ADMM_BLOCK__/__MIXING_BLOCK__/__OT_BLOCK__/__DFT_PRINT_BLOCK__/__FE_PRINT_BLOCK__/__LOCALIZE_BLOCK__/__THERMOSTAT_BLOCK__/__RESTART_BLOCK__/__SURFACE_DIPOLE_BLOCK__ 等 token）。

## 输入正确性验证（重要）

所有模板与生成逻辑都对照 **CP2K 官方参考手册（`cp2k_input.xml`，由 `cp2k-input-tools` 自动生成）** 校验过，**23 类特征组合全部解析通过（0 error / 0 warning）**。

```bash
# 权威校验：用 cp2k-input-tools 的 CP2KInputParser 解析生成的所有特征输入
# （需在隔离 venv 中：cp2k-input-tools 0.9.1 + pint 0.24.4 + numpy 2.5.1）
python _validate_all.py        # 生成 15 类输入并逐个解析，输出错误/警告
python _official_validate.py verify_out/*.inp   # 单文件权威校验
```

> 已知工具坑（已在 venv 与 shim 中解决，不影响生成结果）：
> - pint 0.23 在 numpy 2.x 下崩溃（`cumproduct` 已废弃）→ 用 pint 0.24.4。
> - `cp2k-input-tools` 的 `pint_units.txt` 未定义 CP2K 时间单位 `[fs]`（会误判为 femtosiemens）→ 已在校验脚本里注入 `fs = femtosecond` 并把该误报降级为 NOTE。
> - `&GLOBAL` **没有** `BACKUP_COPIES` 关键字；它属于 `&RESTART`（MOTION/PRINT/RESTART）子节 —— 已改正。
> - `&PROPERTIES` 不能直接装 DOS/PDOS/STRESS/DIPOLE；按上文"放置规则"分落到正确 `&PRINT`。
- `references/run.md` —— 本地与 Slurm 提交命令。
- `references/postprocess.md` —— IR / DOS / PDOS / 能带 / 轨迹 / 电荷 后处理方法。
- `references/course_survey.md` —— **课程资料梳理**：11 文件→5 天→主题映射、字幕同音错字对照表、字幕 vs 讲义互补分析、与 skill 覆盖对照（学习庚子计算视频字幕的入口）。
- `references/course_notes.md` —— **视频字幕实操精要**：后处理工具流（VMD RDF 球面积分 / MSD 平方再平均 / TRAVIS / ELF / 电荷差分）、参数硬经验（DFT+U 必加、BSSE 高估吸附能、OT vs 对角化）、建模实操、实例索引、错字对照表；沉淀讲师"怎么真正跑起来"的经验层。
- `references/course_learned.md` —— **5 天课程主题式综合知识库（逐页无遗漏内化）**：覆盖 5 份 PDF(425 页)+6 份字幕的全部内容，按主题重组为导航枢纽——AIMD 理论基础/后处理公式/CP2K 编译与建模/输入参数全集/NEB 完整流程/电子结构分析(TRAVIS·Bader·PDOS·ELF·功函数)/自由能面(PMF·slow-growth·metadynamics·QM-MM)；含 PDF 独有的公式·参数表·脚本·数值案例·坑，并交叉引用 decide.md/postprocess.md/course_notes.md。是"字幕+PDF 逐页对照"的权威沉淀（批 13 内化）。
- `references/pdf_text/README.md` —— 原始素材（L1–5.txt / learn_L1–5.md / extract_pdf.py）的溯源层说明：文件清单、PDF↔字幕天错位表、同音错字高频例、溯源维持约定（E 层，日常勿直接读）。
- `references/MAINTENANCE.md` —— **skill 维护 SOP**：新增/修正资料的七阶段流程、A–E 分层模型、命名约定、字幕同音错字处理、「无遗漏」审计清单、交叉引用维护。往 skill 加新资料时照此执行，保证不堆乱、跨对话可复用。
