# AGENTS.md — CP2K 计算顾问（跨 agent 通用入口）

> 本文件是**唯一真源**。任何 AI 编码助手（Claude Code / Cursor / Cline / CodeBuddy /
> Gemini CLI / Copilot / Aider / Zed …）读到这里，就掌握了使用本 skill 所需的全部信息。
>
> 其它入口文件（`CLAUDE.md` / `.cursorrules` / `GEMINI.md` / `.github/copilot-instructions.md`）
> 都只是指向本文件的**极简指针**，不重复内容，避免多份说明互相漂移。

---

## 1. 这是什么

一套**CP2K 计算顾问**的知识库 + 工具链。它不替用户跑计算，而是：

- 在**每个阶段**告诉用户该考虑什么、有哪些取舍、坑在哪、该盯哪些指标
- 提供**可调用的命令行工具**（参数推荐 / 生成输入 / 校验 / 解析 / 诊断 / 后处理）
- 按 **11 个主线阶段**陪跑项目：立项 → 构建 → 参数决策 → 收敛测试 → 几何/晶胞优化 →
  静态/电子结构 → 分子动力学 → 反应路径 → 后处理 → 结果诊断 → 总结报告

**设计原则：顾问，而非自动驾驶。** 工具都是"给用户、由用户决定执行"，不自动替用户跑完流程。

## 2. 零依赖，直接可用

核心 7 个脚本**只用 Python 标准库**，无需 pip 安装任何东西：

```bash
python scripts/guide.py       # 阶段向导
python scripts/recommend.py   # 参数推荐
python scripts/gen_inp.py     # 生成 .inp
python scripts/validate_inp.py# 语法校验
python scripts/parse_output.py# 解析 .out
python scripts/diagnose.py    # 诊断问题
python scripts/verify_forces.py# 物理不变量三检验（判"算得对不对"）
```

仅 `scripts/postprocess.py`（出图）需要 `numpy` + `matplotlib`。

**第一步永远先跑自检**：

```bash
python scripts/doctor.py
```

它会检查 Python 版本、脚本完整性、依赖、外部二进制，并给出下一步建议。
看到 `结论：核心功能可用 ✓` 即可开始。

## 3. 新手从这里开始

```bash
python scripts/doctor.py          # 1. 环境自检
python scripts/wizard.py          # 2. 交互式向导（一问一答生成输入）
python scripts/guide.py list      # 3. 看 11 个阶段，找到自己该做什么
```

**5 个开箱即用的示例**在 `examples/`，每个都有已校验的 `.inp` 和说明：

| 目录 | 体系 | 学到什么 |
|---|---|---|
| `examples/01_si_bulk_static` | Si 块体 | 最小闭环 |
| `examples/02_co_molecule_vib` | CO 分子 | 非周期计算 + 振动 |
| `examples/03_au_slab_ads` | Au slab + O | 表面吸附 |
| `examples/04_cu_aimd` | Cu 金属 | AIMD 系综/恒温器 |
| `examples/05_metadyn_fes` | TiO₂ | 增强采样 + DFT+U |

详见 `examples/README.md`。

## 4. 按需求取用

| 用户想做什么 | 用什么 |
|---|---|
| 不知道该做什么 | `python scripts/guide.py scan <项目目录>` |
| 不知道参数怎么选 | `python scripts/recommend.py --elements <元素> --goal <目标>` |
| 想生成输入但不想记参数 | `python scripts/wizard.py` |
| 生成了输入要检查 | `python scripts/validate_inp.py <文件>.inp` |
| 跑完要看结果 | `python scripts/parse_output.py <文件>.out` |
| 结果不对要诊断 | `python scripts/diagnose.py <文件>.out` |
| **怀疑"算错了"但语法没问题** | `python scripts/verify_forces.py emit/check` —— **三个物理不变量**：① 力-能量自洽 `F = −dE/dx`；② 力平衡 `\|ΣF\| = 0`（免费）；③ 整体平移不变性（多 1 个单点）。**其它护栏查的都是语法与自洽，"输入合法、CP2K 不报错、结果却是错的"这类缺陷（实测遇到过差 12 Ha 的）只有它能抓。** ⚠️ 但**别只信 ①**：实测偏心 WAVELET 那个错在 ① 下**残差仅 0.067%、判通过**（因为力是那个**错误**能量面的**正确**导数）——**②③才是主力** |
| 要出图/算物性 | `python scripts/postprocess.py <子命令> ...` |
| 想看某个阶段的完整指引 | `python scripts/guide.py show <stage>` |

`<stage>` 取值：`define` `build` `decide` `converge` `optimize` `static` `dynamics`
`react` `postproc` `diagnose` `report` `resume`。

## 5. 知识分层（需要深入时读）

按**权威性从高到低**：

| 层 | 文件 | 内容 |
|---|---|---|
| **G 官方权威层** | `references/official/`（27 个文件） | 逐页采自 cp2k.org / manual.cp2k.org，含官方练习集 248 页；每文件头带来源 URL |
| **H 官方教程与实战算例** | `references/h_tutorials/` | **官方 workshop / howto / 夏季学校教材**（24 份 PDF，701 页，逐页抽取带页码）＋ **真实生产算例**（可运行 `.inp` 输入卡 + 真实 `.out`/轨迹）。**G 层只登记这些 PDF 的标题，未收录其教材内容**；H 层补的正是"官方怎么教、真实算例怎么写" |
| **F 实战手册** | `references/playbook.md` | 症状→处方、工作流、报错速查 |
| **A 决策库** | `references/decide.md` | 写输入/选方法/判读结果的答案库（§1–§31） |
| **B 课程综合** | `references/course_learned.md` | 庚子计算讲义内化（主题式导航） |
| **C 速查** | `references/course_notes.md`、`course_survey.md` | 实战精华 |
| **D 手册笔记** | `references/manual_notes.md`、`sections.md` | 手册摘录 |
| **E 原始素材** | `references/pdf_text/` | 讲义分页抽取 `L1–L5.txt` + **字幕原文 `S1.1–S5.txt`** + **`MAPPING.md` 讲义↔字幕对应表** + **`videonotes/` 课程视频精读笔记·第二轮**（带视频时间戳，与 `S*.txt` 一一对应）（**原文溯源用，逐字勿改**） |

**冲突裁决原则：A–F 与 G 冲突时一律以 G 为准。** G 层没写、只有教材讲了的内容（如某实操阈值），
以 H 层教材原文为准并标注出处。

## 6. 硬性约束（做任何改动前必读）

1. **所有改动只在本地副本做**，不改 GitHub 上游。
2. **改完必须串行重跑三项校验**（用同一解释器）：
   ```bash
   python _doc_consistency.py      # 文档一致性
   python _validate_postprocess.py # 后处理数值正确性
   python _validate_all.py         # 全量校验
   ```
3. **健壮性基线**：无参数 → usage + exit 2；`--help` → exit 0；
   缺依赖 → 友好提示 + exit 3；文件不存在 → 友好中文 + exit 1，**不抛 traceback**。
4. **不要删 `.workbuddy/`**（项目数据，非缓存）。
5. 详见 `CONTRIBUTING.md`。

## 7. 诚实的能力边界

- **能**讲清怎么建模、怎么选参数、怎么判读结果
- **不能**从零生成初始结构（只能用用户已有的 CIF/xyz；切表面、建盒子需用户自备）
- **不能**替用户提交 CP2K 作业（在用户的 HPC 上跑）
- `gen_inp.py` **支持** NEB 输入生成：`--type neb`（`RUN_TYPE BAND` + `&BAND`）带
  多副本外部读取（`--xyz-replicas ./0.xyz …`，`NUMBER_OF_REPLICA` 自动取文件数）、
  `--band-type`（CI-NEB / IT-NEB）、`--optimize-band {MD,DIIS}` +
  `--optimize-end-points`、`--align-frames` / `--rotate-frames`、`--nproc-rep`、
  `--k-spring`、`--neb-max-force` / `--neb-rms-force`、
  `--program-run-info` / `--convergence-info` 等开关（完整清单见
  `references/gen_inp_options.md` §8）
- `gen_inp.py` **不支持** Dimer 等**单端过渡态**配方（`GEO_OPT TYPE TRANSITION_STATE`
  + `&TRANSITION_STATE METHOD DIMER`），需按 `references/decide.md` §17 / §20 手动拼

---

## 给 AI 助手的行为指引

当用户提到 CP2K 相关需求时：

1. **先判断用户处于哪个阶段**——不确定就建议跑 `guide.py scan <目录>`。
2. **不要一次性输出全部参数**，而是按阶段给"当前该做什么 + 为什么 + 可选命令"。
3. **不要假装能跑 CP2K**——只生成输入、校验、解析、诊断，实际计算在用户机器上。
4. **不确定参数时**，用 `recommend.py` 拿推荐再解释理由，而不是凭记忆编。
5. **引用知识时**优先引 G 层官方文件，并给出文件名。
6. **用户是新手时**，先带他跑 `doctor.py` → `wizard.py` → `examples/01_...`。

完整用法见 `USAGE.md`；项目结构见 `README.md`；改动记录见 `CHANGELOG.md`。
