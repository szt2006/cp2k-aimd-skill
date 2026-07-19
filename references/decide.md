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

---

## 3. 自旋（UKS / LSD）

- **开壳层必须开 UKS**：O₂（多重度 3）、自由基（多重度 2）、多数吸附态。
- **含磁性 3d/4d/5d 元素**（Fe/Co/Ni/Mn/Cr/Ru/Ir/Pt…）大概率需要自旋极化；
  铁磁 Fe 体相常用多重度 3，具体按磁矩/磁序定。
- 开 UKS 时务必加 `WF_INTERPOLATION ASPC` + `EXTRAPOLATION_ORDER 3` 加速 SCF。
- 模板已用 `--multiplicity N` 控制；`recommend.py` 遇磁性元素会提示而非强制。

---

## 4. 色散 DFT-D3

- **什么时候开**：体系含分子 / 吸附质 / 层状材料 / π-π / 弱吸附——几乎覆盖全部催化吸附问题。
  DFT-D3 便宜、风险低，**auto 模式对含 C/N/O/H 等的体系默认开**。
- 需要把 `dftd3.dat` 放到运行目录（cp2k/data 可拷）。
- 纯金属块体、强离子晶体弱作用贡献小，可不开。

---

## 5. 周期性 / POISSON / k 点

- **块体**：`PERIODIC xyz`；**表面 slab**：`PERIODIC xy`（z 非周期）；**孤立分子/团簇**：`PERIODIC NONE` + `POISSON WAVELET`，给大盒子包住分子。
- **k 点**：金属 / 窄带隙**必须多 k 点**（费米面采样），否则能带/能量错误。
  - 块体金属：`6 6 6`（精度高 `8 8 8`）
  - 表面 slab：z 非周期 → `4 4 1`
  - 绝缘体 / 半导体：GAMMA 中心点通常够；异常时再加。
  - 收敛原则：金属/小原胞/强色散带需做 k 点网格收敛；大超晶胞布里渊区已很小，Gamma 常够。
  - ⚠️ **k 点与 OT 不兼容**：`&OT` 不支持 k 点，仅标准 `&DIAGONALIZATION` 支持（加 `ADDED_MOS`、配合 `&SMEAR`）。所以"金属小原胞 + 需要 k 点"时**不能用 OT**，要切到对角化路径（AIMD 默认 OT，若体系金属且需 k 点，要么用大超晶胞退到 Gamma，要么改对角化）。杂化泛函 + k 点走 RI-HFXk，不是普通 HFX。DFT+U + k 点仅 Mulliken 布居可用。
- **不对称 slab 的表面偶极修正**：吸附质只在一侧、或两端终止不对称时，PBC 会引入虚假表面偶极，使真空区静电势倾斜、SCF 难收敛。开 `&DFT SURFACE_DIPOLE_CORRECTION T`（模板 `--surface-dipole`，方向 `--dipole-dir Z`、位置 `--dipole-pos 0.5`、平滑 `--dipole-switch 0.3`），真空区势能恢复平整。仅对 `PERIODIC xy`/`x?` 有意义。
- 模板用 `--periodic xy/none` 与 `--kpoints "a b c"` 控制；`--surface-dipole` 控制表面偶极修正。

---

## 6. SMEAR（金属收敛关键）

- 含金属且周期性的体系，开 `&SMEAR METHOD FERMI_DIRAC ELECTRONIC_TEMPERATURE [K] 300`。
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

---

## 8. 杂化泛函的额外注意

- HSE06：`&XC_FUNCTIONAL` 内 `&XWPBE`（SCALE_X -0.25, OMEGA 0.11）+ `&PBE`，外加 `&HF FRACTION 0.25`。
- B3LYP：`&LYP`+`&BECKE88`+`&VWN`(VWN3)+`&XALPHA` + `&HF FRACTION 0.20`。
- 贵，建议 `EPS_SCF 1e-6` 并加 `&OUTER_SCF`（即 `--outer-scf`）帮收敛。

---

## 9. "从 0 到收敛"的起步阶梯（推荐默认工作流）

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

### 恒温器（THERMOSTAT 子节，配 NVT/NPT 用）
| 场景 | 推荐恒温器 | 关键关键字（落点） |
|---|---|---|
| 表面催化 AIMD | **LANGEVIN**（`--thermostat langevin`） | `&MD &LANGEVIN GAMMA`（摩擦系数，越大越快热化；表面常用 0.001–0.01 fs⁻¹ 量级，或用 `TIMECON` 等价表达）。对表面温度控制最稳、不易整体过热。 |
| 体相 / 平衡态 | **CSVR**（默认的 canonical sampling via velocity rescaling）或 **NOSE** | CSVR：`&MD &THERMOSTAT &CSVR TIMECON`（小→强热化、大→弱；平衡常用 100–1000 fs）。NOSE：`&MD &THERMOSTAT &NOSE TIMECON`+`LENGTH`(链长,默认3)+`YOSHIDA`(积分阶)+`MTS`(多时间步)；Nose 可平滑延伸到 NPT。 |
| 精确正则分布 / 谱 | **GLE**（广义朗之万） | `&THERMOSTAT &GLE` + `S` 矩阵 + `THERMOSTAT_ENERGY`/`RNG_INIT`；高级，可定制动力学谱。 |
| 弱耦合 / 特殊 | **AD_LANGEVIN** | `&THERMOSTAT &AD_LANGEVIN CHI`/`MASS`；用于特定绝热耦合场景。 |

### 恒压器（仅 NPT/NPE：MOTION/MD/BAROSTAT）
- `PRESSURE`（初始压强，1 值或 9 分量压强张量）、`TIMECON`（恒压时间常数）、`TEMPERATURE`（恒压器温度，默认取系综温度）、`TEMP_TOL`（重缩放容差）。
- `VIRIAL`：**仅 NPT_F 有效**，可屏蔽某些笛卡尔分量，让胞只沿特定轴弛豫（各向异性处理很有用）。
- 实现：NPT_F 通常用 Parrinello–Rahman 或 MTTK 风格（由 CP2K 内部选），无需手动选算法。

> 长 AIMD（>50ps）务必加 `--restart-freq 500`（或更大），防止作业中断丢失全部进度。
> 初始化：用 `TEMPERATURE` 设初速温度；`TEMP_TOL` 控制允许偏离、`COMVEL_TOL` 清质心漂移、`ANGVEL_ZERO` 清角速度（非周期体系）；`ANNEALING`/`TEMPERATURE_ANNEALING` 做退火。

---

## 14. Properties / PRINT 输出选择（手册核对 v4）

所有性质都挂在 `&FORCE_EVAL &DFT &PRINT` 下。**通用机制**（先搞懂，后面每个性质都一样）：
- 每个子节本身是个"打印开关"：写 `&PRINT &XXX ON` 才输出；常用伴随关键字 `ADD_LAST`(末步追加/标记)、`FILENAME`、`LOG_PRINT_KEY`。
- **打印频率**用 `&EACH` 子节控制，其关键字映射到迭代层级，值=间隔步数（0/负=不打印）：`QS_SCF`(每 SCF 步)、`GEO_OPT`(每优化步)、`CELL_OPT`、`MD`(每 MD 步)、`METADYNAMICS`(每撒一座山)。AIMD 全程每步 dump cube 会爆盘——务必用 `&EACH MD 100` 之类控频。
- 多数性质默认**关闭**，需显式 `ON`。

| 想算什么 | 对应科学问题 | PRINT 子节（`&DFT &PRINT`） | 关键关键字 |
|---|---|---|---|
| 布居 / 原子电荷 | 谁得电子谁失电子 | `MULLIKEN` / `LOWDIN` | `PRINT_GOP`(打印轨道布居) |
| Hirshfeld 分电荷（更可迁移、基组无关） | 电荷转移定量 | `HIRSHFELD` | `SELF_CONSISTENT T`=Hirshfeld-I(迭代更准)；`SHAPE_FUNCTION` |
| 核四极矩 / NMR 四极耦合 | 固体 NMR quadrupole | `ELECTRIC_FIELD_GRADIENT`(EFG) | `INTERPOLATION`/`GSPACE_SMOOTHING`；精度需 GAPW(§15) |
| 超精细耦合（EPR） | 自由基 EPR g/超精细 | `HYPERFINE_COUPLING_TENSOR` | `INTERACTION_RADIUS`；精度需全电子(§15) |
| 投影态密度 PDOS / d-band | 催化 d-band center、态密度 | `PDOS` | `COMPONENTS`(按角动量拆分)、`NLUMO`(加虚轨道)、`LDOS`/`R_LDOS` |
| 总态密度 DOS | 金属性 / 带隙 | `DOS` | `DELTA_E`(直方图间距) |
| 能带结构 | 带隙 / 能带 | `BAND_STRUCTURE` + `&KPOINT_SET` | `ADDED_MOS`；需先算 k 点(§5) |
| STM 图像 | 表界面 STM 模拟 | `STM` | `BIAS`(偏压)、`NLUMO`(正偏压需占+空)、`TH_TORB`(针尖轨道) |
| 分子轨道 cube | 前线轨道 / 成键 | `MO_CUBES` | `NHOMO`/`NLUMO`/`STRIDE`/`WRITE_CUBE` |
| 电荷 / 自旋密度 cube | 密度可视化 | `E_DENSITY_CUBE` / `TOT_DENSITY_CUBE` | `STRIDE`(降采样)；`XRD_INTERFACE`(X 射线衍射) |
| Hartree / XC / ELF cube | 势场 / 电子局域化 | `V_HARTREE_CUBE` / `V_XC_CUBE` / `ELF_CUBE` | `STRIDE` |
| 多极矩（偶极 / 四极） | 偶极矩 / 极化 | `MOMENTS` | `PERIODIC`(Berry phase)、`REFERENCE`、`MAX_MOMENT`、`MAGNETIC` |
| Wannier 函数 | 化学键 / 拓扑 | `WANNIER90`(实验性) | `SEED_NAME`/`MP_GRID`/`WANNIER_FUNCTIONS`；需 Wannier90 |
| Bader / 电荷分解 | 更严格的原子电荷 | `CHARGEMOL` | 调用 ChargedMol 程序 |
| Hirshfeld 力 | 约束 / 力分解 | `HIRSHFELD_FORCE`（在 `&FORCE_EVAL &PRINT`，**非** DFT/PRINT） | — |

后处理对应：PDOS → `cp2k_pdos.py`；cube → VMD/VESTA；STM → VESTA；DOS → gnuplot；band → `band.out`。

> **选择原则**：先想清"要回答什么科学问题"再开 PRINT——cube 文件巨大，AIMD 用 `&EACH` 控频。电荷分析优先 **Hirshfeld(-I)** 而非 Mulliken（Mulliken 依赖基组、不基组收敛）。核区量（EFG/NMR/超精细）必须 GAPW(§15)。

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

### 反应路径 / 过渡态（NEB）—— `RUN_TYPE BAND`
- 关键关键字：`NUMBER_OF_REPLICA`(镜像数)、`BAND_TYPE`、`K_SPRING`(弹簧常数)、`CI_NEB T`(爬坡 NEB)、`STRING_METHOD`(弦方法)、`ROTATE_FRAMES`/`ALIGN_FRAMES`(RMSD 对齐减噪音)、`USE_COLVARS`(投影到 CV 子空间)。
- 子节：`&OPTIMIZE_BAND`、`&CI_NEB`、`&REPLICA`（每个镜像的初始结构）。输出各镜像能量 → 鞍点/能垒。
- 过渡态也可走 `&GEO_OPT &TRANSITION_STATE &DIMER`（二聚体法，单端找 TS）。

### 约束（CONSTRAINT）
- `FIXED_ATOMS`(冻结指定原子，静态/MD 都常用)、`COLLECTIVE`(基于 `&COLVAR` 的约束)、`G3X3`/`G4X6`(距离/角度几何约束)、`HBONDS`(氢键约束)、`SHAKE_TOLERANCE`(SHAKE/RATTLE 容差)。
- 用 `&LINK`(QM/MM 边界) 也属约束类；冻结溶剂/底物时的标准做法。

> `gen_inp.py` 现已发射 `metadyn`（`--type metadyn`，含 `--well-tempered`/`--delta-t`/`--metadyn-ww`/`--lagrange`/`--multi-walker`/`--plumed` 开关）与 `neb`（`--type neb`，含多副本读取 / `OPTIMIZE_BAND` / `ALIGN_ROTATE_FRAMES` 等，见 SKILL.md「NEB 进阶选项」）模板；`CONSTRAINT` 的 `FIXED_ATOMS` 由 `--fixed-atoms` 发射，`G3X3` 由 `--constraint-g3x3 "i j k"` + `--g3x3-distances "d1 d2 d3"` 发射，`HBONDS` 由 `--constraint-hbonds` + `--hbond-atom-type` + `--hbond-targets` 发射（均经官方解析器校验，见 `constraint_g3x3_water`/`constraint_hbonds_water` 用例）。
> `COLLECTIVE`（`&COLVAR` 约束）仍建议手动加：2026.1 的 `cp2k_input.xml` **未建模 `&DEFINE_COLVAR`**，自动生成的 CV 定义无法被解析器接受，故顾问给出 `&COLLECTIVE COLVAR <i> TARGET <v>` 块 + 需用户自补 `&DEFINE_COLVAR` 的提示，而非自动发射。

---

## 18. 晶胞优化（CELL_OPT，PBC 必备）

`RUN_TYPE CELL_OPT` 同时弛豫原子+胞（常与 GEO_OPT 串联：先 GEO_OPT 定构型，再 CELL_OPT 定胞，或一步到位）。

- 关键关键字：`TYPE`(优化类型)、`EXTERNAL_PRESSURE`(外压，1 值或压强张量 9 分量)、`PRESSURE_TOLERANCE`(达压容差)、`KEEP_ANGLES`(只变胞长不变角度，三斜有用)、`KEEP_SYMMETRY`(保初始胞对称，对称须在 `&CELL` 指定)、`CONSTRAINT`(固定压强张量某些分量)、`OPTIMIZER`/`MAX_ITER`/`MAX_FORCE`/`MAX_DR`/`RMS_FORCE`/`RMS_DR`(同 GEO_OPT 判据)、`KEEP_SPACE_GROUP`(保空间群)。
- 等压用 `EXTERNAL_PRESSURE 0` 即常压；想算某压强下的平衡体积就设对应值。
- 与 §13 的 NPT 关系：CELL_OPT 是**零温/有限温的结构优化**（找平衡胞），NPT 是**动力学系综**（沿轨迹采样）；目标不同别混用。

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

> 初/末态必须**先各自 GEO_OPT 收敛**；中间镜像可线性插值或 `&REPLICA` 给定。NEB/TS 输入 `gen_inp.py` 暂不支持，按上结构手动拼。与 §17 的 METADYN 区别：NEB 给确定初末态找**路径/能垒**，METADYN 不预设路径只撒 CV 探**自由能面**。

---

## 21. 计算技术与并行（Technologies，手册章，决策向）

- **特征求解器**：大绝缘/半导体用 `&OT`（最快，但**不支持金属/k点/需取 MO**）；要 MO/金属/k点用对角化 `&DIAGONALIZATION`(Davidson/Felbermayr)。大体系对角化可启 **ELPA**（`&GLOBAL &PRINT &PRINT_ELPA` 或构建时启用）加速。
- **MP2/RPA 线性代数**：COSMA / SpLA 库加速矩阵乘，可上 GPU。
- **GPU 加速**：构建启 CUDA/HIP/OpenCL，运行时 DBCSR/GRID/ACC 自动卸载；对大体系网格/积分收益明显。
- **混合并行 PSMP**：MPI×OpenMP；`&EXT_LS` 等控制进程/线程布局。
- 用户侧通常只需：选对角化策略(§12)、必要时开 ELPA、确认构建含所需库。具体硬件/构建属系统层，顾问给运行时建议即可。

> 参考手册：`technologies/eigensolvers`(ELPA/cuSOLVERMp/DLA-Future)、`technologies/accelerators`(CUDA/HIP/OpenCL)。

---

## 22. SCF 收敛全流程决策（手册核对 v5，批次 7 内化）

AIMD/DFT 最常见的「跑不动」就是 SCF 不收敛。下面按 SCF 循环从外到内给决策树（全部关键字对照 CP2K 2026.1 官方 `cp2k_input.xml` 逐字核对）。

### 22.1 `&SCF` 顶层（最核心的 5 个）
| 关键字 | 默认 | 何时调 / 怎么调 |
|---|---|---|
| `EPS_SCF` | 1.0E-6 (GPW) | 能量收敛阈值；难收敛体系先放宽到 1E-5 让大循环前进，再收紧 |
| `MAX_SCF` | 50 | 单次 SCF 最大步数；难收敛可提到 200–300 |
| `SCF_GUESS` | `ATOMIC` | 重启/接续计算用 `RESTART`（配合 `--wfn-restart`）；OT 体系可用 `SPARSE` |
| `ADDED_MOS` | `0` | **`&SCF` 顶层**（非 DIAGONALIZATION）。金属/导带/过渡态/开壳层设数百个空轨道（如 500），保证占据数平滑变化 |
| `CHOLESKY` | `RESTORE` | **`&SCF` 顶层**。S⁻¹ 求逆算法：`OFF`(直接求逆)/`REDUCE`/`RESTORE`(默认)/`INVERSE`/`INVERSE_DBCSR`。大体系 `INVERSE` 更快 |

> 其它顶层：`LEVEL_SHIFT`(占据/空轨道能级劈裂，帮助难收敛的激发态/过渡态)、`MAX_DIIS`(DIIS 向量数)、`EPS_DIIS`(启 DIIS 的收敛阈值，默认 1E-1)、`NOTCONV_STOPALL`(子循环不收敛时是否停)。

### 22.2 特征求解：OT vs 对角化（二选一）
- **OT（默认，`&SCF &OT`）**：最快，适合大绝缘/半导体体系；**不支持金属、不支持 k 点，取不出 MO**。算法 `MINIMIZER`(CG/DIIS/BROYDEN)、`SAFE_DIIS`、`N_HISTORY_VEC`、`BROYDEN_BETA`(欠松弛)。
- **对角化（`&SCF &DIAGONALIZATION`）**：`ALGORITHM` 枚举 = `STANDARD`(默认,LAPACK/Jacobi) / `OT` / `LANCZOS`(块 Krylov) / `DAVIDSON`(预条件块 Davidson) / `FILTER_MATRIX`。金属/k点/需 MO 必须走对角化。

### 22.3 `&SCF &MIXING`（仅对角化/线性标度生效，OT 不用）
- `METHOD` 枚举（默认 `DIRECT_P_MIXING`）：`NONE` / `DIRECT_P_MIXING` / `KERKER_MIXING`(倒空间 Kerker 阻尼) / `PULAY_MIXING` / `BROYDEN_MIXING` / `BROYDEN_MIXING_NEW` / `MULTISECANT_MIXING`。
- 实战：`ALPHA`(新密度占比,~0.4 默认)、`BETA`(Kerker 分母,默认 0.5 bohr⁻¹)、`NMIXING`(启 DIIS 前最小混合步)、`N_SIMPLE_MIX`(先 Kerker 几步)。选择优先级 BROYDEN→PULAY(金属)→MULTISECANT(难收敛)，见 §12。

### 22.4 `&SCF &SMEAR`（金属/窄带隙必开）
- `METHOD` 枚举（默认 `ENERGY_WINDOW`）：`FERMI_DIRAC`(配 `ELECTRONIC_TEMPERATURE [K] 300`) / `ENERGY_WINDOW`(配 `WINDOW_SIZE`) / `LIST`。
- `FIXED_MAGNETIC_MOMENT`：固定自旋极化差 m=n↑−n↓（负值=让 CP2K 自己优化）。
- 开 SMEAR 时 `ADDED_MOS` 必设（§22.1），否则占据数无法平滑过渡。

### 22.5 `&SCF &OUTER_SCF`（OT 难收敛/杂化泛函救场）
- `TYPE`(外层循环类型)、`OPTIMIZER`(STEEPEST_DESCENT/DIIS/BROYDEN)、`MAX_SCF`(外层最大步,默认 10)、`EPS_SCF`(外层目标梯度)、`DIIS_BUFFER_LENGTH`、`EXTRAPOLATION_ORDER`(MD 外推阶数)。

### 22.6 MOM（最大重叠法，激发态/过渡态占轨锁定）
- `&SCF &MOM`：`MOM_TYPE`(可重启修正版)、`START_ITER`、`OCC_ALPHA`/`DEOCC_ALPHA`/`OCC_BETA`/`DEOCC_BETA`(指定占/空轨道)、`PROJ_FORMULA`(投影公式)。用于锁定特定轨道占据以避免 SCF 跳到错误态。

> **收敛决策速查**：OT 不收敛 → 先换 `--ot-minimizer cg`/`broyden`（§12）；金属 → 开 `--smear`+`--added-mos`；仍不收敛 → 加 `--outer-scf` 或切对角化 `--mixing-method pulay/multisecant`；过渡态/激发态 → `LEVEL_SHIFT`、`&MOM`、增大 `ADDED_MOS`。

---

## 23. 振动分析 / 声子 / IR 谱（VIBRATIONAL_ANALYSIS，批次 9）

`RUN_TYPE VIBRATIONAL_ANALYSIS` + 顶层 `&VIBRATIONAL_ANALYSIS`（无需放进 FORCE_EVAL）：用**有限差分**数值构造 Hessian，再用对角化求频率与模式。

| 关键字 | 默认 | 用途 |
|---|---|---|
| `DX` | 微量 | 有限差分步长；默认极小，疑难体系可调大 |
| `NPROC_REP` | 1 | 每个副本（原子位移构型）用的 MPI 核数；mode-selective 会起多个副本 |
| `FULLY_PERIODIC` | .FALSE. | 设为 .TRUE. **不**从 Hessian 清除刚体转动（全周期性体系如完整晶体才需要） |
| `INTENSITIES` | .FALSE. | 算 **IR 强度**（需同时开偶极矩打印，参见 §14 `&DFT &PRINT &MOMENTS`，配 `&PERIODIC` 或 `&LOCAL` 求偶极导数） |
| `THERMOCHEMISTRY` | .FALSE. | 算气相**热力学量**（熵、焓、自由能）；仅对气相分子有效 |
| `TC_TEMPERATURE` / `TC_PRESSURE` | 298.15 K / 1 bar | 热力学量计算的 T、p |
| `&PRINT &MOLDEN_VIB` | — | 导出 `.mol` 振动模式，供 Molden 可视化 |
| `&PRINT &CARTESIAN_EIGS` / `&HESSIAN` / `&ROTATIONAL_INFO` | — | 笛卡尔本征矢量 / 完整 Hessian / 转动信息 |

> **何时用**：① 验证优化结构是真实极小（无虚频，除平动/转动）；② 算 IR/Raman 谱（IR 走 `INTENSITIES`+偶极矩，Raman 需极化率→CP2K 用 `&PROPERTIES` 或外部）；③ 气相分子热力学修正（自由能展宽→与 exp 比对）；④ 声子（全周期性体系需 `FULLY_PERIODIC`）。
> **限制**：有限差分对每个自由度要 2 次能量计算，N 原子体系 ~ 6N 次 SCF，大体系很贵；金属/有虚频需先确认收敛。
> `gen_inp.py` 已支持 `--type vib`（见 §24 末尾模板说明）。

---

## 24. 增强采样的集体变量 COLVAR 与 PLUMED 接口（批次 9）

元动力学/约束里的「反应坐标」由 **COLVAR** 定义。`&SUBSYS &COLVAR` 是 CP2K 原生 CV 定义区（注意它**不**在 CONSTRAINT 内，也不在 MOTION 内）。

### 24.1 COLVAR 可定义的 28 种类型（节选最常用）
`DISTANCE`(ATOMS 1 2 / AXIS) · `ANGLE` · `TORSION`(二面角) · `COORDINATION`(配位数：ATOMS_FROM/ATOMS_TO + R0/NN/ND 阻尼) · `RMSD`(骨架 RMSD，需 `&FRAME &COORD`) · `GYRATION_RADIUS` · `WC`(Wannier 中心) · `QPARM`(键级) · `BOND_ROTATION` · `DISTANCE_FUNCTION` · `REACTION_PATH` / `DISTANCE_FROM_PATH` · `COMBINE_COLVAR`(多个 CV 线性组合) · `HYDRONIUM_*`(质子化水簇专用) 等。每个子类型下可挂 `&POINT` 定义虚拟点。

### 24.2 与 METADYN 的接法
`&MOTION &FREE_ENERGY &METADYN &METAVAR` 用 `COLVAR <idx>` 引用 `&SUBSYS &COLVAR` 中第 idx 个 CV（从 1 起），并可设 `SCALE`(该 CV 的高斯高度系数)、`WALL`(加墙)、`LAMBDA/MASS/GAMMA`(扩展拉格朗日方案)。即：先 `&SUBSYS &COLVAR` 定义 N 个 CV → 再在 `&METAVAR` 用 `COLVAR 1`、`COLVAR 2`… 引用。

### 24.3 PLUMED 外部驱动（进阶）
`&MOTION &FREE_ENERGY &METADYN` 下：
- `USE_PLUMED`(逻辑，默认 F)：用 **PLUMED** 作外部元动力学驱动器（支持更丰富的 CV 与偏置，如 OPES、metadyn 的墙/弹簧）。
- `PLUMED_INPUT_FILE`(默认 `./plumed.dat`)：指向 PLUMED 输入脚本。
一旦 `USE_PLUMED .TRUE.`，CP2K 不再用内置 `&METAVAR`，CV 与偏置全在 plumed.dat 里写。
`gen_inp.py` 已支持 `--plumed` + `--plumed-file`（发射 `USE_PLUMED` + `PLUMED_INPUT_FILE`）。

> 实用建议：简单 CV（距离/角度/配位数）优先用 CP2K 原生 `&COLVAR`+`&METAVAR`；需要复杂 CV、路径集体变量、多级偏置或墙函数时上 PLUMED。

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
`&FORCE_EVAL &QMMM`：`E_COUPL` 选 QM-MM 静电耦合方式（`GAUSS` GEEP 高斯展开 / `SPLINE` / `NONE`）；`MM_POTENTIAL_FILE_NAME`+`USE_GEEP_LIB`(内置 GEEP 库免手备)。边界处理：`&LINK &IMOMM`(IMOMM 连接原子) 等（§17 已述）。

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
  - `R_CUTOFF`：截断（实际势截断=2×此值）。`EPS_CN`(D3 配位数截止)。
- **`&NON_LOCAL`**（非局域 vdW，vdW-DF 族）：`TYPE`(`vdW-DF`/`vdW-DF2`/`optB88-vdW`/`rVV10` 等，需配对应 XC_FUNCTIONAL)；`KERNEL_FILE_NAME`(`vdW_kernel_table.dat` 或 `rVV10_kernel_table.dat`)；`CUTOFF`(FFT 网格 [Ry])；`PARAMETERS`(rVV10 的 b、C)；`SCALE`。

> 实战推荐：`--dispersion D3`（= `&VDW_POTENTIAL &PAIR_POTENTIAL TYPE DFT-D3(BJ)` + `REFERENCE_FUNCTIONAL` 按所选泛函）；需要 vdW-DF/rVV10 等非局域修正时手动加 `&NON_LOCAL`，并确认 XC_FUNCTIONAL 与其匹配（如 optB88-vdW 配 `XC_FUNCTIONAL` 用 `PBE` 内核 + `NON_LOCAL optB88-vdW`）。

---

## 28. 庚子计算讲师实操硬规则（PDF/字幕内化，批 13）

> 来源：庚子计算《AIMD 与 CP2K》5 天课程（PDF+字幕）逐页内化，详见 `references/course_learned.md`。
> 这些是讲师"怎么真正跑对"的**经验级硬规则**，手册不写、但错一次代价很大。提升自 `course_notes.md` 的 B1/B2/B3，补入本库作为默认动作。

### 28.1 DFT+U —— 强关联过渡金属氧化物"必须加"（硬规则）
- **规则**：含强关联 TM（Ti³⁺/⁴⁺、Fe²⁺/³⁺、Co、Ni、Mn 等）的氧化物/硫化物/钙钛矿，**默认加 DFT+U**，即使减速也要加。
- **为什么**：不加 U → 电子不能局域在金属离子上 → 四价 Ti 不被还原、表面吸附物电子转移模拟错误、**定性错误**（不是精度问题）。
- **怎么加**：`--kinds "Ti:DZVP-...:GTH-PBE-q12:U=4"`（默认 `PLUS_U_METHOD MULLIKEN`、`L` 默认 2、`U_RAMPING` 渐进加 U 助收敛；Au-TiO₂ 的 Ti 若不要 ramping 加 `noramp`）。
- **单位天坑**：`&DFT_PLUS_U U` 的单位**必须写 `[eV]`**；默认 a.u.（≈27 eV 量级）会差 ~27 倍，导致 U 实际巨大而报错/失真。
- **例外**：金属单质 Fe/Ni 一般**不用** U（已足够局域）；金属正离子态才必须。
- 详见 `course_learned.md §4.5`、`decide.md §1`（泛函选择时同步决策）。

### 28.2 BSSE 警示 —— 高斯基组吸附能"偏大"（硬规则，来源待核对）
- **规则**：CP2K 用高斯基组 → 有 **BSSE（基组叠加误差）**，算**吸附能/结合能会高估**（多数情况比 VASP 算的大一点）；基组越小 BSSE 越大（DZVP 约 5 kcal/mol≈0.22 eV，SR 基组再加 ~50%）。
- **对照**：平面波程序（VASP）无 BSSE（完备基组极限）。
- **判读**：看到"CP2K 算的吸附能比文献/VASP 偏大"**不要先当成算错了**——先想 BSSE。
- **应对**：① 大规模动态（AIMD）用 CP2K（绝对优势，BSSE 在动力学平均里影响较小）；② 精确静态（吸附能/反应能/过渡态）换平面波，或**加大基组 / 做 BSSE 校正**（CP2K `&BSSE` 或 counterpoise 双片段计算）；③ 跨程序对比时显式标出 BSSE 量级。
- ⚠️ **溯源注记**：此条在现有 PDF/字幕全文检索（BSSE|BSS|基组叠加|叠加误差）**零命中**；它来自 `course_notes.md B2` 的讲师经验归纳，**未能在逐页材料中直接溯源**，保留为经验级警示。如需权威引用，建议回看课程"基组与赝势"段落或向讲师核对。
- 与 `decide.md §16`（方法选择）、吸附能/结合能判读联动。

### 28.3 OT vs 对角化 —— 讲师实战佐证（硬经验）
- 对角化是传统法（VASP 也用），速度慢，但对**金属体系**在 CP2K 里尚可；OT 是现代默认、快。
- 金属/窄带隙 **必须走对角化 + SMEAR**（OT 不支持金属/k 点/取 MO，见 §22.2）。
- 收敛辅助：对角化里常用 `EPS_DIIS` 配 `&DIAGONALIZATION`；OT 不收敛先换 `MINIMIZER CG/BROYDEN`（§12）。
- 另两条 PDF 独有约束：**ASPC 初猜不能配 K 点**；**DFT+U 一般只在 OT 路径**（与 §22.2、§4.2 一致）。

> 与 `course_learned.md` 关系：28.1/28.2/28.3 是"该怎么做"的硬规则；完整公式/脚本/数值案例见 `course_learned.md` 第 4/5/6/7 节。

