# CP2K 参数决策知识库（启发式）

本文件是 skill"思考层"的人类可读版决策依据，供 `recommend.py` / `diagnose.py`
与对话中的逐步推理引用。**核心哲学：默认值只是"安全起点假设"，不是定律；
每个新体系都要具体问题具体分析，并依据结果迭代调参。**

---

## 1. 泛函怎么选（v2: 三级阶梯）

| 场景 | 推荐 | 说明 |
|---|---|---|
| 结构优化 / 力学量 / 筛选 | **PBE（=PADE）** | 便宜、对结构/晶格/力可靠，是默认起点 |
| 吸附能 / 表面反应 / 弱作用（比 PBE 准但不想上杂化） | **TPSS** 或 **SCAN** | Meta-GGA，精度介于 PBE 和 HSE06 之间，价格仅 ~1.5-2x PBE。SCAN 对非共价相互作用尤其好；TPSS 对表面化学更成熟。**推荐作为中间台阶。** |
| 反应能 / 吸附能 / 能带隙（需要高精度） | PBE 起步，最后用 **HSE06** 或 **B3LYP** 精修 | 杂化泛函对带隙、电荷转移、反应能明显更准。**务必加 --admm**（见 S8）。 |
| 含强关联 / 磁性 | PBE + **UKS**，多重度按磁序 | 杂化泛函对磁性帮助有限，重点是自旋正确 |
| 大体系 / 快速试探 | PBE 即可 | 杂化泛函贵 5–20×，先用 PBE 跑通再精修 |

> **泛函阶梯**: PBE(筛选) → TPSS/SCAN(精修结构/吸附能) → HSE06/B3LYP(最终能量/带隙)。
> 每一步都可在上一步优化后的结构上做单点能，不必从头重算。
> **强关联 TM 氧化物（Ti/Fe/Co/Ni/Mn 氧化物）**：在选 PBE/TPSS 的同时**默认加 DFT+U**（硬规则，见 §28.1）——不加 U 会定性错误（电子不局域、四价 Ti 不被还原）。`--kinds "...:U=<eV>"`，U 单位必须写 `[eV]`。

---

## 2. 基组 / 赝势（按元素二选一）

- **轻元素 / 主族 / 半导体**：`DZVP-GTH-PADE` 基组 + `GTH-PADE-q<N>` 赝势（Si→q4，C→q4，O→q6）。
- **过渡金属 / 镧锕系 / 后过渡（Tl,Pb,Bi）**：`DZVP-MOLOPT-SR-GTH` 基组 + `GTH-PBE-q<N>` 赝势。
  这是催化体系（Au/Pt/Ni/Fe…）的**硬性要求**：用 PADE/MOLOPT 错配会出错。
- **大核 vs 小核 —— 同一元素有多个赝势时优先选"大核"（价电子数最少的那个）**：
  赝势分大小核，**选大核 = 把更多电子丢给赝势处理**，于是 SCF 迭代里包含的电子数更少 → **更快**。
  讲师口径："我们一般都是用那种**大核**的，就是尽可能让 SCF 迭代的时候里面包含的这个电子数尽可能少"（字幕 `S1.2.txt:623–639`）；
  讲义 `L1.txt:722` 同调："赝势用含有**价电子数最少**的默认赝势即可"。
  > 与下面的 q 表配合：**同一元素若有多个 q 可选，取最小的那个**。前提是该赝势对你研究的问题仍然够用
  > ——若要看半芯态或高氧化态，仍需选能描述该壳层的赝势。`gen_inp.py --potential` 的取值即按此原则给。

### 常用元素价电子数 q（GTH 赝势）

| 轻元素 | q | | 3d 金属 | q | | 4d/5d 贵金属 | q |
|---|---|---|---|---|---|---|---|
| H | 1 | | Ti | 12 | | Ru | 16 |
| C | 4 | | V | 13 | | Rh | 17 |
| N | 5 | | Cr | 6 (高自旋可14) | | Pd | 10 |
| O | 6 | | Mn | 7 | | Ag | 11 |
| F | 7 | | Fe | 16 | | Os | 16 |
| Si | 4 | | Co | 17 | | Ir | 17 |
| P | 5 | | Ni | 18 | | Pt | 10 |
| S | 6 | | Cu | 11 | | Au | 11 |
| Cl | 7 | | Zn | 12 | | Hg | 12 |
| Al | 3 | | | | | Tl/Pb/Bi | 13/14/15 |

> q 是 GTH 赝势的价电子数，决定 POTENTIAL 关键字（如 `GTH-PBE-q11`）。
> 不确定时在 cp2k/data/GTH_POTENTIALS 里核对，`recommend.py` 遇到未知元素会提示你确认。

- **怎么从文献反推 `q`（复现他人计算时最实用的一招）**：读文献给的元素电子构型，数出**价电子数**即得 `q` ——
  O：2s²2p⁴ = 6 ⇒ `-q6`；Na：2s²2p⁶3s¹ = 9 ⇒ `-q9`；Au：5d¹⁰6s¹ = 11 ⇒ `-q11`（基组名 `DZVP-MOLOPT-SR-GTH-q11`）。
  再回 `cp2k/data/BASIS_MOLOPT` 核对这个基组名是否真的存在
  （讲师口径：`videonotes/cp2k-4-过渡态搜索频率计算与AIMD实战-精读笔记 L1490–L1505 [121:44–123:13]`）。
- ⚠️ **不写 `BASIS_SET_FILE_NAME` / `POTENTIAL_FILE_NAME` 时，官方默认去找的文件名是裸的 `BASIS_SET` / `POTENTIAL`**
  —— **不是** `BASIS_MOLOPT` / `GTH_POTENTIALS`（官方 XML `FORCE_EVAL/DFT`：`BASIS_SET_FILE_NAME default=BASIS_SET`、
  `POTENTIAL_FILE_NAME default=POTENTIAL`，可用 `python _kw_probe.py --section FORCE_EVAL/DFT` 复核）。
  ⇒ "两行都不写也能跑"的前提是当前目录里**正好有这两个名字的文件**；套模板时它随 `@SET DATAPATH` 一起改（§30 旁的模板管理）。

### 2.1 GTH 赝势"覆盖到哪个元素"（按泛函）——A–G 层此前缺的维度

出处：H 层 `references/h_tutorials/notes/06_basis_and_intro.md`（**T20 P28**，原始出处 Matthias Krack, 1st CP2K Tutorial, Zurich 2009）。

| 泛函族 | 元素覆盖 |
|---|---|
| **LDA（PADE）** | **H–Rn，含镧系** |
| **PBE** | **H–Rn，不含镧系** |
| PBEsol | H–Kr（+ 少数选定元素） |
| BP | H–Kr（+ 少数选定元素） |
| HCTH | 少数选定元素 |
| **NLCC** 赝势 | 少数选定元素 |

- 文件都在 `cp2k/data`：`POTENTIAL`、`GTH_POTENTIALS`、**`NLCC_POTENTIALS`**（T20 P28）。
- ⚠️ **实操推论**：**镧系体系走"PBE + GTH"这条路本身就受限**（PBE 族不含镧系），要换 **LDA(PADE)** 或别的赝势族。
  这**不是"选大核/小核"能解决的**（对照本节上文的 q 取舍原则）。
- ⚠️ **与 G 层并列、不能直接交叉核对**：G 层 `14_basis_and_potentials.md` §4.1 只列**可选泛函名**、§4.2 只给
  **"元素→qN"**，**不标某个 qN 属哪个泛函族**（粒度不同）。H 层 `notes/06` §6-10 已把这条登记为待办，
  本层照录两说，不擅自合并。
- **赝势文件字段语义**（T20 P27，以 Ti 为例）：`Ti GTH-PBE-q12 GTH-PBE` 下面一行 **`4 6 2` = 各壳层（s/p/d）的价电子数**
  ⇒ 反推芯为 `[Ne]`，正对应 Ti 的 `[Ne]3s²3p⁶4s²3d²`（T20 P22 页脚同款注记）；再往下是 `r_loc` + 势函数个数 + 系数，
  以及每个 `l` 一组 `r_l` + **非局域投影子个数（number of non-local projectors）** + 系数。

### 2.2 自造基组：`OPTIMIZE_BASIS` 完整工作流（A–G 层此前只有工具名）

出处：H 层 `notes/06_basis_and_intro.md`（**T20 P13–P17、P22**）。
**此前全库只有 G 层 `01_global_and_units.md` 的一行工具名与 `20_input_reference_tree.md` 的段树，没有任何一层写过流程。**

1. **选参考（完备）基组**：查 `cp2k/data/BASIS_ADMM` 里的 **`GTH-def2-QZVP`** / **`aug-GTH-def2-QZVP`**，
   或用 **`ATOM` 码**生成未收缩基组（T20 P17；`ATOM` 的算例在 `cp2k/tests/ATOM`）。
2. **用参考基组做精确的分子计算**：训练分子由**不同元素、不同配位环境的小分子**构成，**每个分子最好只含两种元素**
   （其中含目标元素）；**必须用平衡几何（先 `GEO_OPT`）**、**避免同核双原子分子**（T20 P14、P17）。
3. **选定待拟合基组的形式**（优化前就要定）：高斯指数个数、每个角动量的基函数个数、训练集、不同基组是否同时优化、
   **条件数在目标函数里的权重**（T20 P13）。
4. **最小化目标函数** `Ω(α,c) = Δρ_i^{B,M}(α,c) + γ·ln κ(α,c)`（`κ` = 重叠矩阵**条件数**；T20 P16；
   工具实现者 Dr Florian Schiffmann，T20 P16 页脚）。
   输入骨架：`PROGRAM_NAME OPTIMIZE_BASIS` + `BASIS_TEMPLATE_FILE` / `BASIS_WORK_FILE` / `BASIS_OUTPUT_FILE`
   + `&TRAINING_FILES` + `&FIT_KIND <元素> BASIS_SET <名> INITIAL_DEGREES_OF_FREEDOM EXPONENTS`
   + `&CONSTRAIN_EXPONENTS BOUNDARIES 0.1 20 USE_EXP -1 -1`；算例 `cp2k/tests/QS/regtest-optbas`（T20 P22）。

> 与 ADMM 的关系：ADMM 辅助基（§11 的 FIT/cFIT 族）就是用这套工具造出来的，所以"辅助基不够用"时，
> 正规出路是**自己拟合**，而不是随手挑一个别的基组（T20 P16–P22 的教学立场）。

### 2.3 `Deltatest` / Δ-gauge：固体基组质量的独立标尺（A–G 层此前零命中）

出处：H 层 `references/h_tutorials/notes/03_hybrid_admm_parallel.md`（**T06 P31–P36**）。

- **度量**：两条 E(V) 曲线的差 `Δ(a,b) = sqrt( ∫_{0.94V₀}^{1.06V₀} (E_b(V)−E_a(V))² dV / (0.12 V₀) )`；
  覆盖 **40+ 种方法 / 71 种元素（H–Rn 元素晶体）**，**以全电子计算为参考**
  （Lejaeghere et al., *Science* **351**, aad3000 (2016)；*Crit. Rev. Solid State* **39**, 1 (2014)）。
- **CP2K MOLOPT 的结论**（T06 P36，逐字要点）：MOLOPT **适合固体**；**更大的 ζ 系统性更好**
  （DZVP → TZVP → TZV2P → TZV2PX 偏差单调下降）；**基组误差与赝化误差同量级**；
  **某些元素上基组误差会"意外补偿"赝势误差**。
- ⇒ **实践意义**：**别把"换更小的基组结果没变差"当成"基组够用"的证据**——可能是基组误差与赝势误差相互抵消
  （T06 P36）。这与本 skill 对 BSSE/基组收敛的一贯要求一致。

> ⚠️ T06 的 Δ-gauge 图例细节只能部分还原（数值在图片里），引用时只引 P36 的文字结论，不要引具体 Δ 值
> （H 层 `notes/03` §7-8 已登记）。

---

## 3. 自旋（UKS / LSD）

- **开壳层必须开 UKS**：O₂（多重度 3）、自由基（多重度 2）、多数吸附态。
- **含磁性 3d/4d/5d 元素**（Fe/Co/Ni/Mn/Cr/Ru/Ir/Pt…）大概率需要自旋极化；
  铁磁 Fe 体相常用多重度 3，具体按磁矩/磁序定。
- 开 UKS 时务必加 `WF_INTERPOLATION ASPC` + `EXTRAPOLATION_ORDER 3` 加速 SCF。
- 模板已用 `--multiplicity N` 控制；`recommend.py` 遇磁性元素会提示而非强制。
- **`MULTIPLICITY` 不是"必填"：官方默认 `0`**（`FORCE_EVAL/DFT MULTIPLICITY`，别名 `MULTIP`），
  语义是**"偶数电子 → 1（单重态）、奇数电子 → 2（双重态）"**，其余情况才要手工指定。
  ⇒ **必须显式写的只有 S>1 的高自旋态**（O₂ 三重态写 `3`、铁磁/反铁磁序）；闭壳层与奇电子数体系**不写也能跑且默认合理**。
  （官方 XML `DEFAULT_VALUE : 0` + `DESCRIPTION`；`videonotes/cp2k-3-CP2K计算流程与参数详解-精读笔记 L397–L424 [30:33–32:44]`）
  > 📌 **更正记录**：讲师课上强调"在 CP2K 里面呢，这个自旋多重度的定义**是一定要定义的**"（同笔记 `L405 [30:36–31:03]`），
  > 本库早期照录为"需提前指定"。**该说法过强** —— 官方默认 `0` 已覆盖"闭壳层 + 奇电子数"两种最常见情形，
  > 依据是官方 `cp2k_input.xml` 的 `DESCRIPTION`（"Default is 1 (singlet) for an even number and 2 (doublet) for an odd
  > number of electrons"）。**高自旋态仍然必须指定**，这一半讲师是对的。
  > ⚠️ H 层 `h_tutorials/notes/07_qmmm.md:57` 把"默认 MULTIPLICITY=1"当默认写（原文 "`MULTIPLICITY 3`（**默认 MULTIPLICITY=1**）"），
  > 与官方 XML 的 `0` 有出入 —— **以 XML 为准**（`0` 的语义在偶数电子时**恰好退化为 1**，所以两者在闭壳层体系上结论相同，
  > 差别只在奇电子数体系：`0` → 自动取 2，写死 1 会错）。
- **`RELAX_MULTIPLICITY` 的四条硬限制**（官方默认 `0.0` = 不启用；`>0` 即开启，值越大自旋翻转概率越大）：
  ① 必须 `LSD`/`UKS`；② **必须对角化，不能用 OT**；③ 因此**必须 `ADDED_MOS`**；④ **不能用 `SMEAR`**。
  出处：H 层 `h_tutorials/notes/06_basis_and_intro.md:138/651`（四条完整）；讲师只覆盖了 ①②
  （`videonotes/cp2k-3-…-精读笔记 L426–L440 [32:44–33:36]`）。本库 `playbook.md` 此前只有一条"会禁用 OT 等算法"。
  > ⚠️ **语境限定**：**"OT 不能 SMEAR"只在 `RELAX_MULTIPLICITY` 的语境里成立，作为泛论不成立**
  > （`&SCF/&OT` 一侧确有 direct finite-temperature OT 的支持，见 `references/official/02_dft_methods.md`）。

---

## 4. 色散 DFT-D3

- **什么时候开**：体系含分子 / 吸附质 / 层状材料 / π-π / 弱吸附——几乎覆盖全部催化吸附问题。
  DFT-D3 便宜、风险低，**auto 模式对含 C/N/O/H 等的体系默认开**。
- 需要把 `dftd3.dat` 放到运行目录（cp2k/data 可拷）。
- 纯金属块体、强离子晶体弱作用贡献小，可不开。

### 4.1 DFT-D3 的前置条件与盒子耦合（批 14）

> 出处：字幕 `S4.txt:4101–4198`。§27.2 给的是**关键字怎么写**，这里给的是**什么条件下它才真生效、以及它和晶胞尺寸的耦合**。

- **`dftd3.dat` 必须复制到计算目录**（或写绝对路径）。讲师原话："这个文件我们使用的时候，要把它复制到当前文件夹里面去使用"（`S4.txt:4146–4157`）。这是最常见的"写了 D3 却没生效"的来源，报错速查见 `playbook.md` §1.3。
- **截断半径与盒子尺寸是一对**：D3 的截断半径常用 **15 Å**；**盒子边长小于它时，必须把截断同步调小**（讲师例：盒子只有 12 Å 就把截断调小），目的仍是"不要让相邻镜像之间的同一个原子对它自身做作用"（`S4.txt:4168–4179`）。这条与 **§5.1** 的"原子–自身镜像"原则同源——**设了 DFT-D3 时要特别检查**。
  - ⚠️ **"15 Å"是课程自设的常用值，不是 CP2K 默认**：官方 `R_CUTOFF` 默认 **10.5835 Å（= 20 bohr）**
    （`FORCE_EVAL/DFT/XC/VDW_POTENTIAL/PAIR_POTENTIAL/R_CUTOFF`，`DEFAULT_UNIT angstrom`），
    且官方描述明写 **"The cutoff will be 2 times this value"** ⇒ **实际势截断 = 2 × `R_CUTOFF`**，默认即 **21.17 Å**。
    ⇒ **盒子尺寸判据要对的是 `2 × R_CUTOFF`**，不是 `R_CUTOFF` 本身（§27.2 已有"2×"这句，此处补定量与出处）。
    （`python _kw_probe.py --find R_CUTOFF` 复核；`videonotes/cp2k-4-…-精读笔记 L1779–L1786 [150:11–150:59]`）
    > 📌 **更正记录**：`course_learned.md:1410` 与 `playbook.md:193` 把"15 Å"写成 `R_CUTOFF` 的**默认值**，
    > 那其实是**讲义/讲师的自设常用值**；官方默认是 **10.5835 Å**。本条只改 A 层口径，B/F 层措辞归 B/F 层 agent。
- **AIMD 里要不要开**：**可以加，几乎不增加耗时**——讲师的实测口径是"相对于我们做这个 DFT 计算，DFT-D3 可以在非常非常短、零点几秒或者 0.0 几秒之内就完成"（`S1.2.txt:662–669`）。所以**不要为了省时间关掉色散**，那是把长程作用白白丢掉。
- **版本边界**：D4 已经发表，但**尚未集成进 CP2K**，CP2K 侧只能用 D3（`S4.txt:4131–4140`）。
- **非局域 vdW 泛函的取舍**：vdW-DF 族 / SCAN+rVV10 这类**必须编译期装了 libxc** 才能用，且比"直接用 D3 的方法要慢了不少"；只想快速补色散就用 D3（`S4.txt:4114–4129`、`4184–4198`）。

---

## 5. 周期性 / POISSON / k 点

- **块体**：`PERIODIC xyz`；**表面 slab**：`PERIODIC xy`（z 非周期）；**孤立分子/团簇**：`PERIODIC NONE` + `POISSON WAVELET`，给大盒子包住分子。
  - 🔴 **`WAVELET` 有一个硬前提：分子必须居于单胞中心**（2026-10 真机实测；**本条原先漏了**）。
    官方 T24 §3.4 逐字：「如果设置为 WAVELET，不需要设置非常大的单胞，**但分子必须处于单胞的中心**，
    确保单胞的边界处电子密度为 0。可以使用 **TOPOLOGY** 参数来强制将分子置于单胞的中心。」
    ```
    &SUBSYS
      &TOPOLOGY
        &CENTER_COORDINATES
        &END CENTER_COORDINATES
      &END TOPOLOGY
      ...
    ```
    **违反它的后果是静默的物理错误**（CP2K 不报错、SCF 照常"收敛"）。同一水分子实测：

    | 设置 | 总能量 (a.u.) | **\|ΣF\|**（孤立体系必须为 0） |
    |---|---|---|
    | WAVELET + 分子在原点角上 | **−29.225** | **24.72** ❌ |
    | WAVELET + 分子居中（手移坐标） | −17.120 | 0.0005 ✅ |
    | WAVELET + `&CENTER_COORDINATES` | −17.120 | 0.0002 ✅ |
    | `ANALYTIC` / `MT`（不需要居中） | −17.120 | 0.0020 ✅ |

    **差 12 Ha、力全错**，而且居中后还**更快**（70 s vs 109 s）。
    ⇒ **判据就是输出里 `SUM OF ATOMIC FORCES` 那一行**（`diagnose.py` 现已自动检查）。
  - **`ANALYTIC` / `MT` 不需要居中**（实测同样正确、同样快），可作为不想动坐标时的替代；
    但 `MT` 有自己的前提 —— 官方 T24 同段：「如果设置为 MT，**要保证计算使用的单胞体积足够大，
    至少是电荷密度的两倍**」。
  - 官方练习 T13/T14/T15 原文同口径："gas phase systems should have 'NONE' **and a wavelet solver**"
    —— 用 wavelet 没错，**前提是居中**。
  - ✅ **`gen_inp.py --periodic none` 现已自动补 `&TOPOLOGY/&CENTER_COORDINATES`**，不会再漏。
- **k 点**：金属 / 窄带隙**必须多 k 点**（费米面采样），否则能带/能量错误。
  - 块体金属：`6 6 6`（精度高 `8 8 8`）
  - 表面 slab：z 非周期 → `4 4 1`
  - 绝缘体 / 半导体：GAMMA 中心点通常够；异常时再加。
  - 收敛原则：金属/小原胞/强色散带需做 k 点网格收敛；大超晶胞布里渊区已很小，Gamma 常够。
  - ⚠️ **k 点与 OT 不兼容**：`&OT` 不支持 k 点，仅标准 `&DIAGONALIZATION` 支持（加 `ADDED_MOS`、配合 `&SMEAR`）。所以"金属小原胞 + 需要 k 点"时**不能用 OT**，要切到对角化路径（AIMD 默认 OT，若体系金属且需 k 点，要么用大超晶胞退到 Gamma，要么改对角化）。杂化泛函 + k 点走 RI-HFXk，不是普通 HFX。DFT+U + k 点仅 Mulliken 布居可用。
- **不对称 slab 的表面偶极修正**：吸附质只在一侧、或两端终止不对称时，PBC 会引入虚假表面偶极，使真空区静电势倾斜、SCF 难收敛。开 `&DFT SURFACE_DIPOLE_CORRECTION T`（模板 `--surface-dipole`，方向 `--dipole-dir Z`、位置 `--dipole-pos 0.5`、平滑 `--dipole-switch 0.3`），真空区势能恢复平整。仅对 `PERIODIC xy`/`x?` 有意义。
  - **裸关键字是 `SURF_DIP_DIR`（默认 `Z`）**、`SURF_DIP_POS`（默认 −1.0）、`SURF_DIP_SWITCH`（默认 F）；
    **CP2K 里没有 `SURFACE_DIPOLE_DIRECTION` 这个键**（`python _kw_probe.py --find SURFACE_DIPOLE_DIRECTION` → 0 命中）。
    > 📌 **更正记录**：讲师课上念的是"`SURFACE_DIPOLE_CORRECTION`、`SURFACE_DIPOLE_DIRECTION` 这个关键词"
    > （`videonotes/cp2k-3-…-精读笔记 L472–L484 [35:45–36:29]`），该笔记速查表也照抄了错名。
    > **A/F/工具层一直用的是正确的 `SURF_DIP_DIR`；C 层也已在本轮同步更正并留痕**
    > （`course_notes.md:53–57` 的关键字名更正、`course_survey.md:348` 的错字表），本层只钉官方键名。
  - ⚠️ **官方硬限制：只对"法向平行于某一笛卡尔轴"的 slab 实现**（官方描述 "Implemented only for slabs with normal
    parallel to one Cartesian axis"）⇒ **斜切面 / 法向不与 x,y,z 对齐的 slab 加了这个校正也不生效、也不报错**；
    这时要么改用对齐的切法，要么接受真空势倾斜的后果（`python _kw_probe.py FORCE_EVAL/DFT/SURFACE_DIPOLE_CORRECTION`；
    `videonotes/cp2k-5-…-精读笔记 L900–L912 [76:55–77:54]`）。
- 模板用 `--periodic xy/none` 与 `--kpoints "a b c"` 控制；`--surface-dipole` 控制表面偶极修正。

### 5.1 晶胞尺寸与"原子–自身镜像"相互作用（PBC 第一原则，批 14）

> 出处：讲义 `L1 P28–P29`；字幕 `S1.1.txt:2017–2150`。这是讲师定位为"AIMD 里**非常有技巧、非常重要**"的一件事（`S1.1.txt:2069–2071`），而现有文档几乎空白。

- **第一原则**：PBC 下"同一个原子会和它的周期镜像相互作用"，而那是**完全虚假的相互作用**。判据一句话——
  **以原子为中心的作用范围（范德华作用、高斯基组等）必须小于盒子边长。**
  讲义原文（`L1 P28`）："为了避免原子和自身相互作用。范德华作用，高斯基组等原子为中心的作用要小于其盒子边长。"
  - 讲师给的粗口径下限是**边长 > 6 Å**（`L1 P29`："边长合适（> 6 Å）"）；
  - 但 6 Å 只是"不至于离谱"的底线，**真正的判据是"你要观察的物种尺度"**（见下）。
- **设了 DFT-D3 时要特别检查这条**：色散是长程作用。讲师原话："在设定范德华参数（如 DFT-D3）的时候，如果这个 A 分子和它镜像的 A 分子产生了非常明显的相互作用，那这个明显的相互作用就是完全不合理的……一个非常假的相互作用"（`S1.1.txt:2047–2056`）。截断半径与盒子的耦合见 **§4.1**。
- **两侧都是错，方向相反**：
  - **太小** → 团簇/原子与镜像"连成一片"。讲师原例：Au₂₀ 放在 2×2 金包里，模拟中团簇与镜像互相吸引，"连成一个金的纳米棒，或者是连成一个金的纳米饼，那么这个体系就完全失真了"（`S1.1.txt:2086–2102`）。
  - **太大** → **纯浪费机时**。胞从 3×3 扩到 4×4，面积比 16/9 ≈ **1.78**、原子数接近翻倍，但"计算量是呈指数型往上增长的……可能增加了四、五倍、五、六倍"（`S1.1.txt:2103–2125`）。**做机时预算时不要按原子数线性外推。**
- **晶胞尺寸经验三档**（讲师原例，Au 团簇负载于 TiO₂）：

  | 要观察的对象 | 经验胞 | 理由（讲师口径） |
  |---|---|---|
  | 单个金原子（单原子催化剂） | **2×2** | 单原子与镜像原子"发生一个直接的这个结合吸引，那是不太可能的"（`S1.1.txt:2134–2140`） |
  | **Au₂₀** 团簇 | **3×3** | 2×2 太近（团簇与镜像"隔得实在太近了"），3×3 够用（`S1.1.txt:2077–2092`、`2131–2132`） |
  | **Au₅₅** 团簇 | **比 3×3 更大** | Au₅₅ 用 3×3 "可能它又会连成一片，又不合理了"（`S1.1.txt:2141–2150`） |

- **选取判据是"要观察的物理化学现象的尺度"，不是"越大越保险"**："这个一取决于我们想要观察的这个体系，还有我们想要观察的物理化学这个现象"（`S1.1.txt:2126–2130`）。
- 与之联动的三条：① 单 Γ 点要求边长 ≥10 Å（**§5.2**）；② 扩胞代价非线性（上文）；③ 二维材料做 `CELL_OPT` 必须加 `CONSTRAINT Z` 防真空层消失（**§18.1**）。

### 5.2 k 点：CP2K 的已知缺陷与对冲手段（批 14）

> 出处：字幕 `S2.txt:2919–2970`、`S3.txt:4030–4053`；讲义 `L2 P33`。本 §5 上文给的是**k 点怎么用**，这里补的是**这条缺陷会怎样改变你的决策与机时预估**。

- **缺陷本体（已按官方口径更正，2026-10）**：讲师原话是"CP2K 7.1 虽然有 `SYMMETRY` 这个功能，
  但实际计算过程中**它不会因为这个对称性而降低 K 点的个数**"（`S3.txt:4030–4050`）；
  讲义口径（`L2 P33`）：**"K 点功能不完善，只有用 Gamma 点计算比较好用。这意味着对大体系可以，但是小体系计算不准确。"**
  > ⚠️ **旧版此处写成"CP2K 不支持 k 点对称性约化"，过强、不准确**。查官方 `cp2k_input.xml`
  > （`&KPOINTS` 段：`SYMMETRY` 默认 **`F`**、`FULL_GRID` 默认 **`F`**）与 G 层
  > `references/official/02_dft_methods.md §4.6`，CP2K 有**两级** k 点约化：
  > 1. **时间反演（k ↔ −k）约化** —— 对规则 Monkhorst–Pack / MacDonald 网格**默认生效**
  >    （`FULL_GRID F` 即"不请求完整网格"）；
  > 2. **原子（空间群）对称约化** —— 由 `SYMMETRY` 控制，**默认关闭**；需要时写 `SYMMETRY T`，
  >    只保留时间反演则 `SYMMETRY T` + `INVERSION_SYMMETRY_ONLY T`。
  >
  > 所以准确说法是"**CP2K 的原子对称约化默认关闭（需显式 `SYMMETRY T`），时间反演约化默认生效**"。
  > 讲师的**实操结论依然成立**：默认设置下别指望空间群对称帮你省机时。
- **为什么这是一条"决策"而不是一条"报错"**：VASP 里高对称小胞的不可约 k 点很少，所以 k 点很便宜；**在 CP2K 里则是"设了多少就实打实算多少"**。从 VASP 迁过来的人照经验设 `6 6 6`，**机时会比预期高一个量级**（讲义 `L2 P33` 同时把"对导体计算较慢"列为另一条独立缺点，见 §22.2）。
- **实操对策（按优先级）**：
  1. **尽量只用 Γ 点**——"一般来说，我们在使用 CP2K 的时候，尽量用 Γ 点去计算"（`S2.txt:2945–2947`）；默认也是 Γ。
  2. 但单 Γ 点有**建模前提**：**晶胞边长至少 ~10 Å 以上**，"这个时候我们才能用一个 Γ 点去把这个体系描述得还算可以"；边长只有 **5 Å 左右时单 Γ 点结果非常不准确**（`S2.txt:2950–2962`）。
  3. 模型太小就**扩胞**（2×2 / 3×3）——"这样的话我们就可以弥补它 K 点功能不完善的这个缺点"（`S2.txt:2963–2970`）。代价按 §5.1 的**非线性**机时估算，不是线性。
  4. **OT 与 k 点互斥**：`&OT` 只能 Γ 点，要 k 点就必须切 `&DIAGONALIZATION`（§22.2）。所以"金属 + 需要 k 点 + 要跑 AIMD"只有两条路——**大超胞 + Γ + OT**，或**小胞 + k 点 + 对角化（更慢）**（`S3.txt:3977–3989`，另见 §18.1）。
- **连带影响**：CP2K 的 PDOS "不是特别靠谱"，原因之一就是 OT 路径只有 Γ 点、且展宽是人为定的；要更好的 PDOS 需改对角化并显式声明展宽（`S5.txt:1086–1103`，§14）。

---

## 6. SMEAR（金属收敛关键）

- 含金属且周期性的体系，开 `&SMEAR METHOD FERMI_DIRAC ELECTRONIC_TEMPERATURE [K] 300`。
  > **段名与默认值（批 15 用官方 XML 钉死）**：功能段是 **`&SCF/&SMEAR`**，**CP2K 里没有 `&SMEARING` / `SMEARING` 这个键**
  > （`--find SMEARING` → 0 命中；`--find SMEAR` → `FORCE_EVAL/DFT/SCF/SMEAR`）。
  > 且 **`ELECTRONIC_TEMPERATURE` 的官方默认就是 `300 K`**（`_kw_probe.py --find ELECTRONIC_TEMPERATURE`）
  > ⇒ 讲师"给的是 300 K 的温度"**其实就是默认值，不写也一样**；要改的是"有没有开 SMEAR + `METHOD FERMI_DIRAC`"。
  > （`videonotes/cp2k-3-…-精读笔记 L740–L758 [56:41–58:21]`）
- 否则 SCF 在费米面附近抖动、难收敛。`recommend.py` 对金属自动加 `--smear`。
- **固定总磁矩**：`&SMEAR FIXED_MAGNETIC_MOMENT m` 强制自旋向上/向下电子数差 = m（默认负值=允许自由弛豫）。做固定磁矩计算（如特定磁序约束）时用。注意展宽只是收敛手段，最终性质要外推到 0 K（电子温度→0）。

---

## 7. CUTOFF 取值（MGRID）

两个参数共同决定网格精度（都在 `&MGRID`）：
- **CUTOFF**：最细网格的平面波截断（Ry）。
- **REL_CUTOFF**：高斯函数映射到哪层网格的参考截断（Ry）。**它太低会让所有高斯被压到最粗网格**，即便 CUTOFF 很高、有效积分网格仍很粗，能量误差显著；所以 REL_CUTOFF 必须先定够。
- 收敛流程（官方建议）：先固定 `REL_CUTOFF 60`（绝大多数体系够），扫 `CUTOFF`（50→500，步长 50）看总能收敛；再固定 `CUTOFF` 扫 `REL_CUTOFF`（10→100）确认 60 已平。

| 体系 | 平衡 CUTOFF | 高精度 CUTOFF |
|---|---|---|
| 轻元素（体相 Si 实测 250 Ry 即 <1e-8 Ha） | 300 Ry | 400 Ry |
| 重主族（Ga/Ge/As/Se/Br…） | 350 Ry | 400 Ry |
| 过渡金属 / 贵金属 | 400 Ry | 500 Ry |
| 5d / 镧锕系 | 500 Ry | 600 Ry |

> 起步把 `REL_CUTOFF` 设 60，CUTOFF 按上表选；收敛后做 CUTOFF 收敛性测试（递增 50–100 Ry 看能量变化）再最终定档。
> 网格太粗会触发 GPW 病态 / 截断警告 → 增大 CUTOFF；若只增 CUTOFF 不增 REL_CUTOFF，细网格上高斯数反而减少，收敛变慢。

### 7.1 官方默认值、VASP 对照与"三说并列"（批 15，视频复核 + XML 定案）

> 出处：`videonotes/cp2k-3-CP2K计算流程与参数详解-精读笔记`（分段带时间戳）；默认值一律用
> `python _kw_probe.py --section FORCE_EVAL/DFT/MGRID` 与 `--find EPS_DEFAULT` 复核。

- **`REL_CUTOFF` 默认 `40` Ry**，官方描述同时写着 "**A value 50+-10Ry might be required for highly accurate results**"
  ⇒ 讲师"默认 40、建议 50–60"与官方逐字吻合（`videonotes/cp2k-3-…-精读笔记 L581 [43:48–44:58]`）。本条属"讲师记对了"。
- **`EPS_DEFAULT` 官方默认 `1.0E-10`**（在 `FORCE_EVAL/DFT/QS` 下）：它**同时控制约十个 `EPS_*` 子精度**，
  讲师建议收紧到 **1E-12 ~ 1E-14**（那是**推荐值，不是默认值**）。
  ⚠️ `FORCE_EVAL/DFT/ENERGY_CORRECTION` 下另有一个同名键，**勿混**，而且**它的默认值跨版本变过**：
  **CP2K 9.0 = `1E-12`；CP2K 2022.1 = `1E-7`**（两版 XML 实测，其余 63 处版本差异全在
  `PW_DFT`/`ATOM`/RI-RPA 等旁支，与本题无关）。⇒ **引用这个数时务必带你自己的版本**；
  而 `&QS EPS_DEFAULT` 的 **`1.0E-10` 两版一致**，可以放心当默认值用。
  （`videonotes/cp2k-3-…-精读笔记 L502–L515 [37:27–38:48]`）
  > 📌 **更正记录**：讲师口述"这个参数在 CP2K 里默认的是 1×10⁻¹⁴"，同一段又自述"大约 CP2K 2.1.0 那个版本……默认值是
  > 1×10⁻¹⁰"；笔记作者自己也标注"转写中该数值前后不一致……建议查手册确认"。**本轮用官方 XML 定案 = `1.0E-10`**，
  > 讲师建议的 `1E-12 ~ 1E-14` 是**收紧档**。E 层原文不改（只读），在消费层标注。
- **`&QS EXTRAPOLATION` 默认已是 `ASPC`、`EXTRAPOLATION_ORDER` 默认已是 `3`**
  （默认名 `EXTRAPOLATION`，别名 `INTERPOLATION` / `WF_INTERPOLATION`）⇒ 讲师讲的"要设置上"的 MD 提速手段
  **其实就是默认值**。显式写出来仍推荐（可读性 + 防被别的设置覆盖），但**不要当成"不写就慢"**
  （`videonotes/cp2k-3-…-精读笔记 L517–L533 [38:48–39:58]`）。
- ⚠️ **"CP2K 的 CUTOFF 与 VASP 的 ENCUT 没有任何可比性"**（讲师在答疑里给的概念澄清）：
  CP2K 的 `CUTOFF` 指**多重网格中最细那一层**的截断能，"**并不是说我们整个这个傅里叶变化的积分网格
  全都是取到这么大的一个数值**"；单位是 **Ry**（1 Ry ≈ 13.6 eV）。**从 VASP 迁过来的人不要按 ENCUT 的经验换算。**
  （`videonotes/cp2k-3-…-精读笔记 L591–L599 [44:58–45:44]`）
- **CUTOFF 取多少：三说并列（不硬编结论）**

  | 口径 | 数值 | 出处 |
  |---|---|---|
  | 课程讲师（近年口径） | **≥500 Ry**；且"500 其实不够，铁钴镍铜钠这些要到 ~1000 Ry" | `videonotes/cp2k-3-…-精读笔记 L559–L577 [42:08–43:48]` |
  | 本 skill 模板 / 生成器 | **300 Ry** | `references/templates/*.inp`；`gen_inp.py --cutoff` 默认 300 |
  | 官方默认 | **280 Ry** | `FORCE_EVAL/DFT/MGRID/CUTOFF`，`DEFAULT_UNIT Ry` |

  ⇒ **判据优先级按"体系 + 收敛测试"，不要照抄单一数字**：本节上表的两档仍可作起步（偏保守），
  但**发表时按讲师口径取 500 更不容易被审稿人质疑**（`videonotes/cp2k-3-…-精读笔记 L565 [42:08–43:48]`）。

---

## 8. 杂化泛函的额外注意

- HSE06：`&XC_FUNCTIONAL` 内 `&XWPBE`（SCALE_X -0.25, OMEGA 0.11）+ `&PBE`，外加 `&HF FRACTION 0.25`。
- B3LYP：`&LYP`+`&BECKE88`+`&VWN`(VWN3)+`&XALPHA` + `&HF FRACTION 0.20`。
- 贵，建议 `EPS_SCF 1e-6` 并加 `&OUTER_SCF`（即 `--outer-scf`）帮收敛。
- **PBE0-TC-LRC（截断库仑 + 长程校正）**：`&XC_FUNCTIONAL` 里在 `&PBE` **之外再加一个 `&PBE_HOLE_T_C_LR` 子段**
  （`CUTOFF_RADIUS` + `SCALE_X`），并把 `&HF &INTERACTION_POTENTIAL` 的 `CUTOFF_RADIUS` **改成同一个值**（两处必须一致）。
  - 物理含义（H 层教材增量，此前 A–G 层 `PBE_HOLE_T_C_LR` **零命中**；出处 T15 P3，见 `references/h_tutorials/notes/05_howto_exercises.md`）：
    截断库仑算符与 `1/r` 之间的差**用一个特殊的 GGA 交换泛函补偿**，**该泛函随作用范围从 0 到 ∞ 由 PBE 平滑过渡到 PBE0**；
    教材的算例是把 `&PBE_HOLE_T_C_LR / CUTOFF_RADIUS 2.5 / SCALE_X 0.25` 插进 `&XC_FUNCTIONAL`（T15 P3）。
  - 完整输入另见 H 层 T05 P30（左栏，`SCALE_X 0.75` + `SCALE_X 0.25` + `CUTOFF_RADIUS 2.0` + `T_C_G_DATA ./t_c_g.dat`）；
    G 层族名见 `02_dft_methods.md` §6.5 的 **PBE0-TC-LRC**。
- **`&HF &MEMORY` 的两个关键字**（此前 A–G 层 `EPS_STORAGE_SCALING` 零命中；出处 T15 P2）：
  - `MAX_MEMORY <MB>` —— **每个 MPI rank** 的 ERI 内存额度（读法见 §11；G 层 `08_errors_and_faq.md:136`）；
  - **`EPS_STORAGE_SCALING`** —— ERI 存储阈值，用来换内存占用与重算的平衡；
    H 层算例 `EPS_STORAGE_SCALING 0.1` 在 `HFX_MEM_INFO` 里对应 **compression factor 8.03**（T15 P2）。
    注释原话是按需给足内存以拿到 **in-core** 操作（即 `on the fly: 0`）。
- **HF 成分的落点是 `&XC/&HF`，不是 `&SCF`**（`&XC &HF FRACTION 0.25`，即本节 HSE06 那两行）。
  `&SCF` 里与杂化相关的是 `&OUTER_SCF` / `SCF_GUESS`，**`&SCF` 下没有"HF 成分"这个键**。
  > 📌 **更正记录**：讲师课上把 HSE06 的成分说成"就是在 `&SCF` 这个 section 里面，我们要定义它的（Hartree-Fock）的成分"
  > （`videonotes/cp2k-4-…-精读笔记 L1939–L1946 [161:29–162:07]`）。官方路径是 **`FORCE_EVAL/DFT/XC/HF`**
  > （G 层示例 `references/official/02_dft_methods.md:675` 的 `&HF FRACTION 0.25` 位于 `&XC` 块内；
  > `python _kw_probe.py --section FORCE_EVAL/DFT/XC` 可列出 `&HF` 子段）。**按官方路径写，不要照抄讲义这一句。**
- **周期性体系用杂化的代价：两说并列** ——
  讲师口径 **"比纯泛函慢 10 倍或者 100 倍"**（`videonotes/cp2k-4-…-精读笔记 L609–L615 [46:18–46:48]`；理由是周期性体系里
  处理 HF 交换"数学上非常困难，比分子体系难得多"）；本 skill 工具层的对比数字是 **HSE06 约 5–20×、SCAN 只贵 1.5–2×**
  （`scripts/recommend.py` 内的价格对比）。两者体系/版本/是否用 ADMM 都不同，**都保留**；
  给机时预估时按 **5–100× 的区间**说，并要求用户**自己测**（§11 的 ADMM 就是把这档成本压下来的手段）。

---

## 9. "从 0 到收敛"的起步阶梯（推荐默认工作流）

> **第 0 步（写完输入、提交前）：先做输入自检**——`cp2k -c input.inp`（**递归检查所有 `@INCLUDE`**，T09 P8）
> 与 `cp2k -e input.inp`（导出含默认值 + 已解析预处理变量的"完整输入"，T06 P12）。
> 用了 `@SET/@IF/@INCLUDE` 模板的输入**必须**先走这一步；**restart 文件本身就是完整输入**，
> 可直接 `cp2k -i PROJECT-1.restart` 续算。
> **完整规则（`@SET` 只能 3 个 token、文件名行禁止行内注释、`@INCLUDE` 相对 CWD 的多目录布局、
> `&FARMING` 批处理）见 F 层 `playbook.md` §3.1 与本节 §21**——此处只给"提交前动作"这一条。

1. **结构 sanity（最便宜）**：用推荐命令先跑一次；大 slab 先 `--fixed-atoms` 冻底层，
   只放对吸附质/表层。重点确认：SCF 能收敛、初始力方向合理、无 NaN。
2. **生产级优化**：收紧 CUTOFF 到目标档，MAX_FORCE 6e-4，按需开 `--dispersion`/`--multiplicity`；
   金属加 `--smear` + k 点。得到可信平衡结构/能量。
3. **精修（可选）**：在优化结构上用 `--functional HSE06` 做单点能拿准确反应能/带隙；
   或 `--type vib` 确认极小点（无虚频）/ 过渡态（唯一虚频）。
4. **收尾**：`parse_output.py` 取能量/力/收敛 → `diagnose.py` 看是否要调参 →
   后处理（postprocess.md）。

---

## 10. 结果判读（对应 diagnose.py）

| 信号 | 含义 | 改哪 |
|---|---|---|
| SCF NOT converged / 达最大迭代 | SCF 不收敛 | `--outer-scf`；金属加 `--smear`；`&SCF MAX_SCF→500`；`--mixing-method pulay` 或 `multisecant`（注意 `FULL_ALL` 不是合法 `&MIXING METHOD`）；`SCF_GUESS RESTART` |
| GEO_OPT NOT converged | 几何未收敛 | `&GEO_OPT MAX_ITER→800`；力振荡换 `OPTIMIZER CG`/`BFGS`；先 `CELL_OPT`；可放宽 `MAX_FORCE 1e-3` |
| 金属 + k 点但无 SMEAR | 费米面抖动 | `--smear` |
| AIMD 能量漂移 >1% | 积分误差 | `&MD TIMESTEP 0.5→0.25`；查 thermostat；确认 `--smear` |
| 吸附能/结合能比 VASP/文献"偏大" | **先想 BSSE**（高斯基组叠加误差，非算错） | 见 §28.2：加大基组 / 做 BSSE 校正 / 精确静态换平面波 |
| 振动分析有虚频 | 非极小点 / 或预期鞍点 | 极小点目标→沿虚频 distort 再优化；过渡态目标→唯一虚频符合预期 |
| GPW 病态 / 截断警告 | 截断过低 | `&MGRID CUTOFF` 增大；调 `&QS EPS_DEFAULT` |

> 计算化学是"选 → 跑 → 看 → 调"的循环。diagnose.py 把"看"这一步自动化，
> 但它给的是**建议方向**，最终取舍仍由你带化学直觉判断。

### 10.1 吸附能 / 反应能的五步流程（含"裸 slab 必须单独重优化"）

> 出处：`videonotes/cp2k-3-CP2K计算流程与参数详解-精读笔记 L1526–L1543 [142:10–143:42]`。
> 本节上表只给了"吸附能偏大 → 先想 BSSE"，这里补**可照做的工作流**。

1. **优化"分子吸附态"**（整体）→ `grep E=` 从 `cp2k-pos-1.xyz` 注释行取**末帧能量**。
2. 存进表格（讲师用 Excel）。
3. **优化"解离吸附态"**（整体）→ 同样取能量。
4. ⭐ **再算参考态的能量：裸 slab** —— 讲师原话"**还有算两个内容：一个是算这个 slab、
   下面这个 slab 这个能量 —— 把下面单独这一块做一个结构优化**" ⇒
   **裸 slab 必须从吸附体系里抽出来、单独重新优化**（不是拿吸附体系的单点、也不是直接拿整体优化前的初始 slab）。
   > ⚠️ 讲师原话说"算两个内容"但只点明了 slab 这一项；**另一个是什么本层不臆测**（标准定义里还有一个"孤立吸附质"，
   > 但那不在本次可核对的范围内）。**引用时按"至少要有单独重优化的裸 slab"这一条执行。**
5. 相减得吸附能。

- **量级参考**（讲师该算例，**只作量级判据**）：水分子吸附能 ≈ **−1 eV**；解离吸附能 ≈ **1.5 eV**。
- ⚠️ **单位必须换算**："**不要忘记转化一下单位 —— 本来这个单位是 a.u.（Hartree），现在要把它转化成电子伏特**"
  （1 Hartree ≈ 27.211 eV，见 §22.1 的单位警告）。
- **为什么要"单独重优化"**：吸附质会改变表面弛豫/重构，用"初始 slab"或用"未重优化的 slab"当参考，
  等于把**表面弛豫能**混进了吸附能 —— 这是"吸附能对不上文献"的常见第二根因（第一根因是 BSSE，见 §28.2）。
- 与 §28.2 配合：**精确静态吸附能要用大基组或做 BSSE 校正**，且必须写清参考态是怎么算的（可复现性）。

---

## 11. ADMM 杂化降本（v2 新增，已对照手册核对）

| 场景 | 推荐 | 说明 |
|---|---|---|
| HSE06 / B3LYP + 任何 >20 原子体系 | **必须开 `--admm`** | ADMM 用辅助基组算精确交换，成本降 3-5x |
| 杂化泛函 + <10 原子小分子 | 可不开 | 全精度 HF 可接受，但 ADMM 通常更快 |
| Meta-GGA (TPSS/SCAN) | **不需要** | 无精确交换，ADMM 不适用 |

> **ADMM 原理与正确配置**（对照 manual `methods/dft/hartree-fock/admm.html`）：精确交换积分是 O(N^4) 瓶颈。ADMM 把密度矩阵投影到更小的辅助基组算交换、再加主/辅差异的校正项。需要三件套：
> 1. 一个杂化泛函（或任何产生 HFX 的设定）；
> 2. 每个 `&KIND` 加 `BASIS_SET AUX_FIT <辅助基组名>`（模板 `--admm` 自动加 cFIT，MOLOPT 体系用 `BASIS_ADMM_MOLOPT` 文件）；
> 3. `&AUXILIARY_DENSITY_MATRIX_METHOD` 段选 ADMM 变体 + 校正泛函（`ADMM_TYPE ADMMS`，或显式 `METHOD BASIS_PROJECTION` + `ADMM_PURIFICATION_METHOD MO_DIAG` + `EXCH_CORRECTION_FUNC PBEX`——模板用的是后者，等价且合法）。
>
> 实践检查：辅助基组是近似的一部分，太小会让交换校正过大、降精度；太大则提速少。生产工作至少对比一个更大的辅助基组，或在小体系上用无 ADMM 参考核对总能/力。ADMM 只加速交换计算，**不替代**主基组、实空间网格、SCF 阈值的收敛。
> 对催化体系（Au/Pt/Ni slab + 吸附质），HSE06+ADMM 的总耗时通常与 TPSS 持平或更低。

> **HFX 的成本阶梯（H 层教材增量；出处 T05 P8–P11，见 `references/h_tutorials/notes/03_hybrid_admm_parallel.md` §3.1）**
> —— 本节此前只有"精确交换积分是 O(N^4) 瓶颈"一句，以下是这条瓶颈的**三次降价**（第 0 行是标度起点）：
>
> | 步 | 标度 | 机制 | 关键字挂钩 | 出处 |
> |---|---|---|---|---|
> | 0 | `O(N⁴)` | 4 中心 ERI `E_X^HFX[P] = −½ Σ P_μσ P_νσ (μν\|λσ)`，四个基函数指标耦合 | — | T05 P8 |
> | 1 | `(1/8)O(N⁴)` | ERI 的 **8 重置换对称**（只省常数，**不改标度**） | — | T05 P9 |
> | 2 | `O(N²)` | **Schwarz 不等式筛选** `\|(μν\|λσ)\| ≤ \|(μν\|μν)\|^½\|(λσ\|λσ)\|^½`，整块丢掉小积分 | **`EPS_SCHWARZ`**（`&HF &SCREENING`） | T05 P10 |
> | 3 | `O(N)` | **密度矩阵筛选** `P_max × [Schwarz 上界] ≤ ε` | **`SCREEN_ON_INITIAL_P`** | T05 P11 |
>
> **关键实操**：第 3 步的 `P_max` 取自上一步 SCF 的密度矩阵，教材明确要"用**预收敛的 GGA 密度矩阵**"
> （T05 P11，原话 "use pre-converged GGA density matrix"）⇒ **先用 PBE 收敛波函数与几何，再用
> `SCF_GUESS RESTART` + `WFN_RESTART_FILE_NAME` 开杂化**（T05 P25③、T05 P29；与本节上文、§31.7 同一逻辑）。
> 教材另注：第 3 步"**对用杂化泛函做 DFT-MD 特别有用**"，但 `SCREEN_ON_INITIAL_P TRUE` **要求初猜足够好**
> （T15 P2 的 `&SCREENING` 注释 "needs a good (GGA) initial guess"）。
>
> **`HFX_MEM_INFO` 输出块怎么读**（A–G 层此前 grep **零命中**；出处 T05 P31 / T15 P2，见 `notes/03` §3.3 与 `notes/05` §4.11）
> ——真实输出的 ERI 内存账（金刚石例，T05 P31）：`cart. primitive ERI's calculated 218,851,035,670` /
> `sph. ERI's calculated 152,193,561,473` / `stored in-core 22,711,518,963` / `on disk 0` / **`on the fly 0`** /
> `Total memory consumption ERI's RAM [MiB] 21290` / `Whereof max-vals [MiB] 1516` /
> `Total compression factor ERI's RAM 8.14` / `Size of density/Fock matrix [MiB] 764` / `Size of buffers [MiB] 118`。
> - **先看什么**：① `Est. max. program size before HFX` 用来估内存峰值；
>   ② `Total memory consumption ERI's RAM` 是 ERI 常驻内存；③ `Size of density/Fock matrix` 与 `Size of buffers` 是另外两块开销。
> - **`Number of sph. ERI's calculated on the fly` 理想必须是 0**——教材原文 "should ideally be zero.
>   We want to keep ERIs in memory during the SCF loop"（T05 P31）。**非 0 ⇒ ERI 没能常驻内存、每个 SCF 步重算，
>   是第一圈特别慢之外的持续开销**；对策是提高 `MAX_MEMORY` 或用更多 MPI 进程（T05 P32）。
> - `Total compression factor ERI's RAM` 是 `&HF &MEMORY EPS_STORAGE_SCALING` 换来的压缩比
>   （T15 P2 例：`EPS_STORAGE_SCALING 0.1` → **8.03**；该关键字此前 A–G 层零命中，见 §8）。
> - 同块附近的 `*** WARNING in hfx_energy_potential.F:600 :: The Kohn Sham matrix is not 100% occupied …`
>   的官方解读在 G 层 `08_errors_and_faq.md` §3.8.4（本层不重复）。
>
> **`MAX_MEMORY` 是"每个 MPI 进程"的额度**（出处 T05 P32）：教材原文 "Note **MAX_MEMORY is the memory per MPI
> process** for ERIs, you must **leave space for operating system and rest of the CP2K calculation**."
> ⇒ 按"节点内存 ÷ 每节点 MPI 进程数"留出余量后再填，**别按整机内存填**。
> G 层 `08_errors_and_faq.md:136` 只说"上限取决于 MPI 进程数与 `MAX_MEMORY`（MB）"，**未点明 per-MPI-process 与留余量**。
> 极大杂化算例建议用混合 MPI/OpenMP 版 `cp2k.psmp`（T05 P32）。
>
> **ADMM 辅助基组命名学**（A–G 层此前只有文件名，无成分表；出处 T05 P23–P24，见 `notes/03` §3.3）
> - **主族**（最初 H–Cl，按原子逐一优化）：**FIT3** = 每个价轨道 **3 个高斯指数**；**cFIT3** = FIT3 的**收缩**版；
>   **pFIT3** = FIT3 **+ 极化函数**；**cpFIT3** = cFIT3 + 极化；**aug-FIT3 / aug-cFIT3 / aug-pFIT3 / aug-cpFIT3** = 再加一个**弥散**函数。文件 `data/BASIS_ADMM`。
> - **过渡金属**：**FIT10 = 4s+3p+3d**；**FIT11 = 4s+3p+3d+1f**；**FIT12 = 4s+3p+4d+1f**；**FIT13 = 4s+4p+4d+1f**；
>   收缩版 **cFIT10–cFIT13 是 double-ζ 质量**（Ling & Slater, unpublished）。文件 `data/BASIS_ADMM_MOLOPT`。
> - 两条命名学提醒（T05 P24）：**主族与过渡金属的 ADMM 基命名规则"略有不同"**；**"第一个" ADMM 基通常不含极化函数**（别默认它最准）。
> - **为什么有 cFIT 系（收缩）**：教材原文 "Linear algebra can get expensive for larger systems (**reason for contracted
>   auxiliary basis sets**)"（T05 P21）⇒ **c 版主要为省线性代数，不是省积分**。
> - **怎么选**（T05 P25④ + T05 P27）：**从小辅助基起步、逐步加大**，并用无 ADMM 参考或小体系全精度结果核对。
>   T05 P27 的硅例：`cFIT3 → FIT3 → pFIT3` 积分数 4.22×10¹¹ → 4.24×10¹¹ → **1.45×10¹²**（pFIT3 贵 3.4 倍），
>   带隙 1.16 ⚠️ → 1.80 → 1.98 eV（VASP 参考 1.93）⇒ **辅助基越富越准也越贵**。
>
> ⚠️ **版本口径提醒（防误引，非本层旧结论）**：H 层教材 T05 成稿于 **2019-03**，其 T05 P25⑤ 写
> **"ADMM has only been implemented for use with GPW"** —— **现行版本已不成立**：G 层 `11_version_changelog.md:223`
> （2023.2）记 **"GAPW 下启用 ADMM（#2729）"**，同文件 242 行（2023.1）另有 **"TDDFT/线性响应：GAPW/GAPW_XC 与
> ADMM/GAPW 选项（#2200）"**。⇒ **按"G 层 > 教材"裁决：以 G 层为准**，教材那句只能当 2019 年口径引用。
> 同理 T05 P25⑥ 的"只有 ADMM1 兼容 smearing/TDDFPT"也不是现行硬约束（G 层 `02_dft_methods.md` §6.5 认为
> `ADMM2` 在超出基态杂化的流程中支持最广）。**A–F 层此前没有写过"ADMM 只支持 GPW"这类过时结论（已 grep 确认），
> 此处只作防误引登记，不构成对本层的更正。**

---

## 12. SCF 混合方法选择（v2 新增，已对照手册核对）

| 场景 | 推荐混合方法 | 说明 |
|---|---|---|
| 默认 / 绝缘体 / 半导体 | `BROYDEN_MIXING`（`--mixing-method broyden`） | 最通用，收敛稳定 |
| 金属 / 窄带隙体系 | `PULAY_MIXING`（`--mixing-method pulay`） | PULAY 对费米面附近的电荷振荡更鲁棒 |
| 极难收敛（磁性/强关联/大体系） | `MULTISECANT_MIXING`（`--mixing-method multisecant`） | 多重割线混合，比 PULAY 更稳；注意 `FULL_ALL` **不是** `&MIXING` 的合法 METHOD（官方解析器会报错），已废弃 |
| OT 不收敛时 | 换 `--ot-minimizer cg` 或 `broyden` | DIIS 在某些体系发散；CG/BROYDEN 更稳健但每步更贵（注意 `LBFGS` **不是** `&OT` 的合法 MINIMIZER，仅 `&GEO_OPT` 可用） |

> **可微调的实战参数**（手册 `&MIXING` / `&OT`）：
> - BROYDEN：`ALPHA`（新密度占比，~0.1–0.4）、`NBROYDEN`（历史向量数，~8）、`BETA`（Broyden 欠松弛，nico 用 ALPHA 0.1 / BETA 1.5）。
> - PULAY：`ALPHA ~0.2`、`NMIXING 2`（启动 DIIS 前的最小混合步数）、`N_SIMPLE_MIX`（先跑几步 Kerker 阻尼再进 PULAY）。
> - KERKER 阻尼：`BETA`（抑制电荷 sloshing 的分母参数，公式 `rho_mix(g)=rho_in(g)+alpha·g²/(g²+beta²)·(rho_out-rho_in)`）。
> - OT：`SAFE_DIIS`（DIIS 步指向远离极小值时拒绝、改 SD）、`N_HISTORY_VEC`（DIIS/BROYDEN 历史向量数）。OT 默认设置已高效稳健，多数体系无需动。
>
> 混合方法选择优先级：BROYDEN(默认) → PULAY(金属) → MULTISECANT(难收敛)。配合 `&OUTER_SCF` 外层循环使用效果最佳。

> **⚠️ 落点纠正（批次 7 对照 CP2K 2026.1 `cp2k_input.xml` 核实）**：`ADDED_MOS` 与 `CHOLESKY` **不是** `&SCF &DIAGONALIZATION` 的子关键字，而是 **`&SCF` 顶层关键字**（`CHOLESKY` 默认 `RESTORE`，可选 `OFF/REDUCE/RESTORE/INVERSE/INVERSE_DBCSR`；`ADDED_MOS` 默认 `0`，金属/过渡态/开壳层需设数百个空轨道）。`&DIAGONALIZATION` 只含 `ALGORITHM/JACOBI_THRESHOLD/EPS_JACOBI/EPS_ADAPT/MAX_ITER/EPS_ITER`，无 ADDED_MOS/CHOLESKY。`gen_inp.py` 的 `--added-mos`/`--cholesky` 正是写在 `&SCF` 顶层，已校验合法。完整 SCF 收敛决策见 **§22**。

---

## 13. MD 恒温器与系综（手册核对 v3）

### 系综（MOTION/MD 的 ENSEMBLE，严格枚举）
`NVE`(微正则) · `NVT`(正则) · `NPT_I`(等温压，各向同性胞) · `NPT_F`(等温压，柔性胞) ·
`NPE_F`/`NPE_I`(等压，无恒温器) · `MSST`/`MSST_DAMPED`/`HYDROSTATICSHOCK`(稳态冲击) ·
`ISOKIN`(恒动能) · `REFTRAJ`(读 reftraj.xyz 算性质) · `LANGEVIN`(朗之万动力学) ·
`NVT_ADIABATIC`(CAFES 绝热)。
> 注意：没有笼统的 `NPT`——等压必须选 `NPT_I`(胞只缩放、形状不变) 或 `NPT_F`(胞可形变)。`gen_inp.py --ensemble npt` 默认走 `NPT_F`（柔性、最通用）；若要保角度/对称性用 `NPT_I` 或 CELL_OPT。

> **为什么 AIMD 首选 NVT（这是因果，不是习惯）**：AIMD 受计算量限制，原子数只有"100 个或者是几百个"，
> "**这个时候压力是不好控制的**"（NPT 的问题）；而"**如果这个原子数太少的时候，它也是不好在这个 NVE 系综当中平衡下来的**"。
> ⇒ 讲师口径：经典 MD 更常用 NPT/NVE，**而 AIMD 目前最常用的系综还是 NVT**
> （`videonotes/cp2k-1-1-AIMD第一讲-精读笔记 L551–L573 [49:37–52:22]`）。
> NVT 的三个约束要读准：**N 不变、V 在模拟过程中不变、T 只要在一定范围内波动**即可（同上）。

> ⚠️ **`ENSEMBLE` 的官方默认是 `NVE`，不是 NVT**（`MOTION/MD ENSEMBLE default=NVE`，`_kw_probe.py MOTION/MD` 复核）
> ⇒ **写 MD 输入必须显式写系综**，否则你拿到的是微正则系综（总能量守恒、温度自己漂），
> 与"AIMD 最常用 NVT"的直觉正好相反（`videonotes/cp2k-4-…-精读笔记 L766–L784 [60:22–61:50]`）。
> 同理 `TIMESTEP` 默认 `0.5 fs`、`TEMPERATURE` 默认 `300 K` —— 与"含氢体系 0.5 fs"的推荐值一致，属"默认即安全"。

### 恒温器（THERMOSTAT 子节，配 NVT/NPT 用）
| 场景 | 推荐恒温器 | 关键关键字（落点） |
|---|---|---|
| 表面催化 AIMD | **LANGEVIN**（`--thermostat langevin`） | `&MD &LANGEVIN GAMMA`（摩擦系数，越大越快热化；表面常用 0.001–0.01 fs⁻¹ 量级，或用 `TIMECON` 等价表达）。对表面温度控制最稳、不易整体过热。 |
| 体相 / 平衡态 | **CSVR**（默认的 canonical sampling via velocity rescaling）或 **NOSE** | CSVR：`&MD &THERMOSTAT &CSVR TIMECON`（小→强热化、大→弱；平衡常用 100–1000 fs）。NOSE：`&MD &THERMOSTAT &NOSE TIMECON`+`LENGTH`(链长,默认3)+`YOSHIDA`(积分阶)+`MTS`(多时间步)；Nose 可平滑延伸到 NPT。 |
| 精确正则分布 / 谱 | **GLE**（广义朗之万） | `&THERMOSTAT &GLE` + `S` 矩阵 + `THERMOSTAT_ENERGY`/`RNG_INIT`；高级，可定制动力学谱。 |
| 弱耦合 / 特殊 | **AD_LANGEVIN** | `&THERMOSTAT &AD_LANGEVIN CHI`/`MASS`；用于特定绝热耦合场景。 |

> **关键字名钉死：热浴耦合的区域是 `&MD &THERMOSTAT REGION`**（默认 `GLOBAL`），枚举
> **`GLOBAL` / `MOLECULE` / `MASSIVE` / `DEFINED` / `NONE`**（`DEFINED` 配 `&DEFINE_REGION`，用 `LIST`/`MOLNAME` 指定原子或分子）。
> **CP2K 没有 `COUPLING_REGION` 这个关键字**（`python _kw_probe.py --find COUPLING_REGION` → 0 命中）。
> > 📌 **更正记录**：讲师口播为 "`COUPLING_REGION`"（`videonotes/cp2k-4-…-精读笔记 L1025–L1033 [78:17–79:14]`），
> > 但同一处给的取值 GLOBAL/MOLECULE/MASSIVE 与官方 `REGION` 的枚举**完全一致** ⇒ 是**关键字名听错**，不是另一套功能；
> > 且讲师漏了官方另有 `DEFINED` / `NONE` 两档。本库此前只用中文"COUPLING REGION / 热浴耦合方式"表述、没写英文键名，
> > 所以没被带错；**写输入时用 `REGION`**。
> **CSVR 的 `TIMECON` 官方语义**（默认 **1000 fs**）："**A small time constant will result in strong thermostatting
> (useful for initial equilibrations) and a large time constant would be adequate to get weak thermostatting in
> production runs.**" ⇒ **预平衡段把 `TIMECON` 调小（强耦合）快速平衡，生产段调大**。
> 这是与本节表格"小→强热化、大→弱"完全一致的官方背书（`videonotes/cp2k-4-…-精读笔记 L1016–L1023 [77:38–78:17]`）。

### 恒压器（仅 NPT/NPE：MOTION/MD/BAROSTAT）
- `PRESSURE`（初始压强，1 值或 9 分量压强张量）、`TIMECON`（恒压时间常数）、`TEMPERATURE`（恒压器温度，默认取系综温度）、`TEMP_TOL`（重缩放容差）。
- `VIRIAL`：**仅 NPT_F 有效**，可屏蔽某些笛卡尔分量，让胞只沿特定轴弛豫（各向异性处理很有用）。
- 实现：NPT_F 通常用 Parrinello–Rahman 或 MTTK 风格（由 CP2K 内部选），无需手动选算法。

> 长 AIMD（>50ps）务必加 `--restart-freq 500`（或更大），防止作业中断丢失全部进度。
> 初始化：用 `TEMPERATURE` 设初速温度；`TEMP_TOL` 控制允许偏离、`COMVEL_TOL` 清质心漂移、`ANGVEL_ZERO` 清角速度（非周期体系）；`ANNEALING`/`TEMPERATURE_ANNEALING` 做退火。

### 13.1 时间步长与核质量 —— "精度换速度"的两个杠杆（批 14）

> 出处：字幕 `S1.1.txt:1628–1827`、`S1.2.txt:148–162`、`S4.txt:2460–2509`。

- **步长上限的物理判据**：**体系中最快运动周期的 1/10** 是"可以承受的极限"，再大体系就会爆炸、或把不该断的键震断（`S1.1.txt:1729–1738`）。
  - 例：水的 O–H 伸缩 ~3000+ cm⁻¹ ⇒ 周期 ~10 fs ⇒ 1/10 = **1 fs 已是上限**；而讲师明确说"这个时候 1 fs 其实已经是一个比较不合理的数值了"，文献里做水常取 **0.5 fs（= 1/20）**（`S1.1.txt:1739–1756`）。
  - **含氢体系禁用 2 fs**：2 fs 会让 O–H 键"自己就给震断了"（`S1.1.txt:1757–1763`）；`S1.2.txt:154–162` 同口径——"如果这个体系当中包含氢，那肯定不能设置成两飞秒了，这个时候体系会出问题"。
  - **只有重元素、不含氢**的体系才可以把步长放大到 2 fs（`S1.2.txt:155–159`）。
- **步长下限的判据：太短的代价是"白白浪费机时"（不是精度不够，是信息量不够）**：设 **0.1 fs** 时
  "虽然这个时候我们可以把这个模拟得非常精确，但……**我们白白地浪费了很多的计算量**。因为每一步运动的这个距离都太短了，
  那么这个时候我们这个模拟了很长的时间，**它依然没有产生我们想要的变化，或是依然没有得到一条有足够多信息的一条轨迹**"
  （`videonotes/cp2k-1-1-…-精读笔记 L680–L682 [61:11–61:41]`）。
  ⇒ 结论：**步长不是"越小越保险"**。上限由最快振动周期（1/10 极限、1/20 常态）定，**下限由"轨迹要产生足够变化"定**；
  含氢体系落在 **0.5 fs** 上，就是这两条边界之间最宽的那一段。
- **想用长步长，正确做法是"改核质量"，不是"冻结键长"**：
  - 把键长固定死（如 O–H 钉在 1 Å）是**经典 MD** 的常规做法；但 **AIMD 里水分子常直接参与反应**——"如果这个时候把水分子键长给固定住，那这个模拟得到的信息很有可能是错误的"（`S1.1.txt:1768–1793`）。**不要用约束去换步长。**
  - **改核质量是讲师明确推荐的通用技巧（不是个例）**：把 H 的原子质量设为 **2**（即氘代），最大振动频率从 **3300+ cm⁻¹ 降到 ~2500 cm⁻¹**，步长即可放到 **1.2 fs**；相对 0.5 fs，"计算量直接就差出去了一倍多"（`S1.1.txt:1794–1822`）。
  - **文献里的写法就是这条参数操作**：Computational Methods 里写"用 D 取代 H / deuterium"，本质就是"把这个氢的原子质量设置成 2"（`S1.1.txt:1796–1802`）。读文献时看到这句，就知道作者在用质量换步长。
  - ⚠️ **风险等级不同，别混用**：**H→D 是课程推荐的标准动作**；而把**重原子**质量改小（讲师把团簇 Au 的 `MASS` 197 → 19.7，好让 Au 动起来）是"招法"，讲师自己说模拟是否还能还原真实体系变化"**这个是存疑的**"（`S4.txt:2460–2509`）。前者可作默认，后者只在"体系太重、几百 ps 都不动"时作为探索手段，且必须在文中声明。
  - **讲师补的动机（为什么明知存疑还要做）**："因为在这个模拟过程当中，我们这个计算量已经把我们给卡死了 ——
    如果我们设置 197，肯定是模拟不完的。**所以说为了让这个计算量可以承受，必须要把这个质量的值给降下来**"
    （`videonotes/cp2k-4-…-精读笔记 L1131–L1146 [88:04–89:20]`）。
    ⇒ 定性改为"**算力不足时的无奈之举**"，写作时必须在 Computational Methods 里声明，并说明它改变了动力学时间尺度。
- 与 **§29** 的分工：这里管"步长/质量怎么选"，§29 管"选完之后结果为什么不可复现、要不要多副本"。

### 13.2 退火 / 升温：CP2K 侧的两个反直觉点（批 14）

> 出处：字幕 `S4.txt:1640–1740`、`1690–1703`、`2228–2260`。

- **退火与热浴冲突**：设了 `&MD &ANNEALING` 就**不要再设 `&THERMOSTAT`**，退火段用 **NVE**（`S4.txt:1690–1703`、`2228–2229`）。照模板"顺手加个热浴"会踩冲突。
  > ✅ **官方机制（本轮用官方 XML 定案，不再是"讲师经验"）**：`MOTION/MD ANNEALING`（默认 `1.0`）的官方描述原文是
  > "Specifies the rescaling factor for annealing velocities. **Automatically enables the annealing procedure.
  > This scheme works only for ensembles that do not have thermostats on particles.**"
  > ⇒ 退火靠**缩放速度**实现，**凡"把热浴挂在粒子上"的系综都不能用** —— 这是 CP2K 的**实现约束**。
  > （`python _kw_probe.py MOTION/MD/ANNEALING`；`videonotes/cp2k-4-…-精读笔记 L786–L799 [61:50–62:26]`、`L1041–L1053 [79:53–81:15]`）
- **CP2K 的退火只能按倍率，不能线性**：升温用倍率 **1.001**（每步 +1‰），降温用 **0.99 / 0.999**；讲师原话"CP2K 的退火有点不太智能，就是不能以均匀的方式去退火"（`S4.txt:2230–2260`）。**这与 VASP 的线性 `TEBEG`/`TEEND` 直觉不同**——跨程序迁移时要换算成"每步乘一个因子"。
- **热浴的 `TIMECON` 经验档**：`&MD &THERMOSTAT &NOSE` 里"唯一需要改的就是 `TIMECON`"，经验值 **1000–1500**（讲师"一般都是把它设置成 1000 或者 1500 就不动了"），并说 1000/1500/2000 对结果"没有什么特别大影响"（`S4.txt:1711–1740`）。
  > ✅ **单位已彻底查清（2026-10；结论与上一版相反，已更正）**
  >
  > **`TIMECON` 的默认单位是 `fs`，默认值 `1.0E+003`（1000 fs）**（`CSVR`/`BAROSTAT` 同为 fs/1000）。
  > 查证：`python _kw_probe.py --section MOTION/MD/THERMOSTAT/NOSE`。
  >
  > **但 `wavenumber_t` 是 CP2K 的合法时间单位，而且讲义用的正是它** —— 不是笔误：
  > - **语义**：数值是**波数 ν̃（cm⁻¹）**，CP2K 取该波数对应振子的**周期**作为时间，
  >   即 **`t[fs] = 33356.40952 / ν̃[cm⁻¹]`**（波数越大 → 时间越短）。
  > - **权威依据**：CP2K 核心开发者 Matthias Krack 在官方邮件列表的原话——
  >   "`TIME [wavenumber_t] 33356.40952` is equivalent to `TIME [fs] 1.0`"
  >   （[CP2K:15275](https://lists.cp2k.org/archives/cp2k-user/2021-May/015403.html)，2021-05-03）。
  > - **真实算例实测印证**：`references/h_tutorials/cases/` 收录的 **Cu(100)-水 AIMD 生产算例**
  >   输入写 `TIMECON [wavenumber_t] 1000`，其 `cp2k.out` 第 162 行输出
  >   `THERMOSTAT| Nose-Hoover-Chain time constant [  fs]  33.36` —— 与 33356.40952/1000 = **33.36 fs** 完全吻合。
  >
  > ⚠️ **实务要点（这条最容易踩）**：带不带单位标注，**数值含义差 30 倍**：
  > | 写法 | 实际时间常数 | 耦合强度 |
  > |---|---|---|
  > | `TIMECON 1000`（默认单位 fs） | **1000 fs** | 弱 |
  > | `TIMECON [wavenumber_t] 1000` | **33.36 fs** | 强（快 30 倍） |
  >
  > ⇒ **抄别人的输入卡时必须连单位方括号一起抄**。讲师习惯用 `[wavenumber_t]` 写法
  > （"1000" 是他嘴里那个数），换算成 fs 是 **33 fs 量级**，属正常强耦合档；
  > 而"写 1000 就是 1000 fs"的读法只在不带单位时成立。
  >
  > 📌 **更正记录**：2.7.5 曾据官方 XML 的默认单位判定"讲师说的波数有误、直接写 1000 即可"——
  > 该结论**只看到默认单位、漏了显式单位标注**，是错的。本轮由**真实算例的 .out** + **官方邮件列表**
  > 双向核实后更正。
- **系综枚举以本 §13 上文为准**；补充一条对照：CP2K 比 VASP 多出 **`NPE_I`/`NPE_F`**（等压、无恒温器）两档，`NPT_I` 是各向同性胞、`NPT_F` 的 F = flexible 才让晶胞完全自由（`S4.txt:1645–1677`）。

---

## 14. Properties / PRINT 输出选择（手册核对 v4）

所有性质都挂在 `&FORCE_EVAL &DFT &PRINT` 下。**通用机制**（先搞懂，后面每个性质都一样）：
- 每个子节本身是个"打印开关"：写 `&PRINT &XXX ON` 才输出；常用伴随关键字 `ADD_LAST`(末步追加/标记)、`FILENAME`、`LOG_PRINT_KEY`。
- **打印频率**用 `&EACH` 子节控制，其关键字映射到迭代层级，值=间隔步数（0/负=不打印）：`QS_SCF`(每 SCF 步)、`GEO_OPT`(每优化步)、`CELL_OPT`、`MD`(每 MD 步)、`METADYNAMICS`(每撒一座山)。AIMD 全程每步 dump cube 会爆盘——务必用 `&EACH MD 100` 之类控频。
- 多数性质默认**关闭**，需显式 `ON`。
- ⚠️ **`&DFT/&PRINT` 是"全开关"：不设 `&PRINT` 就等于什么都不输出**。讲师原话："`PRINT`……在这个 CP2K 的输入文件里面
  可以说是**无处不在**的……**如果我们不设置 `PRINT`，这相当于这些东西都不输出**"
  （`videonotes/cp2k-3-…-精读笔记 L835–L851 [65:20–66:57]`）。
  ⇒ **"为什么我的 cube / 受力 / PDOS 文件不见了"的第一嫌疑人，是根本没写这个子段**（不是路径写错）。
  找法：想输出什么 → 在 `&DFT/&PRINT` 下写对应子段 + `FILENAME`。
- **`&PRINT` 一族的位置别放错**：`&MOTION/&PRINT` 下有 `&TRAJECTORY` / `&VELOCITIES` / `&RESTART` / `&RESTART_HISTORY`
  等 18 项；而 **`&MOTION/&MD/&PRINT` 里没有 `&TRAJECTORY`**（只有 `FORCE_LAST` 与 `&ENERGY`/`&TEMP_KIND`/
  `&CENTER_OF_MASS`/`&ROTATIONAL_INFO` 等 9 项）⇒ 写成 `&MD &PRINT &TRAJECTORY` 会报"未找到"；
  `MOTION/PRINT/TRAJECTORY &EACH MD` 默认就是 **1**（"AIMD 这里写 1"= 默认）
  （`videonotes/cp2k-4-…-精读笔记 L824–L840 [63:32–64:20]`；`_kw_probe.py --section MOTION/PRINT` 与 `MOTION/MD/PRINT` 复核）。
- **两个"默认就是你要的"写入频率（都不必手写）**：
  - `&MOTION/&PRINT/&RESTART_HISTORY &EACH MD` 默认 **500** ⇒ 讲师说的"我们还需要重新再定义一下这个 500 步"
    **就是官方默认值**，只在需要更密/更疏时才改（`videonotes/cp2k-4-…-精读笔记 L842–L859 [64:24–65:25]`）。
  - `&SCF/&PRINT/&RESTART` 的打印频率默认 **8**（每 8 个 SCF 步写一次 wfn；`FILENAME RESTART`、`BACKUP_COPIES 3`、
    `ADD_LAST NUMERIC`）⇒ 想少写就改大（讲师写 `100`，并猜"默认好像是 25 还是 20"——**都不是，官方默认 8**）
    （`videonotes/cp2k-4-…-精读笔记 L1096–L1099 [85:27–85:52]`；`_kw_probe.py --section FORCE_EVAL/DFT/SCF/PRINT/RESTART`）。

| 想算什么 | 对应科学问题 | PRINT 子节（`&DFT &PRINT`） | 关键关键字 |
|---|---|---|---|
| 布居 / 原子电荷 | 谁得电子谁失电子 | `MULLIKEN` / `LOWDIN` | `PRINT_GOP`(打印轨道布居) |
| Hirshfeld 分电荷（更可迁移、基组无关） | 电荷转移定量 | `HIRSHFELD` | `SELF_CONSISTENT T`=Hirshfeld-I(迭代更准)；`SHAPE_FUNCTION` |
| 核四极矩 / NMR 四极耦合 | 固体 NMR quadrupole | `ELECTRIC_FIELD_GRADIENT`(EFG) | `INTERPOLATION`/`GSPACE_SMOOTHING`；精度需 GAPW(§15) |
| 超精细耦合（EPR） | 自由基 EPR g/超精细 | `HYPERFINE_COUPLING_TENSOR` | `INTERACTION_RADIUS`；精度需全电子(§15) |
| 投影态密度 PDOS / d-band | 催化 d-band center、态密度 | `PDOS` | `COMPONENTS`(按角动量拆分)、`NLUMO`(加虚轨道)、`LDOS`/`R_LDOS`；⚠️ `COMPONENTS` 默认 **F** ⇒ 不写只出 **s/p/d/f 四个角动量通道**，写了才再拆 px/py/pz 等分量（讲师建议**不写**，数据量小好分析） |
| 总态密度 DOS | 金属性 / 带隙 | `DOS` | `DELTA_E`(直方图间距) |
| 能带结构 | 带隙 / 能带 | `BAND_STRUCTURE` + `&KPOINT_SET` | `ADDED_MOS`；需先算 k 点(§5) |
| STM 图像 | 表界面 STM 模拟 | `STM` | `BIAS`(偏压)、`NLUMO`(正偏压需占+空)、`TH_TORB`(针尖轨道) |
| 分子轨道 cube | 前线轨道 / 成键 | `MO_CUBES` | `NHOMO`/`NLUMO`/`STRIDE`/`WRITE_CUBE`；⚠️ `NHOMO` 默认 **1**、`NLUMO` 默认 **0** ⇒ **不显式写 `NLUMO 1` 就没有 LUMO 图**；`STRIDE` 默认 `2 2 2`。**只对分子体系有判读意义**（金属的能带穿越费米能级 ⇒ MO 图无信息） |
| 电荷 / 自旋密度 cube | 密度可视化 | `E_DENSITY_CUBE` / `TOT_DENSITY_CUBE` | `STRIDE`(降采样)、`XRD_INTERFACE`(X 射线衍射)；⚠️ 一次 `&E_DENSITY_CUBE` 会**同时**出电荷密度（α+β）与自旋密度（α−β）两个 cube，机制存疑见 §14.1 |
| Hartree / XC / ELF cube | 势场 / 电子局域化 | `V_HARTREE_CUBE` / `V_XC_CUBE` / `ELF_CUBE` | `STRIDE` |
| 多极矩（偶极 / 四极） | 偶极矩 / 极化 | `MOMENTS` | `PERIODIC`(Berry phase)、`REFERENCE`、`MAX_MOMENT`、`MAGNETIC` |
| Wannier 函数 | 化学键 / 拓扑 | `WANNIER90`(实验性) | `SEED_NAME`/`MP_GRID`/`WANNIER_FUNCTIONS`；需 Wannier90 |
| Bader / 电荷分解 | 更严格的原子电荷 | `CHARGEMOL` | 调用 ChargedMol 程序 |
| Hirshfeld 力 | 约束 / 力分解 | `HIRSHFELD_FORCE`（在 `&FORCE_EVAL &PRINT`，**非** DFT/PRINT） | — |

后处理对应：PDOS → `cp2k_pdos.py`；cube → VMD/VESTA；STM → VESTA；DOS → gnuplot；band → `band.out`。

> **选择原则**：先想清"要回答什么科学问题"再开 PRINT——cube 文件巨大，AIMD 用 `&EACH` 控频。电荷分析优先 **Hirshfeld(-I)** 而非 Mulliken（Mulliken 依赖基组、不基组收敛）。核区量（EFG/NMR/超精细）必须 GAPW(§15)。

### 14.1 电子结构分析的前置条件与判读点（批 15）

> 出处：`videonotes/cp2k-5-电子结构分析与自由能势能面-精读笔记`（含时间戳）；关键字与默认值用 `_kw_probe.py` 复核。

- **⚠️⚠️⚠️ 算电荷密度差分的两个片段"一定不要再优化了"**（本次讲师用三个 ⚠️ 标注）：先**整体优化**吸附结构
  （"代表我们得到了一个局域的极小值、代表它是个吸附结构"），再分别对**裸 slab** 与**孤立吸附质**做**单点**；
  "**如果这个结构优化了之后，我们再来算电荷密度差分，它差分出来的图是不对的**"。
  ✅ 正确操作：**从整体优化末帧的 xyz 里把属于该片段的行抽出来另存**，`RUN_TYPE ENERGY`（或 `ENERGY_FORCE`）**只做单点**
  （`videonotes/cp2k-5-…-精读笔记 L319–L333 [25:08–25:48]`）。这是"差分图看起来不对"最容易被忽略的根因。
- **电荷密度差分有两种，别混**：① **差分** `Δρ = ρ_AB − ρ_A − ρ_B`（文献最常用，本例 AB = CO/Ni、A = Ni slab、B = CO）；
  ② **变形电荷密度**（deformation density）= **自洽迭代后的密度 − 各孤立原子密度之和**；讲师明确"变形电荷密度用得比较少"
  （`videonotes/cp2k-5-…-精读笔记 L312–L315 [23:37–24:54]`）。
- **`&E_DENSITY_CUBE` 一次开关出两个 cube**：`*-cube-ELECTRON_DENSITY-1_0.cube`（α+β 的电荷密度）与
  `*-cube-SPIN_DENSITY-1_0.cube`（α−β 的自旋密度），**画哪个下载哪个**
  （`videonotes/cp2k-5-…-精读笔记 L222–L223、L243–L248 [17:56–22:11]`）。
  > ✅ **机制已定案（2026-10）——原先归给 `TOTAL_DENSITY` 是错的，正确的是"UKS/磁性体系下同一段同时出两个"**：
  > **讲师逐字**："这个 `e_density_cube` **它既包含了这个电荷密度，也包含了自旋密度**啊。电荷密度就是总体的
  > 这 α 电子和 β 电子、总体的加在一块才这个电荷密度；那么这个自旋密度呢，就是自旋向上、自旋向下的 α 电子和
  > β 电子……电荷密度的差值，也就是所谓的这个自旋密度"（`S5.txt`:315–325）；紧接着演示时又说产物是
  > "`-electronic_density`……`-cube`、`-spin_density`——哎，**这两个文件是同时输出的**"（`S5.txt`:428–431）。
  > **真实生产卡也印证**：课程交付卡里那个被注释掉的块自己起的文件名就叫
  > `FILENAME Dentity_maybeSpin.cube`（`h_tutorials/cases/cu100-h2o-opt_cp2k.inp:70–72`）——
  > "**密度，也许还是自旋**"，正是"同一段两种可能"的意思。
  > ⚠️ **`TOTAL_DENSITY` 不是这个机制**：官方 XML 对它的描述是 "Print the total electronic density in the
  > case of a **GAPW** run. This keyword has only an effect, **if PAW atoms are present**. The default is to
  > print only the **soft part** of the density." —— 那是 **GAPW/PAW 的 soft/total 开关**，与 α±β 无关。
  > ⇒ **旧记录判"两说"是因为把两个不相干的东西放在一起解释**：文件个数是两个（事实），
  > 机制是"UKS 下同段输出 ρ 与自旋密度"（讲师明说），`TOTAL_DENSITY` 只在 GAPW/PAW 体系里起作用。
  > 📌 推论：**非磁性/闭壳层体系只会得到一个（电荷密度）** —— 讲师自己也说"这个体系虽然镍表面稍微带点磁性，
  > 不过看不出什么太大内容，我们就不看这个 spin density 了"（`S5.txt`:435–438`）。
- **功函数**：`V_HARTREE_CUBE` 与 VASP 的 `LVHAR` 是**同一件事**（讲师原话"这两个关键词是对应的"）；流程 =
  静电势 cube **沿表面法向做平面平均** → 真空那一段是平的，**平段的能量值就是真空能级** → 从 `cp2k.out` 读**费米能级**
  → **Φ = E_vacuum − E_Fermi**（`videonotes/cp2k-5-…-精读笔记 L858–L898 [73:33–76:55]`）。
  > 前提：slab 不对称时**不加 `SURFACE_DIPOLE_CORRECTION` 会让真空能级倾斜、上下表面功函混在一起**（§5 那条 + 其官方硬限制）。
- **电子结构分析只需单点**：讲义原文"**只需要做单点计算就可以了**"
  （`videonotes/cp2k-5-…-精读笔记 L220 [17:56–22:11]`）；"做了一次结构优化之后呢，后面这些电荷的、
  关于电子结构分析的这些内容**可以一套全都做完**"（同笔记 `L492 [41:55–42:07]`）。
  ⇒ 与 §9 的阶梯配合：**优化一次 → 一次性开齐所有 `&PRINT` 单点**，不要为每个性质重跑结构优化。
- ⚠️ **AIMD 里不要打印电子结构**（与上面这条不矛盾）：AIMD 每步 dump cube 会爆盘；正确做法是**只保留一两个结构、
  跑完再从轨迹里抽帧做单点**（`videonotes/cp2k-4-…-精读笔记 L1101–L1111 [85:52–86:43]`）。

---

## 15. GAPW —— 什么时候需要全电子精度（手册新增）

GPW（默认）只处理价电子密度，对绝大多数能量/结构问题足够。但**核电子密度敏感**的量需要 GAPW：

- 核四极矩 (EFG)、核磁共振 (NMR)、超精细耦合张量、XAS/RIXS、核附近响应；
- 小核赝势 (small-core) 体系若对核区精度要求高。
- **切换方式（CP2K 的 GAPW 是 PAW 式全电子方法）**：只需 `&DFT &QS METHOD GAPW`。**注意**：CP2K GAPW 仍使用 **GTH 赝势 + 常规轨道基组**（如 `DZVP-MOLOPT-SR-GTH`），它额外在核区用局域基组重构全电子密度——并非换 `POTENTIAL ALL`。逐 KIND 的核区半径由 `HARD_EXP_RADIUS` 等关键字控制（有默认，通常无需改）。
- GAPW 专属精度参数 `EPSFIT` / `EPSRHO0` / `EPSSVD` 控制硬/软密度拆分；调紧会增大 CUTOFF 需求。
- 若计算不需要全电子或核区精度，**优先 GPW**（更简单更快）。
- ✅ `gen_inp.py` 现支持一键 GAPW：`--gapw` 会把 `&QS METHOD` 设为 `GAPW`（已校验合法，见 `gapw_static_Si`/`gapw_geoopt_Fe` 用例）。配合 `--properties efg hyperfine` 可同时开核区性质打印。

---

## 16. 选什么计算引擎（建模型 / 方法选择，手册章）

`gen_inp.py` 当前只发射 **DFT（Quickstep / QS）** 输入。但 CP2K 还支持更便宜或更大体系的引擎；**决策阶段**就该先判断用哪种。判断树：

| 你的体系 / 目标 | 推荐引擎 | 为什么 | CP2K 入口（手动设，gen_inp 暂不支持） |
|---|---|---|---|
| 一般 AIMD、能量/结构/电子结构（默认） | **DFT (QS/GPW)** | 第一性原理、精度够、周期/非周期通用 | `METHOD QS` + `&DFT`（本 skill 默认） |
| 大体系快速筛选、构象采样、初猜结构 | **xTB（GFN-xTB）** | 半经验紧束缚，比 DFT 快 1–3 量级，覆盖主族+过渡金属，支持 PBC 与色散(D3/D4) | `&DFT &QS METHOD XTB` + `&XTB`（原生 GFN0/GFN1，或 `GFN_TYPE TBLITE`+`&TBLITE METHOD GFN2`）；PBC 自动 Ewald（2026.2+）。精度为半经验级，不可替 DFT 做定量能垒/反应。 |
| 介于 xTB 与 DFT 之间、需周期体系、或要 DFTB3 三阶 | **DFTB** | 比 xTB 略贵但常更准；需 Slater–Koster 参数文件（mio-1-1 / pbc-0-3 / 3ob / trans3d 等） | `METHOD DFTB` + 参数文件（手册 DFTB 页待补，实测以 `cp2k-input` 为准） |
| 酶/溶液/大生物体系里只有局部要量子精度 | **QM/MM** | 只在 QM 区用量子，其余用经典力场(FIST)，成本可控 | `METHOD QMMM` + `&QMMM`（`&QM_KIND MM_INDEX` 列 QM 原子，`E_COUPL COULOMB` 静电嵌入 / `NONE` 机械嵌入，`&LINK LINK_TYPE IMOMM` 处理断键边界）+ `&MM` 力场（Amber/CHARMM prmtop/psf）。用户须给拓扑+力场文件。 |
| 已有预训练势、要超长 ML-MD | **NNP（神经网势）** | 推理级速度、近 DFT 精度，但**迁移性差**（只在其训练分布内可靠） | `METHOD NNP` + `&NNP POTENTIAL_FILE_NAME`(预训练 .nnp/.in)；支持 NequIP/Allegro/DeePMD/ACE 等（格式各异，详见各 ML 子页）。 |
| 大体系、某碎片需高精度、其余环境可近似 | **Embedding（Kim-Gordon / 量子嵌入）** | 比全 DFT 便宜、比 QM/MM 更自洽 | `&FORCE_EVAL &EMBED` 子节（Kim-Gordon 或 QM/QM 量子嵌入）。 |

> 原则：**先用最便宜的能回答你问题的引擎。** 大体系先 xTB/DFTB 摸结构，关键反应/电子结构再上 DFT；酶反应用 QM/MM；已有势函数且体系在训练域内才用 NNP。
> 参考手册章：`methods/semiempiricals`、`methods/qm_mm`、`methods/machine_learning`、`methods/embedding`。本 skill 的 `recommend.py`/`gen_inp.py` 暂只覆盖 DFT 路径；其余引擎在顾问指导下**手动写输入**。
> **吸附能/结合能判读**：CP2K 高斯基组有 BSSE（基组叠加误差），结果会比平面波(VASP)偏大，这是方法固有偏差而非算错——详见 §28.2；精确静态能建议加大基组或做 BSSE 校正。

---

## 17. 增强采样与反应路径（METADYN / BAND-CI-NEB / CONSTRAINT）

### 元动力学（自由能面）—— `RUN_TYPE FREE_ENERGY` + `&FREE_ENERGY &METADYN`
- 关键关键字：`WW`(高斯高度，默认 0.1)、`DO_HILLS T`(开始撒山)、`WELL_TEMPERED T` + `DELTA_T`(或 `WTGAMMA`，退火温度/γ)、`NT_HILLS`(撒山最大步间隔) / `MIN_NT_HILLS` / `MIN_DISP`(按位移触发)、`LAGRANGE T`(扩展拉格朗日，CV 带质量)、`USE_PLUMED T` + `PLUMED_INPUT_FILE`(用 plumed 当驱动器)。
- CV 定义：`&METAVAR` + `COLVAR`(引用 `&SUBSYS &COLVAR` 定义的集合变量)；`&WALL` 加边界(REFLECTIVE/QUADRATIC/QUARTIC/GAUSSIAN)。
- 后处理：`HILLS` → `sum_hills`/`fes.dat` → 自由能面；本 skill `postprocess.py` 的 FES 模块可用。
- 多 walker：`&MULTIPLE_WALKERS`。
- **`DO_HILLS .FALSE.` + `&METADYN/&PRINT/&COLVAR` = 把 METADYN 当"CV 记录器"**（H 层教材增量 T17；
  出处 `references/h_tutorials/notes/05_howto_exercises.md`，T17 P4）：**关掉撒山**，只借 `&METADYN` 的
  `&PRINT/&COLVAR` 机制**每步把 CV 写盘**（原注释 "Section to print out the values of CVs every step"），
  再用 Python 对 CV 直方图取 `F(s) = −kT·ln P(s)` 得自由能面——**全程无偏置势**。
  - 这种用法下 `&METAVAR SCALE`（峰宽）**不起实际作用**（只有撒山时才用）。
  - 落点：`&FREE_ENERGY`（内含 `&METADYN`）与 `&MD` 在 `&MOTION` 下**并列**；CV 定义在 `&FORCE_EVAL &SUBSYS &COLVAR`（见 §24.4）。
  - 产物是 `PROJECT-COLVAR.metadynLog`。**本节与 §24 此前只讲 `DO_HILLS T` 的撒山用法**，这条是并列的第二种用法。

### 反应路径 / 过渡态（NEB）—— `RUN_TYPE BAND`
- 关键关键字：`NUMBER_OF_REPLICA`(镜像数)、`BAND_TYPE`、`K_SPRING`(弹簧常数)、`CI_NEB T`(爬坡 NEB)、`STRING_METHOD`(弦方法)、`ROTATE_FRAMES`/`ALIGN_FRAMES`(RMSD 对齐减噪音)、`USE_COLVARS`(投影到 CV 子空间)。
- 子节：`&OPTIMIZE_BAND`、`&CI_NEB`、`&REPLICA`（每个镜像的初始结构）。输出各镜像能量 → 鞍点/能垒。
- 过渡态也可走 `&GEO_OPT &TRANSITION_STATE &DIMER`（二聚体法，单端找 TS）。

### 约束（CONSTRAINT）
- `FIXED_ATOMS`(冻结指定原子，静态/MD 都常用)、`COLLECTIVE`(基于 `&COLVAR` 的约束)、`G3X3`/`G4X6`(距离/角度几何约束)、`HBONDS`(氢键约束)、`SHAKE_TOLERANCE`(SHAKE/RATTLE 容差)。
- 用 `&LINK`(QM/MM 边界) 也属约束类；冻结溶剂/底物时的标准做法。

#### 硬约束 vs 谐振约束（两种机制，别混用；H 层教材增量 T17）

- **硬约束（G 层官方示例的写法）**：`&COLLECTIVE COLVAR 1 / INTERMOLECULAR TRUE / TARGET [angstrom] 2.0`，
  **没有 `&RESTRAINT` 子块**，配 `&LAGRANGE_MULTIPLIERS ON` 输出约束力 → 用来做热力学积分（TI）。
  出处：G 层 `17_constrained_dynamics_and_paths.md` §1.2。
- **谐振约束（harmonic restraint，H 层 T17 的写法）**：同样的 `&COLLECTIVE` 里**多一行 `&RESTRAINT K 0.005`**，
  即给 CV 加一个 `½K(s−s₀)²` 的**偏置**（`s₀` 由 `TARGET` 给，T17 例 `TARGET 1.8`）——**CV 仍可涨落**，
  所以原文把这条 MD 称作 "unbiased Molecular Dynamics"（用它把构型限制在反应区附近，而不是算 PMF）。
  出处：H 层 `references/h_tutorials/notes/05_howto_exercises.md`，**T17 P4**。
- **怎么选**：要"钉住 CV 逐点取梯度"（PMF / blue moon / TI）→ **硬约束 + `&LAGRANGE_MULTIPLIERS`**；
  只想"别让分子跑掉、但不改变涨落统计"→ **谐振约束**。两者机制不同，**不能互相替代**。
- ⚠️ **待核（不擅自裁定）**：`&RESTRAINT/K` 与 `TARGET` 的**单位**在 G 层示例与 H 层教材里**都没有明写**
  （H 层 `notes/05` §6-6 已登记"需回官方 Input Reference 的 `MOTION/CONSTRAINT/COLLECTIVE/RESTRAINT` 页核"）。
  按 CP2K 默认长度单位推断 `TARGET` 是 Å，**引用时请自己确认**。

> `gen_inp.py` 现已发射 `metadyn`（`--type metadyn`，含 `--well-tempered`/`--delta-t`/`--metadyn-ww`/`--lagrange`/`--multi-walker`/`--plumed` 开关）与 `neb`（`--type neb`，含多副本读取 / `OPTIMIZE_BAND` / `ALIGN_ROTATE_FRAMES` 等，见 SKILL.md「NEB 进阶选项」）模板；`CONSTRAINT` 的 `FIXED_ATOMS` 由 `--fixed-atoms` 发射，`G3X3` 由 `--constraint-g3x3 "i j k"` + `--g3x3-distances "d1 d2 d3"` 发射，`HBONDS` 由 `--constraint-hbonds` + `--hbond-atom-type` + `--hbond-targets` 发射（均经官方解析器校验，见 `constraint_g3x3_water`/`constraint_hbonds_water` 用例）。
> `COLLECTIVE`（`&COLVAR` 约束）仍建议手动加：2026.1 的 `cp2k_input.xml` **未建模 `&DEFINE_COLVAR`**，自动生成的 CV 定义无法被解析器接受，故顾问给出 `&COLLECTIVE COLVAR <i> TARGET <v>` 块 + 需用户自补 `&DEFINE_COLVAR` 的提示，而非自动发射。

### 17.1 自由能面（FES）：三法怎么选、CV 怎么定（批 14）

> 出处：字幕 `S5.txt:2202–4519`。本 §17 上文给的是**关键字怎么写**，§24 给的是**CV 与 PLUMED 的接法**，这里给的是**方法选择与判据**。

**为什么用 AIMD 而不是 NEB 求自由能**（先确认问题本身适合哪条路）：

- NEB 给的是**DFT 电子能量（0 K 势能面上的鞍点）**，"并不是自由能"——忽略了 ZPE、熵、热容等热力学贡献；且**过渡态位置强依赖插点**，插点不好就找不到（`S5.txt:2213–2237`）。
- 涉及**吸附/脱附、显式溶剂、环境分子取向平均化**的过程，NEB 很难做对，应走 AIMD 自由能面（`S5.txt:2244–2265`、`2542–2565`）。
- 前提是你**接受 AIMD 的时间尺度限制**：常规 10–30 ps 轨迹；按 Arrhenius（指前因子 ~10¹³）估算，0.75 eV 的能垒在 300 K 下平均 ~1 s 才发生一次，**必须靠增强采样**（`S5.txt:2266–2289`）。

**三法的选择与取舍**：

| 方法 | 做法 | 成本 / 取舍 | 什么时候选 |
|---|---|---|---|
| **PMF（受限 AIMD / blue moon）** | 把 CV **钉在一系列定值**上，每条轨迹取一个"自由能对 CV 的梯度 λ"，再**积分**得 FES | **每个 CV 点都要一条完整轨迹**（例：十几个点 = 十几条轨迹），最贵；且**过渡态位置强依赖插点密度**，少插一个点能量可差零点几 eV（`S5.txt:2384–2431`、`2999–3013`） | 需要**严格受限**的 CV、或要逐点核对梯度时；也用于验证别的法子 |
| **Slow-growth** | CV 不再固定，**每步按固定增量缓慢推进**（讲义/讲师给的是 **VASP 侧**的 `INCREM`；**CP2K 侧的控件是 `TARGET_GROWTH`，见 §17.2**），实时捕捉 λ 后积分 | **只需一条轨迹**即可拿到整条曲线（相对 PMF 计算量小很多）；代价是 λ 曲线震荡大、需要取平均（`S5.txt:3014–3086`） | **默认首选**：只要一条轨迹就能出 FES |
| **Metadynamics** | 在 CV 空间**不断填高斯**把盆地填平，再把累加的高斯取负还原真实 FES | 直观、图漂亮；**峰高/峰宽要试**，填太粗结果"坑坑洼洼"，填太细机时爆炸（讲师本例**填平花了约 80 ps**）（`S5.txt:3239–3362`、`3880–3889`） | 需要**多盆地/多路径**探索、或想让势能面自动"探索出"没预期的中间态 |

- **三法共同的物理前提**：不做任何限制，统计意义上的自由能只是一个**定值**，没有分析价值；只有把某个自由度约束住、看自由能**随它变化**才有意义（`S5.txt:2330–2345`）。
- **正则系综给的是亥姆霍兹自由能 A**；要吉布斯自由能 G 得用 NPT（差一个 PV 项，一般可忽略，所以"一般来说我们就是用 NVT 去模拟就可以了"）（`S5.txt:2302–2321`）。**写文章时要说清是 A 还是 G。**

**CV 选取原则**（讲师口径："CV 的选取对于自由能的模拟是非常重要的一个变量"）：

1. **先能用最简单的就用最简单的**：`DISTANCE`（原子–原子 / 原子–键中心 / 原子–由三原子定义的表面）→ `ANGLE` / `TORSION` → 多个自由度的**线性组合**（如两个键长之差）→ `COORDINATION`（配位数，定义较麻烦）（`S5.txt:2469–2510`）。
2. **可加性 CV 要用 `&COLVAR` 的 function 组合**：QM/MM 例里第一个 CV 就是"C–H 键长 1 + C–H 键长 2"之和（`S5.txt:4174–4194`）。
3. **单 CV 控制多键反应会"跑偏"**：用一个 CV 跑 metadynamics，势能面抬到一定程度后体系会跳到**你不想要的解离态**（讲师例：本来解离成 CO₂ + H₂O，中途变成 OH + COOH），两个极小值一重叠，"模拟出来这个势能面就没法分析了"——**要换 CV 或补第二个 CV**（`S5.txt:3892–3922`）。
4. **先粗后精**：拿不准就**先用粗糙参数（大高斯峰）快速跑一段**验证 CV 是否反映你关心的过程，确认后再用小峰精修（`S5.txt:3916–3930`）。
5. **维度只做 1D / 2D**："三维的势能面就不要建议去尝试……基本都是模拟的一维或二维势能面"（`S5.txt:3997–4008`）。
6. **峰宽要贴合盆地**：窄盆地用窄峰（宽峰"和盆底不贴合"），宽盆地用宽峰；**可以中途重启换峰型**，一个体系不同区域用不同宽度（`S5.txt:3931–3969`）。

> **与 VASP 的关键分野**：**CP2K 支持 `&WALL` 加墙，这是它做 metadynamics 相对 VASP 的最大优势**——讲师原话"这个只能是在 CP2K 里面去实现的……在 VASP 里面是不能去实现这个功能的。这也就是 VASP 在做 metadynamics 模拟最大的一个缺点，我觉得是最大的一个缺点：没有办法加这个墙"（`S5.txt:4091–4158`）。**从 VASP 迁过来的用户若不做 metadynamics，不会感到差别；一旦要做 FES，加墙能力就是选程序的理由。**
> 输入落点与墙的参数（`WALL_MINUS`/`WALL_PLUS`/`K`）见 **§24.4**。

### 17.2 slow growth 的 CP2K 控件，与"`ICONST`/`ICRIN` 不是 CP2K 关键字"（批 15，官方 XML 定案）

> 出处：`videonotes/cp2k-5-…-精读笔记 L1384–L1409 [119:15–120:33]`；E 层讲义 `L5.txt:344–379`（VASP 侧逐字）、
> 字幕 `S5.txt:3101–3111`；官方路径与默认值用 `_kw_probe.py` 复核。

- **⚠️ `ICONST` / `ICRIN` 都不是 CP2K 的段或关键字**（`python _kw_probe.py --find ICONST` → **0 处**；
  `--find ICRIN` → **0 处**，本轮已复现）：
  - **`ICONST` 是 VASP 的"约束定义文件"**（文件里写 `R 1 3 0` / `A 3 1 2 0` / `T 5 3 1 2 0` / `S 1. 1. -1 0` 之类的行，
    `STATUS = 0` 代表固定；见讲义 `L5.txt:171–183`、`L5.txt:210–225` 逐字）。
  - ✅ **VASP 侧那个标签的真名是 `INCREM`（2026-10，VASP 官方 wiki 定案）；`ICRIN` 不存在。**
    讲义 `L5.txt:362` 逐字 "INCAR 当中只多了一个参数…… **`INCREM = 0.0005`**"（`:374/376` 同）是**对**的；
    字幕/第二轮笔记的 `ICRIN`（音译形 `i cream` / `ACCREAM`）是**转写产物**。
    **依据**：VASP Wiki 的 *Slow-growth approach* 页在 "How to" 与 "Related tags" 里明确列的是
    **`INCREM`**（"the transformation velocity-related **`INCREM`**-tag for each geometric parameter
    with STATUS=0"；Related tags: `ICONST`, **`INCREM`**, `SHAKEMAXITER`, `SHAKETOL`, `SHAKETOLSOFT`,
    `LBLUEOUT`, `REPORT`）—— <https://vasp.at/wiki/index.php/Slow-growth_approach>。
    ⇒ **旧记录判"两种拼写指同一个标签、不硬编哪一个"可以撤销**：`ICRIN` 在任何 VASP 文档里都不存在。
    可以确定的是：**`INCREM`/`ICRIN` 两者在 CP2K 官方 XML 里各 0 命中**（已复现）。
  - ⇒ **写 CP2K 输入时这两个名字一个都不要写**；`grep cc REPORT` / `b_m` 这些也是 VASP 的输出（`L5.txt:363–367`）。
  > 📌 **更正记录**：`videonotes/cp2k-5-…` 的 §14.3 小标题写作 "`ICONST` 不变，只加一个 `ICRIN`"，
  > **丢了"VASP 的"限定词**（同一份笔记前面 §13.8、后面 §15.4 都带"VASP 的"，唯独这一节漏了），
  > 单独读会以为是 CP2K 写法；笔记正文 `L1409` 其实写明了"在这个 VASP 做计算的过程当中"。
  > 另有 A 层一处需要收紧：本节 §17.1 的 Slow-growth 行原写"每步按 `INCREM` 缓慢推进"，
  > 读起来像 CP2K 关键字 —— **已改为"VASP 侧的 `INCREM`；CP2K 侧是 `TARGET_GROWTH`"**。
  > 处置：只在消费层标注，**不动 E 层原文**（层 README 的维护约定）。
- ★ **CP2K 侧的对应物三件套**（这张表是"从 VASP 迁过来"的落地口径）：

  | 目的 | VASP（**不是 CP2K**） | **CP2K 正确写法** |
  |---|---|---|
  | 定义 CV | `ICONST` 文件的 `R/A/T/M/X,Y,Z` 行 | `&FORCE_EVAL/&SUBSYS/&COLVAR/&{DISTANCE,ANGLE,TORSION,COORDINATION,…}`（几维写几个） |
  | 把 CV **钉在定值**上（PMF / blue moon） | `ICONST` 里 `STATUS 0` | `&MOTION/&CONSTRAINT/&COLLECTIVE`（`COLVAR <序号>` + `TARGET <值>`） |
  | 让 CV **每步微增**（slow growth） | INCAR 的 **`INCREM`**（+ `LBLUEOUT`） | **`&CONSTRAINT/&COLLECTIVE TARGET_GROWTH <增量>`** |
  | 输出自由能梯度 λ | `REPORT` 的 `b_m>` 行 | `&CONSTRAINT/&LAGRANGE_MULTIPLIERS`（拉格朗日乘子 = 约束力 = λ） |

- ★ **`TARGET_GROWTH` 就是 CP2K 的 slow-growth 控件**（`MOTION/CONSTRAINT/COLLECTIVE`，默认 **`0.0`**；
  官方描述"Specifies the growth speed of the target value of the constrained collective variable" ⇒ **非零即启用**）。
  - **官方机制（G 层已收录且公式正确）**：`TARGET(t) = TARGET(0) + TARGET_GROWTH × TIMESTEP × step`，
    单位写法 **`[angstrom*fs^-1]`**（每飞秒多少埃）；出处
    `references/official/17_constrained_dynamics_and_paths.md:242,247,273,287`（官方例 `TARGET_GROWTH [angstrom*fs^-1] 0.0008`）。
  - ⚠️ **换算关系（本库此前零记录，属"照搬会差一个 TIMESTEP"的天坑）**：
    **`TARGET_GROWTH [Å/fs] = INCREM [Å/步] ÷ TIMESTEP [fs]`**。
    例：`INCREM 0.0005 Å/步` 配 `TIMESTEP 0.5 fs` ⇒ **`TARGET_GROWTH 0.001 Å/fs`**（两者每 MD 步推进量相同）。
    直接把 `0.0005` 填进 `TARGET_GROWTH` 会**慢一倍**（少推），把 `TIMESTEP` 当无关参数改大改小也会**顺带改掉扫描速率**。
  - **方向可正可负**（反向扫就把增量设成负值）；**增量越小扫得越慢、结果越准**，太大则"跑着跑着就崩溃掉，
    因为这个结构控制不住"（VASP 侧口径，`videonotes/cp2k-5-…-精读笔记 L1434–L1436 [123:52–125:20]`；
    CP2K 侧同理由 `TARGET_GROWTH` 的语义直接给出）。**扫描区间要覆盖盆地两侧**（起始结构往极小值外侧拉一点）。
  - ⚠️ **同名不同物警告**：**`&METADYN SLOW_GROWTH`**（`python _kw_probe.py --find SLOW_GROWTH` →
  `MOTION/FREE_ENERGY/METADYN`，默认 **`F`**，官方描述 "**Let the last hill grow slowly over NT_HILLS**"）
  是**元动力学里让最后一个高斯峰慢慢长起来**，**不是**上面这套"CV 逐帧推进的 slow growth 方法"。
  **两个名字像、机制完全不同，合并/引用时必须分别立条。**
- **PMF 只能定义一个 CV（一维）**：讲师原话"我们做 PMF……**那只能定义一个 CV 值**"；多键反应要把
  **断裂键取正、生成键取负**组合成**一个**线性组合 CV（例 `R13 + R46 − R36`，即 `S 1. 1. -1 0`）。
  做多维必须换方法（`videonotes/cp2k-5-…-精读笔记 L1247–L1282 [103:10–106:24]`；E 层 `S5.txt:2656–2660`、`L5.txt:213–225`）。
  ⇒ 多维走 §24 的多 CV（`&SUBSYS/&COLVAR` 写 N 个）+ `&COMBINE_COLVAR`，不要指望 PMF 一条轨迹出二维面。
- **metadynamics 的重启关键字**（本库此前只写"可以重启"，没写靠什么重启）：`&METADYN` 下
  **`OLD_HILL_NUMBER`（默认 `0`）/ `OLD_HILL_STEP`（`0`）/ `NHILLS_START_VAL`（`0`）/ `STEP_START_VAL`（`0`）**；
  hills 文件名由 `&METADYN/&PRINT/&HILLS FILENAME` 决定（**默认 `HILLS`**）。
  VASP 侧的等价动作是把 `HILLSPOT` 复制成 `PENALTY_POTENTIAL` 再续算（**那是 VASP 的做法，CP2K 无此文件**）。
  （`videonotes/cp2k-5-…-精读笔记 L1741–L1743 [152:23–152:59]`；
  `_kw_probe.py --section MOTION/FREE_ENERGY/METADYN` 与 `…/PRINT/HILLS` 复核）

---

## 18. 晶胞优化（CELL_OPT，PBC 必备）

`RUN_TYPE CELL_OPT` 同时弛豫原子+胞（常与 GEO_OPT 串联：先 GEO_OPT 定构型，再 CELL_OPT 定胞，或一步到位）。

- 关键关键字：`EXTERNAL_PRESSURE`(外压，1 值或压强张量 9 分量；**官方要求显式设**，示例 1.01325E+00 bar)、`PRESSURE_TOLERANCE`(达压容差，官方示例 100.0)、`KEEP_ANGLES`(只变胞长不变角度，三斜有用)、`KEEP_SYMMETRY`(保初始胞对称，对称须在 `&CELL` 指定)、`CONSTRAINT`(固定压强张量某些分量)、`OPTIMIZER`/`MAX_ITER`/`MAX_FORCE`/`MAX_DR`/`RMS_FORCE`/`RMS_DR`(同 GEO_OPT 判据)、`KEEP_SPACE_GROUP`(保空间群)。
  > ⚠️ **`TYPE` 已于 CP2K 2026.2 移除**，晶胞优化现在**始终用 `DIRECT_CELL_OPT`**（已按官方 G 层修正，见 `references/official/11_version_changelog.md` §2.2、`references/official/05_optimization.md`）。
- 等压用 `EXTERNAL_PRESSURE 0` 即常压；想算某压强下的平衡体积就设对应值。
- 与 §13 的 NPT 关系：CELL_OPT 是**零温/有限温的结构优化**（找平衡胞），NPT 是**动力学系综**（沿轨迹采样）；目标不同别混用。

### 18.1 CELL_OPT 的八条硬补充（讲师实操 + 官方默认值，批 14/15）

> 出处：字幕 `S3.txt:3860–3993`。

1. **`STRESS_TENSOR ANALYTICAL` 与 `RUN_TYPE CELL_OPT` 必须成对**：做晶胞优化就要在 `&FORCE_EVAL &DFT` 里把这个关键词打开——"做晶胞优化的时候，要把这个关键词给打开"（`S3.txt:3866–3876`）。漏了应力张量，晶胞优化在物理上就不成立。
   > ⚠️ **为什么漏了会静默失败**：`FORCE_EVAL STRESS_TENSOR` 的**官方默认是 `NONE`**（`_kw_probe.py --find STRESS_TENSOR`）
   > ⇒ 不写 = **根本没有应力**，优化器拿不到晶胞梯度。判据一句话（讲师口径）：**"晶胞体积会发生变化的计算用 `ANALYTICAL`，
   > 不变的用 `NONE`"**（NPT / CELL_OPT → `ANALYTICAL`；NVT / NVE / GEO_OPT → `NONE`）；
   > 而 G 层 `official/05_optimization.md:91` 的口径弱一些（"再额外指定 `STRESS_TENSOR` 也是合理的"）——
   > **两条不冲突**：官方说"合理"，讲师说"必须"，本 skill 按**必须**执行（否则 CELL_OPT 跑不出来）。
   > 出处：`videonotes/cp2k-3-…-精读笔记 L1586–L1588 [149:09–149:30]`、`L283–L299 [22:25–24:02]`。
2. **优化器用 `CG`，不用 BFGS**：晶胞优化"为了稳定，为了让它的这个优化更为稳定一些，我们就用 CG 这个算法就可以"（`S3.txt:3920–3926`）。（与 §12 的 OT 内部 `MINIMIZER` 是两回事。）
3. **`CONSTRAINT Z` 是二维材料的必开项**：只优化 X/Y、固定 Z，"如果大家想做石墨烯、硫化钼、MoS₂ 这些材料，想让它在二维方向上持续、而真空层保留，就把 `CONSTRAINT Z` 给它打开"；**不打开的话，"可能优化一会儿它这个真空层就消失掉了，真空层就变得越来越短"**（`S3.txt:3927–3949`）。这是 §5.1 盒子原则在 slab/2D 上的具体化。
   > 📌 **关键字名更正**：这个开关的官方名字是 **`&MOTION/&CELL_OPT CONSTRAINT`**，取值是**枚举**（`X`/`Y`/`Z`/`XY`/`NONE`…，
   > 默认 `NONE`）——**CP2K 里没有 `FIXED_Z` 这个关键字**（`_kw_probe.py --find FIXED_Z` → 0 命中；
   > `FIXED_ATOMS` 是 `&MOTION/&CONSTRAINT` 的**子段**，管的是原子不是晶胞方向）。
   > 讲师口述时说的是"固定这个……（`FIXED_Z`）"（`videonotes/cp2k-3-…-精读笔记 L1609–L1617 [151:20–152:07]`），
   > **照抄会写出不存在的键**（而 CP2K 对未知关键字不一定报错）。本库 A/B/D 层此前写的都是正确的 `CONSTRAINT Z`。
4. **`KEEP_ANGLES` / `KEEP_SYMMETRY` 看情况**：正常都打开（把角度和对称性固定死）；但**高对称相本身不稳定时**，硬锁对称性会让它"不会自发地跑到低对称性去"，这时要关掉（`S3.txt:3890–3919`）。
5. **OT 做晶胞优化时不能加 k 点 → 只能扩胞**：原胞一般很小，若走 OT，**"我们不能加 K 点，这时候只能进行扩胞，把这个包扩得大一点，这样才能优化得比较准"**；**金属体系**则可改用对角化 + 多 k 点，"K 点设置得比较多的时候，我们就不需要再去把它扩胞了"（`S3.txt:3976–3992`）。这是 §5.2 那条缺陷在 CELL_OPT 场景的直接推论——**两条路选一条，不能既要小胞又要 k 点又要 OT**。
6. **`&CELL_OPT` / `&GEO_OPT` 的官方默认值（讲师记不清的那几个，本轮 XML 定案）**：

   | 关键字 | 官方默认 | 单位 | 讲师取/建议 |
   |---|---|---|---|
   | `MAX_FORCE` | **4.5E-4** | bohr⁻¹·hartree | 本 skill 模板取 6.0E-4（比默认**放宽**，不是收紧） |
   | `RMS_FORCE` | **3.0E-4** | bohr⁻¹·hartree | 模板同默认 |
   | `MAX_DR` | **3.0E-3** | bohr | 模板同默认 |
   | `RMS_DR` | **1.5E-3** | bohr | 模板同默认 |
   | `MAX_ITER` | **200** | — | 难收敛提到 300 |
   | `OPTIMIZER` | **`BFGS`** | — | 晶胞优化改用 **`CG`**（稳定性，见第 2 条） |
   | `EXTERNAL_PRESSURE` | **100 bar**（单位张量） | bar | 课程模板写 `1`（= 1 bar） |

   - 讲师猜的"0.006 还是 0.0045"里的 **0.0045 就是 `MAX_FORCE`**；换算 **4.5E-4 Ha/bohr ≈ 0.0194 eV/Å**（与他"VASP 里 0.02 左右"的估计方向一致）。
   - ⚠️ **单位混用是本节最容易错的一点**：`MAX_FORCE`/`RMS_FORCE` 是 **bohr⁻¹·hartree**、`MAX_DR`/`RMS_DR` 是 **bohr**，
     而 `&COORD` 与 `&CELL` 的 A/B/C 却是 **Å**（`_kw_probe.py --section MOTION/GEO_OPT`、`FORCE_EVAL/SUBSYS/COORD`）。
     **`&SCF EPS_SCF` 同样是 Hartree（原子单位），与 VASP 的 eV 必须换算**（≈27.211 eV = 1 Hartree）
     （`videonotes/cp2k-3-…-精读笔记 L658–L666 [49:38–50:53]`、`L1413–L1415 [127:10–127:43]`）。
   - **`EXTERNAL_PRESSURE` 的官方默认是 100 bar ≈ 1 atm**，所以"三个方向各一个大气压"**本来就是默认行为、不必手写**；
     单位是 **bar 不是 atm**（官方 XML `DEFAULT_UNIT bar`）。但 G 层 `official/05_optimization.md:91` 仍建议**显式设**
     （可读性 + 防默认值随版本变），**本 skill 采"显式写"**；注意模板里写 `1.0` 是 **1 bar**，与官方示例 `1.01325E+00 bar` 不同
     （`videonotes/cp2k-3-…-精读笔记 L1590–L1593 [149:30–150:00]`）。
7. **`KEEP_SYMMETRY` 默认 `F`，而且"必须配 `&CELL SYMMETRY`"才算数**：官方 Note 明写
   "**`KEEP_SYMMETRY` 应始终与 `FORCE_EVAL/SUBSYS/CELL/SYMMETRY` 指定的晶胞对称性一起使用**"，
   而 **`&CELL SYMMETRY` 的官方默认是 `NONE`** ⇒ **只写 `KEEP_SYMMETRY T` 而不写 `&CELL SYMMETRY` 是空转**
   （`KEEP_ANGLES` 默认同样是 `F`）。现成反例：`references/templates/cell_opt.inp` 开了 `KEEP_ANGLES T`/`KEEP_SYMMETRY T`
   却没有 `&CELL SYMMETRY` —— 模板侧已由工具链 agent 登记（G-10），**A 层这里给出判据：写 `KEEP_SYMMETRY T` 就必须同时写 `&CELL SYMMETRY <点群>`**。
   （`_kw_probe.py --find KEEP_SYMMETRY`/`KEEP_ANGLES`；`official/05_optimization.md:355,480`；
   `videonotes/cp2k-3-…-精读笔记 L1595–L1603 [150:30–151:05]`）
8. **不写 `&CELL_OPT` 段也能跑，但会退回 `OPTIMIZER BFGS`（而不是讲师要的 `CG`）**：
   讲师在算例二、算例三两次实测"不写 `&MOTION` section 其实也能跑，它都是用的默认参数"
   （`videonotes/cp2k-3-…-精读笔记 L1448–L1454 [130:16–130:43]`、`L1522–L1524 [141:30–141:43]`）。
   ⇒ **"能跑"≠"按你的意图在跑"**：`CELL_OPT` 不写段 ⇒ `OPTIMIZER` 默认 `BFGS`、`MAX_ITER` 默认 200、四个判据走默认；
   这正是讲师反复强调"晶胞优化为了稳定要用 `CG`"的原因。**这一条也是 `validate_inp.py` 值得加规则的地方**
   （"缺段静默默认"是本讲两条算例都实测到的假成功风险）。

> 晶胞优化结果的查看：`grep CELL` 之后能看到每步胞的 3×3 矩阵，最后三个数值就是 A/B/C 三个晶格矢量长度；PBE 会**高估**晶胞边长（会从初始值慢慢变大到平衡值）（`S3.txt:3994–4016`）。

> **PBE 高估晶胞边长：实测数字与决策含义**（`videonotes/cp2k-3-…-精读笔记 L1581–L1584 [148:34–149:09]`、`L1692–L1695 [158:27–159:09]`）：
> 讲师实测 **Cu FCC：实验 3.61 Å → PBE 优化后 3.682 Å**（输入给 3.6）。⇒ 决策口径：
> "**严格来说我们需要先做一下晶胞优化，然后再去切表面；如果粗糙一点的话，也可以不优化、用实验值去做。最好的话是要给它优化一下。**"
> —— 因为**切表面用的晶格常数直接决定吸附能/应力**，用未优化的实验值会让 slab 处于虚假应变状态。
> ⚠️ 这也是 `EXTERNAL_PRESSURE` 三档（0 / 1 atm / 目标压强）里"零压平衡体积"这一档的最常见用途。

---

## 19. Post-HF 关联（MP2 / RI-MP2 / RPA / SOS-MP2，手册章）

当 DFT 精度不够（弱作用、反应能、能隙、双杂化基准）时，在 DFT 之上加波函数关联。入口 `&DFT &XC &WF_CORRELATION`，参考一般为 **HF** 或**杂化泛函**。三种 MP2 实现：

- **Canonical MP2**（`&MP2 METHOD DIRECT_CANONICAL`）：最贵，可作核心校正；**无解析力/应力**。
- **GPW-MP2**（`&MP2 METHOD MP2_GPW`）：仅 GPW 参考；需 `&INTEGRALS &WFC_GPW CUTOFF/REL_CUTOFF`；比 canonical 便宜，仍无解析力。
- **RI-MP2**（`&RI_MP2`）：最便宜、**有解析力**（GPW 参考）。需 RI 辅助基组（`BASIS_SET RI_AUX` 或 `AUTO_BASIS RI_AUX LARGE`）。关键：`BLOCK_SIZE`(块大小，内存↔通信权衡)、`NUMBER_INTEGRATION_GROUPS`、`MEMORY`(MB)、`NUMBER_PROC`。

通用关键字：`&INTEGRALS &WFC_GPW`(GPW 积分网格 CUTOFF/REL_CUTOFF)、`SCALE_S`/`SCALE_T`(单/三重态重标，双杂化泛函用)、`EPS_CANONICAL`(简并占据对——对称多原子体系要调大，否则数值不稳)。

**RPA / LT-RI-SOS-MP2**（`&RI_RPA` / `&RI_SOS_MP2`）：对范德华/反应能常比 MP2 更准，但更贵；常配 HF 交换（`&RI_RPA &HF`，同普通 `&HF` 段）。RI-RPA 需 `ri-rpa-admm`/`ri-rpa-aux-basis` 辅助基；`QUADRATURE_POINTS`(Minimax 6–8 / Clenshaw-Curtis 30–40)、`NUM_INTEG_GROUPS`、`RSE` / `EXCHANGE_CORRECTION [NONE|AXK|SOSEX]`(beyond-RPA 修正)。

HF 参考可用 **ADMM 加速**（`&AUXILIARY_DENSITY_MATRIX_METHOD METHOD BASIS_PROJECTION`，`EXCH_CORRECTION_FUNC` 如 PBEX；非常弥散基组推荐）；HF 段 `&HF FRACTION 1.0` + `&SCREENING` + `&INTERACTION_POTENTIAL`(截断库仑 `CUTOFF_RADIUS`/`T_C_G_DATA`)。

> **取舍**：MP2/RPA 比 DFT 贵数~个量级（~N⁵ / ~N⁴），大体系先 RI 或低标度实现；参考 wfn 先收敛（建议 `WFN_RESTART_FILE_NAME` 接预收敛 HF）。**双杂化泛函**（如 B2PLYP，在 `&XC_FUNCTIONAL` 里设）是"DFT 内带 MP2 关联"的折中，常更实惠。Post-HF 输入 `gen_inp.py` 暂不支持，需顾问指导下手动写。
> 参考手册：`methods/post_hartree_fock`(preliminaries / mp2 / rpa / low-scaling)。

---

## 20. 过渡态 / 最小能量路径的 CP2K 输入结构（NEB 补充，手册核对）

`RUN_TYPE BAND`。镜像如何喂入：在 `&SUBSYS &COORD` 里**按顺序**写 初态 → 末态 → 中间镜像，镜像之间用**空行**分隔；CP2K 按 `NUMBER_OF_REPLICA` 切分（也可用 `&REPLICA/COORD` 显式给，旧式）。

关键关键字：
- `NUMBER_OF_REPLICA`(含两端总镜像数，常用 8–16)、`BAND_TYPE [CI-NEB|IT-NEB|SM]`（**CI-NEB** 爬坡找鞍点最常用）、`K_SPRING`(弹簧常数 ~0.05–0.2 hartree/bohr²；太大拖慢、太小路径塌陷)、`CI_NEB T`、`ALIGN_FRAMES`/`ROTATE_FRAMES`(RMSD 对齐减噪音，分子/团簇用)、`USE_COLVARS`(投影到 CV 子空间)。
- `&OPTIMIZE_BAND` + `&DIIS`(或 `&MD` 做 BAND 的 MD 松弛) 控制镜像优化；`&CONVERGENCE_CONTROL` 设 `MAX_FORCE` 等收敛判据；`&CI_NEB` 子节含爬坡参数(`CI_STEPS` 等)。
- 输出：`*-replica-*.ener` 各镜像能量 → 最大者≈鞍点；`*-band-*.XYZ` 路径轨迹。

过渡态另一路：`&GEO_OPT &TRANSITION_STATE &DIMER`（二聚体法，只需一个初态，自动沿最低曲率模找 TS）。

> 初/末态必须**先各自 GEO_OPT 收敛**；中间镜像可线性插值或 `&REPLICA` 给定。
> **`gen_inp.py` 现支持 NEB**：`--type neb` + `--xyz-replicas` / `--band-type` / `--optimize-band` /
> `--align-frames` / `--rotate-frames` / `--nproc-rep` / `--k-spring` / `--neb-max-force` / `--neb-rms-force` 等
> （完整清单见 `references/gen_inp_options.md` §8；**不支持的是 Dimer 等单端过渡态配方**，那部分要按上结构手动拼）。
> 与 §17 的 METADYN 区别：NEB 给确定初末态找**路径/能垒**，METADYN 不预设路径只撒 CV 探**自由能面**。

### 20.1 NEB 的实操决策（讲师经验，批 14）

> 出处：字幕 `S4.txt:336–366`、`470–623`、`680–824`、`986–1002`。

- **该不该做 NEB——先过这一关**。讲师明确列出**没有过渡态的三类化学过程**：**离子键的断裂/生成**、**共价键断裂成自由基**、**表面吸附/脱附**；并且"我们表面吸附过程是不算它的过渡态的，**当然解离吸附是除外**"（`S4.txt:74–132`）。对这几类硬做 NEB 是白烧机时。
  > **补的论据链（为什么"没有"而不是"不算"）**：物理吸附能弱、化学吸附能强，两者在势能曲线上**可能有、也可能没有**
  > 连接它们的鞍点；**解离吸附的 TS 肯定存在**；而非解离的化学吸附，其 TS"一般非常小，而且很难算"
  > （`videonotes/cp2k-4-…-精读笔记 L94–L116 [04:46–06:11]`）。⇒ 判据落在"**过程是否发生键的断裂/生成**"上。
  > 与 §17.1 联动：这些过程（尤其涉及显式溶剂/环境重构的）本来就应该走自由能面而不是 NEB。
- **计算资源怎么申请（CP2K 独有优势）**：**CP2K 的 NEB 可以逐点分批算，VASP 必须所有点同时算**——"在 VASP 里面去算 NEB 的时候，是所有点一定要同时去算的，但是在 CP2K 里可以不用"（`S4.txt:480–508`）。讲师例：56 核机器、每个点 28 核 ⇒ **每次并行 2 个点，分三批**算完 6 个点，**不必凑 6×28=168 核**。这一条直接决定排队策略。
- **必须有"没用但必须有"的 `coord.inc`**：NEB 除 input 外还要准备一个 `coord.inc`——"这个文件是没有什么用处的，但是要有……这就是 CP2K 写这个程序写得不太好的地方"（`S4.txt:684–701`）。缺它会直接卡住提交。
- **收敛信息不在主 out 里**：**每个镜像各写一个 `cp2k-<n>.out`**，结构收敛信息（四个判据）在这些文件里；**主 `cp2k.out` 只给能量**（`S4.txt:706–789`）。只看主 out 会误判成"没在收敛"。
- **能量怎么读**：主 out 里每次输出 6 个点的能量 + 一个"总和"；**总和没用**，画能垒图只用**各点自己的那 6 个能量**；文献里多数只取初态 / 过渡态 / 末态三个值（`S4.txt:720–745`）。
- **插点数**：CI-NEB 相对传统 NEB 的价值不只是"更准"，还**能显著减少插点数**——传统 NEB "可能要插十个点或者十个点以上"，CI-NEB 不用；经验值 **4–5 个**（很近 3 个，很远 6–7 个）（`S4.txt:336–366`）。
- **`K_SPRING`**：弹簧常数越大收敛越快、但精度略差。**粗算取 0.08 / 0.1**（"这是一个比较大的值"），收敛后再用精算值重启；资源紧张时 **0.05–0.08** 也可以（`S4.txt:542–562`）。
- **IT-NEB → CI-NEB 的两段式**：刚插完点时结构不合理，直接开 CI 可能不稳；**先用 IT-NEB 跑约 5 步**，再切 CI-NEB（`S4.txt:564–582`）。
- **表面/材料体系必须关 `ALIGN_FRAMES` / `ROTATE_FRAMES`**：这两个只在**分子（非周期）体系**里打开；材料/表面体系打开会让整个 slab 平移，初末态能量都会变（`S4.txt:515–541`）。
  > ⚠️ **必须"显式写 F"的理由（本轮 XML 定案，把这条的严重性提高了一档）**：`MOTION/BAND` 的
  > **`ALIGN_FRAMES` 与 `ROTATE_FRAMES` 官方默认都是 `T`** —— 表面体系**不写就是生效**，CP2K 会在每一步做 RMSD 旋转对齐，
  > 正好造成讲师警告的"slab 被整体平移/旋转、初末态能量都会变"。
  > **硬规则：表面体系写 `ALIGN_FRAMES F` + `ROTATE_FRAMES F`**（`_kw_probe.py MOTION/BAND/ALIGN_FRAMES` / `ROTATE_FRAMES`；
  > `videonotes/cp2k-4-…-精读笔记 L305–L314 [20:07–21:01]`）。
  > 📌 **更正记录**：曾在 D 层 `sections.md` 的"帧对齐/旋转"行把 `ROTATE_FRAMES` 记作"默认 F" —— **那是错的**；
  > **该文件现已自行更正为"默认 T"并附更正记录 1**（`references/sections.md:89`、`:107–132`），A/D 两层口径已一致。
  > ⚠️ 另注：`gen_inp_options.md` 里 `--rotate-frames T|F（默认 F）` 说的是 **CLI 开关的默认发射值**（对表面体系是好默认），
  > **与 CP2K 关键字自身的默认 `T` 不是一回事** —— 引用时把这两个"默认"分开写清，否则会被读成"CP2K 默认 F"。
- **收敛标准要同时放宽四个判据**：NEB 的收敛"比结构优化要难得多"，**四个判据全放宽、幅度不到一个数量级** ——
  `MAX_FORCE` 由 **0.0006 → 0.001**（`S4.txt:790–816`）。讲师特别提醒：**这些数一般要写进文献的 Computational Methods**，
  文献里常见写法就是 "≈0.001 原子单位"（`S4.txt:817–824`）。
  > 📌 **更正记录（默认值搞错了）**：上面那个 **0.0006 不是 CP2K 的 `&BAND` 默认值，而是本课程 `&GEO_OPT` 模板值**
  > （`references/templates/geo_opt.inp` 的 `MAX_FORCE 6.0E-4`）。官方 `MOTION/BAND/CONVERGENCE_CONTROL` 的
  > `MAX_FORCE` 默认是 **`4.5E-4`**（`_kw_probe.py --section MOTION/BAND/CONVERGENCE_CONTROL` 复核）。
  > ⇒ **结论不变**（"放宽到 0.001"相对 4.5E-4 仍约 2.2 倍），但**表述要改成"课程模板值 6.0E-4 / 官方默认 4.5E-4"**。
  > 出处：`videonotes/cp2k-4-…-精读笔记 L408–L420 [29:48–31:04]`（讲师口述"本来这个最大的受力 max force 是 0.0006"）。
  > ⚠️ **"四个判据一起放宽"容易被读成"只改 `MAX_FORCE`"** —— 现有 A/F 层只记了 `MAX_FORCE` 一个，
  > 讲师原话是"我把这四个标准**全都**给它改大了一些"（`videonotes/cp2k-4-…-精读笔记 L419 [29:48–31:04]`）。**位移类判据要同步放宽**（见下表）。
- **`&BAND` 的四个官方默认值（本库此前零记录；位移类比 `&GEO_OPT` 紧 15 倍）**：

  | 判据 | `&BAND` 默认 | `&GEO_OPT` 默认 | 比值 |
  |---|---|---|---|
  | `MAX_FORCE` | **4.5E-4** | 4.5E-4 | 1× |
  | `RMS_FORCE` | **3.0E-4** | 3.0E-4 | 1× |
  | `MAX_DR` | **2.0E-4** | 3.0E-3 | **紧 15×** |
  | `RMS_DR` | **1.0E-4** | 1.5E-3 | **紧 15×** |

  ⇒ **"NEB 收敛比结构优化难得多"有官方默认值背书**：位移类判据本来就严一个数量级；
  这也解释了讲师"四个标准全都改大一些"的做法（`videonotes/cp2k-4-…-精读笔记 L408–L420 [29:48–31:04]`）。
- **`K_SPRING` 官方默认 `0.02`，且官方 XML 不给单位**（= CP2K 内部原子单位，即 hartree/bohr²）：
  本层 §20 上文写的"~0.05–0.2 hartree/bohr²"与官方单位约定自洽 ✅；
  ⚠️ 而工具层 help 文本把它标成 **eV/Å²**，**没有官方依据**（归工具链 agent 修）。
  （`_kw_probe.py MOTION/BAND/K_SPRING` → `DEFAULT_VALUE 2.0E-2`、`UNIT` 为空；
  对照 `R_CUTOFF` 明确标 `angstrom`，说明"空"就是按内部原子单位。`videonotes/cp2k-4-…-精读笔记 L316–L326 [21:01–21:36]`）
- **三个"讲师说的值其实就是官方默认"的开关**：`&CI_NEB NSTEPS_IT` 默认 **5**、`&BAND NUMBER_OF_REPLICA` 默认 **10**、
  `&OPTIMIZE_BAND OPTIMIZE_END_POINTS` 默认 **F** ⇒ "先跑 5 步 IT-NEB""改成 Force"**都可省**；
  `OPTIMIZE_END_POINTS` 只在用 `&OPTIMIZE_BAND` 且**想同时松弛端点**时才写 `T`
  （`videonotes/cp2k-4-…-精读笔记 L328–L341 [21:36–22:30]`；`_kw_probe.py` 逐项复核）。
  另注 `BAND_TYPE` 官方默认是 **`IT-NEB`**，"默认就是 CI-NEB"是**误解**（要爬坡必须显式 `CI_NEB T` / `BAND_TYPE CI-NEB`）。
- ✅ **每镜像的输出文件名已定案（2026-10）：`<PROJECT>-BAND<n>.out`**（n = 镜像序号）。
  **官方 CP2K NEB 练习页逐字**："For the NEB calculations, CP2K produces a few output files. The most important are:
  `neb1.out`（标准输出，看有没有算完）/ `neb1-pos-Replica_nr_XXX-1.xyz`（**每个 replica 一条轨迹**）/
  **`neb1-BANDXXX.out` : geometry optimization output for each replica**"
  —— 它自己的脚本就是 `for a in 1..10; do grep ENERGY neb1-BAND${a}.out | tail -n 1 …`。
  （出处：<https://www.cp2k.org/exercises:2014_ethz_mmm:nudged_elastic_band>）
  ⇒ 课程里那 **6 个文件 = `cp2k-BAND1.out` … `cp2k-BAND6.out`**（他的 `PROJECT` 就叫 `cp2k`），
  **笔记的 `cp2k-band.out` 与 B/C 层的 `cp2k-<n>.out` 都不准确**（前者丢了序号、后者丢了 `BAND`）——
  旧记录说"官方 XML 不含输出文件名，无法定案"，是因为只查了 XML：**文件名不在输入参考里，在官方练习/用法文档里**。
  > 📌 另一件容易混的事：`&MOTION/&BAND/&CONVERGENCE_INFO` 的 `FILENAME` **默认是 `__STD_OUT__`**（写屏幕/stdout），
  > 那是"**收敛判据的打印**"；**每次几何优化的独立 out 是 `-BAND<n>.out`**。两者不是一回事，别互相解释。
- **必须做频率验证**：NEB 只给路径，**过渡态要用频率确认**（判据见 §23.1）。

---

## 21. 计算技术与并行（Technologies，手册章，决策向）

- **特征求解器**：大绝缘/半导体用 `&OT`（最快，但**不支持金属/k点/需取 MO**）；要 MO/金属/k点用对角化 `&DIAGONALIZATION`(Davidson/Felbermayr)。大体系对角化可启 **ELPA**（`&GLOBAL &PRINT &PRINT_ELPA` 或构建时启用）加速。
- **MP2/RPA 线性代数**：COSMA / SpLA 库加速矩阵乘，可上 GPU。
- **GPU 加速**：构建启 CUDA/HIP/OpenCL，运行时 DBCSR/GRID/ACC 自动卸载；对大体系网格/积分收益明显。
- **混合并行 PSMP**：MPI×OpenMP；`&EXT_LS` 等控制进程/线程布局。
- **任务级并行（高通量）：`&FARMING` 批处理**（H 层教材增量 T06 P23；此前 A–G 层只有 G 层段名清单）
  ——`&GLOBAL PROGRAM FARMING` + **`RUN_TYPE NONE`**，`&FARMING` 下：
  `NGROUPS`(并行作业组数)、**`GROUP_SIZE`(每组处理器数，默认 8)**、**`MASTER_SLAVE`(负载均衡)**；
  每个作业一个 `&JOB`（`JOB_ID`（可选，串依赖时必需）/ `DIRECTORY` / `INPUT_FILE_NAME` / `OUTPUT_FILE_NAME`，
  可用 **`DEPENDENCIES`** 指定依赖的 `JOB_ID`）。
  - 要点（T06 P23 旁注）：**作业跑在同一个 CP2K 进程里、MPI 只初始化一次 ⇒ 省掉重复启动开销**，**适合大量小作业**；
    不适合单个大作业（大作业仍走普通 MPI 提交）。
  - 出处与缺口：H 层 `references/h_tutorials/notes/03_hybrid_admm_parallel.md` §4.4（可照抄配方）；
    G 层 `20_input_reference_tree.md:138` 只有段说明与直接关键字清单，**`&JOB` 的 5 个关键字与 `MASTER_SLAVE` 均未列名**。
  - 与输入预处理器的配合（`@INCLUDE` 相对 CWD）：见 F 层 `playbook.md` §3.1 的多目录工程布局。
- 用户侧通常只需：选对角化策略(§12)、必要时开 ELPA、确认构建含所需库。具体硬件/构建属系统层，顾问给运行时建议即可。

> 参考手册：`technologies/eigensolvers`(ELPA/cuSOLVERMp/DLA-Future)、`technologies/accelerators`(CUDA/HIP/OpenCL)。

---

## 22. SCF 收敛全流程决策（手册核对 v5，批次 7 内化）

AIMD/DFT 最常见的「跑不动」就是 SCF 不收敛。下面按 SCF 循环从外到内给决策树（全部关键字对照 CP2K 2026.1 官方 `cp2k_input.xml` 逐字核对）。

### 22.1 `&SCF` 顶层（最核心的 5 个）
| 关键字 | 默认 | 何时调 / 怎么调 |
|---|---|---|
| `EPS_SCF` | **官方默认 `1.0E-5`**；生产常用 **`1.0E-6`**（官方 HOWTO 的"典型值"） | 能量收敛阈值；难收敛体系先放宽到 1E-5 让大循环前进，再收紧。**AIMD 场景有上下两个边界，见 §22.7**（下方"默认值定案"表给出三档的出处） |
| `MAX_SCF` | 50 | 单次 SCF 最大步数；难收敛可提到 200–300 |
| `SCF_GUESS` | `ATOMIC` | 重启/接续计算用 `RESTART`（配合 `--wfn-restart`）；OT 体系可用 `SPARSE` |
| `ADDED_MOS` | `0` | **`&SCF` 顶层**（非 DIAGONALIZATION）。金属/导带/过渡态/开壳层设数百个空轨道（如 500），保证占据数平滑变化 |
| `CHOLESKY` | `RESTORE` | **`&SCF` 顶层**。S⁻¹ 求逆算法：`OFF`(直接求逆)/`REDUCE`/`RESTORE`(默认)/`INVERSE`/`INVERSE_DBCSR`。大体系 `INVERSE` 更快 |

> 其它顶层：`LEVEL_SHIFT`(占据/空轨道能级劈裂，帮助难收敛的激发态/过渡态)、`MAX_DIIS`(DIIS 向量数)、`EPS_DIIS`(启 DIIS 的收敛阈值，默认 1E-1)、`NOTCONV_STOPALL`(子循环不收敛时是否停)。

> ⚠️ **单位**：`EPS_SCF`（以及 `&QS EPS_DEFAULT`、`&SCF/&OUTER_SCF EPS_SCF`）的数值是 **Hartree（原子单位），不是 eV**
> —— 与 VASP 的 `EDIFF` 直接照搬会错约 27 倍（1 Hartree ≈ 27.211 eV）。这也是"几何优化判据用 bohr⁻¹·hartree / bohr，
> 而 `&COORD` 与 `&CELL` 用 Å"这组混用的同一来源（`videonotes/cp2k-3-…-精读笔记 L658–L666 [49:38–50:53]`）。
> ✅ **`EPS_SCF` 的"默认值"已定案（2026-10）：官方默认 = `1.0E-5`**，表里那个 `1.0E-6` 是**推荐值/常用值**、不是默认值。
> 三个数字各有出处，**互不冲突**：
>
> | | 值 | 出处 |
> |---|---|---|
> | **官方默认** | **`1.0E-5`** | `cp2k_input.xml`：`FORCE_EVAL/DFT/SCF/EPS_SCF` → `DEFAULT_VALUE : 1.00000000E-005`（`&SCF/&OUTER_SCF`、`&XAS/&SCF` 同为 `1.0E-5`）。**全 XML 无任何 GPW/OT 分档说明**，描述只有一句 "Target accuracy for the SCF convergence." |
> | **官方教程的典型值** | **`1.0E-6` ~ `1.0E-7`** | H 层 `h_tutorials` 抽取的官方 HOWTO（`water_cheating.inp`）逐字注释："**SCF 精度典型 `1.0E-6` – `1.0E-7`**"，其输入写 `EPS_SCF 1.0E-6` |
> | **AIMD 的两档推荐** | 长轨迹 `1E-6` / 短轨迹 `1E-5` | §22.7（能量漂移与计算量的折中，`L1 P27`） |
>
> ⇒ **规范说法**：**默认 `1E-5`；生产上常显式收到 `1E-6`（官方 HOWTO 的口径）**；AIMD 按 §22.7 两档选。
> **旧记录为什么判成"两说"**：把"本库沿用的推荐档 `1E-6`"误当成了"官方默认值"，于是与 XML 的 `1E-5` 对不上。
> 二者说的根本不是同一个东西 —— **不需要查源码或手册即可定案**（已核 `_kw_probe.py --find EPS_SCF`：10 处
> `EPS_SCF` 中 `&SCF` 一族全为 `1.0E-005`；`&LS_SCF` 是另一码事，`1.0E-7`，单位也不同）。
> **注意 §22.7 的 AIMD 推荐值不受此影响。**

### 22.2 特征求解：OT vs 对角化（二选一）
- **OT（`&SCF &OT`）**：**大绝缘体 / 半导体的推荐首选**（最快），**不支持金属、不支持 k 点，取不出 MO**。算法 `MINIMIZER`(CG/DIIS/BROYDEN)、`SAFE_DIIS`、`N_HISTORY_VEC`、`BROYDEN_BETA`(欠松弛)、`LINESEARCH`(默认 `2PNT`)。
  - ⚠️ **`PRECONDITIONER` 的官方默认是 `FULL_KINETIC`**，不是 `FULL_SINGLE_INVERSE`；
    `FULL_SINGLE_INVERSE` / `FULL_ALL` 是**显式换用的更强（也更贵）选项**，属"提效手段"而不是默认值
    （`_kw_probe.py --section FORCE_EVAL/DFT/SCF/OT`；`videonotes/cp2k-3-…-精读笔记 L812–L822 [63:24–64:03]`）。
    > 注：`&SCF/DIAGONALIZATION/DAVIDSON` 下也有个同名键，**默认是 `FULL_ALL`** —— 两处别混。
  - **复杂度标度（大体系选型的决定性依据）**：**对角化 = 基函数的三次方（N³）**；
    **OT = 基函数的一次方 × 占据轨道数的平方（N × N_occ²）**。因为"占据轨道的数量肯定要比基函数少得多"，
    **体系一大 OT 就压倒性便宜**（`videonotes/cp2k-3-…-精读笔记 L766–L791 [58:37–61:49]`）。
  - OT 的四条边界（讲师口径）：① 没有 `SMEAR`（适合半导体）；② 金属**收敛性很差**（"算半天它也收敛得很慢"）；
    ③ **DFT+U 只能在 OT 上用**（对角化不能加 U）；④ **k 点只有对角化能加**，OT 只能 Γ 点。
    （同上；与本文件 §5、§28.3、§31.6 同口径）
- **对角化（`&SCF &DIAGONALIZATION`）**：`ALGORITHM` 枚举 = `STANDARD`(默认,LAPACK/Jacobi) / `OT` / `LANCZOS`(块 Krylov) / `DAVIDSON`(预条件块 Davidson) / `FILTER_MATRIX`。金属/k点/需 MO 必须走对角化。

> ⚠️ **`&SCF` 段没有任何"路线"关键字** —— 走 OT 还是对角化，**完全由有没有写 `&OT` / `&DIAGONALIZATION` 决定**；
> 两个都不写就是**对角化**（`ALGORITHM STANDARD`）。
> > 📌 **更正记录**：本行原写作"**OT（默认，`&SCF &OT`）**" —— **措辞不准、会被读成"CP2K 默认走 OT"**。
> > 错在哪：CP2K 的 `&SCF` 段本身没有 `METHOD`/`ALGORITHM` 之类的路线开关，默认路线不是由某个"默认值"给出的；
> > **不写 `&OT` 就是对角化**。正确表述是"**OT 是大绝缘体/半导体的推荐首选，不是 CP2K 的默认路线**"。
> > 依据：官方 `cp2k_input.xml` 的 `FORCE_EVAL/DFT/SCF` 子树里，`&OT` 与 `&DIAGONALIZATION` 是**两个并列的可选子段**，
> > 而 `&SCF` 的**直接关键字里没有任何路线开关**（`python _kw_probe.py --section FORCE_EVAL/DFT/SCF` 实测：
> > `MAX_SCF` / `EPS_SCF` / `SCF_GUESS` / `ADDED_MOS` / `CHOLESKY` … 全是具体参数，没有 `METHOD`/`ALGORITHM`）。

### 22.3 `&SCF &MIXING`（仅对角化/线性标度生效，OT 不用）
- `METHOD` 枚举（默认 `DIRECT_P_MIXING`）：`NONE` / `DIRECT_P_MIXING` / `KERKER_MIXING`(倒空间 Kerker 阻尼) / `PULAY_MIXING` / `BROYDEN_MIXING` / `BROYDEN_MIXING_NEW` / `MULTISECANT_MIXING`。
- 实战：`ALPHA`(新密度占比,~0.4 默认)、`BETA`(Kerker 分母,默认 0.5 bohr⁻¹)、`NMIXING`(启 DIIS 前最小混合步)、`N_SIMPLE_MIX`(先 Kerker 几步)。选择优先级 BROYDEN→PULAY(金属)→MULTISECANT(难收敛)，见 §12。

### 22.4 `&SCF &SMEAR`（金属/窄带隙必开）
- `METHOD` 枚举（默认 `ENERGY_WINDOW`）：`FERMI_DIRAC`(配 `ELECTRONIC_TEMPERATURE [K] 300`，**该默认值就是 300 K**，见 §6) / `ENERGY_WINDOW`(配 `WINDOW_SIZE`) / `LIST`。
- `FIXED_MAGNETIC_MOMENT`：固定自旋极化差 m=n↑−n↓（负值=让 CP2K 自己优化）。
- 开 SMEAR 时 `ADDED_MOS` 必设（§22.1），否则占据数无法平滑过渡。

### 22.5 `&SCF &OUTER_SCF`（OT 难收敛/杂化泛函救场）
- `TYPE`(外层循环类型)、`OPTIMIZER`(STEEPEST_DESCENT/DIIS/BROYDEN)、`MAX_SCF`(外层最大步,默认 10)、`EPS_SCF`(外层目标梯度)、`DIIS_BUFFER_LENGTH`、`EXTRAPOLATION_ORDER`(MD 外推阶数)。
- **⚠️ `OUTER_SCF` 的机制是"重做 preconditioner 再继续 SCF"，不是"把 `MAX_SCF` 调大让它慢慢收敛"**：
  讲师原话——"如果这个 OT 计算……第一圈 SCF 迭代没有收敛……**我们可以去重新进行 preconditioner 的（初猜），
  再去初猜之后再去做这个 SCF 迭代**。这样的话，经过一圈或者两圈的这个 `OUTER_SCF`，它就可以收敛。
  **这是 OT 的算法收敛的一个小技巧**"；并明确"**并不是 OT 收敛算法把这个 `MAX_SCF` 取得特别的大，
  然后让它慢慢地去收敛 —— 这种效率是比较低的**"（`videonotes/cp2k-4-…-精读笔记 L829–L833 [64:31–65:20]`）。
  > 机理在 H 层 `h_tutorials/notes/04_input_running.md:95` 已收录（"若前 `SCF_NCYCLES` 步没收敛，
  > **可在更新预条件后继续更多圈**"）；本层此前只有开关 `--outer-scf`、没有机理 —— 这里补上。
  > ⇒ **实操取舍**：OT 不收敛先上 `&OUTER_SCF`（便宜），不要一上来把 `MAX_SCF` 堆到 500；
  > `MAX_SCF` 500 是**金属走对角化**时的处方（见 §22.7 后的"金属"条与 §31.6）。
- **重启链的两个关键字必须成对**：`&SCF SCF_GUESS RESTART` ↔ `&DFT WFN_RESTART_FILE_NAME <file>`
  （`WFN_RESTART_FILE_NAME` 官方默认 `-`）。波函数文件是**默认自动打印**的，文件名 = **`<PROJECT>-RESTART.wfn`**；
  写统一 `PROJECT cp2k` 时才是 `cp2k-RESTART.wfn`（讲师脚本只认这个前缀）。
  > ⚠️ **AIMD 不建议输出 wfn**：讲师口径"总是会频繁地去读写这个硬盘……一方面会把硬盘撑很大，
  > 一方面会把这个硬盘寿命给降低"；正解是**常规 AIMD 关掉 wfn 输出**，只在需要跨任务续算 SCF 初猜时才开。
  > 想降频而不关掉，就改 §14 提到的 `&SCF/&PRINT/&RESTART` 频率（默认 8）。
  > （`videonotes/cp2k-3-…-精读笔记 L386–L396 [29:36–30:33]`、`L638–L656 [47:53–49:29]`；
  > `_kw_probe.py --section FORCE_EVAL/DFT` 复核 `WFN_RESTART_FILE_NAME default=-`）

### 22.6 MOM（最大重叠法，激发态/过渡态占轨锁定）
- `&SCF &MOM`：`MOM_TYPE`(可重启修正版)、`START_ITER`、`OCC_ALPHA`/`DEOCC_ALPHA`/`OCC_BETA`/`DEOCC_BETA`(指定占/空轨道)、`PROJ_FORMULA`(投影公式)。用于锁定特定轨道占据以避免 SCF 跳到错误态。

> **收敛决策速查**：OT 不收敛 → 先换 `--ot-minimizer cg`/`broyden`（§12）；金属 → 开 `--smear`+`--added-mos`；仍不收敛 → 加 `--outer-scf` 或切对角化 `--mixing-method pulay/multisecant`；过渡态/激发态 → `LEVEL_SHIFT`、`&MOM`、增大 `ADDED_MOS`。

### 22.7 AIMD 场景的 SCF 参数测试（批 14）

> 出处：字幕 `S1.1.txt:1580–1879`。**为什么 AIMD 要单独立一条**：一个结构优化几十~100 步就收敛了，参数快慢无所谓；**AIMD 要跑 1 万步、10 万步，每个离子步内都做一次 SCF**，所以"SCF 参数没测好"在 AIMD 里会被放大成"整条轨迹跑不完"。讲师原话："在做 AIMD 的时候，我们经常要模拟一万步、十万步，那这个时候我们一定要把所有的计算参数仔细地测试好了"（`S1.1.txt:1828–1846`）。

- **`EPS_SCF` 有上限，不是越紧越好**：
  - **下限（不能再松）**：设到 **1×10⁻⁴**（讲义记作 1E-4）时"总能就控制不住了，就会产生 energy drift"（`S1.1.txt:1587–1600`）。
  - **越紧越好吗？不是**：设到 **1×10⁻⁷** 时"这个计算所需要的时间就太长了，我们让一个 SCF 迭代收敛需要特别长的时间，那我们整个 AIMD 模拟需要的时间就非常的长"（`S1.1.txt:1615–1626`）。
  - **折中口径**：讲师给的经验档是"一般来说我们设置 **1×10⁻⁵** 是差不多的"（`S1.1.txt:1627`）。**与 `course_learned.md §1.3` 的 energy-drift 三档判据合并使用**（判据以讲义 `L1 P27` 为准，本节不复述数字）：
    > 漂移角度：**1E-6 / 1E-7** 才是长 AIMD 的安全档，**1E-5 只适合短轨迹**；
    > 机时角度：**1E-7** 会让单次 SCF 慢到整条 AIMD 不可承受。
    > ⇒ **默认落在 `1E-6`（长轨迹）；大体系试探/短轨迹可用 `1E-5`；只有漂移确实压不住时才上 `1E-7`。**
- **AIMD 前的参数速度测试：跑 2–4 步就够**："在我们做这个 AIMD 模拟之前，一定要仔细地来做，来跑几步——简单地跑个三四步、两三步，把这个参数都换一换，来看一下到底使用哪种参数它的计算是最快的"，然后才开正式模拟（`S1.1.txt:1859–1867`）。讲师给的收益量级："本来一个月要模拟完成的任务，可能有两周就模拟完成了"（`S1.1.txt:1869–1872`）。
- **要测什么**：`&OT` 的 **`PRECONDITIONER`** 与 **`MINIMIZER`**（`S1.1.txt:1846–1851`；讲义 `L1 P23` 列的测试清单是 `PRECONDITIONER FULL_SINGLE_INVERSE / FULL_ALL` + `MINIMIZER CG / DIIS / BROYDEN`）。
- **`CG` vs `DIIS` 没有普适答案，必须按体系实测二选一**："有的体系里边我们用共轭梯度（CG）这个方法它算得比较快，有的体系里面我们用 DIIS 的方法它算得比较快"（`S1.1.txt:1852–1858`）。**不要照抄别人的 `MINIMIZER`。**
- **无带隙 / 带隙很小的体系（如石墨烯类）要额外测 OT vs 对角化**（讲义 `L1 P23`）。
- **测试方法就是"做一个离子步的收敛，比 `CG` 快还是 `DIIS` 快"**（不跑整条轨迹）；
  讲师给这段投入的性价比论证可复用："**我们测这几个参数可能用一两个小时就测完了，但是我们跑一条 AIMD 的模拟，
  我们动辄可能跑几周一个月的时间 —— 所以说花一两个小时就测试这个参数其实是非常有必要的**"
  （`videonotes/cp2k-3-…-精读笔记 L793–L833 [62:26–65:20]`）。这与上面"跑 2–4 步"是同一条建议的两种说法。
- **金属体系：`MAX_SCF` 要敢设 500**（不要按量子化学程序的直觉提前掐掉作业）——
  讲师口径：量子化学（高斯那类）SCF **超过 64 / 128 步不收敛就基本不可能收敛**，而
  **第一性原理"三四百步、四五百步才会收敛"** ⇒ `MAX_SCF 500` 是模板推荐值
  （`videonotes/cp2k-3-…-精读笔记 L720–L734 [54:52–56:33]`；与本文件 §22.1 的"难收敛可提到 200–300"是**并列两档**：
  一般体系 200–300 够，金属/对角化模板直接上 500）。
  > 官方 `MAX_SCF` 默认仍是 **50**（`_kw_probe.py FORCE_EVAL/DFT/SCF/MAX_SCF`）——**它是"单次 SCF 最大步数"，
  > 不是"收敛阈值"**，调大只影响"允许迭代多久"，不改变收敛判据。
- 这一节的"为什么"与 §31.1 的**总原则**一致：**AIMD 牺牲精度换速度，静态计算反过来**。

---

## 23. 振动分析 / 声子 / IR 谱（VIBRATIONAL_ANALYSIS，批次 9）

`RUN_TYPE VIBRATIONAL_ANALYSIS` + 顶层 `&VIBRATIONAL_ANALYSIS`（无需放进 FORCE_EVAL）：用**有限差分**数值构造 Hessian，再用对角化求频率与模式。

| 关键字 | 默认 | 用途 |
|---|---|---|
| `DX` | **0.01 bohr** | 有限差分步长（⚠️ **单位是 bohr，不是 Å**：0.01 bohr ≈ 0.0053 Å；写 `0.01 angstrom` 会差 1.9 倍）。疑难体系可调大 |
| `NPROC_REP` | 1 | 每个副本（原子位移构型）用的 MPI 核数；mode-selective 会起多个副本 |
| `FULLY_PERIODIC` | .FALSE. | 设为 .TRUE. **不**从 Hessian 清除刚体转动（官方描述 "**Avoids to clean rotations from the Hessian matrix.**"）。⇒ **它同时决定输出多少个频率**，见 §23.1 |
| `INTENSITIES` | .FALSE. | 算 **IR 强度**（需同时开偶极矩打印，参见 §14 `&DFT &PRINT &MOMENTS`，配 `&PERIODIC` 或 `&LOCAL` 求偶极导数） |
| `THERMOCHEMISTRY` | .FALSE. | 算气相**热力学量**（熵、焓、自由能）；仅对气相分子有效 |
| `TC_TEMPERATURE` / `TC_PRESSURE` | 298.15 K / 1 bar | 热力学量计算的 T、p |
| `&PRINT &MOLDEN_VIB` | — | 导出 `.mol` 振动模式，供 Molden 可视化 |
| `&PRINT &CARTESIAN_EIGS` / `&HESSIAN` / `&ROTATIONAL_INFO` | — | 笛卡尔本征矢量 / 完整 Hessian / 转动信息 |

> **何时用**：① 验证优化结构是真实极小（无虚频，除平动/转动）；② 算 IR/Raman 谱（IR 走 `INTENSITIES`+偶极矩，Raman 需极化率→CP2K 用 `&PROPERTIES` 或外部）；③ 气相分子热力学修正（自由能展宽→与 exp 比对）；④ 声子（全周期性体系需 `FULLY_PERIODIC`）。
> **限制**：有限差分对每个自由度要 2 次能量计算，N 原子体系 ~ 6N 次 SCF，大体系很贵；金属/有虚频需先确认收敛。
> `gen_inp.py` 已支持 `--type vib`（见 §24 末尾模板说明）。

### 23.1 虚频判读与固定原子算频率（讲师经验，批 14）

> 出处：字幕 `S4.txt:986–1002`、`1176–1284`、`1547–1618`。关键字清单见本 §23 上表；这里给的是**判据与两个必踩坑**。

- **成本先算清**：频率只能用**有限位移**（CP2K 没有解析 Hessian），要做 **6N+1 次计算**（3N 个自由度 × 左右各一次 + 中心点一次）；100 个原子 ≈ 600 多次 SCF（`S4.txt:1176–1201`、`1203–1224`）。**大体系算频率前先估机时。**
- **过渡态验证的三档判据**（配合 §20.1 的 NEB）：
  - **1 个虚频** → 一阶鞍点（过渡态）✅
  - **0 个虚频** → 极小值
  - **多个虚频** → "那它啥都不是"，即过渡态搜得不准（讲师另指出常见原因是**收敛阈值设得太宽**）（`S4.txt:986–1002`、`1090–1104`）
- **虚频"大小"是第二道筛子**：**真过渡态的虚频至少约 100 波数（cm⁻¹）**；如果只算出**几个波数**的虚频就要警惕——那多半是**计算误差**，或是混入了平动/转动（`S4.txt:1564–1583`）。
- **第三道证据：虚频振动方向必须连接初态与末态**（用 `movie_mode_1` 在 VMD 里来回播放看）（`S4.txt:1547–1562`）。
- **⚠️ 固定原子算频率：并行 image 数必须调大，否则频率算不对**——"如果比如说我们这里设置 56 的话，它最后算出来的频率是不对的……这个东西是一个数学处理上的问题"；正确做法是**每个位移点用少量核、同时并行多个点**（56 核写 `NPROC_REP 7` ⇒ 同时并行 8 个结构）（`S4.txt:1236–1270`）。**这个错误不会报错，只会给出错的频率。**
  > 📌 **E 层逐字佐证（讲义同一页的旁注）**：`L3.txt:1791–1796` 在频率输出旁写着"**注：如果有固定原子，需要用尽量多的
  > 并行结构，否则会出现不可理的虚频**" —— 这是讲义原文级别的出处，比字幕更硬（`NPROC_REP` 官方默认 **1**，
  > 即**默认串行**，所以"不写就一定踩"）。
- **表面体系算频率要固定 slab、只放开吸附分子 —— 但输出的是 `3N` 个频率，不是 `3N−6` 个**：
  讲师算例是 123 原子、`LIST 1..120` 固定、只放开吸附水的 3 个原子（O/H/H），**打印出来的是 9 个（= 3N，N = 3）频率**，
  并且"**这个 9 个振动频率全都给它算作计算结果里面**"（`S4.txt:1278–1296`、`1411–1439`；
  `videonotes/cp2k-4-…-精读笔记 L621–L633 [46:28–47:27]`、`L654–L677 [50:37–52:39]`，同笔记 `L670` 逐字：
  "因为这个水分子是 3N 的自由度（N = 3，所以 3N = 9）……我们就把这 9 个振动频率全都给它算作计算结果里面"）。
  > 📌 **更正记录**：本行原写作"⇒ **只出 3 个振动**；吸附水的完整振动是 9 个……**不要误以为'9 个里 6 个是平动转动、应当剔除'**"
  > —— **前后两句自相矛盾，且第一句是错的**。
  > 错在哪：把讲师"**真正的分子内振动只有 3N−6 个**"这句解释，误读成"程序只打印 3 个"。
  > 正确表述（依据链）：
  > ① **讲义原文**（`L3.txt:1786` 起的同一算例输出旁）明确注"**所有频率，一共 3N 个**"并列出 **9 个**值
  >    （130.03 / 350.66 / 410.16 / 519.35 / 631.11 / 687.24 / 1604.04 / 3545.82 / 3701.88 cm⁻¹，`L3.txt:1786–1799`）；
  > ② **官方机制**：`VIBRATIONAL_ANALYSIS/FULLY_PERIODIC` 的描述就是 "Avoids to clean rotations from the Hessian matrix."
  >    （默认 `F`）—— 表面算例写 `FULLY_PERIODIC T` 等于**故意不清除转动**；
  > ③ **气相分子**走 `FULLY_PERIODIC F`：清除平动+转动后才是真正的 **`3N−6`** 个振动（讲义 P107 另起一例给
  >    **3 个**值 1617.25 / 3716.94 / 3822.03 cm⁻¹，`L3.txt:1806–1812`）。
  > ✅ **"打印几个"已定案（2026-10），原先的"两说"是个假冲突** ——
  > **三个数字分别对应三种不同情形**，把"体系能不能整体平动/转动"分清就不矛盾了：
  >
  > | 情形 | 能消掉的自由度 | 打印个数 | 出处 |
  > |---|---|---|---|
  > | **周期体系 + 固定原子**（本课那个 123 原子算例；水分子之外全固定） | **无可消**（整体平动/转动本就不存在） | **`3N`**（N = 3 个可动原子 ⇒ **9** 个） | 讲义 `L3.txt:1786–1799` 逐字"**所有频率，一共 3N 个**"＋列出 9 个值 |
  > | **自由分子**，`FULLY_PERIODIC F`（默认） | 3 平动 **+ 3 转动** | **`3N−6`**（线性分子 `3N−5`） | 讲义 P107："分子体系只有 `3N-6` 个振动模式，计算的时候需要 `FULLY_PERIODIC F`，**把转动模式去掉，同时也把平动模式去掉**：最后得到 **3** 个振动频率"（H₂O：1617.25 / 3716.94 / 3822.03 cm⁻¹，`L3.txt:1806–1812`） |
  > | **自由分子**，`FULLY_PERIODIC T` | 只消 3 平动，**保留 3 转动** | **`3N−3`**（其中 3 个是转动） | H 层官方教材 T24 **P18**："`FULLY_PERIODIC T` 避免从 Hessian 矩阵中消除转动模式。开启该关键词后，对于 N 个原子的体系会计算出 **`3N-3`** 个频率，其中包含了 3 个转动自由度"（`references/h_tutorials/notes/06_basis_and_intro.md:140`）——**注意它自己的示例输入正是 `FULLY_PERIODIC T`** |
  >
  > **三者由官方 XML 统一**：`FULLY_PERIODIC` 的描述只有一句 "**Avoids to clean rotations** from the Hessian matrix"（默认 `F`）
  > ⇒ ① **转动**清不清由它管；② 平动在两种取值下**都**会被清（只要体系能平动）；
  > ③ 固定原子/纯周期体系**没有**可清的平动转动，于是什么都不清。
  > **旧记录为什么会判成"两说对不上"**：拿 T24 的 `3N−3` 去套讲义那个 **123 原子固定原子**算例（得 6 ≠ 9）——
  > **两者根本不是同一种情形**（T24 讲的是自由分子）。
  >
  > ✅ **已在真机 CP2K 2022.1 上实测确认（2026-10，H₂O 分子 N=3）** —— 这条从"文献互证"升级为"实测"：
  >
  > | `FULLY_PERIODIC` | `VIB\| Cartesian Low frequencies ---`（**消之前**） | `VIB\|Frequency (cm^-1)`（**消之后**） |
  > |---|---|---|
  > | **`F`** | **9 个** = `3N` | **3 个** = `3N−6` |
  > | **`T`** | **9 个** = `3N` | **6 个** = `3N−3` |
  >
  > **顺带解开了"讲师说 3N"的由来**：CP2K 会**先**打印一行 `Cartesian Low frequencies`
  > 列出**消之前的全部 `3N` 个** Hessian 本征值，**再**打印消完平动/转动后的结果。
  > 讲义 P106 那句"**所有频率，一共 3N 个**"指的正是**前面那一行**；而 P107 的"3 个"是**后面那一行**。
  > ⇒ 三方说法（讲义 P106 / 讲义 P107 / T24 P18）至此**全部对上，且都是实测**。
  > 另注意：`Cartesian Low frequencies` 这行**在两版取值下都是 3N 个**，与 `FULLY_PERIODIC` 无关。
  > **对本条的结论无影响**：无论 9 / 6 / 3，**都不是"只打印 3 个"** —— 原表述的错误是确定的。
  > **B 层 `course_learned.md:1331` 的"只出 3 个振动模式"是同一处误读**（该文件同一章 `:1351–1353` 自己列了 9 个值）。
- 🔴 **`INTENSITIES T` 必须配 `&MOMENTS`，否则 CP2K 直接 Abort**（2026-10 真机实测发现）：
  红外强度要读 `[DIPOLE]` 这个 result；没开偶极矩时 CP2K 在**第一个位移**就死：
  ```
  * [ABORT]  Trying to access result ([DIPOLE]) which was never stored!
  *          common/cp_result_methods.F:183
  ```
  **正确写法**（`&DFT/&PRINT` 下）：
  ```
  &DFT
    &PRINT
      &MOMENTS
        PERIODIC FALSE     ! 分子/PERIODIC NONE 时必须；周期体系用默认 T(Berry 相位)
        MAX_MOMENT 4
      &END MOMENTS
    &END PRINT
  ```
  官方 2022.1 XML 对 `PERIODIC` 的描述："Use **Berry phase** formula (PERIODIC=T) or **simple
  operator** (PERIODIC=F). **The latter normally requires that the CELL is periodic NONE.**"
  ⇒ **`&CELL`/`&POISSON` 是 `PERIODIC NONE`（孤立分子）就用 `F`；周期体系用默认 `T`。**
  ⚠️ **这类缺陷官方解析器查不出来**（输入语法完全合法）—— `validate_inp.py` /
  `_validate_all.py` 的 vib 用例当时**全是绿的**。**只有真机跑才会暴露。**
  > 已同步修掉 `gen_inp.py`：`--type vib` 现在会自动补 `&MOMENTS`（并按 `--periodic` 决定
  > 要不要 `PERIODIC FALSE`），且 `--periodic none` 时把模板写死的 `FULLY_PERIODIC T`
  > 自动改成 **`F`**（分子要的是 3N−6）。见 `CHANGELOG [2.7.10]`。
- ⚠️ **更正记录（2026-10，本条上一版的归因是错的）**
  > **原来怎么写**：把那次"水分子频率出现 **−2004.7 cm⁻¹ 巨大虚频**、最终频率
  > `−2376.8 / 2369.7 / 4677.8`"归因于「**几何没弛豫**，O 上残余力约 15 a.u.」。
  > **错在哪**：那个 **14.90257519 a.u.** 的 O 受力**根本不是残余梯度，而是静电解错的结果** ——
  > 它与「偏心 WAVELET」静态算例的 O 受力**逐位相同**。真正的原因是
  > **`POISSON_SOLVER WAVELET` 而分子没居中**（见 §5）：力从一开始就是垃圾，
  > 频率自然全是垃圾。**同一次运行里 `SUM OF ATOMIC FORCES` 高达 24.7 a.u.**，
  > 那才是当时就该看到的症状。
  > **现在依据什么**：居中后同一分子 `|ΣF|` 降到 0.0002、能量回到 −17.120 Ha（§5 实测表）。
  > **结论怎么变**：下面这条"必须先弛豫"**本身仍然成立**（是独立的一条规矩），
  > 但**它不能解释那次虚频**；看到巨大虚频时**第一嫌疑应是 ΣF 是否为 0**，其次才是几何。
- 🔴 **频率分析必须在已充分弛豫的结构上做**（独立规矩，与上条更正无关）：
  几何没收敛就跑 vib，Hessian 被残余梯度污染，频率（尤其低频与虚频）不可信。
  正确顺序：`GEO_OPT` 收敛 → 取最后一帧 → `VIBRATIONAL_ANALYSIS`。
  （与"算过渡态前必须先把初末态优化好"是同一条道理，只是换到频率上。）
  **但排查顺序要放对**：先看 `diagnose.py` 报的 `|ΣF|`（> 0.05 a.u. 就先修静电），
  再怀疑几何；否则会像上一版那样**修错方向**。
- **"结构优化 / 过渡态 / 频率"这一套要共用同一套 `&FORCE_EVAL`**：唯一允许的例外是**频率精度不够时把 `EPS_SCF` 收到 1E-7**
  （`videonotes/cp2k-4-…-精读笔记 L646–L652 [49:50–50:26]`）。
  理由（本轮补）：三件套之间要**互相可比** —— 能垒是"过渡态能量 − 初态能量"、虚频来自同一势能面，
  **`&FORCE_EVAL` 一变（泛函/基组/CUTOFF/k 点），能垒与频率就不再可比**。
- **虚频自救**：可以把 `EPS_SCF` 收紧到 `1e-7` 试一次；**改了没区别就不用改**（`S4.txt:1365–1377`）。

#### 23.1.1 第二条归因：GTH 赝势的数值噪音（H 层教材增量）

> 出处：H 层 `references/h_tutorials/notes/06_basis_and_intro.md`（**T24 P19**）。
> **本节前半（上面那些条目）把虚频归因于"方法/收敛阈值"，这里补第二条归因——两者不是简单对错，而是两级排查。**

- **教材原话**："使用 CP2K 程序计算一个**优化好的结构**式的频率时，**也常会出现多个虚频**。这并非是几何优化出现了
  问题，而是 **CP2K 计算使用 GTH 赝势时存在的一个问题**。"（T24 P19）
- **教材给的 4 种处置**（T24 P19 原文的 4 条，**编号沿用教材顺序；本层不替教材排优劣**，只在下一条按"先便宜后昂贵"整理成两级排查）：
  1. **换 NLCC 赝势**（原文给 arXiv:1212.6011 链接）——**但原文同时提醒**："NLCC 赝势很不完整，
     只有 B–Cl 的元素有，且只提供了 PBE 泛函的赝势"⇒ 元素范围受限，多数体系用不上；
  2. **增大 `CUTOFF`，用到 600 Ry 以上**；
  3. 在 `XC_GRID` 用平滑参数（原文拼作 **`SMOOTING`**）——**教材明确"不推荐使用"**；
  4. 在 `XC_GRID` 用 **`USE_FINER_GRID`**——加上后 **XC 部分格点精度提高为 `4*CUTOFF`**。
- **两级排查（本层提炼，判据分别来自两处）**：
  - **第一级（先做，便宜）**：过渡态验证走上面的"虚频个数 → 虚频大小 → 振动方向"三档判据；
    多个虚频先**收紧 `EPS_SCF`**（`S4.txt` 口径，即上面的"虚频自救"）。
  - **第二级（仍不行再看）**：结构确实已优化好、却仍有**多个虚频** ⇒ 考虑 **② `CUTOFF ≥ 600 Ry`** 或
    **④ `USE_FINER_GRID`**；**① NLCC 受元素范围限制、③ 教材自己不建议**。
- ⚠️ **引用限定（两条，务必一起带上）**：
  - **T24 成稿锚定 CP2K 2.5.1（≈2014 年）**（`T24 P2`），其默认值/关键字**都必须回 G 层当前手册复核后再用**；
    尤其是 **`USE_FINER_GRID` 的所属段与当前有效性在 G 层没有任何记载**（H 层 `notes/06` §7-9 已登记为待核）。
  - 方案②的 **600 Ry 是"为压赝势数值噪音"的针对性处方**，与常规生产档（§7 的 CUTOFF 取值、F 层 `playbook.md` §0.4）
    **并列不冲突，但代价高一档**——**先确认虚频确由数值噪音引起再上**。
- ⚠️ **与 `tests/` 口径的连带提醒**：T24 同一份教材还提醒 **`tests/` 目录的参数"往往使用了不合理的参数"**
  （T24 P4–P5），与 E 层 `learn_L3.md` 的"优化过的最佳推荐"直接对立，本 skill 采用**更保守的 T24 口径**
  （见 F 层 `playbook.md` §8"学习资源"处的并列说明）。

- **顺带能出静态 IR 谱**：`INTENSITIES T` + 高斯展宽即可画静态红外（讲师本例三个振动约 **1600 / 3700 / 3800 cm⁻¹**）（`S4.txt:1592–1618`）。**这与第 5 天用 AIMD+TRAVIS 算的动态 IR 是两条不同路线**（后者见 `postprocess.md`）；静态 IR 的峰宽是人为展宽，AIMD 的展宽才反映真实动力学。

---

## 24. 增强采样的集体变量 COLVAR 与 PLUMED 接口（批次 9）

元动力学/约束里的「反应坐标」由 **COLVAR** 定义。`&SUBSYS &COLVAR` 是 CP2K 原生 CV 定义区（注意它**不**在 CONSTRAINT 内，也不在 MOTION 内）。

### 24.1 COLVAR 可定义的 28 种类型（节选最常用）
`DISTANCE`(ATOMS 1 2 / AXIS) · `ANGLE` · `TORSION`(二面角) · `COORDINATION`(配位数：ATOMS_FROM/ATOMS_TO + R0/NN/ND 阻尼) · `RMSD`(骨架 RMSD，需 `&FRAME &COORD`) · `GYRATION_RADIUS` · `WC`(Wannier 中心) · `QPARM`(键级) · `BOND_ROTATION` · `DISTANCE_FUNCTION` · `REACTION_PATH` / `DISTANCE_FROM_PATH` · `COMBINE_COLVAR`(多个 CV 线性组合) · `HYDRONIUM_*`(质子化水簇专用) 等。每个子类型下可挂 `&POINT` 定义虚拟点。

### 24.2 与 METADYN 的接法
`&MOTION &FREE_ENERGY &METADYN &METAVAR` 用 `COLVAR <idx>` 引用 `&SUBSYS &COLVAR` 中第 idx 个 CV（从 1 起），并可设 `SCALE`(该 CV 的高斯高度系数)、`WALL`(加墙)、`LAMBDA/MASS/GAMMA`(扩展拉格朗日方案)。即：先 `&SUBSYS &COLVAR` 定义 N 个 CV → 再在 `&METAVAR` 用 `COLVAR 1`、`COLVAR 2`… 引用。

#### 24.2.1 `&WALL` 的四种形式、`K` 的单位，以及 `&COLVAR` 的两个默认值（批 15，官方 XML 定案）

> 出处：`videonotes/cp2k-5-…-精读笔记 L1814–L1818 [158:14–159:05]`；默认值与单位用 `_kw_probe.py --section` 逐项复核。

- **`&WALL` 下只有 `TYPE` + `POSITION` 两个关键字，参数写在"同名的形式子段"里**：
  `TYPE`（默认 **`NONE`**）用来声明形式，随后用 **`&REFLECTIVE` / `&QUADRATIC` / `&QUARTIC` / `&GAUSSIAN`**
  **四种**子段给参数；**`DIRECTION`（默认 `WALL_PLUS`）与 `K` 写在形式子段里**（如 `&WALL/&QUADRATIC`），
  **不是直接写在 `&WALL` 下**。`POSITION` 的单位是 `internal_cp2k`。
  > ✅ **"三次"这条已可定案（2026-10）：CP2K 没有三次墙。**
  > 官方 XML 的 `&WALL` 子段**只有四种且可枚举完**：`&REFLECTIVE` / `&QUADRATIC` / `&QUARTIC` / `&GAUSSIAN`
  > （`_kw_probe.py --section MOTION/FREE_ENERGY/METADYN/METAVAR/WALL`）。讲师口播的"三次"**没有对应子段**。
  > 而且同一套术语在**上游 VASP 侧**就是"二次/四次"两种（VASP wiki 与本课讲义一致），
  > ⇒ 按**口误**处理（更可能是把"四次"顺口说成"三次"，而不是旧版 CP2K 曾有第三种形式 ——
  > 官方模块自述的 `&WALL` 形式史上也没有三次这一档）。**写输入只用官方这四种。**
- ✅ **`K` 的单位：不是"两说"，是"写没写单位"的区别（2026-10 定案）**：
  官方 XML 给的是 `K  unit=hartree` —— 意思是**不写单位就按 hartree 读**；
  而 CP2K **支持在方括号里显式指定单位**，`kcalmol` 是**合法单位**
  （G 层 `official/01_global_and_units.md:326` 列出的能量单位表里就有 `kcalmol`）。
  **讲义例子正是显式写单位的**：`K [kcalmol] 40.0`（`L5.txt:776/781/784/789`）。
  ⇒ 讲师口播"四五十千卡到一百千卡"与 XML 的 `hartree` **不矛盾** —— 他说的是"该给多大",
  照做就必须写 `K [kcalmol] 40`；**裸写 `K 40` 则是 40 hartree ≈ 25000 kcal/mol，差约 628 倍**。
  > **实操记法**：**要么写 `K [kcalmol] 40`，要么写 `K [hartree] 0.064`（≈40 kcal/mol）；绝不裸写。**
  > 换算：1 hartree ≈ 627.5 kcal/mol；**40~100 kcal/mol ≈ 0.064~0.16 hartree**。
  > 旧记录把这条判成"两说并列、要实机复算"是**多余的** —— 单位方括号是 CP2K 的通用语法，
  > 两种写法本来就指同一个物理量，不存在"谁对谁错"。
- **配位数 CV 的三个默认值（本轮首次查到，且单位是 bohr 不是 Å）**：
  `&SUBSYS/&COLVAR/&COORDINATION`：**`R0` 默认 `3.0` bohr**、**`NN` 默认 `6`**、**`ND` 默认 `12`**
  （`R0_B`/`NN_B`/`ND_B` 同默认）。
  - ⚠️ 讲师给的阻尼形式是 `ξ = [1−(r/r₀)⁹] / [1−(r/r₀)¹⁴]`（平衡键长处 ξ = **9/14**，是故意让梯度最大处落在平衡键长，
    以提高 metadynamics 灵敏度；CP2K 里 `NN`/`ND` 可改，讲师建议 **8/14 或 9/14**）——
    **这与官方默认的 `6/12` 不同**，属"讲师推荐值"，不是默认值。
  - ⚠️ **`R0` 的单位是 bohr**：讲师例把 `r₀` 设到 **1.85（Å 口径）**、又说"设到 3 Å 可以让配位数等于 1"——
    写输入时若照 CP2K 默认单位填 3，实际是 **3 bohr = 1.587 Å**。**要确证讲师那两个数字的口径需要实机复算**（本轮无）。
  - **别与 `&METADYN` 自己的两个指数混淆**：`P_EXPONENT`（默认 **8**）/ `Q_EXPONENT`（默认 **20**）
    是**高斯峰尾部截断**用的（配 `HILL_TAIL_CUTOFF`，默认 −1.0），**与 CV 的 9/14 是两套不同的指数**。
  （`videonotes/cp2k-5-…-精读笔记 L1609–L1651 [139:02–141:48]`、`L1814–L1818`；`_kw_probe.py` 逐项复核）

### 24.3 PLUMED 外部驱动（进阶）
`&MOTION &FREE_ENERGY &METADYN` 下：
- `USE_PLUMED`(逻辑，默认 F)：用 **PLUMED** 作外部元动力学驱动器（支持更丰富的 CV 与偏置，如 OPES、metadyn 的墙/弹簧）。
- `PLUMED_INPUT_FILE`(默认 `./plumed.dat`)：指向 PLUMED 输入脚本。
一旦 `USE_PLUMED .TRUE.`，CP2K 不再用内置 `&METAVAR`，CV 与偏置全在 plumed.dat 里写。
`gen_inp.py` 已支持 `--plumed` + `--plumed-file`（发射 `USE_PLUMED` + `PLUMED_INPUT_FILE`）。

> 实用建议：简单 CV（距离/角度/配位数）优先用 CP2K 原生 `&COLVAR`+`&METAVAR`；需要复杂 CV、路径集体变量、多级偏置或墙函数时上 PLUMED。

### 24.4 CP2K 做 metadynamics 的输入落点与"墙"（讲师实操，批 14）

> 出处：字幕 `S5.txt:4024–4159`、`4195–4293`。§24.2 讲的是"CV 与 METAVAR 怎么接"，这里补的是**新手最容易放错层级的几处**。

- **`&COLVAR` 放在 `&FORCE_EVAL &SUBSYS` 下**（"这个 FORCE_EVAL 下面这个下属这个 SUBSYS 这个 section 里面，我们要给他新添加这个 CV 值"）；**要几个维度的 FES 就加几个 CV**（`S5.txt:4024–4042`）。
- **`&FREE_ENERGY` 与 `&MD` 在 `&MOTION` 下并列**——"在 MOTION 那个里面添加一个叫 free energy 的 section，这个 section 是和那个 MD 这个 section 是并列的"（`S5.txt:4067–4072`）。**放到 `&MD` 里面去就算不出来。**
  > 与 VASP 的位置对应关系：VASP 的 `ICONST` 相当于 CP2K 的 `&SUBSYS &COLVAR`，但 CP2K 把驱动器（`&FREE_ENERGY &METADYN`）挪到了 `&MOTION` 层级（`S5.txt:4024–4066`）。
- **`&METADYN` 关键值（讲师例）**：`DO_HILLS T` 开启填峰；`NT_HILLS 30`（每 30 步加一个峰）；`WW`（峰高，本例 `0.02`，单位为 Hartree）；`SCALE`（每个 CV 的峰宽）。**峰宽要按盆地形状取**（窄盆地窄峰、宽盆地宽峰，可重启换峰）（`S5.txt:4073–4090`、`3931–3969`）。
- **⚠️ `WW`（峰高）必须对所有 CV 一致，`SCALE`（峰宽）可以不同**：CP2K 允许给 CV1/CV2 不同的宽度（VASP 不行），但**峰高必须一致**——"峰高的话必须是一致的，CV1 和 CV2 必须是一致的，要不它没法加这个高斯峰"（`S5.txt:4269–4293`）。CV1 是键长、CV2 是配位数时，宽度更应该分开设。
- **`&WALL`：CP2K 相对 VASP 的关键能力**（为什么选 CP2K 做 FES，见 §17.1）。要点：
  - `WALL_MINUS` 定义**下限**、`WALL_PLUS` 定义**上限**；`K` 是墙的高度/强度；强度函数官方**只有二次/四次/高斯/反射四种**
    （讲师口播里的"三次"**没有对应子段**，按口误处理 —— 见 §24.2.1 的定案表）。`S5.txt:4123–4144`。
  - **`K` 的经验值：四五十到一百 kcal/mol 左右**（"这个墙一般定一个四五十千卡，或者是一百千卡左右都是可以的"）；讲义例给的是 40 kcal/mol（`S5.txt:4141–4144`、`L5.txt:789` 写作 **`K [kcalmol] 40.0`**）。
    ⚠️ **必须连方括号单位一起写**——裸写 `K 40` 会被当成 40 hartree（≈25100 kcal/mol，等于没墙），见 §24.2.1 的定案。
  - **⚠️ 方向千万别定错**："这个墙的方向千万别定义错了，这个方向定义错了之后，整个模拟肯定就是不合理的、给坏掉了"（`S5.txt:4128–4140`）。这是**最容易静默出错**的一步——错了不一定报错，只是结果无意义。
- **`&WALL` 的典型用法：把 CV 锁在你关心的区域**，不让它跑到真空层或解离到很远。讲师举例：N–N 键长只想看 3 Å 附近的解离吸附，"至于再低、再远我就不关心了"，就加一道 4 Å 的上限墙把它弹回来（`S5.txt:4091–4121`）。
- **QM/MM 脱氢练习：C–H 之和的上限墙 5 Å 必加**——
  - 该例第一个 CV 是**两个 C–H 键长之和**（4–50 号 与 7–49 号）；上限墙设为 **5 Å**，下限 1 Å。
  - **不加会怎样**："氢气生成了之后，它会跑到真空层当中……从这个三四个 Å 的距离跑到了三五十个 Å，那么这个势能面就太大、太大了，根本就模拟不完"；**"这个上限是一定要加的，如果这个上限不加，这个 METADYNAMICS 是做不完的"**（`S5.txt:4210–4245`）。
  - **下限可以省**：C–H 键不可能低于 1 Å，"如果真的低于 1 Å 了，就说明我们这个 MD 的参数肯定有问题"——**下限其实是自检项**（`S5.txt:4234–4243`）。

---

## 25. 经典力场 FORCEFIELD 与 QM/MM 衔接（批次 10）

QM/MM（`FORCE_EVAL METHOD QMMM`，见 §16）里 MM 部分由 `&FORCE_EVAL &MM &FORCEFIELD` 定义。纯经典 MD 用 `&FORCE_EVAL METHOD FIST` + 同款 `&FORCEFIELD`。

### 25.1 `&FORCEFIELD` 关键关键字
| 关键字 | 用途 |
|---|---|
| `PARMTYPE` | 力场格式/扭转势类型：`CHM`(CHARMM) / `AMBER` / `G96`(GROMOS) / `OFF`(无扭转) 等；决定读参数方式 |
| `PARM_FILE_NAME` | 力场参数文件名（如 `.prm`/`.top`/`.par`） |
| `VDW_SCALE14` / `EI_SCALE14` | 1-4 相互作用的范德华 / 静电缩放因子（CHARMM 常用 1.0/1.0 或 0.5；AMBER 1-4 vdw=0.5、1-4 elec=5/6） |
| `SHIFT_CUTOFF` | 在截断半径处把非键能加常数偏移归零，避免截断突变 |
| `DO_NONBONDED` | 控制所有实空间非键作用计算 |

### 25.2 非键与静电：`&FORCEFIELD &POISSON &EWALD`
- `EWALD_TYPE` 枚举：`NONE`(实空间库仑+非键一起算) / `EWALD`(标准非 FFT Ewald) / `PME`(粒子网格 Ewald，FFT 插值) / **`SPME`(平滑 PME，β-Euler 样条，**推荐**)**。
- 其它非键势：`&NONBONDED` 下 `LENNARD-JONES`(6-12)、`BUCKINGHAM`、`TERSOFF`(键级，材料)、`BMHFT(D)`、`GENPOT`、`EAM`(嵌入原子，金属)、`WILLIAMS`、`GOODWIN` 等；`&NONBONDED14` 专管 1-4。
- 键合项：`&BOND`(键长) / `&BEND`(键角) / `&TORSION`(扭转) / `&IMPROPER`( Improper) / `&OPBEND`(平面外弯曲)；电荷 `&CHARGE`/`&CHARGES`；极化 `&SHELL`(核-壳模型)。

### 25.3 QM/MM 静电耦合
`&FORCE_EVAL &QMMM`：`E_COUPL` 选 QM-MM 静电耦合方式。**官方合法取值只有 5 个**
（`_kw_probe.py --find E_COUPL` 直查 XML，默认 `NONE`）：

| 取值 | 含义（官方描述） |
|---|---|
| **`NONE`**（默认） | **机械耦合**（经典点电荷近似）—— 最常用、最省 |
| **`COULOMB`** | 解析 `1/r` 势；**GPW/GAPW 下不可用** |
| **`GAUSS`** | 静电势的高斯快速展开 `Erf(r/rc)/r`（即 GEEP） |
| **`S-WAVE`** | s 波静电势的高斯快速展开 |
| **`POINT_CHARGE`** | 用量子力学导出的点电荷与 MM 电荷作用 |

`MM_POTENTIAL_FILE_NAME` + `USE_GEEP_LIB`（内置 GEEP 库，免手备）。边界处理：`&LINK &IMOMM`(IMOMM 连接原子) 等（§17 已述）。

> **更正记录**：本行原写"（`GAUSS` GEEP 高斯展开 / **`SPLINE`** / `NONE`）"——
> **`SPLINE` 不是 `E_COUPL` 的合法取值**（官方枚举里没有它；`SPLINE` 是
> `&MM/&FORCEFIELD/&SPLINE` 的**段名**，两回事）。同时补上原先漏掉的
> `COULOMB` / `S-WAVE` / `POINT_CHARGE`。
> 发现路径：H 层 `notes/07_qmmm.md` §7 的存疑（该笔记 137 页里 `SPLINE` 零命中）
> 用 `_kw_probe.py --find ECOUPL` 查官方枚举定案。（另：`E_COUPL` 是默认名，
> **`ECOUPL` 与 `QMMM_COUPLING` 是别名** —— 教材里两种拼写都对。）

> 何时用：体系太大 DFT 跑不动、但只有局部活性区需量子精度（酶催化、溶液反应、大团簇的表面缺陷）。MM 部分需自备力场与拓扑（力场调参是主要成本）。

---

## 26. 其它 FORCE_EVAL 方法（DFTB / NNP / EIP / MIXED / xTB）+ 采样器（批次 11）

### 26.1 半经验 / 机器学习势（均在 `&FORCE_EVAL` 一级 METHOD）
| METHOD | 入口 | 关键输入 |
|---|---|---|
| `DFTB` | `&FORCE_EVAL METHOD DFTB`，密度泛函紧束缚在 `&QS &DFTB &PARAMETER` | Slater-Koster 参数集（`SK_FILE_NAME` 或参数目录）：常用 `mio-1-1`(有机) / `pbc-0-3`(周期) / `ob2`(含 O,B) / `3ob`(第三周期) / `trans3d`(过渡金属)；`&PARAMETER` 可设 `DISPERSION`(self-consistent DFTB-D)、`SCC`(自洽电荷，默认开) |
| `xTB` | `&FORCE_EVAL METHOD QS` + `&QS &XTB`（`&PARAMETER` 选 GFN 版本） | 原生 GFN0/GFN1，或经 `tblite` 用 GFN2；参数自带，几乎免输入 |
| `NNP` | `&FORCE_EVAL METHOD NNP` | `NNP_INPUT_FILE_NAME`(n2p2 / RuNNer 格式) + `SCALE_FILE_NAME`(对称函数缩放)；需**预训练势**；`&MODEL`/`&BIAS` 可选 |
| `EIP` | `&FORCE_EVAL METHOD EIP` | `EIP_MODEL`(经验原子间势，如 ReaxFF 风格势)；用于纯势函数 MD |

### 26.2 MIXED（多哈密顿混合）
`&FORCE_EVAL METHOD MIXED` + `&MIXED`：`MIXING_TYPE`(线性组合/约束/耦合等)、`NGROUPS`/`GROUP_PARTITION`(子 force_eval 分组并行)；子节 `LINEAR`/`MIXED_CDFT`/`COUPLING`/`RESTRAINT`/`GENERIC`/`MAPPING`。用于 QM/MM 之外的自定义组合（如约束 DFT、片段耦合）。

### 26.3 其它 MOTION 采样器（边缘）
- `&MOTION &MD ... &TMC`：过渡态 / 热力学积分蒙特卡洛（TMC），需 `TEMPERATURE` 等。
- `&MOTION &PILE` / 路径积分：`PILE`(Path-Integral 实空间)、`&PINT`(path-integral 量子核效应，核量子化/同位素效应)；对氢键、轻核零点能相关体系有用。
- 还有 `&MC`(经典蒙特卡洛)、`&SHELL`(核-壳模型 MD)、`&WAVEFUNCTION` 等，对照 `cp2k_input.xml` 的 MOTION 子树即可定位。

> 这些方法的 `gen_inp.py` 当前**不发射**（仅 DFT 系 + metadyn/neb/vib/df 模板）。需要用时不发射、按上表手动拼接，或在顾问指导下加开关。

---

## 27. XC_FUNCTIONAL 内置泛函清单与 VDW_POTENTIAL（批次 12，补全 §1/§4）

### 27.1 `&DFT &XC &XC_FUNCTIONAL` 内置泛函名（对照 2026.1 `cp2k_input.xml`）
CP2K 把常用泛函做成**内置名**，直接写 `&XC_FUNCTIONAL <NAME>` 即可（无需拼 LIBXC）：
- 局域/半局域：`LDA` / `PADE`(=PBE 的 LDA 关联，CP2K 里 `PBE` GGA 的关联用 PADE 内核) / `PBE` / `BP86` / `BLYP` / `OLYP`。
- Meta-GGA：`TPSS` / `SCAN` / `RTPSS` / `MVS` / `KCIS` 等。
- 杂化：`PBE0` / `B3LYP` / `BEEFVDW`(带 vdW 的 BEEF) / `HSE06`(需 `&XC &HF` 加 `@HSE06` 或 `&XC_FUNCTIONAL HSE06` + `SCREENING`)，`HSE06` 经 `--xc hse06` 已在模板内置。
- 其它：`revPBE` / `RPBE` / `SRPBE` / `PBEsol` 等。
- 低保真/测试：`LIBXC`(任意 LIBXC 泛函，需手填 exchange/correlation 子节)。
> 选泛函的决策仍见 §1；这里给的是**CP2K 里的写法**。推荐工作流：**PBE 起步 → TPSS/SCAN 精修 → HSE06/B3LYP 终能**（§1）。

### 27.2 `&DFT &XC &VDW_POTENTIAL`（色散修正，补全 §4）
§4 只写了「DFT-D3 用 `--dispersion D3`」。权威结构如下：
- `POTENTIAL_TYPE`：总开关（`PAIR_POTENTIAL` / `NON_LOCAL` / `GCP_POTENTIAL` 等）。
- **`&PAIR_POTENTIAL`**（pair-wise 色散，DFT-D2/D3/D3(BJ)）：
  - `TYPE`：`DFTD2` / `DFT-D3` / `DFT-D3(BJ)` / `DFTD3`(零阻尼) 等。
  - `REFERENCE_FUNCTIONAL`：指定参考泛函以自动取参数（如 PBE、TPSS、B3LYP）；CP2K 据此设 s6/sr6/s8。
  - `SCALING` / `D3_SCALING`：缩放因子（s6,sr6,s8）；设为 0 让 CP2K 从参考泛函猜。
  - `PARAMETER_FILE_NAME`：参数文件名（D3 自带 `dftd3.dat`，通常不用手指定）。
  - `R_CUTOFF`：截断（**实际势截断 = 2 × 此值**，官方描述 "The cutoff will be 2 times this value"）。
    **官方默认 `10.5835 Å`（= 20 bohr）** ⇒ 默认实际截断 **21.17 Å**；课程常用的 **15 Å 是自设值、不是默认值**
    （与 §4.1 同条，`videonotes/cp2k-4-…-精读笔记 L1779–L1786 [150:11–150:59]`）。`EPS_CN`(D3 配位数截止)。
  - `CALCULATE_C9_TERM`：**官方默认 `F`** —— 讲师说"C9 项加不加都可以，加了之后会影响计算量、稍微大一些"
    ⇒ **不写就是不加**，要加才显式 `T`（`_kw_probe.py --find CALCULATE_C9_TERM`）。
- **`&NON_LOCAL`**（非局域 vdW，vdW-DF 族）：`TYPE`(`vdW-DF`/`vdW-DF2`/`optB88-vdW`/`rVV10` 等，需配对应 XC_FUNCTIONAL)；`KERNEL_FILE_NAME`(`vdW_kernel_table.dat` 或 `rVV10_kernel_table.dat`)；`CUTOFF`(FFT 网格 [Ry])；`PARAMETERS`(rVV10 的 b、C)；`SCALE`。

> 实战推荐：`--dispersion D3`（= `&VDW_POTENTIAL &PAIR_POTENTIAL TYPE DFT-D3(BJ)` + `REFERENCE_FUNCTIONAL` 按所选泛函）；需要 vdW-DF/rVV10 等非局域修正时手动加 `&NON_LOCAL`，并确认 XC_FUNCTIONAL 与其匹配（如 optB88-vdW 配 `XC_FUNCTIONAL` 用 `PBE` 内核 + `NON_LOCAL optB88-vdW`）。

---

## 28. 庚子计算讲师实操硬规则（PDF/字幕内化，批 13）

> 来源：庚子计算《AIMD 与 CP2K》5 天课程（PDF+字幕）逐页内化，详见 `references/course_learned.md`。
> 这些是讲师"怎么真正跑对"的**经验级硬规则**，手册不写、但错一次代价很大。提升自 `course_notes.md` 的 B1/B2/B3，补入本库作为默认动作。

### 28.1 DFT+U —— 强关联过渡金属氧化物"必须加"（硬规则）
- **规则**：含强关联 TM（Ti³⁺/⁴⁺、Fe²⁺/³⁺、Co、Ni、Mn 等）的氧化物/硫化物/钙钛矿，**默认加 DFT+U**，即使减速也要加。
- **为什么**：不加 U → 电子不能局域在金属离子上 → 四价 Ti 不被还原、表面吸附物电子转移模拟错误、**定性错误**（不是精度问题）。
- **怎么加**：`--kinds "Ti:DZVP-...:GTH-PBE-q12:U=4"`（默认 `PLUS_U_METHOD MULLIKEN`、**`gen_inp` 发射 `L 2`**、`U_RAMPING` 渐进加 U 助收敛；Au-TiO₂ 的 Ti 若不要 ramping 加 `noramp`）。
  > ⚠️ **措辞要紧**：`L 2` 是**本工具发射的值**，**CP2K 自己的 `L` 默认是 `-1`**
  > （`FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U/L`，9.0 与 2022.1 一致）。
  > 本行与 `course_notes.md:94` 原先都写成"`L` 默认 2"，会被读成 CP2K 默认值 ——
  > 2026-10 由 `_audit_claims.py` 自动核对时抓出，已就地限定来源。
- **落点与关键字名（批 15 用官方 XML 钉死）**：`&DFT_PLUS_U` 在 **`&FORCE_EVAL/&SUBSYS/&KIND/&DFT_PLUS_U`**（**逐 KIND**，
  挂在每种元素下），**不是** `&FORCE_EVAL/&DFT/&DFT_PLUS_U`、**也不是** `&DFT/&QS` 下（后两个都查不到）。
  段内共 5 个关键字与官方默认：

  | 关键字 | 官方默认 | 单位 | 说明 |
  |---|---|---|---|
  | `L` | **`-1`** | — | 加 U 的角动量：**手写输入卡必须自己写 `L 2`（d）/ `L 3`（f）** |
  | `U_MINUS_J` | **`0.0`** | **hartree** | ★ 这就是"**有效 U = U − J**"的正式关键字名 |
  | `U_RAMPING` | **`0.0`** | **hartree** | 每步增量（渐进加 U） |
  | `EPS_U_RAMPING` | **`1.0E-005`** | — | 收敛到什么程度才开始加 U |
  | `INIT_U_RAMPING_EACH_SCF` | **`F`** | — | 每个 SCF 重新起步加 U |

  （`_kw_probe.py --section FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U`；
  `videonotes/cp2k-4-…-精读笔记 L1803–L1842 [151:34–154:47]`；H 层真实算例写法 `U_MINUS_J [eV] 13.6`）
  > 📌 **更正记录一（关键字名）**：`videonotes/cp2k-4-…` 的 §15.2 标题与错字对照表把有效 U 写成 **`U_EFFECTIVE`**
  > —— **官方 XML 里 `U_EFFECTIVE` 0 命中**（本轮已复现），**是概念名/口语名，不是关键字**。
  > 本库 A/D/G 层此前用的都是正确的 `U_MINUS_J`，**只需拒绝这个名字**。
  > 📌 **更正记录二（"`L` 默认 2"）**：本行原写"`L` 默认 2"，那指的是 **`gen_inp.py` 发射的默认值**（d 轨道），
  > 容易被读成 CP2K 默认。**官方默认是 `L = -1`** ⇒ 手写输入卡时**必须自己写 `L 2` / `L 3`**。
  > 📌 **更正记录三（`EPS_U_RAMPING`）**：现有 A/F 层把"收敛到 10⁻³ 之前不加 U"写成**通用规则**，
  > 实际那是**课程模板的取值**（课程算例与讲义都显式写 `EPS_U_RAMPING 1.0E-3`，`L3.txt:2381`、H 层 `cases/TiO2-Au20_cp2k.inp:125`）；
  > **官方默认是 `1.0E-005`**。⇒ 表述应写成"课程模板取 1E-3（更晚才启动加 U、对收敛更友好）；官方默认 1E-5"。
  > 📌 **更正记录四（落点）**：G 层 `official/20_input_reference_tree.md:385` 的 FAQ 行把它写在
  > `&FORCE_EVAL/&DFT/&QS/&DFT_PLUS_U` —— **那一行是 G 层自己写错了**（官方 XML 查得到的是 `&SUBSYS/&KIND/&DFT_PLUS_U`）。
  > 「A–F 与 G 冲突以 G 为准」这条规则在这里**必须反过来用官方 XML 纠正 G** —— G 层修正归 G 层 owner。
- **单位天坑（比原来记的更宽）**：`&DFT_PLUS_U` 里的 **`U_MINUS_J` 与 `U_RAMPING` 默认单位都是 hartree**，
  **凡是以 eV 思考的数都要写 `[eV]`**：
  - `U_MINUS_J 13.6` 不带单位 = **13.6 hartree ≈ 370 eV**（不是 13.6 eV）；
  - `U_RAMPING 0.1` 不带单位 = **0.1 hartree ≈ 2.72 eV** ⇒ 一步就把 U 拉满，"约 40 个电子步线性加到 4 eV"的设计**完全失效**。
  （官方 `<USAGE>` 明写 `U_MINUS_J [eV] 1.4`、`U_RAMPING [eV] 0.1`；`_kw_probe.py --find U_RAMPING`；
  `videonotes/cp2k-4-…-精读笔记 L1836–L1842 [153:52–154:47]`）
  > 📌 **更正记录**：本行原写"`&DFT_PLUS_U U` 的单位**必须写 `[eV]`**；默认 a.u.（≈27 eV 量级）会差 ~27 倍" ——
  > 方向正确，但 ① 关键字名写成了 `U`（官方名是 `U_MINUS_J`）；② **只提了 `U_MINUS_J`，漏了 `U_RAMPING` 同样需要 `[eV]`**；
  > ③ "27 倍"是 `hartree → eV` 的换算（**27.211**），而讲师口播的"每步 +0.1 eV"只有在带 `[eV]` 时才成立。以上三点本轮一次改齐。
- **例外**：金属单质 Fe/Ni 一般**不用** U（已足够局域）；金属正离子态才必须。
- 详见 `course_learned.md §4.5`、`decide.md §1`（泛函选择时同步决策）。

### 28.2 BSSE 警示 —— 高斯基组吸附能"偏大"（硬规则，已溯源到讲义）
- **规则**：CP2K 用高斯基组 → 有 **BSSE（基组叠加误差，Basis Set Superposition Error）**，算**吸附能/结合能会高估**（多数情况比 VASP 算的大一点）；基组越小 BSSE 越大。
- **机理（为什么一定有，讲义原文 L3 P40）**：平面波程序只要 `ENCUT` 相同，不同体系用的基组就**是同一套**；而**高斯基组是"跟着原子走"的**——算 A 体系和 AB 体系用的基组不一样。AB 体系里 **B 的基组也参与描述 A 原子**，等于 A 偷用了 B 的函数，于是 **AB 的能量被额外降低（偏负）**。写成 `E(AB) − E(A) − E(B)`，结果必然**偏负** ⇒ 结合/吸附被**高估**。
  > 一句话：BSSE 不是"误差算错了"，而是**基组不完备导致的系统性偏差**，方向是"结合偏强"。
- **量级（讲义 L3 P41–P42 原文**逐字**，⚠️ 两处基线不同、不可混用）**：
  - **P41**（针对实际体系的经验值）："我们文献中最常用的 **DZVP 基组的 BSSE 误差约为 5 kcal/mol ~ 0.22 eV**。"
  - **P42**（文献基准集实测，另一套基线）：`DZVP-MOLOPT-SR-GTH` vs `DZVP-MOLOPT-GTH` 的 BSSE 为
    **0.32 / 0.16 / 0.31 / 0.24 ← 0.23 / 0.11 / 0.41 / 0.20 kcal/mol**（四个测试例）。
  - ⚠️ **讲义自身两页口径不一致**：P41 的"5 kcal/mol"与 P42 的"0.23–0.41 kcal/mol"相差约 20 倍，
    显然不是同一类体系/同一个量。**引用时必须写明是哪一页、哪套基线**，不要拼成一句话。
  - ⚠️ **不要引用讲师的"≈1 eV"**：字幕 `S3.txt` 2345 行讲师口述"差不多有一个电子伏特左右"，
    与上述任何一套原始数据都差 5 个数量级（1 eV ≈ 23 kcal/mol）。**该数字无出处、不得写入判据。**
  - ⚠️ **"~50%" 是讲义的粗略说法，与其自身数据不完全吻合**：按 P42 四个测试例算，
    变化为 **+39% / +45% / −24% / +20%**（其中一例反而**减小**），均值约 +20%。
    故只能说"**SR 基组的 BSSE 通常会变大，量级在几十个百分点**"，不要当成确定倍数。
- **SR 的取舍（讲义 L3 P42 + 字幕 S3.txt 2320–2359）**：`SR` = **short range**，砍掉部分**弥散基组**贡献，
  对材料性质计算影响很小，**计算速度提升 2–3 倍**（讲义例：64 分子盒子 **25 s vs 111 s**）。
  **AIMD 场景应选 SR** —— 讲师原话："做 AIMD 都是倾向于牺牲一点点精度，把速度提上来"。
  > 判据：**AIMD/大体系 → 选 SR**（速度优先，BSSE 在动力学平均里影响小）；
  > **精确静态吸附能/结合能 → 用非 SR 大基组，或做 BSSE 校正**（见下"应对"）。
- **对照**：平面波程序（VASP）无 BSSE（趋于完备基组极限）。
- **判读**：看到"CP2K 算的吸附能比文献/VASP 偏大"**不要先当成算错了**——先想 BSSE。
- **应对**：① 大规模动态（AIMD）用 CP2K（绝对优势，BSSE 在动力学平均里影响较小）；② 精确静态（吸附能/反应能/过渡态）换平面波，或**加大基组 / 做 BSSE 校正**（CP2K `&BSSE` 或 counterpoise 双片段计算）；③ 跨程序对比时显式标出 BSSE 量级。
- **溯源（已核实，2026-10）**：
  - **讲义 `L2.txt` P33**（讲师"优缺点"页，原话）："对导体计算较慢 / 对于磁性体系处理比较麻烦 / K 点功能不完善 / **高斯基组带来巨大的 BSSE，基组不完备误差，不适合计算结合能**。VASP 使用平面波基组就不存在这个问题。"
  - **讲义 `L3.txt` P40–P42**：BSSE 定义（"基组跟着原子走"）、DZVP 量级、SR 基组实测数据 —— 最权威的量化出处。
  - **字幕 `S2.txt` 2972–3019**：讲师归纳的"CP2K 第 4 个缺点"（含"CP2K 基组比较小所以误差比较大""多数情况比 VASP 稍大一点"）；**4496–4529** 学员问答给出 BSSE 校正做法与"精度要求高才做"的判断。
  - **字幕 `S3.txt` 140–169**：用 `grep` 官方 `tests/` 目录学 `BSSE`/`FRAGMENT` 关键词的方法；**2343–2345**：SR 基组 BSSE 增大 ~50%、约 1 eV。
  > **更正记录**：旧版本此处标注"PDF/字幕全文检索零命中、未能溯源"。那是**搜错了文件**——只检索了 `L4.txt`/`4.txt`，而 `course_survey.md` 又把 BSSE 误归给"第 4 天"，于是得出错误结论。实际 BSSE 出现在 **L2 P33、L3 P40–P42** 与**第 2、3 天字幕**共 19 处以上。归属已在 `course_survey.md` 更正。
- **MOLOPT 基组出处**（讲义 L3 P42）：`Phys. Rev. B` **54**, 1703 (1996) —— molecularly optimized basis functions。
- 与 `decide.md §16`（方法选择）、吸附能/结合能判读联动。

### 28.3 OT vs 对角化 —— 讲师实战佐证（硬经验）
- 对角化是传统法（VASP 也用），速度慢，但对**金属体系**在 CP2K 里尚可；OT 是现代默认、快。
- 金属/窄带隙 **必须走对角化 + SMEAR**（OT 不支持金属/k 点/取 MO，见 §22.2）。
- 收敛辅助：对角化里常用 `EPS_DIIS` 配 `&DIAGONALIZATION`；OT 不收敛先换 `MINIMIZER CG/BROYDEN`（§12）。
- 另两条 PDF 独有约束：**ASPC 初猜不能配 K 点**；**DFT+U 一般只在 OT 路径**（与 §22.2、§4.2 一致）。

> 与 `course_learned.md` 关系：28.1/28.2/28.3 是"该怎么做"的硬规则；完整公式/脚本/数值案例见 `course_learned.md` 第 4/5/6/7 节。
> 批 14 新增的三节（§29 AIMD 统计与重复性、§30 建模硬规则、§31 方法选择清单）见下。

---

## 29. AIMD 的统计、重复性与可复现性（批 14，新增章节）

> 出处：讲义 `L1 P24–P26`；字幕 `S1.1.txt:1880–2016`。
> **为什么单立一节**：现有文档（含 `playbook.md` §5.6）只有"MD 是混沌体系、要多副本"这一句结论，缺四件事——**为什么必然不同、随机数从哪来、多副本必须随机化什么、只有一条轨迹时文章怎么写**。
> 分工：**本节写"决策与理由"**；症状/数值速查见 `playbook.md` §5.6；步长/热浴参数见 §13。

### 29.1 "同输入跑两条 30 ps 结果必然不同"是正常的
- AIMD/MD 是**混沌体系**：对某个原子"给它一个非常非常微小的改变，那么在……一定的时间之后，这个体系都会变得完全不一样"——即**蝴蝶效应**（`S1.1.txt:1886–1899`）。
- 更关键：**哪怕不引入任何随机数**，"浮点精度的一些变化都会影响到整个计算结果"（`S1.1.txt:1900–1903`；讲义 `L1 P24`："MD 模拟具有很强的混沌效应，再加上一些浮点精度偏低，哪怕不用随机数，两次模拟的结果都有可能不一样"）。
- ⇒ **两个完全相同的输入各跑 30 ps，结果不一样，"这个事情是非常正常的"**（`S1.1.txt:1909–1913`）。**不要当成 bug，也不要为此去调并行核数/换初猜。**
- 真正要警惕的是反面：只分析**一次**模拟，"有可能落到了小概率事件上，从而得出错误的结论"（讲义 `L1 P24`）。

### 29.2 多副本：**必须同时随机化"初始坐标"**
**随机数有三个来源**（讲义 `L1 P25`；字幕 `S1.1.txt:1956–1990`）：

| 来源 | 是否引入随机数 | 说明 |
|---|---|---|
| **初始速度** | ✅ 是（CP2K 默认已随机给定） | "CP2K 的 AIMD 初始速度是随机的"（VASP 同理） |
| **初始坐标** | ❌ 否（**要自己随机化**） | "初始坐标可以自己通过编程做随机数处理" |
| **热浴** | ⚠️ 看选哪个 | **Anderson 热浴引入随机数；Nosé–Hoover 热浴不引入随机数** |

- **硬规则**：**做多条轨迹时，必须把初始坐标也随机化。** "如果我们这 100 条轨迹全都给一样的初始坐标，那这个时候初始坐标有可能会影响到我们后面模拟的轨迹，那么做了 100 条轨迹、拿到的统计性质可能就是有偏差的"（`S1.1.txt:1967–1979`）。
  ⇒ **只随机初始速度、不随机初始坐标的多副本，统计是有偏的**——这是"跑了 100 条还是被审稿人挑"的常见根因。
- **例外（要反过来做）**：模拟**非平衡过程**（如单向的化学碰撞反应）时，**应人为限定初始速度/坐标**，不能随机（`L1 P25`）。
- **多副本能回答单条轨迹回答不了的问题**：讲师例——质子在水分子间传递，可能由 1/2/3/4 个水分子参与，"这么四种反应方式到底哪种的概率大，单条轨迹模拟是完全得不出结论的"；作者做了约 **100 条**轨迹才得到概率分布（结论：**2 个水分子参与的概率最大**）（`S1.1.txt:1991–2016`；讲义 `L1 P26` 引 *J. Am. Chem. Soc.* 2016, 138(35), 11164-9）。

### 29.3 只有一条轨迹时，文章怎么写
- 大体系（1000 个原子、几千个原子）**单条轨迹也能发文章**——"由于 AIMD 计算量的限制，我们没有办法再去做多条轨迹……这个时候审稿人大概也会知道我们这个计算量有一个限制，所以说也会默认就通过了"（`S1.1.txt:1936–1955`；讲义 `L1 P24` 同口径）。
- ⇒ **决策**：**小体系走多副本 + 统计平均；大体系允许单条轨迹，但要在文中显式说明计算量约束**，并优先报告**统计平均过的量**（RDF、MSD、时间平均）而不是单帧结构。
- **预平衡段要丢弃**：CP2K 侧常见做法是**丢掉前 500 步**再统计温度/势能曲线与 RDF（`S4.txt:2597–2622`、`3681–3684`）。但"丢前 5 ps / 前 2 ps / 前 1 ps"**没有硬规定**——判据是**把势能图画出来看它稳不稳**："其实这个到底是舍弃前五皮秒呢，还是舍弃前两皮秒、还是舍弃前一皮秒，这东西没有什么严格的说法……因人而异，对不同的体系用不同的处理方法就可以了"（`S1.2.txt:1072–1098`）。

---

## 30. 建模硬规则（批 14，决定成败的前置判断）

> 出处：字幕 `S2.txt:3062–4546`。这些是**参数之外的建模决策**——做错了代价最高（要重跑全部计算），所以必须在建模阶段就定下来。

### 30.1 密度建准 = 可以直接跳过 NPT 预平衡
- **规则**：建模阶段把密度算对（水体系就是 ~1 g/cm³，拿计算器按"分子质量 ÷ 晶胞体积"自己核），**就不必再做 NPT 预平衡**，直接 NVT 开跑（`S2.txt:3550–3587`）。
- **为什么值得**：AIMD 本身极耗时。"一开始我们还需要跑个 NPT……把它这个晶胞的体积跑合适了，然后再去跑 AIMD，这个时候是非常麻烦的"（`S2.txt:3566–3575`）。
- **报错信号**：**Packmol 里分子数填太多而报错 = 密度算错了**——"如果这里我们填 1 万个水分子，那这个程序肯定会报错，那这时候就说明我们这个密度没有算对，我们再去自己算一算，看这个密度是不是搞错了"（`S2.txt:3615–3625`）。**看到这个报错不要去调 Packmol 参数，回去核密度。**
- **补充**：分子数很少（如 30 个水）用 NVT；分子数很大（如 1000 个水）用 NPT 跑也没有问题（`S2.txt:3588–3594`）。

### 30.2 异质结：`mismatch tolerance` 一般 **2–3%**
- **规则**：上下两面的失配率**在 2% 或 3% 以内比较合理**；**超过 3%** 时模型虽然能建出来，**"但建出来之后，我们一优化，其中有一相就可能会崩塌掉，这个结构就会乱掉"**（`S2.txt:3917–3930`）。
- **例外**：**柔性材料（石墨烯、g-C₃N₄ 这类可弯曲性好的）容忍度更大**（`S2.txt:3931–3938`；文献实例见 `playbook.md` §0.8）。
- **这里有一个取舍，不是"越小越好"**：失配率卡得越死，找到的**晶胞往往越大**，"这个很大的晶胞对于我们计算来说是不太有利的"⇒ **适当放宽失配率可以换到更小的晶胞**。实操顺序是**先输小失配率去找**（"先输入个小一点的 mismatch，如果小 mismatch 找不出来，我们再扩大允许的适配率"）（`S2.txt:3943–3996`）。
- **固–固堆叠的前提**：两个结构的 A/B 边长必须先调成一致——"一定要把这两个数值设置成和我们刚才那个表面**一样**，这样才能把这个模型建立起来、能够摞起来；如果数值不一样，那就没有办法建立这个界面了"（`S2.txt:4215–4229`）。

### 30.3 真空层一般 **15 Å**
- 切完 slab 后加真空层，"一般要留 **15** 是比较好的"（`S2.txt:3959–3965`）；表面练习里同样"现在加个 **15 Å** 的真空层"（`S2.txt:4427–4429`）。
- **联动**：二维材料做 `CELL_OPT` **必须加 `CONSTRAINT Z`**，否则"优化一会儿真空层就消失掉了"（**§18.1** 第 3 条）。

### 30.4 六方四指数晶面在 Materials Studio 里**只输三个指数**
- "四指数晶面呢，在 MS 里只输入三个指数，其中第三个指数这里是不输的，因为第三个指数正好等于前两个指数的加和"——**六方密排四指数晶面只要输入三个指数就可以了**（`S2.txt:3786–3793`）。
- 例：Al₂O₃ 最稳定表面是 `0001` 面，在切表面对话框里**写三个数字**（`S2.txt:3780–3784`）。

### 30.5 六方 → 正交的晶格矢量配方：**新 A = 2a + b**
- **适用场景**：要把六方材料（MoS₂ 等，夹角 60°/120°）与正交材料（黑磷等，90°）摞成异质结，**必须先做晶格矢量旋转把它变成正交**——"想要直接去摞肯定是不可能的，肯定是要对这个晶格矢量进行旋转……把它也变成一个正交的，然后才能把它给摞起来"。这就是 MS 建异质结的**核心思想**（`S2.txt:3877–3897`）。
- **具体配方**：MoS₂ 转正交，**新 A = 2a + b，B 不变**——"A 乘以二，两倍的 A 加上一个 B，这就有了新的大 A 了；这个 B 不用变"；在 MS 的 `Build → Symmetry → Redefine Lattice` 里输入 2（代表两个小 a）加一个小 b 即可（`S2.txt:4036–4076`）。
- **为什么必须做（后处理也会被卡住）**：**VMD 无法对非正交晶胞施加 PBC**，六方体系直接拿 VMD 算 RDF 会出错（`playbook.md` §1.4）。而六方与正交材料摞异质结又**必须先转正交**（`S2.txt:3880–3897`）。⇒ 这条既是建模决策，也是**后处理能不能进行的前提**。
- 文献里的 `√3 × √3 R30°` 之类记号，本质就是"对晶胞矢量做旋转 + 边长变成 √3 倍"（`S2.txt:4026–4035`）。

### 30.6 MS `Build Layers` 会主动留空隙 → 水密度偏小
- 界面摞起来之后，"MS 会特意地在这个水层和这个金属层之间**留出一定的空隙**"；**想要 1 g/cm³ 的水，必须把空隙调掉**——做法是把水分子朝表面平移一点，再把 c 轴改小（例 13.3/19.35 → 更短）后重建晶胞，"这样可以保证它的水分子的密度保持在一个比较合理的一克每立方厘米"（`S2.txt:4259–4288`）。
- **判断**：**摞完界面后必须重新核一遍水层密度**；只信 MS 的默认输出会拿到偏稀的水（水偏稀会让后续 RDF/扩散系数整体偏移）。

### 30.7 建模信息从哪来：先问"实验测到了什么"（批 15）

> 出处：`videonotes/cp2k-1-1-AIMD第一讲-精读笔记 L207–L227 [18:50–20:30]`。本节 §30.1–§30.6 都是操作规则，
> 这里补的是**前置问题：初始结构的结构信息本身从哪来**。

- **结构信息来自实验表征，不是凭经验拍脑袋**：**XPS** 给价态/配位信息；**TEM（尤其 HAADF 高角环形暗场）**
  给"非常清晰的原子级成像照片"；**XRD、XAS/EXAFS** 同样提供建模所需的键长/配位/晶格信息。
  讲师典型例：石墨烯上四个氮配位一个金属原子（单原子催化）。
- **配套观念（决定"能不能算"的边界）**："任何实验能测的性质理论都能算，差别只在理论完善程度、方法好用程度与**可行性**"；
  而"**有了几何结构的模型，我们才能去研究下面的性质……说白了就是结构影响性质**"。
  ⇒ **顾问动作**：用户拿来一个课题时，**先问"有没有 XRD/TEM/EXAFS 的实测结构信息"**；
  没有实测结构时，只能走本节下文那条"理论先设计、实验后验证"的路。
- **另一条合法路径：从均相催化剂出发设计异相催化中心**——"从（均相）催化剂出发，去找它的一个均相合成中心 ——
  **把均相催化和异相催化结合起来了**"；现状是"现在这个纯理论计算的文章有很多……**自己去设计这个催化中心，
  然后再让实验科学家去验证**"（`videonotes/cp2k-1-1-…-精读笔记 L264–L274 [22:27–23:23]`）。
  ⇒ 建模阶段就要明确：**这个模型是"复现实测结构"，还是"理论预测的新结构"** —— 两者的验证策略与写作口径不同。

### 30.8 模型简化三步法（上万原子 → 几十原子，判据是"参不参与反应"）

> 出处：`videonotes/cp2k-1-1-…-精读笔记 L229–L262 [20:30–22:27]`（引语见 L248/L256/L257/L258）。

**问题**：真实催化体系"可能有上万个原子，这个时候去算的话可能会比较费劲"（L248）。
**判据**：① **参与不参与反应**；② **反应是否局域**。**三步**：

| 步骤 | 动作 | 讲师理由（逐字） |
|---|---|---|
| ① **删掉载体** | 例：去掉 SiO₂ 载体 | "这个 SiO₂ 的载体，它是不参与到这个催化反应当中的，所以说有没有它对于我们整个计算是没什么影响的" |
| ② **大颗粒换成表面** | 例：大块金属颗粒 → (111)/(110) 表面 | "催化反应一般都是发生在一个很局域的一个位置……那无非就是（金属）的一些表面" |
| ③ **落到几十个原子** | 表面 + 单原子 + 配位原子 | "建立这个 (111) 表面，然后负载一个单原子，然后有氧配位，然后去做这种催化反应" |

- 目标是两全："让我们这个计算可行、又可以真实地反映出来这个实验的性质"，手段是"**把这个次要的信息给它删掉**"。
- ⚠️ **元素指代存疑，落层时不要写死**：该例转写里"薄/铅/铁"混用，E 层 `MAPPING.md:172` 写"铁/Pt 111"自相矛盾，
  笔记 `L1186` 自标"未确认" ⇒ **记为"金属（Pt 或 Fe，原转写不清）"**。
- **与 §30.1–§30.6 的分工**：那六条讲"怎么切、怎么摞、密度怎么核"，这条讲"**该不该砍、砍什么**"——
  砍错方向的代价最高（要重跑全部计算）。

### 30.9 "slab 要不要固定底层"：终止面是金属/不饱和时**不能固定**（反例，批 15）

> 出处：`videonotes/cp2k-3-…-精读笔记 L1510–L1515 [139:31–140:36]`；对照同一讲 `L1234` 的"表面体系下面两层还是要固定的"。

- **默认规则（本节上文 + `workflow.md`）**：表面 slab 固定最下 1–2 层，**目的是防止整个体系整体平移**
  （不固定则"slab 模型可能整体地往上偏、往下偏，或者是给歪掉了"，对后续所有分析不利）。
  ⚠️ **"固定层"往往要固定两族原子**（讲师实例同时固定 `LIST 1..54`（最下两层 O）与 `LIST 289..324`（最下两层 Ce））
  —— **这些序号是该体系特有的，不要当通用阈值**（`videonotes/cp2k-4-…-精读笔记 L1148–L1163 [89:20–90:56]`）。
- **反例（本讲算例二，Al₂O₃ 暴露面）**：**刻意不固定任何原子**。理由——"**它的下表面是铝暴露的这个表面** ——
  对于这种金属暴露的表面，它可能会发生比较强烈的重构……**如果这个时候给它把底层的原子给它固定住，
  那这个时候可能会产生不合理的这个电荷分布在这里** —— 因为这个铝是不饱和的这个位置"。
  实测现象："铝离子都会**陷进去**了……优化前后结构变化非常明显"。
- ⇒ **判据写成一句话**：**终止面是金属 / 配位不饱和（有强重构倾向）⇒ 不固定，让它自由重构；
  终止面是饱和氧化物 / 金属密排面 ⇒ 固定最下 1–2 层防漂移。**
  两者在同一门课里并存但**不矛盾**（Cu(111) 金属 slab 固定；Al 暴露的氧化物表面不固定）。
  > **固定原子的序号怎么读（操作细节）**：序号就是 **xyz 文件里的行号**（讲师："第一行这个铜是第 **93 行**；
  > 下面这一行铜……是第 **124 行**……把这两个数字改成 **93 到 124**"）。所以先用
  > **`-s` 开关按 Z 方向重排原子顺序**（"改变它的原子顺序"是 xyz 相对 CIF 的独有好处），
  > 再写连续的 `LIST 93..124` 就很容易；不重排则坐标"乱排"，只能"一个一个地去看它的原子编号"
  > （`videonotes/cp2k-3-…-精读笔记 L1156–L1163 [97:25–98:11]`、`L1202–L1230 [107:23–110:40]`）。
  > ⚠️ 该重排脚本在 E 层有两种转写（`demcar2xyz.py` 与 `MS_car_to_XYZ.py`），**脚本名归 C 层错字表并列**，本层不裁定。
- **配套操作**：不固定原子的算例改用 `&TOPOLOGY COORD_FILE_NAME <file>.cif` + `COORD_FILE_FORMAT CIF`
  读结构（"因为我们这里不固定原子，不固定原子无所谓了，就用这个 CIF 文件"），**同时必须把 `&COORD` 那几行注释掉**
  （`videonotes/cp2k-3-…-精读笔记 L1517–L1520 [140:46–141:30]`、`L1236–L1252 [111:49–114:07]`）。

### 30.10 三维周期性体系带净电荷 ⇒ 强制引入**均匀背景电荷**

> 出处：`videonotes/cp2k-3-…-精读笔记 L442–L466 [33:36–35:38]`。这是本讲唯一一条"物理级"的建模坑。

- **规则**：**周期性体系尽量把 `CHARGE` 设成 0**（官方默认就是 `0`）。若给周期性体系一个净电荷，
  程序会**强制加一个均匀背景电荷来中和**："如果我们这个体系是带正一，那它就会在这个背景加上一个负一电荷，
  以中和这个体系的这个总的这个电荷"。
- **为什么必须知道**：原因是镜像——"在上下左右前后六个方向上都有它的镜像……整个体系其实是带一个**无限大的正电荷**"；
  ⚠️ 而"**这个背景电荷有的时候会对我们这个计算产生一定的影响**"。
- **对策（按优先级）**：① 体系做成电中性；② 做不成 0 就**加抗衡离子**——"比如说我们要模拟一个酸性溶液……
  引入一些氯离子之类的，那这样呢把这个电荷给中和掉"。
- **落层理由**：全库此前搜 `背景电荷|抗衡离子|jellium` **无实质命中**；
  而这条直接改变"能不能算、要不要加离子"的建模决策（比参数调优优先级更高）。

---

## 31. AIMD 方法选择清单：必须加 / 最好别加（批 14）

> 出处：`S1.2.txt:640–716`、`S4.txt:2427–2467`、`3360–3375`、`4244–4298`、`4302–4522`、`S3.txt:2046–2067`。
> **这一节的优先级高于任何性能调优**：它管的是"结果对不对"，不是"跑得快不快"。

### 31.1 总原则：AIMD 牺牲精度换速度；静态计算反过来
- 讲师原话："在我们做 AIMD 模拟的时候，我们一切的参数设定都是倾向于**以牺牲少部分的计算精度来提高计算速度**，这么一个理念去调节参数的。在我们做静态计算，比如说结构优化、过渡态搜索的时候，一般来说我们调参数的这个思想，都是以**牺牲一定的计算速度来增加计算精度**"（`S1.2.txt:640–652`）。
- ⇒ **这条是本节所有条目的裁决原则**：同一个参数在 AIMD 与静态计算里可以取不同值，**不要用同一套参数跑两种任务**（§22.7 的 `EPS_SCF` 就是典型例子；§28.2 的 SR 基组取舍同源）。

**"什么问题上 AIMD"——一段可直接引用的价值对照**（讲师用氢分子/氧化铝载金属团簇的例子，`videonotes/cp2k-1-1-AIMD第一讲-精读笔记 L289–L294 [24:16–25:00]`）：

- **静态路线**（结构优化 → 中间体能量 → 过渡态搜索）"只能得到一个氢分子吸附它的能量，然后解离它的能量，
  然后**它就没有什么更多的信息了**"。
- **AIMD** 给的是**动态过程**："这个氢气分子，当它要撞击到氧化铝表面的时候，**它是不发生任何反应的**；
  但是当这个氢气分子靠近（负载的金属三原子）团簇中心的时候，**它会瞬间发生了解离，发生解离吸附，变成两个氢原子**"。
- ⇒ 讲师结论："**实际我们在做科研的时候，肯定是两者相辅相成，都是要研究的。**"
  **判据**：当问题涉及"**路径上会不会发生某件事 / 什么时候发生 / 哪个物种先动**"时，静态计算答不了，必须上 AIMD；
  只要"起点、终点、鞍点的能量差"时，NEB/TS 更便宜（§17.1、§20.1）。

### 31.2 什么可以加、什么最好别加（AIMD 专用）

| 项 | AIMD 里 | 理由（讲师口径） |
|---|---|---|
| **DFT-D3 色散** | ✅ **可以加，几乎不增加耗时** | 经验泛函，"零点几秒或者 0.0 几秒之内就完成"（`S1.2.txt:662–669`；细节见 §4.1） |
| **表面偶极校正**（CP2K `SURFACE_DIPOLE_CORRECTION`；VASP 的 `LDIPOL`/`IDIPOL`） | ❌ **最好别加** | "加了这个东西的话，会使得 SCF 迭代收敛速度大大地降低"；**做功函数、静电势的时候才加**（`S1.2.txt:654–661`；用法见 §5 表面偶极修正段） |
| **DFT+U** | ✅ **强关联 TM 氧化物必加** | 不加是**定性错误**（§28.1）；判据见 §31.3 |
| **2 fs 步长** | ❌ **含氢体系禁止** | 会把 O–H 键震断（§13.1） |
| **把重原子质量改小** | ⚠️ 探索手段，讲师自称"存疑" | 见 §13.1 的风险分级 |

### 31.3 何时加 DFT+U（判据一句话）
- **判据**：**过渡金属化合物中金属以正离子态存在 ⇒ 必须加**；**金属单质（Fe 金属、Ni 金属）不用加**——"对于金属体系来说，它本来就是一个导体，在这个费米能级附近它都是有电荷密度存在的，并不需要强制地去加 U 把它的占据轨道和空轨道给他拉开"（`S4.txt:4244–4262`）。
- **不加的后果**：**低估带隙**，"甚至把一个半导体给算成导体"（`S4.txt:4250–4253`）；另一口径是"电子根本就不可能局域在这个金属离子之上……四价 Ti 不被还原"（`S1.2.txt:702–716`、§28.1）。**这是定性错误，不是精度问题。**
- **U 值不能跨程序搬**：VASP 的 U 拿来用没有参照价值；文献给 Ti 的 13.6 eV 是偏大的值，"正常对 Ti 加 **4~5 eV** 就差不多"（`S4.txt:2446–2467`；`playbook.md` §1.5）。
- **`U_RAMPING` 的节奏**：SCF 收敛到 ~10⁻³ **之前不加 U**，之后**每步 +0.1 eV**、约 **40 个电子步**加到目标值（`S4.txt:4266–4298`）。关键字写法与单位坑（**必须写 `[eV]`**）见 §28.1。

### 31.4 磁性体系：AIMD **一律按铁磁处理**
- **硬规则**：**做 AIMD 时把所有磁性体系都当成铁磁体系处理**。反铁磁（如 Fe₂O₃）、亚铁磁（如 Fe₃O₄）的自旋上下交替排列"会使得我们自旋这个迭代变得非常的慢、非常不容易收敛，影响我们计算速度"；而计算结果"**在能量上没有什么太大差别，可能就有个 0.0 几个电子伏特的区别**"（`S1.2.txt:673–695`）。这与 §31.1 的总原则一致。
- **但必须测试**：讲师明确要求"这个东西其实是需要测试的"——如果按反铁磁设置跑起来速度也 OK，那就用反铁磁参数（`S1.2.txt:696–701`）。
- **新版 CP2K 用 `MAGNETIZATION` 设初始磁矩**（老版没有这个关键字，只能用"非常复杂的老办法"）。用法与 VASP 的 `MAGMOM` 类似，**按 `&KIND` 给初始磁矩**；**初始磁矩不代表最终磁矩**，SCF 迭代中自旋态发生变化是正常现象（`S4.txt:4302–4340`）。
  - **语义（官方 XML 逐字，本轮补）**：`FORCE_EVAL/SUBSYS/KIND MAGNETIZATION` 默认 **`0`**，描述为
    "**Adds magnetization/2 spin-alpha electrons and removes magnetization/2 spin-beta electrons**"
    ⇒ **数值单位就是"未成对电子数"**（µB 口径，"加 magnetization/2 个 α 电子、减 magnetization/2 个 β 电子"）。
    这正好给 Fe₃O₄ 的 `4.0 / 5.0 / −5.0` 提供官方解释（Fe²⁺ 高自旋 4 个单电子、Fe³⁺ 高自旋 5 个单电子、负号 = 自旋向下）。
    （`_kw_probe.py FORCE_EVAL/SUBSYS/KIND/MAGNETIZATION`；`videonotes/cp2k-4-…-精读笔记 L1896–L1911 [158:23–159:24]`）
  - **配套写法**：要分开同一元素的不同价态/自旋，**必须在 inp 或结构文件里就把原子区分开**
    （讲师用 `Fe2`（二价铁 ↑）/ `Fe`（三价铁 ↑）/ `Fe3`（三价铁 ↓）三种标签），再写三个 `&KIND` ——
    "**虽然我们这个体系当中就是 Fe 元素，但是 Fe 元素里面有三种，就需要定义三个**"（同上；§31.5 已给拆分原则，这里补结构文件侧的标签写法）。
  - ⇒ **决策含义**：**简单体系（如 O₂）不设也能自动找到正确自旋态；复杂磁性体系（Fe₂O₃、Fe₃O₄）不给初始磁矩，"这个程序是绝对不可能找到一个正确的磁性的"**（`S4.txt:4325–4340`）。

### 31.5 用 `&KIND` 自定义标签拆同一元素的不同价态
- **技巧**：`&KIND` 后面**不一定写真实元素符号**——可写 `Fe2` / `Fe3`（讲师例 `Fe-2`、`Fe-3`），从而**对同一元素的不同价态分别设基组、赝势与初始磁矩**（`S3.txt:2046–2067`；`S4.txt:4408–4436`）。
- **典型用法（Fe₃O₄ 亚铁磁）**：二价铁（自旋向上）`MAGNETIZATION 4.0`、三价铁（自旋向上）`5.0`、三价铁（自旋向下）`−5.0`；体系里只有 Fe 一种元素，却要定义三个 `&KIND`（`S4.txt:4412–4436`）。
- **结果判读**：Mulliken 电荷 0.8/0.9 一类对应二价铁、0.93~1.0 对应三价铁——但**"原子电荷的数值并不是直接对应于它的价态的，我们可以对比它的相对值"**；自旋矩才是硬证据（二价铁 3.8、三价铁向上 4.2、三价铁向下 −4.1）（`S4.txt:4450–4483`）。**不要把 Mulliken 绝对值当价态用**（另见 §14 的选择原则）。
- **`&KIND` 可以多写、不能少写**：多写的不会被读、没有影响；**少写会直接报错**。所以建模后若打算再吸附 CO/水，**提前把 C/H 的 `&KIND` 一起写上**，避免返工（`S4.txt:2427–2445`）。

### 31.6 金属体系：对角化 + SMEAR 300 K
- 金属体系**用对角化比 OT 更好**——讲师在 Au/水体系上"两种方法都算过，后来发现对角化算得比较好"（`S4.txt:3360–3370`、`3528–3531`）；结论与 §22.2、§28.3 一致。
- **Fermi-Dirac smearing、电子温度 300 K** 是讲师模板值（`S4.txt:3371–3375`）；CP2K 一般只用 Γ 点（`S4.txt:3499–3501`，§5.2）。

### 31.7 杂化泛函：ADMM 让"几百原子 + 杂化 AIMD"变得可行，但 AIMD 默认仍是 PBE
- ADMM 辅助基组"可以做几百个原子的杂化泛函，可以把杂化泛函的速度做到和纯泛函的速度差不多，**甚至可以用杂化泛函去跑 AIMD**"（`S4.txt:4494–4502`）。
- **但**：纯 HSE06 太慢；"我们在做 AIMD 的时候……用得最多的还是 PBE 方案"（`S4.txt:4512–4522`）。⇒ **ADMM 是"想做杂化 AIMD"时的钥匙，不是"应该用杂化做 AIMD"的理由**（ADMM 配置见 §11）。

---

> **§29–§31 为批 14 新增**（来源：6 份字幕 `S1.1–S5` + 讲义 `L1 P23–P29`、`L2 P33`）。
> 分层指针：**决策与理由**在本文件；**症状→处方、报错、数值速查**在 `playbook.md`（§0.6–0.9、§1.1–1.5、§5.6）；**课程叙事、公式与脚本**在 `course_learned.md`。

