# cp2k-aimd — CP2K 计算顾问 Skill

一个面向 **CP2K（AIMD / 几何优化 / NEB 过渡态 / 元动力学 / 振动分析 / 电子结构后处理）** 的 WorkBuddy skill。
定位是**「会思考的副驾 / 全过程参谋」，不是自动驾驶**：它在每个阶段告诉你该考虑什么、各选项的取舍、该盯哪些指标、常见坑在哪，并给出可执行的命令——最终怎么选、跑不跑，由你决定。

## 它能帮你做什么

- **① 问诊**：描述体系（元素 / 周期 / 电荷 / 自旋 / 目标）→ 推理泛函·基组·赝势·色散·k 点·SMEAR·CUTOFF，并给"从 0 到收敛"的起步阶梯。
- **② 生成**：按你的选择产出 `.inp`（多元素 / ADMM / Meta-GGA / Properties / 恒温器 / NEB / 元动力学 / QM-MM 等进阶开关）。
- **③ 解读**：校验 `.inp` 语法、解析 `.out` 取能量/受力/收敛、诊断 SCF/几何/虚频并建议改哪一行。
- **④ 后处理**：从轨迹算 RDF / MSD / 扩散 / VACF / IR / PDOS / Bader / 自由能面并出图。
- **⑤ 导航**：11 个主线阶段的项目向导（+ 1 个续算分支）；`guide.py scan` 读你目录推断卡在哪、下一步做什么。
- **⑥ 急救**：`references/playbook.md` 的**症状→处方**对照表——SCF 不收敛、几何振荡、报错原文、后处理算错、数值该取多少，都能直接查到"下一步改什么"。
- **⑦ 溯源**：`references/official/` 的**官方权威层**——需要"官方默认值是多少""官方推荐什么""这个报错官方怎么说""这个功能哪个版本才有"时，直接查逐页采自 cp2k.org / manual.cp2k.org 的原文，带 URL 可核对。

## 安装到 WorkBuddy

```bash
# 放到用户级 skill 目录（所有对话/项目自动加载）
cp -r cp2k-aimd ~/.workbuddy/skills/
```

或在 WorkBuddy 的 skill 管理里「导入本地目录」指向本仓库。

## 跨 agent 使用（不限 WorkBuddy）

本 skill 是**纯文本 + 零依赖脚本**，任何能读文件、能跑命令的 AI 助手都能用：

| 助手 | 读取的入口 |
|---|---|
| Claude Code | `CLAUDE.md` → 指向 `AGENTS.md` |
| Cursor | `.cursorrules` → 指向 `AGENTS.md` |
| Codex / Aider / Zed / 其它 | `AGENTS.md`（事实标准） |
| Gemini CLI | `GEMINI.md` → 指向 `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md` → 指向 `AGENTS.md` |

**`AGENTS.md` 是唯一真源**，其余文件只是极简指针，不重复内容（避免多份说明漂移）。

> **第一次用？先读 [`USAGE.md`](USAGE.md)** —— 面向使用者的完整说明：
> 30 秒上手、十个工具怎么用、八层知识什么时候查哪一层、六类典型任务剧本、常见问题。
> 本文件（README）讲**定位与结构**，`USAGE.md` 讲**怎么用**，`CHANGELOG.md` 讲**改过什么**。
>
> **完全新手？** 三步走：
> ```bash
> python scripts/doctor.py    # 1. 环境自检
> python scripts/wizard.py    # 2. 问答式生成第一个输入
> # 3. 打开 examples/01_si_bulk_static/ 照着跑一遍
> ```

## 知识分层（A–H）

| 层 | 文件 | 角色 |
|---|---|---|
| **A 决策库** | `references/decide.md`（§1–§31） | 写输入 / 选方法 / 判读结果的权威答案；§28 庚子讲师实操硬规则、§29 AIMD 统计与可复现性、§30 建模硬规则、§31 方法选择清单 |
| **B 课程综合** | `references/course_learned.md` | 庚子计算 5 天课程（425 页 PDF + 6 字幕）逐页无遗漏内化，主题式导航枢纽 |
| **C 速查** | `references/course_notes.md`、`course_survey.md` | 实战精华速查 / 文件映射 + 同音错字表 |
| **D 手册笔记** | `references/manual_notes.md`、`_manual_tree.txt`、`sections.md` | 官方手册结构化笔记 |
| **E 原始素材** | `references/pdf_text/`（`L1–5.txt` 讲义 425 页、`S1.1–S5.txt` **字幕原文 22133 行**、`MAPPING.md` 讲义↔字幕对应表、`learn_L1–5.md`、`videonotes/`（**视频精读·第二轮 6 份 / 9803 行，带时间戳**）、3 个抽取/生成脚本） | 溯源层，**原文只读不擅自改** |
| **F 实战手册** | `references/playbook.md` | 症状→处方、任务工作流、数值速查表（"遇到 X 怎么办"） |
| **G 官方权威层** | `references/official/`（27 文件） | **CP2K 官网 + 官方手册 + GitHub + Dashboard + 官方练习集逐页采集**（带 URL + 抓取日期，累计 393 条目）：权威性 L0–L3 分级、`&GLOBAL`/`RUN_TYPE`/单位、输入语法与 printkey、**Input Reference 完整段树**、基组与 GTH 赝势、GPW·OT·k 点·CDFT·DFT+U、**CNEO·GauXC·泊松求解器·RI-HFX**、SCF 与 CUTOFF 收敛、MD 系综与平衡、几何·晶胞优化、约束 MD·蓝月系综、NEB·NEWTON-X、光学谱 TDDFT·GW-BSE·RT-TDDFT·RTBSE·STM、**X 射线谱四路线**、QM/MM·嵌入·ML 势（含 NequIP·MACE·NNP·PAO-ML·ACE·Kim-Gordon·DLA-Future）、后 HF·**BSSE 官方出处**·xTB、重启续算、故障排查+FAQ 19 条、安装与 30 个外部库、benchmark·GPU·Spack·参与开发、版本时间线与不兼容变更、**官方练习集 248 子页（NEB·AIMD·系综·SGCP·i-PI·EOS·PDOS·能带·功函数）** |

| **H 官方教程与实战算例** | `references/h_tutorials/`（`README.md` 层定位、`txt/T01–T24.txt` **24 份官方教材 701 页**、`notes/01–08.md` 精读笔记、`cases/` **真实算例输入卡**、`extract_tutorials.py`） | **官方 workshop / howto / 夏季学校教材**（Hutter 的 GPW 与 AIMD、Watkins 的杂化泛函与 ADMM、Mueller 的自动化/脚本化/测试与性能判读（文件名里的 Parallelization 有误导，见 `h_tutorials/README.md` §3）、Iannuzzi 的 Zurich 教程、三个 `howto_*`、2016/2018/2020 夏校练习、基组赝势、QM/MM 三份、使用入门）＋ **真实生产算例**（Cu(100)-水 opt/AIMD、Au(111)-水、Au(111)-水-6Na、TiO₂-Au₂₀，含可运行 `.inp` 与**真实 `.out`/轨迹**）。**G 层只登记这些 PDF 的标题，未收录教材正文** |

> 日常以 **A / B / F / G** 为准；**凡 A–F 与 G 冲突，以 G 为准**（G 是唯一可回溯到官方原文的层）。
> **G 层没写而只有教材讲了的内容**（如官方教程给的实操阈值），以 **H 层教材原文**为准并标注出处。
> 新增 / 修正资料的标准流程见 `references/MAINTENANCE.md`（含「无遗漏」审计清单）。

## 目录结构

```
cp2k-aimd/
├── AGENTS.md                # **跨 agent 唯一真源入口**（Claude/Cursor/Codex/Gemini/Copilot 通用）
├── CLAUDE.md / .cursorrules / GEMINI.md   # 极简指针 → AGENTS.md
├── .github/copilot-instructions.md        # 极简指针 → AGENTS.md
├── SKILL.md                 # WorkBuddy 入口（name/description/read_when 触发词）
├── USAGE.md                 # **使用说明**（30 秒上手 / 工具用法 / 分层查询 / 任务剧本 / FAQ）
├── README.md                # 本文件（定位与结构）
├── LICENSE                  # MIT（含第三方课程素材例外声明）
├── CHANGELOG.md             # 版本变更
├── CONTRIBUTING.md          # 贡献指南（含三项校验要求）
├── requirements.txt         # 运行依赖（numpy / matplotlib）
├── requirements-dev.txt     # 开发依赖（cp2k-input-tools / pint / lxml / pdfplumber）
├── scripts/                 # doctor / wizard / guide / recommend / gen_inp / validate_inp / parse_output / diagnose / postprocess
│                            #   + _console.py（控制台编码兼容层，中文 Windows 必需，非 CLI）
├── examples/                # **5 个开箱即用示例工程**（01–05，含已校验 .inp + 逐步 README）
├── verify_out/              # 7 个已通过官方解析器校验的示例 .inp
├── _validate_all.py         # 权威校验 harness（29 类特征输入）
├── _official_validate.py    # 单文件官方解析器校验
├── _validate_postprocess.py # 后处理端到端校验（合成数据）
├── _validate_postprocess_analytic.py # 后处理**解析解**自测（72 条断言，每条配反向对照）
├── _doc_consistency.py      # 文档口径一致性自检
├── _collect_new_items.py    # 抽【新】条目 + 核对是否落进消费层（维护用，见 MAINTENANCE.md Phase 3）
├── _kw_probe.py             # 直查官方 cp2k_input.xml 的关键字默认值/单位（维护用，需 cp2k-input-tools）
├── _audit_h_citations.py    # H 层引用审计：笔记的 T** P** 页码能否回 txt/ 对上（零依赖）
├── _audit_videonotes_citations.py # E 层引用审计：videonotes 笔记名/行号 + S*.txt:行号 是否越界
├── _validate_rdf_cn.py      # RDF 归一化验证：配位数 = 直接计数（多帧；单帧抓不到重复归一化）
├── _verify_case_provenance.py # cases/ 溯源核验：清单 sha256 vs 副本与源文件重算
├── _validate_real_data.py   # 真实数据回归：真实 .out/轨迹当锚点（源目录不可用时如实 SKIP）
├── _validate_gbk.py         # GBK 控制台回归：强制 GBK 编码跑 70 个用例，抓"忘挂 _console"
├── _inject_test.py          # 注入测试：故意造错证明各护栏会红（防"假绿"）
├── _gen_cp2k_sections.py    # 生成 scripts/_cp2k_sections.py（1342 个官方段名，需 cp2k-input-tools）
└── references/              # decide / course_learned / course_notes / course_survey / manual_notes
    ├── gen_inp_options.md   # gen_inp.py 进阶开关全集（10 节 + 快速定位表）
    ├── playbook.md          # F 层：实战手册（症状处方 / 任务工作流 / 数值速查）
    ├── workflow.md          # 11 主线阶段完整指引
    ├── MAINTENANCE.md       # 维护 SOP（A–G 分层模型）
    ├── pdf_text/            # 原始素材（E 层）：L1–5.txt 讲义 + S1.1–S5.txt 字幕 + MAPPING.md 对应表
│   └── videonotes/      #   课程视频精读笔记（第二轮 6 份，带视频时间戳）
    │                        #   + learn_L1–5.md 学习稿 + extract_pdf/extract_subtitles/build_mapping 三个脚本
    ├── h_tutorials/         # H 层：官方教程与实战算例（24 份官方教材 701 页 + 真实算例输入卡）
    ├── official/            # G 层：官方权威层（27 文件，带 URL + 抓取日期）
    │   ├── README.md        #    层定位、边界、[默认]/[官方推荐]/[示例] 标注规则
    │   ├── 00_map.md        #    官网+手册内容地图 / HowTo / exercises / 学习路径
    │   ├── 01_global_and_units.md      # &GLOBAL 38 关键字 + RUN_TYPE 29 值 + 单位表
    │   ├── 02_dft_methods.md           # GPW/GAPW·赝势·OT·k 点·CDFT·DFT+U·色散
    │   ├── 03_scf_convergence.md       # SCF 收敛 + CUTOFF 收敛（250/60 推荐）
    │   ├── 04_sampling_md.md           # MD 系综·温控·平衡协议·验证清单
    │   ├── 05_optimization.md          # GEO_OPT/CELL_OPT·优化器·收敛判据
    │   ├── 06_properties.md            # 性质计算索引 + 官方缺口清单
    │   ├── 07_restarting.md            # 波函数/k 点/Harris/NEB/MD/CDFT 重启
    │   ├── 08_errors_and_faq.md        # 故障排查 8 类 + FAQ 19 条
    │   ├── 09_build_libraries.md       # 安装 + 30 个外部库 + 加速器
    │   ├── 10_features_resources.md    # 功能全清单 + 缩写表 + 引用 + 资源
    │   ├── 11_version_changelog.md     # 版本时间线 + 不兼容变更
    │   ├── 12_authority_sources.md     # 权威性 L0–L3 分级 + 官方渠道核实方法
    │   ├── 13_input_syntax_and_print.md# 输入语法 8 规则 + printkey 迭代层级
    │   ├── 14_basis_and_potentials.md  # BASIS_SET 格式 + GTH 赝势 qN 清单
    │   ├── 15_optical_and_xray.md      # TDDFT·GW-BSE·RT-TDDFT·STM
    │   ├── 16_qmmm_embedding_ml.md     # QM/MM·镜像电荷·嵌入·ML 势
    │   ├── 17_constrained_dynamics_and_paths.md  # 约束 MD·蓝月系综·NEWTON-X
    │   ├── 18_posthf_semiempirical_and_xray.md   # 后 HF·BSSE 官方出处·xTB·RTBSE
    │   ├── 19_performance_gpu_community.md       # benchmark·GPU·Spack·参与开发
    │   ├── 20_input_reference_tree.md            # Input Reference 段树 14/76/269/359/750
    │   ├── 21_xray_spectroscopy_full.md          # ΔSCF·XAS_TDP·δ-kick·GW2X 四路线
    │   ├── 22_ml_embedding_dlaf.md               # NequIP·MACE·NNP·PAO-ML·ACE·KG·DLAF
    │   ├── 23_dft_subpages_full.md               # CNEO·GauXC·泊松求解器·RI-HFX
    │   ├── 24_official_exercises.md              # 官方练习集 248 子页（NEB·AIMD·系综·SGCP·i-PI）
    │   └── _sources.md                 # 溯源清单（393 个条目 / 完整度 / 缺口）
    └── templates/           # 8 类 .inp 模板（static/geo_opt/cell_opt/aimd_md/metadyn/neb/vib/qmmm）
```

## 自检

改完任何内容，跑这三条（CI 也会自动跑）：

```bash
python _doc_consistency.py        # 文档口径一致性（零依赖）
python _validate_postprocess.py   # 后处理端到端校验（需 numpy + matplotlib）
python _validate_all.py           # 输入权威校验（需 requirements-dev.txt）
```

## credits

- 决策库与输入结构对照 **CP2K 官方手册**（manual.cp2k.org）与本地 `cp2k_input.xml` 校验。

## 许可

代码与原创文档采用 **MIT 许可**（见 `LICENSE`）。
`references/pdf_text/` 下的课程 PDF 抽取文本与字幕整理稿**版权归原作者所有**，
不在 MIT 范围内，仅作学习与溯源用途。
