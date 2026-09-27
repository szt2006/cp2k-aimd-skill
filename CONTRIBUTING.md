# 贡献指南

感谢你有兴趣改进 cp2k-aimd skill。本仓库既是**给 AI 读的 skill**，也是一份**可核对的知识库**，
所以对改动的要求比普通项目更严：**准确性优先于数量，溯源优先于结论**。

---

## 1. 先理解设计原则

> **顾问，而非自动驾驶。**

本 skill 的定位是"在每个阶段告诉用户该考虑什么、各选项的取舍、该盯哪些指标、常见坑在哪"，
**不是**在后台把整个流程跑完、只丢一堆结果。任何改动都不应破坏这一点：

- 不要在脚本里加入"自动提交 cp2k 作业""自动跑完全流程"这类行为。
- 新增的指导应让用户**自己判断**，而不是替他决定。
- 工具输出要区分"事实"（解析到的数值）与"建议"（下一步可以改哪一行）。

---

## 2. 知识分层（A–G）——往哪儿加东西

| 层 | 文件 | 放什么 |
|---|---|---|
| **A 决策库** | `references/decide.md` | "该选什么 / 为什么 / 怎么判读"的权威答案 |
| **B 课程综合** | `references/course_learned.md` | 课程资料的主题式综合（导航枢纽） |
| **C 速查** | `references/course_notes.md`、`course_survey.md` | 摘要与映射表（不堆深度内容） |
| **D 手册笔记** | `references/manual_notes.md`、`sections.md` | 官方手册的结构化笔记 |
| **E 原始素材** | `references/pdf_text/` | **只读**溯源层，永不删 |
| **F 实战手册** | `references/playbook.md` | **可执行判断**：症状→处方、阈值、命令模板 |
| **G 官方权威层** | `references/official/`（27 文件） | **官方一手基准**：逐页采自 cp2k.org / manual.cp2k.org / GitHub / Dashboard / 官方练习集，带 URL + 抓取日期 |

**判断标准**：这条内容能直接指导"遇到 X 就做 Y"吗？能 → 进 **F**；讲"为什么" → 进 **A/B**；
是官方原文/默认值/版本差异 → 进 **G**（且**只写官方说了什么**，不写"我们觉得该怎么用"）。

> **冲突裁决**：凡 A–F 与 G 冲突，**以 G 为准**，并回修 A–F（在修正处标注"已按官方 G 层修正"）。

完整流程见 `references/MAINTENANCE.md`（含七阶段 SOP 与"无遗漏"审计清单）。
使用者文档（`USAGE.md`）的口径也受 `_doc_consistency.py` 约束，改工具用法时需同步。

---

## 3. 改动的硬性要求

### 3.1 输入文件必须过官方解析器

任何涉及 `.inp` 生成逻辑（`gen_inp.py`、`references/templates/*.inp`）的改动，
**必须**用官方解析器验证：

```bash
pip install -r requirements-dev.txt
python _validate_all.py        # 期望：0 errors, 0 warnings
python _official_validate.py verify_out/*.inp
```

判定依据是 CP2K 官方 `cp2k_input.xml`（由 `cp2k-input-tools` 携带），不是"看起来对"。

### 3.2 后处理改动必须过合成数据校验

```bash
python _validate_postprocess.py   # 期望：ALL POSTPROCESS SUBCOMMANDS PASSED
```

它用随机气箱验 RDF/ADF/CN、已知 D 的布朗运动验 MSD/diffusion、
阻尼振子验 VACF/IR 峰值，因此**不需要真实 CP2K 输出**就能验正确性。

### 3.3 文档数字必须与代码一致

```bash
python _doc_consistency.py     # 期望：OK：文档口径全部一致
```

它会**实测**模板数/阶段数/校验用例数/子命令数并与文档比对。
写文档里的数字前，先 `python _doc_consistency.py --list` 查真值，别手写。

> 历史事故：SKILL.md 同页出现"23 类特征输入"与"生成 15 类输入"；
> README 写"7 类模板"而实际 8 个。这就是该脚本存在的理由。

它现在还管两件容易漂的事：

- **`wizard.py` 的旗标集合**必须覆盖 `gen_inp.py` 的全部带值开关（**实测已漂移过 27 个**）。
  往 `gen_inp.py` 加带值开关时，同步登记 `VALUE_FLAGS` / `MULTI_VALUE_FLAGS`。
- 数值扫描会**先剥掉 markdown 强调符**再匹配，所以 `**28 类**特征输入`、
  `` `17` 个子命令 ``、`子命令 17 个` 这些写法**都躲不过去** —— 写文档别指望换个写法绕过它。

### 3.4 改动知识层必须过引用审计

```bash
python _audit_h_citations.py            # H 层：T** P** 页码越界必须 0
python _audit_videonotes_citations.py   # E 层：videonotes 笔记名/行号 + S*.txt:行号
```

**改哪层跑哪个**。这两条守的是各层的核心承诺"引用能回原文"：
H 层靠页码；E 层靠两类引用 —— `videonotes/<笔记名> L###`（**174 条**）与
`S*.txt:<行号>`（**545 条**，B/C 层的主力形式）。
写 `videonotes/…` 引用时**笔记名不能省**（只有省略号的形式读者回不去原文，审计会报红）；
**在文档里举例说明这种坏写法时，行号请写 `L###` 占位**，否则审计会把例子当成真引用。

### 3.5 新增护栏必须自带注入测试

```bash
python _inject_test.py          # 期望：全部护栏都会红、且写完能复原
python _validate_gbk.py         # 期望：全部通过（强制 GBK 跑全部入口）
python _validate_real_data.py   # 真实算例回归；源目录不在则如实 SKIP（**SKIP ≠ 通过**）
```

`_inject_test.py` 不是可选项。本项目踩过"检查永远绿"的坑：`_validate_all.py` 曾因
静默 `continue` + 分母写死，无论输入多烂都印 `0 errors`。**新增任何护栏，都要在
`_inject_test.py` 里补一条"注入错 → 必须报红"，并且尽量补一条反向对照**
（合法输入必须放行、或把补丁还原后必须复现原缺陷）——只证正向说明不了护栏承重。

### 3.6 脚本的健壮性基线

所有脚本都应满足：

- 无参调用 → 打印 usage + 中文提示，退出码 2（用法错误），**不抛 traceback**。
- `--help` → 正常工作，退出码 0。
- 缺依赖 → 友好提示 + 安装命令，退出码 3，**不抛 ModuleNotFoundError traceback**。
- 文件不存在 → 友好中文错误，退出码 1。

提交前自查：

```bash
python scripts/parse_output.py            # 应打印 usage，exit 2
python scripts/postprocess.py --help      # 应正常，exit 0
```

---

## 4. 提交规范

- **一个改动一个 commit**，message 用祈使句说明"改了什么、为什么"。
  例：`fix(parse_output): 无参调用崩溃 → 改 argparse`
- 🔴 **message 必须以对外版本号开头**，形如 **`V1.2: …`**（或带类型：`V1.2 fix(...): …`）。
  > **为什么**（2026-10 实测踩到）：GitHub 的文件列表只显示"**最后一次改动该文件的提交**"的
  > **message 第一行**。本仓库一度用**工作轮次号**（`v2.7:`）开头，结果 167 个文件在
  > GitHub 上齐刷刷显示 `v2.7: …`，看上去**像这一版叫 V2.7** —— 而对外版本分明是 V1.2。
  > 版本号前置之后，文件列表才读得出"这些文件属于哪一版"。
  >
  > 两种编号的分工别混（详见 `CHANGELOG.md` 的 `## [V1.2]` 段）：
  > **`V1.2` = 对外版本号**（真源是根目录 `VERSION` 文件，由 `_doc_consistency.py` 守着）；
  > **`2.7.x` 之类 = 逐轮工作编号**，只写进 `CHANGELOG` 的条目标题，**不进 commit message 开头**。
- **别攒大提交**：首次入库、批量补文件这类"纯搬运"要**单独一笔**，不要与本轮实际改动混在一起
  —— 否则 `git log` / `git blame` / GitHub 的文件列表全都指不到点子上（本仓库吃过一次：
  一笔 185 文件、10.7 万行的提交把"补入库"和"本轮工作"混在了一起）。
- 涉及口径/阶段/模板数量的改动，**同一 commit 内**更新文档 + 跑 `_doc_consistency.py`。
- 新增经验类内容，**标注来源**：`[L1]`~`[L5]`（PDF 讲义）或 `[字4]`/`[字5]`（视频字幕独有）；
  无直接溯源的结论显式写"来源待核对"，不要包装成事实。
- 更新 `CHANGELOG.md`。

---

## 5. 不要做的事

- ❌ 修改 `references/pdf_text/` 下的原始抽取文本（E 层只读）。
- ❌ 把 A/B 的"为什么"抄进 F 层造成重复。
- ❌ 在文档里手写"XX 类/XX 个"而不跑一致性检查。
- ❌ 加入需要联网或需要 CP2K 二进制才能跑的校验（应保持可用合成数据离线验证）。
- ❌ 提交课程 PDF 原件（版权问题，只允许抽取后的文本按现状保留）。

---

## 6. 版权提示

`references/pdf_text/` 的内容源自「庚子计算」课程 PDF 与视频字幕，
**版权归原作者**，仅作学习与溯源用途。贡献时不要扩大其使用范围，也不要提交原始 PDF。
详见 `LICENSE`。
