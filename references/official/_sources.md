# G 层溯源清单（_sources.md）

> **用途**：记录 G 层每个文件、每一节对应的**官方 URL**、**抓取日期**、**原文完整度**与**缺口**。
> **抓取日期（全部）**：2026-09-08
> **维护约定**：新增/更新 G 层内容时，必须同步更新本表。

---

## 1. 官方站点结构

CP2K 官方资料分布在**两个站点**，职责不同：

| 站点 | 技术栈 | 内容 | 对应 G 层文件 |
|---|---|---|---|
| <https://www.cp2k.org/> | DokuWiki | 门户、About、Features、HowTo、FAQ、下载、文档资源、练习 | `00_map.md`、`08_errors_and_faq.md`（FAQ 部分）、`09_build_libraries.md`（HowTo 部分）、`10_features_resources.md` |
| <https://manual.cp2k.org/trunk/> | Sphinx | 手册正文：Getting Started、Methods、Technologies、References、Acronyms、Changelog、Units、Input Reference | `01`–`07`、`08`（troubleshooting 部分）、`09`（libraries 部分）、`11_version_changelog.md` |

> **重要导航提示**：官网 `howto` 页明确说明"**Most howtos have been moved to https://manual.cp2k.org**"。因此方法类内容优先查 manual，只有少数仍在官网。

---

## 2. 已采集页面总表

### 2.1 manual.cp2k.org（Sphinx 手册）

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 1 | `manual.cp2k.org/trunk/getting-started/installation.html` | Installation | ⚠️ **Instructions 节只有链接** | `09_build_libraries.md` §1–2 |
| 2 | `manual.cp2k.org/trunk/getting-started/troubleshooting.html` | Troubleshooting | ✅ 全文 | `08_errors_and_faq.md` §1–2 |
| 3 | `manual.cp2k.org/trunk/methods/restarting.html` | Restarting CP2K Calculations | ✅ 全文 | `07_restarting.md` |
| 4 | `manual.cp2k.org/trunk/technologies/libraries.html` | Libraries | ✅ 全文（30 个库） | `09_build_libraries.md` §3–4 |
| 5 | `manual.cp2k.org/trunk/technologies/accelerators/index.html` | Accelerators | ⚠️ **只有 2 个链接** | `09_build_libraries.md` §5.1 |
| 6 | `manual.cp2k.org/trunk/technologies/accelerators/cuda.html` | CUDA | ✅ 全文 | `09_build_libraries.md` §5.2 |
| 7 | `manual.cp2k.org/trunk/technologies/accelerators/hip.html` | HIP / ROCm | ✅ 全文 | `09_build_libraries.md` §5.3 |
| 8 | `manual.cp2k.org/trunk/technologies/eigensolvers/index.html` | Eigensolvers | ⚠️ **只有一句话** | `09_build_libraries.md` §6 |
| 9 | `manual.cp2k.org/trunk/acronyms.html` | Acronyms | ✅ 全文（约 130 条） | `10_features_resources.md` §3 |
| 10 | `manual.cp2k.org/trunk/changelog.html` | Changelog | ✅ 全文（2.0–2027.1） | `11_version_changelog.md` |
| 11 | `manual.cp2k.org/trunk/references.html` | References | ❌ **404 Not Found** | 引用规范改由 `faq:cite` + About 页提供（`10_features_resources.md` §4） |

#### 2.1.1 第二轮补充采集（2026-09-08，本轮）

> 本轮起因：用户要求"查找 CP2K 相关的官方、权威资料，先确认其官方、权威性，再看看还有什么遗漏的、可以学习的，学习并落地"。
> 采集依据：官方 GitHub README 的 Links 节 + DokuWiki 全站索引（`www.cp2k.org/?do=index`）+ Sphinx 手册大纲。

**（a）权威性核实类**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 34 | `github.com/cp2k/cp2k`（README Links 节） | CP2K GitHub 仓库 | ✅ 官方渠道清单 | `12_authority_sources.md` §2–§4 |
| 35 | `dashboard.cp2k.org/` | CP2K Dashboard | ✅ 实时测试矩阵 | `12_authority_sources.md`、`19_performance_gpu_community.md` §3 |
| 36 | `groups.google.com/group/cp2k` | CP2K Google Group | ⚠️ 页面未自称"官方"，**由官方 README 确认** | `12_authority_sources.md` §4.1 |
| 37 | Kühne et al., *J. Chem. Phys.* **152**, 194103 (2020), DOI `10.1063/5.0007045` | 官方参考论文 | ✅ 元数据完整 | `12_authority_sources.md` §5 |

**（b）输入语法与输出控制**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 38 | `manual.cp2k.org/trunk/CP2K_INPUT.html` | Input Reference（语法说明节） | ✅ 8 条语法规则 | `13_input_syntax_and_print.md` §2–§5 |
| 39 | `www.cp2k.org/conv` | Coding Convention Messages（c001–c205） | ✅ 全文 | `13_input_syntax_and_print.md` §7 |

**（c）基组与赝势**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 40 | `manual.cp2k.org/trunk/methods/dft/basis_sets.html` | Basis Sets | ✅ 全文（含 15 行硅基组逐行讲解） | `14_basis_and_potentials.md` §1–§4 |
| 41 | `manual.cp2k.org/trunk/methods/dft/pseudopotentials.html` | Pseudopotentials | ✅ 全文（GTH qN 完整清单） | `14_basis_and_potentials.md` §5–§7 |
| 42 | `github.com/cp2k/cp2k-data/blob/master/potentials/Goedecker/index.html` | GTH 赝势库清单 | ✅ 全文（约 100 元素） | `14_basis_and_potentials.md` §5 |

**（d）光学与 X 射线谱**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 43 | `manual.cp2k.org/trunk/methods/properties/optical/index.html` | Optical Spectroscopy | ✅ 全文（Casida 方程 + 选型表） | `18_posthf_semiempirical_and_xray.md` §7.3 |
| 44 | `manual.cp2k.org/trunk/methods/properties/optical/tddft.html` | Time-Dependent DFT | ✅ 全文 | `15_optical_and_xray.md` |
| 45 | `manual.cp2k.org/trunk/methods/properties/optical/bethe-salpeter.html` | GW + Bethe-Salpeter equation | ✅ 全文 | `15_optical_and_xray.md` |
| 46 | `manual.cp2k.org/trunk/methods/properties/optical/rtbse.html` | Real-Time Bethe-Salpeter Propagation | ✅ 全文（本轮新增） | `18_posthf_semiempirical_and_xray.md` §7.1 |
| 47 | `manual.cp2k.org/trunk/methods/properties/optical/vibronicspec.html` | Simulating Vibronic Effects | ⚠️ 仅第 2 节 | `18_posthf_semiempirical_and_xray.md` §7.2 |
| 48 | `manual.cp2k.org/trunk/methods/properties/x-ray/index.html` | X-Ray Spectroscopy | ⚠️ 仅链接树（4 子页未采集） | `18_posthf_semiempirical_and_xray.md` §6 |
| 49 | `manual.cp2k.org/trunk/methods/properties/stm_images.html` | STM images | ✅ 全文 | `15_optical_and_xray.md` |
| 50 | `manual.cp2k.org/trunk/methods/sampling/ehrenfest.html` | Real-Time Propagation and Ehrenfest MD | ✅ 全文 | `15_optical_and_xray.md` |

**（e）QM/MM、嵌入与机器学习势**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 51 | `manual.cp2k.org/trunk/methods/qm_mm/index.html` | QM/MM（章节索引） | ✅ 全文 | `16_qmmm_embedding_ml.md` §1 |
| 52 | `manual.cp2k.org/trunk/methods/qm_mm/qmmm.html` | Built-in Force Field QM/MM | ✅ 全文（完整蛋白质教程） | `16_qmmm_embedding_ml.md` §2 |
| 53 | `manual.cp2k.org/trunk/methods/qm_mm/gromacs.html` | GROMACS QM/MM | ⚠️ 部分 | `16_qmmm_embedding_ml.md` §3 |
| 54 | `manual.cp2k.org/trunk/methods/qm_mm/ic.html` | Image Charge QM/MM | ✅ 全文 | `16_qmmm_embedding_ml.md` §4 |
| 55 | `manual.cp2k.org/trunk/methods/embedding/index.html` | Embedding | ✅ 全文 | `16_qmmm_embedding_ml.md` §5 |
| 56 | `manual.cp2k.org/trunk/methods/machine_learning/index.html` | Machine Learning | ✅ 全文（6 种势） | `16_qmmm_embedding_ml.md` §6 |
| 57 | `manual.cp2k.org/trunk/methods/machine_learning/deepmd.html` | DeePMD | ✅ 全文 | `16_qmmm_embedding_ml.md` §6 |

**（f）约束动力学、路径与表面跳跃（本轮新增文件）**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 58 | `manual.cp2k.org/trunk/methods/sampling/constrained_dynamics.html` | Constrained molecular dynamics | ✅ 全文（含蓝月公式 + Komeiji2007） | `17_constrained_dynamics_and_paths.md` §1–§5 |
| 59 | `manual.cp2k.org/trunk/methods/optimization/nudged_elastic_band.html` | Nudged Elastic Band | ⚠️ **占位页**（4 条练习链接） | `17_constrained_dynamics_and_paths.md` §3 |
| 60 | `manual.cp2k.org/trunk/methods/sampling/newton-x.html` | Surface Hopping with NEWTON-X | ⚠️ 场景 A 完整，场景 B 截断 | `17_constrained_dynamics_and_paths.md` §6 |
| 61 | `manual.cp2k.org/trunk/methods/sampling/index.html` | Sampling（章节索引） | ✅ 全文（4 子页） | `17_constrained_dynamics_and_paths.md` §7.1 |
| 62 | `manual.cp2k.org/trunk/methods/optimization/index.html` | Optimization（章节索引） | ✅ 全文（2 子页） | `17_constrained_dynamics_and_paths.md` §7.2 |

**（g）后 HF 与半经验方法（本轮新增文件）**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 63 | `manual.cp2k.org/trunk/methods/post_hartree_fock/index.html` | Post Hartree-Fock（章节索引） | ✅ 全文 | `18_posthf_semiempirical_and_xray.md` §1 |
| 64 | `manual.cp2k.org/trunk/methods/post_hartree_fock/preliminaries.html` | Preliminaries | ✅ 全文（**含 BSSE 官方章节**） | `18_posthf_semiempirical_and_xray.md` §2 |
| 65 | `manual.cp2k.org/trunk/methods/post_hartree_fock/mp2.html` | Møller–Plesset Perturbation Theory | ✅ 全文（含完整 RI-MP2 梯度输入） | `18_posthf_semiempirical_and_xray.md` §3.1、§3.3 |
| 66 | `manual.cp2k.org/trunk/methods/post_hartree_fock/rpa.html` | RPA and LT-RI-SOS-MP2 | ✅ 全文 | `18_posthf_semiempirical_and_xray.md` §3.2 |
| 67 | `manual.cp2k.org/trunk/methods/post_hartree_fock/low-scaling.html` | Low-scaling post Hartree-Fock | ✅ 全文（含 2 个完整输入） | `18_posthf_semiempirical_and_xray.md` §4 |
| 68 | `manual.cp2k.org/trunk/methods/semiempiricals/index.html` | Semi-Empiricals（章节索引） | ✅ 全文（2 子页） | `18_posthf_semiempirical_and_xray.md` §5.1 |
| 69 | `manual.cp2k.org/trunk/methods/semiempiricals/xtb.html` | Extended Tight Binding | ✅ 全文（含 4 个完整输入） | `18_posthf_semiempirical_and_xray.md` §5.2 |
| 70 | `manual.cp2k.org/trunk/methods/semiempiricals/dftb.html` | Density Functional Tight Binding | ⚠️ **占位页** | `18_posthf_semiempirical_and_xray.md` §5.1 |
| 71 | `manual.cp2k.org/trunk/methods/properties/infrared.html` | Infrared Spectroscopy | ⚠️ **占位页**（2 条链接） | `18_posthf_semiempirical_and_xray.md` §8 |
| 72 | `manual.cp2k.org/trunk/methods/properties/index.html` | Properties（章节索引） | ✅ 全文（完整页面树） | `18_posthf_semiempirical_and_xray.md` §6、§8 |

**（h）性能、加速器与社区（本轮新增文件）**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 73 | `www.cp2k.org/performance` | CP2K Benchmark Suite | ✅ 全文（5 项基准 + 全部结果表） | `19_performance_gpu_community.md` §1 |
| 74 | `www.cp2k.org/performance:systems` | Systems used to obtain performance results | ✅ 全文（6 台机器规格） | `19_performance_gpu_community.md` §2 |
| 75 | `dashboard.cp2k.org/` | CP2K Dashboard（测试矩阵） | ✅ 实时快照 | `19_performance_gpu_community.md` §3 |
| 76 | `manual.cp2k.org/trunk/getting-started/build-with-spack.html` | Build with Spack | ✅ 全文 | `19_performance_gpu_community.md` §6 |
| 77 | `manual.cp2k.org/trunk/development/onboarding.html` | Onboarding | ✅ 全文（完整 PR 流程） | `19_performance_gpu_community.md` §8 |
| 78 | `manual.cp2k.org/trunk/technologies/libraries.html` | Libraries（详细配置要求） | ✅ 全文（补录配置细节） | `19_performance_gpu_community.md` §7 |
| 79 | `manual.cp2k.org/trunk/getting-started/troubleshooting.html` | Troubleshooting（重抓核对） | ✅ 全文 | `19_performance_gpu_community.md` §9 |

#### 2.1.2 第三轮补缺采集（2026-09-09，本轮）

> 本轮起因：用户要求"继续把上面这些缺口也补上"，即第二轮末尾如实登记的 8 类缺口。
> 采集方法：**WebFetch 会在大页面同一位置截断**，故改用 `curl` / Python `urllib.request` 抓原始 HTML，
> 再以自写转换器 `_html2md.py`（Sphinx → Markdown）与 `_doku2md.py`（DokuWiki → Markdown）转换。
> 完整度标记：✅ 全文 / ⚠️ 部分（官方页面自身截断或缺正文）/ 📑 结构化索引。

**（a）X 射线谱四子页（→ `21_xray_spectroscopy_full.md`）**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 80 | `methods/properties/x-ray/delta-scf.html` | Delta SCF（ΔSCF） | ✅ 全文（4 部分 + 2 个完整输入） | `21_xray_spectroscopy_full.md` §1 |
| 81 | `methods/properties/x-ray/tddft.html` | XAS_TDP（LR-TDDFT） | ✅ 全文（3 个完整输入 + 5 条 FAQ） | `21_xray_spectroscopy_full.md` §2 |
| 82 | `methods/properties/x-ray/delta-kick.html` | Delta Kick（δ-kick RT-TDDFT） | ✅ 全文（含完整输入） | `21_xray_spectroscopy_full.md` §3 |
| 83 | `methods/properties/x-ray/correction_scheme.html` | GW2X | ✅ 全文（含 2 个完整输入 + 3 条 FAQ） | `21_xray_spectroscopy_full.md` §4 |

**（b）机器学习势 5 页（→ `22_ml_embedding_dlaf.md`）**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 84 | `methods/machine_learning/nequip.html` | NequIP / Allegro | ✅ 全文 | `22_ml_embedding_dlaf.md` §1 |
| 85 | `methods/machine_learning/mace.html` | MACE | ✅ 全文 | `22_ml_embedding_dlaf.md` §2 |
| 86 | `methods/machine_learning/nnp.html` | Neural Network Potentials (HDNNP) | ✅ 全文 | `22_ml_embedding_dlaf.md` §3 |
| 87 | `methods/machine_learning/pao-ml.html` | PAO-ML | ✅ 全文（含 3 个完整输入） | `22_ml_embedding_dlaf.md` §4 |
| 88 | `methods/machine_learning/ace.html` | ACE | ⚠️ 正文含官方标注 **TODO** | `22_ml_embedding_dlaf.md` §5 |

**（c）嵌入与线性代数（→ `22_ml_embedding_dlaf.md`）**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 89 | `methods/embedding/kim-gordon.html` | Kim-Gordon 密度嵌入 | ✅ 全文（含完整推导 + 教程输入） | `22_ml_embedding_dlaf.md` §6 |
| 90 | `technologies/eigensolvers/dlaf.html` | DLA-Future | ✅ 全文 | `22_ml_embedding_dlaf.md` §7 |
| 91 | `methods/qm_mm/gromacs.html` | GROMACS QM/MM | ✅ 全文（补第二轮仅部分采集） | `22_ml_embedding_dlaf.md` §6 交叉引用 |

**（d）DFT 方法子页 18 个（→ `23_dft_subpages_full.md`）**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 92 | `methods/dft/index.html` | Density Functional Theory（章节索引） | ✅ 全文（18 子页） | `23_dft_subpages_full.md` §0 |
| 93 | `methods/dft/cneo.html` | Constrained Nuclear-Electronic Orbital DFT | ✅ 全文 | `23_dft_subpages_full.md` §1 |
| 94 | `methods/dft/gauxc.html` | GauXC | ✅ 全文（信息密度极高） | `23_dft_subpages_full.md` §2 |
| 95 | `methods/dft/electrostatics/index.html` | Electrostatics and Poisson Solvers | ✅ 全文 | `23_dft_subpages_full.md` §3 |
| 96 | `methods/dft/hartree-fock/index.html` | Hartree-Fock Exchange（索引） | ✅ 全文 | `23_dft_subpages_full.md` §4.0 |
| 97 | `methods/dft/hartree-fock/admm.html` | HFX with ADMM | ✅ 全文 | `23_dft_subpages_full.md` §4.3 |
| 98 | `methods/dft/hartree-fock/ri_gamma.html` | HFX-RI for Γ-Point | ⚠️ 例 2 正文截断 | `23_dft_subpages_full.md` §4.1 |
| 99 | `methods/dft/hartree-fock/ri_kpoints.html` | HFX-RI with k-Points | ⚠️ 输入尾部截断 | `23_dft_subpages_full.md` §4.2 |
| 100 | `methods/dft/local_ri.html` | Local Resolution of Identity | ✅ 全文 | `23_dft_subpages_full.md` §5 |
| 101 | `methods/dft/gpw.html` | Gaussian Plane Wave | ✅ 全文（含流程图） | `23_dft_subpages_full.md` §6.1 |
| 102 | `methods/dft/gapw.html` | Gaussian Augmented Plane Waves | ✅ 全文 | `23_dft_subpages_full.md` §6.2 |
| 103 | `methods/dft/basis_sets.html` | Basis Sets | ✅ 全文 | `23_dft_subpages_full.md` §7.1–7.4 |
| 104 | `methods/dft/pseudopotentials.html` | Pseudopotentials | ✅ 全文 | `23_dft_subpages_full.md` §7.5 |
| 105 | `methods/dft/k-points.html` | K-Points | ✅ 全文 | `02_dft_methods.md` §4（不重复） |
| 106 | `methods/dft/orbital_transformation.html` | Orbital Transformation | ✅ 全文 | `23_dft_subpages_full.md` §8 |
| 107 | `methods/dft/convergence.html` | How to make a SCF run converge | ✅ 全文 | `23_dft_subpages_full.md` §9 |
| 108 | `methods/dft/cutoff.html` | How to Converge the CUTOFF and REL_CUTOFF | ✅ 全文 | `03_scf_convergence.md` §2（不重复） |
| 109 | `methods/dft/constrained.html` | Constrained DFT | ✅ 全文 | `02_dft_methods.md` §7（不重复） |
| 110 | `methods/dft/linear_scaling.html` | Linear Scaling DFT | ⚠️ **占位页** | `23_dft_subpages_full.md` §10 |

**（e）Input Reference 段树（→ `20_input_reference_tree.md`）**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 111 | `manual.cp2k.org/trunk/CP2K_INPUT.html` | CP2K Input Reference（根） | 📑 结构化索引 | `20_input_reference_tree.md` §1–§3 |
| 112 | `CP2K_INPUT/{GLOBAL,FORCE_EVAL,MOTION,ATOM,VIBRATIONAL_ANALYSIS,EXT_RESTART,MULTIPLE_FORCE_EVALS,NEGF,SWARM,FARMING,OPTIMIZE_BASIS,OPTIMIZE_INPUT,TEST,DEBUG}.html` | 14 个顶层段页 | 📑 段名/子段/关键字全列 | `20_input_reference_tree.md` §2 |
| 113 | `CP2K_INPUT/**/*.html`（76 个第二层段页） | 第二层段 | 📑 索引表（含第三层子段与链接） | `20_input_reference_tree.md` §3 |
| 114 | `CP2K_INPUT/**/**/*.html`（269 个第三层段页） | 第三层段 | 📑 清单（按父段分组） | `20_input_reference_tree.md` §4 |

**（f）官网剩余 6 页（→ `00_map.md` §2）**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 115 | `www.cp2k.org/science` | Science（应用案例） | ✅ 全文（**79 个案例**） | `00_map.md` §2.3 |
| 116 | `www.cp2k.org/version_history` | Version History | ⚠️ **跳转页**（→ manual changelog） | `00_map.md` §2.4 |
| 117 | `www.cp2k.org/videos` | Videos | ⚠️ **跳转 YouTube**（2020-08-29） | `00_map.md` §2.4 |
| 118 | `www.cp2k.org/tutorials` | Tutorials | ⚠️ **已改名 howto，多数移至 manual** | `00_map.md` §2.4 |
| 119 | `www.cp2k.org/periodicity` | Periodicity | ✅ 全文 | `00_map.md` §2.1、`23_...` §3 |
| 120 | `www.cp2k.org/tools` | Tools | ✅ 全文（**23 个软件** + GTH 势 + 3 个脚本仓库） | `00_map.md` §2.2、`10_features_resources.md` §6.7 |

**（g）剩余 4 条 FAQ（→ `08_errors_and_faq.md`）**

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 121 | `www.cp2k.org/faq:contribute` | How can I contribute to CP2K? | ✅ 全文 | `08_errors_and_faq.md` §3.14 |
| 122 | `www.cp2k.org/faq:usagestats` | How many people use CP2K? | ✅ 全文 | `08_errors_and_faq.md` §3.15 |
| 123 | `www.cp2k.org/faq:name` | What does CP2K stand for? | ✅ 全文 | `08_errors_and_faq.md` §3.16 |
| 124 | `www.cp2k.org/faq:doing_io` | How can I do I/O? | ✅ 全文 | `08_errors_and_faq.md` §3.17 |

> **统计（第三轮，本轮）**：新增采集 **45 个条目**（#80–#124），其中 **34 个完整**、**9 个部分（截断/TODO/跳转）**、**2 个结构化索引**。
> **累计**：**124 个条目**。新增 G 层专题文件 **4 个**（`20`–`23`），G 层 `.md` 总数 **22 → 26**（专题 00–23 共 24 个 + `README.md` + `_sources.md`）。

#### 2.1.3 第四轮：官方练习集全采（2026-09-09，本轮）

**范围**：`www.cp2k.org/exercises` 全部 **21 个课程命名空间**（2014–2025）+ **248 个子页**。

| 项 | 实测值 |
|---|---|
| 索引页（`:index`） | **21 个**（其中 `exercises:common:index` 为官方现行维护版，2025/06/19 最后修改） |
| 子页总数 | **248 个** |
| 有正文的子页 | **239 个**（累计正文约 **170 万字符**） |
| 官方空链接页 | **9 个**（"This topic does not exist yet"）：`common:{blue_moon,gga,hfx,mlp,pimd,tddft,vdos,vdw,wavefun}` |
| 仅标题无正文 | **1 个**：`common:vib`（只有标题 `Vibrational Analysis`） |
| 抓取失败后重试成功 | **4 个**：`2015_uzh_molsim:ssh`、`2016_ethz_mmm:nacl_md`、`2016_uzh_cmest:defects_in_graphene`、`2018_ethz_mmm:mc2018` |

**落盘**：**`24_official_exercises.md`**（G 层第 27 个文件）。

**重点内容**（不逐页抄录全文，只提炼 + 给完整清单）：

| 主题 | 采集内容 | 落点 |
|---|---|---|
| **NEB / 过渡态** | **7 页完整可运行输入**（此前 `17_...` §3 登记为空白） | `24_...` §1 |
| AIMD / BOPMD | 官方 AIMD 界定与 BOMD 方程 | `24_...` §2.1 |
| **SGCP（第二代 CPMD）** | **CPMD/BOMD/SGCP 三方对比表** + ASPC 公式 + **6 个参数设置表** | `24_...` §2.2 |
| 系综 | NVE/NVT/NPT + g(r)，**截断 < 盒半边长且 > σ** | `24_...` §2.3 |
| 元动力学 | TiO₂ 表面甲酸/水，**~20 Å 真空**，CV 选择原则 | `24_...` §2.4 |
| **i-PI 联用** | INET/UNIX socket 配置 + **超算动态 HOST 替换脚本** | `24_...` §2.5 |
| EOS | **Birch–Murnaghan 公式** + 0.90–1.10 步长 0.025 + 收敛配方 | `24_...` §3.2 |
| PDOS/能带 | **k 点只支持 GGA；不支持杂化泛函做能带** | `24_...` §3.3 |
| 电荷密度差 / 功函数 | Cubecruncher 命令 + 含时版本 | `24_...` §3.4–§3.5 |
| 官方书单 | 8 本教材 + 5 组论文（含 DOI） | `24_...` §3.8 |
| 官方推荐工具 | 含 **VESTA / Avogadro 建 slab 教程** | `24_...` §3.9 |
| 完整清单 | **239 页**（按 21 组，含标题与字符数） | `24_...` §6 |

> **本轮统计**：新增采集条目 **269 个**（21 索引页 + 248 子页），
> 其中 **239 个有正文**、**9 个官方空链接**、**1 个仅标题**。
> **累计**：**124 + 269 = 393 个条目**。G 层 `.md` 总数 **26 → 27**。
>
> **注**：`_sources.md` 的"条目"统计口径此前为"官方文档页"，
> 本轮把 248 个练习子页计入，故累计数跳增。**两者口径一致**（都按"采集的页面数"计）。

### 2.2 www.cp2k.org（DokuWiki）

| # | URL | 页面标题 | 完整度 | 落入 G 层文件 |
|---|---|---|---|---|
| 12 | `www.cp2k.org/` | About CP2K | ✅ 全文 | `10_features_resources.md` §1 |
| 13 | `www.cp2k.org/features` | Features | ✅ 全文（2026-08-21 更新） | `10_features_resources.md` §2、§7 |
| 14 | `www.cp2k.org/faq` | Frequently Asked Questions | ✅ 目录 19 条 | `08_errors_and_faq.md` §3.1 |
| 15 | `www.cp2k.org/faq:cutoff` | How can one guess a reasonable cutoff value? | ✅ 全文 | `08_errors_and_faq.md` §3.4 |
| 16 | `www.cp2k.org/faq:ngrids` | How to choose the NGRIDS in &MGRID | ✅ 全文 | `08_errors_and_faq.md` §3.6 |
| 17 | `www.cp2k.org/faq:common_mistakes` | My simulation fails. Any ideas? | ✅ 全文（**含过时内容**） | `08_errors_and_faq.md` §3.11 |
| 18 | `www.cp2k.org/faq:kpoints` | kpoints | ✅ 全文（**已改为跳转页**） | `08_errors_and_faq.md` §3.10 |
| 19 | `www.cp2k.org/faq:speedup` | How can I speedup my calculations? | ✅ 全文 | `08_errors_and_faq.md` §3.3 |
| 20 | `www.cp2k.org/faq:mpi_vs_openmp` | Should I use MPI or OpenMP or both? | ✅ 全文 | `08_errors_and_faq.md` §3.12 |
| 21 | `www.cp2k.org/faq:hfx_eps_warning` | KS matrix not 100% occupied warning | ✅ 全文 | `08_errors_and_faq.md` §3.8 |
| 22 | `www.cp2k.org/faq:uks_convention` | Into which spin channel do excess electrons go? | ✅ 全文 | `08_errors_and_faq.md` §3.9 |
| 23 | `www.cp2k.org/faq:cite` | How to cite CP2K | ✅ 全文 | `10_features_resources.md` §4 |
| 24 | `www.cp2k.org/faq:cuda_support` | Which parts of CP2K are CUDA-accelerated? | ⚠️ 仅跳转 | `08_errors_and_faq.md` §3.13 |
| 25 | `www.cp2k.org/faq:cholesky_decomp_failed` | CPASSERT failed in cp_fm_cholesky.F | ✅ 全文 | `08_errors_and_faq.md` §3.5 |
| 26 | `www.cp2k.org/faq:new_basis_set` | How can I generate a new basis set? | ✅ 全文 | `08_errors_and_faq.md` §3.2 |
| 27 | `www.cp2k.org/faq:hint_insufficiently_exploiting_cpu_extensions` | Compiler target flags HINT | ✅ 全文 | `09_build_libraries.md` §7.1 |
| 28 | `www.cp2k.org/faq:libsmm_arguments_too_long` | Argument list too long (libsmm) | ✅ 全文 | `09_build_libraries.md` §7.2 |
| 29 | `www.cp2k.org/faq:toolchain_non_zero_exit_code_detected` | Toolchain non-zero exit code | ✅ 全文 | `09_build_libraries.md` §7.3 |
| 30 | `www.cp2k.org/howto` | HOWTOs | ✅ 全文（19 项） | `09_build_libraries.md` §2.1、`00_map.md` |
| 31 | `www.cp2k.org/docs` | More Documentation | ✅ 全文（Talks/Posters/Workshops/Reports/Theses/Books） | `10_features_resources.md` §6 |
| 32 | `www.cp2k.org/download` | Downloading CP2K | ✅ 全文 | `10_features_resources.md` §5 |
| 33 | `www.cp2k.org/resources` | — | ❌ **页面不存在**（DokuWiki 空页） | 学习资源改由 `www.cp2k.org/docs` 提供 |

> **统计（第一轮）**：已采集 33 个页面/条目，其中 **28 个完整**、**4 个不完整（占位/跳转）**、**2 个不存在（404 / 空页）**。
> **统计（第二轮，本轮）**：新增采集 **46 个条目**（#34–#79），其中 **33 个完整**、**11 个不完整（占位/仅链接/截断）**、**2 个需官方 README 佐证**。
> **累计**：**79 个条目**，覆盖 manual.cp2k.org 与 www.cp2k.org 的主要正文页 + 3 个非官网官方渠道（GitHub、Dashboard、Google Group）+ 1 篇官方参考论文。

---

## 3. G 层文件 → 来源映射

| G 层文件 | 主要来源 URL | 次要来源 |
|---|---|---|
| `README.md` | 本层自述（无外部来源） | — |
| `00_map.md` | `www.cp2k.org/`、`www.cp2k.org/howto`、`manual.cp2k.org/trunk/`、`www.cp2k.org/exercises` | `www.cp2k.org/{periodicity,tools,science,version_history,videos,tutorials}` |
| `01_global_and_units.md` | `manual.cp2k.org/trunk/CP2K_INPUT.html`（`&GLOBAL`）、`units.html`、`www.cp2k.org/howto:static_calculation` | `features` |
| `02_dft_methods.md` | `manual.cp2k.org/trunk/methods/dft/*`（含 `constrained.html`、`hartree-fock/index.html`、`k-points.html`）、`www.cp2k.org/howto:dft_u` | `features`、`libraries.html` |
| `03_scf_convergence.md` | `manual.cp2k.org/trunk/methods/scf.html`、`www.cp2k.org/howto:converging_cutoff` | `faq:cutoff`、`faq:ngrids`、`faq:common_mistakes` |
| `04_sampling_md.md` | `manual.cp2k.org/trunk/methods/sampling/*` | `features`、`acronyms.html` |
| `05_optimization.md` | `manual.cp2k.org/trunk/methods/optimization/*`、`methods/nudged_elastic_band.html`（占位） | `features`、`changelog.html` |
| `06_properties.md` | `manual.cp2k.org/trunk/methods/properties/index.html` | `methods/infrared.html`（占位）、`methods/qm_qm.html`（占位）、`methods/dft/vdw.html`（404） |
| `07_restarting.md` | `manual.cp2k.org/trunk/methods/restarting.html` | — |
| `08_errors_and_faq.md` | `manual.cp2k.org/trunk/getting-started/troubleshooting.html`、`www.cp2k.org/faq` 及各 FAQ 子页 | `changelog.html`（过时项核对） |
| `09_build_libraries.md` | `manual.cp2k.org/trunk/getting-started/installation.html`、`technologies/libraries.html`、`technologies/accelerators/*`、`technologies/eigensolvers/index.html`、`www.cp2k.org/howto`、3 条编译 FAQ | `www.cp2k.org/download` |
| `10_features_resources.md` | `www.cp2k.org/features`、`www.cp2k.org/`、`www.cp2k.org/docs`、`www.cp2k.org/download`、`manual.cp2k.org/trunk/acronyms.html`、`faq:cite` | — |
| `11_version_changelog.md` | `manual.cp2k.org/trunk/changelog.html` | 各版本 PR 链接 |
| `12_authority_sources.md` | `github.com/cp2k/cp2k` README Links 节、`dashboard.cp2k.org/`、`groups.google.com/group/cp2k`、Kühne2020 DOI | 官方渠道清单 + 4 级权威性分级 |
| `13_input_syntax_and_print.md` | `manual.cp2k.org/trunk/CP2K_INPUT.html`（语法节）、`www.cp2k.org/conv` | `01_global_and_units.md`（单位方括号）、`07_restarting.md`（printkey） |
| `14_basis_and_potentials.md` | `methods/dft/basis_sets.html`、`methods/dft/pseudopotentials.html`、`github.com/cp2k/cp2k-data` GTH 清单 | `02_dft_methods.md`（`&MGRID`）、`18`（ADMM 辅助基组） |
| `15_optical_and_xray.md` | `methods/properties/optical/tddft.html`、`bethe-salpeter.html`、`methods/properties/stm_images.html`、`methods/sampling/ehrenfest.html` | `methods/properties/optical/index.html` |
| `16_qmmm_embedding_ml.md` | `methods/qm_mm/*`、`methods/embedding/index.html`、`methods/machine_learning/*` | `06_properties.md`（§3 嵌入）、`09`（ML 势库） |
| `17_constrained_dynamics_and_paths.md` | `methods/sampling/constrained_dynamics.html`、`methods/optimization/nudged_elastic_band.html`（占位）、`methods/sampling/newton-x.html` | `methods/sampling/index.html`、`methods/optimization/index.html` |
| `18_posthf_semiempirical_and_xray.md` | `methods/post_hartree_fock/*`、`methods/semiempiricals/*`、`methods/properties/optical/rtbse.html`、`vibronicspec.html` | `methods/properties/index.html`、`methods/properties/infrared.html`（占位） |
| `19_performance_gpu_community.md` | `www.cp2k.org/performance`、`performance:systems`、`dashboard.cp2k.org/`、`getting-started/build-with-spack.html`、`development/onboarding.html` | `technologies/libraries.html`、`getting-started/troubleshooting.html` |
| `20_input_reference_tree.md` | `manual.cp2k.org/trunk/CP2K_INPUT.html` + 14 个顶层段页 + 76 个第二层段页 + 269 个第三层段页 | `www.cp2k.org/{science,version_history,videos,tutorials,periodicity,tools}` |
| `21_xray_spectroscopy_full.md` | `methods/properties/x-ray/{delta-scf,tddft,delta-kick,correction_scheme}.html` | `15_optical_and_xray.md`（页面清单）、`18_...` §6 |
| `22_ml_embedding_dlaf.md` | `methods/machine_learning/{nequip,mace,nnp,pao-ml,ace}.html`、`methods/embedding/kim-gordon.html`、`technologies/eigensolvers/dlaf.html`、`methods/qm_mm/gromacs.html` | `16_qmmm_embedding_ml.md`、`09_build_libraries.md` |
| `23_dft_subpages_full.md` | `methods/dft/{cneo,gauxc,electrostatics/index,hartree-fock/*,local_ri,gpw,gapw,basis_sets,pseudopotentials,orbital_transformation,convergence,cutoff,linear_scaling}.html` | `02_dft_methods.md`、`03_scf_convergence.md`、`14_basis_and_potentials.md` |
| `24_official_exercises.md` | `www.cp2k.org/exercises` + 21 个 `:index` + **248 个子页** | `17_...` §3（NEB 空白）、`04_sampling_md.md`、`06_properties.md`、`03_scf_convergence.md`、`21_...`（`common:lr-tddft` 同源） |
| `_sources.md` | 本文件 | — |

---

## 4. 官方原文缺口汇总（G 层不编造，如实标注）

### 4.1 占位页（官方明说"尚未撰写"）

| 页面 | 官方状态 | G 层处置 |
|---|---|---|
| `methods/optimization/nudged_elastic_band.html` | 占位页，仅 4 条外链 | 标注缺口（`17_...` §3），功能信息取自 `features` 页（B-NEB/IT-NEB/CI-NEB/D-NEB） |
| `methods/linear_scaling.html` | 占位页，仅 2 条外链 | 标注缺口 |
| `methods/properties/infrared.html` | 占位页，仅 2 条外链 | 标注缺口（`18_...` §8） |
| `methods/qm_qm.html` | 占位页，仅 1 条外链 | 标注缺口 |
| `methods/properties/index.html` | 只有链接树 | 标注缺口，给 11 项缺口清单 |
| **`methods/semiempiricals/dftb.html`** | **占位页** | 标注缺口（`18_...` §5.1） |
| **`methods/properties/raman.html`** | **占位页** | 标注缺口（`18_...` §8） |
| **`methods/properties/nmr.html`** | **占位页** | 标注缺口（`18_...` §8） |
| **`methods/qm_mm/polarizable_force_field.html`** | **占位页** | 标注缺口（`16_...` §8） |
| **`methods/qm_mm/implicit_solvation.html`** | **占位页** | 标注缺口（`16_...` §8） |
| **`development/under-the-hood.html`** | **占位页** | 标注缺口（`19_...`） |
| **`methods/properties/electrochemistry.html`** | **占位页**（仅一句 + "Indeed, to be done by J. C."） | 标注缺口 |

### 4.2 404 / 页面不存在

| 页面 | 状态 | G 层处置 |
|---|---|---|
| `manual.cp2k.org/trunk/methods/dft/vdw.html` | **404** | 色散校正信息取自 `features` 页 + `libraries.html` 的 DFTD4/TBLITE 章节 |
| `manual.cp2k.org/trunk/references.html` | **404** | 引用规范取自 `faq:cite` + About 页 |
| `www.cp2k.org/resources` | **不存在**（DokuWiki 空页） | 学习资源取自 `www.cp2k.org/docs` |

### 4.3 只有链接、无正文

| 页面 | 状态 |
|---|---|
| `getting-started/installation.html` 的 Instructions 节 | 只有链接 |
| `technologies/accelerators/index.html` | 只有 2 个链接 |
| `technologies/eigensolvers/index.html` | 只有一句话（无库清单） |
| `faq:cuda_support` | 只有跳转 |
| `faq:kpoints` | 官方主动改为跳转页 |

### 4.4 官方内容已过时（重要）

| 项 | 状态 | G 层处置 |
|---|---|---|
| `faq:common_mistakes`（2020-08-21 修改）称 "**CP2K does not have k-point sampling**" | **已过时** | `08_errors_and_faq.md` §3.11 原文照录 + 明确标注过时，并给出反证（`features` #24、`changelog` 的 k 点时间线） |
| `faq` 页整体最后修改 2020-08-21 | 多数条目未随版本更新 | 各条目加版本坐标提示 |
| `faq:cite` 给的"最新 review"为 2020-05 的 DOI | 可能已有更新 | 原样保留并标注"截至 2020-05" |
| `features` 页未列出 2026.x 新功能 | 版本滞后 | `11_version_changelog.md` 补全 |
| `acronyms.html` 的 `LSD` = Local Spin Density | 与错误消息中 `LSD` 作为 `UKS` 别名并存 | 两处都保留并说明不矛盾 |

### 4.5 官方未覆盖的主题

| 主题 | 官方状态 |
|---|---|
| ~~BSSE 校正方法~~ | ✅ **本轮更正**：官方 `post_hartree_fock/preliminaries.html` **有 BSSE 专节**（见 `18_...` §2.9），自动方案 `FORCE_EVAL/BSSE`、手动方案 `KIND/GHOST`。此前"无专章"的判断已作废 |
| 波函数文件内部二进制格式 | 未公开格式规范 |
| 跨版本波函数兼容性矩阵 | 无，只说 "may vary" |
| 版本兼容性矩阵（输入文件跨版本） | 无 |
| 完整 BibTeX 出版物清单 | 无集中页面 |
| NEWTON-X 场景 B 正文 | 官方页在 "B)" 处截断 |
| X 射线谱 4 个子页正文 | 有链接树，子页未采集 |
| Jarzynski 恒等式中 W 的计算工具 | 官方只给公式，无 CP2K 侧工具 |
| 蓝月系综通用式的实现 | 官方明确"需后处理"，指向 Komeiji2007 |

### 4.6 官方页面自身的笔误与矛盾（照录并标注，不擅改）

| 位置 | 官方原文 | 问题 | G 层处置 |
|---|---|---|---|
| `optical/rtbse.html` | `MAT_ESP` | 应为 `MAT_EXP` | `15_...` 标注 |
| `optical/rtbse.html` | `ERTS` | 应为 `ETRS` | `15_...` 标注 |
| `optical/tddft.html` | `XAD_TDP` | 应为 `XAS_TDP` | `15_...` 标注 |
| `methods/dft/basis_sets.html` | 基函数公式 `n_l×(l+1)` 对 l=2 给 3 | 但官方列了 5 个 d 轨道，自相矛盾 | `14_...` §2.4 标注 |
| `technologies/accelerators/hip.html` | `-DCP2K_WITH_GPU==Mi50...` | 双等号 | `19_...` §4.3 标注 |
| `technologies/accelerators/hip.html` | "AMD ROC TX and Tracer libray" | 拼写 | `19_...` §4.3 标注 |

---

## 5. 待补采集清单（后续可扩充）

> **本轮已完成项**（原清单中的高/中优先级多数已落地）：
> `methods/optimization/*` ✅、`methods/sampling/*` ✅、`methods/dft/basis_sets` + `pseudopotentials` ✅、
> `www.cp2k.org/performance` ✅、`www.cp2k.org/gpu` ✅（并入 accelerators）、`development/onboarding` ✅。
>
> **第三轮（2026-09-09）又完成**：X 射线谱 4 子页 ✅、DFT 方法子页 18 个 ✅、
> 机器学习 5 页 ✅、`embedding/kim-gordon` ✅、`eigensolvers/dlaf` ✅、`qm_mm/gromacs` ✅、
> Input Reference 段树 ✅（索引级）、官网 6 页 ✅、剩余 4 条 FAQ ✅。
>
> **第四轮（2026-09-09）完成**：**官方练习集全采** ✅ ——
> `www.cp2k.org/exercises` 21 个课程命名空间 + **248 个子页**（239 有正文）→ `24_official_exercises.md`。

### 5.1 仍未采集（按优先级）

| 主题 | 目标 URL | 优先级 | 状态 |
|---|---|---|---|
| Input Reference 750 关键字**逐条默认值** | `CP2K_INPUT/**/*.html` 各段页 Keywords 节 | **高** | ⬜ 段树已索引（`20_...`），**默认值/类型/单位未逐条抄录** |
| 练习与教程 | ~~`www.cp2k.org/exercises`（2014–2025，尤其 NEB 相关 4 页）~~ | ~~中~~ | ✅ **已补齐**（第四轮）→ `24_official_exercises.md`（**248 子页全采**） |
| X 射线谱 4 子页 | ~~`methods/properties/x-ray/*`~~ | ~~高~~ | ✅ **已补齐** → `21_xray_spectroscopy_full.md` |
| DFT 方法各子页 | ~~`methods/dft/*`~~ | ~~中~~ | ✅ **已补齐** → `23_dft_subpages_full.md` |
| 机器学习其余 5 页 | ~~`methods/machine_learning/*`~~ | ~~中~~ | ✅ **已补齐** → `22_ml_embedding_dlaf.md` |
| 嵌入 KIM/Gordon | ~~`methods/embedding/kim-gordon.html`~~ | ~~中~~ | ✅ **已补齐** → `22_...` §6 |
| DLAF 特征求解器 | ~~`technologies/eigensolvers/dlaf.html`~~ | ~~中~~ | ✅ **已补齐** → `22_...` §7 |
| GROMACS QM/MM 正文 | ~~`methods/qm_mm/gromacs.html`~~ | ~~中~~ | ✅ **已补齐** |
| 官网剩余页 | ~~`www.cp2k.org/{science,version_history,videos,tutorials,periodicity,tools}`~~ | ~~低~~ | ✅ **已补齐** → `00_map.md` §2.1–§2.4 |
| 剩余 FAQ | ~~`faq:{contribute,usagestats,name,doing_io}`~~ | ~~低~~ | ✅ **已补齐** → `08_errors_and_faq.md` §3.14–3.17 |
| benchmark 绘图脚本 | `tools/benchmark_plots/` 用法 | 低 | ⬜ |
| 官方 example bundle / `lib_tools.zip` | 各页下载链接 | 低 | ⬜ 二进制，非文档正文 |
| 官方页面图片 / 流程图原始 SVG | 各页内嵌图 | 低 | ⬜ 已转录为文字 |

### 5.2 复现用抓取入口

| 用途 | URL |
|---|---|
| DokuWiki 全站索引（48 页 + 12 命名空间） | `https://www.cp2k.org/?do=index` |
| Sphinx 手册大纲 | `https://manual.cp2k.org/trunk/` |
| 官方渠道权威清单 | `https://github.com/cp2k/cp2k`（README → Links 节） |

---

## 6. 维护流程（照 README.md §5 执行）

1. **只加官方内容**。任何推断、经验、课程口径一律不放 G 层。
2. **每个文件头部必须有** `> 来源：<URL>` 与 `> 抓取日期：YYYY-MM-DD`。
3. **每个新页面登记到本文件 §2**：URL、页面标题、完整度、落入哪个 G 层文件。
4. **发现 A–F 层与 G 层冲突**：先以 G 层为准修正 A–F，并在 A–F 对应位置标注"（已按官方 G 层修正，见 references/official/…）"。
5. **不删除官方原文中的版本号、默认值、警告措辞**。官方说 "experimental" 就写 "experimental"。
6. **官方补上占位页后**：重新抓取并覆盖对应章节，更新本文件 §2 与 §4 的完整度标记。

---

## 7. 抓取方法备忘（便于复现）

| 项 | 说明 |
|---|---|
| 抓取工具 | WebFetch（HTML → Markdown） |
| 抓取日期 | 2026-09-08 |
| 官网 DokuWiki 的正文抓取 | 直接访问 `www.cp2k.org/<page>`；子页用 `www.cp2k.org/<namespace>:<page>` |
| 手册 Sphinx 的正文抓取 | 直接访问 `manual.cp2k.org/trunk/<path>.html` |
| 404 判定 | WebFetch 返回 "404 Not Found" 或 "The requested URL was not found" |
| 空页判定 | DokuWiki 返回 "This topic does not exist yet" |
| 占位页判定 | 正文出现 "Unfortunately no one has gotten around to writing this page yet" 或仅列外链 |

> **注意**：DokuWiki 页面可能被随时编辑。若某条内容与 Input Reference 冲突，**以 Input Reference 为准**。
