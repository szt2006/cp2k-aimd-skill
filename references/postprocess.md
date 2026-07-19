# CP2K 后处理（postprocess.py）

`scripts/postprocess.py` 是 skill 闭环的第 5 步：**跑完 cp2k 之后，读它产出的文件，直接算出常用后处理量并出图(.png) + 数据(.csv)**。
呼应庚子计算讲义《AIMD 与 CP2K 讲义-1》的「AIMD 后处理」章节(轨迹查看、键长键角、势能涨落、RDF、VACF、IR、MSD、扩散系数)以及讲义 4 / 番外篇的电子结构分析(DOS/PDOS、Bader、Wannier)与自由能面(FES)。

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
| `*-cube-ELECTRON_DENSITY-*.cube` | `--properties cube`(`STRIDE 1 1 1`) | `bader`(桥接) |
| `metadyn restart` / `HILLS` | `&FREE_ENERGY &METADYN` | `fes`(桥接 CP2K `graph`) |
| 任意轨迹 | — | `travis`(桥接，生成控制文件) |

> **关键衔接坑**：
> - AIMD 轨迹 `*-pos-1.xyz` **不含晶胞**，RDF/MSD/ADF 必须给 cell：`--cell "a b c"` 或 `--cell "ax ay az bx by bz cx cy cz"`，也可自动从 `.out` 的 `CELL|` 行解析。
> - 速度轨迹默认就打印(AIMD 模板)。VACF/IR 直接 `--vel PROJECT-vel-1.xyz`；没有速度文件时可用 `--traj` 走位置差分近似(精度有限，脚本会提示)。
> - 时间单位默认 ps(轨迹注释行 `time=...` 即 ps)，坐标默认 Å。

## 依赖

纯 Python：`numpy` + `matplotlib`(Agg 后端，无界面也能出图)。无需外部程序即可跑核心层。
桥接层(`bader` / `fes` / `travis`)会先 `shutil.which` 检测二进制；**缺失时打印安装指引与等价手动命令，不崩溃中断**。

## 关键公式与判读陷阱（庚子讲义内化，批 13）

> 下面公式/坑来自《AIMD 与 CP2K》讲义 PDF 与字幕逐页内化（详见 `references/course_learned.md` 第 2 节）。
> 写在这里是因为它们是**判读后处理结果对不对**的硬标准；脚本已内部实现，但人要先懂公式才不会误判。

### RDF 与配位数（球面积分，**最易算错**）
- `g(r)`：径向分布函数，某原子周围 r 处找到另一原子的概率密度相对均匀气体的倍数。
- **配位数 = 球面积分**：`CN(<r) = ∫₀ʳ 4π·r'²·g(r')·ρ dr'`（ρ = 数密度）。**必须**用 `4πr²` 球面积分，不能直接在 Origin 里做平面积分 `∫g(r)dr`（讲师强调最多人错的地方）。
- 第一峰顶点横坐标 ≈ 第一配位层距离；第一峰面积 = 第一配位数；第二峰 = 第二配位层。
- 脚本：`postprocess.py rdf`（自动 PBC 归一化）+ `cn`（由 RDF 积分得 CN）。给 `--cell`。

### MSD 与扩散（**VMD √MSD 坑**）
- 定义：`MSD(t) = (1/N)·Σᵢ|rᵢ(t) − rᵢ(0)|²`（多参考帧平均，先做 PBC unwrap）。
- **Einstein**：长时区 `MSD(t) ≈ 2·d·D·t` → `D = slope / (2·d)`；3D 用 `/6`，2D 用 `/4`。
- 单位：`1 Å²/ps = 1e-4 cm²/s`。
- ⚠️ **VMD 坑（讲师当场更正）**：VMD 给的 MSD 实际是 **√MSD（带根号）**。要得正确 MSD 须**先对每个参考帧平方、再跨参考帧平均**（"先平方再平均"，PPT 初稿写成"先平均再平方"被同学指出更正）。多参考帧：以第 0/500/1000… 帧分别为原点各算一条，平方后平均更稳。
- 脚本：`postprocess.py msd` / `diffusion` 内部已做平方与 unwrap，无需手算；给 `--cell`。

### VACF → vDOS → IR（**vDOS ≠ IR**）
- `C(t) = <v(0)·v(t)> / <v²>`；`vDOS(ω) = FFT[C(t)]`。
- ⚠️ vDOS **不是**红外谱：vDOS 只含频率、不含偶极矩变化 → 缺振动强度。真正 IR 需偶极矩随时间变化，CP2K 用 **Wannier 中心 + TRAVIS**（见 `course_learned.md §6.1`）；CP2K 自带 `&MOMENTS` 直接输偶极的方法"不好用"（讲师评价）。
- 脚本：`postprocess.py vacf` / `ir`（用 `--vel` 吃速度轨迹；无速度用 `--traj` 位置差分近似，精度有限）。

### Arrhenius 扩散激活能（讲师实测数值）
- `D = D₀·exp(−Ea/k_BT)` → `ln D vs 1/T` 斜率 = `−Ea/k_B`。
- 讲师用水盒子不同温度 MSD 拟合得 **Ea ≈ 0.2141 eV**（液态水自扩散，量级合理）。
- 稀有事件率 `k = A·exp(−Ea/RT)`（A≈10¹³ s⁻¹）：0.75 eV 能垒 @300K ≈ 1 次/秒；1.75 eV 需 ~1 秒 → AIMD（ps 量级）看不到，需加速采样（PMF / slow-growth / metadynamics，见 `course_learned.md` 第 7 节）。

### 判读联动（结果是否合理）
- 能量漂移 >1%（`energy` 子命令看）→ 减 `TIMESTEP` / 查 thermostat（§22、§13）。
- MSD 非线性、D 随拟合区间剧变 → 模拟太短，延长生产阶段。
- FES 未填满（minima 不全）→ 加 metadynamics 步数 / 调 HILL 高度（`fes` 子命令，`-ndim` 必须填真实 CV 数）。
- PDOS 费米面非零（金属）却没展宽 → 提示加 `--smear`。

## 通用参数

每个子命令都接受 `--prefix <名>`(输出文件前缀，默认用输入名派生)和 `--cell <晶胞>`。

## 子命令

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

### msd —— 均方位移
```bash
python postprocess.py msd traj.xyz --cell "10 10 10" --sel Li --dim 3
```
PBC 解包裹(unwrap)后多时间原点平均。`--sel` 支持元素符号或索引区间 `1..10`。

### diffusion —— 扩散系数 D(Einstein)(讲义第 8 项)
```bash
python postprocess.py diffusion traj.xyz --cell "10 10 10" --dim 3 --fit-lo 0.2 --fit-hi 0.8
```
对 MSD 长时区线性拟合，`D = slope / (2·dim)`，同时给 Å²/ps 与 cm²/s。

### bond / angle / dihedral —— 内禀几何时间序列 + 分布
```bash
python postprocess.py bond traj.xyz --i 1 --j 2
python postprocess.py angle traj.xyz --i 1 --j 2 --k 3
python postprocess.py dihedral traj.xyz --i 1 --j 2 --k 3 --l 4
```
原子索引为 1-based。出时间序列图 + 分布直方图(讲义第 2 项：键长键角跟踪)。

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

### zprofile —— 轴向密度剖面
```bash
python postprocess.py zprofile traj.xyz --cell "10 10 10" --bins 100
```
沿 z 轴(默认)的粒子数密度。

### vacf —— 速度自相关函数(讲义第 5 项)
```bash
python postprocess.py vacf --vel PROJECT-vel-1.xyz --dt 0.5
python postprocess.py vacf --traj traj.xyz          # 位置差分近似
```

### ir / power —— 红外 / 振动态密度(FFT of VACF)(讲义第 6 项)
```bash
python postprocess.py ir --vel PROJECT-vel-1.xyz --dt 0.5
```
对 VACF 加 Hanning 窗做 FFT，给出以 cm⁻¹ 与 1/ps 双横轴的频谱(峰值 ≈ 振动频率)。`power` 为同义别名。

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

### travis —— TRAVIS 谱学桥接(需 `travis` 二进制)
```bash
python postprocess.py travis traj.xyz --vel PROJECT-vel-1.xyz --analyses rdf msd ir
```
生成 TRAVIS 控制文件并运行(IR/Raman/VCD/ROA 等)；二进制缺失时仍生成控制文件供手动跑。

## 与诊断闭环

`postprocess.py` 的结果可回流到 `diagnose.py` 的逻辑，形成完整闭环：
- 能量漂移大 → 减 `TIMESTEP` / 查 thermostat(已有)
- MSD 非线性、D 随拟合区间剧变 → 模拟太短，延长生产阶段
- FES 未填满(minima 不全) → 加 metadynamics 步数 / 调 HILL 高度
- PDOS 费米面非零(金属)却没展宽 → 提示加 `--smear`

校验：`_validate_postprocess.py` 用合成数据(随机气箱验 RDF/ADF/CN、已知 D 的布朗运动验 MSD/diffusion、阻尼振子验 VACF/IR 频谱峰值、伪造 `.pdos` 验绘图、2D 抛物线验 FES 出图)端到端跑通所有子命令，0 error / 0 crash。
