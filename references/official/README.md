# G 层：CP2K 官方权威层

> **来源**：CP2K 官方网站 <https://www.cp2k.org/> 与官方手册 <https://manual.cp2k.org/trunk/>；官方渠道清单依据 <https://github.com/cp2k/cp2k> README 的 Links 节
> **抓取日期**：2026-09-08（第一轮 33 条 / 第二轮 46 条，累计 79 条）；**2026-09-09 第三轮补缺**（X 射线谱 4 页、ML 5 页、DFT 18 子页、官网 6 页、FAQ 4 条、Input Reference 段树），新增 4 个专题文件（20–23），见 `_sources.md`
> **抓取范围**：官网全部导航页 + 官方手册 Getting Started / Methods / Technologies / Development / References 各主要章节 + 3 个非官网官方渠道（GitHub、Dashboard、Google Group）+ 1 篇官方参考论文
> **定位**：官方一手资料，与 E 层（课程溯源）、F 层（实战手册）严格分层、互不混杂

---

## 0. 这一层为什么单独存在

skill 原有的 A–F 层有一个共同特点：**知识来源都是二手转述**。

| 层 | 来源性质 | 典型问题 |
|---|---|---|
| A 决策库 | 讲师经验 + 手册转述 | 讲师的口径可能过时或带个人偏好 |
| B 课程综合 | 培训课程内化 | 课程年份固定，跟不上版本演进 |
| C 速查 | 课程笔记压缩 | 覆盖窄 |
| D 手册笔记 | 旧版手册摘抄 | **手册版本不明，可能与当前版本脱节** |
| E 原始素材 | PDF/字幕逐页稿 | 只读溯源，不便于检索 |
| F 实战手册 | 经验提炼 | 经验≠官方推荐，边界不清 |

G 层的价值就在于**提供一条可回溯到官方原文的基准线**：

1. **凡 A–F 与 G 冲突，以 G 为准**（官方是权威口径），并回查 A–F 标注待修正。
2. **G 层给出官方默认值**，A–F 给出的"推荐值"若与默认值不同，必须说明这是经验性调整而非官方默认。
3. **G 层带版本坐标**。CP2K 版本迭代快（2024.1 起 SCF 不收敛默认 ABORT、2026.2 移除 `CELL_OPT/TYPE` 等），官方文档明确写了版本差异的地方，G 层原样保留版本号。

---

## 1. 与其它层的边界（重要）

**G 层只写官方说了什么，不写"我们觉得该怎么用"。**

| 内容类型 | 归属层 | 说明 |
|---|---|---|
| 官方关键字语义、默认值、可选值 | **G** | 逐条对应官方 Input Reference |
| 官方明确写的推荐做法 | **G** | 例如"常规 NVT 优先用 CSVR" |
| 官方明确的限制、警告、已知问题 | **G** | 例如"小周期胞不适合生产 MD" |
| 官方版本变更与不兼容项 | **G** | 见 `11_version_changelog.md` |
| "我们踩过的坑 / 经验性调参 / 教学场景取舍" | **F** | playbook.md |
| 课程讲师的口径与实操硬规则 | **A** | decide.md |
| 课程原始素材 | **E** | 只读 |

**交叉索引**：G 层每节末尾有 `→ 交叉索引`，指向 A/F 层的对应条目；F/A 层涉及官方口径的条目，也应回指 G 层。

---

## 2. 文件清单与阅读顺序

按"从入口到专题"的顺序排列，编号即建议阅读顺序。

| 文件 | 内容 | 什么时候读 |
|---|---|---|
| `00_map.md` | 官网与手册的完整内容地图、导航结构、HowTo 与教程索引、**周期性约定 / 23 个第三方工具 / 79 个应用案例 / 3 个跳转页** | 想知道"官网上有什么、去哪找" |
| `01_global_and_units.md` | `GLOBAL` 全部 38 个关键字 + `RUN_TYPE` 全部取值 + 单位表 | 写输入文件的开头部分 |
| `02_dft_methods.md` | GPW/GAPW、赝势、基组、OT、k 点、LRI、线性标度、ADMM/HFX、DFT+U、CDFT、色散校正 | 选方法、写 DFT 段 |
| `03_scf_convergence.md` | 官方 SCF 收敛完整指南 + CUTOFF/REL_CUTOFF 收敛教程 | SCF 不收敛 / 收敛网格 |
| `04_sampling_md.md` | MD 系综、温控、压控、平衡协议、时间步长、AIMD 电子设置 | 跑 AIMD |
| `05_optimization.md` | 几何优化、晶胞优化、优化器选择、收敛判据、约束与对称性 | 做优化 |
| `06_properties.md` | 性质计算与电子结构分析（含索引与缺口） | 算性质 |
| `07_restarting.md` | 波函数/MD/NEB/CDFT 重启完整指南 | 续算 |
| `08_errors_and_faq.md` | 官方故障排查六类 + FAQ 清单（19 条，**14 条已取正文**） | 报错 |
| `09_build_libraries.md` | 编译安装、30 个外部库依赖、加速器 | 装 CP2K |
| `10_features_resources.md` | 官方功能全清单、学习资源、引用规范、许可 | 查"能不能算 X" |
| `11_version_changelog.md` | 版本时间线与不兼容变更 | 升级 / 排查版本相关行为 |
| `12_authority_sources.md` | **权威性分级（L0–L3）**、官方渠道逐个核实、判定方法 | **判断某资料是否官方/权威** |
| `13_input_syntax_and_print.md` | 输入文件语法 8 条规则、`&` 段机制、printkey 迭代层级与 `FILENAME` | 写输入 / 控制输出位置 |
| `14_basis_and_potentials.md` | BASIS_SET 文件格式逐行讲解、GTH 赝势 qN 完整清单、5 个赝势库、一致性检查 | 选基组 / 选赝势 |
| `15_optical_and_xray.md` | LR-TDDFT、GW+BSE、RT-TDDFT/Ehrenfest、STM 图像 | 算光学谱 / STM |
| `16_qmmm_embedding_ml.md` | QM/MM（内建力场 / GROMACS / 镜像电荷）、嵌入方法、机器学习势 | 做 QM/MM / 用 ML 势 |
| `17_constrained_dynamics_and_paths.md` | 约束 MD + 蓝月系综校正、NEB（占位）、NEWTON-X 表面跳跃 | 算自由能面 / 非绝热动力学 |
| `18_posthf_semiempirical_and_xray.md` | 后 HF（MP2/RPA/SOS-MP2）、**BSSE 官方出处**、xTB/DFTB、RTBSE、X 射线谱 | 算高精度能量 / 半经验 / 谱学 |
| `19_performance_gpu_community.md` | 官方 benchmark suite、测试机器、Dashboard、CUDA/HIP、Spack、参与开发 | 调性能 / 编译 GPU 版 / 提 PR |
| `20_input_reference_tree.md` | **Input Reference 完整段树**：14 顶层段 / 76 第二层 / 269 第三层 / 359 页面 / 750 直接关键字 + 实操路径表 | **查"某个关键字属于哪个段"** |
| `21_xray_spectroscopy_full.md` | **X 射线谱四路线完整正文**：ΔSCF、XAS_TDP、δ-kick、GW2X（含 5+3 条官方 FAQ） | 算 XAS/XPS / 芯能级谱 |
| `22_ml_embedding_dlaf.md` | **ML 势 5 页 + 嵌入 + 线性代数**：NequIP/Allegro、MACE、NNP、PAO-ML、ACE、Kim-Gordon、DLA-Future | 用 ML 势 / 做嵌入 / 配 DLA-Future |
| `23_dft_subpages_full.md` | **DFT 子页正文补遗**：CNEO-DFT、GauXC/Skala、泊松求解器与带电体系、RI-HFX/RI-HFXk、ADMM 补充 | 量子核 / 外部 XC / 静电边界 / HFX 加速 |
| `24_official_exercises.md` | **官方练习集全采**：**21 个课程 / 248 子页**（239 有正文，约 170 万字符）。**NEB 7 页完整输入**（官方唯一入口）、AIMD/系综/SGCP/i-PI、EOS/PDOS/能带/电荷差/功函数、官方书单与工具、**239 页完整清单** | **跑 NEB / 学 AIMD / 找官方可运行算例** |
| `_sources.md` | 溯源清单：每节对应哪个 URL、抓取日期、原文缺口 | 核对与更新 |

---

## 3. 使用约定

1. **数值单位**：官方文档中 CP2K 内部单位为原子单位（Hartree / Bohr），输入输出中出现的数值默认遵循 `01_global_and_units.md` 的单位表。凡原文带单位标注（如 `ELECTRONIC_TEMPERATURE [K] 300`）的写法，G 层原样保留。
2. **关键字写法**：一律用官方大写形式（`CUTOFF`、`REL_CUTOFF`、`EPS_SCF`）。段名用 `&SECTION` 形式，子段用 `&PARENT/&CHILD` 表示层级。
3. **原文缺口如实标注**：官方有些页面是占位页（"Unfortunately no one has gotten around to writing this page yet"），G 层**不编造内容**，而是标注"官方本页未写，仅有外链"，并给出外链。缺口清单见 `_sources.md`。
4. **"官方默认值"与"推荐值"严格区分**：
   - 标 `[默认]` 的是官方 Input Reference 的默认值；
   - 标 `[官方推荐]` 的是官方正文明确说"推荐 / 更好的选择"的取值；
   - 标 `[示例]` 的是官方示例输入文件中的取值，不代表推荐。
5. **版本敏感项**：凡官方提到"从某版本起"，一律带版本号，并同步登记到 `11_version_changelog.md`。

---

## 4. 已知缺口（官方未覆盖，需靠 A–F 层补）

以下主题官方手册目前**没有正文**（占位页），G 层只能给外链：

| 主题 | 官方页面状态 | 替代来源 |
|---|---|---|
| NEB（Nudged Elastic Band） | 占位页，仅 4 条外链 | A 层 decide.md、F 层 playbook.md、官网 exercises |
| 线性标度 DFT | 占位页，仅 2 条外链 | A 层、官网 exercises |
| 红外光谱 | 占位页，仅 2 条外链 | F 层 postprocess 经验 |
| Raman 光谱 | 占位页 | F 层经验 |
| NMR | 占位页 | F 层经验 |
| QM/MM 量子嵌入理论 | 占位页，仅 1 条外链 | A 层、官网 howto |
| 可极化力场 QM/MM | 占位页 | A 层 |
| 隐式溶剂化 QM/MM | 占位页 | A 层 |
| DFTB | 占位页 | 官网 howto |
| 电化学 | 占位页（"to be done by J. C."） | — |
| Under the Hood（开发内幕） | 占位页 | 源码 |
| 色散校正（vdW） | 手册 `methods/dft/vdw.html` **404** | `10_features_resources.md` 功能清单 + 输入参考 |
| 电子结构分析（DOS/PDOS 等） | 索引页内容极少 | 输入参考各 PRINT 段 |
| X 射线谱 4 个子页 | **已补齐**（2026-09-09）→ `21_xray_spectroscopy_full.md` | — |
| NEWTON-X 场景 B | 官方页在 "B)" 处截断 | NEWTON-X 官网 |
| ML 势 5 页（NequIP/MACE/NNP/PAO-ML/ACE） | **已补齐**（2026-09-09）→ `22_ml_embedding_dlaf.md` | — |
| Kim-Gordon 嵌入 / DLA-Future | **已补齐**（2026-09-09）→ `22_ml_embedding_dlaf.md` | — |
| Input Reference 完整关键字树 | **已补齐**（2026-09-09，索引级）→ `20_input_reference_tree.md`；**750 关键字逐条默认值仍未抄录** | 官方 Input Reference 页面 |
| DFT 子页（CNEO / GauXC / 静电泊松 / RI-HFX 变体） | **已补齐**（2026-09-09）→ `23_dft_subpages_full.md` | — |
| 剩余 4 条 FAQ（contribute / usagestats / name / doing_io） | **已补齐**（2026-09-09）→ `08_errors_and_faq.md` §3.14–§3.17 | — |
| 官网 6 页（science / version_history / videos / tutorials / periodicity / tools） | **已补齐**（2026-09-09）→ `00_map.md` §2.1–§2.4 | — |
| 官方练习集（`exercises`，2014–2025） | **已补齐**（2026-09-09，第四轮）→ `24_official_exercises.md`（**248 子页全采**） | — |
| `exercises:common` 9 个空链接页 + `vib` 空正文 | **官方自身缺口**（"This topic does not exist yet"），如实登记于 `24_...` §5 | 同名主题在手册页已有正文 |
| GauXC / CNEO 完整可运行输入 | 官方页只有片段 | 官方 regtest |
| RI-HFX 固体例 / RI-HFXk 输入尾部 | 官方页代码块截断 | 官方 example bundle |

> **本轮更正**：原表中"BSSE 无专章"的判断**已作废**。官方 `methods/post_hartree_fock/preliminaries.html` 有 BSSE 专节，自动方案 `FORCE_EVAL/BSSE`、手动方案 `KIND/GHOST`，详见 `18_posthf_semiempirical_and_xray.md` §2.9。

**维护约定**：官方补上这些页面后，重新抓取并覆盖对应章节，同时在 `_sources.md` 更新抓取日期。

---

## 5. 维护流程

往 G 层加内容，遵循：

1. **只加官方内容**。任何推断、经验、课程口径一律不放 G 层。
2. **每个文件头部必须有** `> 来源：<URL>` 与 `> 抓取日期：YYYY-MM-DD`。
3. **每个新页面登记到 `_sources.md`**：URL、抓取日期、对应 G 层文件、该页缺口。
4. **发现 A–F 层与 G 层冲突**：先以 G 层为准修正 A–F，并在 A–F 对应位置标注"（已按官方 G 层修正，见 references/official/…）"。
5. **不删除官方原文中的版本号、默认值、警告措辞**。官方说"experimental"就写"experimental"，不要柔化为"可用"。
