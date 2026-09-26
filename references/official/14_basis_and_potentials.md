# 14 · 基组、赝势与参数库（官方）

> **来源**：
> - <https://www.cp2k.org/basis_sets>（基组文件格式，官方逐行讲解）
> - <https://manual.cp2k.org/trunk/methods/dft/pseudopotentials.html>（赝势选择）
> - <https://github.com/cp2k/cp2k-data/blob/master/potentials/Goedecker/index.html>（GTH 赝势索引，官方数据仓库）
> - <https://cp2k.org/static/potentials/>（官方赝势下载页）
> - <https://www.cp2k.org/tools>（第三方基组工具）
> **抓取日期**：2026-09-09

---

## 0. 本文件补什么

上一轮 `02_dft_methods.md` 记录了"用哪套基组/赝势"的**选择**，但没有记录：

1. **BASIS_SET 文件格式**（官方有一页逐行讲解，非常具体）；
2. **GTH 赝势的完整元素/价电子清单**（官方数据仓库索引）；
3. **CP2K 自带的赝势库有哪几个文件、各自用途**；
4. 基组与赝势的**一致性检查**（官方给出 4 条）。

本文件补齐这四块。

---

## 1. 基组的数学构造（官方原文）

官方原文（`basis_sets` 页）：

> CP2K uses **Gaussian type orbitals** as basis functions. Every basis function has the following form: φ_i(r→)=R_i(r)⋅Y_{l_i,m_i}(θ,ϕ)
>
> Where R(r) denotes the radial part and Y_lm(θ,ϕ) spherical harmonics for the angular part. From a physical point of view the best choice for the radial part would be **Slater-type orbitals**. However, CP2K uses **contracted Gaussians** instead, because they have nicer analytic properties. Contracted Gaussians are simply a weighted sum of primitive Gaussians with different exponents: R_i(r)=r^{l_i} Σ_{j=1}^{N} c_{ij}⋅exp(−α_j⋅r²)

**要点**：
- 角向部分 = 球谐函数 `Y_lm`。
- 径向部分：物理上最优是 Slater 型，但 CP2K 用**收缩高斯**（因为解析性质更好）。
- 收缩高斯 = 若干不同指数的**原高斯**的加权和。

---

## 2. BASIS_SET 文件格式（官方逐行讲解）

官方用 `$CP2K_HOME/data/BASIS_SET` 中的硅条目作为例子，**逐行解释**。这是理解"为什么基组要这样写"的最佳材料。

### 2.1 官方示例（原样）

```
 1   # Silicon
 2   #
 3   # Z(nuc) = 14
 4   # Z(eff) = 4
 5   # E(ref) = -3.739451 a.u. (DZV)
 6   #
 7   Si DZVP-GTH-PBE
 8     2
 9     3  0  1  4  2  2
10           1.1815290892   0.3214648125   0.0000000000   0.0458533253   0.0000000000
11           0.4454622072  -0.2454343061   0.0000000000  -0.2633419994   0.0000000000
12           0.1674585747  -0.7952663455   0.0000000000  -0.5433222352   0.0000000000
13           0.0564288769  -0.1828967955   1.0000000000  -0.3560783416   1.0000000000
14     3  2  2  1  1
15           0.4500000000   1.0000000000
```

### 2.2 官方逐行解释（原文对照）

| 行 | 官方原文 | 含义 |
|---|---|---|
| **1–6** | "are comments, because they start with `#`" | 注释行（`#` 起始） |
| **7** | "specifies the element of the basis set (here: silicon) and the name of the basis-set (here: 'DZVP-GTH-PBE')" | **元素名 + 基组名** |
| **8** | "specifies the number of sets this basis set contains (here: 2)" | 该基组含**几个 set** |
| **9** | "specifies the composition of the first set." | 第一个 set 的组成 |
| **10–13** | "specify the coefficients of the first set. Each line consists of an exponent α_j, followed by contraction coefficients c_ij." | 每个 set 的**指数与收缩系数** |
| **14** | "specifies the composition of the second set." | 第二个 set 的组成 |
| **15** | "specify the coefficients of the second set." | 第二个 set 的系数 |

### 2.3 第 9 行的六个数字（官方逐个说明）

官方原文对第 9 行 `3  0  1  4  2  2` 的说明：

| 位置 | 官方原文 | 含义 |
|---|---|---|
| 第 1 个 | "specifies the *principal quantum number* (here: 3). Since this basis-set is meant to be used with pseudo-potentials, it does not contain the core electrons. **CP2K ignores this number.** It is merely present for compatibility reasons and documentation." | **主量子数**——**CP2K 忽略它**，只为兼容与文档 |
| 第 2 个 | "specifies the minimal angular quantum number l_min (here: 0)" | **最小角量子数** |
| 第 3 个 | "specifies the maximal angular quantum number l_max (here: 1)" | **最大角量子数** |
| 第 4 个 | "specifies the number of exponents N (here: 4)" | **指数个数 N** |
| 第 5 个 | "specifies the number of contractions for l=0 or s-functions (here: 2)" | **l=0（s）的收缩数** |
| 第 6 个 | "specifies the number of contractions for l=1 or p-functions (here: 2)" | **l=1（p）的收缩数** |

> **重要事实**：第 1 个数字（主量子数）**被 CP2K 忽略**。这解释了为什么同一元素的不同赝势（不同 `qN`）配同一基组时，基组文件里的主量子数可以不改。

### 2.4 基函数总数公式（官方给出）

官方原文：

> The entire set consists of Σ_{l=l_min}^{l_max} n_l⋅(l+1) basis functions. Each basis function consists of N terms - one for every exponent.

**第一个 set**（l 从 0 到 1，n_0=2，n_1=2）：

```
(2 × (0+1)) + (2 × (1+1)) = 2 + 4 = 8
```

官方明确写出"**The entire first set consists of the following 8 basis functions**"，并逐条列出 φ_1 … φ_8。

**第二个 set**（第 14 行 `3 2 2 1 1`：l_min=2, l_max=2, N=1, n_2=1）：

```
(1 × (2+1)) = 3 × ... 官方给的是 5
```

官方原文："The second set contributes the following 5 basis functions: φ_9 … φ_13"。

> **注**：官方在此处列了 5 个（d 轨道 5 个分量），与公式 `n_l×(l+1)` 对 `l=2` 给 `1×3=3` 不一致——这是**官方页面自身的表述问题**（d 轨道实际有 5 个球谐分量 `m=-2..+2`）。**G 层照录官方原文并标注**，不擅自改公式。

### 2.5 系数行的读法（官方举例）

官方原文：

> For example, line 10 starts with the exponent (1.181), followed by the two contraction coefficients for s-functions (0.321 and 0.0), followed by the two contraction coefficients for p-functions (0.046 and 0.0).

即一行 = `指数 α_j` + `s 收缩系数（n_0 个）` + `p 收缩系数（n_1 个）` + …

---

## 3. 赝势（官方 `pseudopotentials.html`）

### 3.1 主流选择：GTH 范守恒赝势

官方原文：

> Most GPW calculations in CP2K use **norm-conserving Goedecker-Teter-Hutter (GTH)** pseudopotentials. A pseudopotential removes chemically inactive core electrons from the explicit electronic problem and represents their effect on the valence electrons through an effective potential. This reduces the number of electrons and avoids the very hard core density that would otherwise require extremely fine grids.

**为什么用赝势**：去掉化学上不活跃的芯电子 → 减少电子数 + 避免"极硬的芯密度"（否则需要极细的网格）。

### 3.2 怎么指定（官方示例）

```
&FORCE_EVAL
  &DFT
    POTENTIAL_FILE_NAME GTH_POTENTIALS
  &END DFT
  &SUBSYS
    &KIND O
      POTENTIAL GTH-PBE-q6
    &END KIND
    &KIND H
      POTENTIAL GTH-PBE-q1
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

- **赝势文件**用 `DFT/POTENTIAL_FILE_NAME` 指定。
- **具体赝势**用每个 `KIND` 的 `POTENTIAL` 指定。

### 3.3 官方明确的陷阱：`POTENTIAL` 关键字 vs `POTENTIAL` 段

官方原文：

> Do not confuse the `POTENTIAL` *keyword* with the identically-named `POTENTIAL` *section* that also defines a pseudopotential. Their distinction is that the *keyword* takes the type and name of the potential, while the *section* takes the complete specification and data in an internal format. Specifying only the *keyword* as is done above suffices for most practical usage.

| 形式 | 内容 | 用途 |
|---|---|---|
| `POTENTIAL GTH-PBE-q6`（**关键字**） | 赝势的**类型与名称** | **日常用法** |
| `&POTENTIAL ... &END POTENTIAL`（**段**） | 完整的赝势**规格与数据**（内部格式） | 官方说"好奇的人可以看"——restart 文件里会展开成这种写法 |

官方说明：CP2K 会解析用户输入，并在**重启文件里以更冗长但等价**的语法重组。重启文件因此能让人看到关键字与段两种写法的关系：

```
     &KIND "O"
       POTENTIAL "GTH-PBE-q6"
       &POTENTIAL
         2 4
           2.4455430000000000E-001 2 -1.6667214800000000E+001  2.4873113199999999E+000
         2
           2.2095592000000000E-001 1  1.8337458110000000E+001
           2.1133246999999999E-001 0
         # Potential name: GTH-PBE-Q6 for element symbol: O
         # Potential read from the potential filename: GTH_POTENTIALS
       &END POTENTIAL
     &END KIND
```

> **实用价值**：如果想知道某个 `GTH-PBE-qN` 的**具体参数数值**，跑一次算例看 restart 文件即可，不必去找原始数据文件。

### 3.4 `qN` 后缀的含义（官方原文）

> The suffix `q6` in `GTH-PBE-q6`, for example, means that **six valence electrons are treated explicitly**. The chosen basis set should match this valence configuration; for oxygen, the common basis sets with the same suffix in the full name like `DZVP-MOLOPT-GTH-q6` can be used. If some pseudopotentials without corresponding basis sets, or vice versa, are spotted in the built-in data files, consult developers for help.

**规则**：`qN` = **显式处理的价电子数**；**基组后缀必须匹配**（如 O 用 `GTH-PBE-q6` 配 `DZVP-MOLOPT-GTH-q6`）。

### 3.5 怎么选赝势（官方原文）

> Use a pseudopotential generated for the **exchange-correlation functional family** used in the calculation. For example, `GTH-PBE-q6` is a natural choice for PBE calculations with oxygen. Mixing functional families can be acceptable for exploratory work in some cases, but it is **not a systematic route to high accuracy**.

**规则**：赝势要与泛函族**匹配**（PBE 计算用 `GTH-PBE-*`）。混用泛函族"在探索性工作里有时可接受，但不是通向高精度的系统做法"。

### 3.6 CP2K 自带的赝势库（官方逐个说明）

| 文件 | 官方原文 | 用途 |
|---|---|---|
| `GTH_POTENTIALS` | "contains widely used GTH potentials for common GPW calculations" | **最常用**的 GTH 赝势 |
| `POTENTIAL_UZH` | "contains the UZH protocol GTH potentials designed to be used with matching UZH basis sets" | **UZH 协议**赝势，配 UZH 基组 |
| `NLCC_POTENTIALS` | "contain more specialized potentials" | 非线性芯校正（NLCC） |
| `GTH_SOC_POTENTIALS` | "contain more specialized potentials" | 含自旋轨道耦合（SOC） |
| `ECP_POTENTIALS` | "contains effective core potentials for Gaussian integral based calculations" | **有效芯势**（基于高斯积分的计算） |

**官方推荐（重要）**：

> For new GPW production inputs, **prefer a matching UZH protocol pair from `POTENTIAL_UZH` and `BASIS_MOLOPT_UZH` when it is available** for the element and functional family. The older `GTH_POTENTIALS` library remains important for **reproducing established calculations** and for cases where a matching UZH setup is not available.

| 场景 | 官方建议 |
|---|---|
| **新的** GPW 生产计算 | **优先** `POTENTIAL_UZH` + `BASIS_MOLOPT_UZH` 配对（若该元素/泛函族有） |
| **复现已发表结果** | 用原来的 `GTH_POTENTIALS` |
| 没有 UZH 配对时 | 用 `GTH_POTENTIALS` |

### 3.7 全电子计算（官方示例）

> For all-electron calculations, use `POTENTIAL ALL` together with an all-electron basis set and the **GAPW** method:

```
&KIND O
  BASIS_SET SVP-MOLOPT-GGA-ae
  POTENTIAL ALL
&END KIND
```

**三件套**：`POTENTIAL ALL` + 全电子基组（名含 `-ae`）+ `GAPW`。

### 3.8 官方给的一致性检查（4 条）

官方原文：

> - The basis set and pseudopotential should be available in the files named in the `DFT` section.
> - The pseudopotential valence charge should match the basis set suffix where such a suffix is used.
> - The exchange-correlation functional should be consistent with the pseudopotential family.
> - For heavy elements, decide whether a large-core, medium-core, small-core, or all-electron description is appropriate for the property of interest.

| # | 检查 |
|---|---|
| 1 | 基组与赝势**都在** `&DFT` 里列出的文件中存在 |
| 2 | 赝势价电荷与基组后缀**匹配** |
| 3 | 泛函与赝势族**一致** |
| 4 | 重元素：判断用**大芯/中芯/小芯/全电子** |

---

## 4. GTH 赝势完整元素与价电子清单（官方数据仓库索引）

> **来源**：<https://github.com/cp2k/cp2k-data/blob/master/potentials/Goedecker/index.html>
> 官方索引页由 **Matthias Krack（PSI）** 维护，最后更新 **2021-07-09**。

### 4.1 命名与可选泛函

- 文件名形如 `元素-qN`（如 `H-q1`、`Fe-q16`），**完整名称**需加泛函前缀：`GTH-<XC>-qN`。
- 可选交换关联泛函：**BLYP、BP、HCTH/120、HCTH/407、LDA (PADE)、OLYP、PBE、PBESol**
- 可选输出格式：**Abinit、CP2K、CPMD**

> **实用提示**：CP2K 计算里最常用的组合是 `GTH-PBE-qN`。

### 4.2 完整元素 → 可用 qN 清单

**主族元素**

| 元素 (Z) | 可用 qN |
|---|---|
| H (1) | q1 |
| He (2) | q2 |
| Li (3) | q1, q3 |
| Be (4) | q2, q4 |
| B (5) | q3 |
| C (6) | q4 |
| N (7) | q5 |
| O (8) | q6 |
| F (9) | q7 |
| Ne (10) | q8 |
| Na (11) | q1, q9 |
| Mg (12) | q2, q10 |
| Al (13) | q3 |
| Si (14) | q4 |
| P (15) | q5 |
| S (16) | q6 |
| Cl (17) | q7 |
| Ar (18) | q8 |
| Ga (31) | q3, q13 |
| Ge (32) | q4, q14 |
| As (33) | q5 |
| Se (34) | q6 |
| Br (35) | q7 |
| Kr (36) | q8 |
| In (49) | q3, q13 |
| Sn (50) | q4 |
| Sb (51) | q5 |
| Te (52) | q6 |
| I (53) | q7 |
| Xe (54) | q8 |
| Tl (81) | q3, q13 |
| Pb (82) | q4, q14 |
| Bi (83) | q5, q15 |
| Po (84) | q6 |
| At (85) | q7 |
| Rn (86) | q8 |
| Nh (113) | q3 |
| Fl (114) | q4 |
| Mc (115) | q5 |
| Lv (116) | q6 |
| Ts (117) | q7 |
| Og (118) | q8 |

**碱金属 / 碱土金属**

| 元素 (Z) | 可用 qN |
|---|---|
| K (19) | q1, q9 |
| Ca (20) | q2, q10 |
| Rb (37) | q1, q9 |
| Sr (38) | q2, q10 |
| Cs (55) | q1, q9 |
| Ba (56) | q2, q10 |
| Fr (87) | q1, q9 |
| Ra (88) | q2, q10 |

**过渡金属**

| 元素 (Z) | 可用 qN |
|---|---|
| Sc (21) | q3, q11 |
| Ti (22) | q4, q12 |
| V (23) | q5, q13 |
| Cr (24) | q6, q14 |
| Mn (25) | q7, q15 |
| Fe (26) | q8, q16 |
| Co (27) | q9, q17 |
| Ni (28) | q10, q18 |
| Cu (29) | q1, q11, q19 |
| Zn (30) | q2, q12, q20 |
| Y (39) | q3, q11 |
| Zr (40) | q4, q12 |
| Nb (41) | q5, q13 |
| Mo (42) | q6, q14 |
| Tc (43) | q7, q15 |
| Ru (44) | q8, q16 |
| Rh (45) | q9, q17 |
| Pd (46) | q10, q18 |
| Ag (47) | q1, q11, q19 |
| Cd (48) | q2, q12 |
| Hf (72) | q4, q12 |
| Ta (73) | q5, q13 |
| W (74) | q6, q14 |
| Re (75) | q7, q15 |
| Os (76) | q8, q16 |
| Ir (77) | q9, q17 |
| Pt (78) | q10, q18 |
| Au (79) | q1, q11, q19 |
| Hg (80) | q2, q12 |
| Rf (104) | q12 |
| Db (105) | q13 |
| Sg (106) | q14 |
| Bh (107) | q15 |
| Hs (108) | q16 |
| Mt (109) | q17 |
| Ds (110) | q18 |
| Rg (111) | q11 |
| Cn (112) | q12 |

**镧系**

| 元素 (Z) | 可用 qN |
|---|---|
| La (57) | q3, q11 |
| Ce (58) | q12, q30 |
| Pr (59) | q13, q31 |
| Nd (60) | q14, q32 |
| Pm (61) | q15, q33 |
| Sm (62) | q16, q34 |
| Eu (63) | q17, q35 |
| Gd (64) | q18, q36 |
| Tb (65) | q19, q37 |
| Dy (66) | q20, q38 |
| Ho (67) | q21, q39 |
| Er (68) | q22, q40 |
| Tm (69) | q23, q41 |
| Yb (70) | q24, q42 |
| Lu (71) | q25, q43 |

**锕系**

| 元素 (Z) | 可用 qN |
|---|---|
| Ac (89) | q11, q29 |
| Th (90) | q12, q30 |
| Pa (91) | q13, q31 |
| U (92) | q14, q32 |
| Np (93) | q15, q33 |
| Pu (94) | q16, q34 |
| Am (95) | q17, q35 |
| Cm (96) | q18, q36 |
| Bk (97) | q19, q37 |
| Cf (98) | q20, q38 |
| Es (99) | q21, q39 |
| Fm (100) | q22, q40 |
| Md (101) | q23, q41 |
| No (102) | q24, q42 |
| Lr (103) | q25, q43 |

> **注意**：官方索引页对 Fr、Ra 及 Rf–Og 等超重元素标注了 `no` 占位符（脚本会提示"该元素无可用 GTH 赝势"），但仍列出部分 qN 文件。**实际可用性以仓库内容为准**。

### 4.3 GTH 赝势的原始文献（官方索引页给出）

| 文献 | 覆盖范围 |
|---|---|
| S. Goedecker, M. Teter, J. Hutter, *Separable dual-space Gaussian pseudopotentials*, Phys. Rev. B **54**, 1703–1710 (1996) | GTH 方法原始文献 |
| C. Hartwigsen, S. Goedecker, J. Hutter, *Relativistic separable dual-space Gaussian pseudopotentials from H to Rn*, Phys. Rev. B **58**, 3641–3662 (1998) | **H 到 Rn** |
| M. Krack, *Pseudopotentials for H to Kr optimized for gradient-corrected exchange-correlation functionals*, Theor. Chem. Acc. **114**, 145–152 (2005) | **H 到 Kr**，针对 GGA 优化 |

**官方免责声明**：作者不对所提供赝势的正确性或质量作任何担保。

---

## 5. 基组/赝势相关工具（官方 `tools` 页）

| 工具 | 用途 |
|---|---|
| [Basis Set Exchange](https://www.cp2k.org/tools:basissetexchange) | 基组交换库 |
| [cp2k-basis](https://www.cp2k.org/tools:cp2k-basis) | **浏览基组与赝势** |
| [GTH 赝势参数集](https://cp2k.org/static/potentials/) | 官方托管下载页 |
| [AML Python Package](https://www.cp2k.org/tools:aml) | — |
| [PyCP2K](https://www.cp2k.org/tools:pycp2k) | Python 接口 |
| [Avogadro 1/2 输入生成器](https://www.cp2k.org/tools:avogadro2) | 图形化生成输入 |
| [Vim / EMACS / Sublime 插件](https://www.cp2k.org/tools) | 编辑器支持 |

> **BSE 页给出的实际做法**（官方示例）：BSE 计算用 `aug-cc-pVDZ` 与 `aug-cc-pVDZ-RIFIT` 基组，来自 `BASIS-aug` 文件，可**从 Basis Set Exchange 获取**。说明官方也接受从 BSE 取基组。

---

## 6. 常见坑（G 层从官方原文归纳）

| 坑 | 官方依据 | 处置 |
|---|---|---|
| 基组后缀与赝势 `qN` 不匹配 | 官方"should match this valence configuration" | 检查后缀，如 O 用 `q6` 配 `q6` |
| 泛函与赝势族不一致 | 官方"not a systematic route to high accuracy" | PBE 用 `GTH-PBE-*` |
| 混淆 `POTENTIAL` 关键字与段 | 官方明确"Do not confuse" | 日常用关键字 |
| 以为基组第 1 个数字要改 | 官方"CP2K ignores this number" | 不用管 |
| 全电子却没用 GAPW | 官方"together with an all-electron basis set and the GAPW method" | `POTENTIAL ALL` + `-ae` 基组 + GAPW |
| 新计算还在用旧 GTH 库 | 官方"prefer a matching UZH protocol pair" | 有 UZH 配对就优先 |
| 想看赝势具体参数 | 官方 restart 文件会展开 | 跑一次看 restart |

---

## 7. 交叉索引

| 想查 | 去 |
|---|---|
| GPW/GAPW 方法本身 | `02_dft_methods.md` |
| ADMM 辅助基组 | `02_dft_methods.md`（ADMM 节） |
| 赝势相关版本变更 | `11_version_changelog.md` |
| 输入语法（方括号单位等） | `13_input_syntax_and_print.md` |
| 编译时赝势/基组数据文件从哪来 | `09_build_libraries.md` |
| 实操选基组经验 | F 层 `../playbook.md` |
