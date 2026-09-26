# 庚子计算《AIMD 与 CP2K》5 天培训 — 资料梳理报告

> 目录：`D:\石大\化学软件\cp2k\cp2k课程资料_庚子计算 - 副本\讲义和课程视频字幕`
> 梳理时间：2026-07-19；**2026-10 重新学习后大幅修订**（§1–§6 均改过）
> 目的：先摸清"有什么、对应关系、字幕错字"，再据此学习并内化进 cp2k-aimd skill。
>
> **2026-10 修订说明**：本次由 6 位分析员**逐行**读完 6 份字幕（合计 **22133 行**，无抽样、无跳读），
> 产出 6 份精读报告（`study/_extract/` 下 `S1_1.md`、`S1_2.md`、`S2.md`、`S3.md`、`S4.md`、`S5.md`），
> 并把标注【新】的条目汇总成工单 `study/_extract/NEW_ITEMS.md`（277 条）。
> 旧版本文件有两个已被证明会造成误判的缺陷，本次一并修掉：
> 1. §2"五天主题流"是**抽样**得出的（多处漏讲、错讲）；
> 2. §3 错字表**没有"出处"列**，导致把某一天出现的错字当成全课程通用——后续分析员在别的文件里
>    找不到证据，进而误判"笔记造假/无法溯源"（BSSE 被误归第 4 天就是这么发生的）。
> 本次修订的目标是：**本文件里每一句都能用行号回查**。

## 0. 一句话结论

目录共 11 个文件：**5 个 PDF 是结构化讲义（PPT 导出，合计 425 页），6 个 txt 是视频字幕（语音转写，合计 22133 行）**。
字幕是 5 天课程完整录音的转写，已按天拆分（第 1 天拆成上下两段）。
字幕口语化、含**演示操作细节 / 脚本名 / 学员问答 / 踩坑**，但同音识别有错字（见 §3）。
字幕里大量"讲师实操经验"是 PDF 没有的，正是 skill 缺的那一层——**"怎么真正把 CP2K 跑起来"**。
但要注意：**讲义与字幕是"多对多"关系，不能按编号硬对**（见 §1.2）；**字幕错字必须带出处看**（见 §3）。

## 1. 文件清单与对应

### 1.1 字幕（6 份，合计 22133 行）——按"天"录

| 仓库内 | 原始文件 | 规模 | 对应内容 |
|---|---|---|---|
| `S1.1.txt` | `1.1.txt` | 2857 行 / 105 KB | 第 1 天（上）：课程总览 + AIMD 基础（DFT/PBC/系综/热浴）+ 水盒子例子（CP2K & VASP 各跑一遍）|
| `S1.2.txt` | `1.2.txt` | 1532 行 / 55 KB | 第 1 天（下）：作业提交与杀任务 + VASP INCAR 全参数 + AIMD 四步流程 + 后处理（OSZICAR/VMD/抽帧/录屏）|
| `S2.txt` | `2.txt` | 4546 行 / 163 KB | 第 2 天：AIMD 后处理全套（RDF/MSD/VACF/vDOS）+ CP2K 简介/优缺点/编译 + 建模八类 |
| `S3.txt` | `3.txt` | 4142 行 / 149 KB | 第 3 天：CP2K 输入文件全参数（GLOBAL/FORCE_EVAL/DFT/SCF/QS/MGRID/MOTION）+ 两个完整算例 |
| `S4.txt` | `4.txt` | 4537 行 / 160 KB | 第 4 天：过渡态/NEB + 频率与 TS 验证 + AIMD 参数与重启 + 基组/泛函/DFT+U/磁性/QM-MM |
| `S5.txt` | `5.txt` | 4519 行 / 166 KB | 第 5 天：TRAVIS 振动光谱（IR/Raman/VCD）+ 电子结构分析全套 + 自由能面三法（PMF/slow growth/metadynamics）|

> 逐文件行数 / 字节 / sha256 溯源清单见 `references/pdf_text/README.md` §1.2。
> 引用约定：**`S*.txt` 内容逐字未改、行数未变**，所以"`S2.txt` 第 2972 行"就等于"原始字幕 `2.txt` 第 2972 行"，
> 所有行号引用永久有效（见 `README.md` §2）。

### 1.2 讲义 PDF（5 份，合计 425 页）——**按主题切分的 deck，不是按天录的**

> **更正（2026-10）**：旧版此处把 5 份 PDF 笼统写成"对应 5 天的 PPT 讲义"，**这是错的**。
> 讲义是 5 个**按主题切分**的 deck；字幕才是按天录的。两者**多对多**，按编号硬对必然出错——
> 这正是"BSSE 被误归到第 4 天、进而被判'全文零命中、无法溯源'"的根源。
> 完整错位表见 `references/pdf_text/README.md` §3；页 ↔ 行严格对应见 `MAPPING.md`。

| 讲义 | 页数 | 实际主题 | 对应字幕 |
|---|---|---|---|
| `L1.txt` | 83 | AIMD 基本原理 + VASP 做 AIMD + AIMD 后处理 | `S1.1` `S1.2`（第 1 天）+ `S2` 前段（后处理实操）|
| `L2.txt` | 69 | CP2K 简介 / 编译 / 复杂模型建模 | `S2` 后段（第 2 天）|
| `L3.txt` | 156 | CP2K 计算流程 + 输入参数全集（最核心）| `S3`（第 3 天）为主 + `S4` 部分（基组赝势/优化/NEB/频率/AIMD/DFT+U）|
| `L4.txt` | 64 | 振动光谱 TRAVIS + 电子结构分析 | `S5` 前段（第 5 天）|
| `L5.txt` | 53 | AIMD 模拟自由能势能面（三法）| `S5` 后段（第 5 天）|
| （无对应讲义） | — | NEB / 频率 / Au20 / QM-MM | `S4`（第 4 天）—— **PDF 里没有这些内容** |

- 课程大纲原始出处：`L1.txt` **P2**（9/26–9/30 五天安排）。**实际讲课进度比大纲慢半拍**：
  第 2 天补完了大纲第 1 天的后处理，第 3 天才讲大纲第 2 天的"参数详解"，第 4 天讲大纲第 3 天的
  过渡态 + 第 4 天的频率/DFT+U，第 5 天与大纲一致。这是理解错位表的关键。
- **讲解员口径**（`S1.1:199–205`）：讲义共 5 个 PPT，"**不是一天一个**"，第 3 个 PPT 最核心、要讲两天。
- 抽取与生成脚本：`extract_pdf.py`（讲义分页）、`extract_subtitles.py`（字幕逐字入库）、
  `build_mapping.py`（生成 `MAPPING.md`，带 `--check` 校验分段表是否连续覆盖全文）。

## 2. 五天课程主题流（**2026-10 依据 6 份逐行精读报告重写**）

> 旧版本节标题自带"基于字幕抽样定位"——抽样必然漏。六份报告都指出了本节的缺失：
> 第 2 天漏了 VACF/vDOS、CP2K 优缺点、编译部署、近 1500 行的**建模八类**；
> 第 1 天（上）漏了 DFT 理论回顾、PBC 与晶胞尺寸、热浴四法对比三个成体系的大段；
> 第 1 天（下）被压缩成 4 个点、实际漏掉约 2/3；第 5 天漏了电子结构大段（Bader 全流程等）。
> 本节现改为**按行号分块**重写，块边界都取自各报告的 §1 主题分段表（**连续覆盖全文、无空档**）；
> 更细的分段（每段 3–5 句要点）见 **`MAPPING.md` §4**（`S1.1` / `S1.2` / `S2` / `S3` / `S4` / `S5` 各一节）。

### 2.1 第 1 天（上）`S1.1`（2857 行）

| 行号 | 主题 |
|---|---|
| 1–56 | 开场与课程缘起（研之成理首次单独办 CP2K 班）|
| 57–198 | 五天课程大纲 |
| 199–392 | 课程资料与超算环境（网盘、VMD/VESTA 必装、并行桌面、WinSCP/`rz`）|
| 393–530 | 第一性原理计算能做什么（AIMD 与经典 MD 的差别、1987 年首篇 AIMD、DPMD）|
| 531–730 | 结构决定性质与静态 vs 动态（XPS/TEM/球差电镜/XRD/EXAFS；纯理论设计催化中心）|
| **731–1024** | **基础回顾：从薛定谔方程到泛函**（BO 近似 → HF → 两类基组 → **GPW** → Hohenberg-Kohn → 能量四项 → 泛函阶梯）——*旧版漏* |
| 1025–1151 | 势能面、驻点、电子步与离子步（含 IRC）|
| 1152–1320 | AIMD 计算流程六步（无目标位置、每点都是结构）|
| 1321–1393 | 相空间、统计平均、遍历性 |
| 1394–1470 | 系综选择（为什么 AIMD 首选 NVT）|
| 1471–1575 | 速度形式 Verlet 算法（含讲师现场纠错）|
| 1576–1627 | 关键参数 ①：SCF 收敛精度（`EDIFF`/`EPS_SCF`）|
| 1628–1748 | 关键参数 ②：时间步长 Δt（1/10 上限、1/20 常规的经验规律）|
| 1749–1827 | 长步长技巧：固定键长 vs **改核质量（氘代）** |
| 1828–1879 | 关键参数 ③：计算参数测试（跑两三步换参数比速度）|
| 1880–2016 | AIMD 重复性问题（混沌、多副本、随机数来源）|
| **2017–2150** | **周期性边界条件与晶胞尺寸选择**（镜像相互作用、2×2/3×3/4×4 实例、Au₅₅）——*旧版漏* |
| 2151–2295 | 动能 ↔ 温度、`N_C` 被约束自由度、热浴的目的、退火 |
| **2296–2445** | **热浴四法对比**（速度调节 / CSVR / Anderson / Nosé-Hoover，含 `SMASS` vs `TIMECON`）——*旧版漏* |
| 2446–2471 | 上半场小结与过渡 |
| 2472–2546 | 水盒子算例文件清单与结构文件（CIF、POTENTIAL、BASIS_MOLOPT、`dftd3.dat`）|
| 2547–2700 | CP2K 作业提交全过程（`module load`、`srun -n 64`、`qsub`/`sbatch`、`squeue`、`find_my_job`）|
| 2701–2814 | 输出文件解读与轨迹可视化（XYZ 三要素、`cp2k-energy`、Jmol vs VMD）|
| 2815–2857 | 对比 VASP 提交、杀掉演示任务（`qdelete` / `scancel`）|

### 2.2 第 1 天（下）`S1.2`（1532 行）

> 旧版把这一天概括成 4 个点（提交/ACT 对比/DFT+U/抽帧），**实际漏掉约 2/3**。完整分块如下。

| 行号 | 主题 |
|---|---|
| 1–23 | 杀任务（`qdel`/`qdelete`/`scancel`）与新建 VASP 算例文件夹 |
| 24–102 | VASP 输入文件构成（4 输入 + 1 提交脚本）与 `qstat` 状态位（`R`/`C`）|
| 103–250 | **INCAR 参数逐条**：`NSW` → `POTIM` → `TEBEG`/`TEEND` → `NBLOCK` → `KBLOCK` → `POMASS` |
| 251–398 | **`SMASS` 三档语义 + 耦合强度 + `grep SMASS OUTCAR`** 与 `MDALGO` 热浴选择 |
| 399–534 | **AIMD 平衡态模拟四步法**（结构优化 → 退火升温 → 预平衡 → 生产；前 5 ps 弃置；步骤可省）|
| 535–652 | **模板法与注意事项**（`LWAVE`/`LCHARG` 关闭；六条调参注意事项：K 点 1×1×1、大核赝势、牺牲精度换速度、偶极校正最好不加、DFT-D3 可加、磁性一律按铁磁）|
| 653–759 | DFT+U 必加（TM 氧化物）+ **CONTCAR 速度块 bug** |
| 760–921 | **两篇文献精读**（锂磷硫固态电解质 / 电化学固液界面）：把 Computational Methods "翻译"回 INCAR |
| 922–972 | 自己算例回顾 + **OSZICAR 逐列解读**（T/E/F/E0/EK/SP/SK，一般取 E0）|
| 973–1104 | 后处理（一）（二）：温度/势能图的**局限**（讲师否定"跑平稳=稳定"）与"弃前几 ps 无硬规定" |
| 1105–1229 | **轨迹转换链**：XDATCAR → `xdat2xyz.pl` → `movie.xyz` → `md_simplify.py` → `newpos.xyz`；`sz`/WinSCP 下载；VMD 中文路径坑 |
| 1230–1344 | **VMD 出图六命令**（`pbc set/box/wrap` + `depthcue off`/背景白/GLSL）与 Representations（VDW + Create Rep + DynamicBonds）|
| 1345–1407 | 轨迹动画制作与 SI 投稿（**Win+G** 录屏出 mp4，ACS 期刊支持）|
| 1408–1532 | 收尾与**7 条答疑**（录屏范围 / 短时 AIMD 可信度 / Jmol 导 GIF / Langevin 与 `SMASS` / NPT 少用 / Jmol 加盒子 等）|

### 2.3 第 2 天 `S2`（4546 行）

| 行号 | 主题 |
|---|---|
| 1–262 | VMD 规范（VDW+DynamicBonds）、键长跟踪、**PBC 与键长跟踪冲突**、化学反应实例、VASP 能量涨落 |
| 263–632 | **RDF 全套**：原理与归一化 → 配位数必须**球面积分（4πr²）** → VMD 操作 → 水 RDF 读数（2 / ≈3.97）→ 应用三则 → **必须用正交晶胞 + 晶格矢量旋转** |
| **633–760** | **VACF（速度自相关函数）**：定义、以每一点为参考、曲线判读、傅里叶变换得 vDOS、**VASPKIT 取代旧脚本**——*旧版漏* |
| 761–1057 | 静态频率 vs AIMD 展宽、水 vDOS 读数、VASPKIT **727（VACF）/728（vDOS）** 实操、高压 He–H₂O 文献案例 |
| 1058–1306 | **MSD 与离子迁移率**：锂电池背景、5 温度算例、VASPKIT **722**、MSD 与 RMSD 的关系 |
| 1307–1656 | VMD 算 MSD（含 **align**）、手动多参考帧平均、**讲师当场承认 PPT 写错**（先平方再平均）、爱因斯坦公式（三维 /6、二维 /4）、阿伦尼乌斯拟合求 Ea、与 NEB 对比 |
| 1657–1813 | VMD **多帧结构叠加**（画迁移路径图）、超离子态文献案例、后处理小结 |
| 1814–2122 | CP2K 定位与规模优势、**编译三条路线**（管理员装 / 自己编 / **讲师预编译二进制**）、`mpirun` 三行、apt 版本、**ssmp/popt/psmp 取舍**、队列脚本 walltime 改 999 |
| 2123–2274 | CP2K 是什么（"瑞士军刀"与 Quickstep）、**"快"的前提是原子数多**、版本更新节奏、官网下载（建议 7.1）|
| 2275–2575 | CP2K 经典文献 6 则（晶核生长 / 动态单原子催化 / 加氢 / adaptive-buffer QM-MM / 五唑盐 / 溶液腐蚀）+ SN1/SN2 + 固液界面电化学 |
| 2576–2868 | 手册（**按版本查**）、**Google Group 报错第一入口**、Vim 插件高亮当语法检查、注释写法、**CP2K 不识别缩进、不区分大小写** |
| **2869–3079** | **CP2K 优缺点四点清单**（导体慢 / 磁性要手填自旋多重度 / K 点功能不完善 / 高斯基组 BSSE）+ 扬长避短的量化证据 + **建模总纲：8 类体系**——*旧版仅一句带过* |
| **3080–3401** | **建模 ①固体（数据库）②液体（MS Amorphous Cell）③液体/气体（Packmol 安装）** |
| **3402–3744** | **Packmol 输入文件与混合溶液（密度硬规则）**、液液界面、气体建模与工具选型边界 |
| **3745–4005** | **④固气界面（切 slab + 补终端）⑤固固界面/异质结（VASPKIT 804）** |
| **4006–4356** | **MS 手建异质结（晶格矢量旋转 R30/√3）⑥固液界面（Cu(100)+水，A/B 边长必须一致）⑦气液界面** |
| 4357–4546 | 建模小结与第 3 天预告、**⑧团簇建模（Au20 用铅笔工具逐层堆）**、学员问答 4 则（含 BSSE 校正做法、**内存起码 128 GB**）|

### 2.4 第 3 天 `S3`（4142 行）

| 行号 | 主题 |
|---|---|
| 1–169 | 开场：CP2K 计算流程与文件类型总览（输入 5 类 / 输出 8 类）+ **官方 `tests/` 目录 + `grep` 反查关键词工作法（含 BSSE 演示）** |
| 170–414 | 输入文件语法（section/关键词/`&END`）、颜色编码与 `cp2k.vim` 安装、官方 how-to 与 Si 单点算例 |
| 415–529 | `&GLOBAL`：`PROJECT`/`RUN_TYPE`/`PRINT_LEVEL` |
| 530–620 | `&FORCE_EVAL`：`METHOD` 与 `STRESS_TENSOR`（思维导图虚线=成对关系）|
| 621–872 | `&DFT`：基组/赝势文件名、GTH 与 MOLOPT、UKS/LSD 别名、`WFN_RESTART_FILE_NAME`、`MULTIPLICITY`、`RELAX_MULTIPLICITY`、`CHARGE` 与背景电荷 |
| 873–1042 | `SURFACE_DIPOLE_CORRECTION`、`&QS`（`EPS_DEFAULT` 默认 1E-10 的历史原因、**`EXTRAPOLATION ASPC` 是 AIMD 快的原因**）|
| 1043–1260 | `&MGRID`：多套网格、`NGRIDS`、**`CUTOFF` 与 VASP `ENCUT` 没有任何可比性**、元素周期表测试图与性价比档、`&XC` PBE |
| 1261–1403 | `&SCF` 基本：`SCF_GUESS`/`EPS_SCF`（单位 hartree）/`MAX_SCF`/`ADDED_MOS` |
| 1404–1587 | `&DIAGONALIZATION`（DIIS + mixing 开发者模板）、`&SMEAR`（Fermi-Dirac + 电子温度 300 K 模板）|
| 1587–1784 | **`&OT`：原理、计算量公式、OT vs 对角化完整取舍**（OT 只能 Γ 点、对角化不能加 U）、`MINIMIZER`/`LINESEARCH`/`PRECONDITIONER` **必须先测速**、`OUTER_SCF` |
| 1785–1819 | `PRINT` 段总览（不设就不输出）|
| 1820–2030 | **实例 1：铜/水固液界面单点能**（186 原子、对角化、`.inc` 改名、现场纠错 EPS_SCF 1E-6）|
| ↳ 1863–1879 / 2982–3012 | 模板变量机制 `@SET DATAPATH` + `@INCLUDE`、`&SUBSYS &KIND` 选择机制、**`&KIND` 自定义标签拆价态**、`data/` 目录 `grep` 找硅基组与赝势 |
| 2160–2510 | **基组命名学、BSSE 定量（DZVP ≈5 kcal/mol≈0.2 eV）、MOLOPT-SR 取舍、q 值配对**、`&CELL` 两种写法、`&COORD` 与坐标外挂 |
| 2510–2977 | **坐标文件工程**：`.car` → `demcar2xyz.py` → 删前两行 → `coord.inc`；`-s` 按 Z 重排的价值与固定原子思路；**现场重演 Cu(100)-水从零建模**；`&TOPOLOGY` 读 CIF 但 `&CELL` 仍要单独写 |
| 2978–3207 | 提交与运行（单机 vs 队列、忘记 `export` 的报错、186 原子只吃约 10 GB 内存、进程管理、**必引文献清单**）、输出文件解读 |
| 3208–3590 | `&MOTION &GEO_OPT`：优化算法、**四个收敛标准 vs VASP 只看 `EDIFFG`**、`&CONSTRAINT`、`grep MAX` 监控、PDB 轨迹技巧 |
| 3591–3826 | **实例 2：α-Al₂O₃ 表面水分子吸附能/解离吸附能**（不固定原子的理由）+ 结构优化输出无晶胞的三种补边界方法 |
| 3839–4142 | `&MOTION &CELL_OPT` 全参数、晶胞优化两条精度路线、Cu FCC 实例（3.61 → 3.682 Å）、**CP2K 的 k 点"非常残废"**、末尾 DFT-D3 参数文件必须复制的坑 |

### 2.5 第 4 天 `S4`（4537 行）——**讲义无对应，全部内容只在字幕里**

| 行号 | 主题 |
|---|---|
| 1–160 | 表面氧化案例 + 过渡态概念 + **"没有过渡态"的三类化学过程**（表面吸附一般不算 TS，解离吸附除外）|
| 161–370 | TS 搜索算法总览、NEB"珠子+弹簧"、**nudging 与 CI 的必要性**、插点数目经验（一般 4–5 点）|
| 371–628 | NEB 实操：取初/末态末帧（`tail -125`）、`xyz2neb.pl` 插点（off-by-one 坑）、**CI-NEB 输入逐关键词**（CP2K 可逐点分批算、VASP 必须同时算）|
| 629–830 | 插点合理性检查（`cat` 拼 `NEB.xyz` → VMD）、必须有的 `coord.inc`、NEB 输出与收敛监控（**收敛信息在各 replica 的 `cp2k-<n>.out`，主 out 只有能量**）|
| 831–1002 | 取各点末帧拼 NEB.xyz、选过渡态、**三档验证判据**（1 个虚频=TS / 0 个=极小值 / 多个="啥都不是"）|
| 1003–1206 | 频率理论：Hessian → 力常数矩阵 → ZPVE → **有限位移法（6N+1 次计算）** |
| 1207–1300 | 频率输入文件 + **"固定原子时必须多并行 image、每点核数设少"的关键坑** |
| 1301–1456 | 频率实操（`EPS_SCF` 可改 1e-7 自救虚频）、9 个频率的来历（吸附分子平动转动投影到振动）|
| 1457–1625 | `cp2k_frequency.pl`、`cp2k_frequency_to_movie`、**虚频判读阈值（正常 TS 虚频 ≥100 波数）**、静态 IR 谱 |
| 1626–1855 | AIMD 输入（`&MD` 系综全集含 NPE_I/NPE_F）、热浴参数（**`TIMECON` 经验值 1000–1500**、COUPLING REGION）、输出控制（`&RESTART_HISTORY`）、INP"只改一处"哲学 |
| 1855–2142 | **AIMD 重启完整流程（高价值）**：必须新建文件夹、要复制哪些文件、提交脚本必须改；强关联体系要带 `cp2k-RESTART.wfn`；关掉 SCF 波函数输出；用 `cp2k-1.energy` 的 CPU time 估剩余机时；`md_simplify.py` 抽帧但原始 position 要存档 |
| 2143–2292 | CP2K 官网补充：CSVR vs Nosé-Hoover、coupling region、**退火只能按倍率**（1.001 / 0.99）、2013 JACS 案例背景 |
| 2293–2560 | **TiO₂ 负载 Au20 体系 `cp2k.inp` 逐段详解**（DFT+U 要开 UKS、`EPS_SCF` 3E-6 的平衡、**MD 中不要打印 cube**、`&KIND` 可多写不可少写、文献 U=13.6 eV vs 常规 4–5 eV、**Au 质量 197→19.7**、固定 1–54/289–324 防 slab 漂移）|
| 2561–3122 | **后处理六步**：能量/温度曲线（前 500 步弃置）→ VMD 做 movie 全套 → RDF（跳过前 50~100 帧）→ **RDF 估迁移能垒（−RT·ln g）** → **Au20 质心–原子距离（自写 `max_center.py` ≈67 行）** → Au 团簇 MSD |
| 3191–3525 | 实例：金属/水界面水分子取向（2019 厦门大学，PZC / −1.29 V / −1.85 V 三档）+ **精读该文 Computational Methods（讲师建议照抄写法）** |
| 3526–3953 | 金/水体系实操（六层 Au slab、加 Na⁺ 调电势、`zdis_trajectory.py` 算 Z 分布）、真空能级/电极电势/功函数、**"AIMD 必须做统计平均"（20 个结构平均）** |
| 3954–4068 | 实例 ③：CP2K 做 QM/MM（2900 原子、EAM + PM6、三个 `FORCE_EVAL`）+ metadynamics 预告 |
| 4069–4198 | 实例 ④：锂离子迁移与**程序可替代性**（CP2K 可替代 VASP 发文）+ **DFT-D3 色散校正**（"DFT 天生的缺点"）|
| 4199–4301 | **DFT+U 参数详解（单位天坑 `[eV]`）**、`U_RAMPING` 节奏、何时加 U 的判据 |
| 4302–4522 | **原子磁性设置**（Fe₃O₄ 亚铁磁最复杂案例、Fe2/Fe3a/Fe3b 分别设 4.0/5.0/−5.0）、杂化泛函与 ADMM |
| 4523–4537 | 收尾（预告第 5 天 TRAVIS + 电子结构 + 加速 AIMD）|

> **更正（2026-10）**：旧版此处把 **BSSE** 归给第 4 天，属**张冠李戴**。逐字核实：`4.txt` 与 `L4.txt` **全文无 BSSE**；BSSE 的权威出处是**讲义 `L3.txt` P40–P42** 与**字幕 `S2.txt` 2972–3019 / `S3.txt` 140–169、2343–2345**（即第 2、3 天）。详见 `decide.md §28.2`。
> （2026-10 补充：讲义 **`L2.txt` P33** 亦是权威出处之一，见 §4。）
> 由上表可见第 4 天的真实内容是 **NEB/频率/表面/团簇/基组赝势/DFT+U/磁性/QM-MM**——**讲义里没有这一天**。

### 2.6 第 5 天 `S5`（4519 行）

> 旧版只写了 ELF/PDOS/电荷差分 + TRAVIS + 自由能三法，**漏掉电子结构大段**（Bader 全流程、
> Mulliken/Hirshfeld/Löwdin、平面平均、MO cube、静电势/功函数、分子表面 ESP）。完整分块如下。

| 行号 | 主题 |
|---|---|
| 1–63 | 开场 + 第 5 天大纲；TRAVIS 是什么、与 VASP vDOS 的区别、安装 |
| 64–122 | **为什么必须输出 Wannier 中心** + `&LOCALIZE` 写法 |
| 123–265 | TRAVIS 交互实操（水盒子 IR）、画图、CP2K 自带 IR 不推荐 |
| 266–444 | 电子结构分析总览 + 电荷密度/自旋密度 cube + `STRIDE` + 文件格式 |
| 445–556 | **电荷密度差分原理**（Δρ = ρ(AB) − ρ(A) − ρ(B)；两个片段结构一定不能再优化）|
| 557–722 | **VESTA 实操电荷差分 + 二维截面 + 色彩标注** |
| **723–812** | **平面平均（Z 方向投影）**：自写 `cube.py`、三个投影做 B−C−D——*旧版漏* |
| **813–980** | **Bader 全流程**：原子电荷是人为定义、零通量面、`bader` 跑法、`ACF.dat` 与 CO/Ni 数值解读——*旧版漏* |
| **981–1084** | **原子染色 + Hirshfeld/Löwdin/Mulliken 三种电荷**（net charge 直接就是原子电荷）——*旧版漏* |
| 1085–1310 | **PDOS 参数与画图全流程**（Γ 点局限、`NLUMO`/`LDOS`/`COMPONENTS`、必须高斯展宽、自旋向下取负）|
| 1311–1468 | PDOS 应用五例（离子键/共价键/缺陷态/表面态/π–d 配位键）|
| 1469–1695 | **ELF** 原理 + 应用 + 输入（三中心两电子键、电子化合物 Na₂He、非还原性载体氧缺陷）|
| **1696–1843** | **分子轨道 cube**：`NHOMO`/`NLUMO` 数法、单位 Hartree × 27.211——*旧版漏* |
| **1844–2077** | **静电势 / 功函数**：`V_HARTREE_CUBE`、平面平均取真空能级、Φ = 真空能级 − 费米能级、异质结电子流向——*旧版漏* |
| **2078–2199** | **分子表面静电势 ESP**：ISO 值、VESTA 操作顺序、受阻路易斯酸碱对——*旧版漏* |
| 2200–2377 | 转入 FES：为什么用 AIMD 算 FES（时间尺度/加速采样的必要性）、正则系综与限制性 AIMD + CV |
| 2378–2510 | **PMF 原理与 λ（blue moon）**、CV 设置方法 |
| 2511–2637 | PMF 文献案例三则、VASP `ICONST` 文件格式 |
| 2638–2998 | 碳酸分解例 CV 组合、PMF 实操（插点/提交/取 λ）、Origin 处理全流程 |
| 2999–3238 | PMF 短板（依赖插点密度）、**slow growth 原理与实操**、应用（Pt 溶解/沉积）|
| 3239–3496 | **metadynamics 原理与高斯参数**、文献案例三则、VASP 参数与优缺点、Ru(0001) N₂ 解离实例 |
| 3497–3800 | VASP 配位数 CV 的 99 行 `ICONST`、**CP2K 定义 CV（几行搞定）**、提交与 `HILLSPOT` 结构 |
| 3801–4008 | 势能面生长过程 + **收敛判据（来回跳跃 10 次以上）**、CV 选取技巧、峰高/峰宽与重启换峰、well-tempered、不做 3D |
| 4009–4300 | **CP2K 练习一：Ru+N₂ metadynamics**（`&COLVAR`/`&FREE_ENERGY`/`&WALL`，K 方向千万别定义错）、练习二 QM/MM 脱氢、输出列结构 |
| 4301–4519 | `gaussian.py` 画自由能面、Angew 甲烷单原子催化案例、课程收尾 |

## 3. 字幕识别同音错字对照表（精读前必看）

> **本节 2026-10 大幅扩充**：旧版只有 **36 条**、**没有"出处"列**，把某一天出现的错字当成全课程通用，
> 导致后续分析员在别的文件里找不到证据而**误判笔记造假**（BSSE 事件）。本版把 6 份精读报告
> §7/§8/§9 里所有"`course_survey.md §3` 未收录"的条目**全部收录并按主题分组**，
> 且**每条都给出处**（哪几份字幕 + 代表性行号）。**旧表 36 条的映射全部保留（它们是对的），只补出处**。
> **本表现有 11 组、约 420 行**（按"字幕原文"行计，同义变体合并成一行）。
>
> - **出处写法**：`S1.1`=第 1 天（上）、`S1.2`=第 1 天（下）、`S2`…`S5`=第 2–5 天；
>   字幕文件在 `references/pdf_text/S*.txt`，**行号与原始字幕完全一致，可直接回查**。
> - **备注列**：给代表性行号；`（疑）`= 推断或需回看视频画面确认，**不是硬结论**；
>   `（旧表沿用）`= 旧表有该映射但**现字幕里检索不到该词形**，保留映射、但请勿据它去别的文件找证据。
> - 带 ⚠️ 的条目按 `NEW_ITEMS.md` 口径属"待人工确认"，**不要当硬结论引用**。

### 3.1 程序 / 软件名

| 字幕原文 | 正确含义 | 出处 | 备注 |
|---|---|---|---|
| `cp two k` / `c b two k` / `cp to k` / `cp to qu` / `cp to p 点6.1` | **CP2K** | S1.1 S1.2 S2 S3 S4 S5 | 全课程最高频；`cp two p 点6.1`→CP2K 6.1（S3:118）|
| `CPUK` / `CPTOK` / `CB 4 K` / `CBTOK` / `CPUQUE` / `CPUV` / `CPU 库` / `CPU 配` / `CPKTOK` / `CPD K` / `CP 都 K` / `CP 都可以` / `CP 都可` / `CV two k` / `CV two 也` / `sb to quid` | **CP2K** | S1.1 S2 S3 S4 S5 | 同音变体极多；S3:1787、2256 等处 |
| `VSP` / `VSGO` / `AVASP` / `rask` / `vsk` / `vskate` / `VSKATE` / `vs kt` / `VSK` / `mask` / `BUSP` / `bus` / `vs` | **VASP** | S1.1 S1.2 S2 S3 S4 S5 | `VSP` 六份都有 |
| `vast` | **VASP** | S1.2 | 仅 1 处（S1.2:24）；旧版把它当成一条"提交命令"，属表述误导（`S1_2.md §8.11` 已指出）|
| `VKK` / `VSKV` / `vs kid` / `vs cat` / `vs paid` / `vs pad` / `VASKET` / `VASPIT` / `vice pit` / `vs pit` / `VS kit` / `VASKIT` / `vs kate` | **VASPKIT** | S2 S5 | S2:742、745、1168、3833…；S5:21、989 |
| `AAMD` / `AIAMD` | **AIMD**（从头算分子动力学）| S1.1 S1.2 S2 S3 S4 S5 | 六份均高频 |
| `BAMD` / `BMD` / `VAMD` / `V。AMD` / `AVAMD` / `嘴冒` | **VMD** | S1.2 S4 | S1.2:220、1220；S4:650、3125、3648 |
| `J 冒` / `J 帽` / `锦帽` / `准冒` / `举报` / `J 猫` / `简帽` / `J 毛` | **Jmol** | S1.2 S2 | S1.2:1120、1216、1477–1527；S2:1318–1320 |
| `VESA` / `vista` / `west` / `weston time` / `WESTA` | **VESTA** | S1.1 S2 S3 S4 | S1.1:2509；S2:3171–3172；S3:1849、3544 |
| `CBK` | **CPK**（VMD 原子球+键表示法）| S1.2 S2 | S1.2:1308；S2:119 |
| `ORORIGIN` / `orange` | **Origin** | S2 | S2:418、1206 |
| `M 四` / `MS` / `ms s` | **Materials Studio** | S2 S4 | S2:3295、3728；S4:676、932、3550（勿与 MSD 混）|
| `派克帽` / `拍克帽` / `pack 帽` / `TAC 膜` / `pd 帽` / `back 帽` / `开模` / `开合门` / `派克模式` / `派克膜` | **Packmol** | S1.1 S2 | S1.1:251–252；S2:3403–3743 |
| `CHARLES` / `查瓦斯` | **TRAVIS** | S5 | S5:31–32、264 |
| `GDPC` | **glibc** | S2 | S2:1901–1911 |
| `CTOS 7.6` / `sls 7.6` | **CentOS 7.6** | S2 | S2:1896–1898 |
| `英特尔 MMPI` | **Intel MPI** | S2 | S2:1926 |
| `SBQ` / `奥卡 offer` / `all 卡 offer` | **ORCA**（疑）| S2 | S2:2182、1839——（疑）需回看画面 |
| `XTB` / `STP` / `fly` / `虚拟` | **xTB**（半经验方法）| S2 | S2:2250–2254 |
| `series` | **`&CSR` / CSRC 模块**（Quantum ESPRESSO 代码移植进 CP2K）| S2 | S2:2255–2256 |
| `CONOMICPRESSO` / `conomy express` / `CONOMYPRESSO` / `QUANTUDEPRESS` | **Quantum ESPRESSO** | S2 | S2:2256–2272 |
| `ALA`（与高斯并列）| **ADF**（疑）| S2 | S2:2978——（疑）|
| `SSD 这个数据库` | **ICSD** | S2 | S2:3274 |
| `crystal` / `crystal open database` | **COD**（Crystallography Open Database）| S2 | S2:3113–3114 |
| `setup 课题组` / `SA 课题组` | Materials Project 相关课题组（疑）| S2 | S2:3180–3181；Materials Project 出自 MIT/LBNL，字幕口误待核 |
| `JGDFTX` / `GDFTX` | **JDFTx** | S4 | S4:3882–3885 |
| `MDALYSIS` | **MDAnalysis** | S4 | S4:3689–3693 |
| `north ho 夫` / `north 考夫` | **Nørskov** | S4 | S4:3891、3895（**勿与 `north hover`=Nosé–Hoover 混**）|
| `micro break` | **Michiel Sprik**（slow growth 提出者）| S5 | S5:3016 |
| `偷 chin` | **toolchain** | S4 | S4:4190 |
| `偷称编` | **Intel 编译**（ifort/icc）| S3 | S3:3036 |
| `MK 2 的这个数据库` | **MKL**（Math Kernel Library）| S3 | S3:3038 |
| `SLM` | **SLURM** | S3 | S3:3099 |
| `lib x c` | **libxc** | S4 | S4:4188–4196 |
| `open plus` / `club park` / `SKR 派克` | **OpenBLAS / ScaLAPACK（或 cuBLAS）** | S3 | S3:1414、1419 |
| `CSIS 这个库` | cclib / ASE 之类轨迹读取库（存疑）| S1.2 | S1.2:1188——（疑）无法确证 |

### 3.2 文件类型 / 文件名

| 字幕原文 | 正确含义 | 出处 | 备注 |
|---|---|---|---|
| `postcard` | **POSCAR**（结构文件）**或 POTCAR**（赝势文件）——**一词两义** | S1.1 S1.2 S3 S5 | **见 §3.11 专条**：S1.2:65=POSCAR、S1.2:66–67=POTCAR；机械解码必错 |
| `podcar` | **POTCAR** | S1.2 | S1.2:29 |
| `COSTCARD` | **POSCAR** | S1.2 | S1.2:238 |
| `pos postcard` | **POSCAR**（取其晶格行）| S1.2 | S1.2:1248 |
| `counter card` / `counter car` / `count cut` / `bust content car` | **CONTCAR** | S1.2 | S1.2:738、741、743–744、753 |
| `in car` / `音 cut` | **INCAR** | S1.2 S2 | S1.2:27–58、535、864；S2:1123、1133 |
| `key points` / `key pots boss car` | **KPOINTS** | S1.2 S2 | S1.2:28、61；S2:1123 |
| `奥迪 car` / `ODA` / `orz car` / `oz car` / `奥卡` | **OSZICAR** | S1.2 S2 | S1.2:943、944、987；S2:235–239 |
| `out out to car` | **OUTCAR** | S1.2 | S1.2:960 |
| `x data car` / `s data car` / `x data a car` / `x data to` | **XDATCAR / `xdat2xyz`** | S1.2 S2 | S1.2:1117–1128；S2:893、1153–1155 |
| `x data to x y z 脚本` | **`xdat2xyz.pl`**（VTST 脚本）| S1.2 | S1.2:1123–1126 |
| `movie 点 XYZ` / `魔鬼点 XYZ` | **`movie.xyz`** | S1.2 | S1.2:1134、1135、1194 |
| `md simplify 点 PY` | **`md_simplify.py`** | S1.2 | S1.2:1182（讲义作 `mdsimplify.py`，无下划线）|
| `new position` / `new post` | **`newpos.xyz`**（S4 作 `new_position.xyz`）| S1.2 S4 | S1.2:1208–1215；S4:2105、2643 |
| `cp two k 杠 position 杠一` | **`cp2k-pos-1.xyz`** | S1.2 S4 | S1.2:1196–1198；S4:3138 |
| `cp two k 杠半的点 out` / `杠半六点 alt` | ✅ **`<PROJECT>-BAND<n>.out`**（如 `cp2k-BAND1.out` … `cp2k-BAND6.out`，**每个 replica 一个**）| S4 | S4:709、751、752、761——"杠半"即 `-BAND`。**已定案（2026-10）**：官方 CP2K NEB 练习页逐字"**`neb1-BANDXXX.out` : geometry optimization output for each replica**"，脚本即 `grep ENERGY neb1-BAND${a}.out`（<https://www.cp2k.org/exercises:2014_ethz_mmm:nudged_elastic_band>）。课程 6 个文件 = `cp2k-BAND1..6.out`（`PROJECT` 就叫 `cp2k`）。**旧记的 `cp2k-band.out`（丢序号）与 `cp2k-<n>.out`（丢 `BAND`）都不准确**；同页另有 `cp2k.out`（标准输出）与 `cp2k-pos-Replica_nr_XXX-1.xyz`（每 replica 轨迹）。**统一判据**：盯 replica 级的 out，主 `cp2k.out` 只给能量 |
| `cp to palt` / `cp to get 点 alt` / `CPUKEOUT` / `CPU create out` / `CPUK 点 hot` / `cp two kint` | **`cp2k.out`** | S5 | S5:1763、1783、1784、1829、1928、2007 |
| `super create 点 energy` | **`cp2k-energy` / `cp2k-1.energy`** | S1.1 S4 | S1.1:2744；S4:1907–1913 |
| `cp two k 杠一点 restart` | **`cp2k-1.restart`**（本身即 input 文件）| S4 | S4:1856、1899、1951–1979 |
| `c b two t 杠一点 position` | **`cp2k-1.position`** | S4 | S4:1914–1923、2095、3138 |
| `cp two p 杠 VEL 杠一点 XYZ` | **`cp2k-VEL-1.xyz`** | S4 | S4:1930 |
| `这模特包杠杠 WFN 文件` | **`cp2k-RESTART.wfn`** | S4 | S4:2003–2048 |
| `CORINNATE 点 ink` / `CORONNET 点 X Y Z` / `COORD 点 ink` / `CORD 点 ink` / `COORD 点 int` | **`coord.inc`**（`ink`→`inc`）| S3 S4 | S3:1833、1958、2527、2565；S4:687、699、1334、2424 |
| `XTT` / `STT` | **`.xtd`**（MS 结构文件）| S2 | S2:3378、3381 |
| `OPG` | **`.opj`**（Origin 工程文件）| S5 | S5:2924、3154 |
| `hills 点 sport` / `ho sport` / `hero sport` / `through sport` | **`HILLSPOT`** | S5 | S5:3779、3976、4355、4407 |
| `penalty potential` / `惩罚函数` | **`PENALTYPOT`** | S5 | S5:3978–3979 |
| `PACKMORE 点 ta 点 JZ` | **`packmol.tar.gz`** | S2 | S2:3425 |
| `base set 这个文件` / `base m o o l o p t` / `basis m o l o t t` / `MOLOPTUCL` | **`BASIS_SET` / `BASIS_MOLOPT` / MOLOPT** | S3 S4 | S3:401–404、669–670；S4:3411 |
| `gt h potential` / `gt a 是 potentials` / `gt h` / `gt gt h` / `g t h e n s` / `beset` | **`GTH_POTENTIALS` / GTH 赝势 / basis 文件** | S3 S4 | S3:404、2110；S4:1905、3423–3425 |
| `d z v p m o l s 2g t h q11` | **`DZVP-MOLOPT-SR-GTH-q11`** | S4 | S4:3432 |
| `DJVP` / `t CV two p` / `tz v to p x` | **DZVP / TZV2P / TZV2PX**（基组名）| S3 | S3:2190、2200 |
| `LV 哈水` | **`LVHAR = .TRUE.`** | S5 | S5:1932 |
| `LV 5` / `l charge` | **`LWAVE` / `LCHARG`** | S1.2 | S1.2:558、561 |
| `cb two k 杠 cube 杠 x tronic density` | **`cp2k-cube-electronic_density`** | S5 | S5:742–792 |
| `cub c RT` / `cube enter` / `cube ra` / `TOS cube enter` | CP2K 官方 cube 类小程序（名称无法从字幕确证）| S5 | S5:748、800、801、804——（疑）|
| `DFT 第三点 data` / `DFTD 3点 data` / `DFT 杠第三这个文件` | **`dftd3.dat`** | S1.1 S4 | S1.1:2581–2588；S4:4148–4160 |
| `NAB 点 XYZ` / `NEB 一点 XYZ` / `N 1 B 3` | **`NEB.xyz` / `NEB.3`** | S4 | S4:640、866、885、930 |
| `零点 XYZ 到五点 XYZ` | **`0.xyz` … `5.xyz`**（插点结果）| S4 | S4:451–455、611 |
| `last 是 XYZ` / `last 点 XYZ` | **`last.xyz`** | S4 | S4:1526–1537 |
| `movie mode 杠123456789` | **`movie_mode_1` … `movie_mode_9`** | S4 | S4:1542–1545（mode 1 = 虚频）|
| `DENCYDIDISTANCE 这个文件` | **`distance`**（`max_center.py` 输出）| S4 | S4:3088–3091 |
| `distance 杠阳` / `distance 杠清` | **`distance_O` / `distance_H`** | S4 | S4:3720–3728（阳=氧、清/轻=氢）|
| `water 点 cf` | **`water.cif`** | S1.1 | S1.1:2507、2513–2529 |
| `cp two k 点 input` | **`cp2k.inp`** | S1.1 | S1.1:2548–2556 |
| `验式 / potential`（文件语境）| **`POTENTIAL`**（CP2K 赝势文件）| S1.1 | S1.1:2557–2571 |
| `sub cp tok` / `sub cp two k` / `sub bus` / `sub 瓦斯` / `sub 问` | **提交脚本**（如 `sub_cp2k`、`sub.vasp`）| S1.1 S1.2 S2 | S1.1:2604–2613；S1.2:68–72、926–928；S2:1125 |
| `白板文件` | **空白（模板）文件** | S2 | S2:3306–3307 |

### 3.3 CP2K 关键词 / section

| 字幕原文 | 正确含义 | 出处 | 备注 |
|---|---|---|---|
| `a test 这个目录` / `CPTOPID 这个 test 这个文件夹` | CP2K **`tests/` 目录** | S2 S3 | S3:102–110、135–138；S2:4508 |
| `HOTO` | **how-to**（官网 how to 页面）| S3 | S3:342–343 |
| `NO smarin` / `vs marian` | **no smearing / with smearing**（官方 Si 算例两个子目录）| S3 | S3:365–367 |
| `plus u method` / `DFT 加 U` | **`&DFT_PLUS_U`（DFT+U）** | S3 S4 | S3:931、1667；S4:4219 |
| `surface dio correction` / `surface deo direction` / `surface deo correction` | **`SURFACE_DIPOLE_CORRECTION` + `SURF_DIP_DIR`**（⚠️ **CP2K 没有 `SURFACE_DIPOLE_DIRECTION` 这个关键字**）| S3 S5 | S3:933–942；S5:1955。**更正（2026-09，第二轮视频精读）**：讲师口播的 `SURFACE_DIPOLE_DIRECTION` 在官方 XML 里 **0 命中**；正确的是 **`SURF_DIP_DIR`**（默认 `Z`，别名 `SURFACE_DIPOLE`/`SURF_DIP`），官方 `SURFACE_DIPOLE_CORRECTION` 的描述里就点名 "The normal direction is given by the keyword **SURF_DIP_DIR**"（查证：`python _kw_probe.py --find SURFACE_DIPOLE_CORRECTION`）。旧表把口播名当成关键字名，`course_notes.md:45` 同错、已改 |
| `extension`（"还有 extension 这个关键词"）| **`&EXCITED_STATES` / TDDFPT 相关关键词** | S3 | S3:952 |
| `e p s default` / `eps default` | **`EPS_DEFAULT`** | S3 | S3:969、1170；默认 1E-10 有历史原因 |
| `extra pulation` / `expation order` / `explanation` | **`EXTRAPOLATION` / `EXTRAPOLATION_ORDER`** | S3 | S3:972–973、1011、1034 |
| `a asp c` / `波函数外推 SPC` | **ASPC**（always stable predictor corrector）| S3 S4 | S3:1027；S4:2341 |
| `n grace` | **`NGRIDS`** | S3 | S3:1055、1083、1169、1183 |
| `real cut off` | **`REL_CUTOFF`** | S3 | S3:1093–1094、1162 |
| `sf section` / `s t f guess` / `sf gus` / `EPSSF` / `EPSS DS` | **`&SCF` / `SCF_GUESS` / `EPS_SCF` / `EPS_DIIS`** | S3 S4 | S3:1263–1325、1440–1448；S4:1370、2344 |
| `ADD monitor oritos` / `莫里科 ORITOS` | **`ADDED_MOS`**（added molecular orbitals）| S3 | S3:1382–1383 |
| `orial transformation` / `轨道转换` / `OT 算法` | **OT（orbital transformation）** | S3 S4 | S3:1390–1391、1588–1589；S4:2373 |
| `单 ANONALIZATION` / `双 ANONALIZATION` / `DIAAG` / `两话` | **DIAGONALIZATION（对角化）** | S3 | S3:1406、3986、1687 |
| `SMARRY` / `smiling` / `SMELING` / `smell in` / `simian` / `SMELI` / `SMR` | **`SMEAR`（展宽）** | S3 | S3:1528、1540、1562、1574、1647、1653 |
| `SMEARING` / `small ring` / `Smering` | **`SMEAR`**（⚠️ **CP2K 没有 `SMEARING` 这个段名**）| S3 | 讲师全程念 "SMEARING"（S3:1528 一带）。**更正（2026-09，第二轮视频精读）**：官方 XML 查 `SMEARING` **0 命中**；正确的是 **`&SCF/&SMEAR`**（配 `METHOD FERMI_DIRAC` + `ELECTRONIC_TEMPERATURE`，后者官方默认就是 **300 K**）。第二轮笔记的错字表把 `Smering` "校正"成 `SMEARING`——**校正方向反了** |
| `费米隆基` | **费米能级** | S3 | S3:1567 |
| `这个 boy 不太知道怎么读` | **`BROYDEN`**（OT 第三种 MINIMIZER）| S3 | S3:1709–1710 |
| `land search` / `3 PNT` / `2 PNT` | **`LINESEARCH 3PNT / 2PNT`** | S3 | S3:1729–1733、3966 |
| `PGTATION` / `PANTATION` / `PCONDITION` / `PGNITION` / `PROCONDITION` | **PRECONDITIONER** | S3 | S3:1734–1736、1742、1773–1784 |
| `food single inverse` / `flow single inverse` / `full single inverse` / `flow` / `follow all` | **`FULL_SINGLE_INVERSE` / `FULL_ALL`** | S3 S4 | S3:1744、1750；S4:2374 |
| `TOONTATION` | **OT 的 preconditioner** | S4 | S4:2373 |
| `alter sf` | **`OUTER_SCF`（外圈 SCF）** | S3 | S3:1368 |
| `sb to quid` / `sb to quid 输入文件` | **CP2K 输入文件** | S3 | S3:1787 |
| `太密度` / `投影态密度` / `碳密度` / `整栋的 v DOS` | **态密度 / 投影态密度（PDOS）/ vDOS** | S2 S3 | S3:1800–1801；S2:750、1005、3198、3215 |
| `loading hush field` / `MOLAN 电荷` / `MONICC` / `MICKEN` / `MODEI 电荷` / `木类根电荷` / `穆里肯电荷` / `目的根电荷` / `穆里根` / `MONICON` / `莫里 in charge` | **MULLIKEN（电荷）** | S3 S4 | S3:1802、1811–1813；S4:1932、1941、2410、4451、2324、4205 |
| `logo 定电荷` | **Löwdin 电荷** | S4 | S4:2410 |
| `ELELF` | **ELF**（电子局域函数）| S3 | S3:1803 |
| `坡松 server` / `pon server` / `泊松 server` / `坡松` | **`&POISSON`** | S3 S4 | S3:1909、1926、2469；S4:2343 |
| `sell optimization` / `精包优化` / `静脉优化` / `镜包优化` / `SOPPT` / `精波优化` | **CELL_OPT（晶胞优化）** | S3 S4 | S3:447、565–573、3877、3946；S4:9、57 |
| `energy false` | **`ENERGY_FORCE`** | S3 | S3:449、1873 |
| `GOOPT` / `gu gt` / `JJUOPT` / `GUOPT` / `GUOOPT` | **`GEO_OPT`** | S3 | S3:3238、3257、3383、3392、3953 |
| `quick step` / `quickstep` | **QUICKSTEP**（`&FORCE_EVAL METHOD Quickstep`）| S3 | S3:547、966、3121 |
| `fast`（"经典的分子动力学…写 fast"）| **FIST**（CP2K 力场模块）| S3 | S3:552 |
| `QMMM` | **QM/MM** | S2 S3 | S3:550；S2:2359、2396 |
| `半径件方法` | **半经验方法** | S3 | S3:546、560 |
| `base function` / `奇函数` | **基函数** | S3 | S3:1610–1618 |
| `S 2`（"这个 S 2 的意思呢，是 short range"）| **SR（short range）** | S3 | S3:2321–2336 |
| `加电子` | **价电子** | S3 | S3:2134、2374–2404 |
| `CONSTRAZ` | **`CONSTRAINT Z`** | S3 | S3:3944–3945 |
| `opt cell` / `o p t cell` | **`OPTCELL`**（VASP 选择性优化晶格矢量文件）| S3 | S3:3934 |
| `sq 等于 true` | **`SCALED .TRUE.`**（分数坐标开关）| S3 | S3:2488 |
| `cell` / `sell` / `SL` | **`&CELL`** | S4 | S4:2421、2422 |
| `hos evo` | **`FORCE_EVAL`** | S4 | S4:4012、4013 |
| `mini meter` | **MINIMIZER（CG / DIIS）** | S4 | S4:2377 |
| `NAT 的正则系综` | **NVT 正则系综** | S4 | S4:3467 |
| `n normal` / `NLUO` / `n lo` | **`NLUMO`** | S5 | S5:1112、1173、1737 |
| `n homo` | **`NHOMO`** | S5 | S5:1729、1737 |
| `LDELS` / `2 dos` | **`LDOS`** | S5 | S5:1119、1183 |
| `stat` / `straight` / `stress` | **`STRIDE`** | S5 | S5:349、376、1638 |
| `econst` / `i cos` / `accost` / `ECONST` / `ACCORE` | **`ICONST`**（⚠️ **VASP 的约束定义文件，不是 CP2K 关键字**）| S5 | S5:2582、2779、2890、3064、3495。官方 XML 查 `ICONST` **0 命中**；E 层讲义 `L5.txt:171–183`"VASP 中限制性 AIMD 的文件：ICONST"。CP2K 侧对应 `&SUBSYS/&COLVAR`（定义 CV）+ `&MOTION/&CONSTRAINT/&COLLECTIVE`（钉住 CV）|
| `FIXED_Z` | **`&MOTION/&CELL_OPT CONSTRAINT Z`**（⚠️ CP2K 无 `FIXED_Z`）| S3 | S3:3944–3945。**更正（2026-09）**：讲师现场口播"固定这个……（`FIXED_Z`）"，官方 XML 查 `FIXED_Z` **0 命中**；`&CELL_OPT CONSTRAINT` 取枚举（`X`/`Y`/`Z`/`XY`/`NONE`，默认 `NONE`）。注意与 `&MOTION/&CONSTRAINT/&FIXED_ATOMS`（原子约束）不是一回事 |
| `U_EFFECTIVE` | **`U_MINUS_J`**（"有效 U = U − J"，别名 `U_EFF`）| S4 | 官方 XML 查 `U_EFFECTIVE` **0 命中**、`U_MINUS_J` **1 处**（`FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U`，`unit=hartree`，默认 `0.0`）。⚠️ **DFT+U 的落点在 `&KIND` 下**，不在 `&DFT/&QS` |
| `COUPLING_REGION`（口播） | **`&THERMOSTAT REGION`** | S4 | S4:2171–2196。官方 XML 查 `COUPLING_REGION` **0 命中**；`MOTION/MD/THERMOSTAT/REGION` 默认 `GLOBAL`，枚举 `GLOBAL`/`MOLECULE`/`MASSIVE`/**`DEFINED`**/**`NONE`** |
| `i cream` / `ACCREAM` | ✅ **不是 CP2K 关键字**：这是 **VASP 的 INCAR 标签 `INCREM`**（slow growth 的每步增量，Å/步）| S5 | S5:3072、3103、3109、3180。官方 XML 查 `ICRIN`/`INCREM`/`ICONST` **各 0 命中**；同段字幕 `S5.txt:3101–3111` 讲师原话是"在这个 **VSK（=VASP）** 做计算的过程当中…… **in cut（=INCAR）** 这个文件里面"；`S5.txt:3500–3503` 还专门做了 VASP/CP2K 对照。**CP2K 侧的对应物是 `&MOTION/&CONSTRAINT/&COLLECTIVE` 的 `TARGET_GROWTH`**（单位 `[angstrom*fs^-1]`；换算 `TARGET_GROWTH = 每步增量 ÷ TIMESTEP`）。**✅ 标签真名已定案（2026-10）**：VASP 官方 wiki 明确写的是 **`INCREM`**（Related tags: `ICONST`, `INCREM`, `SHAKEMAXITER`, `SHAKETOL`, `LBLUEOUT`, `REPORT`）—— <https://vasp.at/wiki/index.php/Slow-growth_approach>；**`ICRIN` 在任何 VASP 文档里都不存在**，是字幕音译产物（讲义 `L5.txt:362` 写的 `INCREM` 才对） |
| `STPTOS` / `statues` | **`STATUS`** | S5 | S5:2588、3497 |
| `ANGOA` | **`A`**（VASP ICONST 角度 FLAG）| S5 | S5:2596 |
| `free anna` | **free energy（自由能）** | S5 | S5:2578、2815、3708 |
| `MEODYNAMICS` / `MEHADAMICS` / `METHNAMICS` / `MAD dynx` / `MEADYAMIX` / `meal dynamics` / `mec dynamics` / `matter dynamic` / `meta dnx mix` / `METDNAMICS` | **metadynamics** | S5 | S5:3294、4423、3441、3295、3705、3768、3422、4354、4048、3492 |
| `METDYNAMICS` / `metadyn` | **metadynamics（元动力学）** | S2 S5 | S2:2494；S5:15、3656、3890、3899、4256 |
| `枪` / `word` / `words` | **墙（wall）** | S5 | S5:4091、4092、4151、4158 |
| `风高` | **峰高（高斯峰高度）** | S5 | S5:3793、4290 |
| `静包的编程` / `cell 的编程` | **晶胞的边长** | S5 | S5:149、165 |
| `B 目录` | **`~/bin`**（PATH 目录）| S5 | S5:58 |
| `氧化控线` | **氧空位**（疑）| S5 | S5:1597——（疑）|
| `item 这模块` | 无法确定（讲师本人也表示不知道）| S3 | S3:4138 |

### 3.4 VASP 关键词

| 字幕原文 | 正确含义 | 出处 | 备注 |
|---|---|---|---|
| `PUTIN` / `PUTM` / `two tm` / `staff 的时候是 time step` | **`POTIM`** | S1.2 S2 | S1.2:148、149；S2:1393、1401 |
| `PROMAX` / `po max` | **`POMASS`** | S1.2 | S1.2:223、224、247、248 |
| `n b block` / `n block` / `nb block` | **`NBLOCK`** | S1.2 | S1.2:185、186、586 |
| `k block` | **`KBLOCK`** | S1.2 | S1.2:214、216 |
| `T 1比根` / `t e begin` | **`TEBEG`** | S1.2 | S1.2:167、483、597 |
| `T 1暗的` / `t and` / `t e and` | **`TEEND`** | S1.2 | S1.2:167、483、597 |
| `m d l go` / `MDL 狗` / `MDL 5` | **`MDALGO`** | S1.2 | S1.2:164、369、385、389、395 |
| `SMS` / `s max` / `SMSMSMS` / `grape s max` | **`SMASS` / `grep SMASS`** | S1.1 S1.2 | S1.1:2430、2440；S1.2:163、281、333、343、596 |
| `e d i i f e d i f f` | **`EDIFF`**（VASP 的 SCF 收敛精度）| S1.1 | S1.1:1582–1584 |
| `S 米锤` | **`ISYM`**（=0 不施加对称性）| S1.2 | S1.2:898 |
| `SB 的关键词` / `艾滋病的关键词` | **`ISPIN`** | S3 | S3:756–757 |
| `on restrict 空扇` | **`UNRESTRICTED`**（开壳层）| S3 | S3:739 |
| `CSV 2` / `cs v 2` | **CSVR**（canonical sampling through velocity rescaling）| S1.1 S4 | S1.1:2346、2355；S4:2151、2163、2219 |
| `安 DERSON` / `ANDERSON` / `ANDERSON 热域` | **Andersen 热浴** | S1.1 S1.2 | S1.1:2357、2386–2387；S1.2:385、396 |
| `north hoover` / `north hover` / `north howard` / `not hot` / `not hoover` / `north hover train` | **Nosé–Hoover 热浴** | S1.1 S1.2 S4 | S1.1:2395–2404；S1.2:298、386、391、393、825、906；S4:1706–2217 |
| `老中爱热域` | **Langevin（朗之万）热浴** | S1.2 | S1.2:387 |
| `热域` / `热于耦合` / `热域耦合区域` | **热浴（thermostat）** | S4 | S4:1704–1710、2165、2173、2186–2191 |
| `ron global` / `region` / `messi` / `massive` | **`&THERMOSTAT &NOSE &REGION GLOBAL / MOLECULE / MASSIVE`** | S4 | S4:2171–2196 |
| `time m com` | **`TIMECON`**（CP2K 热浴耦合参数）| S1.1 | S1.1:2432 |
| `词性` | **磁性** | S1.2 | S1.2:673、674、683 |
| `自选阿尔法` / `自选贝塔` | **自旋 α / β** | S1.2 | S1.2:684 |
| `资源向上` / `资源向下` / `自旋模板` / `资源密度` | **自旋向上 / 自旋向下 / 自旋密度** | S4 S5 | S4:3324、4328、4389–4390、4432–4436、4473；S5:317、1160、1224–1226、1661–1663 |
| `spring moment` / `spring moon` | **spin moment（自旋矩）** | S4 S5 | S4:4455；S5:1038–1039 |
| `DFT 杠第三` / `DFT 杠 D 3` / `DFTD 3` / `D、F、GD 3` / `gram d 3` / `gram` / `DF、C 杠 D` / `DFT 第三点 data` | **Grimme DFT-D3（色散校正）** | S1.1 S1.2 S3 S4 | S1.1:2049；S1.2:663、668；S3:1247、4130–4137；S4:3445、4129–4160 |
| `放大化校正` / `分散化校正` | **范德华（色散）校正** | S1.2 | S1.2:662、671 |
| `费米狄拉克转换` / `FIRMMESMIRROR` | **Fermi-Dirac smearing（`&SMEAR`）** | S4 | S4:3371–3373 |
| `被带薪低估` / `带细` | **把带隙低估（band gap）** | S4 | S4:4251、4252 |
| `结纳能` / `截纳能` | **截断能（cutoff energy）** | S4 | S4:3434 |
| `SKT` / `范思思 can` | **SCAN（泛函）** | S4 | S4:4119、4185、4186、4197 |
| `r v v ten` | **rVV10（vdW 泛函）** | S4 | S4:4119、4186、4197 |
| `PPE` / `PPT 的泛函` / `DFGPP` / `PPE 泛函` / `PBE 方函` / `PPP` | **PBE（泛函）** | S3 S4 | S3:1224–1226、1259；S4:3437–3442、4124、4521 |
| `GDA 纯泛函` | **GGA 纯泛函** | S3 | S3:1236 |
| `hash fork` | **Hartree-Fock** | S3 | S3:1229 |
| `B 3 LYP` | **B3LYP** | S3 | S3:1233 |
| `DFTB 方法` | **DFTB** | S3 | S3:545 |
| `HIS 106` / `HISHIS 106` | **HSE06（杂化泛函）** | S4 | S4:4515、4517 |
| `杂化方向函数` / `杂化方向` | **杂化泛函（hybrid functional）** | S4 | S4:4493、4494 |
| `PPA 去算的` | **PBE**（GGA 泛函）| S2 | S2:3241 |
| `优质` / `油脂` | **U 值（Hubbard U）** | S4 | S4:2448–2467、4219–4225、4269–4297 |
| `波 n open hem molecular orbitals` / `BOMD` | **Born-Oppenheimer MD** | S4 | S4:3456、3457、3460 |
| `INDEAL 3 P 秒` / `regardless eclipum p` | **initial 3 ps is regarded as equilibration** | S4 | S4:3488 |
| `矩阵的系统` | **巨正则系综（grand-canonical）** | S4 | S4:3886——⚠️ 推断 |
| `PCE` / `PZ` | **PZC**（零电荷电势，potential of zero charge）| S4 | S4:3212、3213 |
| `OR` | **OER**（氧析出反应）| S4 | S4:3806、3807 |
| `标准轻电极` | **标准氢电极（SHE）** | S4 | S4:3798、3799 |
| `em` / `嵌入式原子式模型` | **EAM**（embedded atom method）| S4 | S4:3970、3971 |
| `四想化三铁` / `三化二铁` / `坚决实行的四氧化三铁` | **Fe₃O₄（四氧化三铁）/ 尖晶石型（spinel）** | S1.2 S3 S4 | S1.2:682；S3:840；S4:4342 |
| `金属铁`（语境"铁磁性的金属铁"）| **α-Fe（铁磁金属铁）** | S3 | S3:839–840 |
| `亚铁磁性、亚铁磁性的`（重复口述）| **亚铁磁（ferrimagnetic）** | S3 | S3:841–842 |
| `TROHRA` | **tetrahedral（Td 四配位）** | S4 | S4:4393 |
| `五撮盐` / `五错盐` | **五唑盐**（pentazole）| S2 | S2:2406、2407 |
| `SN 1反应` / `SN 2` | **S_N1 / S_N2**（亲核取代）| S2 | S2:2497、2508 |

### 3.5 Linux / 超算命令

| 字幕原文 | 正确含义 | 出处 | 备注 |
|---|---|---|---|
| `q sub` / `s match` | **`qsub` / `sbatch`** | S1.1 S1.2 S2 | S1.1:2631–2634；S1.2:72、101；S2:1125、1137 |
| `q state` / `q std` | **`qstat`** | S1.2 S3 | S1.2:76；S3:3103 |
| `to delete` / `CUDELETE` / `q delete` | **`qdel` / `qdelete`** | S1.1 S1.2 | S1.1:2851；S1.2:6、85、121 |
| `s cancel` | **`scancel`** | S1.2 | S1.2:6 |
| `S QUEEN` | **`squeue`** | S1.1 | S1.1:2637 |
| `model load` / `model view` / `model 系统` | **`module load` / `module avail`** | S1.1 | S1.1:2615、2668–2675 |
| `s run 杠 64`（"64 个盒"）| **`srun -n 64`**（"盒"=核）| S1.1 | S1.1:2626–2628 |
| `tr 杠 GXVF` / `ZXVF` / `tag 杠 ZXVF` | **`tar -zxvf`** | S2 S3 | S3:120–121、359–361；S2:3424 |
| `点杠 CONFIG` | **`./configure`** | S2 | S2:3432 |
| `change mode 加 X` / `四维都可` / `可知权行权限` / `加一下可知权行权限` | **`chmod +x`** | S3 S4 | S3:2700–2701；S4:433、1476–1477、1512–1513 |
| `till` / `T 5` / `tie` / `T 有` / `Q` | **`tail`**（取文件末尾若干行）| S1.1 S4 | S1.1:2692；S4:404、858、865、1320、1324、1329、1521、1527、1876 |
| `用这个 hand 的这个 car 这个命令` / `hand position` / `用 to 杠125` / `这个 tale` | **`head` / `tail -n 125`** | S3 | S3:2785、3764、3767、3773 |
| `grp max` / `grape max` | **`grep MAX`** | S3 | S3:3401、3403 |
| `grape 等号 CV two k 杠 P 杠 position` | **`grep ENERGY cp2k-pos-1.xyz`** | S3 | S3:3437–3438 |
| `group cell` / `grp cell` | **`grep CELL`** | S3 | S3:3995–3996、4105 |
| `group` / `grape` / `GRP` | **`grep`** | S5 | S5:2902、2929、3123、3147 |
| `PS 4杠 EF` / `PS 杠 EF` | **`ps -ef`** | S3 | S3:3078–3079 |
| `Q 2杠九` / `Q 2` | **`kill -9` / `kill`**（或 `qdel`）| S3 | S3:3084、3090–3091 |
| `NO Hope` | **`nohup`** | S3 | S3:3042、3072 |
| `down` | **`done`**（for 循环结束）| S4 | S4:892 |
| `ls s` | **`ls`** | S4 | S4:449 |
| `DL 2` | **`dir`**（Windows 列目录）| S4 | S4:3073 |
| `SZ` | **`sz`**（lrzsz 下载命令）| S1.2 | S1.2:1211、1212 |
| `RZ 一下` | **`rz`**（上传文件到服务器）| S2 | S2:3607 |
| `NSCP` | **WinSCP**（传文件工具，"Wi" 被吞）| S1.1 | S1.1:340 |
| `win s c p` | **WinSCP** | S1.2 | S1.2:1214 |
| `rip 等号`（"怎么去看它的能量 rip 等号"）| 不明（疑为查看能量的命令/操作）| S4 | S4:389——⚠️ 未确认 |
| `p bc rap 杠 all` / `p bc rap 刚好` / `PPT set` / `pbc set all` | **`pbc wrap -all` / `pbc set {…} -all` / `pbc box`** | S1.2 S2 | S1.2:1239–1274；S2:38 |
| `display deep clue of` | **`display depthcue off`** | S1.2 | S1.2:1279–1281 |
| `color display background right` | **`color Display Background white`** | S1.2 | S1.2:1282–1283 |
| `creep rap` / `create rap` | **VMD 的 Create Rep** | S1.2 | S1.2:1317–1325 |
| `UTILISIS` / `asset unit self dimension` | **Utilities → Set Unit Cell Dimensions** | S2 | S2:369、370 |
| `moth label bd` / `mos label bd` | **Mouse → Label → Bonds** | S2 | S2:90、122 |
| `graph` / `graphic` / `graphic labels` | **Graphics** | S2 | S2:93、98 |
| `radio per distribution function` | **radial pair distribution function** | S2 | S2:366 |
| `frequent count` / `fband count` / `frequency count` | **Origin 的 `Frequency Count`** | S4 | S4:3094、3095、3733、3739、3740 |
| `new layer wry` | **Origin 的 `New Layer (Right Y)`** | S4 | S4:2936、2937 |
| `飞艇` / `飞艇 liner fitting` | **fitting / Origin 的 `linear fitting`** | S2 | S2:1539 |
| `change mode 加 x deo car` | **`chmod +x demcar2xyz.py`** | S3 | S3:2700 |

### 3.6 工具与脚本（含自写脚本、VMD/MS/VESTA 菜单）

| 字幕原文 | 正确含义 | 出处 | 备注 |
|---|---|---|---|
| `md simplify 点 PY` / `mt simplify` | **`md_simplify.py`**（抽帧，VASP/CP2K 通用）| S1.2 S4 | S1.2:1182；S4:2097–2106 |
| `AMISON 配发的脚本` | **`md_simplify.py` 的发放者**（不明）| S4 | S4:2099——⚠️ 未确认 |
| `x data to x y z 点 PY` | **`xdat2xyz.pl`** | S1.2 | S1.2:1123–1126 |
| `DEMCAR` / `deom car` / `DEMK 文件` / `demcar to x y z 点 PY` | **`demcar2xyz.py`**（DEMCAR→XYZ 转换脚本）| S3 | S3:2553–2555、2590、2694、2704 |
| `x y z to n e b 点 pr` / `x y z to n e b 点这个 P 2` | **`xyz2neb.pl`**（插点）| S4 | S4:425–456——⚠️ 后缀按 `.pl` 记 |
| `n e b make` | **`nebmake.pl`** | S5 | S5:2736 |
| `neb_movie` | **`neb_movie`**（生成 movie.xyz 检查插点）| S5 | S5:2725 |
| `masc` / `max center` | **`max_center.py`**（约 67 行，质心–原子距离）| S4 | S4:3030–3032、3091 |
| `z d i s trajectory` | **`zdis_trajectory.py`**（元素 Z 方向分布）| S4 | S4:3698–3728 |
| `cb two k frequency 点 pl` | **`cp2k_frequency.pl`** | S4 | S4:1462–1494 |
| `cb two k frequency to movie` / `cb tok frequent into movie` | **`cp2k_frequency_to_movie`** | S4 | S4:1500–1544 |
| `python cube 点 PY` | **`cube.py`**（平面平均，自写）| S5 | S5:742–792 |
| `角高 TIONPY` / `Python 点高深` / `高深点 PY` / `高时` | **`gaussian.py`**（画自由能面，VASP/CP2K 通用）| S5 | S5:4297、4302、4357、4380 |
| `六点 PY` / `new 点 PY` | **`new.py`**（CP2K 官网 PDOS 展宽脚本）| S5 | S5:1250、1251 |
| `pythmatt plot lib` / `matt plot lib` | **matplotlib** | S5 | S5:4336、4400 |
| `rip 硅 basis molecular o p t` | **`grep Si BASIS_MOLOPT`** | S3 | S3:2100–2110 |
| `let is` / `LETIS` / `let is part me` / `LIS 3 D` | **Lattice**（MS 晶胞参数面板）| S2 | S2:3778、4200、4281、4245 |
| `letis plan` / `LETIS` | **lattice plane**（VESTA 切面）| S5 | S5:646 |
| `2 d data play` | **2D Data Plane** | （旧表沿用）| **6 份字幕均检索不到该词形**——请勿据此在字幕里找证据 |
| `clive surface` / `click surface` / `固体的电化` | **Cleave Surface** | S2 | S2:3762、3783、3794 |
| `read finanis` / `read flight is` / `redefine metics` | **Redefine Lattices** | S2 | S2:4044、4045、4075 |
| `build vaculab` / `vaculab` | **Build Vacuum**（真空层）| S2 | S2:4427、4428 |
| `INCEL 一下 LIS 这里` | **In-Cell** | S2 | S2:3390 |
| `models mole cell` / `models 和 mobile cell construction` / `a more for cell construction` / `moon cell` | **Amorphous Cell (Construction)** | S2 S3 | S2:3322、3325、4211；S3:2643 |
| `space group input` | **（MS）Symmetry → Space Group** | S2 | S2:3265 |
| `matc` / `match` | **Matching**（Build Layers 适配率面板）| S2 | S2:4251 |
| `cross 包` / `跨包` / `挎包` | **扩胞（Supercell）** | S2 | S2:4173、4174、4175 |
| `see along za in s z plan` | **`c along z` / `a in xz plane`**（MS Build Crystal 取向选项）| S3 | S3:3803 |
| `dynamic bd` / `dynamic bounds` | **DynamicBonds** | S1.2 S2 | S1.2:1307、1313；S2:63、65 |
| `VMVDVDW` / `发达华` / `方达华半径` | **VDW 绘制 / 范德华半径** | S1.2 | S1.2:1295、1297、1298 |
| `VVDW` / `VEW` | **VDW**（VMD 显示方式）| S2 | S2:63、64 |

### 3.7 材料与元素

| 字幕原文 | 正确含义 | 出处 | 备注 |
|---|---|---|---|
| `太阳` / `泰` / `泰勒` / `太` | **钛（Ti）** | S4 | S4:2430、2763、2843 |
| `基因` / `基` / `筋` / `精` / `金` / `金叹` / `金太监` / `金碳键` / `基金键` | **金（Au）/ 金–钛键 / 金–碳键 / 金–金键** | S2 S4 | S2:496、514、557、559、566；S4:2276、2460、2470–2489、3410、3541、3641 |
| `阳` / `仰视` | **氧（O）** | S4 | S4:3679、3723 |
| `清` / `轻` / `倾` | **氢（H）** | S4 | S4:3312、3641、3672、3727、3985–3989 |
| `同水` / `桶水` / `铜水` | **铜–水（Cu/water）体系** | S3 | S3:1826、2637、2750 |
| `薄` / `跛` | **铂（Pt）** | S5 | S5:3224、3225 |
| `鸟` / `锂` / `表` / `了` | **钌（Ru）** | S5 | S5:3479、3482、3484、3510、3514、3523、3718、3719、4014 |
| `蛋` / `弹` / `电` | **氮（N）** | S5 | S5:1394、3514、3522、3560、3580、3681 |
| `势` / `式` / `市` / `士` | **铈（Ce）**（CeO₂）**或钛（Ti）**（TiO₂）——需按上下文判定 | S5 | S5:1329–1333（**CeO₂**，Au 单原子/CeO₂ 的 Ce⁴⁺→Ce³⁺）、S5:2117–2124（**CeO₂**，FLP 页）。**更正（2026-09，第二轮视频精读）**：旧表把 `S5:2120`/`2124` 归给 TiO₂——**不对**；讲义 `L4.txt:777–779` 同一页（受阻路易斯酸碱对/异裂活化 H₂）明写"**Ce 是亲电位点，O 是亲核位点**"。⇒ 该段的 `势/式/市/士`（连同 `二氧化式`/`二氧化石`/`二氧化硫`/`二氧化室`）**一律指 CeO₂**。真正的 Ti 例在 S5:1353–1360（Al 掺 TiO₂）与 S5:2024–2036（g-C₃N₄/TiO₂ 功函数）|
| `折100表面` | ✅ **Ge(100) 表面**（**已定案**，2026-10）| S1.1 | S1.1:493"去研究这个**折100**表面的重构啊"（同段 489–492 只说"第一篇是在 1987 年 / 当时是用的这个 LDA 泛函"，**没有元素名**）。**定案依据**：*M. Needels, M. C. Payne, J. D. Joannopoulos, "Ab initio molecular dynamics on the **Ge(100)** surface", Phys. Rev. Lett. **58**, 1765–1768 (**1987**)**, DOI 10.1103/PhysRevLett.58.1765 —— 年份 1987 与讲师所述吻合，正是"第一次把 AIMD 用到表面重构"。**音证亦合**："折（zhé）"≈"锗（zhě）"，而"硅（guī）"与"折"不音近。**旧版写 Si(100) 的来源**：1985 年 Car–Parrinello **方法学**原文用的是 Si，与本条"第一篇**实际应用**"不是同一篇。（旧记录说"PubMed 203 / Scilit 403 取不到"——已改走 **Crossref API** 取到完整元数据） |
| `离离者磷硫` / `离者磷硫` / `离者临流` / `离者林游` / `离者零流` / `礼锂离子` / `铝元素`（指 Li）| **Li₁₀GeP₂S₁₂ 固态电解质 / 锂（Li）**（疑）| S1.2 S2 | S1.2:783、784；S2:1074、1084、1097、1334、1353、1578——（疑）|
| `二氧化石` | **二氧化钛（TiO₂）**；`S5:2119` 是 **CeO₂** | S5 | S5:1514（TiO₂）；⚠️ **更正（2026-09）**：`S5:2119`"**二氧化石**表面靠近氧的这个位置它更红"属于**受阻路易斯酸碱对**那一页，讲义 `L4.txt:777–779` 明写"**Ce 是亲电位点**" ⇒ 该处是 **CeO₂**，不是 TiO₂（见 §3.11 第 4 条）|
| `二氧化式` / `二氧化硫` / `二氧化室` | **CeO₂**（`S5:1331`、`S5:2117`、`S5:2124`）或 **TiO₂**（`S1.2:709/715`、`S5:1514`）——需按上下文判定 | S1.2 S5 | S1.2:709、715（TiO₂）；S5:1331（**CeO₂**：Au 单原子/CeO₂，Ce⁴⁺→Ce³⁺、f 轨道）、S5:1514（TiO₂）、S5:2117/2124（**CeO₂**：FLP 页）——见 §3.11 |
| `二氧化碳`（本课程多数指 TiO₂）| **二氧化钛 TiO₂**；`S5:3898` 才是**真 CO₂**；`S1.1:2073` 是 **TiO₂** | S1.1 S5 | S5:2024、2028、2036（"二氧化碳的公函稍微大一点" = g-C₃N₄/TiO₂ 的**功函数**）；`S1.1:2073`"它模拟**二氧化碳**表面上金20团簇……负载" = **Au₂₀/TiO₂**（讲义 `L1.txt` P66 有 Ti-Au 键可证）；`S5:3898`（"解离成二氧化碳和水分子"）= **真 CO₂**（H₂CO₃ 的 metadynamics 例）——见 §3.11 |
| `氧化钠` / `氧化土`（"氧化锆、氧化钠、氧化土…非还原性载体"）| **氧化铪 HfO₂ / 氧化钍 ThO₂** | S5 | S5:1583（对照讲义 L4 P39："ZrO₂ HfO₂ ThO₂ 表面氧缺陷"）|
| `精22氧化碳` / `精22氧化碳表面` | **ZrO₂ 或 TiO₂(110) 表面**（无法唯一确定）| S3 | S3:3828——（疑）保留原文 |
| `淡化家` / `氧化嘎` | **氮化镓 GaN** | S5 | S5:1390、1391 |
| `黑林` / `黑人` | **黑磷** | S2 | S2:3867、4086 |
| `硫化墨` / `硫化木` / `硫化膜` / `硫化物` | **二硫化钼（MoS₂）** | S2 S3 | S2:3877、3884、3893、4053；S3:3939 |
| `magazine` | **MXene** | S3 | S3:3939 |
| `钢玉` | **刚玉**（α-Al₂O₃）| S2 | S2:3781 |
| `阿尔法氧化铝` / `贝塔氧化铝` / `C 塔氧化铝` / `θ氧化铝` / `陈塔氧化铝` | **α / β / θ-Al₂O₃** | S2 | S2:3162、3773 |
| `氦化钠` | **Na₂He**（高压钠氦化合物）| S5 | S5:1552、1553 |
| `棚材料` | **硼材料（boron）**，二维硼 | S5 | S5:1524（二维硼三中心两电子键段 S5:1525–1605）|
| `彭13` | **B₁₃ 团簇** | S5 | S5:1604 |
| `铜八团素` / `同八团送` | **Cu₈ 团簇** | S5 | S5:3424、3429 |
| `进二` | **金20（Au₂₀）** | S4 | S4:3010 |
| `精20` / `金20` / `金团素` / `团素` / `弹速` / `团速` / `传输` / `歼20` / `筋` | **Au₂₀ / 金团簇 / 团簇** | S1.1 S2 S4 S5 | S1.1:2087、2096、2131–2133；S2:476、486、509、520、4405–4412；S4:2142、2978–3002；S5:2053、2070、2569 |
| `金55` | **Au₅₅** | S1.1 | S1.1:2142–2144 |
| `纳米饼` | **纳米片**（nanosheet）| S1.1 | S1.1:2100 |
| `组速` / `组速催化剂` | **团簇 / 团簇催化剂** | S1.1 | S1.1:626、634 |
| `四氯化碳` 的前文误写 `氯粉` / `氯` | **四氯化碳（CCl₄）/ 氯仿** | S2 | S2:3663、3670 |
| `荷尔蒙分子` | **激素分子（hormone）** | S2 | S2:3667、3687 |
| `荷尔蒙` / `晴根` / `穷基` / `秀原子` / `碳氯酸` / `碳氯三` / `点` | **hormone / 氰根 CN⁻ / 氰基 / 溴原子 / 碳中心 / 碳中心 / 碘** | S2 | S2:2500–2505、3667 |
| `一氧化碳氧化` 与 `氢原子` 混用（Au 被误说成"氢"）| **金原子（Au）** | S2 | S2:572、596、602 |
| `地核基底` | **铁中心（Fe 中心）配合物** | S2 | S2:178 |
| `氨气分子`（与"亚硫酸根"并列的质子链例子）| **联氨 / 肼（N₂H₄）或氨**（疑）| S2 | S2:223——（疑）|
| `氮氮生成连体` / `氮氮氢中间体` | **N₂H₄ / NNH 中间体** | S2 | S2:180、184、2348 |
| `动态单元子` / `单元子催化` / `SAC` | **动态单原子（催化）/ single-atom catalysis** | S2 | S2:2304、2307、2308 |
| `氧化室` | **氧化锌 / 氧化锡**（疑）| S2 | S2:2884——（疑）|
| `碳碳氮四` / `碳酸氮四` / `碳三氮四` | **g-C₃N₄** | S5 | S5:2023–2025 |
| `六连本` | 六联苯 / 六苯基苯类分子（讲师未给英文名）| S4 | S4:3983、3984——⚠️ 未确认 |

### 3.8 物理量与概念

| 字幕原文 | 正确含义 | 出处 | 备注 |
|---|---|---|---|
| `京弯` / `金包` / `精包` / `镜包` / `静包` / `京包` / `经包` / `金毛` / `晶波` / `积分包` / `基因传错经常错` | **晶胞（cell）** | S1.1 S1.2 S2 S3 S4 S5 | 六份全有；S1.1:2078、2081–2086、2126–2141、2525；S1.2:610–611、1241–1247；S2:344、615–632、2954–2955、3250–3257、3630、4002–4029；S3:447、566–602、2409–2410、2781–2782、2813（**`京弯` 只此一处**）、2956–2959、3490、3505、3761、3788–3811；S4:9、57、1667–1673、2301–2302、2422；S5:165、354 |
| `机组` / `记录文件` | **基组（basis set）** | S1.1 S2 S3 S4 S5 | S1.1:117、847–857；S2:1845–1848、2178、2896、2974–2976；S3:28、403、631–669（**S3 内共 107 处，最高频**）；S4:1903、1976、2313–2316、3360–3364；S5:928 |
| `验室` / `验尸` / `验式` / `样式` / `验试` | **赝势（pseudopotential）** | S1.1 S1.2 S3 S4 | `验室`：S1.1:2569、S1.2:637、S3:28–3131、S4:1976–3408；`验尸`：S1.2:627、630、S3:29、S4:1902；`验式`：S1.1:2558–2567、S1.2:242–247、S3:404–2031、S4:2316–4209；`样式`：S3:681、S4:4405；`验试`：S1.2:66–67、S3:631–2990、S4:3425 |
| `军方位1` / `军方位移` / `均方位1` / `均衡位移` / `MIST` | **MSD（均方位移）** | S2 | S2:1067、1094、1177、1232、1283、1463、1492、1584——**只在 S2**，见 §3.11 |
| `军方位移 RMSD`（把 MSD 叫 RMSD）| **MSD** | S2 | S2:1270、1276、1427、1463（RMSD 出现了，但讲的是 MSD）|
| `2MSD` / `二点 MSD` | **√MSD（RMSD）** | （旧表沿用）| **6 份字幕均检索不到该词形**；实际作 `RMSD`（S2:1270–1280），VMD 直接输出的是带根号的 MSD |
| `镜像分布函数` / `进项分布函数` | **径向分布函数 RDF**（对关联函数）| S2 S4 | S2:264、280–295、352；S4:2754–2756、2777、2844、2848 |
| `配备风` / `配位风` / `三个配备风` | **配位峰** | S2 | S2:428、429、431 |
| `配备元素层` / `配备原子层` / `配位原子层` | **配位层** | S2 | S2:297、299、300 |
| `配备半径` | **配位半径** | S2 | S2:319 |
| `风`（"三个风"）| **峰（peak）** | S2 S4 | S2:433；S4:3000、3001 |
| `查间` / `渐长` / `箭角` / `建成` / `形成见` | **键长 / 键角 / 成键** | S2 | S2:141、166、187、192、203 |
| `承建` / `断电` | **成键 / 断键** | S1.2 | S1.2:1305、1309、1310 |
| `爱因斯坦公式` / `阿列纽斯` / `阿伦尼乌斯` | **爱因斯坦关系 / 阿伦尼乌斯（Arrhenius）公式** | S2 | S2:1553、1612、1613 |
| `质全因子` / `指前因子` | **指前因子（pre-exponential factor）** | S2 | S2:1614、1632 |
| `前移能内累` / `迁移能力` / `求解到的数值` | **迁移能垒 Ea / 迁移能垒 / 解得的数值** | S2 | S2:1611、1618、1625 |
| `量雷` / `能雷` | **能垒** | S2 | S2:1609、1610 |
| `代谢` | **带隙（band gap）** | S2 | S2:2881、2886、3210 |
| `太密度` / `windows` / `整栋的 v DOS` | **态密度（DOS）/ 振动态密度（vDOS）** | S2 | S2:750、1005、3198、3215 |
| `静电式` | **静电势** | S1.2 | S1.2:659 |
| `公函` / `工行` / `宫寒` | **功函数（work function）** | S1.2 S3 S4 S5 | S1.2:658；S3:944–947；S4:3819、3856–3857、3922–3940；S5:1871、1874、1893、1930、2023、2024 |
| `电机电势` / `电力电视` / `电流电视` / `电离电势` | **电极电势** | S4 | S4:3259、3260、3344、3779、3812、3816–3817、3855、3878、3946–3948 |
| `海森矩阵` / `HYTHON 矩阵` / `开 THON 矩阵` | **Hessian 矩阵** | S4 | S4:1004、1006、1021、1023、1035、1043、1177 |
| `立常数矩阵` / `立场是矩阵` | **力常数矩阵** | S4 | S4:558、1039、1069、1178 |
| `一加 N 点` / `一键安点` / `一阶安点` / `一级安检` / `一键安检` | **一阶鞍点（first-order saddle point）** | S1.1 S4 | S1.1:1072、1091、1167；S4:65、66、73、200、316、328、333、991 |
| `虚品` / `需品` / `血瓶` / `区别` / `食品` / `实体` / `实品` / `虚平` / `十品` | **虚频 / 实频** | S1.1 S4 | S1.1:1070、1094–1095；S4:986、994、997、999、1098、1104、1406、1407、1450、1489 |
| `郭德泰` / `good 多菜` / `国多态` / `构多肽` / `工作态` / `过滤态` / `过多菜` / `过多肽` / `过多态` / `过渡态度` / `godhead` / `构造 head` / `go 多 tag` / `GODOT` / `构多态` / `郭德 TE` / `固德 TE` | **过渡态（TS）** | S1.1 S3 S4 | S1.1:1051、1090、1096、1168、1241；S3:1153、3340、3594–3605；S4:2、98、117–148、175、318、345、379、501、523、740、898、922、940、1589、1591 |
| `纳指` | **nudging**（NEB 的投影步骤）| S4 | S4:284、285、286 |
| `珠子` / `处子` / `竹子` / `珍珠` | **珠子（image）** | S4 | S4:227–278、300、321、323 |
| `内冰反应坐标` / `LRC` | **内禀反应坐标 IRC** | S1.1 | S1.1:1097–1102 |
| `电子部` / `离子波` | **电子步 / 离子步** | S1.1 | S1.1:1106–1151 |
| `降空间` / `向空间` / `象空间` | **相空间（phase space）** | S1.1 | S1.1:1322、1325、1334、1355 |
| `细综` / `系统` / `系中` | **系综** | S1.1 | S1.1:1393、1395、1445 |
| `无赖算法` | **Verlet 算法**（速度形式）| S1.1 | S1.1:1488–1489、1572——见 §3.11 |
| `courage 反应` | **Grotthuss 反应**（质子接力传递）| S1.1 | S1.1:1992——见 §3.11 |
| `吹 er` | **tri-（三个水分子参与）** | S1.1 | S1.1:2014 |
| `公过梯度的方法 CG` / `DNS is` | **共轭梯度法 CG / DIIS** | S1.1 | S1.1:1855、1857 |
| `团队 dynamics` | **thermodynamics（热力学）** | S3 | S3:3231 |
| `季度重叠误差` / `机组成交误差` / `记录成电误差` / `机组成量误差` / `机组成员误差` | **基组重叠误差（BSSE）** | S3 | S3:2284、2285、2299、2304、2313 |
| `BSS 1` / `BSS E` / `BSS E 5差` | **BSSE（基组叠加误差）** | S2 S3 | S2:2972、2979、2986、2989；S3:687 |
| `长城因素` / `长城的` | **长程（弥散）因素** | S3 | S3:2335、2337 |
| `正交精细` | **正交晶胞（晶胞正交化）** | S3 | S3:2974–2976 |
| `静招的晶包` / `净正招` | **正交晶胞** | S2 | S2:623 |
| `sel` / `正交格子` | **正交晶胞（ORTHORHOMBIC）** | S4 | S4:1814 |
| `镜包乱跑` | **晶胞整体平移** | S3 | S3:2863 |
| `镜包边旧毛边界` | **晶胞边界** | S3 | S3:2410 |
| `聚氨反应` / `聚原反应` / `绝缘` / `机缘` / `聚氨` | **基元反应** | S3 S5 | S3:3599–3601；S5:2550、3381、3420、3437–3438 |
| `解出`（本次语境为氧化铝解离吸附）| **OH / 解离态** | S3 | S3:3616–3619 |
| `词句出差` | **自旋初猜** | S3 | S3:2065 |
| `自旋多程度` / `集全流程度` / `词句` / `姿态` | **自旋多重度 / 磁矩** | S2 | S2:2898、2900、2914、2917 |
| `不可约的 K 点` / `缩点计算量` / `解释这些不可约的 K 点` | **不可约 K 点 / 缩减计算量 / 只算这些不可约 K 点** | S2 | S2:2928、2937、2942 |
| `钢版点` / `GA 点` / `伽马点` / `伽瓦点` / `钢板点` | **Γ（Gamma）点** | S2 | S2:2946、2949、2950、2957 |
| `塑形包` / `素精包` | **primitive cell（素晶胞）** | S2 | S2:3249、3257 |
| `贯用镜包` / `惯用镜包` | **conventional cell（惯用晶胞）** | S2 | S2:3250 |
| `页页界面` / `业业界面` | **液液界面** | S2 | S2:3644、3651 |
| `业界界面` / `工业界面` / `固器建模` | **固液界面 / 固气（界面）建模** | S2 | S2:3651、3750、4130 |
| `抑智节` / `一制节` / `一指节` / `一字节` / `一智结` | **异质结（heterojunction）** | S2 | S2:3757、3829、3890、3916、4109 |
| `GOGO 建模` / `GOGO 界面` / `google 界面` | **固固（界面）建模** | S2 | S2:3745、3746、3747 |
| `纯向的液体` | **纯相液体** | S2 | S2:3514、3515 |
| `立场方法` | **力场（force field）** | S2 | S2:3334、3369 |
| `史莱姆模型` | **slab 模型** | S5 | S5:1915 |
| `势能变` / `适应面` | **势能面** | S5 | S5:2999、4006 |
| `graph ribon` | **graphene ribbon（石墨烯纳米带）** | S5 | S5:999 |
| `DEFASION` | **diffusion（扩散）** | S5 | S5:3851 |
| `吸附托付` / `西部托付` / `托付` | **吸附脱附 / 吸附脱附 / 脱附（desorption）** | S5 | S5:2245、2249、4431、4459、4465、4471 |
| `枪基` | **羟基（–OH）** | S5 | S5:2547 |
| `拍` / `拍反电` / `拍板键` / `排成键` / `西格玛` | **π / π\*（反键）/ π 反键 / π 成键 / σ** | S5 | S5:1422、1449、1756、1757、1759 |
| `网件中心` / `板件中心` / `玩件 centers` / `绑架中心` / `估值电子中心` | **Wannier centers（瓦尼尔中心）** | S5 | S5:111、121、122、127、141、188 |
| `三中心两电子键` | three-center two-electron bond | S5 | S5:1528、1529、1538、1607（此写法是对的）|
| `电子化合物` | electrides | S5 | S5:1540、1542、1572、1573 |
| `解力吸附` / `方程解力吸附` | **解离吸附（dissociative adsorption）** | S1.1 S3 S5 | S1.1:684–685；S3:3616；S5:1512、4014、4104 |
| `电商` | **电荷（charge）** | S5 | S5:605、3580 |
| `解出` | **CO**（吸附质，电荷差分 total−CO−metal）| S1.1 S2 S5 | S1.1:837、862、869、891、1118、1160；S2:2482、2487、2492；S5:625、3232、3416、3421 |
| `总` / `解出`（后两项）| **total / CO / metal** | S1.1 S5 | 电荷差分三项（S5:625–700 一带）|
| `金字塔形` | **金字塔形（pyramidal）** | S4 | S4:2131、2789、2813、3004、3010、3014 |
| `质心到原子` | **centroid-to-atom** | S4 | S4:2982、2983、2996、3017、3042、3086 |
| `competitional method` | **Computational Methods 章节** | S4 | S4:3348、3349、3353、3511 |
| `spring information` / `support ting information` | **Supporting Information（SI）** | S4 | S4:2571、2572、2576、2749、2750 |
| `A 变` | **again**（重启文件夹名，如 `again_md`）| S4 | S4:1881、1883、1943、2642 |
| `223 个月` | **两三个月** | S4 | S4:2273 |
| `盒` / `和数` | **核（core）** | S4 | S4:489、490、505、1245、1268、2276、2277 |
| `联想其他的常数` | **理想气体常数 R** | S4 | S4:2887、2888 |
| `400 个得拜` | 400（截断能数值，单位疑为 Ry）| S4 | S4:3435——⚠️ 未确认 |
| `angle 这篇文章` | **a paper / an article**（泛指文献）| S4 | S4:21——**注意 `angle` 在 S2:142–151 等处是"键角"，勿一律套用** |
| `PM 、 F` | **PMF**（伞采样）| S5 | **旧表词形**；字幕实际作 `PEMF` / `PMPMF` / `PMF`（S5:2381、2443、2513、3084）|
| `PEMF` / `PMPMF` / `PTOSHOP me false` | **PMF / potential of mean force** | S5 | S5:2381、2443、2513、3084、2636 |
| `slow growth` / `SLOGLOSE` / `SLOGOS` / `slow boos` / `slow boss` / `slow cloth` / `slow gross` / `SLOGOUSE` | **slow growth（缓慢增长）** | S5 | S5:3018、3060、3063、3106、3153、3215、3222 |
| `限制AAMD` | **限制性 AIMD** | （旧表沿用）| 字幕整体作 `AAMD`；"限制AAMD"整串未检到——映射本身没错 |
| `自由能势能面` | **free energy surface (FES)** | S3 S4 S5 | 字幕常用说法，非错字 |
| `ELF` / `ERF` / `ELELF` | **ELF（电子局域函数）** | S3 S5 | S5:1520、1634；S3:1803 |

### 3.9 单位

| 字幕原文 | 正确含义 | 出处 | 备注 |
|---|---|---|---|
| `两批秒` / `一批秒` / `平秒` / `频秒` / `P 秒` / `三批秒` / `五批秒` / `平方` / `皮秒` / `批秒` / `匹秒` / `品种` | **ps（皮秒）** | S1.1 S1.2 S2 S4 S5 | S1.1:1667–1668；S1.2:803、810、846、851、1081–1093、1458–1461、1473；S2:1605、2288、3059；S4:42、2274、2280、2486、3491、3919–3920；S5:2269、2914–2915、3885、3889 |
| `两分秒` / `一分秒` / `40分秒` / `分秒` | **fs（飞秒）** | S1.2 S4 | S1.2:161、317、834、940；S4:2059、2061、2133、2136、3104、3143、3477 |
| `十分秒` / `时分秒`（的 1/10）| **十飞秒**（O–H 振动周期 ≈10 fs）| S1.1 | S1.1:1744、1745 |
| `电子肤色` / `电子红色` / `电子图层` / `电子福特` / `电子负载` | **电子伏特（eV）** | S4 | S4:2336、2340、2452、2457、2459、3800 |
| `拨鼠` | **波数（cm⁻¹）** | S4 | S4:1405 |
| `焦米摩尔` | **焦每摩尔（J/mol）** | S4 | S4:2893、2894 |
| `哈水` / `哈欠` / `哈 sh` / `hash` / `含水` | **Hartree（a.u.）** | S5 | S5:1835、1866、1867、1929、1970、2092、2093、2148 |
| `harsh 美波尔` / `HARR` | **hartree（a.u.）/ bohr** | S3 | S3:1328、3313 |
| `波尔` | **bohr（玻尔）** | S3 | S3:1351 |
| `彼得堡 RY` / `里得堡` / `给特保值` | **里德伯 Ry（Rydberg）** | S3 | S3:1090、1125、1136–1138 |
| `平米`（"782 平米"）| **皮米 pm** | S5 | S5:156、157（讲义 L4 P6："Enter length of cell vector in pm: 782"）|
| `I` / `A` / `EI` / `EA` / `3 S` | **埃 Å** | S5 | S5:2353、2354、3460、4100、4106、4233、4236、4239、4241 |
| `X 创的` / `I`（长度单位）| **Å（埃）** | S3 | S3:2483 |
| `111 K 点` / `221` / `331` / `333` | **1×1×1 / 2×2×1 / 3×3×1 / 3×3×3 K 点网格** | S1.2 | S1.2:608、614、615、892 |

### 3.10 其它 / 杂项

| 字幕原文 | 正确含义 | 出处 | 备注 |
|---|---|---|---|
| `研之城里` | **研之成理**（机构名）| S1.1 | S1.1:1–56 一带 |
| `安慰`（改微信群备注的方式）| **单位**（备注按"姓名 + 单位"改）| S1.1 | S1.1:375–376 |
| `电话` | **电化学** | S1.2 | S1.2:868、869 |
| `ASS 那个期刊` | **ACS 期刊** | S1.2 | S1.2:1350 |
| `JS 文章` | **JACS**（美国化学会志）| S4 | S4:2266、2874——⚠️ 推断 |
| `GCP 上` | GCP 期刊（或指新版论文所在期刊）| S3 | S3:3113–3114——（疑）|
| `皮老师`（第 2 篇文献作者称呼）| 存疑（讲义对应 PNAS 2017, 114(8), 1795-1800）| S1.2 | S1.2:867——（疑）无法确证 |
| `无能累过程` | **无（势）垒过程**（疑）| S1.2 | S1.2:1457——（疑）|
| `令` / `是 is` 类碎片（语音切分错误）| 无法确定，不解读 | S2 | S2 多处；**不要试图解码** |

### 3.11 特别标注：一词两义 / 跨天混记 / 化学式歧义（**旧表踩过的坑，逐条留证**）

1. **`postcard` 一词两义（S1.2 同一段内指两个不同文件）**——机械解码必错：
   - `S1.2:65`："这里是 postcard **结构文件**" → **POSCAR**；
   - `S1.2:66–67`："postcard 是**验试**"（= 赝势）→ **POTCAR**；
   - `S1.2:29` 同时列出 `postcard` 与 `podcar`（= POTCAR）。
   - 其它文件的 `postcard` 也多为 **POSCAR**：`S1.1:2542–2543`（"VASP 必须用 postcard 这个格式"）、
     `S3:2416`（"原子坐标在那个 postcard 文件里面一起读进去的"）、`S5:2828`（`postcard 杠 FS` = `POSCAR_FS`）、
     `S5:3532`（"postcard 在 postcard 里面…在这个结构里面"）。
   - **结论：见到 `postcard` 必须先看上下文是"结构"还是"赝势"，不能一律当 POTCAR。**
2. **`差（点）/ 差点` = 插点，只在"讲插点"的语境出现**：
   - `S4`（NEB 全段，14 处）：203、204、226、338、339、425、618、655、661、664、665、671、729、971；
   - `S5` **PMF 插点段**同样用"差点"：`S5:2735–2737`（"这个差点的过程…用这个 neb make 这个脚本去差点"）、
     `S5:3007–3008`（"非常取决于我们差点的这个密度"）；
   - 而 **`S1.1` 里"差"全是正常词**：174（差分）、546（求差）、1627（差不多）、1822（差出去）、1975（偏差）；
   - `S3:123`（"差点比雷 to"）也**不是**插点，是解压上下文。
   - **结论：`差点`=插点只在 S4/S5 的插点语境成立；旧表把它写成全课程通用映射，属跨天混记。**
3. **`军方位1` = MSD 出现在 `S2`，不在 `S1.1`**：
   - S2 命中 7 处：1067、1094、1177、1232、1283、1463、1492（`军方位1` 本词形在 `S2:1492`）；
   - `S1.1` 全文无"军方位1/均方位"字样（只有正常词"差"等）。
   - **结论：拿"军方位1"去 `S1.1` 里找证据必然找不到——不是笔记造假。**
4. **`二氧化碳` 在字幕里多数指 TiO₂**（化学式歧义，最危险的一类）：
   - `S5:2024`（"二氧化碳的公函稍微大一点"）、`S5:2028`、`S5:2036` → **TiO₂**（讲 g-C₃N₄/TiO₂ 异质结的功函数）；
   - `S5:3898`（"解离成二氧化碳和水分子"）→ **真 CO₂**（H₂CO₃ → H₂O + CO₂ 的 metadynamics 例）；
   - **`S1.1:2073`（"它模拟二氧化碳表面上金20团簇……负载的一个动态变化的一个过程"）→ TiO₂**
     （⚠️ **2026-09 新增/更正**：该句是**语音识别错字**——"二氧化钛"被听成"二氧化碳"，钛 tài / 碳 tàn；
     同一段里 `AIMD`→`AAMD`、`晶胞`→`金包/精包`，可证是纯转写；
     **决定性依据**是讲义 `L1.txt` **PAGE 66**："完美的 **TiO₂** 表面上 **Ti** 和 **Au** 没有化学键作用，
     但是在有缺陷的 TiO₂ 表面上，Au₂₀ 金字塔结构坍塌，形成 **Ti-Au** 化学键。*J. Am. Chem. Soc.* 2013, 135 (29), 10673-83."
     ——含 **Ti–Au** 键 ⇒ 载体含 Ti；仓库自带真实算例 `h_tutorials/cases/TiO2-Au20_cp2k.inp` 同案。
     ⇒ **第一轮内化曾把它写成"CO₂ 表面"，第二轮视频精读又误推成"CeO₂"，两者都不对**，
     正确是 **TiO₂**；`course_learned.md §1.8` 与 `course_notes.md §D` 已按此更正）；
   - `S5:1331`（"表面是**二氧化式**体系"、"四价式变成三价式"、F 轨道）→ **CeO₂**；
   - `S5:2117–2124`（"**二氧化石**表面靠近氧的这个位置它更红"、"二氧化硫、二氧化室里面的势"）→ **CeO₂**
     （同一页讲义 `L4.txt:777–779` 明写"受阻路易斯酸碱对…… **Ce 是亲电位点，O 是亲核位点**"）；
   - `S5:1583`（"氧化锆、**氧化钠**、**氧化土**…非还原性载体"）→ 对照讲义 L4 P39"ZrO₂ HfO₂ ThO₂ 表面氧缺陷"，
     实为 **HfO₂ / ThO₂**；
   - `S1.2:709、715`（"二氧化式"）→ TiO₂；`S3:3828`（"精22氧化碳表面"）→ ZrO₂ 或 TiO₂(110)（疑）。
   - **结论：看到"二氧化碳/二氧化式/氧化钠"必须先判体系，别当化学式照抄。**
5. **三个易被"望文生义"的专名**（旧表口径正确，此处补行号）：
   - `courage 反应` = **Grotthuss 反应**（质子接力传递）—— `S1.1:1992`；
   - `无赖算法` = **Verlet 算法**（速度形式）—— `S1.1:1488–1489`、`S1.1:1572`；
   - `刀` = **氘（D）** —— `S1.1:1799`、`S1.1:1804`、`S1.1:1815`；`S1.2:227`、`S1.2:885–886`。
6. **`north hover` ≠ `north ho 夫`**：前者是 **Nosé–Hoover 热浴**（S1.1/S1.2/S4），
   后者是 **Nørskov**（人名，`S4:3891、3895`）。同音不同义，切勿合并。
7. **旧表里 3 条"查无实据"的词形**（保留正确映射，但**不要拿它们去字幕里找证据**）：
   `2MSD`、`二点 MSD`（实际作 `RMSD`，`S2:1270–1280`）、`多点`（实际说法是"差点这个差的不是特别的密"，`S5:3008`）、
   `2 d data play`（S5 讲 VESTA 切面时的用词是 `letis plan`，`S5:646`）。
   这三条是旧版**抽样**阶段的产物，属"笔记里有、字幕里无"——本次照实标注，不再当成硬结论。

8. **ASR 专名"推定还原"清单（2026-10 复核：依据=音近 + 上下文/化学式；标注置信度）**

   上一轮遗留了若干只有"（疑）"的专名。逐条复核后，以下几条**可以由音近 + 上下文定案**，
   不必再挂着"疑"（但仍**不作为讲师原话引用**，写法用"转写作 X，应为 Y"）：

   | 字幕转写 | 应为 | 依据 | 置信度 |
   |---|---|---|---|
   | `离者磷硫` | **锂锗磷硫 = Li₁₀GeP₂S₁₂** | 音近（lǐ-zhě-lín-liú ← 锂锗磷硫）+ 它是公认的锂超离子导体，与该段"锂电池固态电解质 Li 迁移"语境完全吻合 | **高** |
   | `无能累过程` | **无能垒过程**（barrierless） | 累/垒同音 lěi；且该段正当讲"过渡态是否存在"，与"没有过渡态的情形"直接对应 | **高** |
   | `矩阵的系统` | **巨正则系综**（grand canonical） | 音近（jù-zhèn-de ≈ jù-zhèng-zé）+ 该处在枚举 CP2K 的 `ENSEMBLE` 取值，巨正则正是系综名 | **高** |
   | `JS 文章` | **JACS**（*J. Am. Chem. Soc.*） | 课程引用的顶级期刊以 JACS 为主，多处文献均标 JACS | 中高 |
   | `氧化控线` | **氧空位** | 该段讲"非还原性载体 / 表面氧缺陷"，语义吻合（音近程度一般） | 中 |
   | `SBQ` / `奥卡 offer` | **ORCA** | 同句在列举"同样有 BSSE 的量化程序"，ORCA 在列 | 中 |
   | `ALA` | **ADF** | 同上（讲师原话是"包括高斯、ADF 等等这些程序"） | 中 |
   | `CSIS 这个库` | 疑 **ASE**（次选 `cclib`） | 语境是"用 Python 库读轨迹参数"，ASE 是读 XYZ/轨迹的事实标准；讲师此处有"这，呃"的回忆停顿。详见 `course_notes.md` 的复核条目 | 中 |

   > ⚠️ **仍不足以定案的**（保留"（疑）"，不要升级）：`皮老师`、`GCP 上`（期刊名）、`rip 等号`、
   > `AMISON 配发的脚本`、`六连本`、`item 这模块`、`400 个得拜`、`cp two k 杠半的点 out`、
   > `氧化室`、`精22氧化碳`、`氨气分子`。这类要么是画面里才有的信息（需回看视频），
   > 要么是讲师口误/环境噪声，**不要凭音近硬猜**。

   > ✅ **复核后确认"不是错误"的一条**：字幕里的 `1×10 的十次方` 指 **1E-10**，
   > 与官方 `&QS EPS_DEFAULT` 的默认值 **`1.0E-10`** 一致（查证：`python _kw_probe.py FORCE_EVAL/DFT/QS/EPS_DEFAULT`）
   > ——讲师说得对，只是口语说法绕。

9. **Cu/水固液界面算例：晶面与水分子数 —— ✅ 已定案（2026-10，用真实交付文件）**：
   - **晶面 = `Cu(100)`**（(111) 已被排除）
     - 讲义幻灯片题注"练习一：**Cu(100)** + 46H₂O"（`L2.txt` P61、`L3.txt:1059`，并写"2. 切 **100** 面"）；
       字幕 `S2.txt:4156`"第一步是需要把这个铜的这个 slab **100表面**给它建出来"、`S2.txt:4167`"去切他的这个 **100表面**"。
     - **决定性证据（真实交付输入卡）**：`cu100-h2o-opt/cp2k.inp` 与 `cu100-h2o-aimd/cp2k.inp` **都是**
       `ABC 10.242489 10.242489 …` + `ALPHA_BETA_GAMMA 90 90 90` ⇒ **面内是正方胞（a = b、γ = 90°）**。
       而 **Cu(111) 的面胞必为六方（γ = 60°/120°）**，正交化后也只能得到 `a × a√3`，**不可能 a = b 且 γ = 90°**
       ⇒ **(111) 被排除**。目录名 `cu100-h2o-*` 亦为 (100)。
     - ⇒ 字幕 `S2.txt:4152` 的"**同幺幺**表面"（= 铜 111）是**讲师口误** —— 他**同一段话里紧接着就改口**说"100 表面"。
     - ⚠️ **推翻原"几何旁证（倾向 (111)）"**：那条说"`10.2239 Å` 只有 (111) 4×4 对得上，因为 Cu(100) 面点阵 = `a`
       ⇒ 3×3 = 10.845、4×4 = 14.46"。**前提就错了**：MS/VESTA 切出的 Cu(100) 面是**素胞**，边长 `a/√2 = 2.556 Å`
       ⇒ **4×4 = 10.224 Å ✓**。更要紧的是 **Cu(100) 素胞与 Cu(111) 面胞的最近邻间距同为 `a/√2`**，
       所以 **`10.22 Å` 这个数根本不能区分两面** —— 该"旁证"从一开始就不成立。
   - **水分子数：讲义与 opt 文件都是 `46`；AIMD 实跑是 `28`**
     - 讲义题注：`L2.txt` P61 "Cu(100) + **46**H₂O"（`L3.txt:1059` 同）。
     - **实测随课发文件**（数元素可得）：

       | 文件 | 组成 | 总原子 |
       |---|---|---|
       | `cu100-h2o-opt/Layer.xyz`、`.../coord.inc` | 48 Cu + **46** H₂O | **186** |
       | `cu100-h2o-aimd/coord.inc`、`.../cp2k-pos-1.xyz` | 48 Cu + **28** H₂O | **132** |

     - ⇒ **46** 与讲义题注、"186 原子单点"完全吻合；**AIMD 实跑文件里是 28 个水**。H/O 计数比恰为 2.0（水都完好）。
     - **口述的 64/46/30 怎么解释**：**46 属实**；**64 与"同幺幺表面"同出一句口误**（`S2.txt`:4152–4153）；
       **30 是建模演示中的口述**（`S2.txt`:4214"给它挪个 30 个水分子吧"），而**最终 AIMD 交付文件是 28 个**。
     - ⚠️ **Cu 层数 = 3 层**：48 Cu = 4×4 × **3 层**（旧文/字幕说"切 4 个原子层"与文件不符）。
     - 🔒 这两个组成已钉进 `_validate_real_data.py` 的真实数据回归，改动会被测出来。

10. **第二轮视频精读（`videonotes/`）的三处"连带误推"——不要采用**（**2026-09 新增**）：
    第二轮的 6 份录屏精读笔记质量很高，但它**不是权威层**：当它与 E 层（`L*.txt`/`S*.txt`）冲突时**一律以 E 层为准**。
    本轮已查出并否决的三处（正文均已加防错注）：
    - **Au₂₀ 的载体**：`videonotes/cp2k-1-1-...` 写 **CeO₂** ⇒ **错，实为 TiO₂**（讲义 `L1.txt` P66 的 Ti-Au 键；见本条 §3.11 第 4 条与 `course_learned.md §1.8`）；
    - **Al 掺杂的氧化物**：`videonotes/cp2k-5-...` 写 **CeO₂ 掺 Al** ⇒ **错，实为 TiO₂ 掺 Al**
      （`S5.txt:1353`"本来这是个**二氧化钛**的这个体系"、`S5.txt:1354–1360`"把这个**钛**换成了铝……钛有四个价电子、铝有三个"）；
    - **`.hills` 的列数**：`videonotes/cp2k-5-...` 整理成 **5 列** ⇒ **不完整**，讲义 `L5.txt:814` 的数据行是 **6 个数**
      （`25.0 4.19568 5.71958 0.30000 0.30000 0.00300`，第 6 个 = 峰高）⇒ **仍按 6 列**。
    > 另外提醒：`videonotes/cp2k-2-...` 曾把锂固态电解质判成 **Li₄SiO₄** ⇒ 该判读已被 §3.11 第 8 条的
    > `离者磷硫 = Li₁₀GeP₂S₁₂`（置信度**高**）否决，**以知识库为准**。

## 4. 字幕 vs 讲义：互补关系

- **PDF 讲义**：结构化、有公式和图，但缺"演示操作细节 + 学员问答 + 踩坑现场"。
- **字幕独有高价值信息**（每条给字幕行号）：
  1. **后处理工具操作流**：VMD 算 RDF **必须加 PBC**、配位数要**球面积分（4πr²，不是直接面积分）**
     （`S2:304–336`）、MSD 要**"先平方再平均"**（VMD 输出的是 √MSD/RMSD，`S2:1267–1522`，
     讲师当场承认 PPT 写错）；TRAVIS 控制文件怎么写（`S5:123–265`）；VESTA 做电荷差分 / ELF 切片（`S5:557–722`）。
  2. **脚本名（按天列全，旧版漏了第 1 天）**：
     - 第 1 天（上/下）：`sub_cp2k`（超算 `bin` 里的提交脚本）、**`find_my_job`（讲师自写，看任务运行情况，
       `S1.1:2639–2646`）**、`xdat2xyz.pl`（VTST，`S1.2:1123–1126`）、`md_simplify.py`（抽帧，
       VASP/CP2K 通用，`S1.2:1182`）、VMD"六行 PBC 脚本"（`S1.2:1239–1274`）、Win+G 录屏（`S1.2:1356–1367`）。
     - 第 2 天：VASPKIT 功能号 **722/727/728/804**、Packmol、MS 的 Amorphous Cell / Cleave Surface / Build Layers。
     - 第 3 天：**`demcar2xyz.py`**（`.car`→xyz，`-s` 按 Z 重排，`S3:2510–2606`）、`cp2k.vim` 语法插件。
     - 第 4 天：**`xyz2neb.pl`**、**`cp2k_frequency.pl`**（末位 0=全实频/1=有虚频）、
       **`cp2k_frequency_to_movie`**（出 9 个振动 movie）、**`max_center.py`**（质心分析，约 67 行）、
       **`zdis_trajectory.py`**（元素 Z 分布，输出 `distance_H`/`distance_O`）、`md_simplify.py`。
     - 第 5 天：**`cube.py`**（平面平均）、**`gaussian.py`**（画自由能面，VASP/CP2K 通用）、
       **`new.py`**（官网 PDOS 展宽）、`neb_movie`、`nebmake.pl`。
  3. **参数经验（手册没有的"为什么"）**：OT vs 对角化对金属的取舍（`S3:1587–1694`、`S4:3365–3370`）；
     **DFT+U 对 TM 氧化物不加会定性错误**（`S1.2:653–759`、`S4:4244–4262`）；
     轨迹抽帧存盘与"原始 position 必须存档"（`S4:2094–2126`、`S4:3134–3139`）。
  4. **建模实操**：用 `include` 读坐标 + 改晶胞边界套模板；原子顺序可重排（`demcar2xyz.py -s`，`S3:2814–2901`）；
     建模八类的完整配方（`S2:3062–4401`）。
  5. **学员常见坑**：
     - MSD：PPT 原写"先平均再平方"是错的，应"先平方再平均"（讲师当场承认更正，`S2:1441–1522`）。
     - RDF 不加 PBC 不准（`S2:100–132` 讲的是**反过来**：跟踪单键键长时不能加 PBC）。
     - VASP 结构优化后 CONTCAR 末块是速度、会被置零（`S1.2:653–759`）。
     - DFT+U 的 U 值忘了写 `[eV]` → 默认 a.u.，差约 27 倍（`S4:4219–4237`）。
- **更正（2026-10）：BSSE 不属于"字幕独有"**。旧版本节把 **BSSE** 列为字幕独有高价值信息之一，**这是错的**：
  BSSE 的权威出处是**讲义 `L2.txt` P33 + `L3.txt` P40–P42**（另有字幕 `S2:2972–3019`、
  `S3:140–169`、`S3:2343–2345` 的讲师口径），详见 `decide.md §28.2`。
  （§2 第 4 天条目下就地保留的更正记录同时有效，二者一致。）
  同一条目下旧版还把"BSSE 让 CP2K 吸附能比 VASP 偏大"当字幕独有——**讲师的原话是定量口径**
  （DZVP 的 BSSE ≈5 kcal/mol ≈0.2 eV，`S3:2284–2345`），引用时请用这个带数字的版本。

## 5. 与 cp2k-aimd skill 现有覆盖对照（**2026-10 更新**）

- skill 已从官方手册内化 `decide.md` 全部分节（结构/GLOBAL/FORCE_EVAL/DFT/SCF/GAPW/CONSTRAINT/MOTION/
  Methods/性质/Post-HF/NEB/振动/COLVAR/PLUMED/力场/QM-MM/XC/VDW/BSSE 等；分节数在本次学习期间仍在扩充，
  引用时请以 `decide.md` 目录为准），并有 `postprocess.py`
  （RDF/MSD/IR/PDOS/bader/fes/travis）、`sections.md`、`workflow.md`、`playbook.md`、
  `gen_inp.py`（含 GAPW/CONSTRAINT/NEB/metadyn 等开关）。
- 本次重新学习后，**课程知识已回灌到各层**（不再是"待办"）：
  1. 字幕原文与讲义抽取文本入库 → `references/pdf_text/S1.1–S5.txt`（E 层，逐字、行号不变）；
  2. 讲义 ↔ 字幕对应表 → `references/pdf_text/MAPPING.md`（§2 页→主题、§3 对应锚点、§4 字幕逐段主题）；
  3. 分层综合稿：`course_learned.md`（B 层）、`course_notes.md`（C 层）、`decide.md`（A 层）、
     `playbook.md`（F 层）、`postprocess.md`（后处理工具流）；
  4. 本文件 §3 错字表补"出处"列——这是本次**最关键的口径修复**。
- **仍然偏弱、值得继续补的点**（供后续迭代）：
  1. `decide.md` 里缺第 1 天的"PBC 与晶胞尺寸选择""多副本随机化与混沌"两块硬经验（`S1.1:1880–2150`）；
  2. `decide.md` 缺"CP2K 不支持 k 点对称性缩减"这条与 VASP 的关键差异（`S3:3994–4123`）；
  3. 自写脚本（`zdis_trajectory.py`、`max_center.py`、`cube.py`、`gaussian.py`）只有文件名与用途，
     没有可运行实现——如需复现要在 `postprocess.py` 里补等价子命令。

## 6. 本次（2026-10）重新学习已执行的动作与产物

> 旧版本节记录的是 2026-07 的首次学习流程（当时只有"产出 course_notes.md + 登记 SKILL.md 索引"）。
> 本节改写为**本次重新学习**的实际动作与产物。

| 动作 | 产物 | 说明 |
|---|---|---|
| ① 字幕入库（逐字、行号不变）| `references/pdf_text/S1.1.txt` … `S5.txt`（6 份 / 22133 行）| `extract_subtitles.py`；带行数 + sha256 溯源清单（`README.md` §1.2）|
| ② 讲义分页抽取 | `references/pdf_text/L1.txt` … `L5.txt`（5 份 / 425 页）| `extract_pdf.py`；页边界 `========== PAGE N ==========` |
| ③ 讲义↔字幕对应表 | `references/pdf_text/MAPPING.md` | `build_mapping.py`（`--check` 校验分段表连续覆盖全文）；含错位说明、页→主题索引、28 条对应锚点、6 份字幕逐段主题表 |
| ④ 素材说明重写 | `references/pdf_text/README.md` | 新增 §3"PDF 序号 ≠ 字幕第 N 天"错位表；明确"讲义是按主题切分的 5 个 deck" |
| ⑤ 6 份逐行精读报告 | `study/_extract/S1_1.md`、`S1_2.md`、`S2.md`、`S3.md`、`S4.md`、`S5.md` | 6 位分析员**逐行**读完（无抽样），每份含"主题分段表 + 实操硬规则 + 工具清单 + 踩坑 + 答疑 + 同音错字 + 与现有笔记的冲突" |
| ⑥【新】条目工单 | `study/_extract/NEW_ITEMS.md`（277 条）| `collect_new_items.py` 自动抽取；每条带报告行号，便于回查 |
| ⑦ 各层回灌 | `course_learned.md`（B）、`course_notes.md`（C）、`decide.md`（A）、`playbook.md`（F）、`postprocess.md` | 按"硬规则→A 层、症状处方→F 层、课程叙事→B 层"的分层规则落点 |
| ⑧**错字表口径修复（本文件）** | 本文件 §3 | 补"出处"列、按主题分组、全部收录；并修 §1 讲义描述、重写 §2 主题流、更正 §4 的 BSSE 归属与脚本清单、更新 §5 覆盖对照、改写本节 |
| ⑨ 文档一致性校验 | `python _doc_consistency.py` | 要求输出 `OK：文档口径全部一致`（另按 `AGENTS.md` §6.2 串行跑 `_validate_postprocess.py`、`_validate_all.py`）|

- 引用规范：讲义写 `L3 P40–P42`；字幕写 `S2.txt:2972–3019`（`MAPPING.md` §5）。
- 维护约定：**发现本文件与原文不符时，以 `L*.txt`/`S*.txt` 原文为准并回来修本文件**。

> **第二轮视频精读（`references/pdf_text/videonotes/`）落层时的 C 层改动（2026-09）**
>
> 本轮的输入是 6 份**录屏精读笔记**（带 `[mm:ss]` 时间戳，与 `S1.1`–`S5` 一一对应），
> 由 B/C 层落层时据此修了本文件以下位置（每一处都带"更正/并列"说明，**没有静默改写**）：
> ① §3.2 `cp2k-band.out` 并列；② §3.3 `SURFACE_DIPOLE_DIRECTION` → **`SURF_DIP_DIR`**；
> ③ §3.3 新增 `SMEARING` → `SMEAR`、`FIXED_Z` → `CONSTRAINT Z`、`U_EFFECTIVE` → `U_MINUS_J`、
> `COUPLING_REGION` → `REGION` 四行；④ §3.3 `INCREM` 行改标为 **VASP 的 `ICRIN`**（并给出 CP2K 的 `TARGET_GROWTH` 对应）；
> ⑤ §3.3 `ICONST` 行补"VASP 文件、非 CP2K 关键字"；⑥ §3.7 `势/式/市/士` 与 `二氧化石/二氧化式` 的
> **CeO₂/TiO₂ 归属**（FLP 页 = CeO₂）；⑦ §3.7 `折100表面` 改 **Si(100)/Ge(100) 并列**；
> ⑧ §3.11 第 4 条补 `S1.1:2073` 的 **TiO₂** 判定（Au₂₀ 载体）；⑨ §3.11 新增第 9 条（Cu 晶面 + 水分子数并列）
> 与第 10 条（`videonotes` 三处必须否决的连带误推）。
> **本文件本轮未改任何"已正确"的结论**；`course_learned.md`（B 层）与 `course_notes.md`（C 层）的改动见各文件正文与
> `course_learned.md` 文末的《第二轮视频精读落层记录》。
