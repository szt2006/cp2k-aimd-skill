# references/pdf_text/ — 庚子计算课程原始素材（溯源层，勿改）

本目录是 `course_learned.md`（权威主题综合）的**唯一溯源来源**。保留它是为了"逐页无遗漏 + 可核对"，**日常不要直接读这些文件**（冗长、按页组织、未去重）；需要课程实战细节时请读 `references/course_learned.md`，发现它有遗漏/错误时再回本目录校正。

## 文件清单

| 文件 | 内容 | 规模 |
|---|---|---|
| `extract_pdf.py` | 用 pdfplumber 把 5 份 PDF 抽成带 `========== PAGE N ==========` 页码标记的分页文本（去"庚子计算-AIMD与CP2K讲义-"前缀与" - 副本"后缀）。重跑可复现 L1–L5.txt | 脚本 |
| `L1.txt` … `L5.txt` | 5 份 PDF 的分页抽取文本（L1=Day1=83页 / L2=Day2=69页 / L3=Day3=156页 / L4=电子结构=64页 / L5=自由能面=53页，共 425 页） | 原文 |
| `learn_L1.md` … `learn_L5.md` | 5 个并行 Agent 的**逐页学习原始稿**（每页覆盖清单 + 标【新】未入 notes 的内容）。是 course_learned.md 的母本 | 原始学习稿 |

## 重要：PDF 序号 ≠ 字幕"第 N 天"（错位表）

| PDF | 实际主题（字幕"天"） | 映射说明 |
|---|---|---|
| L1 | 第 1 天 | AIMD 基础 / 水盒子 / VASP 对照 |
| L2 | 第 2 天 | CP2K 编译 / 建模（非"后处理"） |
| L3 | 第 3 天 | CP2K 输入参数全集 / NEB / 频率 / DFT+U / HSE06 |
| L4 | 第 5 天 | 电子结构（ELF / PDOS / 电荷差分 / 功函数） |
| L5 | 第 5 天续 | 自由能面（PMF / slow growth / metadynamics / QM-MM） |

> 字幕 `4.txt` 才是真"第 4 天"（NEB/频率/Au20）——与 PDF 编号不对应。综合稿 `course_learned.md` 已按**主题**重组，不受此错位影响。

## 字幕同音错字对照（快速参考）

字幕是语音转文字，含大量同音错字。完整表见 `references/course_survey.md` §同音错字表。高频几例：cp two k=CP2K、VSP=VASP、AAMD=AIMD、验室/验尸=赝势、机组=基组、京弯=晶胞、军方位1=MSD、BSS1=BSSE、镜像分布函数=RDF、二氧化石=TiO₂、进二=Au20、PM,F=PMF、METDYNAMICS=metadynamics。

## 溯源维持约定

- 改 `course_learned.md` 时，若涉及某页具体表述，**回对应 `learn_Ln.md` / `Ln.txt` 核对**，避免凭记忆改错。
- 若发现 `learn_L*.md` 本身有误（如 L4 Agent 曾误判"BSSE 不存在"），以 `course_learned.md` / `decide.md §28` 为准，并在本目录不修正原始稿（保留真相溯源），只在综合稿标注更正。
- 本目录文件**不会被 SKILL.md 自动加载**，仅在需要时手动 Read。
