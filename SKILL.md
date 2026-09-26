---
name: cp2k-aimd
description: CP2K 计算顾问（AIMD / 几何优化 / 晶胞优化 / NEB 过渡态 / 元动力学 / 振动分析 / 电子结构后处理）。给出参数推荐、生成与校验 .inp、解析 .out、诊断 SCF/几何/虚频问题、后处理轨迹出图，并按 11 个主线阶段向导陪跑项目。Use when 用户要做 CP2K 计算、问 CP2K 输入怎么写或参数怎么选、需要校验 .inp / 解析 .out / 判断 SCF 收敛 / 决定下一步调什么、或做 RDF/MSD/扩散/VACF/IR/PDOS/Bader/自由能面等后处理时。
title: CP2K 计算助手（会思考的版本 v2）
summary: 基于庚子计算《AIMD与CP2K讲义》(1-5) 等资料提炼的 CP2K 计算顾问，定位是"全过程参谋，不是自动驾驶"：每个阶段只讲清该考虑什么、取舍、坑、判读指标，并给出可选命令，决定权在用户。工具链：recommend.py 推理参数、gen_inp.py 生成 .inp、validate_inp/parse_output/diagnose 校验·解读·诊断、postprocess.py 后处理出图、guide.py 阶段向导。知识分 A–H 八层：A 决策库 / B 课程综合 / C 速查 / D 手册笔记 / E 原始素材 / F 实战手册（症状→处方 / 数值速查 / 报错速查）/ G 官方权威层（逐页采自 cp2k.org / manual.cp2k.org，带来源 URL）/ H 官方教程与实战算例（24 份官方 workshop·howto·夏校教材共 701 页，逐页抽取带页码，附逐主题精读笔记与真实生产算例输入卡）。冲突裁决：A–F 与 G 冲突以 G 为准；G 未覆盖而 H 教材讲了的内容以 H 原文为准并标注 T** P** 页码。
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
python guide.py list                       # 看全 11 个主线阶段（+ 1 个续算分支）
python guide.py show optimize              # 展开"几何优化"阶段的完整指引
python guide.py scan /path/to/project      # 读你目录里的真实文件，推断卡在哪、下一步做什么
python guide.py next /path/to/project      # 只给下一步行动
```

`scan` / `next` 会读目录中的 `.inp` / `.out` / `*-pos-1.xyz` 轨迹 / `*.pdos` / `*.cube` / `ACF.dat` / `HILLS` / `fes.dat`，
据此判断你**已做完哪些阶段、当前在哪个阶段、下一步最该做什么**——这是它和"空壳工作流"的根本区别。
完整阶段模型与陪跑路径见 `references/workflow.md`。

> **11 个主线阶段**（即项目推进顺序）：
> ① 立项 → ② 构建 → ③ 参数决策 → ④ 收敛测试 → ⑤ 几何/晶胞优化 →
> ⑥ 静态/电子结构性质 → ⑦ 分子动力学(AIMD/MD) → ⑧ 反应路径(NEB/元动力学) →
> ⑨ 后处理分析 → ⑩ 结果诊断 → ⑪ 总结报告。
> 闭环不是直线的：⑩ 诊断常把你打回 ⑤/⑥/⑦ 调参重算，这正是"按结果不断调整"的常态。
> 此外 `guide.py` 还带一个**续算分支**（↻ 从检查点恢复被中断的计算），它不属于主线推进顺序，而是任何阶段都可能触发的旁路。

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

### ③′ 关键一步：**验"算得对不对"**（不是语法，是物理）
`validate_inp.py` 只能证"输入合法"，`diagnose.py` 只能读"输出里有什么"——
**两者都判不了"这套设置算出来的东西对不对"**。有一类缺陷正是钻这个空子：
输入完全合法、CP2K 不报错、SCF 照常"收敛"，**结果是错的**（实测遇到过总能量差 12 Ha 的）。
用**三个物理不变量**去查：

```bash
python verify_forces.py emit cp2k.inp --ref-out cp2k.out -o vf/   # 参考 + ±h 位移 + 1 张整体平移卡
# 把这些 vf_*.inp 跑成单点
python verify_forces.py check cp2k.out vf/                        # 三个检验 + 总判定
```

| 检验 | 内容 | 成本 | 实测（正确 / 偏心 WAVELET 错 12 Ha） |
|---|---|---|---|
| ① 力-能量自洽 | `F = −dE/dx` | 每自由度 2 个单点 | 1.5e-4 ✅ ／ **6.8e-3 判通过 ⚠️** |
| ② 力平衡 | `\|ΣF\| = 0` | **0**（参考输出里就有） | 0.0020 ✅ ／ **24.7 ❌** |
| ③ 整体平移不变性 | 平移后 `ΔE = 0`（仅 `PERIODIC NONE`） | 1 个单点 | 1.0e-4 ✅ ／ **1.22e+1 ❌** |

> 🔴 **务必看懂第①行那个"⚠️"**：检验一查的是**力与能量面是否自洽**，不是能量面本身对不对。
> 偏心 WAVELET 那个错**恰好自洽**（解析力是那个**错误**能量面的**正确**导数），
> 于是检验一**判它通过**。**②③才是抓这类错误的主力，而且都很便宜。**
> 同理，"检验一通过"也**不等于"算对了"** —— 工具的输出里会明说这一点。

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

## 进阶能力（催化计算常用）

> **完整开关清单已外移到 `references/gen_inp_options.md`**（泛函阶梯 / ADMM / Properties /
> SCF 工具箱 / MD / 逐原子 KIND / NEB / 元动力学 / QM-MM 共 10 节，含 §0 快速定位表）。
> 下面只列**最常用、最该记住**的几条；需要细节时按需读该文件。

- **泛函阶梯**：PBE（默认）→ `--functional TPSS`/`SCAN`（Meta-GGA，吸附能更准，仅 1.5-2x 成本）→ `--functional HSE06`/`B3LYP`（杂化，最准但贵，**大体系务必配 `--admm` 降本 3-5x**）。
- **自旋/色散/金属**：`--multiplicity N`（开壳层）、`--dispersion`（弱吸附必备）、`--smear`（金属）、`--kpoints "6 6 6"`。
- **表面 slab**：`--periodic xy` + `--fixed-atoms "1..54"`（冻结底层）+ 可选 `--surface-dipole`（不对称 slab 修正）。
- **强关联过渡金属**：`--kinds "Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=5.0:U=3"`（DFT+U + 逐原子自旋，详见 gen_inp_options.md §7）。
- **SCF 不收敛**：`--mixing-method pulay`（金属）/ `--ot-minimizer cg`（DIIS 不行时）/ `--outer-scf`；报错原文与处方见 `references/playbook.md` §1.1。
- **长 AIMD**：`--restart-freq N`（必开）+ `--thermostat langevin`（表面催化推荐）。
- **几何优化器**：`--optimizer bfgs`（块体默认）/ `cg`（slab/缺陷常用）。
- **读结构文件**：`--topology POSCAR.cif --topology-format cif`（替代 `--xyz`）。

### 后处理引擎（postprocess.py，闭环第 ⑤ 步，按需调用）
- **何时用（按需，非必须）**：当你想从跑完的轨迹 / `*.out` / `*.pdos` / `*.cube` / metadyn `restart` 里**提取物理意义**（如结构有序度、扩散快慢、振动频率、电子结构）时，这些是可选的分析工具。阶段向导的"后处理"阶段会提示你该看哪些量、怎么判断结果是否合理；具体跑不跑、跑哪些，**由你决定**。
- **核心层（纯 numpy + matplotlib，零外部依赖，全部已用合成数据校验通过）**：
  - `energy` 能量/温度曲线；`rdf` 径向分布函数 g(r)；`msd` 均方位移；`diffusion` 扩散系数 D(Einstein，给 Å²/ps 与 cm²/s)；
  - `bond` / `angle` / `dihedral` 内禀几何时间序列+分布；`pdos` 态密度/投影态密度(自动按元素分解、Gaussian 展宽)；`adf` 角分布函数；`cn` 配位数；`zprofile` 轴向密度剖面；
  - `vacf` 速度自相关；`ir` / `power` 红外/振动态密度(对 VACF 做 FFT，双横轴 cm⁻¹ 与 1/ps)。
- **桥接层（检测外部二进制，缺失时给指引不中断）**：`bader`(Bader 电荷，需 `bader`)；`fes`(元动力学自由能面，调 CP2K `graph` 工具重建 FES 并出 2D 等值线，注意 `-ndim` 必须填真实 CV 数)；`travis`(TRAVIS 谱学 IR/Raman/VCD/ROA，生成控制文件并运行)。
  - **衔接要点**：RDF/MSD/ADF 需晶胞(`--cell` 或自动从 `.out` 解析)；VACF/IR 用 AIMD 默认打印的速度轨迹 `*-vel-1.xyz`(`--vel`)，无速度时可用位置轨迹差分近似。所有子命令出 `.png` + `.csv`。详见 `references/postprocess.md`。

### 项目阶段向导（guide.py，总入口）
- **它解决什么**：你不需要记"一个 CP2K 项目从头到尾要经历什么"——`guide.py` 把全流程拆成 11 个主线阶段（立项→构建→决策→收敛→优化→静态→动力学→反应路径→后处理→诊断→报告，另有 1 个续算分支），每个阶段告诉你目标、该做的清单、决策点（带指引）、常见坑、对应命令、完成判据、下一步。
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
| **A 决策知识库（权威）** | `references/decide.md`（§1–§31） | 所有"该选什么 / 为什么 / 判读结果"的答案库，含 §28 庚子讲师实操硬规则、**§29 AIMD 统计与可复现性、§30 建模硬规则、§31 AIMD 方法选择清单**（批 14 由字幕回灌） | 写输入、做方法选择、判读结果时**首选** |
| **B 课程综合（权威·主题式）** | `references/course_learned.md` | 庚子计算 5 份 PDF(425 页)+6 字幕**逐页无遗漏**内化，按主题重组的导航枢纽（含 PDF 独有公式/脚本/数值案例/坑） | 需要课程实战细节、NEB/电子结构/自由能面完整流程时 |
| **C 速查/摘要** | `references/course_notes.md`（87 行）<br>`references/course_survey.md`（100 行） | C 是课程实战精华速查；survey 是文件→天→主题映射+同音错字表 | 想快速看"经验要点"或"字幕同音错字对照"时 |
| **D 手册笔记** | `references/manual_notes.md`<br>`references/_manual_tree.txt`<br>`references/sections.md` | 官方手册的结构化笔记（SECTION 树/关键字） | 查某个 SECTION 的官方字段含义时 |
| **E 原始素材（溯源·勿改）** | `references/pdf_text/L1–L5.txt`（讲义 PDF 分页抽取，425 页）<br>`references/pdf_text/S1.1–S5.txt`（**视频字幕原文 6 份，22133 行，行号与原始字幕一致**）<br>`references/pdf_text/MAPPING.md`（**讲义页码 ↔ 字幕行号 严格对应表**）<br>`references/pdf_text/learn_L1–5.md`（逐页学习原始稿·**第一轮**）<br>`references/pdf_text/videonotes/`（**课程视频精读笔记·第二轮 6 份 / 9803 行**，带**视频时间戳**与 `⭐/⚠️` 标记；6 份与 `S1.1–S5.txt` **一一对应**）<br>`extract_pdf.py` / `extract_subtitles.py` / `build_mapping.py` | **B/C 层的来源**：无遗漏的溯源依据。**`L*.txt` 与 `S*.txt` 一律不改**（保真相）；`MAPPING.md` 由脚本生成 | 当 B 疑似遗漏某页/某段细节、需回查原文时；**引用"字幕第 N 行"前先看这里的行号约定** |
| **F 实战手册（遇到问题先查这里）** | `references/playbook.md` | **症状→诊断→处方** 的对照表 + 任务工作流 + 数值速查表 + 建模实操 + 判读经验 + 编译部署 + 报错原文速查 | **"跑出问题了怎么办""这个数该多大"** 时首选；写输入前扫一眼对应工作流 |
| **G 官方权威层（可回溯的一手基准）** | `references/official/`（README + `00_map`–`24_official_exercises` + `_sources`，共 27 文件） | **CP2K 官网 + 官方手册 + GitHub + Dashboard + 官方练习集** 逐页采集（累计 393 条目）：权威性分级 L0–L3 / `&GLOBAL` 38 关键字 / RUN_TYPE 29 值 / 单位表 / 输入语法 8 规则 / **Input Reference 完整段树 14-76-269-359-750** / 基组·GTH 赝势 / GPW·OT·k 点·CDFT·DFT+U / **CNEO 量子核·GauXC/Skala·泊松求解器·RI-HFX(Γ/k)** / SCF 与 CUTOFF 收敛 / MD 系综与平衡 / 几何·晶胞优化 / 约束 MD·蓝月系综 / NEB·NEWTON-X / 光学谱 TDDFT·GW-BSE·RT-TDDFT·RTBSE·STM / **X 射线谱四路线 ΔSCF·XAS_TDP·δ-kick·GW2X** / QM-MM·嵌入·ML 势（NequIP·MACE·NNP·PAO-ML·ACE·Kim-Gordon·DLA-Future）/ 后 HF·**BSSE 官方出处**·xTB / 重启续算 / 故障排查+FAQ 19 条 / 安装与 30 个外部库 / benchmark·GPU·Spack·参与开发 / 版本时间线 / **官方练习集 248 子页（NEB 完整输入·AIMD·系综·SGCP·i-PI·EOS·PDOS·能带·电荷差·功函数）** | **需要官方默认值、官方推荐、版本差异、报错原文、可运行算例**时；**凡 A–F 与 G 冲突，以 G 为准** |
| **H 官方教程与实战算例层** | `references/h_tutorials/`：`README.md`（层定位）<br>`txt/T01–T24.txt`（**24 份官方教材逐页抽取，701 页**）<br>`notes/01–08.md`（逐主题精读：教了什么＋核心逻辑链＋可执行要点）<br>`cases/`（**真实生产算例的输入卡原文** ＋ 配方卡）<br>`extract_tutorials.py` | **官方 workshop / howto / 夏季学校教材**（Hutter 的 GPW 与 AIMD、Watkins 的杂化泛函与 ADMM、Mueller 的自动化/脚本化/测试与性能判读、Iannuzzi 的 Zurich 教程、`howto_static/geo_opt/converging_cutoff`、2016/2018/2020 夏校练习、基组赝势、QM/MM 三份、CP2K 使用入门）＋ **随资料附带的真实生产算例**（Cu(100)-水 opt/AIMD、Au(111)-水、Au(111)-水-6Na、TiO₂-Au₂₀；含可运行 `.inp`/`.inc` 与**真实 `.out` 与轨迹**）。**G 层只把这些 PDF 当"外部资源标题"登记，未收录教材正文**——H 层补的正是"**官方怎么教、真实算例怎么写**" | 想知道**"这个参数官方教程里怎么讲、为什么这么取"**、想看**真实生产输入卡长什么样**、或需要**真实 CP2K 输出做回归/练手**时；**G 层没写而教材讲了的内容，以 H 层原文为准并标注出处** |

> **关键约定**：
> - **B 是 C 的超集且已替代 C 的深度**——C 仅作"速查"，正经内容以 B/A 为准。
> - **E 是溯源层**：保留它是为了"全面、可核对"，日常不要直接读 E（冗长）；发现 B 有误时回 E 校正，再同步回 A/B。
> - **F 是"急救层"**：不重复 A/B 的知识，只把**可执行的判断**（症状→处方、数值阈值、命令模板）提炼成对照表。遇到报错、异常、数值疑问时先查 F，需要"为什么"再回 A/B。
> - **G 是"权威层"**：A–F 都是二手转述，G 逐页采自 `cp2k.org` / `manual.cp2k.org`，带 URL + 抓取日期，可回溯核对。**G 只写官方说了什么，不写"我们觉得该怎么用"**；凡 A–F 与 G 冲突，以 G 为准并回修 A–F。官方占位页/404 一律如实标注，不编造。
> - 交叉引用已在 A、B、F、G、postprocess.md 之间打通（如 A §28 ↔ B 的 DFT+U 节 ↔ F §1.5 ↔ G `02_dft_methods.md` §8）。
> - **新增/修正资料的标准流程见 `references/MAINTENANCE.md`（分层 SOP + 无遗漏审计清单）**。

## 文件索引
- **`AGENTS.md`** —— **跨 agent 唯一真源入口**：任何 AI 助手（Claude Code / Cursor / Cline / CodeBuddy / Gemini CLI / Copilot / Aider / Zed）读这一个文件即可上手。含零依赖说明、新手三步、按需求取用表、知识分层、硬性约束、能力边界、给 AI 助手的行为指引。`CLAUDE.md` / `.cursorrules` / `GEMINI.md` / `.github/copilot-instructions.md` 都只是指向它的极简指针。
- **`USAGE.md`** —— **面向使用者的使用说明**（30 秒上手 / 十个工具用法 / 八层知识什么时候查哪一层 / 六类任务剧本 / FAQ / 已知边界）。给**人**读；`SKILL.md` 是给 **AI** 读的入口。
- `scripts/doctor.py` —— **一键环境自检**（新手第一步）：查 Python 版本 / 仓库完整性 / Python 依赖 / 外部二进制 / 校验可运行性，输出"能不能用、缺什么、下一步做什么"。支持 `--json` / `--quiet`。
- `scripts/_console.py` —— **控制台输出兼容层**（内部依赖，不是 CLI）：中文 Windows（代码页 936/GBK）下让 `✓ ✗ • ⚠ ✖ ⑪ ↻ Å ² ³` 等 GBK 无法表示的字符不再触发 `UnicodeEncodeError` + traceback。分层策略：Windows 终端 → 切 UTF-8 代码页（符号原样显示）；输出重定向 → UTF-8；都不行 → `errors="replace"` 有损兜底，**永不抛异常**。9 个 CLI 与 4 个 harness 只要 `import` 它即生效；`_doc_consistency.py` 有护栏防止漏挂或文件被删。
- `scripts/wizard.py` —— **交互式向导**（新手第二步）：一问一答问出体系类型/元素/自旋/色散/金属性等，内部复用 `recommend.py` + `gen_inp.py` 生成输入。`--yes` 可非交互直通。
- `examples/` —— **5 个开箱即用示例工程**（`01_si_bulk_static` / `02_co_molecule_vib` / `03_au_slab_ads` / `04_cu_aimd` / `05_metadyn_fes`）：每个含已校验 `.inp` + 坐标 + 逐步 README（怎么跑 / 该看什么 / 学到什么 / 下一步）。
- `scripts/recommend.py` —— **思考层①**：体系描述 → 参数推荐（含 TPSS/SCAN Meta-GGA、ADMM 推荐、Properties 推荐、恒温器建议）+ 理由 + 起步阶梯 + 生成命令。
- `scripts/diagnose.py` —— **思考层③**：读 `.out` → 诊断问题 → 给改哪行的建议。
- `scripts/guide.py` —— **项目阶段向导（总入口）**：`list`/`show <stage>`/`scan <dir>`/`next <dir>`。每个阶段告诉你该做什么；`scan` 读你目录的真实文件推断当前进度与下一步，避免空跑工作流。
- `scripts/gen_inp.py` —— 由模板生成 `.inp`（多元素 + ADMM/Meta-GGA/Properties(布居/电荷/cube 进阶)/MIXING/OT/Thermostat/NPT + 逐原子 KIND(DFT+U/自旋/质量) + NEB 进阶(多副本读取/OPTIMIZE_BAND DIIS/ALIGN_ROTATE_FRAMES/PROGRAM_RUN_INFO/CONVERGENCE_INFO) + QM/MM(MIXED/FIST/Quickstep-PM6) 等全部进阶开关）。
- `scripts/validate_inp.py` —— 内置语法校验（零依赖；白名单含 ADMM/TPSS/SCAN/MGGA_X_SCAN 等新 SECTION）。
- `_validate_all.py` —— **权威校验 harness**：用 `cp2k-input-tools` 的 `CP2KInputParser`（对照官方 `cp2k_input.xml`）生成并解析 **29 类**特征输入，输出 error/warning（已处理 pint/fs 工具坑）。
- `_official_validate.py` —— 单文件权威校验（对单个 .inp 跑 `CP2KInputParser`，把 `fs` 误报降级为 NOTE）。
- `verify_out/*.inp` —— 7 个已通过权威校验的示例输入（HSE06/TPSS/SCAN/MD-NPT/PULAY/OT-CG/B3LYP）。
- `scripts/parse_output.py` —— 解析 `.out` 取能量/受力/收敛。
- `scripts/postprocess.py` —— **后处理引擎**（闭环第 ⑤ 步）：子命令 `energy / rdf / msd / diffusion / bond / angle / dihedral / pdos / adf / cn / zprofile / vacf / ir / power`（纯 numpy+matplotlib，零外部依赖）+ 桥接 `bader`(Bader 电荷) / `fes`(元动力学自由能面，调 CP2K graph) / `travis`(谱学)。详见 references/postprocess.md。
- `_validate_postprocess.py` —— 后处理端到端校验 harness（合成数据：随机气箱验 RDF/ADF/CN、已知 D 的布朗运动验 MSD/diffusion、阻尼振子验 VACF/IR 频谱峰值、伪造 .pdos 验绘图、2D 抛物线验 FES 出图），全子命令 0 error / 0 crash。**注意它的 RDF 锚点是单帧随机气体 —— 单帧抓不到"归一化被写进帧循环"这类错误**（见下一条）。
- `_validate_rdf_cn.py` —— **RDF 归一化的解析型验证**（零依赖）：用定义验证 `CN = ∫g(r)ρ_B·4πr²dr` 必须等于**逐帧直接数出来**的平均近邻数，不依赖任何参照实现，且默认 **40 帧**（多帧才能暴露重复归一化）。`--postprocess <路径>` 可指向别的副本做 A/B 对照。它守的是这样一个真实 bug：`postprocess.py` 的归一化原本写在帧循环体内，1 帧时完全正确、2535 帧时**偏 1659 倍**。
- `_doc_consistency.py` —— **文档口径一致性自检**（零依赖）：实测模板数/阶段数/校验用例数/子命令数，与文档中的口径表述比对，防止"23 类 vs 15 类"式数字漂移。改完文档必跑；`--list` 可查真值。另含 3 项**代码健壮性护栏**：入口是否都挂控制台兼容层、是否有跟随 locale 的文本 I/O、`--json` 支持情况。
- `_collect_new_items.py` —— **学习稿回灌核验工具**（维护用，零依赖）：从 `learn_L*.md` 与精读报告里抽出所有标 `【新】` 的条目，再对消费层（B/C/A/F/postprocess）做线索检索，给出"疑似已落 / 疑似未落 / 需人工"的**分诊报告**。`MAINTENANCE.md` Phase 3 要求"禁止无核验地写'全部已收录'"，本脚本就是那个核验手段。`--stats` 看统计，`--verify` 出报告。
- `_kw_probe.py` —— **官方关键字查询工具**（维护用，需 cp2k-input-tools）：直接查 `cp2k_input.xml` 拿某个 SECTION/KEYWORD 的**类型、默认值、单位、枚举**，用来给讲师口述"对表"。三种用法：`--section <路径>` 列子项、`<路径>/<关键字>` 打详情、**`--find <关键字名>` 全库搜它属于哪些段**；`--json` 给结构化输出。**遇到"这个参数默认多少/什么单位/它在哪一段/合法取值有哪些"的疑问，先跑它，别猜。**
  - **`--find` 也搜别名**（这是必需能力，不是锦上添花）：CP2K 一个关键字可有多个 `<NAME>`，如 `EXTRAPOLATION` 的别名是 `INTERPOLATION` 与 **`WF_INTERPOLATION`**。只搜默认名会 0 命中，进而把**合法写法误判成"关键字不存在"** —— 真实生产卡 7/7 张都写 `WF_INTERPOLATION ASPC`，就是这么差点被误判的。
  - ⚠️ **版本前提（2026-10 补，很重要）**：它查的是 `cp2k-input-tools` 随包分发的那份 XML，当前是 **CP2K 9.0**（XML 内 `<CP2K_VERSION>CP2K version 9.0</CP2K_VERSION>`）。**所以它给出的每个"默认值"严格说都是"9.0 的默认值"**：
    ① 引用时**不要写成无版本的"官方默认"**，本仓库统一口径是"（9.0 XML）"；
    ② **跨版本会变**，典型如 `&CELL_OPT TYPE` 在 **2026.2 被移除**，而 9.0 的 XML 里它还在 —— 这类"版本差异"**本工具查不出来**，要看 G 层的版本变更记录；
    ③ **要核对自己手上那版**：设环境变量 **`CP2K_INPUT_XML`** 指向你 CP2K 安装目录里的 `cp2k_input.xml`，工具就改查那一版（也可以是官方手册上任意版本的 XML）。现在输出头部会自动打印版本（`--version` 亦可单查），避免"结论脱离它成立的前提"。
  - ✅ **跨版本核验结论（2026-10，可复现）**：本库**断言过的 48 项核心默认值**在 **CP2K 9.0 与 2022.1** 两份官方 XML 上**逐条比对、全部一致**；两版之间的 **63 处默认值差异全在 `PW_DFT`/`ATOM`/RI-RPA 等旁支**，与 Quickstep 主线无关。唯一与知识库相关的一处是 `FORCE_EVAL/DFT/ENERGY_CORRECTION/EPS_DEFAULT`（9.0 `1E-12` → 2022.1 `1E-7`），已在 `decide.md §7.1` 就地标明。⇒ **默认值语料是跨版本稳健的**，但引用前仍建议用 ③ 复核一次。
  - **同名关键字可能出现在多个段**（如 `RUN_TYPE` 在 `/GLOBAL` 与 `/ATOM` 下默认值不同），所以**查关键字要带段路径**，否则会看到另一个段的默认值而误判。
  - 它也是**唯一能定案单位争议**的手段。实例：`TIMECON` 官方默认 `1.0E3`、单位 `fs`；而 `[wavenumber_t]` **确实是合法的 CP2K 时间单位**（值取波数 cm⁻¹，CP2K 换算成该振子的周期 `t[fs] = 33356.40952 / ν̃[cm⁻¹]`）。所以 `TIMECON 1000`（=1000 fs）与 `TIMECON [wavenumber_t] 1000`（=**33.36 fs**，强 30 倍）**不是同一个东西** —— 讲师说的"波数"没错，是**换了个单位**。
  - 同类的定案还有 `EPS_DEFAULT/100` 的归属：官方原文是 `EPS_CORE_CHARGE` "Overrides **EPS_DEFAULT/100.0**"、`EPS_GVG_RSPACE`/`EPS_PGF_ORB` "Overrides **SQRT(EPS_DEFAULT)**"。
  - 也用来**定案教材存疑**：`--find EMAX_SPLINE` 查出它在 `FORCE_EVAL/MM/FORCEFIELD/SPLINE`（**经典 MM 样条**，默认 0.5 hartree），而不是 QS 的 `&KIND`；`--find POISSON_SOLVER` 给出别名 `POISSON`/`PSOLVER`。
- `_audit_h_citations.py` —— **H 层引用审计**（零依赖）：核验 `references/h_tutorials/notes/*.md` 里的 `T** P**` 页码能否回 `txt/` 的对应页对上。H 层的价值主张就是"逐页可回溯"，本工具是那个承诺的**检验手段**：越界引用（`T05 P99` 而 T05 只有 43 页）是硬错误必须为 0；引号片段对不上的按"疑似错页 / 无法定位 / 公式记号 / 关键字标签"分类，只有第一类需人工修。`--detail` 列明细，`--json` 给结构化输出。
- `_audit_videonotes_citations.py` —— **E 层引用审计**（零依赖；**文件名是历史遗留**，它现在查**两类**引用）。本轮把 6 份视频精读笔记（9803 行）的成果并进 A/B/C/F，四层里新增 **174 条** `videonotes/<笔记名> L###` 引用；而 B/C 层用得**更多**的是 **545 条 `S*.txt:<行号>` 字幕/讲义引用**（`S5.txt:2071`、`S4.txt:2447–2448` 这种）。H 层有 `_audit_h_citations.py` 守 `T** P**`，**这两类此前都没有工具在守**。硬错误（必须 0）：① `videonotes/` 的**笔记名要能唯一解析**到 6 份之一（支持 `cp2k-4-…-精读笔记` 缩写，按 `…` 前的**前缀唯一匹配**）—— 本轮真抓到 `decide.md` 两条把笔记名省成光一个省略号，读者回不去原文；② 行号必须在文件范围内（`cp2k-1-1` 只有 1195 行，写 `L99999` 就是错的）；③ **`S*.txt` 必须是真实存在的文件**且**行号在该文件实际行数内**（对照 11 份 `S*/L*.txt` 实测行数）。软指标：`videonotes/` 引用行 ±60 行内**应当能找到 `[mm:ss–mm:ss]` 时间戳**，找不到只列"待复核"（时间戳常标在整段末尾）。当前 **174 + 545 = 719 处 / 硬错误 0 / 软指标 0**。`--detail`、`--json` 同 H 层那个。**改完 A–F 任何一层都要重跑。**
  > ⚠️ **写文档举例说明"坏写法"时，行号请写成 `L###` 占位**：审计的正则只认 `L` 后跟数字，`L###` 天然被跳过；写成真数字会让它把例子当成真引用而误报（本轮踩过）。
- `_gen_cp2k_sections.py` —— 从官方 `cp2k_input.xml` 重新生成 `scripts/_cp2k_sections.py`（**1342 个官方 SECTION 名**，含 14 个顶层段）。`validate_inp.py` 靠它判段名拼写：手工维护的子集只有 156 个（覆盖率 12%），会把 `&MULLIKEN` 这类合法官方段误报成 typo —— 这个假阳性是**拿 H 层 `cases/` 里的真实生产输入卡去跑**才暴露的。生成物是纯数据模块，不影响零依赖。
- `references/gen_inp_options.md` —— **gen_inp.py 进阶开关全集**（§0 快速定位表 + 泛函阶梯/ADMM/Properties/SCF 工具箱/MD/逐原子 KIND/NEB/元动力学/QM-MM 共 10 节）。SKILL.md 正文只留最常用几条，细节按需读本文件。
- `references/playbook.md` —— **F 层实战手册（遇到问题先查这里）**：症状→诊断→处方对照表（SCF 不收敛/几何振荡/报错原文/后处理算错/磁性 DFT+U）、任务工作流（收敛测试/AIMD/NEB/频率/FES/电子结构/功函数/QM-MM）、数值速查表（单位换算/EPS_SCF↔能量漂移/BSSE/CUTOFF/成本估算）、建模实操（切表面/晶格旋转/异质结/溶剂层/团簇）、判读经验（RDF/VACF/扩散/电荷方法可信度）、CP2K 适用边界、编译与部署、报错原文速查。每条经验标注来源 `[L*]`/`[字*]`。
- `references/decide.md` —— **决策知识库（§1–§31）**：泛函阶梯(GGA→Meta-GGA→杂化)/基组/赝势/q 表/自旋/色散/k点/SMEAR/CUTOFF/ADMM/混合法/恒温器/Properties(PRINT 全套：EFG/超精细/Hirshfeld/Wannier/DOS/PDOS/STM/cube/MOMENTS)/方法选择(xTB/DFTB/QM-MM/NNP/Embedding)/增强采样与反应路径(NEB/元动力学/CONSTRAINT)/CELL_OPT/Post-HF(MP2/RPA)/NEB 输入结构/计算技术(OT/对角化/ELPA/GPU)/**SCF 收敛全流程决策(§22：EPS_SCF/MAX_SCF/SCF_GUESS/ADDED_MOS/CHOLESKY 落点纠正、OT vs 对角化、MIXING/SMEAR/OUTER_SCF/MOM 关键字枚举与取舍)**/振动分析(VIBRATIONAL_ANALYSIS：DX/INTENSITIES/THERMOCHEMISTRY/FULLY_PERIODIC)/经典力场(FORCEFIELD：PARMTYPE/PARM_FILE_NAME + EWALD_TYPE SPME)/其它 FORCE_EVAL 方法(DFTB/NNP/EIP/MIXED)+采样器(TMC/PILE 路径积分)/**XC_FUNCTIONAL 内置泛函清单(PADE/PBE/BP86/BLYP/TPSS/SCAN/PBE0/B3LYP/HSE06/BEEFVDW…)与 VDW_POTENTIAL(PAIR_POTENTIAL DFT-D3(BJ)/NON_LOCAL vdW-DF/rVV10)** 的选择理由 + 结果判读对照表。**§29–§31（批 14 由课程字幕回灌）**：AIMD 的统计/重复性/可复现性（混沌、多副本随机化、单轨迹怎么写）、建模硬规则（密度建准可跳过 NPT、异质结 mismatch 2–3%、真空层、四指数只输三个）、AIMD 方法选择清单（调参总原则、DFT+U 判据、磁性、`&KIND` 拆价态、ADMM 界限）。
- `references/sections.md` —— 各 SECTION 含义与推荐取值速查（含 PROPERTIES/ADMM/Meta-GGA 条目）。
- `references/workflow.md` —— **项目阶段向导总文档**：11 阶段完整指引（目标/该做的/决策点/坑/命令/完成判据）+ 陪跑路径 + 与其他脚本的关系。
- `references/templates/*.inp` —— static / geo_opt / cell_opt / aimd_md / metadyn / neb / vib / qmmm **八类模板**（均含 __ADMM_BLOCK__/__MIXING_BLOCK__/__OT_BLOCK__/__DFT_PRINT_BLOCK__/__FE_PRINT_BLOCK__/__LOCALIZE_BLOCK__/__THERMOSTAT_BLOCK__/__RESTART_BLOCK__/__SURFACE_DIPOLE_BLOCK__ 等 token）。

## 输入正确性验证（重要）

所有模板与生成逻辑都对照 **CP2K 官方参考手册（`cp2k_input.xml`，由 `cp2k-input-tools` 自动生成）** 校验过，**29 类特征组合全部解析通过（0 error / 0 warning）**。

```bash
# 权威校验：用 cp2k-input-tools 的 CP2KInputParser 解析生成的所有特征输入
# 依赖安装（两步，原因见 requirements-dev.txt 的「已知的钉版冲突」；
# cp2k-input-tools 0.9.1 自己钉了 Pint<0.24，与本仓库需要的 pint>=0.24.4 互斥）：
#   python -m pip install --no-deps "cp2k-input-tools==0.9.1"
#   python -m pip install "pint>=0.24.4" transitions "pydantic>=2,<3.0" lxml
python _validate_all.py        # 生成 29 类输入并逐个解析，输出错误/警告
python _official_validate.py verify_out/*.inp   # 单文件权威校验
```

> **退出码语义（2.7.2 起）**：`_validate_all.py` 在「生成失败 / error / warning」
> 任一出现时 `exit 1`，小结按 `解析通过/总数` 显示。此前它**无论发生什么都会报
> "0 errors, 0 warnings across 28 cases" 并以 0 退出**（假绿，CI 拦不住回归）。
>
> 已知工具坑（已在 shim 中解决，不影响生成结果）：
> - `cp2k-input-tools` 0.9.1 声明 `Pint<0.24`，但 pint < 0.24 会调用 numpy 2.x 已移除的
>   `cumproduct`。实测 **pint 0.26.1 与该工具完全兼容**（28/28 用例 0 error / 0 warning），
>   故用 `--no-deps` 装它、再单独装现代 pint。
> - `cp2k-input-tools` 的 `pint_units.txt` 未定义 CP2K 时间单位 `[fs]`（会误判为 femtosiemens）→ 已在校验脚本里注入 `fs = femtosecond` 并把该误报降级为 NOTE（不计入 warning、不影响退出码）。
> - `&GLOBAL` **没有** `BACKUP_COPIES` 关键字；它属于 `&RESTART`（MOTION/PRINT/RESTART）子节 —— 已改正。
> - `&PROPERTIES` 不能直接装 DOS/PDOS/STRESS/DIPOLE；按上文"放置规则"分落到正确 `&PRINT`。
- `references/run.md` —— 本地与 Slurm 提交命令。
- `references/postprocess.md` —— IR / DOS / PDOS / 能带 / 轨迹 / 电荷 后处理方法。
- `references/course_survey.md` —— **课程资料梳理**：11 文件→5 天→主题映射、字幕同音错字对照表、字幕 vs 讲义互补分析、与 skill 覆盖对照（学习庚子计算视频字幕的入口）。
- `references/course_notes.md` —— **视频字幕实操精要**：后处理工具流（VMD RDF 球面积分 / MSD 平方再平均 / TRAVIS / ELF / 电荷差分）、参数硬经验（DFT+U 必加、BSSE 高估吸附能、OT vs 对角化）、建模实操、实例索引、错字对照表；沉淀讲师"怎么真正跑起来"的经验层。
- `references/course_learned.md` —— **5 天课程主题式综合知识库（逐页无遗漏内化）**：覆盖 5 份 PDF(425 页)+6 份字幕的全部内容，按主题重组为导航枢纽——AIMD 理论基础/后处理公式/CP2K 编译与建模/输入参数全集/NEB 完整流程/电子结构分析(TRAVIS·Bader·PDOS·ELF·功函数)/自由能面(PMF·slow-growth·metadynamics·QM-MM)；含 PDF 独有的公式·参数表·脚本·数值案例·坑，并交叉引用 decide.md/postprocess.md/course_notes.md。是"字幕+PDF 逐页对照"的权威沉淀（批 13 内化）。
- `references/pdf_text/README.md` —— 原始素材的溯源层说明：**讲义 + 字幕双份清单（含 sha256）**、`MAPPING.md` 用法、**行号/页码引用约定**、讲义↔字幕错位表（含"实际讲课比大纲慢半拍"）、同音错字高频例、溯源维持约定（E 层，日常勿直接读）。
- `references/pdf_text/MAPPING.md` —— **讲义页码 ↔ 字幕行号 严格对应表**（由 `build_mapping.py` 生成，`--check` 可校验分段连续性）：5 个讲义 deck 的页→主题索引、**28 条对应锚点**、6 份字幕逐段主题表。**要定位"某个知识点的课程原文"时先查它。**
- `references/official/` —— **G 层官方权威层**（27 文件，逐页采自 cp2k.org + manual.cp2k.org + GitHub + Dashboard + 官方练习集，均带来源 URL + 抓取日期）：
  - `README.md` 层定位与边界（G 只写官方原话；A–F 与 G 冲突以 G 为准；`[默认]`/`[官方推荐]`/`[示例]` 标注规则）
  - `00_map.md` 官网+手册完整内容地图、HowTo 19 项、exercises 2014–2025 索引、官方学习路径
  - `01_global_and_units.md` `&GLOBAL` **38 个关键字**（类型/默认值/别名）+ `RUN_TYPE` **29 个取值** + 单位表 11 类 + Si bulk8 完整官方示例
  - `02_dft_methods.md` GPW/GAPW·赝势·基组·**OT 两套算法**·k 点（含功能兼容表）·LRIGPW·ADMM/HFX·**CDFT**·**DFT+U 官方算例**·色散校正（vdw 页 404 的替代来源）
  - `03_scf_convergence.md` SCF 收敛（**2024.1 起不收敛默认 ABORT**；官方数值建议 MAX_SCF 16–32 / OUTER_SCF 8–16）+ CUTOFF 收敛（`Ecutᵢ = Ecut₁/α⁽ⁱ⁻¹⁾`，**最终推荐 CUTOFF 250 + REL_CUTOFF 60**）
  - `04_sampling_md.md` MD 系综表·温控器（**默认 NOSE，官方推荐 CSVR**）·NPT 四步·时间步长·AIMD 电子设置·平衡协议·**官方验证清单 10 项**·Do/Don't·26 行关键字速查
  - `05_optimization.md` GEO_OPT vs CELL_OPT·优化器（BFGS 默认/LBFGS/CG）·收敛判据原文·约束·**CELL_REF 固定网格点数**·40+ 行关键字表
  - `06_properties.md` 性质计算索引 + **11 项官方缺口清单**（如实标注，不编造）
  - `07_restarting.md` 波函数/k 点 `.kp`·**Harris 三步链**·Band/NEB 每 replica 波函数·MD `&EXT_RESTART` 全表·CDFT 重启
  - `08_errors_and_faq.md` 官方故障排查 8 类 + FAQ 19 条正文（含 **HFX `EPS_PGF_ORB` 警告机理**、`cp_fm_cholesky` CPASSERT、**已过时的"CP2K 无 k 点"表述**）
  - `09_build_libraries.md` 安装 6 项前提 + **30 个外部库** + CMake 标志全集 + CUDA/HIP 加速器 + 3 条编译 FAQ
  - `10_features_resources.md` **官方功能全清单**（"能不能算 X"速查表）+ 缩写表 130 条 + 引用规范 + 许可 + 学习资源
  - `11_version_changelog.md` 版本时间线 2.0→2027.1 + **不兼容变更专题汇总**（升级前逐条自查）
  - `12_authority_sources.md` **权威性 4 级分级（L0–L3）** + 官方渠道逐个核实（GitHub README Links 节 / manual / dashboard / Google Group / 资助页）+ 可复现判定流程 + 反例澄清
  - `13_input_syntax_and_print.md` 输入语法 **8 条官方规则**（`&` 段/大小写/`#`·`!` 注释/单位方括号/续行/三态逻辑值）+ **printkey 迭代层级**（`1_4_5`=第 4 MD 步第 5 SCF 步）+ `EACH`/`ADD_LAST`/`COMMON_ITERATION_LEVELS`/`FILENAME` + `cp2k --html` 排查法
  - `14_basis_and_potentials.md` **BASIS_SET 文件格式逐行讲解**（第 9 行六数字、主量子数被忽略、基函数计数公式）+ **GTH 赝势 qN 完整清单**（约 100 元素）+ **5 个赝势库** + 基组/赝势一致性检查
  - `15_optical_and_xray.md` LR-TDDFT（TDA 基础/`&TDDFPT`/sTDA/`DIPOLE_FORM` 三档适用面）+ **GW+BSE**（`evGW0` 官方推荐/内存估算/仅分子）+ RT-TDDFT·Ehrenfest（三传播子/`MAT_EXP` ARNOLDI 快 5 倍/`&EFIELD`）+ STM（Tersoff-Hamann/仅 Γ 点/输出三维 cube）
  - `16_qmmm_embedding_ml.md` QM/MM 完整蛋白质教程（chorismate mutase/`&QM_KIND`/`E_COUPL` 三档/AMBER HO·HG 的 LJ 改法/`&LINK` IMOMM/侧链电荷中和）+ GROMACS QM/MM + **镜像电荷 IC-QM/MM**（`WIDTH`/MME）+ 嵌入 + **6 种 ML 势**（DeePMD `ATOMS_DEEPMD_TYPE` 必须匹配）
  - `17_constrained_dynamics_and_paths.md` **约束 MD + 蓝月系综**（`&COLVAR`+`&COLLECTIVE`/`INTERMOLECULAR`/`TARGET`/`TARGET_GROWTH`/SHAKE vs RATTLE 乘子/单位陷阱/Z 重加权公式/两原子距离可直接平均 λ、三原子距离差不可）+ NEB（占位页 4 链接）+ **NEWTON-X 表面跳跃**（Tully 跳跃概率/OD·Baeck-An 耦合及引用要求/完整输入）
  - `18_posthf_semiempirical_and_xray.md` 后 HF 五步准备（PBS/RI 基组/赝势/预优化轨道/`ERI_METHOD` 三档限制）+ MP2 三实现 + RPA/SOS-MP2（Clenshaw-Curtis 30–40 点 vs Minimax 6–8 点）+ **BSSE 官方专节（来源确证）** + 低标度后 HF（`SORT_BASIS EXP`/`EPS_FILTER`/`MEMORY_CUT`）+ **xTB/DFTB**（原生 vs tblite/k 点/spGFN2）+ RTBSE（von Neumann/COHSEX/需先做 GW/Padé 插值）+ 振动耦合 + X 射线谱 4 页清单
  - `19_performance_gpu_community.md` **官方 benchmark suite 5 项**（H2O-64/Fayalite-FIST/LiH-HFX/H2O-DFT-LS/H2O-64-RI-MP2，含全部结果表）+ 测试机器规格 + **Dashboard 回归测试矩阵** + CUDA/HIP 逐条编译选项 + Spack 完整用法 + 库配置细节 + **参与开发完整 PR 流程**
  - `20_input_reference_tree.md` **Input Reference 完整段树**：14 顶层段 / 76 第二层 / 269 第三层 / 359 页面 / **750 直接关键字** + 各段规模表 + 实操路径表 17 条 + **同级段语义不同警告**（`&PRINT/&FORCES` 在 `&FORCE_EVAL`/`&MOTION`/`&MD` 下语义不同，务必写全路径）
  - `21_xray_spectroscopy_full.md` **X 射线谱四路线完整正文**：ΔSCF（GAPW 全电子/4 部分流程/谱文件 6 列）+ **XAS_TDP**（三近似/`DONOR_STATES`/`KERNEL`/CO₂·NaAlO₂·TiCl₄ 三例/官方 5 条 FAQ）+ δ-kick（时间步比周期小一个数量级/需跑 3 次/规范选择）+ **GW2X**（`ω = ε_a − ε_I + Δ_xc`/只能配杂化泛函/OCS 修正 1.9 eV/官方 3 条 FAQ）
  - `22_ml_embedding_dlaf.md` **ML 势 5 页 + 嵌入 + 线性代数**：NequIP/Allegro（`&NEQUIP`/LibTorch 2.4–2.7/与 LAMMPS 一致）+ MACE（导出脚本/每 rank 求值整个体系再除 rank 数）+ NNP（n2p2 格式/委员会 8 个/`RAD_SPLINE_N` 8192）+ PAO-ML（五步/`MAX_PAO 0` + `PENALTY_STRENGTH 0.0` 是"力正确"必要条件）+ ACE（官方标 TODO）+ **Kim-Gordon**（减法方案/非可加动能/`&COORD` 第四列标子系统）+ **DLA-Future**（GPU 大矩阵优化/小矩阵可能更慢）
  - `23_dft_subpages_full.md` **DFT 子页正文补遗**：**CNEO-DFT**（量子核 + 位置约束/`POTENTIAL CNEO`/`BASIS_SET NUC`/GAPW 必需/PB4-D～PB6-H/同位素 √(m_d/m_p) 缩放）+ **GauXC/Skala**（外部 XC 积分器/分子求积 vs 原生网格/`PAW_ONE_CENTER` 15 个交叉项/NLCC 增强 ρ 与 ∇ρ 而 τ 仅价电子）+ **静电与泊松求解器**（边界条件是物理不是数值/六求解器选型表/带电体系无真空无关极限/不同求解器能量不自动同参考）+ **RI-HFX/RI-HFXk**（Bussy2023/2024、~O(N³) vs 与 k 点网格无关、局域原子特异 RI 基、BvK 超胞装球要求）
  - `24_official_exercises.md` **官方练习集全采**（21 课程 / **248 子页** / 239 有正文 / 约 170 万字符）：**NEB 7 页完整可运行输入**（`common:neb` 最小可跑 + `2015_cecam_tutorial:neb` 的 **`MULTIPLE_FORCE_EVALS` QM/MM 混合力场做 NEB** + IT-NEB 三条硬规则）+ **AIMD/BOMD 方程** + **SGCP 三方对比表与 6 参数设置** + 系综（截断 < 盒半边长且 > σ）+ 元动力学（20 Å 真空/CV 选择）+ **i-PI 联用与超算 HOST 替换脚本** + **Birch–Murnaghan EOS** + **k 点只支持 GGA/不支持杂化做能带** + 电荷密度差/功函数（Cubecruncher）+ 官方书单与工具 + **239 页完整清单** + **9 个官方空链接页如实登记**
  - `_sources.md` 溯源清单：**393 个条目**/URL/完整度/缺口 + 官方页面自身笔误登记 + 待补采集清单 + 抓取方法备忘
- `references/h_tutorials/` —— **H 层：官方教程与实战算例**（新层，与 G 层分工见下）：
  - `README.md` 层定位与边界（G 层答"官方规定了什么"，H 层答"官方怎么教的、真实算例怎么写"）、24 份教材清单 + 页码、引用约定、抽取假象说明
  - `txt/T01–T24.txt` **24 份官方教材逐页抽取（701 页，带 `========== PAGE N ==========`）**：Hutter 的 **GPW** 与 **AIMD/BOMD**、Watkins 的 **杂化泛函与 ADMM**、Mueller 的 **自动化/脚本化/测试**(T06; 文件名里的 Parallelization 有误导)、Iannuzzi 的 **Zurich 2017（GPW 与 GAPW）**、`howto_static` / `howto_geometry_optimisation` / `howto_converging_cutoff`、2016 夏校（AIMD/表面 OPT/HFX）、2018 夏校 **SCF 设置（对角化 vs OT）**、2020 UZH **NEB**、官方练习汇总、**基组与赝势**、**QM/MM 三份**、**CP2K 使用入门**、CP2K 输入基础与运行
  - `notes/01–08.md` 逐主题精读：**教了什么 ＋ 核心逻辑链 ＋ 可执行要点 ＋ 与 A–G 层的增量/冲突**
  - `cases/` **真实生产算例的输入卡原文**（Cu(100)-水 opt/AIMD、Au(111)-水、Au(111)-水-6Na、TiO₂-Au₂₀）＋ 配方卡；随资料附带**真实 `.out` 与轨迹**（最大 21.9 MB），可作为 `parse_output.py`/`diagnose.py`/`postprocess.py` 的**真实回归数据**（现有 harness 用的是合成数据）
  - `extract_tutorials.py` 抽取脚本（按 sha256 去重：源目录 27 个 PDF 里有 3 对完全重复 → 24 份唯一内容）
- `references/MAINTENANCE.md` —— **skill 维护 SOP**：新增/修正资料的七阶段流程、A–H 分层模型、命名约定、字幕同音错字处理、「无遗漏」审计清单、交叉引用维护。往 skill 加新资料时照此执行，保证不堆乱、跨对话可复用。
