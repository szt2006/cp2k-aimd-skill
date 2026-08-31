# cp2k-aimd — CP2K 计算顾问 Skill

一个面向 **CP2K（AIMD / 几何优化 / NEB 过渡态 / 元动力学 / 振动分析 / 电子结构后处理）** 的 WorkBuddy skill。
定位是**「会思考的副驾 / 全过程参谋」，不是自动驾驶**：它在每个阶段告诉你该考虑什么、各选项的取舍、该盯哪些指标、常见坑在哪，并给出可执行的命令——最终怎么选、跑不跑，由你决定。

## 它能帮你做什么

- **① 问诊**：描述体系（元素 / 周期 / 电荷 / 自旋 / 目标）→ 推理泛函·基组·赭势·色散·k 点·SMEAR·CUTOFF，并给"从 0 到收敛"的起步阶梯。
- **② 生成**：按你的选择产出 `.inp`（多元素 / ADMM / Meta-GGA / Properties / 恒温器 / NEB / 元动力学 / QM-MM 等进阶开关）。
- **③ 解读**：校验 `.inp` 语法、解析 `.out` 取能量/受力/收敛、诊断 SCF/几何/虚频并建议改哪一行。
- **④ 后处理**：从轨迹算 RDF / MSD / 扩散 / VACF / IR / PDOS / Bader / 自由能面并出图。
- **⑤ 导航**：11 阶段项目向导（`guide.py scan` 读你目录推断卡在哪、下一步做什么）。

## 安装到 WorkBuddy

```bash
# 放到用户级 skill 目录（所有对话/项目自动加载）
cp -r cp2k-aimd ~/.workbuddy/skills/
```

或在 WorkBuddy 的 skill 管理里「导入本地目录」指向本仓库。

## 知识分层（A–E）

| 层 | 文件 | 角色 |
|---|---|---|
| **A 决策库** | `references/decide.md`（§1–§28） | 写输入 / 选方法 / 判读结果的权威答案；§28 庚子讲师实操硬规则 |
| **B 课程综合** | `references/course_learned.md` | 庚子计算 5 天课程（425 页 PDF + 6 字幕）逐页无遗漏内化，主题式导航枢纽 |
| **C 速查** | `references/course_notes.md`、`course_survey.md` | 实战精华速查 / 文件映射 + 同音错字表 |
| **D 手册笔记** | `references/manual_notes.md`、`_manual_tree.txt`、`sections.md` | 官方手册结构化笔记 |
| **E 原始素材** | `references/pdf_text/`（L1–5.txt、learn_L1–5.md、extract_pdf.py） | 溯源层，只读不擅自改 |

> 日常以 **A / B** 为准；新增 / 修正资料的标准流程见 `references/MAINTENANCE.md`（含「无遗漏」审计清单）。

## 目录结构

```
cp2k-aimd/
├── SKILL.md                 # 入口（自动加载，含 read_when 触发词）
├── README.md                # 本文件
├── scripts/                 # recommend / gen_inp / validate / diagnose / parse_output / postprocess / guide
└── references/              # decide / course_learned / course_notes / course_survey / MAINTENANCE
    ├── pdf_text/            # 原始素材（溯源层）+ extract_pdf.py
    └── templates/           # 7 类 .inp 模板（static/geo_opt/cell_opt/aimd_md/metadyn/neb/vib）
```

##  credits

- 决策库与输入结构对照 **CP2K 官方手册**（manual.cp2k.org）与本地 `cp2k_input.xml` 校验。

## 许可

本仓库用于学习与科研交流；课程原始 PDF / 字幕版权归原作者所有，请遵守其使用条款。
