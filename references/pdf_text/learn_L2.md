# 庚子计算《AIMD 与 CP2K》第 2 天 — 全面学习笔记 (learn_L2.md)

> 来源文件：
> - PDF 文本：`references/pdf_text/L2.txt`（即 `庚子计算-AIMD与CP2K讲义-2 - 副本.pdf`，**共 69 页**）
> - 视频字幕：`D:\石大\化学软件\cp2k\cp2k课程资料_庚子计算 - 副本\讲义和课程视频字幕\2.txt`（**4546 行**）
> - 已读笔记：`course_notes.md`、`course_survey.md`
> 整理时间：2026-07-19

---

## ⚠️ 重要说明：文件内容 vs 主题预期（务必先读）

用户任务描述中预期「第 2 天 = AIMD 后处理（轨迹查看、势能涨落、键长键角、RDF、VACF、IR、MSD、扩散系数）」。实际核对后：

- **PDF（`L2.txt`，第 2 份讲义）的内容是 CP2K 编译 + CP2K 简介/优缺点 + 建模（表面/异质结/Packmol）**，即 P3–P69，并**不含** RDF/VACF/IR/MSD 的讲解。
- **后处理（RDF/VACF/IR/MSD/扩散系数 + 相应的公式与实操）全部在视频字幕 `2.txt` 里**，是讲师口头讲出来的（配合 VMD/VASPKIT/Origin 演示）。
- 因此本笔记按主题组织，**同时收录 PDF 内容与字幕内容**，使「第 2 天」资料无遗漏。公式主要来自字幕（PDF 未写公式，PDF 偏编译/建模步骤），已用「★公式★」标注。

---

# 主题一：AIMD 后处理（来自字幕 2.txt，PDF 未含）

这是用户最关心的部分。讲师用「水盒子」例子（CP2K 与 VASP 各跑一遍，见第 1 天）演示全部后处理。

## 1.1 轨迹可视化（VMD 导入 + 周期性边界条件）

- 无论 CP2K 的 `position` 还是 VASP 的 `XDATCAR`，都能导入 VMD。
- **必须加周期性边界条件（PBC）**：`pbc set <box>` → `pbc wrap -all`。不加 PBC 会导致相邻镜像原子不算进来，RDF/MSD 失真。
- 显示方法：`VDW`（球）显示原子 + `DynamicBonds`（按距离显示化学键），画图好看。
- 演示踩坑：跟踪跨越盒子边界的原子键长会"跳变"，应选盒子中间、**不穿越边界**的分子来跟踪；或临时关掉 PBC 跟踪。

## 1.2 键长 / 键角 / 二面角跟踪

- 工具：`Mouse → Label → Bonds`（选两原子）或 `Angle`（选三原子），再到 `Graphics → Labels` 选中，用 `Graph` 画随时间变化。
- 示例：水分子 O–H 键长一直在 **~1 Å**（约 EI≈1 Å）附近波动；H–O–H 键角约 **105°** 波动。
- 保存：从 `Files` 保存成文本文件 → 导入 **Origin** 重画。
- **应用案例（化学键跟踪看反应）**：配合物活化 N₂ 分子（解离吸附 vs 缔合机制 associated mechanism）。跟踪 N–N、N–H、O–H 键长，观察质子链传递。纵轴键长、横轴时间，可看到约 **800 fs** 处化学反应发生：旧键断裂、新键（~1 Å 的 O–H）生成。类似地用于 NH₃/亚硫酸根体系的质子链传递。
- 说明：键长/键角/二面角跟踪是 AIMD 最直观、最常见的分析之一。也可自编程或用 `mdtraj`/`MDAnalysis` 等后处理程序。

## 1.3 能量涨落（势能 / 温度稳定性）

- VASP：`grep "E" OUTCAR` 提取总能/势能/动能/热浴能量；重定向 `> energy.txt` 保存，再导入 Origin 画温度、总能、势能曲线。
- 此部分第 1 天已讲（看模拟是否稳定），第 2 天复习。

## 1.4 RDF（径向分布函数 / 对关联函数 g(r)）

### ★公式★
- **定义**：以某参考粒子（一个原子 / 一种元素 / 一组原子）为中心，计算距其 r 处的局部数密度，除以体系**体相数密度 ρ**（bulk density），且在**无穷远处 g(r)→1**：
  ```
  g(r) = (距参考粒子 r 处的局部粒子数密度) / (体系体相数密度 ρ)
  ```
  无穷远处趋于 1，方便看图。
- **配位数（球面积分，关键！）**：
  ```
  N(r) = ∫₀^r 4π r'² · g(r') · ρ dr'
  ```
  ⚠️ **是球面积分（引入 4πr²），不是平面积分**。讲师反复强调：在 Origin 里直接对 g(r) 做"面积分"数值**不对**，必须引入 4πr² 做球面积分。第一峰积分面积 = 第一配位数，第二峰 = 第二配位层。

### 物理意义与判读
- 第一峰顶点横坐标 ≈ **第一配位层距离**；第二峰 ≈ 第二配位层；第三峰……。
- **水分子的判读实例**（以 O 为中心）：
  - 第一峰（又高又尖）≈ **1.1 Å** → 对应 O–H 键（第一配位层 = 2 个 H 原子）。
  - 第二峰 → 对应**氢键**（弱相互作用）；积分值 ≈ **3.97 ≈ 4** → 第二配位层约 4 个 H。
  - 一个氧周围共约 4 个 H（2 个来自自身分子 O–H，2 个来自相邻水分子的氢键）。
  - 共约 3 个明显配位峰；第四、五层峰很弱，说明影响很弱。
- **应用实例（Au20/TiO₂ 单原子催化，第 4 天细讲）**：
  - 完美 TiO₂（无缺陷）：Au–Ti RDF 几乎看不到第一/第二配位峰 → Au20 与载体作用极弱，金字塔结构不被破坏。
  - 引入氧空位（TiO₂₋ₓ）或额外杂原子 → Au–Ti 第一配位峰出现在**不到 3 Å** 处 → 明显 Au–Ti 键生成，团簇–载体强相互作用。
  - CO 吸附在 Au20 上：跟踪 Au–C 与 Au–Au 的 RDF。**Au–C 第一、二配位层之间概率密度=0 → Au–C 键在模拟中不断裂（稳定）**；而 Au–Au 第一、二峰之间仍有密度 → Au–Au 键像液体一样可断可生。
  - **酸性溶液（H₃O⁺）判据**：第一、二配位层之间出现概率密度 → 说明氢原子在配位层间交换（水分子间交换 H）。中性水第一、二峰之间为 0 → 无 H 交换。
  - 反应机理补充：CO 氧化反应在界面发生，是 **Au 原子拉着 CO 分子作为 "AuCO" 物种一起跑到界面**反应（而非 CO 自己迁移），反应后 Au 回到团簇。这颠覆了传统催化认为"CO 自己迁移到界面"的观点。

### 操作（VMD）
- `Extensions → Analysis → Radial Pair Distribution Function (g(r))`。
- 一定先加 PBC（见 1.1）；也可在 `Utilities → Unit Cell → Wrap` 加。
- 选 `selection`：用 `name` 或 `element`（如选 O 和 H）。
- 把横坐标 **bin 间隔取密一点** → 图更精细。
- 勾选 `integral` → 同时输出积分值（即配位数平台值）。
- 导出 `export` 成文本 → Origin 画图。
- ⚠️ **晶胞要求**：最好用**正交晶胞**；非正交（如石墨烯、MoS₂ 等六方，夹角≠90°）在 VMD 里**无法加 PBC 算 RDF**。技巧：建模时用晶格矢量旋转把六方转成正交（见主题三 3.2）。

## 1.5 VACF（速度自相关函数）与 vDOS、IR

### ★公式★
- **VACF 定义**：
  ```
  C_vv(t) = ⟨ v(0) · v(t) ⟩ / ⟨ v(0)·v(0) ⟩
  ```
  归一化到 t=0 时 = 1（最大相关性）；相关性随 t 降低，最终趋于 0。
  - t 时刻速度与 0 时刻速度点积越大 → 越平行（正相关）；越负 → 越相反。
- **vDOS（振动态密度）** = 对 VACF 做傅里叶变换：
  ```
  vDOS(ω) = ∫ C_vv(t) · e^{-iωt} dt
  ```
  再把横坐标转成**波数（cm⁻¹）**，即可对应实验 **IR / Raman 光谱**。
- ⚠️ **vDOS ≠ 真实 IR 光谱**：vDOS 未考虑偶极矩信息。真实 IR 需把**偶极矩 μ(t) 与速度一起**做变换：
  ```
  IR(ω) ∝ | ∫ μ(t) · e^{-iωt} dt |²
  ```
  CP2K 可提取偶极信息 + 速度信息一起算，得到真实红外光谱数值；VASPKIT 算的是 vDOS（不含偶极）。

### 物理意义与判读
- 振动强烈体系（如水，O–H 振动强）：VACF 趋于 0 时**强烈振荡**。
- 振动弱体系（如硅晶体熔化）：VACF 以**缓慢方式**趋于 0。
- 无论何种体系，无穷远处 VACF→0。

### 操作（VASPKIT，最新版）
- **727 功能** = VACF（速度/加速度自相关）。选原子（全部 / 某分子 / 某官能团 / 元素）。
  - 读 `XDATCAR`，问 `skip` 前面多少帧（预平衡）→ 输入 **1000**（即前 1000 帧当预平衡，从 1001 帧起算）。
  - `参考点间隔 = 1`（以轨迹上**每一帧**为参考，FFT 加速，准确）。
- **728 功能** = vDOS。同样选元素（H、O）、skip 1000、间隔 1。横坐标选**波数**单位，范围 0–4000 cm⁻¹。
- 下载 `.dat` 导入 Origin 画图。
- 也可选部分原子（如单原子催化剂上吸附的 CO）→ 只看该分子的 vDOS（避免整体峰太乱）。
- **CO 吸附实例**：吸附 CO 越多，振动峰**红移**（波数变化），实验 IR 可对应观察。
- **核量子效应实例**（Nature Physics，超离子态 He+H₂O 高压）：对比 H 核 vs D 核，vDOS 范围明显不同；并考察 0 K / 200 K / 2400 K。
- 对比静态频率计算（如 Gaussian）：只能得单值 + 人为高斯展宽；AIMD+VACF→vDOS 的峰展宽更真实（~1500–1600 cm⁻¹ 处的剪式振动又瘦又高；3000–3800 cm⁻¹ 处又大又宽是对称/反对称伸缩振动）。水还能给出 <1000 cm⁻¹ 指纹区（氢键等弱相互作用），静态单分子频率计算难以还原。

## 1.6 MSD（均方位移）与扩散系数 D（Einstein 公式）

### ★公式★
- **MSD 定义**：
  ```
  MSD(t) = (1/N) Σ_i | r_i(t) − r_i(0) |²
  ```
  N 为粒子数，r_i(0) 与 r_i(t) 为参考时刻与 t 时刻位置。
- **RMSD（均方根位移）** = √MSD。⚠️ **VMD 直接输出的是 RMSD（带根号），不是 MSD**。
- **Einstein 扩散公式**：
  ```
  D = lim_{t→∞} MSD(t) / (2 · d · t)
  ```
  d = 维度。长时区线性拟合 MSD–t 得**斜率 slope**，则：
  - **3D（体相/体积迁移）**：`D = slope / 6`
  - **2D（如双层石墨烯夹层内离子迁移）**：`D = slope / 4`

### 单位换算
- 计算值单位通常为 **Å²/ps**；实验常用 **cm²/s**。
- `1 Å²/ps = 1×10⁻¹⁶ cm² / 1×10⁻¹² s = 1×10⁻⁴ cm²/s`。
- 实操：slope（Origin 拟合，Å²/单位时间）→ 除以 6 → D(Å²/ps) → 换算 cm²/s。

### 操作（关键坑：先平方再平均）
- VASPKIT **722 功能** = average MSD（仅最新版有）。选 Li 元素（骨架 Li₁₀GeP₂S₁₂ 中 Li 迁移，其余为骨架不迁移），skip 1000、间隔 1 → 输出 `MSD.dat` → Origin 画图。可画总 MSD 与 X/Y/Z 方向分量。
- **VMD 操作**：`Extensions → Analysis → M2 MSD (Trajectory)…`，选元素（如 Li），**最好点 Align**（消除晶胞整体平动，只关注 Li 迁移）。起始参考帧（0 即第 0 帧）、skip（忽略前 N 帧当预平衡）、输入时间步长。
  - 时间步长来源：① VASP `POTIM`（如 =2 → 2 fs/步）；② `md_simplify.py` 抽帧（每 10–20 帧取一结构 → 每帧 = 20–40 fs）。
- ⚠️ **最重要坑（讲师当场更正）**：PPT 原写"**先平均再平方**"是错的，应为"**先平方，再平均**"。
  - VMD 输出 RMSD（带根号）。以多个参考帧（第 0/500/1000/1500/2000 帧）各算一条 RMSD 曲线 → 每条**先平方**得 MSD → 再**跨参考帧平均** → 得到平滑拟合曲线。单参考帧会很"刺"。
  - 讲师演示：在 Origin 用 `Set Column Value` 对 B/C/D/E/F 各列做平方，再求平均；再做 linear fitting 得 slope。
- **实例**（Li₁₀GeP₂S₁₂ 固态电解质，5 个温度 600/800/1000/1200/1400 K）：
  - 骨架（Ge/P/S）只在原位振动不迁移；Li（紫色）不断跳跃迁移 → 用 MSD 看扩散快慢 → 得扩散系数 D。
  - 超离子态实例（Nature Physics 高压 He+H₂O）：1600 K 时 He/H/O 全为平线（只振动不迁移）；2000 K 时 He 线"飞起"（有斜率，自由移动）；2300 K 时 H 也自由移动 → 超离子液体临界温度 2000–2300 K。拟合斜率得迁移率。

### VMD 多帧叠加（看迁移路径）
- `Graphics → Representation → Trajectory`：设 `start / stop / step`（如 1 / 2000 / 20）。
- 技巧：骨架（如 S）只显示第 1 帧（`Draw = off` 或单个 representation），Li 显示所有帧 → 直观看到 Li 迁移轨迹。可加 PBC。

## 1.7 迁移能垒（Arrhenius 拟合）

### ★公式★
- **Arrhenius**：`D = A · exp(−Ea / (k_B T))`
- 两边取 log：`ln D = ln A − Ea/(k_B T)`
- 以 `ln D` 为纵轴、`1/T` 为横轴拟合直线：
  - **斜率 = −Ea/k_B** → 求迁移能垒 Ea。
  - **截距 = ln A** → 指前因子 A。
- 对比：NEB 也能算扩散能垒，但**指前因子算极不准**；AIMD 是先得 D 再反推 Ea，更准确。

---

# 主题二：CP2K 简介、编译与优缺点（PDF L2 P3–P34 + 字幕）

## 2.1 CP2K 是什么 / 为什么快

- 量子化学 + 固态物理第一性原理软件包，可算固态/液态/分子/生物体系。
- 框架：混合高斯基组+平面波 **GPW / GAPW** 的 DFT；还支持 DFTB、LDA、GGA、杂化泛函、MP2、RPA、半经验（AM1/PM3/PM6/RM1/MNDO）、经典力场（AMBER/CHARMM）。
- 功能：MD、metadynamics、Monte Carlo、Ehrenfest dynamics、振动分析、core-level 光谱、能量最小化、NEB/dimer 过渡态。
- **最大优势：快**，尤其 **Quickstep（DFT 模块）**。原因：
  - 高斯+平面波混合基组（GPW/GAPW）比纯平面波快；
  - 代码新（2000 年由 Parrinello & Hutter 始创，开源，社区活跃）；
  - 千核并行、计算速度随体系**线性增长**；VASP 平面波 scaling 差、代码老。
  - 前沿"黑科技"算法：**OT（Orbital Transformation）、ASPC（Always Stable Predictor Corrector）、ADMM（Auxiliary Density Matrix Methods，算杂化泛函）、PIMD（Path-Integral MD）、adaptive buffered QM/MM**。
- 维基百科对比上百种程序，CP2K 最全面（支持周期/非周期、MD、半经验、HF、后HF、DFT、GPU）。但**最特长 = AIMD**。
- 速度前提：**原子数多（≥100–200）才显优势**；<100 原子时与 VASP 差不多甚至更慢。两三百原子是 VASP 极限，CP2K 轻松处理四五百乃至上千原子。

## 2.2 编译方法（PDF P4–P15 详细；字幕补充）

### 方法对比表（PDF P7）
| 方法 | 效率(相对) | 能否跨节点 | 方便程度 |
|---|---|---|---|
| 懒人法1：官网预编译 **ssmp** | 1.3–1.5 | 不能 | 方便 |
| 懒人法2：Ubuntu `apt-get install cp2k`（GNU+openmpi+OpenBLAS+ScaLAPACK） | 1.1（数学库稍慢） | 能 | 方便，可装插件 |
| 正常方法：源码编译（改 arch 模板） | 1 | 能 | 麻烦，手动装库/插件 |
| 最好方法：`/tools/toolchain` | 1 | 能 | 正常，自动装库/插件 |
| 懒人法3：静态库版本 | 1 | 能 | 方便（二进制跨机，需 intel mkl 同版本） |

### 预编译版（字幕重点推荐："保证编译成功"）
- 讲师提供已编译二进制：`cp2k-7.1`（CentOS 7.6 编译，glibc **2.17**，Intel 编译器 **2018.0.0**；2019/2020 编译器也行）。
- 使用：服务器 `source` 英特尔编译器 + 英特尔 MPI → `mpirun -n 56 cp2k.popt cp2k.inp 1>cp2k.out 2>cp2k.err`。
- Ubuntu 直接 `apt-get install cp2k`（18.04→5.1/6.1；20.04→6.1，够用）。
- 预编译 **ssmp**（OpenMP 节点内并行）：效率比 popt 慢 **30%–50%**，不建议正经计算。
- **popt**（MPI，跨节点）vs **psmp**（MPI+OpenMP 混编）：psmp 内存效率高（杂化泛函/HSE06 吃内存时有优势），但**通常比 popt 稍慢**；纯 GGA/PBE 吃内存少，用 popt 即可。

### toolchain 法（PDF P8–P15 详细步骤）
- **为什么用**：一键配置编译环境；自动装扩展库（ELPA、QUIP、PLUMED、PEXSI、libvdwxc、libxc、FFTW、CMAKE 等）；Intel MKL + OpenMPI 速度快（可换 OpenBLAS/ScaLAPACK，稍慢）。
- **第一步 下载**（P9）：
  ```
  git clone -b support/v7.1 https://github.com/cp2k/cp2k.git cp2k
  git submodule update --init --recursive
  ```
- **第二步 准备 GNU + Intel MKL**（P10–P12）：
  - GNU 必须 ≥5（7.3/7.5/8.3/9.3）；CentOS7 默认 gcc4.8.5 需升级：`yum install centos-release-scl` → `yum install devtoolset-9-gcc*` → `scl enable devtoolset-9 bash`。
  - Intel 只需 **MKL 库**（免费），不需编译器：`source /opt/intel/mkl/bin/mklvars.sh intel64` 或 `yum install -y intel-mkl`。
- **第三步 toolchain 装库**（P13）：
  ```
  cd tools/toolchain
  ./install_cp2k_toolchain.sh --with-openmpi=install --math-mode=mkl \
    --with-scalapack=no --with-ptscotch=install --with-parmetis=install \
    --with-metis=install --with-superlu=install --with-pexsi=install \
    --with-quip=install --with-plumed=install
  ```
  - 系统已有的库用 `--with-****=system`，没有的用 `=install`，不想装的用 `=no`。默认配置一般合理。
- **第四步 编译 + 测试**（P14–P15）：
  ```
  cp /opt/cp2k710/tools/toolchain/install/arch/* ../../arch/
  source /opt/cp2k710/tools/toolchain/install/setup
  cd ../..
  make -j 112 ARCH=local VERSION="popt psmp"
  make -j 112 ARCH=local VERSION="popt psmp" test
  ```
  - 测试 WRONG 多为精度问题（如参考 1e-13，我们得到 4.27e-10），只要在可接受范围即可；SCF 一般要求 1e-8。
  - 提交：`source .../setup; source mklvars.sh intel64; export PATH=$PATH:/opt/cp2k-7.1/exe/local; mpirun -n 56 cp2k.popt cp2k.inp 1>cp2k.out 2>cp2k.err`

## 2.3 版本建议
- 最近稳定版 **7.1**；master **8.0 暂不建议**（bug 多）。7.1 新增：XTB（半经验，可算几千~上万原子 AIMD）、移植 Quantum ESPRESSO（纯平面波，但讲师建议纯平面波还是回 VASP/QE）。

## 2.4 优缺点（PDF P32–P33 + 字幕更细）

**优点**：计算速度快；免费开源；功能全面且更新快；AIMD 相关功能极强；适合大体系（>200 原子）大规模并行。

**缺点**（讲师强调必须熟记，扬长避短）：
1. **导体计算慢**：OT 算法对带隙体系收敛快，但原理上不适用于导体 → 导体需用较慢的对角化方法。
2. **磁性体系麻烦**：需提前指定**自旋多重度**（像 Gaussian），不能像 VASP 自动寻找磁矩。
3. **K 点功能不完善**：仅 Gamma 点好用（7.1 甚至不能做 K 点对称性约化）。→ 建模时晶胞边长**至少 ≥10 Å** 才能用单 Gamma 点；太小（如 5 Å）则结果不准确 → 可扩成 2×2/3×3 大晶胞弥补。
4. **高斯基组带来 BSSE（基组叠加误差）**：高估结合能/吸附能（多数情况比 VASP 算的大一点）；基组越小 BSSE 越大。平面波（VASP）无此误差。

**程序互补**（字幕 P34/结尾）：CP2K 擅 AIMD（动态信息），VASP/Gaussian/ORCA/ADF 擅精确静态（吸附能、反应能、过渡态、片段分析）。例：JACS 2017 139(17) 6190-6199（AIMD 用 CP2K，静态用 VASP，SI 片段分析用 ADF）。

## 2.5 CP2K 经典文章（PDF P22–P30，作 AIMD 应用示例）
- 第二代 CPMD 模拟 Sc/Sb/Te 结晶（Phys. Rev. Lett. 98, 066401；Science 358, 1423–1427 (2017)）。
- 动态单原子催化 DSAC：Au₂₀/CeO₂₋ₓ，CO 吸附在界面生成 Au(I)CO（Wang Y.-G. et al. Nat. Commun. 2015, 6, 6511）。
- 水促 O₂ 活化生成 OOH：473 K，Δt=0.5 fs，Au/α-Al₂O₃(0001) + 20 H₂O，5–8 ps（ACS Catal. 2016, 6(4), 2525-2535）。
- adaptive buffered QM/MM 模拟 Criegee 反应（J. Am. Chem. Soc. 2016, 138(35), 11164-9）。
- 分子晶体五唑盐（pentazolate）加氢/脱氢：123 K 脱氢、390 K 加氢（J. Am. Chem. Soc. 2019, 141, 2984−2989）。
- Metadynamics Al³⁺ 水合反应势能面（Nat. Commun. 2019, 10(1), 3139）；Metadynamics S₂/S₁ 反应势能面（J. Comput. Chem. 2015, 36(11), 785-94）。
- 固液界面 AIMD：Na⁺ 个数调电极电势，影响 H₂O 分子取向（Nature Materials 18, 697–701 (2019)）。
- 催化反应 Fe₃O₄ STM（ACS Catal. 2019, 9(9), 7876-7887）。

## 2.6 学习资源（PDF P31 + 字幕）
- 官网 cp2k.org：features / science / tools / 下载（GitHub，建议 7.1）。
- **手册（第一手资料）**：`http://manual.cp2k.org/trunk/`（树状 section/关键词，Ctrl+F 搜）。注意版本对应：用 7.1 就看 `manual.cp2k.org/7.1/`；默认 trunk=8.0，差别不大但最好版版对应。
- **Google Group**（国内需科学上网）：最全面论坛，开发者直接答疑，可注册收邮件。
- Zevan 博客（http://kenshin325.lofter.com/tag/cp2k）、兰一知乎专栏（https://zhuanlan.zhihu.com/cp2k-tutorial）。
- 强烈推荐：赵亚凡《CP2K 入门使用》材料（~2014/15，十几页，参数设置思路仍适用）。
- **VIM 插件 `cp2k.vim`**：input 文件彩色高亮（section 绿、关键词淡黄、参数红/黑、注释蓝/井号），写错关键词一眼可见（见字幕 P2800+ 演示）。
- 在线输入文件生成器：cp2k-www.epcc.ed.ac.uk（≤4.0）、CP2K_Editor（GitHub avishart，≤5.1）。
- CP2K 编译教程：http://bbs.keinsci.com/thread-19009-1-1.html ；B 站视频 BV1Y54y1e7Yx（GCC 编译法）。

---

# 主题三：建模（PDF L2 P35–P69 + 字幕详细演示）

## 3.0 体系分类框架（字幕临时加的 PPT）
8 类：固体、液体、气体；固-固界面、固-液界面、固-气界面、液-液界面、气-液界面。

## 3.1 表面 terminal 与悬挂键（PDF P37–P41）
- **练习 1**：α-Al₂O₃(0001) 构建。切表面 `Build → Surface → Cleave Surface`，四指数六方晶面在 MS 只输前 3 个指数（如 0 0 1）。调 `Top` 得不同暴露：O-terminated 或 Al-terminated。
- **Al-terminated**：上下对称（暴露不饱和 Al³⁺，需加悬挂基团）；或不对称（产生表面偶极，需加 `IDIPOL`/`LDIPOL` 消除）。
- ⚠️ 移动 Top 时**上下表面同时变**（Slab 有两面）。无法既满足化学计量比又上下都 O 暴露：O/Al=18/12=2/3 vs 21/12 不符计量比。
- **悬挂键饱和**：用 Sketch Atom 加 OH 饱和不饱和 Al；OH 是 −1 价，需额外加一个 H 平衡电荷（相当于引入一个解离的 H₂O 分子）。最符合常温大气下 α-Al₂O₃(0001) 实况。最后加真空层扩胞。
- **文献参考**：Hoffmann, Angew. Chem. Int. Ed. 2013, 52, 93-103（表面模型构建常见错误，自然界不存在的表面勿做催化计算）。

## 3.2 Wood 表面标记法 / 晶格矢量旋转（PDF P42–P49）

### ★公式★（Redefine Lattice 矩阵，P43）
```
[1 0 0]   [a]   [a]        [1 1 0]   [a]   [a+b]      [2 0 0]   [a]   [2a]
[0 1 0] · [b] = [b]   ;  [0 1 0] · [b] = [b]    ;  [0 1 0] · [b] = [b]
[0 0 1]   [c]   [c]        [0 0 1]   [c]   [c]        [0 0 1]   [c]   [c]
```

### Wood 标记（P42）
- FCC(100)-p(1×1)：p=primitive（默认）；c(2×2)：c=center（表面 cell 中心多一单元）。
- 重构矢量与未重构成 45° 夹角：`fcc(100)-(√2×√2)R45°`（2=边长，R=旋转，45°=角度）。

### 旋转晶格矢量（P44–P45）Au(111)-(√3×√3)R30°
- 用旧晶格 a,b 组合新晶格 A,B：
  ```
  A = a − b
  B = 2a + b
  ```
  矩阵：
  ```
  [ 1 -1  0] [a]   [a−b]
  [ 2  1  0] [b] = [2a+b]
  [ 0  0  1] [c]   [ c ]
  ```

### 魔角石墨烯（P46–P49）
- 扭转角由 (m,n) 决定。脚本 `magicAngle.py`（见 P49 源码）：
  ```
  C = π/3; c = a²+b²−2ab·cos(C); sinB = b·sin(C)/√c; angle = asin(sinB)·180/π
  ```
- 常用表（m n Angle）：
  | m | n | Angle(°) | | m | n | Angle(°) |
  |---|---|---|---|---|---|---|
  | 5 | 1 | 10.89339 | | 55 | 1 | 0.910375 |
  | 10 | 1 | 5.208719 | | 60 | 1 | 0.833884 |
  | 15 | 1 | 3.417981 | | 65 | 1 | 0.76925 |
  | 20 | 1 | 2.542924 | | 70 | 1 | 0.713914 |
  | 25 | 1 | 2.024447 | | 75 | 1 | 0.666005 |
  | 30 | 1 | 1.681537 | | 80 | 1 | 0.624121 |
  | 35 | 1 | 1.437947 | | 85 | 1 | 0.587194 |
  | 40 | 1 | 1.255991 | | 90 | 1 | 0.554392 |
  | 45 | 1 | 1.114906 | | 95 | 1 | 0.52506 |
  | 50 | 1 | 1.002314 | | 100 | 1 | 0.498677 |
  | 105 | 1 | 0.474818 | | | | |
- 建 (11,1) 扭转石墨烯：导入石墨→去对称→去一层→`Redefine Lattice`：
  ```
  [11  1  0]
  [-1 10  0]
  [ 0  0  1]
  ```
  再导入一层做 11×11×1 超胞（失配率 4.2%；10×10×1 则 5.1%），扩包后见摩尔纹。

## 3.3 异质结（PDF P50–P56；字幕 VASPKIT 804 演示）
- **练习 3**：g-C₃N₄/TiO₂ 界面（Phys. Chem. Chem. Phys. 2016, 18, 31175）。
  1. 导入 TiO₂ anatase CIF，切 (100) 表面厚 3 层，lattice U 方向显示 4 周期。
  2. `Build → Symmetry → Redefine Lattice` 按文献调表面晶格矢量。
  3. 导入 C₃N₄ CIF（Materials Project **mp-567885**），按文献显示 2×4 晶胞。
  4. 同理 Redefine Lattice 调 C₃N₄ 表面矢量。
  5. `Build → Build Layers`：Layer1=TiO₂(100)，Layer2=C₃N₄。mismatch：a 8.88%、b 4.21%、angle 4.60%（很大，但 2D 材料可塑性强，可变形匹配）。matching 选 layer1（或 Average）→ build → yes。
  6. 删最上层 C₃N₄，真空层 c 方向 +15 Å。可对 a,b 做**选择性优化**（水平方向弛豫）。
- **VASPKIT 804（最新 2.0 版才有）建异质结**：自动遍历两材料转换矩阵最小公倍数。输入 `mismatch tolerance`（一般 2–3% 合理；柔性材料如石墨烯/C₃N₄ 可放宽）；`interlayer space`（层间距，如 2.5 Å）；`vacuum`（两端真空，一般 15 Å）。mismatch 太小（如 0.5）只找到一个超大晶胞解；调大可找小晶胞。heterojunctions list 文件含转换矩阵、适配率、晶胞角度/边长。
- **MS 手建异质结核心思想**：晶格矢量旋转（乘转换矩阵）把六方（如 MoS₂，60°/120°）转成正交，再 `Build Layers` 摞起。例：MoS₂ 转正交：新大 A = 2a + b，B 不变（`Redefine Lattice` 输入 2,1,0 / 0,1,0）。再找黑磷（a=3.3, b=4.56）与 MoS₂（a=5.52, b=3.19）最小公倍数使 a,b 边长误差 <2%。

## 3.4 固-液界面（字幕重点；PDF P60–P64）
- **最常见 AIMD 体系**（电催化、电池、刻蚀、沉积）。
- **Cu(100) + 46 H₂O 实例**（PNAS 2017 114(8) 1795-1800，CO₂ 电还原）：
  1. 切 Cu(100) 表面，厚度 ~4 原子层，`Supercell` 扩 3×3（边长 **10.22 Å**，记下此数）。
  2. 用 Amorphous Cell 建水盒子（30/46 个 H₂O），晶胞 A、B 设成 **10.22 × 10.22**（必须与 Cu 表面一致才能摞）。
  3. `Build Layers` 摞起（mismatch≈0%）→ MS 自动在水/金属间留空隙。
  4. 若要保持 1 g/cm³ 水密度，可平移水稍近表面 + `Rebuild Crystal` 改 c 边长（如 13.3→19.35 改短）。
  5. 可再加吸附分子（如 CO）于界面。
- ⚠️ **AIMD 体积限制**：原子数少，**基本不能做 NPT 平衡盒子大小，只能 NVT 或 NVE**，须提前算好体积。建议初始密度就建准（1 g/cm³），省去预平衡。

## 3.5 溶剂化层建模：MS Amorphous Cell 与 Packmol

### MS Modules–Amorphous Cell（PDF P60–P64；字幕演示）
- 新建非周期文件 → 建一个 H₂O 分子 → `Modules → Amorphous Cell → Construction` → Add H₂O → 设数量（如 16）→ 温度（常温）→ 勾 periodic → **密度 1 g/cm³** → 指定 a,b 边长（水默认立方体 **7.82 Å**，改一个方向其余自动随密度变）→ Construct。
- 得到 `.xtd` → In-Cell 显示 → export 成 cif/car。
- 适用：给 slab 加溶剂（比手摆构型好）。

### Packmol（PDF P65–P68；字幕演示）
- 经典 MD 液相建模程序，比 Amorphous Cell **灵活**，但**不好做固体表面**。
- 下载 http://m3g.iqm.unicamp.br/packmol/ ；安装：`tar -zxvf packmol.tar.gz; cd packmol; ./configure; make` → 生成 `packmol` 可执行。
- **案例 1：水+尿素混合**（P66）：
  ```
  tolerance 2.0        # 分子间距 > 2 Å
  filetype pdb
  output mixture.pdb
  structure water.pdb
    number 1000
    inside box 0. 0. 0. 40. 40. 40.
  end structure
  structure urea.pdb
    number 400
    inside box 0. 0. 0. 40. 40. 40.
  end structure
  ```
  密度须自己算（分子质量/晶胞体积 ≈ 1 g/cm³）；建不好需先 NPT 跑盒子（麻烦），故初始密度要建准。
- **案例 2：水/氯仿界面 + 荷尔蒙**（P68）：
  ```
  tolerance 2.0
  filetype xyz
  output interface.xyz
  structure water.xyz
    number 1019
    inside box -20. 0. 0. 0. 39. 39.   # 负半边水
  end structure
  structure chlor.xyz
    number 199
    inside box 0. 0. 0. 21. 39. 39.    # 正半边氯仿
  end structure
  structure t3.xyz
    centerofmass
    fixed 0. 20. 20. 1.57 1.57 1.57    # 荷尔蒙质心固定+平移+旋转
  end structure
  ```
- 产出文件**不含晶胞边界**，需 `Build Crystal` 手动加边界（如 40 40 40）。
- 气体建模同理（控制压力/区域内分子数）。

## 3.6 团簇建模：Au20（字幕结尾；PDF P50 提及）
- 负载/真空团簇建模同理。例：Au20 负载于 TiO₂（金红石 rutile，最稳 110 表面，厚 3 层，表面原子设为 O）→ 加 15 Å 真空层 → `Supercell` 5×3（够放大团簇）→ 用 Pencil 工具一点点拉出 Au20（底 10 原子，复制 CTRL-C/V 往上摞成金字塔，共 20 原子）→ Shift+右键旋转整型 → 结构优化 → 跑 AIMD。
- 真正最稳定构型需全局极小值搜索；建模只给初始结构。
- 大纳米颗粒（如 400 原子）MS 手拉不现实，有专门建纳米颗粒程序（讲师未详述）。

## 3.7 数据库（字幕）
- **Materials Project**（materialsproject.org，需注册）：全为计算结果（能带、PDOS、弹性/压电、EOS、计算参数），可下载 primitive / conventional cell（CIF）。例：搜 Al₂O₃ → 加对称性 → space group C 2/m。
- **COD**（Crystal Open Database）：比 ICSD 更全（录入松）。
- **CCDC**：分子晶体/有机配合物。
- **ICSD**：部分学校未购买。
- 固体建模：数据库找结构 → 扩包/引缺陷。

## 3.8 画论文示意图（扩展，PDF P57–P59）
- MS / VESTA / VMD / Origin / Illustrator 配合。例：Fe₃ 团簇橙色、半径 0.8、背景白；超胞 5×5×1；`Display Options` 设 perspective、`Depth Cue Intensity` 调高；`Lighting` 勾第二高光；调视角截图。

---

# 主题四：与字幕交叉对照 + PDF 独有 vs 字幕独有

## 4.1 PDF 每个主要主题，字幕是否覆盖
| PDF 主题 | 字幕覆盖情况 |
|---|---|
| CP2K 编译（toolchain 详细步骤） | 字幕只讲"预编译二进制 + apt + 不推荐手编"，**未覆盖 toolchain 详细步骤**（PDF 独有） |
| CP2K 简介/快的原因/黑科技算法 | 字幕完全覆盖且更口语化，并补"原子数门槛""版本 7.1/8.0""XTB/QE 移植" |
| CP2K 优缺点（4 点） | 字幕完全覆盖，并补"导体 vs 半导体速度对比""K 点需≥10Å晶胞/扩包""BSSE 实例对比 VASP 吸附能" |
| 经典文章 | 字幕覆盖并加 DSAC 动态单原子机制、超离子态等解读 |
| 学习资源 | 字幕补 manual 版本对应、Google Group、vim 插件演示 |
| 表面 terminal/悬挂键 | 字幕用 Al₂O₃(0001) 实际演示，覆盖并深化 |
| Wood/晶格旋转/魔角 | 字幕在异质结部分简要提及"乘转换矩阵"，**未展开公式/魔角表**（PDF 独有） |
| 异质结 g-C₃N₄/TiO₂ | 字幕用 VASPKIT 804 另演示黑磷/MoS₂，覆盖思想但例子不同 |
| Amorphous Cell / Packmol | 字幕完整演示水盒子/水+尿素/水+氯仿，覆盖并补操作细节 |
| 团簇 Au20 | 字幕结尾演示铅笔工具建 Au20，覆盖 |

## 4.2 仅字幕有、PDF 没有的实操补充（高价值）
1. **VMD 加 PBC**：`pbc set` + `pbc wrap -all`（RDF/MSD 必须）。
2. **RDF 球面积分**：配位数 = ∫4πr²g(r)ρdr，**不能在 Origin 直接平面积分**；需正交晶胞才算 RDF PBC。
3. **MSD 先平方再平均**：VMD 输出 RMSD（带根号），以多参考帧（0/500/1000/1500/2000）各算→先平方→再平均；PPT 原"先平均再平方"被讲师当场更正。
4. **Einstein D**：3D `D=slope/6`，2D `D=slope/4`；Å²/ps→cm²/s（×1e-4）。
5. **Arrhenius 反推 Ea**：ln D vs 1/T，斜率=−Ea/k_B；NEB 指前因子不准。
6. **VACF/vDOS**：VASPKIT 727/728；vDOS≠IR（缺偶极）；CP2K 可提偶极得真实 IR。
7. **能量涨落**：VASP `grep "E" OUTCAR` → energy.txt → Origin。
8. **md_simplify.py** 每 10–20 步抽帧（时间步换算）。
9. **VASPKIT 722**（MSD）、**804**（异质结，2.0 版），需最新版。
10. **键长/键角跟踪**：VMD `Label → Bonds/Angle` + `Graphics → Labels → Graph`。
11. **固液界面体积限制**：AIMD 只能 NVT/NVE，初始密度建准（1 g/cm³），不能 NPT。
12. **晶胞边长记录**：异质结/固液界面两材料 A、B 边长须一致（如 Cu 10.22 Å）。

## 4.3 仅 PDF 有、字幕没有的（补充进知识库）
- toolchain 编译全步骤（gcc 升级、MKL、install_cp2k_toolchain.sh 各 flag、make test 精度容忍）。
- 编译方法对比表（5 种）。
- OT/ASPC/ADMM/PIMD 算法名罗列。
- Wood 标记法、Redefine Lattice 矩阵公式、Au(111)(√3×√3)R30° 旋转公式。
- 魔角石墨烯 + magicAngle.py 源码 + (m,n)→角度表。
- g-C₃N₄/TiO₂ mismatch 具体数值（a 8.88%/b 4.21%/angle 4.60%）。
- Packmol 两个完整输入脚本（水+尿素、水+氯仿+荷尔蒙）。

---

# 主题五：与 course_notes.md 的差异（未收录的新内容）

`course_notes.md` 已覆盖：RDF PBC+球面积分(A1)、MSD √MSD+平方再平均(A2)、频率→movie(A3)、ELF/PDOS/电荷差分(A4)、FES三法(A5)、DFT+U(B1)、BSSE(B2)、OTvs对角化(B3)、md_simplify(B4)、建模 include(C)、实例索引(D)。

**本次第 2 天字幕/PDF 中，course_notes.md 尚未收录或需强化的新内容：**
- 键长/键角/二面角 VMD `Label` 跟踪法 + 化学反应（N₂活化、质子链）判读。
- 能量涨落 `grep "E" OUTCAR` 提取 total/kinetic/potential/thermostat。
- VACF 完整定义 + vDOS=FFT(VACF) + **vDOS≠IR（缺偶极）** + VASPKIT 727/728 + 核量子效应/超离子态实例。
- MSD **Einstein 公式两种维度**（3D/6，2D/4）+ **单位换算 1 Å²/ps=1e-4 cm²/s** + **Arrhenius 反推 Ea**（lnD vs 1/T）。
- 水 RDF 判读数值：第一峰 ~1.1 Å（O-H，配位 2 H），第二峰~氢键（配位~4 H）；缺陷对 Au20/TiO₂ Au-Ti 峰的影响；酸性 H₃O⁺ 配位层间交换判据。
- CP2K 编译实战：预编译二进制（glibc 2.17/Intel 2018）、psmp vs popt（内存vs速度）、apt 安装版本。
- CP2K 版本 7.1/8.0、XTB、QE 移植。
- 学习资源：manual 版本对应、Google Group、cp2k.vim 插件。
- 建模 8 类框架、Materials Project/COD/CCDC 数据库、MS Amorphous Cell 水盒子（7.82 Å 立方, 密度 1）、Packmol 双脚本、VASPKIT 804 异质结、Au20 铅笔工具建团簇。
- **PDF 独有**（知识库可补充）：toolchain 编译全步骤、编译对比表、Wood/晶格旋转矩阵、魔角表、g-C₃N₄/TiO₂ mismatch 数值。

---

# 主题六：PDF 页码覆盖清单（确认每页已处理）

| 页 | 主题 | 处理 |
|---|---|---|
| P1 | 版权声明 | ✓ |
| P2 | CP2K 简介 封面（刘锦程） | ✓ |
| P3 | 程序对比图（速度/力场/尺度/黑科技/后HF/已灭绝/精度） | ✓ |
| P4 | CP2K 编译-预编译版下载（6.1 ssmp, GitHub, 教程链接） | ✓ |
| P5 | 预编译版上传即用 + OpenMP 脚本 + 效率 30–50%↓ | ✓ |
| P6 | 稳定版 7.1 / master 8.0；popt/psmp/ssmp | ✓ |
| P7 | 编译方法对比表（5 种） | ✓ |
| P8 | toolchain 为什么用（ELPA/QUIP/PLUMED/PEXSI 等） | ✓ |
| P9 | toolchain 第一步：下载（git clone v7.1） | ✓ |
| P10 | 第二步：GNU≥5 + Intel MKL | ✓ |
| P11 | 升级 gcc（centos7 devtoolset-9） | ✓ |
| P12 | 升级 Intel MKL（免费, source mklvars） | ✓ |
| P13 | 第三步：install_cp2k_toolchain.sh 各 flag | ✓ |
| P14 | 第四步：cp arch / source setup / make / test | ✓ |
| P15 | 测试精度容忍（1e-13 vs 1e-10，SCF 1e-8）+ 提交命令 | ✓ |
| P16 | CP2K 简介 分节封面 | ✓ |
| P17 | CP2K 功能总览（GPW/GAPW/DFTB/MP2/RPA/力场/MD…） | ✓ |
| P18 | 维基对比最全面；特长 AIMD | ✓ |
| P19 | 优势：快（Quickstep） | ✓ |
| P20 | 为什么快：高斯+平面波、Parrinello&Hutter、线性并行 | ✓ |
| P21 | 黑科技算法（OT/ASPC/ADMM/PIMD/QM-MM）+ science | ✓ |
| P22 | 经典文章：第二代 CPMD Sc/Sb/Te（PRL/Science） | ✓ |
| P23 | 经典文章：DSAC Au20/CeO2-x（Nat. Commun. 2015） | ✓ |
| P24 | 经典文章：水促 O2 活化（ACS Catal. 2016, dt=0.5fs） | ✓ |
| P25 | 经典文章：adaptive QM/MM Criegee（JACS 2016） | ✓ |
| P26 | 分子晶体五唑盐 123K/390K（JACS 2019） | ✓ |
| P27 | Metadynamics Al3+ 水合（Nat. Commun. 2019） | ✓ |
| P28 | Metadynamics S2/S1（J. Comput. Chem. 2015） | ✓ |
| P29 | 固液界面 Na+ 调电势（Nature Materials 2019） | ✓ |
| P30 | 催化 Fe3O4 STM（ACS Catal. 2019） | ✓ |
| P31 | 入门学习资源（tutorials/manual/group/博客/编辑器） | ✓ |
| P32 | 优点总结（快/开源/全面/AIMD强/大体系） | ✓ |
| P33 | 缺点（导体慢/磁性/ K点/ BSSE） | ✓ |
| P34 | 程序互补（CP2K+VASP+JDFTx+Gaussian/ORCA/ADF） | ✓ |
| P35 | 建模 分节封面（刘锦程） | ✓ |
| P36 | 复杂建模八项清单 | ✓ |
| P37 | 表面 terminal：α-Al2O3(0001) cleave, O/Al-terminated | ✓ |
| P38 | Al/O-terminated 对称/不对称、表面偶极 IDIPOL | ✓ |
| P39 | Top 同时变上下表面；计量比约束 | ✓ |
| P40 | 悬挂键 OH 饱和 + 加 H 平衡电荷 + 真空层 | ✓ |
| P41 | 文献参考 Hoffmann 2013 | ✓ |
| P42 | Wood 标记法（p(1×1)/c(2×2)/(√2×√2)R45°） | ✓ |
| P43 | Redefine Lattice 矩阵公式 | ✓ |
| P44 | 旋转晶格 Au(111)(√3×√3)R30°：A=a−b,B=2a+b | ✓ |
| P45 | 旋转矩阵 [1 -1 0;2 1 0;0 0 1] | ✓ |
| P46 | 魔角石墨烯补充 (-1,19)/(20,1) | ✓ |
| P47 | 建(11,1)扭转石墨烯 redefine lattice | ✓ |
| P48 | 11×11×1 超胞，失配率 4.2%/5.1% | ✓ |
| P49 | magicAngle.py 源码 + (m,n)→角度表 | ✓ |
| P50 | 练习3 g-C3N4/TiO2（PCCP 2016） | ✓ |
| P51 | (1) TiO2 anatase 切(100) 厚3层 | ✓ |
| P52 | (2) redefine lattice 调表面矢量 | ✓ |
| P53 | (3) C3N4 CIF（mp-567885）2×4 | ✓ |
| P54 | (4) C3N4 redefine lattice | ✓ |
| P55 | (5) Build Layers 异质结；mismatch a8.88%/b4.21%/ang4.60% | ✓ |
| P56 | (6) 删 C3N4 层 + 真空 +15Å；a,b 选择性优化 | ✓ |
| P57 | 案例4 画示意图（MS/VESTA/VMD/Origin，Fe3 橙） | ✓ |
| P58 | 超胞 5×5×1；perspective/depth cue/第二高光 | ✓ |
| P59 | 调视角截图 | ✓ |
| P60 | 练习 Cu/H2O 界面（Amorphous Cell + Build Layers） | ✓ |
| P61 | Cu(100)+46H2O；PNAS 2017；手动/Amorphous/Packmol | ✓ |
| P62 | Amorphous Cell：建 H2O, density 1, a,b=10.2425 | ✓ |
| P63 | 运行得 Molecule.xtd；In-Cell；Build layers | ✓ |
| P64 | 调水/Slab 距离；近表面密度≠1；AIMD 只能 NVT/NVE | ✓ |
| P65 | Packmol 介绍/下载/安装（j comput chem 30 2157 2009） | ✓ |
| P66 | Packmol 案例：水+尿素（tolerance 2.0, box 40³） | ✓ |
| P67 | （空页） | ✓ |
| P68 | Packmol 案例：水/氯仿界面 + 荷尔蒙（centerofmass fixed） | ✓ |
| P69 | 版权声明 | ✓ |

**共 69 页，全部覆盖（无漏页）。字幕 2.txt（4546 行）已全文读取并提取。**

---

# 附：关键公式速查

```
RDF:        g(r) = 局部密度(r) / 体相密度 ρ        （∞处→1）
配位数:     N(r) = ∫₀ʳ 4π r'² g(r') ρ dr'          （球面积分！）
VACF:       C_vv(t) = ⟨v(0)·v(t)⟩ / ⟨v(0)·v(0)⟩     （t=0 归一为1）
vDOS:       vDOS(ω) = ∫ C_vv(t) e^{-iωt} dt         （FT→波数对应IR/Raman）
IR:         IR(ω) ∝ |∫ μ(t) e^{-iωt} dt|²          （需偶极，vDOS≠IR）
MSD:        MSD(t) = (1/N) Σ |r_i(t)−r_i(0)|²       （VMD 输出其根号=RMSD）
Einstein:   D = slope / (2 d t)  →  3D: /6, 2D: /4
单位:       1 Å²/ps = 1×10⁻⁴ cm²/s
Arrhenius:  ln D = ln A − Ea/(k_B T)               （斜率=−Ea/k_B）
```
