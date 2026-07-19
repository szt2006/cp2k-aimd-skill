# cp2k-aimd skill 维护清单（SOP）

> 用途：往本 skill 里**新增资料**（新课/新讲义/新手册章/新实战经验）或**修正已有内容**时，照此流程分层落库，保证"全面、不堆乱、跨对话可复用"。
> 配套阅读：SKILL.md「知识来源层级与阅读顺序」、references/pdf_text/README.md（溯源层说明）。
> 设计原则不变：**顾问，而非自动驾驶**；本清单是"怎么维护知识库"，不是"怎么跑计算"。

---

## 0. 牢记分层模型（A–E）

| 层 | 文件 | 角色 | 改动频率 |
|---|---|---|---|
| **A 决策库** | `references/decide.md`（§1–§28） | 写输入/选方法/判读结果的权威答案；§28 为讲师硬规则 | 低（稳定答案） |
| **B 课程综合** | `references/course_learned.md` | 课程/实战资料的**主题式权威综合**（导航枢纽） | 中（新资料进来就扩） |
| **C 速查** | `references/course_notes.md`、`course_survey.md` | 87 行实战精华 / 文件映射+错字表 | 低 |
| **D 手册笔记** | `references/manual_notes.md`、`_manual_tree.txt`、`sections.md` | 官方手册结构化笔记 | 低 |
| **E 原始素材** | `references/pdf_text/`（L*.txt、learn_L*.md、extract_pdf.py）+ 本目录 README | **溯源层，只读不擅自改** | 仅新增 |

**黄金规则**
1. 日常以 **A / B** 为准；C 仅速查；D 查官方字段；E 只在"溯源校正"时读。
2. **B 是 C 的超集**——新增深度内容进 B，别再往 C 堆（C 保留作摘要即可）。
3. **E 永不删**——它是"无遗漏"的溯源证据；发现 B 有误，回 E 核对后改 B，再视情况同步 A。
4. 任何跨文件结论都要**打通交叉引用**（A↔B↔postprocess.md）。
5. 凡"经验级但无直接溯源"的结论（如 BSSE），在落库处**显式标注"来源待核对"**，不硬塞成事实。

---

## 1. 新增资料的标准流程（七阶段）

### Phase 0 — 受理与梳理（survey）
- 列出新增文件清单（PDF/字幕/网页/手册导出），确认类型与对应关系。
- 若含视频字幕：先建**同音错字表**（见 §4），避免后续误读。
- 若 PDF 序号 ≠ 字幕"天"序号：建**错位映射表**（参考 pdf_text/README.md 的错位表），后续按**主题**而非按页号重组。
- 产出可暂存 `course_survey.md` 增量，或新建 `survey_YYYYMMDD.md`。

### Phase 1 — 抽取原始文本（落 E 层）
- PDF → 分页文本：用隔离 venv 的 pdfplumber 跑 `references/pdf_text/extract_pdf.py`（脚本已处理前缀/副本后缀，输出 `L1.txt`~`L5.txt`，带 `========== PAGE N ==========` 标记）。
  - 重跑命令示例：
    用装了 pdfplumber 的 Python 运行（无需固定路径）：`python references/pdf_text/extract_pdf.py`
- 核对**总页数**与空页/版权页（空页也计入"已处理"，避免漏页错觉）。
- 更新 `pdf_text/README.md`：把新文件登记进"文件清单"表，并补错位/错字信息。

### Phase 2 — 逐页无遗漏学习（落 E 层 learn_*.md）
- 派 **N 个并行 Agent**（按资料份数），每个 Agent 读"指定原文全文 + 对应字幕 + 已有 notes"，产出 `learn_Ln.md`。
- **每个 Agent 必须产出"页覆盖清单"**（逐页 ✓），确保无遗漏；并标 `【新】` 未入 B 的内容。
- Agent 易错点（已踩过）：字幕同音误判（如把 BSSE 当不存在）、PDF 主题与"天"标签不符——让 Agent 同时读 PDF+字幕全文交叉比对，按**主题**重组。

### Phase 3 — 综合内化（落 B 层 course_learned.md）
- 把各 `learn_Ln.md` 按**主题**重组进 `course_learned.md`（非按页），作为导航枢纽。
- 规则：A/C/D 已覆盖的**只索引不重写**；PDF/字幕**独有**的公式、参数表、脚本命令、数值案例、坑，**全量收录**。
- 顶部头注保持"权威综合层(B)、已替代 C 深度"标注（见现有头注）。
- 保留与 A、postprocess.md 的交叉引用链接。

### Phase 4 — 提升硬规则 / 决策（落 A 层 decide.md）
- 若新资料给出可复用的"必做/必避"结论（如 DFT+U 必加、BSSE 警示、OT vs 对角化），提升到 `decide.md`：
  - 新增小节（如 §29、§30…），或并入 §28 同主题。
  - 在相关既有节（§1/§10/§16 等）加 `见 §XX` 交叉指针。
  - SKILL.md summary 的 `§1–§N` 计数 +1，文件索引里 decide.md 描述同步。
- 无直接溯源的经验结论：标注"来源待核对"。

### Phase 5 — 公式与判读陷阱（落 postprocess.md）
- 新资料里的后处理公式（RDF 积分求 CN、MSD 平方再平均、VACF→vDOS≠IR、Einstein D、Arrhenius 等）补进 postprocess.md「关键公式与判读陷阱」节；软件坑（VMD 平面积分、√MSD 等）一并记。

### Phase 6 — 索引与元数据（SKILL.md）
- `SKILL.md` 文件索引：登记任何**新增**文件（如新的 survey/course 文件）；course_learned.md 已在索引中不必重复加。
- summary 行：更新 `§1–§N` 计数、新增能力一句话。
- 「知识来源层级」表：若新增了层或文件，同步更新。

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

---

## 5. "无遗漏"审计清单（每次新增必勾）

- [ ] 每份原始文件都已抽取/读取，**空页与版权页也计入已处理**。
- [ ] 每个 `learn_Ln.md` 附**逐页覆盖清单**，无页遗漏。
- [ ] PDF 与字幕**错位**已识别并按主题重组（未受页号误导）。
- [ ] 所有 `【新】` 内容已落入 B（或 A/C/D），无悬空。
- [ ] 新增硬规则已落 A 且加交叉指针；SKILL.md `§1–§N` 计数已更新。
- [ ] 后处理公式/坑已落 postprocess.md。
- [ ] SKILL.md 索引 + summary + 知识来源层级表已同步。
- [ ] 项目日志 + 跨项目记忆已写。
- [ ] 经验级但无直接溯源的结论已标"来源待核对"。

---

## 6. 交叉引用维护

- decide.md 各节用 `见 §XX` 互链；B 与 A、postprocess.md 之间用相对路径链接。
- 删/改某节导致编号漂移时，**全局搜旧 `§XX` 引用**并批量更新（用脚本做字节安全替换，避免 en-dash 等特殊字符手改出错）。
- 每季度（或每次大改后）通读一遍 A/B 交叉链接是否有效。
