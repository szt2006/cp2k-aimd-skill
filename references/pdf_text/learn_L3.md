# 庚子计算《AIMD 与 CP2K》第3天讲义 — 全面逐页学习笔记（learn_L3）

> 来源文件：
> - PDF 文本：`references/pdf_text/L3.txt`（156 页，标注 `========== PAGE N ==========`）
> - 视频字幕：`D:\石大\化学软件\cp2k\cp2k课程资料_庚子计算 - 副本\讲义和课程视频字幕\3.txt`（4142 行）
> - 已有笔记：`references/course_notes.md`、`references/course_survey.md`
>
> 组织方式：按**主题**组织（不按页码）。所有公式/表格原文照抄。
> 标记约定：
> - 【新】= 本笔记发现、`course_notes.md` 尚未收录的新内容（详见末章缺口清单）。
> - （字幕补充）= 仅字幕有、PDF 没有的实操细节。
> - 主讲人：刘锦程。

---

## 0. 总览：第3天讲什么

第3天是从 VASP 转入 **CP2K 输入文件全参数 + 各类计算任务** 的核心一天。主题顺序：
1. CP2K 计算流程与文件类型
2. 输入文件写法（section 结构、变量、vim 插件）
3. 各 SECTION 逐个讲：GLOBAL / FORCE_EVAL / DFT / QS / MGRID / XC / SCF / PRINT / SUBSYS(KIND/CELL/COORD/TOPOLOGY)
4. 基组与赝势（GTH/MOLOPT，BSSE）
5. 输出文件与 .out 解读
6. 结构优化 / 晶胞优化 / K 点
7. 过渡态 NEB / CI-NEB
8. 频率计算
9. AIMD（NVT 等）
10. DFT+U 与磁性
11. 杂化泛函 HSE06、vdW（D3、rvv10）
12. 后处理（RDF / MSD / 扩散 / 质心 / constant potential）
13. 建模实操（MS / Packmol / Amorphous Cell）

---

## 1. CP2K 计算流程与文件类型

【新】整体流程（PDF P3、字幕全程）：
- 输入：`.inp` 输入文件 + 基组文件（`BASIS_SET/BASIS_MOLOPT` 等）+ 赝势文件（`GTH_POTENTIALS`）+ 坐标文件（`.xyz`/`.car`/`.cif` 等）+ 提交脚本。
- 计算：`CP2K` + 提交脚本（队列系统）。
- 输出：`.out`（主输出）、`.err`（报错，实际报错信息通常在 `.out` 末尾）、`.xyz` 轨迹、`.wfn` 波函数、`.cube` 格点（电荷密度/ELF/轨道）、`.ener` 动力学能量、`.restart` 等。
- 分析：`VESTA`/`Jmol`/`VMD`（结构、电子结构）、`Origin`/`TRAVIS`（曲线、光谱）、脚本（后处理）。

【新】输出文件清单（PDF P3）：
| 文件 | 内容 | 查看工具 |
|---|---|---|
| `*.inp` | 输入文件 | vim/编辑器 |
| `.xyz` | 坐标（默认不带晶胞） | VESTA/Jmol/VMD |
| `.out` | 完整输出 | 文本 |
| `.cube` | 格点文件（电荷密度/ELF/轨道） | VESTA/Jmol |
| `.wfn` | 波函数 | 重启读取 |
| `.ener` | 动力学能量 | Origin/脚本 |
| `.err` | 报错 | 文本 |

【新】手册与 examples 查找（PDF P4、字幕）：
- 手册：`https://manual.cp2k.org/trunk/index.html`
- 源码 `tests/` 目录有 ~3000 个测试输入（参数为优化过的最佳推荐，但未必最优）：用 `grep -iR keyword tests/` 找含某关键词的输入文件，例如 `grep -iR ADMM tests/`。
- 在线输入文件生成器（不好用）：`http://cp2k-www.epcc.ed.ac.uk/cp2k-input-editor/#/edit`
- 第一个例子（Si 体单点）：`https://www.cp2k.org/howto:static_calculation`

---

## 2. 输入文件格式基础

【新】section / subsection 结构（PDF P5–P6、字幕）：
- 文件一般命名为 `cp2k.inp`。
- 关键词以 **`&section_name` 开头、`&END section_name` 结尾**；顺序随意，但**嵌套不能乱**。
- 每行一个关键词 + 参数；大小写、空格不敏感。
- 示例骨架：
```
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME BASIS_SET
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    ...
  &END DFT
&END FORCE_EVAL
```

【新】vim 语法高亮插件（PDF P6、字幕详细步骤）：
- 地址：`https://www.cp2k.org/tools:vim`
- 步骤：
```
mkdir -p ~/.vim/syntax
wget -O ~/.vim/syntax/cp2k.vim http://manual.cp2k.org/trunk/cp2k.vim
# 在 ~/.vim 里新建 filetype.vim：
if exists("did_load_filetypes")
  finish
endif
augroup filetypedetect
  au! BufNewFile,BufRead *.inp setf cp2k
augroup END
```
- 颜色含义（字幕）：棕褐色=关键词，绿色=section，黑色=参数值。
- 作用：可一眼看出 section 是否配对（`&END` 缺失会立即报错，字幕强调"嵌套多了会看花眼"）。

【新】变量与 include（PDF P37、P47、字幕）：
- 定义变量：`@SET DATAPATH /opt/cp2k/cp2k-6.1/data`，调用用 `${DATAPATH}`。
- 基组/赝势文件可放当前目录，或用绝对路径，或写成变量形式，方便改路径（字幕强调"改模板第一件事就是改这个路径"）。
- 坐标外挂：`&COORD ... @INCLUDE 'coord.inc' ... &END COORD`（`coord.inc` = 去掉前两行的 `.xyz`）。

【新】提交任务（PDF P10、P50、字幕）：
- 单机：`mpirun -n 56 cp2k.popt cp2k.inp 1>cp2k.out 2>cp2k.err`（`-n`=物理核数，`cp2k.popt` 需在 PATH 内）。
- 超算（slurm 示例）：`module load cp2k/intel17/4.1-v2`，`srun -p pg2_64_pool -n 20 -N 1 cp2k.popt cp2k.inp 1>cp2k.out 2>cp2k.err`。
- （字幕补充）后台运行：`nohup ... >log 2>&1 &`；查看后台 `ps -ef | grep cp2k`；杀进程 `qdel`(队列) 或 `kill -9` / `top` 里 `k`；单机无队列系统时不方便，建议用队列。
- （字幕补充）超算需先 `source` 环境（setup、MKL），否则找不到 `cp2k.popt`。

---

## 3. GLOBAL Section

【新】控制整体计算任务类型（PDF P13、字幕）：
```
&GLOBAL
  PROJECT cp2k
  RUN_TYPE GEO_OPT
  PRINT_LEVEL LOW
&END GLOBAL
```
- `PROJECT`：任务名（建议统一写 `cp2k`，否则所有输出文件前缀随之改变，字幕提醒"改了名字会导致只识别 cp2k 前缀的脚本失效"）。
- `RUN_TYPE` 枚举（PDF P13 明确列出，**比 course_notes 更全**）：
  - `MD`：分子动力学
  - `GEO_OPT`：几何优化
  - `ENERGY_FORCE`：单点能 + 受力
  - `ENERGY`：单点能（不算受力）
  - `CELL_OPT`：晶胞优化
  - `BAND`：**NEB 过渡态**（注意！CP2K 里 BAND 不是能带，字幕强调"看到 BAND 容易误以为是能带，其实是 NEB"）
  - `PINT`：Path integral（PIMD）
  - `VIBRATIONAL_ANALYSIS`：振动频率
- `PRINT_LEVEL`：LOW（MD 用）/ MEDIUM 等（默认打印太多占硬盘、妨碍找关键信息，一般 LOW）。
- （字幕补充）`ENERGY` vs `ENERGY_FORCE`：前者只给单点能/电子结构，后者多算原子受力。

---

## 4. FORCE_EVAL Section

【新】（PDF P14、字幕）：
```
&FORCE_EVAL
  METHOD Quickstep
  STRESS_TENSOR None
&END FORCE_EVAL
```
- `METHOD` 枚举：
  - `FIST`：经典分子力学 MD
  - `QMMM`：QM/MM
  - `QUICKSTEP`：DFT、DFTB、SE、XTB、RPA、HF、post-HF 等第一性原理（最常用）
- `STRESS_TENSOR`：是否算晶胞应力。需晶胞体积/形状变化时打开（NPT、CELL_OPT、NVT/NVE/不优化晶胞时一般写 `None` 或不写）。
  - 字幕明确：NPT、CELL_OPT 要打开；NVT/NVE/不优化晶胞不用。
  - 打开写法：`STRESS_TENSOR ANALYTICAL`（字幕/PDF P75）。

---

## 5. DFT Section 总览与基组/赝势文件

【新】文件定位（PDF P15、字幕）：
```
&BASIS_SET_FILE_NAME BASIS_MOLOPT
&POTENTIAL_FILE_NAME GTH_POTENTIALS
```
- 基组文件常用 `BASIS_MOLOPT`；`BASIS_MOLOPT_UCL` 可选元素更多（重元素如 La、Ce）。
- 赝势文件常用 `GTH_POTENTIALS`。
- GTH 赝势 = Goedecker, Teter, Hutter 三人（1996），文献 *Phys. Rev. B 54, 1703 (1996)*。
- `BASIS_MOLOPT` = molecularly optimized basis（*J. Chem. Phys. 127, 114105 (2007)*）。

【新】DFT 下其它高频关键词（PDF P16、字幕，比 course_notes 更全）：
| 关键词 | 作用 |
|---|---|
| `UKS T` | 开壳层/自旋极化（别名 LSD / SPIN_POLARIZED / UNRESTRICTED，字幕） |
| `ROKS T` | 限制性开壳层（实际很少用） |
| `WFN_RESTART_FILE_NAME ./RESTART.wfn` | 读波函数（需配合 `SCF_GUESS RESTART`） |
| `MULTIPLICITY` | 自旋多重度 2n+1（字幕：氧气=三重态=3，甲基自由基=双重态=2，闭壳层=1） |
| `RELAX_MULTIPLICITY >0` | 允许多重度自动翻转（字幕：不好用，且会禁用 OT 等算法，不建议开） |
| `CHARGE` | 体系总电荷（字幕：周期性体系尽量设 0，否则引入背景电荷；分子体系无所谓） |
| `PLUS_U_METHOD` | DFT+U 方法（U 值在 &KIND 控制） |
| `SURFACE_DIPOLE_CORRECTION T` | 表面偶极校正（类 VASP LDIPOL） |
| `SURF_DIP_DIR Z` | 偶极校正方向（类 VASP IDIPOL，slab 法向一般 Z） |
| `EXCITATIONS` | TDDFPT 激发态 |

（字幕补充）周期性体系加电荷会引入均匀背景电荷补偿，一般建模技巧（如酸性溶液加抗衡离子 Cl⁻）把体系做成电中性。

---

## 6. QS Section（Quickstep 精度与外推）

【新】（PDF P17–P18、字幕）：
```
&QS
  EPS_DEFAULT 1.0E-14
  EXTRAPOLATION ASPC
  EXTRAPOLATION_ORDER 3
&END QS
```
- `EPS_DEFAULT`：总精度开关，联动 `EPS_CORE_CHARGE`、`EPS_GVG_RSPACE`、`EPS_PGF_ORB`、`EPS_KG_ORB` 等约 10 个 EPS_* 参数。默认 `1.0E-10`（粗糙，10 年前定的）；高精度建议 `1.0E-14`（Google Group 建议）。字幕：一般 `-12` 也可。
- `EXTRAPOLATION ASPC`（Always Stable Predictor Corrector）：用前几个离子步波函数组合外推下一离子步初猜，加速 SCF 收敛——**这是 CP2K 跑 AIMD 快的重要原因之一**。
- `EXTRAPOLATION_ORDER`：默认 3（有时调 2/1）。
- 重要限制（PDF P18、字幕）：**ASPC 不能与 K 点同时使用**！

---

## 7. MGRID Section（多重网格/截断能）

【新】（PDF P19–P21、字幕）：
```
&MGRID
  NGRIDS 4
  CUTOFF 300
  REL_CUTOFF 60
&END MGRID
```
- CP2K 用**多重网格叠加做 FFT**，每套网格截断能不同，减少计算量。网格从粗糙到精细 4 级（默认 `NGRIDS 4`，套数越多越快但不精确）。
- `CUTOFF`：整体网格最高精度，单位 **Ry（Rydberg）**，默认 280；现在文章一般 >400 Ry。
- `REL_CUTOFF`：多少网格点落到最精细级，默认 40 Ry，一般设 50~60。
- `USE_FINER_GRID`：提高精细度。
- （字幕补充，重要）**CP2K 的 CUTOFF 单位 Ry，与 VASP 的 ENCUT 完全不可比**：1 Ry ≈ 13.6 eV，且 CUTOFF 指"多重网格最高级"的截断，不是整体积分网格。VASP 取 ~400 eV 已很大，CP2K 取 400~500 Ry 才相当（实际远不够，详见下）。
- （字幕/PDF P21）**元素相关 CUTOFF**：Na, O, F, Ne, Fe, Ni, Zn, Ga 等需要 >800 Ry。论坛建议按元素表取不同 CUTOFF。一般文章 >400 Ry。相对能量（吸附能、反应能、结合能）误差可抵消，故取 400~500 Ry 足够；但绝对能量未完全收敛。

---

## 8. XC Section（泛函 / vdW / 杂化）

【新】基础泛函（PDF P23、字幕）：
```
&XC
  &XC_FUNCTIONAL PBE
  &END XC_FUNCTIONAL
&END XC
```
等价于（显式写法）：
```
&XC
  &XC_FUNCTIONAL NO_SHORTCUT
    &PBE T
    &END PBE
  &END XC_FUNCTIONAL
&END XC
```
- 可用 LIBXC 里的泛函。
- （字幕）周期性体系算杂化泛函比纯泛函慢 10~100 倍，故表面/材料体系常用 PBE（GGA）。

【新】vdW 校正（PDF P146–P147，字幕末尾提到 dftd3.dat 需复制到当前目录）：
- **DFT-D3**：
```
&XC
  &XC_FUNCTIONAL PBE
  &END XC_FUNCTIONAL
  &vdW_POTENTIAL
    DISPERSION_FUNCTIONAL PAIR_POTENTIAL
    &PAIR_POTENTIAL
      TYPE DFTD3
      PARAMETER_FILE_NAME dftd3.dat   # 在源码包 ./data，需复制到当前目录（字幕强调）
      REFERENCE_FUNCTIONAL PBE
      R_CUTOFF [angstrom] 15
      #CALCULATE_C9_TERM TRUE
    &END PAIR_POTENTIAL
  &END vdW_POTENTIAL
&END XC
```
- **SCAN + rvv10**（非局域 vdW）：
```
&XC
  &XC_FUNCTIONAL
    &LIBXC
      FUNCTIONAL XC_MGGA_X_SCAN
    &END LIBXC
    &LIBXC
      FUNCTIONAL XC_MGGA_C_SCAN
    &END LIBXC
  &END XC_FUNCTIONAL
  &vdW_POTENTIAL
    DISPERSION_FUNCTIONAL NON_LOCAL
    &NON_LOCAL
      TYPE RVV10
      PARAMETERS 6.3 0.0093
      KERNEL_FILE_NAME rVV10_kernel_table.dat
      CUTOFF 150
    &END NON_LOCAL
  &END vdW_POTENTIAL
&END XC
```

【新】杂化泛函 HSE06（PDF P155、字幕）：
- 公式（原文照抄）：
  $$E_{xc}^{HSE}=aE_x^{HF,SR}(\omega)+(1-a)E_x^{PBE,SR}(\omega)+E_x^{PBE,LR}(\omega)+E_c^{PBE}$$
- 输入（节选）：
```
&XC
  &XC_FUNCTIONAL
    &XWPBE
      SCALE_X -0.25
      SCALE_X0 1.0
    &END XWPBE
    &PBE
      SCALE_X 0.0
      SCALE_C 1.0
    &END PBE
  &END XC_FUNCTIONAL
  &HF
    &SCREENING
      EPS_SCHWARZ 1.0E-10
      OMEGA 0.11     # 截断长程 HF
    &END SCREENING
    &INTERACTION_POTENTIAL
      POTENTIAL_TYPE SHORTRANGE
      OMEGA 0.11
    &END INTERACTION_POTENTIAL
    &MEMORY
      MAX_MEMORY 2400   # 内存上限 MB/core
    &END MEMORY
  &END HF
&END XC
&HF
  FRACTION 0.25    # HF 比例 25%
&END HF
```
- 小贴士：用 `psmp` 版本（OpenMP+MPI 混编）提高内存效率；用 **ADMM** 辅助基组提速。
- 引用：HSE06 相关文献需引用。

---

## 9. SCF Section（对角化 vs OT）

### 9.1 通用参数（PDF P24、字幕）
```
&SCF
  SCF_GUESS RESTART
  EPS_SCF 1.0E-6
  MAX_SCF 300
  ...
&END SCF
```
- `SCF_GUESS`：`ATOMIC`（原子电荷密度/波函数初猜）或 `RESTART`（读已有波函数，文件不存在则退化为 ATOMIC）。
- `EPS_SCF`：SCF 收敛能量标准，**单位 hartree**，默认 `1.0E-5`，一般设 `< 1.0E-5`（字幕：1 a.u.=27.211 eV）。
- `MAX_SCF`：最大 SCF 迭代步数（一般 300；对角化金属体系可 500）。
- **【重要，字幕强调】与 Gaussian 不同：即使 SCF 不收敛，CP2K 也会继续算下一个离子步**，需自己注意收敛情况。

### 9.2 对角化方法（Diagonalization）（PDF P25–P29、P27、字幕）
- 原理：把解 **KS 方程** 转化为解本征方程，用 SCALAPACK 库求解，得本征值（轨道能量 ε）和本征矢（系数矩阵 C = 波函数展开系数）。
- 收敛判据：输入/输出密度矩阵的差别（PDF P26）。
- 模板（含 SMEAR / MIXING）：
```
&SCF
  SCF_GUESS RESTART
  EPS_SCF 1.0E-6
  MAX_SCF 500
  ADDED_MOS 500
  CHOLESKY INVERSE
  &SMEAR ON
    METHOD FERMI_DIRAC
    ELECTRONIC_TEMPERATURE [K] 300
  &END SMEAR
  &DIAGONALIZATION
    ALGORITHM STANDARD
    EPS_ADAPT 0.01
  &END DIAGONALIZATION
  &MIXING
    METHOD BROYDEN_MIXING
    ALPHA 0.1
    BETA 1.5
    NBROYDEN 8
  &END MIXING
&END SCF
```
- `SMEAR`（PDF P28、字幕）：费米能级附近电子占据在 0 K 由 1 突变为 0，不利于积分，故人为展宽使占据连续变化。展宽越大 SCF 越易收敛但越不精确。
- `EPS_ADAPT 0.05`：DIIS 收敛算法开启阈值（字幕：DIIS 仅在接近收敛时切换效果好，离收敛远切换反而有反效果）。
- `ADDED_MOS`：对角化专用，添加额外空轨道（金属体系 500）。
- 字幕：对角化是 VASP 也用的方法；CP2K 里对金属体系尚可；Google Group 有官方推荐模板。

### 9.3 OT 方法（Orbital Transformation）（PDF P30–P32、字幕）
- 原理：通过轨道转换、把占据空间参数化，降低部分空轨道计算量（只需算准占据轨道能量，PDF P29）。
- 模板：
```
&SCF
  MAX_SCF 100
  EPS_SCF 1E-06
  SCF_GUESS RESTART
  &OT T
    MINIMIZER CG        # 或 DIIS / BROYDEN
    LINESEARCH 3PNT
    PRECONDITIONER FULL_SINGLE_INVERSE   # 推荐；难收敛用 FULL_ALL（稳定但耗时）
    # 超大体系(编译CUDA)加：PRECOND_SOLVER INVERSE_UPDATE
  &END OT
  &OUTER_SCF T
    EPS_SCF 1.0E-05
    MAX_SCF 100
  &END OUTER_SCF
&END SCF
```
- `MINIMIZER`：CG / DIIS / BROYDEN（字幕：先测试 CG 还是 DIIS 哪个对当前体系快）。
- `LINESEARCH`：3PNT 或 2PNT（需测试）。
- `PRECONDITIONER`：`FULL_SINGLE_INVERSE`（推荐）或 `FULL_ALL`（稳定耗时）。
- `OUTER_SCF`：OT 第一圈 SCF 未收敛时，重新做 preconditioner 再做 SCF 可加速收敛（字幕：这是 OT 收敛小技巧，不要靠把 MAX_SCF 调很大硬凑）。

### 9.4 对角化 vs OT 对比表（PDF P30，原文）
| Diagonalization | Orbital transformation |
|---|---|
| Expensive | Cheap |
| Smearing | No smearing |
| Mixing | Poor convergence for metallic system |
| Doesn't support DFT+U | DFT + U method |
| Support KPOINTS sampling | No KPOINTS sampling |
| 计算量 O(M³) | 计算量 O(MN²) |
| M: 基函数数 | M: 基函数数, N: 占据轨道数 |
| 内存 O(MN) | |

- （字幕补充）**适用场景**：OT 适合带隙的半导体/绝缘体；对角化适合金属（OT 对金属收敛差，因无带隙区分占据/空轨道）。**OT 不能加 K 点、只能用 Γ 点**；**DFT+U 只能在 OT 下用**（对角化不能加 U，但金属一般也不用加 U，故无冲突）。
- （字幕补充，呼应 course_notes B3）OT 计算量随体系增大增长温和（MN²），对角化为 M³；OT 更快，AIMD 前务必测试 MINIMIZER / LINESEARCH / PRECONDITIONER。
- **course_notes 已收录** OT vs 对角化对金属取舍（B3），此处 PDF 提供更完整的对比表与公式。

---

## 10. PRINT（通用输出控制）

【新】（PDF P33、字幕）：`&PRINT` 无处不在（FORCE_EVAL、DFT、SCF 等 section 下都有）。
- 打印原子受力（默认**不打印**，需手动开）：
```
&FORCE_EVAL
  &PRINT
    &FORCES ON
    &END FORCES
  &END PRINT
&END FORCE_EVAL
```
- 波函数（默认打印，改名用 `FILENAME`）：
```
&FORCE_EVAL
  &DFT
    &SCF
      &PRINT
        &RESTART
          FILENAME =RESTART.wfn
        &END RESTART
      &END PRINT
    &END SCF
  &END DFT
&END FORCE_EVAL
```
- （字幕）电荷密度、PDOS、Mulliken 电荷、ELF、分子轨道、受力等全都靠 `&PRINT` 控制；不设置=不输出。设置方式是在对应 section 的 `&PRINT` 下写子块 + `FILENAME`。

---

## 11. SUBSYS：KIND / CELL / COORD / TOPOLOGY

### 11.1 KIND（元素/基组/赝势/磁性）（PDF P35–P36、P150–P154、字幕）
```
&KIND Si
  ELEMENT Si
  BASIS_SET DZVP-GTH-PADE
  POTENTIAL GTH-PADE-q4
&END KIND
```
- `ELEMENT` 真正定义元素；不写则取 KIND 名对应元素。
- KIND 名可自定义（如 `&KIND Fe_2` / `&KIND Fe_3`），用于区分不同价态/磁矩的同元素（字幕：二价铁、三价铁分别定义）。
- **基组/赝势一定要配套**（价电子数 q 一致，PDF P43–P44）。
- 改质量（AIMD 用）：`&KIND Au ... MASS 19.7`（PDF P119，把 197 改成 19.7 加速运动，失真但得统计信息）。

### 11.2 基组（BASIS_SET）详解（PDF P38–P43、字幕）
- 查看某元素可选基组：`grep Si BASIS_MOLOPT`；重元素用 `grep La BASIS_MOLOPT_UCL`。
- 劈裂/极化含义：`SZV < DZVP < TZVP < TZV2P < TZV2PX`（计算量递增）。
  - `DZVP` = double-ζ Valence Polarized（最常用，大体系首选；精度要求高用 TZVP）。
  - `VP` = Valence Polarized（加极化函数）。
  - 字幕：`Usage hint: 'NGRIDS 5'` 对带弥散基组计算更快（×2）。
- **MOLOPT** = molecularly optimized basis（*Phys. Rev. B 54, 1703 (1996)*）。
- **SR**（short range）基组（`DZVP-MOLOPT-SR-GTH` 等）：砍掉弥散贡献，对周期性固体/表面 slab 适用，提速 2~3 倍，但 **BSSE 增大 ~50%**（字幕：约增到 0.3 eV 量级）。
- **-q4** 是价电子数：基组与赝势必须统一（如 Ce 有 q12 / q30，精度越高越慢）。

### 11.3 赝势（POTENTIAL）详解（PDF P44、字幕）
- `grep Si GTH_POTENTIALS`：`GTH-BLYP-q4` / `GTH-BP-q4` / `GTH-PADE-q4` / `GTH-PBE-q4` 等。
- 赝势名里的 BLYP/PBE 表示针对该泛函开发；用其他泛函（SCAN、HSE）也可套用 PBE 赝势。
- 价电子数 -q 必须与基组一致。

### 11.4 基组重叠误差 BSSE（PDF P40–P41、字幕详细）
- 原因：高斯基组随原子走，AB 体系中 B 的基组也贡献于描述 A，使 E(AB) 被低估 → 结合能/吸附能偏负（高估稳定性）。平面波（VASP）基组不随原子，无 BSSE。
- 量级：DZVP 的 BSSE ≈ **5 kcal/mol ≈ 0.22 eV**（字幕：约 0.2 eV）；基组越大 BSSE 越小（TZ/QZ 几乎消失）。
- SR 基组使 BSSE 增大约 50%（≈0.3 eV 量级），但提速 2~3 倍（AIMD 常用 SR 基组换速度）。
- **course_notes 已收录** BSSE 警示（B2），此处 PDF 给出公式推导与数量级。

### 11.5 CELL（晶胞）（PDF P45–P46、字幕）
```
&CELL
  A 5.430697500 0.000000000 0.000000000
  B 0.000000000 5.430697500 0.000000000
  C 0.000000000 0.000000000 5.430697500
&END CELL
```
或
```
&CELL
  ABC 5.4306975 5.4306975 5.4306975
  ALPHA_BETA_GAMMA 90 90 90
&END CELL
```
- 默认单位 **[Angstrom]**。
- `PERIODIC`：默认 `XYZ`；可选 `X/Y/Z/XY/YZ/XZ/XYZ/NONE`（NONE=分子/非周期，需配 POISSON section）。
- 从文件读：`CELL_FILE_FORMAT` + `CELL_FILE_NAME`（CIF/XSF）。
- （字幕补充）**CP2K 晶胞与坐标分开读**（VASP 在 POSCAR 一起）；非周期体系要设 POISSON section。

### 11.6 COORD 与坐标读入（PDF P46–P49、字幕）
- 笛卡尔坐标（默认），分数坐标需 `SCALED .TRUE.`。
- `&COORD ... @INCLUDE 'coord.inc' ... &END COORD`：`coord.inc` = `.xyz` 去掉前两行（PDF P47）。
- 转换脚本（字幕/PDF P47）：`dmolcar2xyz.py ***.car`（`.car`→`.xyz`）；`dmolcar2xyz.py -s ***.car` 按 z 坐标从小到大重排（便于固定底层原子）。
- `&TOPOLOGY` 读坐标（PDF P48、字幕）：
```
&TOPOLOGY
  COORD_FILE_NAME coord.xyz
  COORD_FILE_FORMAT XYZ
&END TOPOLOGY
```
可读 XYZ/CIF/PDB/XTL 等；读入后 COORD 里不必再写。
- （字幕补充）AIMD 尽量把晶胞做成**正交晶系**方便后处理；六方可用 MS `Build-symmetry-Redefine lattice` 转正交（如石墨）。`grep PBC *.car` 看晶胞参数。

---

## 12. 输出文件与 .out 解读

【新】（PDF P54–P57、字幕）：
- `.wfn`：波函数文件，每次产生会把上一个存为 `.bak-n`（共 4 个，循环覆盖）；建议打印成 `RESTART.wfn`。未指定输出名时，文件名以 `PROJECT` 命名（如 `cp2k-RESTART.wfn`）。
- `.out` 解读（PDF P55–P57）：开头打印数学库/版本/计算类型/内存；然后大 "Quickstep"；基础参数。
- SCF 收敛表（PDF P56 原文示例）：
```
Number of electrons: 32
Number of occupied orbitals: 16
Number of molecular orbitals: 16
Number of orbital functions: 104
Extrapolation method: initial_guess
SCF WAVEFUNCTION OPTIMIZATION Broyden...
Step Update method   Time  Convergence       Total energy    Change
1    NoMix/Diag.    0.40E+00  0.6  0.75558724  -32.2320848878  -3.22E+01
...
10   Broy./Diag.    0.40E+00  1.1  5.6405E-09  -31.2978852054  -1.66E-06
*** SCF run converged in 10 steps ***
```
- 最终能量（PDF P57）：`ENERGY| Total FORCE_EVAL ( QS ) energy (a.u.): -31.297885372811002`；换算 `-31.2978853 Hartree * 27.211 = -851.659 eV`。
- `ATOMIC FORCES in [a.u.]`：每个原子受力；只有当四个收敛标准全 YES 才算收敛（结构优化）。
- （字幕补充）观察 SCF 收敛看 `.out` 里 `convergence` 逐行；能量 `-31.297...` 取最后一个。

---

## 13. 结构优化 GEO_OPT

【新】（PDF P59–P62、字幕、course_notes 未系统收录参数）：
```
&GLOBAL
  RUN_TYPE GEO_OPT
  OPTIMIZER LBFGS   # 超大体系
&END GLOBAL
&MOTION
  &GEO_OPT
    OPTIMIZER BFGS   # 中等体系（默认，快且通用）
    MAX_ITER 400
    MAX_DR 0.003
    RMS_DR 0.0015
    MAX_FORCE 0.0006    # = 6.0E-4 a.u./bohr
    RMS_FORCE 0.0003
    # &LBFGS
    #   MAX_H_RANK 30
    # &END LBFGS
  &END GEO_OPT
  &CONSTRAINT
    &FIXED_ATOMS
      LIST 1..54
      LIST 289..324
      # COMPONENTS_TO_FIX 控制固定方向
    &END FIXED_ATOMS
  &END CONSTRAINT
&END MOTION
```
- `OPTIMIZER`：`BFGS`（默认，中等体系）/ `LBFGS`（超大体系，一两千原子）/ `CG`（稳定但慢，一个离子步算数个 SCF）。
- **4 个收敛标准**（PDF P61、字幕强调比 VASP 严格）：`MAX_DR`、`RMS_DR`、`MAX_FORCE`、`RMS_FORCE`，**全部 YES 才收敛**（VASP 仅看最大受力 EDIFFG）。单位 a.u.（hartree/bohr）。
- 字幕：CP2K 默认收敛标准约相当于 VASP 的 0.02~0.03 eV/Å；过渡态可放宽（如改成 1E-3 或 8）易收敛，但结构优化不必改。
- 查看收敛：`grep Max\.\ g cp2k.out`；查看每步能量：`grep = cp2k-pos-1.xyz`（注释行含能量）。
- 轨迹：每步结构写在 `cp2k-pos-1.xyz`，可用 Jmol/VMD 看。
- 固定原子：`&CONSTRAINT &FIXED_ATOMS LIST 1..54`（点号=范围）；`COMPONENTS_TO_FIX` 控方向。

---

## 14. 晶胞优化 CELL_OPT

【新】（PDF P74–P78、字幕）：
```
&FORCE_EVAL
  STRESS_TENSOR ANALYTICAL
  &DFT
    &KPOINTS
      SCHEME MONKHORST-PACK 3 3 3
    &END KPOINTS
  &END DFT
&END FORCE_EVAL
&MOTION
  &CELL_OPT
    EXTERNAL_PRESSURE 1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0
    KEEP_ANGLES T
    KEEP_SYMMETRY T
    OPTIMIZER CG
    # CONSTRAINT Z
    # TYPE DIRECT_CELL_OPT
    &CG
      &LINE_SEARCH
        TYPE 2PNT
      &END LINE_SEARCH
    &END CG
  &END CELL_OPT
  &GEO_OPT
  &END GEO_OPT
&END MOTION
```
- `STRESS_TENSOR ANALYTICAL` 必须开（与 CELL_OPT 关联）。
- `EXTERNAL_PRESSURE`：3×3 矩阵（对角=各方向 1 atm 大气压）；非对角=剪切（一般不设）。
- `KEEP_ANGLES T` / `KEEP_SYMMETRY T`：保持夹角/空间群对称（看情况，高对称不稳定体系会自发到低对称，强开则锁死）。
- `OPTIMIZER CG`（稳定）；`CONSTRAINT Z` 只优化 XY（二维材料常用，防真空层消失）。
- `TYPE DIRECT_CELL_OPT` = 原子+晶胞同时优化（默认即同时）。
- 原包太小不准 → 扩胞 或 加 K 点（**仅对角化法可加 K 点**，字幕：OT 不能加 K 点，只能扩胞）。
- 查看：`grep CELL cp2k.out`（含 Volume、a/b/c 矢量、角度、是否正交）。
- 字幕实战：Cu FCC 优化前 3.6147 Å → 优化后 3.682 Å（PBE 高估晶胞，比实验大）。

---

## 15. K 点（KPOINTS）

【新】（PDF P77–P78、字幕，含重要坑）：
```
&KPOINTS
  SCHEME MONKHORST-PACK 3 3 3
  SYMMETRY T
  VERBOSE T
  FULL_GRID T
&END KPOINTS
```
- 与 VASP 类似；可用 MP 或 Γ 点方案。
- **（字幕重要坑）CP2K 的 K 点"残废"**：即使开 `SYMMETRY`，**也不会利用对称性缩减不可约 K 点数目**（与 VASP 不同），要么全开要么全关，计算量不因此减少。当前版本不支持，未来可能支持。
- 只能用于对角化方法（OT 无 K 点）。
- 数目越多越精确越慢。

---

## 16. 过渡态搜索：NEB / CI-NEB

【新】（PDF P79–P96、字幕部分）：
- 过渡态 = 一阶鞍点（MEP 路径上能量最高点，沿反应路径极大、正交方向极小）。
- 有些过程无过渡态（离子键断裂、共价键断裂成自由基、部分吸附脱附；但自由能面因熵效应可能有）。
- 方法分类：单初猜（DIMER）、反应物+产物（CI-NEB）、单反应物、势能面扫描。
- **NEB**（nudged elastic band）：反应物(0)到产物(P)插 P-1 个点，所有点一起优化；受两力：势能面力 + 链方向弹簧力。
- **nudge 过程**：只保留弹簧力平行路径分量 + 势能力垂直路径分量，使收敛后正确描述 MEP。
- **CI-NEB**（climbing image）：能量最高点不受相邻弹簧力、且将其平行路径的势能力分量符号反转，使其爬到过渡态；只需很少点（含初末态 3~5 个，远则 6~8 个）。
- CP2K 输入（PDF P91–P93）：
```
&MOTION
  &BAND
    BAND_TYPE CI-NEB
    ALIGN_FRAMES F
    ROTATE_FRAMES F
    NUMBER_OF_REPLICA 6
    K_SPRING 0.08
    &CONVERGENCE_CONTROL
      MAX_DR 0.01
      MAX_FORCE 0.001
      RMS_DR 0.02
      RMS_FORCE 0.001
    &END CONVERGENCE_CONTROL
    &CI_NEB
      NSTEPS_IT 5
    &END CI_NEB
    &OPTIMIZE_BAND
      OPT_TYPE DIIS
      OPTIMIZE_END_POINTS F
    &END OPTIMIZE_BAND
  &END BAND
  &REPLICA
    COORD_FILE_NAME ./1.xyz
  &END REPLICA
  ...（2.xyz ~ 5.xyz 各一个 &REPLICA）
&END MOTION
```
- 关键词表（PDF P93 原文）：
| 关键词 | 示例 | 解释 |
|---|---|---|
| NPROC_REP | 28 | 每个结构用 CPU 数 |
| NUMBER_OF_REPLICA | 6 | 总结构数（含初末态）；NPROC_REP×NUMBER 可 > 总核数，按核数/ NPROC_REP 并行算点数 |
| BAND_TYPE | CI-NEB | NEB 计算方法 |
| ALIGN_FRAMES/ROTATE_FRAMES | F | 禁止整体平移/旋转 |
| K_SPRING | 0.08 | 弹簧劲度；大=快但不准，小=慢但准；先 0.08 再放松至 0.02 取精 |
| NSTEPS_IT | 5 | 启用 CI 前先用 IT 算法的步数 |
| OPTIMIZE_END_POINTS | F | 是否优化初末态（否；仍要计算，不能像 VASP 不算初末态）|
- 工作流（PDF P91）：① 优化初末态；② `tail -[原子数+2] cp2k-pos-1.xyz > is.xyz` 取末帧；③ `./xyz2neb.pl is.xyz fs.xyz 5` 生成 0~5.xyz（中间 4 个待算）；④ 准备 &SUBSYS 一个占位结构；⑤ 写 &MOTION &BAND。
- 跟踪收敛：`grep -1 MAX cp2k-BAND6.out`；结构：`for i in {1..6}; do tail -n 125 "cp2k-pos-Replica_nr_${i}-1.xyz" > neb.xyz; done`（PDF P94–P95）。
- 能量画图（PDF P96）：单位 a.u.，`E_a=0.21 eV`，`ΔE=-0.42 eV`。
- 字幕：VASP(VTST) 最常用 DIMER / CI-NEB；CP2K 也有。CP2K 引用：NEB 相关文章。
- **course_notes 在 D 实例索引/第4天提 NEB，但第3天 PDF 给出完整 CI-NEB 输入与脚本 `xyz2neb.pl` 是新增细节**。

---

## 17. 频率计算（VIBRATIONAL_ANALYSIS）

【新】（PDF P97–P108、字幕部分）：
- **Hessian 矩阵**（PDF P98）：
  $$H_{i,j}=\frac{\partial^2 E}{\partial x_i\partial x_j}$$
  3N 维实对称矩阵。
- **质量权重 Hessian（力常数矩阵）**（PDF P99–P100）：
  $$\Theta = M^{-1/2} H M^{-1/2},\quad \Theta_{i,j}=\frac{H_{i,j}}{\sqrt{M_i M_j}}=\frac{\partial^2 E}{\partial q_i\partial q_j}$$
  $q_i = \sqrt{m_i}\,\xi_i$，$M$ 为 3N 对角质量矩阵。
- **振动频率**（PDF P101）：对角化 Θ 得本征值 λ_i 与本征矢；非线性分子 3N-6 模式，线性 3N-5。
  $$\nu_i = \frac{1}{2\pi}\sqrt{\lambda_i}$$
  本征矢=振动方向；6 个平动/转动投影可忽略（气态/液态）；表面吸附分子平动转动耦合进这 6 个，可按 3N 算。
- **零点振动能 ZPVE**（PDF P103）：
  $$\hat H\Psi=H\Psi=\left(-\frac{\hbar^2}{2m}\frac{d^2}{dx^2}+\frac{1}{2}kx^2\right)\Psi,\quad E_{vib}=\left(n+\frac{1}{2}\right)hv$$
  n=0 基态能量 hv/2 = ZPVE（0 K 振动能，基于谐振近似）。
- **有限位移法**（PDF P104）：对每个原子 ±x,±y,±z 共 6 方向位移，数值求二阶导（力常数），共 **6N+1 次 SCF**（CP2K 用数值法；VASP 仅 Γ 点，须配 phonopy 算声子谱）。
- 输入（PDF P105、P108）：
```
&GLOBAL
  RUN_TYPE VIBRATIONAL_ANALYSIS
&END GLOBAL
&VIBRATIONAL_ANALYSIS
  DX 0.01
  INTENSITIES T
  NPROC_REP 7
  FULLY_PERIODIC T
&END VIBRATIONAL_ANALYSIS
&MOTION
  &CONSTRAINT
    &FIXED_ATOMS
      LIST 1..120
    &END FIXED_ATOMS
  &END CONSTRAINT
&END MOTION
```
- `NPROC_REP`：每结构 CPU 数；结构数=总核数/NPROC_REP（如 56/7=8）。**固定原子算频率须用尽量多并行结构，否则出现不合理虚频**（PDF P106）。
- `FULLY_PERIODIC F`：分子体系去平动/转动模式（得 3N-6）。
- 工作流（PDF P106–P107）：① 结构优化/过渡态搜索；② `mkdir freq`，`tail –[原子数] ../cp2k-pos-1.xyz > coord.inc`；③ 提交；④ `./cp2kfreq.pl cp2k.out` 得频率（实频…0，虚频…1）；⑤ 振动模式：`tail –[原子数] ../cp2k-pos-1.xyz > last.xyz`，`./cp2kfreq2mov.pl cp2k.out last.xyz` 生成 mode-N.xyz，Jmol 选 Tool–animate–palindrome 看。
- IR 强度：`&DFT &PRINT &MOMENTS` 开启；`grep -E "Freq|Intensities" cp2k.out` → `VIB|Frequency (cm^-1) ...` / `VIB|Intensities ...`。
- 实例（PDF P106）：H₂O 频率 1617/3717/3822 cm⁻¹（实频）；表面吸附可固定 slab 只让吸附原子振动。
- **course_notes A3 已收录频率→动画流程（cp2k_frequency_to_movie），但本 PDF 给出完整 VIBRATIONAL_ANALYSIS 输入、`cp2kfreq.pl`/`cp2kfreq2mov.pl`、ZPVE/Hessian 公式，是新增细节。**

---

## 18. AIMD（分子动力学）

【新】（PDF P109–P113、P118–P125、P130–P144、字幕部分）：
```
&GLOBAL
  RUN_TYPE MD
&END GLOBAL
&MOTION
  &MD
    ENSEMBLE NVT
    STEPS 500000
    TIMESTEP 0.5
    TEMPERATURE 600.0
    # ANNEALING 0.98
    &THERMOSTAT
      TYPE NOSE
      # REGION MASSIVE
      &NOSE
        LENGTH 3
        YOSHIDA 3
        MTS 2
        TIMECON [wavenumber_t] 1000
      &END NOSE
    &END THERMOSTAT
  &END MD
  &PRINT
    &TRAJECTORY
      &EACH
        MD 1
      &END EACH
    &END TRAJECTORY
    &VELOCITIES
      &EACH
        MD 1
      &END EACH
    &END VELOCITIES
    &RESTART_HISTORY
      &EACH
        MD 500
      &END EACH
    &END RESTART_HISTORY
  &PRINT
&END MOTION
```
- 参数表（PDF P111 原文）：
| 关键词 | 设置 | 解释 |
|---|---|---|
| ENSEMBLE | NVT | 小体系 NVT，大体系可 NVE/NPT |
| STEPS/TIMESTEP | 500000/0.5 | 总步数 / 步长 [fs] |
| TEMPERATURE | 600 | 温度 |
| ANNEALING | 0.98 | 退火系数，每步基准温度=前一步×0.98 |
| THERMOSTAT/TYPE | NOSE | Nose-Hoover；可选 AD_LANGEVIN/CSVR |
| THERMOSTAT/REGION | GLOBAL | 所有原子耦合一个热浴；MASSIVE=每自由度一个热浴 |
| NOSE/TIMECON | 1000 | 热浴链时间常数 [cm⁻¹]，多数取 1000，默认 [fs] |
| PRINT/TRAJECTORY/MD | 1 | 每几步打印坐标 |
| PRINT/VELOCITIES/MD | 1 | 每几步打印速度 |
| PRINT/RESTART_HISTORY/MD | 500 | 每几步单独存 restart |

- 注意事项（PDF P112、字幕）：
  - 轨迹 `cp2k-pos-1.xyz` 默认 XYZ（不带晶胞），尽量用正交格子。
  - `&MOTION` 里可同时保留 GEO_OPT 和 MD，靠 `RUN_TYPE` 切换。
  - 每 1 步存轨迹/速度/`cp2k-1.restart`；每 500 步存 `cp2k-1_****.restart`。
  - **重启 AIMD 直接把 `cp2k-1.restart` 当输入提交**（含轨迹/速度/热浴信息）。
  - 可在 `&SCF &PRINT &RESTART OFF` 关掉波函数输出避免 I/O 浪费（字幕：AIMD 频繁读写硬盘损寿命、撑大文件，建议关）。
- 输出 `cp2k-1.ener`（PDF P113）：`Step Nr. Time[fs] Kin.[a.u.] Temp[K] Pot.[a.u.] Cons Qty[a.u.] UsedTime[s]`。
- **质量加速 trick**（PDF P119）：`&KIND Au MASS 19.7`（197→19.7），使 Au 运动加快得统计意义，代价是失真。
- 固定原子（PDF P119、字幕）：`&CONSTRAINT &FIXED_ATOMS LIST 1..54 LIST 289..324`（固定最下 O-Ti-O 层）。
- **course_notes 未系统收录 AIMD 完整输入参数表**（仅 C 建模、B4 抽帧），本 PDF §18 是新增。

---

## 19. AIMD 后处理（RDF / MSD / 扩散 / 质心 / constant potential）

【新】（PDF P120–P144、字幕部分）：
- 后处理入口（PDF P120–P125）：
  - 画能量/温度曲线。
  - 运动轨迹存 movie：VMD 中 `pbc set {17.7540 19.4907 27.2817} -all` / `pbc box` / `pbc wrap -all` / `display depthcue off` / `color Display Background white` / `display rendermode GLSL`。
  - **RDF**（PDF P122、字幕）：VMD–Analysis–Radial pair distribution function g(r)；**先加 pbc set 否则不准**；Ti-O / Au-Ti / Au-O 因固定原子出现尖峰。
  - 质心分布：`python masscenter-TiO2.py newpos.xyz`（PDF P124）。
  - **MSD/RMSD**（PDF P125、字幕）：VMD–Analysis–RMSD Trajectory Tool；**RMSD 最好在不加 pbc set 前算**，否则原子穿越边界可能不对。
  - z 方向分布：`python zdistr.py cp2k-pos-1.xyz H`（PDF P131）。
  - Cu-O/Cu-H RDF（PDF P132）：忽略前 500 帧当预平衡。
- **均方位移 MSD**（PDF P137–P140）：
  - 定义：粒子相对参考位置随时间变化；VMD 算 RMSD（Root Mean Square Displacement），平方得 MSD。
  - 取参考点平均：因 AIMD 短（<100 ps）曲线震荡，取 0/500/1000/1500/2000 帧为参考点算 RMSD 再平均、再平方得 MSD（字幕：取多参考点平均得拟合更好的线）。
- **扩散系数**（PDF P141–P143）：
  - Einstein 公式：3 维 d=3，**D = MSD 斜率 / 6**（模拟越久越准）。
  - 另一种 Green-Kubo（速度自相关）不便。
  - 数据表（PDF P142 原文，含 600~1400 K）：
| T/K | 1000/T | MSD A²/ps | D A²/ps | D cm²/s | log(D) |
|---|---|---|---|---|---|
| 600 | 1.666667 | 0.44461 | 0.0741017 | 7.41017E-06 | -5.13017 |
| 800 | 1.25 | 1.03847 | 0.1730783 | 1.73078E-05 | -4.76176 |
| 1000 | 1 | 2.18712 | 0.36452 | 3.64520E-05 | -4.43828 |
| 1200 | 0.833333 | 3.61754 | 0.6029233 | 6.02923E-05 | -4.21974 |
| 1400 | 0.714286 | 4.3699 | 0.7283167 | 7.28317E-05 | -4.13768 |
  - **阿伦尼乌斯**（PDF P143）：`log(D)` 对 `1000/T` 斜率 = `-Ea/(2.303 k_B)`；本例斜率 `-1.07871`，`k_B=8.6173×10⁻⁵ eV`，得 **Ea=0.2141 eV**（截距 -3.35865）。
- VMD 多帧同显（PDF P144）：Graphics–Representation–Trajectory–Draw Multiple Frames `b:s:e`（初始:间隔:终止）。
- **Constant potential**（PDF P133–P134）：标准氢电极 SHE 相对真空绝对电位 **4.44 V**；`2.40 V(vs Vacuum) ≡ -2.04 V(vs SHE)`，`3.81 V(vs Vacuum) ≡ -0.63 V(vs SHE)`。做法：建模→优化→预平衡→跑 20 ps AIMD，每 1 ps 取结构算单点拿功函，20 个平均得平均功函。
- **course_notes A1/A2 已收录 RDF 配位数球面积分、MSD 先平方再平均、PBC 坑**，但本 PDF 给出完整 AIMD 后处理流程、扩散系数数据表、Arrhenius 推导、constant potential 定量换算，是新增补充。

---

## 20. DFT+U 与磁性

【新】（PDF P148–P154、字幕部分、course_notes B1 已收录"必须加"经验）：
- 输入（PDF P148）：
```
&DFT
  PLUS_U_METHOD MULLIKEN
  &KIND Fe
    BASIS_SET DZVP-MOLOPT-SR-GTH
    POTENTIAL GTH-PBE-q16
    &DFT_PLUS_U
      EPS_U_RAMPING 1.0E-3
      U_RAMPING 0.1
      L 2
      U_MINUS_J [eV] 4.0
    &END DFT_PLUS_U
  &END KIND
&END DFT
```
- 参数：`EPS_U_RAMPING`（激活 +U 的 SCF 阈值，促收敛）、`U_RAMPING`（U 递增值）、`L`（轨道角量子数，2=d，3=f）、`U_MINUS_J`（有效 U 值）。
- **收敛技巧 ramping**（PDF P149）：OT 换用 DIIS；先用较低 U 优化收敛，再逐步 `U_RAMPING` 递增到 `U_MINUS_J`。
- 字幕/PDF：**不同程序的 U 值无相互参照价值，别直接把 VASP 的 U 给 CP2K 用**。
- 原子磁矩初猜：`&KIND ... MAGNETIZATION 1.0/4.0/5.0/-5.0`（PDF P150、P152）；反铁磁 inverse spinel（PDF P151–P153）：四面体 Fe³⁺ 与八面体 Fe²⁺/Fe³⁺ 自旋相反；初猜磁矩不一定等于最终排列，SCF 中自动调整，最后用原子电荷/自旋布局/自旋密度分布（黄=Spin UP，蓝=Spin DOWN）判断。
- 老办法 `&BS`（PDF P154）：`&ALPHA`/`&BETA` 下 `NEL`/`L`/`N` 指定轨道电子数变化（如 Fe 4s²3d⁶ → α: 4s (2-2)/2=0, 3d (6+4)/2=5；β: 4s 0, 3d (6-4)/2=1）。
- **course_notes B1 已收"TM 氧化物必须加 U"经验**，此处 PDF 给出完整 DFT+U 输入、ramping 机制、磁性初猜、&BS 老办法，是新增参数细节。

---

## 21. 有用教程链接（PDF P145）

【新】CP2K 官方 exercises：
- PMF：`https://www.cp2k.org/exercises:2018_ethz_mmm:pmf`
- metadynamics（配位数作变量）：`https://www.cp2k.org/exercises:2015_cecam_tutorial:mtd1`
- HF exchange & ADMM：`https://www.cp2k.org/exercises:2016_summer_school:hfx`
- 乙炔在金属间表面吸附：`https://www.cp2k.org/exercises:2018_ethz_mmm:adsorption_2018`
- 石墨烯/h-BN 的 PDOS：`https://www.cp2k.org/exercises:2016_uzh_cmest:calculating_pdos`
- KCl QMMM 模型验证：`https://www.cp2k.org/exercises:2018_ethz_mmm:qmmm_2018`

---

## 22. 建模实操（MS / Packmol / Amorphous Cell）

【新】（PDF P63–P73、字幕全程演示）：
- **Cu(100)+46H₂O 结构优化（练习一）**（PDF P63）：晶胞优化→切 100 面建水/金属模型→优化表面（模板）→读最后能量。
- 加溶剂水分子：手动复制（初始构型差）或 **Packmol**（生物体系加水）、**MS Modules–Amorphous Cell**（给 slab 加水好用，PDF P64–P67）：建 H₂O 分子→Amorphous cell construction→Add 水分子改数量→密度 1 g/cm³→Specify a,b 边长（MS 自动判 c）→run 得 Molecule.xtd→In-Cell 显示 lattice→Build-build layer 建异质结→调水/slab 距离（接近表面水密度≠1 g/cm³，需按 Cu 半径留空间）→rebuild crystal 调 z。
- 提交：保存 `.car`→`dmolcar2xyz.py -s Layer.car`（按 z 排序）→`Layer.xyz` 去前两行→`@INCLUDE` 读入→套 inp 模板改 `&CELL`（`grep PBC *.car`）→固定最下两层 Cu（`LIST 139..170`）→提交。
- 轨迹查看：Jmol/VMD 打开 `cp2k-pos-1.xyz`；看每步能量 `grep = cp2k-pos-1.xyz`。
- **练习二：Al₂O₃(0001) 上 H₂O 吸附能**（PDF P70）：孤立 H₂O、Al₂O₃ 表面、H₂O 吸附、H₂O 解离吸附四者分别优化，吸附能 = E(H₂O-Al₂O₃) − E(H₂O) − E(Al₂O₃)。实例值：H₂O -17.2199 a.u.，Al₂O₃ -1261.3349 a.u.，吸附 -1.13 eV，解离 -1.54 eV（需换算 a.u.→eV）。
- **给 xyz 加晶胞边界三种方法**（PDF P71–P72）：① MS build–build crystal；② VMD `pbc set {7.820 7.821 7.823 90 90 120} -all` / `pbc box` / `pbc wrap -all`；③ CP2K 直接 `&MOTION &PRINT &TRAJECTORY FORMAT PDB`（自带晶胞）。
- **课后练习**：Au₂₀/TiO₂(110) 优化（套 OT 模板、固定最下 O-Ti-O、改晶胞、加基组赝势、加 DFT+U，PDF P73）。
- **course_notes C 已收录 include/改晶胞/DEMCAR -s**，此处 PDF 给出完整 Cu(100)+水、Al₂O₃ 吸附能四态法、Amorphous Cell 加水、三种加晶胞法，是新增实操细节。

---

## 23. 工具 / 脚本 / 软件清单

【新】本天出现的所有工具（汇总，便于 skill 落地）：
| 工具 | 作用 | 出现处 |
|---|---|---|
| `cp2k.vim` | vim 语法高亮 | PDF P6/字幕 |
| `grep -iR keyword tests/` | 查 CP2K 测试输入 | PDF P4/字幕 |
| `@SET` / `@INCLUDE` | 输入文件变量/外挂坐标 | PDF P37/P47 |
| `dmolcar2xyz.py` | .car→.xyz（`-s` 按 z 重排） | PDF P47/字幕 |
| `Packmol` | 生物体系加水分子 | PDF P63 |
| MS `Amorphous Cell` | slab 加溶剂化层 | PDF P64 |
| `xyz2neb.pl` | NEB 插点 | PDF P91 |
| `cp2kfreq.pl` | 解析频率输出 | PDF P106 |
| `cp2kfreq2mov.pl` | 生成振动模式 xyz | PDF P107 |
| `cp2k_frequency_to_movie` | 频率→动画（course_notes A3） | 笔记 |
| `masscenter-TiO2.py` | 质心-原子分布 | PDF P124 |
| `zdistr.py` | z 方向分布统计 | PDF P131 |
| `max_center.py` | 质心分析（course_notes，Au20） | 笔记 |
| `md_simplify.py` | 轨迹抽帧（course_notes B4） | 笔记 |
| VMD / Jmol / VESTA / MS / Origin / TRAVIS | 可视化/后处理 | 多处 |
| `dftd3.dat` / `rVV10_kernel_table.dat` | vdW 参数文件（须复制到当前目录） | PDF P146-147/字幕 |

---

## 24. 文献索引（本天出现，【新】汇总）

- *Phys. Rev. B 54, 1703 (1996)* — GTH 赝势 / MOLOPT 基组
- *J. Chem. Phys. 127, 114105 (2007)* — BASIS_MOLOPT
- *J. Chem. Phys. 152, 194103 (2020)*; doi:10.1063/5.0007045 — CP2K 相关
- *Proc. Natl. Acad. Sci. U. S. A. 2017, 114 (8), 1795-1800* — 固液界面/水层建模
- *Science 2003, 299 (5608), 864-867* — Au₂₀/TiO₂(110)
- *J. Am. Chem. Soc. 2013, 135 (29), 10673-83* — Au₂₀/TiO₂(110)
- *DOI: 10.1063/1.2408420* — （AIMD 相关）
- *J. Am. Chem. Soc. 138(33): 10467-10476* — RDF 推键断裂/成键能垒
- *Nature Materials 18, 697–701 (2019)* — 金属/水界面分子取向（电极电势）
- *Chem. Commun., 2017, 53, 2594-2597* — constant potential（SHE 4.44 V）
- *Chem. Mater. 2012, 24, 15-17* — Li₁₀GeP₂S₁₂ 锂离子迁移
- *Phys. Chem. Chem. Phys., 2014, 16, 21082-21097* — inverse spinel Fe 磁性
- 引用类：CP2K 文章（2014 + 新文）、Quickstep 模块、GTH 三人、OT 算法文章（字幕 P3109-3138 列了应引用的 4~5 篇 CP2K 文章）

---

## 25. 与字幕（3.txt）交叉对照

### 25.1 PDF 与字幕共同覆盖的主题
GLOBAL/FORCE_EVAL/DFT/QS/MGRID/XC/SCF（对角化+OT）/PRINT/KIND/CELL/COORD/输出/.out/结构优化/晶胞优化/K点/NEB/频率/AIMD/DFT+U/HSE06/D3/rvv10/BSSE/建模/后处理。**PDF 是结构化骨架，字幕是边讲边演示的口语展开，二者高度一致。**

### 25.2 仅字幕有、PDF 没有的实操补充（高价值）
1. **vim 插件安装逐条命令**（mkdir/wget/filetype.vim 实操）。
2. **`tests/` 目录 `grep` 查关键词**的具体演示（含 BSSE 例子）。
3. **CUTOFF 单位澄清**：1 Ry≈13.6 eV，CP2K CUTOFF 指多重网格最高级、与 VASP ENCUT 不可比（PDF 只说"不可比"，字幕给了数值理由）。
4. **OT vs 对角化取舍**（course_notes B3 已收，但字幕更细）：OT 适合半导体、对角化适合金属；OT 不能 K 点/只能用 Γ、DFT+U 仅 OT；AIMD 前须测试 MINIMIZER/LINESEARCH/PRECONDITIONER（CG vs DIIS、2PNT vs 3PNT、FULL_SINGLE_INVERSE vs FULL_ALL）。
5. **EPS_SCF 单位 hartree（1 a.u.=27.211 eV）**，与 VASP eV 区分。
6. **MAX_SCF 不收敛 CP2K 仍继续下一离子步**（与 Gaussian 不同，PDF P24 提过，字幕强调）。
7. **BSSE 图解 + 5 kcal/mol≈0.22 eV + SR 基组增 50%**（PDF 有公式与数字，字幕有图示讲解）。
8. **Q4 价电子数含义 + 基组/赝势必须统一**（字幕用 Si 3s²3p²=4 举例）。
9. **Cu(100)+水 完整建模 walkthrough**：DEMCAR `-s` 按 z 排序→固定最下两层 Cu（用 93~124 或 139~170 实例）→`LIST` 固定；AIMD 表面体系仍需固定底层。
10. **提交/杀任务实操**：`source` 环境、`mpirun`、`nohup ... &`、`ps -ef`、`qdel`、`top`+`k`；单机不方便建议用队列。
11. **xyz 默认无晶胞边界，三种加边界法**（MS / VMD pbc / PDB 输出）——PDF 也有，字幕演示更细。
12. **Al₂O₃ 上 H₂O 吸附能四态法**实操（不固定原子原因：Al 暴露面重构强，固定会致不合理电荷分布）。
13. **晶胞优化 KEEP_ANGLES/KEEP_SYMMETRY 看情况开**；`CONSTRAINT Z` 保二维材料真空层；OT 不能 K 点只能扩胞、对角化可加 K 点。
14. **（字幕重要坑）CP2K K 点不支持对称性缩减不可约 K 点数**（与 VASP 不同），计算量不因此减少。
15. **CP2K 应引用文章清单**（2014 老文 + 新文 + Quickstep + GTH + OT，共 4~5 篇）。
16. **dftd3.dat 须复制到当前目录**才能用 DFT-D3（字幕末尾提醒）。
17. **RELAX_MULTIPLICITY 不好用且禁用 OT** 等算法（字幕）。

### 25.3 仅 PDF 有、字幕未展开（偏公式/表格）
- 完整 SCF 收敛表示例、能量换算 -31.2978853×27.211=-851.659 eV。
- Hessian / 质量权重力常数矩阵 / ZPVE 公式。
- 扩散系数数据表（600~1400 K）+ Arrhenius 推导（Ea=0.2141 eV）。
- HSE06 完整公式与输入、SCAN+rvv10 输入。
- CI-NEB 完整输入 + 关键词表 + `xyz2neb.pl` 工作流。
- 频率 `cp2kfreq.pl`/`cp2kfreq2mov.pl` 工作流、FULLY_PERIODIC 去平动转动。
- constant potential 定量换算（4.44 V、2.40/-2.04、3.81/-0.63）。
- inverse spinel Fe 磁性结构 + `&BS` 老办法。
- 全部文献 doi/出处。

---

## 26. 与 course_notes.md 的缺口标注（本 PDF 新内容）

`course_notes.md` 目前覆盖：后处理（RDF/MSD/频率/电子结构/FES）、参数经验（DFT+U、BSSE、OT vs 对角化、抽帧）、建模（include/DEMCAR）、实例索引、错字表。

**本 PDF（第3天）显著补充、course_notes 尚未系统收录的内容（标记【新】于上）：**
1. 输入文件 section 结构、vim 插件、`@SET`/`@INCLUDE` 变量机制（§2）
2. GLOBAL 全部 RUN_TYPE 枚举（BAND=PINT 等，§3）
3. FORCE_EVAL METHOD 枚举 + STRESS_TENSOR（§4）
4. DFT 下全套关键词表（UKS/ROKS/MULTIPLICITY/CHARGE/SURFACE_DIPOLE 等，§5）
5. QS EPS_DEFAULT / ASPC 外推（含"不能配 K 点"限制，§6）
6. MGRID NGRIDS/CUTOFF/REL_CUTOFF + 元素相关 CUTOFF（§7）
7. XC 完整：PBE/LIBXC、D3、SCAN+rvv10（§8）
8. HSE06 杂化泛函公式与输入（§8）
9. SCF 全参数：SCF_GUESS/EPS_SCF/MAX_SCF/DIAGONALIZATION/SMEAR/MIXING/OT+OUTER_SCF（§9）
10. PRINT 通用（FORCES/RESTART，§10）
11. KIND/CELL/COORD/TOPOLOGY 细节 + 基组劈裂含义 + 赝势（§11）
12. 输出文件与 .out 收敛表解读（§12）
13. 结构优化 4 收敛标准 + OPTIMIZER 三选一 + CONSTRAINT（§13）
14. 晶胞优化完整输入 + KEEP/CONSTRAINT Z（§14）
15. K 点（含"不支持对称缩减"坑）（§15）
16. CI-NEB 完整输入 + 关键词表 + xyz2neb.pl 流程（§16）
17. 频率计算 Hessian/ZPVE 公式 + 完整输入 + cp2kfreq 脚本（§17）
18. AIMD 完整输入参数表 + 质量加速 trick + restart（§18）
19. AIMD 后处理：MSD/扩散系数数据表/Arrhenius/constant potential 定量（§19）
20. DFT+U ramping 机制 + 磁性初猜 + &BS 老办法（§20）
21. 官方 exercises 链接（§21）
22. 建模：Amorphous Cell 加水、Al₂O₃ 吸附能四态法、三种加晶胞法（§22）
23. 工具脚本清单 + 文献索引（§23-24）

**建议 skill 后续动作**：
- 把 §3–§20 的参数细节内化进 `decide.md`（目前 decide.md 未见如此完整的 GLOBAL/SCF/QS/MGRID/NEB/频率/AIMD 输入模板）。
- 把 §19 constant potential 定量换算、§16 NEB 工作流补进 `workflow.md`/`gen_inp.py`（NEB/CI-NEB 开关）。
- 把 §8 HSE06、§20 DFT+U ramping 补进 `gen_inp.py` 开关（目前 gen_inp.py 已有 --type metadyn 等，未见 HSE06/DFT+U ramping 显式开关）。

---

## 27. PDF 页码覆盖清单（确认全部 156 页已处理）

| 页 | 主题 | 页 | 主题 |
|---|---|---|---|
| 1-2 | 版权声明 / 标题 | 79-81 | 过渡态定义（一阶鞍点） |
| 3 | CP2K 计算流程（图） | 82 | 无过渡态的过程 |
| 4 | 手册/tests 查找 | 83 | 过渡态方法分类（DIMER/CI-NEB） |
| 5-6 | 输入文件格式/ vim 插件 | 84-88 | NEB/CI-NEB 原理（nudge/MEP） |
| 7 | Si 单点例子（FORCE_EVAL/SUBSYS） | 89-90 | CI-NEB 优势（少点定位） |
| 8-9 | DFT/SCF 参数例子 | 91 | xyz2neb.pl 插点工作流 |
| 10 | 提交第一个任务 | 92-93 | CI-NEB 输入 + 关键词表 |
| 11 | 输入文件（标题） | 94-96 | 跟踪收敛 / 能量画图 |
| 12 | 思维导图(1) | 97 | 频率计算（标题） |
| 13 | GLOBAL section | 98-101 | Hessian / 力常数 / 振动模式 |
| 14 | FORCE_EVAL section | 102-103 | 驻点验证 / ZPVE |
| 15-16 | DFT（文件/UKS/CHARGE/+U 等） | 104-108 | 有限位移法 / 频率输入 / cp2kfreq |
| 17-18 | QS（EPS_DEFAULT/ASPC） | 109 | CP2K AIMD（标题） |
| 19-21 | MGRID（CUTOFF/元素表） | 110-113 | AIMD NVT 输入 / 注意事项 / .ener |
| 22 | （空白图） | 114-117 | （空白）/ DOI |
| 23 | XC（PBE/LIBXC） | 118 | Au₂₀/TiO₂ AIMD 练习 |
| 24 | SCF 通用 | 119-120 | Au 质量加速 / 后处理(能量) |
| 25-26 | 对角化原理 / 收敛判据 | 121-125 | 轨迹movie / RDF / 质心 / MSD |
| 27 | 对角化 SCF 模板（SMEAR） | 126-127 | 金属/水界面取向（Nature Mater） |
| 28 | 温度对 Fermi-Dirac 影响 | 128-130 | 建模/Au/H₂O+Na 异质结 |
| 29-30 | OT 原理 / 对角化 vs OT 对比表 | 131-132 | zdistr.py / Cu-O RDF |
| 31 | （空白） | 133-134 | constant potential（SHE 4.44 V） |
| 32 | OT 方法输入 | 135-136 | Li₁₀GeP₂S₁₂ 迁移 / 退火 |
| 33 | PRINT（FORCES/RESTART） | 137-140 | MSD / RMSD 平均 |
| 34 | 基组赝势坐标（标题） | 141-143 | 扩散系数 / Arrhenius（Ea=0.2141） |
| 35-36 | KIND（自定义名/ELEMENT） | 144 | VMD 多帧同显 |
| 37 | @SET 变量 | 145 | CP2K 教程链接 |
| 38-39 | 基组查询 / 劈裂含义 | 146-147 | DFT-D3 / SCAN+rvv10 |
| 40-42 | BSSE / MOLOPT-SR | 148-149 | DFT+U / ramping 收敛 |
| 43-44 | 价电子数 q / 赝势 | 150-151 | 磁矩初猜 / inverse spinel |
| 45-46 | CELL / COORD | 152-153 | Fe 磁性结构 / 自旋布局 |
| 47-49 | 坐标读入（include/TOPOLOGY/PBC） | 154 | &BS 老办法 |
| 50 | 提交小结（单机/队列） | 155 | HSE06 杂化泛函 |
| 51 | 文献 JCP 152,194103 | 156 | 版权声明 |
| 52-53 | （空白）/ 输出文件（标题） | | |
| 54-57 | 输出文件 / .out 解读 | | |
| 58 | 结构优化（标题） | | |
| 59 | 思维导图(2) | | |
| 60-62 | GEO_OPT（4 收敛标准/跟踪） | | |
| 63-68 | 练习一 Cu(100)+水 建模/优化 | | |
| 69 | 轨迹 PDB 输出 | | |
| 70-72 | 练习二 Al₂O₃ 吸附能 / 加晶胞 | | |
| 73 | 课后 Au₂₀/TiO₂ 优化 | | |
| 74-78 | 晶胞优化 / K 点 | | |

**结论：156 页全部逐页读取并处理，无遗漏。** 其中 22、31、52、114、115、116、117、129、154 附近为空白页/纯图页（仅标题或图，无文字知识点），已在清单标注；其余每页知识点均提取入对应主题章节。

---

*本文件由第3天 PDF（L3.txt）+ 字幕（3.txt）+ 已有笔记交叉对照生成，覆盖全部 156 页。公式与表格均原文照抄，【新】标记 course_notes.md 未收录内容。*
