# 庚子计算《AIMD 与 CP2K》5 天课程 — 主题式综合知识库（逐页无遗漏内化）

> 本文件是 `learn_L1.md`~`learn_L5.md`（5 份逐页提取）的主题式重组与权威沉淀，
> 覆盖 5 份 PDF（共 425 页）+ 6 份视频字幕（`1.1/1.2/2/3/4/5.txt`）的**全部**内容。
> 目的：把"讲义该学的都学了、不遗漏"，并作为 skill 知识库的**导航枢纽**——
> 凡 `decide.md`/`postprocess.md`/`course_notes.md` 已覆盖的，本文件**只索引不重写**；
> 凡 PDF/字幕**独有**的公式、参数表、脚本命令、数值案例、坑，本文件**全量收录**。
>
> **本文件是课程知识的【权威综合层】（SKILL.md 来源层 B）**，已替代 `course_notes.md` 的深度（`course_notes.md` 仅作 87 行速查，见 SKILL.md 来源层 C）。
> 需要某页原始表述时，回 `references/pdf_text/`（见该目录 `README.md` 的溯源约定），不要直接改本文件的结论。
>
> 源文件位置：
> - PDF 文本：`references/pdf_text/L1.txt`~`L5.txt`
> - 逐页提取：`references/pdf_text/learn_L1.md`~`learn_L5.md`
> - 梳理/精要：`references/course_survey.md`、`references/course_notes.md`
>
> ⚠️ **编号错位须知**：PDF 序号 ≠ 字幕"第 N 天"序号。
> - `L1.pdf`=第 1 天（AIMD 基础/势能面/水盒子/VASP 对照）
> - `L2.pdf`=**第 2 天**（CP2K 编译 + 建模），**不是**后处理
> - `L3.pdf`=**第 3 天**（CP2K 输入参数全集 / NEB / 频率 / DFT+U / HSE06）
> - `L4.pdf`=**第 5 天**（电子结构分析：TRAVIS-IR / 电荷差分 / Bader / PDOS / ELF / MO / 功函数）
> - `L5.pdf`=**第 5 天续**（自由能面 FES：PMF / slow-growth / metadynamics / QM-MM）
> - 字幕 `4.txt` 才是真正的"第 4 天"（NEB / 频率 / 表面氧化 / Au20 / 基组赝势），与 `L4.pdf` 主题几乎不重叠。
> 本库按**主题**重组，故不受编号错位影响。

---

## 0. 速查：课程主题地图

| 主题 | 主要来源 | 对应 skill 现有章节 |
|---|---|---|
| AIMD 理论基础（势能面/驻点/Verlet/系综/EPS_SCF 漂移） | L1 | `decide.md §13`、`course_notes A` |
| 后处理公式（RDF/MSD/扩散/VACF/vDOS/IR/Arrhenius） | L1/L2 | `postprocess.md`（本库 §6 补公式） |
| CP2K 编译与建模（表面终止/Wood 记号/异质结/Packmol/Au20） | L2 | `decide.md §16` |
| CP2K 输入参数全集 | L3 | `decide.md` 全文、`SKILL.md` 进阶能力 |
| NEB / CI-NEB 完整流程与脚本 | L3 + 字幕 `4.txt` | `decide.md §17/§20` |
| 频率计算（有限差分/ZPVE/虚频判据） | L3 + 字幕 `4.txt` | `decide.md §23` |
| DFT+U / HSE06 / 磁性 / 色散 | L3 + 字幕 `4.txt` | `decide.md §1/§22/§27` |
| 电子结构分析（TRAVIS/Bader/PDOS/ELF/MO/功函数） | L4 + 字幕 `5.txt` | `decide.md §14`、`postprocess.md bader` |
| 自由能面（PMF/slow-growth/metadynamics/QM-MM） | L5 + 字幕 `5.txt` | `decide.md §17`、`postprocess.md fes/travis` |

---

## 1. AIMD 理论基础（L1）

### 1.1 势能面与驻点
- **势能面（PES）**：体系能量随所有原子核坐标（3N 维）的函数 E(**R**)。
- **驻点**：∇E = 0（受力为零）。
  - **极小点（minima）**：所有本征值为正 → 稳定结构（反应物/产物/中间体）。
  - **一阶鞍点（first-order saddle point）**：有且仅有 1 个负本征值 → **过渡态（TS）**，沿该虚频模式连接初末态。
  - **高阶鞍点**：≥2 个负本征值，一般不关注。
- 反应路径：从一个极小点沿最小能量路径翻越一阶鞍点到另一个极小点；鞍点能量 − 初态能量 = **能垒**。

### 1.2 Verlet 积分（速度 Verlet）
AIMD 标准积分器，位置/速度递推（h = 时间步长 Δt）：
```
r(t+h) = r(t) + v(t)·h + ½·a(t)·h²
v(t+h) = v(t) + ½·[a(t) + a(t+h)]·h
```
- 优点：时间反演对称、能量长期守恒好、每步只算一次力。
- CP2K 默认用 Velocity Verlet；`&MD TIMESTEP` 一般 0.5 fs（金属/不稳体系可 0.25 fs）。

### 1.3 系综与恒温器（与 `decide.md §13` 互补的讲师实操）
- **NVE（微正则）**：孤立系，能量/体积/粒子数守恒；用于检验积分误差（能量漂移）。
- **NVT（正则）**：控温；最常用。
- **NPT**：控压（§13 已说明必须选 `NPT_I`/`NPT_F`，无笼统 NPT）。
- 能量漂移（energy drift）是 AIMD 积分精度核心判据：**漂移应 < 1%**，否则减 `TIMESTEP` 或查 thermostat。
- 漂移与 `EPS_SCF` 的关系（**PDF 独有表**，讲师实测水盒子）：

  | EPS_SCF | 单点能误差 | AIMD 长时能量漂移 | 评价 |
  |---|---|---|---|
  | 1E-4 | ~1e-3 eV/atom | 明显（>1%） | 太松，不可用于长 AIMD |
  | 1E-5 | ~1e-4 eV/atom | 可接受 | 平衡档 |
  | 1E-6 | ~1e-5 eV/atom | <0.1% | 高精度，慢 |

  > 实践：生产 AIMD 至少 `EPS_SCF 1E-5`；短预平衡可 1E-4；精确性质（功函数、电荷）用 1E-6。

### 1.4 VASP INCAR 对照（L1 讲师给的 AIMD 模板，供跨程序参考）
- `SMASS`（Nose-Hoover 质量参数，控温度涨落）：

  | SMASS | 含义 | 何时用 |
  |---|---|---|
  | -3 | 常量温度（无质量） | 严格 NVT 采样 |
  | -1 | 不控温（NVE） | 漂移测试 |
  | ≥0 | Nose-Hoover，值越大温度涨落越小 | 一般 NVT |

- `MDALGO`（MD 类型）：

  | MDALGO | 含义 |
  |---|---|
  | 0 | 标准 AIMD（无约束） |
  | 1 | 退火（annealing） |
  | 2 | 限制性 AIMD（PMF，蓝月法） |
  | 3 | 元动力学（VASP） |
  | 21 | 元动力学（VASP 另一写法） |

- 预平衡（equilibration）模板：先 `NSW` 短跑升温→退火稳定 → 再正式生产。
- 退火示例：`MDALGO=1` 配合温度线性变化（如 300→600→300 K）帮助跳出局部极小。

---

## 2. 后处理公式与判读（L1/L2，PDF 独有数学细节 → 已补 `postprocess.md §公式`）

> 下面每条公式/陷阱是 PDF 与字幕独有的**数学层**，已汇总进 `postprocess.md`「关键公式与判读陷阱」节；此处给索引与要点。

### 2.1 RDF 与配位数（球面积分，**关键坑**）
- g(r) 定义：径向分布函数，反映某原子周围 r 处找到另一原子的概率密度相对均匀气体的倍数。
- **配位数 = 球面积分**：`CN(<r) = ∫₀ʳ 4π·r'²·g(r')·ρ dr'`（ρ = 数密度）。
- ⚠️ **坑（讲师强调最多）**：很多同学直接在 Origin 里做**平面积分**（∫g(r)dr）算错；必须用 **4πr² 球面积分**。第一峰顶点横坐标 ≈ 第一配位层距离，第一峰面积 = 第一配位数。
- 迁移能垒估算（表面重构/RDF 应用）：用第一/第二配位层距离做 `RT·ln(...) ` 粗估（R=8.314 J/mol/K，600 K，结果 ÷96000 转 eV）。

### 2.2 MSD 与扩散系数（**VMD √MSD 坑**）
- 定义：`MSD(t) = (1/N)·Σᵢ|rᵢ(t) − rᵢ(0)|²`（多参考帧平均）。
- **Einstein 关系**：长时区 `MSD(t) ≈ 2·d·D·t`（d 维数）→ `D = slope / (2·d)`。
  - 3D：`D = slope / 6`；2D：`D = slope / 4`。
- 单位：`1 Å²/ps = 1e-4 cm²/s`。
- ⚠️ **VMD 坑（讲师当场更正）**：VMD 给出的 MSD 实际是 **√MSD（带根号）**，不是 MSD。要得正确 MSD 须**先对每个参考帧输出平方、再跨参考帧平均**（"先平方再平均"，非 PPT 初稿写的"先平均再平方"）。多参考帧：以第 0/500/1000… 帧分别为原点各算一条，平方后平均 → 更稳。
- skill 对照：`postprocess.py msd/diffusion` 内部已做平方与 PBC unwrap，无需手算。

### 2.3 VACF → vDOS → IR（**vDOS ≠ IR**）
- 速度自相关：`C(t) = <v(0)·v(t)> / <v²>`。
- 振动态密度 `vDOS(ω) = ∫ C(t)·e^{iωt} dt`（FFT）。
- ⚠️ **vDOS 不是 IR 谱**：vDOS 只含频率信息，不含偶极矩变化 → 缺振动强度。真正 IR 需偶极矩随时间变化（CP2K 用 Wannier 中心 + TRAVIS，见 §6）。
- 实操：AIMD 默认打印速度轨迹 `*-vel-1.xyz`；`postprocess.py vacf/ir` 用 `--vel`；无速度时用位置差分近似（精度有限）。

### 2.4 Arrhenius 扩散激活能（**PDF 独有 Ea 数值**）
- `D = D₀·exp(−Ea/k_BT)` → `ln D vs 1/T` 斜率 = `−Ea/k_B`。
- 讲师用水盒子不同温度 MSD 拟合得 **Ea ≈ 0.2141 eV**（液态水自扩散激活能，量级合理）。
- 稀有事件率：`k = A·exp(−Ea/RT)`（A≈10¹³ s⁻¹）；0.75 eV 能垒 @300K ≈ 1 次/秒；1.75 eV 需 ~1 秒（故 AIMD ps 量级看不到，需加速采样，见 §7）。

---

## 3. CP2K 编译与建模（L2）

### 3.1 CP2K 编译（toolchain）
- 官方 `toolchain` 脚本装依赖（工具链：编译器 + BLAS/LAPACK + FFTW + Libint + libxc + ELPA + CUDA(可选)）。
- 两种可执行：
  - `cp2k.popt`：纯 MPI（生产常用，多节点）。
  - `cp2k.psmp`：MPI×OpenMP 混合并行（单节点多核推荐）。
- 关键依赖对功能的影响：缺 libxc → 无 SCAN/Meta-GGA；缺 libint → 无 ADMM/HF/HSE06；缺 ELPA → 大对角化慢。

### 3.2 建模实操（PDF 独有）
- **表面终止（surface termination）**：切 slab 后暴露面需补终端原子（如 TiO₂(110) 桥氧/五配位 Ti）；终端类型决定表面态与功函数。
- **Wood 记号**：描述吸附层与基底晶格匹配（如 `(2×2)`、`p(2×2)`、`c(2×2)`）；用于异质结/超胞建模。
- **魔角石墨烯（magic-angle graphene）**：两层石墨烯转 ~1.1° 出现平带，建模需精确转角 + 大超胞。
- **异质结（heterojunction）**：两层不同材料堆叠；注意晶格失配（用应变或超胞匹配）；功函数差预测电子流向（见 §6.10）。
- **无定形/液体建模**：
  - `Amorphous Cell`（Materials Studio）或 **Packmol** 随机填充分子到盒子 → 再用 CP2K 退火弛豫。
  - 水盒子：Packmol 填 N 个 H₂O 到设定密度盒子。
- **Au20 团簇**：金字塔形（tetrahedral Au20），顶点/边/面心 3 类对称不等价 Au；稳定性用"质心-原子距离分布"分析（见 §8.13）。

---

## 4. CP2K 输入参数全集（L3，已与 `decide.md`/`SKILL.md` 对齐，此处收 PDF 独有要点）

> `decide.md §1–§27` + `SKILL.md`「进阶能力」已覆盖绝大多数关键字落点。以下为 PDF/字幕**独有**或需强化的点。

### 4.1 CUTOFF 单位坑（**关键**）
- `&MGRID CUTOFF` 单位是 **Ry（里德伯）**，不是 VASP 的 eV。
- VASP `ENCUT 400 eV` ≈ CP2K `CUTOFF 30 Ry`（1 Ry ≈ 13.6 eV）。
- 经验：轻元素 300–400 Ry（讲义常写 300 Ry，但金属/精确用 350–500 Ry）；别拿 eV 数值直接填 CUTOFF。

### 4.2 OT vs 对角化对照表（**PDF 独有完整版**）
| 维度 | OT（轨道变换） | 对角化（DIAGONALIZATION） |
|---|---|---|
| 速度 | 快（大体系首选） | 慢（O(N³) 但常数大） |
| 金属/窄带隙 | ❌ 不支持（无 SMEAR 路径） | ✅ 必须走对角化 + SMEAR |
| k 点 | ❌ 不支持 | ✅ 支持 |
| 取 MO/cube | ❌ 取不出完整 MO | ✅ 可取 |
| ASPC 初猜 | ✅ 可配合 | ❌ ASPC 不能与 K 点混用 |
| DFT+U | ✅ 仅 OT 路径支持 | ⚠️ 一般走 OT |
| 收敛辅助 | `MINIMIZER CG/DIIS` | `EPS_DIIS` + PULAY |

> `decide.md §22.2` 已覆盖；此处补全"ASPC 不能配 K 点""DFT+U 一般只在 OT"两条 PDF 独有约束。

### 4.3 GEO_OPT 四个收敛判据
`MAX_FORCE` / `RMS_FORCE` / `MAX_DR` / `RMS_DR` 同时达标才算收敛；NEB 同此四标准（NEB 可适当放宽，如 `MAX_FORCE 0.0006→0.001`）。

### 4.4 恒电势（constant potential，电催化，PDF 独有）
- 金属-水界面建模：PZC（零电荷电势）、加 Na⁺ 调控电极电势、水分子取向、Z 方向分布。
- 真实电势 = 功函数（真空能级 − 费米能级）相对 **SHE（标准氢电极）= 4.44 eV** 折算。
- 例：算得 Φ = 5.26 eV → 相对 SHE 电势 = 5.26 − 4.44 = +0.82 V。

### 4.5 DFT+U 渐进加 U（**PDF 独有 URAMPING 细节** → 已提升为硬规则，见 `decide.md §28`）
- `&DFT_PLUS_U`：`U_METHOD MULLIKEN`（默认）、只给 D/F 轨道加 U；有效 U = U − J，**单位必须写 `[eV]`**（默认 a.u. 会差 ~27 倍，天坑）。
- `U_RAMPING`：每步 +0.1 eV，收敛到 10³ 量级后逐步加到目标（如 4 eV），助收敛。
- 过渡金属正离子态必须加 U；金属 Fe/Ni 一般不用。
- 强关联 TM 氧化物（TiO₂、Fe₃O₄）**不加 U 会定性错误**（电子不局域、四价 Ti 不被还原）。

### 4.6 HSE06 公式（PDF 独有，补全 `decide.md §27`）
-  screened 杂化：`E_X^HSE = α·E_X^HF,sr(ω) + (1−α)·E_X^PBE,sr(ω) + E_X^PBE,lr(ω)`
- α = 0.25（HF 交换比例），ω = 0.11 bohr⁻¹（屏蔽长度）。
- 必须 `&XC &HF` + `SCREENING`；**务必 `--admm`** 降本（大体系否则天价）。

### 4.7 磁性（PDF 独有）
- 新版 `MAGNETIZATION` 直接设初猜（同 VASP `MAGMOM`）。
- Fe₃O₄ 亚铁磁：二价铁高自旋 4 单电子、三价铁高自旋 5 单电子；四配位 Td 自旋向下、八配位 Oh 自旋向上 → 三价铁分别设 `4.0 / 5.0 / −5.0`。
- 输出 Mulliken 电荷与自旋矩，看自旋电荷密度 cube 判磁性。

---

## 5. NEB / CI-NEB 完整流程（L3 + 字幕 `4.txt`，PDF 独有脚本与坑）

> `decide.md §17/§20` 已给关键字落点；此处补**实操脚本与讲师坑**。

### 5.1 插点脚本 `xyz2neb.pl`（**off-by-one 坑**）
- 用法：`xyz2neb.pl 初态.xyz 末态.xyz N`
- ⚠️ **坑：要插 4 个点需写 `N=5`**（脚本 off-by-one，生成的 0.xyz~5.xyz 中 0/5 为初末态，中间 4 个为插点）。
- 用 `cat 0.xyz 1.xyz ... 5.xyz > NEB.xyz` 拼好，VMD 检查线性插点是否合理；出现极短键（如 0.5 Å）需手动平移修正。

### 5.2 BAND 输入要点
- `RUN_TYPE BAND` + `&BAND`；`NPROC_REP`、`REPLICA` 数（初末态+插点）、`BAND_TYPE CI-NEB`。
- `ALIGN_FRAME`/`ROTATE_FRAME` 对**表面体系必须 false**（仅非周期分子体系才开，否则会扰动路径）。
- `K_SPRING`：粗算取大（0.08/0.1）易收敛但精度差，收敛后换精确值重算。
- `OPTIMIZE_END_POINTS false`（初末态已优化）。
- `ITNEB`：初插点不合理时先 IT-NEB 算几步（如 5 步）再开 CI，更稳。

### 5.3 收敛与取过渡态（**PDF 独有**）
- 收敛信息在 `cp2k-<n>.out`（**不是**主 `cp2k.out`）；四标准同几何优化，NEB 可适当放宽。
- 取过渡态：`for` 循环 `tail -125` 取各 replica 末帧拼成 `NEB.xyz`，比较各点能量，最高点 = 过渡态（例：第 3 点）。
- 插点数经验：按初末态距离，一般 4–5 个；太近 3 个、远则 6–7 个；CI-NEB 比传统 NEB 更准、可少插点。

---

## 6. 电子结构分析（L4 + 字幕 `5.txt`，PDF 独有公式与流程）

### 6.1 TRAVIS 算 IR/Raman/VCD/ROA（**必须输出 Wannier 中心**）
- 安装：下载源码 → `make`（GNU C++，默认 GCC）→ `exe/travis`。
- CP2K 须先在 `&DFT &LOCALIZE` 设 `METHOD CRAZY` + `&PRINT &WANNIER_CENTERS FILENAME wannier.xyz &EACH MD 1`，输出 `IONS+CENTERS`（原子核 + 以 X 代表的 Wannier 中心）。
- ⚠️ **坑**：TRAVIS 必须读**带 Wannier 中心的 xyz**，**不能读 `cp2k-position`**（只含原子核，无偶极变化）。
- 运行：`travis -p wannier.xyz`，交互：晶格大小（水 782 pm / 立方选 yes）、光谱类型（L2=IR）、时间步长 0.5 fs、偶极模式选 1（Wannier 方式）、X 原子电荷 2、输出整体 IR `yes`。
- 输出 `ir_spectrum_global.csv` / `ir_spectrum_H2O.csv`，Origin 画（X 轴波数 cm⁻¹，0–4000）。
- 替代（不推荐）：`&DFT &PRINT &MOMENTS` 直接输体系偶极算 IR（CP2K 官网例子，结果不好用）。

### 6.2 电荷密度 / 自旋密度 cube
- `&DFT &PRINT &E_DENSITY_CUBE STRIDE 2 2 2`（默认，文件小粗糙）/ `1 1 1`（精细，文件大）。
- 单点计算即可；输出 `ELECTRON_DENSITY`（电荷密度）与 `SPIN_DENSITY`（自旋密度）cube。
- 例：H–TiO₂(111) 电子从 H 转移到表面 Ti；Au–CeO₂(111) 电子从 Au 转移到 Ce。

### 6.3 电荷密度差分（**VESTA 操作坑**）
- 两种算法：
  - `∆ρ = ρ_AB − ρ_A − ρ_B`（体系减各片段）
  - 变形电荷密度 `∆ρ = ρ_self-consistent(AB) − ρ_atomic(AB)`
- VESTA 操作：`Edit → Edit Data → Volume Data`，用 **SUBSTRACT**（减，不是 ADD）：导入 total → 减 CO → 减 metal。黄=电荷增加、蓝/青=减少。
- 片段准备：先优化整体结构；再算两个单独单点能（结构**务必不再优化**，从整体截取坐标）；得 3 个 cube。
- 平面平均（Z 方向）：`python cube.py cp2k-cube-ELECTRON_DENSITY-1_0.cube` → 对 total/CO/metal 各做，Origin 中 `B − A − C` 得电荷重排（>0 增、<0 减）。
- 二维截面：`Edit → lattice plane`（选 3 原子定面）或 `Utilities → 2D Data Plane`；调边界（0~0.1 或 −0.05~0.05）让图像清晰。

### 6.4 Bader / Lowdin / Hirshfeld / Mulliken 原子电荷
- Bader（AIM，零通量面法，物理意义最明确）：`bader cp2k-cube-ELECTRON_DENSITY-1_0.cube` → `ACF.dat`（净电荷在 CHARGE 行）。
- **净电荷公式（q 值决定核电荷数）**：`净电荷 = 价电子数(q) − Bader 电子数`。
  - 例 CO/Ni(100)：C 用 q4 → `4 − 2.36 = +1.64 |e|`；O 用 q6 → `6 − 7.86 = −1.86 |e|`；Ni 用 q18 → `18 − 17.94 = +0.06 |e|`。
- 自旋电荷：`bader cp2k-cube-SPIN_DENSITY-1_0.cube`。
- 四方法对比（CO/Ni(100)）：

  | 方法 | Ni | C | O |
  |---|---|---|---|
  | Bader | +0.06 | +1.64 | −1.86 |
  | Lowdin | −0.062 | +0.239 | +0.138 |
  | Hirshfeld | −0.630 | +0.947 | −0.240 |
  | Mulliken | −0.327 | +0.443 | −0.076 |

  > 结论：原子电荷主要看**相对值、横向对比**，绝对数值意义有限；凝聚态/表面看 Bader 最靠谱（C 正 O 负符合化学直觉），Mulliken 常把 O 算成正（不可靠）。

### 6.5 PDOS
- `&DFT &PRINT &PDOS NLUMO -1 &LDOS LIST 1..26`（合并若干原子 PDOS）；输出 `cp2k-ALPHA_k1-1.pdos` 等。
- 画图须高斯展宽：`python new.py -s 0.01 cp2k-ALPHA_k26-1.pdos cp2k-BETA_k26-1.pdos > dos.txt`（`-s` 调 sigma；Spin up/down 分开）。
- 列：`MO Eigenvalue [a.u.]  Occupation  s  p  d  f`。费米能级在 pdos 头注释（如 `E(Fermi) = 0.122425 a.u.`）。
- CP2K 默认只算 Γ 点（尤其 OT 法），PDOS 不如多 K 点准；对角化可含更多 K 点。应用：d-band center、离子键（费米能级下新峰）vs 共价键（PDOS 峰重合）、掺杂缺陷态、表面态、吸附反馈键。

### 6.6 ELF（电子局域函数）
- 定义：`ELF(r) = 1 / [1 + (D(r)/G(r))²]`，D=Pauli 动能密度，G=Weizsäcker 动能密度。
  - `ELF=0`：完全离域（均匀电子气）；`ELF=1`：完全定域；**`ELF>0.5`**：共价键/孤对/内层电子/多中心键。
- CP2K：`&DFT &PRINT &ELF_CUBE FILENAME elf STRIDE 1 1 1` → `cp2k-elf-ELF_S1-1_0.cube` 等。
- 应用：有机/无机小分子、表面、团簇、二维材料、芳香性、氢键、金属键、多中心键、反应机理。案例：FeB₆（三中心 B-B-B 键）、Na₂He 电子化合物、ZrO₂ 氧缺陷局域电子、B₁₃ 团簇。

### 6.7 MO cube
- `&DFT &PRINT &MO_CUBES NHOMO -1 NLUMO -1 STRIDE 1 1 1 FILENAME MO` → `cp2k-MO-WFN_00001_1-1_0.cube`。
- 轨道能级单位 Hartree，画图转 eV 乘 **27.211**；费米能级在 `.out`（eV）。

### 6.8 静电势 / 功函数（**PDF 独有完整流程**）
- 功函数：`Φ = E_vac − E_Fermi`（真空能级 − 费米能级）。
- CP2K：
  ```
  &DFT
    SURFACE_DIPOLE_CORRECTION T
    SURF_DIP_DIR Z
    &PRINT &V_HARTREE_CUBE FILENAME hartree STRIDE 1 1 1
  ```
- 实例数值：真空能级 = 0.3158 a.u.，费米能级 = 0.1224 a.u. → **Φ = 5.26 eV**。
- 非对称表面（上下表面不等价）真空能级斜，需**偶极校正**；异质结（g-C₃N₄/TiO₂）功函数小者更易失电子，结合电荷差分判断电子流向。
- 分子表面 ESP：最常用**范德华表面**（一定电荷密度表面）：气相 `0.001 a.u. = 0.00675 e/Å³`、凝聚态 `0.002 a.u. = 0.0135 e/Å³`（`1 a.u. = 6.748 e/Å³`）。红=低静电势（易受亲电进攻）、蓝=高（易受亲核进攻）。

### 6.9 三条计算警告 + OT 技巧（**PDF 独有，诊断用**）
- `EMAX_SPLINE too small`：两原子距离过小（<0.0189 au）→ 调大 `EMAX_SPLINE`。
- `WFN_RESTART_FILE_NAME ... does not exist`：文件不存在 → 自动改 `ATOMIC GUESS`，计算继续（非致命）。
- OT 收敛：`MINIMIZER CG`（比默认 STRICT 快 5–20% 但稳定性差）、`LINESEARCH 2PNT`（大体系有时 3PNT）、`PRECONDITIONER FULL_ALL`（极难收敛用 GOLD）。

---

## 7. 自由能面 FES（L5 + 字幕 `5.txt`，PDF 独有公式与 CP2K 输入）

### 7.1 为什么用 AIMD 算 FES（CI-NEB 的 4 个局限）
- 能量基于 DFT 电子能量，**不是自由能**（忽略 ZPE/熵/热容）。
- 过渡态位置**非常依赖初猜**。
- 对**吸附/解离吸附/脱附能垒**难以计算。
- 不易把环境分子（如水溶剂）影响**平均化**。
- 阿伦尼乌斯 `k = A·e^{−Ea/RT}`（A≈10¹³ s⁻¹）；0.75 eV@300K≈1 次/秒；AIMD ps 量级看不到稀有事件 → 需加速采样（PMF / slow-growth / metadynamics）。

### 7.2 PMF（蓝月法 / 限制性 AIMD）
- 数学：`A(ξ₁)−A(ξ₀) = ∫_{ξ₀}^{ξ₁} (dA/dξ) dξ`；`PMF = <dA/dξ>`（限制性 MD 系综平均）。
- VASP：`ICONST` 文件定义 CV（R 距离 / A 角度 / T 二面角 / M 中点 / X,Y,Z 坐标 / S 线性组合）；`MDALGO=2` + `LBLUEOUT=.TRUE.`。
- 输出 `REPORT`：`b_m>` 行 = 自由能梯度 `λ`：`lambda |z|^(-1/2) GkT |z|^(-1/2)*(lambda+GkT)`，取 `lambda` 列平均即该 ξ 的 PMF；`grep b_m REPORT > bm.txt`。
- 插点：`nebmake.pl ../opt1/CONTCAR ../opt2/CONTCAR 10`（插 10 点 → 共 12 点）；12 套 AIMD 各跑；Origin `Statistics on Column` 求 mean+SD → `Y error` 画 → `Mathematics → Integrate` 积分得 A。实例碳酸分解能垒 ~1.3 eV。
- ⚠️ **过渡态位置强烈依赖插点密度**，点稀能量差可达 0.1 eV 级误差。

### 7.3 slow-growth（推荐，Sprik 1998）
- 只跑**一条** AIMD，CV 每步微增（`INCREM=0.0005`），共 ~10000 步；每步算 λ 取平均得连续平滑 FES。
- 比 PMF 准（实例 1.5 eV vs PMF 1.3 eV）；`INCREM` 可正可负（反向扫）；越小越准。
- 应用：Pt 表面溶出一个 Pt 原子（配位数 CV，6.49822→1.49822）。

### 7.4 metadynamics
- 原理：MD 中不断加高斯势填平势能面，直到填平（CV 来回震荡 ≥10 次认为填平）。
- 标准偏置势：`V(s) = Σᵢ h·exp(−|s−sᵢ|² / 2w²)`。
- CP2K 偏置势：`WW·Σⱼ Πₖ exp[−0.5·((ss−ss0(k,j))/SCALE(k))²]`。
- 峰高 `h`：取预估能垒 ~1/50（1 eV 能垒取 0.02 eV，越小越准但越慢）。
- 配位数公式：`ξ = [1−(r/d)⁹] / [1−(r/d)¹⁴]`，平衡时 ξ=**9/14**（最灵敏，非化学配位数）。CP2K `&COLVAR &COORDINATION FROM_KIND TO_KIND R0 NN ND`（NN/ND 可调，如 8&14、7&12）；VASP 需 100+ 行且不可调。
- HILLSPOT / `cp2k-HILLS.metadynLog`：`python gaussian.py 1 x1 x2`（1D）/ `2 x1 x2 y1 y2`（2D）画 FES。
- **WALL 仅 CP2K/Plumed 有，VASP 无**；VASP 重启 `cp HILLSPOT PENALTYPOT`；**well-tempered 仅 Plumed 实现**（VASP 不能）；**不要尝试 3D 势能面**（计算量爆炸）；1D 比 2D 小得多。

### 7.5 CP2K metadynamics 完整输入（**PDF 独有，已对齐 `decide.md §17`**）
```text
&COLVAR
  &COMBINE_COLVAR
    &COLVAR &DISTANCE ATOMS 4 50 &END
  &END COLVAR
  &COLVAR &DISTANCE ATOMS 7 49 &END
  FUNCTION CV1+CV2  VARIABLES CV1 CV2  ERROR_LIMIT 1.0E-8
&END
&COLVAR &DISTANCE ATOMS 49 50 &END   # CV2 = L(H-H)

&MOTION
  &MD ENSEMBLE NVT STEPS 200000 TIMESTEP 0.5 TEMPERATURE 450.0
     &THERMOSTAT TYPE CSVR TIMECON [fs] 200.0 &END
  &END MD
  &FREE_ENERGY
    &METADYN DO_HILLS NT_HILLS 50
      &METAVAR COLVAR 1 SCALE 0.3 WW 3.0e-3 &END
      &METAVAR COLVAR 2 SCALE 0.3 WW 3.0e-3 &END
      &WALL &QUADRATIC COLVAR 1 DIRECTION WALL_PLUS TYPE QUADRATIC
            POSITION [angstrom] 5 K [kcalmol] 40.0 &END QUADRATIC
    &END METADYN
  &END FREE_ENERGY
  &PRINT
    &TRAJECTORY &EACH MD 50 &END &END
    &RESTART &EACH MD 100 &END &END
    &HILLS COMMON_ITERATION_LEVELS 3 &END
  &END PRINT
&END MOTION
```
- 输出 `cp2k-COLVAR.metadynLog`（时间, CV1, CV1宽, CV2宽, 峰高）、`cp2k-HILLS.metadynLog`。
- CP2K 可给 CV1/CV2 **不同宽度**（VASP 必须同宽）。

### 7.6 QM-MM（CP2K，PDF 独有输入骨架）
- `METHOD MIXED` + `&MULTIPLE_FORCE_EVALS FORCE_EVAL_ORDER 2 3 MULTIPLE_SUBSYS T`。
- `&MAPPING &FORCE_EVAL_MIXED &FRAGMENT 1`（QM 原子区间）/ `&FRAGMENT 2`（MM 原子区间）。
- QM 区：`METHOD Quickstep` + `&QS METHOD PM6`（半经验，无需基组/赝势）；MM 区：`METHOD FIST` + `&MM`（EAM 势等）。
- 实例：Cyclohexaphenylene 在 Cu(111) 脱氢，CI-NEB 算能垒。

---

## 8. 实例索引（供讲解/对照，跨天汇总）

| 实例 | 天数 | 演示要点 | 对应本库节 |
|---|---|---|---|
| 水盒子 H₂O box | 第 1–2 天 | RDF/MSD/扩散标准流程（CP2K & VASP 对照）；Ea=0.2141 eV | §2 |
| TiO₂（二氧化钛） | 第 1/3 天 | DFT+U 演示（不加 U 电子不局域）；表面氧化 AIMD | §4.5/§8 |
| Cu 表面氧化 | 第 4 天（字幕） | AIMD 模拟 O₂/CO 插层、表面变氧化物；EPS_SCF ~3e6 平衡 | §4.3 |
| Au20 团簇 | 第 4 天（字幕） | 金字塔结构稳定性；质心-原子距离分析（自写 `max_center.py` ~67 行）；2 fs 步长致不稳（应用 1 fs） | §3.2 |
| CO/Ni(100) | 第 5 天 | 电荷差分、Bader 净电荷、ELF 看共价/离子成分 | §6.3/§6.4/§6.6 |
| 碳酸分解 H₂CO₃ | 第 5 天 | PMF 蓝月法（nebmake 插 12 点，能垒 ~1.3 eV） | §7.2 |
| Pt 溶解 | 第 5 天 | slow-growth（配位数 CV，能垒 ~1.5 eV） | §7.3 |
| N₂ 解离吸附 Ru(0001) | 第 5 天 | metadynamics（CV1=Ru-N 配位数，CV2=N-N 键长） | §7.4 |

---

## 9. 同音错字解码表（字幕转写修正，继续 `course_survey.md §3`）
`cp two k`=CP2K、`VSP`=VASP、`AAMD`=AIMD、`PM,F`=PMF、`METDYNAMICS`=metadynamics、
`验室/验尸`=赝势、`机组`=基组、`京弯`=晶胞、`军方位1`=MSD、`风`=峰、`差`=插、
`BSS1`=BSSE、`镜像分布函数`=RDF、`二氧化石`=TiO₂、`进二`=Au20、`ELF/ERF`=ELF、
`letis plan`=lattice plane、`2 d data play`=2D data plane、`飞艇`=fitting、`棚材料`=硼材料、
`限制AAMD`=限制性 AIMD、`自由能势能面`=FES。

---

## 10. 与现有 skill 文件的关系（避免重复、明确边界）
- **`decide.md`**：参数决策权威库（§1–§27 + 本库提升的 §28 硬规则）。本库第 4/5/6/7 节仅收 PDF 独有的公式/脚本/坑，主体以索引形式指回 decide.md。
- **`postprocess.md`**：后处理脚本用法；本库 §2 的公式已补入该文件「关键公式与判读陷阱」节。
- **`course_notes.md`**：讲师经验高层精要（A1–A5 后处理、B1–B4 参数经验）。本库是其**逐页无遗漏展开版**——notes 是"索引级"，本库是"全量级"。
- **`course_survey.md`**：资料梳理（文件→天→主题映射、错字表）。本库 §0 复用其结论。

> 审计结论（回答"是否遗漏"）：5 份 PDF（425 页，含 L4 的 4 空页、L1/L4/L5 版权页）与 6 份字幕（含字幕 `4.txt`=第4天 NEB/频率/Au20、字幕 `5.txt`=第5天振动光谱+电子结构+FES）**全部逐页/逐行处理**；所有 PDF `【新】` 标记项已落入本库对应节；BSSE 在两文件全文检索零命中（`course_notes B2` 经验无法直接溯源，保留为讲师经验级警示，已在 `decide.md §28` 标注来源待核对）。
