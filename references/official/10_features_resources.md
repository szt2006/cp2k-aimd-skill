# 10 · 官方功能清单、学习资源、引用与许可

> **来源**：
> - <https://www.cp2k.org/features>（功能全清单，2026-08-21 更新）
> - <https://www.cp2k.org/>（About CP2K）
> - <https://www.cp2k.org/docs>（More Documentation：报告/论文/书）
> - <https://www.cp2k.org/download>（下载与许可）
> - <https://manual.cp2k.org/trunk/acronyms.html>（缩写表）
> - <https://www.cp2k.org/faq:cite>（引用规范）
> **抓取日期**：2026-09-08
> **本文件定位**：G 层（官方权威层）。用于回答"CP2K 能不能算 X"、"怎么引用"、"去哪学"。

---

## 1. CP2K 是什么（官方 About 页原文）

> CP2K is a quantum chemistry and solid state physics software package that can perform atomistic simulations of solid state, liquid, molecular, periodic, material, crystal, and biological systems. CP2K provides a general framework for different modeling methods such as **DFT using the mixed Gaussian and plane waves approaches GPW and GAPW**. Supported theory levels include **DFTB, LDA, GGA, MP2, RPA, semi-empirical methods (AM1, PM3, PM6, RM1, MNDO, …), and classical force fields (AMBER, CHARMM, …)**. CP2K can do simulations of **molecular dynamics, metadynamics, Monte Carlo, Ehrenfest dynamics, vibrational analysis, core level spectroscopy, energy minimization, and transition state optimization using NEB or dimer method**.

**技术栈**：

> CP2K is written in **Fortran 2008** and can be run efficiently in parallel using a combination of **multi-threading, MPI, CUDA, and HIP**. It is freely available under the **GPL license**.

**官方免责声明（重要）**：

> Please note that **CP2K comes without any warranty or direct support**.

**官方关键结构**：

> Some of the key parts of CP2K are **Quickstep, FIST, and QM/MM**.

**官方对使用门槛的提醒**：

> Using CP2K for scientific simulations requires a **good understanding of the underlying theory and algorithms**; glossary of acronyms can be helpful. In addition to references listed in the manual, the recommended readings (talks, technical reports, theses, books) can be found on the additional documentation page.

---

## 2. 官方功能全清单（features 页逐条）

官方开头定位：

> CP2K is a program to perform simulations of solid state, liquid, molecular and biological systems. It is especially aimed at **massively parallel and linear scaling electronic structure methods** and **state-of-the-art ab-initio molecular dynamics (AIMD) simulations**.
>
> CP2K is optimized for the mixed **Gaussian and Plane-Waves (GPW)** method based on pseudopotentials, but is able to run **all-electron or pure plane-wave/Gaussian calculations** as well.

### 2.1 Quickstep 模块的从头算电子结构方法

| # | 官方功能条目 |
|---|---|
| 1 | Density-Functional Theory (DFT) energies and forces |
| 2 | Hartree-Fock (HF) energies and forces |
| 3 | Moeller-Plesset 2nd order perturbation theory (MP2), Scaled-Opposite-Spin-MP2 (SOS-MP2), Random-Phase-Approximation (RPA): energies and forces |
| 4 | Double-Hybrid Functionals based on MP2, SOS-MP2 and RPA: energies and forces |
| 5 | Gas phase or Periodic boundary conditions (PBC) |
| 6 | Basis sets include various standard Gaussian-Type Orbitals (GTOs), Pseudopotential plane-waves (PW), and a mixed Gaussian and (augmented) plane wave approach (GPW/GAPW) |
| 7 | PW DFT functionality (energy, forces, stress), including LAPW (all-electron) |
| 8 | Norm-conserving, seperable Goedecker-Teter-Hutter (GTH) and non-linear core corrected (NLCC) pseudopotentials, or all-electron calculations |
| 9 | Local Density Approximation (LDA) XC functionals including **SVWN3, SVWN5, PW92 and PADE** |
| 10 | Gradient-corrected (GGA) XC functionals including **BLYP, BP86, PW91, PBE and HCTH120** as well as the meta-GGA XC functional **TPSS** |
| 11 | Hybrid XC functionals with exact Hartree-Fock Exchange (HFX) or RI-based Hartree-Fock-exchange (RI-HFX) including **B3LYP, PBE0 and MCY3** |
| 12 | Additional XC functionals via **LibXC** |
| 13 | Dispersion corrections via **DFT-D2 and DFT-D3** pair-potential models |
| 14 | Non-local van der Waals corrections for XC functionals including **B88-vdW, PBE-vdW and B97X-D** |
| 15 | **DFT+U (Hubbard) correction** |
| 16 | Density-Fitting for DFT via Bloechl or Density Derived Atomic Point Charges (DDAPC) charges, for HFX via Auxiliary Density Matrix Methods (ADMM) and for MP2/RPA via Resolution-of-identity (RI) |
| 17 | Sparse matrix and prescreening techniques for linear-scaling Kohn-Sham (KS) matrix computation |
| 18 | **Orbital Transformation (OT) or Direct Inversion of the iterative subspace (DIIS) self-consistent field (SCF) minimizer** |
| 19 | Local Resolution-of-Identity Projector Augmented Wave method (**LRIGPW**) |
| 20 | Absolutely Localized Molecular Orbitals SCF (**ALMO-SCF**) energies for linear scaling of molecular systems |
| 21 | Excited states via time-dependent density-functional perturbation theory (**TDDFPT**) |
| 22 | Bandstructure-calculations within the **GW-approximation** |
| 23 | Optical properties using the **Bethe-Salpeter-equation** |
| 24 | **K-Point-technique supported for a variety of methods (DFT, RI-based Hartree-Fock)** |
| 25 | Machine-learning based density-functional **Skala** developed by Microsoft |

> **重要**：第 24 条明确"**K-Point-technique supported for a variety of methods (DFT, RI-based Hartree-Fock)**"。这是 G 层对 FAQ 中过时表述（"CP2K does not have k-point sampling"）的权威反证，见 `08_errors_and_faq.md` §3.11。

> **色散校正的权威记录**：第 13、14 条给出 **DFT-D2 / DFT-D3 配对势模型** 与 **非局域 vdW（B88-vdW / PBE-vdW / B97X-D）**。这是手册 `methods/dft/vdw.html` 404 时最可靠的官方来源，配合 `09_build_libraries.md` 的 DFTD4 / TBLITE 章节。

### 2.2 从头算分子动力学（AIMD）

| # | 官方功能条目 |
|---|---|
| 1 | Born-Oppenheimer Molecular Dynamics (**BOMD**) |
| 2 | Ehrenfest Molecular Dynamics (**EMD**) |
| 3 | PS extrapolation of initial wavefunction |
| 4 | Time-reversible Always Stable Predictor-Corrector (**ASPC**) integrator |
| 5 | Approximate Car-Parrinello like Langevin Born-Oppenheimer Molecular Dynamics (**Second-Generation Car-Parrinello Molecular Dynamics**) |

> **关键澄清（官方原文末句）**：
>
> > **CP2K does not implement conventional Car-Parrinello Molecular Dynamics (CPMD).**
>
> 即 CP2K **不实现**传统 CPMD，只有"近似 Car-Parrinello 式的 Langevin BOMD"（第二代 CPMD）。

### 2.3 混合量子-经典（QM/MM）模拟

| # | 官方功能条目 |
|---|---|
| 1 | Real-space multigrid approach for the evaluation of the Coulomb interactions between the QM and the MM part |
| 2 | Linear-scaling electrostatic coupling treating of periodic boundary conditions |
| 3 | Adaptive QM/MM |

### 2.4 其它功能（Further features include）

| # | 官方功能条目 |
|---|---|
| 1 | Single-point energies, geometry optimizations and frequency calculations |
| 2 | Several nudged-elastic band (**NEB**) algorithms (**B-NEB, IT-NEB, CI-NEB, D-NEB**) for minimum energy path (MEP) calculations |
| 3 | Global optimization of geometries |
| 4 | Solvation via the **Self-Consistent Continuum Solvation (SCCS)** model |
| 5 | Semi-Empirical calculations including the **AM1, RM1, PM3, MNDO, MNDO-d, PNNL and PM6** parametrizations, **density-functional tight-binding (DFTB)** and **self-consistent-polarization tight-binding (SCP-TB)**, with or without periodic boundary conditions |
| 6 | Classical Molecular Dynamics (MD) simulations in **microcanonical ensemble (NVE)** or **canonical ensmble (NVT)** with **Nose-Hover** and **canonical sampling through velocity rescaling (CSVR)** thermostats |
| 7 | **Metadynamics** including well-tempered Metadynamics for Free Energy calculations |
| 8 | Classical Force-Field (MM) simulations |
| 9 | **Monte-Carlo (MC) KS-DFT** simulations |
| 10 | Static (e.g. spectra) and dynamical (e.g. diffusion) properties |
| 11 | **ATOM code** for pseudopotential generation |
| 12 | Integrated molecular basis set optimization |

> **NEB 的官方功能记录**：第 2 条明确列出 **B-NEB、IT-NEB、CI-NEB、D-NEB 四种算法**。这是官方手册 NEB 页为占位页时最权威的功能来源，见 `05_optimization.md` 的 NEB 说明。

> **温控器官方记录**：第 6 条明确 CP2K 提供 **Nose-Hover** 与 **CSVR** 两种恒温器，用于 NVE / NVT 系综。见 `04_sampling_md.md`。

---

## 3. 缩写表（官方 acronyms 页，约 130 条）

> **来源**：<https://manual.cp2k.org/trunk/acronyms.html>

| 缩写 | 官方展开 |
|---|---|
| ADMM | Auxiliary Density Matrix Method |
| ALMO | Absolutely Localized Molecular Orbitals |
| AM1 | Austin Model 1 |
| AMBER | Assisted Model Building and Energy Refinement |
| APT | Atomic Polarization Tensor |
| ASE | Atomic Simulation Environment |
| ASPC | Always Stable Predictor-Corrector |
| BCC | Body-Centered Cubic crystal structure |
| BFGS | Broyden–Fletcher–Goldfarb–Shanno algorithm |
| BOMD | Born-Oppenheimer Molecular Dynamics |
| BSE | Bethe-Salpeter Equation |
| BSSE | Basis Set Superposition Error |
| CDFT | Constrained Density Functional Theory |
| CDFT-CI | Constrained Density Functional Theory Configuration Interaction |
| CG | Conjugated Gradients algorithm |
| CHARMM | Chemistry at HARvard Molecular Mechanics |
| CIF | Crystallographic Information File |
| COLVAR | COLlective VARiable |
| CP | Car-Parrinello method |
| CPMD | Car-Parrinello Molecular Dynamics |
| CSVR | Canonical Sampling through Velocity Rescaling |
| CUDA | Compute Unified Device Architecture |
| DBCSR | Distributed Block Compressed Sparse Row library |
| DDAPC | Density Derived Atomic Point Charges |
| DFTB | Density Functional Tight Binding |
| DFT | Density Functional Theory |
| DFET | Density Functional Embedding Theory |
| DIIS | Direct Inversion of the Iterative Subspace |
| DLA-F | Distributed Linear Algebra from the Future |
| DOS | Density Of States |
| EAM | Embedded-Atom Method |
| EC | Energy Correction |
| EHT | Extended Hückel Theory |
| EIP | Empirical Interatomic Potential |
| ELPA | Eigenvalue soLvers for Petascale Applications |
| EMD | Ehrenfest Molecular Dynamics |
| EPR | Electron Paramagnetic Resonance |
| ERI | Electron Repulsion Integral |
| FCC | Face-Centered Cubic crystal structure |
| FIST | Frontiers In Simulation Technology (CP2K's force field implementation) |
| FPGA | Field Programmable Gate Array |
| GAPW | Gaussian Augmented-Plane Waves method |
| gCP | Geometrical CounterPoise |
| GCP | Google Cloud Platform |
| GEEP | Gaussian Expansion of the Electrostatic Potential |
| GGA | Generalized Gradient Approximations |
| GHO | Generalized Hybrid Orbital method |
| GLE | Generalized Langevin Equation thermostat |
| GPW | Gaussian Plane Wave method |
| GROMOS | GROningen MOlecular Simulation |
| GTH | Goedecker-Teter-Hutter pseudopotentials |
| GTO | Gaussian Type Orbitals |
| GW | GW approximation |
| HCP | Hexagonal Close-Packed crystal structure |
| HF | Hartree Fock |
| HFX | Hartree Fock eXchange |
| HIP | Heterogeneous Interface for Portability |
| IEEE | Institute of Electrical and Electronics Engineers |
| IMOMM | Integrated Molecular Orbital Molecular Mechanics method |
| K-point | a vector in reciprocal space |
| KS | Kohn-Sham |
| LCAO | Linear Combination of Atomic Orbitals |
| LDA | Local-Density Approximation |
| LDOS | Local Density of States |
| LINRES | LINear RESponse |
| LRIGPW | Local Resolution-of-Identity Projector Augmented Wave method |
| LS | Linear Scaling |
| LSD | Local Spin Density |
| MAO | Modified Atomic Orbitals |
| MC | Monte Carlo method |
| MD | Molecular Dynamics |
| MM | Molecular Mechanics |
| MME | MiniMax-Ewald |
| MNDO | Modified Neglect of Diatomic Overlap |
| MO | Molecular Orbitals |
| MOM | Maximum Overlap Method |
| MP2 | Møller–Plesset perturbation theory to 2nd order |
| MPI | Message Passing Interface |
| MSST | Multi-Scale Shock Technique |
| NDDO | Neglect of Diatomic Differential Overlap |
| NEB | Nudged Elastic Band |
| NEGF | Non-Equilibrium Green's Function |
| NMR | Nuclear Magnetic Resonance |
| NNP | Neural Network Potential |
| NpE | Constant Number, Pressure, and Energy |
| NVE | Constant Number, Volume, and Energy |
| NVT | Constant Number, Volume, and Temperature |
| OF | Orbital Free |
| OpenCL | Open Computing Language |
| OpenMP | Open Multi-Processing |
| OT | Orbital Transformation method |
| PAO-ML | Polarized Atomic Orbitals from Machine Learning |
| PBC | Periodic Boundary Conditions |
| PBE | Perdew–Burke–Ernzerhof exchange-correlation functional |
| PDB | Protein Data Bank (the database or the format specification) |
| PIGLET | Path Integral Generalized Langevin Equation Thermostat |
| PILE | Path Integral Langevin Equation thermostat |
| PINT | Path INTegral |
| PM3 | Parameterized Model number 3 |
| PM6 | Parameterized Model number 6 |
| POD | Projection-Operator Diabatization |
| PP | Pseudo-Potential |
| PW | Plane Waves |
| QMMM | Quantum Mechanics / Molecular Mechanics |
| QM | Quantum Mechanics |
| QS | Quick Step (cp2k's quantum methods implementation) |
| RESP | Restrained ElectroStatic Potential |
| RESPA | REversible reference System Propagator Algorithm |
| RI | Resolution of Identity |
| RM1 | Recife Model 1 |
| RMA | Remote Memory Access |
| RMSD | Root-Mean-Square Deviation |
| RPA | Random-Phase Approximation |
| RPMD | Ring Polymer Molecular Dynamics |
| SCCS | Self-Consistent Continuum Solvation model |
| SCF | Self Consistent Field algorithm |
| SCPTB | Self-Consistent-Polarization Tight-Binding |
| SE | Semi-Empirical methods |
| SIC | Self Interaction Correction |
| SOC | Spin-Orbit Couplings |
| STM | Scanning Tunneling Microscope |
| TDDFPT | Time Dependent Density Field Perturbation Theory |
| TMC | Tree Monte Carlo algorithm |
| TRS4 | TRace reSetting 4th order scheme |
| UFF | Universal Force Field |
| UKS | Unrestricted Kohn-Sham |
| VMD | Visual Molecular Dynamics |
| XAS | X-ray Absorption Spectra |
| XC | eXchange and Correlation functional |
| xTB | eXtended Tight Binding |
| Z-matrix | formalism to represent atomic coordinates |
| ZMP | Zhao-Morrison-Parr potential |

> **注意**：官方缩写表中 `LSD` 的展开是 **Local Spin Density**，而 `08_errors_and_faq.md` §2.8 提到错误消息里 `LSD` 是 `UKS` 的别名。两者不矛盾：**`LSD` 作为理论缩写指 Local Spin Density（即自旋极化/LSDA），在 CP2K 输入中作为 `UKS` 的别名使用。**

> **`BSSE` 在官方缩写表中存在**（Basis Set Superposition Error），但**官方手册没有 BSSE 校正的专章**。这是 G 层的重要发现——用户记忆中提到"BSSE 在 PDF/字幕全文零命中"，官方缩写表证实该概念被承认，但**校正方法与输入关键字在官方文档中缺失**。

---

## 4. 引用规范（官方 faq:cite + About 页）

### 4.1 官方原文

> When performing calculations with CP2K, you will find a "**R E F E R E N C E S**" section in the output. This section lists the scientific articles that describe the specific modules and methods used in the calculation.
>
> When using CP2K as part of a scientific publication, the CP2K developer team kindly asks you to acknowledge their work by citing the articles in the "R E F E R E N C E S" section.
>
> Sometimes, you may need to cite CP2K in contexts where a detailed list of references is not appropriate (for example, as part of a list of quantum chemistry or solid state physics software packages). In this case, we recommend citing **the latest relevant CP2K review**. **As of May 2020, this is [10.1063/5.0007045](https://dx.doi.org/10.1063/5.0007045)**.

### 4.2 落地规则

| 场景 | 官方要求的做法 |
|---|---|
| 正式论文 | 引用输出文件里 `R E F E R E N C E S` 段列出的**全部相关文章** |
| 软件清单 / 综述里提及 CP2K | 引用**最新 CP2K 综述**（截至 2020-05 为 DOI `10.1063/5.0007045`） |

> **版本坐标提醒**：`10.1063/5.0007045` 是官方页面在 **2020 年 5 月**给出的"最新 review"。G 层原样保留，**不擅自替换为更新的综述**。若需最新引用，应回查官网。

### 4.3 引用规范的意义（G 层给的使用提示）

官方明确要求引用输出里的 `REFERENCES` 段——**这意味着一份规范的 CP2K 计算结果，其"方法部分"应当能从这个段里直接抄出**。做后处理与写作时，`REFERENCES` 段是权威来源。

---

## 5. 下载与许可（官方 download 页）

### 5.1 许可

> The source of CP2K is open and freely available for everybody under **the GPL license**.

| 项 | 内容 |
|---|---|
| 许可 | **GPL** |
| 许可全文 | <http://www.gnu.org/licenses/gpl.html> |
| 免责 | CP2K comes **without any warranty or direct support** |

### 5.2 版本策略（官方原文）

| 版本类型 | 官方描述 |
|---|---|
| **Development Version** | Most recent / All new features / **Potentially unstable / buggy** / **only available via Git** |
| **Released Version** | Older / Stable, no ongoing development / All major functionality in good shape / Only rare backports of bug fixes (as time permits) |

> Looking at the version history might help you to decide.

### 5.3 下载途径

| 途径 | 说明 |
|---|---|
| **官方发行版** | <https://github.com/cp2k/cp2k/releases/>；**请使用带版本号的 tarball（`cp2k-X.Y.tar.bz2`）** |
| 预编译版 | precompiled single node, optimised CP2K versions for Linux 也可用 |
| 第三方 | Debian/Ubuntu 替代：<http://packages.mccode.org/> |
| Windows | <https://www.cp2k.org/howto:compile_on_windows> |
| macOS | <https://www.cp2k.org/howto:compile_on_macos> |

### 5.4 DBCSR 的独立发布

> The sparse matrix library **DBCSR is part of CP2K**, and made available **standalone** at the DBCSR page.

| 资源 | 链接 |
|---|---|
| DBCSR 页 | <https://www.cp2k.org/dbcsr> |

### 5.5 Git 使用（官方原文）

**克隆最新 master**：

```
git clone https://github.com/cp2k/cp2k.git cp2k
```

**直接检出某个分支**：

```
git clone --recursive -b support/v2026.2 https://github.com/cp2k/cp2k.git cp2k
```

> 注意 `--recursive`——**必须递归克隆子模块**。

**保持克隆更新（Git ≥ 2.14）**：

```
cd cp2k
git config submodule.recurse true
git config pull.rebase true
```

之后更新：

```
cd cp2k
git pull
```

**保持克隆更新（Git < 2.14）**：

```
cd cp2k
git config pull.rebase true
```

之后更新：

```
cd cp2k
git pull
git submodule update --recursive
```

> 官方对 Dashboard 的说明：The code in Git is under constant development. Check the **Dashboard** (<http://dashboard.cp2k.org>) for current issues.

---

## 6. 官方学习资源（docs 页：报告、论文、书）

### 6.1 Talks（官方清单）

| 标题 | 讲者 / 场合 |
|---|---|
| Developing, Maintaining, Integrating CP2K | Marcella Iannuzzi, CECAM 2022 |
| Nanostructures at interfaces: How to understand the wavy flatland with computers | Marcella Iannuzzi, UZH 2018 |
| CP2K: Recent performance improvements and new TD-DFT functionality | Iain Bethune and Matthew Watkins, ARCHER courses 2016 |
| Accelerated Sparse Matrix Multiplication for Quantum Chemistry with CP2K on Hybrid Supercomputers | Ole Schütt, GTC 2015 |
| Petascale resources and CP2K | Joost VandeVondele, CSCS 2014 |
| Introductory Lecture: Converting petaflops in nanometers and sunlight into electricity | Joost VandeVondele, ETH 2012 |

### 6.2 Posters

| 标题 | 说明 |
|---|---|
| Introduction to CP2K | L. Tong et al., 2015 |

### 6.3 Workshops（官方清单，共 20 项）

| 年份 | 活动 |
|---|---|
| 2022 | Hybrid Quantum Mechanics/Molecular Mechanics (QM/MM) Approaches to Biochemistry (and beyond) (CECAM) |
| 2018 | CP2K User Tutorial "Computational Spectroscopy" (Paderborn, Aug 2018) |
| 2018 | CP2K Summer School |
| 2018 | 5th Annual CP2K UK Users Meeting (12 Jan 2018) |
| 2017 | CP2K User Tutorial on "Advanced ab-initio MD methods" (12–14 July 2017) |
| 2017 | 4th Annual CP2K UK Users Meeting (9 Jan 2017) |
| 2016 | CP2K Summer School |
| 2016 | PRACE Spring School incl. CP2K tutorial (16–20 May 2016) |
| 2016 | 3rd Annual CP2K UK Users Meeting (22 Feb 2016) |
| — | Joint MCC-UKCP-EPCC workshop on ab-initio periodic codes |
| 2015 | 4th CP2K Tutorial (CECAM) |
| 2015 | 2nd Annual CP2K UK Users Meeting |
| 2014 | NSCCS / ARCHER CP2K UK Workshop |
| 2014 | Parallel Materials Modelling Packages (23–25 April 2014) |
| 2014 | 1st Annual CP2K UK Users Meeting |
| 2013 | 3rd CP2K Tutorial (CECAM) |
| 2011 | 2nd CP2K Tutorial: enabling the power of imagination in MD simulations |
| 2009 | 1st CP2K Tutorial: enabling the power of imagination in MD simulations |
| 2008 | Standardisation and databasing of ab-initio and classical simulations |

### 6.4 Technical Reports（官方清单）

| 标题 | 作者 / 年份 |
|---|---|
| Electron Transport based on Non-Equilibrium-Green's-Functions Method | Sergey K. Chulkov et al., March 2018 |
| Local Excitement in CP2K | Sergey K. Chulkov, Matthew B. Watkins, Iain Bethune, March 2017 |
| Optimising CP2K for the Intel Xeon Phi | F. Reid, I. Bethune, PRACE White Paper, 2013 |
| Enabling CP2K Application for Exascale Computing with Accelerators using OpenACC and OpenCL | M. Uchrońskia et al., PRACE White Paper, 2013 |
| Evaluating CP2K on Exascale Hardware: Intel Xeon Phi | F. Reid, I. Bethune, PRACE White Paper, 2013 |
| High Performance MP2 for Condensed Phase Simulations | R. Reyesa, I. Bethune, PRACE White Paper, 2013 |
| CP2K - Scalable Atomistic Simulations for the PRACE Community | I. Bethune et al., PRACE White Paper, 2012 |
| CP2K - Sparse Linear Algebra on 1000s of Cores | I. Bethune, HECToR dCSE Report, Jan 2012 |
| Million Atom KS-DFT with CP2K | I. Bethune et al., PRACE White Paper, 2011 |
| Improving the scalability of CP2K on multi-core systems | I. Bethune, HECToR dCSE Report, Sep 2010 |
| Improving the performance of CP2K on HECToR | I. Bethune, HECToR dCSE Report, Jul 2009 |

### 6.5 Theses（官方清单，18 篇）

| 标题 | 作者 / 年份 |
|---|---|
| Efficient Implementation of Double-Hybrid Functionals for Condensed Phase Systems | Frederick Stein, 2022 |
| Low-Scaling Electronic Structure Methods Based on Sparse Tensor Contraction | Patrick Seewald, 2021 |
| Combining Ehrenfest Molecular Dynamics with Linear Scaling and Subsystem DFT | Samuel T. Andermatt, 2018 |
| Hydrogen Evolution Reaction on Carbon Nanotubes: Insights from Electronic Structure Theory | Nico Holmberg, 2018 |
| Low-Scaling Many-Body Perturbation Theory for Nanoscopic Systems | Jan Wilhelm, 2017 |
| Ab-initio Quantum Transport Simulations for Nanoelectronic Devices | Sascha Brück, 2017 |
| Large-Scale Nanoelectronic Device Simulation from First Principles | Mohammad Hossein Bani-Hashemian, 2016 |
| Enabling Large Scale DFT Simulation with GPU Acceleration and Machine Learning | Ole Schütt, 2016 |
| Efficient methods to reduce the complexity of the charge density within density functional theory for large systems | Dorothea Golze, 2016 |
| Efficient non-local dynamical electron correlation for condensed matter simulations | Mauro Del Ben, 2015 |
| Enabling DFT Simulations of Large Metallic Systems by Integrating the PEXSI Method into CP2K | Patrick Seewald, 2015 |
| High performance Tree Monte Carlo applied to solid and liquid water | Mandes Schönherr, 2014 |
| Parallel Global Geometry Optimization of Molecular Clusters | Ole Schütt, 2014 |
| An atomistic picture of the active interface in dye sensitized solar cells | Florian Schiffmann, 2010 |
| High performance Hartree-Fock exchange for large and condensed phase systems | Manuel Guidon, 2010 |
| Excitation energy calculations with TD-DFT | Thomas Chassaing, 2005 |
| Extending length and time scales of ab initio molecular dynamics simulations | Joost VandeVondele, 2001 |
| Die GAPW-Dichtefunktional-Methode für Ab-Initio-Molekulardynamik-Simulationen | Gerald Lippert, 1998 |

### 6.6 Books（官方推荐书目，8 本）

| 书名 | 作者 / 出版社 / 年份 |
|---|---|
| Molecular Electronic-structure Theory | Helgaker, Jorgensen, and Olsen, John Wiley & Sons, 2014 |
| Introduction to Computational Chemistry | Jensen, John Wiley & Sons, 2013 |
| Essentials of Computational Chemistry: Theories and Models | Cramer, John Wiley & Sons, 2013 |
| Ab Initio Molecular Dynamics: Basic Theory and Advanced Methods | Marx and Hutter, Cambridge University Press, 2009 |
| Electronic Structure: Basic Theory and Practical Methods | Martin, Cambridge University Press, 2004 |
| Understanding Molecular Simulation: from Algorithms to Applications | Frenkel and Smit, Academic Press, 2001 |
| Molecular Modelling: Principles and Applications | Leach, Pearson Education, 2001 |
| Density-Functional Theory of Atoms and Molecules | Parr and Yang, Oxford University Press, 1994 |

> **官方对书目的定位**：这些是"**recommended readings**"，用于补充手册中列出的参考文献。官方明确说"用 CP2K 做科学模拟需要对底层理论与算法有良好理解"。

### 6.7 官方在线资源

| 资源 | 链接 | G 层内容落点 |
|---|---|---|
| CP2K 官网 | <https://www.cp2k.org/> | §1 |
| 官方手册 | <https://manual.cp2k.org/trunk/> | `00_map.md` §3 |
| Input Reference | <https://manual.cp2k.org/trunk/CP2K_INPUT.html> | `20_input_reference_tree.md` |
| GitHub | <https://github.com/cp2k> | `12_authority_sources.md` |
| 开发者列表 | <https://github.com/cp2k/cp2k/graphs/contributors> | — |
| 社区论坛 | <https://groups.google.com/group/cp2k> | `12_authority_sources.md` |
| Dashboard（当前问题） | <http://dashboard.cp2k.org> | `19_performance_gpu_community.md` §3 |
| **科学应用案例** | <https://www.cp2k.org/science> | **`00_map.md` §2.3（79 个案例）** |
| 版本历史 | <https://www.cp2k.org/version_history> | **跳转页** → `11_version_changelog.md` |
| 缩写表（官网版） | <https://www.cp2k.org/acronyms> | §3 |
| **工具集** | <https://www.cp2k.org/tools> | **`00_map.md` §2.2（23 个软件 + GTH 势 + 3 个脚本仓库）** |
| 下载 | <https://www.cp2k.org/download> | §5 |
| 更多文档 | <https://www.cp2k.org/docs> | §6 |
| 功能清单 | <https://www.cp2k.org/features> | §2 |
| FAQ | <https://www.cp2k.org/faq> | `08_errors_and_faq.md` §3 |
| HowTo | <https://www.cp2k.org/howto> | `00_map.md` §4 |
| 练习/教程 | <https://www.cp2k.org/exercises> | `00_map.md` §5 |

> **官方生态的完整清单**（AiiDA / ASE / i-PI / Phonopy / PYCP2K / Seek-path / TAMkin 等 23 项 +
> GTH 势参数集 + 3 个用户脚本仓库）见 **`00_map.md` §2.2**。

### 6.8 官方列出的其它主题页

| 主题 | 链接 | G 层内容落点 |
|---|---|---|
| Quickstep（GPW） | <https://www.cp2k.org/quickstep> | `02_dft_methods.md` §1、`23_...` §6.1 |
| GPU 页 | <https://www.cp2k.org/gpu> | `09_build_libraries.md` §5 |
| 性能 | <https://www.cp2k.org/performance> | `19_performance_gpu_community.md` §1 |
| DBCSR | <https://www.cp2k.org/dbcsr> | `09_build_libraries.md` §3 |
| 代码结构 | <https://www.cp2k.org/dev:codestructure> | `19_performance_gpu_community.md` §8 |
| 开始开发 | <https://www.cp2k.org/dev:starting> | `19_performance_gpu_community.md` §8 |
| **周期性约定** | <https://www.cp2k.org/periodicity> | **`00_map.md` §2.1（胞 0→h 不中心化）** |
| **视频** | <https://www.cp2k.org/videos> | **跳转 YouTube**（`00_map.md` §2.4） |

---

## 7. 官方功能"能不能算 X"速查

| 想算的东西 | 官方是否支持 | 官方条目位置 |
|---|---|---|
| DFT 能量与力 | ✅ | §2.1 #1 |
| HF 能量与力 | ✅ | §2.1 #2 |
| MP2 / SOS-MP2 / RPA | ✅ | §2.1 #3 |
| 双杂化泛函 | ✅ | §2.1 #4 |
| 气相 / 周期性 | ✅ | §2.1 #5 |
| GTO / PW / GPW / GAPW 基组 | ✅ | §2.1 #6 |
| 全电子 / LAPW | ✅ | §2.1 #7 |
| GTH / NLCC 赝势 | ✅ | §2.1 #8 |
| LDA / GGA / meta-GGA | ✅ | §2.1 #9–10 |
| 杂化泛函（HFX / RI-HFX） | ✅ | §2.1 #11 |
| LibXC 泛函 | ✅ | §2.1 #12 |
| 色散校正 DFT-D2 / DFT-D3 | ✅ | §2.1 #13 |
| 非局域 vdW（B88-vdW / PBE-vdW / B97X-D） | ✅ | §2.1 #14 |
| DFT+U | ✅ | §2.1 #15 |
| 密度拟合（Bloechl / DDAPC / ADMM / RI） | ✅ | §2.1 #16 |
| 线性标度 KS 矩阵 | ✅ | §2.1 #17 |
| OT / DIIS SCF | ✅ | §2.1 #18 |
| LRIGPW | ✅ | §2.1 #19 |
| ALMO-SCF | ✅ | §2.1 #20 |
| TDDFPT 激发态 | ✅ | §2.1 #21 |
| GW 能带 | ✅ | §2.1 #22 |
| BSE 光学性质 | ✅ | §2.1 #23 |
| **k 点** | ✅（DFT、RI-HF 等） | §2.1 #24 |
| Skala 机器学习泛函 | ✅ | §2.1 #25 |
| BOMD | ✅ | §2.2 #1 |
| EMD | ✅ | §2.2 #2 |
| ASPC 积分器 | ✅ | §2.2 #4 |
| **传统 CPMD** | ❌ **官方明确不实现** | §2.2 末句 |
| QM/MM | ✅ | §2.3 |
| 几何优化 / 频率 | ✅ | §2.4 #1 |
| **NEB（4 种算法）** | ✅ | §2.4 #2 |
| 全局优化 | ✅ | §2.4 #3 |
| SCCS 溶剂化 | ✅ | §2.4 #4 |
| 半经验（AM1/PM3/PM6/RM1/MNDO…） | ✅ | §2.4 #5 |
| DFTB / SCP-TB | ✅ | §2.4 #5 |
| 经典 MD（NVE / NVT） | ✅ | §2.4 #6 |
| **Nose-Hover / CSVR 恒温器** | ✅ | §2.4 #6 |
| 元动力学（含 well-tempered） | ✅ | §2.4 #7 |
| 力场（MM） | ✅ | §2.4 #8 |
| Monte-Carlo KS-DFT | ✅ | §2.4 #9 |
| 静态 / 动态性质 | ✅ | §2.4 #10 |
| ATOM 码（赝势生成） | ✅ | §2.4 #11 |
| 基组优化 | ✅ | §2.4 #12 |

> **2026.1 / 2026.2 新增但 features 页可能未同步的功能**（见 `11_version_changelog.md`）：CNEO-DFT、SF-TDDFT、RIXS、MiMiC 接口、Dimer 初始化、固定体积晶胞优化、巨正则 SCF（恒定电势）、MACE 接口等。

---

## 8. 官方页面缺口

| 项 | 状态 | 处置 |
|---|---|---|
| `manual.cp2k.org/trunk/references.html` | **404** | 引用见 §4（来自 `faq:cite` 与 About 页） |
| `www.cp2k.org/resources` | **页面不存在**（DokuWiki 空页） | 学习资源见 §6（来自 `www.cp2k.org/docs`） |
| `features` 页未列出 2026.x 最新功能 | 版本滞后 | 见 `11_version_changelog.md` |
| BSSE 校正方法 | 缩写表有，**无专章** | G 层如实标注，见 §3 末注 |
| 完整出版物清单（BibTeX） | 官方无集中页面 | 以输出文件 `REFERENCES` 段为准 |
| `www.cp2k.org/acronyms`（官网版） | 与手册版可能不同 | 本层以手册版 `acronyms.html` 为准 |

---

## → 交叉索引

| 本文件内容 | 关联 A/F 层条目 | 关联 G 层文件 |
|---|---|---|
| 功能清单：能不能算 X | F 层 `playbook.md` 方法选择 | `02_dft_methods.md` |
| k 点支持（反证 FAQ 过时表述） | — | `02_dft_methods.md` §4、`08_errors_and_faq.md` §3.11 |
| 色散校正（DFT-D2/D3、非局域 vdW） | A 层 decide.md | `02_dft_methods.md` §11、`09_build_libraries.md` §3.6 |
| NEB 四种算法 | A 层 decide.md NEB 节 | `05_optimization.md`、`07_restarting.md` §4 |
| 恒温器（Nose-Hover / CSVR） | F 层 `playbook.md` MD 设置 | `04_sampling_md.md` |
| AIMD 类型（BOMD / EMD） | A 层 decide.md | `04_sampling_md.md` |
| 引用规范 | — | — |
| 缩写表 | A/B/C 层术语 | 全部 G 层文件 |
| 下载与 Git | F 层 `playbook.md` 环境搭建 | `09_build_libraries.md` |
| 学习资源（书 / 报告 / 教程） | B 层 `course_learned.md` | `00_map.md` |
| 版本策略（dev vs release） | — | `11_version_changelog.md` |
