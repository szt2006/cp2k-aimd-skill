# 庚子计算《AIMD 与 CP2K》第 4 天资料 — 全面逐页学习与交叉对照

> 源文件：
> - PDF 文本：`references/pdf_text/L4.txt`（`庚子计算-AIMD与CP2K讲义-4 - 副本.pdf`，**64 页**）
> - 字幕：课程资料目录中的 `4.txt`（庚子计算《AIMD与CP2K》讲义+字幕，**4537 行**）
> - 已有笔记：`course_notes.md`、`course_survey.md`
> 整理时间：2026-07-19

---

## ⚠️ 0. 重要歧义声明（请先读）

任务描述把"第 4 天"的主题写成 **过渡态搜索/NEB、AIMD 频率、BSSE 与基组、表面氧化、Au20 团簇**。但逐文件精读后发现**编号严重错位**：

1. **`L4.txt` PDF 实际讲的是"电子结构分析"**，内容主题与 `course_survey.md §2` 归给**第 5 天**的"ELF / PDOS / 电荷差分 / 振动光谱(TRAVIS)"完全一致：
   - TRAVIS 计算 IR 光谱、Wannier 中心
   - 电荷密度 / 自旋电荷密度 / 电荷密度差分
   - 原子电荷（Bader / Lowdin / Hirshfeld / Mulliken）
   - 态密度 PDOS
   - 电子局域函数 ELF、分子轨道 MO cube
   - 静电势 ESP / 功函数 Work Function
   - 以及 3 条计算警告、OT 收敛技巧
   **PDF 中完全没有 NEB、没有频率计算、没有 BSSE、没有 Au20。**

2. **字幕 `4.txt` 才是真正的"第 4 天"**，覆盖 NEB/CI-NEB、频率计算、表面氧化（Cu/TiO₂/Au20）、基组与赝势、DFT-D3、DFT+U、磁性、QM/MM、杂化泛函——与任务描述主题吻合。字幕末尾（约 4525 行）明确说"明天去讲 TRAVIS…电子结构分析方法"，印证电子结构分析在"第 5 天"，而 PDF `L4.txt` 正是这部分内容 ⇒ **PDF `L4.txt` 标号为 4，实为第 5 天讲义**。

3. **BSSE 在 `L4.txt` 与 `4.txt` 中均未出现**（对两文件做 `BSSE|BSS|基组叠加|叠加误差` 全文检索，零命中）。`course_notes.md` 的 B2 经验"CP2K 高斯基组有 BSSE、吸附能比 VASP 偏大"在现有两份字幕/PDF 文本中**无法直接溯源**（可能来自讲师口头补充、或课程其他段落、或笔记作者归纳，需进一步核对）。**任务描述里的 BSSE 主题在当前给定的两份文件里都找不到。**

**结论**：本文件以 `L4.txt` PDF 为逐页提取主体（因任务明确要求"逐页读 PDF"），§A 为 PDF 全量提取；§B 用字幕 `4.txt` 做交叉对照并列出"仅字幕有"的实操补充；§C 标注 `course_notes.md` 缺口。凡任务期望的 NEB/频率/BSSE/Au20 内容，实际只在**字幕**里，见 §B。

---

# A. PDF（L4.txt）逐主题全量提取（共 64 页）

> 按主题重组，保留原文公式、参数表、脚本名、文献。每节标注对应页码。

## A0. 版权声明页（P1、P64）
- 研之成理 AIMD 与 CP2K 课程学习圈；版权归研之成理(杭州)网络科技有限公司。
- 仅限学员个人学习，不得翻录/复制/传播/出售；举报盗版奖励免费正版课程 + 500 元现金。
- P1 与 P64 内容相同（首尾声明）。

---

## A1. TRAVIS 计算红外（IR）振动光谱（P2–P8）

### A1.1 TRAVIS 是什么（P2）
- TRAVIS = **Trajectory Analyzer and Visualizer**，轨迹分析与可视化程序。
- 官网：https://www.cp2k.org 、http://www.travis-analyzer.de 、https://brehm-research.de
- 德国 **Martin Brehm** 课题组开发，专为 CP2K 的 MD 模拟后处理而生，尤其擅长振动光谱。
- 可计算：**infrared (IR)、Raman、vibrational circular dichroism (VCD)、Raman optical activity (ROA)**。

### A1.2 TRAVIS 安装（P3）
- 下载源代码；有 Win 预编译版。
- 用 GNU C++ 编译器，`make` 直接编译，无需修改。
```makefile
# Your C++ compiler
CXX = g++
```
- 在 `exe/` 下生成可执行文件，例如：
  `~/apps/travis-src-200504-hf2/exe/travis -p water_wannier.xyz`

### A1.3 CP2K + TRAVIS 算 IR 第一步：AIMD 输出 Wannier 中心（P4）
- 在 `FORCE_EVAL/DFT/` 里设 `LOCALIZE`：
```text
&LOCALIZE
  METHOD CRAZY
  &PRINT
    &WANNIER_CENTERS
      FILENAME = wannier.xyz
      &EACH
        MD 1        # 每个 MD 步骤都输出 wannier 中心轨迹
      &END
    &END
  &END
&END LOCALIZE
```
- `IONS+CENTERS`：在轨迹文件同时输出**原子坐标**和 **Wannier 孤对电子(X)位置**。
- 其他参数同正常 AIMD；跑得越长光谱越准。

### A1.4 wannier.xyz 文件格式（P5）
- 以 XYZ 格式同时输出原子坐标 + Wannier 中心(X)，可直接被 TRAVIS 读取用于模拟偶极矩变化。
- 示例（13 Particles + Wannier centers, Iteration:1_0）：
```text
13
Particles+Wannier centers. Iteration:1_0
H   0.8475400000  0.0347400000  1.0345300000
C   0.3504800000  0.0067500000  0.0608400000
H   0.6350700000  0.8927600000 -0.5200600000
H   0.6629400000 -0.8933800000 -0.4828300000
O  -1.0108300000 -0.0082300000  0.3643900000
H  -1.4852000000 -0.0326300000 -0.4568500000
X  -1.2528419315 -0.0215972485 -0.0983108307
X  -1.0589004435 -0.2725462315  0.4997402423
X  -1.0668135257  0.2604099419  0.4875935596
X   0.5633305803 -0.6060535347 -0.3129155542
X  -0.4892919965 -0.0033936899  0.2128858495
X   0.5444857259  0.6095972585 -0.3382963438
X   0.6959346227  0.0255362399  0.7138015652
```

### A1.5 TRAVIS 计算 IR 第二步：运行（P6）
```bash
~/apps/travis-src-200504-hf2/exe/travis -p wannier.xyz
```
- 参考算例 `.log`，交互式输入：
  - `Are the 3 cell vectors of the same size (yes/no)? [yes]`
  - `Enter length of cell vector in pm: 782` （输入晶胞大小）
  - `Which functions to compute (comma separated)? Ir` （光谱类型）
  - `Enter the physical time distance between successive trajectory frames in fs: [0.5] 0.5` （时间步长）
  - `The following dipole modes can be set for all molecules at once: 1, 5, 6, 7, 8`
  - `Which dipole mode to set for all molecules at once? [none] 1` （第一种模式）
  - `Enter the correlation depth of the ACF (in trajectory frames): [3115]` （自相关深度）
  - `Compute IR spectrum of whole system (y/n) [no] y` （计算整体 IR 光谱）

### A1.6 TRAVIS 绘图（P7）
- 生成两个文件：
  - `ir_spectrum_global.csv` — 整体红外振动光谱
  - `ir_spectrum_H2O.csv` — 指定分子片段的振动光谱
- 导入 Origin 绘图（X 轴 Wavenumber cm⁻¹）。

### A1.7 替代方案：直接输出体系 Dipole（P8）
- CP2K 官网另有直接输出体系 Dipole 算 IR 的方法（结果"并不好用"，可自学尝试）：
  - https://www.cp2k.org/exercises:2018_ethz_mmm:infrared_2018
  - https://www.cp2k.org/exercises:2014_ethz_mmm:infra_red
- 关键字：`FORCE_EVAL / DFT / PRINT / MOMENTS`

---

## A2. 电荷密度（Charge density）cube（P9）
- 关键字：
```text
FORCE_EVAL/DFT/PRINT
& E_DENSITY_CUBE
  STRIDE 2 2 2          # 默认 2 2 2，间隔输出，文件小、画图粗糙
  FILENAME cube         # 文件名称
  # STRIDE 1 1 1        # 每个点都输出，画图精细，文件大
&END E_DENSITY_CUBE
```
- 只需**单点计算**。
- 输出两个文件：
  - `cp2k-cube-ELECTRON_DENSITY-1_0.cube`（电荷密度）
  - `cp2k-cube-SPIN_DENSITY-1_0.cube`（自旋密度）
- 直接看电荷密度基本看不出有用信息，需进一步做电荷密度差分、原子电荷布局等。

---

## A3. 自旋电荷密度（Spin charge density）（P10）
- 练习：计算带 H 吸附的 **TiO₂(110)** 表面的自旋电荷密度。
- VESTA 打开 `cp2k-cube-SPIN_DENSITY-1_0.cube`。
- 示例：
  - H–TiO₂(111)：电子从 H 转移到表面 Ti 上
  - Au–CeO₂(111)：电子从 Au 转移到表面 Ce 上
- 文献：Wang, Y. G., et al. (2015) *Nat Commun* **6**: 6511.

---

## A4. 电荷密度差分（Charge density difference）（P11–P16）

### A4.1 两种计算方式（P11）
**(1) 体系密度减各片段密度：**
```
∆ρ = ρ_AB − ρ_A − ρ_B
```
**(2) SCF 收敛后体系电荷密度减各原子自由态球对称电荷密度（变形电荷密度 Deformation charge density）：**
```
∆ρ = ρ_self-consistent(AB) − ρ_atomic(AB)
```

### A4.2 练习：CO/Ni(100) 电荷差分（P12–P13）
- 步骤一：优化 CO/Ni(100) 结构。
- 步骤二：分别计算 CO/Ni(100)、Ni(100)、CO 的**单点能**（结构从 CO/Ni(100) 直接截取，**不要再结构优化**；计算参数保持不变）。
- 步骤三：用 VESTA 依次导入三个片段的 cube 文件。
- 公式：`r = r(CO/Ni) – r(CO) – r(Ni)`（先导入整体 cube，再减两个片段 cube）。

### A4.3 显示控制（P14）
- 控制电荷密度等值面：数值（原子单位 e/bohr³）、颜色、透明度。

### A4.4 平面平均电荷差分密度图（Planar-Average，P16）
- 对 XY 平面内的格点做平均，画随 Z 变化的曲线：
```bash
python ./cube.py cp2k-cube-ELECTRON_DENSITY-1_0.cube
```
- 三个 cube 分别做线，再 `ab − a − b` 得电荷差分的 Planar-Average。

---

## A5. 原子电荷（Atomic charge）：Bader / Lowdin / Hirshfeld / Mulliken（P17–P24）

### A5.1 定义与种类（P17）
- 原子电荷 = 核电荷数 − 原子所带电子数。
- 意义：把一定空间内的电荷密度划分给附近一个原子，人为规则定义。
- 特点：**人为划分，不唯一**。
- VASP 可做的种类：
  - **Bader charge**（最常用）
  - Mulliken charge
  - Löwdin charge
  - HIRSHFELD charge
  - NPA charge

### A5.2 Bader 电荷（P18）
- 又称 **AIM (atom-in-molecule)** 电荷；以电子密度的**零通量面**为分界面划分原子空间。
- Henkelman 课题组 Bader 程序可处理 VASP、CP2K 的 CHGCAR 得到 Bader 电荷。
- 下载：http://theory.cm.utexas.edu/henkelman/code/bader/

### A5.3 Bader 原子盆示例（P19）
- Al 的原子盆 +2.45 |e|；O 的原子盆 −1.64 |e|
- CO 中 O 的原子盆 +1.83 |e|；C 的原子盆 −1.83 |e|

### A5.4 Bader 计算命令（P20）
```bash
bader cp2k-cube-ELECTRON_DENSITY-1_0.cube
```
- 成功生成：`ACF.dat`、`BCF.dat`、`AVF.dat`（Bader 电荷在 **ACF.dat**）。
- 总电子数在 ACF.dat。
- 自旋电荷布局：`bader cp2k-cube-SPIN_DENSITY-1_0.cube`

### A5.5 练习：CO/Ni(100) Bader（P21–P22）
- 步骤一：优化 CO/Ni(100) 结构。
- 步骤二：算 CO/Ni(100) 单点能，输出电荷密度（`&E_DENSITY_CUBE FILENAME Dentity_maybeSpin.cube STRIDE 1 1 1`）。
- 步骤三：`bader cp2k-cube-ELECTRON_DENSITY-1_0.cube` → ACF.dat。
- ACF.dat 给出：笛卡尔坐标、电子数、原子盆体积、原子核到原子盆边界最小距离。
- 净电荷示例（基组 q 值决定核电荷数）：
  - C 用 q4：`4 − 2.36 = +1.64 |e|`
  - O 用 q6：`6 − 7.86 = −1.86 |e|`
  - Ni 用 q18：`18 − 17.94 = +0.06 |e|`

### A5.6 Bader 着色结构图（P23）
- 补充：按 Bader 原子电荷着色结构图 https://mp.weixin.qq.com/s/BNzjhz8SI_HXkaEnyL29Bg

### A5.7 Lowdin / Hirshfeld / Mulliken（P24）
```text
FORCE_EVAL/DFT/PRINT
&LOWDIN    SILENT  FILENAME lowdin      # cp2k-lowdin-1.lowdin
&HIRSHFELD SILENT  FILENAME hirshfeld  # cp2k-hirshfeld-1.hirshfeld
&MULLIKEN  SILENT  FILENAME Mulliken    # cp2k-Mulliken-1.mulliken
```
- 输出：Net charge（净电荷）、Spin moment（自旋电荷）。
- CO/Ni(100) 各方法电荷对比表（Ni / C / O）：

| 方法 | Ni | C | O |
|---|---|---|---|
| Bader | +0.06 | +1.64 | −1.86 |
| Lowdin | −0.062 | +0.239 | +0.138 |
| Hirshfeld | −0.630 | +0.947 | −0.240 |
| Mulliken | −0.327 | +0.443 | −0.076 |

---

## A6. 态密度（PDOS）计算（P25–P26）

### A6.1 关键字（P25）
```text
FORCE_EVAL/DFT/PRINT
&PDOS
  NLUMO -1          # 包括的空轨道总数；-1 代表全部包括
  # COMPONENTS      # 按量子数拆分密度
  &LDOS
    LIST 1..26      # 合并输出几个原子的 PDOS
  &END LDOS
&END PDOS
```
- 生成：`cp2k-ALPHA_k1-1.pdos`、`cp2k-BETA_k1-1.pdos` … 每个原子的 PDOS。
- 费米能级示例：`# Projected DOS for atomic kind Ni1 at iteration step i = 0, E(Fermi) = 0.122425 a.u.`
- 列：`MO Eigenvalue [a.u.]  Occupation  s  p  d  f`（轨道本征值 / 占据数 / 轨道角动量 pdos）。

### A6.2 画 DOS（P26）
- pdos 文件只有轨道能级信息，画图需加**高斯展宽**：
```bash
python new.py -s 0.01 cp2k-ALPHA_k26-1.pdos cp2k-BETA_k26-1.pdos > dos.txt
```
- `-s 0.01` 调整展宽 sigma；Spin up / Spin down 分别处理；Origin 绘图。

---

## A7. 电子结构分析案例（P27–P32）
- **案例一（P27）**：研究相互作用模型 — Ce 4f 空轨道、电荷差分、O–Au 作用、Ce 4f 占据一个局域电子（共价作用 / 电子转移）。文献：*J. Am. Chem. Soc.* **2009**, *131*, 10473–10483.
- **案例二（P28）**：研究缺陷态 — TiO₂ 中 Al 缺陷导致多余空穴在表面 O 上。文献：*J. Magn. Magn. Mater.* **404** (2016) 7–13.
- **案例三（P29）**：研究表面态（带边位置计算）— GaN 表面配位不饱和原子 DOS 在带隙出现新表面态。文献：*ACS Appl. Mater. Interfaces* **2018**, *10*, 17419−17426.
- **案例四（P30）**：新材料电子结构（对比周期性与孤立体系 DOS）— 反夹心化合物。DOI: 10.1021/acs.inorgchem.8b02263.
- **案例五（P31）**：吸附分子与载体相互作用模型 — CO/Ni，CO 的 s 轨道能量降低、p* 轨道能量上升（s 配位 + 反馈 π 键）。图示：p* ↑、E、f、s。
- **案例六（P32）**：催化吸附轨道相互作用模型（部分活化的 N₂）— Fe₃：low charge state (0.59 |e|)、high spin polarization (10 mB)；d–p* 相互作用使电荷从 Fe 转移到 N₂ 的 p* 轨道。文献：*Nat. Commun.* **2018**, *9*, 1610.

---

## A8. 电子局域函数 ELF（P33–P41）

### A8.1 定义与应用（P33）
- Electron Localization Function (ELF)：展现三维实空间不同位置电子定域程度，易计算、易图形分析。
- 应用：有机/无机小分子、晶体、固体表面、配位化合物、团簇、二维量子点、芳香性、氢键、金属键、多中心键、反应机理。
- 文献：物理化学学报 2011, 27(12), 2786–2792.

### A8.2 数学（P34–P35）
- `D(r)`：Pauli 动能密度（超额动能密度，体现费米穴大小）。`G(r)` 或梯度动能密度（Weizsäcker 泛函，无 Pauli 互斥时的动能密度）。
- Becke 把 `D(r)` 投影到 [0,1]：**数值越大定域程度越高**。
  - `ELF(r) = 0`：等同非相互作用均匀电子气，电子完全离域。
  - `ELF(r) = 1`：电子完全定域。
  - **`ELF(r) > 0.5`**：共价键、孤对电子、内层电子、多中心键出现的区域。
- 文献：A. D. Becke and K. E. Edgecombe, *J. Chem. Phys.* **92**, 5397 (1990)；卢天, 陈飞武, 物理化学学报, 27, 2786–2792 (2011).

### A8.3 ELF 案例（P36–P40）
- **P36** H₂ 异裂催化反应过渡态：O–H 共价键成分高，Ce–H 更强离子成分。ACS Catal. 2018, 8, 546−554.
- **P37** FeB₆ 二维材料：中间三个 B 之间更红（可能有三中心键）；Fe–B 有蓝色成分（Fe 可能呈离子态）。J. Am. Chem. Soc. 2016, 138, 5644−5651.
- **P38** 电子化合物 Na₂He（electride）：电子对可独立于原子核孤立存在、定域化程度高区域。ACS Catal. 2018, 8, 546−554.
- **P39** 缺陷态：ZrO₂ / HfO₂ / ThO₂ 表面氧缺陷使电子对局域在空穴位置。J. Phys. Chem. C 2016, 120, 17514−17526.
- **P40** 分子团簇 B₁₃：外围 B–B 强共价键，中心 3 个 B 可能有 3 中心键。物理化学学报 2018, 34(5), 503–513.

### A8.4 CP2K 计算 ELF（P41）
```text
FORCE_EVAL/DFT/PRINT
&ELF_CUBE
  FILENAME elf
  STRIDE 1 1 1
&END
```
- 输出：`cp2k-elf-ELF_S1-1_0.cube`、`cp2k-elf-ELF_S2-1_0.cube`（可看孤对电子、配位键）。

---

## A9. 分子轨道 MO cube（P42–P43）

### A9.1 关键字（P42）
```text
FORCE_EVAL/DFT/PRINT
&MO_CUBES
  NHOMO -1
  NLUMO -1
  FILENAME MO
  STRIDE 1 1 1
&END MO_CUBES
```
- `STRIDE 1 1 1` 每点都输出（默认 2 2 2 间隔、文件小、粗糙）；`1 1 1` 更精细。
- `NHOMO`/`NLUMO` 一般只看费米能级附近，不需 −1 全输出。
- 输出：`cp2k-MO-WFN_00001_1-1_0.cube` 等。

### A9.2 能级示例（P43）
```
Energy Level /a. u.
 0.33291
-0.05825  -0.05822
-0.30822
-0.40726  -0.40726
-0.50286
-1.04822
```

---

## A10. 静电势 ESP / 功函数 Work Function（P44–P56）

### A10.1 静电势定义（P44）
- 衡量 r 处单位点电荷与体系的静电相互作用势。
- 第一性原理中：接近原子核处为负值，远离原子核的真空中为 0。

### A10.2 N₂ 静电势（P45）
- 氮气分子范德华表面静电势：N 端（电子占主导）为负、N≡N 中间（原子核占主导）为正。
- **VASP 算得真空能级不为 0，需把真空能级 shift 到 0，静电势绝对值才有意义。**

### A10.3 功函数定义（P46）
- 功函数（Work function / 逸出功）：使一粒电子立即从固体表面逸出所需最小能量（eV）。
- 不是材料体相本征性质，而是**表面性质**（暴露晶面、受污染程度）。

### A10.4 功函数公式（P47）
```
Φ = E_vac − E_F
```
- 从计算角度：功函 = 真空能级 − 费米能级（第一性原理程序把 VBM 当费米能级，与实验略有不同）。
- 计算：在 slab 法向（z 方向）取静电势分布。

### A10.5 VASP 算功函数（P48）
- `INCAR` 设 `LVHAR = .TRUE.` 输出静电势文件 `LOCPOT`（格式同 CHGCAR）。
- 若 `LVTOT = .TRUE.` 且 `LVHAR = .FALSE.`，`LOCPOT` 是包含静电势 + 交换关联势的**总势**。

### A10.6 CP2K 算静电势与功函数（P49）
```text
&DFT
  SURFACE_DIPOLE_CORRECTION T
  SURF_DIP_DIR Z
  ...
  &PRINT
    &V_HARTREE_CUBE
      FILENAME hartree
      STRIDE 1 1 1
    &END V_HARTREE_CUBE
  ...
```
- 实例数值：
  - 真空能级 = 0.3158 a.u.
  - `grep Fermi cp2k.out` → 费米能级 = 0.12242 a.u.（算 pdos 时输出）
  - **Φ = E_vac − E_F = 5.26 eV**
- 若真空层静电势不平（上下表面不对称、严重），需做**偶极校正**。

### A10.7 异质结静电势分析（P50–P51）
- 静电势不仅算功函数，也是分析表面电子结构利器；可预测异质结电子流向：
  - 例：Φ = 5.22 eV 与 Φ = 6.43 eV 两材料。文献：*Phys. Chem. Chem. Phys.* **2016**, *18*, 31175–31183.
- TiO₂/g-C₃N₄ 异质结：电子从 g-C₃N₄ 转移到 TiO₂（与电荷差分结果一致）。

### A10.8 表面负载团簇电子流向（P52）
- 文献：*J. Am. Chem. Soc.* **2013**, *135*, 10673–1052683（注：原文页码转录疑似有误，应为 10673–10683 量级）。

### A10.9 分子表面静电势（扩展内容，P53）
- 最常用分子表面 = **范德华表面**（一定电荷密度的表面）。
  - 气相分子：`r = 0.001 a.u. = 0.00675 e/Å³`
  - 凝聚相：`r = 0.002 a.u. = 0.0135 e/Å³`
  - 换算：`1 a.u. = 1 e/Bohr³ = 6.748 e/Å³`
- N₂ 范德华表面静电势可反映分子/材料表面电子结构特征（孤对电子、离域 π 键）。

### A10.10 范德华表面 ESP 案例（P54）
- 受阻路易斯酸碱对（frustrated Lewis pair）异裂活化 H₂：Ce 亲电位点、O 亲核位点；H₂ 靠近时极化。*Nature Communications* **2017**, *8*: 15266.

### A10.11 VESTA 练习：O/Au(111)-p(2×2) 静电势（P55–P56）
- (1) VESTA 导入 `cp2k-cube-ELECTRON_DENSITY-1_0.cube`，选 `Edit – Lattice Planes`。
- (2) `surface coloring` 里导入 `cp2k-hartree-v_hartree-1_0.cube`。
- (3) `Properties – Isosurface` 调电荷密度表面数值 `0.002 e/Bohr³`。
- 判读：**越红静电势更低 → 易受亲电试剂进攻；越蓝静电势更高 → 易受亲核试剂进攻。**

---

## A11. 空页（P57–P60）
- 4 页全空（仅页眉"研之成理AIMD与CP2K课程学习圈"）。无内容。

---

## A12. 计算警告：EMAX_SPLINE 太小（P61）
```text
WARNING| Particles: 208 31 at distance [au]: 0.00000058 less than: 0.01889726; increase EMAX_SPLINE.
*******************************************************************************
* [ABORT] GEOMETRY wrong or EMAX_SPLINE too small! *
* fist_neighbor_lists.F:607 *
```
- 含义：两个原子（208 与 31）距离过小（0.00000058 au < 0.01889726 au），需调大 `EMAX_SPLINE`。

## A13. 计算警告：RESTART wfn 不存在（P62）
```text
*** WARNING in qs_initial_guess.F:280 :: User requested to restart the wavefunction
from the file named: ./cp2k-RESTART.wfn. This file does not exist. Please check
the existence of the file or change properly the value of the keyword
WFN_RESTART_FILE_NAME. Calculation continues using ATOMIC GUESS. ***
```
- 处理：文件不存在时自动改用 **ATOMIC GUESS**，计算继续。

## A14. OT 收敛技巧（P63）
```text
&OT
  # MINIMIZER DIIS
  MINIMIZER CG       # 比默认 STRICT 快 5–20%，但有时稳定性不好
  # ALGORITHM IRAC
  LINESEARCH 2PNT    # 大多数 2PNT 即可；大体系有时需 3PNT
  PRECONDITIONER FULL_ALL   # 极难收敛体系可能需 GOLD
  # ENERGY_GAP 0.001
&END OT
```
- 用 DIIS 可能速度更快；CG 速度比默认 STRICT 快 5–20% 但稳定性差。

---

# B. 字幕（4.txt）交叉对照

> 字幕 `4.txt` 是真正"第 4 天"内容（NEB/频率/表面氧化/Au20/基组…），与 PDF `L4.txt` 主题**几乎不重叠**。下面分三部分：字幕覆盖主题清单、仅字幕有而 PDF 没有的实操补充、字幕中与 PDF 电子结构呼应的部分。

## B1. 字幕覆盖的"第 4 天"主题（PDF 中均无）
1. **过渡态搜索 NEB / CI-NEB**（行 ~10–1001）：过渡态=势能面一阶鞍点；并非所有反应都有过渡态（离子键断裂、自由基生成、部分物理吸附无）；解离吸附必有。
2. **NEB 方法原理**（"珠子+弹簧"直觉，行 ~227–298）：弹簧两作用（保持珠子间距、使链落在反应路径）；弹簧引入额外受力会拉偏最高点 → NEB 投影掉垂直分量；CI（climb image）放开能量最高点的受力使其自动爬到一阶鞍点。
3. **CI-NEB vs 传统 NEB**（行 ~306–360）：CI-NEB 能量最高点更准、可少插点；插点数按初末态距离定，经验 4–5 个；太近 3 个、远则 6–7 个。
4. **ITNEB 算法**（行 ~568–580）：初插点结构不合理时先 ITNEB 算几步（如 5 步）再开 CI，更稳定。
5. **NEB 输入与操作**（行 ~463–705）：`MOTION & BAND`，`NPROC_REP`、`REPLICA` 数（初末态+插点）、`RUN_TYPE BAND`、`ALIGN_FRAME`/`ROTATE_FRAME` 对表面体系**必须 false**（仅非周期分子体系才开）、`K_SPRING` 弹簧力常数（粗算取大如 0.08/0.1 易收敛但精度差，收敛后换精确值重算）、`OPTIMIZE_END_POINTS false`（初末态已优化）。
6. **插点脚本 `xyz2neb.pl`**（行 ~426–460）：用法 `xyz2neb.pl 初态.xyz 末态.xyz N`；**坑：要插 4 个点需写 5**（脚本 off-by-one）；生成 0.xyz…5.xyz（0/5 为初末态，中间为插点）；用 `cat` 拼成 `NEB.xyz` 在 VMD 检查线性插点是否合理，出现极短键（如 0.5 Å）需手动平移修正。
7. **NEB 收敛与取过渡态**（行 ~748–976）：收敛信息在 `cp2k-<n>.out`（非主 `cp2k.out`）；四个收敛标准（max displacement / RMS displacement / max force / RMS force）同几何优化；**NEB 收敛更难，可适当放宽**（如 `MAX_FORCE` 由 0.0006→0.001）；用 for 循环取各 replica 末帧 `tail -125` 拼成 `NEB.xyz`，比较各点能量取最高点即过渡态（例：第 3 点）。
8. **频率计算验证过渡态**（行 ~977–1608）：过渡态判据=受力为 0 且二阶导数有**一个虚频**；极小值零虚频；多个虚频则非过渡态。Hessian 矩阵（3N×3N）对质量矩阵变换得力常数矩阵，对角化得频率与振动矢量；非线性分子 3N−6 振动模式，线性 3N−5；固定表面时只算吸附分子（3N 个频率全作结果）。**零点振动能 ZPVE = Σ ½hμ**（谐振子基态能量，0 K 仍存在）。
9. **有限位移法**（行 ~1148–1206）：CP2K **无解析频率，只能有限位移**；每个自由度位移两次 + 中心点 = **6N+1 次计算**；`RUN_TYPE VIBRATIONAL_ANALYSIS`，`DX=0.01`（默认），`INTENSITIES T/F`，`NPROC_PER_VIRTUAL` 并行。
10. **固定原子频率的并行坑**（行 ~1256–1269）：固定部分原子算频率时，必须把并行 image 数设多（每 image 核数写小，如 56 核写 7→同时 8 个并行），否则频率算错。
11. **`cp2k_frequency_to_movie` 出 9 个振动模式**（行 ~1464–1585）：`cp2k_frequency.pl`（判虚频：0=全实频、1=有虚频）；`cp2k_frequency_to_movie cp2k.out last.xyz` 生成 `mode-1…9.xyz`（9 模式，第 1 个为虚频）；虚频振动方向应连接初末态；正常过渡态虚频至少 ~100 cm⁻¹，过小（几个波数）可能是误差（平动/转动混入）。
12. **表面氧化 AIMD 实例**（行 ~15–45, ~2261–2560）：Cu 表面氧化（O₂/CO 插入铜层）；TiO₂ 表面 DFT+U 模拟（文献 2013 JACS，450+ 原子、30 ps）；建模、固定最下两层原子防整体平移；`EPS_SCF ~3×10⁶`（太松→energy drift，太严→慢，平衡在 10⁵–10⁶）；MD 重启（新建文件夹、复制 `-1.restart`/`能量`/`position` 文件、改 sub 提交 restart 文件、关 WFN 频繁输出）；MD 轨迹用 `md_simplify.py` 每 20 帧抽帧。
13. **Au20 团簇稳定性**（行 ~2131–3114）：金字塔形 Au20（顶点/边上/面心 3 类对称不等价 Au）；**质心-原子距离（centroid-to-atom）分析**：若金字塔稳定则距离分布有 3 个峰，引入氧缺陷/多加 O 后结构破坏→分布无序；**需自写 ~67 行 Python `max_center.py`**（读轨迹→算质心到三类原子距离→输出 `distance` 文件→Origin 用 frequency count 画分布）；建议用 anaconda 跑 Python；模拟用 2 fs 步长致结构不稳、只看到 2 个峰（应用 1 fs）。
14. **RDF / MSD 补充**（行 ~2754–3175）：Au–Ti、Au–Au、Ti–O 的 RDF（表面重构判断）；用 RDF 第一/第二配位层做 `RT ln` 算迁移能垒（R=8.314 J/mol/K，600 K，结果转 eV：÷96000）；Au MSD 算迁移率（斜率÷6）；MSD 参考帧平均（多参考帧平方再平均）。
15. **基组与赝势（GPW）**（行 ~3358–3448）：GPW=高斯+辅助平面波；对角化适合金属（OT 不如对角化）；费米-狄拉克 300 K；**q 值表**（氧 q6=2s²2p⁴、钠 q9=2s²2p⁶3s¹、金 q11=5d¹⁰6s¹）；GTH 赝势；高斯基组 DZVP（double-ζ with polarization，如 `dzvp molopt gth q11`）；平面波截断 400 Ry；PBE 泛函；DFT-D3 色散校正。
16. **金属水界面（电催化）**（行 ~3191–3953）：PZC（零电荷电势）、加 Na⁺ 调控电极电势、水分子取向、Z 方向分布、功函数（真空能级−费米能级）相对 SHE（4.44 eV）算真实电势；明天的电子结构分析（PDF 本内容）用来算功函数。
17. **DFT-D3 色散校正**（行 ~4102–4198）：DFT 对长程范德华描述差；DFT-D3（Grimme）设 `XC & VDW_POTENTIAL`、`parameter file name DFTD3.dat`（须复制到当前目录）、截断半径 15 Å；scan+rVV10 需 libxc。
18. **DFT+U**（行 ~4199–4298）：`+ U_METHOD MULLIKEN`、`&DFT_PLUS_U`（只给 D/F 轨道加 U）；有效 U = U − J，单位须写 `[eV]`（默认 a.u. ≈27 eV 会错）；过渡金属正离子态须加 U，金属 Fe/Ni 不用；`URAMPING` 逐步加 U（收敛到 10³ 后每步 +0.1 eV，40 步到目标 4 eV）助收敛。
19. **磁性设置**（行 ~4302–4489）：新版 `MAGNETIZATION` 直接设初猜（同 VASP MAGMOM）；Fe₃O₄ 亚铁磁（二价铁高自旋 4 单电子、三价铁高自旋 5 单电子，四配位 Td 自旋向下、八配位 Oh 自旋向上）→ 三种 Fe 元素分别设 4.0 / 5.0 / −5.0；输出 Mulliken 电荷与自旋矩（spin moment），看自旋电荷密度 cube 判磁性。
20. **杂化泛函 / ADMM**（行 ~4491–4532）：HSE06、`&XC &HF`；ADMM 辅助基组加速杂化泛函，可做几百原子甚至跑 AIMD。
21. **QM/MM 与 metadynamics**（行 ~3954–4068）：2900+ 原子 Cu 表面六连苯脱 H 自组装，QM(上)/MM(EAM,下) 分区；metadynamics 自由能面（"明天讲"）。

## B2. 仅字幕有、PDF 没有的实操补充（知识库应补）
- **NEB "珠子+弹簧"物理直觉**（弹簧两作用、投影掉垂直分量、CI 爬坡）——PDF 完全无 NEB。
- **`xyz2neb.pl` 插点脚本 + off-by-one 坑**（插 4 点写 5）。
- **`K_SPRING` 取值策略**：粗算大值(0.08/0.1)易收敛、精算小值；`ITNEB` 先算几步再开 CI。
- **`ALIGN_FRAME`/`ROTATE_FRAME` 对表面必须 false**。
- **NEB 收敛信息在 `cp2k-<n>.out`、四个标准放宽**；for 循环 `tail -125` 拼 NEB.xyz 取最高点。
- **频率固定原子时并行 image 数须设多**的坑。
- **`cp2k_frequency_to_movie` 出 9 个振动模式、第 1 为虚频、虚频应≥~100 cm⁻¹**。
- **Au20 质心-原子距离分析 + `max_center.py`(~67 行)** 评估金字塔稳定性；2 fs 步长致不稳。
- **RDF 做 RT ln 算迁移能垒**的具体公式与单位换算（÷96000）。
- **DFT+U 的 `URAMPING` 逐步加 U、单位 [eV]**；磁性 `MAGNETIZATION` 三价铁设置。
- **讲师经验**：CP2K 高斯基组 **BSSE 使吸附能比 VASP 偏大**（⚠️ 见 §0.3，此条在 4.txt 全文检索未命中，可能源自其他段落/口头，需核对）。

## B3. 字幕中与 PDF 电子结构主题呼应处
- 字幕末尾（行 ~4525–4532）明确"明天讲 TRAVIS 算 IR、电子结构分析方法"——印证 **PDF `L4.txt` 是第 5 天电子结构讲义**，与字幕 `4.txt`（第 4 天）错开一天。
- 字幕行 ~2404–2418：MD 中**不建议输出 cube 文件**（几十~100 MB/个，撑爆硬盘），只输出 Mulliken 等小体积原子电荷；需电子结构信息时单独取几个结构再算——与 PDF A2/A5/A8 的 cube 流程互补。
- 字幕行 ~4451–4483：算完 Mulliken 电荷后可看 net charge / spin moment，并导出自旋电荷密度 cube 到 VESTA 看黄(↑)/蓝(↓)——与 PDF A3/A5 一致。

---

# C. `course_notes.md` 尚未收录的新内容

> 对照 `course_notes.md`（A1–A5 实操精要）与 `course_survey.md`。

### C1. PDF `L4.txt` 中、course_notes.md 完全未覆盖（应补进知识库）
- **TRAVIS / Wannier 中心 IR 光谱全流程**（A1）：`LOCALIZE METHOD CRAZY` + `WANNIER_CENTERS`、wannier.xyz 格式、`travis -p` 交互选项（cell 782 pm、IR、0.5 fs、dipole mode 1、ACF 3115）、`ir_spectrum_global.csv`/`ir_spectrum_H2O.csv`、替代 `MOMENTS` 法。
- **电荷密度 / 自旋密度 cube**（A2–A3）：`&E_DENSITY_CUBE STRIDE`、TiO₂(110)/TiO₂(111)/CeO₂(111) 自旋转移案例。
- **电荷密度差分两种方法 + Planar-Average**（A4）：`∆ρ = ρ_AB − ρ_A − ρ_B` 与变形电荷密度；`cube.py` 平面平均。
- **Bader 全流程 + q 值净电荷公式**（A5）：Henkelman `bader` 命令、ACF.dat、CO/Ni(100) 示例 `4−2.36=+1.64`、`6−7.86=−1.86`、`18−17.94=+0.06`；Lowdin/Hirshfeld/Mulliken 四方法对比表。
- **PDOS 完整流程**（A6）：`&PDOS NLUMO -1 &LDOS LIST`、`new.py -s 0.01` 高斯展宽。
- **6 个电子结构分析案例文献**（A7）。
- **ELF 数学与 5 个案例 + `&ELF_CUBE`**（A8）：Becke/Edgecombe 原文、ELF>0.5 判据、FeB₆/B₁₃/Na₂He 等。
- **MO cube + 能级示例**（A9）。
- **静电势 / 功函数完整计算**（A10）：`SURFACE_DIPOLE_CORRECTION`、`V_HARTREE_CUBE`、Φ=5.26 eV 实例、VESTA O/Au(111) 流程、范德华表面 ESP 阈值（0.001/0.002 a.u.）。
- **三条计算警告 + OT 技巧**（A12–A14）：`EMAX_SPLINE too small`、`WFN_RESTART_FILE_NAME` 不存在→ATOMIC GUESS、`MINIMIZER CG`/`LINESEARCH 2PNT`/`PRECONDITIONER FULL_ALL`。

### C2. course_notes.md 已涉及、但 PDF 提供了更具体参数/公式（可回链补全）
- course_notes A4 提到 ELF、电荷差分、PDOS 实操，但**未含** cube 关键字细节、Bader q 值公式、功函数 SURFACE_DIPOLE_CORRECTION、EMAX_SPLINE 警告——这些 PDF 独有。
- course_notes A3 提到 `cp2k_frequency_to_movie` 出 9 模式（来自字幕），PDF 未覆盖；但 PDF 覆盖了频率的 ZPVE、`6N+1` 公式（在字幕 B1.8 提取，PDF 无）——属字幕独有。

### C3. 歧义待解（建议后续核对）
- **BSSE**：任务描述与 course_survey 均将 BSSE 列为第 4 天主题，但 `L4.txt` 与 `4.txt` 均未出现；course_notes B2 的 BSSE 经验无法直接溯源，需查其他字幕/PDF 或向讲师核对。
- **编号错位**：PDF `L4.txt` 实为第 5 天电子结构讲义；字幕 `4.txt` 为第 4 天。建议将 `learn_L4.md` 视为"第 5 天电子结构"资料，并另行对字幕 `4.txt` 建立"第 4 天"专题笔记。

---

# D. PDF 页码覆盖清单（确认每页都处理过）

| 页码 | 主题 | 处理 |
|---|---|---|
| P1 | 版权声明 | ✅ A0 |
| P2 | TRAVIS 简介 | ✅ A1.1 |
| P3 | TRAVIS 安装 | ✅ A1.2 |
| P4 | AIMD 输出 Wannier 中心 | ✅ A1.3 |
| P5 | wannier.xyz 格式示例 | ✅ A1.4 |
| P6 | TRAVIS 运行交互选项 | ✅ A1.5 |
| P7 | TRAVIS 输出 csv 绘图 | ✅ A1.6 |
| P8 | 替代 Dipole 法 (MOMENTS) | ✅ A1.7 |
| P9 | 电荷密度 cube | ✅ A2 |
| P10 | 自旋电荷密度 + TiO₂ 案例 | ✅ A3 |
| P11 | 电荷密度差分两种方法 | ✅ A4.1 |
| P12 | CO/Ni(100) 差分步骤 | ✅ A4.2 |
| P13 | CO/Ni(100) 差分公式 | ✅ A4.2 |
| P14 | 等值面显示控制 | ✅ A4.3 |
| P15 | 平面/原子/数值范围选择 | ✅ A4.3（P15 注明选 Miller 指数/三原子/数值范围，归显示控制） |
| P16 | Planar-Average 电荷差分 | ✅ A4.4 |
| P17 | 原子电荷定义与种类 | ✅ A5.1 |
| P18 | Bader 电荷原理与程序 | ✅ A5.2 |
| P19 | Bader 原子盆示例 | ✅ A5.3 |
| P20 | bader 命令与输出 | ✅ A5.4 |
| P21 | CO/Ni(100) Bader 练习 | ✅ A5.5 |
| P22 | ACF.dat 与 q 值净电荷 | ✅ A5.5 |
| P23 | Bader 着色结构图 | ✅ A5.6 |
| P24 | Lowdin/Hirshfeld/Mulliken + 对比表 | ✅ A5.7 |
| P25 | PDOS 关键字 | ✅ A6.1 |
| P26 | PDOS 高斯展宽绘图 | ✅ A6.2 |
| P27 | 案例一 Ce 4f | ✅ A7 |
| P28 | 案例二 TiO₂ Al 缺陷 | ✅ A7 |
| P29 | 案例三 GaN 表面态 | ✅ A7 |
| P30 | 案例四 反夹心化合物 | ✅ A7 |
| P31 | 案例五 CO/Ni DOS | ✅ A7 |
| P32 | 案例六 Fe₃ N₂ | ✅ A7 |
| P33 | ELF 简介 | ✅ A8.1 |
| P34 | ELF 数学 (D(r)) | ✅ A8.2 |
| P35 | ELF 定义与判据 | ✅ A8.2 |
| P36 | ELF 案例 H₂ 异裂 | ✅ A8.3 |
| P37 | ELF 案例 FeB₆ | ✅ A8.3 |
| P38 | ELF 案例 Na₂He | ✅ A8.3 |
| P39 | ELF 案例 ZrO₂/HfO₂/ThO₂ | ✅ A8.3 |
| P40 | ELF 案例 B₁₃ | ✅ A8.3 |
| P41 | CP2K 算 ELF cube | ✅ A8.4 |
| P42 | MO cube 关键字 | ✅ A9.1 |
| P43 | 能级示例 | ✅ A9.2 |
| P44 | 静电势定义 | ✅ A10.1 |
| P45 | N₂ 静电势 + VASP 真空能级 | ✅ A10.2 |
| P46 | 功函数定义 | ✅ A10.3 |
| P47 | 功函数公式 Φ=E_vac−E_F | ✅ A10.4 |
| P48 | VASP 算功函数 (LVHAR/LOCPOT) | ✅ A10.5 |
| P49 | CP2K 算静电势/功函数 + 实例 5.26 eV | ✅ A10.6 |
| P50 | 异质结静电势 | ✅ A10.7 |
| P51 | TiO₂/g-C₃N₄ 电子转移 | ✅ A10.7 |
| P52 | 表面负载团簇电子流向 | ✅ A10.8 |
| P53 | 分子表面 ESP（vdW 阈值） | ✅ A10.9 |
| P54 | 受阻 Lewis 对 ESP 案例 | ✅ A10.10 |
| P55 | VESTA O/Au(111) 练习(1) | ✅ A10.11 |
| P56 | VESTA 练习(2) 判读红/蓝 | ✅ A10.11 |
| P57 | 空页 | ✅ A11 |
| P58 | 空页 | ✅ A11 |
| P59 | 空页 | ✅ A11 |
| P60 | 空页 | ✅ A11 |
| P61 | 警告 EMAX_SPLINE | ✅ A12 |
| P62 | 警告 RESTART wfn 不存在 | ✅ A13 |
| P63 | OT 收敛技巧 | ✅ A14 |
| P64 | 版权声明 | ✅ A0 |

**全部 64 页均已覆盖**（P57–P60 为空页已确认）。

---

# E. 一句话总结（供速览）
PDF `L4.txt` 实为**第 5 天电子结构讲义**（TRAVIS-IR、电荷密度/Bader/PDOS/ELF/MO/静电势-功函数 + 3 条警告 + OT 技巧），与任务描述"第 4 天 NEB/频率/BSSE/Au20"**主题完全错配**；真正第 4 天内容在字幕 `4.txt`（NEB/CI-NEB、频率验证、表面氧化、Au20 质心分析、基组赝势），且 **BSSE 在两文件中均未出现**。本文件已逐页提取 PDF 全量知识并交叉对照字幕，标注 course_notes 缺口。
