# 庚子计算《AIMD 与 CP2K》视频字幕 — 实操精要（course_notes）

> 来源：5 天培训字幕 `references/pdf_text/S1.1.txt`、`S1.2.txt`、`S2.txt`–`S5.txt`（**行号与原始字幕一致，可直接核对**）+ 讲义页码 `L1–L5 P n`（`L*.txt` 里的 `========== PAGE n ==========`）。
> 定位：补充 `decide.md`（参数决策）与 `postprocess.md`（后处理）里**手册没有的讲师实操经验**。凡与 `decide.md` 重复者以 `decide.md` 为准；此文件记"为什么 / 坑 / 工具流"。
> 分工：公式与方法叙事 → `course_learned.md`（B 层）；症状→处方 / 报错 / 数值速查 → `playbook.md`（F 层）；参数硬规则 → `decide.md`（A 层，§28 即讲师硬规则）；后处理引擎 → `postprocess.md`；资料对应与错字表 → `course_survey.md`。
> **本文件刻意保持精简**：每条只给"结论 + 出处"，细则已在其它层写清的一律只留指针，不复制正文。
> 引用格式：`S2.txt:1508–1516`（字幕行号范围）、`L1 P66–P67`（讲义页码）。

---

## A. 后处理（对应 `postprocess.md`；判读话术见 `playbook.md §0.5/§1.4/§5`）

### A1. RDF（对关联函数 / 径向分布函数）
- **必须用周期性边界条件**：VMD 导入轨迹后先加 PBC，否则相邻镜像原子不算进来，g(r) 失真（`S2.txt:340–355`）。
- **配位数 = 球面积分**：对 RDF 做 `∫ 4πr²·g(r)·ρ dr`，**不能直接在 Origin 里做平面积分**——讲师强调很多同学在这里算错（`S2.txt:396–416`）。第一峰顶点横坐标 = 第一配位层距离，第一峰积分 = 第一配位数，第二峰 = 第二配位层。
- 水盒子实测读数（**注意：这是分子内共价键，不是一般配位距离**）：第一峰又高又尖 = 水分子内 **O–H 共价键**，顶点 **~1.0 Å**（**讲义 `L1 P65` 权威值 `O–H ~0.99 Å`**；讲师口播"大约 1.1 Å"是现场约读，`S2.txt:322–327`），积分 **2.00**（= 每个水分子自己的 2 个 H）；**氢键 O···H 在 ~1.73 Å**（`L1 P65`）；第二配位层积分 **≈3.97** 个 H（`S2.txt:444–452`、`L1 P65`）→ 一个 O 周围约 4 个 H。
- 与 skill：`postprocess.py rdf` / `cn` 已自动用 cell 做 PBC 归一化与积分，等价于这里的操作（出图时注意给 `--cell`）。

### A2. MSD 与扩散系数
- VMD 给出的 MSD 实际是 **√MSD（带根号）**，不是原始 MSD。要得到 MSD 须**对每个参考帧的输出先平方、再跨参考帧平均**（多参考帧：以第 0/500/1000… 帧分别为参考各算一条线，平方后平均）。
- **坑（重要）**：讲师原 PPT 写成"先平均再平方"，被同学指出后当场更正为"先平方再平均"——该更正在**第 2 天** `S2.txt:1508–1516`（`S1.1` 是第 1 天，**全文无 MSD 内容**，勿再把这条归到第 1 天）。
- 长时区线性拟合得斜率 → `D = slope / (2·dim)`：三维迁移 ×1/6，**二维迁移（如双层石墨烯夹层）是 ×1/4**（`S2.txt:1562–1583`）。同时给 Å²/ps 与 cm²/s。
- **MSD 不要加 PBC**："算迁移率的时候我们最好别加那个格子边界，加上那个格子边界的话它会跳"（`S4.txt:3126–3131`）。
  > ✅ **"与 RDF 方向相反"已经查清，不是矛盾**：这里说的 PBC 操作是 **`pbc wrap`（把原子折回盒子内）**。
  > RDF **需要** wrap 后的坐标（或等价的最小镜像约定）才能正确统计配位；MSD **需要** 连续的**未折叠**坐标，
  > wrap 会让跨边界原子"瞬移"从而毁掉位移统计。所以准确口径是"**RDF 要 wrap，MSD 要 unwrap**"，
  > 不是"一个要 PBC 一个不要 PBC"。`postprocess.py` 里 `rdf` 用最小镜像、`msd` 内部 `unwrap_traj()`，**各自都做对了**。
  VMD 算 MSD 前**必须先 align**，消除骨架整体平动（`S2.txt:1354–1372`）。
- MSD 要用**完整轨迹**（`cp2k-1.position`），不要用抽帧的 `new_position`（`S4.txt:3134–3139`）。
- 与 skill：`postprocess.py msd` / `diffusion` 直接算，注意给 `--cell`；**但 `course_learned.md §2.2` 写"`msd` 内部已做 PBC unwrap"，与讲师口径方向不同**，取用时以 `decide.md` / `playbook.md §1.4` 的最终口径为准。

### A3. 频率计算 → 振动动画
- AIMD / 频率任务跑完后，用 `cp2k_frequency_to_movie` 脚本（需先取末帧结构 `last.xyz` = position 末 125 行）→ 输入 `cp2k.out` 和 `last.xyz` → 输出 9 个振动模式 movie（mode 1 是**虚频**，过渡态特征）。
- **过渡态判据**：有 1 个虚频（负频率）。**虚频太小要警惕**：正常过渡态虚频至少 ~100 波数，只有几个波数多半是计算误差或平动/转动混入；虚频振动方向须连接初态与末态（`S4.txt:1564–1583`、`1547–1562`）。
- 与 skill：`gen_inp.py --type vib`（`RUN_TYPE VIBRATIONAL_ANALYSIS`）+ `&VIBRATIONAL_ANALYSIS INTENSITIES` 对应此流程；`decide.md` §23 已覆盖，固定原子算频率的并行 image 数坑见 `playbook.md §0.7/§2.5`。

### A4. 电子结构可视化（第 5 天 `S5.txt:266–2201`；工作流 `playbook.md §2.7/§2.8`）
- **总则：不做总电荷密度分析，只做差分**——总密度图"其实没什么太大用处"（`S5.txt:328–338`）。
- **ELF（电子局域函数）**：看共价/离子性、三中心两电子键（如二维硼材料）、电子化合物。值 >0.5 局域强，≈0 离域。用 `--properties elf` 出 cube，VESTA 看。
- **电荷差分**：VESTA 里 `total − CO(吸附质) − metal(基底)`，黄=电荷增加、蓝/青=减少。注意导入顺序用"减"不是"加"。二维截面：选三原子定面（lattice plane）或用 2D data plane。
- **平面平均（沿 Z 投影）**：`python cube.py` 处理电子密度 cube，**三个投影做 B − C − D**，>0 增加 / <0 减少 → 异质结电荷转移方向的定量证据（`S5.txt:723–792`）；CP2K 官方脚本（字幕作 `cubecr`）"不太好用"，讲师用自写脚本（`S5.txt:747–812`）。
- **原子电荷四件套**：`&PRINT` 里打开 Mulliken / Hirshfeld / Löwdin 三个 section 即可输出（`S5.txt:1011–1024`），**Mulliken 文件看 net charge 列 = 原子电荷，不用再减价电子数**（本例 C +0.44、O −0.07；闭壳层 spin moment 全 0，`S5.txt:1024–1039`）。**Bader 最靠谱**：`bader cp2k-cube-electronic`（自旋用 spin）→ `ACF.dat` 的 `CHARGE` 行，**价电子数 − Bader 电子数 = 原子电荷**（C 4→2.36 ⇒ +1.64，O 6→7.85 ⇒ −1.85；`S5.txt:864–980`）。**原子电荷只能横向对比、绝对值无意义**，且 ≠ 化学价态（`S5.txt:813–855`、`1072–1082`）；可信度排序见 `playbook.md §5.5`。
- **PDOS / d-band**：`--properties pdos`，看金属 d-band center、元素贡献。CP2K 的 PDOS"不是特别靠谱"（Γ 点 + 人为展宽）：要用就换对角化（可含更多 k 点），并显式声明展宽（胖 0.02~0.03 / 瘦 0.005~0.001）；`COMPONENTS` 会把 s/p/d 再拆分量、数据量爆炸，默认不必（`S5.txt:1086–1144`）。出图只看费米能级附近 **−10 ~ +10 eV**（0 = 费米能级），自旋向下取负（`S5.txt:1288`；⚠️ 见下方口径更正）。
- **PDOS 判读五招**（`S5.txt:1336–1468`）：**离子键** = 费米能级下出现新峰（电子转移）；**共价键** = **相邻原子之间的 PDOS 峰重合**；**掺杂缺陷态** = 费米能级附近或以上的新态；**半导体表面态** = 表面不饱和键带来的费米能级附近新态；**自旋极化** = α/β 两套峰错位（可解释 N₂ 在 Fe 团簇上的活化）。另：`NHOMO`/`NLUMO` 官方默认 **1 / 0** ⇒ 想要 HOMO+LUMO 图必须显式写 `NLUMO 1`。
  > ⚠️ **两处口径更正（第二轮视频精读落层，2026-09）**：
  > ① **能量窗口**：旧版第一轮内化写作 `−10~0 eV`，来自字幕 `S5.txt:1288` 的"十电子伏特到**正式**电子伏特"——
  > 其中"正式"是 ASR 把"**正十**"听错 ⇒ 应为 **−10 ~ +10 eV**（`course_learned.md §6.10` 同改）。
  > ② **"判读三招"→"五招"**：旧版本条只列了三招（离子/共价/缺陷态），**漏了表面态与自旋极化**，
  > 现按 `S5.txt:1336–1468` 补全为五招；第三招"缺陷态"的**完整机理**（Ce⁴⁺→Al³⁺ 缺电子 ⇒ 两个 O 各出一个 ⇒ O 变 p⁴ ⇒
  > 两个费米能级之上的缺陷态）与"自旋极化的能级匹配"叙述见 `course_learned.md §6.10`。
- **MO cube**：按费米能级往上/往下各取几个轨道（先 1+1，别全出）；**轨道能级单位是 Hartree、费米能级是 eV，画能级图要 ×27.211 统一**（`S5.txt:1726–1841`）。
- **静电势 / 功函数**：Φ = 真空能级 − 费米能级，沿 Z 做平面平均取平台差值；CP2K 用 `v_hartree cube`（VASP 用 LOCPOT）；上下表面分别取（`S5.txt:1871–2014`）。**非对称 slab 做功函数必须开 `SURFACE_DIPOLE_CORRECTION` + `SURF_DIP_DIR Z`**，否则真空层电势不平（`S3.txt:932–949`，另见 `decide.md §14`）。
  > ✅ **关键字名更正（第二轮视频精读落层，2026-09）**：旧版此处写 `SURFACE_DIPOLE_DIRECTION Z`——**CP2K 没有这个关键字**
  > （官方 XML 0 命中）；正确的是 **`SURF_DIP_DIR`**（默认 `Z`，别名 `SURFACE_DIPOLE`/`SURF_DIP`；
  > 查证：`python _kw_probe.py --find SURFACE_DIPOLE_CORRECTION` 的官方描述里就点名
  > "The normal direction is given by the keyword **SURF_DIP_DIR**"）。
  > 讲师口播的是 "`SURFACE_DIPOLE_DIRECTION`"（字幕 `S3.txt`:933/942 转写作 `surface deo direction`）——**口播名有误**。
  > 另一条官方硬限制：`SURFACE_DIPOLE_CORRECTION` **只对"法向平行于某一笛卡尔轴"的 slab 实现**（官方描述原文），
  > 而 `decide.md:1094`"AIMD/常规计算最好别加（拖慢 SCF）"与本条**不冲突**：那是常规计算口径，**做功函数/静电势时必须加**。异质结电子流向 = 功函数差 + 电荷差分双证据，且**表面带电/缺陷状态不同会让电子流向反转**（`S5.txt:2014–2075`）；AIMD 后处理须多帧平均（20 ps 取 20 个结构：单点 2.53 vs 平均 2.40 eV，`S4.txt:3915–3937`）。
- **分子表面 ESP**：VESTA 先导入电子密度，再 `Edit → Edit Data → Volume Data → Surface Coloring` 导入 hartree density；ISO 默认太大，调到 0.01/0.001；染色范围调到 0.3~0.32 才看得到正负电中心（`S5.txt:2140–2188`）。受阻路易斯酸碱对判据 = 正/负电中心被晶格固定、彼此有距离（`S5.txt:2100–2138`）。
- 与 skill：`postprocess.py pdos` / `bader` 覆盖；ELF cube 由 `--properties elf` 生成（段名单数 `ELF_CUBE`）。

### A5. 自由能面（FES）三种方法（第 5 天；参数速查 `playbook.md §0.6/§2.6`）
- **PMF / 伞采样**：沿 CV 离散插点、每点加偏置窗；过渡态位置**强烈依赖插点密度**——讲师原话是"这中间少插了一个点，那这个能量就可能差个**零点几个电子伏特**"（`S5.txt:3010–3013`；**不是"0.1 eV 级"**）。
- **slow growth（缓慢增长）**：限制下让 CV 每步微增，捕捉自由能对 CV 的梯度 λ（blue moon），取平均得光滑 FES。**原理讲解处举例 +0.0001**（`S5.txt:3029–3030`）；**实操/讲义值为每步 `0.0005`**（1 万步使 CV 0.1700→5.1700，`S5.txt:3136–3139`、`L5 P23`）——字幕 `S5.txt:3075/3109` 口播的 0.005 是**丢零口误**。越小越准、越不易崩；可取负反向扫。
  > ⚠️ **关键字归属更正（第二轮视频精读落层，2026-09）**：旧版把上面这个"每步微增"写成 CP2K 的 **`INCREM`**——**错**。
  > `INCREM` / `ICRIN` / `ICONST` **都不是 CP2K 关键字**（官方 XML 各 0 命中），它们是 **VASP 侧**的：
  > `ICONST` 是**约束定义文件**（`L5.txt:171–183`），**`INCREM` 是 INCAR 标签**（`S5.txt` 3101–3111，讲师原话就在讲
  > "在这个 VSK（=VASP）做计算的过程当中……**in cut（=INCAR）** 这个文件里面"）。
  > ✅ **真名是 `INCREM`、`ICRIN` 不存在（2026-10 定案）**：VASP 官方 wiki 的 *Slow-growth approach* 页
  > 在 How-to 与 Related tags 里列的都是 **`INCREM`**（<https://vasp.at/wiki/index.php/Slow-growth_approach>）；
  > 讲义 `L5.txt:362` 写的 `INCREM = 0.0005` 是对的，`ICRIN` 只是字幕音译（`i cream` / `ACCREAM`）。
  > **CP2K 侧的对应物是 `&MOTION/&CONSTRAINT/&COLLECTIVE` 的 `TARGET_GROWTH`**：
  > 单位 **`[angstrom*fs^-1]`**，官方语义 `TARGET(t) = TARGET(0) + TARGET_GROWTH × TIMESTEP × step`。
  > **换算：`TARGET_GROWTH [Å/fs] = INCREM [Å/步] ÷ TIMESTEP [fs]`** ⇒ 每步 `0.0005` 配 `TIMESTEP 0.5 fs`
  > 就是 **`TARGET_GROWTH 0.001`**。
  > ⚠️ 别与 `&METADYN SLOW_GROWTH` 混：后者是"**让最后一个高斯峰慢慢长**"（官方描述 "Let the last hill grow slowly over NT_HILLS"），
  > **同名不同物**。详见 `course_learned.md §7.3`。
- **metadynamics（元动力学）**：自适应撒山填面；well-tempered 让山随时间变扁、收敛更稳。**加墙**：`K` 经验 40~100 kcal/mol（`S5.txt:4141–4144`），**上限墙必须加**（否则 H₂ 跑进真空层、模拟做不完），方向（`WALL_MINUS`/`WALL_PLUS`）定错整个模拟报废（`S5.txt:4128–4245`）；VASP 不能加墙，这是讲师眼中 VASP 做 metadynamics 的最大缺点（`S5.txt:4152–4158`）。
- 与 skill：`gen_inp.py --type metadyn`（含 `--well-tempered`/`--delta-t`/`--metadyn-ww`/`--lagrange`/`--multi-walker`/`--plumed`）已支持；`postprocess.py fes` 桥接 CP2K `graph` 重建 FES（**-ndim 必须填真实 CV 数**）。

### A6. VASPKIT / VMD 工具流速查（原笔记全文零命中）
- **VASPKIT 功能号**（讲师用它做轨迹统计，取代旧的自写脚本）：**`722` = MSD**（`S2.txt:1181`、`1223`）、**`727` = VACF**（`S2.txt:871–873`）、**`728` = vDOS**（`S2.txt:943–944`）、**`804` = 异质结建模**（`S2.txt:3915–3916`）。其余见 `playbook.md §3`。
- **VACF 的参考点间隔填 1**（以轨迹上每一个点都为参考，结果更准；VASPKIT 用 FFT 加速，长轨迹也快）（`S2.txt:901–918`）；曲线形状 = 体系振动强弱的判据（`playbook.md §5.2`）。
- **vDOS ≠ 红外谱**：它没考虑偶极；真 IR 要"把偶极信息和速度自相关一起做变换"（`S2.txt:758–858`）。静态频率的峰宽是人为高斯展宽，AIMD 的展宽才真实。
- **VMD**：算 MSD / RDF 前**必须先 align**（`S2.txt:1354–1372`）；**多帧叠加画"迁移路径图"**是论文标准插图——`Trajectory → Trajectory Drawing` 设起始帧/终止帧/**间隔**后叠加（`S2.txt:1657–1710`）；PBC 六行脚本、VDW + DynamicBonds 双层、关透视用正交、`Win+G` 录屏出 mp4 放 SI，见 `playbook.md §3`。

---

## B. 参数经验（对应 `decide.md`）

### B1. DFT+U —— 过渡金属氧化物"必须加"（建议提升为硬规则）
- 强关联 TM 化合物（TiO₂、Fe₃O₄ 等）：**不加 U 会定性错误**——电子不能局域在金属离子上，四价 Ti 不被还原，表面吸附物电子转移模拟不对。即使减速也要加。
- 与 skill：`--kinds "...:U=3"` 已支持（默认 MULLIKEN ramping，**`gen_inp` 发射 `L 2`** —— 注意措辞：**CP2K 自己的 `L` 默认是 `-1`**，`2` 是本工具发射值）。硬规则落点见 `decide.md §28.1`（含"金属单质 Fe/Ni 一般不用 U"与"U 单位必须写 `[eV]`，默认 a.u. 差 ~27 倍"的天坑）。

### B2. BSSE 警示 —— **讲师经验与官方关键字要分层**（建议提升为硬规则）
- **现象**：CP2K 用高斯基组 → 有 **BSSE（基组叠加误差）**，算吸附/结合能会**高估**（多数情况比 VASP 算的大一点，"结合偏强"）；基组越小 BSSE 越大。平面波程序（VASP）无 BSSE（`S2.txt:2972–3007`）。
- **讲师经验（口述，与关键字无关）**：BSSE 校正在**官方 `tests/` 目录里有现成算例**（如两个水分子结合）；做法是**把两个 fragment 各用完整基组分别算、能量再相减**；"精度要求高才做，差不多就行可以不做"（`S2.txt:4496–4529`）。字幕里 `BSSE` 一词只出现在"**用 `grep` 搜官方 `tests/` 目录学关键词**"的语境（`S3.txt:136–163`），**讲师从未把 `&BSSE` 作为校正方案给出**——旧版本写成"CP2K 可用 `&BSSE` 或 counterpoise"，属把讲师经验与官方关键字混为一谈。
- **权威出处**：讲义 `L2 P33`（四大缺点页，明确 BSSE）+ `L3 P40–P42`（定义与 DZVP / SR 基组量化）；手册侧 `&BSSE` / `FRAGMENT` 属另一层。**量化与机理一律以 `decide.md §28.2` 为准**（旧版把两组不同基线的数拼成一句，勿在此复述数字）。
- 与 skill：`decide.md` 吸附能/结合能判读应加此警示，避免"CP2K 算的吸附能偏大 = 算错了"的误判；数值速查见 `playbook.md §0.3`。

### B3. OT vs 对角化（讲师口语佐证 `decide.md` §22 / §28.3）
- 对角化是传统法（VASP 也用），速度慢，但对**金属体系**在 CP2K 里更好；OT 是现代默认、快，但原理上不适用于导体。
- 收敛辅助：对角化里常用 DIIS（`EPS_DIIS`），开 `&DIAGONALIZATION`。
- 与 skill：§22 已覆盖关键词落点与取舍，§28.3 收讲师实战佐证，此处不重复。

### B4. 轨迹抽帧 —— **与时间步长的耦合**（原条目漏了这层）
- AIMD 2 万帧的 movie 文件可能 ~59 MB，下载/处理困难。用 `md_simplify.py`（CP2K/VASP 通用）每 10~20 帧抽一帧再后处理（`S1.2.txt:1179–1196`、`S4.txt:2094–2126`）。
- **坑（易错 20 倍）**：抽帧后每帧的物理时间 = `POTIM` × 抽帧间隔。VMD 里 MSD / 横轴的 `timestep` 必须与所喂轨迹一致——喂完整 `cp2k-1.position` 填 `POTIM`（本例 2 fs，`S4.txt:3140–3144`）；喂 `new_position`（每 20 帧一帧）**必须填 2 fs × 20 = 40 fs**，否则横轴差 20 倍。
- **抽帧只用于看动画 / 降体积**：MSD、扩散系数必须用原始 `cp2k-1.position`（RDF 可用抽帧轨迹，但要跳过前 50~100 帧），**原始 position 必须存档**（`S4.txt:3134–3139`、`2765–2776`）。
- 与 skill：`postprocess.py` 直接吃轨迹，无需先抽帧；但若文件过大可先抽（统计量分析别用抽帧文件）。
- **"CSIS 这个库"的复核结论（2026-10）**：原条目里的 `cclib` / `ASE` 指的是同一处字幕
  `S1.2.txt:1185–1189`——讲师在讲自己写的通用抽帧脚本 `md_simplify.py`（VASP 读 `movie.xyz`、
  CP2K 读 `cp2k-position-1`）时说"可以自己在脚本基础上改，用这个 **CSIS** 这、呃，这个库去读这个参数也可以"。
  他在此处**明显在回忆库名**（有"这，呃"的停顿），转写作 `CSIS`：
  - 上下文要求的是**能读 XYZ/轨迹的 Python 库**；按此，**`ASE`（Atomic Simulation Environment）
    是最可能的所指**——它正是读 XYZ/轨迹的事实标准，且课程在讲 IRC 时也用过 ASE（`learn_L1.md §1.3`）；
  - `cclib` 主要解析**量化程序输出文件**（Gaussian/VASP 的 `.out`），与"读轨迹参数"的语境稍远，列为次要可能。
  ⇒ 处理方式：**不作为讲师原话引用**；需要时写"讲师提到可用第三方 Python 库读轨迹（转写为 `CSIS`，
  疑为 ASE）"。**不要写成讲师推荐了某个具体库**。

### B5. AIMD 调参总则与"跑前必测"（**细则已进 `decide.md §22.7` / `§31.1`，此处只留结论 + 指针**）
- **总原则**：**AIMD 牺牲少量精度换速度；静态计算（结构优化/过渡态）反过来牺牲速度换精度**（`S1.2.txt:640–652` → `decide.md §31.1`）。
- **AIMD 前必须做参数速度测试**：跑"三四步、两三步"、把 `PRECONDITIONER`/`MINIMIZER`（VASP 侧对应 ALGO 一类收敛控制参数）换一换比速度，选最快的再正式跑；CG 与 DIIS 谁快**因体系而异，必须实测**（`S1.1.txt:1859–1867`）。
- **`EPS_SCF` 有上限，不是越紧越好**：1E-7 会让单个 SCF 迭代时间过长、整条 AIMD 不可承受；讲师折中口径 1E-5（`S1.1.txt:1580–1627`）。**三档判据与数字以 `decide.md §22.7` 为准，此处不复述。**
- **含氢体系时间步长上限 1 fs**：只有"重元素且不含氢"才可放到 2 fs（`S1.2.txt:152–162`）；讲师自评用 2 fs 跑 Au₂₀ 致结构不稳、"应该用 1 fs"（`S4.txt:2133–2142`）。想放大步长应**改核质量**（氘代：H 质量设为 2，最大振动频率 3300→2500 cm⁻¹），**不要固定键长**——AIMD 里水常参与反应，固定键长会得到错误信息（`S1.1.txt:1770–1809`）。

---

## C. 建模实操（对应 `decide.md` §结构 / `gen_inp.py`；硬规则速查见 §G）

- 用 `&SUBSYS &TOPOLOGY COORD_FILE_NAME` 读坐标（CIF/POSCAR/xyz），或用 `&COORD` 内联；模板里用 `include` 把坐标文件读进来。
- 改晶胞边界：从 POSCAR/CIF 的 cell 行找到 `&CELL` 的 A/B/C 向量，重写进 inp。
- 原子顺序可重排：`DEMCAR -s`（写 POSCAR 时）或 Materials Studio 里调整，便于套模板。
- 与 skill：`gen_inp.py --topology POSCAR.cif --topology-format cif` 已覆盖"从文件读结构"，等价于这里讲师的 include 操作；`&COORD @INCLUDE` 的 `.inc` 必须删掉 XYZ 前两行、CIF 自带晶胞但 CP2K 不认等坑见 `playbook.md §4` / `decide.md §5`。

---

## D. 实例索引（供以后讲解/对照）

| 实例 | 出现天数 | 演示要点 |
|---|---|---|
| 水盒子（H₂O box）| 第 1–2 天 | RDF / MSD / 扩散标准流程（CP2K & VASP 对照）；RDF 读数 2 / 3.97（`L1 P65`、`S2.txt:444–452`）|
| 键长/键角跟踪（配合物反应）| 第 2 天 | 跟踪单键键长看化学反应进程；**跟踪键长时必须关掉 PBC**，否则曲线出现伪跳跃（`S2.txt:71–109`、`171–231`）|
| Li 固态电解质离子迁移（字幕"离者磷硫"）| 第 2 天 | 退火升温 + **5 个温度（600 / 800 / 1000 / 1200 / 1400 K）**平衡态 AIMD → VASPKIT `722` 算 MSD → D → **Arrhenius 拟合反推 Ea**（截距=指前因子）；讲师强调 NEB 的指前因子算不准，AIMD 是"反途径"（`S2.txt:1074–1143`、`1307–1345`、`1608–1656`）|
| TiO₂（二氧化钛）| 第 1 天 | DFT+U 演示（不加 U 电子不局域）|
| Cu 表面氧化 | 第 4 天 | AIMD 模拟 O₂/CO 插层、表面变氧化物 |
| **Au₂₀ 负载的晶胞选择**（**TiO₂** 表面上）| **第 1 天** | 2×2 / 3×3 / 4×4 的选择：**2×2 时 Au₂₀ 与周期性镜像太近，模拟中会连成"金的纳米棒/纳米片"、体系彻底失真**；太大则计算量指数上升、纯浪费机时（`S1.1.txt:2072–2150`）|
| 缺陷 TiO₂ 上的 Au₂₀（RDF 应用）| 讲义 `L1 P66–P67` | 完美 TiO₂ 表面 Ti–Au 无成键；有缺陷时 **Au₂₀ 金字塔坍塌、形成 Ti–Au 化学键**；CO 吸附时 C–Au 键不断、Au–Au 不断断裂再生成（`L1 P66–P67`，JACS 2013, 135, 10673）|
| Au₂₀ 团簇（第 4 天，**另一个话题**）| 第 4 天 | 质心-原子距离分析（自写 `max_center.py` ≈67 行 → `distance` → Origin Frequency Count）；讲师自评 2 fs 步长致团簇不稳、应用 1 fs（`S4.txt:3020–3098`、`2133–2142`）|
| CO 吸附在金属表面 | 第 5 天 | 电荷差分、ELF 看共价/离子成分 |

> ⚠️ **上表"Au₂₀ 负载的晶胞选择"的载体更正（2026-09，经讲义原文复核）**：
> 旧版此格写"**CO₂ 表面上**"——**错**。载体是 **TiO₂（二氧化钛）**，与 CO₂ 无关（CO₂ 是分子，不能当载体）。三层依据：
> ① 字幕 `S1.1.txt:2073` 的"二氧化碳"是**语音识别错字**（"二氧化钛"被听成"二氧化碳"，钛 tài / 碳 tàn；同一段里 `AIMD`→`AAMD`、`晶胞`→`金包`，可证是纯语音转写）；
> ② **讲义 `L1.txt` PAGE 66**（第 969–973 行）原文："完美的 **TiO₂** 表面上 **Ti** 和 **Au** 没有化学键作用，但是在有缺陷的 TiO₂ 表面上，Au₂₀ 金字塔结构坍塌，形成 **Ti-Au** 化学键。*J. Am. Chem. Soc.* **2013**, 135 (29), 10673-83."——含 **Ti–Au** 键 ⇒ 载体含 Ti；
> ③ 仓库自带真实算例 `references/h_tutorials/cases/TiO2-Au20_cp2k.inp` 同案（第 4 天字幕 `S4.txt`:2447–2448 也写"对这个**钛**加了 13.6 个电子伏特的优质"）。
> 📌 第二轮视频精读笔记（`videonotes/cp2k-1-1-...`）据同一句 ASR 误推成"CeO₂"，**不采用**；`course_learned.md §1.8` 有完整更正记录。

---

## E. 错字对照表（解码用，完整表见 `course_survey.md §3`）

- **完整表在 `course_survey.md §3`**（该表正扩充为带「出处」列、附字幕行号的可核对版本）；本文件不复制。
- 最高频：`cp two k`=CP2K、`VSP`=VASP、`AAMD`=AIMD、`验室/机组`=赝势/基组、`京弯`=晶胞、`军方位1`=MSD、`风`=峰、`差`=插、`BSS 1`=BSSE、`镜像分布函数`=RDF、`二氧化石`=TiO₂、`进二`=Au20、`PM 、 F`=PMF、`METDYNAMICS`=metadynamics、`ELF/ERF`=ELF。
- 读字幕时注意**数字丢零/口误**：slow growth 的每步增量口播 0.005、实务为 **0.0005**（`S5.txt:3075/3109` vs `L5 P23`；⚠️ **该增量是 VASP 侧 `ICRIN` 的量，CP2K 用 `TARGET_GROWTH`，见 §A5**）；`CSIS 这个库` 疑为 ASE（`S1.2.txt:1186–1189`，**存疑**）。

---

## F. CP2K 四大缺点（速查指针；完整清单见 `playbook.md §6.2`）

1. 导体计算慢（OT 原理上不适用导体 → 需较慢的对角化）
2. 磁性体系麻烦（要**手填自旋初猜**，不能自动找磁矩；⚠️ 官方 `MULTIPLICITY` 默认 `0` = 按电子数奇偶自动定，**只有高自旋态必须显式写**，见 `course_learned.md §4.7`）
3. **k 点功能不完善**
4. **BSSE**（高斯基组）

（`S2.txt:2869–3019` 讲师逐条归纳；讲义 `L2 P33` 同页。）

- **最反直觉之一：k 点的"对称性约化"要按官方口径理解**（旧版写成"CP2K 完全不做对称性约化"，**过强**）。官方 `cp2k_input.xml` 与 G 层 `02_dft_methods.md §4.6` 给出的是**两级**：① **时间反演（k↔−k）约化对规则网格默认就做**；② **原子（空间群）对称约化由 `&KPOINTS SYMMETRY` 控制、默认 `F`（关闭）**，需要时显式写 `SYMMETRY T`。⇒ 讲师"别指望对称性省机时"的经验在**默认设置下仍然成立**，但不是"不支持"。规避法不变：尽量只用 Γ 点，代价是晶胞边长 ≥10 Å，太小就扩成 2×2/3×3（`S2.txt:2919–2970`）。详见 `playbook.md §6.2` 注。
- **最反直觉之二：BSSE 的方向是"结合偏强"**。高斯基组 → 吸附能/结合能**被高估**，多数情况比 VASP 算的稍大；这不是"算错了"，而是基组不完备的系统性偏差（`S2.txt:2986–3007`）。详见 `decide.md §28.2`。

---

## G. 建模硬规则速查（**详版在 `decide.md §30`（批 14 新增）与 `§5.1`；此处只做索引，不复制**）

- `decide.md §30.1` **密度建准 = 可以完全跳过 NPT 预平衡**（`S2.txt:3555–3587`）· `§30.2` **异质结 mismatch 2–3%**（`S2.txt:3917–3996`）· `§30.3` 真空层 15 Å · `§30.4` **六方四指数在 MS 只输三个指数**（`S2.txt:3788–3793`）· `§30.5` 六方→正交配方 · `§30.6` `Build Layers` 会主动留空隙。
- `decide.md §5.1` **PBC 第一原则**：以原子为中心的作用范围（范德华、高斯基组）**必须小于盒子边长**，否则是原子与自身镜像的**虚假相互作用**（`S1.1.txt:2047–2056`、讲义 `L1 P28`）。讲师原例：Au₂₀ 放 2×2 金包会与镜像连成"金的纳米棒/纳米片"而彻底失真；反之放大到 4×4 则计算量"呈指数型往上增长"、纯浪费机时——**判据是要观察的物种尺度**（`S1.1.txt:2065–2150`）。
- 建模工具流（切表面与终端饱和、固液界面先对齐 A/B 边长、团簇、数据库、晶格矢量旋转）：`playbook.md §4.1–4.6`。
- **周期性体系带净电荷 ⇒ 强制引入均匀背景电荷**（第二轮视频精读补，`S3.txt:621–952`）：`CHARGE ≠ 0` 时程序会补一个均匀背景电荷中和，
  ⚠️ "**这个背景电荷有的时候会对我们这个计算产生一定的影响**" ⇒ **尽量保持 `CHARGE 0`**，做不到就**加抗衡离子**（讲师例：酸性溶液里加 Cl⁻）。详见 `course_learned.md §1.8`。
- **模型简化三步法**（上万原子 → 几十原子）与**结构信息的实验来源**（XPS / TEM-HAADF / XRD / XAS-EXAFS）：`course_learned.md §3.2`。
- **"什么时候该用 AIMD、什么时候不该用"**（静态路线只能给吸附能/解离能两个数 vs AIMD 给动态过程）：`course_learned.md §1.13`。

---

## H. VASP ↔ CP2K 对照速查（**第二轮视频精读新增**；VASP 列只作对照，**不是 CP2K 参数**）

> 出处：`videonotes/cp2k-1-2-VASP的AIMD与后处理-精读笔记`（全篇 VASP 侧总表）、
> `videonotes/cp2k-3-CP2K计算流程与参数详解-精读笔记 N-51`（讲师逐条给的 6 组对照）；
> CP2K 侧的默认值均已用 `python _kw_probe.py` 对官方 XML 核对（本文件与 `course_learned.md` 各节）。
> ⚠️ **用法约定**：左列是"同一个物理量在两个程序里怎么写/怎么读"，**VASP 写法不得直接抄进 CP2K 输入**。

| 物理量 / 概念 | VASP 侧（**不是 CP2K**） | CP2K 侧 |
|---|---|---|
| 时间步长 | `POTIM`（fs） | `&MD TIMESTEP`（fs） |
| 轨迹写入间隔 | `NBLOCK`（AIMD 一律 **1**；经典 MD 相反） | `&MOTION/&PRINT/&TRAJECTORY &EACH MD 1` |
| 原子质量（氘代） | `POMASS`（H→2；顺序须与 `POSCAR` 一致） | `&KIND H MASS 2`（工具：`--kinds "...:mass=2"`） |
| 系综 | `SMASS` + `MDALGO`（0=NVE、1=Andersen、2=Nosé–Hoover、3=Langevin） | `&MD ENSEMBLE`（⚠️ **官方默认是 `NVE`**，必须显式写 NVT/NPT_I/NPT_F） |
| 热浴耦合强度 | `SMASS`（−3 NVE / −1 速度调节 / ≥0 NVT+Nosé–Hoover；默认值查 `OUTCAR`） | `&THERMOSTAT &NOSE TIMECON`（默认 **1000 fs**；也可写 `[wavenumber_t]`） |
| 退火 | `TEBEG`/`TEEND` **线性**温度区间 + `SMASS=-1` | `&MD ANNEALING` **只能按倍率**（1.001 / 0.99）；⚠️ **与 `&THERMOSTAT` 实现层互斥** |
| 步数 | `NSW`（设大，够了 `scancel`） | `&MD STEPS` |
| 势能（文献画图用） | `E0`（`OSZICAR`，**一般取 E0 而不是 E**） | `.out` 的 `ENERGY` 行（`Total FORCE_EVAL`）/ `.ener` 的 `Pot` 列 |
| "平线"的守恒量 | `E`（动能+势能+热浴） | `.ener` 的 `Cons Qty`（+ `ENERGY DRIFT PER ATOM [K]`） |
| k 点 | `KPOINTS`（1×1×1 = Γ） | `&KPOINTS`（默认 Γ；**Γ 点要求晶胞边长 ≥ 10 Å**） |
| 赝势策略 | "**价电子最少的大核**"赝势 | GTH `q` 值取**最小可用** |
| 输出波函数 / 电荷 | `LWAVE` / `LCHARG`（`CHGCAR` 会涨到几十~几百 G ⇒ AIMD 关掉） | AIMD **不建议输出 wfn**；cube 不打印，事后挑结构单点算 |
| 轨迹格式 | `XDATCAR` → `xdat2xyz` → `movie.xyz` 才能进 VMD | `cp2k-pos-1.xyz` **直接进 VMD** |
| 抽帧脚本 | `md_simplify.py 20`（读 `movie.xyz`） | **同一个脚本**（读 `cp2k-pos-1.xyz`）；⚠️ 抽帧后横轴 = `POTIM × 间隔` |
| 重启 | `CONTCAR → POSCAR`（⚠️ 先删末尾速度块） | `&EXT_RESTART RESTART_FILE_NAME ...-1.restart`（`.restart` 本身就是输入文件） |
| 限制性 AIMD 的 CV 定义 | **`ICONST` 文件**（`R`/`A`/`T`/`M`/`X,Y,Z`/`S` + `STATUS`） | `&SUBSYS/&COLVAR`（几维写几个） |
| 让 CV 每步微增（slow growth） | INCAR 的 **`ICRIN`**（Å/**步**） | `&CONSTRAINT/&COLLECTIVE TARGET_GROWTH`（Å/**fs**；× `TIMESTEP` = 每步推进量） |
| 自由能梯度 λ 的输出 | `REPORT` 的 `b_m>` 行（取第 1 列平均） | `&CONSTRAINT/&LAGRANGE_MULTIPLIERS`（拉格朗日乘子 = 约束力 = λ） |
| 自由能面 | `ICONST` + `HILLSPOT` + `PENALTYPOT`；**不能加墙** | `&COLVAR` + `&FREE_ENERGY/&METADYN`（+ `&WALL` 加墙） |
| 元动力学重启 | `HILLSPOT → PENALTYPOT` | `&METADYN OLD_HILL_NUMBER`/`OLD_HILL_STEP`/`NHILLS_START_VAL`/`STEP_START_VAL` |
| 自旋极化开关 | `ISPIN` | `UKS`（= `LSD` = `SPIN_POLARIZED` = `UNRESTRICTED_KOHN_SHAM`） |
| 自旋多重度 | 无（只有 `NUPDOWN`，定不定义都可以） | `MULTIPLICITY`（默认 `0` = 按电子数奇偶自动定；**高自旋态必须显式写**） |
| 自旋初猜 | `MAGMOM` | `&KIND MAGNETIZATION`（数值 = **未成对电子数 µB**，负号 = 自旋向下） |
| 表面偶极校正 | `LDIPOL` / `IDIPOL` | `SURFACE_DIPOLE_CORRECTION` + **`SURF_DIP_DIR`**（⚠️ 只对"法向平行于笛卡尔轴"的 slab 实现） |
| 晶胞选择性优化 | `OPTCELL` 文件 | `&CELL_OPT CONSTRAINT Z`（二维材料保真空层） |
| 几何优化收敛判据 | `EDIFFG`（**单一**判据，只看最大受力） | `MAX_FORCE`/`RMS_FORCE`/`MAX_DR`/`RMS_DR`（**四个全 YES 才算收敛**） |
| 最终结构带晶胞 | `CONTCAR` **自带**晶胞 | `cp2k-pos-1.xyz` **不带**（用 `&TRAJECTORY FORMAT PDB` 或手动补） |
| 静电势输出 | `LVHAR = .TRUE.` → `LOCPOT` | `&DFT/&PRINT/&V_HARTREE_CUBE`（"这两个关键词是对应的"） |
| 波函数文件名的用法 | `WAVECAR` 固定名 | `<PROJECT>-RESTART.wfn`；重启要 `WFN_RESTART_FILE_NAME` + `SCF_GUESS RESTART` **成对**写 |

---

## I. 读文献 "Computational Method" → 反推参数（**第二轮视频精读新增**）

> 讲师把这套方法叫"**从文献里还原参数**"：读文献里的一句话，反推出一个输入数值。
> ⚠️ 下表的**措辞多出自 VASP 侧论文**，反推出来的落点要按程序换算（见 §H）；价电子数/文献体系的数字**只对该文献成立**。

| 文献里的写法 | 反推 | 出处 |
|---|---|---|
| "time step of 0.5 fs" | `POTIM` / CP2K `&MD TIMESTEP` | `S1.2.txt:103–398` |
| "hydrogen mass set to 2" / "deuterated water" | 氘代：`POMASS` / `&KIND H MASS 2`（最大振动 3300→2500 cm⁻¹，步长可放宽） | `learn_L1.md:520–524` |
| "gamma point only" | `KPOINTS` 1×1×1 / CP2K 默认 Γ（要求晶胞 ≥10 Å） | `learn_L1.md:520–524` |
| "no symmetry" | `ISYM = 0`（关对称性） | `learn_L1.md:520–524` |
| "temperature damping parameter = 100 fs" | `SMASS` **被调大**了（默认约每 40 fs 调节一次 ⇒ 写 100 说明动过它） | `S1.2.txt`（讲师逐条推理） |
| "velocity scaling thermostat" | `SMASS = -1`（速度调节法；**只能用于退火/预平衡**） | `MAPPING.md:217/219` |
| "equilibration 5 ps + production 40 ps" | 其实是**一条 45 ps 轨迹**，分析时丢掉前 5 ps | `videonotes/cp2k-1-2-...` L287–336 |
| "initial 3 ps is regarded as equilibration" | 丢前 3 ps（0.5 fs ⇒ **6000 步**） | `S4.txt:3488` |
| "O 2s²2p⁴ / Na 2s²2p⁶3s¹ / Au 5d¹⁰6s¹" | GTH 价电子数 ⇒ `-q6` / `-q9` / `-q11` ⇒ 基组名 `DZVP-MOLOPT-SR-GTH-q11` | `S4.txt:3423–3432` |
| "U = 13.6 eV for Ce/Ti" | `&KIND … &DFT_PLUS_U U_MINUS_J [eV] 13.6`（**必须带 `[eV]`**） | `L3.txt:2381`、`cases/TiO2-Au20_cp2k.inp:127` |
| "work function averaged over 20 snapshots" | 单点值不可信：**多结构平均**（例 2.53 → 2.40 eV） | `S4.txt:3915–3937` |
| "13 ps trajectory, first 3 ps equilibration" | 采样窗口只有 10 ps ⇒ 统计量要按 10 ps 讨论 | `S4.txt`（Au/水界面 Methods 精读） |

---

## J. 算例实测数字速查（**第二轮视频精读新增**；⚠️ **全部是"该算例/该文献"的读数，不是通用阈值**）

| 项 | 数值 | 出处 |
|---|---|---|
| 第 1 天水盒子 | **16 H₂O = 48 原子** | `videonotes/cp2k-1-1-...` L942–975 |
| Cu/水固液界面 | **186 原子**；Cu(111) 4×4 超胞边长 **10.2239 / 10.22 Å**；水 **30 个**、c = **8.58 Å** | `S2.txt:4200–4220`；`S3.txt` 1820–2030 |
| 结构优化收敛步数 | 例中 **163–165 步**收敛 | `videonotes/cp2k-3-...` L1466–1481 |
| 氧化铝体系末帧 | **123 原子**（固定前 120，只放开 3 个） | `L3.txt:1780–1799` |
| 吸附能量级 | 分子吸附 ≈ **−1 eV**；解离吸附 ≈ **1.5 eV** | `videonotes/cp2k-3-...` L1538–1541 |
| BSSE 量级 | DZVP ≈ **5 kcal/mol ≈ 0.2 eV**；换 QZ 后 <1 kcal | 讲义 `L3 P41`（权威见 `decide.md §28.2`） |
| SR 基组 | 提速 **2–3 倍**（64 分子盒子 25 s vs 111 s），代价是 BSSE 变大 | 讲义 `L3 P42` |
| Cu FCC 晶胞优化 | 初始 **3.61 Å** → 收敛 **3.682 Å**（PBE 高估实验值） | `S3.txt` 3839–3993 |
| `REL_CUTOFF` | 官方默认 **40 Ry**，建议 **50–60** | `S3.txt` 1093–1162 |
| 功函数例 | 真空能级 **0.3158** a.u.、费米能级 **0.1224** a.u. ⇒ **Φ = 5.26 eV**（未加偶极校正时真空位读数 ≈0.31 a.u.） | `S5.txt:1871–2014` |
| 频率例（表面吸附水，3N = 9 个） | 130.03 / 350.66 / 410.16 / 519.35 / 631.11 / 687.24 / 1604.04 / 3545.82 / 3701.88 cm⁻¹ | `L3.txt:1786–1799` |
| 游离 H₂O | 1617 / 3717 / 3822 cm⁻¹（`FULLY_PERIODIC F` ⇒ 3N−6 = 3 个） | `L3.txt:1806–1812` |
| FES 三例 | PMF **1.3 eV** / slow growth **1.5 eV**；metadynamics 填平 ≈ **80 ps**、判据 CV 来回跳 **≥10 次**；PMF 12 条轨迹合计 **7696** 个数据点 | `S5.txt:3056–3062`、`S5.txt` 1693/1701、L5 P50 |
| 单位换算 | 1 Hartree ≈ **27.211 eV**；1 Ry ≈ **13.6 eV**；1 bohr = **0.529 Å**；**23 kcal ≈ 1 eV**；1 eV ≈ **96 kJ/mol** | `S3.txt`/`S5.txt`（讲义换算页） |

- 引用规范：以上数字**必须带"算例/文献"限定**——它们不是通用阈值（第二轮视频精读反复强调这一点）。
