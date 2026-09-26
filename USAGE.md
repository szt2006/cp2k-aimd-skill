# cp2k-aimd 使用说明

> 面向使用者。想改这个 skill 请读 `CONTRIBUTING.md` 与 `references/MAINTENANCE.md`；
> 想知道"为什么这么设计"请读 `README.md`；想知道"改过什么"请读 `CHANGELOG.md`。

---

## 1. 它是什么，不是什么

**它是什么**：一个 CP2K 计算的**全过程参谋**。在每个阶段告诉你——该考虑什么、各选项的取舍、该盯哪些指标判断好坏、常见坑在哪，并给出**你可以自己决定跑不跑**的命令。

**它不是什么**：

| 它不做 | 说明 |
|---|---|
| ❌ 替你提交 CP2K 作业 | 它给提交命令（`references/run.md`），但作业在你自己的 HPC/本地跑 |
| ❌ 从零生成初始结构 | 不切表面、不建溶剂盒。能读你已有的 CIF/XYZ，但结构得你自备（官方练习集里有 VESTA/Avogadro 建 slab 教程，见 G 层 `24_official_exercises.md`） |
| ❌ 自动跑完整个流程 | 没有"一键出结果"。每个工具都是你按需调用 |
| ❌ 编造官方没说过的话 | 官方占位页/404/空链接一律如实登记（G 层 `_sources.md` 有缺口清单） |

**一句话**：它把课题组的经验和官方原文固化成"随时可查的判断"，**决定权始终在你**。

---

## 2. 安装与加载

```bash
# 用户级（所有对话/项目自动加载）
cp -r cp2k-aimd ~/.workbuddy/skills/
```

或在 WorkBuddy 的 skill 管理里「导入本地目录」指向本仓库。

**用别的 AI 助手也能用**（Cursor / Claude Code / Codex / Gemini CLI / Copilot / Aider / Zed）：

| 助手 | 它会读 |
|---|---|
| Claude Code | `CLAUDE.md` → 指向 `AGENTS.md` |
| Cursor | `.cursorrules` → 指向 `AGENTS.md` |
| Codex / Aider / Zed / 其它 | `AGENTS.md` |
| Gemini CLI | `GEMINI.md` → 指向 `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md` → 指向 `AGENTS.md` |

**`AGENTS.md` 是唯一真源**，其余都是极简指针。整个 skill 是纯文本 + 零依赖脚本，
复制到任何位置都能用（脚本用 `__file__` 相对定位资源，无硬编码路径）。

**依赖**：

```bash
pip install -r requirements.txt        # 运行依赖：numpy / matplotlib（后处理出图用）
pip install -r requirements-dev.txt    # 开发依赖：cp2k-input-tools / pint / lxml / pdfplumber（校验用）
```

> 十个 CLI 工具中，`doctor` / `wizard` / `recommend` / `gen_inp` / `validate_inp` / `parse_output` / `diagnose` / `verify_forces` / `guide`
> **零第三方依赖**，纯标准库，装了 Python 就能跑。
> 只有 `postprocess.py` 需要 numpy + matplotlib（缺了会友好提示并 `exit 3`，不会抛 traceback）。
>
> **不确定环境行不行？跑 `python scripts/doctor.py`**，它会逐项检查并告诉你缺什么、怎么补。

**在 WorkBuddy 里怎么触发**：直接说人话即可，例如
"帮我看看这个 Au slab 吸附 O 该怎么设参数"、"SCF 不收敛怎么办"、"帮我算这个轨迹的 RDF"。
skill 的 `read_when` 触发词覆盖了 cp2k / AIMD / NEB / 元动力学 / PDOS / DFT+U / QM-MM 等。

---

## 3. 30 秒上手

### 完全新手：三步

```bash
cd <skill 目录>

# ① 环境自检（第一次必跑）——告诉你这台机器能不能用、缺什么
python scripts/doctor.py

# ② 交互式向导——一问一答生成第一个 .inp
python scripts/wizard.py

# ③ 照着示例跑一遍（含已校验输入 + 逐步说明）
#    打开 examples/01_si_bulk_static/README.md
```

### 熟悉命令行：完整链路

```bash
cd <skill 目录>

# ① 看有哪些阶段
python scripts/guide.py list

# ② 让工具"问诊"一个体系，拿推荐参数 + 可直接跑的命令
python scripts/recommend.py --elements Au O --goal geo_opt --periodic xy \
    --multiplicity 3 --vdw auto --accuracy balanced

# ③ 按它给的命令生成 .inp
python scripts/gen_inp.py --type geo_opt --elem Au O \
    --basis DZVP-MOLOPT-SR-GTH DZVP-GTH-PADE \
    --potential GTH-PBE-q11 GTH-PADE-q6 \
    --multiplicity 3 --dispersion --periodic xy --smear --kpoints "4 4 1" \
    -o geo_opt.inp

# ④ 语法自检
python scripts/validate_inp.py geo_opt.inp

# ⑤ 提交（命令见 references/run.md）
mpirun -n 4 cp2k.popt geo_opt.inp 1>cp2k.out 2>cp2k.err

# ⑥ 跑完读结果 + 诊断
python scripts/parse_output.py cp2k.out
python scripts/diagnose.py cp2k.out

# ⑦ 想从轨迹里提取物理量就后处理
python scripts/postprocess.py rdf cp2k-pos-1.xyz --pairs "Au O"
```

> **`-o` 是 `--output` 的短名**。注意 `--out` 会与 `--outer-scf` 撞车（argparse 报 ambiguous），写 `-o` 或 `--output`。
> **输出路径的目录必须已存在**，`gen_inp.py` 不会自动建目录。
>
> **MD/元动力学步数太大？** 模板默认 500000 步（生产级）。先用 `--steps 500` 做冒烟测试，
> 确认能跑通再放大。

---

## 4. 八层知识：什么时候查哪一层

这是本 skill 最核心的部分。**按"你想知道什么"选层**：

| 你想知道… | 查这层 | 文件 |
|---|---|---|
| "该选什么泛函/基组/参数？为什么？结果怎么判读？" | **A 决策库** | `references/decide.md`（§1–§31） |
| "课程的完整流程/公式/数值案例是什么？" | **B 课程综合** | `references/course_learned.md` |
| "快速看要点 / 字幕错字对照" | **C 速查** | `references/course_notes.md`、`course_survey.md` |
| "某个 SECTION 的字段含义" | **D 手册笔记** | `references/manual_notes.md`、`sections.md` |
| "跑出问题了怎么办？这个数该多大？" | **F 实战手册** | `references/playbook.md` |
| **"官方默认值是多少？官方推荐什么？官方怎么说的？"** | **G 官方权威层** | `references/official/` |
| 要回查原始讲义 / 字幕原文（B 疑似遗漏、想核对"字幕第 N 行"） | **E 溯源层** | `references/pdf_text/`（只读；**`MAPPING.md` 可把页码与行号互相定位**） |
| 想按**视频时间**找内容（"讲师在 1:20:30 说的那个"）／想看**录屏里实际的操作** | **E 层·视频精读** | `references/pdf_text/videonotes/`（第二轮精读，6 份，带 `[mm:ss]` 时间戳；与 `S*.txt` 一一对应，可交叉核对） |
| **"这个参数官方教程里怎么讲、为什么这么取？"／"真实生产输入卡长什么样？"** | **H 官方教程与实战算例** | `references/h_tutorials/`（`notes/` 精读笔记；`cases/` 真实算例输入卡） |
| "gen_inp 有哪些进阶开关？" | 入口配套 | `references/gen_inp_options.md` |

### 4.1 优先级规则（重要）

> **凡 A–F 与 G 冲突，一律以 G 为准。**

G 层是唯一**逐页采自官方**、带 URL + 抓取日期的层，可回溯核对。A–F 都是二手转述。

> **G 层没写、只有 H 层教材讲了的内容**（如某实操阈值、某工具流程），**以 H 层原文为准**，
> 并标注 `T** P**` 页码（如 `T05 P30`）便于回原文核对。
> H 层教材自身也有过时处（如 T24 锚定 CP2K 2.5.1 ≈ 2014，其默认值须回 G 层复核），
> 已在各精读笔记的"冲突 / 存疑"节逐条标注 —— **引用 H 层前先看那一节**。

### 4.2 G 层怎么查（27 个文件）

G 层按主题编号，**先看 `official/README.md` 定位，或直接按编号找**：

| 编号 | 主题 | 典型问题 |
|---|---|---|
| `00_map` | 官网+手册地图、HowTo 19 项、学习路径 | "官方有哪些教程？" |
| `01_global_and_units` | `&GLOBAL` 38 关键字 / `RUN_TYPE` 29 值 / 单位表 | "RUN_TYPE 有哪些取值？" |
| `02_dft_methods` | GPW/GAPW、OT、k 点、CDFT、DFT+U、色散 | "OT 和传统对角化怎么选？" |
| `03_scf_convergence` | SCF 收敛 + CUTOFF 收敛 | "CUTOFF 该取多少？" |
| `04_sampling_md` | MD 系综、温控器、平衡协议、验证清单 | "NVT 用什么恒温器？" |
| `05_optimization` | GEO_OPT/CELL_OPT、优化器、收敛判据 | "BFGS 还是 CG？" |
| `06_properties` | 性质计算索引 + 官方缺口清单 | "能算 EFG 吗？" |
| `07_restarting` | 波函数/k 点/Harris/NEB/MD 重启 | "中断了怎么续算？" |
| `08_errors_and_faq` | 故障排查 8 类 + FAQ 19 条 | "这个报错官方怎么说？" |
| `09_build_libraries` | 安装 + 30 个外部库 + CUDA/HIP | "编译要装哪些库？" |
| `10_features_resources` | 功能全清单 + 缩写表 130 条 | "CP2K 能不能算 X？" |
| `11_version_changelog` | 版本时间线 + 不兼容变更 | "升级前要自查什么？" |
| `12_authority_sources` | 权威性 L0–L3 分级 | "这个来源可信吗？" |
| `13_input_syntax_and_print` | 输入语法 8 规则 + printkey 迭代层级 | "怎么只打印第 4 步的力？" |
| `14_basis_and_potentials` | BASIS_SET 格式 + GTH 赝势 qN 清单 | "Au 的赝势 q 是多少？" |
| `15_optical_and_xray` | TDDFT、GW-BSE、RT-TDDFT、STM | "怎么算吸收谱？" |
| `16_qmmm_embedding_ml` | QM/MM、镜像电荷、嵌入、6 种 ML 势 | "QM/MM 怎么设边界？" |
| `17_constrained_dynamics_and_paths` | 约束 MD、蓝月系综、NEWTON-X | "怎么算 PMF？" |
| `18_posthf_semiempirical_and_xray` | 后 HF、BSSE 官方出处、xTB/DFTB、RTBSE | "BSSE 官方怎么说？" |
| `19_performance_gpu_community` | benchmark、GPU、Spack、参与开发 | "怎么编译 GPU 版？" |
| `20_input_reference_tree` | **Input Reference 完整段树** 14/76/269/359/750 | "`&FORCES` 该放哪一层？" |
| `21_xray_spectroscopy_full` | ΔSCF、XAS_TDP、δ-kick、GW2X 四路线 | "怎么算 XAS？" |
| `22_ml_embedding_dlaf` | NequIP、MACE、NNP、PAO-ML、ACE、Kim-Gordon、DLAF | "怎么用机器学习势？" |
| `23_dft_subpages_full` | CNEO、GauXC/Skala、泊松求解器、RI-HFX | "带电体系怎么选泊松求解器？" |
| `24_official_exercises` | **官方练习集 248 子页**（含 NEB 7 页完整输入） | "NEB 的输入怎么写？" |
| `_sources` | 393 条目溯源清单 + 缺口 | "哪些还没采？" |

> **★ NEB 特别提示**：官方手册的 NEB 页是**占位页**（"nobody has gotten around to writing this page yet"）。
> NEB 的官方知识**只在练习页里**，已全部采入 `24_official_exercises.md` §1（7 页完整可运行输入）。
> 这是本 skill 相对官方手册的**独有优势**。

---

## 5. 十个工具怎么用

> **前两个是给新手准备的入口**（`doctor` 自检、`wizard` 向导），后面八个是主力工具。
> 全部 CLI 都支持 `--json`（给 agent / 脚本调用）。

### 5.0 `doctor.py` — 环境自检（新手第一步）

```bash
python scripts/doctor.py            # 人类可读
python scripts/doctor.py --json     # 机器可读
python scripts/doctor.py --quiet    # 只输出结论（CI 用）
```

检查 5 组：Python 版本（≥3.8）/ 仓库完整性（6 CLI + 控制台兼容层 + 1 后处理 + 5 个校验 harness + 8 模板 + G 层 27）/
Python 依赖 / 外部二进制（cp2k / mpirun / bader / travis / graph）/ 校验可运行性。

末尾给出结论（`核心功能可用 ✓` 或列出缺失项）与**下一步该做什么**。

> 外部二进制缺失**不影响**生成/校验输入——只有实际跑计算或特定后处理才需要。

### 5.0b `wizard.py` — 交互式向导（新手第二步）

```bash
python scripts/wizard.py            # 一问一答
python scripts/wizard.py --yes      # 非交互，全用推荐默认值
```

7 类体系（分子/团簇、表面吸附、块体/晶体、表面 slab 优化、AIMD、NEB、振动分析），
8 个提问点（类型 / 元素 / 开壳层 / 多重度 / 色散 / 金属 / 结构文件 / 输出名）。

**它内部调用 `recommend.py` + `gen_inp.py`**，不重写参数推理——所以向导给的参数
和直接用 CLI 得到的完全一致（单一真源）。

### 5.1 `recommend.py` — 问诊（思考层①）

**用途**：描述体系 → 推理参数 → 给理由 + 起步阶梯 + 可直接执行的生成命令。

```bash
python scripts/recommend.py --elements Au O --goal geo_opt --periodic xy \
    --multiplicity 3 --vdw auto --accuracy balanced
```

**常用参数**：

| 参数 | 取值 | 说明 |
|---|---|---|
| `--elements` | 元素列表 | 必填，如 `Au O` |
| `--goal` | `energy` / `geo_opt` / `cell_opt` / `md` / `neb` / `vib` / `ts` / `qmmm` | `ts` = 过渡态 Dimer 法；`qmmm` = QM/MM |
| `--periodic` | `xyz` / `xy` / `none` | 块体 / 表面 slab / 分子 |
| `--multiplicity` | 整数 | 开壳层（O₂、自由基、多数吸附态）必开 |
| `--vdw` | `auto` / `yes` / `no` | 弱作用/层状结构建议 `auto` |
| `--accuracy` | `fast` / `balanced` / `accurate` | 控制 CUTOFF 与 k 点密度 |
| `--functional` | `PADE` / `PBE` / `TPSS` / `SCAN` / `HSE06` / `B3LYP` | 覆盖默认 PBE |
| `--json` | — | 机器可读输出 |

**它会自动做的事**：按元素逐个查好赝势的 `q` 值；识别金属自动建议 `SMEAR` + k 点；识别 d 电子过渡金属自动建议 `DFT+U`；识别吸附/层状自动建议色散。

**输出分四段**：推荐参数 → 选择理由（每条带"为什么"）→ 起步阶梯（4 步）→ 生成命令。

### 5.2 `gen_inp.py` — 生成输入

```bash
python scripts/gen_inp.py --type geo_opt --elem Au O \
    --basis DZVP-MOLOPT-SR-GTH DZVP-GTH-PADE \
    --potential GTH-PBE-q11 GTH-PADE-q6 \
    --multiplicity 3 --dispersion --periodic xy --smear --kpoints "4 4 1" \
    -o geo_opt.inp
```

**八类模板**（`--type`）：`static` / `geo_opt` / `cell_opt` / `aimd_md` / `metadyn` / `neb` / `vib` / `qmmm`

**最该记住的进阶开关**（完整清单见 `references/gen_inp_options.md`）：

| 场景 | 开关 |
|---|---|
| 泛函阶梯 | `--functional TPSS` / `SCAN` / `HSE06` / `B3LYP` |
| 杂化降本 | `--admm`（大体系必配，降 3–5x） |
| 表面 slab | `--periodic xy --fixed-atoms "1..54"`（冻结底层）+ `--surface-dipole` |
| 强关联 TM | `--kinds "Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=5.0:U=3"` |
| SCF 不收敛 | `--mixing-method pulay`（金属）/ `--ot-minimizer cg` / `--outer-scf` |
| 长 AIMD | `--restart-freq N`（必开）+ `--walltime <秒>`（按队列时限收尾）+ `--thermostat langevin` |
| 读结构文件 | `--topology POSCAR.cif --topology-format cif` |
| NEB | `--xyz-replicas a.xyz b.xyz ...` / `--optimize-band DIIS` / `--k-spring 0.05` |
| 元动力学 | `--well-tempered` / `--metadyn-ww` / `--multi-walker` / `--plumed` |
| **MD 步数** | `--steps 500`（冒烟测试）/ 默认 AIMD 500000、metadyn 200000（生产级） |
| **机器可读** | `--json`（返回 `ok` / `output` / `type` / `kinds` / `bytes`） |

> **`--steps` 是新手最该知道的一个开关**：模板默认 50 万步，直接跑会让你以为程序卡死。
> 先 `--steps 500` 确认流程通了，再放大到生产规模。

### 5.3 `validate_inp.py` — 语法自检（零依赖）

```bash
python scripts/validate_inp.py out.inp
python scripts/validate_inp.py --cp2klint out.inp   # 额外跑官方 cp2klint（需安装）
python scripts/validate_inp.py --json out.inp       # 机器可读（ok / errors / warnings）
```

内置白名单含 ADMM/TPSS/SCAN/MGGA_X_SCAN 等新 SECTION。**生成 .inp 后先跑这个，再提交。**

### 5.4 `parse_output.py` — 解析输出

```bash
python scripts/parse_output.py cp2k.out
python scripts/parse_output.py cp2k.out --json     # 机器可读
```

取能量 / 受力 / 收敛信息，含 SCF 收敛计数、"CP2K 不收敛也会继续下一步"警示、eV 换算、`PROGRAM ENDED` 状态。

### 5.5 `diagnose.py` — 诊断（思考层③）

```bash
python scripts/diagnose.py cp2k.out
python scripts/diagnose.py cp2k.out --verbose      # 显示 WARNING 明细与能量统计
python scripts/diagnose.py cp2k.out --json         # 机器可读（findings + stats）
```

判断 SCF / 几何 / 能量 / 虚频是否健康，**并告诉你下一步可改哪一行**（如"加 `--smear`""减 `TIMESTEP`" "换 `OPTIMIZER CG/BFGS`"）。

> **它给的是方向，不是命令。** 改不改、怎么改，你决定。方向对应的处方表在 `references/playbook.md` §1。

### 5.5b `verify_forces.py` — 物理不变量三检验（**判"物理算得对不对"**）

`validate_inp.py` 只能证"输入合法"，`diagnose.py` 只能读"输出里有什么" ——
**两者都判不了"这套设置算出来的东西对不对"**。有一类缺陷正钻这个空子：输入完全合法、
CP2K 不报错、SCF 照常"收敛"，**但结果是错的**（实测遇到过总能量差 **12 Ha**）。
用**三个物理不变量**去查：

| 检验 | 判据 | 成本 | 实测：正确 / 偏心 WAVELET（错 12 Ha） |
|---|---|---|---|
| ① 力-能量自洽 | `F = −dE/dx`（中心差分） | 每自由度 2 个单点 | `1.5e-4` ✅ ／ `6.8e-3`（相对 0.07%）**判通过** |
| ② 力平衡 | `\|ΣF\| = 0`（牛顿第三定律） | **0** —— 参考输出里就有 | `0.0020` ✅ ／ **`24.7` ❌** |
| ③ 整体平移不变性 | 整体平移后 `ΔE = 0`（仅 `PERIODIC NONE`） | 1 个单点 | `1.0e-4` ✅ ／ **`1.22e+1` ❌** |

> 🔴 **第①行那个"判通过"必须看懂**：检验一查的是**力与能量面是否自洽**，不是能量面本身对不对。
> 偏心 WAVELET 那个错**恰好自洽** —— 解析力是那个**错误**能量面的**正确**导数，
> 所以检验一**判它通过**。**②③才是抓这类错误的主力，而且都极便宜。**
> `check` 的输出在通过时也会明说："这只证明自洽，不证明算对了"。

```bash
# ① 生成：参考几何 + 每个选中自由度的 ±h 位移输入（默认挑受力最大的 2 个原子）
python scripts/verify_forces.py emit cp2k.inp --ref-out cp2k.out -o vf/

# ② 把这些 vf_*.inp 跑成**单点**（每个自由度 2 次，都很快）

# ③ 判定
python scripts/verify_forces.py check cp2k.out vf/
python scripts/verify_forces.py check cp2k.out vf/ --json      # 机器可读
```

判据是 **`残差 ≤ max(1e-3, 2%×|F|)`**（相对 + 绝对混合）。真实 CP2K 2022.1 实测：
正确计算残差约 `1e-4 ~ 1.5e-4`，留 ~7 倍余量；而偏心 `POISSON_SOLVER WAVELET`
那种错误残差在 `1e0` 量级 —— **中间有三个数量级的安全带**。

**两个必须知道的限制**（工具会主动提示，不会让你误以为"过了就没问题"）：

- **力太小时不灵敏**：`emit` 会检查待测原子的 `|F|`，低于 `0.05 a.u.` 就**告警**。
  原因很实在：接近极小点的几何所有力只有 ~0.02 a.u.，而"彻底算错"能造成的残差也是这个量级
  —— 那时**错误的计算也可能"通过"**。正确做法是先明显扰动几何（如把一根键拉长 0.1 Å）再测。
- **只在单点上成立**：`GEO_OPT` / `MD` 里"力"不是纯势能梯度，`&FIXED_ATOMS` 约束住的原子同理
  （工具会自动把被约束的原子剔除并提示）。

### 5.6 `postprocess.py` — 后处理（24 个子命令）

**核心层（纯 numpy + matplotlib，零外部依赖）**：

```bash
python scripts/postprocess.py energy cp2k.out                       # 能量/温度曲线
python scripts/postprocess.py rdf cp2k-pos-1.xyz --pairs "Au O"     # 径向分布函数 g(r)
python scripts/postprocess.py msd cp2k-pos-1.xyz --sel "1..10"      # 均方位移
python scripts/postprocess.py diffusion cp2k-pos-1.xyz              # 扩散系数 D
python scripts/postprocess.py bond cp2k-pos-1.xyz --i 1 --j 2       # 键长（--i/--j 必填）
python scripts/postprocess.py angle cp2k-pos-1.xyz --i 1 --j 2 --k 3      # 键角
python scripts/postprocess.py dihedral cp2k-pos-1.xyz --i 1 --j 2 --k 3 --l 4  # 二面角
python scripts/postprocess.py pdos cp2k-Au_k1-1.pdos                # 态密度（自动按元素分解）
python scripts/postprocess.py cn cp2k-pos-1.xyz --pairs "Au O" --rcut 3.5   # 配位数
python scripts/postprocess.py adf cp2k-pos-1.xyz --center 1         # 角分布（--center 必填）
python scripts/postprocess.py zprofile cp2k-pos-1.xyz               # 轴向密度剖面
python scripts/postprocess.py vacf --vel cp2k-vel-1.xyz             # 速度自相关
python scripts/postprocess.py ir --vel cp2k-vel-1.xyz               # 红外/振动态密度（FFT）
```

**电子结构 / 光谱 / 自由能（同样零外部依赖）**：

| 子命令 | 用途 |
|---|---|
| `power` | 功率谱（等价于 `ir`） |
| `cube` | Gaussian cube 的**平面平均**（可任选轴）—— 静电势/密度剖面 |
| `cdd` | **电荷密度差分** Δρ = ρ_AB − Σρ_frag（⚠️ 各片段**绝不能再单独优化**） |
| `workfunc` | **功函** Φ = E_vac − E_F，并换算成相对 SHE 的电极电势 |
| `ir-static` | **静态** IR（频率 + 强度 → 高斯展宽），与 AIMD 的 `ir` 互补 |
| `arrhenius` | 多温度 `D` → **Arrhenius 拟合**出 Ea 与 D₀（锂离子迁移那套） |
| `pmf-rdf` | 由 RDF 反推**能垒** w(r) = −RT·ln g(r) |
| `dipoles` | Wannier 中心 → 每帧偶极（**同时是 TRAVIS 的前置自检**） |

**桥接层（检测外部二进制，缺失时给指引不中断）**：

| 子命令 | 需要什么 | 用途 |
|---|---|---|
| `bader` | `bader` 二进制 | Bader 电荷 |
| `fes` | CP2K `graph` 工具 | 元动力学自由能面（**`--ndim` 必须填真实 CV 数**） |
| `travis` | TRAVIS | 谱学 IR/Raman/VCD/ROA |

**衔接要点**：
- RDF / MSD / ADF 需要晶胞（`--cell 'a b c'`，或自动从 `.out` 解析）
- VACF / IR 用 AIMD 默认打印的 `*-vel-1.xyz`（`--vel`），无速度轨迹时可用位置差分近似
- 所有子命令都出 `.png` + `.csv`
- **全部 24 个子命令都支持 `--json`**，返回 `{ok, command, outputs:[...], stdout}`，
  方便脚本/agent 拿到产物路径

详见 `references/postprocess.md`；各子命令的完整参数用 `python scripts/postprocess.py <子命令> --help`。

### 5.7 `guide.py` — 阶段向导（总入口）

```bash
python scripts/guide.py list                  # 看全 11 个主线阶段 + 1 个续算分支
python scripts/guide.py show optimize         # 展开"几何优化"阶段完整指引
python scripts/guide.py scan /path/to/project # 读你的目录，推断卡在哪、下一步做什么
python scripts/guide.py next /path/to/project # 只给下一步行动
python scripts/guide.py --json list           # 机器可读（list / show / scan / next 都支持）
```

**`scan` 为什么不是空壳**：它真的读你目录里的文件——`.inp` / `.out` / `*-pos-1.xyz` 轨迹 / `*.pdos` / `*.cube` / `ACF.dat` / `HILLS` / `fes.dat`，据此推断进度。

实测例子（扫描只有 `.inp` 的目录）：

```
推断当前阶段：③ 计算方法与参数决策（安全起点）
  · 已生成输入 t1_hse06.inp, ... 但未运行。下一步：校验 + 提交计算（见 references/run.md）。
```

---

## 6. 11 个主线阶段：陪跑流程

`guide.py list` 输出的阶段顺序：

```
① 立项与问题定义 → ② 体系构建 → ③ 参数决策 → ④ 收敛测试 → ⑤ 几何/晶胞优化
→ ⑥ 静态/电子结构性质 → ⑦ 分子动力学(AIMD/MD) → ⑧ 反应路径(NEB/元动力学)
→ ⑨ 后处理分析 → ⑩ 结果诊断 → ⑪ 总结报告
（↻ 续算：任何阶段被中断都可能触发的旁路分支，不属于主线顺序）
```

**闭环不是直线的**：⑩ 诊断常把你打回 ⑤/⑥/⑦ 调参重算——这正是"按结果不断调整"的常态。

**标准陪跑路径**：

1. 开新项目 → `guide.py show define` 想清楚要算什么
2. 结构就绪 → `guide.py show decide` + `recommend.py` 定参数
3. 生成 `.inp` → `guide.py scan .` 确认"下一步去提交"
4. 跑完 → `guide.py scan .` 看它提示做收敛检查 / 后处理 / 诊断
5. 每一步都对照 `show <stage>` 的"决策点"和"常见坑"——**别跳过收敛测试、别拿未收敛当结果**

完整阶段指引见 `references/workflow.md`。

---

## 7. 典型任务剧本

### 剧本 A：表面吸附（Au slab 吸附 O）

```bash
# 1. 问诊（金属 + 吸附 → 自动建议 SMEAR + k 点 + 色散）
python scripts/recommend.py --elements Au O --goal geo_opt --periodic xy \
    --multiplicity 3 --vdw auto --accuracy balanced

# 2. 生成（注意冻结底层 + 表面偶极修正）
python scripts/gen_inp.py --type geo_opt --elem Au O \
    --basis DZVP-MOLOPT-SR-GTH DZVP-GTH-PADE \
    --potential GTH-PBE-q11 GTH-PADE-q6 \
    --multiplicity 3 --dispersion --periodic xy --smear --kpoints "4 4 1" \
    --fixed-atoms "1..54" --surface-dipole -o ads.inp

# 3. 校验 → 提交 → 读结果
python scripts/validate_inp.py ads.inp
python scripts/parse_output.py cp2k.out
python scripts/diagnose.py cp2k.out
```

### 剧本 B：金属氧化物 DFT+U（Fe₃O₄）

```bash
# recommend 会自动识别 d 电子 TM 并建议 DFT+U
python scripts/recommend.py --elements Fe O --goal geo_opt --periodic xyz --plus-u auto

# 逐原子 KIND 带 U 值与自旋
python scripts/gen_inp.py --type geo_opt --elem Fe O \
    --kinds "Fe:DZVP-MOLOPT-SR-GTH:GTH-PBE-q16:mag=5.0:U=3" \
    -o fe3o4.inp
```

> **硬规则**（A 层 §28 / F 层 §1.5）：含 d 电子过渡金属的氧化物/硫化物**几乎必加 DFT+U**，否则能带和 d 带中心错。

### 剧本 C：NEB 过渡态

```bash
# 官方练习集给了最小可跑流程（24_official_exercises.md §1）
# 1. 先优化两端（GEO_OPT）
python scripts/gen_inp.py --type geo_opt --elem C H Cl --project ch3cl -o init.inp

# 2. 再生成 NEB
python scripts/gen_inp.py --type neb --elem C H Cl \
    --xyz-replicas init.xyz final.xyz \
    --optimize-band DIIS --k-spring 0.05 -o neb.inp
```

**三条硬规则**（官方原文，见 `24_official_exercises.md` §1）：
1. 起始 `&REPLICA` 必须**第一个**
2. 终止 `&REPLICA` 必须**最后一个**
3. `&OPTIMIZE_BAND` **必需**（照抄）

**推荐流程**：先 `NSTEPS_IT 5` 跑 5 步 IT-NEB，再开 CI-NEB。

### 剧本 D：AIMD + 后处理

```bash
# 1. 生成 AIMD（长跑必开 restart-freq）
python scripts/gen_inp.py --type aimd_md --elem Cu O \
    --ensemble nvt --thermostat langevin --restart-freq 100 -o aimd.inp

# 2. 跑完做后处理
python scripts/postprocess.py energy cp2k.out
python scripts/postprocess.py rdf cp2k-pos-1.xyz --pairs "Cu O" --cell "12.8 12.8 12.8"
python scripts/postprocess.py msd cp2k-pos-1.xyz --sel "1..64"
python scripts/postprocess.py diffusion cp2k-pos-1.xyz --dim 2
python scripts/postprocess.py vacf cp2k-vel-1.xyz
python scripts/postprocess.py ir --vel cp2k-vel-1.xyz
```

### 剧本 E：SCF 不收敛

```bash
# 1. 先诊断，看它建议改哪行
python scripts/diagnose.py cp2k.out

# 2. 对症下药（金属 → PULAY；OT 的 DIIS 不行 → CG；仍不行 → OUTER_SCF）
python scripts/gen_inp.py --type static --elem Au --smear \
    --mixing-method pulay -o retry.inp
python scripts/gen_inp.py --type static --elem Au --ot-minimizer cg -o retry2.inp
python scripts/gen_inp.py --type static --elem Au --outer-scf -o retry3.inp
```

报错原文与完整处方表见 `references/playbook.md` §1.1。

### 剧本 F：查官方默认值

直接读 G 层。例如"`&MD` 默认用哪个恒温器？"

```bash
# 在 references/official/04_sampling_md.md 里查（官方：默认 NOSE，官方推荐 CSVR）
```

---

## 8. 常见问题

**Q：工具跑不了，报缺 numpy？**
只有 `postprocess.py` 需要 numpy/matplotlib。缺了它会提示安装命令并 `exit 3`。其余六个工具零依赖。

**Q：`gen_inp.py` 报 `ambiguous option: --out`？**
`--out` 同时匹配 `--outer-scf` 和 `--output`。用 `-o` 或 `--output`。

**Q：生成时报 `FileNotFoundError`？**
输出路径的目录必须已存在，`gen_inp.py` 不自动建目录。先 `mkdir -p`。

**Q：我是新手，从哪儿开始？**
```bash
python scripts/doctor.py    # ① 环境自检
python scripts/wizard.py    # ② 一问一答生成第一个输入
# ③ 打开 examples/01_si_bulk_static/README.md 照着跑一遍
```

**Q：用 Cursor / Claude Code / Copilot 能用吗？**
能。它们读 `AGENTS.md`（或对应的指针文件 `CLAUDE.md` / `.cursorrules` / `GEMINI.md` /
`.github/copilot-instructions.md`）。整个 skill 是纯文本 + 零依赖脚本，复制到任意位置可用。

**Q：程序好像卡住了，一直不动？**
AIMD/元动力学模板默认 **50 万步**（生产级），单机跑几天很正常。
先用 `--steps 500` 做冒烟测试确认流程通了，再放大。

**Q：想给脚本/agent 拿机器可读结果？**
所有 9 个 CLI 都支持 `--json`。例如：
```bash
python scripts/validate_inp.py --json out.inp
python scripts/guide.py --json scan ./myproject
python scripts/diagnose.py --json cp2k.out
```

**Q：怎么知道文档里的数字是不是最新的？**
```bash
python _doc_consistency.py --list      # 实测真值
python _doc_consistency.py             # 检查文档口径是否与真值一致
```
它**不硬编码真值**，而是数模板文件、数 STAGES、数子命令，所以不会随版本失效。

**Q：A 层和 G 层说法不一样，信谁？**
**信 G。** G 逐页采自官方，带 URL 可核对；A–F 是二手转述。冲突时 G 为准，并回修 A–F。

**Q：官方练习集里的 9 个空链接页是什么？**
`exercises:common` 索引里 `blue_moon`/`gga`/`hfx`/`mlp`/`pimd`/`tddft`/`vdos`/`vdw`/`wavefun` 这 9 页**官方实际不存在**（"This topic does not exist yet"）。已如实登记在 `24_official_exercises.md` §5，**不编造**。

**Q：官方没说但课程说了的结论怎么办？**
标注为经验级结论，不冒充官方出处。例：官方确认"后 HF 方法存在严重 BSSE 且 CP2K 因多基组并用而加剧"，但**未直接说**"高斯基组高估吸附能"——后者仍属经验级。

---

## 9. 自检（改完任何内容都跑）

```bash
python _doc_consistency.py        # 文档口径一致性（零依赖）
python _validate_postprocess.py   # 后处理端到端校验（需 numpy + matplotlib）
python _validate_all.py           # 输入权威校验（需 requirements-dev.txt）
```

> **三项必须串行跑**，且后两项需在同一个有 numpy 的环境里。
> 并行跑会因临时目录内存竞争报 `MemoryError('bad allocation')`。
> 详见 `references/MAINTENANCE.md` 黄金规则第 9 条。

**当前状态**（2026-09-09）：

| 校验 | 结果 |
|---|---|
| `_doc_consistency.py` | OK：文档口径全部一致（模板 8 类 / 主线 11 阶段 / 校验 29 类 / 子命令 24 个 / G 层 27 文件 / 示例 5 个） |
| `_validate_postprocess.py` | ALL POSTPROCESS SUBCOMMANDS PASSED (0 error / 0 crash) |
| `_validate_all.py` | 0 errors, 0 warnings across 28 cases |

---

## 10. 已知边界（如实登记）

| 边界 | 说明 |
|---|---|
| 不能从零建结构 | 不切表面、不建溶剂盒。能读已有 CIF/XYZ，结构需自备 |
| 不替你提交作业 | 给命令，你跑 |
| Input Reference 750 关键字默认值未逐条抄录 | 段树已索引在 `20_input_reference_tree.md`，**这是当前唯一剩下的高优先级缺口** |
| 部分官方页自身截断 | `ri_gamma` 例 2、`ri_kpoints` 输入尾部、`ace` 标 TODO —— 官方缺口，如实登记 |
| 官方占位页 | NEB / 线性标度 / 红外 / QM-QM / DFTB 的手册页是占位页（NEB 已由练习集补齐） |
| 课程素材版权 | `references/pdf_text/` 版权归原作者，仅作学习与溯源，不在 MIT 范围内 |

---

## 11. 相关文档

| 文档 | 什么时候看 |
|---|---|
| `AGENTS.md` | **跨 agent 通用入口**（Cursor / Claude Code / Codex / Gemini / Copilot 都读它） |
| `README.md` | 快速了解定位与能力清单 |
| `SKILL.md` | skill 入口（自动加载），含完整文件索引 |
| `CHANGELOG.md` | 想看改过什么 |
| `CONTRIBUTING.md` | 想贡献改动 |
| `references/MAINTENANCE.md` | 想往 skill 加资料（七阶段 SOP） |
| `references/workflow.md` | 11 阶段完整指引 |
| `references/playbook.md` | 遇到问题先查这里（症状→处方） |
| `references/official/README.md` | G 层定位、标注规则、缺口清单 |
| `examples/README.md` | 5 个示例工程的索引与推荐顺序 |
