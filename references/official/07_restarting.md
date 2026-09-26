# 07 · 重启与续算（Restarting CP2K Calculations）

> **来源**：<https://manual.cp2k.org/trunk/methods/restarting.html>
> **抓取日期**：2026-09-08
> **官方原文范围**：Basic / K-Points / Harris Chain / Band and NEB Calculations / Molecular Dynamics / CDFT / References
> **本文件定位**：G 层（官方权威层）。只写官方说了什么，不写经验性做法。经验性续算策略见 F 层 `playbook.md`。

---

## 0. 官方对"重启"的定位

官方原文开头：

> This guide explains how to restart CP2K calculations from previously saved wavefunction files. Restarting is useful for continuing calculations that were interrupted, extending molecular dynamics simulations, or using converged wavefunctions as starting points for new calculations.

即官方把重启的用途分成三类：

| 用途 | 官方原文表述 | 典型场景 |
|---|---|---|
| 续算被中断的计算 | continuing calculations that were interrupted | 作业被墙钟时间杀掉 |
| 延长 MD | extending molecular dynamics simulations | 生产 MD 分段跑 |
| 用收敛波函数作新计算的起点 | using converged wavefunctions as starting points for new calculations | 换方法/换泛函时复用密度 |

**关键前提**：重启必须有**先前保存的波函数文件**（通常 `.wfn` 扩展名）。**没有波函数文件就不是"重启"，只能重新算。**

---

## 1. 基本重启（Basic）

### 1.1 最小重启输入

官方给出的最小示例：

```
&DFT
  WFN_RESTART_FILE_NAME your_restart_file.wfn
  &SCF
    SCF_GUESS RESTART
  &END SCF
&END DFT
```

两个关键字的官方职责划分：

| 关键字 | 位置 | 官方描述 |
|---|---|---|
| `WFN_RESTART_FILE_NAME` | `&DFT` | points to the wavefunction file（**指向波函数文件**） |
| `SCF_GUESS RESTART` | `&DFT/&SCF` | instructs CP2K to use it as the initial guess（**指示 CP2K 用它作为初始猜测**） |

> **注意**：两者必须同时出现。只写 `SCF_GUESS RESTART` 而不给文件名，CP2K 会去找默认命名的重启文件；只给文件名而不写 `SCF_GUESS RESTART`，文件不会被用作初猜。

### 1.2 如何产生重启文件

官方给出的 `&PRINT/&RESTART` 配置：

```
  &PRINT
    &RESTART
      FILENAME ./your_project_name
      BACKUP_COPIES 3
      COMMON_ITERATION_LEVELS 1
      &EACH
        JUST_ENERGY 1  ! Write at end of each SCF (produces your_project_name-RESTART.wfn)
        QS_SCF 0
      &END EACH
    &END RESTART
  &END PRINT
```

其中项目名由 `GLOBAL` 段设定：

```
&GLOBAL
  PROJECT your_project_name
&END GLOBAL
```

### 1.3 关键字语义（官方原文逐条）

| 关键字 | 官方描述 | 说明 |
|---|---|---|
| `FILENAME` | Base name for restart files (suffix is `-RESTART.wfn` or `-{step}_0.wfn`) | 重启文件的基础名；**后缀由 CP2K 自动加** |
| `BACKUP_COPIES` | Number of backup copies to retain (default: 1) | 保留的备份份数，**默认 1** |
| `COMMON_ITERATION_LEVELS` | How many iteration levels share a common filename (default: 0) | 多少个迭代层级共用同一文件名，**默认 0** |
| `JUST_ENERGY 1` | Write at end of SCF → produces `{FILENAME}-RESTART.wfn` | 每个 SCF 结束时写，产出 `-RESTART.wfn` |
| `QS_SCF N` | Write every N SCF steps → produces `{FILENAME}-{i}_0.wfn` | 每 N 个 SCF 步写一次，产出 `-{i}_0.wfn` |

> **两种命名的差别（重要）**：
> - `JUST_ENERGY 1` → 文件名是 `-RESTART.wfn`（**固定名，被覆盖**）
> - `QS_SCF N` → 文件名是 `-{i}_0.wfn`（**带 SCF 步号，累积多份**）

### 1.4 优化 / MD 的写盘频率

官方给出的几何优化与 MD 写法：

```
&EACH
  GEO_OPT 1  ! or MD 1
  QS_SCF 0
&END EACH
```

即**每个优化步 / 每个 MD 步都写一次**。注释里 `GEO_OPT 1` 与 `MD 1` 是二选一，取决于 `RUN_TYPE`。

### 1.5 官方给的 Best practices（原文三条）

官方原文：

1. Use descriptive filenames that include the project name and step number.
2. Verify the original calculation converged properly before restarting.
3. Ensure the restart uses the same basis sets, functionals, and parameters.

译述：

| # | 官方建议 | 含义 |
|---|---|---|
| 1 | 用描述性文件名，包含项目名与步号 | 避免多个计算的重启文件互相覆盖 |
| 2 | **重启前先确认原计算正常收敛** | 不收敛的波函数当起点没意义 |
| 3 | 重启必须用**相同的基组、泛函、参数** | 换参数后 `wfn` 不匹配 |

### 1.6 波函数文件格式（官方明确警告）

官方原文：

> CP2K wavefunction restart files (`*.wfn`) are binary and architecture-specific. The exact format may vary between CP2K versions — use restart files with the same CP2K version that generated them.

拆成两条硬约束：

| 约束 | 官方措辞 |
|---|---|
| 二进制且**与体系结构相关** | binary and **architecture-specific** |
| **格式可能随版本变化** | The exact format **may vary between CP2K versions** |
| 处置办法 | **use restart files with the same CP2K version that generated them** |

> **推论（非官方原文，但由原文直接得出）**：跨机器、跨编译器、跨 CP2K 版本搬 `.wfn` 有失败风险；跨大版本基本不可靠。

### 1.7 官方 Troubleshooting 三条

| 症状 | 官方描述 | 官方处置 |
|---|---|---|
| **Incompatible Parameters** | 参数不兼容 | Ensure the restart uses identical settings to the original (basis sets, k-points, XC functional, etc.) |
| **File Not Found** | 找不到文件 | Verify the restart file path is correct and the file exists |
| **Corrupted Files** | 文件损坏 | Try an earlier backup copy（用更早的备份副本） |

> `Corrupted Files` 的处置办法正是 `BACKUP_COPIES` 存在的理由。

---

## 2. k 点体系的重启（K-Points）

### 2.1 文件扩展名差异

官方原文：

> For periodic systems using k-point sampling, CP2K stores wavefunction restart files with the `.kp` extension. The procedure is the same as the basic case but uses a different file extension.

| 体系 | 波函数重启文件扩展名 |
|---|---|
| Gamma 点 | `.wfn` |
| k 点采样 | `.kp` |

**流程与基本重启完全一致**，只是文件扩展名不同。

### 2.2 `FULL_GRID`：k 点重启的关键参数

官方对 `&KPOINTS` 段中 `FULL_GRID` 的说明：

| 取值 | 官方描述 | 后果 |
|---|---|---|
| `FULL_GRID ON` | Writes all k-points (**including symmetry-equivalent ones**). Use this for maximum restart flexibility. | 写全部 k 点（含对称等价点），**重启灵活性最大** |
| `FULL_GRID OFF`（**默认**） | Writes only irreducible k-points. Faster but restricted to the same symmetry settings. | 只写不可约 k 点，更快，但**受限于相同对称性设置** |

> **这是 k 点重启最容易踩的点**：默认 `FULL_GRID OFF` 写出的文件，只能在**相同对称性设置**下重启。

### 2.3 生成 k 点重启文件

```
&KPOINTS
  FULL_GRID ON
  SCHEME MONKHORST-PACK 2 2 2
  SYMMETRY ON
&END KPOINTS
```

### 2.4 使用 k 点重启文件

官方示例（**注意：官方原文此段 `&SCF` 段以 `&END PRINT` 收尾，疑为官方笔误，正确应为 `&END SCF`；此处原样保留并标注**）：

```
&DFT
  WFN_RESTART_FILE_NAME your_project-RESTART.kp
  &KPOINTS
    FULL_GRID ON
    SCHEME MONKHORST-PACK 2 2 2
    SYMMETRY ON
  &END KPOINTS
  &SCF
    SCF_GUESS RESTART
  &END PRINT      ! ← 官方原文如此，疑为 &END SCF 笔误
  ...
&END DFT
```

### 2.5 跨 `FULL_GRID` 设置重启

官方明确说明：

> K-point restart files generated with `FULL_GRID ON` can be used with `FULL_GRID OFF` in the restart calculation (or vice versa). Both converge to the same energy, typically in 1 SCF step.

| 生成时 | 重启时 | 是否可用 | 收敛速度 |
|---|---|---|---|
| `FULL_GRID ON` | `FULL_GRID OFF` | ✅ 可用 | typically in **1 SCF step** |
| `FULL_GRID OFF` | `FULL_GRID ON` | ✅ 可用（vice versa） | 同上 |
| 任意 | 任意 | 两者收敛到**相同能量** | — |

### 2.6 官方完整 k 点示例（H_SYM）

```
&GLOBAL
  PROJECT H_SYM
  RUN_TYPE ENERGY
&END GLOBAL

&FORCE_EVAL
  &DFT
    BASIS_SET_FILE_NAME GTH_BASIS_SETS
    POTENTIAL_FILE_NAME POTENTIAL
    &KPOINTS
      FULL_GRID ON
      SCHEME MONKHORST-PACK 2 2 2
      SYMMETRY ON
    &END KPOINTS
    &SCF
      SCF_GUESS ATOMIC
      &PRINT
        &RESTART ON
        &END RESTART
      &END PRINT
    &END SCF
    &XC
      &XC_FUNCTIONAL PADE
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 3.56683 3.56683 3.56683
    &END CELL
    &COORD
      SCALED
      H     0.100000    0.000000    0.000000
      H     0.500000    0.500000    0.000000
      ...
    &END COORD
    &KIND H
      BASIS_SET SZV-GTH
      POTENTIAL GTH-PADE-q1
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

产出 `H_SYM-RESTART.kp`。

**用不同 `FULL_GRID` 设置重启**：

```
&DFT
  WFN_RESTART_FILE_NAME H_SYM-RESTART.kp
  &KPOINTS
    FULL_GRID OFF  ! Different from initial calculation
    SCHEME MONKHORST-PACK 2 2 2
    SYMMETRY ON
  &END KPOINTS
  &SCF
    SCF_GUESS RESTART
    MAX_SCF 3
    &PRINT
      &RESTART OFF
    &END RESTART
  &END PRINT
  &XC
    &XC_FUNCTIONAL PADE
  &END XC
&END DFT
```

> 官方示例中同时给了 `MAX_SCF 3`（因为期望 1 步收敛，3 步是余量）与 `&RESTART OFF`（不再写新的重启文件）。

### 2.7 官方测试用例位置

> The CP2K test suite includes k-point restart tests in `tests/QS/regtest-kp-1/`.

---

## 3. Harris 链（Harris Chain）

### 3.1 官方定义

官方原文：

> The Harris functional converts a k-point wavefunction into a gamma-point wavefunction, enabling k-point-converged densities to seed gamma-point calculations. The three-step chain is: `k-point SCF` → `k-point Harris functional` → `gamma-point DFT`.

**用途**：把 k 点收敛的密度用作 Gamma 点计算的初猜（例如先小 k 点网格收敛密度，再做大胞 Gamma 点）。

三步链：

```
① k-point SCF  →  ② k-point Harris functional  →  ③ gamma-point DFT
```

### 3.2 第 1 步：k 点 SCF

产出 `{PROJECT}-1_0.kp`。

```
&GLOBAL
  PROJECT Carbon
  RUN_TYPE ENERGY
&END GLOBAL

&FORCE_EVAL
  &DFT
    BASIS_SET_FILE_NAME BASIS_SET
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    &KPOINTS
      FULL_GRID ON
      SCHEME MONKHORST-PACK 2 2 2
      SYMMETRY ON
    &END KPOINTS
    &SCF
      SCF_GUESS ATOMIC
      &PRINT
        &RESTART ON
        &END RESTART
      &END PRINT
    &END SCF
    &XC
      &XC_FUNCTIONAL PADE
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 3.56683 3.56683 3.56683
    &END CELL
    &COORD ...
    &KIND C
      BASIS_SET ORB DZVP-GTH-PADE
      POTENTIAL GTH-PADE-q4
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

> **注意产出文件名是 `Carbon-1_0.kp`**，不是 `-RESTART.kp`。这是因为 `&RESTART ON` 不带 `&EACH` 时按步号命名。

### 3.3 第 2 步：k 点 Harris 泛函

读取 `.kp`，并通过 `HARRIS_OUTPUT_WFN` 写出 Gamma 点波函数到 `{PROJECT}-Harris-1_0.kp`：

```
&GLOBAL
  PROJECT Carbon
  RUN_TYPE ENERGY
&END GLOBAL

&FORCE_EVAL
  &DFT
    BASIS_SET_FILE_NAME BASIS_SET
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    WFN_RESTART_FILE_NAME ./Carbon-1_0.kp
    &ENERGY_CORRECTION
      ENERGY_FUNCTIONAL HARRIS
      HARRIS_BASIS HARRIS
      &KPOINTS
        FULL_GRID ON
        SCHEME MONKHORST-PACK 2 2 2
        SYMMETRY ON
      &END KPOINTS
      &PRINT
        &HARRIS_OUTPUT_WFN
        &END HARRIS_OUTPUT_WFN
      &END PRINT
      &XC
        &XC_FUNCTIONAL PBE
      &END XC
    &END ENERGY_CORRECTION
    &SCF
      SCF_GUESS RESTART
      &PRINT
        &RESTART OFF
      &END RESTART
    &END PRINT
    &XC
      &XC_FUNCTIONAL PADE
    &END XC
  &END DFT
  &SUBSYS
    &KIND C
      BASIS_SET ORB DZVP-GTH-PADE
      BASIS_SET HARRIS SZV-GTH-PADE
      POTENTIAL GTH-PADE-q4
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

官方 Key points 五条：

| # | 官方原文 | 含义 |
|---|---|---|
| 1 | `ENERGY_CORRECTION` + `ENERGY_FUNCTIONAL HARRIS` enables the Harris functional | 这两项是开启 Harris 泛函的开关 |
| 2 | `HARRIS_BASIS HARRIS` uses the smaller Harris basis set | 用**更小的** Harris 基组 |
| 3 | `KPOINTS` in `ENERGY_CORRECTION` **must match the step 1 grid** | `ENERGY_CORRECTION` 里的 k 点网格**必须与第 1 步一致** |
| 4 | `HARRIS_OUTPUT_WFN` writes `{PROJECT}-Harris-1_0.kp` | 输出文件命名规则 |
| 5 | The `KIND` section needs **both** the orbital and the `HARRIS` basis set | `&KIND` 里要同时给轨道基组和 Harris 基组 |

产出 `Carbon-Harris-1_0.kp`。

### 3.4 第 3 步：Gamma 点 DFT

读取 Harris 波函数，可选写出 `.wfn`：

```
&GLOBAL
  PROJECT Carbon_gamma
  RUN_TYPE ENERGY
&END GLOBAL

&FORCE_EVAL
  &DFT
    BASIS_SET_FILE_NAME BASIS_SET
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    WFN_RESTART_FILE_NAME ./Carbon-Harris-1_0.kp
    &SCF
      SCF_GUESS RESTART
      &PRINT
        &RESTART ON
      &END RESTART
    &END PRINT
    &XC
      &XC_FUNCTIONAL PADE
    &END XC
  &END DFT
  &SUBSYS
    &KIND C
      BASIS_SET ORB DZVP-GTH-PADE
      POTENTIAL GTH-PADE-q4
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
```

官方两条要点：

- **No `KPOINTS` section** — this is a gamma-point calculation（**不写 `&KPOINTS` 段**）
- `&RESTART ON` writes `Carbon_gamma-RESTART.wfn`

### 3.5 官方测试用例位置

> The CP2K test suite includes these Harris chain tests in `tests/QS/regtest-harris-kp/` (`cc_kp_01.inp`, `cc_kp_02.inp`, `cc_kp_03.inp`) which demonstrate the three-step k-point restart process.

**三个输入文件正好对应三步**，可直接对照。

---

## 4. Band 与 NEB 计算的重启

### 4.1 每个 replica 一个波函数文件

官方原文：

> A band calculation writes a separate wavefunction restart for every replica. CP2K derives the replica project names from the project in `GLOBAL`, for example:
> ```
> neb-BAND1-RESTART.wfn
> neb-BAND2-RESTART.wfn
> neb-BAND3-RESTART.wfn
> ```

| 体系 | 文件名模式 |
|---|---|
| Gamma 点 | `{PROJECT}-BAND<N>-RESTART.wfn` |
| k 点 | `{PROJECT}-BAND<N>-RESTART.kp` |

> With k-point sampling, the corresponding files have the `.kp` extension.

### 4.2 正确写法：设 `SCF_GUESS RESTART`，但**不设** `WFN_RESTART_FILE_NAME`

官方原文：

> To reuse these files, set `SCF_GUESS RESTART` but normally **omit** `WFN_RESTART_FILE_NAME`

```
&GLOBAL
  PROJECT neb
  RUN_TYPE BAND
&END GLOBAL

&EXT_RESTART
  RESTART_FILE_NAME neb-1.restart
&END EXT_RESTART

&FORCE_EVAL
  &DFT
    # Do not set WFN_RESTART_FILE_NAME here.
    &SCF
      SCF_GUESS RESTART
    &END SCF
  &END DFT
  ...
&END FORCE_EVAL
```

### 4.3 为什么不能显式给文件名（关键机制）

官方原文：

> CP2K then selects `neb-BAND<N>-RESTART.wfn` or `neb-BAND<N>-RESTART.kp` after assigning the current replica project name. In contrast, an explicitly specified `WFN_RESTART_FILE_NAME` is interpreted **literally** and is **shared by all replicas**; CP2K does **not** insert the `-BAND<N>` part.

| 写法 | CP2K 行为 |
|---|---|
| 不设 `WFN_RESTART_FILE_NAME` | 按当前 replica 项目名自动选 `{PROJECT}-BAND<N>-RESTART.{wfn,kp}` |
| 显式设 `WFN_RESTART_FILE_NAME neb-RESTART.kp` | **字面解释**，所有 replica 共用同一个文件，**不会**插入 `-BAND<N>` |

官方给出的用途说明：

> An explicit name is therefore useful when all replicas should deliberately start from the same wavefunction, but a name such as `neb-RESTART.kp` will not select the per-replica files shown above.

即：

- **想让所有 replica 从同一个波函数起步** → 显式指定（有用）
- **想各自续算** → 不要指定（否则找不到 per-replica 文件）

### 4.4 `EXT_RESTART` 与波函数重启是两件独立的事

官方原文：

> The `EXT_RESTART` file restores the band coordinates and optimizer state. This is independent of the per-replica wavefunction restarts, so use **both** `EXT_RESTART` and `SCF_GUESS RESTART` when both parts of an interrupted band calculation should be continued. Keep the original `PROJECT` name and run from the directory containing the restart files, or preserve their relative paths.

| 恢复对象 | 由谁负责 |
|---|---|
| 带坐标（band coordinates）与优化器状态 | `&EXT_RESTART` |
| 各 replica 波函数 | `SCF_GUESS RESTART`（不设文件名） |

**两条官方硬约束**：

1. 保持**原始 `PROJECT` 名**；
2. **在包含重启文件的目录下运行**，或保持其相对路径。

---

## 5. 分子动力学重启（Molecular Dynamics）

### 5.1 官方说明

> For continuing molecular dynamics simulations, CP2K stores positions, velocities, cell parameters, and thermostat/barostat state in `.restart` files. Use the `EXT_RESTART` section for fine-grained control over which components to restore.

MD 的 `.restart` 文件里存四类信息：**位置、速度、晶胞参数、恒温器/恒压器状态**。

### 5.2 `&EXT_RESTART` 关键字全表（官方逐条）

| 关键字 | 官方描述 | 备注 |
|---|---|---|
| `RESTART_FILE_NAME` / `EXTERNAL_FILE` | Restart file to read | 两个名字等价 |
| `RESTART_DEFAULT` | Set all `RESTART_*` options at once (**default: TRUE**) | **默认 TRUE**，即默认全恢复 |
| `RESTART_POS` | Restart positions (bare keyword = TRUE) | 裸写即 TRUE |
| `RESTART_VEL` | Restart velocities (bare keyword = TRUE) | 裸写即 TRUE |
| `RESTART_CELL` | Restart cell parameters (bare keyword = TRUE) | 裸写即 TRUE |
| `RESTART_THERMOSTAT` | Restart thermostat state (bare keyword = TRUE) | 裸写即 TRUE |
| `RESTART_BAROSTAT` | Restart barostat state (bare keyword = TRUE) | 裸写即 TRUE |
| `RESTART_RANDOMG` | Restart RNG state (bare keyword = TRUE) | 恢复随机数发生器状态 |
| `RESTART_COUNTERS` | Restart step counter and walltime (bare keyword = TRUE) | 恢复步数与墙钟 |
| `RESTART_BAROSTAT_THERMOSTAT` | Restart barostat thermostat (bare keyword = TRUE) | 恒压器的恒温器 |
| `RESTART_SHELL_POS` / `RESTART_CORE_POS` | Restart shell-model positions | 壳模型专用 |
| `RESTART_SHELL_VELOCITY` / `RESTART_CORE_VELOCITY` | Restart shell-model velocities | 壳模型专用 |
| `RESTART_SHELL_THERMOSTAT` | Restart shell thermostat | 壳模型专用 |

> **裸关键字语法**：`RESTART_POS` 单独写一行等价于 `RESTART_POS TRUE`。这与 01 层提到的单位书写语法同属 CP2K 的输入约定。

### 5.3 官方给出的三种常见场景

**场景 1：只重启位置（速度重新抽样）**

```
&EXT_RESTART
  EXTERNAL_FILE equilibration.restart
  RESTART_POS
  RESTART_VEL FALSE
&END EXT_RESTART
```

> 用途：平衡段结束后，从平衡构型重新赋予初速度开始生产段。

**场景 2：完整重启**

```
&EXT_RESTART
  EXTERNAL_FILE previous_md.restart
  RESTART_POS
  RESTART_VEL
  RESTART_CELL
&END EXT_RESTART
```

**场景 3：NPT 重启**

```
&EXT_RESTART
  EXTERNAL_FILE npt_equil.restart
  RESTART_POS
  RESTART_VEL
  RESTART_CELL
  RESTART_BAROSTAT .FALSE.
&END EXT_RESTART
```

> 注意场景 3 里 `RESTART_BAROSTAT .FALSE.`——**显式关掉恒压器状态恢复**。官方原文未解释原因，此处只照录，不推断。

### 5.4 官方 Best practices（原文一条）

> Best practices: check parameter consistency, keep backup copies for long simulations, and validate energies and temperatures after restarting.

拆成三条：

| # | 官方建议 | 落地动作 |
|---|---|---|
| 1 | check parameter consistency | 核对参数一致性（与波函数重启的"同基组同泛函"同理） |
| 2 | keep backup copies for long simulations | 长模拟保留备份副本 |
| 3 | **validate energies and temperatures after restarting** | 重启后**验证能量与温度** |

> 第 3 条是 MD 重启的官方验收动作：续算后温度/能量应连续，否则说明恢复不完整。

---

## 6. CDFT 重启

### 6.1 官方说明

> For mixed CDFT calculations, each constrained state requires its own wavefunction restart file. Specify `SCF_GUESS RESTART` and `WFN_RESTART_FILE_NAME` per `FORCE_EVAL` subblock.

**要点**：混合 CDFT 中，**每个约束态各需一个波函数重启文件**，且要在**各自的 `FORCE_EVAL` 子块**里分别指定。

### 6.2 官方示例

```
&FORCE_EVAL
  METHOD MIXED
  &MIXED
    MIXING_TYPE MIXED_CDFT
    &MIXED_CDFT
      WFN_OVERLAP TRUE
      WFN_RESTART_FILE_NAME reference_wavefunction.wfn
    &END MIXED_CDFT
  &END MIXED
&END FORCE_EVAL
```

注意 `WFN_RESTART_FILE_NAME` 的位置：在 `&MIXED/&MIXED_CDFT` 段内，**不是**在 `&DFT` 段内。这与基本重启（§1.1）的位置不同。

### 6.3 官方测试用例位置

> The CP2K test suite includes examples in `tests/QS/regtest-cdft-3/`: single-state CDFT calculations generate wavefunction files that are then used as restarts for mixed CDFT calculations.

即：**先跑单态 CDFT 生成波函数，再作为混合 CDFT 的重启**。

---

## 7. 官方参考链接（原文 References 节）

| 资源 | 链接 |
|---|---|
| CP2K Input Reference（关键字详细文档） | <https://manual.cp2k.org/trunk/CP2K_INPUT.html> |
| 示例输入文件 | CP2K 发行版 `tests` 目录 |
| CP2K 论坛 | <https://groups.google.com/group/cp2k> |

---

## 8. 速查：按场景选重启方式

| 场景 | 需要的输入 | 关键点 |
|---|---|---|
| 静态计算续算（Gamma 点） | `WFN_RESTART_FILE_NAME *.wfn` + `SCF_GUESS RESTART` | 同基组同泛函 |
| 静态计算续算（k 点） | `WFN_RESTART_FILE_NAME *.kp` + `SCF_GUESS RESTART` | 注意 `FULL_GRID` |
| 跨 `FULL_GRID` 重启 | 同上 | `ON`↔`OFF` 都可，约 1 步收敛 |
| k 点密度 → Gamma 点初猜 | 三步 Harris 链 | 第 2 步 k 点网格须与第 1 步一致 |
| NEB / BAND 续算 | `&EXT_RESTART` + `SCF_GUESS RESTART`（**不设文件名**） | 保持 PROJECT 名与工作目录 |
| MD 续算（全恢复） | `&EXT_RESTART` + `EXTERNAL_FILE` | 默认 `RESTART_DEFAULT TRUE` |
| MD 只接构型 | `RESTART_POS` + `RESTART_VEL FALSE` | 速度重抽 |
| 混合 CDFT 续算 | 每个约束态一个 `WFN_RESTART_FILE_NAME` | 写在 `&MIXED_CDFT` 内 |

---

## 9. 官方原文中的注意事项汇总

| # | 官方措辞 | 影响 |
|---|---|---|
| 1 | `.wfn` 是 **binary and architecture-specific** | 跨机器搬运有风险 |
| 2 | 格式 **may vary between CP2K versions** | 用同一版本生成的重启文件 |
| 3 | `FULL_GRID OFF`（默认）**restricted to the same symmetry settings** | 改对称性后可能无法重启 |
| 4 | `WFN_RESTART_FILE_NAME` 被 **interpreted literally and is shared by all replicas** | NEB 中不要显式指定 |
| 5 | `RESTART_DEFAULT` **default: TRUE** | 默认恢复全部状态 |
| 6 | 重启前 **Verify the original calculation converged properly** | 未收敛的波函数无意义 |
| 7 | 重启后 **validate energies and temperatures** | MD 续算的验收动作 |

---

## 10. 官方页面缺口

本页内容**完整**，无占位段。但以下相关主题在官方手册中**没有独立页面**：

| 主题 | 状态 |
|---|---|
| 重启文件内部的二进制格式说明 | 官方未公开格式规范 |
| `&EXT_RESTART` 关键字的**完整**默认值表 | 本页只给部分；完整默认值见 Input Reference |
| 跨版本波函数兼容性矩阵 | 官方无此表，只说"may vary" |

---

## → 交叉索引

| 本文件内容 | 关联 A/F 层条目 | 关联 G 层文件 |
|---|---|---|
| 波函数重启文件命名与写盘频率 | F 层 `playbook.md` 续算与作业管理 | — |
| `SCF_GUESS` 三种取值 | — | `03_scf_convergence.md` §1.3 |
| k 点 `FULL_GRID` 与对称性 | A 层 decide.md k 点相关节 | `02_dft_methods.md` §4 |
| MD `.restart` 与恒温器状态 | F 层 `playbook.md` MD 续算 | `04_sampling_md.md`（系综与温控） |
| NEB 每 replica 波函数 | A 层 decide.md NEB 节（官方 NEB 页为占位页） | `05_optimization.md` §NEB 占位说明 |
| CDFT 混合计算 | — | `02_dft_methods.md` §7 |
| `&PRINT` 段与输出控制 | F 层 `playbook.md` 输出管理 | `01_global_and_units.md`（`PRINT_LEVEL`） |
