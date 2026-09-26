# CP2K 后处理（postprocess.py）

`scripts/postprocess.py` 是 skill 闭环的第 5 步：**跑完 cp2k 之后，读它产出的文件，直接算出常用后处理量并出图(.png) + 数据(.csv)**。
呼应庚子计算讲义《AIMD 与 CP2K 讲义-1》的「AIMD 后处理」章节(轨迹查看、键长键角、势能涨落、RDF、VACF、IR、MSD、扩散系数)以及讲义 4 / 番外篇的电子结构分析(DOS/PDOS、Bader、Wannier)与自由能面(FES)。

> **批 14 回灌**：第 2 / 4 / 5 天课程里这些量本来是**手工在 VMD / VASPKIT / Origin 里一步步做**的。
> 本文件把那条手工工具链按「课程手工步骤 → 对应子命令 → 脚本内部替你做了什么 → 仍需你自己注意什么」
> 四层写进来，并补齐课程侧的公式与判读陷阱（VMD 细则、VASPKIT 工具链、自写脚本清单、TRAVIS、自由能面三法）。
> **参数决策**（泛函 / 基组 / `CUTOFF` / `EPS_SCF` / INCAR 怎么写）不属本文件，只留指针 → `decide.md §1–§7`、`§13`、`§17`、`§22`、`§24`。
> 引用格式：字幕用 `S2.txt:863–941` 这类**行号**（与 `references/pdf_text/S*.txt` 原文逐行对应），讲义用 `L5 P23` 这类**页码**。

## 衔接关系(数据怎么流)

```
gen_inp.py 布 PRINT  →  cp2k 跑  →  产出文件  →  postprocess.py 吃文件  →  出图/csv  →  diagnose 判读  →  回 gen_inp 调参
```

| CP2K 产出 | 怎么来的(输入开关) | postprocess 子命令 |
|---|---|---|
| `*.out` | 默认 | `energy` |
| `*-pos-1.xyz` 轨迹 | `&PRINT &TRAJECTORY &EACH MD 1`(模板默认) | `rdf` `msd` `diffusion` `bond` `angle` `dihedral` `adf` `cn` `zprofile` `vacf`(差分近似) |
| `*-vel-1.xyz` 速度 | `&PRINT &VELOCITIES &EACH MD 1`(**AIMD 模板默认开**；`--no-velocities` 关) | `vacf` `ir` / `power`(用 `--vel`) |
| `*.pdos` | `--properties pdos` | `pdos` |
| `*-cube-ELECTRON_DENSITY-*.cube` | `--properties cube`(`STRIDE 1 1 1`) | `cube`(平面平均) / `cdd`(差分) / `bader`(桥接) |
| `*-cube-V_HARTREE-*.cube` | `--properties vhartree` | `cube` / `workfunc`(功函) |
| `*-cube-ELF-*.cube`、`*-cube-MO_*-*.cube` | `--properties elf` / `mo` | `cube` |
| `*.out`（含 `VIB\|` 行） | `--type vib`（`&VIBRATIONAL_ANALYSIS`） | `ir-static`(静态 IR) |
| 多个 `*_diffusion.txt` 或手给 `T:D` | 多温度各跑一条 AIMD | `arrhenius`(Ea / D₀) |
| `*_rdf.csv` | `rdf` 子命令产物 | `pmf-rdf`(−RT·ln g) |
| `wannier.xyz`（含 `X` 行） | `&DFT &LOCALIZE` + `IONS+CENTERS` | `dipoles`(偶极自检) / `travis`(桥接) |
| `metadyn restart` / `HILLS` | `&FREE_ENERGY &METADYN` | `fes`(桥接 CP2K `graph`) |
| 任意轨迹 | — | `travis`(桥接，生成控制文件) |

> **关键衔接坑**：
> - AIMD 轨迹 `*-pos-1.xyz` **不含晶胞**，RDF/MSD/ADF 必须给 cell：`--cell "a b c"` 或 `--cell "ax ay az bx by bz cx cy cz"`。
>   ⚠️ **批 14 核对**：源码里那条"也可自动从 `.out` 的 `CELL|` 行解析"实际走不通——`get_cell()` 读的是 `args.out`，
>   而 **`--out` 这个选项在任何子命令上都不存在**（只有 `energy` 有一个位置参数叫 `out`，但它不需要晶胞）。
>   `--cell` 的 `--help` 文本里也写着"缺省尝试从 .out 解析"，**别被它误导**。
>   所以**必须显式 `--cell`**；漏给会退化成"包围盒近似"（`rdf` 的图标题会标 `NON-PBC(包围盒近似)`，其它子命令不会提示）。
>   9 个数的写法是给**六方/一般 3×3 晶胞**用的——这正是课程里"VMD 只能正交、六方要在建模阶段转正交"那个坑的解。
> - 速度轨迹默认就打印(AIMD 模板)。VACF/IR 直接 `--vel PROJECT-vel-1.xyz`；没有速度文件时可用 `--traj` 走位置差分近似(精度有限，脚本会提示)。
> - 时间单位默认 ps(轨迹注释行 `time=...` 即 ps)，坐标默认 Å。

## 依赖

纯 Python：`numpy` + `matplotlib`(Agg 后端，无界面也能出图)。无需外部程序即可跑核心层。
桥接层(`bader` / `fes` / `travis`)会先 `shutil.which` 检测二进制；**缺失时打印安装指引与等价手动命令，不崩溃中断**。

## 课程手工工具链 ↔ postprocess.py 等价对照（批 14 回灌）

> 课程里这些分析全是手工做的：VMD 点面板、VASPKIT 敲功能号、Origin 里拖列做公式。
> 下表把每一步映到子命令，并写清**脚本内部替你做了什么**、**哪些坑它已经规避 / 哪些还得你自己防**。
> 没有对应子命令的课程工具（VASPKIT / `md_simplify.py` / `max_center.py` /
> `xyz2neb.pl` / `cp2k_frequency*.pl` / `gaussian.py` / 交互式 TRAVIS）见后面各节。
> ⚠️ **批 15 起 `zdis_trajectory.py` 已移出这张"无对应子命令"清单** —— `zprofile --sel` 就是它的等价物。

| 课程里手工做的一步 | 出处 | 对应子命令 | 脚本内部替你做了什么 | 仍需你自己注意 |
|---|---|---|---|---|
| VMD `pbc set {…} -all` + `pbc wrap -all` 之后再算 RDF | `S2.txt:31–39`、`L3 P122` | `rdf` | 给 `--cell`（**必须显式给**，见上文「关键衔接坑」核对）后按**最小镜像约定**算原子对距离，再按 `4πr²·dr·ρ` 归一化 | `--cell` 必须给对；`--rmax` 别超过最短晶胞高度的一半，否则最小镜像约定失效 |
| VMD RDF 面板里 `skip first N frames`，丢掉未平衡段（本例 500 帧跳前 50~100） | `S4.txt:2765–2776` | 无 | — | **没有 `--skip`**：先在外部把轨迹前段截掉再喂进来 |
| VMD RDF 勾 `integral` 读配位数；或在 Origin 里乘 `4πr²` 手算 | `S2.txt:299–316`、`396–398` | `cn` | 直方图乘 `4πr²·dr` 再按（中心原子数×帧数）归一——**就是球面积分**，不存在"平面积分"那个坑 | `--rcut` 取到第一峰之后的第一个极小值，不要拿 `--rmax` 硬截 |
| VMD `Extensions → Analysis → m2msd trajectory`：先 `align`、手动取 5 个参考帧、导出后在 Origin 里**先平方再平均** | `S2.txt:1346–1372`、`1440–1522` | `msd` | 先对每个原子做 PBC **unwrap** 得连续坐标，再对**所有时间原点**做多原点平均，直接输出 Å² 的 MSD（不用再平方） | **别把 `pbc wrap` 过的轨迹喂进来**（wrap 是把原子折回盒子，反而制造跳变）；脚本要原始 `*-pos-1.xyz`，并给 `--cell` |
| VMD `m2msd` 面板里那个 **`align` 按钮**（Reference mol + Steps） | `S2.txt:1346–1372`、`496` | `msd` / `diffusion` 的 **`--align [SEL]`** | 对每帧做刚体对齐：① 扣掉**参考组**的质心平动；② 用 **Kabsch（SVD）** 消掉参考组的整体转动。默认参考组 = **除 `--sel` 选中原子以外的骨架原子**（`--align rest`），对齐后骨架不动、看被跟踪物种自己怎么动 | 不给 `--align` 就**不做对齐**（与旧版完全一致）；`diffusion` 会同时打印**对齐前/后的 D** 供你判断漂移是否显著；⚠️ `--align` 与 `--sel` 指同一批原子会把 MSD 压到 ≈0（脚本会 WARN） |
| Origin 里拟合 MSD 斜率再 `÷6`（三维）或 `÷4`（二维夹层） | `S2.txt:1562–1586` | `diffusion` | 直接线性拟合 `MSD(t)`，`D = slope/(2·dim)`，同时给 Å²/ps 与 cm²/s | **二维迁移必须 `--dim 2`**（默认 3，结果差 1.5 倍）；拟合区间 `--fit-lo/--fit-hi` 默认 0.2~0.8，避开弹道段 |
| VASPKIT `727` 算 VACF、`728` 算 vDOS（参考点间隔都填 1） | `S2.txt:863–958` | `vacf` / `ir` | `vacf` 同样是**全时间原点平均**并归一到 `C(0)=1`；`ir` 在其上加 Hanning 窗做 FFT，给 1/ps 与 cm⁻¹ 双横轴 | 脚本吃 CP2K 的 `*-vel-1.xyz`（`--vel`）；没有速度文件时才退化成位置中心差分（会打 NOTE，精度有限） |
| VMD `Mouse → Label → Bonds/Angle` 跟踪键长键角，导出进 Origin | `S2.txt:89–160` | `bond` / `angle` / `dihedral` | 1-based 索引给原子号，出时间序列 + 分布直方图 | 脚本**同样不施加 PBC**（直接算坐标差）→ 课程里"原子穿越盒子边界曲线会跳"这个坑脚本**没有替你规避**，要自己挑不穿越边界的原子 |
| `grep` OUTCAR / 读 `cp2k-1.energy` 画温度与势能，**丢掉前 500 步** | `S2.txt:236–255`、`S4.txt:2600–2623` | `energy` | 从 `.out` 抽每步总能（`ENERGY\| Total FORCE_EVAL`）与温度，出两张图 + csv | 同样**没有 `--skip`**：未平衡段要自己先截掉 |
| 自写 `zdis_trajectory.py` 算元素 Z 分布，再用 Origin `Frequency Count` 统计 | `S4.txt:3698–3743` | `zprofile --sel H` | 沿 z 的数密度剖面（`1/Å³`），自动用 `\|a×b\|` 当横截面积；`--sel` 复用 `msd --sel` 的语法（元素符号或 `1..10` 索引区间） | 不给 `--sel` 就是**全原子**（向后兼容）；课程里 H、O 分开看取向写 `--sel H` / `--sel O` 各跑一次 |
| 自写脚本累加高斯峰还原 FES；画"前 N 个 hill"的生长图 | `S5.txt:4294–4334` | `fes`（路线不同） | `fes` 调 CP2K 官方 `graph` 工具从 `metadyn restart` 重建 FES 再出图 | `fes` **不吃 `HILLS.metadynLog`**；要"只看前 400 个 hill"的演化图得用课程那个 `gaussian.py` |
| 交互式 `travis -p wannier.xyz` 算 IR | `S5.txt:123–209`、`L4 P4–P7` | `travis`（路线不同） | 生成 `*.travis.in` 控制文件后再 `travis <ctrl>` 跑；**跑之前先扫轨迹**：没有 `X` 行且 analyses 含 `ir/raman/vcd/roa` 就直接 exit 1 并给出 `&LOCALIZE` 处方；给了 `--cell` 会把 `CELL` 段写进控制文件 | 控制文件路线仍与课程交互式路线不同（默认 analyses 是 `rdf msd`）；**晶胞长度单位是 pm**（水盒输 782）脚本会提示但没法替你填；只想跑 rdf/msd 时用 `--no-require-x` 可跳过 `X` 检查 |
| VESTA 里手动 `Import` 三份 cube 再做 `Subtract` 得电荷密度差分 | `S5.txt:312–335`、`409–416` | `cdd` | `Δρ = ρ_AB − Σρ_frag`（3D 逐点相减），**校验三份 cube 的格点数与原点/步进矢量必须一致**，输出可直接进 VESTA 的 `*_cdd.cube`；`--planar-axis z` 再给平面平均图 | ⚠️ **两个片段绝不能再单独优化**（`S5.txt:319–333`，vn5 N-03/P-01）；三份 cube 必须同一 `STRIDE`/同一 `&CELL`；`∫Δρ` 不严格为 0 是正常的（看的是空间分布）；`--deformation` 走"变形电荷密度"语义 |
| 自写 `cube.py` 把 cube 沿 z 做平面平均（讲义产物名 `ChargeIntegration.txt`） | `S5.txt:399–416`、`922–923` | `cube` | 零依赖读 Gaussian cube（含 `natoms<0` / `n<0` 的 **bohr 单位约定**），沿 `--axis` 对另两轴做面内平均，输出 `*_planar.csv/.png` + 宏观平均 | 横坐标按 `原点 + k·步进矢量` 算（**不是**用 `CUTOFF` 反推网格数）；`STRIDE` 只改格点数、不改这套坐标；斜晶胞退化为投影到该轴 |
| 静电势 cube 沿 z 平面平均 → 找真空平台 → `Φ = E_vac − E_F` | `S5.txt:887–928`、`course_learned.md:808–809`、`:1320` | `workfunc` | 对 `V_HARTREE_CUBE` 做平面平均 → 两侧分别找**最长平坦段**当真空区 → `Φ = E_vac − E_F`，并给**相对 SHE 的电极电势** `U = Φ − 4.44 V` | 费米能级从 `.out` 解析（认 `Fermi energy:` / `E(Fermi) = … a.u.` / `fermi energy [eV] = …` 三种写法，**按行内单位换算**）；真空位倾斜会 WARN 并提示 `SURFACE_DIPOLE_CORRECTION` |
| 把 `VIB\|Frequency` + `VIB\|Intensities` 抄进 Origin 手动做高斯展宽 | `S4.txt:1600–1625`、`L3 P108` | `ir-static` | 读 `.out` 的 `VIB\|` 行，按 `σ = FWHM/2√(2ln2)` 高斯展宽、峰高按 intensity 加权，出静态 IR | 与 `ir` **不是同一件事**：`ir` 是 VACF 的 FFT（峰宽更真实）、`ir-static` 是人为展宽；虚频不计入谱但会单独报出来；没有 `INTENSITIES T` 时退化为等权展宽并提示 |
| 5 个温度各跑 MSD → D → Excel 里画 `log(D)` vs `1000/T` 求 Ea | `S2.txt:1650–1656`、`L1 P75–P81` | `arrhenius` | 读多组 `(T, D)`（`--d "600:1e-6" …` 或若干 `*_diffusion.txt`），线性拟合出 **Ea（eV 与 kJ/mol）**、**D₀**、R²，出图 + csv + txt | 默认横轴 `1/T`（斜率 = −Ea/k_B）；加 `--per-1000t` 用讲义口径 `log10 D vs 1000/T`（斜率 = −Ea/(2.303·k_B)，**别漏横轴带进来的 ×1000**）；R² < 0.95 会提示三种常见原因 |
| 把 RDF 那一列做 `−RT·ln g` 再 ÷96000 转 eV | `S4.txt:2881–2925` | `pmf-rdf` | 读 `*_rdf.csv`，算 `w(r) = −R·T·ln g(r)`，双 Y 轴出 `g(r)` 与 `w(r)`，同时给 kJ/mol 与 eV | `T` 必须给**实际模拟温度**；⚠️ **只适用于「第一配位层与第二配位层之间发生原子交换」这一类过程**（讲师原话「这个迁移能垒比较的局限」）；`g=0` 的区间夹地板并显式提示 |
| （前置自检）想确认轨迹里到底有没有偶极起伏 | `S5.txt:83–137` | `dipoles` | 解析含 `X` 行的 `wannier.xyz`：`μ = Σ Z_i r_i − 2·Σ r_X`，出每帧 μx/μy/μz/|μ| 时间序列 + 分布 | `--nuclear-charges` **必填**（不自动猜有效电荷）；偶极是直线 ⇒ WARN「TRAVIS 白跑」；**不替代** TRAVIS（TRAVIS 还要做 ACF 与变换、Raman/VCD） |

## 关键公式与判读陷阱（庚子讲义内化，批 13）

> 下面公式/坑来自《AIMD 与 CP2K》讲义 PDF 与字幕逐页内化（详见 `references/course_learned.md` 第 2 节）。
> 写在这里是因为它们是**判读后处理结果对不对**的硬标准；脚本已内部实现，但人要先懂公式才不会误判。

### RDF 与配位数（球面积分，**最易算错**）
- `g(r)`：径向分布函数，某原子周围 r 处找到另一原子的概率密度相对均匀气体的倍数。
- **配位数 = 球面积分**：`CN(<r) = ∫₀ʳ 4π·r'²·g(r')·ρ dr'`（ρ = 数密度）。**必须**用 `4πr²` 球面积分，不能直接在 Origin 里做平面积分 `∫g(r)dr`（讲师强调最多人错的地方）。
- 第一峰顶点横坐标 ≈ 第一配位层距离；第一峰面积 = 第一配位数；第二峰 = 第二配位层。
- 脚本：`postprocess.py rdf`（自动 PBC 归一化）+ `cn`（由 RDF 积分得 CN）。给 `--cell`。
- **晶胞前提（VMD 手工路线）**：VMD 只能给**正交晶胞**加 PBC，六方晶胞（石墨烯、二硫化钼这类）"在 VMD 里是没法添加边界条件的"，所以要在**建模阶段**就把六方晶胞转成直角晶胞——对原晶格矢量乘一个转换矩阵（`S2.txt:605–632`；RDF 必须先加 PBC 见 `S2.txt:340–356`、`L3 P122`）。
  - 反差点：`postprocess.py rdf` 用**最小镜像约定**，`--cell` 支持一般的 9 个数 3×3 晶胞，所以"六方必须先转正交"这条**在 skill 里被规避了**；代价是 `--rmax` 不能超过最短晶胞高度的一半。
- **水的一/二峰实测值**（O 为中心、H 为配位原子）：第一峰积分 ≈ **2**（分子内 O–H），第二峰积分 ≈ **3.97 ≈ 4**（氢键壳层），第三层往后就不明显了（`S2.txt:427–457`）。
- **第一峰顶点 ≈ 1.1 Å 的物理含义**：它是**水分子内的 O–H 共价键**，不是一般意义的配位距离（`S2.txt:317–331`、`401–406`）——用 `cn --rcut` 时别把 1.1 Å 当成配位半径。
- **两配位层之间有没有原子交换**：看 RDF 在**第一、第二配位层之间**的概率密度是否为零；为零 = 该时间尺度内不发生原子交换（水与水之间不换氢），有值 = 在交换（酸性溶液里的 H₃O⁺ 就会在这里出密度）（`S2.txt:528–553`）。

### MSD 与扩散（**VMD √MSD 坑**）
- 定义：`MSD(t) = (1/N)·Σᵢ|rᵢ(t) − rᵢ(0)|²`（多参考帧平均，先做 PBC unwrap）。
- **Einstein**：长时区 `MSD(t) ≈ 2·d·D·t` → `D = slope / (2·d)`；3D 用 `/6`，2D 用 `/4`。
- 单位：`1 Å²/ps = 1e-4 cm²/s`。
- ⚠️ **VMD 坑（讲师当场更正）**：VMD 给的 MSD 实际是 **√MSD（带根号）**。要得正确 MSD 须**先对每个参考帧平方、再跨参考帧平均**（"先平方再平均"，PPT 初稿写成"先平均再平方"被同学指出更正）。多参考帧：以第 0/500/1000… 帧分别为原点各算一条，平方后平均更稳。
- 脚本：`postprocess.py msd` / `diffusion` 内部已做平方与 unwrap，无需手算；给 `--cell`。
- **横坐标时间步长 = `TIMESTEP`（VASP 的 `POTIM`）× 抽帧间隔**——课程里"要根据两个方面来输入"：例 `POTIM = 2` fs、`md_simplify.py 20`（每 20 帧取一帧）→ 每帧 **40 fs**；漏填横轴，斜率（进而 D）会**错 20 倍**（`S2.txt:1386–1422`）。
  - 脚本对应：`--dt` 只在轨迹注释**没有** `time=` 时才生效；抽帧后若注释仍带 `time=`，横轴会自动正确；但 VMD/Origin 导出的裸 xyz 丢了注释，就**必须**显式 `--dt <抽帧后的步长>`。
- **二维 ≠ 三维**：`D = 斜率/(2·dim)`，三维 `÷6`，**二维（如双层石墨烯夹层里的离子迁移）`÷4`**，不是 `÷6`（`S2.txt:1562–1586`）→ 脚本对应 `--dim 2`。
- **PBC 的方向性（最容易一把梭的地方）**：RDF **必须**加 PBC；而算 MSD 时讲师明确说"最好别加那个格子边界，加上那个格子边界的话**它会跳**"（`S4.txt:3126–3131`；讲义同口径：RMSD 计算最好不要加 `pbc set`，否则原子穿越边界算不对，`L3 P125`）。
  - 两者不矛盾：`pbc wrap` 是把原子**折回**盒子（制造跳变），而 MSD 需要的是**解包裹**（unwrap，消除跳变）。`postprocess.py msd` 做的是 **unwrap**，所以要给 `--cell` 而不是先把轨迹 wrap 一遍。

### VACF → vDOS → IR（**vDOS ≠ IR**）
- `C(t) = <v(0)·v(t)> / <v²>`；`vDOS(ω) = FFT[C(t)]`。
- ⚠️ vDOS **不是**红外谱：vDOS 只含频率、不含偶极矩变化 → 缺振动强度。真正 IR 需偶极矩随时间变化，CP2K 用 **Wannier 中心 + TRAVIS**（见 `course_learned.md §6.1`）；CP2K 自带 `&MOMENTS` 直接输偶极的方法"不好用"（讲师评价）。
- 脚本：`postprocess.py vacf` / `ir`（用 `--vel` 吃速度轨迹；无速度用 `--traj` 位置差分近似，精度有限）。

### Arrhenius 扩散激活能（讲师实测数值）
- `D = D₀·exp(−Ea/k_BT)` → `ln D vs 1/T` 斜率 = `−Ea/k_B`；讲义口径是 **`log D` vs `1000/T`**，
  斜率 = `−Ea/(2.303·k_B)`（`learn_L3.md:832`；可用 `arrhenius --per-1000t` 走这条口径）。
- ⚠️ **归属更正（2026-10，两轮重核）**：旧版此处写"讲师用**水盒子**不同温度 MSD 拟合得 **Ea ≈ 0.2141 eV**（**液态水**自扩散）"——**归属错了**。`Ea = 0.2141 eV` 出自
  **练习二：Li₁₀GeP₂S₁₂ 锂离子迁移**（5 个温度 600/800/1000/1200/1400 K 各 80 ps → VASPKIT 722 各得 MSD → D → Arrhenius），
  拟合截距 **−3.35865**、斜率 **−1.07871**，取 `k_B = 8.6173×10⁻⁵ eV` ⇒ `1.07871 × 2.303 × 8.6173e-5 × 1000 = 0.2141 eV`
  （`L1.txt:1170`、`L3.txt:2272`「求得：E = 0.2141 eV」；600–1400 K 做"水"在物理上也不成立）。
  权威更正见 `course_learned.md:340–344`、`:1808`。**同一处错误文本也曾出现在 `playbook.md:117`**（已由合并方处理）。
- 稀有事件率 `k = A·exp(−Ea/RT)`（A≈10¹³ s⁻¹）：0.75 eV 能垒 @300K ≈ 1 次/秒；1.75 eV 需 ~1 秒 → AIMD（ps 量级）看不到，需加速采样（PMF / slow-growth / metadynamics，见 `course_learned.md` 第 7 节）。
- 脚本：`postprocess.py arrhenius --d "600:1.0e-6" "800:5.0e-6" "1000:2.0e-5"`（或 `--diffusion a.txt b.txt …`）。

### RDF → 势能面：`−RT·ln g` 的适用局限（含一处口播疑误）
- 做法：把 RDF 那一列做 `−RT·ln g`（R = 8.314 J·mol⁻¹·K⁻¹，T 用**实际模拟温度**，例 600 K），再 ÷96000 转 eV（1 eV ≈ 96 kJ/mol；讲师口播"9 万 6"）（`S4.txt:2881–2894`、`2909–2925`）。
- **局限**：只能算"**第一配位层与第二配位层之间发生原子交换**"的能垒，别的过程套不上（讲师原话"这个迁移能垒比较的局限"，`S4.txt:2864–2870`、`2969–2972`）。
- ⚠️ **数值疑误**：同一段里讲师先读出两个纵轴值 −0.21 与 −0.06（差 **0.15**），口播结论却是"大约是在 **1.5** 个电子伏特左右"（`S4.txt:2957–2962`）；紧接着引用的文献值是 **0.23 eV**（`S4.txt:2968`）。引用时按 **0.15 eV** 理解，并**标注字幕口播疑为转写 / 口误**，不要照抄 1.5 eV。

### NEB 与 AIMD 的分工（扩散系数谁算得准）
- 用 NEB 算**能垒**可以；但 NEB 的**指前因子非常不准** → "用 NEB 去算它的扩散系数是不准确的"（`S2.txt:1640–1650`）。
- AIMD 走的是**相反的途径**：先把扩散系数算出来（MSD 斜率），再用 Arrhenius（`ln D vs 1/T`）反推 `Ea`（`S2.txt:1650–1656`）——与本节前面「Arrhenius 扩散激活能」是一套。
- NEB 插点脚本的 off-by-one 见下节 `xyz2neb.pl`；NEB 输入怎么拼见 `decide.md §20`。

### 自由能面三法：PMF / slow growth / metadynamics（课程第 5 天）
- **三法定位**：PMF（约束 MD，把"自由能对受限自由度的梯度"积分）、slow growth、metadynamics（`S5.txt:2378–2383`）。NVT 系综给的是**亥姆霍兹自由能 A**；要吉布斯自由能得用 NPT，两者差一个 PV 项（一般可忽略，"一般来说我们就是用 NVT 系统去模拟就可以了"）（`S5.txt:2301–2321`）。
- **PMF / 伞采样对插点密度的依赖**：每一个受限自由度取值都要**单独跑一条完整的 AIMD 轨迹**再做统计平均（"本来键长是 1 Å，现在扩大到 1.1 Å，再做完整一条模拟"）→ 插点越密成本线性上涨；讲师例子里"做 PMF 要十一二条轨迹才能拿到一张图"（`S5.txt:2423–2440`、`3084–3086`）。
- **λ 是什么**：自由能对受限自由度的**梯度**，别名 blue moon（`REPORT` 里的 `b_m` 行）；`grep b_m REPORT > bm.txt`，先做平均再做积分（`S5.txt:2451–2459`、`2880–2911`）。
- **slow growth 的 `INCREM`：实为 0.0005，不是 0.005**（字幕口播 0.005 是**丢了一个零**）：
  - 反推证据：同一段给出的 CV 序列是 `0.1705 → 0.1710 → 0.1715`，每步只涨 **0.0005**（`S5.txt:3136–3139`）；
  - 讲义明写 `INCREM = 0.0005`："每一步增大 0.0005，一共跑 10000 步，即从 0.1700 → 5.1700"（`L5 P23`）。
  - 后果：填 0.005 会**大 10 倍**——1000 步就扫完，而且更容易崩（讲师原话"这个 0.005 已经是一个比较大的数值了……结构控制不住它就会崩溃掉"，`S5.txt:3075–3078`）。CV 要从大到小扫就把 `INCREM` 设成负值（`L5 P24`）。
- **metadynamics 的 HILLS 文件列**：`cp2k-HILLS.metadynLog` 共 **6 列**——时间、CV1、CV2、CV1 宽度、CV2 宽度、峰高（`S5.txt:4256–4270`）。VASP 侧 `HILLSPOT` **没有时间列**（1 个 CV 三列：CV1/峰高/峰宽；2 个 CV 四列）（`L5 P36`）——自己写累加脚本时别把时间列当成 CV。
- **CP2K 相对 VASP 的两个差异**：
  1. **峰高 `WW` 必须对所有 CV 一致，宽度 `SCALE(k)` 可以按 CV 不同**（CP2K 支持每个 CV 一个宽度；VASP 侧只能给所有 CV 用同一个宽度，字幕此处转写残缺，原意是"VASP 没有这个自由度"）。理由：`WW` 在连乘之外、`SCALE(k)` 在连乘之内（`S5.txt:4269–4293`；公式见 `L5 P52`）。
  2. **`&WALL` 加墙只有 CP2K（或外挂 PLUMED）能做，VASP 做不了**——讲师称之为 VASP 做 metadynamics"最大的一个缺点"（`S5.txt:4110–4158`）。上限墙**必须**加：官方 QM/MM 练习里不加墙，H₂ 生成后跑进真空层、CV 从三四 Å 跑到二三十 Å，"这个 METADYNAMICS 是做不完的"；下限可以不设，真低于 1 Å 说明 MD 参数就有问题（`S5.txt:4234–4245`）。`K` 取四五十到 100 kcal/mol；`WALL_MINUS`/`WALL_PLUS` 定上下限，**方向定义错整个模拟就废**（`S5.txt:4128–4144`）。
- **收敛判据**：跟踪两个 CV 随时间的变化（把这两列拿出来画图），**来回跳跃 ≥10 次**才算把势能面填平；只跳一两次就下结论误差很大。本例填平约花 **80 ps**（`S5.txt:3857–3889`）。
- **CV 选取**：单 CV 控制多键反应，势能面抬高到一定程度后会**跳到不想要的解离态**（如变成 OH + COOH），两个极小值重叠后势能面就没法分析了 → 换 CV 或加第二个 CV（`S5.txt:3892–3915`）。峰参数**先粗后精**：先用大而粗的高斯峰跑一段，精修阶段再用小峰；窄盆地用窄峰、宽盆地用宽峰，可中途重启换参数（`S5.txt:3916–3969`）。
- 输入落点：`&COLVAR` 放 `&SUBSYS` 下（几维就写几个 CV），`&FREE_ENERGY` 与 `&MD` 在 `&MOTION` 下**并列**（`S5.txt:4024–4079`）——放错层级算不出来；具体取值决策见 `decide.md §17`、`§24`。
- skill 侧：`fes` 子命令走 CP2K 官方 `graph`（从 `metadyn restart` 重建），**不吃 `HILLS.metadynLog`**；`--ndim` 必须填真实 CV 数。要做课程那种"只看前 N 个 hill 的势能面生长图"，用课程自带的 `gaussian.py`（见下节）。

### 判读联动（结果是否合理）
- 能量漂移 >1%（`energy` 子命令看）→ 减 `TIMESTEP` / 查 thermostat（§22、§13）。
- MSD 非线性、D 随拟合区间剧变 → 模拟太短，延长生产阶段。
- FES 未填满（minima 不全）→ 加 metadynamics 步数 / 调 HILL 高度（`fes` 子命令，`-ndim` 必须填真实 CV 数）。
- PDOS 费米面非零（金属）却没展宽 → 提示加 `--smear`。

## VASPKIT 工具链（VASP 侧的课程主线，批 14）

> 这是本文件此前**全文零命中**的一块。课程第 2 天的 VACF / vDOS / MSD / 异质结全是 VASPKIT 做的；
> skill 面向 CP2K，所以这里只作**对照与概念来源**记录——遇到 VASP 轨迹时知道该敲哪个功能号。

**⚠️ 时效性更正**：讲义第 1 天给的 VACF 脚本路线**已弃用**——`xdat2vdat.pl`（VASP 不输出每步速度，
只能"每两点坐标差 ÷ 时间步长"求速度）以及 Qijing Zheng 写的 `vacf.py`（一次输出 `pcf.png` 径向分布 /
`pdos.png` / `vacf.png`，讲义第 1 天把它当成 vDOS→红外谱的路线），讲师在第 2 天明确说：
"这个脚本是一个比较老的脚本，**现在我们都不用了**，现在我们用 VASPKIT 这个程序直接就可以算"
（`S2.txt:738–748`；旧脚本见 `L1 P71`、`L1 P72`）。看到教程里还在用 `xdat2vdat.pl` / `vacf.py`，
应视为过时路线。

| 功能号 | 名称 | 讲师的操作要点 |
|---|---|---|
| `72` | 分子动力学后处理模块总入口 | 727 / 728 / 722 都在它下面（`S2.txt:863–871`） |
| `727` | VACF（速度自相关函数） | ① **选原子**：可以输全部元素（如 H、O → 整个体系），也可以输**某一个分子 / 某几个原子 / 某个官能团**的原子序号——大体系（如单原子催化剂上吸附的 CO）只算关心区域的振动贡献，否则 vDOS "峰太多了，也比较乱"；② 读 `XDATCAR`；③ 问 **skip 前面多少帧**（当作预平衡，例 1000 帧 → 从 1001 帧开始算）；④ 问**参考点间隔**——正常填 **1**，即轨迹上每一个点都当参考，"这样算出来的数值会更为准确一些"；⑤ 内部用 **FFT 加速**，很长的轨迹也很快；⑥ 输出 VACF 数据 → Origin。看前 0~1000 点即可：从剧烈振荡收敛到 0，**振荡强弱是体系振动强弱的判据**（水的 O–H 振动强烈 → 曲线在趋零时剧烈振荡；硅晶体熔化则平缓趋零）（`S2.txt:863–941`、`1006–1043`） |
| `728` | vDOS（振动态密度） | ① 选横坐标单位——用**波数**；② 同样选元素（H、O = 全体系）；③ 同样 skip 前 1000 帧、间隔填 1；④ 输出 vDOS 文件 → Origin，横坐标取 0~4000 cm⁻¹；⑤ 做红外对比时讲师习惯把纵坐标倒过来（`S2.txt:942–971`） |
| `722` | average MSD（**只有新版 VASPKIT 才有**） | 老版本没有这个功能（"如果用老版本的同学应该是没有这个功能的"）。① 选元素——LiGePS 固态电解质里只算 **Li**，另外三种元素是骨架、不发生迁移；② skip 前 N 帧（例 1000，当预平衡）；③ 参考点间隔填 1（每一帧都当参考，"得到的数据才会更为精确"）；④ 内部同样用**傅里叶变换加速**；⑤ 输出 `MSD.data` → Origin；⑥ 还可以单独输出 x / y / z 三个方向的 MSD（理想状态是直线）（`S2.txt:1165–1240`） |
| `804` | 异质结（heterojunction）搜索 | ① 准备两个结构文件；② 输入 **mismatch tolerance**——一般 **2%~3%** 合理，超过 3% 虽然能建出模型，但一优化就有可能崩塌；柔性材料（石墨烯、g-C₃N₄）容忍度更大；③ 输入**层间距**（例 2.5 Å）与**真空层厚度**（一般留 **15 Å**）；④ 程序自动取两材料边长的**最小公倍数**并遍历所有转换矩阵组合，列出所有可能的异质结供挑选（几十秒）；⑤ **mismatch 先给小**（例 0.5），找不到再逐步放宽（`S2.txt:3908–3972`） |

配套口径（与 `postprocess.py` 的关系见前面的对照表）：

- **VASPKIT 只能得 vDOS，不能得红外谱**：它拟合的是速度自相关函数，"这个 vDOS 里面它没有包含这个偶极的信息，所以说它并不是直接反映的那个红外光谱"（`S5.txt:20–26`）；要真 IR 必须"偶极 + 速度一起做变换"（`S2.txt:761–769`）。
- **静态频率计算的峰宽是人为高斯展宽，AIMD 的展宽才真实**：直接做频率计算只得到一个单值频率，画谱时的峰宽是人为加的；AIMD → VACF → FFT 得到的 vDOS，峰宽是"更为真实的一种情况"（`S2.txt:794–807`）。
- VASP 侧参数（INCAR 怎么设）不属本文件，超出 skill 主体范围，仅作对照。

## VMD 实操细则（课程第 2 / 4 天，手工路线的坑）

> 这些是**手工路线**的操作细节。用 `postprocess.py` 时大部分不必再做，但对照表里标了"仍需注意"的几条必须知道。

**1) PBC 脚本（RDF 必须加）**
- 命令行版：`pbc set {a b c α β γ} -all` + `pbc wrap -all`，"那这样我就把这周期性边界条件给加成功了"（`S2.txt:31–39`）；讲师给的六行脚本按不同材料只改晶胞数值（`S4.txt:2646–2656`）。
- 水盒子例：`pbc set {7.820 7.821 7.823} –all` / `pbc wrap –all`（`L1 P55`、`L3 P72`）。
- 也可以不用命令行、直接在 VMD 面板上加（讲师当天就是面板加的；命令行版本在录屏时反而容易把 VMD 卡死）（`S2.txt:357–380`）。
- **RDF 一定要加**：不加就不会算镜像里的邻居，"求算这个径向分布函数其实是不准确的"（`S2.txt:340–356`）；讲义同口径："计算 RDF 要先加 `pbc set`，否则计算 RDF 没法考虑周期性镜像，计算不准确"（`L3 P122`）。

**2) MSD 反而不要加 PBC（方向相反！）**
- 讲师原话："算迁移率的时候，我们最好别加那个格子边界，**加上那个格子边界的话，它会跳**"（`S4.txt:3126–3131`）。
- 讲义同口径：RMSD 计算最好不要加 `pbc set`，否则原子穿越边界计算可能不对（`L3 P125`）。
- → **RDF 要 wrap，MSD 要 unwrap**，这是同一套 PBC 术语下方向相反的两个要求。`postprocess.py` 里 `rdf` 用最小镜像、`msd` 用 unwrap，各自都按正确方向做了。

**3) `align`（算 MSD 前必做）**
- `Extensions → Analysis → m2msd trajectory`，选元素（`name` 填 Li 等）后**先点 `align`**，"消除这个整个晶胞整体的它的这个平动"——模型小的时候骨架会整体漂移，而你关心的是里面离子/团簇自身的运动（`S2.txt:1346–1372`）。
- 同面板还要填：起始参考帧、`skip`（忽略前多少帧）、**时间步长**（见 MSD 小节的两步法）（`S2.txt:1374–1425`）。

**4) `all` 会卡死 → 手动多参考帧**
- VMD 那个"每一帧都为参考帧"的选项，"只要一点的话，我这个电脑就卡死了"（`S2.txt:1440–1450`）。
- 替代做法：以第 0 帧为参考导出一次，再依次以第 500 / 1000 / 1500 / 2000 帧为参考各导出一次（每次 `skip` 相应帧数），把 5 组数据复制到同一张表里，**对每一列先平方**，再相加除以 5 做平均（"这里先是先平方，然后再对这些线做平均"——讲师当场更正 PPT 里写反的"先平均再平方"）（`S2.txt:1454–1522`）。

**5) 多帧叠加画"迁移路径图"**
- `Graphics → Representations` 里给一个 VDW 模型，再进 `Trajectory` 设三个数：**初始帧 / 间隔 / 终止帧**（例：1 / 20 / 2000），回车即把所有帧叠在一张图里（`S2.txt:1670–1698`）。
- 再开**第二层 representation**：第一层只显示骨架元素的**第 1 帧**，第二层显示迁移粒子（如 Li）的**全部帧**，这样"骨架还是骨架，锂离子的迁移路径大概就是这个样子"（`S2.txt:1699–1736`）——这是论文里那张图的标准做法。
- 想让图更大范围地展示运动，可在 `Trajectory → Project` 里改 `range` 把周期镜像一起显示（`S4.txt:2729–2740`）。

**6) 键长 / 键角 / 二面角跟踪**
- `Mouse → Label → Bonds` 选两个原子得键长，`Angle` 选三个原子得键角；再在 `Graphics → Labels` 下拉选中该 label → `Graph` 出曲线 → `File` 导出进 Origin（`S2.txt:89–160`）。
- ⚠️ **跟踪单键键长时必须关掉 PBC，并且要挑不穿越盒子边界的分子**：讲师第一次就撞上"它穿越盒子边界会这个会跳"，于是重新导入、把周期性关掉、换一个在盒子中间、不穿越边界的分子（`S2.txt:100–118`）。
- skill 等价：`bond --i --j` / `angle --i --j --k` / `dihedral`。**脚本也不施加 PBC**（直接算坐标差），所以这个跳跃坑脚本**没有替你规避**——要么挑不穿越边界的原子，要么先把轨迹 unwrap 再算。
- 化学反应跟踪的用法：横坐标时间、纵坐标键长，新键生成 / 旧键断裂都能从曲线看出来（课程例子：N₂ 活化里的 N–H、O–H 键长，约 800 fs 处质子转移）（`S2.txt:171–231`）。

## 课程自写 / 自带脚本清单（skill 未内置）

> 这些脚本在课程网盘里发给大家，`postprocess.py` **没有**实现。列在这里是为了：
> ① 遇到对应分析时知道该找哪个脚本；② 知道哪些是 skill 能替代的、哪些必须自己来。
> 讲师的总原则："基本的 AIMD 分析方法在 VMD 里都可以实现，但想做比较深入、比较特殊的统计方法的分析，
> 就需要我们自己去编程去实现"（`S4.txt:3115–3121`）。

| 脚本 | 作用 | 用法 / 输出 | 出处 | skill 侧怎么办 |
|---|---|---|---|---|
| `md_simplify.py`（讲义写作 `mdsimplify.py`） | **抽帧**：每 N 帧留一个结构，把大轨迹变小 | `md_simplify.py 20` = 每 20 帧取一帧 → `new_position.xyz`；脚本里**第一行对应 VASP 的 `movie.xyz`、第二行对应 CP2K 的 `cp2k-pos-1.xyz`**（两个程序通用，改注释切换）；VASP 上游还要先用 VTST 的 `xdat2xyz` 把 `XDATCAR` 转成 `movie.xyz` | `L1 P53`、`S1.2.txt:1178–1215`、`S1.2.txt:1120–1134` | 各子命令都能直接读原始 `*-pos-1.xyz`，不需要抽帧。**但两条课程铁律要记住**：① 原始 `cp2k-1.position` **必须存档**（"说不定哪天后来又会用到"）；② `new_position.xyz` 只是下载/看图方便，**统计（MSD 等）必须用完整轨迹**——"别导这个 new position，导这个完整的 `cp2k-position-1`"（`S4.txt:2094–2126`、`3134–3139`） |
| `cp2k_frequency.pl` | 汇总频率计算结果，**快速判定极小值 / 过渡态** | 分析 `cp2k.out`；输出的总结里**末位 0 = 全实频（极小值），1 = 有虚频** | `S4.txt:1462–1494` | 频率/虚频判读见 `decide.md §23`；本文件不管 |
| `cp2k_frequency_to_movie` | 把频率结果转成**振动动画** | 需先备好末帧结构（从轨迹尾部取，如 `tail -125` 存 `last.xyz`），输入 `cp2k.out` + `last.xyz`，输出 9 个振动 movie（表面吸附水放开 9 个自由度时） | `S4.txt:1500–1539` | 用 VMD 播放虚频的振动方向来验证过渡态是课程的标准动作 |
| `max_center.py` | **质心到原子的距离**分布（如 Au₂₀ 团簇质心到顶点/边上/面心三类 Au 的距离，峰数=结构是否保持） | 约 **67 行**；`python max_center.py <轨迹文件>` → 输出距离值到 `distance` 文件 → 在 Origin 用 **Frequency Count** 统计分布 | `S4.txt:3020–3098` | **无等价子命令**，要自写或用 MDAnalysis |
| `zdis_trajectory.py` | 元素的 **Z 方向分布**（固液界面水取向） | `python zdis_trajectory.py <轨迹> H` → `distance_H`；换 O → `distance_O`；同样用 Origin `Frequency Count` 画图，横坐标取晶胞 z 长度 | `S4.txt:3685–3748` | **`zprofile --sel H` 就是它的内置等价物**（批 15 补齐）；自己写也行，但不必了 |
| `xyz2neb.pl` | **NEB 插点** | `xyz2neb.pl <初态> <末态> <插点数>`，生成 `0.xyz`…`N.xyz`（首末两个就是初末态）。⚠️ **off-by-one：插 4 个点要写 5，插 5 个要写 6**（"这个脚本写的有一点问题"，讲师原话） | `S4.txt:418–456` | `gen_inp.py` 不支持 NEB（见 `AGENTS.md §7`）；NEB 输入手拼见 `decide.md §20` |
| `gaussian.py`（讲师自写） | 读 metadynamics 的高斯峰文件，**自己累加还原势能面** | **同一脚本支持两种程序**（改注释切换）：VASP 读 `HILLSPOT`，CP2K 读 `HILLS.metadynLog`。参数依次是**维度**（一维写 1、二维写 2，**三维不支持**）、X 范围、Y 范围；默认把全部数据画完，也可以**只取前 N 个 hill**（例：总共 2913 个数据只取前 400）来画"势能面随时间生长"的图，判断有没有单调填平 | `S5.txt:4294–4334`、`4355–4375`、`4406–4417` | `fes` 走 CP2K `graph` 工具，**不吃** `HILLS.metadynLog`；要"前 N 个 hill 的演化图"就得用这个脚本 |
| `MDAnalysis`（现成第三方库） | 通用轨迹后处理 | 讲师点名的"现成的后处理程序，这个程序也是可以用的" | `S4.txt:3685–3696` | 自写脚本之外的备选路线 |

## TRAVIS 谱学流程（CP2K 侧算真 IR，批 14）

> 与后面的 `### travis` 子命令互补：这里是**课程的手工流程**，子命令那条是控制文件路线。

**1) 前提：先让 CP2K 输出 Wannier 中心**
- 轨迹里只有原子核位置，而原子核都带正电；要得到偶极变化还需要**带负电的电子对中心**——"我们有了这个正电中心，有了这个负电中心的坐标信息，那我们就知道这个分子偶极矩的变化了"（`S5.txt:85–100`）。
- 落地写法：在 `&DFT` 下加 `&LOCALIZE`（`METHOD CRAZY` + `&PRINT &WANNIER_CENTERS`，`IONS+CENTERS`，`&EACH MD 1`），得到 `wannier.xyz`——同一个 XYZ 文件里既有原子核、也有以 `X` 标记的 Wannier 中心（`L4 P4`、`L4 P5`；`S5.txt:101–115`）。
- 讲师评价：CP2K 官网自带的直接输出偶极（`FORCE_EVAL/DFT/PRINT/MOMENTS`）路线"其实不太好用，所以说我就没有去用这个功能"（`S5.txt:254–262`；`L4 P8`）。

**2) 运行：交互式，不是控制文件**
- `travis -p <带 Wannier 中心的 xyz>`（`L4 P6`）。**不能读 `cp2k-pos-1.xyz`**——"这个文件别读那个 `cp2k-position`……读这个文件是不行的"（`S5.txt:123–132`）。
- 程序会一路提问，除下面几项外全部回车用默认（`S5.txt:134–209`）：

| 提示 | 怎么填 | 坑 |
|---|---|---|
| 三边等长？ | `yes`（立方格子） | — |
| **晶胞矢量长度** | 课程例：**`782`**，单位是 **pm**（782 pm = 7.82 Å，与"16 个水分子 ≈1 g/cm³"自洽） | ⚠️ **单位是 pm，不是 Å、更不是 Å³**："这个边界要输的是皮米……这个单位不要搞错了啊"（`S5.txt:149–159`）。`references/pdf_text/learn_L5.md:485` 曾把它记成 **Å³**，**以字幕 pm 为准** |
| 算什么光谱 | `Ir`（红外） | 还可算拉曼、振动圆二色（VCD）等（`S5.txt:28–30`） |
| 时间步长 | 0.5 fs | 与 AIMD 的 `TIMESTEP` 一致 |
| 偶极模式 | `1`（Wannier 中心方式；`X` 带 2 个电荷） | — |
| 忽略前多少帧 | 不忽略就填 `1`，也可填 100 / 1000 丢未平衡段 | 与 RDF/MSD 的"丢前段"同理（`S5.txt:202–209`） |
| 是否输出整体 IR | `y` | TRAVIS 还会**自动识别体系里的分子**（如水）并额外给单分子谱 |

**3) 输出与绘图**
- 生成两个 CSV：`ir_spectrum_global.csv`（整体红外振动光谱）+ `ir_spectrum_H2O.csv`（自动识别出的分子片段光谱）（`L4 P7`；`S5.txt:216–222`）。
- 用 Excel 分列后两列 = 波数 / 强度，丢进 Origin，横坐标取 0~4000 cm⁻¹（`S5.txt:223–238`）。

**4) skill 侧的差别（务必知道）**
- `postprocess.py travis` 走的是**控制文件路线**：生成 `*.travis.in` 后再 `travis <ctrl>`（默认 analyses 是 `rdf msd`，要 IR 就 `--analyses ir`）。两条路都能算 IR，但：
  - 脚本**会扫轨迹**：若 analyses 含 `ir/raman/vcd/roa` 而轨迹里没有任何 `X` 行，**直接中文报错 exit 1**，
    并给出 `&LOCALIZE` + `IONS+CENTERS` + `FILENAME = wannier.xyz` + `&EACH MD 1` 三步处方，
    同时点名"**不能拿 `cp2k-pos-1.xyz` 去跑**"（G-06 第 1、2 条；只跑 rdf/msd 这类不需要偶极的分析时可用 `--no-require-x` 跳过）；
  - **`--cell "a b c"` 会把 `CELL` 段写进控制文件**（Å 语义，与其它子命令一致；不给就没有 CELL 段）；
  - 课程那个 **pm 单位**的坑脚本会**提示但没法替你填**（TRAVIS 交互式提问的单位就是 pm：水盒输 782）。
- 不变的硬口径：**vDOS ≠ 红外谱**。VASP 侧用 VASPKIT 只能得 vDOS（不含偶极）；要真 IR 必须"偶极 + 速度一起做变换"，即 CP2K `&LOCALIZE` + TRAVIS 这条链（`S2.txt:761–769`、`803–807`；`S5.txt:20–30`）。

## 通用参数

每个子命令都接受 `--prefix <名>`(输出文件前缀，默认用输入名派生)和 `--cell <晶胞>`、
`--json`（输出 `{ok, command, outputs:[...], stdout}`，列出产物路径，给 agent 用）。
`--prefix` 缺省时**只砍最后一个扩展名**（`v_hartree.cube` → `v_hartree`，`x-pos-1.xyz` → `x-pos-1`）。

## 子命令

> **共 24 个**（批 15 新增 7 个：`cube` / `cdd` / `workfunc` / `ir-static` / `arrhenius` / `pmf-rdf` / `dipoles`；
> 另给 `msd`/`diffusion` 加了 `--align`，给 `vacf`/`ir`/`power`/`zprofile` 加了 `--sel`，给 `travis` 加了前置检查）。
> 完整清单用 `python scripts/postprocess.py --help`。

### energy —— 能量 / 温度曲线(讲义：势能涨落)
```bash
python postprocess.py energy cp2k.out
```
从 `.out` 抽每步总能(`ENERGY| Total FORCE_EVAL`)与温度，出 `*.energy.png` + `.csv`。
也接受退化两列 `.ener` 文件。

### rdf —— 径向分布函数 g(r)(讲义第 4 项)
```bash
python postprocess.py rdf traj.xyz --cell "10 10 10" --pairs "O O" "O H" --rmax 10 --bins 200
```
PBC 下邻居直方图归一化；`--pairs` 省略则算所有唯一元素对。出 `*.rdf.png/.csv`。
> 课程等价：VMD RDF 面板（**必须先 `pbc set` + `pbc wrap -all`**，且只能给正交晶胞加 PBC）。
> 本脚本用最小镜像约定，`--cell` 支持一般 3×3 晶胞（六方不必先转正交），但 `--rmax` 别超过最短晶胞高度的一半。

### msd —— 均方位移
```bash
python postprocess.py msd traj.xyz --cell "10 10 10" --sel Li --dim 3
python postprocess.py msd traj.xyz --cell "10 10 10" --sel Li --align      # 消骨架整体漂移
```
PBC 解包裹(unwrap)后多时间原点平均。`--sel` 支持元素符号或索引区间 `1..10`。
> 课程等价：VMD `m2msd trajectory` + 手动多参考帧 + Origin 里**先平方再平均**。**平方与多原点平均这两步脚本已替你做掉**。
> ⚠️ **`align` 不是自动做的**（`--align` 默认关闭，向后兼容）—— 讲师明确要求"算 MSD 前最好 align 一下，
> 消除整个晶胞整体的平动"（`S2.txt:1346–1372`）。要它就用 `--align`（不给值 = `rest` = 以"除 `--sel` 以外的
> 骨架原子"为参考组，做刚体平动 + Kabsch 转动对齐）。
> 仍需注意：二维迁移用 `--dim 2`；抽帧/裸 xyz 丢了注释时用 `--dt`（详见「MSD 与扩散」小节）。

### diffusion —— 扩散系数 D(Einstein)(讲义第 8 项)
```bash
python postprocess.py diffusion traj.xyz --cell "10 10 10" --dim 3 --fit-lo 0.2 --fit-hi 0.8
python postprocess.py diffusion traj.xyz --cell "10 10 10" --sel Li --align   # 并打印对齐前/后的 D
```
对 MSD 长时区线性拟合，`D = slope / (2·dim)`，同时给 Å²/ps 与 cm²/s。
> 给了 `--align` 时**同时输出对齐前后的 D 与比值**（`*_diffusion.txt` 里也有）——
> 比值明显 ≠1 就说明骨架整体平动/转动原本在污染 D，也可以据此判断模型是不是太小。

### bond / angle / dihedral —— 内禀几何时间序列 + 分布
```bash
python postprocess.py bond traj.xyz --i 1 --j 2
python postprocess.py angle traj.xyz --i 1 --j 2 --k 3
python postprocess.py dihedral traj.xyz --i 1 --j 2 --k 3 --l 4
```
原子索引为 1-based。出时间序列图 + 分布直方图(讲义第 2 项：键长键角跟踪)。
> ⚠️ 与 VMD 口径一致：本脚本**不施加 PBC**（直接算坐标差）。所以课程里"原子穿越盒子边界曲线会跳"的坑
> **没有被规避**——要么挑不穿越边界的原子，要么先把轨迹 unwrap 再算（`S2.txt:100–118`）。

### pdos —— 态密度 / 投影态密度(讲义 4 + 番外篇)
```bash
python postprocess.py pdos ./  --fermi 0.0 --broaden 0.1 --de 0.01
python postprocess.py pdos cp2k-O_k1-1.pdos
```
接受单个 `.pdos` 或含多个 `.pdos` 的目录(自动按元素/kind 分解)；`--fermi` 缺省自动检测占据跨越 0.5 处；Gaussian 展宽后绘图。出 `*.pdos.png/.csv`(能量单位 eV)。
> CP2K 2026.2+ 的 `.dos`/`.pdos` 已是展宽后可直接画图；旧版为 raw `.pdos_raw`，本脚本按 raw 解析并自行展宽。

### adf —— 角分布函数
```bash
python postprocess.py adf traj.xyz --cell "10 10 10" --center O --rcut 3.5
```
以 `--center` 元素为顶角，统计邻域原子对的夹角分布。

### cn —— 配位数
```bash
python postprocess.py cn traj.xyz --cell "10 10 10" --rcut 3.5
```
由 RDF 积分得 `CN(对) <= rcut`。
> 课程等价：VMD RDF 面板勾 `integral` 读平台值。本脚本走的乘 `4πr²·dr` 就是课程强调的**球面积分**（不是平面积分）。

### zprofile —— 轴向密度剖面
```bash
python postprocess.py zprofile traj.xyz --cell "10 10 10" --bins 100
python postprocess.py zprofile traj.xyz --cell "10 10 10" --sel H   # 只看 H（课程 zdis_trajectory.py 的等价物）
```
沿 z 轴(默认)的**全原子**粒子数密度；`--sel` 复用 `msd --sel` 的语法（元素符号或 `1..10` 索引区间）。
> 课程里"固液界面水取向"正是要 **H、O 分开**看：`--sel H` / `--sel O` 各跑一次即可，
> 不必再自写 `zdis_trajectory.py` 或用 MDAnalysis。不给 `--sel` 时行为与旧版一致（全原子）。

### vacf —— 速度自相关函数(讲义第 5 项)
```bash
python postprocess.py vacf --vel PROJECT-vel-1.xyz --dt 0.5
python postprocess.py vacf --traj traj.xyz          # 位置差分近似
python postprocess.py vacf --vel PROJECT-vel-1.xyz --sel "O H"    # 只算关心的元素/分子
```
> 课程等价：VASPKIT `727`（选元素或原子序号；skip 前 N 帧预平衡；**参考点间隔填 1** = 每一帧都当参考）。
> 本脚本同样是全时间原点平均并归一到 `C(0)=1`。**`--sel` 在大体系里是必用的**：全原子 VDOS
> "峰太多了，也比较乱，不容易把我们的核心内容给它拿出来"（VN2 §5.7）——
> 加选区后归一分母**同步改为选中原子数**，`C(0)` 仍是 1。注意：vDOS/IR 里**没有偶极信息**，不是红外谱。

### ir / power —— 红外 / 振动态密度(FFT of VACF)(讲义第 6 项)
```bash
python postprocess.py ir --vel PROJECT-vel-1.xyz --dt 0.5
python postprocess.py ir --vel PROJECT-vel-1.xyz --sel O        # 选区（同 vacf）
```
对 VACF 加 Hanning 窗做 FFT，给出以 cm⁻¹ 与 1/ps 双横轴的频谱(峰值 ≈ 振动频率)。`power` 为同义别名、参数完全一致。
> ⚠️ 这是 **AIMD 路线**（VACF → FFT），峰宽更真实；**静态频率计算**那条路（频率 + 强度 → 人为高斯展宽）
> 见下面的 `ir-static`，**两条路不是同一件事**。

### ir-static —— 静态红外谱(频率 + 强度 → 高斯展宽)
```bash
python postprocess.py ir-static cp2k.out --fwhm 20 --df 1.0
```
读 `.out` 里的 `VIB|Frequency (cm^-1)` 与 `VIB|Intensities`（同行的与分两行打印的**两种形态都认**），
按 `σ = FWHM / 2√(2·ln2)` 对**每个频率**做高斯展宽、峰高按 intensity 加权。
> 课程出处：讲师原话"其实我是有一个程序的，但这里没有总结出来"（`course_learned.md:1363`，讲义 P108）。
> - **虚频**（负 cm⁻¹）**不计入谱**，但会单独报出来并给出个数 —— 它们是鞍点/数值噪声，不是吸收峰。
> - 输入里没有 `INTENSITIES T` ⇒ 没有强度行，退化为**等权**展宽并打 `[note]`。
> - **峰宽是人为的**：这正是它与 `ir`（FFT of VACF，峰宽更真实）的区别，也是本子命令最重要的一句话。

### cube —— Gaussian cube 平面平均(任意轴)
```bash
python postprocess.py cube v_hartree.cube --axis z --show-std
python postprocess.py cube a.cube b.cube --axis xy        # 多条曲线同图
```
零依赖读 Gaussian cube（CP2K 由 `--properties cube/vhartree/elf/mo` 产出）→ 沿 `--axis` 对另两轴求平均 →
`*_planar.csv`（坐标 Å + 值）+ `*_planar.png`；`--show-std` 叠加**面内 ±1σ** 看面内起伏有多大。
- `--axis` 取 `x|y|z|xy|xz|yz`；`xy` 表示"对 x、y 求平均 ⇒ 横坐标是 z"（讲义里"把 xy 面投影到 z"就是这个意思）。
- **横坐标** = `原点 + k · 步进矢量`（**不是**用 `CUTOFF` 反推网格数）；`STRIDE` 只改格点数、不改这套坐标。
- **单位约定（两处是两回事）**：第 3 行的 `natoms<0` ⇒ **原子坐标**以 bohr 计；3 行格点定义里的 `n<0` ⇒ **该轴步进矢量**以 bohr 计。脚本各按 Gaussian 约定换算。
- 解析失败会**说清失败在哪一步**（读前 6 行 / 第 3 行 `natoms ox oy oz` / 读原子行 / 读格点定义行 / 读体数据），中文提示 + exit 1、不抛 traceback。

### cdd —— 电荷密度差分 Δρ = ρ_AB − Σρ_frag
```bash
python postprocess.py cdd --total AB.cube --frag A.cube B.cube --planar-axis z
python postprocess.py cdd --total scf.cube --frag atom1.cube atom2.cube --deformation
```
3D 逐点相减（先校验**格点数**与**原点/步进矢量**必须完全一致，否则中文报错并给出检查方向），输出：
- `*_cdd.cube` —— 单位 **eV/Å³**（把 a.u. 乘了 `HARTREE_EV`），可直接进 VESTA 看正负区，**替代手工 Import + Subtract**；
- `∫Δρ dV` 的净电子数 + 正/负分区积分（"差分是否守恒"自检）；
- 给了 `--planar-axis` 时再给 `*_cdd_planar.csv/.png`（红 = 电子增多、蓝 = 电子减少）。

> ⚠️ **两个片段一定不要再单独优化**（`S5.txt:319–333`；vn5 N-03/P-01）：正确做法是从整体优化末帧里抽原子行、只做单点。
> ⚠️ 三份 cube 必须**同一 `STRIDE` / 同一 `&CELL`**（官方 `STRIDE` 默认 `2 2 2`，讲义要求 `1 1 1`）。
> ⚠️ `∫Δρ` 不严格为 0 是**正常**的：差分图看的是**空间分布**（哪里增、哪里减），不是绝对电子数。
> `--deformation`（变形电荷密度 `ρ_SCF − Σρ_孤立原子`）与前者**算法完全相同**，只改语义提示。

### workfunc —— 功函 Φ = E_vac − E_F → 相对 SHE 的电极电势
```bash
python postprocess.py workfunc cp2k-cube-V_HARTREE-1_0.cube --out cp2k.out --axis z
python postprocess.py workfunc v_hartree.cube --fermi 1.36      # 直接给费米能级(eV)
```
对 Hartree 势 cube 做平面平均 → 在**两侧**分别找**最长平坦段**当真空区（判据 `|dV/dz| < --slope-tol`，
且该段至少要有 `--vacuum-window` 那么宽）→ 取该段均值作 `E_vac`，再算 `Φ = E_vac − E_F`。
输出 `*_workfunc.csv`（`E_vac / Phi / U_vs_SHE` 各两侧 + 平台范围与宽度 + **eV 与 Hartree 双单位**）与
`*_workfunc.png`（`V(z)` 曲线 + 标出真空平台与费米能级横线）。

- **费米能级解析**：认三种写法 —— `Fermi energy: 0.2086…`（**默认 Hartree**，见 `official/01_global_and_units.md:544`）、
  `E(Fermi) = 0.122425 a.u.`（`.pdos` 头注释）、`fermi energy [eV] = -5.12`（行内声明单位）。
  **必须按行内单位标注换算** —— 这正是 N-19 那个"eV / a.u. 差 27 倍"的单位坑。
- **相对 SHE 的电极电势**：`U = Φ − 4.44 V`（SHE 绝对电势 **4.44 eV**，庚子讲义口径：
  `course_learned.md:808–809`「真实电势 = 功函数（真空能级 − 费米能级）相对 SHE = 4.44 eV 折算」，
  算例 `Φ = 5.26 eV → +0.82 V`；另见 `playbook.md:40`、`learn_L3.md:834`）。
  `--she` 可改这个常数，改了会打 `[note]` 提醒偏离了仓库口径。
- ⚠️ **真空位倾斜告警**：平台内 `max|dV/dz|` 超过 `--warn-grad` 就在 stderr 警告
  "真空段有宏观电场残留 / 疑似非对称 slab 未开 `SURFACE_DIPOLE_CORRECTION`"，并给出官方硬限制
  （**只对法向平行于某一笛卡尔轴的 slab 实现**，方向由 `SURF_DIP_DIR` 给）。这就是 P-08 那条坑的运行时版本。
  整条曲线都带宏观斜率（找不到任何平坦段）时**不退出**，而是取该半段均值作为可诊断的 `E_vac`，
  并明确写"数值**不可直接引用**，先修模型"。

### arrhenius —— 多温度 D → Ea 与 D₀
```bash
python postprocess.py arrhenius --d "600:1.0e-6" "800:5.0e-6" "1000:2.0e-5" "1200:6.0e-5" "1400:1.5e-4"
python postprocess.py arrhenius --diffusion d600_diffusion.txt d800_diffusion.txt ...
python postprocess.py arrhenius --per-1000t --d ...      # 讲义口径：log10 D vs 1000/T
```
线性拟合出 **Ea（同时给 eV 与 kJ/mol）**、**D₀**、斜率、截距、R²，出 `*_arrhenius.csv/.png/.txt`。
- 默认横轴 `1/T`（自然对数）：`ln D = ln D₀ − Ea/(k_B·T)` ⇒ 斜率 = `−Ea/k_B` ⇒ `Ea = −slope·k_B`。
- `--per-1000t`（**讲义口径**，`learn_L3.md:832`）：横轴 `1000/T`、纵轴 `log10 D` ⇒ 斜率 = `−Ea/(2.303·k_B)`
  ⇒ `Ea = −slope × 2.303 × k_B × 1000`。⚠️ **末尾那个 ×1000 来自横轴的 `1000/T`**，漏掉会静默差 1000 倍
  （自检：讲义算例 `1.07871 × 2.303 × 8.6173e-5 × 1000 = 0.2141 eV`）。
- `--diffusion` 读 `*_diffusion.txt` 时必须能从文件里读到 `D = … Angstrom^2/ps` 与温度（`T=… K`），
  读不到就**报错而不是猜温度**。
- R² < 0.95 会提示三种常见原因（温度范围太窄 / MSD 没进线性扩散区 / 某温度发生了相变）。
- ⚠️ 单温度没有意义：至少给**两对** `(T, D)`（讲义用 600/800/1000/1200/1400 K 五个温度）。

### pmf-rdf —— 由 RDF 反推能垒 w(r) = −RT·ln g(r)
```bash
python postprocess.py pmf-rdf cp2k_rdf.csv --temp 600 --rmax 8
```
读 `rdf` 子命令产出的两列 `(r, g)`，算 `w(r) = −R·T·ln g(r)`（`R = 8.314 J·mol⁻¹·K⁻¹`，**T 用实际模拟温度**），
再 ÷`96.4853` 转 eV，输出 `*_pmf.csv`（r / g / w[kJ/mol] / w[eV]）与**双 Y 轴**图（左 g(r)、右 w(r)）。
> ⚠️ **局限（写进了图标题与 `--help`）**：**只适用于「第一配位层与第二配位层之间发生原子交换」这一类过程**，
> 别的过程套不上（讲师原话"这个迁移能垒比较的局限"，`S4.txt:2864–2870`、`2969–2972`）。
> `g = 0` 的区间（正是"概率密度为零"那段）`ln g → −∞`，脚本夹到 `--gfloor`（默认 `1e-6`）并**显式提示**被夹的点数。
> ⚠️ 数值疑误（讲义）：同一段里两个纵轴值差 **0.15**，口播却说"**1.5** 个电子伏特"，引用的文献值是 **0.23 eV** ——
> 按 **0.15 eV** 理解并标注转写疑误。

### dipoles —— Wannier 中心 → 每帧偶极（TRAVIS 前置自检）
```bash
python postprocess.py dipoles wannier.xyz --nuclear-charges "H=1,O=6"
```
解析轨迹里的 `X` 行（Wannier 中心），按 `μ = Σ Z_i·r_i − 2·Σ r_X` 累加得每帧总偶极
（正电中心 = 原子核，负电中心 = 成对电子带 2 个电荷；`S5.txt:83–137`），
输出 `*_dipoles.csv`（μx/μy/μz/|μ|）与「时间序列 + |μ| 分布」双联图。
- `--nuclear-charges` **必填且不自动猜** —— 基组/赝势的有效电荷不是原子序数，猜错会让偶极整体平移。
- 轨迹里**没有 `X` 行** ⇒ 中文报错 exit 1 并给 `&LOCALIZE` 处方（与 `travis` 的前置检查同一口径）。
- 偶极是一条**直线**（标准差 ≈ 0）⇒ WARN「轨迹里没有偶极起伏，TRAVIS 白跑」。
- **不替代 TRAVIS**：TRAVIS 还要做 ACF + 偶极的变换、Raman/VCD；这里只是跑之前先看一眼有没有偶极起伏。

### bader —— Bader 电荷(桥接，需 `bader` 二进制)
```bash
python postprocess.py bader cp2k-cube-ELECTRON_DENSITY-1_0.cube
```
检测 `bader` → 运行 → 解析 `ACF.dat` → `*.bader.csv`。cube 由 `--properties cube` 产出。

### fes —— 元动力学自由能面(桥接，需 CP2K `graph` 工具)
```bash
python postprocess.py fes --restart metadyn.restart --ndim 2 --ndw 1 2
python postprocess.py fes --fesdat fes.dat          # 直接对已有 fes.dat 出图
```
调用 `graph -cp2k -ndim N -ndw ... -file <restart>` 重建 FES，解析 `fes.dat` 出 1D/2D 图(能量转 kJ/mol)。
**注意**：`-ndim` 必须填 metadynamics 实际的 CV 数(不是你想投影的维数)，否则得到错误但看似合理的 FES。
> 课程等价：第 5 天是拿 `cp2k-HILLS.metadynLog`（**6 列**：时间/CV1/CV2/CV1 宽/CV2 宽/峰高）用自写 `gaussian.py`
> 自己累加高斯峰；本子命令改走 CP2K 官方 `graph`，**不吃 HILLS 文件**。"只看前 N 个 hill 的生长图"仍要用 `gaussian.py`。

### travis —— TRAVIS 谱学桥接(需 `travis` 二进制)
```bash
python postprocess.py travis traj.xyz --vel PROJECT-vel-1.xyz --analyses rdf msd ir
```
生成 TRAVIS 控制文件并运行(IR/Raman/VCD/ROA 等)；二进制缺失时仍生成控制文件供手动跑。
> ⚠️ 课程走的是**交互式** `travis -p wannier.xyz`（**不能读 `cp2k-pos-1.xyz`**），且前提是先在 `&DFT` 下加
> `&LOCALIZE` 让轨迹里出现 Wannier 中心 `X`。本子命令**不检查这两件事**，控制文件里也没写晶胞
> （课程那个"晶胞长度单位是 **pm**"的坑要自己确认）。完整手工流程见「TRAVIS 谱学流程」一节。

## 与诊断闭环

`postprocess.py` 的结果可回流到 `diagnose.py` 的逻辑，形成完整闭环：
- 能量漂移大 → 减 `TIMESTEP` / 查 thermostat(已有)
- MSD 非线性、D 随拟合区间剧变 → 模拟太短，延长生产阶段
- FES 未填满(minima 不全) → 加 metadynamics 步数 / 调 HILL 高度
- PDOS 费米面非零(金属)却没展宽 → 提示加 `--smear`

校验：`_validate_postprocess.py` 用合成数据(随机气箱验 RDF/ADF/CN、已知 D 的布朗运动验 MSD/diffusion、阻尼振子验 VACF/IR 频谱峰值、伪造 `.pdos` 验绘图、2D 抛物线验 FES 出图，**以及批 15 的 cube/cdd/workfunc/ir-static/arrhenius/pmf-rdf/dipoles/`--align` 八条解析解断言**)端到端跑通所有子命令，0 error / 0 crash。
> **新增子命令必须进这个 harness**（它是仓库登记的"后处理数值正确性基线"，`AGENTS.md §6.2` 三项串行校验之一）——
> 加了子命令却不进它，等于"加了但没人测"。逐条与解析解比对的更细版本另见 `_validate_postprocess_analytic.py`。
