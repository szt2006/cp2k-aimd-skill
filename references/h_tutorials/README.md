# references/h_tutorials/ — H 层：官方教程与实战算例

> **层定位**：收录 **CP2K 官方 workshop / howto / 夏季学校的一手教学材料**，以及随资料附带的
> **真实生产算例工程**（可运行的 `.inp`/`.inc` ＋ 真实 `.out` 与轨迹）。
>
> **一句话**：G 层答"**官方规定了什么**"，H 层答"**官方是怎么教的、真实的算例是怎么写的**"。

---

## 1. 为什么要有这一层（与既有层的边界）

| 层 | 收什么 | 与 H 层的区别 |
|---|---|---|
| **G 官方权威层**（`references/official/`） | 官网 / 手册的**参考条目**逐页采集（关键字、默认值、语法规则、版本变更） | G 层**只把这些教程 PDF 当"外部资源标题"登记**（见 `10_features_resources.md` 的课程清单），**没有收录其教材内容**。凡"官方默认值/语法"这类，以 G 层为准，H 层只写指针 |
| **E 原始素材**（`references/pdf_text/`） | **庚子计算课程**（第三方培训）的讲义 PDF 抽取 ＋ 视频字幕 | E 是**第三方培训**；H 是**官方一手教材**。两者互补：E 讲"讲师怎么跑起来的"，H 讲"官方怎么设计的" |
| **A/B/C/F 层** | 决策库 / 课程综合 / 速查 / 实战手册 | 那些是**蒸馏后的结论**；H 是**原始教材与真实算例**，是它们的溯源依据之一 |

> **冲突裁决**：H 层与 A–F 层冲突时，**先用 G 层裁定**（官方参考最权威）；
> 若属"G 层没写、只有教材讲了"的内容（如某个实操阈值），则以 H 层教材原文为准，并在 A/F 层标注出处。

## 2. 目录结构

```
references/h_tutorials/
├── README.md              # 本文件（层定位 / 清单 / 引用约定）
├── extract_tutorials.py   # 抽取脚本（PDF → txt，按 sha256 去重、带页码标记）
├── extract_doc.py         # 抽取脚本（非 PDF 素材 .doc → doc_text/，最小 OLE2/Word97 解析，零依赖）
├── txt/                   # 24 份教程的分页文本 T01–T24（带 ========== PAGE N ==========）
├── doc_text/              # 非 PDF 素材的正文抽取（无页码标记，**不占 T 编号**，与 txt/ 平行）
├── notes/                 # 逐主题精读笔记，命名 NN_<主题>.md，NN 与 T 编号的主题分组对应
│                          #   01 GPW/GAPW(T01,T19)  02 AIMD/BOMD(T02,T03,T04)  03 杂化与并行(T05,T06)
│                          #   04 输入与运行(T07,T08,T09,T18)  05 HOWTO 与练习(T10–T17)
│                          #   06 基组与上手(T20,T24)  07 QM/MM(T21,T22,T23)  08 真实算例工程(cases/)
└── cases/                 # 真实算例工程：输入卡原文（.inp / 提交脚本）+ 配方卡
    ├── README.md          # ⚠️ **先读**：这批卡有已知错误（4/5 张的 &FIXED_ATOMS 索引是错的，
    │                      #   而 CP2K 静默通过）+ 打包/溯源约定
    └── ...                # 逐工程配方卡与逐行拆解见 ../notes/08_case_projects.md
```

## 3. 教程清单（24 份唯一 PDF，**701 页**；其中 T03 的 74 页与 T02 正文相同，见 §5.2）

> 源目录里 27 个 PDF 中有 **3 对完全重复**（同一份内容既在顶层、又在
> `CP2K官方workshop课件练习资料/` 内），抽取脚本按 sha256 去重，只取 24 份唯一内容。

| 编号 | 短名 | 页 | 原始文件 | 主题 |
|---|---|---|---|---|
| T01 | `gpw_hutter` | 73 | `【gpw-…】hutter-gpw.pdf` | **GPW 方法**（Hutter，官方 workshop）〔3 份重复之一〕 |
| T02 | `aimd_hutter_ws` | 74 | `Ab initio Molecular Dynamics - Juerg Hutter.pdf` | **AIMD**（Hutter，官方 workshop） |
| T03 | `bomd_hutter` | 74 | `【bomd-…】hutter-bomd.pdf` | BOMD 讲义（Hutter）。**抽取出的正文与 T02 逐行相同**，只有 `# SOURCE`/`# TOPIC` 两行元数据头不同（见 §5） |
| T04 | `moving_atoms` | 35 | `【bomd-…】cp2k_moving_atoms.pdf` | MD 中原子如何运动 |
| T05 | `hybrid_admm_watkins` | 43 | `Hybrid Functionals, ADMM - Matt Watkins.pdf` | **杂化泛函与 ADMM**（Watkins） |
| T06 | `parallel_input_mueller` | 42 | `Parallelization, Automatization, Input Magic - Tiziano Mueller.pdf` | **自动化 / 脚本化 / 测试与性能判读**（Mueller）。⚠️ 文件名里的 "Parallelization" 有误导：PDF 标题页是 *"CP2K: Automation, Scripting, Testing"*（T06 P1），**全篇没有 MPI/OpenMP/`GROUP_PARTITION` 并行层次内容**；并行那部分知识在 G 层与 T08/T19 |
| T07 | `cp2k_basics` | 14 | `【输入文件-…】cp2k_basics.pdf` | CP2K 输入基础（Input Basics）〔3 份重复之一〕 |
| T08 | `running2018` | 22 | `【输入文件-…】running_cp2k_calculations2018.pdf` | Running CP2K calculations 2018 |
| T09 | `cp2k3_input` | 26 | `【输入文件-…】cp2k-3.pdf` | CP2K 输入文件 |
| T10 | `howto_static` | 8 | `【单点静态计算-…】howto_static_calculation…pdf` | **HOWTO：单点静态计算** |
| T11 | `howto_geo_opt` | 5 | `【结构优化-…】howto_geometry_optimisation…pdf` | **HOWTO：几何优化** |
| T12 | `howto_cutoff` | 10 | `【截断能测试-…】howto_converging_cutoff…pdf` | **HOWTO：截断能收敛测试** |
| T13 | `ex2016_aimd` | 9 | `【bomd-…】exercises_2016_summer_school_aimd…pdf` | 2016 夏校练习：AIMD |
| T14 | `ex2016_gga` | 10 | `【表面OPT+AIMD-…】exercises_2016_summer_school_gga…pdf` | 2016 夏校练习：表面 OPT + AIMD |
| T15 | `ex2016_hfx` | 7 | `【杂化泛函-…】exercises_2016_summer_school_hfx…pdf` | 2016 夏校练习：杂化泛函 |
| T16 | `ex2018_scf_setup` | 4 | `【对角化vsOT算法-…】events_2018_summer_school_scf_setup…pdf` | 2018 夏校：**SCF 设置（对角化 vs OT）** |
| T17 | `ex2020_uzh_neb` | 6 | `【NEB-…】exercises_2020_uzh_acpc2_ex03…pdf` | 2020 UZH 练习 ex03：**NEB** |
| T18 | `exercises_all` | 6 | `【官方练习汇总-…】exercises.pdf` | 官方练习汇总〔3 份重复之一〕 |
| T19 | `iannuzzi_zurich2017` | 43 | `【GPW和GAPW-…】iannuzzi_cp2k-tutorial-zurich2017.pdf` | **CP2K 教程 Zurich 2017（GPW 与 GAPW）** |
| T20 | `ling_basis_pseudo` | 34 | `【基组和赝势-…】ling_basis_pseudo.pdf` | **基组与赝势** |
| T21 | `qmmm_basic` | 28 | `【QMMM-…】Basic Usage of QMMM in CP2K.pdf` | QM/MM 基本用法 |
| T22 | `qmmm_2d_embedding` | 23 | `【QMMM-…】CP2K Quantum Mechanics  Molecular Mechanics 2D Embedding…pdf` | QM/MM 2D 嵌入 |
| T23 | `qmmm_aimd_approaches` | 86 | `【QMMM-…】QMMM approaches in ab initio molecular dynamics.pdf` | AIMD 中的 QM/MM 方法 |
| T24 | `cp2k_intro` | 19 | `【强烈推荐-…】CP2K使用入门.pdf` | CP2K 使用入门 |

> 另有随资料附带的 **`CP2K User Self Support.doc`**（旧版 Word）与
> **`编译cp2k7.1_intel_libxsmm_libxc_libint.popt.popt`**（编译脚本），处理情况见 §6。

## 4. 引用约定

- **教程**：写 `T13 P7` 或 `T01 P12–P15`（页码即 `txt/` 文件里的 `========== PAGE N ==========`）。
- **算例**：写工程名 + 文件，如 `cu100-h2o-aimd/cp2k.inp` 第 15 行。
- 重跑抽取：`python extract_tutorials.py --src "<资料目录>"`（源目录也可用环境变量 `CP2K_TUTORIAL_SRC`）。
  `--list` 只列清单不抽取。

## 5. 抽取的已知假象（读文本前必看）

`pdfplumber` 对**两端对齐**的排版常**丢掉词间空格**，例如：

```
Hutter,J;Iannuzzi,M;Schiffmann,F;VandeVondele,J.      ← 逗号后无空格
CP2Kversion7.0(DevelopmentVersion),                   ← 词粘连
AhybridGaussianandplanewavedensityfunctionalscheme    ← 整句粘连
```

这是**抽取工具的假象，不是原文错误**。读的时候按语义还原；引用时若需逐字，回 PDF 核对。
另外幻灯片类 PDF 文本量天然少（约 330–640 字节/页），正文型 howto 则高（2000–3000 字节/页），
**"字节少"≠"没内容"**，很多信息在图里。

### 5.1 NUL 字节（已修复，但会影响可读性）

T04 / T05 / T19 / T23 里的某些字形**没有 ToUnicode 映射**，`pdfplumber` 只能把它们
抽成 `\x00`，使 `.txt` 被编辑器与 `read`/`grep` 当成二进制文件。
`extract_tutorials.py` 的 `clean()` 已把 `\x00` 统一换成**普通空格**
（**不改动任何可见字符**，也不折叠空格以免破坏 `pdfplumber` 用空格做的缩进布局）。

> ⚠️ **`\x00` 不是"空格"** —— 这一点本层笔记**逐字符核对过**
> （`notes/02_aimd_bomd.md` §7 第 6 条、`notes/01_gpw_gapw.md` §7 第 1/2 条）。
> 实测这些位置原本是**数学字体的符号**，按字体分四类：
>
> | 字体 | 原字符 | 实例 |
> |---|---|---|
> | `CMMI8` | 希腊字母（**π**） | `E_cutoff = π²/(2h²)` 里的 π |
> | `CMSS10` | **Φ** | T04 P17/P18（4 处） |
> | `CMSY8` | **减号** | 科学计数法上标（T04 的 45 处） |
> | — | **`ff` 连字** | 另一类 |
>
> 也就是说：**只把 NUL 当"少了个减号"是不够的**，它也可能少了一个 π 或 Φ。

代价：这些符号的位置会**空一格**，最典型的是科学计数法——

```
10 08   ← 原文是 10⁻⁰⁸（NUL=CMSY8 减号）
E = 2h2 ← 原文是 E_cutoff = π²/(2h²)（NUL=CMMI8 的 π 与上下标）
```

读的时候按上下文还原。**没有**把 `\x00` 替换成 U+2212 或 π：
**同一个 NUL 在不同页可能是不同的符号**，凭空补一个具体字符属于**发明原文**，
与本层"原文只读"的约定冲突。同一页真正的 U+2212 减号（≠ NUL）是完好保留的，
两者不要混为一谈。

### 5.2 文本内容相同 ≠ PDF 相同（T02 / T03）

`extract_tutorials.py` 用 **PDF 文件的 sha256** 去重，只能拦住**字节完全相同**的重复。
T02 与 T03 是两个不同的 PDF（4 975 762 / 4 981 591 字节，文件名与路径都不同），**躲过了去重**；
但抽出来的正文**逐行完全一致**（各 1471 行，只有 `# SOURCE`/`# TOPIC` 两行不同）。
所以：**T02 与 T03 引用任一份即可，不要当成两份独立材料统计页数**（§3 的 701 页里
T03 那 74 页是重复计数）。

### 5.3 BOM

本层的 `.txt` 与 `.md` 一律 **UTF-8 无 BOM**。附带提醒：`.inp` 若带 UTF-8 BOM，
**CP2K 自己解析首行会失败**（`&GLOBAL` 变成 `\ufeff&GLOBAL`）；`scripts/validate_inp.py`
会检出并给出警告。

## 7. 引用可回溯性（本层的核心承诺，有工具在守）

笔记里每条知识都带 `T** P**` 页码，读者可以回 `txt/` 的对应页核对 —— **这是 H 层
区别于"二手转述"的地方，所以它必须可检验，不能只是口号。**

```bash
python _audit_h_citations.py          # 摘要（在仓库根跑）
python _audit_h_citations.py --detail # 未命中项明细
python _audit_h_citations.py --json   # 给 agent 用
```

它把笔记里英文引号片段回"该行被引用的任意一页"里找，并正确处理页码范围
（`P23–P32`）、并列页（`P19/P25`）、混合写法（`P22、P24–P25`）。两类判据：

| 判据 | 含义 | 基线 |
|---|---|---|
| **页码越界** | 引了该教程不存在的页（`T05 P99` 而 T05 只有 43 页） | **必须为 0**（当前 **0**） |
| **待复核** | 片段在本教程的**其它页**找得到 | 复核清单，**不是**错误清单（当前 **22**） |

**「待复核」为什么不归零**：实测逐条复核过 36 条，其中 **15 条是真错位（已改对）、
21 条是合法的** —— 片段属于**同一行的另一条声明**（行尾在讲 G/D 层对照）、属于
**与 G/D 层对照的那一列**、或被 **PDF 纵向排版拆行**（归一化空白后仍不连续）。
所以这个数字会长期在 **20 上下浮动**，**看到它不要当成"这么多错误"**。

> **这些数字是会变的**（笔记一改就动）：2.7.6 初版是 2363 处被引页 / 待复核 24；
> 做完一轮「§7 存疑逐条查证」后是 **2362 处 / 待复核 22**（agent 顺手改对了 2 处页码）。
> **别把这里的数字当契约** —— 硬契约只有一条：**越界必须为 0**。

「无法定位」同理：多是**中文转述**（笔记在讲教材某页的意思，而不是抄原文），
以及公式记号、关键字标签。它的数量会随笔记里"解释性文字"的多寡明显起伏
（本轮从 183 涨到 247，因为查证过程往 §7 写进了大量源码/手册引用），
**这属于正常增长，不是问题信号**。

### 7.1 `cases/` 的溯源也要可验证

`cases/` 里的输入卡声称是"原文照抄"。清单 `_COPY_MANIFEST.tsv` 逐文件登记了
**源路径 + 字节数 + sha256**；但**清单本身也可能写错**，所以有工具独立重算：

```bash
python _verify_case_provenance.py          # 副本与源文件都重算 sha256
python _verify_case_provenance.py --json
```

它验三件事：① 副本没被改过；② 清单里的**源** sha256 没记错；③ 截断件
（`*.head10tail5.txt`）必须**如实标注**为 excerpt。

**大文件怎么处理**：坐标文件动辄 300+ 行，全量入库会让仓库膨胀，所以只存
"前 10 行 + 后 5 行"的摘录；但清单里**同时登记源文件完整行数与字节数**
（如 `head10+tail5 excerpt (303 lines / 9205 bytes)`），读者一眼知道被截了多少。
⇒ **因此 `cases/` 里的 `.inp` 用 `@INCLUDE 'coord.inc'` 引用坐标时，包含文件不在
本地**，`validate_inp.py` 会如实报"找不到 @INCLUDE 的文件"。这是**打包方式的
必然结果，不是输入卡有问题**；要真跑，请从源目录取完整 `coord.inc`。

源目录不可用时（别人只拿到 skill 副本），脚本会**退化为只验副本自身一致性**并
明确说"来源未验证"——**不会假装验过了**。

### 7.2 真实数据也是回归基线

这批算例的价值不止"读一遍"：它们是**唯一能抓住某些缺陷的测试数据**。合成 harness
用的是单帧随机气体与正常结束的日志，于是下面这些**一个都抓不到**：

| 缺陷 | 合成 harness 为什么漏掉 |
|---|---|
| RDF 归一化写在帧循环体内 | 锚点是**单帧**，单帧只除一次正好正确（真实 2535 帧偏 1659 倍） |
| `energy` 静默吃下轨迹文件 | 没人拿 `.xyz` 去喂 `energy` |
| `parse_output.py` 找 `Max. force` | 合成用例不产真实收敛表（真实输出里 `Max. force` **0 次**） |
| `diagnose.py` 不识别作业被 kill | 合成用例都是"正常结束" |
| `&MULLIKEN` 被误报成 typo | 合成用例从不写 `&MULLIKEN` |
| `BASIS_SET_FILE_NAME` 只比全路径 | 合成用例写裸文件名，真实卡写 `${DATAPATH}/BASIS_MOLOPT` |

所以有一个专门 harness 把这些**钉成回归基线**（源目录不可用时如实 SKIP）：

```bash
python _validate_real_data.py          # 5 项：梯度 / kill 检测 / 拒收轨迹 / RDF CN / 无误报
python _validate_real_data.py --json
```

要**新增**真实算例时：把它放进源目录 → 在 `_validate_real_data.py` 的期望常量旁
补一条断言（**别只加注释**，注释不会红）。

## 8. 非 PDF 素材

| 文件 | 处理 |
|---|---|
| `编译cp2k7.1_intel_libxsmm_libxc_libint.popt.popt` | 纯文本编译脚本，可直接读；是对 `09_build_libraries.md`（G 层）的**实战补充** |
| `CP2K User Self Support.doc` | **已抽取** → `doc_text/cp2k_user_self_support.txt`（34 833 字节 / 163 行）。用 `extract_doc.py` 的**最小 OLE2/Word97 解析器**（纯标准库 `struct`）读出：OLE2 复合文档 → `WordDocument` 流（51 234 字节）→ FIB `fcMin=1536` / `fcMac=36840` → cp1252 解码。**局限**：只取正文文字，**不保留表格 / 图片 / 批注 / 页眉页脚**，且已删掉 Word 的结构控制字符（`\x07` 单元格标记、`\x13/\x14/\x15` 域标记）⇒ **表格的行列边界丢失**，`HYPERLINK`/`INCLUDEPICTURE` 域会留下"域代码 + 域结果"两遍文本 |

> **更正留痕（2026-09-17）**：本表原先记的是「旧版 Word 二进制格式，`pdfplumber` 无法解析；
> **如实标注为未抽取**，需要时用 Word/LibreOffice 另存为 docx/pdf 后再补」。
> **该表述已被证伪**：本机没有 `olefile` / `soffice` / `antiword`，但 OLE2/Word97 的文本层
> **用标准库就能读出来**（见 `extract_doc.py`），无需 Word 或任何第三方包。
> 原判断的错误在于把"`pdfplumber` 不会解析 `.doc`"当成了"这份素材取不出文字"。

### 8.1 `doc_text/` 与 `txt/` 的分工（**不要混用编号**）

| | `txt/` | `doc_text/` |
|---|---|---|
| 来源 | 官方教程 **PDF**（24 份） | 非 PDF 素材（**`.doc`**） |
| 编号 | **`T01–T24`** | **无编号**（用文件名，如 `cp2k_user_self_support.txt`） |
| 页标记 | 有 `========== PAGE N ==========` | **无**（`.doc` 没有页边界） |
| 引用写法 | `T13 P7` | 文件名 + **行号**，如 `cp2k_user_self_support.txt:145` |

> **为什么 `.doc` 不叫 `T25`**：`T01–T24` 是"**PDF 逐页抽取 + 页码标记**"的专用编号空间。
> 把没有页标记的 `.doc` 塞进去，会同时破坏 `_audit_h_citations.py` 的页码审计
> （§7 的「页码越界必须为 0」）与全仓库「**24 份教程 / 701 页**」的口径（§3）。
> 所以它落在与 `txt/` **平行**的 `doc_text/` 子目录。

## 9. 维护约定

- **教程原文只读不改**（`txt/` 是从 PDF 抽取的溯源层）；发现教材有笔误，**在 `notes/` 里标注**，不动原文。
  > **唯一的例外是文件头那三行元数据**：`# SOURCE` / `# PAGES` / `# TOPIC` 是**我们自己的
  > 抽取脚本生成的**，不是教材内容。事实错了就应当更正——否则读者打开文件就被旧描述带偏。
  > 实例：T06 的 `# TOPIC` 原写"并行、自动化与 Input Magic"，而 PDF 标题页是
  > *"CP2K: Automation, Scripting, Testing"*、全篇没有任何并行层次内容（见 §3）。
  > 更正时**同时改 `extract_tutorials.py` 的 `FILTERS` 主题表与 `txt/` 的头部**，保证两者一致；
  > 只改一处会让下次重抽又变回去。
- **改完 `notes/` 必须重跑 `python _audit_h_citations.py`**，确认「页码越界」仍为 0
  （见 §7）。若你改动了被引页码，也要顺手看一眼「待复核」有没有变化。
- **改完 `cases/` 必须重跑 `python _verify_case_provenance.py`**，确认溯源仍一致（见 §7.1）。
- 新增资料：把 PDF 放进源目录 → 在 `extract_tutorials.py` 的 `FILTERS` 里登记映射 → 重跑抽取 →
  补写 `notes/` → 更新本 README 的 §3 清单。
- **新增非 PDF 素材**（`.doc`/`.xls` 等二进制附件）：抽取脚本放**本目录**（`extract_*.py`），
  产物放 **`doc_text/`**，**不进 `txt/`、不占 `T**` 编号**（理由见 §8.1）；
  脚本必须**零依赖**（只用标准库）并挂 `scripts/_console.py` 兼容层，产物为 UTF-8 无 BOM + LF。
  若发现旧记录与实际不符，**按 §8 的"更正留痕"写法改**（写清原记录错在哪），不要悄悄改掉。
- 本目录**不会被 SKILL.md 自动加载**，仅在需要时手动读。
