# 01 · GPW / GAPW 方法（H 层精读笔记）

> **精读对象**（逐页读完，无抽样）：
> - `txt/T01_gpw_hutter.txt` —— **73 页**，Jürg Hutter《Gaussian and Plane Waves Method》(GPW)，
>   CP2K 官方 workshop 教材（原文件 `【gpw-…】hutter-gpw.pdf`）。本笔记简称 **T01 P*n***。
> - `txt/T19_iannuzzi_zurich2017.txt` —— **43 页**，Marcella Iannuzzi《CP2K: GPW and GAPW》，
>   Zurich 2017 CP2K tutorial（原文件 `【GPW和GAPW-…】iannuzzi_cp2k-tutorial-zurich2017.pdf`）。简称 **T19 P*n***。
>
> **定位提醒**：G 层（`references/official/`）只把这两份 PDF 当"外部资源标题"登记
> （`10_features_resources.md` 课程清单），**未收录教材内容**。因此本文件里凡是
> "官方默认值 / 关键字语法"一律只写指针（如"见 G 层 `02_dft_methods.md §4.6`"），
> 只写教材**自己讲出来的道理、数字与配方**。
>
> **抽取假象**：pdfplumber 对两端对齐排版丢词间空格（`CP2Kversion7.0`、`AhybridGaussianandplanewavedensityfunctionalscheme`），
> 本笔记按语义还原。另外 T19 原 txt 里有 **240 个 NUL 字节**（公式字体把空格提成 `\x00`，
> 会被读文件工具判为二进制），**已修**：`extract_tutorials.py` 增加 `clean()` 去掉 NUL，
> 并重新抽取了 T04/T05/T19/T23 四份受影响的文件（详见文末「附」）。

---

## 1. 这两份材料教什么

**T01（Hutter，73 页）——一句话**：从 KS-DFT 与 LCAO 出发，讲清楚
**GPW 为什么要把"高斯基组 + 辅助平面波 + 多重实空间网格"三样东西拼起来**，
以及这套拼法在数值上究竟付出了什么代价（ripples、负密度、筛选阈值），
最后落到赝势、MOLOPT 基组与 OT/线性标度这些"能跑起来"的部件。

- 它不是 howto，而是**方法学推导课**：第 4–13 页搭 KS-DFT 与 GTO 的账，
  第 12–13、21–23、25–26 页把 GPW 的能量表达式一项一项推出来，
  第 26–37 页专讲实现层的筛选与网格误差，第 41–56 页讲赝势与基组，第 57–72 页讲求解器与标度。
- 它**明确点出了 GPW 的软肋**：实空间网格的平移不变性破坏会产生 "ripples"（P24）、
  Fourier 插值会在低密度区给出**负密度**（P33）、阈值取不好会让 overlap 矩阵 Cholesky 分解失败（P27）。
  这三条在 CP2K 官方手册的对应页里**没有**，是本层最硬的增量。
- 它给出的**唯一一组带机时的对照数据**（P37，64 水分子 / LDA / 24 核）是判断
  "CUTOFF 该花在哪、NGRIDS 值不值"的原始依据。
- 后半段（P57–P72）的 OT、DIIS、预条件、线性标度 `P = sign(S⁻¹(H−μI))S⁻¹` 与 DBCSR
  **不属于 GPW 特有内容**，本笔记只登记页码，不展开。

**T19（Iannuzzi，43 页）——一句话**：用同一套代数语言把 **GPW 与 GAPW 的公式并排写出来**，
并在 GPW 侧补上"密度从 GTO 到网格怎么走、多重网格到底在做什么"的完整实现细节，
在 GAPW 侧给出**密度分区（硬/软）的匹配条件、补偿电荷、以及一份可直接照抄的 GAPW 输入卡**。

- 前 18 页是 GPW 的实现剖面：解析积分（P7）、GTH 赝势的分离形式（P11）、
  静电能的 Ewald 式分解（P12–P13）、实空间网格与 collocation/screening 循环（P14）、
  多重网格的分配规则与实测（P15–P16）、GPW 能量泛函与"线性标度 KS 矩阵构建"（P17），
  并以一份完整 CP2K 输入卡收尾（P18）。
- 第 19–25 页是 GAPW：从 APW/LAPW/LMTO/PAW 的方法谱系（P19）讲到
  **密度分区 n = ñ + Σ_A(n_A − ñ_A)** 与**两条匹配条件**（P20），
  再到局域密度/基组投影（P21）、XC 与静电能的 GAPW 分解（P22–P24）与输入卡（P25）。
- 第 26–33 页（能量最小化、对角化、OT、线性标度）与 **36–43 页（金属 SCF、smearing、
  特征值求解器 ELPA 论文截图）已越出 GPW/GAPW 主题**，本笔记只在 §2 登记页码，
  并在 §7 标注"未提取为要点"。

---

## 2. 逐节要点

### 2.1 T01 —— GPW 方法（Hutter）

**A. 铺垫：KS-DFT 与两族基组（T01 P4–P11）**

- `T01 P4–P6` KS-DFT 三定理（Hohenberg–Kohn I/II + Kohn–Sham）与能量五项：
  动能、外势（电子-核）、Hartree、XC，外加**轨道正交归一约束**与**电子数约束**。
  P6 把每一项的显式形式列全（`E_kin = −½Σ_i f_i(Φ_i|∇²|Φ_i)` 等）。
- `T01 P7` LCAO 记账：基组展开 → overlap `S_αβ` → 正交归一条件 `c†Sc = δ` →
  密度矩阵 `P_αβ = Σ_i f_i c_αi c*_βi` → 密度 `ρ(r) = Σ_αβ P_αβ φ_α φ*_β`。
  **这一页是后面所有 GPW 公式的符号表**。
- `T01 P8–P10` GTO 本身：原始函数 `φ(r) = r^l Y_lm exp[−α(r−A)²]`、收缩 `χ = Σ_k d_k φ_k`
  （收缩系数与指数**固定**，只对同一角动量收缩）。
  优点列了 5 条，其中**与我们直接相关的两条**：
  "**Optimal for regular grids**"与"**Fourier transform is again a Gaussian**"；
  缺点 5 条里最关键的是"**Non-orthogonal basis**"与"linear dependencies for larger basis sets"。
- `T01 P11` KS-DFT 用 GTO 基组时的积分分类，**这一页是整个 GPW 设计的动机页**：
  | 积分 | 处理方式 |
  |---|---|
  | 动能、外势、overlap | **解析** |
  | Coulomb（4 中心 ERI，Mulliken 记法 `(αβ\|γδ)`） | 解析，但**是 CPU 与内存瓶颈** |
  | XC 能量与积分 | **数值积分** |
  → 一句话结论：**瓶颈在 ERI**。

**B. GPW 的核心推导：把 ERI 换成 FFT（T01 P12–P25）**

- `T01 P12` **目标：避免计算 ERI**。做法是把三项静电作用**合并成一个总静电能**
  （电子-电子 + 电子-核 + 核-核），一次处理。
- `T01 P13` 关键技巧：引入**高斯原子电荷** `ρ_A(r) = Z_A(α/π)^{3/2} exp[−α(r−A)²]`，
  构造总电荷 `ρ_tot = ρ_e + Σ_A ρ_A`，于是静电能 = **长程项（ρ_tot 的 Hartree）+ 短程项
  （用 `erfc` 的电子-核吸引）+ 短程对相互作用 `E_pair(R_A−R_B)` − 自相互作用 `Σ_A E_self`**。
  这正是 Ewald 分割的 GPW 版本。
- `T01 P14` PBC：Bloch 态、k 点采样、**Γ 点**（单点 (0,0,0) 积分）、
  以及周期化内积 `(α|O|β) → Σ_L (α(0)|O|β(L))`。
- `T01 P15–P18` 平面波与倒空间：`φ(r) = Ω^{−1/2} exp[iG·r]`（正交、与原子位置无关、
  天然周期，缺点是**函数数目多**）；盒子矩阵 `h = [a₁,a₂,a₃]`、`Ω = det h`；
  倒格 `2π(hᵗ)⁻¹ = [b₁,b₂,b₃]`，`b_i·a_j = 2πδ_ij`。
- `T01 P19` **cutoff 与基组大小的定量关系**：
  `½G² ≤ E_cut`，且 **`N_PW ≈ (Ω/2π²)·E_cut^{3/2}` [a.u.]**，
  即"**基组大小只取决于盒子体积与 cutoff**"（后面 §3 的推理链要用这条）。
- `T01 P20` **实空间网格的理论下限 = 采样定理**：区间 `Δ = L/N`，Nyquist 临界频率 `f_c = 1/(2Δ)`；
  "给定平面波 cutoff，存在一个**最小**的等距实空间网格点数，能给出同等精度"。
  再引出 FFT：`ψ(G) ↔ ψ(R)` 信息等价，`N²` vs `N log N`。
- `T01 P21` **Parseval 定理**给出积分在实空间与倒空间等价：
  `Ω Σ_G A*(G)B(G) = (Ω/N) Σ_i A*(R_i)B(R_i)` —— 这就是 GPW 可以"挑便宜的表示算"的数学许可。
- `T01 P22` 长程项：解 Poisson 方程 `∇²V_H = −4πρ_tot`，得 `V_H(G) = (4π/G²)ρ_tot(G)`，
  故 `E_LRT = (2π/Ω) Σ_G |ρ_tot(G)|²/G²`。
- `T01 P23` XC 项：`ε_xc(G)` **在 G 空间不是局域的**，所以必须回实空间算；
  教材的做法是定义有限 Fourier 变换 `Ẽ_xc(G)`，在网格上算 `E_xc = (Ω/N_xN_yN_z) Σ_R ε_xc(R)ρ(R)`。
- `T01 P24` **"ripples"（波纹）**：**只有按网格间距整数倍平移，总能量才不变**；
  于是能量超曲面被引入了一层小的调制。**这是 GPW 数值误差的本质描述**（§3 重点）。
- `T01 P25` **GPW 能量表达式（本课的中心公式）**：
  `E_KS^GPW = E_kin(P) + δE_ext(P) + E_xc(ρ̃) + E_H(ρ̃) + E_ovrl − E_self`
  其中高斯部分 `Φ_i = Σ_α c_αi φ_α`、`P_αβ = Σ_i f_i c_αi c_βi`；
  PW 部分 `ρ̃(G) = Σ_αβ (φ_α·φ_β)(G)`、`ρ̃_tot(G) = ρ̃(G) + Σ_A ρ_A(G)`。
  两条**关键的变分性说明**：
  ① `E_KS^GPW` **只对 GTO 系数 c_αi 变分**（辅助 PW 基组不引入新的变分自由度）；
  ② `ρ̃(G)` 同时是 `c_αi` 与辅助 PW 基组的函数。

**C. 实现层：筛选、网格、误差（T01 P26–P37）**

- `T01 P26` **高效计算 = 三级 screening**：
  ① 永远用**原始高斯**，解析积分 → 按距离 `R = A − B` 做**距离筛选**，得到 overlap `S_αβ`
  与力矩阵 `T_αβ` 的**稀疏模式**；
  ② 实空间密度 `ρ(R) = Σ P_αβ φ_α(R)φ_β(R)` → FFT → `ρ̃(G)`，
     只有落在 `S_αβ` 稀疏模式内的 `P_αβ` 才需要算；
  ③ `φ_αβ(R) ≠ 0` 的**距离（径向）筛选**。
- `T01 P27` **筛选阈值由 `EPS_DEFAULT` 统一控制**（`CP2K_INPUT / FORCE_EVAL / DFT / QS`），
  并列出**两类典型故障**：
  - **overlap 矩阵 Cholesky 分解失败** ← 基组条件数 × `EPS_DEFAULT` 太大；
  - **实空间网格上电荷不准** ← PW cutoff 太低 和/或 `EPS_DEFAULT` 太大（实质是 `φ_αβ` 的延展被截掉）。
- `T01 P28` 有限 cutoff + 计算盒子 ⇒ 定义实空间网格 `{R}`。
- `T01 P29` 高斯 ↔ 平面波的一对 Fourier 变换：
  `(α/π)^{3/4} exp(−αr²) ⇄ (α/π)^{3/4}·(π/α)^{3/2} exp(−G²/4α)`，
  给出两条性质：**R 空间高效筛选** + **积分的指数收敛**。
- `T01 P30` **高斯基函数积分到底要多少点（硬数字）**：
  "对**指数为 1** 的高斯函数，要达到 **10⁻¹⁰** 的精度，需要**积分范围 10 bohr**、
  **cutoff 25 Ry**，结果是 **22 个积分点**（每维），约 **5000 个积分点/积分批次**"。
  T19 P15 复述了同一组数字。
- `T01 P31–P32` **Multigrid 与 PW cutoff**：cutoff 与 multigrid 设置共同决定
  密度展开的精度与效率，节名 `&MGRID ... &END MGRID`，列出 6 个关键字及其默认值：
  `CUTOFF`（默认 **280 Ry**）、`REL_CUTOFF`（**指数为 1 的高斯所用最小 cutoff，默认 40 Ry**）、
  `NGRIDS`（默认 **4**）、`PROGRESSION_FACTOR`（默认 **3**）、
  `MULTIGRID_SET`（默认 F）、`MULTIGRID_CUTOFF`（逐网格 cutoff 列表）。
  > 默认值语义以 G 层为准（`official/20_input_reference_tree.md`、`official/01_global_and_units.md`），
  > 本条只是教材的复述与**理由**：`REL_CUTOFF` 的定义对象是"**指数为 1 的高斯**"。
- `T01 P33` **XC 精度与网格的三条警告**：
  ① XC 能量精度由**密度展开精度 + 总 PW cutoff** 决定；
  ② CP2K **从密度的平面波展开求密度梯度**；
  ③ **Fourier 插值会在低密度区产生负密度，而 multigrid 会放大这个问题**（原文加重号）。
  再按泛函阶梯给出对密度的敏感度：LDA 用 `ρ`，GGA 用 `(∇ρ)²/ρ^{4/3}`，meta 用 `τ`；
  对应三个关键字 **`DENSITY_CUTOFF` / `GRADIENT_CUTOFF` / `TAU_CUTOFF`**（在 `FORCE_EVAL/DFT/XC`），
  更多高级选项在 **`FORCE_EVAL/DFT/XC/XC_GRID`**。
- `T01 P34` **Coulomb 势的完整链路**：
  `P → ρ(R) −FFT→ ρ(G) → V_H(G) = ρ(G)/G² −FFT→ V_H(R) → V_μν`，
  总代价 `O(n log n)`；两端都是**同一套 `χ̄_μν(R) = χ_μ(R)χ_ν(R)` 的稀疏求和**
  （`ρ(R) = Σ P_μν χ̄_μν`、`V_μν = Σ_R V(R) χ̄_μν`），所以筛选可以复用。
- `T01 P35–P36` 两张图的标题即为结论：**PW 展开对 Coulomb 能量的精度**、
  **PW 展开对 XC 能量的精度（PBE 泛函，体相硅）**（图形内容未随文本抽出）。
- `T01 P37` **唯一一组带机时的对照表**（64 个水分子、**2560 个基函数**、**LDA**、**24 核**）：

  | `EPS_DEFAULT` | cutoff (Ry) | ngrids | time (s) | Energy (Ha) |
  |---|---|---|---|---|
  | −12 | 280 (30) | 4 | 1.5 | x.0377660911 |
  | −12 | 400 (60) | 4 | 2.7 | x.0368292349 |
  | −12 | 400 (60) | 1 | 21.9 | x.0368292282 |
  | −12 | 800 (60) | 6 | 3.0 | x.0371244786 |
  | −12 | 800 (60) | 4 | 3.0 | x.0371244689 |
  | −12 | 800 (60) | 1 | 76.5 | x.0371244096 |
  | −8 | 1600 (60) | 6 | 3.7 | x.0371421086 |
  | −10 | 1600 (60) | 6 | 4.7 | x.0371296795 |
  | −12 | 1600 (60) | 6 | 4.7 | x.0371288794 |
  | −14 | 1600 (60) | 6 | 4.9 | x.0371287675 |

  （"x." 是原幻灯片被遮住的整数位；对照 E 层讲师引用的同一张表：CUTOFF 400 + REL_CUTOFF 60 +
  NGRIDS 4 + EPS_DEFAULT −12 → **2.7 s**，见 `pdf_text/MAPPING.md` 行 320 与
  `course_learned.md` §"&MGRID"条，两处数字一致。）
  **本表能读出的三条结论**：
  ① `NGRIDS 1` 是灾难（400/60：**2.7 s → 21.9 s**，约 8 倍；800/60：**3.0 s → 76.5 s**，约 25 倍），
     而能量几乎不变（…2349 vs …2282）——**多网格只影响速度，不影响该档精度**；
  ② 该体系 cutoff 从 280 → 400 Ry 时能量变 9.4×10⁻⁴ Ha（≈0.59 mHa ≈ 0.6 meV/atom 量级，仍未收敛），
     到 1600 Ry 才落到 −12 档的 0.0371288794；
  ③ **网格精度（EPS_DEFAULT）与 cutoff 是两笔账**：1600 Ry 下把 `EPS_DEFAULT` 从 −8 收到 −12，
     能量变 1.3×10⁻⁵ Ha 而机时只从 3.7 s 到 4.7 s；再收到 −14 几乎不变（4.9 s）——
     **即"cutoff 不够"不能靠收紧 EPS 弥补**（−8/1600 与 −12/1600 差 1.3e−5 Ha 是两回事）。

**D. BSSE 与非周期计算（T01 P38–P40）**

- `T01 P38` **BSSE 的机理页**：定域非正交 AO 基组是不完备的，且"**局域完备性取决于原子位置**"，
  团簇里基组比孤立分子更完备 → **束缚态被过度稳定** → 二聚体/表面吸附/结合能被高估。
  给了 Counterpoise 估计式：`E_BSSE ≈ E_A(A+B) + E_B(A+B) − E_A(A) − E_B(B)`（片段取团簇几何）。
- `T01 P39` 液态水中的 BSSE 图（横轴结合能 kcal/mol，纵轴 BSSE）：基组 `DZVP` / `TZV2P` /
  `QZV2P` / `QZV3P(f,d)`，**基组越大 BSSE 越小**（图形数值未随文本抽出）。
- `T01 P40` **非周期体系也能用 PW 算**（解非周期边界条件的 Poisson 方程）：
  球形/柱形/1-d cutoff 有解析解（Marx & Hutter, NIC Series）、
  wavelet 求解器（Genovese et al, JCP 2006, 125 074105）、
  Martyna–Tuckerman 求解器（JCP 1999, 110 2810-2821）。

**E. 赝势与冻芯近似（T01 P41–P52）**

- `T01 P41` 为什么要赝势：**减小基组大小**（提速）、**减少电子数**（减自由度）、
  **部分纳入相对论效应**。
- `T01 P42` 冻芯近似：把不活跃电子自由度替成有效势；势要**可加（additive）**且**可迁移（transferable）**；
  "**可加的一般选择就是原子赝势**，可迁移的做法是**只移除芯电子**"。
  在平面波计算里 **core = 全部满壳层**；芯波函数从原子参考计算转入；
  **不同原子的芯电子不重叠**。
- `T01 P43` **剩下的问题（这一页解释了"为什么后面会需要 GAPW 式思路"）**：
  ① 价波函数必须与芯态正交 → **出现节点结构 → 需要很高的 PW cutoff**；
  ② 好的赝势应当给出**无节点（node-less）**函数并把 Pauli 排斥包含进去；
  ③ 赝势替代了芯电子贡献的 Hartree 与 XC 势，而 **XC 泛函是非线性的**：
     `E_XC(ρ_c+ρ_v) ≠ E_XC(ρ_c) + E_XC(ρ_v)`——**该近似假设芯与价不重叠**，
     破例时要用 **non-linear core correction** 修正。
- `T01 P44` 生成赝势的通用配方 4 步：全电子参考计算 → 赝化 `Φ^PS` → 反解势 →
  **unscreening** `V^PS = V − V_H(n_PS) − V_XC(n_PS)`；注意"**`V_i^PS` 是态相关的（state dependent）**"。
- `T01 P45` 价波函数的赝化：在 cutoff 半径 `r_c` 内用**光滑连续**的轨道接续真实轨道（配图）。
- `T01 P46` 半局域赝势 `V^PS(r,r') = Σ_L V_L^PS(r)|Y_L⟩⟨Y_L|` 与
  "**所有 L > L_max 的势都等于 `V_loc^PS`**"的分解，得到
  `V^PS = V_loc^PS(r) + Σ_{L=0}^{L_max} ΔV_L^PS(r)|Y_L⟩⟨Y_L|`。
- `T01 P47–P48` **空白页**（幻灯片为纯图/未提取出任何文本）。
- `T01 P49` Kleinman–Bylander 形式（`1 = Σ_L |φ_L⟩⟨ΔV_Lφ_L| / ⟨φ_LΔV_Lφ_L⟩`）与
  `E_PS = Σ_L Σ_i f_i⟨Φ_i|ΔV_Lφ_L⟩ ω_L ⟨ΔV_Lφ_L|Φ_i⟩`，`ω_L = ⟨φ_LΔV_Lφ_L⟩`；
  并给出**计数代价**："对带 s 与 p 非局域势的原子，这需要算 **4 × 态数** 的 `⟨ΔV_Lφ_L|Φ_i⟩` 积分"。
- `T01 P50` **Dual-space（双空间）赝势 = GTH**：文献 Goedecker 1996 / Hartwigsen 1998 / Krack 2005；
  形式 `V_pp(r) = V_loc(r) + Σ_L Σ_ij |p_i^L⟩h_ij^L⟨p_j^L|`；
  给出 `V_loc(r) = −(Z_ion/r)erf[r̄/√2] + exp[−r̄²/2](C₁+C₂r̄²+C₃r̄⁴+C₄r̄⁶)`，
  投影子 `p_i(r) = N_i r^l exp[−r²/(2r_l²)]`（`r̄ = r/r_c`）。
  **两条对本 skill 有实操意义的性质**：
  ① **完全非局域 ⇒ 解析积分与 FFT 都容易**（这正是它能塞进 GPW 的原因）；
  ② "**高斯形式 + 少数可调参数**"，且**全局优化所有参数去拟合占据与虚轨道的原子轨道能**。
- `T01 P51–P52` **NLCC（非线性芯校正）**：对很多原子（**碱金属、过渡金属**）芯态与价态重叠，
  XC 能量的线性化假设失效。两条出路：把更多态算进价电子（semi-core，**代价：电子更多、cutoff 更高**），
  或**把芯电荷加进价电荷再算 XC**（NLCC，Louie et al., PRB 26, 1738 (1982)）；
  P52 给出定义 `E_xc = E_xc(n + ñ_core)`，`ñ_core(r) = n_core(r)` 当 `r > r₀`。

**F. 基组：MOLOPT（T01 P53–P56）**

- `T01 P53` MOLOPT 的目标 5 条：**同时适合气相与凝聚相/界面**、精度可系统提升、
  适合大尺度模拟、在函数数目少时最优、**良态（well conditioned）**、**弱相互作用下 BSSE 低**。
- `T01 P54` MOLOPT 的基本思想：**一般收缩（generally contracted）+ 含弥散原始函数 + 全分子优化**；
  三条因果：一般收缩 → **没有孤立的弥散函数、良态**；弥散原始函数 → **BSSE 降低**；
  分子优化 → **小而准**。
- `T01 P55` 家族参数表：**一般收缩、所有指数对所有角动量（含极化）共用**；
  **6/7 个原始函数**（赝势、仅价电子）；**大基组是小基组的扩展**；当时覆盖 **H–Rn**：

  | basis | 第一/二周期 | 氢 |
  |---|---|---|
  | m-SZV | 1s1p | 1s |
  | m-DZVP | 2s2p1d | 2s1p |
  | m-TZVP | 3s3p1d | 3s1p |
  | m-TZV2P | 3s3p2d | 3s2p |
  | m-TZV2PX | 3s3p2d1f | 3s2p1d |

- `T01 P56` **条件数 `log κ = log(σ_max/σ_min)`（液相）实测表**（这是"为什么 MOLOPT 良态"的硬证据）：

  | 基组族 | water | BQ/MeOH | acetonitrile |
  |---|---|---|---|
  | SZV | 1.00 | 1.30 | 1.34 |
  | DZVP | 2.97 | 5.11 | 4.15 |
  | TZV2P | 4.46 | 6.89 | 5.69 |
  | QZV3P | 5.64 | 8.66 | 7.46 |
  | aug-DZVP | 10.11 | 11.00 | 9.89 |
  | aug-TZV2P | 12.54 | 13.52 | 14.58 |
  | aug-QZV3P | 15.11 | 13.94 | 14.23 |
  | **m-SZV** | **0.83** | **1.04** | **1.11** |
  | **m-DZVP** | **3.20** | **3.34** | **3.23** |
  | **m-TZV2P** | **4.18** | **4.46** | **4.18** |
  | **m-TZV2PX** | **4.27** | **4.66** | **4.36** |

  → **同尺寸下 MOLOPT 的条件数一律低于常规/弥散基组**（m-TZV2P ≈ TZV2P，而 aug-TZV2P 高出 3 倍）；
  **弥散（aug-）把条件数抬高一个量级**——这正是 P27 所说的"Cholesky 分解失败"风险的来源。

**G. 求解器与标度（T01 P57–P72，非 GPW 特有）**

- `T01 P57` 不动点法（对角化+混合）7 步流程。
- `T01 P58` 直接最小化：Lagrange 函数 `Ẽ_KS[c,Λ] = E_KS(c) − Tr{Λ(c†c−1)}` 与梯度表达式。
- `T01 P59–P60` **OT 方法**：直接优化、约束是线性的；**内存 `MN`、标度 `MN²`**
  （M = 基函数数，N = 占据轨道数）；变量变换 `C(X) = C₀cosU + XU⁻¹sinU`，`U = (XᵗSX)^{1/2}`，
  线性约束 `XᵗSC₀ = 0`；配线搜索与预条件。
- `T01 P61` 空白页。
- `T01 P62–P64` DIIS：在迭代子空间内直接求逆最优条件，构建 `Σc_i = 1` 约束下的线性方程组
  （`b_ij = ⟨e_i|e_j⟩`）；**误差向量**取"到驻点的距离"，AO 基组下 HF/KS 用 Pulay 式
  `{e}_ij = Σ_kl(F_ik P_kl S_lj − S_ik P_kl F_lj)`；GDIIS 用 `e_i = −P g(x_i)`。
- `T01 P65` 预条件：**对直接最小化的收敛至关重要**；`P = M⁻¹` 作用在梯度上；
  `FULL_ALL` 是态相关的，单态近似在内存与 CPU 上更好；**预条件依赖哈密顿量，优化过程中不应更新**；
  **预条件太差时必须重启优化**（即 CP2K 的 outer SCF）。
- `T01 P66` **GPW 计算标度**（N = 占据轨道数=电子数，M = 基函数数）：
  KS 矩阵 `O(M log N)`、密度矩阵（非完备稀疏）`O(MN)`、**OT 优化 `O(MN²)`**。
- `T01 P67–P68` 体系尺寸标度曲线与 **GGA 泛函效率**标尺：**1 ps/day、10 ps/day、50 ps/day** 三档。
- `T01 P69` **线性标度 KS-DFT**：避开矩阵对角化，
  `P = sign(S⁻¹(H − μI))S⁻¹`，用 **Newton–Schultz 迭代** `A_{i+1} = ½A_i(3I − A_i²)` 算 `S⁻¹` 与 `sign(A)`
  ——**只需要矩阵乘法**；由 **DBCSR** 稀疏矩阵乘法库支撑。
- `T01 P70–P71` 线性标度曲线（图）。`T01 P72` PAO-ML（Schütt & VandeVondele, JCTC 2018, 14, 4168）。
- `T01 P73` 封底 `www.cp2k.org`。

### 2.2 T19 —— GPW 与 GAPW（Iannuzzi, Zurich 2017）

**A. 框架与方法谱系（T19 P2–P4）**

- `T19 P2` 基组表示下的 KS 矩阵形式：体系规模记号 `{N_el, M}`、`P [M×M]`、`C [M×N]`；
  能量五项 `E[Φ_i] = T[Φ_i] + E_ext[n] + E_H[n] + E_XC[n] + E_II`；矩阵形式 `K(C)C = SCϵ`。
  （与 T01 P5–P7 同构，符号更"实现派"。）
- `T19 P3` SCF 循环流程图（初猜密度 → 初猜 KS 势 → 解 KS 方程 → 新密度 → 收敛判据）。
- `T19 P4` **四类基组与 GPW/GAPW 的一句话定位**（本层最凝练的一页）：
  - 扩展基组（PW）：凝聚相；
  - 定域基组（原子中心 GTO）；
  - **GPW 的思想：为表示密度引入一套辅助基组**（"auxiliary basis set to represent the density"）；
  - **混合（GTO+PW）以取两者之长 → GPW**；
  - **增广基组 → GAPW：把密度分成 hard 与 soft 两个区域处理**。

**B. GPW 的实现剖面（T19 P5–P18）**

- `T19 P5` **GPW 配方（5 条）**：GTO 的**线性标度 KS 矩阵**计算、高斯基组（多项解析）、
  赝势、**以平面波作 Coulomb 积分的辅助基组**、**规则网格 + FFT 处理密度**、
  **稀疏矩阵（KS 与 P）**、**高效筛选**；文献 Lippert 1997、VandeVondele 2005。
- `T19 P6` 高斯基组的**稀疏性**：`S = ∫φ_αφ_β dr`、`H = ∫φ_α v φ_β dr` 的稀疏模式
  **只取决于基组与原子空间位置，与体系的化学性质无关（GGA DFT 下）**；
  "**overlap（基函数乘积的积分）随空间分离迅速衰减**"；
  实例：**HIV-1 蛋白酶-DMP323 复合物溶液，3200 原子**。
- `T19 P7` 解析积分：笛卡尔高斯
  `g(r,n,α,R) = (x−R_x)^{n_x}(y−R_y)^{n_y}(z−R_z)^{n_z} exp(−α(r−R)²)`、
  微分关系、**Obara–Saika 递推**（Obara & Saika, JCP 84 (1986) 3963）。
- `T19 P8` 基组库与**"同名不同库"的坑**：`GTH_BASIS_SETS ; BASIS_MOLOPT ; EMSL_BASIS_SETS`
  三库并列，同一元素同一风格的名字在各库写法不同
  （如 `SZV-MOLOPT-GTH-q6`、`DZVP-MOLOPT-GTH-q6`、`TZVP-MOLOPT-GTH-q6` 属 MOLOPT；
  `6-31G*`、`6-311++G(3df,3pd)` 属 EMSL）。**配基组时必须同时确认"库 + 全名"**。
- `T19 P9` CP2K 的 `cp2k/data/` 目录内容清单（基组/势文件全表）：
  `ALL_BASIS_SETS`、`ALL_POTENTIALS`、`BASIS_ADMM`、`BASIS_ADMM_MOLOPT`、`BASIS_LRIGPW_AUXMOLOPT`、
  `BASIS_MOLOPT`、`BASIS_MOLOPT_UCL`、`BASIS_RI_cc-TZ`、`BASIS_SET`、`BASIS_ZIJLSTRA`、
  `DFTB`、`ECP_POTENTIALS`、`EMSL_BASIS_SETS`、`GTH_BASIS_SETS`、`GTH_POTENTIALS`、
  `HFX_BASIS`、`HF_POTENTIALS`、`MM_POTENTIAL`、`NLCC_POTENTIALS`、`POTENTIAL`、
  `dftd3.dat`、`nm12_parameters.xml`、`rVV10_kernel_table.dat`、`t_c_g.dat`、`t_sh_p_s_c.dat`、
  `vdW_kernel_table.dat`；并说明 CP2K 自带**基组优化工具**（基于原子与分子电子结构计算）。
- `T19 P10` 赝势总览页：`Z_val = Z − Z_core`；原子 1s `exp{−Z r}`；
  "**光滑无节点赝波函数 close to nuclei**"、"裸库仑被屏蔽库仑替代"、含相对论效应、可迁移；
  **角动量依赖的势**（以 Pt 为例："p peaked at 3.9 Å、s peaked at 2.4 Å、d peaked at 1.3 Å"——
  原幻灯片单位为 Å，疑为 bohr 的排版笔误，见 §7）。
- `T19 P11` **GTH 赝势**：模守恒、可分、双空间；局域部分有短程+长程两项
  （`erf` 长程项 "analytically part of ES"），非局域部分用**高斯型投影子**
  `V_nl(r,r') = Σ_lm Σ_ij ⟨r|p_i^{lm}⟩h_ij^l⟨p_j^{lm}|r'⟩`，
  `⟨r|p_i^{lm}⟩ = N_i^l Y_lm(r̂) r^{l+2i−2} e^{−r²/(2r_l²)}`；
  特征词：**Scalar relativistic、Few parameters、Accurate and Transferable**；
  文献 Goedecker/Teter/Hutter PRB 54 (1996) 1703、Hartwigsen/Goedecker/Hutter PRB 58 (1998) 3641。
- `T19 P12` **静电能的周期体系形式**（GPW 的实现式）：
  `E_ES = ∫V_loc^PP(r)n(r)dr + 2πΩ Σ_{G≠0} ñ*(G)ñ(G)/G² + ½Σ_{A≠B}Z_AZ_B/|R_A−R_B|`；
  总电荷 `n_tot = n + Σ_A n_A`，其中
  `n_A(r) = Z_A/(√(2π) r_c³)·... `（**高斯芯电荷**，`r_c = √2·r_loc^A` 的写法在原页，
  要点是"**`r_c` 的选取使长程项与局域赝势的长程部分相消**"），
  再由 `E_ES^SR = ∫V_loc^PP n + ½∬ n_tot n_tot/|r−r'|` 拆出
  **long range / smooth** 与 **`E_ov`（short range, pair）/ `E_self`**。
- `T19 P13` **辅助基组与实空间网格的精度证据页**（本层最有价值的一张图）：
  - "**Orthogonal, unbiased, naturally periodic PW basis**"；
  - 长程项 = 非局域 Hartree 势 `E_H[n_tot] = ½∬ n_totn_tot/|r−r'|`，
    倒空间解为 `E_H[n_tot] = 2πΩ Σ_G ñ*_tot(G)ñ_tot(G)/G²` → **Poisson 方程线性标度求解**；
  - 图 1 的说明文字（正文级）：体系是**单个水分子**，用"**fairly hard GTH 赝势**"与
    **TZV2P 基组**，放在 **10 Å 立方盒**里；纵轴是**固定密度矩阵下静电能的绝对误差 [a.u.]**
    （从 10⁻¹ 到 10⁻⁷），横轴是 **plane wave cutoff 100–500 Ry**；
  - **网格间距与 cutoff 的换算关系**：`E_cutoff = π²/(2h²)`（原页排版为 `E_cutoff = 2h²` 的错位，
    按上下文应为 `π²/(2h²)`；同一页横轴给了网格间距刻度 **0.15 / 0.13 / 0.11 / 0.10 / 0.09 / 0.08 Å**）；
  - 文字结论（与 T01 P12–P13 对应）：静电能的**所有项同时处理**，
    长程在 Fourier 空间、短程在实空间，"用平面波电子结构程序里常见的 Ewald 求和实现"；
    核的分离靠"**为每个核引入高斯电荷分布 `n_I^c(r)`**"。
- `T19 P14` **实空间积分的完整循环图**（GPW 每个 SCF 步真正在做什么）：
  密度 collocation（`n(r) = Σ_μν P_μν φ_μφ_ν` → `Σ_μν P_μν φ̄_μν(R) = n(R)`）
  → 筛选 → `n̂(G)` → `V_H(G) = n̂(G)/G²` → `V_H(R)` → `∇n(R)`（**数值梯度**）
  → `ε_XC` 与 `∂ε_XC/∂n` 在网格上取值 → `V_XC(R)` →
  **实空间积分回矩阵元** `H^HXC_μν = ⟨μ|V_HXC(r')|ν⟩ → Σ_R V_HXC(R)φ̄_μν(R)`。
  文献 Lippert 1997、VandeVondele 2005。**"密度→网格→密度梯度→XC→势→矩阵元"这条路
  就是 GPW 每步的固定税**。
- `T19 P15` **多重网格的分配规则（本课最实用的一页）**：
  - 每层网格的 cutoff 按几何级数递减：**`E_cut,i = E_cut,1 / α^{i−1}, i = 1..N`**；
  - "**高斯乘积的指数决定它落在哪一层网格**"；
  - "**每个高斯的网格点数目与指数无关（exponent-independent）**"——所以层数越多、平均每层负担越小；
  - **cutoff 精度**：`∝ 1/2·α²`（原页 `⇥ = 1/2·`，按上下文为 cutoff 与指数平方的关系），
    并标出 **"Relative Cutoff ~30 Ry"**；
  - 复述 T01 P30 的硬数字："**指数为 1 的高斯要达到 10⁻¹⁰ 精度，需要积分范围 10 bohr、
    cutoff 25 Ry，结果 22 个积分点 ⇒ 约 5000 个积分点/积分批次**"；
  - 配图横轴为 **Exponent 0–8**，纵轴 **Number of pairs**（10000/30000/50000/70000），
    标注 `n_j = f_j^c(n_i)`——即**不同指数的高斯对分布在不同网格上**。
- `T19 P16` **多重网格实测（体相 Si，8 原子，a = 5.43 Å，E_cut = 100 Ry，E_rel = 60 Ry）**：
  - 官方风格的 `MULTIGRID INFO` 输出：
    `count for grid 1: 2720 cutoff [a.u.] 50.00` /
    `grid 2: 5000 cutoff 16.67` / `grid 3: 2760 cutoff 5.56` / `grid 4: 16 cutoff 1.85` /
    `total gridlevel count : 10496`
    （注意：此处列的是 **cutoff [a.u.] = Ry/2**，50.00 a.u. = 100 Ry，且 **16.67 ≈ 50/3**，
    印证 `PROGRESSION_FACTOR 3`）。
  - **"Changing E_cut from 50 to 500 Ry"（REL_CUTOFF = 60 固定）**：

    | Cutoff (Ry) | Total Energy (Ha) | NG grid 1 | NG grid 2 | NG grid 3 | NG grid 4 |
    |---|---|---|---|---|---|
    | 50.00 | −32.3795329864 | 5048 | 5432 | 16 | 0 |
    | 100.00 | −32.3804557631 | 2720 | 5000 | 2760 | 16 |
    | 150.00 | −32.3804554850 | 2032 | 3016 | 5432 | 16 |
    | 200.00 | −32.3804554982 | 1880 | 2472 | 3384 | 2760 |
    | 250.00 | −32.3804554859 | 264 | 4088 | 3384 | 2760 |
    | 300.00 | −32.3804554843 | 264 | 2456 | 5000 | 2776 |
    | 350.00 | −32.3804554846 | 56 | 1976 | 5688 | 2776 |
    | 400.00 | −32.3804554851 | 56 | 1976 | 3016 | 5448 |
    | 450.00 | −32.3804554851 | 0 | 2032 | 3016 | 5448 |
    | 500.00 | −32.3804554850 | 0 | 2032 | 3016 | 5448 |

    **三条结论**：
    ① **该体系 100 Ry 起总能量就到 1e−8 Ha 量级收敛**（100→500 Ry 只动 1e−9 Ha 量级），
       50 Ry 才明显不对（差 9.2e−4 Ha）——即"cutoff 只要够高，再高没有收益"；
    ② **高斯在不同网格间的分配随 CUTOFF 剧烈重组**（grid 1 从 5048 → 0，grid 4 从 0 → 5448），
       这就是"**只增 CUTOFF 不增 REL_CUTOFF 会让高斯被推到粗网格**"这句话的定量证据；
    ③ **最细网格上的函数数可以降到 0**，说明 `CUTOFF` 与"实际参与积分的精度"不是同一件事。
- `T19 P17` **GPW 泛函（与 T01 P25 同一件事的另一种写法）**：
  `E^el[n] = Σ_μν P_μν⟨φ_μ| −½∇² + V_loc^SR + V_nl |φ_ν⟩ + 2πΩ Σ_G ñ*_totñ_tot/G² + Σ_R ñ(R)V_XC(R)`
  `= Σ_μν P_μν⟨φ_μ| −½∇² + V_ext + V_HXC(R)|φ_ν⟩`；
  图注一句话点题：**"Linear scaling KS matrix construction"**。
- `T19 P18` **完整 GPW 输入卡（照抄级）**：

  ```
  &FORCE_EVAL
    METHOD Quickstep
    &DFT
      BASIS_SET_FILE_NAME GTH_BASIS_SETS
      POTENTIAL_FILE_NAME GTH_POTENTIALS
      LSD F
      MULTIPLICITY 1
      CHARGE 0
      &MGRID
        CUTOFF 300
        REL_CUTOFF 50
      &END MGRID
      &QS
        EPS_DEFAULT 1.0E-10
      &END QS
      &SCF
        MAX_SCF 50
        EPS_SCF 2.00E-06
        SCF_GUESS ATOMIC
      &END SCF
      &XC
        &XC_FUNCTIONAL
          &PBE
          &END PBE
        &END XC_FUNCTIONAL
        &XC_GRID
          XC_DERIV SPLINE2_smooth
          XC_SMOOTH_RHO NN10
        &END XC_GRID
      &END XC
    &END DFT
    &SUBSYS
      &CELL
        PERIODIC XYZ
        ABC 8. 8. 8.
      &END CELL
      &COORD
        O  0.000000  0.000000 -0.065587
        H  0.000000 -0.757136  0.520545
        H  0.000000  0.757136  0.520545
      &END COORD
      &KIND H
        BASIS_SET DZVP-GTH-PBE
        POTENTIAL GTH-PBE-q1
      &END KIND
      &KIND O
        BASIS_SET DZVP-GTH-PBE
        POTENTIAL GTH-PBE-q6
      &END KIND
    &END SUBSYS
  &END FORCE_EVAL
  ```

  （8 Å 立方盒里的单个水分子；`DZVP-GTH-PBE` / `GTH-PBE-q1|q6` 是 `GTH_BASIS_SETS` 里的**旧命名**，
  现代推荐见 G 层 `14_basis_and_potentials.md` §2.4 的 UZH 配对与 A 层 `decide.md` §4；
  `XC_DERIV SPLINE2_smooth` + `XC_SMOOTH_RHO NN10` 正是 T01 P33 "抑制负密度"的实操手段。）

**C. GAPW：密度分区（T19 P19–P25）**

- `T19 P19` **方法谱系页**：标题 "Hard and Soft Densities"（以甲醛为例）。
  四条路线并列：**赝势 ⇒ frozen core**；**Augmented PW ⇒ separate regions (matching at edges)**
  （LAPW、LMTO，O.K. Andersen, PRB 12, 3060 (1975)）；
  **Dual representation ⇒ localized orbitals and PW**；**PAW**（P.E. Blöchl, PRB 50, 17953 (1994)）。
  → **CP2K 的 GAPW 站在"Augmented PW + PAW"这一支**。
- `T19 P20` **密度的分区（GAPW 的核心公式）**：
  `n = ñ + Σ_A (n_A − ñ_A)`；区域划分为**原子区 A** 与**间隙区 I（interstitial）**，
  并要求**两条匹配条件**：
  - 在 `r ∈ I`：`n(r) − ñ(r) = 0` **且** `n_A(r) − ñ_A(r) = 0`；
  - 在 `r ∈ A`：`n(r) − Σ_A n_A(r) = 0` **且** `ñ(r) − Σ_A ñ_A(r) = 0`。
  三种表示的展开：`n = Σ_μν P_μν χ_μχ_ν`（GTO）、`ñ = Σ_μν P_μν φ̃_μφ̃_ν`（**光滑部分，全局网格**）、
  `n̂(G)e^{iG·R}`（PW）。**标题即结论：Gaussian Augmented Plane Waves**。
- `T19 P21` **局域密度 `n_A` 怎么来**：
  `n_A(r) = Σ_μν P_μν χ_μ^A(r)χ_ν^A(r)`，其中 `χ_μ^A = Σ_α d_μα^A g_α(r)` 是
  "**把 φ_μ 投影到 Ω_A 上**"的结果，投影系数由**原子依赖的投影基组 `{p_α}`**给出：
  `d_μα^A = Σ_β (⟨p_α|φ_μ⟩ − Σ_{λ,k}⟨p_α|φ_λ⟩ S^{-1}_{λk}⟨φ_k|g_β⟩)`（原页排版含
  `λ = k λ'`、`min` 等索引，要点是"**用同尺寸的投影基组做重叠区投影**"）；
  最后 `n_A(r) = Σ_αβ P^A_αβ g_α(r)g_β(r)`，`P^A_αβ = Σ_μν P_μν d_μα^A d_νβ^A`。
  **这一页说明：硬密度不是"再算一遍全电子"，而是把已有的 P 投影到原子中心的局域基组上。**
- `T19 P22` **XC 项在 GAPW 下怎么算**：密度梯度
  `∇n(r) = ∇ñ(r) + Σ_A(∇n_A(r) − ∇ñ_A(r))`；
  `E_xc[n] = Σ ∫V_loc(r)n(r) = Σ_A ∫Ṽ_loc(r)[ñ(r) + Σ_A(n_A − ñ_A)]dr`
  `= ∫Ṽ_loc(r)ñ(r) + Σ_A[∫V_loc^A(r)n_A(r) − ∫Ṽ_loc^A(r)ñ_A(r)]`。
  即 **"光滑部分在全局网格上（collocation + FFT），原子部分用解析积分 + 局域球面网格"**。
- `T19 P23` **静电项与非局域 Coulomb 算符**：
  引入**补偿电荷（compensation charge）** `n^0(r) = Σ_A n_A^0(r) = Σ_A Σ_L Q_A^L g_A^L(r)`，
  多极矩用与局域密度**相同的多极展开**：
  `Q_A^L = ∫_{r<r_cut} [n_A(r) − ñ_A(r) + n_A^0(r)] r^l Y_lm(θφ) r²dr sinθdθdφ`；
  能量三项分解 `V[ñ+n⁰] + V[n+n⁰] − V[ñ+n⁰]`，分别对应
  **Interstitial region / Atomic region**。
- `T19 P24` **GAPW 泛函总式（与 P20 一一对应）**：
  `E_xc[n] = E_xc[ñ] + Σ_A E_xc[n_A] − Σ_A E_xc[ñ_A]`；
  `E_H[n+n⁰] = E_H[ñ+n⁰] + Σ_A E_H[n_A+n⁰_A] − Σ_A E_H[ñ_A+n⁰_A]`；
  图注把三块的计算手段钉死：**"on global grids via collocation + FFT"**、
  **"Analytic integrals"**、**"Local Spherical Grids"**。
  文献：Lippert et al., Theor. Chem. Acc. 103, 124 (1999)；Iannuzzi, Chassaing, Hutter, Chimia (2005)；
  Krack et al., PCCP 2, 2105 (2000)；VandeVondele, Iannuzzi, Hutter, CSCM2005 proceedings。
- `T19 P25` **GAPW 输入卡（照抄级，本层最实用的一段）**：

  ```
  &DFT
    ...
    &QS
      EXTRAPOLATION ASPC
      EXTRAPOLATION_ORDER 4
      EPS_DEFAULT 1.0E-12
      METHOD GAPW
      EPS_DEFAULT 1.0E-12        ! 原幻灯片重复出现一次
      QUADRATURE GC_LOG
      EPSFIT 1.E-4
      EPSISO 1.0E-12
      EPSRHO0 1.0E-8
      LMAXN0 4
      LMAXN1 6
      ALPHA0_H 10
    &END QS
  &END DFT
  &SUBSYS
    ...
    &KIND O
      BASIS_SET DZVP-MOLOPT-GTH-q6
      POTENTIAL GTH-BLYP-q6
      LEBEDEV_GRID 80
      RADIAL_GRID 200
    &END KIND
    &KIND O1
      ELEMENT O
      # BASIS_SET 6-311++G2d2p
      BASIS_SET 6-311G**
      POTENTIAL ALL
      LEBEDEV_GRID 80
      RADIAL_GRID 200
    &END KIND
  &END SUBSYS
  ```

  **读法（重要）**：这张卡**同时**演示了两条路——
  ① `&KIND O` 用 **GTH-BLYP-q6 赝势 + MOLOPT 轨道基组**；
  ② `&KIND O1` 用 `POTENTIAL ALL` + **EMSL 全电子基组 `6-311G**`**（注释掉的第一候选是 `6-311++G2d2p`）。
  即**同一个 GAPW 方法既能配赝势、也能配全电子势**，区别只在你写什么 `POTENTIAL`/`BASIS_SET`。
  逐 kind 的 `LEBEDEV_GRID 80` / `RADIAL_GRID 200` 是**原子区球面/径向网格**；
  `QUADRATURE GC_LOG`（Gauss–Chebyshev 对数型径向求积）、`EPSFIT 1.E-4`、`EPSISO 1.0E-12`、
  `EPSRHO0 1.0E-8`、`LMAXN0 4`、`LMAXN1 6`、`ALPHA0_H 10` 是硬/软拆分与补偿电荷的参数。
  > 这些关键字的**官方语义与默认值**以 G 层为准：`official/23_dft_subpages_full.md` §GAPW、
  > `official/02_dft_methods.md` §1.2、`official/21_xray_spectroscopy_full.md`（含 `EPSFIT 1.E-4` 的用法）；
  > 本文件只记录"教材给的这套取值"及其教学意图。

**D. 能量最小化与 OT（T19 P26–P33，非 GPW/GAPW 特有）**

- `T19 P26` 最小化问题 `C = arg min E(C) s.t. CᵗSC = 1` 的三条路线：
  对角化+mixing（DIIS；迭代对角化 Kresse et al., PRB 54 (1996) 11169）、
  直接优化（orbital rotations / 最大定域 Wannier 函数）、线性标度方法；
  密度矩阵衰变 `P(r,r') ~ e^{−c·E_gap|r−r'|}`；实例 **DNA 晶体，2388 原子、3960 轨道、38688 基函数（TZV(2d,2p)）**。
- `T19 P27` 传统对角化流程（SCALAPACK、Cholesky 归约、只做占据轨道 20%、DIIS 误差矩阵 `e = KPS − SPK`），
  并点明两条代价："**scaling O(M³) 与稳定性问题**"。
- `T19 P28–P31` **OT 方法**：`C(X) = C₀cos(U) + XU^{−1}sin(U)`、`U = (XᵗSX)^{1/2}`、
  约束 `XᵗSC₀ = 0`；预条件梯度 `PX = P(H − Sϵ)X`、理想预条件
  `P = (H − Sϵ_n)^{−1}`，实现选项 **Full All / Full Single Inverse / Full Kinetic / Full S Inverse / Full Single**；
  OT 性能 8 条（内外循环、CG+线搜索保证收敛、避免 KS 对角化、可用 S/H 稀疏性、
  **标度 `O(N²M)` CPU、`O(NM)` 内存**、适合大体系与高质量基组）；
  精细化预条件（Schiffmann & VandeVondele, JCP 142, 244117 (2015)）在**大体系、良态基组的 MD 中最有效**，
  "**But OT is hard to beat!**"（3844 节点，8 核 + 1 GPU）。
- `T19 P32` **OT 输入卡**：
  ```
  &SCF
    EPS_SCF 1.01E-07
    &OUTER_SCF
      MAX_SCF 20
      EPS_SCF 1.01E-07
    &END OUTER_SCF
    SCF_GUESS RESTART
    MAX_SCF 20
    &OT
      MINIMIZER DIIS
      PRECONDITIONER FULL_ALL
    &END OT
  &END SCF
  ```
- `T19 P33` 线性标度 SCF：`P = ½(I − sign(S⁻¹H − μI))S⁻¹` 式的新算法（VandeVondele/Borstnik/Hutter,
  JCTC 10, 3566 (2012)）；**CP2K 迄今最大的 O(N³) 计算 ≈ 6000 原子，最大的 O(N) 计算 ≈ 1 000 000 原子**。

**E. 并行与稀疏矩阵（T19 P34–P35，非 GPW/GAPW 特有）**

- `T19 P34` DBCSR（Distributed Blocked Compressed Sparse Row）：面向"**每行上万个非零元**"的科学场景，
  Cannon 式通信、2D 布局、按原子/分子分块、同质化以平衡负载。
- `T19 P35` 百万原子凝聚相：46656 核，**10⁶ 原子 < 2 小时**（最小基组）；**9216 核**配准确基组。
  注：幻灯片对 DBCSR 缩写给了两种展开（"Compressed Sparse Row" 与 "Cannon Sparse Recursive"），见 §7。

**F. 金属与特征值求解器（T19 P36–P43）**

- `T19 P36–P38` 金属电子结构：k 点积分、费米面、"**charge sloshing 与极慢收敛**"、
  "波函数必须与能量接近的空带正交"、"占据数不连续导致不稳定（n(r) 大变化）"；
  Mermin 泛函 `F(T) = E − k_BT Σ_n S(f_n)`、Fermi–Dirac 占据、G 空间混合
  `n^{in}_{m+1} = n^{in}_m + G[R[n^{in}]] + α Σ_i(n^{in}_i + G[R[n^{in}_i]])`（残差 `R` 与预条件矩阵 `G`）。
  **与 GPW/GAPW 无直接关系，本笔记不作为要点展开**（金属 SCF 在 G 层 `03_scf_convergence.md`、
  A 层 `decide.md` §6 已有更贴实操的版本）。
- `T19 P39` Rh 体相与表面（**唯一一组"赝势价电子数 ↔ 基组尺寸 ↔ 物理量"的对照**）：

  | Basis | PP | a [Å] | B [GPa] | E_s [eV/Å²] | W [eV] |
  |---|---|---|---|---|---|
  | Q17（`3s2p2df`, 17e） | | 3.80 | 258.3 | 0.186 | 5.11 |
  | Q9 DZVP（`2s2p2df`, 9e） | | 3.83 | 242.6 | 0.172 | 5.14 |
  | SZVP（`2sp2d`, 9e） | | 3.85 | 230.2 | 0.167 | 5.20 |
  | SZV（`spd`, 9e） | | 3.87 | 224.4 | 0.164 | 5.15 |

  体相用 **4×4×4** k 点、表面 **6×6 / 7 层**；表面模型：**4 层 slab、576 个 Rh 原子、
  5184 个电子、8640 个基函数**。
  → **同是 9 个价电子，基组从 SZV 到 DZVP 使晶格常数变 0.02 Å、体模量变 18 GPa**（约 7%）。
- `T19 P40–P41` 特征值求解器（ELPA 项目论文截图：ScaLAPACK 性能、两步三对角化、CRAY-XE6 与 BG/P 基准）。
  **非 GPW/GAPW 主题，未提取要点。**
- `T19 P42` 大金属体系：hBN/Rh(111) 纳米网格（13×13 hBN on 12×12 Rh slab；
  **2116 Ru 原子 + 1250 C 原子、N_el = 21928、N_ao = 47990、~25 天/结构优化，1024 CPU**；
  以及 **4 层：576 Rh + 169 BN、N_ao = 19370、N_el = 11144** 与
  **7 层：1008 Rh + 338 BN、N_ao = 34996、N_el = 19840**，结构优化 > 300 次迭代 ⇒ **1–2 周 / 512 核**）。
- `T19 P43` **金属 SCF 输入卡（照抄级）**：
  ```
  &SCF
    SCF_GUESS ATOMIC
    MAX_SCF 50
    EPS_SCF 1.0e-7
    EPS_DIIS 1.0e-7
    &SMEAR
      METHOD FERMI_DIRAC
      ELECTRONIC_TEMPERATURE 500.
    &END SMEAR
    &MIXING
      METHOD BROYDEN_MIXING
      ALPHA 0.6
      BETA 1.0
      NBROYDEN 15
    &END MIXING
    ADDED_MOS 20 20
  &END SCF
  &XC
    &XC_FUNCTIONAL PBE
    &END
    &vdW_POTENTIAL
      DISPERSION_FUNCTIONAL PAIR_POTENTIAL
      &PAIR_POTENTIAL
        TYPE DFTD3
        PARAMETER_FILE_NAME dftd3.dat
        REFERENCE_FUNCTIONAL PBE
      &END PAIR_POTENTIAL
    &END vdW_POTENTIAL
  &END XC
  ```

---

## 3. 核心逻辑链（重点）

### 3.1 起点：两族基组在"密度形状"上的分工

- T19 P4 把话说到最直白：PW 属于"扩展基组 → 凝聚相"，GTO 属于"定域基组 → 原子位置中心"；
  **GPW = 混合起来取两者之长**，GAPW = **把密度切成 hard/soft 两块**。
- 为什么天然要这么切？T01 P43 从赝势侧给了物理解释：**核附近波函数必须与芯态正交 → 出现节点结构
  → 需要很高的平面波 cutoff**。反过来，**核间/间隙区的密度是平滑的**，用平面波只要少数几个 G 就够。
  一句话：**hard 的地方用定域表示，soft 的地方用扩展表示。**
- 而且两族的"便宜点"正好互补（T01 P9/P21/P22/P29）：
  - GTO 侧：**解析积分**（动能/外势/overlap，T01 P11）、**R 空间距离筛选**（P26）、
    Fourier 变换后**仍是高斯**（P9、P29）→ 适合"抓住局域的尖峰"；
  - PW 侧：**正交、与原子位置无关、天然周期**（T01 P15）、可以用 FFT 把 Poisson 方程
    `∇²V = −4πρ` 变成逐 G 的除法 `V(G) = 4πρ(G)/G²`（T01 P22、T19 P13）→ 适合"处理长程与平移不变的部分"。

### 3.2 为什么"不能用纯高斯基组解周期 DFT"——瓶颈是 ERI

T01 P11 把账摆在桌面上：动能、外势、overlap 都是解析的（便宜），
**只有 Coulomb 的 4 中心 ERI `(αβ|γδ)` 是 CPU 与内存瓶颈**。
T01 P12 于是把目标写成一句话："**Goal: Avoid calculation of ERI**"。

这一步是整个 GPW 存在的理由。若没有它，CP2K 就只是"另一个高斯基组程序"，
而高斯基组程序在**周期性凝聚相 + 大体系**上会被 ERI 的标度压死；
反过来纯平面波程序（T01 P15）又需要**数量极多**的函数，且天然不适合描述核附近的尖峰。

### 3.3 GPW 的三步"偷换"，以及它凭什么合法

**第 1 步（T01 P12–P13，T19 P12）：把三项静电能合并成一个总静电能，再用 Ewald 式分割。**
不再逐对算 ERI，而是：
1. 给每个核配一个**高斯原子电荷** `ρ_A(r) = Z_A(α/π)^{3/2}e^{−α(r−A)²}`（T01 P13）；
2. 构造**总电荷** `ρ_tot = ρ_e + Σ_A ρ_A`；
3. 用这个总电荷的长程项 + `erfc` 短程项 + 短程对相互作用 − 自相互作用修正，
   把核-电子、电子-电子、核-核三段一次算完（T01 P13 的四项式；T19 P12 的
   `E_ES = ∫V_loc^{PP}n + 2πΩΣ_{G≠0}ñ*ñ/G² + ½Σ_{A≠B}Z_AZ_B/R_AB`）。
   T19 P12 特别点明：**高斯芯电荷的宽度 `r_c` 的选择，使它的长程项与局域赝势的长程部分相消**——
   这不是随便挑的，是**为了消掉 `G→0` 的库仑发散**。

**第 2 步（T01 P19–P22、P34；T19 P13–P14）：长程项搬到倒空间，用 FFT 解 Poisson。**
- cutoff 定了基组大小：`N_PW ≈ (Ω/2π²)E_cut^{3/2}`（T01 P19）——**只跟盒子体积和 cutoff 有关**，
  所以 PW 侧的代价是"可预测、可控制"的；
- 长程能写成 `E_LRT = (2π/Ω)Σ_G |ρ_tot(G)|²/G²`（T01 P22），只需一次 FFT；
- 全链路代价 `O(n log n)`（T01 P34），两端复用同一套 `χ̄_μν(R)`，筛选可以共享。

**第 3 步（T01 P21、P23、P25）：在两个表示之间"机会主义地"切换，并用一个修正项保证自洽。**
- 数学许可 = **Parseval 定理**（T01 P21）：实空间积分与倒空间积分等价，
  于是"哪里便宜就在哪里算"；
- XC 必须回实空间（因为 `ε_xc(G)` 在 G 空间**非局域**，T01 P23），
  在网格上算 `E_xc = (Ω/N)Σ_R ε_xc(R)ρ(R)`；
- 但这样一来，**能量里同时出现了"GTO 表示的密度 `ρ`"和"网格/PW 表示的密度 `ρ̃`"**，
  两者不严格相等，于是 GPW 能量表达式必须写明修正项（T01 P25）：
  `E_KS^GPW = E_kin(P) + δE_ext(P) + E_xc(ρ̃) + E_H(ρ̃) + E_ovrl − E_self`。
  教材的两句关键限定：
  - **`E_KS^GPW` 只对 GTO 系数 `c_αi` 变分**；
  - `ρ̃(G)` 同时是 `c_αi` **与辅助 PW 基组**的函数。
  → 换句话说：**辅助平面波基组是"数值工具"，不是变分自由度**；
  整个方法仍然是变分的、可以求解析力的**唯一原因**就在这里。

**推理链汇总（一句话版）**：
> ERI 太贵 → 合并静电能 + 高斯核电荷 + Ewald 分割 → 长程搬到倒空间用 FFT 解 Poisson（O(n log n)）→
> XC 必须回实空间 → 用辅助 PW 基组承载 `ρ̃` 与 `V_H`，用 Parseval 在两个表示间自由切换 →
> 代价是 `ρ ≠ ρ̃`，于是能量式里多出 `δE_ext + E_ovrl − E_self` 三项做账 →
> 变分自由度仍然只有 GTO 系数 ⇒ 既便宜又可求力。

### 3.4 代价（一）：数值误差不是"更小的数"，而是"另一种性质的误差"

**(a) ripples —— 平移不变性的破缺（T01 P24）**
原文一句话："**只有按网格间距的整数倍平移，总能量才不变**。这引入能量超曲面的一个小调制，
叫做 ripples。" 这是**几何优化与 AIMD 的力噪声来源**：力 = 能量对坐标的导数，
而能量随原子位置有非物理的小周期振荡 → 力的系统性偏差。
T01 P25 的 `δE_ext`/`E_ovrl`/`E_self` 三项修正正是为了把这一类不一致压下去。

**(b) 网格分配是"指数决定论"（T19 P15）**
"**高斯乘积的指数决定它落在哪一层网格**"，且"**每个高斯的网格点数目与指数无关**"。
推论：**同一个基组里弥散函数与紧函数的积分精度天生不同**，
而且改 `CUTOFF` 会让高斯**在网格之间重新分配**（T19 P16 的表：grid 1 从 5048 → 0，
grid 4 从 0 → 5448）——**"提高 CUTOFF"不是单调地"提高同一个计算的精度"，
而是在改变整个积分方案**。这就是 A 层 `decide.md` §7 那句
"只增 CUTOFF 不增 REL_CUTOFF，细网格上高斯数反而减少、收敛变慢"的**机制来源**。

**(c) 负密度（T01 P33）**
XC 必须用实空间密度与**数值梯度**（T19 P14），而"**Fourier 插值会在低密度区产生负密度，
multigrid 会加重这个问题**"（T01 P33，加重号）。
后果按泛函阶梯放大：LDA 只吃 `ρ`，GGA 吃 `(∇ρ)²/ρ^{4/3}`，meta 还吃 `τ`——
**分母里的 ρ 或 ρ^{4/3} 在负/近零密度处直接爆掉**。
所以 T01 P33 给了三个显式关键字 `DENSITY_CUTOFF` / `GRADIENT_CUTOFF` / `TAU_CUTOFF`
与 `&XC/&XC_GRID` 的出口；T19 P18 的输入卡则示范了
`XC_DERIV SPLINE2_smooth` + `XC_SMOOTH_RHO NN10` 这对"平滑化"设置。

**(d) 筛选是"软的"（T01 P27，T19 P6）**
整个效率来自"基函数乘积随距离衰减"（T19 P6）与三级筛选（T01 P26），
而筛选阈值由 `EPS_DEFAULT` 统一控制（T01 P27）。
于是出现一类**不是数值噪声、而是流程失败**的症状：
**overlap 矩阵 Cholesky 分解失败**（基组条件数 × 阈值太大）。
T01 P56 的条件数表正好给出"谁能容忍多少"：**aug- 系列把 κ 抬高一个量级**
（aug-QZV3P 在水里 15.11，m-TZV2PX 只有 4.27）——
**基组越"弥散完备"，越容易踩到 Cholesky 与筛选的坑**。

**(e) 代价的量级（T01 P37）**
同一体系同一精度档，`NGRIDS` 从 4 降到 1 慢 **8–25 倍**（2.7→21.9 s；3.0→76.5 s），
而能量只动到小数点后第 7–8 位。**这就是"多网格"的全部意义：它买速度，不买精度。**
另一头，cutoff 从 280→1600 Ry 一共只买回 ~1.2×10⁻³ Ha，机时从 1.5 s 到 4.7 s（约 3 倍）。
**两笔账必须分开算。**

### 3.5 代价（二）：GPW 的价值全部建立在"核不用被显式描述"之上

这是理解 **GPW↔GAPW 分界**的关键，而 T01 把这条线索埋在了赝势章节：

- T01 P41：赝势存在的三个理由——**减小基组、减少电子数、部分纳入相对论**；
- T01 P42：**冻芯**，且平面波计算里 "**core = 全部满壳层**"，**不同原子的芯电子不重叠**；
- T01 P43：**芯-价 XC 的线性化假设 `E_XC(ρ_c+ρ_v) ≈ E_XC(ρ_c)+E_XC(ρ_v)`**，
  破例时用 NLCC（P51–P52）；
- T01 P43 第 ① 条：**"价波函数必须与芯态正交 → 节点结构 → 高 PW cutoff"**。

把这四条连起来：
> **GPW 之所以便宜，是因为它把"核附近那部分难描述的密度"整个外包给了赝势。**
> 网格只需承载**光滑的价电子密度**；`CUTOFF/REL_CUTOFF/NGRIDS` 的全部讨论，
> 都以"密度里没有核附近的尖峰"为前提。

**一旦这个前提被打破，GPW 的三条支柱同时崩：**
1. 密度里出现紧的核区分量 → 需要极高的 `CUTOFF` 才能跟上（T01 P30：
   **仅指数为 1 的高斯，10⁻¹⁰ 精度就要 25 Ry、10 bohr 范围、22 个积分点/维**；
   真实的芯函数指数是 10¹–10⁴ 量级，代价不可承受）；
2. 单位体积的高斯数目暴涨（T19 P15/P16：层分配是按指数走的）→
   "每个高斯点数目与指数无关"这条便利失效；
3. XC 与 Hartree 都在**同一个粗网格**上算 → 核区误差直接进入能量与力。

**GAPW 就是针对这三条的对症解。**

### 3.6 GAPW 做了什么：把"核区"从网格上摘出去

公式（T19 P20）：**`n = ñ + Σ_A(n_A − ñ_A)`**。
读法：
- `ñ` = **光滑部分**，仍然走 GPW 的老路（全局网格 + collocation + FFT，T19 P24 图注）；
- `(n_A − ñ_A)` = **原子中心的硬部分修正**，在**原子区 A 内**用**局域球面网格 + 解析积分**处理；
- 两条**匹配条件**（P20）保证：
  在间隙区 I，`n − ñ = 0` 且 `n_A − ñ_A = 0`（**修正项在间隙区自动消失**）；
  在原子区 A，`n − Σ_A n_A = 0` 且 `ñ − Σ_A ñ_A = 0`（**全局与局域的一致拼接**）。

三个"为什么这样设计"的答案：
1. **为什么修正项只在原子区内非零？** 因为 hard 的东西本来就在核附近——
   把修正的支撑集限制在 `Ω_A` 内，间隙区的计算量一点不增加。
2. **为什么需要补偿电荷 `n⁰`（P23）？** 因为一旦把密度拆成两块，
   `n_A − ñ_A` 这个差值带着**多极矩**，直接算它的 Hartree 会有条件数极差的近奇异项；
   补偿电荷 `n⁰ = Σ_A Σ_L Q_A^L g_A^L(r)` 用**与局域密度相同的多极展开**
   （`Q_A^L` 由 `[n_A − ñ_A + n_A⁰]` 的球面积分给出）把差值的多极矩"补平"，
   使 `V[ñ+n⁰] + V[n+n⁰] − V[ñ+n⁰]` 三项的**近程奇异性相互抵消**。
3. **为什么硬部分不必"重算全电子"？** 因为 `n_A` 是**投影**出来的（P21）：
   `χ_μ^A = Σ_α d_μα^A g_α(r)`，`d` 由**原子中心投影基组 `{p_α}`** 与重叠矩阵给出，
   最终 `P^A_αβ = Σ_μν P_μν d_μα^A d_νβ^A`。
   **同一个密度矩阵 P，换一套局域基组重新展开一次**——这是 GAPW 相对全电子程序便宜的根本原因，
   也是 G 层说的"**PAW 式**"的确切含义。

**GAPW 的分界与代价（什么时候必须上）**：

| 判据 | 依据 | 结论 |
|---|---|---|
| 需要核区密度/核区响应（EFG、NMR、超精细、XAS/RIXS） | G 层 `02_dft_methods.md §1.2`；A 层 `decide.md` §14/§15 | **必须 GAPW** |
| 需要**全电子**（与全电子分子程序对照、core level） | T19 P19/P25（`POTENTIAL ALL` + `6-311G**`） | **必须 GAPW** |
| 用**小芯赝势**、核区精度要求高 | G 层 `02_dft_methods.md §1.2` | **必须 GAPW** |
| 标准仅价电子赝势的常规能量/结构/AIMD | G 层同条"对标准仅价电子赝势 DFT 计算，GPW 通常更简单更快"；T01 P41–P43 | **优先 GPW** |

**上 GAPW 之后的代价（教材侧证据）**：
- 你要额外交付一套**原子区网格**（`LEBEDEV_GRID 80` / `RADIAL_GRID 200`，T19 P25），
  以及一组硬/软拆分参数（`EPSFIT / EPSISO / EPSRHO0 / LMAXN0 / LMAXN1 / ALPHA0_H / QUADRATURE`）；
- **容差要收紧**：T19 P18 的 GPW 卡用 `EPS_DEFAULT 1.0E-10`，GAPW 卡用 **`1.0E-12`**；
- **cutoff 需求上升**：G 层 `02_dft_methods.md §1.2` 的官方说明——`EPSFIT` 调紧会把更硬的高斯纳入
  soft density，**通常需要更大的 `CUTOFF`**；官方实操建议"检查 SCF 收敛后打印的电子计数"
  作为 hard/soft 拆分质量的诊断；
- **官方示例可能用更激进的网格**：`official/17_constrained_dynamics_and_paths.md` 的 GAPW 示例用
  `REL_CUTOFF 100`、`NGRIDS 5`（对比 T19 P18 的 GPW 卡 `REL_CUTOFF 50`）。
  → **"GAPW 比 GPW 贵"在输入卡上就表现为：更紧的 EPS + 更大的 REL_CUTOFF/NGRIDS + 原子区网格。**

### 3.7 整条链的一句话总结

> **GPW 把"难的部分"（核附近的尖密度）外包给赝势，只让网格承载光滑的价密度；
> 于是它必须在两处付账——一是 GTO↔网格不一致带来的 ripples/负密度/筛选阈值，
> 二是"核区信息被丢掉了"。GAPW 把第二笔账买回来：用 `n = ñ + Σ_A(n_A − ñ_A)`
> 把硬密度局部化到原子球内、用补偿电荷消掉多极奇异性、用投影（而非重算）得到 `n_A`，
> 代价是原子区网格、更紧的容差、更高的 cutoff，以及"必须自己判断 hard/soft 拆分够不够"。
> 判据只有一条：**你要的东西里，有没有"核附近"这一项。** 有 → GAPW；没有 → GPW。**

---

## 4. 可执行要点

### 4.1 `&MGRID`：cutoff 与多重网格

```text
&MGRID
  CUTOFF            300      ! 最细网格的 PW cutoff（Ry）；决定密度/势/XC 的展开精度
  REL_CUTOFF        50       ! "指数为 1 的高斯"所用最小 cutoff（Ry）；决定高斯如何分配到各层
  NGRIDS            4        ! 实空间网格层数
  PROGRESSION_FACTOR 3       ! 相邻层 cutoff 的衰减因子：E_cut,i = E_cut,1 / α^(i-1)
  ! MULTIGRID_SET    F      ! 是否由输入直接给定各层 cutoff（默认 F）
  ! MULTIGRID_CUTOFF ...    ! MULTIGRID_SET T 时逐层列出
&END MGRID
```

- **数值**（T19 P18 的完整示例）：`CUTOFF 300` + `REL_CUTOFF 50`，8 Å 盒、单水分子、PBE。
- **数值**（T19 P16 的实测环境）：体相 Si，8 原子，`a = 5.43 Å`，`E_cut = 100 Ry`，`E_rel = 60 Ry`，
  `NGRIDS 4`，输出 `total gridlevel count : 10496`，各层 cutoff `[a.u.]` = **50.00 / 16.67 / 5.56 / 1.85**
  （注意 a.u. 与 Ry 差 2 倍，16.67 = 50/3 印证 `PROGRESSION_FACTOR 3`）。
- **分配规则**（T19 P15）：`E_cut,i = E_cut,1/α^{i−1}`；
  **高斯乘积的指数决定它去哪一层**；**每层上每个高斯的点数与指数无关**。
- **`REL_CUTOFF` 的官方定义对象**（T01 P32）："**指数为 1 的高斯所用的最小 cutoff，默认 40 Ry**"。
  → 换句话说，`REL_CUTOFF` 是**指数标尺**，不是"密度精度"旋钮。
- **理由（为什么不能只调 `CUTOFF`）**：T19 P16 的表显示，`REL_CUTOFF` 固定 60 时把 `CUTOFF`
  从 50 提到 500 Ry，grid 1 上的高斯数从 **5048 掉到 0**、grid 4 从 **0 涨到 5448**——
  **`CUTOFF` 改的是"整个积分方案"，不是"同一方案的精度"**。
- **`NGRIDS` 的价格**（T01 P37）：`NGRIDS 1` 相对 `NGRIDS 4` 慢 **8 倍**（400 Ry 档：21.9 s vs 2.7 s）
  到 **25 倍**（800 Ry 档：76.5 s vs 3.0 s），能量不变。
- **`NGRIDS` 的官方选择法** → 指针：G 层 `08_errors_and_faq.md` §3.6（`faq:ngrids`），
  含 `exponent × REL_CUTOFF ≤ cutoff` 这条判据。
- **收敛流程** → 指针：G 层 `03_scf_convergence.md` §第二部分（官方 `cutoff.html`），
  A 层 `decide.md` §7。

### 4.2 `&QS` 与 `EPS_DEFAULT`（筛选总开关）

```text
&QS
  EPS_DEFAULT       1.0E-10     ! T19 P18 的 GPW 示例
  ! EPS_DEFAULT     1.0E-12     ! T19 P25 的 GAPW 示例（GAPW 要更紧）
&END QS
```

- `T01 P27`：**所有单项筛选阈值都由 `EPS_DEFAULT` 控制**
  （路径 `CP2K_INPUT / FORCE_EVAL / DFT / QS`）。
- `T01 P27` 记录的两类故障（**这是教材独有的诊断线索**）：
  - **overlap 矩阵 Cholesky 分解失败** ← 基组条件数 × `EPS_DEFAULT` 太大；
  - **实空间网格上电荷不准** ← PW cutoff 太低 和/或 `EPS_DEFAULT` 太大（`φ_αβ` 的延展被截断）。
- `T01 P56` 给出条件数量级：aug-QZV3P 在水里 `logκ = 15.11`，m-TZV2PX 只有 `4.27`。
  → **用弥散基组（aug-）时不要同时把 `EPS_DEFAULT` 放得很松。**
- 关键字语义与默认值 → 指针：G 层 `20_input_reference_tree.md`、`01_global_and_units.md`。
- **一个"分账"提醒**（T01 P37）：1600 Ry 下 `EPS_DEFAULT −8 → −12` 能量变 1.3×10⁻⁵ Ha，
  机时 3.7 s → 4.7 s；**cutoff 不够不能靠收紧 EPS 补**。

### 4.3 `&XC` 与 `&XC_GRID`（负密度对策）

```text
&XC
  &XC_FUNCTIONAL
    &PBE
    &END PBE
  &END XC_FUNCTIONAL
  &XC_GRID
    XC_DERIV      SPLINE2_smooth   ! T19 P18
    XC_SMOOTH_RHO NN10             ! T19 P18
  &END XC_GRID
&END XC
```

- `T01 P33`：XC 能量精度由"**密度展开精度 + 总 PW cutoff**"决定；
  CP2K **从密度的平面波展开求梯度**；
  **Fourier 插值会在低密度区产生负密度，multigrid 会加重该问题**。
- `T01 P33` 按泛函阶梯给的密度依赖：**LDA `ρ` / GGA `(∇ρ)²/ρ^{4/3}` / meta `τ`**，
  对应关键字 **`DENSITY_CUTOFF` / `GRADIENT_CUTOFF` / `TAU_CUTOFF`**（在 `FORCE_EVAL/DFT/XC`）；
  更多高级选项在 **`FORCE_EVAL/DFT/XC/XC_GRID`**。
- `T19 P14` 给出这条路在每一步 SCF 里的确切位置：
  `n(R) → n̂(G) → V_H(G)=n̂/G² → V_H(R) → ∇n(R) → ε_XC, ∂ε_XC/∂n → V_XC(R)
  → H^HXC_μν = Σ_R V_HXC(R)φ̄_μν(R)`。
- 关键字默认值/枚举 → 指针：G 层 `23_dft_subpages_full.md`（`&XC/&XC_GRID` 全表）、
  `21_xray_spectroscopy_full.md`（`XC_DERIV NN50_SMOOTH` / `XC_SMOOTH_RHO NN50` 用法）。

### 4.4 基组与赝势文件的选择

**文件层（T19 P8–P9，`cp2k/data/`）**：
- 三套常用基组库并列：`GTH_BASIS_SETS`、`BASIS_MOLOPT`、`EMSL_BASIS_SETS`；
  **同一个化学风格的名字在不同库里写法不同** → 写 `BASIS_SET_FILE_NAME` 时必须与 `BASIS_SET` 全名配套。
- `cp2k/data/` 里与本主题相关的势文件：
  `GTH_POTENTIALS`（GTH 常规）、`NLCC_POTENTIALS`（非线性芯校正）、
  `POTENTIAL`、`ALL_POTENTIALS`、`ECP_POTENTIALS`（用于高斯积分计算的有效芯势）、
  `HF_POTENTIALS`、`GTH_SOC_POTENTIALS`（T19 P9 未列全，补自 G 层 `14_basis_and_potentials.md` §2.4）。
- CP2K 自带**基组优化工具**（基于原子/分子电子结构计算）——T19 P9。

**T19 P18 的完整 KIND 段（照抄可运行）**：
```text
&KIND H
  BASIS_SET  DZVP-GTH-PBE
  POTENTIAL  GTH-PBE-q1
&END KIND
&KIND O
  BASIS_SET  DZVP-GTH-PBE
  POTENTIAL  GTH-PBE-q6
&END KIND
```
配套 `BASIS_SET_FILE_NAME GTH_BASIS_SETS` + `POTENTIAL_FILE_NAME GTH_POTENTIALS`。

**T19 P25 的 GAPW KIND 段（两条路并列，照抄可运行）**：
```text
&KIND O
  BASIS_SET      DZVP-MOLOPT-GTH-q6
  POTENTIAL      GTH-BLYP-q6          ! 路①：小芯/赝势路线
  LEBEDEV_GRID   80
  RADIAL_GRID    200
&END KIND
&KIND O1
  ELEMENT        O
  BASIS_SET      6-311G**             ! 路②：全电子路线（备选注释里是 6-311++G2d2p）
  POTENTIAL      ALL
  LEBEDEV_GRID   80
  RADIAL_GRID    200
&END KIND
```
→ **GAPW 不是"必须 `POTENTIAL ALL`"**：同一份输入卡演示了"GTH 赝势 + MOLOPT"与
"`POTENTIAL ALL` + EMSL 全电子基组"两种配法（详见 §6 纠错 3）。

**基组选择的理论依据（T01 P53–P56）**：
- MOLOPT 的五个目标与三条因果（一般收缩 → 良态无孤立弥散；弥散原始函数 → 低 BSSE；
  全分子优化 → 小而准）；
- 家族阶梯 `m-SZV(1s1p) → m-DZVP(2s2p1d) → m-TZVP(3s3p1d) → m-TZV2P(3s3p2d) → m-TZV2PX(3s3p2d1f)`，
  氢对应 `1s → 2s1p → 3s1p → 3s2p → 3s2p1d`；**每个函数 6/7 个原始高斯**，**大基组是小基组的扩展**；
- 条件数表（T01 P56，见 §2.1 F）——**同尺寸下 MOLOPT 条件数最低**。
- 现代推荐命名（UZH 协议配对）与默认值 → 指针：G 层 `14_basis_and_potentials.md` §2.4 / §2.5，
  A 层 `decide.md` §4。

**赝势侧的三条实操判据（T01 P41–P52）**：
1. 需要**相对论效应**、要**减少电子数**、要**缩小基组** → 用赝势（P41）；
2. **碱金属、过渡金属**芯-价重叠明显 → 要么把 semi-core 算进价电子（代价：电子更多、**cutoff 更高**），
   要么用 **NLCC**（`NLCC_POTENTIALS`）（P51–P52）；
3. `V^PS` 是**态相关**的（P44），所以**不要跨泛函族混用赝势与基组**
   （与 G 层 `02_dft_methods.md` §2.4 "用与泛函族匹配的赝势"一致）。
- GTH 的可分离形式 `V_loc + Σ_L Σ_ij |p_i^L⟩h_ij^L⟨p_j^L|`（T01 P50 / T19 P11）
  之所以能塞进 GPW，是因为它**完全非局域 ⇒ 解析积分与 FFT 都容易**（T01 P50）。

### 4.5 BSSE：机理与估计式

- `T01 P38`：定域非正交 AO 基组不完备 + "**局域完备性取决于原子位置**" ⇒
  **团簇比孤立分子更完备 ⇒ 结合能被高估**（二聚体、表面吸附）。
- Counterpoise 估计（**片段取团簇几何**）：
  `E_BSSE ≈ E_A(A+B) + E_B(A+B) − E_A(A) − E_B(B)`。
- `T01 P39`：液水 BSSE 随基组 `DZVP → TZV2P → QZV2P → QZV3P(f,d)` 递减。
- **注意**：G 层 `18_posthf_semiempirical_and_xray.md` §2 已确认 BSSE 在官方手册有明文，
  但**没有校正方法章节**；T01 P38 的机理与 Counterpoise 式是本层新增的**第一手教材出处**。

### 4.6 GAPW 输入片段（T19 P25，照抄可运行）

```text
&QS
  EXTRAPOLATION       ASPC        ! ASPC 外推（MD 场景）
  EXTRAPOLATION_ORDER 4
  METHOD              GAPW
  EPS_DEFAULT         1.0E-12     ! 注意：比 GPW 卡的 1.0E-10 更紧
  QUADRATURE          GC_LOG      ! 径向求积方案
  EPSFIT              1.E-4       ! hard/soft 高斯指数拆分
  EPSISO              1.0E-12
  EPSRHO0             1.0E-8
  LMAXN0              4
  LMAXN1              6
  ALPHA0_H            10         ! hard 补偿电荷的指数
&END QS
```
逐 kind 另加 `LEBEDEV_GRID 80` / `RADIAL_GRID 200`（原子区球面/径向网格）。
关键字语义 → 指针：G 层 `23_dft_subpages_full.md`（GAPW 小节）、`02_dft_methods.md` §1.2、
`21_xray_spectroscopy_full.md`（同一组参数的另一种取值：`EPSFIT 1.E-4`、`LMAXN0 4`、`ALPHA0_H 10`、
`QUADRATURE GC_LOG`、`RADIAL_GRID 80` / `LEBEDEV_GRID 120`）。

### 4.7 非 GPW 专属但可照抄的两张卡

**OT（T19 P32）**：`EPS_SCF 1.01E-07` + `&OUTER_SCF MAX_SCF 20 / EPS_SCF 1.01E-07` +
`SCF_GUESS RESTART` + `MAX_SCF 20` + `&OT MINIMIZER DIIS / PRECONDITIONER FULL_ALL`。

**金属 SCF（T19 P43）**：`MAX_SCF 50` / `EPS_SCF 1.0e-7` / `EPS_DIIS 1.0e-7` /
`&SMEAR METHOD FERMI_DIRAC ELECTRONIC_TEMPERATURE 500.` /
`&MIXING METHOD BROYDEN_MIXING ALPHA 0.6 BETA 1.0 NBROYDEN 15` / `ADDED_MOS 20 20` /
`&XC_FUNCTIONAL PBE` + `&vdW_POTENTIAL DISPERSION_FUNCTIONAL PAIR_POTENTIAL &PAIR_POTENTIAL
TYPE DFTD3 PARAMETER_FILE_NAME dftd3.dat REFERENCE_FUNCTIONAL PBE`。
（金属 SCF 的更完整决策 → 指针：G 层 `03_scf_convergence.md`、A 层 `decide.md` §6。）

---

## 5. 【新】相对既有 A–G 层的增量

> 写之前已 grep A–G 全部 `.md`（`official/*.md`、`decide.md`、`playbook.md`、`manual_notes.md`、
> `course_learned.md`、`course_notes.md`、`course_survey.md`、`sections.md`、`postprocess.md`、
> `workflow.md`、`gen_inp_options.md`）。以下各项**确认零命中或仅有标题级登记**。

| # | 增量内容 | 页码出处 | grep 证据（A–G 现状） |
|---|---|---|---|
| 1 | **ripples**：网格平移不变性破缺 ⇒ 能量超曲面被小调制 | T01 P24（+P25 的三项修正） | A–G 中 `ripple` **零命中** |
| 2 | **GPW 能量表达式的完整形式**与"只对 GTO 系数变分"的变分性说明 | T01 P25；T19 P17 | G 层只有文字层面的"collocation/integration 机会主义切换"（`02_dft_methods.md` §1.1），**没有公式与变分性说明** |
| 3 | **三级 screening 的具体内容** + `EPS_DEFAULT` 控制筛选阈值 + **两类阈值故障**（Cholesky 失败 / 网格电荷不准） | T01 P26–P27 | A–G 中"Cholesky 分解失败"**零命中**；G 层只有 `PREFERRED_CHOLESKY_LIBRARY` 这类性能关键字 |
| 4 | **高斯基函数积分要多少点**：指数 1、10⁻¹⁰ 精度 ⇒ **10 bohr 范围 + 25 Ry cutoff + 22 积分点 ⇒ ~5000 点/批次** | T01 P30；T19 P15（复述） | A–G 中 `5000 integration` / `10 bohr` **零命中** |
| 5 | **`N_PW ≈ (Ω/2π²)E_cut^{3/2}`**：PW 基组大小只取决于体积与 cutoff | T01 P19 | A–G 中 `N_PW` **零命中** |
| 6 | **采样定理给出的实空间网格下限**（`f_c = 1/(2Δ)`） | T01 P20 | 无 |
| 7 | **多重网格分配规则**：`E_cut,i = E_cut,1/α^{i−1}`；**指数决定层归属**；**每高斯点数与指数无关**；**指数 1 ↔ 相对 cutoff ~30 Ry** | T19 P15 | A 层只有"`REL_CUTOFF` 太低会把高斯压到最粗网格"的**结论**（`decide.md` §7），无机制 |
| 8 | **多重网格实测表**（体相 Si，8 原子，a=5.43 Å，100 Ry/60 Ry；`MULTIGRID INFO` 输出；50→500 Ry 的 10 行数据与 grid-1 从 5048→0 的重组现象） | T19 P16 | A–G 中无此表；G 层 `03_scf_convergence.md` 只有官方 cutoff 教程的误差表 |
| 9 | **`NGRIDS 1` 的真实价格**：8–25 倍慢、能量不变（64 水/LDA/24 核全套 10 行数据） | T01 P37 | A/C 层只有"`NGRIDS 1` 速度会非常慢"的定性说法，**无倍数、无出处表** |
| 10 | **Fourier 插值产生负密度、multigrid 加重**，以及按泛函阶梯的 `DENSITY_CUTOFF`/`GRADIENT_CUTOFF`/`TAU_CUTOFF` 出口 | T01 P33 | A–G 中 `negative densit` / `DENSITY_CUTOFF` / `GRADIENT_CUTOFF` / `TAU_CUTOFF` **全部零命中** |
| 11 | **BSSE 的机理页 + Counterpoise 公式**（片段取团簇几何）与液水 BSSE–基组关系 | T01 P38–P39 | G 层确认"官方手册有 BSSE 词条但无校正章节"（`18_...` §2）；**机理与公式无出处**，本层补上 |
| 12 | **NLCC 的物理动机与两种出路**（semi-core vs 加芯电荷），以及"XC 线性化假设在碱金属/过渡金属失效" | T01 P43、P51–P52 | G 层只登记了 `NLCC_POTENTIALS` 文件名与"非线性芯校正"四字（`14_basis_and_potentials.md` §2.4），**无动机与判据** |
| 13 | **MOLOPT 条件数实测表**（`logκ`，含 aug- 系列对比）与"aug- 抬高一个量级"的结论 | T01 P56 | A–G 中 `condition number` / `m-SZV` **零命中** |
| 14 | **MOLOPT 家族参数表**（`m-SZV(1s1p) … m-TZV2PX(3s3p2d1f)`、氢的对应、**6/7 原始函数**、**大基组扩展小基组**） | T01 P55 | A–G 无此表（G 层 `14_...` 只讲命名与库） |
| 15 | **GTH 赝势的显式解析形式**（`V_loc` 的 erf + 多项式形式、投影子高斯形式）与"完全非局域 ⇒ 解析积分与 FFT 都容易" | T01 P50；T19 P11 | G 层只有文献引用与"模守恒 GTH"一句 |
| 16 | **Kleinman–Bylander 的计数代价**："s+p 非局域势需要 4×态数 个积分" | T01 P49 | 无 |
| 17 | **GAPW 密度分区的两条匹配条件**（间隙区/原子区各两条）与 `n = ñ + Σ_A(n_A − ñ_A)` 的精确含义 | T19 P20 | G 层 `02_dft_methods.md` §1.2 只有"平滑部分留在网格、核附近用原子中心贡献"的**一句话概述**；**匹配条件无出处** |
| 18 | **GAPW 的补偿电荷机制**：`n⁰ = Σ_A Σ_L Q_A^L g_A^L`、`Q_A^L` 的球面积分定义、"与局域密度相同的多极展开"、以及 `V[ñ+n⁰]+V[n+n⁰]−V[ñ+n⁰]` 三项抵消奇异性的用意 | T19 P23 | A–G 中无"补偿电荷"（compensation charge）内容 |
| 19 | **`n_A` 来自投影而非重算**：`χ_μ^A = Σ_α d_μα^A g_α`、`P^A_αβ = Σ_μν P_μν d_μα^A d_νβ^A` | T19 P21 | 无。这是"GAPW 是 PAW 式、比全电子便宜"的**机制级证据** |
| 20 | **GAPW 泛函三项分解**：`E_xc[ñ] + Σ_A(E_xc[n_A] − E_xc[ñ_A])`；`E_H[ñ+n⁰] + Σ_A(E_H[n_A+n_A⁰] − E_H[ñ_A+n_A⁰])`；分别对应"全局网格 collocation+FFT / 解析积分 / 局域球面网格" | T19 P22、P24 | G 层无公式级内容 |
| 21 | **GAPW 的输入卡原型**（含 `QUADRATURE GC_LOG`、`EPSFIT 1.E-4`、`EPSISO 1.0E-12`、`EPSRHO0 1.0E-8`、`LMAXN0 4`、`LMAXN1 6`、`ALPHA0_H 10`、`LEBEDEV_GRID 80`、`RADIAL_GRID 200`，以及"赝势路线 vs `POTENTIAL ALL` 路线"并列） | T19 P25 | G 层 `21_...` 有同一组参数的**另一套取值**，但**没有"两条路并列"的教学对照** |
| 22 | **GAPW 相对 GPW 的容差差异**：T19 P18 GPW 卡 `EPS_DEFAULT 1.0E-10` vs P25 GAPW 卡 `1.0E-12` | T19 P18、P25 | A 层 §15 只说"调紧会增大 CUTOFF 需求"，**无教材侧的标准取值对照** |
| 23 | **`XC_GRID` 的负密度对策写法**：`XC_DERIV SPLINE2_smooth` + `XC_SMOOTH_RHO NN10` | T19 P18 | G 层 `21_...` 用的是 `XC_DERIV NN50_SMOOTH` + `XC_SMOOTH_RHO NN50`（XAS 场景），**SMOOTH2/NN10 这一组与"抑制负密度"的因果链是新的** |
| 24 | **每步 SCF 的实空间积分完整链路图**（含 `∇n` 的数值梯度与 `H^HXC_μν = Σ_R V_HXC(R)φ̄_μν(R)`） | T19 P14；T01 P34 | G 层 `02_dft_methods.md` §1.1 只有"collocation / integration"两个词 |
| 25 | **CP2K 基组/势文件的全目录清单**（`cp2k/data/` 25 项，含 `BASIS_ZIJLSTRA`、`t_c_g.dat`、`t_sh_p_s_c.dat` 等） | T19 P9 | G 层 `14_basis_and_potentials.md` 只列常用若干；**全目录清单是新的** |
| 26 | **"赝势价电子数 ↔ 基组 ↔ 物理量"对照**（Rh：17e/9e × Q17/DZVP/SZVP/SZV 的 `a`、`B`、`E_s`、`W`） | T19 P39 | 无 |
| 27 | **GPW 标度三条式**（KS 矩阵 `O(M log N)`、密度矩阵 `O(MN)`、OT `O(MN²)`）与 GGA 效率标尺（1/10/50 ps/day） | T01 P66–P68；T19 P30（`O(N²M)` CPU / `O(NM)` 内存） | A–G 无标度的显式表达式 |
| 28 | **Kohn–Sham 线性标度式** `P = sign(S⁻¹(H−μI))S⁻¹` + Newton–Schultz 迭代（只需矩阵乘法） | T01 P69 | A–G 中 `Newton-Schultz` **零命中** |

**属于本层但"已有更贴实操版本"、故只写指针的**：
`CUTOFF/REL_CUTOFF` 收敛流程（G `03_scf_convergence.md` §第二部）、
`NGRIDS` 选择法（G `08_errors_and_faq.md` §3.6）、
GAPW 何时用（G `02_dft_methods.md` §1.2 + A `decide.md` §15）、
基组/赝势现代命名（G `14_basis_and_potentials.md`）、
金属 SCF 与 smearing（G `03_...` + A §6）、OT 输入（A §22）。

---

## 6. 与既有层的冲突 / 纠错

> 以下 4 条是**教材原文与 A–G 层表述不一致**的地方。铁律是"冲突以 G 层裁定"，
> 但这里的分歧**恰恰是 G 层没写的部分**（教材讲机理、G 层讲条目），
> 所以逐条给出**页码证据**与"应改成什么"。

### 6.1 `REL_CUTOFF` 的定义：A 层的描述不够准确（应补机制）

- **A–G 现状**：A 层 `decide.md` §7 写"**REL_CUTOFF**：高斯函数映射到哪层网格的参考截断（Ry）。
  **它太低会让所有高斯被压到最粗网格**"。
- **教材原文**：`T01 P32` 把 `REL_CUTOFF` 定义为
  "**Minimal cutoff used for Gaussian with exponent of 1（指数为 1 的高斯所用的最小 cutoff），默认 40 Ry**"；
  `T19 P15` 给出分配规则"**高斯乘积的指数决定它落在哪一层网格**"，
  并标出"Relative Cutoff ~30 Ry"（指数为 1 处）。
- **问题**：A 层的"**所有**高斯被压到最粗网格"不准确——**只有小指数（弥散）高斯**会被推到粗网格，
  大指数（紧）高斯本来就去细网格。T19 P16 的表是最直接的反例：
  `REL_CUTOFF` 固定 60、`CUTOFF = 50 Ry` 时 grid 1 上仍有 **5048** 个高斯（并非 0）。
- **应改成**：`REL_CUTOFF` 是**以"指数为 1 的高斯"为标尺**的截止；低于它，**小指数高斯**
  会落到过粗的网格上，导致积分误差；大指数高斯不受影响。
  机制出处 `T19 P15`、定义出处 `T01 P32`、数据反例 `T19 P16`。

### 6.2 "只增 CUTOFF 不增 REL_CUTOFF 收敛变慢"：结论对，但机制要换

- **A 层现状**（`decide.md` §7）："若只增 CUTOFF 不增 REL_CUTOFF，**细网格上高斯数反而减少**，收敛变慢。"
- **教材证据**：`T19 P16` 的表**支持这条**（REL_CUTOFF 固定 60，CUTOFF 100→450 Ry 时
  grid 1 上的高斯数 **2720 → 0**，grid 4 从 16 → 5448）。
- **但 A 层没说"为什么"**，容易读成"细网格没用了"。正确的机制是
  `T19 P15` 的两条规则：**① 层 cutoff 按 `α^{i−1}` 递减；
  ② "每个高斯的网格点数与指数无关"**。
  所以提高 `CUTOFF` 只是把**整个指数标尺拉长**，高斯按指数重新洗牌到各层；
  真正决定"每个高斯被多少点采样"的是 `REL_CUTOFF`。
- **应改成**：保留结论，补上机制句与出处（`T19 P15–P16`）。

### 6.3 GAPW 是否必须 `POTENTIAL ALL` + 全电子基组：A 层与 G 层的表述需要在**同一段里区分两条路线**

- **A 层现状**（`decide.md` §15）：明确写过"**注意**：CP2K GAPW 仍使用 **GTH 赝势 + 常规轨道基组**…
  **并非换 `POTENTIAL ALL`**"，并记录了这句纠错的历史（`manual_notes.md` 批次 8）。
- **G 层现状**：`02_dft_methods.md` §1.2 与 `14_basis_and_potentials.md` §2.4/§2.6 写的是
  "全电子 GAPW 还需要全电子基组与 `POTENTIAL ALL`"、"对全电子计算，用 `POTENTIAL ALL` +
  全电子基组 + GAPW 三件套"。
- **教材证据（T19 P25，一页之内同时给出两条路）**：
  - `&KIND O`：`BASIS_SET DZVP-MOLOPT-GTH-q6` + `POTENTIAL GTH-BLYP-q6` + GAPW 参数 →
    **GAPW 配赝势，合法且是教材的首选示范**；
  - `&KIND O1`：`BASIS_SET 6-311G**`（注释里的备选 `6-311++G2d2p`，均为 EMSL 全电子基组）+
    `POTENTIAL ALL` + 同一套 GAPW 参数 → **GAPW 配全电子，也合法**。
  另外 `T19 P19` 的方法谱系页把 GAPW 归到 **PAW / augmented PW** 一支，
  而 PAW 的整个卖点就是"用赝势框架达到全电子精度"。
- **冲突判定**：两者**都对，但适用条件不同**，任何一边单独写都会误导。
- **应改成**（建议给 A 层 §15 补一句、给 G 层 §1.2 补一句，两处互相交叉引用）：
  > GAPW **不必**换全电子：它可以照旧用 **GTH 赝势 + 常规轨道基组**
  > （教材示范 `DZVP-MOLOPT-GTH-q6` + `GTH-BLYP-q6`，`T19 P25`），
  > 此时 GAPW 的价值在于**用原子中心局域基组把核区密度补回来**
  > （`n = ñ + Σ_A(n_A − ñ_A)`，`T19 P20–P21`）；
  > 只有在**必须做全电子**时，才额外要求 **`POTENTIAL ALL` + 全电子基组**
  > （教材示范 `POTENTIAL ALL` + `6-311G**`，同一页 `T19 P25`；G 层 `14_...` §2.4/§2.6）。
  > 两条路都要逐 kind 给 `LEBEDEV_GRID` / `RADIAL_GRID`。

### 6.4 `EPS_DEFAULT` 在 GAPW 下的标准档：A 层缺一个"教材对照值"

- **A 层现状**（`decide.md` §15）：只说"GAPW 专属精度参数 `EPSFIT`/`EPSRHO0`/`EPSSVD` 控制硬/软密度拆分；
  **调紧会增大 CUTOFF 需求**"，**没有给出该设成多少**。
- **教材证据**：**同一份讲义的两张卡**（`T19 P18` vs `T19 P25`）：
  GPW 用 `EPS_DEFAULT 1.0E-10`，GAPW 用 **`EPS_DEFAULT 1.0E-12`**。
- **应改成**：建议在 A 层 §15 补一句"教材在 GAPW 场景把 `EPS_DEFAULT` 收到 **1E-12**
  （GPW 示例为 1E-10），`T19 P18`/`P25`"，与 G 层 `17_constrained_dynamics_and_paths.md`
  里官方 GAPW 示例的 `REL_CUTOFF 100` / `NGRIDS 5` 一起构成"GAPW 就是更贵"的量化说明。

---

## 7. 存疑

> 本节原为**未决清单**。本轮已**逐条查证**：能定案的写成「✅ **已定案** + 依据」；推翻原文猜法的另附
> **更正记录**（留痕，不静默改写）；本地手段不足以定案的改写成
> 「⚠️ **未能确证，已排除…/仍不确定的是…/要确证需要…**」三段式，**不硬编结论**。
> 查证手段一律是**只读**源 PDF / 官方 XML / 真实 `.out`；可复现命令见本节末尾「查证手段」。

1. ✅ **已定案**：**那一列的 `x` 是幻灯片作者自己敲的占位符，不是"被遮挡/未提取的整数位"。**
   - 该页文本层里每个能量值的首字符就是**小写拉丁字母 x**：`text='x'`、`u0078`、字体
     `TURRKN+NimbusSanL-Regu`、`size=10.9`、`x0=267.5`、`top=101.3`；**同一个字体**在
     `EPS_DEFAULT` 列里渲染的负号是 `u002d`（`x0=63.9`）——所以不是"字体把负号映成了 x"。
     整列 13 个字符**两端对齐**（每行首字符 x0=267.5、末字符 x1=336.6 完全一致），
     字段宽度刚好容下 `x.dddddddddd`。
   - 把该页**渲染成图**肉眼核对（pypdfium2，scale=4）：幻灯片上印的就是 `x.0377660911`
     …`x.0371287675`，作者用 `x` 把总能量的整数位**故意隐去**（该页只讲精度差异）。
   - **更正记录**：原文写「"x." 是幻灯片上被遮挡或未提取的整数位」——错在把**作者占位符**
     当成了**抽取缺陷**。逐字符 + 渲染双重核对后，`x` 是真实字形。
   - 后果：原文「本笔记只引用相对变化，不引用绝对值」的做法**依然正确且必要**——不是
     因为抽不出来，而是因为**幻灯片上本来就没有绝对值**。（表格数字可直接引，见 §2 表。）

2. ✅ **已定案**：**该页公式确为 `E_cutoff = π²/(2h²)`，原文的判断正确。**
   - 证据一（图注，同一页）：`The relation E_cutoff = π²/(2h²) is used throughout this work
     to convert the grid spacing h to the corresponding plane wave cutoff.`（Fig. 1 的图注，
     `txt/T19_iannuzzi_zurich2017.txt` P13 末段）。
   - 证据二（逐字符坐标，定死分子分母）：分子是 `CMMI8` 的 **π**（该字体的 π 没有 ToUnicode，
     被抽成 `\x00`/丢字）带上标 `2`（`CMR6`，`top=842.3`）；随后 `=`；分母是 `2h²`
     （`CMR8` 的 `2` + `CMMI8` 的 `h` + `CMR6` 的 `2`，三者 `top=852.5`，即**下标位置**）。
     于是文本层里的 `E = 2` / `2h2` 只是"π 与上下标丢字"后的残骸。
   - **无更正**（原文猜对了），只是把「未在原文中逐字确认」升级为**已逐字确认**；
     并记录一条可复用经验：`T19` 里 `\x00` 多为 **CMMI/CMSY 数学字体的希腊字母**。
   - ⚠️ **顺带更正一处指针**（**本节未改那段文字**，按维护约定留给维护者）：本文件末尾附录写
     `T19` 的 NUL「来源是这些 PDF 的公式字体把**空格**提取成 `\x00`」——至少本次逐字符核对的
     那几处**不是空格**：P13 的两处分别是 **π** 与 **`cutoff` 的 `ff` 连字**（`cuto`+`\x00`=
     `cutoff`）。建议把那句改为「公式字体的**非 ASCII 字形/连字**丢 ToUnicode 映射」；
     `02_aimd_bomd.md` §7#6 另有 T04「`Φ` + 减号」两类的完整实证可一并参考。

3. 部分定案 + 收窄（三层结论，最后一层仍不确定）：
   - ✅ **已定案（抽取层）**：幻灯片上**逐字**就是 `Pt p peaked at 3.9Å`、`s peaked at 2.4Å`、
     `d peaked at 1.3Å` —— 单位符号是**原文印的**：字符层里 `˚`(u02da)+`A`（`top` 比正文高
     1.2 pt，即上标 Å），渲染图肉眼也确认。**更正记录**：原文「未逐字核对 PDF，存疑」→
     现已核对，**文字与单位都不是抽取假象**。
   - ✅ **已定案（来源层）**：这一页**不是本教程自己的内容，是借用的幻灯片**。该页页脚写着
     `Marialore Sulpizi` / `Density Functional Theory: from theory to Applications`
     （T19 P10 文本层，行首即署名）。所以这些数字与 CP2K/GPW 所用的 **GTH 赝势没有直接关系**。
   - ✅ **已定案（定量反证）**：拿 CP2K 自己的 GTH 数据对照——官方仓库
     `data/GTH_POTENTIALS` 里 Pt 的 `GTH-PADE-q18`（= `GTH-LDA-q18`）参数为：
     `r_loc = 0.50` bohr；三个非局域通道半径 `r(s) = 0.40994`、`r(p) = 0.39865`、
     `r(d) = 0.36796` bohr（**0.195–0.217 Å**）。而幻灯片给的是 **1.3 / 2.4 / 3.9**：
     按 Å 读就等于 0.69 / 1.27 / 2.06 bohr，按 bohr 读就是 1.3 / 2.4 / 3.9 bohr ——
     **两种读法都比 GTH 的 r_l 大 3–20 倍**。⟹ 这些数字**不可能是 GTH 的 r_l 或"角动量势峰位"**，
     原文"疑为 bohr 排版笔误"的方向**也不足以解释**（换成 bohr 仍然对不上 GTH）。
   - ⚠️ **仍不确定的是**：该页原本指的是**哪一族赝势**（NC / Troullier–Martins 的 `r_c`？）
     以及其**真实单位**。**要确证需要**：Sulpizi 那门课的原始课件（本次尝试的
     `https://www.staff.uni-mainz.de/sulpizi/teaching_files/abinitio_3.pdf` 已 **404**），
     或该图的原始出处文献。
   - **建议**：引用时按"**借页 + 单位可疑 + 与 GTH 无关**"处理，不要用它支撑任何
     GTH/CP2K 参数说法。（笔记 §2.1 已按此口径标注。）

4. ✅ **已定案**：**两个公式都读通了**，且原文把它称作"cutoff–指数关系"的说法需要更正。
   - 多网格：**`E_cut^i = E_cut^1 / α^(i−1)`，`i = 1..N`**（几何级数，公比 α）——与原文
     「几何级数递减」一致。
   - 那个"残缺公式" `⇥ = 1/2·` 实为 **`σ_p² = 1/(2η_p)`**（**高斯积的方差**，
     `σ`、下标 `p`、`η` 都来自 CMMI/CM 数学字体，故抽取残缺）；它旁边就是绿框
     `Accuracy => Relative Cutoff ~30 Ry`，两者一起说明"**由高斯积的指数决定该用哪一级网格**"。
     **更正记录**：原文称其为"cutoff–指数关系…残缺公式，不引用"——它其实**不是** cutoff 公式，
     而是高斯积方差公式；现已把正确形式写进本条（§2.2 引用的两条规则无需改）。
   - 同页其余内容照录：右上三联小图（纵轴 Error `1e-15…1e-3`，三个横轴分别是
     `Integration range` / `Cutoff (Ry)` / `Integration Points`，黑线画在 `1e-12`，
     并标注 `Exponent = 1`）；左下 `Number of pairs` vs `Exponent`（0–8，峰值 ~7×10⁴）；
     右下 FFT 映射示意 `n_j^f = I_j(n_i^c)`；文字
     "with exponent 1 an accuracy of 10⁻¹⁰ requires an integration range of 10 bohr,
     a cutoff of 25 Rydberg, resulting in 22 integration points" 与
     "5000 integration points/integral batch"。

5. ✅ **已定案**：**两种展开都在 PDF 里，而且是"叠在同一坐标的两个文本层"**（不是抽取幻觉，
   也不是"两种官方展开"）。
   - 同一页（T19 P34）按 `top` 聚行后能看到**四层标题**：`top=-55` 的 `DBCSR: a sparse matrix
     library`（已越出页面）、`top=1.0` 的 `Distributed Blocked Compressed Sparse Row`、
     `top=22.0` 的 **`Distributed Blocked Cannon Sparse Recursive`**、`top=31` 的
     `Sparse Matrix Library`，以及 `top=122` 的（渲染图上唯一可见的）
     `DBCSR: Distributed Blocked Compressed Sparse Row`。
   - 隐藏层还带**另一套要点**：`Optimized for the science case: 10000s of non-zeros per row.` /
     `The dense limit as important as the sparse limit.` / `Cannon style communication on a
     homogenized matrix for strong scaling` / `Borstnik et al. : submitted`；可见层则是
     `For massively parallel architectures` / `Optimised for 10000s of non-zeros per row` /
     `Stored in block form` / `Cannons algorithm: 2D layout (rows/columns)…` / `Homogenised for load balance`。
   - ⟹ 结论不变：**以标准展开 "Distributed Blocked Compressed Sparse Row" 为准**
     （G 层 `09_build_libraries.md` 同）。**更正记录**：原文猜"疑为幻灯片动画/前版的残留"——
     方向对，现升级为**确认**：同页确实存在"前一动画状态"的文本对象；"Cannon"一词来自
     同页要点 `Cannons algorithm`（Cannon 矩阵乘法算法），是那一层把它并进了缩写展开。

6. ✅ **已定案**：**渲染图逐字确认该页就是那样写的**，"功能示范卡、不能直接投产"的判断正确。
   - 左栏 `&QS` 里 `EPS_DEFAULT 1.0E-12` **确实出现两次**（第 3 行与第 5 行），
     之间夹着 `METHOD GAPW`；同段还有 `EXTRAPOLATION ASPC`、`EXTRAPOLATION_ORDER 4`、
     `QUADRATURE GC_LOG`、`EPSFIT 1.E-4`、`EPSISO 1.0E-12`、`EPSRHO0 1.E-8`、
     `LMAXN0 4`、`LMAXN1 6`、`ALPHA0_H 10`。
   - 右栏同时并列**两条路线**：`&KIND O` + `BASIS_SET DZVP-MOLOPT-GTH-q6` +
     `POTENTIAL GTH-BLYP-q6`（**赝势**）与 `&KIND O1` + `ELEMENT O` +
     `# BASIS_SET 6-311++G2d2p` / `BASIS_SET 6-311G**` + `POTENTIAL ALL`（**全电子**），
     两者都给 `LEBEDEV_GRID 80` / `RADIAL_GRID 200`。
   - 页面只给了 `&DFT … &END DFT` 与 `&SUBSYS … &END SUBSYS` 两个**片段**（各带 `...`），
     确实**不含** `&FORCE_EVAL`/`&GLOBAL`/`&MOTION`/`&CELL`/`&COORD`/`&SCF` ⟹ 照抄要补齐。
   - **补一条可用事实**（`python _kw_probe.py --find <名>`）：卡里 7 个 GAPW 关键字在**现行**
     官方 XML 里都合法，且默认值是 `EPSFIT 1e-4`、`EPSISO 1e-12`、`EPSRHO0 **1e-6**`、
     `EPSSVD 1e-8`、`LMAXN0 2`、`LMAXN1 −1`（自动）、`ALPHA0_HARD 0`（**`ALPHA0_H` 是它的别名**）、
     `QUADRATURE GC_LOG` ⟹ 这张卡把 `EPSRHO0`（1e-6→1e-8）、`LMAXN0`（2→4）、`LMAXN1`（自动→6）、
     `ALPHA0_H`（0→10）都**收紧**了，其余取默认。这也顺便给了 §6.4"GAPW 就是更贵"的量化注脚。

7. ✅ **已定案（且内容已取出）**：**P47/P48 不是空白页，是两张整页位图**，图上内容可读。
   - 机制：`chars = 0`、`images = 1`（bbox 几乎满页 68–298 × 22–255 pt）⟹ 文本层为空是
     "**整页是一张图片**"造成的，不是页被删/页损坏。
   - **P47 = "Silicon: Radial densities"**：纵轴 `4πr²n(r) (bohr⁻³)`、横轴 `r (bohr)`；
     曲线 `pseudo valence`（实线，峰在 r≈1.7 bohr、高约 2）与 `true core`（虚线，峰在
     r≲0.5 bohr、高约 13）。
   - **P48 = "Silicon: ionic pseudo potentials"**：纵轴 `V^PS(r) (hartree)`、横轴 `r (bohr)`；
     三条通道曲线标注 `0 r_c=1.703`、`1 r_c=1.878`、`2 r_c=2.021`（l=0,1,2 的芯半径，单位 bohr）。
   - **更正记录**：原文两处都错——①「内容不可考」：错，渲染出来就能读（正是"赝价密度 vs
     真实芯密度"与"l 依赖离子赝势"的数值插图）；②「推测 P47–P48 是 KB 形式的推导图」：错，
     这两页是在给 P46（半局域赝势的局域/非局域分拆）配**数值例子**，为 P49 的 Kleinman–Bylander
     形式做铺垫。**未改 §1–§6 正文**（正文未涉及这两页的内容）。
   - 同类还有一页原文**漏登记**：**P61**（`chars=0`、1 张满页图）。渲染出来是
     **`OT versus Diag-DIIS`** 的 SCF 收敛对比图：纵轴 `convergence (energy a.u.)`
     `1e-01…1e-07`、横轴 `time (s)` 0–20000；三条曲线 = `OT`（圆点）、另一条 OT 型曲线
     （菱形）、`DIIS`（十字）；图内注 `256 H2O TZV(2d,2p) 10240 BF on 4 CPUs SUN ultrasparc`。

8. 部分定案 + 更正（名单需修正）：
   - ✅ **T01 实测**：全 73 页里文本 < 120 字符的有 **15 页**：`P1`（标题页）、`P16`、`P28`、
     `P31`、`P35`、`P36`、**`P47`、`P48`、`P61`（这 3 页 `chars=0`，纯整页图）**、`P67`、
     `P68`、`P70`、`P71`、`P72`、`P73`。
   - **更正记录（三处）**：① 原名单里的 `P39`、`P68` **不止标题** —— P39 还有坐标轴刻度
     （0–7 与 −30–0）、轴标签 `Binding energy [kcal/mol]` / `BSSE [kcal/mol]` 与图例
     `DZVP`/`TZV2P`/`QZV2P`/`QZV3P(f,d)`；P68 还有 `1 ps/day` / `10 ps/day` / `50 ps/day`。
     ② 漏登记 `P61`（纯图页，内容见上条：`OT versus Diag-DIIS` 收敛图）与
     `P1`/`P16`/`P28`/`P31`/`P72`/`P73`。
     ③ **"T19 的多数图页只有标题"不成立**：T19 全 43 页**没有一页**文本 < 120 字符
     （最短的 `P32` 也有 176 字符），多数页带完整正文/图注（如 P13 带 Fig. 1 的整段图注）。
     即"纯标题页"是 **T01 的现象**，不是 T19 的。
   - 结论方向不变：这些页的**数值都在图形里**，要引用就得读图（本轮已把 §7 各条需要的图读完）。

9. ✅ **已定案（登记准确，附页题清单备查）**：`T19 P26–P43` 确实越出 GPW/GAPW 主题，
   本笔记"只做页码登记与最小要点、未逐页展开"是**有意识的取舍且取舍正确**。
   - 逐页首行（本次按页统计）：`P26` Energy Functional Minimisation、`P27` Traditional
     Diagonalisation、`P28` Orbital Transform、`P29` Preconditioned OT、`P30` OT Performance、
     `P31` "But OT is hard to beat !"、`P32` OT input、`P33` Linear Scaling SCF、`P34` DBCSR、
     `P35` Millions of atoms、`P36` Metallic Electronic Structure、`P37` Smearing & Mixing in
     G-space、`P38` Iterative Improvement of the n(r)、`P39` Rhodium: Bulk and Surface、
     `P40`/`P41`（见下）、`P42` Large metallic systems、`P43` SCF for Metals。
   - **ELPA（P40–P41）登记的"论文截图"说法也对**，并已可细化：
     `P40` = **T. Auckenthaler et al., Parallel Computing 37 (2011) 783–794** 的论文页截图
     （带**可抽取文本 14216 字符**！本次实测），页面上还叠了讲师加的要点
     （`Parallel performance depends on data locality and scalability`、`>70% in eigenvalue solver`、
     `ScaLAPACK need improvements in numerical stability, parallel scalability, and memory
     bandwidth limitations`、`Syevd: D&C` / `Syevr: MRRR`）；`P41` = Bruno Lang
     《Eigenvalue Solvers—The ELPA Project and Beyond》15/31 页截图（含 CRAY-XE6 基准数字
     与 `atom=480; Nel=6000; nmo=7400; nao=14240` 这类标注）。
   - ⟹ 若将来要补 ELPA 一节，`P40` 的文本层**可当论文原文引用**（不必再找原刊）。

10. 一条定案 + 一条收窄（原来把两条绑在一起说"都未出现"，现在要分开处置）：
    - ✅ **已定案（第 1 条故障名）**：`Failure in Cholesky decomposition of overlap matrix`
      **不是** CP2K 的运行时字符串。官方 FAQ 里这个故障的真实输出是 **`CPASSERT failed`** +
      调用栈 **`fm/cp_fm_cholesky.F:94`**（`prepare_preconditioner` 路径）：
      <https://www.cp2k.org/faq:cholesky_decomp_failed> ；cp2k-user 列表里另一条真实措辞是
      `Cholesky decompose failed: the matrix is not positive definite or ill-conditioned`：
      <https://lists.cp2k.org/archives/cp2k-user/2024-July/020489.html> 。
      G 层已收录前者（`official/08_errors_and_faq.md` §3.5，含同一段调用栈）
      ⟹ **诊断条目直接引 G 层**，不要引 T01 的这句转述。
    - ⚠️ **未能确证（第 2 条 `Inaccurate charge on real space grid`）**：
      **已排除以下可能**：它不是 G 层 `08_errors_and_faq.md` 的条目（本地 grep 零命中）；
      不在本 skill 收录的两个真实 `.out` 里（`cu100-h2o-opt/cp2k.out`、`cu100-h2o-aimd/cp2k.out`
      对 `Inaccurate` / `real space grid` 均零命中）；不在 `scripts/diagnose.py` 的关键字表里
      （对 `Cholesky`/`Inaccurate`/`real space` 零命中）；以精确短语做网络检索也只命中无关文档
      （如 Quantum ESPRESSO 讲义），**没有任何 CP2K 源码片段或报错实例**——检索入口例：
      <https://api.github.com/search/issues?q=repo:cp2k/cp2k+%22real+space+grid%22>
      只返回 18 条与该字符串无关的 issue/PR。
      **仍不确定的是**：CP2K 是否存在一条**语义相近但措辞不同**的"网格电荷不准/积分电子数偏差"
      警告，以及它的确切正文（本次无法查 CP2K 源码树）。**要确证需要**：一份出现该警告的真实
      `.out`，或 CP2K 源码 `src/qs_*.F`（如 `qs_rho_methods.F`、`qs_ks_methods.F`）的全文检索环境。
      **已查到的相关事实**（可供写诊断条目时兜底）：该页把两个故障都挂在"阈值"标题下，机理是
      "基组条件数 × `EPS_DEFAULT` 太大"与"PW cutoff 太小 / `EPS_DEFAULT` 太大"；现行默认值
      `FORCE_EVAL/DFT/QS/EPS_DEFAULT = 1.0E-10`、`FORCE_EVAL/DFT/MGRID/CUTOFF = 280 Ry`
      （`python _kw_probe.py <路径>`）。⟹ 写诊断项时这两条**只描述机理，不要写死字符串**。

---

### 查证手段（可复现，全部只读）

- 源 PDF 在 `D:\cp2k-aimd\study\庚子计算整理-cp2k资料-持续更新\`：`T01` = `【庚子计算整理】CP2K官方workshop课件练习资料\Gaussian and Plane Waves Method - Juerg Hutter.pdf`；`T19` = `【GPW和GAPW-庚子计算整理】iannuzzi_cp2k-tutorial-zurich2017.pdf`。**未改 `txt/`**。
- ① 单页重抽 + 逐字符坐标（pdfplumber 0.11.9）：
  `python -c "import pdfplumber,sys;d=pdfplumber.open(sys.argv[1]);p=d.pages[int(sys.argv[2])-1];print(p.extract_text());print([(c['text'],c['fontname'],round(c['x0'],1),round(c['top'],1)) for c in p.chars])" <pdf> <页号>`
- ② 渲染成 PNG 肉眼看图/看表（pypdfium2）：
  `python -c "import pypdfium2 as f,sys;f.PdfDocument(sys.argv[1])[int(sys.argv[2])-1].render(scale=4).to_pil().save('p.png')" <pdf> <页号>`
- ③ 关键字/别名/枚举/默认值：`python _kw_probe.py --find <名>`、`python _kw_probe.py <段/路径>`、`python _kw_probe.py --section <段>`。
- ④ 真实产出物：`study\…\cu100-h2o-opt\cp2k.out`、`…\cu100-h2o-aimd\cp2k.out`（行号见 §7 各条与 `02_aimd_bomd.md` §7）。

---

## 附：本层抽取层的两处修复（与内容无关，供维护参考）

- `T19_iannuzzi_zurich2017.txt` 原文含 **240 个 NUL 字节**（`T04` 49 个、`T05` 8 个、`T23` 114 个）。
  后果：读文件工具把 `.txt` 判为二进制而拒读（本次精读时实测），grep 也不友好。
- **修复**：`extract_tutorials.py` 增加 `clean()`（只把 `\x00` 换成空格，**不折叠空格**，
  以免破坏 pdfplumber 用空格做的缩进布局），并在写入前调用；随后用同一 `pdfplumber 0.11.9`
  **重新抽取了全部 24 份**，逐字节比对确认**除 NUL→空格 外无任何差异**，
  再把 T04/T05/T19/T23 四份替换回 `txt/`。
- ⚠️ **口径更正（原写"公式字体把空格提取成 `\x00`"，不准确）**：本笔记 §7 第 1/2 条与
  `02_aimd_bomd.md` §7 第 6 条的**逐字符核对**证明，NUL 位置原本是**数学字体的符号**，
  按字体分四类：`CMMI8`→**π**、`CMSS10`→**Φ**、`CMSY8`→**减号**（T04 的 45 处）、
  另有 **`ff` 连字**。⇒ "只当少了个减号"会漏掉"少了个 π"。
  **结论不变**：仍替换为空格、而不替换成具体字符（同一个 NUL 在不同页可能是不同符号，
  凭空补一个等于发明原文）。
- ✅ **README §5.1 已按上述四类口径改写**（含四类对照表），`clean()` 的 docstring 同步更新。
  **此项已闭环，不再是待办。**
