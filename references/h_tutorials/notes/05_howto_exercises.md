# 05 · 官方 howto 系列 + 夏季学校练习（T10–T17）精读

> **来源**：`references/h_tutorials/txt/T10_howto_static.txt` … `T17_ex2020_uzh_neb.txt`
> （8 份 PDF，共 **59 页**，逐页读完，未抽样）
> **引用格式**：`T12 P6` —— 页号即 txt 文件里的 `========== PAGE N ==========`
> **抽取假象提醒**：pdfplumber 对两端对齐排版常丢词间空格（例如本文档原文里的
> `Narrow and sharp Gaussians`、`Converging the CUTOFF and REL_CUTOFF` 等可能粘连）。
> 本文按语义还原；**凡要逐字引用，回 PDF 核对**。
> **层内边界**：本文只写这 8 份**教材正文里的方法与输入**；G 层已逐字收录的部分（见 §5）
> 一律**只写指针 + 补细节**，不重复抄录。

---

## 0. 总览表

| 编号 | 文件 | 页 | 类型 | 一句话 |
|---|---|---|---|---|
| T10 | `howto_static` | 8 | 官方 howto | 用 Si bulk8 走完"单点能 + 力"的**最小完整闭环**：输入逐段讲解 → 运行 → 读输出 → 加 smearing |
| T11 | `howto_geo_opt` | 5 | 官方 howto | 用 H₂O 分子走完**固定晶胞的几何优化**：四收敛判据、CG 调参、`FIXED_ATOMS` 约束、读 `Informations at step` |
| T12 | `howto_cutoff` | 10 | 官方 howto | **把"怎么做截断能收敛测试"讲成可复制流程**：模板 + 三个 shell 脚本 + 十行数据表 + 判据 |
| T13 | `ex2016_aimd` | 9 | 2016 夏校练习 | 把上一题的 GGA 单点改成**液态水 AIMD**：生产模式（压输出/开重启）、读 `.ener`、VMD 做 g(r) 与 IR |
| T14 | `ex2016_gga` | 10 | 2016 夏校练习 | **乙酸在 anatase TiO₂ 上两种吸附构型**：密度差三算例 + cubecruncher、相对稳定性、可选 AIMD |
| T15 | `ex2016_hfx` | 7 | 2016 夏校练习 | **凝聚相杂化泛函 PBE0-D3**：截断库仑算符 + `&SCREENING` 稳定化 + `PBE_HOLE_T_C_LR` + ADMM |
| T16 | `ex2018_scf_setup` | 4 | 2018 夏校练习 | **对角化 vs OT 的对照实验**：同一盒水只换 `&SCF` 段，再用"换基组 / 换泛函 / 换体系大小"逐层扫 |
| T17 | `ex2020_uzh_neb` | 6 | 2020 UZH 练习 | **S_N2 反应 Cl⁻+CH₃Cl**：PM6 半经验两端优化 → CI-NEB 找能垒 → 无偏 MD + 约束做 2D 自由能面 |

**这 8 份构成两条完整教学链：**

```
链 A（howto 三连，官方手把手）
  T10 静态能+力  ──"网格够不够？"──▶  T12 收敛 CUTOFF/REL_CUTOFF  ──"现在可以优化了"──▶  T11 几何优化
  （T10 P1 末尾点名 T12；T11 P1 开头要求先会 T10 + T12 —— 三份互相引用，见 §3.1）

链 B（夏校练习，从单点到动力学到反应路径）
  T14 表面 GGA 单点/OPT  ──▶  T13 液态水 AIMD（生产模式）  ──▶  T15 杂化泛函 AIMD（电荷定域）
  T16 独立：SCF 求解器选择（先修课）
  T17 独立：反应路径（PM6 → CI-NEB → 自由能面）
```

> **共同血统**：T10/T11/T12 明确标注 `CP2K version 2.4`（T10 P1、T11 P1、T12 P1），
> 页面最后修改时间分别为 2019-03-10 / 2018-01-25 / 2018-06-07；
> T13–T15 为 2016 夏校（最后修改 2016-08-23，作者 `ibethune`），T16 为 2018 夏校
> （2018-06-17，作者 `mwatkins`），T17 为 2020 UZH ACPC2（2020-04-21，作者 `jglan`）。
> **引用这些数字时务必带上"练习/教程原本的版本语境"**（见 §6、§7）。

---

## 1. 这 8 份各教什么（逐份一句话）

1. **T10 `howto_static`** —— 教"**一次单点能 + 力计算的每一个关键字为什么在那里**"：`RUN_TYPE ENERGY_FORCE`、`&KIND`/基组赝势配对、`&MGRID` 的 `CUTOFF`/`REL_CUTOFF`、对角化+Broyden 混合、`SCF_GUESS`、`&PRINT/&FORCES`，以及**怎么读 SCF 表和能量分解、怎么加 smearing 并引用 TS→0 的自由能**。（T10 P1–P8）

2. **T11 `howto_geo_opt`** —— 教"**固定晶胞下把结构弛豫到极小**"：`RUN_TYPE GEO_OPT`、`&MOTION/&GEO_OPT` 的**四个收敛判据必须同时满足**、`OPTIMIZER CG` + `&CG` 的 `MAX_STEEP_STEPS`/`RESTART_LIMIT`、用 `&CONSTRAINT/&FIXED_ATOMS` 钉住一个原子防止分子漂移，以及**续算用 `-1.restart`**。（T11 P1–P5）

3. **T12 `howto_cutoff`** —— 教"**收敛测试本身怎么做成可自动化的流程**"：先讲清 multi-grid 怎么搭、高斯怎么映射，再给 `template.inp` + `LT_cutoff`/`LT_rel_cutoff` 占位符 + `inputs/run/analyse` 三段式脚本，最后用 10 行 ×2 张数据表给出判据（**先扫 CUTOFF 定档，再扫 REL_CUTOFF 确认**）。（T12 P1–P10）

4. **T13 `ex2016_aimd`** —— 教"**AIMD 从能跑到能分析**"：`RUN_TYPE MD` + `&MD`（NVT/300 K/0.5 fs/1000 步）+ GLE 热浴；**生产模式三件事**（`WALLTIME` 限时、`IOLEVEL LOW` 压 IO、`&RESTART OFF` 不写波函数）；`&EXT_RESTART` 续算；读 `WATER-1.ener` 判断守恒量与平衡；VMD 做 g(r) 与电荷近似的 IR。（T13 P1–P9）

5. **T14 `ex2016_gga`** —— 教"**表面吸附体系的 GGA 标准工作流**"：`DZVP-MOLOPT-SR-GTH` + `CUTOFF [Ry] 400` + PBE + **DFT-D3（`dftd3.dat`）**；用**三次单点 + cubecruncher.x 相减**得到结合诱导密度差 `Δρ = ρ_complex − ρ_dye − ρ_slab`；再 `GEO_OPT` 比相对稳定性；最后可选 `RUN_TYPE MD` 看 OH 距离。（T14 P1–P10）

6. **T15 `ex2016_hfx`** —— 教"**凝聚相怎么做杂化泛函**"：**先用 GGA 产生 wfn 重启**再开 HFX；`SCALE_X 0.75` + `FRACTION 0.25` = PBE0；**截断库仑算符**（`POTENTIAL_TYPE TRUNCATED` + `CUTOFF_RADIUS` ≤ L/2 + `T_C_G_DATA`）；`EPS_SCHWARZ`/`SCREEN_ON_INITIAL_P` 保稳定；`&PBE_HOLE_T_C_LR` 做短程交换；**ADMM**（`AUX_FIT_BASIS_SET` + `&AUXILIARY_DENSITY_MATRIX_METHOD`）降本。（T15 P1–P7）

7. **T16 `ex2018_scf_setup`** —— 教"**怎么判断该用对角化还是 OT**"：给出**同一盒 32 H₂O 的 TD 输入**，然后**只改 `&SCF` 段**换成 OT 输入，让学员在"换基组（DZVP→TZV2P→MOLOPT）/换泛函（PADE→PBE）/换体系大小"的条件下逐项对比效率；结尾点明**最重要的'参数'其实是体系本身**（水是闭壳大带隙的乖体系）。（T16 P1–P4）

8. **T17 `ex2020_uzh_neb`** —— 教"**从两端极小值到能垒再到自由能面**"：PM6 半经验（`&QS METHOD PM6` + `&SE`，非周期 `PERIODIC NONE` + `PSOLVER WAVELET`）做两端 `GEO_OPT` → `RUN_TYPE BAND` + `CI-NEB`（`NUMBER_OF_REPLICA 10`、`K_SPRING 0.05`、`NSTEPS_IT 5`）→ 无偏 MD + `&COLLECTIVE` 谐振约束 + `&METADYN DO_HILLS .FALSE.` 导出 CV → Python 直方图算 `F(s) = −kT log(P(s))`。（T17 P1–P6）

---

## 2. 逐节要点（带页码）

### 2.1 T10 `howto_static`（8 页）

| 页 | 要点 |
|---|---|
| **P1** | 目标：QUICKSTEP 下做一次 **自洽 Kohn-Sham DFT 的单点能与力**计算。体系：**面心立方 bulk Si，立方单胞内 8 个原子**。算例包 `static_calculation.tgz`，**CP2K version 2.4**。明确声明：**示例用的积分网格设置已经选得对该精度足够，另有专门教程讲怎么做到**（→ 指 T12）。必需文件三个：`Si_bulk8.inp`（主输入）、`BASIS_SET`、`GTH_POTENTIALS`（后两者在 `cp2k/data/`）。输入文件**名字任意、扩展名任意**；输入由**有序的 block 和 keyword** 组成，**顺序不重要**；block 称为 "section"，可有子 section。 |
| **P2** | 给出完整输入（见 §4.1 指针：G 层已逐字收录）。主 section 两类：`GLOBAL`（作业名、运行类型）与 `FORCE_EVAL`（所有与受力评估有关的参数，含初始坐标）。`RUN_TYPE` 必须设 `ENERGY_FORCE`；`PROJECT` 是 `PROJECT_NAME` 的**别名**，决定所有自动生成输出的前缀；`PRINT_LEVEL` 控默认详细度、可在各子段覆盖。`METHOD Quickstep` = 用 **GPW** 做 DFT。 |
| **P3** | `&KIND`：**每个元素必须有一个**；本例 Si 用 `DZVP-GTH-PADE`（**double-ζ with polarisation**，为 GTH PADE LDA 赝势优化）+ `GTH-PADE-q4`（**4 个价电子**）。基组/赝势名**必须**在 `BASIS_SET_FILE_NAME`/`POTENTIAL_FILE_NAME` 指定的文件里存在。**照抄了 `BASIS_SET` 里的 Si `DZVP-GTH-PADE` 条目原文**与 `GTH_POTENTIALS` 里的 `Si GTH-PADE-q4 GTH-LDA-q4` 条目原文（见 §4.2）。 |
| **P4** | `&CELL`：`A`/`B`/`C` 是三个晶格矢量，**Angstrom 是默认单位**；本例晶格常数 **5.4306975 Å**。`&COORD` 默认格式 `<ATOM_KIND> X Y Z`（**Cartesian，Å**）；`SCALED .TRUE.` 改分数坐标；`UNIT` 改单位；`ATOM_KIND` 标签须对应 `&KIND`。`&DFT` 子段**仅当 `METHOD` 是 QUICKSTEP 时相关**。`EPS_DEFAULT` 设 QUICKSTEP 内**所有容差的默认值**，单独的 `EPS_*` 会**覆盖**它。`&MGRID`：**多网格**表示高斯，**窄而尖的映射到更细网格**；`NGRIDS 4`、最细网格平面波截断 **300 Ry**、任何高斯下方的网格间距要比等效平面波截断 **60 Ry** 更细；**并点名让读者去读 T12**。 |
| **P5** | `&XC` 用 **PADE LDA**，与所选基组/赝势一致。`&SCF`：`SCF_GUESS ATOMIC` 用原子电荷密度重叠产生初始密度（**好的初始密度对快速收敛很重要**）；`EPS_SCF` 是**电荷密度残差**容差、覆盖 `EPS_DEFAULT`；`MAX_SCF` 是每次基态能量计算允许的最大自洽步数。`&DIAGONALIZATION ON` + `ALGORITHM STANDARD` = 传统对角化，STANDARD 指用 **LAPACK/SCALAPACK**；**换 OT 的做法：删掉 `DIAGONALIZATION` 块，或把 ON 改 OFF（`.FALSE.`），并加 `&OT` 子段**。`&MIXING T`：`ALPHA 0.4` 的含义是**0.4 份输出密度 + 0.6 份输入密度**组成下一轮输入密度；**`&MIXING` 只对传统对角化适用，OT 用另一套电荷混合**。 |
| **P6** | `NBROYDEN` 是 `NBUFFER` 的别名，设 Broyden 混合的历史数目。`&PRINT/&FORCES ON` 打印原子力。运行：`mpirun -n 2 cp2k.popt -o Si_bulk8.out Si_bulk8.inp &`；**`-o` 会把连续多次运行的输出追加到同一文件，想从头开始必须先删掉 `Si_bulk8.out`**。产物：`Si_bulk8.out`、`Si_bulk8-RESTART.wfn`、`Si_bulk8-RESTART.wfn.bak-1`（`.bak-<n>` 是**前 n 个 SCF 步**的波函数）。续算：把 `SCF_GUESS` 改 `RESTART`，**前提是新计算与生成该 wfn 的计算共享同一 `PROJECT_NAME`**，否则要改名。输出头部：电子数 32、占据轨道 16、分子轨道 16、轨道函数 104。 |
| **P7** | **照抄 10 步 SCF 表**（第 1 步 `NoMix/Diag.`，第 2–10 步 `Broy./Diag.`，能量 `-32.2320848878` → `-31.2978852054`）与 `*** SCF run converged in 10 steps ***`。**能量分解块**与 `ENERGY| Total FORCE_EVAL ( QS ) energy (a.u.)`（见 §4.2）。**ATOMIC FORCES 表**（8 个 Si 的力全在 ±1e-8 量级，`SUM OF ATOMIC FORCES` 为 0）。**结果自检要点**：① 从最终电子密度算出的**总电子数必须正确**（本例 31.9999999939）；② **力几乎为零 ⇒ 体系基本弛豫、几何接近基态最优**。最后引出 smearing。 |
| **P8** | **加 smearing**：大带隙体系不加没问题；**金属或小带隙体系会因占据函数的不连续而不稳定甚至永不收敛**。做法：`&SMEAR ON` + `METHOD FERMI_DIRAC` + `ELECTRONIC_TEMPERATURE [K] 300`；**CP2K 里可用方括号显式给单位，如 `[K]`，写在数值前**。**只加 SMEAR 不够——smearing 会让轨道被占据到导带，必须用 `ADDED_MOS 10` 把最低的 10 个空轨道纳进来**（否则为省成本被省略）；给定基组下分子轨道数有上限，理论上限是哈密顿量的**秩**（本例 104 个基函数，26 个 MO 远在限内）。带 smearing 的输出多出熵项：`Electronic entropic energy: -0.00001687947145`、`Fermi energy: 0.20867150262130`；**熵项必须小，才说明结果可靠地近似零电子温度**；**最终自由能 = 总 DFT 能量 + 熵能**；**应当引用的是 TS→0 外推的自由能**（本例 `ENERGY| … -31.297887031736590`）。 |

### 2.2 T11 `howto_geo_opt`（5 页）

| 页 | 要点 |
|---|---|
| **P1** | 目标：**弛豫结构但不改晶胞尺寸**（"without changing the cell dimensions"），例子是 H₂O。算例包 `geometry_optimisation.tgz`，**CP2K 2.4**。**先修要求**：会做静态能+力（T10）、会找够用的网格截断（T12）。给出 **DIIS** 的定义（direct inversion in the iterative subspace，又名 **Pulay mixing**，是外推技术，由 Peter Pulay 在量子化学领域提出，用于加速和稳定 HF SCF 收敛）。输入开头（`&GLOBAL` → `&MGRID CUTOFF 200`）。 |
| **P2** | 输入其余部分（`NGRIDS 4`、`REL_CUTOFF 30`、`&SCF` 用 `&DIAGONALIZATION T ALGORITHM STANDARD` + `&MIXING T ALPHA 0.5 METHOD PULAY_MIXING NPULAY 5`、`&PRINT/&RESTART OFF`、`XC PADE`、`&MOTION/&GEO_OPT` + `&CG` + `&CONSTRAINT`）。`RUN_TYPE GEO_OPT`。**明确说明本例走对角化 + Pulay 混合（5 个历史）**。`&MOTION/&GEO_OPT` 只适用于**晶胞尺寸不变**的计算；允许晶胞弛豫的情形见另一份教程（指 `CELL_OPT`）。 |
| **P3** | `TYPE`：`MINIMIZATION`（局部极小）或 `TRANSITION_STATE`（鞍点）。**四个判据**：`MAX_DR`/`RMS_DR`（原子位移的最大值/均方根，**Bohr**）、`MAX_FORCE`/`RMS_FORCE`（力的最大值/均方根）。**只有四个判据全部满足，几何才算优化好**。`MAX_ITER` 最大迭代数。`OPTIMIZER` 本例用 **CG**。`&CG`：本例 **`MAX_STEEP_STEPS 0`**（CG 开始前**不做**最速下降步）、**`RESTART_LIMIT 9.0E-01`**（若连续两个搜索方向夹角余弦 < 0.9 则**重置 CG 并做一次最速下降步**）。`&CONSTRAINT/&FIXED_ATOMS`：`COMPONENTS_TO_FIX XYZ` 把所有方向钉死；`LIST` 后的数字是**原子序号，顺序对应 `&COORD` 里自上而下的原子**（`LIST 1 2 3 ... N`）；**本例固定氧原子，好让水分子在弛豫时不会跑动**。运行用**串行版** `cp2k.sopt -o H2O.out H2O.inp &`。 |
| **P4** | 产物：`H2O.out`、`H2O-pos-1.xyz`（**每步坐标轨迹，最后一组即弛豫后结构**）、`H2O-1.restart`（**本身就类似一份 `H2O.inp`，含最新坐标**）、`H2O-1.restart.bak-1/2/3`。**作业挂掉后用 `cp2k.sopt -o H2O.out H2O-1.restart &` 继续**；`-1.restart` 也可当模板写后续计算。**逐步输出的读法**：`-------- Informations at step = N ------------` 块里 `Optimization Method`、`Total Energy`、`Real energy change`、`Decrease in energy`、`Used time`，以及四条 `Convergence check` 的"实测值 / 收敛限 / YES|NO"。照抄了 step = 1（未收敛）的完整块。 |
| **P5** | 照抄 step = 11 的完整块：**四条判据全 YES**；`Max. step size 0.0003393150`、`RMS step size 0.0001493298`、`Max. gradient 0.0001787448`、`RMS gradient 0.0000786642`，收敛限均为 `0.0010000000`。随后 `*** GEOMETRY OPTIMIZATION COMPLETED ***` 与 **"Reevaluating energy at the minimum"**（在极小点重算能量）：电子数 8、占据轨道 4、轨道函数 23；打印 **ASPC 方法参数**（`ASPC order: 3`，`B(1)…B(5) = 3.000000 / -3.428571 / 1.928571 / -0.571429 / 0.071429`）；SCF 2 步收敛（`Pulay/Diag. 0.50E+00`）；最终 `Total energy: -17.16463477110803`、`ENERGY| Total FORCE_EVAL ( QS ) energy (a.u.): -17.164634771108034`。 |

### 2.3 T12 `howto_cutoff`（10 页）

| 页 | 要点 |
|---|---|
| **P1** | QUICKSTEP 与几乎所有从头算 DFT 程序一样需要**实空间（RS）积分网格**表示某些函数（电子密度、乘积高斯）。用 **multi-grid**：**宽而平滑的高斯映射到更粗网格，窄而尖的映射到更细网格**；**电子密度永远映射到最细网格**。选够细的网格对结果有意义、准确**至关重要**。算例包 `converging_grid.tgz`，**CP2K 2.4**。所有 multi-grid 设置都在 `&MGRID`：`NGRIDS`（层数，**默认 4**）；`CUTOFF`（**最细层的平面波截断，默认单位 Ry**，越高网格越细）；**各层递推公式 `Ecut_i = Ecut_1 / α^(i−1)`**，`α` **默认 3.0**，自 **CP2K 2.0** 起可用 **`PROGRESSION_FACTOR`** 配置。**`REL_CUTOFF` 控制哪些乘积高斯被映射到哪一层**：CP2K 尽量让每个高斯覆盖的网格点数**大致相同**；`REL_CUTOFF` 定义的是"**单位标准差高斯所覆盖的参考网格**的平面波截断"。 |
| **P2** | 一个高斯会被映射到**最粗的那一层**，条件是它在该层覆盖的网格点数 **≥ 它在 `REL_CUTOFF` 定义的参考网格上覆盖的点数**。**最关键的两个关键字就是 `CUTOFF` 与 `REL_CUTOFF`**：`CUTOFF` 太低 → 所有网格都粗、结果不准；**`REL_CUTOFF` 太低 → 即使 `CUTOFF` 很高，所有高斯也都被压到最粗层，有效积分网格仍然太粗**。给出算例（8 原子立方 Si）与**目标精度写法**："say, **10⁻⁶ Ry** in total energy"；流程是**做一系列单点能计算**，用脚本自动化。`template.inp` 开始。 |
| **P3** | `template.inp` 其余部分：`&KIND Si` 用 **`SZV-GTH-PADE`**（注意：**比 T10 的 DZVP 更小**）+ `GTH-PADE-q4`；`&CELL SYMMETRY CUBIC`；`&PRINT/&TOTAL_NUMBERS ON`。**值得注意的设置**：`RUN_TYPE ENERGY`（**只算能量、不算力**——只关心网格收敛时看总能通常就够，而且要做一连串计算，**每次越便宜越好**）；`PRINT_LEVEL MEDIUM`（**必须，因为要看"多少个高斯被映射到哪层网格"，用来判断 `REL_CUTOFF` 是否合适**）；`&MGRID` 里 `CUTOFF LT_cutoff` / `REL_CUTOFF LT_rel_cutoff` 是**占位标记，由脚本搜索并替换**；两者默认单位都是 **Ry**。 |
| **P4** | `&SCF` 设 **`MAX_SCF 1`** ⇒ **不做任何自洽循环**。**原文理由**："This is okay for checking the integration grid, because **irrespective of self-consistency, grid settings with fine enough meshes should give consistent energies**."（不管自洽与否，网格够细就应该给出一致的能量。）**收敛 CUTOFF 的做法**：**先把 `REL_CUTOFF` 设得相对高**，再系统地变 `CUTOFF`；**`REL_CUTOFF 60 Ry` 对大多数计算通常够用**，而且**后面还会再检查它**。扫描范围 **50 Ry → 500 Ry，步长 50 Ry**（原文：从经验看，10⁻⁶ Ry 精度所需的 CUTOFF 应**远在此范围内**）。给出**完整 `cutoff_inputs.sh`**（见 §4.3），含 `sed` 替换、建目录、拷基组/赝势。 |
| **P5** | `chmod u+x ./cutoff_inputs.sh` → `./cutoff_inputs.sh` 生成 `cutoff_50Ry … cutoff_500Ry`，每个目录里都有 `BASIS_SET`、`GTH_POTENTIALS` 和一份只差 `CUTOFF`/`REL_CUTOFF` 的 `Si_bulk8.inp`。给出**完整 `cutoff_run.sh`**（见 §4.3）：**变量 `cp2k_bin=cp2k.popt`、`no_proc_per_calc=2`、`no_proc_to_use=16`**，用 `max_parallel_calcs=$(expr $no_proc_to_use / $no_proc_per_calc)` 与 `bc` 取模控制**最多 8 个作业并行**；原文说明这是在 **24 核本地工作站**上跑、总共用 16 核、每算例 2 核。`chmod u+x` + `./cutoff_run.sh &` 后台跑；**"本地工作站上只需几分钟"**。 |
| **P6** | 分析：每个作业目录的 `Si_bulk8.out` 里都有总能与高斯分布信息。照抄 `cutoff_100Ry/Si_bulk8.out` 的片段——**注意 `*** SCF run NOT converged ***`，这在 `MAX_SCF 1` 下是正常的**；总能行用 **正则 `^[ \t]*Total energy:`** 抓。照抄 **`---- MULTIGRID INFO ----` 块**（grid 1: `count 2720 cutoff [a.u.] 50.00`；grid 2: `5000 / 16.67`；grid 3: `2760 / 5.56`；grid 4: `16 / 1.85`；`total gridlevel count : 10496`）。**单位换算标注：`[a.u.]` 是 Hartree 能量单位，1 Ha = 2 Ry。** 给出 `cutoff_analyse.sh` 前半。 |
| **P7** | `cutoff_analyse.sh` 后半（用 `grep -e '^[ \t]*Total energy'` + `awk '{print $3}'` 取总能；用 `grep -e '^[ \t]*QS\| Number of grid levels:'` + `awk '{print $6}'` 取层数；用 `grep -e '^[ \t]*count for grid'` + `awk -v igrid=$igrid '(NR == igrid){print $5}'` 取每层高斯数）。产出 **`cutoff_data.ssv`**（**10 行数据，见 §4.4**）。**判据**：在 `REL_CUTOFF = 60 Ry` 下，**`CUTOFF` ≥ 250 Ry 时总能误差 < 10⁻⁸ Ha**。**关键观察**：**随 `CUTOFF` 增大，被分配到最细网格的高斯数目反而减少**；因此**只增 `CUTOFF` 而不增 `REL_CUTOFF`，最终会导致能量收敛变慢**——越来越多高斯被推到粗层，抵消掉 `CUTOFF` 的增加。**选 250 Ry 的理由（原文）**："it is the **lowest cutoff energy where the finest grid level is used**, but at the same time **with the majority of the Gaussians on the coarser grids**"（最低的、用上了最细层网格的截断，同时多数高斯仍在较粗层）。 |
| **P8** | **下一步：固定 `CUTOFF` 250 Ry，变 `REL_CUTOFF`**。给出**完整 `rel_cutoff_inputs.sh`**（扫描 `10 20 30 40 50 60 70 80 90 100`，`sed` 同时替换两个标记）。 |
| **P9** | 给出**完整 `rel_cutoff_run.sh`**（与 cutoff 版同构）；`./rel_cutoff_run.sh &`；分析方式与 CUTOFF 完全相同；给出 `rel_cutoff_analyse.sh`（只改 `plot_file=rel_cutoff_data.ssv`、注释头写 `# CUTOFF = ${cutoff}`、循环变量换名）。 |
| **P10** | 产出 **`rel_cutoff_data.ssv`**（**10 行数据，见 §4.4**）。**判据**：随 `REL_CUTOFF` 增大，**更多高斯被映射到更细网格**；**`REL_CUTOFF` ≥ 60 Ry 时总能误差降到 10⁻⁸ Ha 以下**。**结论**：`&MGRID / CUTOFF 250 / REL_CUTOFF 60` 对该精度要求已经足够。 |

### 2.4 T13 `ex2016_aimd`（9 页）

> 源页：`exercises/2016_summer_school/aimd.txt`，最后修改 2016-08-23，作者 `ibethune`。

| 页 | 要点 |
|---|---|
| **P1** | 前提："一旦标准 GGA 模拟搭好了，做 AIMD 就很容易"。体系：**bulk 液态水**（引用 10.1063/1.1828433 与 10.1021/jp901990u；后者"令人信服地说明为什么色散校正必不可少"）。**两个目标**：① 搭一个**生产模式**的模拟（压输出、开重启）；② 看懂 `.ener` 文件并用 VMD 做基本轨迹分析。**Topics：`MD` section（timestep）、Thermostat（NVE、NVT、NPT）**。**基组警告（原文）**：为跑得快，用 `HFX_BASIS` 文件里的 `DZVP-GTH`；**这个基组比液态水这种"subtle substance"该用的要小，生产跑应当用 `TZV2P-GTH`、`TZV2P-MOLOPT-GTH`、`cc-TZV2P` 或更好**。**1st task**：从上一题的 `mode1.inp` 改名 `water.inp`，再从 `cp2k/data` 拿 `HFX_BASIS`。要改的关键字：`PROJECT WATER`、`RUN_TYPE MD`、`BASIS_SET_FILE_NAME HFX_BASIS`、**`MINIMIZER DIIS`**、`ABC [angstrom] 12.42 12.42 12.42`、`COORD_FILE_NAME water.xyz`、`BASIS_SET DZVP-GTH`。要插的块：`&GLOBAL` 里 **`WALLTIME 300`**（注释 "limit the runs to 5min"）与 **`IOLEVEL LOW`**；`&SCF/&PRINT/&RESTART OFF`（注释 "**do not write the wfn restart file every step, for large systems this is slow**"、"**do not store the wfn during MD**"）。 |
| **P2** | `&DFT/&PRINT` 里：`&E_DENSITY_CUBE OFF`；`&MO_CUBES` 用 `NLUMO 4` / `NHOMO 4` / **`WRITE_CUBE .FALSE.`** / **`&EACH MD 10`**（注释"每 10 个 MD 步算一次本征值与 homo-lumo gap，但**不写 cube**"）。`&MOTION/&PRINT`：`&TRAJECTORY &EACH MD 1`、`&VELOCITIES OFF`、`&FORCES OFF`、**`&RESTART_HISTORY &EACH MD 500`**、**`&RESTART BACKUP_COPIES 3 &EACH MD 1`**。跑完检查 **timing report 或输出里的 `ENDED AT` 行**。产物：**`WATER-1.restart`（"用编辑器打开看，它其实就是一份普通输入文件"）、`WATER-pos-1.xyz`、`WATER-1.ener`（势能、动能、守恒量）**。**续算**：加 `&EXT_RESTART / RESTART_FILE_NAME WATER-1.restart / &END`，并把 `WALLTIME`（和作业脚本时限）加大。**原文经验**："as soon as the job runs significantly longer than the time needed to perform the first few steps, restarting the job doesn't influence the efficiency." |
| **P3** | **2nd task：可视化 `.ener`**。照抄列头与 6 行数据（见 §4.7）；列序为 `Step Nr. / Time[fs] / Kin.[a.u.] / Temp[K] / Pot.[a.u.] / Cons Qty[a.u.] / UsedTime[s]`。gnuplot：**守恒量 `plot './WATER-1.ener' u 2:6 w lp`**，与势能对比 `u 2:5` 再 `replot … u 2:6`。**若守恒量守不住，原文给三条处方**：① **把 `EPS_SCF` 调紧（减少漂移）**；② **把 `TIMESTEP` 调短（减少涨落）**；③ **调 `EXTRAPOLATION_ORDER`（减少漂移和/或不稳定）**。**平衡判据（原文）**：温度与势能**都必须围绕平均值振荡且没有长期漂移**。**经验法则：丢掉轨迹的前 1/3，用后 2/3 做数据分析。** **3rd task：VMD 分析轨迹**；`vmd WATER-pos-1.xyz`。**g(r)**：`Extensions/Analysis/Radial Pair Distribution Function`（原文 "Function g®" 是抽取时把 `(r)` 抽成了 `®`），**先 `Utilities/Set unit cell size dimensions` 设好单胞**；再用 `Graphics/Representations` 显示邻胞与氢键。算 **O-O 与 O-H 的 pair distribution function（含积分）**；**思考题：一个水分子平均有几个邻居？（3 / 3-4 / 4 / 4-5 / 5）**。**IR**：从偶极随时间的演化估算 IR 谱密度；**从 AIMD 估偶极需要 Wannier 中心，超出本教程范围**；**这里用简单近似：给水分子赋经典点电荷**（原文认为在此语境下该近似合理）。建 `charges.dat`：`O -1.2` / `H +0.6`；`Extensions/Analysis/Spectral density calculator`，选轨迹、**timestep 改 0.5 fs**、**最大频率 6000 cm^-1**；`Utilities/Load name↔charge map from file`。**思考题：OH 伸缩你预期在哪？复现了吗？** **低频需要更长的轨迹才能合理估计，至少是信号周期的 10 倍。** |
| **P4** | **4th task（可选）**：往水里引入离子，平衡后研究动力学与溶剂化结构；**最省事的做法是把一个或多个水分子换成目标离子**（个数视离子大小）；**这样造出来的构型显然远非平衡，必须跑一段才具代表性**。有趣的玩法：**把 H₂O 换成 H⁺，看能否观察到 Eigen 态、Zundel 态与 Grotthuss 机制**。开始列 `water.xyz`：**`192` 个原子**，注释行给出 `water with unit cell: ABC [angstrom] 12.42 12.42 12.42`。 |
| **P5–P6** | `water.xyz` 的 192 个原子坐标（O 先、每个 O 后跟 2 个 H；坐标跨 P5–P6 两页）。**P6 末尾**开始给 `water_cheating.inp`（"卡住了才看"的完整答案）。 |
| **P6–P9** | **`water_cheating.inp` 全文**（见 §4.8）。要点：`WALLTIME 1800`（注释写 30min，与正文的 300 s 不同）；`&MGRID CUTOFF [Ry] 400`，注释："**取决于元素（基组），截断太小会导致 eggbox 效应**；某些计算（**几何优化、振动频率、NPT 与晶胞优化）需要更高的截断**"；`&QS METHOD GPW`、`EPS_DEFAULT 1.0E-10`、**`EXTRAPOLATION ASPC`**（注释"used for MD"）；`&POISSON PERIODIC XYZ`（注释"默认值；**气相体系应当用 `NONE` 加 wavelet 求解器**"）；`&SCF SCF_GUESS ATOMIC / MAX_SCF 30 / EPS_SCF 1.0E-6`（注释"**SCF 精度典型 1.0E-6 – 1.0E-7**"）；**`&OT PRECONDITIONER FULL_SINGLE_INVERSE / MINIMIZER DIIS`**（注释："an accurate preconditioner suitable also for larger systems"、"**the most robust choice (DIIS might sometimes be faster, but not as stable)**"）；`&OUTER_SCF MAX_SCF 10 / EPS_SCF 1.0E-6`（注释"**repeat the inner SCF cycle 10 times**"、"**must match the above**"）；`&XC &PBE`；**`&VDW_POTENTIAL POTENTIAL_TYPE PAIR_POTENTIAL / &PAIR_POTENTIAL PARAMETER_FILE_NAME dftd3.dat / TYPE DFTD3 / REFERENCE_FUNCTIONAL PBE / R_CUTOFF [angstrom] 16`**；`&TOPOLOGY COORD_FILE_NAME water.xyz / COORD_FILE_FORMAT XYZ`；`&KIND H DZVP-GTH + GTH-PBE-q1`、`&KIND O DZVP-GTH + GTH-PBE-q6`；`&MOTION/&GEO_OPT OPTIMIZER BFGS / MAX_ITER 100 / MAX_DR [bohr] 0.003`；**`&MD ENSEMBLE NVT / TEMPERATURE [K] 300 / TIMESTEP [fs] 0.5 / STEPS 1000`** + **`&THERMOSTAT REGION MASSIVE / TYPE GLE / &GLE NDIM 5 / A_SCALE [ps^-1] 1.00 / A_LIST …`（5 行 5 列，注明由 `http://epfl-cosmo.github.io/gle4md` 生成）**；`&MOTION/&PRINT` 四个打印块；末尾 `&EXT_RESTART RESTART_FILE_NAME WATER-1.restart`。 |

### 2.5 T14 `ex2016_gga`（10 页）

> 源页：`exercises/2016_summer_school/gga.txt`，最后修改 2016-08-23，作者 `ibethune`。

| 页 | 要点 |
|---|---|
| **P1** | GGA DFT 在 CP2K 里对很多体系都相对容易；手册列了各种选项，但**体系初始搭建很简单、几乎不需要知道内部细节**；本文给的输入是很好的模板起点。**起步关键**：一个**合理的初始结构**，以及凝聚相体系的**模拟盒子尺寸**；这两样确定后**复制粘贴可能就够了**。**四个重要参数**：model（结构）、Gaussian basis set、Plane Waves (PW) cutoff、Density functional；**评估这些参数的影响可能更具挑战性**。体系：**乙酸（acetic acid）在 anatase TiO₂ 上的两种可能结合模式**；乙酸含**羧基**，在**染料敏化太阳能电池（DSSC）**里常作把光捕获染料锚定到半导体基底上的**锚定基团**；本文用乙酸当更复杂染料分子的模型（仿 10.1021/jp4117563）；**为加速计算只用最小的 slab 模型**。**1. Task**：用 VMD 可视化 `mode1.xyz` 与 `mode2.xyz`；编辑器用 vi/nano（vi 可配色 CP2K 输入，见 `http://www.cp2k.org/tools`）；需要 `cp2k/data` 下的 **`BASIS_MOLOPT`、`GTH_POTENTIALS`、`dftd3.dat`**，**除非编译时带了 `-D__DATA_DIR`** 让程序自动找到。作业脚本示例开始。 |
| **P2** | 作业脚本原文（PBS + `aprun`，见 §4.9）。**2. Task：结合诱导的密度差**。目标：算 `ρ_induced = ρ_slab-dye-complex − ρ_dye − ρ_slab`。先讨论 `mode1.inp` 里结构与选择的细节，**topics 清单**：Project name、Runtype、Gaussian Basis & pseudopotentials、PW Cutoff、thresholds、**SCF: OT**、XC 与 -D3 校正、Unit cell choice。然后跑 `cp2k.popt -i mode1.inp -o mode1.out`，除 `mode1.out` 外 CP2K 还会生成名为 **`MODE1*`** 的文件；**阅读 topics**：General overview、**OT output**、**Various grid quantities**、**Density cube output**、Timing report。**第三**：算密度差要跑**三次**单点能量：① 结合态（`mode1.xyz`）；② 单独乙酸（把 slab 坐标删掉，命名 `mode1_dye.xyz`）；③ 单独 TiO₂ slab（把乙酸坐标删掉，命名 `mode1_slab.xyz`）；用 VMD 检查子体系是否正确；再由 `mode1.inp` **改 `COORD_FILE_NAME` 与 `PROJECT` 两处**得到 `mode1_dye.inp`、`mode1_slab.inp`。分析用 CP2K 自带的 **`cubecruncher.x`**（可做 cube 相减）；编译：`module load cp2k` → `cp -r $CP2K/../../tools/cubecruncher .` → `cd cubecruncher` → `module swap PrgEnv-cray PrgEnv-gnu` → `make`。 |
| **P3** | cubecruncher 两条命令（**`-center geo` 在第二条**，见 §4.9），结果 `MODE1_delta.cube` 用 VMD 可视化。**3. Task：相对稳定性**：要比较 mode1 与 mode2 必须**两个构型都做几何优化**；做法：**关掉 cube 生成（`&E_DENSITY_CUBE OFF`）**、`RUN_TYPE` 改成 **`GEO_OPT`**、改工程名；mode2 同理另建一份输入。**输入 topics**：`BFGS vs LBFGS`、`EPS_SCF`、`CUTOFF`、`MAX_DR`、…；**输出 topics**：`Informations at step`、**轨迹 `MODE1_GEO-pos-1.xyz`**。比较最终能量行 **`ENERGY\| Total FORCE_EVAL ( QS ) energy (a.u.):`**，判断哪个模式更稳定；**并与所引论文的 Table 1 对照**。**4. Task（可选）：AIMD**——把 `RUN_TYPE` 改成 **`MD`**，跑 ~**1000 步 ≈ 0.5 ps**；**"跑几个小时作业应该就结束了"**；在 VMD 里分析 **OH 距离**；思考题：**与表面的氢键、两个氧的相对酸性**；**原文提醒：要有统计意义需要更长的轨迹，而且 slab 厚度会起重要作用**；与论文 **Fig. 7** 对照。 |
| **P4–P6** | **`mode1.inp` 全文**（见 §4.10 指针 + 增量）：`PROJECT MODE1` / `RUN_TYPE ENERGY`；`BASIS_SET_FILE_NAME BASIS_MOLOPT` / `POTENTIAL_FILE_NAME GTH_POTENTIALS`；`CHARGE 0` / `MULTIPLICITY 1`；**`&MGRID CUTOFF [Ry] 400`**（注释同 T13：太小 → eggbox；几何优化/振动/NPT/晶胞优化需要更高）；`&QS METHOD GPW / EPS_DEFAULT 1.0E-10 / EXTRAPOLATION ASPC`；`&POISSON PERIODIC XYZ`；**`&PRINT &E_DENSITY_CUBE ON`**；**`&SCF SCF_GUESS ATOMIC / MAX_SCF 30 / EPS_SCF 1.0E-6 / &OT PRECONDITIONER FULL_SINGLE_INVERSE / MINIMIZER CG / &OUTER_SCF MAX_SCF 10 / EPS_SCF 1.0E-6`**（**注意与 T13 的差别：这里 `MINIMIZER` 是 `CG`，T13 是 `DIIS`**）；`&XC &PBE` + D3；`&CELL ABC [angstrom] 10.2270 11.3460 20.000`；`&TOPOLOGY COORD_FILE_NAME mode1.xyz / COORD_FILE_FORMAT XYZ`；**四个 `&KIND` 全部用 `DZVP-MOLOPT-SR-GTH`**，赝势分别为 `GTH-PBE-q1 / -q4 / -q6 / -q12`（H/C/O/Ti）；`&MOTION` 同时给了 `&GEO_OPT`（BFGS / MAX_ITER 100 / MAX_DR [bohr] 0.003）与 `&MD`（NVT / 300 K / 0.5 fs / 1000 步 / GLE）。 |
| **P6–P10** | **`mode1.xyz` 与 `mode2.xyz` 全文**：两者首行都写 **`116`**，实测**都确实是 116 个原子**，且成分完全一致：**36 个 Ti + 74 个 O + 2 个 C + 4 个 H**（即 **`Ti36O72` slab = 原子 1–108** ＋ **乙酸 `CH₃COOH` = 原子 109–116**，共 8 个：`H C H H C O O H`）。**关键发现：两个文件的元素序列逐位相同**（原子 1–108 是 slab、109–116 是乙酸，位置完全对应）——**所以"切子体系"可以按同一套原子号做**（删 109–116 得 `mode1_dye.xyz`/`mode2_dye.xyz`；删 1–108 得 `mode1_slab.xyz`/`mode2_slab.xyz`）。**但两个文件的 slab 坐标不同**（mode1 的 Ti 在 z ≈ −0.09 Å 与 −3.71 Å 两族，mode2 在 −0.24 Å 与 −3.80 Å 附近），**因为两种结合模式对应两个不同的优化前构型**。 |

### 2.6 T15 `ex2016_hfx`（7 页）

> 源页：`exercises/2016_summer_school/hfx.txt`，最后修改 2016-08-23，作者 `ibethune`。

| 页 | 要点 |
|---|---|
| **P1** | 目的：讲**凝聚相体系里怎么用 CP2K 算杂化泛函（HFX）**。基于 10.1021/ct900494g、10.1063/1.2931945，以及其高效扩展 **ADMM**（10.1021/ct1002225）。**CP2K 的 HFX 基于四中心积分，用外部库 libint 计算；做这些练习 CP2K 必须链接该库。** **成本强烈依赖基组性质**——**除非配合 ADMM，否则不要把 MOLOPT 基组用于 HFX**；本练习用 `HFX_BASIS` 里的基组（合适）。**截断库仑算符**：在凝聚相（**仅在 Gamma 点**）CP2K 对交换部分用**截断库仑算符**；物理图像是**不想要电子与其在邻胞中的镜像发生"自交换"相互作用**。**经验规则：最大作用范围（截断半径）是 L/2，L 是单胞最小边长**；**交换能对该半径的收敛是指数式的**；**通常 5–6 Å 就能给出好结果，但这取决于体系性质，即带隙或最大局域化 Wannier 轨道的范围**。**1st task：GGA 重启 wfn**——用上一题的水输入做一次单点 GGA，产生初始波函数重启（**HFX 计算从中受益**）：改 `RUN_TYPE ENERGY`、`IOLEVEL MEDIUM`、`RESTART ON`、注释掉 `&EXT_RESTART` 段；跑完把 `WATER-RESTART.wfn` 改名 `WATER-RESTART-GGA.wfn`，**并记下 HOMO-LUMO gap [eV]**。 |
| **P2** | **2nd task：PBE0-D3 water**。做杂化只要改 `&XC` 段。改 `SCF_GUESS RESTART` + **`WFN_RESTART_FILE_NAME WATER-RESTART-GGA.wfn`**。`&XC` 段全文（见 §4.11）：`&PBE SCALE_X 0.75`（注释 "75% GGA exchange"）/ `SCALE_C 1.0`（"100% GGA correlation"）；`&HF FRACTION 0.25`（"25 % HFX exchange"）；**`&SCREENING EPS_SCHWARZ 1.0E-6`（注释 "important parameter to get stable HFX calcs"）+ `SCREEN_ON_INITIAL_P TRUE`（注释 "needs a good (GGA) initial guess"）**；**`&INTERACTION_POTENTIAL POTENTIAL_TYPE TRUNCATED`（"for condensed phase systems"）+ `CUTOFF_RADIUS 6.0`（"should be less than halve the cell"）+ `T_C_G_DATA ./t_c_g.dat`（"data file needed with the truncated operator"）**；**`&MEMORY MAX_MEMORY 4000`（"In MB per MPI rank.. use as much as need to get in-core operation"）+ `EPS_STORAGE_SCALING 0.1`**；`&VDW_POTENTIAL … REFERENCE_FUNCTIONAL PBE0 / R_CUTOFF [angstrom] 16`。**Topics 清单**：`EPS_SCHWARZ`、`EPS_PGF_ORB`、`SCREEN_ON_INITIAL_P`（**保证 SCF 稳定的参数**）、交换的分数（`SCALE_X`、`FRACTION`）。**照抄 `HFX_MEM_INFO` 输出块**（见 §4.11）：`Number of cart. primitive ERI's calculated: 20780449251`、`sph. ERI's calculated: 4626861713`、`stored in-core: 1440639962`、`on disk: 0`、`on the fly: 0`、`Total memory consumption ERI's RAM [MB's]: 1368`、`max-vals [MB's]: 78`、`Total compression factor ERI's RAM: 8.03`、`disk: 0 / 0.00`、`Size of density/Fock matrix [MB's]: 14`、`Size of buffers [MB's]: 2`、`Number of periodic image cells considered: 27`、`Est. max. program size after HFX [MB's]: 243`；SCF 第 1 步 `1 OT DIIS 0.80E-01 68.5 0.00096341 -1102.1375916328 -1.10E+03`；`Trace(PS): 512.0000000000`。 |
| **P3** | SCF 第 2 步 `2 OT DIIS 0.80E-01 4.1 0.00064929 -1102.1607534171 -2.32E-02`。**Topics**：in-core operation；**怎么察觉"筛选太激进"导致的不稳定**。**思考题 1**：这个构型的 HOMO-LUMO gap 是多少？与 GGA 结果比如何？**把交换分数改成 20% 和/或 30%（"modify the input in two places!"——即 `SCALE_X` 与 `FRACTION` 两处）**，gap 怎么变？**截断库仑算符 + 长程校正**：像 HSE 那样，**交换所用算符与 1/r 之间的差**可以用**一个特殊的 GGA 交换泛函**来补偿；对截断库仑算符这也可行，**从而支持只嵌入极短程交换算符的 xc 泛函**；这样可**加速计算同时保留 HFX 的收益**；**该泛函随作用范围从 0 到 ∞ 从 PBE 平滑过渡到 PBE0**。**3rd task**：在 `&XC_FUNCTIONAL` 里（**在 `&PBE` 之外再加**）插入 **`&PBE_HOLE_T_C_LR / CUTOFF_RADIUS 2.5 / SCALE_X 0.25 / &END`**，并**把 `&INTERACTION_POTENTIAL` 的 `CUTOFF_RADIUS` 改成同一个值**；重跑单点并记录带隙。**思考题**：这么短的作用范围足以对带隙产生可观影响吗？**截断半径 2.5 Å 与 6.0 Å 两次计算的 `HFX_MEM_INFO\| Number of cart. primitive ERI's calculated` 差别大吗？** |
| **P3–P4** | **ADMM**：为缓解大基组下 HFX 的成本而提出的方法。**尤其是用 MOLOPT 基组时标准 HFX 变得太贵（CP2K 不能高效处理高度收缩的 AO）**。ADMM 引入 **`AUX_FIT_BASIS_SET`**，通过**投影**造出**辅助密度矩阵（ADM）**；**HFX 对这个 ADM 求值**，而**用 ADM 引入的误差用一个 GGA 交换泛函来校正**。 |
| **P4** | **4rd task：引入 ADMM**（原文序号就写作 "4rd"）。三步：① 插入一行 `BASIS_SET_FILE_NAME BASIS_ADMM`（需要时从 `cp2k/data` 拷该文件）；② **给每个 `&KIND` 插一行 `AUX_FIT_BASIS_SET cFIT3`**；③ 插入 `&AUXILIARY_DENSITY_MATRIX_METHOD` 段：**`METHOD BASIS_PROJECTION`（注释 "recommended, i.e. use a smaller basis for HFX / each kind will need an AUX_FIT_BASIS_SET"）** + **`ADMM_PURIFICATION_METHOD MO_DIAG`（注释 "recommended, this method is stable and allows for MD. can be expensive for large systems"）**。**原文重要限定**：本教程把 ADMM（很小的 `cFIT3`）与很小的主基组（`DZVP-GTH`）组合，**收益至多很小，而且结果不太准**；**ADMM 在配优质主基组（如 MOLOPT）时最有用**。**CP2K 2.7 有新的 ADMM 基组库 `BASIS_ADMM_MOLOPT`**（给出 SourceForge 链接）。**跑一遍输入，HOMO-LUMO gap 是多少？** **"追逐液态水中的电荷定域"**：**截断交换 + ADMM 的组合是跑杂化泛函 AIMD 最有效的方式**；有些体系 GGA DFT 与杂化的差别非常大，**其中之一是电离后的液态水（charge +1）——只有杂化才能形成预期的物种（OH 自由基）**（10.1063/1.3664746）。 |
| **P4** | **5th task（可选）：电离的水**。改造 ADMM 输入：**`LSD`**、`CHARGE 1`、`MULTIPLICITY 2`；**因为体系初始在电子结构上非常难，把收敛阈值 `EPS_SCF` 降到 `1.0E-5`（"twice"）**；**注意 `WFN_RESTART_FILE_NAME` 必须指向"同电荷、同多重度"的 GGA 计算结果（先把这个算出来）**。跑单点，**交换分数从 0.25 变到 0.50**，看 Mulliken 自旋布居能否复现 10.1021/ct1002225 的 Fig. 2；**分数取 0.5 时跑 50–100 fs 的 AIMD**（若时间允许），看自旋定域的那个水分子发生了什么，与 10.1063/1.3664746 是否一致。**本节声明不需要新文件**。 |
| **P4–P7** | **`water_pbe0_cheating.inp` 全文**（见 §4.11）：与 T13 的 `water_cheating.inp` 同源，差异在 `RUN_TYPE ENERGY`、`IOLEVEL MEDIUM`、`WFN_RESTART_FILE_NAME`、`SCF_GUESS RESTART`、`&SCF/&PRINT/&RESTART ON`，以及整段 `&XC`（PBE0 + HF + D3）。**注意：答案文件里 `&MOTION` 同时保留了 `&GEO_OPT` 与 `&MD` 两块，但 `RUN_TYPE` 是 `ENERGY`**（教学答案保留了后续任务的骨架）。 |

### 2.7 T16 `ex2018_scf_setup`（4 页）

> 源页：`events/2018_summer_school/scf_setup.txt`，最后修改 2018-06-17，作者 `mwatkins`。

| 页 | 要点 |
|---|---|
| **P1** | 标题 **"Sensible SCF setups"**，页眉带 `http://www.cp2k.org`。**SCF 的难点陈述（原文）**："The Kohn-Sham equations are **non-linear**. The potential changes as we optimise the Molecular Orbitals."（KS 方程是非线性的——优化分子轨道时势会变。）本练习探索若干选项，**以便对大多数体系获得快速且稳健的优化**。**Traditional Diagonalisation (TD)**：给出**周期性水盒子的 TD 基础输入** `scf_basic.inp`（见 §4.12）：`FORCE_EVAL METHOD QS`；`&DFT` 里 **两个 `BASIS_SET_FILE_NAME`**（`GTH_BASIS_SETS` + `BASIS_MOLOPT`）、`POTENTIAL_FILE_NAME POTENTIAL`；`&MGRID CUTOFF 300`；**`&QS EPS_DEFAULT 1.0E-12`**；`&SCF SCF_GUESS ATOMIC`（旁边注释掉的 `# SCF_GUESS RESTART`）、**`EPS_SCF 1.0E-5`**、**`&MIXING ALPHA 0.4`（注意：没写 `METHOD`）**；`&XC &XC_FUNCTIONAL Pade`；`&SUBSYS &CELL ABC 9.8528 9.8528 9.8528`（**注释给出来历：`# 32 H2O (TIP5P,1bar,300K) a = 9.8528`**）；`&COORD` 32 个 O 开始。 |
| **P2** | O 坐标续（共 32 个 O），H 坐标开始。 |
| **P3** | H 坐标续（共 64 个 H）；`&KIND H BASIS_SET DZVP-GTH / POTENTIAL GTH-PADE-q1`、`&KIND O BASIS_SET DZVP-GTH / POTENTIAL GTH-PADE-q6`；`&GLOBAL PROJECT H2O-32 / RUN_TYPE MD / PRINT_LEVEL MEDIUM`。**TASK（原文）**："This uses a rather small BASIS_SET DVZP-GTH which is **much too small for production runs**. Repeat the calculation using `BASIS_SET TZV2P-GTH`、`BASIS_SET DZVP-MOLOPT-GTH`、`BASIS_SET TZV2P-MOLOPT-GTH`。**You should change the basis set for each atomic type (kind) in each case.**"（注意原文把 DZVP 拼成了 **`DVZP`**——原文笔误。）**Orbital Transformation (OT)**：**"We can see the effect of changing to the OT method by simply changing the SCF section."** 给出 OT 版 `&SCF`（见 §4.12）：`SCF_GUESS ATOMIC`、**`EPS_SCF 1.0E-06`**、**`MAX_SCF 20`**、**`&OT ON MINIMIZER DIIS PRECONDITIONER FULL_ALL ENERGY_GAP 0.001`**、**`&OUTER_SCF MAX_SCF 2`**。**TASK**："See how OT compares with TD for the different basis sets you ran previously." |
| **P4** | **Other parameters**（原文："There are other factors that influence the effectiveness of the setups."）。**TASK 泛函**："We were using LDA (the particular parameterization is called PADE in CP2K). Try changing the functional to **`PBE`** (in the `XC` section) and see how this changes convergence. **Also change the pseudopotential you are using in the KIND sections so it matches the functional.**" **TASK 体系大小**："System size affects the efficiency too. You can find larger water boxes in the **`${main directory of my cp2k installation}/tests/QS/benchmarks`** directory, or online. **Change the CELL parameters and the coordinates of the atoms** and see how the methods scale. **You could also explore how the methods scale with number of processors used.**" **TASK 体系本身（原文称"probably the most important 'parameter'"）**："**Water is quite well behaved – largely meaning it is closed shell and has a large band gap. Try similar tests on a system you are interested in!**" |

### 2.8 T17 `ex2020_uzh_neb`（6 页）

> 源页：`exercises/2020_uzh_acpc2/ex03.txt`，最后修改 2020-04-21，作者 `jglan`。

| 页 | 要点 |
|---|---|
| **P1** | 研究 **S_N2 亲核取代**：`Cl⁻ + CH₃Cl ⟷ ClCH₃ + Cl⁻`。能量与力用 **PM6（Parameterization Method 6）**，一种相对便宜的电子的**半经验**模型；**原文提醒：要做准确的反应表征，应当用从头算方法，如 DFT 或更高等级**。**NEB 活化能**：用 NEB 找**最小能量路径（MEP）**。**MEP 的定义（原文）**：MEP 是 **3N 维**势能面上的一条**一维**路径，路径上**每一点在垂直于路径的所有方向上都是势能极小**；**MEP 至少经过一个鞍点，最高鞍点的能量就是该反应活化能垒的峰**。**先做几何优化**取得两个局部极小构型：给出 `geo.inp`（全文见 §4.13）：`GLOBAL` `PRINT_LEVEL LOW / PROJECT ch3cl / RUN_TYPE GEO_OPT`（注释 "Geometry optimization calculation"）；`&MOTION/&GEO_OPT MAX_FORCE 1.0E-4 / MAX_ITER 2000 / OPTIMIZER BFGS / &BFGS TRUST_RADIUS [bohr] 0.1`；`&FORCE_EVAL METHOD Quickstep`；**`&DFT CHARGE -1`（注释 "There is a negatively charged anion"）**；**`&QS METHOD PM6`（注释 "Parametrization Method 6"）+ `&SE`**；`&SCF SCF_GUESS ATOMIC / EPS_SCF 1.0E-5 / MAX_SCF 50 / &OUTER_SCF EPS_SCF 1.0E-7 / MAX_SCF 500`；**`&POISSON PERIODIC NONE / PSOLVER WAVELET`（注释 "POISSON solver for non-periodic calculation"）**；`&CELL ABC 10.0 10.0 10.0 / PERIODIC NONE`；`&COORD` 六个原子：`C`、三个 `H`、两个 `Cl`（坐标见 §4.13）。 |
| **P2** | 坐标续。**TASK 1**："Run the geometry optimization calculation. **Modify the initial geometry guess in the input and run a second optimization to obtain the other local minimum geometry (The other Cl needs to make a covalent bond with the C).**" **NEB**：从 **`GEO_OPT` 轨迹（`ch3cl-pos-1.xyz` 的最后一步）**取出两个优化后的几何，放到单独文件夹，命名 **`init.xyz`** 与 **`final.xyz`**。`neb.inp`：`&GLOBAL PRINT_LEVEL LOW / PROJECT ch3cl / RUN_TYPE BAND`（注释 "Nudged elastic band calculation"）；`&MOTION/&BAND NUMBER_OF_REPLICA 10`（注释 "Number of 'replica' geometries along the path"）/ `K_SPRING 0.05` / `&OPTIMIZE_BAND OPT_TYPE DIIS / &DIIS MAX_STEPS 1000` / **`BAND_TYPE CI-NEB`（注释 "Climbing-image NEB"）** / **`&CI_NEB NSTEPS_IT 5`（注释 "First take 5 normal steps, then start CI"）** / 两个 `&REPLICA COORD_FILE_NAME init.xyz` 与 `final.xyz` / `&PROGRAM_RUN_INFO INITIAL_CONFIGURATION_INFO`。 |
| **P3** | `neb.inp` 其余：`&FORCE_EVAL METHOD Quickstep / &DFT … same as GEO_OPT …`（**原文用省略号，实际要把 `geo.inp` 的整个 `&DFT` 搬过来**）；`&SUBSYS &CELL ABC 10.0 10.0 10.0 / PERIODIC NONE`；**`&TOPOLOGY COORD_FILE_NAME init.xyz / COORDINATE xyz`**。**主输出里每步一段**，照抄（见 §4.13）：`BAND TYPE = CI-NEB`、**`BAND TYPE OPTIMIZATION = SD`**、`STEP NUMBER = 1`、`NUMBER OF NEB REPLICA = 10`、**`DISTANCES REP =` 9 个数**、**`ENERGIES [au] =` 10 个数**、`BAND TOTAL ENERGY [au] = -248.08548199708440`。**原文说明**：这些段给出**每个 replica 到相邻点的距离与其能量**；**最后一段对应收敛后的 NEB 轨迹**。**TASK 2**："Run the NEB calculation. **Find the activation barrier of the reaction in eV.**" **自由能面（FES）**：采样 FES 是探索各种稳定构型与可能反应路径的便利方法；对复杂体系要用高级采样（**umbrella sampling、metadynamics、parallel tempering…**），**但对这个简单 S_N2 反应我们用无偏 MD**。**FES 是高维自由能景观向少数（通常两个）维度的投影**，这两维叫**集体变量（CV）**，**必须选得能区分各种稳定构型、并能充分描述反应路径**；对复杂体系**选 CV 是非平凡任务**；**本体系选取很简单：两个 Cl 阴离子到中心 C 的距离作为 CV**。**为帮助采样我们关心的 FES 区域，在 MD 里加约束，防止 Cl 阴离子跑得太远。** 给出 `md.inp`。 |
| **P4** | `md.inp` 前半（全文见 §4.13）：`&GLOBAL PRINT_LEVEL LOW / PROJECT ch3f / RUN_TYPE MD`；`&MOTION/&MD ENSEMBLE NVT / STEPS 200000 / TIMESTEP 0.5 / TEMPERATURE 1000.0`；**`&THERMOSTAT TYPE NOSE / &NOSE TIMECON 100.`**；**两个 `&CONSTRAINT/&COLLECTIVE`**（`INTERMOLECULAR`、`COLVAR 1`/`COLVAR 2`、**`TARGET 1.8`**、**`&RESTRAINT K 0.005`**）；**`&FREE_ENERGY/&METADYN DO_HILLS .FALSE.`**（注释 "Section to print out the values of CVs every step"）+ **两个 `&METAVAR SCALE 0.2 / COLVAR 1|2`** + `&PRINT/&COLVAR COMMON_ITERATION_LEVELS 3 / &EACH MD 1`；`&FORCE_EVAL …`（原文省略号）。 |
| **P5** | `md.inp` 其余：`&SUBSYS &CELL ABC 10.0 10.0 10.0 / PERIODIC NONE`；`&COORD`（与 `geo.inp` 完全相同的六个原子）；**`&COLVAR/&DISTANCE ATOMS 1 5`** 与 **`&COLVAR/&DISTANCE ATOMS 1 6`**（注释 "CV definitions"）。**自由能公式（原文）**：`F(s) = −kT log(P(s))`，其中 `s` 是 CV 集合、`P(s)` 是体系取该组 CV 值的概率。**给出完整 Python 脚本**从 **`ch3f-COLVAR.metadynLog`** 算 FES（见 §4.13），**并提醒"别忘了改脚本里的温度！"**。 |
| **P6** | **1000 K 的示例输出**：**清楚看到两个局部极小**，对应**一个 Cl 与 C 共价成键（距离 1.8 Å）而另一个在 ~2.5 Å 附近**。**TASK 3**："Run the MD calculation for **400K, 800K, 1200K and 1600K**. (The calculations can take a while.) Create the corresponding FES plots and discuss the temperature dependence. **In general, how does potential energy differ from free energy? For our reaction, what are the activation barriers from the different free energy surfaces? How and why do they differ from the NEB barrier?**" |

---

## 3. 核心逻辑链（重点）

### 3.1 截断能收敛测试的方法论（T12）——把"怎么做收敛测试"变成可复制流程

#### 3.1.1 为什么必须测（T12 P1–P2）

1. **QUICKSTEP 必须在实空间网格上数值表示某些函数**（电子密度、乘积高斯）。这些函数无法解析积分，只能映射到网格上求和 ⇒ **网格粗细直接决定积分误差**（T12 P1）。
2. **采用 multi-grid：不同"宽窄"的高斯走不同层级的网格**。窄而尖 → 细网格；宽而平滑 → 粗网格；**电子密度例外，永远在最细层**（T12 P1）。
3. ⇒ **两个独立的自由度**：最细层多细（`CUTOFF`）、以及"哪个高斯去哪一层"（`REL_CUTOFF`）。**只调一个不够**（T12 P2、P7、P10）。
4. **两个失效模式（这是最该背下来的一段，T12 P2）**：
   - `CUTOFF` 太低 ⇒ **所有**层都粗 ⇒ 计算不准；
   - **`REL_CUTOFF` 太低 ⇒ 即使 `CUTOFF` 很高，所有高斯仍被压到最粗层** ⇒ **有效积分网格依然太粗**。
5. **反向陷阱（T12 P7）**：**随 `CUTOFF` 增大，被分到最细层的高斯数目反而减少**。所以"只堆 `CUTOFF`"最终会让能量收敛变慢——增加的部分被"更多高斯下沉到粗层"抵消掉。

#### 3.1.2 网格是怎么搭出来的（T12 P1–P2，机制层）

| 项 | 规则 | 出处 |
|---|---|---|
| 层数 | `NGRIDS`，**默认 4** | T12 P1 |
| 最细层截断 | `CUTOFF`，**默认单位 Ry**，越高越细 | T12 P1 |
| 各层递推 | **`Ecut_i = Ecut_1 / α^(i−1)`**，`α` 默认 **3.0** | T12 P1 |
| `α` 可配置 | 自 **CP2K 2.0** 起用 **`PROGRESSION_FACTOR`** | T12 P1 |
| 高斯去哪一层 | `REL_CUTOFF` 定义"**单位标准差高斯所覆盖的参考网格**"的平面波截断；一个高斯映射到**它覆盖的网格点数 ≥ 参考网格点数**的**最粗**那一层 | T12 P1–P2 |
| 设计意图 | CP2K 尽量让**每个高斯覆盖的网格点数大致相同**（不论宽窄） | T12 P1 |

> **读法提示（T12 P2 原文）**：`REL_CUTOFF` 并不是"某个网格的截断"，而是**一根参考尺**——它决定"一个高斯要覆盖多少格点才算够"。把它调大 = 要求高斯覆盖更多格点 = **更多高斯被推到更细的层**。

#### 3.1.3 测试怎么设计（T12 P2–P9，可复制流程）

**前置约定**：目标精度先写死。原文写法：**"say, 10⁻⁶ Ry in total energy"**（T12 P2），后文重复"10⁻⁶ Ry 精度所需的 CUTOFF"（T12 P4）。

**第 0 步 · 写模板 `template.inp`（T12 P2–P4）**
- 用**占位标记** `LT_cutoff` / `LT_rel_cutoff` 占住 `&MGRID` 里两个位置，交给 `sed` 替换。
- `RUN_TYPE ENERGY`：**不算力**。原文理由：只关心网格收敛时看总能通常就够，而要做一连串计算，**每次越便宜越好**。
- **`PRINT_LEVEL MEDIUM`：不是"为了看得爽"，而是必须**——要看 "how many Gaussian functions are mapped onto which grid"，**用来判断 `REL_CUTOFF` 选得合不合适**。
- **`MAX_SCF 1`：故意不做自洽循环**。原文理由：*"irrespective of self-consistency, grid settings with fine enough meshes should give consistent energies."*
- 测试体系可以比生产体系小/基组可以更小：模板用 **`SZV-GTH-PADE`**（而 T10 的静态算例用 `DZVP-GTH-PADE`）。**这一点决定了本测试只回答"网格是否够细"，不回答"基组是否够好"。**

**第 1 步 · 扫 `CUTOFF`：先把 `REL_CUTOFF` 钉在高位（T12 P4–P7）**
- **先把 `REL_CUTOFF` 设"相对高"**；原文给出经验值：**`REL_CUTOFF 60 Ry` 对大多数计算通常够用**，而且**后面会再验证它**。
- 扫描范围：**50 Ry → 500 Ry，步长 50 Ry**（共 10 个点）。
- 自动化三段式（T12 P4/P5/P7）：`cutoff_inputs.sh`（建目录 + `sed` 生成输入 + 拷 `BASIS_SET`/`GTH_POTENTIALS`）→ `cutoff_run.sh`（`mpirun` 提交，**每算例 2 核、共 16 核 ⇒ 最多 8 个并行**）→ `cutoff_analyse.sh`（grep 提取 → 汇总成 `.ssv`）。
- 提取方式（**照抄**）：总能 `grep -e '^[ \t]*Total energy' … | awk '{print $3}'`；层数 `grep -e '^[ \t]*QS\| Number of grid levels:' … | awk '{print $6}'`；每层高斯数 `grep -e '^[ \t]*count for grid' … | awk -v igrid=$igrid '(NR == igrid){print $5}'`。原文另给**正则 `^[ \t]*Total energy:`**（T12 P6）。

**第 2 步 · 用 `CUTOFF` 扫描结果"定档"——判据是"能量平台 + 网格使用合理"两个条件（T12 P7）**
- **能量判据**：与更高 cutoff 的平台比，误差 < **10⁻⁸ Ha**（`REL_CUTOFF = 60 Ry` 下 `CUTOFF ≥ 250 Ry`）。
- **效率/合理性判据（原文给出的选点理由，非常重要）**：选 **250 Ry** 是因为它是 *"the **lowest cutoff energy where the finest grid level is used**, but at the same time **with the majority of the Gaussians on the coarser grids**"*。
  - 换句话说：**不能只看能量平了没有，还要看最细层有没有被真正用起来**（`NG on grid 1 > 0`）；同时**别把绝大多数高斯都堆到最细层**（那说明还能更省）。
  - 数据表印证（T12 P7）：250 Ry 时 `NG on grid 1 = 264`；50 Ry 时 `NG on grid 1 = 5048`（最细层没被用上，`NG on grid 4 = 0`）；450/500 Ry 时 `NG on grid 1 = 0`（**最细层完全没用上** ⇒ 高 cutoff 纯浪费）。

**第 3 步 · 固定 `CUTOFF`，扫 `REL_CUTOFF` 验证（T12 P8–P10）**
- 固定 `CUTOFF 250`，扫 **`REL_CUTOFF = 10 20 30 40 50 60 70 80 90 100`**（共 10 个点）。
- 脚本只需把 `rel_cutoff_inputs.sh` / `rel_cutoff_run.sh` / `rel_cutoff_analyse.sh` 里的循环变量换掉、把注释头改成 `# CUTOFF = ${cutoff}`。
- **判据**：`REL_CUTOFF ≥ 60 Ry` 时总能误差 < **10⁻⁸ Ha**。
- **物理读法**：`REL_CUTOFF` 越大，越多高斯被映射到更细网格；到 60 Ry 后能量不再变。

**第 4 步 · 交付结论（T12 P10 原文）**
```
&MGRID
  CUTOFF 250
  REL_CUTOFF 60
&END MGRID
```
是"对该精度要求"足够的设置。

#### 3.1.4 `CUTOFF` 与 `REL_CUTOFF` 的关系（一句话背下来）

> **`CUTOFF` 决定"最细的那层网格有多细"；`REL_CUTOFF` 决定"有多少高斯能落到细网格上"。**
> 前者是**分辨率**，后者是**分配规则**。**两者必须一起收敛**：只加 `CUTOFF` 会把高斯往粗层挤（T12 P7），
> 只加 `REL_CUTOFF` 而 `CUTOFF` 太低则所有层都粗（T12 P2）。
> **正确顺序：先钉高 `REL_CUTOFF`（60 Ry）扫 `CUTOFF` 定档，再固定 `CUTOFF` 扫 `REL_CUTOFF` 复核。**

#### 3.1.5 这套流程的可迁移性（连同 T12 P3 的伏笔）

- **必须自己重跑**：250/60 是**Si bulk8 + SZV-GTH-PADE** 的结论，不是普适推荐值（G 层 `03_scf_convergence.md` §2.5 也这样提醒）。
- **体系/基组变了就要重测**：T12 P3 的模板用 `SZV-GTH-PADE`，而 T10 用 `DZVP-GTH-PADE`；**基组里最陡的高斯指数决定"最细层要多细"**，所以换基组必须重测（这一点在 T12 里是隐含的，`REL_CUTOFF` 的定义直接依赖高斯的宽度分布）。
- **用途变了也要重测**：T13/T14 的输入注释明确写 **"certain calculations (e.g. geometry optimization, vibrational frequencies, NPT and cell optimizations, need higher cutoffs)"**（T13 P7、T14 P4）——**力/应力类任务比单点能量需要更细的网格**。

### 3.2 SCF 设置的选择逻辑（T16）——OT vs 对角化

#### 3.2.1 T16 的原话与实验设计

T16 本身**没有给判定表**，它给的是一条**对照实验路径**（T16 P1–P4）：

```
基线：32 H2O 周期性盒子（TIP5P, 1 bar, 300 K, a = 9.8528 Å）+ DZVP-GTH + PADE(LDA) + CUTOFF 300
  ↓ 只改 &SCF 段
TD 版：SCF_GUESS ATOMIC / EPS_SCF 1.0E-5 / &MIXING ALPHA 0.4
OT 版：SCF_GUESS ATOMIC / EPS_SCF 1.0E-06 / MAX_SCF 20
       &OT ON / MINIMIZER DIIS / PRECONDITIONER FULL_ALL / ENERGY_GAP 0.001
       &OUTER_SCF MAX_SCF 2
  ↓ 逐层加变量（T16 P3–P4 TASK）
  ① 换基组：DZVP-GTH → TZV2P-GTH / DZVP-MOLOPT-GTH / TZV2P-MOLOPT-GTH（每个 KIND 都要改）
  ② 换泛函：PADE(LDA) → PBE（并同步把 KIND 里的赝势换成匹配的）
  ③ 换体系大小：改 CELL 与坐标（更大的水盒子在 tests/QS/benchmarks）
  ④ 换并行核数
  ⑤ 换体系本身（"probably the most important 'parameter'"）
```

**T16 的核心教学句（P4 原文）**：
> "And of course, probably the most important 'parameter' is **the system itself**. Water is quite well behaved – largely meaning it is **closed shell and has a large band gap**. Try similar tests on a system you are interested in!"

即：**SCF 求解器的选择不是普适知识，必须在"你的体系 + 你的基组"上实测**；水（闭壳、大带隙）是**最有利**的情形，在它上面测出的结论**不能外推到金属/小带隙/强关联体系**。

#### 3.2.2 结合 A–G 层给出的"该怎么判断"（H 层证据 + G 层裁定）

> 下面每条都标明是 H 层 T16 给的、还是 G/A/F 层给的；**冲突时以 G 层为准**（AGENTS.md §5）。

| 判据 | 该用哪个 | 证据 |
|---|---|---|
| **有没有带隙** | **有带隙（半导体/绝缘体/分子）→ OT**；**没有带隙（金属/导体）→ 传统对角化 + smearing** | H：T16 只把水（大带隙）当 OT 的演示对象（T16 P3–P4）；明确判据在 A/F 层（`decide.md` §28、`course_learned`/`MAPPING` 转述讲师口径） |
| **体系里有几个原子 / 基函数** | **大体系优先 OT**（对角化的 `O(N³)` 对角化 + 稠密矩阵会成为瓶颈） | H：T16 P4 的 TASK 就是"改 CELL 与坐标看方法怎么 scale"；G：`02_dft_methods.md` §3、`03_scf_convergence.md` §1.4 |
| **是否要 k 点** | **要 k 点 → 只能对角化**（OT 只在 Γ 点） | G 层权威；H 层 T13–T17 全部是 Γ 点计算，未涉及 |
| **是否要 DFT+U** | **DFT+U → 用 OT** | G 层权威；T16 未涉及 |
| **SCF 死活不收敛** | 先调**求解器内部参数**（`MINIMIZER` / `PRECONDITIONER` / `OUTER_SCF`），最后才动结构/初猜 | H：T16 P3 的 OT 段给全了这三项；T13 P7 的答案文件注释直接说 `MINIMIZER DIIS` 是 "**the most robust choice (DIIS might sometimes be faster, but not as stable)**"；G：`03_scf_convergence.md` §1.4–§1.5 给出 `MAX_SCF` 16–32、`OUTER_SCF/MAX_SCF` 8–16 |

#### 3.2.3 切换的后果（T16 + T13/T14/T15 的实测证据）

1. **`&MIXING` 段在 OT 下失效**。T10 P5 原文：**`&MIXING` 只适用于传统对角化；OT 用另一套电荷混合方式**。所以 T16 从 TD 切 OT 时，**`&MIXING ALPHA 0.4` 被整段换掉了**（T16 P1 vs P3）——不是"忘了写"，而是**必须换机制**。
2. **相关关键字必须一起换**：
   - TD 侧：`EPS_SCF 1.0E-5` + `&MIXING`（+ `ADDED_MOS`/`&SMEAR` 若需要）。
   - OT 侧：`EPS_SCF 1.0E-06` + **`MAX_SCF 20`** + `&OT` + **`&OUTER_SCF MAX_SCF 2`** + **`ENERGY_GAP 0.001`**（T16 P3）。
   - **`ENERGY_GAP` 是 OT 的特有旋钮**：它是预条件子用的"能隙估计"，**给错会让 OT 收敛变差**；T16 直接给 `0.001`（Ha），**这是为教学演示固定值，不是对水的推荐值**。
3. **`MAX_SCF` 的含义变了**：G 层 `03_scf_convergence.md` §1.4：**OT 是两层循环——内层 `SCF/MAX_SCF` 控 OT 迭代步数，外层 `SCF/OUTER_SCF/MAX_SCF` 控"重置预条件子"的次数**；官方建议内层 **16–32**、外层 **8–16**。T16 用 **20 / 2**，**是为了每次对照实验都快**（教学值，见 §3.3）。
4. **初猜策略不变但更重要**：T16 两版都用 `SCF_GUESS ATOMIC`，并留了注释掉的 `# SCF_GUESS RESTART`（T16 P1）；而 T13/T15 的生产做法是"**先 GGA 跑出 wfn，再 `SCF_GUESS RESTART` + `WFN_RESTART_FILE_NAME` 开杂化**"（T15 P1–P2）。
5. **换成 OT 后能开的东西**：`PRECONDITIONER`（T16 用 `FULL_ALL`；T13/T14/T15 用 `FULL_SINGLE_INVERSE`）与 `MINIMIZER`（T16 用 `DIIS`；T14 用 `CG`；T13/T15 用 `DIIS`）。**这三个值在不同练习里全不一样，正好说明"必须实测"**。

### 3.3 八个练习的设计意图：每个练习想让你掌握什么，以及**哪些设置是"为了教学"而非"生产"**

#### 3.3.1 逐练习设计意图

| 练习 | 想让你掌握的核心能力 | "读完应该能自己做"的事 |
|---|---|---|
| T10 | **读懂一份 CP2K 输入 + 读懂一份 CP2K 输出** | 从零写 Si/简单晶体单点输入；从 `.out` 里认出电子数、SCF 收敛、能量分解、力；知道金属要加 smearing 且引用 TS→0 自由能 |
| T11 | **会设优化判据、会读优化输出、会续算** | 给任意体系设 `GEO_OPT` 四判据；判断"优化完了没有"；作业挂了会用 `-1.restart` 继续 |
| T12 | **会把"参数收敛测试"做成自动化流程** | 对**自己的**体系重跑 CUTOFF 与 REL_CUTOFF 收敛；会用 `MULTIGRID INFO` 判断选点是否浪费 |
| T13 | **把能跑的单点变成能分析的生产 AIMD** | 压输出、限墙钟、关 wfn 写盘、开重启历史；从 `.ener` 判断守恒与平衡；VMD 出 g(r)/IR |
| T14 | **表面吸附体系的标准三段式：单点 → 密度差 → 相对稳定性 → 动力学** | 用 cubecruncher 做结合诱导密度差；用 D3 处理色散主导的吸附；比较两种吸附模式 |
| T15 | **在凝聚相里把杂化泛函跑起来并控制成本** | 先 GGA 出 wfn 再开 HFX；设截断库仑半径 ≤ L/2；用 `&SCREENING` 保稳定；用 ADMM 换成本 |
| T16 | **建立"SCF 求解器是体系依赖的实测决策"这个观念** | 拿到新体系时，会搭 TD/OT 两版做对照，并在换基组/泛函/尺寸后重测 |
| T17 | **走完反应路径的完整链条：两端 OPT → CI-NEB → 自由能面** | 会读 NEB 主输出的 `DISTANCES REP` / `ENERGIES [au]` 得到能垒；会用受约束 MD + `DO_HILLS .FALSE.` 导出 CV 并用直方图算 FES |

#### 3.3.2 "为了教学"而非"生产"的设置清单（**这是引用这些输入卡时最容易踩的坑**）

| 位置 | 教学设置 | 为什么是教学 | 生产该怎么做 |
|---|---|---|---|
| **T12 P4** | `MAX_SCF 1` | **故意不做自洽**，只为快速扫网格 | 正常生产用默认/足够大的 `MAX_SCF` |
| **T12 P3** | 测试模板用 `SZV-GTH-PADE`（比 T10 的 `DZVP-GTH-PADE` 更小） | 让 10 次扫描更快 | 网格收敛结论**可迁移**，但要在**生产基组**上复核（换基组 ⇒ 换高斯宽度分布 ⇒ 可能要更高 cutoff） |
| **T12 P3** | `&CELL SYMMETRY CUBIC` | 测试用固定对称性立方胞 | 视体系而定 |
| **T12 P6** | 输出里 `*** SCF run NOT converged ***` | **`MAX_SCF 1` 下的正常现象**，**不是错误** | 生产里出现这行才是真问题 |
| **T11 P2** | `EPS_SCF 1.0E-05`、`CUTOFF 200` / `REL_CUTOFF 30` | 5 页的小教程，H₂O 一个分子；**为了几分钟跑完** | H₂O 分子也要按 T12 流程测 cutoff；`EPS_SCF` 通常 1e-6–1e-7 |
| **T11 P2** | `&PRINT/&RESTART OFF` | 关掉每步 restart 写盘 | 生产按需开 |
| **T16 P1** | `EPS_DEFAULT 1.0E-12` 而 `EPS_SCF 1.0E-5` | **故意把数值底线压得很紧、SCF 判据放得很松**，让 TD/OT 的效率差异**看得清楚** | 生产按 G 层/A 层推荐（如 `EPS_DEFAULT 1e-10`、`EPS_SCF 1e-6`） |
| **T16 P3** | `MAX_SCF 20` + `OUTER_SCF MAX_SCF 2` + `ENERGY_GAP 0.001` | **让每次对照实验都很快**；官方建议内层 16–32 / 外层 8–16 | 按 G 层 `03_scf_convergence.md` §1.4 的官方区间设；`ENERGY_GAP` 按体系带隙给 |
| **T16 P1/P3** | 基组用 `DZVP-GTH` 并**明文写"much too small for production runs"**（T16 P3） | 教学开场用最小基组 | 按 T16 P3 的 TASK 换成 `TZV2P-GTH`/`DZVP-MOLOPT-GTH`/`TZV2P-MOLOPT-GTH` |
| **T13 P1** | 基组 `DZVP-GTH`（来自 `HFX_BASIS`），**明文写"比液态水该用的要小"** | 为跑得快 | `TZV2P-GTH`、`TZV2P-MOLOPT-GTH`、`cc-TZV2P` 或更好 |
| **T13 P1/P6** | `WALLTIME 300`（正文）vs `WALLTIME 1800`（答案文件） | 课堂时限 | 按队列时限设 |
| **T13 P2** | `&RESTART OFF`（SCF 的打印）+ `&MO_CUBES WRITE_CUBE .FALSE.` + `&E_DENSITY_CUBE OFF` | **教学点就是"生产模式要压 IO"** | 与教学相反才是对的：**保持压低 IO**（这条是"教学即生产"的少数例外） |
| **T13 P1/P6** | `MINIMIZER DIIS`（正文列在"要改的关键字"里，实际在 `&OT` 段内） | 与 `RUN_TYPE MD` 等并列，**容易误当成顶层关键字** | 抄的时候认准它在 `&SCF &OT` 里（T13 P7 答案文件为证） |
| **T13 P7 / T14 P4** | `CUTOFF [Ry] 400`，注释写"几何优化/振动/NPT/晶胞优化需要更高" | 400 是**给水/氧化物 GGA 的通用起点**，不是实测收敛值 | 按 T12 流程在自己体系上测 |
| **T14 P1–P3** | "**只有最小的 slab 模型**"；`ABC 10.2270 11.3460 20.000` | 为加速；**原文自己提醒"slab 厚度会起重要作用"**（T14 P3） | 做 slab 厚度收敛测试 |
| **T14 P3** | AIMD 只跑 ~1000 步 ≈ 0.5 ps | "跑几个小时就该结束" | **原文自己说"要有统计意义需要更长的轨迹"**（T14 P3） |
| **T14 P5 vs T13 P7** | 同一个 `&OT` 段，`MINIMIZER` 一个是 `CG`（T14）、一个是 `DIIS`（T13） | **两个练习合起来教"这个值必须实测"** | 按 G/A/F 层"跑几步比 `UsedTime[s]`"的做法实测 |
| **T15 P3** | `AUX_FIT_BASIS_SET cFIT3` + 主基组 `DZVP-GTH`，**原文自己承认"收益至多很小、结果不太准"** | **只为演示 ADMM 的机械步骤** | 用优质主基组（MOLOPT）+ `BASIS_ADMM_MOLOPT` / `BASIS_ADMM_UZH` |
| **T15 P2** | `MAX_MEMORY 4000`（MB per MPI rank）、`EPS_STORAGE_SCALING 0.1` | 注释写"use as much as need to get **in-core** operation"——**是这台机器的内存数** | 按自己的节点内存调 |
| **T15 P4** | `LSD` + `CHARGE 1` + `MULTIPLICITY 2` + `EPS_SCF 1.0E-5`（放宽两倍） | 电离水初始极难，**为了让它能跑起来** | 生产要回到 1e-6–1e-7 并检查自旋态 |
| **T17 P1/P4** | `&QS METHOD PM6` + `&SE`（半经验） | **原文明说"要做准确的反应表征，应当用 DFT 或更高"** | 换 DFT |
| **T17 P2** | `K_SPRING 0.05` | 单一取值，未做弹簧常数敏感性 | F 层经验：粗算 0.08–0.1 易收敛，精算降到 0.02 |
| **T17 P4** | `STEPS 200000`、`TIMESTEP 0.5`（fs）、`TEMPERATURE 1000.0`、`TIMECON 100.` | 让 2D FES 在课堂时间内铺满 | 生产按体系定温度/时长；`TIMECON` 按 G 层 `04_sampling_md.md` 推荐 |
| **T17 P5** | `PROJECT ch3f` 与整个练习的 `ch3cl` 不一致 | 原文沿用了 CH₃F 版本残留（见 §6） | 统一工程名，否则输出前缀混乱 |
| **T17 P6** | `TASK 3` 要跑 400/800/1200/1600 K 四个温度 | **教学重点是"温度依赖 + 自由能与势能的区别"** | 按需选温度 |

---

## 4. 可执行要点（照抄）

> **说明**：本节把 8 份里出现的**完整输入、命令、脚本、数据表**照抄下来。
> **凡 G 层已逐字收录的输入**（T10 的 `Si_bulk8.inp`、T17 的 NEB 输入块），
> 此处**只给指针 + 只抄增量**（见 §5）；其余全部原文照抄。
> **单位、关键字、文件名、数字一律照抄，未做任何"规范化"。**

### 4.1 T10：主输入 `Si_bulk8.inp`

> **指针**：**G 层 `references/official/01_global_and_units.md` §5.2 已逐字收录本输入的全文**，
> 并在 §5.3 逐关键字讲解、§5.4 给运行命令、§5.5 给产物、§5.6 给结果检查要点、§5.7 讲 smearing。
> **此处不重复**。H 层补的增量见 §4.2（原材料条目）与 §4.16（输出表）。

**运行命令（T10 P6，照抄）**：
```bash
mpirun -n 2 cp2k.popt -o Si_bulk8.out Si_bulk8.inp &
```

**续算改动（T10 P6，照抄）**：
```
SCF_GUESS RESTART
```

### 4.2 T10：`BASIS_SET` / `GTH_POTENTIALS` 里的**原材料条目**（G 层未收录，新）

**`BASIS_SET` 文件中的 Si DZVP-GTH-PADE 条目（T10 P3 照抄）**：
```
Si DZVP-GTH-PADE
2
3 0 1 4 2 2
1.2032422345 0.3290350445 0.0000000000 0.0474539126 0.0000000000
0.4688409786 -0.2533118323 0.0000000000 -0.2594473573 0.0000000000
0.1679863234 -0.7870946277 0.0000000000 -0.5440929303 0.0000000000
0.0575619526 -0.1909898479 1.0000000000 -0.3624010364 1.0000000000
3 2 2 1 1
0.4500000000 1.0000000000
```

**`GTH_POTENTIALS` 文件中的 Si GTH-PADE-q4 条目（T10 P3 照抄）**：
```
Si GTH-PADE-q4 GTH-LDA-q4
2 2
0.44000000 1 -7.33610297
2
0.42273813 2 5.90692831 -1.26189397
3.25819622
0.48427842 1 2.72701346
```
> T10 P3 的解读：基组名 **`DZVP-GTH-PADE`** = double-ζ with polarisation，为 GTH PADE LDA 赝势优化；
> 赝势名 **`GTH-PADE-q4`** = Geodecker-Teter-Hutter PADE LDA 赝势、**q4 = 4 个价电子**。
> 条目名里的 `GTH-LDA-q4` 是它的**别名**（同一行第二个字段）。

### 4.3 T12：收敛测试三件套（**完整照抄**）

**（a）`template.inp`（T12 P2–P3）** —— 占位标记 `LT_cutoff` / `LT_rel_cutoff` 是重点：
```
&GLOBAL
  PROJECT Si_bulk8
  RUN_TYPE ENERGY
  PRINT_LEVEL MEDIUM
&END GLOBAL
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME BASIS_SET
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    &MGRID
      NGRIDS 4
      CUTOFF LT_cutoff
      REL_CUTOFF LT_rel_cutoff
    &END MGRID
    &QS
      EPS_DEFAULT 1.0E-10
    &END QS
    &SCF
      SCF_GUESS ATOMIC
      EPS_SCF 1.0E-6
      MAX_SCF 1
      ADDED_MOS 10
      CHOLESKY INVERSE
      &SMEAR ON
        METHOD FERMI_DIRAC
        ELECTRONIC_TEMPERATURE [K] 300
      &END SMEAR
      &DIAGONALIZATION
        ALGORITHM STANDARD
      &END DIAGONALIZATION
      &MIXING
        METHOD BROYDEN_MIXING
        ALPHA 0.4
        BETA 0.5
        NBROYDEN 8
      &END MIXING
    &END SCF
    &XC
      &XC_FUNCTIONAL PADE
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS
    &KIND Si
      ELEMENT Si
      BASIS_SET SZV-GTH-PADE
      POTENTIAL GTH-PADE-q4
    &END KIND
    &CELL
      SYMMETRY CUBIC
      A 5.430697500 0.000000000 0.000000000
      B 0.000000000 5.430697500 0.000000000
      C 0.000000000 0.000000000 5.430697500
    &END CELL
    &COORD
      Si 0.000000000 0.000000000 0.000000000
      Si 0.000000000 2.715348700 2.715348700
      Si 2.715348700 2.715348700 0.000000000
      Si 2.715348700 0.000000000 2.715348700
      Si 4.073023100 1.357674400 4.073023100
      Si 1.357674400 1.357674400 1.357674400
      Si 1.357674400 4.073023100 4.073023100
      Si 4.073023100 4.073023100 1.357674400
    &END COORD
  &END SUBSYS
  &PRINT
    &TOTAL_NUMBERS ON
    &END TOTAL_NUMBERS
  &END PRINT
&END FORCE_EVAL
```
> **与 T10 静态算例的差异（值得注意，不是笔误）**：`RUN_TYPE ENERGY`（不算力）、`PRINT_LEVEL MEDIUM`、
> **`MAX_SCF 1`**、`ADDED_MOS 10` + `&SMEAR ON`（费米-狄拉克 300 K）+ `CHOLESKY INVERSE`、
> `&MIXING` 多一个 `BETA 0.5`、基组换成 **`SZV-GTH-PADE`**、`&CELL` 多 `SYMMETRY CUBIC`、
> `&PRINT/&TOTAL_NUMBERS ON`。（对比 T10 P2 的输入）

**（b）`cutoff_inputs.sh`（T12 P4 完整照抄）**：
```bash
#!/bin/bash
cutoffs="50 100 150 200 250 300 350 400 450 500"
basis_file=BASIS_SET
potential_file=GTH_POTENTIALS
template_file=template.inp
input_file=Si_bulk8.inp
rel_cutoff=60
for ii in $cutoffs ; do
  work_dir=cutoff_${ii}Ry
  if [ ! -d $work_dir ] ; then
    mkdir $work_dir
  else
    rm -r $work_dir/*
  fi
  sed -e "s/LT_rel_cutoff/${rel_cutoff}/g" \
      -e "s/LT_cutoff/${ii}/g" \
      $template_file > $work_dir/$input_file
  cp $basis_file $work_dir
  cp $potential_file $work_dir
done
```
```bash
chmod u+x ./cutoff_inputs.sh
./cutoff_inputs.sh
```

**（c）`cutoff_run.sh`（T12 P5 完整照抄）**：
```bash
#!/bin/bash
cutoffs="50 100 150 200 250 300 350 400 450 500"
cp2k_bin=cp2k.popt
input_file=Si_bulk8.inp
output_file=Si_bulk8.out
no_proc_per_calc=2
no_proc_to_use=16
counter=1
max_parallel_calcs=$(expr $no_proc_to_use / $no_proc_per_calc)
for ii in $cutoffs ; do
  work_dir=cutoff_${ii}Ry
  cd $work_dir
  if [ -f $output_file ] ; then
    rm $output_file
  fi
  mpirun -np $no_proc_per_calc $cp2k_bin -o $output_file $input_file &
  cd ..
  mod_test=$(echo "$counter % $max_parallel_calcs" | bc)
  if [ $mod_test -eq 0 ] ; then
    wait
  fi
  counter=$(expr $counter + 1)
done
wait
```
```bash
chmod u+x ./cutoff_run.sh
./cutoff_run.sh &
```
> T12 P5 说明：这是在一台 **24 核本地工作站**上跑，**总共用 16 核、每算例 2 核 ⇒ 最多 8 个作业并行**；
> "This calculation only took **a couple of minutes** to complete on our local workstation."

**（d）`cutoff_analyse.sh`（T12 P6–P7 完整照抄）**：
```bash
#!/bin/bash
cutoffs="50 100 150 200 250 300 350 400 450 500"
input_file=Si_bulk8.inp
output_file=Si_bulk8.out
plot_file=cutoff_data.ssv
rel_cutoff=60
echo "# Grid cutoff vs total energy" > $plot_file
echo "# Date: $(date)" >> $plot_file
echo "# PWD: $PWD" >> $plot_file
echo "# REL_CUTOFF = $rel_cutoff" >> $plot_file
echo -n "# Cutoff (Ry) | Total Energy (Ha)" >> $plot_file
grid_header=true
for ii in $cutoffs ; do
  work_dir=cutoff_${ii}Ry
  total_energy=$(grep -e '^[ \t]*Total energy' $work_dir/$output_file | awk '{print $3}')
  ngrids=$(grep -e '^[ \t]*QS| Number of grid levels:' $work_dir/$output_file | \
           awk '{print $6}')
  if $grid_header ; then
    for ((igrid=1; igrid <= ngrids; igrid++)) ; do
      printf " | NG on grid %d" $igrid >> $plot_file
    done
    printf "\n" >> $plot_file
    grid_header=false
  fi
  printf "%10.2f %15.10f" $ii $total_energy >> $plot_file
  for ((igrid=1; igrid <= ngrids; igrid++)) ; do
    grid=$(grep -e '^[ \t]*count for grid' $work_dir/$output_file | \
          awk -v igrid=$igrid '(NR == igrid){print $5}')
    printf " %6d" $grid >> $plot_file
  done
  printf "\n" >> $plot_file
done
```
```bash
chmod u+x ./cutoff_analyse.sh
./cutoff_analyse.sh
```

**（e）`rel_cutoff_inputs.sh`（T12 P8 完整照抄）**：
```bash
#!/bin/bash
rel_cutoffs="10 20 30 40 50 60 70 80 90 100"
basis_file=BASIS_SET
potential_file=GTH_POTENTIALS
template_file=template.inp
input_file=Si_bulk8.inp
cutoff=250
for ii in $rel_cutoffs ; do
  work_dir=rel_cutoff_${ii}Ry
  if [ ! -d $work_dir ] ; then
    mkdir $work_dir
  else
    rm -r $work_dir/*
  fi
  sed -e "s/LT_cutoff/${cutoff}/g" \
      -e "s/LT_rel_cutoff/${ii}/g" \
      $template_file > $work_dir/$input_file
  cp $basis_file $work_dir
  cp $potential_file $work_dir
done
```

**（f）`rel_cutoff_run.sh`（T12 P8–P9 完整照抄）**：
```bash
#!/bin/bash
rel_cutoffs="10 20 30 40 50 60 70 80 90 100"
cp2k_bin=cp2k.popt
input_file=Si_bulk8.inp
output_file=Si_bulk8.out
no_proc_per_calc=2
no_proc_to_use=16
counter=1
max_parallel_calcs=$(expr $no_proc_to_use / $no_proc_per_calc)
for ii in $rel_cutoffs ; do
  work_dir=rel_cutoff_${ii}Ry
  cd $work_dir
  if [ -f $output_file ] ; then
    rm $output_file
  fi
  mpirun -np $no_proc_per_calc $cp2k_bin -o $output_file $input_file &
  cd ..
  mod_test=$(echo "$counter % $max_parallel_calcs" | bc)
  if [ $mod_test -eq 0 ] ; then
    wait
  fi
  counter=$(expr $counter + 1)
done
wait
```
```bash
./rel_cutoff_run.sh &
```

**（g）`rel_cutoff_analyse.sh`（T12 P9 完整照抄）**：
```bash
#!/bin/bash
rel_cutoffs="10 20 30 40 50 60 70 80 90 100"
input_file=Si_bulk8.inp
output_file=Si_bulk8.out
plot_file=rel_cutoff_data.ssv
cutoff=250
echo "# Rel Grid cutoff vs total energy" > $plot_file
echo "# Date: $(date)" >> $plot_file
echo "# PWD: $PWD" >> $plot_file
echo "# CUTOFF = ${cutoff}" >> $plot_file
echo -n "# Rel Cutoff (Ry) | Total Energy (Ha)" >> $plot_file
grid_header=true
for ii in $rel_cutoffs ; do
  work_dir=rel_cutoff_${ii}Ry
  total_energy=$(grep -e '^[ \t]*Total energy' $work_dir/$output_file | awk '{print $3}')
  ngrids=$(grep -e '^[ \t]*QS| Number of grid levels:' $work_dir/$output_file | \
           awk '{print $6}')
  if $grid_header ; then
    for ((igrid=1; igrid <= ngrids; igrid++)) ; do
      printf " | NG on grid %d" $igrid >> $plot_file
    done
    printf "\n" >> $plot_file
    grid_header=false
  fi
  printf "%10.2f %15.10f" $ii $total_energy >> $plot_file
  for ((igrid=1; igrid <= ngrids; igrid++)) ; do
    grid=$(grep -e '^[ \t]*count for grid' $work_dir/$output_file | \
          awk -v igrid=$igrid '(NR == igrid){print $5}')
    printf " %6d" $grid >> $plot_file
  done
  printf "\n" >> $plot_file
done
```
```bash
./rel_cutoff_analyse.sh
```

### 4.4 T12：两张结果数据表（**全文照抄，G 层只给了汇总结论**）

**`cutoff_data.ssv`（T12 P7，`REL_CUTOFF = 60`）**：
```
# Grid cutoff vs total energy
# Date: Mon Jan 20 21:20:34 GMT 2014
# PWD: /home/tong/tutorials/converging_grid/sample_output
# REL_CUTOFF = 60
# Cutoff (Ry) | Total Energy (Ha) | NG on grid 1 | NG on grid 2 | NG on grid 3 | NG on grid 4
   50.00  -32.3795329864   5048   5432     16      0
  100.00  -32.3804557631   2720   5000   2760     16
  150.00  -32.3804554850   2032   3016   5432     16
  200.00  -32.3804554982   1880   2472   3384   2760
  250.00  -32.3804554859    264   4088   3384   2760
  300.00  -32.3804554843    264   2456   5000   2776
  350.00  -32.3804554846     56   1976   5688   2776
  400.00  -32.3804554851     56   1976   3016   5448
  450.00  -32.3804554851      0   2032   3016   5448
  500.00  -32.3804554850      0   2032   3016   5448
```
> **怎么读这张表（H 层提炼，原文只给了结论）**：① **100 Ry → 150 Ry 还差 2.78e-7 Ha**，
> 但**从 150 Ry 起、150–500 Ry 之间的总能极差只有 1.39e-8 Ha**（最小 −32.3804554982 @200 Ry，
> 最大 −32.3804554843 @300 Ry）——**已经进入 1e-8 量级，但还没"锁死"**；
> ② **`NG on grid 1`（最细层的高斯数）随 cutoff 增大单调下降**：
> 50 Ry 时 `grid 4 = 0`（最粗层没用上 ⇒ 全部挤在细层），450 Ry 起 `grid 1 = 0`（**最细层完全没用上 ⇒ 白花钱**）；
> ③ **250 Ry 是"最细层第一次被用上（264 个）"且"仍有 2760 个在 grid 4"的转折点** —— 原文选点理由即此。

**`rel_cutoff_data.ssv`（T12 P10，`CUTOFF = 250`）**：
```
# Rel Grid cutoff vs total energy
# Date: Mon Jan 20 00:45:14 GMT 2014
# PWD: /home/tong/tutorials/converging_grid/sample_output
# CUTOFF = 250
# Rel Cutoff (Ry) | Total Energy (Ha) | NG on grid 1 | NG on grid 2 | NG on grid 3 | NG on grid 4
   10.00  -32.3902980020      0      0   2032   8464
   20.00  -32.3816384686      0    264   4088   6144
   30.00  -32.3805115576      0   2032   3016   5448
   40.00  -32.3805116025     56   1976   3016   5448
   50.00  -32.3804555002    264   2456   5000   2776
   60.00  -32.3804554859    264   4088   3384   2760
   70.00  -32.3804554859   1880   2472   3384   2760
   80.00  -32.3804554859   1880   2472   3384   2760
   90.00  -32.3804554848   2032   3016   5432     16
  100.00  -32.3804554848   2032   3016   5432     16
```
> **怎么读**：① `REL_CUTOFF` 从 10 → 60，**大量高斯从 grid 4 迁移到 grid 1**
> （grid 4：8464 → 2760；grid 1：0 → 264），同时**总会能从 −32.3902980020 一路收敛到 −32.3804554859**
> （**10 → 60 Ry 一共降了 9.8e-3 Ha，是全部变化的主体**）；
> ② **60 / 70 / 80 三个值的 10 位小数完全相同**（都是 −32.3804554859）；
> 90 / 100 也只差 **1.1e-9 Ha**。**结论：60 Ry 已经足够，再往上加只多花钱。**

**抽样输出片段（T12 P6，`cutoff_100Ry/Si_bulk8.out` 照抄）**：
```
SCF WAVEFUNCTION OPTIMIZATION
 Step Update method Time Convergence Total energy Change
------------------------------------------------------------------------------
Trace(PS): 32.0000000000
Electronic density on regular grids: -31.9999999980 0.0000000020
Core density on regular grids: 31.9999999944 -0.0000000056
Total charge density on r-space grids: -0.0000000036
Total charge density g-space grids: -0.0000000036
      1 NoMix/Diag. 0.40E+00 0.4 1.10090760 -32.3804557631 -3.24E+01
*** SCF run NOT converged ***
Electronic density on regular grids: -31.9999999980 0.0000000020
Core density on regular grids: 31.9999999944 -0.0000000056
Total charge density on r-space grids: -0.0000000036
Total charge density g-space grids: -0.0000000036
Overlap energy of the core charge distribution: 0.00000000005320
Self energy of the core charge distribution: -82.06393942512820
Core Hamiltonian energy: 16.92855916540793
Hartree energy: 42.17635056223367
Exchange-correlation energy: -9.42142606564066
Electronic entropic energy: 0.00000000000000
Fermi energy: 0.00000000000000
Total energy: -32.38045576307407
```
> T12 P6 原文提醒：正则 **`^[ \t]*Total energy:`** 就能抓到相关行。
> 注意 `Electronic entropic energy: 0.00000000000000` 与 `Fermi energy: 0.00000000000000`——
> **`MAX_SCF 1` 下没有真正做自洽，所以熵项与费米能都是 0**。

**抽样输出片段（T12 P6，`MULTIGRID INFO` 照抄；对应 `CUTOFF 100` / `REL_CUTOFF 60`）**：
```
-------------------------------------------------------------------------------
---- MULTIGRID INFO ----
-------------------------------------------------------------------------------
count for grid 1:        2720          cutoff [a.u.]         50.00
count for grid 2:        5000          cutoff [a.u.]         16.67
count for grid 3:        2760          cutoff [a.u.]          5.56
count for grid 4:          16          cutoff [a.u.]          1.85
total gridlevel count : 10496
```
> **单位换算（T12 P6 原文）**：`[a.u.]` 是 Hartree 能量单位，**1 Ha = 2 Ry**。
> ⇒ grid 1 的 50.00 Ha = 100 Ry = `CUTOFF`；grid 2 的 16.67 Ha ≈ 100/3 Ry（`PROGRESSION_FACTOR 3.0`）。

### 4.5 T11：完整输入（照抄，G 层未收录本教程输入）

```fortran
&GLOBAL
  PROJECT H2O
  RUN_TYPE GEO_OPT
  PRINT_LEVEL LOW
&END GLOBAL
&FORCE_EVAL
  METHOD QS
  &SUBSYS
    &CELL
      ABC 12.4138 12.4138 12.4138
    &END CELL
    &COORD
      O 12.235322  1.376642 10.869880
      H 12.415139  2.233125 11.257611
      H 11.922476  1.573799  9.986994
    &END COORD
    &KIND H
      BASIS_SET DZVP-GTH-PADE
      POTENTIAL GTH-PADE-q1
    &END KIND
    &KIND O
      BASIS_SET DZVP-GTH-PADE
      POTENTIAL GTH-PADE-q6
    &END KIND
  &END SUBSYS
  &DFT
    BASIS_SET_FILE_NAME ./BASIS_SET
    POTENTIAL_FILE_NAME ./POTENTIAL
    &QS
      EPS_DEFAULT 1.0E-7
    &END QS
    &MGRID
      CUTOFF 200
      NGRIDS 4
      REL_CUTOFF 30
    &END MGRID
    &SCF
      SCF_GUESS ATOMIC
      EPS_SCF 1.0E-05
      MAX_SCF 200
      &DIAGONALIZATION T
        ALGORITHM STANDARD
      &END DIAGONALIZATION
      &MIXING T
        ALPHA 0.5
        METHOD PULAY_MIXING
        NPULAY 5
      &END MIXING
      &PRINT
        &RESTART OFF
        &END RESTART
      &END PRINT
    &END SCF
    &XC
      &XC_FUNCTIONAL PADE
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
&END FORCE_EVAL
&MOTION
  &GEO_OPT
    TYPE MINIMIZATION
    MAX_DR    1.0E-03
    MAX_FORCE 1.0E-03
    RMS_DR    1.0E-03
    RMS_FORCE 1.0E-03
    MAX_ITER 200
    OPTIMIZER CG
    &CG
      MAX_STEEP_STEPS 0
      RESTART_LIMIT 9.0E-01
    &END CG
  &END GEO_OPT
  &CONSTRAINT
    &FIXED_ATOMS
      COMPONENTS_TO_FIX XYZ
      LIST 1
    &END FIXED_ATOMS
  &END CONSTRAINT
&END MOTION
```

**运行（T11 P3 / P4，照抄）**：
```bash
cp2k.sopt -o H2O.out H2O.inp &
# 作业挂掉后续算：
cp2k.sopt -o H2O.out H2O-1.restart &
```

**产物清单（T11 P4 照抄）**：
```
H2O.out
H2O-pos-1.xyz
H2O-1.restart
H2O-1.restart.bak-1
H2O-1.restart.bak-2
H2O-1.restart.bak-3
```

**输出：step = 1（T11 P4 照抄）**：
```
-------- Informations at step =  1 ------------
Optimization Method      =      SD
Total Energy             =     -17.1643447508
Real energy change       =      -0.0006776683
Decrease in energy       =                  YES
Used time                =              90.837
Convergence check :
Max. step size           =       0.0336570168
Conv. limit for step size  =       0.0010000000
Convergence in step size =                   NO
RMS step size            =       0.0168136889
Conv. limit for RMS step =       0.0010000000
Convergence in RMS step  =                   NO
Max. gradient             =       0.0182785685
Conv. limit for gradients =       0.0010000000
Conv. for gradients      =                   NO
RMS gradient              =       0.0091312361
Conv. limit for RMS grad. =       0.0010000000
Conv. for gradients      =                   NO
---------------------------------------------------
```

**输出：step = 11 与收尾（T11 P5 照抄）**：
```
-------- Informations at step = 11 ------------
Optimization Method      =      SD
Total Energy             =     -17.1646204766
Real energy change       =      -0.0000000529
Decrease in energy       =                  YES
Used time                =              49.893
Convergence check :
Max. step size           =       0.0003393150
Conv. limit for step size  =       0.0010000000
Convergence in step size =                  YES
RMS step size            =       0.0001493298
Conv. limit for RMS step =       0.0010000000
Convergence in RMS step  =                  YES
Max. gradient             =       0.0001787448
Conv. limit for gradients =       0.0010000000
Conv. in gradients       =                  YES
RMS gradient              =       0.0000786642
Conv. limit for RMS grad. =       0.0010000000
Conv. in RMS gradients   =                  YES
---------------------------------------------------
*******************************************************************************
***                        GEOMETRY OPTIMIZATION COMPLETED                    ***
*******************************************************************************
Reevaluating energy at the minimum
Number of electrons: 8
Number of occupied orbitals: 4
Number of molecular orbitals: 4
Number of orbital functions: 23
Number of independent orbital functions: 23
Parameters for the always stable predictor-corrector (ASPC) method:
 ASPC order: 3
 B(1) =   3.000000
 B(2) =  -3.428571
 B(3) =   1.928571
 B(4) =  -0.571429
 B(5) =   0.071429
Extrapolation method: ASPC
SCF WAVEFUNCTION OPTIMIZATION
 Step Update method Time Convergence Total energy Change
------------------------------------------------------------------------------
    1 Pulay/Diag. 0.50E+00  0.5  0.00005615  -17.1646204762  -1.72E+01
    2 Pulay/Diag. 0.50E+00  1.0  0.00000563  -17.1646347711  -1.43E-05
*** SCF run converged in 2 steps ***
Electronic density on regular grids:  -8.0000016293  -0.0000016293
Core density on regular grids:        7.9999992554  -0.0000007446
Total charge density on r-space grids:  -0.0000023739
Total charge density g-space grids:     -0.0000023739
Overlap energy of the core charge distribution:     0.00000004555422
Self energy of the core charge distribution:      -43.83289054591484
Core Hamiltonian energy:              12.82175605770555
Hartree energy:                       17.97395116120845
Exchange-correlation energy:          -4.12745148966141
Total energy:                        -17.16463477110803
ENERGY| Total FORCE_EVAL ( QS ) energy (a.u.):        -17.164634771108034
```

### 4.6 T10：输出表（G 层只给了要点，**此处补全数字**）

**SCF 表（T10 P7 照抄，无 smearing）**：
```
Number of electrons: 32
Number of occupied orbitals: 16
Number of molecular orbitals: 16
Number of orbital functions: 104
Number of independent orbital functions: 104
Extrapolation method: initial_guess
SCF WAVEFUNCTION OPTIMIZATION
 Step Update method Time Convergence Total energy Change
------------------------------------------------------------------------------
    1 NoMix/Diag. 0.40E+00  0.6  0.75558724  -32.2320848878  -3.22E+01
    2 Broy./Diag. 0.40E+00  1.1  0.05667976  -31.1418135481   1.09E+00
    3 Broy./Diag. 0.40E+00  1.1  0.09691469  -31.1974003416  -5.56E-02
    4 Broy./Diag. 0.40E+00  1.1  0.00245608  -31.3378474040  -1.40E-01
    5 Broy./Diag. 0.40E+00  1.1  0.00235460  -31.3009654398   3.69E-02
    6 Broy./Diag. 0.40E+00  1.1  0.00007565  -31.2972158934   3.75E-03
    7 Broy./Diag. 0.40E+00  1.1  0.00009004  -31.2977293749  -5.13E-04
    8 Broy./Diag. 0.40E+00  1.1  0.00000186  -31.2978454163  -1.16E-04
    9 Broy./Diag. 0.40E+00  1.1  0.00000252  -31.2978835492  -3.81E-05
   10 Broy./Diag. 0.40E+00  1.1  5.6405E-09  -31.2978852054  -1.66E-06
*** SCF run converged in 10 steps ***
```

**能量分解 + 力（T10 P7 照抄，无 smearing）**：
```
Electronic density on regular grids:  -31.9999999889   0.0000000111
Core density on regular grids:         31.9999999939  -0.0000000061
Total charge density on r-space grids:   0.0000000051
Total charge density g-space grids:      0.0000000051
Overlap energy of the core charge distribution:     0.00000000005320
Self energy of the core charge distribution:      -82.06393942512820
Core Hamiltonian energy:              18.06858429706010
Hartree energy:                       42.41172824581682
Exchange-correlation energy:          -9.71425832315952
Total energy:                        -31.29788520535761
ENERGY| Total FORCE_EVAL ( QS ) energy (a.u.):        -31.297885372811002
ATOMIC FORCES in [a.u.]
 # Atom   Kind   Element          X              Y              Z
     1      1      Si            0.00000000     0.00000000     0.00000000
     2      1      Si            0.00000000     0.00000001     0.00000001
     3      1      Si            0.00000001     0.00000001     0.00000000
     4      1      Si            0.00000001     0.00000000     0.00000001
     5      1      Si           -0.00000001    -0.00000001    -0.00000001
     6      1      Si           -0.00000001    -0.00000001    -0.00000001
     7      1      Si           -0.00000001    -0.00000001    -0.00000001
     8      1      Si           -0.00000001    -0.00000001    -0.00000001
SUM OF ATOMIC FORCES          -0.00000000    -0.00000000    -0.00000000       0.00000000
```
> T10 P7 的检查要点：**"One should always check if the total number of electrons calculated from
> the final electron density, in this case 31.9999999939, is correct."**（本例应等于 32）
> 以及：**力几乎为零 ⇒ 体系基本弛豫，几何接近基态最优结构**。

**加 smearing 后的对照（T10 P8 照抄）**：
```
Number of electrons: 32
Number of occupied orbitals: 16
Number of molecular orbitals: 26
Number of orbital functions: 104
Number of independent orbital functions: 104
```
```
Core Hamiltonian energy:              18.06842027191411
Hartree energy:                       42.41184371469986
Exchange-correlation energy:          -9.71419454555998
Electronic entropic energy:           -0.00001687947145
Fermi energy:                          0.20867150262130
Total energy:                        -31.29788686349247
ENERGY| Total FORCE_EVAL ( QS ) energy (a.u.):        -31.297887031736590
```
> T10 P8 的关键读法：**分子轨道数 16 → 26（= 16 占据 + `ADDED_MOS 10`）**；
> **`Electronic entropic energy` 必须很小**；**最终要引用的是 TS→0 外推的自由能**
> （即 `ENERGY|` 那一行 `-31.297887031736590`），而不是 `Total energy`。
> 对照无 smearing 的 `-31.297885372811002`，两者差 ~1.7e-6 Ha —— **这正是 smearing 引入的熵贡献量级**。

**添加 smearing 的输入片段（T10 P7–P8 照抄）**：
```
&SMEAR ON
  METHOD FERMI_DIRAC
  ELECTRONIC_TEMPERATURE [K] 300
&END SMEAR
```
```
ADDED_MOS 10
```

### 4.7 T13：`.ener` 文件与 gnuplot（照抄）

**`WATER-1.ener` 列头与前 6 行（T13 P3 照抄）**：
```
#     Step Nr.          Time[fs]        Kin.[a.u.]          Temp[K]            Pot.[a.u.]        Cons Qty[a.u.]         UsedTime[s]
         0            0.000000         0.273612846       300.000000000     -1102.629448594     -1102.355835748          0.000000000
         1            0.500000         0.279633819       306.601634956     -1102.634728486     -1102.356032711         70.082937483
         2            1.000000         0.278176228       305.003473822     -1102.643688340     -1102.356285321         11.608515253
         3            1.500000         0.280393422       307.434493169     -1102.653080703     -1102.356547289         11.607597935
         4            2.000000         0.282889483       310.171274373     -1102.655862600     -1102.356593452         11.617385623
         5            2.500000         0.294372846       322.762089451     -1102.653391721     -1102.356505399         11.665471402
```

**gnuplot 命令（T13 P3 照抄）**：
```
gnuplot> plot './WATER-1.ener' u 2:6 w lp
gnuplot> plot './WATER-1.ener' u 2:5 w lp
gnuplot> replot './WATER-1.ener' u 2:6 w lp
```
> 即：**横轴第 2 列 = 时间 [fs]**；**第 5 列 = 势能 [a.u.]**；**第 6 列 = 守恒量 [a.u.]**。

**守恒量守不住时的三条处方（T13 P3 照抄原文）**：
```
Make EPS_SCF tighter (to reduce drift)
Make TIMESTEP shorter (to reduce fluctuations)
Play with EXTRAPOLATION_ORDER (to reduce drift and or instabilities)
```

**IR 谱用的电荷文件 `charges.dat`（T13 P3 照抄）**：
```
O -1.2
H +0.6
```

**VMD 操作路径（T13 P3 照抄）**：
```
Extensions/Analysis/Radial Pair Distribution Function g(r)  →  Utilities/Set unit cell size dimensions
Extensions/Analysis/Spectral density calculator             →  Utilities/Load name↔charge map from file
```
VMD 启动：`vmd WATER-pos-1.xyz`；IR 设置：**timestep 0.5 fs、最大频率 6000 cm^-1**。

**续算段（T13 P2 照抄）**：
```
&EXT_RESTART
  RESTART_FILE_NAME WATER-1.restart
&END
```

**"压 IO / 开重启"的输入片段（T13 P1–P2 照抄）**：
```
&GLOBAL
  ! limit the runs to 5min
  WALLTIME 300
  ! reduce the amount of IO
  IOLEVEL LOW
&END GLOBAL
```
```
&SCF
  ! do not store the wfn during MD
  &PRINT
    &RESTART OFF
    &END
  &END
&END SCF
```
```
&PRINT
  ! at the end of the SCF procedure generate cube files of the density
  &E_DENSITY_CUBE OFF
  &END E_DENSITY_CUBE
  ! compute eigenvalues and homo-lumo gap each 10nd MD step
  &MO_CUBES
    ! compute 4 unoccupied orbital energies
    NLUMO 4
    NHOMO 4
    ! but don't write the cube files
    WRITE_CUBE .FALSE.
    ! do this every 10th MD step.
    &EACH
      MD 10
    &END
  &END
&END
```
```
&MOTION
  &PRINT
    &TRAJECTORY
      &EACH
        MD 1
      &END EACH
    &END TRAJECTORY
    &VELOCITIES OFF
    &END VELOCITIES
    &FORCES OFF
    &END FORCES
    &RESTART_HISTORY
      &EACH
        MD 500
      &END EACH
    &END RESTART_HISTORY
    &RESTART
      BACKUP_COPIES 3
      &EACH
        MD 1
      &END EACH
    &END RESTART
  &END PRINT
&END MOTION
```

**`water.xyz` 头部（T13 P4 照抄）**：
```
192
water with unit cell: ABC [angstrom] 12.42 12.42 12.42
O  3.8585873763 -4.7533175213  5.5091974759
H  4.2109950951 -5.5568705259  5.9994585948
H  3.0947084560 -4.3172663108  5.9135950646
...（共 192 个原子，坐标见 T13 P4–P6）
```
> **注意第二行的注释内容**——**xyz 文件的注释行里塞了单胞信息**，而 CP2K 侧是靠
> `&CELL ABC [angstrom] 12.42 12.42 12.42` 提供的（T13 P1）。**两者要保持一致。**

### 4.8 T13：`water_cheating.inp` 全文（答案文件，照抄）

```fortran
&GLOBAL
  ! the project name is made part of most output files... useful to keep order
  PROJECT WATER
  ! various runtypes (energy, geo_opt, etc.) available.
  RUN_TYPE MD
  ! limit the runs to 5min
  WALLTIME 1800
  ! reduce the amount of IO
  IOLEVEL LOW
&END GLOBAL
&FORCE_EVAL
  ! the electronic structure part of CP2K is named Quickstep
  METHOD Quickstep
  &DFT
    ! basis sets and pseudopotential files can be found in cp2k/data
    BASIS_SET_FILE_NAME HFX_BASIS
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    ! Charge and multiplicity
    CHARGE 0
    MULTIPLICITY 1
    &MGRID
      ! PW cutoff ... depends on the element (basis) too small cutoffs lead to the eggbox effect.
      ! certain calculations (e.g. geometry optimization, vibrational frequencies,
      ! NPT and cell optimizations, need higher cutoffs)
      CUTOFF [Ry] 400
    &END
    &QS
      ! use the GPW method (i.e. pseudopotential based calculations with the Gaussian and Plane Waves scheme).
      METHOD GPW
      ! default threshold for numerics ~ roughly numerical accuracy of the total energy per electron,
      ! sets reasonable values for all other thresholds.
      EPS_DEFAULT 1.0E-10
      ! used for MD, the method used to generate the initial guess.
      EXTRAPOLATION ASPC
    &END
    &POISSON
      PERIODIC XYZ ! the default, gas phase systems should have 'NONE' and a wavelet solver
    &END
    &PRINT
      ! at the end of the SCF procedure generate cube files of the density
      &E_DENSITY_CUBE OFF
      &END E_DENSITY_CUBE
      ! compute eigenvalues and homo-lumo gap each 10nd MD step
      &MO_CUBES
        NLUMO 4
        NHOMO 4
        WRITE_CUBE .FALSE.
        &EACH
          MD 10
        &END
      &END
    &END
    ! use the OT METHOD for robust and efficient SCF, suitable for all non-metallic systems.
    &SCF
      SCF_GUESS ATOMIC ! can be used to RESTART an interrupted calculation
      MAX_SCF 30
      EPS_SCF 1.0E-6 ! accuracy of the SCF procedure typically 1.0E-6 - 1.0E-7
      &OT
        ! an accurate preconditioner suitable also for larger systems
        PRECONDITIONER FULL_SINGLE_INVERSE
        ! the most robust choice (DIIS might sometimes be faster, but not as stable).
        MINIMIZER DIIS
      &END OT
      &OUTER_SCF ! repeat the inner SCF cycle 10 times
        MAX_SCF 10
        EPS_SCF 1.0E-6 ! must match the above
      &END
      ! do not store the wfn during MD
      &PRINT
        &RESTART OFF
        &END
      &END
    &END SCF
    ! specify the exchange and correlation treatment
    &XC
      ! use a PBE functional
      &XC_FUNCTIONAL
        &PBE
        &END
      &END XC_FUNCTIONAL
      ! adding Grimme's D3 correction (by default without C9 terms)
      &VDW_POTENTIAL
        POTENTIAL_TYPE PAIR_POTENTIAL
        &PAIR_POTENTIAL
          PARAMETER_FILE_NAME dftd3.dat
          TYPE DFTD3
          REFERENCE_FUNCTIONAL PBE
          R_CUTOFF [angstrom] 16
        &END
      &END VDW_POTENTIAL
    &END XC
  &END DFT
  ! description of the system
  &SUBSYS
    &CELL
      ! unit cells that are orthorhombic are more efficient with CP2K
      ABC [angstrom] 12.42 12.42 12.42
    &END CELL
    ! atom coordinates can be in the &COORD section,
    ! or provided as an external file.
    &TOPOLOGY
      COORD_FILE_NAME water.xyz
      COORD_FILE_FORMAT XYZ
    &END
    ! MOLOPT basis sets are fairly costly,
    ! but in the 'DZVP-MOLOPT-SR-GTH' available for all elements
    ! their contracted nature makes them suitable
    ! for condensed and gas phase systems alike.
    &KIND H
      BASIS_SET DZVP-GTH
      POTENTIAL GTH-PBE-q1
    &END KIND
    &KIND O
      BASIS_SET DZVP-GTH
      POTENTIAL GTH-PBE-q6
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
! how to propagate the system, selection via RUN_TYPE in the &GLOBAL section
&MOTION
  &GEO_OPT
    OPTIMIZER BFGS ! Good choice for 'small' systems (use LBFGS for large systems)
    MAX_ITER 100
    MAX_DR [bohr] 0.003 ! adjust target as needed
    &BFGS
    &END
  &END
  &MD
    ENSEMBLE NVT ! sampling the canonical ensemble, accurate properties might need NVE
    TEMPERATURE [K] 300
    TIMESTEP [fs] 0.5
    STEPS 1000
    # GLE thermostat as generated at http://epfl-cosmo.github.io/gle4md
    # GLE provides an effective NVT sampling.
    &THERMOSTAT
      REGION MASSIVE
      TYPE GLE
      &GLE
        NDIM 5
        A_SCALE [ps^-1] 1.00
        A_LIST  1.859575861256e+2   2.726385349840e-1   1.152610045461e+1  -3.641457826260e+1   2.317337581602e+2
        A_LIST -2.780952471206e-1   8.595159180871e-5   7.218904801765e-1  -1.984453934386e-1   4.240925758342e-1
        A_LIST -1.482580813121e+1  -7.218904801765e-1   1.359090212128e+0   5.149889628035e+0  -9.994926845099e+0
        A_LIST -1.037218912688e+1   1.984453934386e-1  -5.149889628035e+0   2.666191089117e+1   1.150771549531e+1
        A_LIST  2.180134636042e+2  -4.240925758342e-1   9.994926845099e+0  -1.150771549531e+1   3.095839456559e+2
      &END GLE
    &END THERMOSTAT
  &END
  &PRINT
    &TRAJECTORY
      &EACH
        MD 1
      &END EACH
    &END TRAJECTORY
    &VELOCITIES OFF
    &END VELOCITIES
    &FORCES OFF
    &END FORCES
    &RESTART_HISTORY
      &EACH
        MD 500
      &END EACH
    &END RESTART_HISTORY
    &RESTART
      BACKUP_COPIES 3
      &EACH
        MD 1
      &END EACH
    &END RESTART
  &END PRINT
&END
&EXT_RESTART
  RESTART_FILE_NAME WATER-1.restart
&END
```
> **注**：`&MOTION` 里同时保留了 `&GEO_OPT` 与 `&MD`——但 `RUN_TYPE MD`，所以实际生效的是 `&MD`；
> **答案文件把两段都留着是为了让学员接着改 `RUN_TYPE` 做别的任务**。
> 另外 `WALLTIME 1800` 与正文要求的 `WALLTIME 300`（T13 P1）不一致，**答案文件放宽了**。

### 4.9 T14：作业脚本与 cubecruncher 命令（照抄）

**PBS 作业脚本（T14 P1–P2 照抄）**：
```bash
#PBS -N mode1
#PBS -l select=2
#PBS -l walltime=0:20:0
#PBS -A y14
#PBS -j oe
cd $PBS_O_WORKDIR
module load cp2k
aprun -n 48 cp2k.popt -i mode1.inp -o mode1.out
```

**编译 `cubecruncher`（T14 P2 照抄）**：
```bash
~$ module load cp2k
~$ cp -r $CP2K/../../tools/cubecruncher .
~$ cd cubecruncher
~$ module swap PrgEnv-cray PrgEnv-gnu
~$ make
```

**算密度差的两条命令（T14 P3 照抄）**：
```bash
~$ cubecruncher.x -i MODE1-ELECTRON_DENSITY-1_0.cube -subtract MODE1_dye-ELECTRON_DENSITY-1_0.cube -o tmp.cube
~$ cubecruncher.x -i tmp.cube -subtract MODE1_slab-ELECTRON_DENSITY-1_0.cube -center geo -o MODE1_delta.cube
```
> **命名规律**：cube 文件名是 **`<PROJECT大写>-ELECTRON_DENSITY-1_0.cube`**——
> 由 `PROJECT` 名 + 固定的后缀组成。所以做三次计算时**必须改 `PROJECT`**，
> 否则三份 cube 会同名互相覆盖（这也解释了 T14 P2 为什么强调"**改 `COORD_FILE_NAME` 和 `PROJECT` 两处**"）。

**直接运行（T14 P2 / P3 照抄）**：
```bash
cp2k.popt -i mode1.inp -o mode1.out
```

### 4.10 T14：`mode1.inp` 全文（照抄）

```fortran
&GLOBAL
  ! the project name is made part of most output files... useful to keep order
  PROJECT MODE1
  ! various runtypes (energy, geo_opt, etc.) available.
  RUN_TYPE ENERGY
&END GLOBAL
&FORCE_EVAL
  ! the electronic structure part of CP2K is named Quickstep
  METHOD Quickstep
  &DFT
    ! basis sets and pseudopotential files can be found in cp2k/data
    BASIS_SET_FILE_NAME BASIS_MOLOPT
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    ! Charge and multiplicity
    CHARGE 0
    MULTIPLICITY 1
    &MGRID
      ! PW cutoff ... depends on the element (basis) too small cutoffs lead to the eggbox effect.
      ! certain calculations (e.g. geometry optimization, vibrational frequencies,
      ! NPT and cell optimizations, need higher cutoffs)
      CUTOFF [Ry] 400
    &END
    &QS
      ! use the GPW method (i.e. pseudopotential based calculations with the Gaussian and Plane Waves scheme).
      METHOD GPW
      ! default threshold for numerics ~ roughly numerical accuracy of the total energy per electron,
      ! sets reasonable values for all other thresholds.
      EPS_DEFAULT 1.0E-10
      ! used for MD, the method used to generate the initial guess.
      EXTRAPOLATION ASPC
    &END
    &POISSON
      PERIODIC XYZ ! the default, gas phase systems should have 'NONE' and a wavelet solver
    &END
    &PRINT
      ! at the end of the SCF procedure generate cube files of the density
      &E_DENSITY_CUBE ON
      &END E_DENSITY_CUBE
    &END
    ! use the OT METHOD for robust and efficient SCF, suitable for all non-metallic systems.
    &SCF
      SCF_GUESS ATOMIC ! can be used to RESTART an interrupted calculation
      MAX_SCF 30
      EPS_SCF 1.0E-6 ! accuracy of the SCF procedure typically 1.0E-6 - 1.0E-7
      &OT
        ! an accurate preconditioner suitable also for larger systems
        PRECONDITIONER FULL_SINGLE_INVERSE
        ! the most robust choice (DIIS might sometimes be faster, but not as stable).
        MINIMIZER CG
      &END OT
      &OUTER_SCF ! repeat the inner SCF cycle 10 times
        MAX_SCF 10
        EPS_SCF 1.0E-6 ! must match the above
      &END
    &END SCF
    ! specify the exchange and correlation treatment
    &XC
      ! use a PBE functional
      &XC_FUNCTIONAL
        &PBE
        &END
      &END XC_FUNCTIONAL
      ! adding Grimme's D3 correction (by default without C9 terms)
      &VDW_POTENTIAL
        POTENTIAL_TYPE PAIR_POTENTIAL
        &PAIR_POTENTIAL
          PARAMETER_FILE_NAME dftd3.dat
          TYPE DFTD3
          REFERENCE_FUNCTIONAL PBE
          R_CUTOFF [angstrom] 16
        &END
      &END VDW_POTENTIAL
    &END XC
  &END DFT
  ! description of the system
  &SUBSYS
    &CELL
      ! unit cells that are orthorhombic are more efficient with CP2K
      ABC [angstrom] 10.2270 11.3460 20.000
    &END CELL
    ! atom coordinates can be in the &COORD section,
    ! or provided as an external file.
    &TOPOLOGY
      COORD_FILE_NAME mode1.xyz
      COORD_FILE_FORMAT XYZ
    &END
    ! MOLOPT basis sets are fairly costly,
    ! but in the 'DZVP-MOLOPT-SR-GTH' available for all elements
    ! their contracted nature makes them suitable
    ! for condensed and gas phase systems alike.
    &KIND H
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q1
    &END KIND
    &KIND C
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q4
    &END KIND
    &KIND O
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q6
    &END KIND
    &KIND Ti
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q12
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
! how to propagate the system, selection via RUN_TYPE in the &GLOBAL section
&MOTION
  &GEO_OPT
    OPTIMIZER BFGS ! Good choice for 'small' systems (use LBFGS for large systems)
    MAX_ITER 100
    MAX_DR [bohr] 0.003 ! adjust target as needed
    &BFGS
    &END
  &END
  &MD
    ENSEMBLE NVT ! sampling the canonical ensemble, accurate properties might need NVE
    TEMPERATURE [K] 300
    TIMESTEP [fs] 0.5
    STEPS 1000
    # GLE thermostat as generated at http://epfl-cosmo.github.io/gle4md
    # GLE provides an effective NVT sampling.
    &THERMOSTAT
      REGION MASSIVE
      TYPE GLE
      &GLE
        NDIM 5
        A_SCALE [ps^-1] 1.00
        A_LIST  1.859575861256e+2   2.726385349840e-1   1.152610045461e+1  -3.641457826260e+1   2.317337581602e+2
        A_LIST -2.780952471206e-1   8.595159180871e-5   7.218904801765e-1  -1.984453934386e-1   4.240925758342e-1
        A_LIST -1.482580813121e+1  -7.218904801765e-1   1.359090212128e+0   5.149889628035e+0  -9.994926845099e+0
        A_LIST -1.037218912688e+1   1.984453934386e-1  -5.149889628035e+0   2.666191089117e+1   1.150771549531e+1
        A_LIST  2.180134636042e+2  -4.240925758342e-1   9.994926845099e+0  -1.150771549531e+1   3.095839456559e+2
      &END GLE
    &END THERMOSTAT
  &END
&END
```
> **三个任务共用的同一份输入**（这正是教学设计的巧妙处）：
> - 任务 2（密度差）→ 保持 `RUN_TYPE ENERGY` + `&E_DENSITY_CUBE ON`；
> - 任务 3（相对稳定性）→ 改 `RUN_TYPE GEO_OPT` + `&E_DENSITY_CUBE OFF` + 改 `PROJECT`（T14 P3）；
> - 任务 4（AIMD）→ 改 `RUN_TYPE MD`（T14 P3）。
> **坐标系/原子序数一览（实测，非原文）**：`mode1.xyz` 与 `mode2.xyz` 首行都是 **`116`**，
> 实测都是 **36 Ti + 74 O + 2 C + 4 H = 116**：
> **原子 1–108 = `Ti36O72` slab**，**原子 109–116 = 乙酸 `CH₃COOH`（`H C H H C O O H`）**。
> **两个文件的元素序列逐位相同**（1–108 slab、109–116 乙酸），**所以两份输入可以用同一套原子号切子体系**：
> - `modeN_dye.xyz` ← 删掉原子 1–108；
> - `modeN_slab.xyz` ← 删掉原子 109–116。
>
> **乙酸片段原文（`mode1.xyz` 原子 109–116，照抄）**：
> ```
> H -3.2770955004 -2.4268873548 8.1687296457
> C -3.1978647566 -1.3575831172 7.9359146369
> H -4.2239524320 -0.9733256879 7.8414028480
> H -2.6752907472 -0.8249390527 8.7355765151
> C -2.5132448898 -1.1924834089 6.6141051521
> O -2.8755597850 -1.8460118394 5.6163779603
> O -1.5275649623 -0.3212592281 6.6009413157
> H -1.0670534373 -0.2549619720 5.6840567874
> ```
> **乙酸片段原文（`mode2.xyz` 原子 109–116，照抄）**：
> ```
> H -1.3211320733 -0.5901398003 7.3622691450
> C -2.2774669737 -0.0487846563 7.3616031246
> H -2.9713818519 -0.6195053843 7.9928436643
> H -2.1415146457 0.9598101494 7.7628564958
> C -2.8081585120 -0.0061954447 5.9550273922
> O -3.0662415287 -1.1345711119 5.4074245732
> O -2.9500441444 1.1398319329 5.4010622063
> H -0.3897742635 1.0153182782 4.6757696096
> ```
> **两种模式的几何差别（从上面两段坐标直接读出的事实）**：
> | 量 | mode1 | mode2 |
> |---|---|---|
> | 甲基碳 z | 7.936 | 7.362 |
> | 羧基碳 z | 6.614 | 5.955 |
> | 两个羧基氧的 z | **5.616 / 6.601**（相差 0.985 Å） | **5.407 / 5.401**（相差 0.006 Å） |
> | 两个羧基氧的 x | **−2.876 / −1.528**（相差 1.348 Å） | **−3.066 / −2.950**（相差 0.116 Å） |
> | 羟基 H 的 z | 5.684 | **4.676** |
> | slab 原子（1–108）最高 z | **4.3992**（`O -5.4086768695 -1.8843459443 4.3991860126`；O 中最高） | **4.3320** |
> | slab 中 O 的最高 z | 4.3992 | 4.3320 |
> | 乙酸最低原子的 z 与 slab 顶的间隙 | **1.217 Å**（羧基 O，5.6164 − 4.3992） | **0.344 Å**（羟基 H，4.6758 − 4.3320） |
>
> **⇒ [H 层推断，非原文结论]** mode1 的两个羧基氧**不等价**（z 差 0.985 Å、x 差 1.348 Å），
> 靠近表面的只有其中一个 ⇒ 形貌接近**单齿**；mode2 的两个羧基氧**几乎完全等价**
> （z 差 0.006 Å、x 差 0.116 Å）、且都比 mode1 更低 ⇒ 形貌接近**双齿/桥式**，
> 同时羟基 H 被压到 z = 4.6758 Å（**离 slab 顶仅 0.344 Å**）⇒ **很可能对应解离吸附**。
> **教程原文只用 "two possible binding modes" 描述（T14 P1），没有给出"单齿/双齿/解离"的命名**，
> 也把这个问题留给学员用 `GEO_OPT` 后的能量去回答（T14 P3：与论文 Table 1 对照）。

### 4.11 T15：`&XC` 段（PBE0-D3）与 `water_pbe0_cheating.inp`

**核心 `&XC` 段（T15 P1–P2 / P5–P6 照抄）**：
```
! specify the exchange and correlation treatment
&XC
  ! use a PBE0 functional
  &XC_FUNCTIONAL
    &PBE
      ! 75% GGA exchange
      SCALE_X 0.75
      ! 100% GGA correlation
      SCALE_C 1.0
    &END PBE
  &END XC_FUNCTIONAL
  &HF
    ! 25 % HFX exchange
    FRACTION 0.25
    &SCREENING
      ! important parameter to get stable HFX calcs
      EPS_SCHWARZ 1.0E-6
      ! needs a good (GGA) initial guess
      SCREEN_ON_INITIAL_P TRUE
    &END
    &INTERACTION_POTENTIAL
      ! for condensed phase systems
      POTENTIAL_TYPE TRUNCATED
      ! should be less than halve the cell
      CUTOFF_RADIUS 6.0
      ! data file needed with the truncated operator
      T_C_G_DATA ./t_c_g.dat
    &END
    &MEMORY
      ! In MB per MPI rank.. use as much as need to get in-core operation
      MAX_MEMORY 4000
      EPS_STORAGE_SCALING 0.1
    &END
  &END
  ! adding Grimme's D3 correction (by default without C9 terms)
  &VDW_POTENTIAL
    POTENTIAL_TYPE PAIR_POTENTIAL
    &PAIR_POTENTIAL
      PARAMETER_FILE_NAME dftd3.dat
      TYPE DFTD3
      REFERENCE_FUNCTIONAL PBE0
      R_CUTOFF [angstrom] 16
    &END
  &END VDW_POTENTIAL
&END XC
```

**3rd task 的短程交换（T15 P3 照抄）** —— 加在 `&XC_FUNCTIONAL` 里、与 `&PBE` 并列：
```
&PBE_HOLE_T_C_LR
  CUTOFF_RADIUS 2.5
  SCALE_X 0.25
&END
```
> 同时**必须把 `&INTERACTION_POTENTIAL` 的 `CUTOFF_RADIUS` 也改成 2.5**（T15 P3 原文：
> "and employ the same CUTOFF_RADIUS for the INTERACTION_POTENTIAL"）。

**4rd task 的 ADMM 三步（T15 P3 照抄）**：
```
! ① 加一行
BASIS_SET_FILE_NAME BASIS_ADMM

! ② 每个 &KIND 里加一行
AUX_FIT_BASIS_SET cFIT3

! ③ 新增一段
! use ADMM
&AUXILIARY_DENSITY_MATRIX_METHOD
  ! recommended, i.e. use a smaller basis for HFX
  ! each kind will need an AUX_FIT_BASIS_SET.
  METHOD BASIS_PROJECTION
  ! recommended, this method is stable and allows for MD.
  ! can be expensive for large systems
  ADMM_PURIFICATION_METHOD MO_DIAG
&END
```

**1st task 的 GGA 重启改动（T15 P1 照抄）**：
```
RUN_TYPE ENERGY
IOLEVEL MEDIUM
RESTART ON
# comment section &EXT_RESTART
```
```
SCF_GUESS RESTART
WFN_RESTART_FILE_NAME WATER-RESTART-GGA.wfn
```

**5th task 的电离水改动（T15 P4 照抄）**：
```
! Charge and multiplicity
LSD
CHARGE 1
MULTIPLICITY 2
```

**`HFX_MEM_INFO` 输出（T15 P2 照抄）**：
```
HFX_MEM_INFO| Number of cart. primitive ERI's calculated:               20780449251
HFX_MEM_INFO| Number of sph. ERI's calculated:                           4626861713
HFX_MEM_INFO| Number of sph. ERI's stored in-core:                       1440639962
HFX_MEM_INFO| Number of sph. ERI's stored on disk:                                 0
HFX_MEM_INFO| Number of sph. ERI's calculated on the fly:                          0
HFX_MEM_INFO| Total memory consumption ERI's RAM [MB's]:                        1368
HFX_MEM_INFO| Whereof max-vals [MB's]:                                            78
HFX_MEM_INFO| Total compression factor ERI's RAM:                               8.03
HFX_MEM_INFO| Total memory consumption ERI's disk [MB's]:                          0
HFX_MEM_INFO| Total compression factor ERI's disk:                              0.00
HFX_MEM_INFO| Size of density/Fock matrix [MB's]:                                 14
HFX_MEM_INFO| Size of buffers [MB's]:                                              2
HFX_MEM_INFO| Number of periodic image cells considered:                          27
HFX_MEM_INFO| Est. max. program size after HFX [MB's]:                           243
```
> **读法**：`on disk: 0` + `on the fly: 0` ⇒ **全部 in-core**（这正是 `MAX_MEMORY 4000` 换来的）；
> `compression factor 8.03` ⇒ `EPS_STORAGE_SCALING 0.1` 带来的压缩比；
> `periodic image cells considered: 27` = 3×3×3，对应 `CUTOFF_RADIUS 6.0`。

**SCF 前两步（T15 P2–P3 照抄）**：
```
    1 OT DIIS 0.80E-01   68.5  0.00096341  -1102.1375916328  -1.10E+03
Trace(PS): 512.0000000000
Electronic density on regular grids:  -511.9999999886   0.0000000114
Core density on regular grids:         511.9999999836  -0.0000000164
Total charge density on r-space grids:  -0.0000000051
Total charge density g-space grids:     -0.0000000051
    2 OT DIIS 0.80E-01    4.1  0.00064929  -1102.1607534171  -2.32E-02
```
> **第 1 步 68.5 s vs 第 2 步 4.1 s**：这正是 G 层 `08_errors_and_faq.md` 说的
> "首个 SCF 循环因要先算 ERI 通常非常耗时"的实测印证；
> **`Trace(PS) = 512` ⇒ 512 个价电子**（GTH-PBE：O 贡献 6、H 贡献 1 ⇒ 每个 H₂O 8 个价电子
> ⇒ **512 / 8 = 64 个水分子**，与 T13 P4 的 `water.xyz`（**192 原子 = 64 个 H₂O**）以及
> 单胞 `12.42³ Å³`（水密度下约 64 个分子）**三方自洽**；T15 P1 说 "Using the water input from the
> previous exercise"，指的就是 T13 那份）。

**`water_pbe0_cheating.inp` 全文（T15 P4–P7 照抄）**：
```fortran
&GLOBAL
  ! the project name is made part of most output files... useful to keep order
  PROJECT WATER
  ! various runtypes (energy, geo_opt, etc.) available.
  RUN_TYPE ENERGY
  ! limit the runs to 30min
  WALLTIME 1800
  ! reduce the amount of IO
  IOLEVEL MEDIUM
&END GLOBAL
&FORCE_EVAL
  ! the electronic structure part of CP2K is named Quickstep
  METHOD Quickstep
  &DFT
    ! basis sets and pseudopotential files can be found in cp2k/data
    BASIS_SET_FILE_NAME HFX_BASIS
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    ! GGA restart to provide a good initial density matrix
    WFN_RESTART_FILE_NAME WATER-RESTART-GGA.wfn
    ! Charge and multiplicity
    CHARGE 0
    MULTIPLICITY 1
    &MGRID
      ! PW cutoff ... depends on the element (basis) too small cutoffs lead to the eggbox effect.
      ! certain calculations (e.g. geometry optimization, vibrational frequencies,
      ! NPT and cell optimizations, need higher cutoffs)
      CUTOFF [Ry] 400
    &END
    &QS
      ! use the GPW method (i.e. pseudopotential based calculations with the Gaussian and Plane Waves scheme).
      METHOD GPW
      ! default threshold for numerics ~ roughly numerical accuracy of the total energy per electron,
      ! sets reasonable values for all other thresholds.
      EPS_DEFAULT 1.0E-10
      ! used for MD, the method used to generate the initial guess.
      EXTRAPOLATION ASPC
    &END
    &POISSON
      PERIODIC XYZ ! the default, gas phase systems should have 'NONE' and a wavelet solver
    &END
    &PRINT
      ! at the end of the SCF procedure generate cube files of the density
      &E_DENSITY_CUBE OFF
      &END E_DENSITY_CUBE
      ! compute eigenvalues and homo-lumo gap each 10nd MD step
      &MO_CUBES
        NLUMO 4
        NHOMO 4
        WRITE_CUBE .FALSE.
        &EACH
          MD 10
        &END
      &END
    &END
    ! use the OT METHOD for robust and efficient SCF, suitable for all non-metallic systems.
    &SCF
      SCF_GUESS RESTART ! can be used to RESTART an interrupted calculation
      MAX_SCF 30
      EPS_SCF 1.0E-6 ! accuracy of the SCF procedure typically 1.0E-6 - 1.0E-7
      &OT
        ! an accurate preconditioner suitable also for larger systems
        PRECONDITIONER FULL_SINGLE_INVERSE
        ! the most robust choice (DIIS might sometimes be faster, but not as stable).
        MINIMIZER DIIS
      &END OT
      &OUTER_SCF ! repeat the inner SCF cycle 10 times
        MAX_SCF 10
        EPS_SCF 1.0E-6 ! must match the above
      &END
      ! do not store the wfn during MD
      &PRINT
        &RESTART ON
        &END
      &END
    &END SCF
    ! specify the exchange and correlation treatment
    &XC
      ! use a PBE0 functional
      &XC_FUNCTIONAL
        &PBE
          ! 75% GGA exchange
          SCALE_X 0.75
          ! 100% GGA correlation
          SCALE_C 1.0
        &END PBE
      &END XC_FUNCTIONAL
      &HF
        ! 25 % HFX exchange
        FRACTION 0.25
        &SCREENING
          ! important parameter to get stable HFX calcs
          EPS_SCHWARZ 1.0E-6
          ! needs a good (GGA) initial guess
          SCREEN_ON_INITIAL_P TRUE
        &END
        &INTERACTION_POTENTIAL
          ! for condensed phase systems
          POTENTIAL_TYPE TRUNCATED
          ! should be less than halve the cell
          CUTOFF_RADIUS 6.0
          ! data file needed with the truncated operator
          T_C_G_DATA ./t_c_g.dat
        &END
        &MEMORY
          ! In MB per MPI rank.. use as much as need to get in-core operation
          MAX_MEMORY 4000
          ! additional accuracy for storing compressed results
          EPS_STORAGE_SCALING 0.1
        &END
      &END
      ! adding Grimme's D3 correction (by default without C9 terms)
      &VDW_POTENTIAL
        POTENTIAL_TYPE PAIR_POTENTIAL
        &PAIR_POTENTIAL
          PARAMETER_FILE_NAME dftd3.dat
          TYPE DFTD3
          REFERENCE_FUNCTIONAL PBE0
          R_CUTOFF [angstrom] 16
        &END
      &END VDW_POTENTIAL
    &END XC
  &END DFT
  ! description of the system
  &SUBSYS
    &CELL
      ! unit cells that are orthorhombic are more efficient with CP2K
      ABC [angstrom] 12.42 12.42 12.42
    &END CELL
    ! atom coordinates can be in the &COORD section,
    ! or provided as an external file.
    &TOPOLOGY
      COORD_FILE_NAME water.xyz
      COORD_FILE_FORMAT XYZ
    &END
    ! MOLOPT basis sets are fairly costly,
    ! but in the 'DZVP-MOLOPT-SR-GTH' available for all elements
    ! their contracted nature makes them suitable
    ! for condensed and gas phase systems alike.
    &KIND H
      BASIS_SET DZVP-GTH
      POTENTIAL GTH-PBE-q1
    &END KIND
    &KIND O
      BASIS_SET DZVP-GTH
      POTENTIAL GTH-PBE-q6
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
! how to propagate the system, selection via RUN_TYPE in the &GLOBAL section
&MOTION
  &GEO_OPT
    OPTIMIZER BFGS ! Good choice for 'small' systems (use LBFGS for large systems)
    MAX_ITER 100
    MAX_DR [bohr] 0.003 ! adjust target as needed
    &BFGS
    &END
  &END
  &MD
    ENSEMBLE NVT ! sampling the canonical ensemble, accurate properties might need NVE
    TEMPERATURE [K] 300
    TIMESTEP [fs] 0.5
    STEPS 1000
    # GLE thermostat as generated at http://epfl-cosmo.github.io/gle4md
    # GLE provides an effective NVT sampling.
    &THERMOSTAT
      REGION MASSIVE
      TYPE GLE
      &GLE
        NDIM 5
        A_SCALE [ps^-1] 1.00
        A_LIST  1.859575861256e+2   2.726385349840e-1   1.152610045461e+1  -3.641457826260e+1   2.317337581602e+2
        A_LIST -2.780952471206e-1   8.595159180871e-5   7.218904801765e-1  -1.984453934386e-1   4.240925758342e-1
        A_LIST -1.482580813121e+1  -7.218904801765e-1   1.359090212128e+0   5.149889628035e+0  -9.994926845099e+0
        A_LIST -1.037218912688e+1   1.984453934386e-1  -5.149889628035e+0   2.666191089117e+1   1.150771549531e+1
        A_LIST  2.180134636042e+2  -4.240925758342e-1   9.994926845099e+0  -1.150771549531e+1   3.095839456559e+2
      &END GLE
    &END THERMOSTAT
  &END
  &PRINT
    &TRAJECTORY
      &EACH
        MD 1
      &END EACH
    &END TRAJECTORY
    &VELOCITIES OFF
    &END VELOCITIES
    &FORCES OFF
    &END FORCES
    &RESTART_HISTORY
      &EACH
        MD 500
      &END EACH
    &END RESTART_HISTORY
    &RESTART
      BACKUP_COPIES 3
      &EACH
        MD 1
      &END EACH
    &END RESTART
  &END PRINT
&END
```

### 4.12 T16：TD 与 OT 两版 `&SCF` + 完整输入（照抄）

**TD 版完整输入 `scf_basic.inp`（T16 P1–P3 照抄）**：
```fortran
&FORCE_EVAL
  METHOD QS
  &DFT
    BASIS_SET_FILE_NAME GTH_BASIS_SETS
    BASIS_SET_FILE_NAME BASIS_MOLOPT
    POTENTIAL_FILE_NAME POTENTIAL
    &MGRID
      CUTOFF 300
    &END MGRID
    &QS
      EPS_DEFAULT 1.0E-12
    &END QS
    &SCF
      SCF_GUESS ATOMIC
      # SCF_GUESS RESTART
      EPS_SCF 1.0E-5
      &MIXING
        ALPHA 0.4
      &END
    &END SCF
    &XC
      &XC_FUNCTIONAL Pade
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 9.8528 9.8528 9.8528
    &END CELL
    # 32 H2O (TIP5P,1bar,300K) a = 9.8528
    &COORD
      O  2.280398  9.146539  5.088696
      O  1.251703  2.406261  7.769908
      O  1.596302  6.920128  0.656695
      O  2.957518  3.771868  1.877387
      O  0.228972  5.884026  6.532308
      O  9.023431  6.119654  0.092451
      O  7.256289  8.493641  5.772041
      O  5.090422  9.467016  0.743177
      O  6.330888  7.363471  3.747750
      O  7.763819  8.349367  9.279457
      O  8.280798  3.837153  5.799282
      O  8.878250  2.025797  1.664102
      O  9.160372  0.285100  6.871004
      O  4.962043  4.134437  0.173376
      O  2.802896  8.690383  2.435952
      O  9.123223  3.549232  8.876721
      O  1.453702  1.402538  2.358278
      O  6.536550  1.146790  7.609732
      O  2.766709  0.881503  9.544263
      O  0.856426  2.075964  5.010625
      O  6.386036  1.918950  0.242690
      O  2.733023  4.452756  5.850203
      O  4.600039  9.254314  6.575944
      O  3.665373  6.210561  3.158420
      O  3.371648  6.925594  7.476036
      O  5.287920  3.270653  6.155080
      O  5.225237  6.959594  9.582991
      O  0.846293  5.595877  3.820630
      O  9.785620  8.164617  3.657879
      O  8.509982  4.430362  2.679946
      O  1.337625  8.580920  8.272484
      O  8.054437  9.221335  1.991376
      H  1.762019  9.820429  5.528454
      H  3.095987  9.107088  5.588186
      H  0.554129  2.982634  8.082024
      H  1.771257  2.954779  7.182181
      H  2.112148  6.126321  0.798136
      H  1.776389  7.463264  1.424030
      H  3.754249  3.824017  1.349436
      H  3.010580  4.524142  2.466878
      H  0.939475  5.243834  6.571945
      H  0.515723  6.520548  5.877445
      H  9.852960  6.490366  0.393593
      H  8.556008  6.860063 -0.294256
      H  7.886607  7.941321  6.234506
      H  7.793855  9.141028  5.315813
      H  4.467366  9.971162  0.219851
      H  5.758685 10.102795  0.998994
      H  6.652693  7.917443  3.036562
      H  6.711966  7.743594  4.539279
      H  7.751955  8.745180 10.150905
      H  7.829208  9.092212  8.679343
      H  8.312540  3.218330  6.528858
      H  8.508855  4.680699  6.189990
      H  9.742249  1.704975  1.922581
      H  8.799060  2.876412  2.095861
      H  9.505360  1.161677  6.701213
      H  9.920117 -0.219794  7.161006
      H  4.749903  4.186003 -0.758595
      H  5.248010  5.018415  0.403676
      H  3.576065  9.078451  2.026264
      H  2.720238  9.146974  3.273164
      H  9.085561  4.493058  9.031660
      H  9.215391  3.166305  9.749133
      H  1.999705  2.060411  1.927796
      H  1.824184  0.564565  2.081195
      H  7.430334  0.849764  7.438978
      H  6.576029  1.537017  8.482885
      H  2.415851  1.576460  8.987338
      H  2.276957  0.099537  9.289499
      H  1.160987  1.818023  4.140602
      H  0.350256  2.874437  4.860741
      H  5.768804  2.638450  0.375264
      H  7.221823  2.257514  0.563730
      H  3.260797  5.243390  5.962382
      H  3.347848  3.732214  5.988196
      H  5.328688  9.073059  5.982269
      H  5.007063  9.672150  7.334875
      H  4.566850  6.413356  3.408312
      H  3.273115  7.061666  2.963521
      H  3.878372  7.435003  6.843607
      H  3.884673  6.966316  8.283117
      H  5.918240  3.116802  5.451335
      H  5.355924  2.495093  6.711958
      H  5.071858  7.687254 10.185667
      H  6.106394  7.112302  9.241707
      H  1.637363  5.184910  4.169264
      H  0.427645  4.908936  3.301903
      H  9.971698  7.227076  3.709104
      H 10.647901  8.579244  3.629806
      H  8.046808  5.126383  2.213838
      H  7.995317  4.290074  3.474723
      H  1.872601  7.864672  7.930401
      H  0.837635  8.186808  8.987268
      H  8.314696 10.115534  2.212519
      H  8.687134  8.667252  2.448452
    &END COORD
    &KIND H
      BASIS_SET DZVP-GTH
      POTENTIAL GTH-PADE-q1
    &END KIND
    &KIND O
      BASIS_SET DZVP-GTH
      POTENTIAL GTH-PADE-q6
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
&GLOBAL
  PROJECT H2O-32
  RUN_TYPE MD
  PRINT_LEVEL MEDIUM
&END GLOBAL
```
> **注意**：原文里 `&FORCE_EVAL` 在 `&GLOBAL` **之前**（T16 P1 vs P3）——印证 T10 P1 的说法
> "**顺序不重要**"。原文注释里 `# 32 H2O (TIP5P,1bar,300K) a = 9.8528` 交代了盒子的来历。

**OT 版 `&SCF` 段（T16 P3 照抄）**：
```
&SCF
  SCF_GUESS ATOMIC
  EPS_SCF 1.0E-06
  MAX_SCF 20
  &OT ON
    MINIMIZER DIIS
    PRECONDITIONER FULL_ALL
    ENERGY_GAP 0.001
  &END OT
  &OUTER_SCF
    MAX_SCF 2
  &END OUTER_SCF
&END SCF
```

**TD 版 `&SCF` 段（T16 P1 照抄，用于对照）**：
```
&SCF
  SCF_GUESS ATOMIC
  # SCF_GUESS RESTART
  EPS_SCF 1.0E-5
  &MIXING
    ALPHA 0.4
  &END
&END SCF
```
> **T16 没告诉你的**（G 层可补）：`&MIXING` 不写 `METHOD` 时用的是**默认混合方法 `DIRECT_P_MIXING`**
> （G 层 `03_scf_convergence.md` §1.3）。**这是"最小 TD 输入"的写法**；T10 P5 的 `BROYDEN_MIXING` 是显式指定。

**T16 的四个 TASK（照抄原文清单）**：
```
TASK 1  This uses a rather small BASIS_SET DVZP-GTH which is much too small for production runs.
        Repeat the calculation using
          BASIS_SET TZV2P-GTH
          BASIS_SET DZVP-MOLOPT-GTH
          BASIS_SET TZV2P-MOLOPT-GTH
        You should change the basis set for each atomic type (kind) in each case.
TASK 2  See how OT compares with TD for the different basis sets you ran previously.
TASK 3  Exchange correlation functional.  ... Try changing the functional to `PBE` ...
        Also change the pseudopotential you are using in the KIND sections so it matches the functional.
TASK 4  System size affects the efficiency too ... ${main directory of my cp2k installation}/tests/QS/benchmarks ...
        Change the CELL parameters and the coordinates of the atoms and see how the methods scale.
        You could also explore how the methods scale with number of processors used.
TASK 5  And of course, probably the most important 'parameter' is the system itself. ...
        Try similar tests on a system you are interested in!
```

### 4.13 T17：`geo.inp` / `neb.inp` / `md.inp` / FES 脚本（照抄）

> **指针**：**G 层 `24_official_exercises.md` §1.2 已收录 `geo.inp` 与 `neb.inp` 的骨架**
> （`GEO_OPT`、`&QS METHOD PM6`、`&POISSON`、`&BAND`、`RUN_TYPE BAND`、输出块）。
> **此处补 G 层未收的增量**：① `geo.inp` 的**真实 6 原子坐标**；② `neb.inp` 的 **`&TOPOLOGY`** 与**完整 9+10 个输出数字**；
> ③ **`md.inp` 全文**（G 层完全没有 FES 部分）；④ **FES 的 Python 脚本全文**。

**`geo.inp` 的坐标（T17 P1–P2 照抄）**：
```
&COORD
  C  -4.03963494  0.97427857 -0.29785096
  H  -3.97152206  2.11080568 -0.35500445
  H  -3.95108814  0.19729141  0.53163699
  H  -3.95810737  0.47922964 -1.32151084
  Cl -5.77885435  1.07089312 -0.04609427
  Cl -1.77974793  0.99422072 -0.29785096
&END COORD
```
> TASK 1 要求"**改初始几何猜测**再跑第二个优化，得到另一个局部极小（**另一个 Cl 要与 C 成共价键**）"
> ——即把上面第 5、6 行的两个 Cl 的坐标对调/互换。

**`neb.inp` 的 `&TOPOLOGY`（T17 P3 照抄；G 层未收）**：
```
&TOPOLOGY
  COORD_FILE_NAME init.xyz
  COORDINATE xyz
&END TOPOLOGY
```

**NEB 主输出的完整数字（T17 P3 照抄；G 层只抄了前 4 个值）**：
```
*******************************************************************************
  BAND TYPE                     =                                          CI-NEB
  BAND TYPE OPTIMIZATION        =                                              SD
  STEP NUMBER                   =                                               1
  NUMBER OF NEB REPLICA         =                                              10
  DISTANCES REP =        0.252266        0.229810        0.225933        0.227113
                         0.201788        0.138731        0.138676        0.204817
                         0.252328
  ENERGIES [au] =      -24.815004      -24.813368      -24.808500      -24.803002
                       -24.800607      -24.802583      -24.805589      -24.809114
                       -24.813372      -24.815004
  BAND TOTAL ENERGY [au]        =                             -248.08548199708440
*******************************************************************************
```
> **能垒怎么读**：10 个镜像的能量里，两端（第 1 与第 10 个）都是 **`-24.815004`**（对称反应），
> 最高点在第 5 个 **`-24.800607`** ⇒ 能垒 ≈ `(-24.800607) − (-24.815004)` = **0.014397 Ha**；
> **换算成 eV 需乘 27.2114**（≈ **0.392 eV**）。**T17 P3 只要求"Find the activation barrier of the reaction in eV"，
> 没给换算系数——按 CP2K 的 a.u. 惯例（1 Ha = 27.2114 eV）换算。**
> **注意**：上面这是 **STEP NUMBER = 1** 的输出，**不是收敛后的结果**；原文说"最后一段对应收敛的 NEB 轨迹"。

**`md.inp` 全文（T17 P4–P5 照抄；G 层未收）**：
```fortran
&GLOBAL
  PRINT_LEVEL LOW
  PROJECT ch3f
  RUN_TYPE MD          # Molecular Dynamics
&END GLOBAL
&MOTION
  &MD                  # MD parameters
    ENSEMBLE NVT
    STEPS 200000
    TIMESTEP 0.5
    TEMPERATURE 1000.0
    &THERMOSTAT
      TYPE NOSE
      &NOSE
        TIMECON 100.
      &END NOSE
    &END THERMOSTAT
  &END MD
  &CONSTRAINT          # Restraints to keep Cl from going too far
    &COLLECTIVE
      INTERMOLECULAR
      COLVAR 1
      TARGET 1.8
      &RESTRAINT
        K 0.005
      &END
    &END
    &COLLECTIVE
      INTERMOLECULAR
      COLVAR 2
      TARGET 1.8
      &RESTRAINT
        K 0.005
      &END
    &END
  &END
  &FREE_ENERGY         # Section to print out the values of CVs every step
    &METADYN
      DO_HILLS .FALSE.
      &METAVAR
        SCALE 0.2
        COLVAR 1
      &END
      &METAVAR
        SCALE 0.2
        COLVAR 2
      &END
      &PRINT
        &COLVAR
          COMMON_ITERATION_LEVELS 3
          &EACH
            MD 1
          &END
        &END COLVAR
      &END PRINT
    &END METADYN
  &END FREE_ENERGY
&END MOTION
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    ... Same as before ...
  &END DFT
  &SUBSYS
    &CELL
      ABC 10.0 10.0 10.0
      PERIODIC NONE
    &END CELL
    &COORD
      C  -4.03963494  0.97427857 -0.29785096
      H  -3.97152206  2.11080568 -0.35500445
      H  -3.95108814  0.19729141  0.53163699
      H  -3.95810737  0.47922964 -1.32151084
      Cl -5.77885435  1.07089312 -0.04609427
      Cl -1.77974793  0.99422072 -0.29785096
    &END COORD
    &COLVAR            # CV definitions
      &DISTANCE
        ATOMS 1 5
      &END
    &END COLVAR
    &COLVAR
      &DISTANCE
        ATOMS 1 6
      &END
    &END COLVAR
  &END SUBSYS
&END FORCE_EVAL
```
> **关键设计点（H 层提炼）**：**这条 MD 根本不是 metadynamics**——`DO_HILLS .FALSE.` 关掉了撒山，
> 只是**借用 `&METADYN` 的 `&PRINT/&COLVAR` 机制把两个 CV 每步写盘**（注释原文就说
> "Section to print out the values of CVs every step"）。**两个 `&COLLECTIVE` 谐振约束
> （`TARGET 1.8`、`K 0.005`）是"伞形采样式的窗口约束"**，目的是把构型限制在反应区附近、
> 不让 Cl 跑掉，**而不是施加偏置势去算 PMF**。所以原文说"we will use **unbiased** Molecular Dynamics"。
> `&METAVAR SCALE 0.2` 只影响撒山宽度，**在 `DO_HILLS .FALSE.` 下不起实际作用**。
>
> **与 G 层的对照（重要）**：G 层 `17_constrained_dynamics_and_paths.md` §1.2 给的官方示例是
> **硬约束**（`&COLLECTIVE COLVAR 1 / INTERMOLECULAR TRUE / TARGET [angstrom] 2.0`，
> **没有 `&RESTRAINT` 子块**，配 `&LAGRANGE_MULTIPLIERS ON` 输出约束力做热力学积分）；
> **T17 用的是谐振约束（harmonic restraint，多了 `&RESTRAINT K 0.005`）**——两者机制不同：
> 硬约束锁死 CV 值，谐振约束只加一个 `½K(s−s₀)²` 的偏置，CV 仍可涨落。**⇒ T17 的写法是 G 层示例之外的另一种用法，H 层首次登记。**
>
> **另一个易错点**：T17 写的是**裸关键字 `INTERMOLECULAR`**（无取值），
> G 层 `17_...` §1.2 写的是 **`INTERMOLECULAR TRUE`**；CP2K 的逻辑关键字省略取值时默认 `.TRUE.`，
> **所以两者等价**（G 层 §1.1 也确认"跨分子必须加"）。

**FES 的 Python 脚本（T17 P5 完整照抄）**：
```python
import numpy as np
import matplotlib.pyplot as plt

bohr_2_angstrom = 0.529177
kb = 8.6173303e-5  # eV * K^-1
temperature = 1000.0  #Change temperature according to your MD simulations!

colvar_path = "./ch3f-COLVAR.metadynLog"

# Load the colvar file
colvar_raw = np.loadtxt(colvar_path)

# Extract the two CVs
d1 = colvar_raw[:, 1] * bohr_2_angstrom
d2 = colvar_raw[:, 2] * bohr_2_angstrom

# Create a 2d histogram corresponding to the CV occurances
cv_hist = np.histogram2d(d1, d2, bins=50)

# probability from the histogram
prob = cv_hist[0]/len(d1)

# Free energy surface
fes = -kb * temperature * np.log(prob)

# Save the image
extent = (np.min(cv_hist[1]), np.max(cv_hist[1]), np.min(cv_hist[2]), np.max(cv_hist[2]))
plt.figure(figsize=(8, 8))
plt.imshow(fes.T, extent=extent, aspect='auto', origin='lower', cmap='hsv')
cbar = plt.colorbar()
cbar.set_label("Free energy [eV]")
plt.xlabel("d1 [ang]")
plt.ylabel("d2 [ang]")
plt.savefig("./fes.png", dpi=200)
plt.close()
```
> **脚本里三个硬编码要改**：① `temperature`；② `colvar_path` 的文件名前缀（**必须与 `PROJECT` 一致**）；
> ③ `bohr_2_angstrom = 0.529177`（**说明 `*COLVAR.metadynLog` 里的 CV 是 Bohr，不是 Å**）。
> `kb = 8.6173303e-5 eV·K⁻¹` ⇒ **FES 直接以 eV 输出**。
> **原文提醒**："(Don't forget to change the temperature in Python script!)"（T17 P5）。

### 4.14 三份练习共享的"通用注释块"（**值得单列，因为它是官方对参数依赖性的明确表述**）

T13 P7、T14 P4–P5 的输入里，同一段注释出现了两次，是这 8 份里少见的"官方参数警告"：

```
! PW cutoff ... depends on the element (basis) too small cutoffs lead to the eggbox effect.
! certain calculations (e.g. geometry optimization, vibrational frequencies,
! NPT and cell optimizations, need higher cutoffs)
CUTOFF [Ry] 400
```
> **两层含义**：① **最优 `CUTOFF` 取决于元素与基组**（→ 呼应 T12 的收敛测试）；
> ② **`CUTOFF` 太小的典型症状叫 "eggbox effect"（蛋盒效应）**；
> ③ **力/应力类任务（几何优化、频率、NPT、晶胞优化）需要更高的 cutoff**。

另一段重复出现的注释（T13 P7、T14 P5）：
```
! unit cells that are orthorhombic are more efficient with CP2K
ABC [angstrom] 12.42 12.42 12.42
```
```
! MOLOPT basis sets are fairly costly,
! but in the 'DZVP-MOLOPT-SR-GTH' available for all elements
! their contracted nature makes them suitable
! for condensed and gas phase systems alike.
```
```
! use the OT METHOD for robust and efficient SCF, suitable for all non-metallic systems.
```
> **最后这条注释就是"OT 适用面"的官方教学口径：`suitable for all non-metallic systems`（适用于所有非金属体系）**
> ——这与 T16 用"闭壳、大带隙的水"演示 OT（T16 P4）是同一逻辑。

### 4.15 三份练习共用的 GLE 热浴参数（照抄，**这是本批里最"照抄才有用"的一块**）

T13 P8、T14 P6、T15 P7 完全相同的 GLE 参数（注释标明来源）：
```
# GLE thermostat as generated at http://epfl-cosmo.github.io/gle4md
# GLE provides an effective NVT sampling.
&THERMOSTAT
  REGION MASSIVE
  TYPE GLE
  &GLE
    NDIM 5
    A_SCALE [ps^-1] 1.00
    A_LIST  1.859575861256e+2   2.726385349840e-1   1.152610045461e+1  -3.641457826260e+1   2.317337581602e+2
    A_LIST -2.780952471206e-1   8.595159180871e-5   7.218904801765e-1  -1.984453934386e-1   4.240925758342e-1
    A_LIST -1.482580813121e+1  -7.218904801765e-1   1.359090212128e+0   5.149889628035e+0  -9.994926845099e+0
    A_LIST -1.037218912688e+1   1.984453934386e-1  -5.149889628035e+0   2.666191089117e+1   1.150771549531e+1
    A_LIST  2.180134636042e+2  -4.240925758342e-1   9.994926845099e+0  -1.150771549531e+1   3.095839456559e+2
  &END GLE
&END THERMOSTAT
```
> **配套的 `&MD` 段（T13 P8 等）**：`ENSEMBLE NVT` / `TEMPERATURE [K] 300` / `TIMESTEP [fs] 0.5` / `STEPS 1000`。
> **注意对比 T17 P4 用的是 `TYPE NOSE` + `TIMECON 100.`**——**同一批教材里两种热浴都出现了**，
> 正好可以拿来和 G 层 `04_sampling_md.md` §7（官方推荐常规 NVT 用 `CSVR`）对照。

### 4.16 T12 + T10 的"参数速查卡"（汇总本批出现的数值，便于比对）

| 出处 | `CUTOFF` | `REL_CUTOFF` | `NGRIDS` | 基组 | 泛函 | 判据/备注 |
|---|---|---|---|---|---|---|
| T10 P2（静态 Si） | **300** | **60** | 4 | DZVP-GTH-PADE | PADE (LDA) | 官方声明"已对该精度足够" |
| T12 P3（收敛模板） | `LT_cutoff` | `LT_rel_cutoff` | 4 | **SZV-GTH-PADE** | PADE (LDA) | `MAX_SCF 1` |
| T12 P10（结论） | **250** | **60** | — | SZV-GTH-PADE | PADE (LDA) | 误差 < 1e-8 Ha |
| T11 P2（H₂O geo_opt） | **200** | **30** | 4 | DZVP-GTH-PADE | PADE (LDA) | 教程演示值，**未做收敛测试** |
| T13 P7 / T14 P5 | **400** | 未给 | 未给 | DZVP-GTH / DZVP-MOLOPT-SR-GTH | PBE + D3 | 注释："太小 → eggbox；力/应力任务需更高" |
| T15 P2/P5（PBE0） | **400** | 未给 | 未给 | DZVP-GTH（HFX_BASIS） | PBE0 + D3 | 另加 `CUTOFF_RADIUS 6.0` |
| T16 P1 | **300** | 未给 | 未给 | DZVP-GTH | PADE (LDA) | 教学对照用 |
| T17 P2 | 未给 | 未给 | 未给 | 无（**PM6 半经验，不需要基组/赝势**） | PM6 | `PERIODIC NONE` + `PSOLVER WAVELET` |

---

## 5. 【新】相对既有 A–G 层的增量（先 grep 确认）

### 5.1 grep 方法与结果（在 `references/` 下，`include=*.md`）

| 检索词 | 命中（G/A–F 层） | 结论 |
|---|---|---|
| `REL_CUTOFF` / `PROGRESSION_FACTOR` / `MULTIGRID INFO` | `official/03_scf_convergence.md` §2（**方法论汇总**）、`01_global_and_units.md` §5.2、`08_errors_and_faq.md`、`23_dft_subpages_full.md` §3.5 | **方法论已在 G 层**；但**脚本、模板、两张 10 行数据表原文**未收 |
| `PBE_HOLE_T_C_LR` | **全库 0 命中** | **H 层首次登记** |
| `SCREEN_ON_INITIAL_P` | 仅 `official/18_...md`（**HF/MP2 页，取 `.FALSE.`**） | T15 的 **`TRUE`** + 教学动机是新内容 |
| `EPS_STORAGE_SCALING` | **全库 0 命中** | **H 层首次登记** |
| `MAX_STEEP_STEPS` / `RESTART_LIMIT` | **全库 0 命中** | **T11 的 `&CG` 调参是 H 层首次登记** |
| `Informations at step` | **全库 0 命中**（G 05 只有关键字的机制说明） | **T11 的输出读法（含完整数字块）是 H 层首次登记** |
| `A_SCALE` | **全库 0 命中** | **T13/T14/T15 的 GLE 参数块（含 5×5 `A_LIST`）是 H 层首次登记** |
| `PM6` / `&SE` | `official/10_features_resources.md`（功能清单）、`16_qmmm_embedding_ml.md`（登记为"未逐页采集"）、`sections.md`/`gen_inp_options.md`（QM/MM 用法） | **T17 的 PM6 非周期输入（`PERIODIC NONE` + `PSOLVER WAVELET` + `CHARGE -1`）是 H 层首次给出可用输入** |
| `TOTAL_NUMBERS` / `SYMMETRY CUBIC`（在 MGRID 语境） | 只有 `20_input_reference_tree.md` 的段名清单 | T12 模板里的用法是新细节 |
| `DO_HILLS .FALSE.` | A 层 `decide.md` §17、B 层 `course_learned.md` §（metadyn 章）都讲 `DO_HILLS T` 的撒山用法；**`DO_HILLS .FALSE.` + `&COLLECTIVE` 谐振约束 + `&METADYN` 当"CV 记录器"** 的组合未收 | **T17 的"借用 METADYN 打印 CV"技巧是 H 层首次登记** |
| `&RESTRAINT`（在 `&COLLECTIVE` 内） | G 层 `17_constrained_dynamics_and_paths.md` §1.2 的官方示例**只有硬约束**（`COLVAR 1` / `INTERMOLECULAR TRUE` / `TARGET [angstrom] 2.0`，**无 `&RESTRAINT`**），配 `&LAGRANGE_MULTIPLIERS ON` 做 TI | **T17 的谐振约束写法（`&RESTRAINT K 0.005`）是 H 层首次登记**；裸 `INTERMOLECULAR` 与 G 层 `INTERMOLECULAR TRUE` 等价 |
| `cubecruncher` | `official/24_official_exercises.md` §3.4（`common:chg` 页的两条命令） | **T14 的三算例命名规律（`<PROJECT大写>-ELECTRON_DENSITY-1_0.cube`）与 `-center geo` 是增量** |
| `summer_school` / `scf_setup` | `h_tutorials/README.md` 自身；`pdf_text/learn_L3.md` 只有一行**链接** | **T13/T14/T15/T16 四份 2016/2018 夏校教材在 G/A–F 层完全没有内容**（连链接登记都没有） |

### 5.2 逐份增量结论

| 文件 | G/A–F 层已有 | **H 层（本文）新增** |
|---|---|---|
| **T10** | **G 层 `01_global_and_units.md` §5.2–5.7 已**几乎逐字收录主输入、逐关键字讲解、运行命令、产物、结果检查、smearing 全流程 | ① **`BASIS_SET` / `GTH_POTENTIALS` 里的原材料条目**（§4.2）；② **完整 10 步 SCF 表 + 能量分解 + ATOMIC FORCES 表**的数字（§4.6）；③ **加 smearing 前后的数字对照**（MO 16→26、熵项、Fermi 能，§4.6）；④ "文件扩展名任意、block 顺序不重要"等**输入格式事实**（T10 P1） |
| **T11** | G 层 `05_optimization.md` §4–§8 覆盖 `GEO_OPT`/`CELL_OPT` 的**关键字机制**（来自 manual）；`FIXED_ATOMS`/`COMPONENTS_TO_FIX`/`LIST` 在 §8 | ① **H₂O 完整输入**（§4.5）；② **`&CG` 的 `MAX_STEEP_STEPS` / `RESTART_LIMIT`**；③ **`PULAY_MIXING` + `NPULAY 5`**；④ **`Informations at step` 完整输出块与读法**（含"四条判据全 YES 才算收敛"的实测演示）；⑤ **`-1.restart` 续算流程与产物清单**；⑥ **极小点重算 + ASPC 参数打印** |
| **T12** | **G 层 `03_scf_convergence.md` §2 已给方法论**（原理、`MAX_SCF 1` 技巧、`PRINT_LEVEL MEDIUM`、三脚本结构、汇总结论 250/60） | ① **`template.inp` 全文**（§4.3a）；② **六个 shell 脚本全文**（§4.3b–g）；③ **两张 10 行 `.ssv` 数据表全文**（§4.4）；④ **`MAX_SCF 1` 的原文理由**；⑤ **选点判据的原文**（"最低的用上最细层的 cutoff，同时多数高斯在粗层"，§3.1.3）；⑥ **`MULTIGRID INFO` 实块 + 1 Ha = 2 Ry 换算**；⑦ **正规表达式与 awk 提取法** |
| **T13** | G 层 `04_sampling_md.md` §13.2 只给了 `.ener` 的**列语义**（`md_step, time[fs], e_kin, temp, e_pot, e_tot, elapsed`）；`07_restarting.md` §5 覆盖 `EXT_RESTART` 机制 | ① **完整 `water_cheating.inp`**（§4.8）；② **生产模式三件事的原文与代码**（`WALLTIME`/`IOLEVEL LOW`/`&RESTART OFF`，§4.7）；③ **`.ener` 的实际 6 行数据与 gnuplot 命令**；④ **守恒量守不住的三条处方原文**（§4.7）；⑤ **"丢 1/3、用 2/3"的平衡经验**；⑥ **GLE 参数块**（§4.15）；⑦ **VMD 做 g(r)/IR 的完整操作路径 + `charges.dat` 点电荷近似**；⑧ **192 原子 `water.xyz` 的头部与来历** |
| **T14** | G 层 `24_official_exercises.md` §4.4 **只把 `dye_tio` 登记为一个词条 + 字符数 24,959/25,057**；§3.4 有 cubecruncher 的两条通用命令 | ① **完整 `mode1.inp`**（§4.10）；② **三算例密度差完整流程 + cube 文件命名规律 + `-center geo`**（§4.9）；③ **PBS 作业脚本与 cubecruncher 编译步骤**；④ **`mode1.xyz`/`mode2.xyz` 的原子数（116）与乙酸片段位置**；⑤ **四个 Task 的完整教学意图（含"Table 1 / Fig. 7 对照"）** |
| **T15** | G 层 `18_...md` §（HF/MP2 页）有 **`FRACTION 1.0` + `TRUNCATED` + `T_C_G_DATA` + `&SCREENING`（`SCREEN_ON_INITIAL_P .FALSE.`）** 的写法；`23_dft_subpages_full.md` §4 有**现代 RI-HFX / ADMM（`ADMM_TYPE ADMMS`、`EXCH_CORRECTION_FUNC PBEX`、`BASIS_ADMM_UZH`）** 的官方写法 | ① **PBE0 的 `SCALE_X 0.75` / `FRACTION 0.25` 双处改法**（"modify the input in two places!"）；② **`&PBE_HOLE_T_C_LR`**（全库首次）；③ **`SCREEN_ON_INITIAL_P TRUE` 与"必须先有 GGA 初猜"的因果**；④ **`EPS_STORAGE_SCALING`**（全库首次）；⑤ **`HFX_MEM_INFO` 输出块与读法**；⑥ **`MAX_MEMORY 4000` 换来的 in-core 操作**；⑦ **ADMM 的三步机械改动 + 老式 `METHOD BASIS_PROJECTION`/`MO_DIAG`/`cFIT3` 路线**；⑧ **`TRUNCATED` 的物理图像与"L/2、5–6 Å、指数收敛"三条经验**；⑨ **电离水（`LSD`/`CHARGE 1`/`MULTIPLICITY 2`）的初猜链要求** |
| **T16** | **全库无任何 `scf_setup` 内容**；A 层 `decide.md` §28 有 OT vs 对角化的**结论性口径**；G 层 `03_scf_convergence.md` §1.4 有 `OUTER_SCF` 机制与官方步数建议 | ① **TD 与 OT 两版完整输入**（§4.12），**唯一变量就是 `&SCF` 段**；② **`ENERGY_GAP 0.001` 与 `PRECONDITIONER FULL_ALL`** 的教学取值；③ **`EPS_DEFAULT 1.0E-12` vs `EPS_SCF 1.0E-5` 的"放大对比度"设计**；④ **TASK 清单：换基组/换泛函/换尺寸/换核数/换体系**；⑤ **"最重要的参数是体系本身"这句官方教学口径**；⑥ **`&MIXING` 在 TD→OT 切换时必须整段替换**的实证（对照 T10 P5 的规则） |
| **T17** | **G 层 `24_official_exercises.md` §1.2 已收录 `geo.inp` + `neb.inp` 骨架与输出解读**（NEB 那一半基本齐了）；A/F 层 `decide.md` §17、`playbook.md` §2.4 有 CI-NEB 的实操经验；G 层 `17_constrained_dynamics_and_paths.md` §1.2 有**硬约束版**的 `&COLLECTIVE` | ① **`geo.inp` 的真实 6 原子坐标**；② **`neb.inp` 的 `&TOPOLOGY`**；③ **NEB 输出的完整 9 个距离 + 10 个能量数字**；④ **`md.inp` 全文**（G 层完全没有）；⑤ **FES 的 Python 脚本全文**；⑥ **`&COLLECTIVE` 谐振约束（`&RESTRAINT K 0.005`）+ `DO_HILLS .FALSE.` 当 CV 记录器的技巧**（G 层只有硬约束版）；⑦ **`PROJECT ch3f` 的命名坑**（见 §6）；⑧ **TASK 3 的四个温度点** |

### 5.3 一句话总结增量

> **T13 / T14 / T15 / T16 四份在 A–G 层几乎是空白**（G 层最多只登记了"页名 + 字符数"或一行链接）；
> **T10 / T12 / T17 三份在 G 层已有高质量覆盖**，本文只补**可执行原文（脚本 / 数据表 / 输出块 / 坐标）**；
> **T11 落在中间**——关键字机制在 G 层，**输入、输出读法与 `&CG` 调参是新的**。

---

## 6. 与既有层的冲突 / 纠错（给页码证据）

| # | 冲突/疑点 | 证据（页码） | 判定与处理 |
|---|---|---|---|
| **1** | **T11 把力的单位写成 "Bohr/Hartree"** | **T11 P3**（"MAX_FORCE and RMS_FORCE (in **Bohr/Hartree**)"）；同页位移写 "(in **Bohr**)" | **原文单位顺序写反**。力在原子单位制下是 **Hartree/Bohr**。**以 G 层为准**：G `05_optimization.md` §4.1 给的是数值不给单位，但 CP2K 全部使用原子单位（A/F 层 `course_learned`/`MAPPING` 转述讲师口径"CP2K 单位 a.u./bohr"）。**引用 T11 时写 `Hartree/Bohr`。** |
| **2** | **T11 输入 `OPTIMIZER CG`，输出却打印 `Optimization Method = SD`** | 输入：**T11 P2**（`OPTIMIZER CG`）+ **T11 P3**（`MAX_STEEP_STEPS 0`）；输出：**T11 P4**（`Optimization Method = SD`，step 1）与 **T11 P5**（同为 `SD`，step 11） | **已更正（原判"两者不自洽"，已推翻）**：`Optimization Method = SD` 是 `OPTIMIZER CG` 的**正常首步输出**——CP2K 的 CG 优化器**首步方向就是最速下降方向**，且该方法名标签在首步打印时**尚未**被改成 `CG`；`MAX_STEEP_STEPS 0` 只关掉"开局连续做若干 SD 步"，**关不掉首步**。**⇒ 示例输出与示例输入同源，不必怀疑。** 依据（CP2K 源码行号）见 **§7 第 1 条**。 |
| **3** | **T11 的 `H2O.out` 在第 1 步耗时 90.8 s、第 11 步 49.9 s——与 "CP2K 2.4 的 H₂O 分子"量级不符** | **T11 P4**（`Used time = 90.837`）、**T11 P5**（`49.893`） | 单个 H₂O、23 个基函数、每步 SCF 只 2 步却要几十秒 ⇒ **这是 2018 年的老机器/老版本实测**。**不要在性能对比里引用这些时间**。（与 G 层 `19_performance_gpu_community.md` 的现代性能数字不同量级，但那不是"冲突"，只是年代差。） |
| **4** | **T12 目标精度写 `10⁻⁶ Ry`，结论表却报 `10⁻⁸ Ha`** | 目标：**T12 P2**、**T12 P4**（"an accuracy of 10⁻⁶ Ry for the total energy"）；结论：**T12 P7**、**T12 P10**（"error in total energy less than 10⁻⁸ Ha"） | **不是冲突，是单位混用**：`1e-6 Ry = 5e-8 Ha`，而判据用的是 **`1e-8 Ha`（更严）**。**⇒ 引用时不要写"精度 1e-8 Ry"**，也不要写"目标 1e-6 Ha"。**照抄原文单位。** |
| **5** | **T16 的 OT 步数远低于官方建议区间** | **T16 P3**：`MAX_SCF 20` + `&OUTER_SCF MAX_SCF 2`；G 层 **`03_scf_convergence.md` §1.4**（官方）：`SCF/MAX_SCF` **16–32**、`OUTER_SCF/MAX_SCF` **8–16** | **不冲突，但必须标明语境**：T16 是**对照实验**，`OUTER_SCF MAX_SCF 2` 是为了让每次测试都快。**生产按 G 层官方区间设。** |
| **6** | **T15 用 `SCREEN_ON_INITIAL_P TRUE`，G 层官方 HF/MP2 页用 `.FALSE.`** | **T15 P2**（`SCREEN_ON_INITIAL_P TRUE`，注释 "needs a good (GGA) initial guess"）；G 层 **`18_posthf_semiempirical_and_xray.md`**（`SCREEN_ON_INITIAL_P .FALSE.`，注释 "Tune these parameters"） | **不是冲突，是场景差异**：T15 的 `TRUE` 与它 `SCF_GUESS RESTART` + `WFN_RESTART_FILE_NAME WATER-RESTART-GGA.wfn`（**T15 P1**）**成对使用**（先有 GGA 初猜才敢在初始 P 上筛选）。**G 层权威性更高（官方 manual），但它讲的是另一条 workflow。⇒ 引用时两条并存并写明前提。** |
| **7** | **T17 的 `PROJECT ch3f` 与整个练习的 CH₃Cl 体系不符** | **T17 P1**（`PROJECT ch3cl`）、**T17 P2**（`PROJECT ch3cl`）vs **T17 P4**（`PROJECT ch3f`）；**T17 P5** 脚本读 `./ch3f-COLVAR.metadynLog` | **原文残留（沿用了 CH₃F 版本的工程名）**，**不是笔误而是实际的输入内容**。**照抄可行，但必须知道**：① `md.inp` 的输出前缀是 **`ch3f-*`**，不是 `ch3cl-*`；② Python 脚本里的 `colvar_path` 必须与之匹配；③ **`GEO_OPT`/`NEB` 阶段仍是 `ch3cl-*`**（`ch3cl-pos-1.xyz`，T17 P2）。**⇒ 工程目录里会同时出现两套前缀。** |
| **8** | **T17 输入 `OPT_TYPE DIIS`，输出首行却写 `BAND TYPE OPTIMIZATION = SD`** | 输入：**T17 P2**（`&OPTIMIZE_BAND OPT_TYPE DIIS`）；输出：**T17 P3**（`BAND TYPE OPTIMIZATION = SD`） | **已更正（原判"两者不一致"，已推翻）**：`&OPTIMIZE_BAND &DIIS` 的 `MAX_SD_STEPS` **默认 1**（"maximum number of SD steps to perform before switching on DIIS"），即 `OPT_TYPE DIIS` 时**第一步本来就是 SD（带线搜索）**，DIIS 被接受后才切成 `DIIS` ⇒ `STEP NUMBER = 1` 写 `SD` 是**预期输出**。F 层 `playbook.md` §2.4 与 B 层 `course_learned` §5.5 的"**CI-NEB 收敛用 DIIS**"**仍然成立**。依据（CP2K 源码行号 + `_kw_probe.py` 默认值）见 **§7 第 4 条**。 |
| **9** | **T13 正文要求 `MINIMIZER DIIS` 时把它列进了"顶层关键字"清单** | **T13 P1**（"Change keywords to: PROJECT WATER / RUN_TYPE MD / BASIS_SET_FILE_NAME HFX_BASIS / **MINIMIZER DIIS** / ABC … / COORD_FILE_NAME … / BASIS_SET DZVP-GTH"）；但 **T13 P7** 的答案文件里 `MINIMIZER DIIS` 位于 **`&SCF &OT`** 内 | **正文措辞会误导**（把段内关键字与顶层关键字并列）。**⇒ 抄的时候认准 `&SCF &OT`**（G 层 `21_...`/`02_...` 的官方写法一致）。 |
| **10** | **T15 的 ADMM 与 G 层的现代 ADMM 写法不同** | **T15 P3** 老式：`METHOD BASIS_PROJECTION` + `ADMM_PURIFICATION_METHOD MO_DIAG` + `AUX_FIT_BASIS_SET cFIT3` + `BASIS_ADMM`（CP2K **2.7** 时代的 `BASIS_ADMM_MOLOPT`）；G 层 `23_dft_subpages_full.md` §4.3 现式：`ADMM_TYPE ADMMS` + `EXCH_CORRECTION_FUNC PBEX` + `BASIS_ADMM_UZH`；A 层 `decide.md` §11 已注"**模板用的是后者，等价且合法**" | **不冲突，是版本演进的两种等价写法**。**⇒ 生产优先用 G 层的现式（`ADMM_TYPE`/`EXCH_CORRECTION_FUNC`）；T15 的老式路线作为"机制解释"保留。** |
| **11** | **同一个 `CUTOFF 400` 在两个练习里被当成"通用起点"** | **T13 P7**、**T14 P4–P5**（注释：`PW cutoff ... depends on the element (basis)`） | **不是冲突**，但**两处都与 T12 的"必须自己测"直接呼应**。**⇒ 引用时必须带注释原文，不能把 400 写成推荐值**（G 层 `04_sampling_md.md` §（AIMD 可更松）另给"优化/能量用 400 → AIMD 可用 300"的官方口径，两者要一起看）。 |
| **12** | **T14 的 AIMD 任务只有 0.5 ps，却又要求讨论氢键与酸性** | **T14 P3**（"~1000 steps, ~0.5ps"）vs 同页原文提醒（"**in order to be statistically relevant, longer trajectories should be employed, and surface slab thickness will play an important role**"） | **原文自己已声明局限**，不算冲突。**⇒ 引用时把这条免责声明一起带上**（与 G 层 `04_sampling_md.md` §14 验证清单第 1 条"轨迹长度必须足以克服自相关"一致）。 |
| **13** | **T15 声称"截断半径通常 5–6 Å 就够"，但 `CUTOFF_RADIUS` 必须是 L/2 以下** | **T15 P1**（"the maximum range (truncation radius) is **L/2** where L is the smallest edge of the unit cell. … Typically, **5-6A** provides good results"）；**T15 P2** 用 `CUTOFF_RADIUS 6.0` + 单胞 `12.42³`（**6.0 = 12.42/2，正好卡在上限**） | **数值自洽**（6.0 ≤ 12.42/2 = 6.21）。**⇒ 这是一个"恰好贴边"的例子**：单胞换成 12.0 Å 就会违反规则。**抄 `CUTOFF_RADIUS 6.0` 时必须同时检查自己的最小边长。**（G 层 `18_...`/`23_...` 反复强调 `CUTOFF_RADIUS < L/2`，一致。） |
| **14** | **T16 的 `BASIS_SET` 拼写 `DVZP-GTH`** | **T16 P3**（"This uses a rather small BASIS_SET **DVZP**-GTH"）；同段其它两处都写 `DZVP-GTH`（`&KIND` 块） | **原文笔误**（`DVZP` ↔ `DZVP`）。**⇒ 抄基组名一律用 `DZVP-GTH`。** |
| **15** | **T13 的 `WALLTIME` 正文 300 s vs 答案文件 1800 s** | **T13 P1**（`WALLTIME 300`，注释 `! limit the runs to 5min`）vs **T13 P6**（答案文件 `WALLTIME 1800`，注释 `! limit the runs to 30min`） | **答案文件放宽了 6 倍**（因为答案里 `STEPS 1000`、`TIMESTEP 0.5` ⇒ 500 fs，5 分钟跑不完 1000 步）。**⇒ 照抄时按自己的机器改。** |

---

## 7. 存疑

> 本节 12 条原为"**无法从这 8 份文本内部断定**"的未决项。本轮**逐条查证**：
> 能定案的写 `✅ **已定案**`，不能定案的收窄成"已排除 / 仍不确定 / 要确证需要"。
> 查证手段（按优先级）：**本地官方 `cp2k_input.xml`**（`python _kw_probe.py`）→ **重抽源 PDF**
> （`pdfplumber` / `PyMuPDF`，**只读源 PDF**）→ **官方手册与 CP2K 源码（GitHub，给 URL）** → 真实产出物。
> **凡结论推翻原文猜测者，一律附「更正记录」留痕。**

1. **T11 的示例输出与示例输入是否同源？**（**T11 P2 输入 vs P4/P5 输出**）
   - ✅ **已定案：同源；`Optimization Method = SD` 是 `OPTIMIZER CG` 的**正常首步输出**，不是"输出对不上输入"。**
   - **依据（CP2K 源码 `src/motion/cg_optimizer.F`）**：
     行 223–225 `g = -xi / h = g / xi = h`（**首步方向就是最速下降方向**）；
     行 229 循环开始**前** `wildcard = "   SD"`；
     行 233 `CALL gopt_f_io_init(..., wildcard, ...)`；
     行 250 `CALL cg_linmin(...)`（先沿 `xi` 走一步）；行 265–267 `CALL gopt_f_io(..., wildcard, ...)`
     打印 `Informations at step = its`；**行 287 才**把 `wildcard` 改成 `"   CG"`。
     ⇒ **第 1 步的打印值必然是 `SD`**（`wildcard` 还没被改成 `CG`），与 `MAX_STEEP_STEPS 0` 无关。
     后续步骤只有当**重置条件**触发时（行 298–303：`(g·h)² > res_lim²·|g|²·|h|²`，即 `|cos(g,h)| > RESTART_LIMIT`）
     才回到 `SD`；T11 P2 设了 `RESTART_LIMIT 9.0E-01`，第 11 步重新打印 `SD` 完全可能。
   - 源码 URL：<https://github.com/cp2k/cp2k/blob/master/src/motion/cg_optimizer.F>
   - **更正记录**：原文写"**两者不自洽**…**最可能的解释是示例输出与示例输入并非同一次运行**"。
     **错在把"打印出来的方法名"当成了"优化器设置"**——`wildcard` 是优化器的**逐步状态标签**，
     不是 `OPTIMIZER` 的复述。**⇒ 不要据此怀疑示例不同源。**
   - **附带发现（同一页）**：T11 P3 的散文把重置条件写成"the cosine of the angles between two consecutive
     searching directions is **less than** 0.9"，而源码行 298 的比较是 `>`（即 `|cos|` **大于** `RESTART_LIMIT` 时重置）。
     **散文与代码的不等号方向相反**；引用该规则时以源码为准。

2. **T12 表格里的 `Date: Mon Jan 20 … GMT 2014` 与文档 "CP2K 2.4" 的关系**
   - ✅ **已定案：数据是 2014 年用 CP2K 2.4 跑的；2018 年只改了页面。**
   - **依据（全在 T12 文本内部，无需外部资料）**：
     T12 行 23 `The calculations were carried out using CP2K version 2.4.`；
     T12 行 334 的分析脚本本身用 `echo "# Date: $(date)" >> $plot_file`
     ⇒ **`.ssv` 头里的日期是"运行时写入"的**，不是页面日期；
     T12 行 369 `# Date: Mon Jan 20 21:20:34 GMT 2014`、行 510 `# Date: Mon Jan 20 00:45:14 GMT 2014`；
     T12 行 541 页脚 `howto/converging_cutoff.txt · Last modified: 2018/06/07 19:26`。
   - **⇒ 结论与原文一致**（"引用时不要写'2018 年的数据'"），本条由"存疑"升级为**已定案**。

3. **T12 P6 里同一行 SCF 记录出现两次**
   - ✅ **已定案：重复**在源 PDF 的文本层里**，不是 pdfplumber 的抽取重复。**
   - **依据**：直接重抽源 PDF（`【截断能测试-庚子计算整理】howto_converging_cutoff ….pdf`）**第 6 页**，
     该页 `width×height = 594.96×841.92`、`chars=3264`、**单栏**；三种参数都出现两遍：
     - `extract_text(layout=True)` → `1 NoMix/Diag. 0.40E+00 0.4 1.10090760 -32.3804557631 -3.24E+01` 连出两行
     - `extract_text(x_tolerance=1.5)` → 同样两行
     - `extract_text()` 默认 → 同样两行
     ⇒ PDF 里就写了两遍（txt 行 293–294 忠实于 PDF）。
   - **仍不确定的是**：CP2K 运行时是否真的把这一行打印了两遍（本层与 PDF 都只能证明"**PDF 里写了两遍**"；
     这行 `Step = 1` 的两次输出连收敛判据与总能量都完全相同）。
   - **要确证需要**：一份同版本 CP2K、`MAX_SCF` 收到不收敛时的真实 `.out`（本仓 `cases/` 与两个真实
     `cp2k.out` 都是 `PRINT_LEVEL` 较低/已收敛的输出，没有这种"未收敛 SCF 表"可对照）。
   - **更正记录**：原文猜"**抽取重复**（pdfplumber 把跨栏/跨页的同一行重复输出），**不是 CP2K 真的打印了两遍**"。
     **前半句被推翻**（该页是单栏，且三组参数一致）；后半句仍未定。

4. **T17 P3 的 `BAND TYPE OPTIMIZATION = SD` 究竟是不是首步特例**
   - ✅ **已定案：是 CP2K 的正常首步行为（`OPT_TYPE DIIS` 前先做 SD 步），既不是"输入输出不一致"，也不是抽取问题。**
   - **依据**：
     · `python _kw_probe.py MOTION/BAND/OPTIMIZE_BAND/DIIS/MAX_SD_STEPS`
       → `DEFAULT_VALUE : 1`，描述 `Specify the maximum number of SD steps to perform before switching on DIIS
       (the minimum number will always be equal to N_DIIS).`；T17 P2 **没有**设 `MAX_SD_STEPS` ⇒ 取默认 1。
     · CP2K 源码 `src/motion/neb_methods.F`：行 399（进入 `neb_diis`）与行 451（主循环内）都先写
       `neb_env%opt_type_label = "SD"`；行 477–481
       `diis_on = accept_diis_step(istep > max_sd_steps, …)` / `IF (diis_on) THEN neb_env%opt_type_label = "DIIS" END IF`
       ⇒ **只有 DIIS 真正被接受之后标签才变 `DIIS`**。
     · `src/motion/neb_io.F` 行 412–413 才是打印点：
       `WRITE (output_unit, FMT='(A,T61,A)') ' BAND TYPE OPTIMIZATION        =', ADJUSTR(neb_env%opt_type_label(1:20))`
     · 旁证：T17 P2 的 `OPT_TYPE DIIS` 与 `&DIIS MAX_STEPS 1000` 都在输入里（行 105–110），而输出这段是
       `STEP NUMBER = 1`（行 150）⇒ **首步标 `SD` 正是默认行为**。
   - 源码 URL：<https://github.com/cp2k/cp2k/blob/master/src/motion/neb_methods.F> 、
     <https://github.com/cp2k/cp2k/blob/master/src/motion/neb_io.F>
   - **更正记录**：原文写"输入 `OPT_TYPE DIIS`，输出首段却写 `SD`…**两者不一致**"，
     并在 §3 第 8 行建议"**不要拿输出这一行去判断优化器**"。**前半句错**（这是正常的 SD 起步）；
     后半句的**实用建议仍然对**（首步就是 SD）。
   - **⇒ 这也解释了 §3 第 8 行的疑问**：`STEP NUMBER = 1` 那一段写 `SD` 是**预期输出**，不是冲突。

5. **T17 的 S_N2 能垒数值未在文中给出**
   - ✅ **已定案：原文确实从头到尾没给能垒数值（这是留给读者的 TASK），能垒只能自算。**
   - **依据**：
     · T17 P3 只给 `STEP NUMBER = 1` 的 10 个 replica 能量（行 155–157）与"TASK 2 … Find the activation
       barrier of the reaction in eV."（行 162–164）；
     · T17 P6 只给 1000 K 的 FES 文字描述（"distance 1.8 Å" / "around distance 2.5 Å"，行 313–314）
       与 400/800/1200/1600 K 的 TASK（行 315–319）；**全文无"能垒 = X eV"**。
   - **自算复核（本层自算，不是原文数字）**：取行 155–157 的最大值与端点值，
     `-24.800607 − (−24.815004) = 0.014397 Ha × 27.2114 = **0.3918 eV**`，与 §4.13 的 ≈0.392 eV 一致。
     ⚠️ 该值只用 10 个 replica 的离散能量取样，**不是收敛的 MEP 鞍点能**。

6. **T17 的 `&RESTRAINT K 0.005` 的单位与语义**
   - ✅ **已定案（并更正原文两处假设）**：
     · 语义：**谐振式软约束** `E = K·(X − TARGET)²`（**不是**硬约束）、`K` 为**力常数**（real 型，默认 `0.0`）；
     · 单位：`K` 与 `TARGET` 都是 `internal_cp2k`，即**该 CV 的内部单位**；对 `&DISTANCE` CV ⇒ **长度用 bohr**、
       **`K` 的单位是 hartree/bohr²**。
   - **依据**：
     · `python _kw_probe.py MOTION/CONSTRAINT/COLLECTIVE/RESTRAINT/K`
       → `DEFAULT_VALUE : 0.00000000E+000` / `DEFAULT_UNIT : internal_cp2k` /
       `DESCRIPTION : Specifies the force constant for the harmonic restraint.
       The functional form for the restraint is: K*(X-TARGET)^2.`
     · `python _kw_probe.py FORCE_EVAL/... ` 同族：`_kw_probe.py --section MOTION/CONSTRAINT/COLLECTIVE`
       列出 `COLVAR / MOLECULE / MOLNAME / INTERMOLECULAR / TARGET / TARGET_GROWTH / TARGET_LIMIT / EXCLUDE_QM /
       EXCLUDE_MM / &RESTRAINT`，其中 `TARGET` 也是 `unit=internal_cp2k`。
     · 官方手册 `TARGET` 的原文：**"Specifies the target value of the constrained collective variable
       (units depend on the colvar)."** —— <https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/CONSTRAINT/COLLECTIVE.html>
     · CP2K 源码 `src/input_cp2k_constraints.F` 行 292–296：`name="TARGET"` 且 **`unit_str="internal_cp2k"`**
       （`internal_cp2k` = 不做单位换算）。
     · CP2K 源码 `src/restraint.F` 行 557–587（`restraint_colv_low`）：`tab = diff_colvar(colvar, targ)`、
       **`energy = energy + k*tab**2`**、`force(:,ind) = force(:,ind) - 2.0_dp*k*tab*dsdr` ⇒ 与手册的 `K*(X-TARGET)^2` 逐字对应。
     · **CV 的单位是 bohr（教程自证）**：T17 P5 的 Python 行 284 定义 `bohr_2_angstrom = 0.529177`，
       行 291–292 `d1 = colvar_raw[:, 1] * bohr_2_angstrom` / `d2 = colvar_raw[:, 2] * bohr_2_angstrom`，
       再把 `d1 [ang]` 画出来；T17 P6 行 314 才得到"键合的 Cl **距离 1.8 Å**"这个物理正确值。
       ⇒ **`ch3f-COLVAR.metadynLog` 里的 CV 是 bohr**，故 `&COLLECTIVE ... TARGET 1.8`（**未给单位**）
       = **1.8 bohr = 0.9525 Å**，**不是** 1.8 Å。
     · 旁证：`SCALE`（别名 `WIDTH`）只是**高斯山宽的缩放因子**（手册原文给出 `EXP[-0.5*((ss-ss0)/SCALE)^2]`），
       且本输入 `DO_HILLS .FALSE.` ⇒ **`SCALE 0.2` 不影响 CV 的数值与单位**。
       <https://manual.cp2k.org/trunk/CP2K_INPUT/MOTION/FREE_ENERGY/METADYN/METAVAR.html>
   - **定量（"这个约束有多硬"）**：`E = K·ΔX²`、回复力 `F = 2K·ΔX`，`K = 0.005 Ha/bohr²`：
     | ΔX | E（hartree） | E（eV） | F（eV/Å） |
     |---|---|---|---|
     | 0.5 bohr（0.265 Å） | 1.25e-3 | **0.034** | **0.257** |
     | 1.0 bohr（0.529 Å） | 5.00e-3 | **0.136** | **0.514** |
     | 1.6 bohr（0.847 Å） | 1.28e-2 | **0.348** | **0.823** |
     对照 1000 K 的 `kT = 0.0862 eV` ⇒ **软约束**（ΔX≈1.6 bohr 才到约 4 kT）。
   - **更正记录（两处）**：
     ① 原文"**`TARGET 1.8` 也未给单位（按 CP2K 默认应为 Å）**"——**错**。CP2K 的默认**不是 Å**，
        而是"该 CV 的内部单位"；`&DISTANCE` 用 bohr。**要写 Å 必须显式写 `TARGET [angstrom] 1.8`**
        （官方手册自己在示例里就是这么写的：`TARGET [angstrom] 2.0`，
        <https://manual.cp2k.org/trunk/methods/sampling/constrained_dynamics.html>）。
        ⇒ **T17 这份 `md.inp` 的 `TARGET 1.8` 与其叙述的"1.8 Å 键合极小"不一致，是一个应当显式带单位的坑。**
     ② 原文对 G 层的判断**是对的**：G 层 `17_…` §2.1 讲的 `hartree/bohr` 确属 **`LAGRANGE_MULTIPLIERS` 输出文件**
        （手册原文："A distance constraint therefore produces a multiplier in hartree/bohr"），
        **不适用于 `&RESTRAINT/K`**；本轮把 `K` 的单位补齐如上。

7. **T16 的 `ENERGY_GAP 0.001` 是否是水的合理值**
   - ✅ **已定案：它是**预条件参数**，不是物理 HOMO–LUMO 间隙；`0.001` 正好落在官方推荐用法内。**
   - **依据**：
     · `python _kw_probe.py --find ENERGY_GAP` → 命中 `FORCE_EVAL/DFT/SCF/OT`，**默认 `-1.0`**，官方描述原文：
       "Should be an estimate for the energy gap [a.u.] (HOMO-LUMO) and is used in preconditioning, especially
       effective with the **FULL_ALL** preconditioner, in which case it **should be an underestimate of the gap
       (can be a small number, e.g. 0.002)**. FULL_SINGLE_INVERSE takes it as lower bound (values below 0.05 can
       cause stability issues). In general, higher values will tame the preconditioner in case of poor initial
       guesses. A negative value will leave the choice to CP2K depending on type of preconditioner."
       另一处（`SCF/DIAGONALIZATION/DAVIDSON`）的描述直接写 "**0.001 doing normally fine**"。
     · T16 P3 行 178–186 用的正是 `&OT ON / MINIMIZER DIIS / PRECONDITIONER FULL_ALL / ENERGY_GAP 0.001`
       ⇒ **`FULL_ALL` + 故意取小**，与官方描述逐条对上。
   - **⇒ 不要拿它跟液态水的真实间隙比**（水 ≈ 8–9 eV ≈ 0.3 Ha）；这里要的是**下界估计**，取小是对的。
   - **更正记录**：原文"G 层 `03_scf_convergence.md` §1.4 只列了 `PRECONDITIONER`/`MINIMIZER`/`ALGORITHM`/`LINESEARCH`
     四个关键字，**没有 `ENERGY_GAP`**"——这是**事实正确但推断有偏**：`ENERGY_GAP` 属于 `&SCF &OT`
     （不在那四个之列），所以 G 层没列它**不是缺口**，只是编排范围。原文"它的语义与取值建议需回官方
     Input Reference 核"现已核完，见上。

8. **T15 的 `EPS_PGF_ORB` 在 `&SCREENING` 里怎么设**
   - ✅ **已定案：`EPS_PGF_ORB` 不在 `&SCREENING`，它在 `&QS`；Topics 清单只是把三个"保 SCF 稳定"的参数并列。**
     （即**原文"大概率 Topics 清单里那个应属 `&QS`"的猜测被证实**。）
   - **依据**：
     · `python _kw_probe.py --find EPS_PGF_ORB` → 15 处命中，其中**唯一的 QS 层**是
       `FORCE_EVAL/DFT/QS`：`Sets precision of the overlap matrix elements. Overrides SQRT(EPS_DEFAULT) value`；
       另外 13 处在 `.../XC/HF/RI`（"Sets precision of the integral tensors."，默认 1e-5）。
     · `python _kw_probe.py --find EPS_SCHWARZ` / `--find SCREEN_ON_INITIAL_P` → 宿主都是
       `FORCE_EVAL/DFT/XC/HF/SCREENING`（默认分别 `1.0E-010` / `F`）⇒ **`&SCREENING` 的父段是 `&XC &HF`**。
     · `python _kw_probe.py --section FORCE_EVAL/DFT/QS | Select-String "SCREEN|EPS_"` → `&QS` 下**没有** `SCREENING` 子段，
       只有一串 `EPS_*`（含 `EPS_PGF_ORB`，默认 "-" 即继承 `SQRT(EPS_DEFAULT)`）。
     · T15 P2 行 92–93 的 Topics 原文是
       "`EPS_SCHWARZ`, `EPS_PGF_ORB`, `SCREEN_ON_INITIAL_P` : parameters to guarantee stable SCF."，
       而它给出的 `&SCREENING` 块（行 61–66）**只有** `EPS_SCHWARZ` 与 `SCREEN_ON_INITIAL_P` ⇒ **输入本身没设错**。
   - **⇒ 落地写法**：`&DFT &QS … EPS_PGF_ORB 1.0E-30 … &END QS`（或干脆不写，让它继承 `SQRT(EPS_DEFAULT)`）。

9. **T13 的 IR 谱用"经典点电荷"近似的适用范围**
   - ⚠️ **未能确证，已排除以下可能**：
     ① **官方 manual 的 `methods/properties/infrared.html` 是占位页**——本轮实取该页，**无正文、无适用条件判据**
        （与 G 层 `06_properties.md` §1.2 / `18_…` §8 的登记一致）；
     ② **官方 CP2K 红外练习也不是这条路**——`exercises:2018_ethz_mmm:infrared_2018` 用的是
        `&DFT &PRINT &MOMENTS PERIODIC FALSE`（由电子密度算偶极）+ 单独的模式分析，
        另一条任务才用 MD 的偶极自相关；**它同样没给"固定电荷什么时候不行"的判据**。
     ③ 三份教材（T13/T14/T15）都没写"context 的边界"。
   - **仍不确定的是**：T13 那句 "In this context the approximation is reasonable" 里的 **"context" 到底划在哪**——
     即哪些体系不能把偶极写成 `Σ qᵢ rᵢ`（固定电荷），必须回到 Wannier 中心 / 密度积分。
   - **要确证需要**：官方（或教材作者）对"固定电荷偶极近似"的误差来源与适用条件的**明文**表述；
     本轮在 cp2k.org / manual.cp2k.org 上找不到，不敢从物理常识外推成结论。
   - **已查到的相关事实**：T13 P3 行 148–159 原文把 Wannier 中心路线标为 "out of scope of the current
     tutorial (TODO: find link)"、改用 `charges.dat`（`O -1.2` / `H +0.6`）、声明 "In this context the
     approximation is reasonable"，并把检验交给读者（"Where do you expect the OH stretch to be? Is this
     reproduced?"），另注"Lower frequencies need longer trajectories…at the very least 10 times the period"。

10. **T14 的 `mode1.xyz` / `mode2.xyz` 的元素序列是否真的一致**
    - ✅ **已定案（实测复核通过，原文的"已解决"部分确认无误）。**
    - **依据（只读 T14 的 txt，解析两块内嵌坐标）**：T14 行 268–269 与行 394–395 分别是两份 xyz 的
      文件名行 + 首行 `116`；逐行解析后：
      · 两者 `N = 116`（各解析出 116 行坐标）；
      · 成分都是 **Ti 36 / O 74 / C 2 / H 4**；
      · **元素序列逐位完全相同 = True**（脚本输出 `element sequences identical (position by position)? True`）；
      · **坐标不同 = True**（`coordinates identical? False`）。
      切分也复核了：**原子 109–116 = C₂H₄O₂（乙酸）**、**1–108 = TiO₂ slab（36 Ti + 72 O）**。
    - **残留（仍不是原文文字）**：教程**从未说明**哪个文件是单齿、哪个是双齿。
      原文只有 T14 P1 行 24 的 "two possible binding modes" 一句，**并没有把这两个模式与两个文件对应起来**。
      也没给"删哪些原子得到子体系"的操作步骤：T14 P2 行 75–76 只说
      "just remove slab's coordinates" / "just remove the acid's coordinates"。
      **⇒ 原子 1–108 / 109–116 的切分是本文实测得出的，不是原文文字**（已在 §4 标注）。

11. **T10 P7 的 `SUM OF ATOMIC FORCES` 第四个数字**
    - ✅ **已定案：第 4 个数 = **净力矢量的模** `SQRT(SUM(total_force(:)**2))`（不是逐原子力模之和）。**
    - **依据（CP2K 源码 `src/force_env_utils.F`，`SUBROUTINE write_forces_to_file`）**：
      · 行 591 打印表头：`uc_label//" FORCES in [a.u.]"`、`"# Atom"`、`"Kind"`、`"Element"`、`"X"`、`"Y"`、`"Z"`
        （`uc_label` 由 `label="Atomic"` 转大写 ⇒ 正是 `ATOMIC FORCES in [a.u.]`）；
      · 行 580 `fmtstr3 = "(T2,A,T28,4(1X,F  .  ))"` ⇒ **四个 F 格式数**；
      · 行 592 / 607 `total_force(1:3)` 逐原子累加 `f(1:3)`（**矢量和**）；
      · 行 609–610：
        `WRITE (UNIT=iw, FMT=fmtstr3) "SUM OF "//uc_label//" FORCES", total_force(1:3), SQRT(SUM(total_force(:)**2))`
        ⇒ 第 4 个数就是 `|Σᵢ fᵢ|`。
      · 单位随表头 `[a.u.]` = **hartree/bohr**；同族还有 `GRAND TOTAL FORCE`（行 616–617，同样 4 个数）。
    - 源码 URL：<https://github.com/cp2k/cp2k/blob/master/src/force_env_utils.F>
    - **含义**：这是**净力**（应趋零的收敛量），**与"原子力模之和"完全不是一回事**；
      T10 行 382 该值 `0.00000000` 正说明体系已弛豫。
      **⇒ 照抄时把 4 个数都留下，并可放心解读为"净力 → 0"。**（原文"勿臆测"现可撤下。）

12. **T12 里 `NGRIDS 4` 与"最细层 = grid 1"的编号约定**
    - ✅ **已定案：`grid 1` = `CUTOFF` = **最细**；编号与"1 号最小"的直觉相反。**
    - **依据（三重互证）**：
      ① **教材原文自己说了**：T12 行 320–324 "2720 product Gaussians has been distributed to
         **grid level 1, the finest level**, 5000 for level 2, 2760 for level 3 and 16 for level 4,
         **the coarsest**."；
      ② **数值算术自洽**：T12 行 315–318 的
         `count for grid 1: 2720 cutoff [a.u.] 50.00` / `grid 2: … 16.67` / `grid 3: … 5.56` / `grid 4: … 1.85`，
         而同页说明该次计算 `CUTOFF = 100 Ry`（行 320–321）⇒ `100 Ry = 50 Ha` **正是 grid 1**，
         其后 `100/3 = 33.33 Ry = 16.67 Ha`、`100/9 = 11.11 Ry = 5.56 Ha`、`100/27 = 3.70 Ry = 1.85 Ha`；
      ③ 与官方输入参考一致：`python _kw_probe.py --section FORCE_EVAL/DFT/MGRID` →
         `NGRIDS` 默认 **4**、`CUTOFF` 默认 280 Ry、**`PROGRESSION_FACTOR` 默认 `3.0`**
         （`Factor used to find the cutoff of the multigrids that where not given explicitly`）。
    - **⇒ 抽样脚本里 `awk 'NR == igrid'` 的 1→最细顺序是对的**，原文判定无需修改。

---

## 附：本批 8 份的文件清单与页码对照

| 编号 | txt 文件 | 行数 | 页 | 末行来源标记 |
|---|---|---|---|---|
| T10 | `T10_howto_static.txt` | 444 | 8 | `howto/static_calculation.txt · Last modified: 2019/03/10 22:24` |
| T11 | `T11_howto_geo_opt.txt` | 285 | 5 | `howto/geometry_optimisation.txt · Last modified: 2018/01/25 11:52` |
| T12 | `T12_howto_cutoff.txt` | 541 | 10 | `howto/converging_cutoff.txt · Last modified: 2018/06/07 19:26` |
| T13 | `T13_ex2016_aimd.txt` | 565 | 9 | `exercises/2016_summer_school/aimd.txt · Last modified: 2016/08/23 06:53 by ibethune` |
| T14 | `T14_ex2016_gga.txt` | 520 | 10 | `exercises/2016_summer_school/gga.txt · Last modified: 2016/08/23 06:51 by ibethune` |
| T15 | `T15_ex2016_hfx.txt` | 405 | 7 | `exercises/2016_summer_school/hfx.txt · Last modified: 2016/08/23 06:54 by ibethune` |
| T16 | `T16_ex2018_scf_setup.txt` | 207 | 4 | `events/2018_summer_school/scf_setup.txt · Last modified: 2018/06/17 09:39 by mwatkins` |
| T17 | `T17_ex2020_uzh_neb.txt` | 320 | 6 | `exercises/2020_uzh_acpc2/ex03.txt · Last modified: 2020/04/21 09:54 by jglan` |

> **合计 59 页 / 3287 行 / 130,962 字节 ≈ 128 KB**（含 T14 的 232 行坐标与 T13 的 192 行坐标）。
> （行数 = 各 txt 的换行符计数，与 `read` 工具报告的 total 一致；字节数取自文件大小。）
> 与 G 层的对应关系：**T10 → `01_global_and_units.md` §5**；**T12 → `03_scf_convergence.md` §2**；
> **T17（NEB 半）→ `24_official_exercises.md` §1.2**；**T11 → `05_optimization.md`（部分）**；
> **T13/T14/T15/T16 → G 层仅词条级登记，无正文**。
