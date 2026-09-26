# 16 · QM/MM、嵌入方法与机器学习势（官方）

> **来源**：
> - <https://manual.cp2k.org/trunk/methods/qm_mm/index.html>
> - <https://manual.cp2k.org/trunk/methods/qm_mm/builtin.html>
> - <https://manual.cp2k.org/trunk/methods/qm_mm/gromacs.html>
> - <https://manual.cp2k.org/trunk/methods/qm_mm/polarizable_force_field.html>
> - <https://manual.cp2k.org/trunk/methods/qm_mm/implicit_solvation.html>
> - <https://manual.cp2k.org/trunk/methods/qm_mm/image_charges.html>
> - <https://manual.cp2k.org/trunk/methods/embedding/index.html>
> - <https://manual.cp2k.org/trunk/methods/machine_learning/index.html>
> - <https://manual.cp2k.org/trunk/methods/machine_learning/deepmd.html>
> - <https://manual.cp2k.org/trunk/methods/post_hartree_fock/index.html>
> - <https://manual.cp2k.org/trunk/methods/semiempiricals/index.html>
> **抓取日期**：2026-09-09

---

## 0. 本文件补什么

上一轮 `06_properties.md` §3 明确登记缺口："**QM/MM 的具体输入关键字应查官方 Input Reference；G 层未抓取该页面**"。本文件补齐 QM/MM 全家 + 嵌入 + 机器学习势。

**本轮实测页面状态**：

| 页面 | 状态 |
|---|---|
| `qm_mm/index.html` | ✅ 5 个子页链接 |
| `qm_mm/builtin.html` | ✅ **内容极丰富**（完整蛋白质教程） |
| `qm_mm/image_charges.html` | ✅ **内容完整**（含公式与输入） |
| `qm_mm/gromacs.html` | 存在，见 §3 |
| `qm_mm/polarizable_force_field.html` | ❌ **占位页** |
| `qm_mm/implicit_solvation.html` | ❌ **占位页** |
| `machine_learning/index.html` | ✅ 6 个子页链接 |
| `machine_learning/deepmd.html` | ✅ 内容完整 |
| `embedding/qm_qm.html` | ❌ 占位页（上一轮已登记） |

---

## 1. QM/MM 章节结构（官方）

```
QM/MM
├── QM/MM with Built-in Force Field     ← 内建力场（见 §2，内容最丰富）
├── QM/MM with GROMACS                  ← 与 GROMACS 耦合
├── Polarizable Force Field             ← ❌ 占位页
├── Implicit Solvation                  ← ❌ 占位页
└── Image Charges                       ← 镜像电荷（见 §4，内容完整）
```

> **官方额外给的资源**："See also the full playlist from BioExcel"——<https://www.youtube.com/playlist?list=PLzLqYW5ci-2dvlvgySfQDu-TKkr3fHSIA>（BioExcel 的完整播放列表）。这是官方推荐的 QM/MM 视频教程。

---

## 2. 内建力场 QM/MM（官方教程，内容极丰富）

### 2.1 官方体系（原文）

> This tutorial will illustrate the setup process of a QM/MM protein - substrate system. The model system we will be using is **chorismate mutase**, an enzyme that catalyzes the conversion of chorismate to prephenate, which is a critical reaction in the shikimate pathway. One attractive feature of this enzyme is that it catalyzes the reaction in an **electrostatic manner, without forming covalent bonds to the substrate**. This allows us to treat the complete enzyme at the computationally cheap MM level, **saving us the headache of setting up bonds across the QM/MM border**.

**关键设计**：因为该酶**不形成共价键**，所以**不需要 link atom**。这是"什么时候可以避免 link atom"的官方范例。

### 2.2 准备流程（官方步骤）

| 步骤 | 官方做法 |
|---|---|
| 1. 取结构 | PDB ID **2CHT**；原结构含 12 个单元 + 12 个抑制剂，需**删掉多余亚基与抑制剂**，把抑制剂**替换成底物** |
| 2. 生成拓扑 | CP2K 支持 **CHARMM 型 PSF** 与 **Amber 型 prmtop**；官方用 Ambertools |
| 3. 小分子参数化 | `antechamber` + `parmchk2`，电荷用 **bcc** 方法，力场 **GAFF2** |
| 4. 组装 | `tleap`，蛋白用 **Amber14（ff14SB）** |
| 5. 溶剂化 | 立方水盒，从蛋白向外 **14 Å**，加 **Na⁺** 中和 |
| 6. 得到文件 | `complex.prmtop`（拓扑）+ `complex.inpcrd`（坐标） |

**官方命令（逐字）**：

```bash
for i in A B C; do antechamber -i Lig${i}.mol2 -o Ligand${i}.mol2 -fi mol2 -fo mol2 -c bcc -pf yes -nc -2 -at gaff2 -j 5 -rn CH${i}; done
for i in A B C; do parmchk2 -i Ligand${i}.mol2 -f mol2 -o Ligand${i}.frcmod -s 2; done
```

```
source leaprc.protein.ff14SB
source leaprc.gaff2
source leaprc.water.tip3p

ligA = loadmol2 LigandA.mol2
ligB = loadmol2 LigandB.mol2
ligC = loadmol2 LigandC.mol2

loadamberparams LigandA.frcmod
loadamberparams LigandB.frcmod
loadamberparams LigandC.frcmod

protein = loadPDB Protein.pdb
complex = combine {protein ligA ligB ligC}
```

```
solvateBox complex TIP3PBOX 14.0 iso
addIonsRand complex  Na+ 0
saveamberparm complex complex.prmtop complex.inpcrd
quit
```

**官方提醒**：

> The distance is determined by the cutoffs for nonbonded interactions, plus some buffer to account for cell shrinking. For production simulations you may want to switch to a **dodecahedron or octahedron** for increased efficiency.
>
> Using your favourite visualisation tool, check that the **Na⁺ ions did not get placed right next to your ligand** - their placement is random. The box size can be found at the bottom of the inpcrd file, followed by the vectors. These dimensions should be specified in the `CELL` subsection of your input file.

### 2.3 MM 层平衡（官方）

> We will first run 1000 steps of energy minimization (or fewer, depending on the convergence) with the input file `em.inp` to eliminate bad contacts.

```bash
cp2k.sopt em.inp > em.out          # 单进程
mpirun -np N cp2k.popt em.inp > em.out   # 多进程
```

> **CP2K will warn you about missing forcefield terms. You can have CP2K output these using `FF_INFO`.** In this case, the missing terms are Urey-Bradley interactions. **This is normal**, as the Amber force field we are employing here does not use Urey-Bradley terms. A second warning states that our CRD file lacks velocities and box information will not be read. **This is not a problem either**, as we do not have velocities at this moment and box parameters are provided in the input file.

| 警告 | 官方判定 |
|---|---|
| 缺 Urey-Bradley 项 | **正常**（Amber 力场不用 UB） |
| CRD 无速度与盒子信息 | **不是问题**（速度此刻不需要；盒子在输入里给了） |

> **实用要点**：`FF_INFO` 是**查缺失力场项**的官方关键字。

### 2.4 指定 QM 区（`&QM_KIND`，官方示例）

> We first have to specify which atoms should be treated at the QM level using the `QM_KIND` section:

```
&QM_KIND O
  MM_INDEX 5668 5669 5670 5682 5685 5686
&END QM_KIND
&QM_KIND C
  MM_INDEX 5663 5666 5667 5671 5673 5675 5676 5678 5680 5684
&END QM_KIND
&QM_KIND H
  MM_INDEX  5664 5665 5672 5674 5677 5679 5681 5683
&END QM_KIND
```

**要点**：`&QM_KIND 元素` + `MM_INDEX 原子索引列表`。

### 2.5 嵌入方式（官方明确的三档）

> We will use the semi-empirical **AM1** method as our QM method, electrostatically embedded in the MM system: `E_COUPL COULOMB`. **This allows for the QM region to be polarized by the MM environment.** Mechanical embedding, where the QM region only interacts with the MM region as point charges and no polarization occurs, can be selected through `E_COUPL NONE`. **In DFT calculations, the highly efficient GEEP method can be used as well.**

| `E_COUPL` | 含义 | 特点 |
|---|---|---|
| `COULOMB` | 静电嵌入 | **QM 区可被 MM 环境极化** |
| `NONE` | 机械嵌入 | QM 只与 MM 的点电荷相互作用，**无极化** |
| `GEEP` | 高斯展开静电势 | **DFT 计算中可用**，官方称"highly efficient" |

### 2.6 官方明确的关键坑：AMBER 氢原子类型的 LJ 参数

> Before running the QM/MM simulation we need to amend our prmtop file, because in the classical forcefield, several hydrogen atom types **do not have separate Lennard-Jones parameters or they are set up to 0.0**. The AMBER FF atom types are **HO** (from the TIP3P water model), **HG** (from serine, threonine and tyrosine residues). **This will cause unphysical interactions with the QM region and the simulation will fail due for stability reasons.** The hydrogen atoms with these atom types will strongly interact with the QM electron clouds, eventually crashing the system.

**修法**（官方用 `parmed`）：

```bash
$ parmed complex.prmtop
changeLJSingleType :WAT@H1 0.3019 0.047
changeLJSingleType :*@HO 0.3019 0.047
outparm complex_LJ_mod.prmtop
quit
```

> Either if we are using `changeLJSingleType` or `addLJType`, we need to ensure that we are changing the right atom index. To do so, we need to use `printDetails` or `printLJTypes` that print the information on the selected atom index.

**规则**：把 `HO`、`HG` 等**无 LJ 参数或为 0.0** 的氢类型，改成 GAFF2 醇类氢的参数 `0.3019 0.047`。

### 2.7 用 link atom 把酶残基放进 QM 区（官方做法）

> High-level calculations in literature have shown **Arg90** (take care, this is **residue 89 in parmed**) to be the most important residue for catalysis, so we will treat this residue at the QM level. ... **Try to cut across the most boring aliphatic C-C bond in your residue, and definitely avoid cutting across heavily polarized bonds.** In our case, we will cut the **Cα - Cβ** bond. The Cα will be a part of the MM subsystem while the Cβ will be a part of the QM subsystem.

```
&LINK
  MM_INDEX  1411
  QM_INDEX  1413
  LINK_TYPE IMOMM
&END LINK
```

> Note the `LINK` subsection. This tells cp2k where the two subsystems are linked, in this case through a bond between MM atom 1411 (Cα) and QM atom 1413 (Cβ), as well as how to treat the link. We are using the **IMOMM** method for the link.

**官方给出的切键规则（很重要）**：

| 规则 | 官方原文 |
|---|---|
| 切最"无聊"的键 | "cut across the most boring aliphatic C-C bond" |
| 避免切强极化键 | "definitely avoid cutting across heavily polarized bonds" |
| 索引要小心 | "take care, this is residue 89 in parmed" |

### 2.8 官方明确的电荷中和细节（很容易忽略）

> The arginine sidechain has now been moved to the QM region. This means we need to adjust the QM charge to **-1**, but this also affects the MM region. The partial charges on the atoms of the arginine residue sum up to **+1**. When we move the sidechain atoms to the QM region, **their charges are no longer counted in the MM region, leading to a residual partial charge. In our case, the total charge amounts to -0.0362.** We can neutralize the system by distributing an equal but opposite charge across all 6 mainchain atoms of the residue. For example, the charge on the N is -0.3479. **Subtracting -0.0362/6 from that gives us the new charge, -0.3419.** Do the same calculation for the 5 remaining mainchain atoms and check that the modified charges for the six atoms add up to zero. Then, apply the changes using parmed's change command:

```
change charge @1409 -0.3419
```

> **这是 QM/MM 最隐蔽的坑之一**：把残基侧链移入 QM 区后，MM 区**残留非零净电荷**，必须手动分配抵消。官方给了完整算法与数值。

### 2.9 元动力学与集合变量（官方）

> The input file `monitor.inp` will perform 5 ps of simulation in the NVT ensemble. ... We have also defined a **collective variable (CV)**, i.e. a variable that that describes our process of interest well and allows us to monitor this variable as a surrogate for the process. **The CV for this system is the difference in distance between the C-O bond that we will be breaking and the C-C bond that we will be forming.** Start the simulation and observe the collective variable output in the `MONITOR-COLVAR.metadynLog` file.

> Metadynamics: ... `NT_HILLS` parameter large enough to allow the simulation to equilibrate after each hill addition.

| 项 | 内容 |
|---|---|
| 系综 | NVT，5 ps |
| CV | **断键距离 − 成键距离**（C-O 与 C-C 之差） |
| 输出 | `MONITOR-COLVAR.metadynLog` |
| 元动力学 | `NT_HILLS` 要足够大，让每次加山后系统能平衡 |

---

## 3. 与 GROMACS 的 QM/MM

> 官方页面 `qm_mm/gromacs.html` 存在。上一轮 `09_build_libraries.md` 已记录：**9.1 起支持 Gromacs QM/MM**；dashboard 有 `Gromacs QM/MM` 集成测试；CMake 相关开关见 `09`。
>
> 具体输入流程本文件未逐页采集，**缺口登记在 `_sources.md` §5**。

---

## 4. 镜像电荷 QM/MM（IC-QM/MM，官方内容完整）

### 4.1 官方定位（原文）

> The image charge (IC) augmented QM/MM model in CP2K is designed for the simulation of **adsorbate-metal systems**. The adsorbate is treated by QM whereas the metallic substrate is described by classical force fields.

**用途**：吸附物-金属体系。吸附物用 QM，金属基底用经典力场。

### 4.2 原理（官方公式）

金属中的电荷分布 ρ_m 由一组以金属原子为中心的高斯电荷（镜像电荷）建模：

```
ρ_m(r) = Σ_a c_a g_a(r, R_a)
```

系数 c_a 未知，通过**自洽过程**确定，施加金属内**恒电势条件**：

```
V_H(r) + V_m(r) = ∫ [ρ(r') + ρ_m(r')] / |r' − r| dr' = V_0
```

其中 V_0 是可不为零的常数电势（若施加外电势）。

> The implementation is embedded in the Gaussian and plane waves scheme of CP2K and thus **naturally suited for periodic systems**.

### 4.3 基本输入（官方）

```
&QMMM
  :
  :
  &IMAGE_CHARGE
    MM_ATOM_LIST 1..576
    EXT_POTENTIAL 0.0
  &END IMAGE_CHARGE
&END QMMM
```

| 关键字 | 说明 |
|---|---|
| `MM_ATOM_LIST` | **携带镜像电荷的 MM 原子列表**（通常是全部金属原子） |
| `EXT_POTENTIAL` | 对应 V_0，**默认 0.0 V** |

> **官方注意**："Note that the **QM and MM box must have the same size** for an IC-QM/MM calculation."

### 4.4 打印选项（官方）

```
&QMMM
  :
  :
  &PRINT
    &IMAGE_CHARGE_INFO
    &END
  &END PRINT
&END QMMM
```

> Detailed energy information and the **normalized IC coefficients q_a** can be printed out by `IMAGE_CHARGE_INFO`. The normalized IC coefficients are defined as `q_a = c_a (α/π)^{−3/2}`, where α is the width of the Gaussian.

### 4.5 进阶关键字（官方）

```
&IMAGE_CHARGE
  MM_ATOM_LIST 1..576
  EXT_POTENTIAL 0.0
  WIDTH 3.5
  IMAGE_MATRIX_METHOD MME
  DETERM_COEFF CALC_MATRIX
  RESTART_IMAGE_MATRIX .false.
&END IMAGE_CHARGE
```

| 关键字 | 官方说明 |
|---|---|
| `WIDTH` | 高斯宽度 α，**IC 模型中唯一的可调参数**。**能量与梯度在 α > 3.0 Å⁻² 时不再依赖 α**。α 太小 → 高斯极宽 → 技术伪影；极大也不推荐 |
| `IMAGE_MATRIX_METHOD` | IC 矩阵 T_ab 的算法：`GPW`（对应 Golze2013 图 1 的算法）/ `MME`（**新实现的积分方案，显著更快**） |
| `DETERM_COEFF` | 系数 c_a 的确定方式：`CALC_MATRIX`（算 T_ab 并解线性方程组）/ `ITERATIVE`（用迭代共轭梯度，避免每 SCF 步算 T_ab）。**新积分方案 MME 算 T_ab 极快，因此不需要迭代 → 总设 `CALC_MATRIX`** |
| `RESTART_IMAGE_MATRIX` | 若用 `ITERATIVE`，可重启 T_ab 用于 MD |

> **官方明确**："Setting these additional keywords is typically **not required**. The default settings are fine."

### 4.6 典型设置（官方）

> The typical setup for an IC-QM/MM simulation is as follows
> - adsorbed molecules described by DFT
> - metal is constrained or described by an embedded atom model (EAM)
> - Interactions between QM and MM:
>   - Pauli repulsion, dispersion etc. modeled by force fields e.g. Lennard Jones
>   - electrostatic interaction/induction: IC model

### 4.7 官方示例（GitHub）

| 示例 | 说明 |
|---|---|
| [Au111_guanine](https://github.com/cp2k/cp2k-examples/tree/master/image_charges/Au111_guanine) | 单个鸟嘌呤分子在 Au(111) 上，用**修改的 Born-Mayer 势**描述 Pauli 排斥与色散 |
| [Pt111_1H2O](https://github.com/cp2k/cp2k-examples/tree/master/image_charges/Pt111_1H2O) | 单个水分子在 Pt(111) 上，用 **Siepmann-Sprik 势**描述水-金属相互作用 |

### 4.8 原始文献

- `Golze2013`（theory and implementation，J. Chem. Theory Comput., 9, 5086 (2013)）
- `Siepmann1995`（水-金属势）

---

## 5. 嵌入方法（Embedding）

```
Embedding
├── Kim-Gordon            ← `methods/embedding/kim-gordon.html`
└── Quantum Embedding Theories   ← ❌ 占位页（上一轮已登记）
```

> **QM/MM 不在 `embedding` 下**，而在 `Methods` 下的独立项——上一轮已澄清，此处重申。

**官方占位页给的外链**（量子嵌入理论）：`_media/events:2017_dev_meeting/rybkin_cp2kdev-meeting_zurich2017-7.pdf`

---

## 6. 机器学习势（Machine Learning）

### 6.1 官方支持的 ML 势（页面结构）

```
Machine Learning
├── NequIP and Allegro
├── MACE
├── Neural Network Potentials
├── PAO-ML
├── DeePMD-kit
└── Atomic Cluster Expansion (ACE)
```

| ML 势 | 页面 |
|---|---|
| NequIP / Allegro | `machine_learning/nequip.html` |
| MACE | `machine_learning/mace.html` |
| 神经网络势（NNP） | `machine_learning/nnp.html` |
| PAO-ML | `machine_learning/pao-ml.html` |
| DeePMD-kit | `machine_learning/deepmd.html`（内容完整，见 §6.2） |
| ACE | `machine_learning/ace.html` |

> 上一轮 `09_build_libraries.md` 记录了 `libtorch` 等库依赖与"libtorch ≤2.12.1 与 oneMKL 不兼容"的事实，此处补充**方法层**的输入写法。

### 6.2 DeePMD-kit（官方内容完整）

**官方定位**：

> DeePMD-kit is a package written in Python/C++, designed to minimize the effort required to build deep learning-based models of interatomic potential energy and force field and to perform molecular dynamics (MD).

**输入段**（官方原文）：

> Inference in CP2K is performed through the `DEEPMD` section.

```
&DEEPMD
  ATOMS W
  ATOMS_DEEPMD_TYPE 0
  POT_FILE_NAME DeePMD/W.pb
&END DEEPMD
```

| 关键字 | 官方说明 |
|---|---|
| `ATOMS` | 元素/kind 的列表 |
| `ATOMS_DEEPMD_TYPE` | 对应元素在 DeePMD-kit 参数 `type_map` 中的**索引**。**"If this is not done unphysical results will be obtained. Spotting such issues is quite straightforward as the energy is significantly wrong."** |
| `POT_FILE_NAME` | 部署好的 DeePMD 模型（`.pb`） |

**完整示例**（官方指向 regtest）：[DeePMD_W.inp](https://github.com/cp2k/cp2k/blob/master/tests/Fist/regtest-deepmd/DeePMD_W.inp)

**编译要求**（官方）：

> Running with DeePMD-kit requires compiling CP2K with the **libdeepmd_c** library. For the CP2K binaries, please install the toolchain using the flag `--with-deepmd`, which would download libdeepmd_c from DeePMD-kit Github release and compile. **GPU support is enabled when CUDA environment exists.**

| 项 | 内容 |
|---|---|
| 必需库 | `libdeepmd_c` |
| toolchain 开关 | `--with-deepmd` |
| GPU | 有 CUDA 环境时自动启用 |

> **重要陷阱**：`ATOMS_DEEPMD_TYPE` 必须与 DeePMD 模型 `type_map` 一致，否则**能量会明显错误**——官方说"很容易发现，因为能量显著不对"。

---

## 7. 后 HF 与半经验方法（页面结构）

### 7.1 Post Hartree-Fock

页面：`methods/post_hartree_fock/index.html`

> 上一轮 `02_dft_methods.md` 已记录 MP2 / SOS-MP2 / RPA / GW 的功能与版本时间线；`10_features_resources.md` 记录了功能清单。**本轮未逐页采集该章节正文**，缺口登记于 `_sources.md` §5。

### 7.2 Semi-Empiricals

页面：`methods/semiempiricals/index.html`

> 官方功能清单与 README 记载支持 **AM1、PM3、PM6、RM1、MNDO、DFTB、xTB** 等（见 `10_features_resources.md`）。**本轮未逐页采集**。

> **注意**：QM/MM 教程里用的 **AM1** 就属于半经验方法（见 §2.5）。

---

## 8. 本文件明确登记的占位页（官方无正文）

| 页面 | 官方状态 |
|---|---|
| `qm_mm/polarizable_force_field.html` | "Unfortunately no one has gotten around to writing this page yet :-(" + 仅 1 条文献链接（Devynck2012） |
| `qm_mm/implicit_solvation.html` | "Unfortunately, nobody has gotten around to writing this page yet :-(" |
| `embedding/qm_qm.html` | 占位页（上一轮已登记） |

> **G 层不编造**。隐含溶剂化模型（SCCS 等）的输入写法请查官方 Input Reference 的 `&SCCS` 段；F 层可能有实操经验。

---

## 9. 交叉索引

| 想查 | 去 |
|---|---|
| QM/MM 功能清单 | `10_features_resources.md` |
| QM/MM 相关库依赖与编译开关 | `09_build_libraries.md` |
| 元动力学（一般用法） | `04_sampling_md.md`；F 层 |
| 集合变量 COLVAR | `17_optimization_advanced.md`（约束动力学节） |
| 半经验方法/DFTB/xTB | `10_features_resources.md`、`11_version_changelog.md` |
| ML 势的库依赖（libtorch 等） | `09_build_libraries.md` |
| 性质计算 | `06_properties.md`、`15_optical_and_xray.md` |
| 实操 QM/MM 经验 | F 层 `../playbook.md` |
