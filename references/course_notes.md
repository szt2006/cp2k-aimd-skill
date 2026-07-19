# 庚子计算《AIMD 与 CP2K》视频字幕 — 实操精要（course_notes）

> 来源：5 天培训视频字幕（`1.1/1.2/2/3/4/5.txt`），口语转写，已按 `course_survey.md` §3 错字对照表解码。
> 定位：补充 `decide.md`（参数决策）与 `postprocess.md`（后处理）里**手册没有的讲师实操经验**。凡与 `decide.md` 重复者以 `decide.md` 为准；此文件记"为什么 / 坑 / 工具流"。
> 关联：`course_survey.md`（资料梳理）、`decide.md`（§1–§27）、`postprocess.md`（后处理引擎）。

---

## A. 后处理（对应 `postprocess.md`）

### A1. RDF（对关联函数 / 径向分布函数）
- **必须用周期性边界条件**：VMD 导入轨迹后先加 PBC，否则相邻镜像原子不算进来，g(r) 失真。
- **配位数 = 球面积分**：对 RDF 做 `∫ 4πr²·g(r)·ρ dr`，**不能直接在 Origin 里做平面积分**——讲师强调很多同学在这里算错。第一峰顶点横坐标 ≈ 第一配位层距离（如 ~1.1 Å），积分第一峰面积 = 第一配位数，第二峰 = 第二配位层。
- 与 skill：`postprocess.py rdf` / `cn` 已自动用 cell 做 PBC 归一化与积分，等价于这里的操作（出图时注意给 `--cell`）。

### A2. MSD 与扩散系数
- VMD 给出的 MSD 实际是 **√MSD（带根号）**，不是原始 MSD。要得到 MSD 须**对每个参考帧的输出先平方、再跨参考帧平均**（多参考帧：以第 0/500/1000… 帧分别为参考各算一条线，平方后平均）。
- **坑（重要）**：讲师原 PPT 写成"先平均再平方"，被同学指出后当场更正为"先平方再平均"。
- 长时区线性拟合得斜率 → `D = slope / (2·dim)`，同时给 Å²/ps 与 cm²/s。
- 与 skill：`postprocess.py msd` / `diffusion` 直接算，注意给 `--cell`；无需手动平方平均（脚本内部已做）。

### A3. 频率计算 → 振动动画
- AIMD / 频率任务跑完后，用 `cp2k_frequency_to_movie` 脚本（需先取末帧结构 `last.xyz` = position 末 125 行）→ 输入 `cp2k.out` 和 `last.xyz` → 输出 9 个振动模式 movie（mode 1 是**虚频**，过渡态特征）。
- **过渡态判据**：有 1 个虚频（负频率）。
- 与 skill：`gen_inp.py --type vib`（`RUN_TYPE VIBRATIONAL_ANALYSIS`）+ `&VIBRATIONAL_ANALYSIS INTENSITIES` 对应此流程；`decide.md` §23 已覆盖。

### A4. 电子结构可视化
- **ELF（电子局域函数）**：看共价/离子性、三中心两电子键（如二维硼材料）、电子化合物。值 >0.5 局域强，≈0 离域。用 `--properties elf` 出 cube，VESTA 看。
- **电荷差分**：VESTA 里 `total − CO(吸附质) − metal(基底)`，黄=电荷增加、蓝/青=减少。注意导入顺序用"减"不是"加"（total 减 CO 减 metal）。二维截面：选三原子定面（lattice plane）或用 2D data plane。
- **PDOS / d-band**：`--properties pdos`，看金属 d-band center、元素贡献。
- 与 skill：`postprocess.py pdos` / `bader` 覆盖；ELF cube 由 `--properties elf` 生成（段名单数 `ELF_CUBE`）。

### A5. 自由能面（FES）三种方法（第 5 天）
- **PMF / 伞采样**：沿 CV 离散插点、每点加偏置窗；过渡态位置**强烈依赖插点密度**，点稀则能量差可达 0.1 eV 级误差。
- **slow growth（缓慢增长）**：限制下让 CV 每步微增（如 +0.0001），捕捉自由能对 CV 的梯度 λ，取平均得光滑 FES。改进 PMF 对插点密度的依赖。
- **metadynamics（元动力学）**：自适应撒山填面；well-tempered 让山随时间变扁、收敛更稳。
- 与 skill：`gen_inp.py --type metadyn`（含 `--well-tempered`/`--delta-t`/`--metadyn-ww`/`--lagrange`/`--multi-walker`/`--plumed`）已支持；`postprocess.py fes` 桥接 CP2K `graph` 重建 FES（**-ndim 必须填真实 CV 数**）。

---

## B. 参数经验（对应 `decide.md`）

### B1. DFT+U —— 过渡金属氧化物"必须加"（建议提升为硬规则）
- 强关联 TM 化合物（TiO₂、Fe₃O₄ 等）：**不加 U 会定性错误**——电子不能局域在金属离子上，四价 Ti 不被还原，表面吸附物电子转移模拟不对。即使减速也要加。
- 与 skill：`--kinds "...:U=3"` 已支持（默认 MULLIKEN ramping，`L` 默认 2）。此经验应写入 `decide.md` 方法选择作为 TM 氧化物的默认动作。

### B2. BSSE 警示（高斯基组 vs 平面波）（建议提升为硬规则）
- CP2K 用高斯基组 → 有 **BSSE（基组叠加误差）**，算吸附/结合能会**高估**（多数情况比 VASP 算的大一点）。基组越小 BSSE 越大。
- 平面波程序（VASP）无 BSSE。
- 实践建议（讲师）：AIMD 大规模动态用 CP2K（绝对优势）；精确静态（吸附能、反应能、过渡态）可换平面波、或加大基组 / 做 BSSE 校正（CP2K 可用 `&BSSE` 或 counterpoise）。
- 与 skill：`decide.md` 吸附能/结合能判读应加此警示，避免"CP2K 算的吸附能偏大 = 算错了"的误判。

### B3. OT vs 对角化（讲师口语佐证 `decide.md` §22）
- 对角化是传统法（VASP 也用），速度慢，但对**金属体系**在 CP2K 里尚可；OT 是现代默认、快。
- 收敛辅助：对角化里常用 DIIS（`EPS_DIIS`），开 `&DIAGONALIZATION`。
- 与 skill：`§22` 已覆盖关键词落点与取舍，此处为讲师实战佐证。

### B4. 轨迹抽帧存盘
- AIMD 2 万帧的 movie 文件可能 ~59 MB，下载/处理困难。用 `md_simplify.py`（CP2K/VASP 通用）每 10~20 步抽一帧再后处理；也可自己用 `cclib` / ASE 读。
- 与 skill：`postprocess.py` 直接吃轨迹，无需先抽帧；但若文件过大可先抽。

---

## C. 建模实操（对应 `decide.md` §结构 / `gen_inp.py`）

- 用 `&SUBSYS &TOPOLOGY COORD_FILE_NAME` 读坐标（CIF/POSCAR/xyz），或用 `&COORD` 内联；模板里用 `include` 把坐标文件读进来。
- 改晶胞边界：从 POSCAR/CIF 的 cell 行找到 `&CELL` 的 A/B/C 向量，重写进 inp。
- 原子顺序可重排：`DEMCAR -s`（写 POSCAR 时）或 Materials Studio 里调整，便于套模板。
- 与 skill：`gen_inp.py --topology POSCAR.cif --topology-format cif` 已覆盖"从文件读结构"，等价于这里讲师的 include 操作。

---

## D. 实例索引（供以后讲解/对照）

| 实例 | 出现天数 | 演示要点 |
|---|---|---|
| 水盒子（H₂O box）| 第 1–2 天 | RDF / MSD / 扩散标准流程（CP2K & VASP 对照）|
| TiO₂（二氧化钛）| 第 1 天 | DFT+U 演示（不加 U 电子不局域）|
| Cu 表面氧化 | 第 4 天 | AIMD 模拟 O₂/CO 插层、表面变氧化物 |
| Au20 团簇 | 第 4 天 | 金字塔结构稳定性，质心-原子距离分析（需自写 Python）|
| CO 吸附在金属表面 | 第 5 天 | 电荷差分、ELF 看共价/离子成分 |

---

## E. 错字对照表（解码用，亦见 `course_survey.md` §3）

见 `course_survey.md` §3 完整表。最高频：`cp two k`=CP2K、`VSP`=VASP、`AAMD`=AIMD、`验室/机组`=赝势/基组、`京弯`=晶胞、`军方位1`=MSD、`风`=峰、`差`=插、`BSS 1`=BSSE、`镜像分布函数`=RDF、`二氧化石`=TiO₂、`进二`=Au20、`PM 、 F`=PMF、`METDYNAMICS`=metadynamics、`ELF/ERF`=ELF。
