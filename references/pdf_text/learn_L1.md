# 庚子计算《AIMD 与 CP2K》第 1 天 — 全面学习笔记（learn_L1）

> 来源：
> - PDF 讲义：`references/pdf_text/L1.txt`（共 83 页，含 83 个 `========== PAGE N ==========` 标记；全文逐页提取）
> - 视频字幕：`1.1.txt`（2857 行，上）、`1.2.txt`（1532 行，下），逐行通读
> - 已有笔记：`course_notes.md`、`course_survey.md`（用于交叉比对，避免重复，标注缺失）
> 说明：公式与表格尽量**原文照抄**。文末附「PDF 页码覆盖清单」与「course_notes.md 未收录新内容清单」。
> 【新】= 该内容在 course_notes.md 中尚未收录（经比对确认）。

---

## 0. 课程总览（Day 1 定位）【新】

PDF 大纲（P2）+ 字幕（1.1）给出五天安排。第 1 天只讲 **AIMD 基础 + VASP 跑 AIMD + 后处理**；第 2 天起才深入 CP2K。第 1 天主讲人：刘锦程。

> 字幕补充（1.1）：课程资料含 5 个 PPT，第 3 个 PDF（CP2K 参数详解）最核心，要用 2 天讲；第 1/2/4/5 各约 1 天。超算账号为「SC50209」，约 10 月 1 日关闭，**不要在其上跑科研任务**；练习须建立在超算 `work` 目录下自己的文件夹里（避免搞乱上百学员的共享环境）。

**五天大纲（P2）**
- 9/26：量子化学/第一性原理/分子动力学基本知识；AIMD 基本知识；VASP 做 AIMD 的参数设置；AIMD 后处理分析
- 9/27：CP2K 编译/简介；复杂模型建模；CP2K 计算流程与参数详解
- 9/28：CP2K 基组、赝势、坐标读入；输出文件；几何优化/晶胞优化；过渡态搜索
- 9/29：CP2K 频率计算；AIMD 详解；DFT+U、磁性、杂化泛函；文献计算案例重复
- 9/30：电子结构分析（电荷密度/差分/原子电荷/态密度/ELF/分子轨道/静电势/功函）；限制性 AIMD 与自由能势能面；PMF、Metadynamics

**必须安装的本地软件（字幕 1.1）**：VMD（必装，后处理主力）、VESTA（"west"，必装）、Jmol（建议装，看轨迹方便）。建模用 Materials Studio（MS）、Packmol（"派克膜"）。Windows 自带 Win+G 游戏录屏可录 VMD 动画。

---

## 1. 势能面、驻点与结构优化基础【新】

### 1.1 势能面上的特殊点（P4）
- 驻点（Stationary point）：所有原子梯度模都为 0 的结构。极大点、极小点、鞍点都属于驻点。
- 极小点（局部极小）、极大点（局部/全局极大）、全局极小点、拐点、过渡态（一阶鞍点）。

### 1.2 驻点 / 极小点 / 过渡态 的数学定义（P5–P6）
**驻点（P5）**：对任意原子 A
$$F_A = -\frac{\partial E(R_1,R_2,\dots,R_N)}{\partial R_A} = 0$$
能量对坐标的一阶导数都为 0 ⇒ 受力为 0。极大点、极小点、鞍点都属于驻点。

**极小点（Minimum，P5）**：对任意 A
$$F_A = -\frac{\partial E}{\partial R_A}=0,\quad \frac{\partial^2 E}{\partial R_A\partial R_B} > 0$$
能量对坐标的二阶导数都大于 0；任何微调都会使能量升高。

**全局极小点**：势能面上能量最低的点。搜索是计算科学大课题（模拟退火、CALYPSO、USPEX、SSW 等程序）。【新】（文献程序名）

**过渡态 = 一阶鞍点（Saddle point，P6）**：
$$F_A=0,\quad \frac{\partial^2 E}{\partial R_A\partial R_B} < 0\;(\text{某方向}),\quad \frac{\partial^2 E}{\partial R_A\partial R_B}>0\;(\text{其余方向})$$
在虚频方向上移动结构能量下降，其余方向上升。**有且只有一个虚频**即一阶鞍点。

### 1.3 IRC 内禀反应坐标（P7）
- 最小能量路径（MEP）：质权坐标下连续两个相邻极小点的最小能量路径。
- **VASP 没有自带 IRC 功能，需外接 ASE 包计算 IRC**。【新】

### 1.4 电子步与离子步（P8）【新】
- 每个黄色点 = 一个离子步；离子步内做 SCF（自洽场）迭代，SCF 中每一步 = 一个电子步。
- 流程：构建 Fock 矩阵 → 对角化 Fock 矩阵、解出系数矩阵 C → SCF 收敛后算原子受力 → 按算法移动原子坐标到势能面下一点（离子步）→ 新结构再 SCF… 直到所有原子受力 < |EDIFFG|。

### 1.5 单点能 / 结构优化 / 过渡态搜索（P9–P11）【新】
- 单点能（single point）：只算势能面上一个点的能量。
- 结构优化（geometry optimization）：从初始结构找到局部能量极小点（local minimum）。
- 过渡态搜索：也是结构优化，但优化到一阶鞍点；**结束后需计算能量二阶导数（频率计算）**确认虚频。

### 1.6 分子动力学模拟（P11）【新】
- MD = 在势能面上原子核以牛顿运动方程不断演化（黄色曲线的运动路径）。

---

## 2. AIMD 计算基本流程（P13）【新】

```
初始结构，初始速度
   ↓
DFT 计算原子受力
   ↓
更新原子位置、速度
   ↓
应用周期性边界条件、控温、控压技术
   ↓
输出感兴趣的量、更新时间
   ↓
判断结束条件 → 输出汇总
```

字幕（1.1）补充：初始结构对 AIMD 不重要（随便给、具随机性即可；而结构优化/过渡态会落在离初始结构最近的驻点）；初始速度必须给定（F=ma ⇒ 加速度；据初始速度+受力演化）。可人为加限制：控温、控压、PBC、限定键长/键角等。

---

## 3. 相空间、统计平均与系综（P14–P18）【新】

### 3.1 相空间（P14）
- 经典力学中 N 粒子体系状态用动量 p 和坐标 r 描述，皆 3N 维矢量，构成 **6N 维相空间**。
- 微观态 ↔ 相空间一点；任意性质可标记为 $A[p(t), r(t)]$。
- MD 通过对相空间取系综平均（时间平均 + 副本平均）获得物理/化学性质。

### 3.2 宏观量计算（P15）
- 对模拟时间平均（时间越长采样越充分）；对多个模拟副本平均（副本越多越精确）。
- 遍历性（ergodic）假设：无限长时间体系可遍历所有微观态。

### 3.3 常见系综（P16）
| 符号 | 含义 |
|---|---|
| NVT | 正则系综（Canonical ensemble）|
| NVE | 微正则系综（Microcanonical ensemble）|
| NPT | 等温等压系综 |
| μVT | 巨正则系综（Grand canonical ensemble）|

- N=粒子数，V=体积，T=温度，E=能量，P=压力，μ=化学势。
- 经典 MD 最常用 NPT；但 **AIMD 原子数有限 ⇒ 压力剧烈涨落、不易控压**，故 AIMD 最常用 **NVT 或 NVE**。

### 3.4 NVE 系综总能（P17）
- NVE 系综总能不变（通过 DFT 计算得到）。

---

## 4. 牛顿运动方程与 Verlet 算法（P18–P20）

### 4.1 牛顿运动方程（P18）【新】
- 加速度 = 能量一阶导数；原子受力通过 DFT 计算得到；原子质量 m。
- 即 $F = ma$（a = 加速度）。

### 4.2 速度形式的 Verlet 算法（P19）【新】
1. 规定初始位置（t 时刻）：R(t)
2. 规定初始速度（t 时刻）：V(t)
3. 计算第 n 步受力（t 时刻）：F(t)（DFT 得到）
4. 计算第 n+1 步位置（t+Δt）
5. 计算第 n+1 步受力（t+Δt）：F(t+Δt)（DFT）
6. 计算第 n+1 步速度（t+Δt）

> 字幕（1.1）关键修正：速度更新用的是 **(F(t)+F(t+Δt))/2** 的平均力，再除以质量得加速度 ⇒ ΔV = a·Δt；位置更新 $R(t+\Delta t) = R(t) + V(t)\Delta t + \frac12 a\Delta t^2$。讲师当场纠正把 $\frac12 a$ 误说成 $\frac12 ma$。

### 4.3 AIMD 关键参数（P20）
- SCF 收敛精度、时间步长、总步数、温度、控温方式、感兴趣的信息输出。
- **速度瓶颈在 SCF 收敛**。示例：平均一个 SCF 需 50 s，时间步长 1 fs ⇒ 一天可跑 1728 步 ≈ 1.7 ps；完成 30 ps 约需 **17 天**。

---

## 5. 时间步长选择（P21–P22）

### 5.1 总则（P21）
- 动力学总时间 = 时间步长 × 步数。
- 步长太小 ⇒ 步数多、浪费时间；太大 ⇒ 精度损失甚至模拟崩溃。

| 范围 | 取值 |
|---|---|
| 太短 | ~0.1 fs |
| 合适 | 0.5 ~ 2 fs |
| 太长 | ~5 fs |

### 5.2 经验准则（P22）【新】
- 可接受极限 ≈ 系统最快运动周期的 **<1/10**，一般取 **1/20** 较合适。
- 例：水分子 O–H 伸缩振动 3300–3600 cm⁻¹，周期约 **10 fs** ⇒ 1/10 = 1 fs，1/20 = 0.5 fs。文献含 H 的 AIMD 步长多在 **0.5 fs**。
- 技巧：用**氘（D）取代氢**。O–D 振动约 2500 cm⁻¹ ⇒ 可用更大步长。例：PNAS 2017, 114(8), 1795-1800 模拟 D₂O 用 **1.2 fs**。

---

## 6. 参数测试（P23）【新】

AIMD 每个离子步 SCF 极耗时，大规模计算前须仔细测试参数、选最快方式。

| 测试项 | CP2K | VASP |
|---|---|---|
| PRECONDITIONER | FULL_SINGLE_INVERSE / FULL_ALL | NCORE = 10 |
| MINIMIZER | CG / DIIS / BROYDEN | ALGO = Veryfast 或 Normal |
| 其他 | （OT/对角化） | KPAR = 1，ISMEAR = 1 或 0，ENCUT，KPOINTS |

- 无带隙/带隙很小的体系（如石墨烯类）需测试 OT 与 diag（对角化）方法。

---

## 7. AIMD 的重复性问题（P24–P26）

- MD 是混沌体系（蝴蝶效应）；浮点精度差异即使不用随机数，两次模拟结果也可能不同。
- 单次模拟可能落小概率事件 ⇒ 错误结论。**较可信做法：多次模拟、统计平均**（审稿人也常默认通过）。
- 如何保证多路径随机（P25）：CP2K 初始速度随机；初始坐标可自编随机数处理；Anderson 热浴引入随机数，Nose-Hoover 不用随机数。非平衡过程（单向化学碰撞）可限定初始速度/坐标。
- 例（P26）：作者模拟 **100 条 AIMD**，分析出 5 种反应路径并统计；文献 J. Am. Chem. Soc. 2016, 138(35), 11164-9。

---

## 8. Energy drift 问题（P27）【新】

- NVE 系综总能理论不变，但模拟误差（过长步长、过松 SCF 阈值）引起 drift。
- 示例（SCF 收敛阈值 EPS_SCF）：

| EPS_SCF | 现象 |
|---|---|
| 1E-4 | Energy drift 严重 |
| 1E-5 | 300 ps 后明显 |
| 1E-6 / 1E-7 | 几乎没有 |

> 字幕（1.1）强调：EPS_SCF 不能太大（如 1E-4 → total energy 失控产生 drift），一般取 **1E-5 左右**；又不能太高（如 1E-7 太慢），需精度与耗时折中。

---

## 9. 周期性边界条件 PBC（P28–P29）【新】

- PBC 假定宏观体系由盒子无限平移延展产生；粒子跨边界从反向回到晶胞。
- 为避免原子与自身相互作用，范德华作用、高斯基组等以原子为中心的作用要 **< 盒子边长**。
- 盒子边长合适（> 6 Å，P29）：太大浪费计算量；太小则与其镜像作用、模拟失败。

> 字幕（1.2/1.1）补充实例：模拟 TiO₂ 上 Au20 团簇，2×2 晶胞因团簇与镜像太近会吸成纳米棒/纳米饼（失真）；4×4 太费；Au20 用 3×3 合理，Au55 需更大。原则是"观察对象 + 想看的现象"决定晶胞大小。

---

## 10. 动能与温度（P30）【新】

- AIMD 温度取决于动能：

$$K = \sum_i \frac{P_i^2}{2m_i} = \frac{N_c}{2}k_B T$$

- N = 总原子数；Nc = 被约束的自由度数；Pi = 第 i 个原子动量；mi = 质量。
- 例：固定最下层 10 个原子的体系，Nc = 30（48 个原子 - 3×6 = 30 自由度）。
- 自由、孤立体系：粒子平均动能 $\frac{3}{2}k_BT$（每自由度 $\frac12 k_BT$）。

---

## 11. 控温技术 / 热浴（P31–P37）

### 11.1 总论（P31）【新】
- NVT/NPT：温度在目标附近涨落（粒子越少涨落越明显）。热浴在温度高时降动能、低时升动能。
- **NVE 不与外界换热 ⇒ 不能用热浴**（动能↔势能交换，温度不可控）。

### 11.2 Maxwell–Boltzmann 分布（P32）【新】
- 衡量热浴好坏的关键指标，也是设置 MD 初始速度的标准。

### 11.3 退火 Annealing（P33）【新】
- 源于固体退火：加温至充分高 → 徐徐冷却。是一种基于概率、寻找全局极小值的方法。
- MD 中：把体系从低温慢慢提高到一定温度再做采样；一般"变温模拟"都叫退火。

### 11.4 速度调节法（P34）
- 对所有粒子统一乘校正因子，强行拉回目标温度；可每步或每几步校正。
- 缺点：人为太强、不符合 Maxwell 分布，**采样时不能用**，但预平衡/升温可用。
- CP2K 有改良版：**CSVR** 热浴（基于速度调节 + 引入随机变量，使速度更符合 Maxwell 分布）。【新】

### 11.5 Anderson 热浴（P35）
- 每隔一定步数随机选一个粒子，将其速度设为参考温度下 Maxwell 分布随机值（等效随机碰撞）。也可 Massive 法一次性把所有原子调成 Maxwell 分布。
- 优点：速度分布符合 Maxwell。缺点：人为性强、轨迹不平滑。
- 文献：Anderson J. Chem. Phys., 72, 2384 (1980)。

### 11.6 Nosé–Hoover 热浴（P36）
- 目前 AIMD 最常用。把热浴当作体系一部分，赋参数 Q（虚拟质量）随体系演化；Q 越大耦合越弱、温度波动频率越低。
- VASP 通过 **SMASS** 控制 Q；CP2K 通过 **TIMECON** 控制 Q。

> 注：P37 为空白页（仅页眉），无内容。

---

## 12. 水盒子建模（MS Amorphous cell）（P38–P41）【新】

- 第 1 天练习：含水盒子建模 → CP2K 与 VASP 各跑一遍。
- 建模步骤（P39–P40，Materials Studio）：
  1. 新建非周期性模型，构建一个 H₂O 分子。
  2. 新建 **Amorphous cell** 任务（construction），选中水分子 Add，修改数量；密度 **1 g/cm³**；Specify a,b,c 边长 **10.2425 Å**（MS 自动判断 c 方向长度）。
  3. 运行约 1 分钟 ⇒ 得到 `Molecule.xtd`；用 In-Cell 显示 lattice。

### CP2K 平衡态任务提交所需文件（P41）
| 文件 | 作用 |
|---|---|
| cp2k.inp | CP2K 输入文件 |
| BASIS_MOLOPT | 基组文件 |
| POTENTIAL | 赝势文件 |
| water.cif | 结构文件（xyz/cif/pdb 等）|
| sub_cp2k | 提交脚本 |
| dftd3.dat | DFT-D3 校正参数（其他如力场文件）|
| 计算案例文件夹 | `./h2o` |

> 字幕（1.1）补充：cif 是晶体/表面/周期性常用格式，含晶胞三向量 + 三角度（α,β,γ）。CP2K 输入结构格式自由（XYZ/CIF/PDB 均可）；VASP 必须用自有 POSCAR 格式。坐标可用 VESTA 打开。

---

## 13. VASP 做 AIMD 的参数详解（P42–P50）【核心·新】

### 13.1 平衡态模拟参数（P42）
> 前提：编译 VASP 时加了 `-Dtbdyn`（VASP 5.4+ 自动添加）才能用热浴和高级采样。

| 参数 | 值 | 含义 |
|---|---|---|
| 总模拟时间 | = NSW × POTIM | |
| POTIM | 2 | 时间步长（fs）|
| NSW | 100000 | 总步数（设大些没关系，可随时终止）|
| SMASS | 0 | 控制系综/热浴 |
| MDALGO | 2 | 控制热浴 |
| TEBEG | 600 | 初始温度 |
| TEEND | 600 | 末尾温度 |
| NBLOCK | 1 | 每多少步写一次 XDATCAR/CONTCAR |
| KBLOCK | 50 | NBLOCK×KBLOCK 步写一次 PCDAT/DOSCAR |
| POMASS | — | 调整原子质量 |

### 13.2 SMASS 控制系综/热浴（P43）【新】
| SMASS | 系综 / 热浴 |
|---|---|
| -3 | NVE 系综（microcanonical）|
| -1 | NVT，速度调节法热浴，每 NBLOCK 步调节（一般用于退火）|
| ≥ 0 | NVT，Nose-Hoover 热浴 |

- 字幕重点：SMASS=0 对应约 40 个步长的震荡周期（POTIM=1 fs 时温度约 40 fs 波动一次），对含高频振动（如 H ~3000 cm⁻¹）体系合理；若热浴温度振动周期与体系最高频率差一个数量级以上 ⇒ decouple 问题，取 SMASS=0 即可。
- 从 VASP 源码看，该参数量纲为 **[能量×时间²]**，设置难度高。
- 全重原子（无 H/He/Li）频率小，SMASS 可适当调大（如模拟液态 Si）。

### 13.3 MDALGO 控制热浴（P44）【新】
> 仅当编译加 `-Dtbdyn`（5.4+ 自动）可用；是 VASP 做 AIMD 的"灵魂参数"。

| MDALGO | 热浴 |
|---|---|
| 0 | 默认，NVE 系综 |
| 1 | Andersen 热浴（ANDERSEN_PROB 控制碰撞概率，保持默认）|
| 2 | Nose-Hoover（须 SMASS ≥ 0；不设 MDALGO 但 SMASS≥0 也等同）|
| 3 | Langevin 热浴（NVT 或 NPT）|

### 13.4 AIMD 平衡态模拟一般步骤（P45）
1. 优化结构（初始结构合理可省略）。
2. 模拟退火升温 100 K → 目标温度；NVT，速度调节法（SMASS=-1）。
3. 目标温度平衡几 ps；NVT/NVE/NPT，Nose-Hoover 或 Andersen。
4. 特定温度模拟足够长时间（分析用，一般 >10 ps，可与第 3 步合并）。
- 非平衡态（如快速化学过程）可能在升温中已反应 ⇒ 可省略第 2 步。

### 13.5 INCAR 模板【新】

**退火升温（P46）**
```
##### I/O #####        #### Elec Relax ####     #### MD ####
SYSTEM = Au            ENCUT = 400             NSW = 5000
#KPAR = 4              ISMEAR = 0              POTIM = 2
NCORE = 12             SIGMA = 0.05            SMASS = -1
ISTART = 1             EDIFF = 1E-6            TEBEG = 100
ICHARG = 1             NELMIN = 5              TEEND = 1400
LWAVE = .FALSE.        NELM = 300              NBLOCK = 20
LCHARG = .FALSE.       GGA = PE                # MDALGO = 2
LVTOT = .FALSE.        LREAL = Auto
LVHAR = .FALSE.        ISYM = 0
LELF = .FALSE.
#LORBIT = 11
```
> 不要保存电荷密度和波函数；不要限制对称性 ISYM=0。时间步长 2 fs，共 5000 步 = 10000 fs，100 K→1400 K，每 20 步调节温度。

**平衡态（P47）**
```
##### I/O #####        #### Elec Relax ####     #### MD ####
SYSTEM = Au            ENCUT = 400             NSW = 100000
#KPAR = 4              ISMEAR = 0              POTIM = 2
NCORE = 12             SIGMA = 0.05            SMASS = 0
ISTART = 1             EDIFF = 1E-6            MDALGO = 2
ICHARG = 1             NELMIN = 5              TEBEG = 1400
LWAVE = .FALSE.        NELM = 300              TEEND = 1400
LCHARG = .FALSE.       GGA = PE                # NBLOCK = 1
LVTOT = .FALSE.        LREAL = Auto
LVHAR = .FALSE.        ISYM = 0
LELF = .FALSE.
#LORBIT = 11
```
> 读上一个 MD 的 CONTCAR；NSW 尽量大；一般 Nose-Hoover SMASS=0 或按 OUTCAR 值调大。TEBEG=TEEND，NBLOCK=1，每步保存轨迹。

### 13.6 其他参数注意事项（P48）【新】
- **KPOINTS**：用 `1 1 1`；用 vasp_gam 版本可大幅加速。
- **赝势**：用价电子数最少的默认赝势（加速）。
- **表面偶极校正**：最好不加（减慢 SCF 收敛）。
- **范德华校正（DFT-D3）**：可加，几乎不增耗时。
- **复杂磁性体系**（反铁磁/亚铁磁）：非专门研究磁性时可用**铁磁**代替（牺牲极小精度换速度）。
- **过渡金属氧化物**：**DFT+U 最好设置**（虽减慢 SCF，但不加会引起定性错误）。
- **用结构优化的 CONTCAR 作初始结构**：一定要**删除最后的速度信息**，否则初始速度为 0。

### 13.7 案例文献解析（P49–P50）【新】
- **Chem. Mater. 2012, 24, 15−17**（Li₁₀GeP₂S₁₂ 锂离子迁移）：第二步升温 100 K→(600–1500 K)，速度调节法，共 2 ps；第三步达目标温度后 NVT Nose-Hoover 平衡 5 ps，再同参数继续 40 ps，步长 2 fs。
- **PNAS 2017, 114(8), 1795-1800**（固液界面电催化）：步长 **1.2 fs**，H 质量设为 2（D₂O）；速度调节法每 20 步调温到目标；NVT Nose-Hoover，热浴温度波动 100 fs 一周期。

---

## 14. AIMD 后处理分析（P51–P82）

### 14.1 练习一：VASP 计算 16H₂O 盒子（P52）【新】
- 密度 1 g/cm³ 水盒子（MS Amorphous cell）。
- 步骤：①优化结构（省略）；②退火升温 100 K→300 K，SMASS=-1，2000 步；③复制 CONTCAR 为新 POSCAR，300 K 模拟 20 ps（20000 步 × 1 fs = 20 ps，前 5 ps 弃作平衡），NVT Nose-Hoover。

| 第二步（退火）| 第三步（平衡）|
|---|---|
| NSW=2000, POTIM=1, SMASS=-1 | NSW=20000, POTIM=1, SMASS=0 |
| TEBEG=100, TEEND=300, NBLOCK=20 | TEBEG=300, TEEND=300, NBLOCK=1 |

> 计算案例文件夹：`./h2o-vasp`。

### 14.2 轨迹查看（P53）【新】
- 查看工具：Jmol（最方便）、MS、VMD（功能最强）。
- VASP 轨迹存于 `XDATCAR`；先用 **xdat2xyz.pl**（VTST 脚本）转成 `movie.xyz`。
- 再用 **mdsimplify.py + [整数]** 每间隔 N 点保存一帧 ⇒ `newpos.xyz`。例：每 20 点取一帧：`mdsimplify.py 20`。
  > ⚠️ 歧义/不一致：PDF P53 写的是 `mdsimplify.py`，字幕 1.2 与其脚本名为 `md simplify 点 PY`（`md_simplify.py`），course_notes.md 记为 `md_simplify.py`。**两处命名不一致，实际操作以字幕/notes 的 `md_simplify.py` 为准**（通用 CP2K/VASP）。

### 14.3 VMD 图像调整（P54）【新】
- 轨迹操作：创建/删除新轨迹、设定显示范围、效果叠加、周期性、当前 Rep 等。
- Graphics → Representations：设定原子选择、着色、绘制风格、材质。

### 14.4 VMD 常用命令（P55）【新】
- Selected Atoms 关键词：`name`(原子名)、`all`、`element`(元素名)、`none`、`index`(0 开始)、`noh`(除 H)、`serial`(1 开始)。
- 设定 PBC（边长从 POSCAR 读）：
```
pbc set {7.820 7.821 7.823} -all
pbc box
pbc wrap -all
```
- 改善画质：
```
display depthcue off
color Display Background white
display rendermode GLSL
File – Render – Tachyon (internal, in-memory rendering)
```
- Win10 自带游戏录屏：Win+G 录动画。

### 14.5 键长/键角/二面角跟踪（P56–P58）【新】
- Mouse → Label（bonds, Angles, Dihedral）标记。
- Graphics → Labels 检视详细信息并可作图。
- 适用于研究化学反应进程（如 N₂ 加氢：J. Phys. Chem. A 2018, 122(18), 4530-4537；质子链传递：JACS 2016, 138(6), 1816-9；JACS 2016, 138(35), 11164-9）。

### 14.6 势能涨落（P59–P62）【新】
- VASP 的 `REPORT` 存 MD 总结；看能量用 `OSZICAR` 更清晰：
```
grep = OSZICAR > energy.txt   # 注：PDF 原文如此；实际应为 grep 过滤 OSZICAR
```
- OSZICAR 每行字段：①当前步数 ②T 温度 ③E 总能(动能+势能+热浴能) ④F 和 E0 是势能（一般取 **E0**，Sigma 外推到 0 的能量）⑤EK 动能 ⑥SP 热浴势能 ⑦SK 热浴动能。
- 总能有微小 Energy drift 一般不管；势能在区间震荡平衡 ⇒ 体系达平衡态；统计时忽略前几 ps。
- 不少文章以"模拟一段时间结构不垮塌 + 势能稳定"作材料稳定判据（此法不严格）：JACS 2018, 140(43), 14161-14168；类似 J. Phys. Chem. C 2019, 123(31), 19066-19076；JACS 2016, 138(17), 5644-5651。

### 14.7 径向分布函数 RDF（P63–P68）
- RDF（对关联函数）：相距参考粒子 r 处粒子密度 g(r)，无穷远处为 1。参考粒子在原点 O，平均密度 ρ = N/V，距 O 为 r 处平均密度 = ρ·g(r)。
- VASP 自身可算 RDF（参数 APACO/NPACO），但不方便。
- VMD 操作（P64）：Extensions → analysis → RDF；设晶胞参数、选轨迹、选原子对、设起止帧、最大 r、横纵坐标取点密度、保存文件到 Origin 再画图。
- 应用（P65）：水中 O–H 距离 ~0.99 Å，氢键中 O···H 距离 ~1.73 Å；第一配位层 2.00 个 H（形成两个氢键），第二配位层 3.97 个 H。
- 应用（P66–P67）：完美 TiO₂ 表面 Ti-Au 无化学键，有缺陷 TiO₂ 表面 Au₂₀ 金字塔坍塌形成 Ti-Au 键（JACS 2013, 135(29), 10673-83）；CO 吸附 Au 上，C-Au 键不断、Au-Au 不断断裂再生（JACS 2013, 135(29), 10673-83）。
- **VMD 算 RDF 只能处理正交晶胞**（P68）：先旋转晶格矢量变正交（如石墨用 Build → symmetry → Redefine lattice）；做 AIMD 尽量用正交晶系方便分析。

### 14.8 速度自相关函数 VACF（P69–P71）【新】
- VACF 描述某时刻速度与另一时刻速度的关联，自变量为关联时间 t；尖括号为系综平均。0 时刻与 t 时刻接近 ⇒ 关联强、点乘大；远离 ⇒ 弱。
- 以轨迹上所有点（不只第一个）为参照计算自相关；振动越慢 VACF 越平缓。
- VASP 求 VACF：VASP 不输出每步速度，只能对相邻坐标差/时间步长求速度。脚本 **xdat2vdat.pl**；更方便的是 **Qijing Zheng 写的 vacf.py**（修改脚本末尾原子对）：
```
python3 vacf.py
```
  输出 `pcf.png`(RDF)、`pdos.png`(IR 光谱)、`vacf.png`(速度相关函数)。

### 14.9 红外光谱（P72）【新】
- 对 VACF 做傅里叶变换（FFT）⇒ Vibrational DOS（IR 光谱）。仍用 **vacf.py**。
- 例：300 K 水的 IR 光谱（VACF-FFT 计算值 vs 实验值对比图）。

### 14.10 练习二：VASP 计算 Li₁₀GeP₂S₁₂ 锂离子迁移（P73–P74）【新】
- 电极材料 Li⁺ 嵌入脱出速度决定倍率性能；AIMD 可模拟 Li⁺ 扩散常数（NEB 也可得）。文献 Chem. Mater. 2012, 24, 15−17。
- 步骤：①优化结构；②退火升温 100 K→(600/800/1000/1200/1400 K)；③80 ps AIMD，用最后 60 ps 分析。

| 退火升温 | 平衡态模拟 |
|---|---|
| NSW=5000, POTIM=2, SMASS=-1 | NSW=40000, POTIM=2, SMASS=0 |
| TEBEG=100, TEEND=1400, NBLOCK=20 | MDALGO=2, TEBEG=1400, TEEND=1400 |

### 14.11 均方位移 MSD（P75–P78）
- MSD = 相对于参考位置的粒子位置随时间变化度量；可算 3D、1D 或 2D。
- VMD 算的是 **RMSD（Root Mean Square Displacement）**，对其平方 ⇒ MSD。
  > ⚠️ 重要更正（与 course_notes.md 一致）：VMD 输出的是 **√MSD（带根号）**；要得 MSD 须"**先平方、再跨参考帧平均**"。PPT 原写"先平均再平方"被学员指出后现场更正为"先平方再平均"。
- VMD 操作（P76）：Extensions → analysis → RMSD Trajectory Tool；选原子/元素、参考第***帧、忽略前***帧、画图/保存、删除/添加轨迹。
- 因逐帧取平均极慢且卡死 VMD，取 **0, 500, 1000, 1500, 2000 帧** 为参考点取 RMSD，平均后再平方得 MSD（P78）。

### 14.12 扩散系数（P79–P80）
- MD 求扩散常数两法；常用 **Einstein 公式**：
$$D = \frac{\text{MSD 斜率}}{2d},\quad d=\text{维度}$$
- 3 维 d=3 ⇒ **D = MSD 斜率 / 6**。模拟时间越长越准。
- 另一法：基于 VACF 的 Green-Kubo 关系（不方便）。
- 数据表（P80，Li₁₀GeP₂S₁₂ 不同温度）：

| T/K | 1000/T | MSD (A²/ps) | D (A²/ps) | D (cm²/s) | log(D) |
|---|---|---|---|---|---|
| 600 | 1.666667 | 0.44461 | 0.0741017 | 7.41017E-06 | -5.13017 |
| 800 | 1.25 | 1.03847 | 0.1730783 | 1.73078E-05 | -4.76176 |
| 1000 | 1.0 | 2.18712 | 0.36452 | 3.6452E-05 | -4.43828 |
| 1200 | 0.833333 | 3.61754 | 0.6029233 | 6.02923E-05 | -4.21974 |
| 1400 | 0.714286 | 4.3699 | 0.7283167 | 7.28317E-05 | -4.13768 |

### 14.13 阿伦尼乌斯公式求迁移能垒（P81）【新】
- 扩散系数与能垒满足阿伦尼乌斯公式：
$$\log(D)\ \text{vs}\ 1000/T\ \text{斜率} = -\frac{E_a}{2.303\,k_B}$$
- 本例：截距 -3.35865，斜率 -1.07871；$k_B = 8.6173\times10^{-5}$ eV ⇒
$$E_a = 0.2141\ \text{eV}$$

### 14.14 VMD 同时显示多帧结构（P82）【新】
- Graphics → Representation → Trajectory → Create Rep 建新图层（如 name Li）。
- Draw Multiple Frames：`b:s:e`（b=初始帧，s=间隔，e=终止帧）展示体系运动状态。

---

## 15. 字幕独有实操补充（仅字幕有，PDF 无）【新·核心】

以下为视频字幕（1.1 / 1.2）包含的实操细节，PDF 讲义中没有，正是 skill 缺的"怎么真正跑起来"一层。

### 15.1 超算环境与作业提交（1.1）
- **并行桌面（ParaCloud/"变形桌面"）**：账号 SC50209，北京 A 分区；首次用需在账号添加超算名 + 上传证书。或用 **SSH / Xshell** 登录。
- 登录后先建自己文件夹（在 `work` 目录下，用自己的名字命名）；**不要建到别处**（上百学员共享）。
- 传文件：WinSCP（左右拖）、`rz` 上传、`sz` 下载。
- **module 系统**：`module load cp2k` 加载编译好的程序（国内大型超算一般都有；LM、GROMACS、NAMD、GCC、Python 等开源免费程序基本都配好；收费程序如 VASP 可私问管理员）。
- 提交任务：`qsub sub_cp2k` 或 `sbatch sub_cp2k`；查状态 `qstat`/`squeue`；杀任务 `qdelete`/`scancel`/`to delete`/`s cancel`。
- 讲师自用脚本 `find_my_job` 看任务运行情况。
- 提交后服务器小 bug：该分区提交后约等 **12 分钟** 才输出内容；输出主要为 `cp2k.out` 等。

### 15.2 CP2K 任务提交实操（1.1）
- 需准备文件：`water.cif`（结构）、`cp2k.inp`（输入）、`BASIS_MOLOPT`（基组）、`POTENTIAL`（赝势）、`dftd3.dat`（可选）、`sub_cp2k`（提交脚本，从 `bin` 目录 `cp` 过来）。
- `sub_cp2k` 内含 `module load cp2k` + `srun -n 64`（64 核）。
- 提交后 `tail -f cp2k.out` 跟踪输出。
- **输出文件**：轨迹默认存为 **`.xyz`** 文件（`cp2k-pos-1.xyz`），格式三部分 = ①原子数（第一行）②注释（第二行，含 I=步数、时间、E=势能）③原子坐标；能量/温度变化在 **`cp2k-energy`**（supercell 的 energy 文件，字幕口误为 "super create energy"）中。
- VMD/Jmol 看轨迹：Jmol 免安装（装 Java 即可），File→动画 loop；VMD 功能强但操作复杂。

### 15.3 VASP 任务提交实操（1.2）
- VASP 输入 **四个文件**：`INCAR`（参数）、`KPOINTS`（倒空间撒点，此处用伽马点）、`POSCAR`（结构）、`POTCAR`（赝势）+ 提交脚本 `sub_vasp`（从 `bin` 复制）。
- 文件夹结构：`step-1`（退火升温）、`step-2`（平衡态模拟）。
- 提交：`qsub sub_vasp`；`qstat` 看 R(运行)/C(结束或死掉)。
- 输出：`OUTCAR`（含 SMASS 默认值，可 `grep SMASS` 捕捉）、`OSZICAR`、`XDATCAR`（轨迹）。
- **VASP 小 bug（重要）**：结构优化后 `CONTCAR` 末尾有一段速度信息且全为 0；若直接复制成 POSCAR 做 AIMD，**初始速度为 0（相当于 0 K 开始）**，务必删掉末尾速度块。
- 轨迹后处理：`xdat2xyz.pl`（VTST）→ `movie.xyz` → `md_simplify.py 20` → `newpos.xyz`（每 20 步抽一帧，2 万帧→1000 帧）。**注意文件路径不能有中文**（VMD 导入会出错）。
- VMD 加 PBC 命令（与 PDF P55 一致）：`pbc set {7.82 ...} -all`、`pbc box`、`pbc wrap -all`；显示美化：`display depthcue off`、`color Display Background white`、`display rendermode GLSL`；Graphics→Representation 用 VDW + dynamic bond 图层（dynamic bond 比 CPK 好，断键后不乱连）；关掉透视。
- 录制动画：Win+G 游戏录屏（选中 VMD 窗口）；VMD 自身也可导出视频但讲师认为不如 Win10 自带好用。Jmol 导 GIF 需用 console 命令行，麻烦。
- **Langevin 热浴**（MDALGO=3）主要用于 NPT；NPT 压力难控（粒子数少时），故少用；用 Langevin 时 SMASS 不用设。

### 15.4 从文献 computational method 还原参数（1.2）
- 读文章 `computational method` 即可推断 INCAR：
  - "heated to ... K"、"velocity rescaling" ⇒ SMASS=-1 退火；
  - "constant volume" + Nose-Hoover ⇒ NVT（SMASS≥0, MDALGO=2）；
  - "time step" ⇒ POTIM；"hydrogen mass set to 2" ⇒ POMASS 或赝势文件里 `POMASS`；
  - "gamma point" ⇒ 1×1×1 K 点；"no symmetry" ⇒ ISYM=0；
  - "temperature damping parameter 100 fs" ⇒ SMASS 被调大（默认 40 fs/次）。
- 文献 1：Li₁₀GeP₂S₁₂（Chem. Mater. 2012, 24, 15−17）：initial 100 K，升温至 600–1500 K，velocity rescaling 2 ps，NVT Nose-Hoover 40 ps（前 5 ps 弃）。
- 文献 2：固液界面（PNAS 2017, 114(8), 1795-1800）：time step 1.2 fs，H mass=2（D₂O），gamma point，ISYM=0，velocity rescaling 预平衡，Nose-Hoover，damping 100 fs。

### 15.5 DFT+U 对过渡金属氧化物的必要性（1.2，亦见 course_notes B1）
- 强关联 TM 化合物（TiO₂、Fe₃O₄ 等）：**不加 U 会定性错误**——电子不能局域在金属离子上，四价 Ti 不被还原，表面吸附物电子转移模拟不对。虽减速也要加。后续会用 TiO₂ 演示"不加 U 电子不局域"。

### 15.6 其他字幕坑点（1.2）
- 初始结构搭太差（如 O-H 键仅 0.5 Å）会一上来"炸掉"（温度飙升到几万度）→ 先结构优化 10 步 8 步把不合理短键/结构"撑开"，不要求优化到极小。
- AIMD 一切参数设定理念 = **牺牲小部分精度换计算速度**（与静态计算"牺牲速度换精度"相反）。
- 磁性体系当铁磁处理，能量差别仅 ~0.0x eV，但 SCF 收敛快得多。

---

## 16. 软件 / 工具 / 脚本名汇总【新】

| 名称 | 类型 | 作用 | 出现处 |
|---|---|---|---|
| CP2K | 程序 | 混合高斯基组+平面波（GPW），AIMD/DFT | 全篇/1.1 |
| VASP | 程序 | 平面波 AIMD/DFT | 全篇 |
| GPW | 方法 | Gaussian+Plane Wave 混合基组（核附近高斯、核间平面波）| 1.1 |
| VMD | 程序 | 轨迹查看/后处理主力 | P53-55,82 / 1.2 |
| VESTA（"west"）| 程序 | 看 cif/电荷差分/ELF | 1.1 |
| Jmol | 程序 | 看轨迹（方便）| P53 / 1.2 |
| Materials Studio（MS）| 程序 | 建模（Amorphous cell）| P39-40 |
| Packmol（"派克膜"）| 程序 | 建模（填充盒子）| 1.1 |
| TRAVIS | 程序 | 第 5 天：IR/Raman/VCD/ROA | survey |
| Plumed | 程序 | 自由能面（metadynamics）| survey |
| ASE | 程序 | 外接 IRC、建模 | P7 |
| DPMD（深度势能）| 程序 | 机器学习势函数（AIMD+ML）| 1.1 |
| xdat2xyz.pl | 脚本(VTST) | XDATCAR→movie.xyz | P53 / 1.2 |
| mdsimplify.py / md_simplify.py | 脚本 | 轨迹抽帧（每 N 步一帧）| P53 / 1.2 / notes |
| xdat2vdat.pl | 脚本 | XDATCAR→速度 | P71 |
| vacf.py（Qijing Zheng）| 脚本 | VACF/vDOS/RDF 输出 png | P71-72 |
| frequency_to_movie | 脚本 | 频率→振动动画（第 4 天）| notes |
| max_center.py | 脚本 | Au20 质心-原子距离（第 4 天）| notes |
| sub_cp2k / sub_vasp | 脚本 | 作业提交（bin 目录）| 1.1/1.2 |
| find_my_job | 脚本 | 查任务运行状态 | 1.1 |

---

## 17. 文献 / 作者索引【新】

| 文献 | 主题 |
|---|---|
| 第一篇 AIMD（1987, LDA，Si(100) 表面重构）| AIMD 起源 |
| PNAS 2017, 114(8), 1795-1800 | D₂O 步长 1.2 fs，固液界面 |
| JACS 2016, 138(35), 11164-9 | 100 条 AIMD 统计质子链传递路径 |
| JACS 2016, 138(6), 1816-9 | 质子链传递 |
| J. Phys. Chem. A 2018, 122(18), 4530-4537 | N₂ 加氢反应 |
| JACS 2018, 140(43), 14161-14168 | 材料稳定判据（AIMD 不垮塌）|
| J. Phys. Chem. C 2019, 123(31), 19066-19076 | 类似稳定判据 |
| JACS 2016, 138(17), 5644-5651 | 类似稳定判据 |
| JACS 2013, 135(29), 10673-83 | TiO₂ 上 Au₂₀ / CO on Au |
| Chem. Mater. 2012, 24, 15−17 | Li₁₀GeP₂S₁₂ 锂离子迁移 |
| Anderson J. Chem. Phys., 72, 2384 (1980) | Anderson 热浴 |
| Nature 2019 | 二氧化硅载体铁催化剂（建模简化案例）|
| 全局极小搜索程序 | CALYPSO、USPEX、SSW |

---

## 18. 幻灯片关键图描述（即使无法提取图，注明每页讲了什么图）【新】

| 页 | 图内容 |
|---|---|
| P4 | 势能面示意图：极大/极小/过渡态/鞍点/拐点标注 |
| P7 | 过渡态 + 最小能量路径 IRC 连线两个极小点 |
| P8 | 电子步/离子步流程图（黄色点=离子步，内含 SCF 电子步）|
| P9/P11 | 势能面上不同演化路径（单点能点、结构优化曲线、MD 黄色运动曲线）|
| P10 | 过渡态搜索示意（优化到一阶鞍点）|
| P12 | 结构优化 vs 分子动力学 对比（空图占位）|
| P13 | AIMD 计算流程图（6 框循环）|
| P14 | 相空间 6N 维示意 |
| P16 | 系综 NVT/NVE/NPT/μVT 定义 |
| P17 | NVE 总能不变曲线 |
| P21 | 时间步长三种情况对比（太短/合适/太长）|
| P27 | Energy drift 三条曲线（EPS_SCF 1E-4/1E-5/1E-6）|
| P29 | 盒子边长太小/太大对比 |
| P30 | 动能-温度公式示意 |
| P33 | 退火温度-时间曲线 |
| P34 | 速度调节法温度-时间曲线（每 20 步校正）|
| P35 | Anderson 热浴平滑/不平滑轨迹对比 |
| P36 | Nose-Hoover 耦合强弱温度波动对比 |
| P39-40 | MS Amorphous cell 建水盒子界面截图 |
| P52 | VASP 16H₂O 两步 INCAR 参数块截图 |
| P53 | VMD/Jmol 轨迹查看界面 |
| P54 | VMD Representation 设置面板 |
| P56-57 | Label bonds/angles 标记 + Labels 作图 |
| P59 | OSZICAR 能量字段说明 |
| P60 | 势能震荡平衡图 |
| P63 | RDF 定义示意图（参考粒子 O，密度 ρ·g(r)）|
| P65 | 水 RDF 第一/第二配位层峰（O-H ~0.99 Å, H-bond O···H ~1.73 Å）|
| P66-67 | TiO₂-Au / CO-Au RDF 应用 |
| P68 | 正交晶胞重定义示意 |
| P70 | VACF 典型图像（振动慢则平缓）|
| P72 | 300 K 水 IR 光谱（计算 vs 实验）|
| P75 | MSD 定义示意（参考位置 vs t 时刻位置）|
| P77 | 不同温度（600–1400 K）RMSD 曲线 |
| P80 | MSD 斜率→D 数据图 |
| P82 | VMD 多帧显示（Draw Multiple Frames b:s:e）|

---

## 19. 与字幕交叉对照小结

- PDF 每个主要主题（势能面、AIMD 流程、系综、Verlet、时间步长、PBC、热浴、水盒子、VASP 参数、SMASS/MDALGO、INCAR 模板、RDF、VACF、MSD、扩散系数、阿伦尼乌斯）**字幕均覆盖**，且字幕在以下方面做了补充/更正：
  - 现场纠错：Verlet 速度更新公式 $\frac12 a$（非 $\frac12 ma$）；PPT"先平均再平方"→"先平方再平均"。
  - 实操层：超算环境、module load、qsub/scancel、find_my_job、sz/rz、CP2K/VASP 输出文件格式、xyz 三部分结构、CONTCAR 速度置零 bug、VESTA 开 cif。
  - 参数理念：AIMD"牺牲精度换速度" vs 静态"牺牲速度换精度"；SMASS 量纲[能量×时间²]；磁性当铁磁处理。
- **仅字幕有、PDF 无**的实操补充（见 §15）：超算作业提交全流程、CP2K/VASP 文件清单与提交脚本、文献 computational method 还原法、DFT+U 对 TM 氧化物的必要性（TiO₂ 演示预告）、VASP CONTCAR bug、多参考帧 MSD 平均技巧、md_simplify.py 抽帧、xdat2vdat.pl / vacf.py / xdat2xyz.pl 脚本、CSVR 热浴、Langevin 主要用于 NPT、GPW 原理解释、DPMD 机器学习势。

---

## 20. course_notes.md 尚未收录的新内容清单【新】

经比对 course_notes.md（仅覆盖 RDF 球面积分、MSD 平方再平均、频率动画、ELF/电荷差分/PDOS、FES 三法、DFT+U、BSSE、OT vs 对角化、md_simplify 抽帧、建模 include、实例索引），以下 Day 1 内容**notes 未收录**，建议后续补入 skill：

1. **势能面/驻点数学定义与公式**（F=−∂E/∂R=0；极小点/过渡态二阶导数判据；IRC 需 ASE）— P4–P7
2. **电子步/离子步、单点能、结构优化、过渡态搜索概念** — P8–P11
3. **AIMD 基本流程图、相空间 6N 维、系综定义（NVT/NVE/NPT/μVT）** — P13–P16
4. **牛顿方程 F=ma、速度 Verlet 算法 6 步（含平均力求速度）** — P18–P19
5. **时间步长选择准则**（1/10~1/20 最快周期；O-H ~10 fs ⇒ 0.5 fs；D₂O 1.2 fs）— P21–P22
6. **参数测试表**（CP2K PRECONDITIONER/MINIMIZER vs VASP NCORE/KPAR/ALGO）— P23
7. **重复性问题**（混沌、100 条模拟、Anderson 引入随机数 vs Nose-Hoover 不引入）— P24–P26
8. **Energy drift 与 EPS_SCF 关系**（1E-4/1E-5/1E-6）— P27
9. **PBC 盒子边长 >6 Å、TiO₂-Au20 晶胞大小实例** — P28–P29
10. **动能-温度公式** $K=\sum P_i^2/2m_i=(N_c/2)k_BT$ — P30
11. **控温全谱系**：速度调节法（采样不可用）、退火、Anderson（轨迹不平滑）、Nose-Hoover（Q/TIMECON）、**CSVR 热浴** — P31–P37
12. **MS Amorphous cell 建水盒子步骤**（密度 1 g/cm³、边长 10.2425 Å）— P39–P40
13. **CP2K 文件清单**（cp2k.inp/BASIS_MOLOPT/POTENTIAL/water.cif/sub_cp2k/dftd3.dat）— P41
14. **VASP AIMD 全套参数**：NSW/POTIM/SMASS/MDALGO/TEBEG/END/NBLOCK/KBLOCK/POMASS；**SMASS 三态表（-3/-1/≥0）、MDALGO 四态表（0/1/2/3）** — P42–P44
15. **AIMD 一般步骤 4 步**、**退火/平衡 INCAR 完整模板**（含 ENCUT=400、SIGMA=0.05、NELMIN=5、ISYM=0 等）— P45–P47
16. **参数注意事项**：KPOINTS 1×1×1 + vasp_gam、价电子最少赝势、偶极校正不加、DFT-D3 可加、磁性当铁磁、CONTCAR 删速度 — P48
17. **两篇案例文献参数还原**（Chem. Mater. 2012；PNAS 2017）— P49–P50
18. **后处理细节**：Jmol/MS/VMD 看轨迹、xdat2xyz.pl、mdsimplify.py；VMD 命令全集（pbc set/box/wrap、display depthcue off 等）、Selected Atoms 关键词；键长键角跟踪；**OSZICAR 7 字段含义 + grep 提取**；势能涨落平衡判据；RDF 仅正交晶胞+Redefine lattice；VACF 定义 + xdat2vdat.pl + vacf.py（pcf/pdos/vacf.png）；IR 由 VACF-FFT；Li₁₀GeP₂S₁₂ 练习参数表 — P51–P74
19. **MSD 多参考帧（0/500/1000/1500/2000）平均法**；**Einstein 公式 D=斜率/6**；**扩散系数数据表**；**阿伦尼乌斯 Ea=0.2141 eV** — P75–P81
20. **VMD 多帧显示 b:s:e** — P82
21. **超算作业提交全流程**（SC50209、work 目录、module load、qsub/scancel、find_my_job、sz/rz、bin 目录 sub 脚本）— 1.1/1.2
22. **CP2K 输出文件**：cp2k.out、cp2k-pos-1.xyz（三部分格式）、cp2k-energy — 1.1
23. **VASP 四文件 + step-1/step-2 + OUTCAR grep SMASS + CONTCAR 速度置零 bug + 中文路径坑** — 1.2
24. **文献 computational method 还原 INCAR 的方法论** — 1.2
25. **GPW 原理（核附近高斯、核间平面波）**、**DPMD 机器学习势** — 1.1
26. **脚本全集**：xdat2vdat.pl、vacf.py(Qijing Zheng)、xdat2xyz.pl(VTST)、sub_cp2k/sub_vasp、find_my_job — 全篇

---

## 21. PDF 页码覆盖清单（确认每页均处理）

| 页 | 主题 | 状态 |
|---|---|---|
| 1 | 版权声明 | ✅ |
| 2 | 五天大纲 | ✅ |
| 3 | AIMD 主讲人/目录 | ✅ |
| 4 | 势能面特殊点 | ✅ |
| 5 | 驻点/极小点公式 | ✅ |
| 6 | 过渡态（一阶鞍点）公式 | ✅ |
| 7 | IRC / ASE | ✅ |
| 8 | 电子步/离子步 | ✅ |
| 9 | 单点能 | ✅ |
| 10 | 过渡态搜索 | ✅ |
| 11 | 分子动力学模拟 | ✅ |
| 12 | 结构优化 vs MD（占位）| ✅ |
| 13 | AIMD 基本流程 | ✅ |
| 14 | 相空间 6N 维 | ✅ |
| 15 | 宏观量计算/遍历性 | ✅ |
| 16 | 常见系综 | ✅ |
| 17 | NVE 总能不变 | ✅ |
| 18 | 牛顿运动方程 | ✅ |
| 19 | 速度 Verlet 算法 | ✅ |
| 20 | AIMD 关键参数/速度瓶颈 | ✅ |
| 21 | 时间步长选择 | ✅ |
| 22 | 时间步长准则/O-H/D₂O | ✅ |
| 23 | 参数测试表 | ✅ |
| 24 | 重复性问题（混沌）| ✅ |
| 25 | 重复性问题（随机性）| ✅ |
| 26 | 100 条 AIMD 文献 | ✅ |
| 27 | Energy drift | ✅ |
| 28 | PBC 定义 | ✅ |
| 29 | PBC 盒子边长 | ✅ |
| 30 | 动能与温度 | ✅ |
| 31 | 控温/热浴总论 | ✅ |
| 32 | Maxwell-Boltzmann | ✅ |
| 33 | 退火 | ✅ |
| 34 | 速度调节法/CSVR | ✅ |
| 35 | Anderson 热浴 | ✅ |
| 36 | Nose-Hoover 热浴 | ✅ |
| 37 | （空白页，仅页眉）| ✅ |
| 38 | AIMD 计算练习目录 | ✅ |
| 39 | 水盒子建模步骤1-2 | ✅ |
| 40 | 水盒子建模步骤3 | ✅ |
| 41 | CP2K 文件清单 | ✅ |
| 42 | VASP AIMD 参数 | ✅ |
| 43 | SMASS 系综/热浴表 | ✅ |
| 44 | MDALGO 热浴表 | ✅ |
| 45 | AIMD 一般步骤 | ✅ |
| 46 | 退火 INCAR 模板 | ✅ |
| 47 | 平衡 INCAR 模板 | ✅ |
| 48 | 参数注意事项 | ✅ |
| 49 | 案例文献1（Chem. Mater.）| ✅ |
| 50 | 案例文献2（PNAS）| ✅ |
| 51 | 后处理分析目录 | ✅ |
| 52 | VASP 16H₂O 练习 | ✅ |
| 53 | 轨迹查看/xdat2xyz/mdsimplify | ✅ |
| 54 | VMD 图像调整 | ✅ |
| 55 | VMD 常用命令 | ✅ |
| 56 | 键长键角标记 | ✅ |
| 57 | Labels 作图 | ✅ |
| 58 | 键长键角应用文献 | ✅ |
| 59 | 势能涨落/OSZICAR | ✅ |
| 60 | 势能平衡判据 | ✅ |
| 61 | 材料稳定判据文献 | ✅ |
| 62 | 类似稳定判据文献 | ✅ |
| 63 | RDF 定义 | ✅ |
| 64 | VMD 算 RDF | ✅ |
| 65 | 水 RDF 配位层 | ✅ |
| 66 | TiO₂-Au RDF | ✅ |
| 67 | CO-Au RDF | ✅ |
| 68 | RDF 仅正交晶胞 | ✅ |
| 69 | VACF 定义 | ✅ |
| 70 | VACF 典型图 | ✅ |
| 71 | VASP VACF 脚本 | ✅ |
| 72 | IR 光谱（VACF-FFT）| ✅ |
| 73 | Li₁₀GeP₂S₁₂ 练习 | ✅ |
| 74 | Li₁₀GeP₂S₁₂ 参数 | ✅ |
| 75 | MSD 定义 | ✅ |
| 76 | RMSD Trajectory Tool | ✅ |
| 77 | 扩散系数/Einstein | ✅ |
| 78 | 多参考帧平均 | ✅ |
| 79 | 扩散系数两法 | ✅ |
| 80 | 扩散系数数据表 | ✅ |
| 81 | 阿伦尼乌斯 Ea | ✅ |
| 82 | VMD 多帧显示 | ✅ |
| 83 | 版权声明（结尾）| ✅ |

**覆盖结论：83 页全部处理，无遗漏（P37 为空白页，已注明）。**

---

## 22. 歧义与待确认事项

1. **`mdsimplify.py` vs `md_simplify.py`**：PDF P53 写 `mdsimplify.py`，字幕 1.2 与 course_notes 写 `md_simplify.py`。以 `md_simplify.py` 为准（字幕/notes 一致），但需讲师提供的实际文件名确认。
2. **P59 `grep = OSZICAR > energy.txt`**：PDF 原文疑似笔误（应为 `grep` 过滤或 `cp` 复制），实际操作是取 OSZICAR 下载到 Origin 画图。
3. **POMASS 改质量两法**：INCAR 里按 POTCAR 元素顺序写 `POMASS = 16 2`（O=16, H=2），或在赝势文件里改 `POMASS` 参数（字幕 1.2 口误"max/po max"=POMASS）。
4. **Energy drift 与 EPS_SCF**：PDF 用阈值为 1E-4/1E-5/1E-6/1E-7，字幕口述"1E-5 左右合适"，未冲突但建议实践用 1E-5~1E-6。
5. 同音错字已全部按 course_survey.md §3 对照表解码（cp two k=CP2K、VSP=VASP、AAMD=AIMD、验室=赝势、机组=基组、京弯=晶胞、军方位1=MSD、风=峰、差=插、BSS1=BSSE、镜像分布函数=RDF、二氧化石=TiO₂、进二=Au20、PM,F=PMF、METDYNAMICS=metadynamics、ELF/ERF=ELF 等）。
