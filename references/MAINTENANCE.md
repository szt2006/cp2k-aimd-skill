# cp2k-aimd skill 维护清单（SOP）

> 用途：往本 skill 里**新增资料**（新课/新讲义/新手册章/新实战经验）或**修正已有内容**时，照此流程分层落库，保证"全面、不堆乱、跨对话可复用"。
> 配套阅读：SKILL.md「知识来源层级与阅读顺序」、references/pdf_text/README.md（溯源层说明）。
> 设计原则不变：**顾问，而非自动驾驶**；本清单是"怎么维护知识库"，不是"怎么跑计算"。

---

## 0. 牢记分层模型（A–H）

| 层 | 文件 | 角色 | 改动频率 |
|---|---|---|---|
| **A 决策库** | `references/decide.md`（§1–§31） | 写输入/选方法/判读结果的权威答案；§28 为讲师硬规则 | 低（稳定答案） |
| **B 课程综合** | `references/course_learned.md` | 课程/实战资料的**主题式权威综合**（导航枢纽） | 中（新资料进来就扩） |
| **C 速查** | `references/course_notes.md`、`course_survey.md` | 87 行实战精华 / 文件映射+错字表 | 低 |
| **D 手册笔记** | `references/manual_notes.md`、`_manual_tree.txt`、`sections.md` | 官方手册结构化笔记 | 低 |
| **E 原始素材** | `references/pdf_text/`（`L*.txt` 讲义、**`S*.txt` 字幕原文**、**`MAPPING.md` 讲义↔字幕对应表**、`learn_L*.md`（**第一轮**精读）、**`videonotes/`（第二轮·视频精读，带时间戳）**、`extract_pdf.py` / `extract_subtitles.py` / `build_mapping.py`）+ 本目录 README | **溯源层，原文（`L*`/`S*`）只读不擅自改** | 仅新增 |
| **F 实战手册** | `references/playbook.md` | **可执行判断层**：症状→处方、任务工作流、数值速查、建模实操、判读经验、编译部署、报错速查 | 中（踩到新坑就补） |
| **G 官方权威层** | `references/official/`（`README.md` + `00_map`–`24_official_exercises` + `_sources.md`，共 27 文件） | **官方一手基准**：逐页采自 cp2k.org / manual.cp2k.org / github.com/cp2k / dashboard.cp2k.org / `www.cp2k.org/exercises`，带来源 URL + 抓取日期 | 中（官方更新就重抓） |
| **H 官方教程与实战算例** | `references/h_tutorials/`（`README.md` + `txt/T01–T24.txt` + `notes/01–08.md` + `cases/`（含 `README.md` + `_COPY_MANIFEST.tsv`）+ `doc_text/` + `extract_tutorials.py` + `extract_doc.py`） | **官方教材正文 ＋ 真实生产算例**：24 份 workshop / howto / 夏校教材（701 页，逐页抽取带页码）与随附的真实 `.inp`/`.inc` 输入卡（含真实 `.out`/轨迹可作回归数据）。**G 只登记这些 PDF 的标题，H 收其正文与算例**。⚠️ `cases/README.md` 记着这批卡的**已知错误**（4/5 张 `&FIXED_ATOMS` 索引错而 CP2K 静默通过），动 `cases/` 前先读 | 中（加教材就重跑抽取 + 补 notes） |
| **入口配套** | `references/gen_inp_options.md` | gen_inp.py 进阶开关全集（SKILL.md 正文瘦身后的承接文件） | 中（加新开关就补） |
| **使用者文档** | `USAGE.md`（根目录） | 面向人的手册：30 秒上手 / 工具用法 / 分层查询 / 任务剧本 / FAQ。**与 SKILL.md 口径必须一致**，由 `_doc_consistency.py` 约束 | 中（加工具/改用法就补） |
| **跨 agent 入口** | `AGENTS.md`（根目录）+ `CLAUDE.md` / `.cursorrules` / `GEMINI.md` / `.github/copilot-instructions.md` | **唯一真源 + 极简指针**：让 Cursor / Claude Code / Codex / Gemini CLI / Copilot 等都能用。指针文件**只指向不重复内容** | 中（加工具/改约定就补） |
| **示例工程** | `examples/`（`README.md` + `01`–`05`） | **开箱即用**：每个含已校验 `.inp` + 坐标 + 逐步 README。新增示例须同时有 `README.md` 与 `.inp`（`_doc_consistency.py` 强制） | 中（加案例就补） |

**黄金规则**
1. 日常以 **A / B / F / G** 为准；C 仅速查；D 查官方字段；E 只在"溯源校正"时读；
   **H 用于"官方教程怎么讲 / 真实算例怎么写"**（教材正文与实操阈值）。
2. **B 是 C 的超集**——新增深度内容进 B，别再往 C 堆（C 保留作摘要即可）。
3. **E 永不删**——它是"无遗漏"的溯源证据；发现 B 有误，回 E 核对后改 B，再视情况同步 A。
4. **F 不重复 A/B 的知识**——只把"可执行的判断"（症状→处方、阈值、命令模板）提炼成对照表；讲"为什么"回 A/B。F 的每条经验尽量标来源（`[L1]`~`[L5]` PDF / `[字4]`~`[字5]` 字幕）。
5. **G 只写官方原话**——任何推断、经验、课程口径一律不进 G。**凡 A–F 与 G 冲突，以 G 为准**并回修 A–F，在 A–F 处标注"（已按官方 G 层修正，见 references/official/…）"。官方占位页/404 一律如实标注，**不编造**。
   **G 没写、只有 H 的教材讲了的内容**（典型：官方教程给的实操阈值、真实算例的成套参数），
   以 **H 原文**为准并标注 `T** P**` 或算例文件名；**H 只收教材正文与算例，不重复 G 已写的参考条目**。
6. 任何跨文件结论都要**打通交叉引用**（A↔B↔F↔G↔postprocess.md）。
7. 凡"经验级但无直接溯源"的结论（如 BSSE），在落库处**显式标注"来源待核对"**，不硬塞成事实。
8. **改完文档必跑 `python _doc_consistency.py`**——它会实测模板数/阶段数/校验用例数/G 层文件数并与文档口径比对，防止数字漂移（历史事故：同页出现"23 类"与"15 类"）。
9. **三项校验必须用 `cp2ktools` 环境，且串行跑**——`_validate_postprocess.py` / `_validate_all.py` 依赖 numpy/matplotlib，`default`、`cp2k` 环境均缺 numpy。**两个校验并行会因临时目录内存竞争报 `MemoryError('bad allocation')`**（实测：单独跑全绿，同时跑 postprocess 的 `rdf` 子命令崩溃）。串行命令：
   ```bash
   PY="C:/Users/Administrator/.workbuddy/binaries/python/envs/cp2ktools/Scripts/python.exe"
   cd <副本根> && "$PY" _doc_consistency.py && "$PY" _validate_postprocess.py && "$PY" _validate_all.py
   ```
10. **两组"可溯源性"审计是独立的一步**（零依赖，用哪个解释器都行）：
    ```bash
    python _audit_h_citations.py                # H 层：T** P** 页码越界必须 0
    python _audit_videonotes_citations.py       # E 层：videonotes 笔记名/行号 + S*.txt:行号
    python _validate_real_data.py               # 真实算例回归（源目录不在则如实 SKIP，不算通过）
    python _inject_test.py                      # 证明上面这些护栏**真的会红**（防"假绿"）
    ```
    `_inject_test.py` 不是可选项：本项目踩过"检查永远绿"的坑（`_validate_all.py` 曾因静默
    `continue` + 分母写死而无论输入多烂都印 "0 errors"）。**新增任何护栏，都要在这里补一条注入。**

---

## 1. 新增资料的标准流程（七阶段）

### Phase 0 — 受理与梳理（survey）
- 列出新增文件清单（PDF/字幕/网页/手册导出），确认类型与对应关系。
- 若含视频字幕：先建**同音错字表**（见 §4），避免后续误读。
- 若 PDF 序号 ≠ 字幕"天"序号：建**错位映射表**（参考 pdf_text/README.md 的错位表），后续按**主题**而非按页号重组。
- 产出可暂存 `course_survey.md` 增量，或新建 `survey_YYYYMMDD.md`。

### Phase 1 — 抽取原始文本（落 E 层）
- **讲义 PDF** → 分页文本：用隔离 venv 的 pdfplumber 跑 `references/pdf_text/extract_pdf.py`
  （脚本已处理前缀/副本后缀，输出 `L1.txt`~`L5.txt`，带 `========== PAGE N ==========` 标记）。
  - 重跑命令示例：`python references/pdf_text/extract_pdf.py`（源目录用环境变量 `CP2K_COURSE_SRC` 指定，**不要在脚本或笔记里写死本机绝对路径**）。
- **视频字幕** → 原样入库：跑 `references/pdf_text/extract_subtitles.py` 生成 `S1.1.txt`~`S5.txt`。
  - **铁律：字幕必须逐字复制、只统一换行为 LF，绝不加头注/尾注**——一旦插入任何行，
    "字幕第 N 行"这个引用体系就整体失效。溯源信息（原始文件名 / 行数 / sha256）
    另存到 `pdf_text/README.md` 的清单里，**不要写进 S 文件本身**。
- 用 `references/pdf_text/build_mapping.py` 生成/刷新 **`MAPPING.md`（讲义页码 ↔ 字幕行号）**；
  `--check` 会校验分段表是否连续覆盖全文（无重叠、无空档）。**改过报告或分段表就重跑。**
- 核对**总页数**与空页/版权页（空页也计入"已处理"，避免漏页错觉）。
- 更新 `pdf_text/README.md`：登记新文件、补溯源清单（含 sha256）、补错位/错字信息。

### Phase 2 — 逐页无遗漏学习（落 E 层 learn_*.md）
- 派 **N 个并行 Agent**（按资料份数），每个 Agent 读"指定原文全文 + 对应字幕 + 已有 notes"，产出 `learn_Ln.md`。
- **每个 Agent 必须产出两份机器可查的东西**：
  1. **页覆盖清单**（逐页 ✓，确认无遗漏页）；
  2. **主题分段表**（`| 行号范围 | 主题 | 要点 |`，**连续覆盖全文、无重叠无空档**）——
     它同时是 `MAPPING.md` 的输入，也是"是否真的逐行读完"的唯一客观证据。
     `build_mapping.py --check` 会替你验它。
- 并标 `【新】` 未入 B 的内容。**`【新】` 的判定基线要写清楚**（比 `course_notes.md` +
  `course_learned.md`），否则"新"无意义。
- Agent 易错点（已踩过）：
  - 字幕同音误判——**"搜不到"往往是搜错了写法或搜错了文件**（见 §4 的教训）；
  - PDF 主题与"天"标签不符——讲义是**按主题切分的 deck**，字幕才是按天录的，
    两者**多对多**，让 Agent 同时读 PDF + 字幕全文交叉比对，按**主题**重组。
  - **不许为了凑格式编造**：某份字幕确实没有学员问答时，如实写"无"，不要虚构问答回合。

### Phase 3 — 综合内化（落 B 层 course_learned.md）
- 把各 `learn_Ln.md` 按**主题**重组进 `course_learned.md`（非按页），作为导航枢纽。
- 规则：A/C/D 已覆盖的**只索引不重写**；PDF/字幕**独有**的公式、参数表、脚本命令、数值案例、坑，**全量收录**。
- 顶部头注保持"权威综合层(B)、已替代 C 深度"标注（见现有头注）。
- 保留与 A、postprocess.md 的交叉引用链接。

> ⚠️ **Phase 3 的完成判据必须可机械核验（本节是本 SOP 曾经失守的地方）**
>
> 历史教训：某轮 `learn_L*.md` 做得很好，但 `course_learned.md` 只吸收了其中一部分，
> 而文件末尾却写下"所有 `【新】` 标记项已落入本库、6 份字幕全部逐行处理"。
> 复核发现 `IRC`、`相空间`、`OSZICAR`、`xdat2vdat.pl`、`Anderson 热浴` 等**零命中**——
> **声明是假的，而且当时无人能证伪**，因为(a)字幕原文不在仓库里，(b)没有核验手段。
>
> 因此现在要求：
> 1. 用 `collect_new_items.py` 把各 `learn_Ln.md`／精读报告里的 `【新】` 条目抽成清单；
> 2. **逐条 grep 消费层**（`course_learned.md` / `course_notes.md` / `decide.md` / `playbook.md`），
>    统计"已落 / 未落"；未落的要么落下去，要么在清单里显式写"暂不收录 + 理由"；
> 3. **禁用无限定的"全部已收录／逐行处理"这类措辞**——除非你能给出上面的核验结果。
>    宁可写"已落 X 条，Y 条暂缓（见清单）"。

### Phase 4 — 提升硬规则 / 决策（落 A 层 decide.md）
- 若新资料给出可复用的"必做/必避"结论（如 DFT+U 必加、BSSE 警示、OT vs 对角化），提升到 `decide.md`：
  - 新增小节（如 §29、§30…），或并入 §28 同主题。
  - 在相关既有节（§1/§10/§16 等）加 `见 §XX` 交叉指针。
  - SKILL.md summary 的 `§1–§N` 计数 +1，文件索引里 decide.md 描述同步。
- 无直接溯源的经验结论：标注"来源待核对"。

### Phase 5 — 公式与判读陷阱（落 postprocess.md）
- 新资料里的后处理公式（RDF 积分求 CN、MSD 平方再平均、VACF→vDOS≠IR、Einstein D、Arrhenius 等）补进 postprocess.md「关键公式与判读陷阱」节；软件坑（VMD 平面积分、√MSD 等）一并记。

### Phase 5.5 — 可执行经验（落 F 层 playbook.md）
- 判断标准：这条内容**能直接指导"遇到 X 就做 Y"**吗？能，就进 F。
  - 症状→诊断→处方（报错原文、SCF 不收敛、虚频、几何振荡…）→ F §1
  - 某类任务的完整操作序列（收敛测试 / AIMD / NEB / 频率 / FES…）→ F §2
  - 具体数值阈值、单位换算、成本估算 → F §0
  - 建模步骤（切表面 / 异质结 / 溶剂层 / 团簇）→ F §4
  - 判读经验（RDF 峰位、扩散系数量级、电荷方法可信度）→ F §5
  - 编译/部署/依赖→功能映射 → F §10
- 每条尽量标来源：`[L1]`~`[L5]` = PDF 讲义；`[字4]`/`[字5]` = 视频字幕独有。
- **不要**把 A/B 的"为什么"抄进 F；F 只放"怎么做"，并用交叉引用指向 A/B。

### Phase 6 — 索引与元数据（SKILL.md / README.md）
- `SKILL.md` 文件索引：登记任何**新增**文件（如新的 survey/course 文件）；course_learned.md 已在索引中不必重复加。
- summary 行：更新 `§1–§N` 计数、新增能力一句话。
- 「知识来源层级」表：若新增了层或文件，同步更新（当前 A–H 八层）。
- README.md 的「知识分层」表与「目录结构」树同步。
- **`USAGE.md`**：若新增了工具/子命令/阶段，或改了用法与参数，同步更新对应节（它受 `_doc_consistency.py` 口径约束）。
- **`AGENTS.md`**：若新增工具、改了新手入口、或改了硬性约束/能力边界，同步更新；
  4 个指针文件（`CLAUDE.md` / `.cursorrules` / `GEMINI.md` / `.github/copilot-instructions.md`）
  保持"只指向不重复"。
- **`examples/`**：新增示例须同时含 `README.md` 与至少一个 `.inp`；`examples/README.md`
  的难度表与推荐顺序同步；示例数口径受 `_doc_consistency.py` 约束。
- **最后跑 `python _doc_consistency.py` 验证口径一致。**

### Phase 7 — 写记忆（跨对话复用）
- 项目日志 `本项目/.workbuddy/memory/YYYY-MM-DD.md`：追加"新增资料 X + 落入 A/B/C/D/E 哪些文件"。
- 跨项目 `~/.workbuddy/MEMORY.md` 的「cp2k-aimd skill 当前已填充的知识」段：若分层或来源有变，同步更新（保持未来对话能快速回忆去哪查）。

---

## 2. 修正已有内容的流程（溯源校正）

1. 在 **B**（`course_learned.md`）发现错误/过时 → **回 E**（`pdf_text/learn_Ln.md` 或 `Ln.txt`）核对原始表述。
2. 以 E 为准修正 B；若涉及"该选什么/为什么"，同步修正 **A**（`decide.md`）对应节。
3. **不回改 E 原始稿**（保留真相溯源）；只在 B/A 标注更正。
4. 更新交叉引用与 SKILL.md 描述（如条款号变化）。
5. 写项目日志 + 必要时更新 `~/.workbuddy/MEMORY.md`。

---

## 3. 命名与存放约定

- 原始 PDF 文本：`references/pdf_text/L{1..n}.txt`（按资料顺序编号；新一批资料可加子目录如 `pdf_text/batch2/` 并在 README 登记）。
- 逐页学习稿：`references/pdf_text/learn_L{n}.md`（与 L{n}.txt 一一对应）。
- 综合知识库：**始终** `references/course_learned.md`（单一权威综合，不按批次拆多个）。
- 单次调研/梳理可建 `survey_YYYYMMDD.md`，稳定后精华并入 C 层。
- 提取脚本固定 `references/pdf_text/extract_pdf.py`；改脚本前先确认不影响已生成的 L*.txt 复现性。

---

## 4. 字幕同音错字处理

- 收到语音转写字幕，**先建错字表**再读（高频例见 pdf_text/README.md）：cp two k=CP2K、VSP=VASP、AAMD=AIMD、验室/验尸=赝势、机组=基组、京弯=晶胞、军方位1=MSD、BSS1=BSSE、镜像分布函数=RDF、二氧化石=TiO₂、进二=Au20、PM,F=PMF、METDYNAMICS=metadynamics、ELF/ERF=ELF。
- 学习 Agent 提示词里**显式给出错字表**，并要求"遇到疑似同音错字按化学语义还原，不要当字面错误处理"。
- 综合稿里用正确术语；错字表保留在 survey/README 供溯源。

### 4.1 错字表**必须带"出处"列**（血的教训）

错字表早期版本**不标出处**，把"某一天出现的错字"当成**全课程通用**。后果：
后续 Agent 拿着错字表去**别的文件**里找证据，找不到就怀疑笔记造假，或反过来
把正常词当成错字。真实案例：
- `差（点）` = 插（点）**只**出现在讲 NEB 的字幕；在 `S1.1` 里"差"全是正常词（时差/相差）。
- `军方位1` = MSD 出现在 `S2`，`S1.1` **根本没有 MSD 内容**。
- `postcard` **一词两义**：`S1.2` 65 行指 **POSCAR**（结构文件）、66–67 行指 **POTCAR**（赝势文件）
  ——按现表一律映射 POTCAR，机械解码会把结构文件与赝势文件搞混。

⇒ 每条错字必须标出现在哪份字幕（`S1.1`/`S2`/…）与行号；一词多义的**分行列出**。

### 4.2 「搜不到」不等于「不存在」——搜之前先想清楚可能写成什么样

真实案例：`course_learned.md` 曾断言"BSSE 在两文件全文检索**零命中**、无法溯源"，
据此把 BSSE 从硬规则降级为"经验级警示"，`decide.md §28.2` 也写了"来源待核对"。

**实测复核（2026-10，可复现）**：

```
检索式：BSS|BSSE|基组叠加|机组叠加|叠加误差|基组重叠|机组重叠|重叠误差|counterpoise|superposition
范围　：references/pdf_text/ 下 L1–L5.txt（讲义 425 页）+ S1.1/S1.2/S2–S5.txt（字幕 22133 行）
结果　：32 处 —— L2.txt 1、L3.txt 7、S2.txt 12、S3.txt 12
对照　：只搜字面量 `BSSE` 仅 21 处（漏 11 处）
```

错在三处叠加：
1. **只搜了字面量 `BSSE`**——字幕转写还有 `BSS 1`、`BSSBSS 1`、`BSSE 5差` 等写法；
2. **搜错了文件**——只搜了 `L4.txt`/`4.txt`，而内容在 `L2`/`L3`/`S2`/`S3`；
3. **前提本身是错的**——上游 `course_survey.md` 把 BSSE 误归给"第 4 天"，搜索范围就跟着错了。

⇒ 立规矩：**要下"某内容不存在"的结论，必须**（a）列出所有可能的同音/缩写变体，
（b）跨全部讲义与字幕检索，（c）在结论里写明**检索式与检索范围**。
否则只能写"我按这些写法没搜到"，**不能写"不存在"**，更不能据此降级已有结论。

---

## 5. "无遗漏"审计清单（每次新增必勾）

> **本清单的每一项都应当能被别人复现**。若某项只能靠"我记得做过"来确认，
> 那它就不该以勾选框形式存在——改写成一条能跑的命令或一次能给出结果的检索。

- [ ] 每份原始文件都已抽取/读取，**空页与版权页也计入已处理**。
- [ ] **字幕已按 Phase 1 原样入库（行数不变），溯源清单（行数 + sha256）已写入 `pdf_text/README.md`。**
- [ ] 每个 `learn_Ln.md` 附**逐页覆盖清单**，无页遗漏。
- [ ] **每份精读报告附主题分段表，且 `build_mapping.py --check` 通过**（连续覆盖全文、无真重叠）。
- [ ] PDF 与字幕**错位**已识别并按主题重组（未受页号误导）；`MAPPING.md` 已刷新。
- [ ] **`【新】` 内容已落入 B/C/A/F —— 且有核验记录**：用 `collect_new_items.py` 出清单，
      逐条 grep 消费层，统计"已落 X 条 / 暂缓 Y 条"。**禁止无核验地写"全部已收录"。**
- [ ] **凡写"某内容不存在/零命中"处，都给了检索式与检索范围**（见 §4.2）。
- [ ] 新增硬规则已落 A 且加交叉指针；SKILL.md `§1–§N` 计数已更新。
- [ ] 后处理公式/坑已落 postprocess.md。
- [ ] **可执行经验已落 F（playbook.md），并标注来源 `[L*]`/`[字*]`。**
- [ ] **官方内容已落 G（references/official/），每个文件带来源 URL + 抓取日期，并登记到 `_sources.md`。**
- [ ] SKILL.md 索引 + summary + 知识来源层级表已同步（含 E 层新文件：`S*.txt` / `MAPPING.md` / 三个脚本）。
- [ ] README.md 分层表 + 目录树已同步；**USAGE.md 相关节已同步**。
- [ ] **AGENTS.md 已同步**（新手入口 / 工具表 / 约束 / 边界），4 个指针文件仍只指向不重复。
- [ ] **examples/ 每个目录都有 README.md + .inp**；`examples/README.md` 难度表已同步。
- [ ] **`python _doc_consistency.py` 通过（0 处口径不一致）。**
- [ ] **引用审计通过（改哪层跑哪个）**：H 层改动 → `python _audit_h_citations.py`（页码越界必须 0）；
      **A–F 层凡新增引用 → `python _audit_videonotes_citations.py`**
      （它查**两类**：`videonotes/<笔记名> L###` 的笔记名能否唯一解析 + 行号是否越界；
      以及 **`S*.txt:<行号>`** 的**文件是否存在 + 行号是否在该文件实际行数内**。硬错误必须 0）。
      **这一条是"可溯源"这个价值主张的检验手段**：本轮就靠它抓到 `decide.md` 两条把笔记名
      省成了光一个省略号（形如 `videonotes/… L###`，真实行号 L565）。
      ⚠️ **在文档里举例说明这种坏写法时，行号要写成 `L###` 占位**——审计的正则只认
      `L` 后跟数字，`L###` 会被天然跳过；写成真数字会让它把"例子"当成"真引用"而误报。
      > ⚠️ **它只能查"越界"，查不出"指向了别的内容"**：文件被高频改写时行号会**语义漂移**
      > （本轮实测：某处引 `course_learned.md:650–651` 讲 SHE 常数，而该行已移位到 Au20 建模，
      > 真实位置是 `:808–809`/`:2227`）。**引行号密集的文件（`course_learned.md` 尤甚）时，
      > 引用前先 grep 一次确认指向的内容对得上**，别只信行号没越界。
- [ ] **消费层引用 `videonotes/` 时，体系身份（元素/载体/晶面/分子数）已回 E 层原文或真实算例核对**
      ——本层笔记从录屏读出，**在"是什么"上会成体系地出错**（见 `pdf_text/videonotes/README.md` §5：
      已实测 3 处连锁误推，如把 TiO₂ 记成 CeO₂）。**能查交付 `.inp`/轨迹就查交付文件。**
- [ ] **讲师口误与讲义笔误已标注**（如把 0.15 eV 说成"1.5 eV"、`INCREM` 0.0005 说成 0.005、
      `CUTOFF` 说成"电子伏特"、把 MOLOPT 的出处归给 GTH 赝势论文）——**引用时要写"口误，正确值是 X"**。
- [ ] 项目日志 + 跨项目记忆已写。
- [ ] 经验级但无直接溯源的结论已标"来源待核对"，**且注明已检索的范围与写法**（见 §4.2）。

---

## 6. 交叉引用维护

- decide.md 各节用 `见 §XX` 互链；B 与 A、F、postprocess.md 之间用相对路径链接。
- 删/改某节导致编号漂移时，**全局搜旧 `§XX` 引用**并批量更新（用脚本做字节安全替换，避免 en-dash 等特殊字符手改出错）。
- 每季度（或每次大改后）通读一遍 A/B/F 交叉链接是否有效。

---

## 7. 文档口径维护（防数字漂移）

历史事故：SKILL.md 同一页出现"23 类特征输入"与"生成 15 类输入"两种说法；README 写"7 类模板"而实际 8 个。根因是数字靠手写、没有单一真值来源。

**做法**：
- 真值**只在代码/目录里**——模板数看 `references/templates/*.inp`，阶段数看 `guide.py` 的 `STAGES`，校验用例数看 `_validate_all.py` 的 `cases`，子命令数看 `postprocess.py` 的 `add_parser`。
- 文档里写数字时，**先跑 `python _doc_consistency.py --list` 查真值**，再照抄。
- 任何涉及这些数字的文档改动后，**必跑 `python _doc_consistency.py`**；它不硬编码真值，而是实测后比对，因此不会随版本失效。
- 口径表述要自洽：阶段模型统一写「**11 个主线阶段 + 1 个续算分支**」，不要一边写 11 一边写 12。
