# 庚子计算《AIMD 与 CP2K》第 5 天资料 — 全面逐页学习与交叉对照

> 源文件：
> - PDF 文本：`references/pdf_text/L5.txt`（`庚子计算-AIMD与CP2K讲义-5 - 副本.pdf`，**53 页**）
> - 字幕：课程资料目录中的 `5.txt`（庚子计算《AIMD与CP2K》讲义+字幕，**4519 行**）
> - 已有笔记：`course_notes.md`、`course_survey.md`
> 整理时间：2026-07-19

---

## ⚠️ 0. 重要歧义声明（请先读）

任务描述把"第 5 天"的主题写成 **ELF / PDOS / 电荷差分 / 功函数 / TRAVIS(IR·Raman·VCD·ROA) / 自由能面(伞采样·slow growth·元动力学)**。但逐文件精读后发现**资料编号错位**（与 `learn_L4.md` 的发现一致）：

1. **`L5.txt` PDF 实际只讲"自由能势能面(FES)"**，53 页全为 PMF / slow-growth / metadynamics（含 VASP 与 CP2K 输入），**完全没有 ELF / PDOS / 电荷差分 / 功函数 / TRAVIS**。
2. **电子结构（ELF / PDOS / 电荷差分 / 功函数）与 TRAVIS 振动光谱内容，出现在 `5.txt` 字幕里**（约第 1–2200 行），并且这些内容在 PDF 体系里属于 **`L4.txt` PDF**（已由 `learn_L4.md` 沉淀）。即：课程"第 5 天"被拆成两份 PDF——`L4`=电子结构、`L5`=FES；而 `5.txt` 字幕一次性讲完了整个第 5 天。
3. 因此本文件的处理方式：
   - **§A = `L5.txt` PDF 全量逐页提取（FES，53 页全覆盖）**——这是任务"A. 逐页读 PDF"的主体。
   - **§B = `5.txt` 字幕全量补充**，其中 FES 实操（与 PDF 交叉对照）放在 B3，电子结构 + TRAVIS（PDF 没有、仅字幕有）放在 B1、B2，并标注哪些已被 `learn_L4.md` 覆盖、哪些是字幕独有细节。
   - **§C** 标注 `course_notes.md` 未收录的新内容。
   - **§D** 为 PDF 页码覆盖清单（1–53 全确认）。

凡任务期望在 PDF 里找到的 ELF/PDOS/TRAVIS 公式，实际只在**字幕**（`5.txt`）中，见 §B1、§B2。

---

# A. PDF（L5.txt）逐主题全量提取 — 自由能势能面 FES（共 53 页）

> 按主题重组，保留原文公式、参数表、脚本名、文献。每节标注对应页码。

## A0. 版权声明页（P1、P53）
- 研之成理 AIMD 与 CP2K 课程学习圈；版权归研之成理(杭州)网络科技有限公司。
- 仅限学员个人学习，不得翻录/复制/传播/出售；举报盗版奖励免费正版课程 + 500 元现金。
- P1 与 P53 内容完全相同（首尾声明）。

---

## A1. 课程大纲 / 封面（P2）
- 标题：**AIMD 模拟自由能势能面**
- 主讲人：**刘锦程**
- 三种方法：
  1. **Potential of Mean Force（Blue-moon method）** → PMF / 伞采样
  2. **Slow-growth method**
  3. **Metadynamics**

---

## A2. 为什么用 AIMD 模拟自由能势能面（P3）
- CI-NEB 或 Dimer 方法可找反应路径能垒，但**不是万能**：
  - 能量基于 DFT 电子能量，**不是自由能**（忽略 ZPE、熵、热容贡献）；
  - 过渡态位置**非常依赖初猜**；
  - 对**吸附 / 解离吸附 / 脱附能垒难以计算**；
  - 不容易把环境分子（如水溶剂）的影响**平均化**。
- **AIMD 可以模拟出自由能势能面**，解决上述问题。

---

## A3. 稀有事件 Rare Events（P4）
- 快过程：在极小点附近震荡；慢过程：翻越势垒从一个极小值到另一个极小值。
- 阿伦尼乌斯方程：
  $$k = A\,e^{-E_a/RT}$$
  - 指前因子量级约 **10¹³ s⁻¹**。
  - 对 **0.75 eV 能垒，300 K** 下约 **1 s 发生一次**。
- AIMD 模拟时间量级 ~ps，正常 AIMD **不可能观察到**稀有事件（如 1.75 eV 能垒需模拟 ~1 s）。
- ⇒ 需要**加速采样方法**：研究化学反应、成核、晶体生长、迁移、相变、表面重排等慢过程有用。

---

## A4. 正则系综 canonical ensemble（P5）
- 正则系综每个微观态个数正比于 **exp(−βE)**，其中 **β = 1/k_BT**。
- 配分函数 = 对所有微观态 exp(−βE) 求和/积分。
- 正则系综特征函数 = **亥姆霍兹自由能 A(N,V,T)**，与配分函数关系（PDF 原文未完整写出公式，仅示意）：
  - A(N,V,T) = −k_BT ln Z

---

## A5. 限制性 constrained AIMD（P6）
- MD 模拟中自由能 A 是所有粒子 3N 坐标 + 3N 动量的函数；对平衡态 MD 求系综平均得定值。
- 若固定其中一个坐标自由度 **ξ**（如一个键长），则 A 成为 ξ 的函数 **A(ξ)**。
- "限制性 MD = 固定相空间中某些自由度的 MD"。

---

## A6. PMF 数学原理（P7–P8）
- 从 ξ₀ → ξ₁ 自由能 A(ξ) 的变化 = 对 dA(ξ)/dξ 的积分：
  $$A(\xi_1)-A(\xi_0)=\int_{\xi_0}^{\xi_1}\frac{dA(\xi)}{d\xi}\,d\xi$$
- dA(ξ)/dξ 通过限制性 MD 采样得到，**取系综平均即为 Potential of Mean Force（PMF）**。
- P7 左图（经典 PMF 结果）：黑色 = PMF ⟨F⟩；红色 = PMF 的积分 = 亥姆霍兹自由能 A 势能面。
- P8 方法一 PMF 计算要点：
  - 限制相空间中 6N 自由度中的 **1 个自由度 + 动量**，做一段 MD；
  - AIMD 每个点得瞬时梯度 dA(ξ)/dξ，平均即该 ξ 对应的 PMF；
  - 原理参考 **VASP 手册 "Constrained molecular dynamics"**。

---

## A7. collective variables（P9）
- 被限制的自由度 ξ 种类多样，称 **collective variables（CV）**，如键长、键角、二面角、配位数、坐标等。

---

## A8. 文献案例（PMF 应用，P10–P12）
| 体系 | 要点 | 文献 |
|---|---|---|
| Cu 单原子位点吸附分子 | 受吸附分子影响位置变化，吸附过程**无能垒**，NEB 难算，PMF 可准确描述 | J. Chem. Theory Comput. 2018, 14, 929−938 |
| 表面电催化步骤过渡态 | 溶剂分子构象不断变化影响自由能，NEB 直接算能垒不准，需 MD 对溶剂影响平均化 | J. Am. Chem. Soc. 2016, 138, 13802−13805 |
| 负载 Au 催化剂动态变化 | Au-CO 动态生成 → CO+O→CO₂，Au 原子返回团簇；PMF 算关键步骤自由能垒 | Nat. Commun. 2015, 6, 6511 |

---

## A9. VASP 限制性 AIMD 文件：ICONST（P13–P15）
- 基本 VASP 模拟 4 个文件；限制性 AIMD 多一个 **ICONST** 文件，保存被限制的自由度模式（CV）。
- 书写形式：`FLAG atom(1) ... atom(N) STATUS`
  - **STATUS = 0** 代表固定。
  - **FLAG** 为限制类型：

| FLAG | 含义 | 例 |
|---|---|---|
| R | 原子间距离 | `R 1 2 0` |
| A | 角度 | `A 1 2 3 0` |
| T | 二面角 | `T 1 2 3 4 0` |
| M | 原子(1)与原子(2)(3)中点的距离 | `M 1 2 3 0` |
| X, Y, Z | 坐标 | `X 1 0` |

- P14 实例：固定 C(1)–O(2) 键长 `R 1 2 0`；固定 O(3)–C(1)–O(2) 键角 `A 3 1 2 0`；固定 H(5)–O(3)–C(1)–O(2) 二面角 `T 5 3 1 2 0`；固定多个 `R 1 3 0` / `R 4 6 0` / `R 3 6 0`。
- P15 组合 CV：多个键长组合成新 CV，如 `r1 + r2 − r3`：
  ```
  R 1 3 0
  R 4 6 0
  R 3 6 0
  S 1. 1. -1 0     # S = 线性组合；系数 1, 1, -1；STATUS=0
  ```

---

## A10. 实例：H₂CO₃ 碳酸分解自由能势能面（PMF 法，P16–P21）

**步骤 1（P16）**：结构优化初态、末态（类似 NEB 过渡态计算）。
**步骤 2（P16）**：用 `nebmake.pl` 脚本插点（**最好密集**），如：
```bash
nebmake.pl ../opt1/CONTCAR ../opt2/CONTCAR 10   # 插 10 个点 → 共 12 个点
```
每个文件夹准备 ICONST 和其他输入文件，共需 **12 个 AIMD 模拟**。

**INCAR（P17）**：
```text
SYSTEM = Au      ENCUT = 400      NSW = 10000
#KPAR = 4        ISMEAR = 0       POTIM = 1
NCORE = 12       SIGMA = 0.05     SMASS = 0
ISTART = 1       EDIFF = 1E-6     MDALGO = 2      # PMF 用 MDALGO=2
ICHARG = 1       NELMIN = 5       TEBEG = 300
LWAVE = .FALSE.  NELM = 300       TEEND = 300
LCHARG = .FALSE. GGA = PE         NBLOCK = 1
LVTOT = .FALSE.  LREAL = Auto     LBLUEOUT = .TRUE.   # 关键：输出蓝月梯度
LVHAR = .FALSE.  ISYM = 0
LELF = .FALSE.
# LORBIT = 11
# ICONST 文件内容：
R 1 3 0
R 4 6 0
R 3 6 0
S 1. 1. -1 0
```

**步骤 3（P18）结果分析**：REPORT 文件每帧输出：
```
>Const_coord
cc> S 0.17000 0.17000 0.301200E-05
>Blue_moon
lambda |z|^(-1/2) GkT |z|^(-1/2)*(lambda+GkT)
b_m> -0.137162E+01 0.730324E+00 0.439271E-02 -0.998520E+00
```
- `cc>` = 限制性 MD 中 CV 值；`b_m>` = 自由能 A 沿限制自由度的**梯度**（需时间平均即 PMF）。
- 取 `lambda` 或 `|z|^(-1/2)*(lambda+GkT)`（两数据基本一致），取平均即可。
- 提取命令：`grep b_m REPORT > bm.txt`

**步骤 4（P19–P20）Origin 画图**：
- 把 bm.txt 拖入 Origin，`Statistics on Column` 对 lambda 一列统计得**平均值 + 标准差**。
- 12 套数据都处理，汇总到新表；对 lambda 求平均和标准差，用 **Y error** 方式画图。
- 对 PMF 求积分 ⇒ 得到自由能 A（红最高点到两侧差 = 能垒）。

**成品图（P21）**：红色线最高点到两侧差 = 自由能能垒，**此例 ~1.3 eV**。**在最高点附近插点越密集，能垒计算越准确**。

---

## A11. 方法二：Slow-growth 方法（推荐，P22–P25）

- PMF 缺点：计算量太大（需跑十几条 AIMD）；能垒不准确（最高点不能正好落在鞍点）。
- **Michiel Sprik 1998** 改进提出 Slow-growth：只跑**一条** AIMD，让 CV 非常缓慢变化，每步算自由能梯度，积分得连续平滑势能面。
- P22 实例能垒：PMF ~1.3 eV；Slow-growth ~1.5 eV（更准确）。

**步骤（P23）**：
- 步骤 1：结构优化初态（末态优化不优化均可）。
- 步骤 2：从初态做一条 AIMD，限制 CV（r1+r2−r3）缓慢增大，每步增 **0.0005**，共跑 **10000 步**（0.1700 → 5.1700）。
  ```text
  INCREM = 0.0005    # 每步 CV 增量
  ```
- 步骤 3：提取 CV 和 lambda：`grep cc REPORT > cc.txt` / `grep b_m REPORT > bm.txt`
- 步骤 4：导入 Origin，cc 变化作 X 轴，lambda 作 Y 轴，积分作图。

**小技巧（P24）**：
- CV 可从小到大扫，也可从大到小扫（`INCREM` 设负值）。
- `INCREM` 越小扫得越慢、结果越准。
- 可手动调结构让初始 CV 更小/更大，在极小值附近更多采样。
- 适当对 bm.txt 的 lambda 做平均让曲线更平滑。

**应用（P25）**：Pt 表面溶解一个 Pt 原子的自由能能垒。建模→结构优化→升温退火(或预平衡)→从初态一条 AIMD，限制表面 Pt 与其他所有 Pt 的**配位数 CV**，每步增 0.0005，10000 步（6.49822 → 1.49822）→ 提取 CV 与 lambda 画图。

---

## A12. 方法三：Metadynamics 原理（P26–P27）

- Metadynamics = 在 MD 模拟中**不断加上高斯势函数抬高势能面，直到把整个势能面填平**。
- 新势能面（biased）= 原本势能面（unbiased）+ 高斯势函数。
- **CV (ξ)**：控制要增强采样的自由度。
- 每个高斯势函数需定义**高度 h、宽度 w**，每 **t** 步加一个高斯函数。
- 标准偏置势（手册通用形式）：
  $$V(s)=\sum_i h\cdot\exp\!\left(-\frac{|s-s_i|^2}{2w^2}\right)$$
  （CP2K 具体形式见 A24 / P52）

---

## A13. 文献案例（metadynamics，P28–P30）
| 体系 | 要点 | 文献 |
|---|---|---|
| 表面电催化 *CHOH + H₂O⁺ → *CH + 2H₂O | 两条路径：先变成 CHOH₂，或直接一步反应 | J. Phys. Chem. Lett. 2015, 6, 4767−4773 |
| Al³⁺ 从表面脱出到溶液 | 路径与能垒计算 | Nat. Commun. 2019, 10(1), 3139 |
| CH₄ 在 Cu₈ 团簇上 C-H 活化 | NEB 不易，用 C-H 配位数定义 CV 得 C-H 解离能垒 | J. Chem. Phys. 142, 184308 (2015) |

---

## A14. Metadynamics INCAR（VASP，P31）
```text
SYSTEM = Au      ENCUT = 400      NSW = 1000000
#KPAR = 4        ISMEAR = 0       POTIM = 1
NCORE = 12       SIGMA = 0.05     SMASS = 0
ISTART = 1       EDIFF = 1E-6     MDALGO = 21     # metadynamics 用 MDALGO=21
ICHARG = 1       NELMIN = 5       TEBEG = 300
LWAVE = .FALSE.  NELM = 300       TEEND = 300
LCHARG = .FALSE. GGA = PE         NBLOCK = 1
LVTOT = .FALSE.  LREAL = Auto     HILLS_H = 0.02   # 高度 h (eV)
LVHAR = .FALSE.  ISYM = 0         HILLS_W = 0.1    # 宽度 w (ξ)
LELF = .FALSE.                     HILLS_BIN = 30   # 间隔 t (step)
```
- 高度 h：`HILLS_H`；宽度 w：`HILLS_W`；间隔 t：`HILLS_BIN`。

---

## A15. 实例：N₂ 解离吸附自由能垒（metadynamics，P32–P35）
- Ru(0001) Fix Fix；峰高 0.1 eV、峰宽 0.2、间隔 30 步；ICONST 设两个 CV：
  - **CV1** = Ru–N 配位数；
  - **CV2** = N–N 键长。

**配位数 CV 设定方法（P33–P34）**——VASP 不能设元素间配位数，需逐一列出原子对：
```
R 49 1 0   ...   R 49 48 0      # 1. 列出 R（48 个 Ru 与 N 原子 1 的距离）
R 50 1 0   ...   R 50 48 0      # 2. 列出 R（48 个 Ru 与 N 原子 2 的距离）
D 1.85 ...(共96个1.85) 1.85 0 5  # 3. 配位数组合 D（Ru-N 配位数），ci=1.85 平衡键长
S 0 ...(共96个0) 0 1 5          # 4. 距离线性组合 S（N-N 键长）
```
- `D`：配位数，按配位数公式组合前面所有自由度；`ci` = 平衡键长（0 不计算，此处取 **1.85** 为 Ru–N 平衡键长），`qi` = 当前键长。
- `S`：键长线性组合。

**配位数经典公式（P35）**：当处于平衡键长时 ξ 数值 = **9/14**（两个指数比值），**不能直接对应化学定义配位数，但反映配位数变化趋势**。当 c_i = 1.2 时，平衡位置配位数值是 9/14。

---

## A16. Metadynamics 输出文件：HILLSPOT（P36）
- 1 个 CV：`HILLSPOT` 三列（CV1 值，峰高，峰宽）。
- 2 个 CV：`HILLSPOT` 四列（CV1 值，CV2 值，峰高，峰宽）。
```
0.15448 1.11035 0.10000 0.10000
0.16506 1.09978 0.10000 0.10000
...
```
- 运行脚本画图：
  ```bash
  # 1D surface
  python gaussian.py 1 x1 x2
  # 2D surface
  python gaussian.py 2 x1 x2 y1 y2
  ```

---

## A17. CV 震荡判据（P37–P38）
- P37 时间轴示意：7.5 ps / 15 ps / 30 ps / 45 ps / 60 ps / 79 ps → 极小值1 / TS / 极小值2 / 极小值3。
- **CV 值来回震荡十次以上**，体系势能面被填平，数据可用。

---

## A18. Metadynamics 技巧：CV 选取（P39）
- CV 选取非常需要技巧，要保证只在我们想要的过程中采样。
  - 例：碳酸分解若仍用 slow-growth 的 `r1 + r2 − r3`，随势能面升高会发生 **OH 和 COOH 分离**（不是想要的 H₂O 和 CO₂），影响能垒计算。
- 深入理解 CV 建议搜知乎：**"计算化学中的 metadynamics 中的 collective variable 如何选取？"**

---

## A19. Metadynamics 技巧：峰高/宽/重启/维度（P40–P42）
- **对初态位置无要求**（PMF 和 slow-growth 对初态有要求）。
- **峰高（h）**：直接决定能垒计算误差。取预估能垒的 **~1/50**，如 1 eV 能垒峰高取 **0.02 eV**（越小越准但要可接受计算量）。
- **峰宽（w）**：过小计算慢、不能还原盆地形状；过大不能描述陡峭部分、势能面不平。
- **峰高/宽可在 AIMD 中调整**，不同盆地适合不同峰（P41：N–N 适合峰平宽；CV1 Ru–N 配位数适合峰高且窄）。
- **重启计算（P42）**：需读取已加高斯峰（`PENALTYPOT` 文件）：
  ```bash
  cp XDATCAR XDATCAR.bak
  cp POSCAR POSCAR.bak
  cp CONTCAR POSCAR
  cp HILLSPOT PENALTYPOT
  ```
  - 可先加大高斯势跑一段，重启减小高斯势继续跑以平滑势能面（或调 Plumed 用 **well-tempered** 方法——**VASP 不能用，CP2K 可以**）。
  - **1D 势能面比 2D 计算量小得多；不要尝试 3 维势能面**（计算量太大）。
  - Metadynamics 可与 PMF / Slow-growth **结合互相印证**。

---

## A20. 练习 CP2k + QM/MM（P43–P46）
- 练习：Nanostructures and adsorption on metallic surfaces — Cyclohexaphenylene。
  - 链接：https://scc.acad.bg/.../Dehydrogenation_of_cyclohexaphenylene_on_Cu_111.pdf
  - https://www.cp2k.org/exercises:2015_cecam_tutorial:neb
  - A.C. Levi, P.Calvini, Surf. Sci. 601, 1494 (2007)
- QM 区域：半经验 **PM6**；MM 区域：Cu 用 **EAM 势**；Cu–C / Cu–H 用非键相互作用模型。
- 计算脱氢过程能垒，采用 **CI-NEB** 方法。

**cp2k.inp（P45–P46）多区域 / QM-MM 框架**：
```text
&MULTIPLE_FORCE_EVALS
  FORCE_EVAL_ORDER 2 3
  MULTIPLE_SUBSYS T        # 共需 3 个 FORCE_EVAL
&END
# 第一个定义 QM 和 MM 区域范围；第二个定义 MM 计算参数和格子；第三个定义 QM 计算参数和格子
&MAPPING
  &FORCE_EVAL_MIXED
    &FRAGMENT 1            # 片段1，包含 1..56 号原子
      1 56
    &END
    &FRAGMENT 2            # 片段2，包含 57..2936 号原子
      57 2936
    &END
  &END
&END
&FORCE_EVAL 1
  DEFINE_FRAGMENTS 1 2     # MM 区域，包括片段1和2
&END
&FORCE_EVAL 2
  DEFINE_FRAGMENTS 1       # QM 区域，包括片段1
&END
&FORCE_EVAL
  METHOD FIST              # MM
  &MM ... &SUBSYS &CELL ABC 40.764229 39.715716 70. &TOPOLOGY COORD_FILE_NAME ./s ...
&END
&FORCE_EVAL
  METHOD Quickstep         # QM
  &DFT &QS METHOD PM6
  &SUBSYS &CELL ABC 30 30 30 PERIODIC NONE &TOPOLOGY COORD_FILE_NAME ./f ...
&END
```

---

## A21. CP2K Metadynamics 定义 CV（P47）
```text
&COLVAR
  &COMBINE_COLVAR
    &COLVAR
      &DISTANCE ATOMS 4 50   # L(C-H)
    &END
  &END COLVAR
  &COLVAR
    &DISTANCE ATOMS 7 49     # L(C-H)
    &END
  &END COLVAR
  FUNCTION CV1+CV2
  VARIABLES CV1 CV2
  ERROR_LIMIT 1.0E-8
&END
&COLVAR
  &DISTANCE ATOMS 49 50      # L(H-H)
  &END
&END
```
- CV1 = L(C-H) + L(C-H)；CV2 = L(H-H)。

---

## A22. CP2K Metadynamics 输入：`&MOTION &FREE_ENERGY &METAVAR`（P48）
```text
&MOTION
  &MD
    ENSEMBLE NVT
    STEPS 200000
    TIMESTEP 0.5
    TEMPERATURE 450.0
    &THERMOSTAT
      TYPE CSVR
      TIMECON [fs] 200.0
    &END
  &END MD
  &FREE_ENERGY
    &METADYN
      DO_HILLS
      NT_HILLS 50
      &METAVAR
        COLVAR 1
        SCALE 0.3           # 峰宽 SCALE
        WW 3.0e-3           # 峰高 WW
      &END METAVAR
      &METAVAR
        COLVAR 2
        SCALE 0.3
        WW 3.0e-3
      &END METAVAR
      &WALL
        &QUADRATIC
          COLVAR 1
          DIRECTION WALL_PLUS
          TYPE QUADRATIC
          POSITION [angstrom] 5
          K [kcalmol] 40.0
        &END QUADRATIC
      &END WALL
      ... (WALL_MINUS 等)
    &END METADYN
  &END FREE_ENERGY
  &PRINT
    &TRAJECTORY &EACH MD 50 &END &END
    &RESTART &EACH MD 100 &END &END
    &HILLS COMMON_ITERATION_LEVELS 3 &END
  &END PRINT
&END MOTION
```

---

## A23. CP2K 输出文件与绘图（P49–P51）
- P49：Cu 用 VDW；C 和 H 用 VDW 和 dynamicBonds 混合。
- 输出文件（P50）：
  - `cp2k-COLVAR.metadynLog`
  - `cp2k-HILLS.metadynLog`
  ```
  25.0 4.19568 5.71958 0.30000 0.30000 0.00300
  50.0 4.19083 5.72538 0.30000 0.30000 0.00300
  ...
  # 时间  CV1  CV1宽度  CV2宽度  峰高
  ```
- 绘制等高线图（P51）：
  ```bash
  python ./gaussian.py 2 1 6 0 5    # 维度  X范围  Y范围
  # 2 = 2D；1 6 = X 范围；0 5 = Y 范围
  # CV1 / L(C-H) + L(C-H)
  ```

---

## A24. Metadynamics 设置 WW（峰高）和 SCALE（峰宽）（P52）
- 官方说明：history dependent term 表达式：
  $$WW \times \sum_{j=1}^{n_{\text{hills}}} \prod_{k=1}^{n_{\text{colvar}}}\left[\exp\!\left(-0.5\left(\frac{ss-ss0(k,j)}{SCALE(k)}\right)^2\right)\right]$$
  - `ncolvar` = 定义的 METAVAR 数；`nhills` = spawned hills 数。
- 不合适的峰宽度 vs 合适的峰宽度（图示）。

---

# B. 字幕（5.txt，4519 行）全量补充

> 字幕是"第 5 天"完整录音转写，覆盖 **振动光谱(TRAVIS) + 电子结构分析 + FES**。下面按主题提取，并标注与 PDF 的对应关系。同音错字依 `course_survey.md §3` 解码（cp two k=CP2K、VSP=VASP、AAMD=AIMD、PM,F=PMF、METDYNAMICS=metadynamics、限制AAMD=限制性AIMD、自由能势能面=FES、ELF/ERF=ELF、letis plan=lattice plane、2 d data play=2D data plane、风=峰、差(点)=插(点)、多点=密点、飞艇=fitting、BSS1=BSSE、镜像分布函数=RDF、二氧化石=TiO₂、进二=Au20、棚材料=硼材料 等）。

## B1. 振动光谱 TRAVIS 算 IR / Raman / VCD / ROA（字幕 1–266 行）【PDF 完全没有】

### B1.1 为什么用 TRAVIS
- VASP 可用 `vibrat` 拟合**速度自相关函数**算 **vDOS**，但 vDOS **不含偶极信息**，不是真正的红外光谱。
- **CP2K 可联用 TRAVIS** 模拟红外(IR)、拉曼(Raman)、振动圆二色谱(VCD)、ROA 等。
- TRAVIS = 德国 **Martin Brehm** 课题组开发的轨迹分析程序（字幕称"martin 从课题组"）。

### B1.2 安装
- 官网下载源代码 → 传到服务器 → 解压 → 目录内有 `makefile` → `make`（默认 GCC 编译）→ 在 `EXE/` 生成可执行 `TRAVIS`。
- 可复制到 `~/bin` 或当前工作目录使用。

### B1.3 必须输出 Wannier 中心（偶极变化来源）
- 算振动光谱**必须输出 Wannier 中心坐标**（孤对电子 / 电子对中心位置）。原子核带正电，还需带负电的电子对中心才能算偶极变化 → 才能模拟 IR。
- CP2K 输入：在 `&DFT` 下加 `&LOCALIZE`（字幕写 "local lights / localize"），定义输出文件名（X,Y,Z 格式的 XYZ 轨迹，含原子核 + 以 X 代表的 Wannier 中心）。
- **坑**：运行 TRAVIS 读轨迹必须读**带 Wannier 中心的 XYZ 文件**，**不能读 `cp2k-position`**（只含原子核，不行）。

### B1.4 TRAVIS 交互流程（水分子 IR 实例，字幕 123–235 行）
- 运行：`travis -p <带Wannier中心的xyz>`（`-p` 读入轨迹）。
- 交互参数（其余默认）：
  - `SL` / 晶格边界：从 CP2K 读出，**单位 Å³**（水盒子例输入 782，立方格子选 yes 表示三方向等长）。
  - 是否开高级模式：**NO**（默认）。
  - 算哪种光谱：输入 **L2**（RIR = 红外光谱）；再问高级模式仍选默认。
  - 时间步长：**0.5 fs**。
  - 提供偶极信息方式：选 **1（Wannier 中心方式）**。
  - 哪个原子代表 Wannier 中心：**X 原子**；过滤电子带多少电荷：**2**（默认）。
  - 原子核电荷（水：H=+1, O=+6）一路回车。
  - 是否输出整体 IR 光谱：**yes**。
  - 起始帧：忽略前 N 帧填 1（全读入）；或填 100/1000 忽略前面。
- 输出 CSV（波数行 + 光谱高度行），用 Origin 画图，波数范围 **0–4000 cm⁻¹**。
- 结果：3000–4000 cm⁻¹ 高峰（O-H 伸缩）；与第 2 天 vDOS 比，考虑偶极后**振动强度划分更合理**。

### B1.5 CP2K 自带 IR 功能（不推荐）
- CP2K 官网有两个自带输出 IR 的例子，但"功能不太好用"，一般结合 TRAVIS 算。

> 注：Raman / VCD / ROA 字幕仅列为 TRAVIS 可算类型，未展开控制文件写法（控制文件交互中 L2=IR；Raman 等对应其他菜单）。

---

## B2. 电子结构分析（CP2K print section，字幕 266–2200 行）【PDF 完全没有；与 learn_L4.md 重叠，此处补充字幕独有实操】

> 说明：ELF / PDOS / 电荷密度 / 功函数 的详细公式与图已在 `learn_L4.md`（源自 L4 PDF）沉淀；下面聚焦 **5.txt 字幕独有的实操细节、脚本、参数值、数值案例**，并标注新增点。

### B2.1 电荷密度 / 自旋密度（E_DENSITY_CUBE）
- 所有电子结构输出都在 `&DFT &PRINT` 下：DOS/PDOS、Mulliken/Hirshfeld/Lowdin 原子电荷、电荷密度/自旋密度(ELECTRONIC_DENSITY)、ELF_CUBE、MO_CUBE、V_HARTREE(静电势)、偶极。
- `E_DENSITY_CUBE` 同时含电荷密度（α+β 电子）与自旋密度（α−β）。
- **STRIDE（收缩）**：cube 文件格点极密（如 100×100×100 = 100 万点）。默认 **STRIDE 2 2 2**（每 2 点取 1，忽略一半，文件小但画图有棱角）；改 **STRIDE 1 1 1** 输出全部格点，图平滑。
- cube 文件格式：前几行原子坐标（如 28=Ni, 6=C, 8=O），再是 X/Y/Z 方向格点数（如 60×60×270），后几万行格点数值。VESTA（或 VMD）可读。
- 一般**不直接分析总电荷密度**，而是分析**电荷密度差分**。

### B2.2 电荷密度差分（VESTA，total − CO − metal）【重要实操】
- **操作流程**：在 VESTA `Edit → Edit Data → Volume Data`，用 **SUBSTRACT**（减，不是 ADD 加）。
  - 导入 total（整体，如 Ni + CO）；再 import CO 片段选 SUBSTRACT；再 import metal 片段选 SUBSTRACT。
  - ⇒ total − CO − metal。黄色 = 电荷增加；蓝色/青色 = 电荷减小。
- **片段准备**：先优化整体结构（得吸附结构/极小点）；再算两个单独计算（整体 slab、单独分子），**结构务必不再优化**（否则差分图不对）。把对应坐标摘出各算单点能，得 3 个 cube 文件。
- **变形电荷密度**（deformation charge density）= 自洽后电荷密度 − 各孤立原子电荷密度（用得少）。
- **二维截面**两种方法：
  - `Edit → lattice plane`（letis plan）：选 3 个原子定面 → slice → calculate the best plane。
  - `Utilities → 2D Data Plane`（2 d data play）：选 3 原子 → slice。
  - 调边界（如 0~0.1 或 −0.05~0.05）让图像清晰；VESTA 不能直接显示坐标范围，需在 PPT 手动加数值（如 −0.03~+0.03，中间 0）。

### B2.3 平面平均电荷密度（Z 方向投影）【新增脚本】
- 用讲师自写 `cube.py`（或 CP2K 官方 `cube_cr` / `cube_xyz` 小程序）对 cube 文件做 Z 方向平均投影：
  ```bash
  python cube.py cp2k-cube-electronic_density     # 输出 charge integration.txt
  ```
- 在 total / CO / metal 三个文件夹各跑，得 3 个投影值，Origin 中 **B − C − D** 得到 Z 方向电荷重排（>0 增加，<0 减小）。用于异质结（如 g-C₃N₄/TiO₂）电子流向分析。

### B2.4 原子电荷（Bader / Mulliken / Hirshfeld / Lowdin）
- 原子电荷是人为划分（氢氧键中间电荷划给谁无严格物理意义），与化学价态不同概念。
- **Bader 电荷**（零通量面法）：以**电荷密度梯度为零**的曲面为分界面，物理意义明确。命令：
  ```bash
  bader cp2k.cube electronic      # 输出 ACF.dat
  ```
  看 `ACF.dat` 的 `CHARGE` 行；价电子数 − Bader 电荷 = 原子电荷。
  - 例（CO/Ni）：C 本 4 个价电子 → Bader 2.36 → **+1.64**；O 本 6 → 7.85 → **−1.85**；Ni 变化很小。
  - 凝聚态/表面体系看 Bader 更靠谱、更接近化学直觉（C 正、O 负）。
- 也可在 `&PRINT` 打开 `HIRSHFELD` / `MULLIKEN` / `LOWDIN` 三个 section（定义 filename），输出 net charge。
  - 例：Mulliken C=+0.44, O=−0.07（都接近 0，且 O 算成 +，判断得失电子不准）。**原子电荷主要看相对值、横向对比**，绝对数值意义不大。
- 原子染色（按原子电荷数值染色）可用于看整体电荷分布（如石墨烯纳米带左右电荷差异）。

### B2.5 PDOS / d-band（态密度）【新增参数细节】
- CP2K 默认只算 Γ 点（尤其 OT 法），PDOS 不如多 K 点准确；对角化可含更多 K 点。
- `&PDOS` 参数：
  - `NLUO` = 空轨道数（`=1` 输出所有空轨道；或 30 只输出 30 条空轨道）。
  - `LDOS`（local DOS）：把若干原子 PDOS 合起来输出（如 1~26 号原子整体）。
  - `COMPONENTS`：是否分量子数（px/py/pz、d 五个分量）；不加则只分 s/p/d。
- 输出：`cp2k-AlphaK-1...`（自旋向上）、`cp2k-BetaK-1...`（自旋向下）；开 UKS 则两套。
- **必须做高斯展宽**才能画图：直接生成的文件不能直接画，需运行 CP2K 官网脚本（字幕称 `nw.py`，即高斯展宽脚本）转成 `DOS.txt`：
  ```bash
  python nw.py     # 转成 DOS.txt
  ```
  - DOS.txt 前三列自旋向上（s/p/d）、后三列自旋向下；自旋向下通常取负画。能量范围关注费米能级附近（如 −10~0 eV）。展宽参数可调（0.005 瘦峰 / 0.02~0.03 胖峰）。
- **应用**：d-band center、离子键（电子转移，费米能级下出现新峰）vs 共价键（相邻原子 PDOS 峰重合）、掺杂（如 Al 替 Ti 产生氧 p 轨道缺陷态在费米能级以上）、表面态（如 GaN 表面不饱和键在费米能级附近新态）、吸附（CO 的 π/π* 与金属 d 反馈键）。

### B2.6 ELF（电子局域函数）【新增公式与应用】
- 公式（数值范围 **0~1**）：当分母项（动能密度贡献）= 0 时 ELF=1（完全局域）；为无穷大时 ELF=0（完全离域）。
  - ELF **>0.5** 局域强（孤对电子、共价键、多中心键）；**≈0** 离域。
- CP2K：`&PRINT &ELF_CUBE`，`STRIDE 1 1 1`；输出 `elf.cube`（α/β）。VESTA 切片（2D data slice，选 3 原子），纵坐标范围一般 **0~1**（或 0~0.8），标色彩分布范围。
- **应用**：表面催化（N₂/H₂ 在 TiO₂ 上解离的共价/离子成分）、**二维硼材料的"三中心两电子键"**（最红处=电子聚集最高）、**电子化合物 electrides**（无核位置强局域电子，如 Na₂He 高压）、**非还原性载体**（Al₂O₃/SiO₂/ZrO₂ 氧缺陷处局域电子）、硼团簇（B₁₃ 中心三中心两电子键、其余两中心两电子键）。CO/Ni 例中：氧孤对电子（红）、C–O 共价键、新形成的 C–Ni 配位键。

### B2.7 分子轨道 MO cubes（HOMO/LUMO）【新增】
- `&PRINT &MO_CUBE`：`N_LUMO` / `N_HOMO` = 要画的 LUMO/HOMO 数（从费米能级上下数；全输出写 1）；`STRIDE 1 1 1`。
- 分子体系有用（金属体系 γ 点 MO 看不出信息）。轨道能级从 `cp2k.out` 读（occupied/unoccupied），单位是 **Hartree**，画图转 **eV 需 ×27.211**。费米能级在 out 文件中（eV）。

### B2.8 静电势 / 功函数（V_HARTREE，Φ）【新增公式与数值】
- Kohn-Sham 哈密顿量：第1项电子动能，第2项电子–核势能，第3项电子–电子势能；静电势 = 第2+3项。
- CP2K：`&PRINT &V_HARTREE_CUBE`（`file name` 可写 hartree，`STRIDE 1 1 1`）。
- **功函数 Φ = E_vac − E_Fermi**（真空能级 − 费米能级）。
  - VASP 用 `LVHARTREE=.TRUE.`；CP2K 用 `V_HARTREE_CUBE`（两个关键词对应）。
  - 算真空能级：对静电势 cube 做 **Z 方向平面平均**（用同一 `cube.py`），得曲线，平段 = 真空能级。
  - **表面偶极校正**：非对称表面（如上表面有 CO、下表面无）上下表面功函数不同、真空能级斜，须加 `SURFACE_DIPOLE_CORRECTION` 截断屏蔽，分别读上下真空值减费米能级。
  - 实例数值：真空能级 **0.3158 Ha**，费米能级 **0.1224 Ha** ⇒ **Φ ≈ 5.26 eV**。
  - 异质结（g-C₃N₄/TiO₂）功函数小者更易失电子，结合电荷差分判断电子从 g-C₃N₄ 流向 TiO₂。

### B2.9 分子表面静电势 ESP（分布）【新增】
- 定义：在一定电荷密度表面（气相分子取 **0.001 a.u.**，凝聚态取 **0.002 a.u.**）的静电势数值。
- 用 `electronic density` + `hartree density` 两个 cube，VESTA `Edit Data → Volume Data → Surface Coloring` import hartree density 染色，调 iso surface（如 0.001）与显色范围（如 0.3~0.32）。
- 应用：受阻路易斯酸碱对（如 TiO₂ 氧缺陷暴露正电中心+负电中心），极化 H₂/CH₄ 等分子，判断亲核/亲电位点。

---

## B3. FES 字幕增量（与 PDF A 节交叉对照，字幕 2200–4519 行）

> 下表把字幕独有的 FES 实操/坑与 PDF 对照，并标"仅字幕有"。

| 主题 | PDF（A 节） | 字幕独有补充（仅字幕有） |
|---|---|---|
| 为什么 AIMD 算 FES | P3 四条缺点 | 字幕补充：NEB 静态算忽略 ZPE/熵/热容；显式溶剂必须 AIMD；时间尺度问题（AIMD ~10–30 ps，真实反应需 ~1 s，故需加速采样或升温） |
| 正则系综 | P5 A(N,V,T) | 字幕：NVT→亥姆霍兹自由能 A；吉布斯需 NPT（差 PV 项，通常可忽略，用 NVT 即可） |
| 限制性 AIMD / CV | P6–P9 | 字幕：CV 可设 distance（原子–原子 / 原子–键中心 / 原子–面中心 / 原子–表面）、angle、二面角、多自由度组合；CP2K 自由度远大于 VASP |
| PMF 数学 | P7–P8 | 字幕：λ = dA/dξ 梯度，<λ>=PMF，积分得 A(ξ)；蓝月法；提取 `grep b_m REPORT`；严格用第4列/第2列比值平均，实际第1列即可；Origin `Statistics on Column` 求 mean + SD；`Mathematics → Integrate` 积分；**过渡态位置强烈依赖插点密度，点稀能量差可达 0.1 eV 级** |
| ICONST | P13–P15 | 字幕：`nebmake.pl ../opt1/CONTCAR ../opt2/CONTCAR 10`；`grep cc REPORT` 取 CV；`grep b_m REPORT`；VASP 只 4–5 种 CV，CP2K 可随心定义；INCAR 仅多 `LBLUEOUT=.TRUE.` |
| 碳酸分解 PMF 实例 | P16–P21 | 字幕完整演示：上传算例 `free_energy/PMF_BLUE_MOON`，`nebmake` 生成 12 文件夹；每个跑 AIMD；`report` 中 `b_m` 行；`grep b_m report > BM00.txt`；Origin `Statistics on Column` 得 mean/SD；`Y error` 画图；`Mathematics → Integrate` 积分。PMF ~1.3 eV，点稀能垒不准 |
| Slow-growth | P22–P25 | 字幕：CV 可正/反向扫（`INCREM` 负）；`INCREM` 越小越不易崩溃；手动拉初态结构以采到盆地两侧；应用 Pt 溶解（配位数 CV 6.49822→1.49822）。PMF 1.3 eV vs slow-growth 1.5 eV |
| Metadynamics 原理 | P26–P27 | 字幕：不断加高斯填盆地直至填平；填越多越高、过渡态处低；累加反转取负还原真实势能面；只控制 1–2 维（体系 3N 维不可能全控） |
| Metadynamics VASP 参数 | P31 | 字幕：`HILLS_H`（eV）/ `HILLS_W`（CV 同单位，键长=Å、角度=°）/ `HILLS_BIN`（步）；只能控这 3 个；CV 跑到哪加哪，频率/高度/宽度可控，位置不可控 |
| 配位数 CV | P33–P35 | 字幕：配位数公式 = 两个高斯比值 `1−(r/d)^9 / 1−(r/d)^14`（9 和 14 VASP 不可调，CP2K 可调 NN/ND）；平衡键长 ci=1.85；ξ=9/14 时梯度最大、最灵敏（非化学配位数 1）；CP2K `&COLVAR &COORDINATION FROM_KIND TO_KIND R0 NN ND` 几行搞定（VASP 需 100+ 行） |
| HILLSPOT / 画图 | P36 | 字幕：`HILLSPOT`（VASP）/ `cp2k-HILLS.metadynLog`（CP2K）；讲师自写 `gaussian.py` 既支持 VASP 又支持 CP2K（切换文件名）；`python gaussian.py 1 x1 x2` / `2 x1 x2 y1 y2`；可只取前 100/200/... 数据看势能面生长过程 |
| CV 震荡判据 | P37–P38 | 字幕：CV 来回跳跃 **≥10 次** 认为填平；例 80 ps 模拟完成 N₂ 解离（跳跃 8 次还不够，需再跑） |
| 峰高/宽/重启 | P40–P42 | 字幕：先填大峰探路、再填小峰精细化；VASP 重启 `cp HILLSPOT PENALTYPOT`；**well-tempered 仅 Plumed 实现**；1D/2D 不要 3D |
| CP2K metadynamics 输入 | P43–P52 | 字幕补充：`&COLVAR` 用 `&COORDINATION FROM_KIND TO_KIND`（NN/ND/R0 可调 8&14、7&12 等）；**WALL 仅 CP2K/Plumed 有，VASP 无**（可限制 CV 范围，如 N–N 键长<4 Å、C–H 之和<5 Å、>1 Å）；CP2K 可给 CV1/CV2 **不同宽度**（VASP 必须同宽）；输出 `cp2k-COLVAR.metadynLog`(时间,CV1,CV1宽,CV2宽,峰高) 与 `cp2k-HILLS.metadynLog` |
| 应用案例 | P10–P12, P28–P30 | 字幕补充：单原子 Cu 吸附 NH₃（构象多，需 MD 平均）；CO₂ 电催化多步（显性溶剂）；Au 团簇 Au–H 脱出；甲烷在单原子催化剂上解离+脱附（两种路径：脱附 ~1.4 eV / 转移 ~0.6 eV，实验 Science 支持脱附，仍有争议） |

---

# C. 与 course_notes.md 对照（标注未收录 / 新增内容）

> `course_notes.md` 已覆盖的 L5 相关项（A4 电子结构可视化、A5 FES 三法）属**高层概述**。以下为 **course_notes.md 未收录、本文件新提取**的内容（【新增】）：

**FES（方法层，大量新增）：**
- 【新增】阿伦尼乌斯指前因子 10¹³ s⁻¹、0.75 eV@300K≈1s、1.75 eV 需 1s 的定量估算（A3 / 字幕）。
- 【新增】正则系综 A(N,V,T)=−kT lnZ；NVT→亥姆霍兹、NPT→吉布斯（差 PV）（A4 / 字幕）。
- 【新增】PMF 完整 INCAR（MDALGO=2, LBLUEOUT, ENCUT=400, NSW=10000 等）、REPORT `b_m` 行格式 `lambda |z|^(-1/2) GkT |z|^(-1/2)*(lambda+GkT)`、nebmake.pl 命令、Origin `Statistics on Column`+`Integrate`+`Y error` 全流程（A10 / 字幕）。
- 【新增】Slow-growth `INCREM` 参数、单向/反向扫、手动拉结构、Pt 溶解配位数 CV 实例（A11 / 字幕）。
- 【新增】Metadynamics VASP INCAR（MDALGO=21, HILLS_H/W/BIN）、配位数 CV 的 D/S 写法与 `9/14` 公式、HILLSPOT 格式、`gaussian.py` 用法（A12–A19）。
- 【新增】Well-tempered 仅 Plumed（VASP 不可）；1D/2D 不 3D；重启 `cp HILLSPOT PENALTYPOT`（A19 / 字幕）。
- 【新增】**CP2K metadynamics 完整输入**：`&MULTIPLE_FORCE_EVALS`、QM/MM（FIST+Quickstep PM6）、`&COLVAR &COMBINE_COLVAR &DISTANCE`、`&MOTION &FREE_ENERGY &METADYN SCALE/WW/NT_HILLS`、`&WALL QUADRATIC`（WALL_PLUS/MINUS, K, POSITION）、输出 `cp2k-COLVAR/HILLS.metadynLog`、CP2K 可不同 CV 宽度、WALL 仅 CP2K 有（A20–A24 / 字幕）。
- 【新增】大量文献案例与 DOI（A8, A13, A20）。

**电子结构 / TRAVIS（PDF 无，仅字幕；与 learn_L4.md 互补）：**
- 【新增】TRAVIS 安装（`make` 生成 EXE）、**必须输出 Wannier 中心**（&LOCALIZE）、交互流程（L2=IR, 0.5 fs, Wannier 方式选1, X原子电荷2）、**必须读 Wannier XYZ 不能读 position**、波数 0–4000 cm⁻¹（B1）——这些为字幕独有实操，learn_L4 未含命令级细节。
- 【新增】电荷差分 VESTA `SUBSTRACT` 操作、2D 切片 lattice plane / 2D data plane、边界调 0~0.1/−0.05~0.05（B2.2）。
- 【新增】平面平均电荷密度 Z 投影 `cube.py` → `charge integration.txt` → B−C−D（B2.3）。
- 【新增】Bader `bader cp2k.cube electronic` → ACF.dat 具体命令；CO/Ni 数值 C+1.64/O−1.85（B2.4）。
- 【新增】PDOS `NLUO/LDOS/COMPONENTS`、高斯展宽脚本 `nw.py`、自旋上下取负画、−10~0 eV 范围（B2.5）。
- 【新增】ELF 公式 0~1、三中心两电子键/电子化合物/非还原性载体应用、切片 0~1(或0~0.8)（B2.6）。
- 【新增】MO_CUBE `N_LUMO/N_HOMO`、Hartree→eV ×27.211（B2.7）。
- 【新增】功函数 Φ=E_vac−E_Fermi、SURFACE_DIPOLE_CORRECTION、实例 0.3158−0.1224=5.26 eV（B2.8）。
- 【新增】分子表面 ESP 0.001/0.002 a.u.（B2.9）。

> 即：`course_notes.md` 的 A4/A5 仅为索引级，本文件与 learn_L4.md 共同补齐了**全部公式、参数表、脚本命令、数值案例、文献、操作流程**。

---

# D. PDF（L5.txt）页码覆盖清单

| 页 | 主题 | 已处理 |
|---|---|---|
| 1 | 版权声明 | ✅ A0 |
| 2 | 封面/大纲（主讲刘锦程；PMF/Slow-growth/Metadynamics） | ✅ A1 |
| 3 | 为什么 AIMD 算 FES（CI-NEB 4 局限） | ✅ A2 |
| 4 | 稀有事件 / 阿伦尼乌斯 k=Ae^(−Ea/RT) | ✅ A3 |
| 5 | 正则系综 / 亥姆霍兹自由能 A(N,V,T) | ✅ A4 |
| 6 | 限制性 constrained AIMD，A(ξ) | ✅ A5 |
| 7 | PMF 数学：dA/dξ 积分，黑=PMF 红=积分 | ✅ A6 |
| 8 | 方法一 PMF 原理 / VASP 手册 | ✅ A6 |
| 9 | collective variables (CV) | ✅ A7 |
| 10 | 文献案例 PMF（Cu 单原子吸附） | ✅ A8 |
| 11 | 文献案例 PMF（表面电催化溶剂） | ✅ A8 |
| 12 | 文献案例 PMF（Au-CO 动态） | ✅ A8 |
| 13 | VASP ICONST 文件（FLAG/STATUS） | ✅ A9 |
| 14 | ICONST 实例（R/A/T/多 R） | ✅ A9 |
| 15 | ICONST 组合 CV（S 1.1.-1） | ✅ A9 |
| 16 | 实例 H₂CO₃ 碳酸分解 PMF（nebmake 插点） | ✅ A10 |
| 17 | INCAR（MDALGO=2, LBLUEOUT, ICONST） | ✅ A10 |
| 18 | REPORT `b_m` 行 / grep b_m | ✅ A10 |
| 19 | Origin Statistics on Column | ✅ A10 |
| 20 | 对 PMF 积分得 A（Y error） | ✅ A10 |
| 21 | 成品图 ~1.3 eV，插点越密越准 | ✅ A10 |
| 22 | 方法二 Slow-growth（Sprik 1998，~1.5 eV） | ✅ A11 |
| 23 | Slow-growth 步骤（INCREM=0.0005, 10000 步） | ✅ A11 |
| 24 | Slow-growth 技巧（反向/调结构/平均） | ✅ A11 |
| 25 | Slow-growth 应用（Pt 溶解配位数 CV） | ✅ A11 |
| 26 | 方法三 Metadynamics 标题 | ✅ A12 |
| 27 | Metadynamics 原理（biased=unbiased+高斯） | ✅ A12 |
| 28 | 文献案例 metadyn（*CHOH 路径） | ✅ A13 |
| 29 | 文献案例 metadyn（Al³⁺ 脱出） | ✅ A13 |
| 30 | 文献案例 metadyn（CH₄ Cu₈ C-H 活化） | ✅ A13 |
| 31 | metadyn INCAR（MDALGO=21, HILLS_H/W/BIN） | ✅ A14 |
| 32 | 实例 N₂ 解离吸附（Ru(0001), CV1/CV2） | ✅ A15 |
| 33 | 配位数 CV 设定（R/D/S 写法） | ✅ A15 |
| 34 | D 配位数 / S 键长组合 | ✅ A15 |
| 35 | 配位数公式 ξ=9/14 | ✅ A15 |
| 36 | HILLSPOT 输出 / gaussian.py 用法 | ✅ A16 |
| 37 | 时间轴（7.5–79 ps，极小/TS） | ✅ A17 |
| 38 | CV 震荡 ≥10 次填平 | ✅ A17 |
| 39 | CV 选取技巧（碳酸分解 OH/COOH 分离） | ✅ A18 |
| 40 | 峰高（~1/50 能垒）/ 宽技巧 | ✅ A19 |
| 41 | 不同盆地不同峰（N-N 平宽 / Ru-N 窄） | ✅ A19 |
| 42 | 重启 PENALTYPOT / well-tempered / 不 3D / 互证 | ✅ A19 |
| 43 | 练习 CP2k（Cyclohexaphenylene, 文献） | ✅ A20 |
| 44 | QM(PM6)/MM(EAM) / CI-NEB 脱氢 | ✅ A20 |
| 45 | cp2k.inp `&MULTIPLE_FORCE_EVALS` / `&MAPPING` | ✅ A20 |
| 46 | `&FORCE_EVAL` FIST / Quickstep PM6 | ✅ A20 |
| 47 | CP2K `&COLVAR &COMBINE_COLVAR &DISTANCE` | ✅ A21 |
| 48 | CP2K `&MOTION &FREE_ENERGY &METADYN` + `&WALL` | ✅ A22 |
| 49 | Cu VDW / C,H VDW+dynamicBonds | ✅ A23 |
| 50 | 输出 `cp2k-COLVAR/HILLS.metadynLog` 列格式 | ✅ A23 |
| 51 | `gaussian.py 2 1 6 0 5` 等高线图 | ✅ A23 |
| 52 | WW/SCALE 公式（history dependent term） | ✅ A24 |
| 53 | 版权声明 | ✅ A0 |

**53/53 页全部覆盖。**

---

## 附：关键公式速查
- 阿伦尼乌斯：$k = A e^{-E_a/RT}$（A≈10¹³ s⁻¹；0.75 eV@300K≈1 s）
- 亥姆霍兹自由能：$A(N,V,T) = -k_BT\ln Z$
- PMF：$A(\xi_1)-A(\xi_0)=\int_{\xi_0}^{\xi_1}\frac{dA}{d\xi}d\xi$，PMF=$\langle dA/d\xi\rangle$
- 蓝月 REPORT：`lambda |z|^(-1/2) GkT |z|^(-1/2)*(lambda+GkT)`
- Metadynamics（通用）：$V(s)=\sum_i h\exp(-|s-s_i|^2/2w^2)$
- CP2K 偏置势：$WW\sum_{j}\prod_k\exp[-0.5((ss-ss0(k,j))/SCALE(k))^2]$
- 配位数公式：平衡时 ξ=9/14（两个高斯比值 $1-(r/d)^9 / 1-(r/d)^{14}$）
- 功函数：$\Phi = E_{vac} - E_{Fermi}$（实例 0.3158−0.1224=5.26 eV）
- 轨道能级换算：Hartree → eV 乘 **27.211**
- 分子表面 ESP 等密度面：气相 0.001 a.u. / 凝聚态 0.002 a.u.
