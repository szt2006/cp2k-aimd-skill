# 庚子计算《AIMD 与 CP2K》5 天培训 — 资料梳理报告

> 目录：`D:\石大\化学软件\cp2k\cp2k课程资料_庚子计算 - 副本\讲义和课程视频字幕`
> 梳理时间：2026-07-19
> 目的：先摸清"有什么、对应关系、字幕错字"，再据此学习并内化进 cp2k-aimd skill。

## 0. 一句话结论
目录共 11 个文件：**5 个 PDF 是结构化讲义（PPT 导出），6 个 txt 是视频字幕（语音转写）**。
字幕是 5 天课程完整录音的转写，已按天拆分（第 1 天拆成上下两段）。字幕口语化、含**演示操作细节 / 脚本名 / 学员问答 / 踩坑**，但同音识别有错字（见 §3）。
字幕里大量"讲师实操经验"是 PDF 没有的，正是 skill 缺的那一层——**"怎么真正把 CP2K 跑起来"**。

## 1. 文件清单与对应

| 文件 | 类型 | 规模 | 对应内容 |
|---|---|---|---|
| `1.1.txt` | 字幕 | 2857 行 / 105 KB | 第 1 天（上）：课程总览 + AIMD 基础 + 水盒子例子（CP2K & VASP 各跑一遍）|
| `1.2.txt` | 字幕 | 1532 行 / 55 KB | 第 1 天（下）：作业提交（VASP/vast）、DFT+U、轨迹抽取 `md_simplify.py` |
| `2.txt` | 字幕 | 4546 行 / 163 KB | 第 2 天：水盒子后处理（VMD 看轨迹、RDF、MSD）+ 转入 CP2K |
| `3.txt` | 字幕 | 4142 行 / 162 KB | 第 3 天：CP2K 输入文件全参数（GLOBAL/FORCE_EVAL/DFT/SCF/QS）、OT vs 对角化、建模（cell/include 模板）|
| `4.txt` | 字幕 | 4537 行 / 166 KB | 第 4 天：过渡态/NEB、AIMD 频率、表面氧化实例、BSSE 与基组、Au20 团簇 |
| `5.txt` | 字幕 | 4519 行 / 162 KB | 第 5 天：电子结构（ELF/PDOS/电荷差分）、振动光谱（TRAVIS 算 IR/Raman/VCD）、自由能面（伞采样/slow growth/元动力学）|
| `庚子计算-AIMD与CP2K讲义-1~5.pdf` | 讲义 | 2.8 / 2.6 / 9.5 / 5.7 / 1.9 MB | 对应 5 天的 PPT 讲义（结构化、有公式与图）|

## 2. 五天课程主题流（基于字幕抽样定位）

- **Day 1（上，1.1）**：5 天大纲 → AIMD 是什么/为什么重要 → 最简单例子：建水盒子、用 CP2K 和 VASP 各跑一遍。
- **Day 1（下，1.2）**：作业提交（`vast` 命令、`to delete`/`s cancel` 杀任务）→ 与 VASP 输入（INCAR/KPOINTS/POTCAR）对比 → **DFT+U 对过渡金属氧化物的必要性**（不加会定性错误）→ 轨迹文件太大 → `md_simplify.py` 每 10~20 步抽一帧。
- **Day 2（2.txt）**：水盒子后处理——VMD 导入轨迹、**加周期性边界条件**、算 **RDF（对关联函数）**、算 **MSD（均方位移）→ 扩散系数**、配位数（RDF 第一峰球面积分）、Origin 拟合 → 然后正式进入 CP2K 课程。
- **Day 3（3.txt）**：CP2K 输入文件逐段讲——GLOBAL、FORCE_EVAL、DFT（&MGRID/&XC/&POISSON/&KPOINTS）、SCF（对角化 vs OT、DIIS、EPS_SCF）、QS、&SUBSYS（&CELL/&COORD/&KIND）→ 建模实操：用 `include` 读坐标、改晶胞边界、套模板。
- **Day 4（4.txt）**：过渡态搜索（NEB，"珠子+弹簧"、CI-NEB）→ AIMD 频率计算（`frequency_to_movie` 出 9 个振动模式动画，第 1 个是虚频）→ 表面氧化实例（Cu 氧化）→ **BSSE：CP2K 高斯基组有 BSSE，高估吸附/结合能；平面波 VASP 无 BSSE** → 基组讨论 → Au20 团簇稳定性（质心-原子距离，需自写 ~67 行 Python）。
- **Day 5（5.txt）**：电子结构分析——**ELF**（共价/离子、三中心两电子键）、**PDOS/d-band**、**电荷差分**（VESTA：total−CO−metal，黄=增、蓝青=减）→ 振动光谱：**TRAVIS** 联用算 IR/拉曼/VCD/ROA（VASP 只能算 VDOS 不含偶极）→ 自由能面：PMF（伞采样，精度依赖插点密度）→ slow growth（缓慢变 CV、平均 λ 梯度）→ metadynamics（自适应填面）。

## 3. 字幕识别同音错字对照表（精读前必看）

| 字幕原文 | 正确含义 | 备注 |
|---|---|---|
| cp two k / c b two k / cp to k / CPUK / CPTOK / cp to qu | **CP2K** | 程序名 |
| VSP / vast | **VASP** | 平面波第一性原理程序 |
| AAMD / AIAMD | **AIMD**（从头算分子动力学）| |
| postcard / podcar | **POTCAR** | VASP 势文件 |
| 验室 / 验尸 | **赝势**（pseudopotential）| |
| 机组 / 记录文件 | **基组**（basis set）| |
| 京弯 / 金包 / 精包 | **晶胞**（cell）| |
| 军方位1 / 均方位移 | **MSD**（均方位移）| |
| 2MSD / 二点 MSD | **√MSD** | VMD 输出的是带根号的 MSD |
| 风 | **峰**（peak）| 如"三个风"=三个峰 |
| 差（点）/ 差点 | **插（点）/ 插点** | NEB 线性插点 |
| 多点 | **密点** | 插点密度 |
| 飞艇 | **fitting** | Origin 拟合 |
| BSS 1 / BSS E / BSS E 5差 | **BSSE**（基组叠加误差）| |
| 镜像分布函数 / 进项分布函数 | **径向分布函数 RDF**（对关联函数）| |
| 二氧化石 | **二氧化钛（TiO₂）** | 表面 |
| 棚材料 | **硼材料**（boron）| 二维硼 |
| 三中心两电子键 | three-center two-electron bond | |
| 电子化合物 | electrides | |
| 解力吸附 | **解离吸附**（dissociative adsorption）| |
| 电商 | **电荷**（charge）| 电荷差分 |
| 解出 | **CO**（吸附质）| 电荷差分 total−CO−metal |
| 总 / 解出(后两项) | total / CO / metal | 电荷差分三项 |
| 进二 | **金20（Au20）** | 团簇 |
| 金字塔形 | 金字塔形（pyramidal）| Au20 结构 |
| 质心到原子 | centroid-to-atom | 稳定性分析 |
| max center / masc | **max_center.py** | 质心分析脚本 |
| PM 、 F | **PMF**（伞采样）| 自由能三法之一 |
| METDYNAMICS / metadyn | **metadynamics**（元动力学）| |
| slow growth / SLOGOUSE | slow growth（缓慢增长）| |
| 限制AAMD | 限制性 AIMD | |
| 自由能势能面 | free energy surface (FES) | |
| ELF / ERF | **ELF**（电子局域函数）| |
| letis plan | lattice plane（VESTA 切面）| |
| 2 d data play | 2D data plane | |
| angle 这篇文章 | a paper / an article | 泛指文献 |

## 4. 字幕 vs 讲义：互补关系

- **PDF 讲义**：结构化、有公式和图，但缺"演示操作细节 + 学员问答 + 踩坑现场"。
- **字幕独有高价值信息**：
  1. **后处理工具操作流**：VMD 算 RDF **必须加 PBC**、配位数要**球面积分**（不是直接面积分）、MSD 要**"先平方再平均"**（VMD 输出的是 √MSD）；TRAVIS 控制文件怎么写；VESTA 做电荷差分 / ELF 切片。
  2. **脚本名**：`md_simplify.py`、`frequency_to_movie`、`max_center.py`（质心分析）。
  3. **参数经验（手册没有的"为什么"）**：OT vs 对角化对金属的取舍；**DFT+U 对 TM 氧化物不加会定性错误**；**BSSE 让 CP2K 吸附能比 VASP 偏大**；轨迹抽帧存盘。
  4. **建模实操**：用 `include` 读坐标 + 改晶胞边界套模板；原子顺序可重排（`DEMCAR -s`）。
  5. **学员常见坑**：
     - MSD：PPT 原写"先平均再平方"是错的，应"先平方再平均"（讲师当场承认更正）。
     - RDF 不加 PBC 不准。
     - VASP 结构优化后 CONTCAR 末块是速度、会被置零的小 bug。

## 5. 与 cp2k-aimd skill 现有覆盖对照

- skill 已从官方手册内化 `decide.md` §1–§27（结构/GLOBAL/FORCE_EVAL/DFT/SCF/GAPW/CONSTRAINT/MOTION/Methods/性质/Post-HF/NEB/振动/COLVAR/PLUMED/力场/QM-MM/XC/VDW），并有 `postprocess.py`（RDF/MSD/IR/PDOS/bader/fes/travis）、`decide.md`、`sections.md`、`workflow.md`、`gen_inp.py`（含 GAPW/CONSTRAINT/NEB/metadyn 等开关）。
- 字幕补的是 **"实操经验层"**，skill 目前偏弱的点：
  1. DFT+U 的"必须加"硬经验（TM 氧化物）→ 应进 `decide.md` 方法选择。
  2. BSSE 警示（高斯基组 vs 平面波）→ 应进 `decide.md` 吸附能/基组判读。
  3. 后处理"工具操作细节 + 常见坑"（VMD 球面积分、MSD 平方再平均、PBC）→ 进 `postprocess.md` / `course_notes.md`。
  4. NEB / 自由能三法 / ELF / 电荷差分的"讲师直觉" → 进 `course_notes.md`。

## 6. 本次"学习"已执行的动作

- 产出 `references/course_notes.md`：把字幕里的实操经验、脚本、坑、参数经验按主题沉淀，交叉引用 `decide.md` 章节。
- 在 SKILL.md 文件索引登记 `course_survey.md` 与 `course_notes.md`。
- 后续可选项：把 `course_notes.md` 中 B1（DFT+U）、B2（BSSE）两条硬规则**提升进 `decide.md` 方法选择/吸附能判读章节**（需再读 decide.md，避免误改）。
