# 03 · SCF 收敛与 CUTOFF/REL_CUTOFF 收敛（官方）

> **来源**：
> - <https://manual.cp2k.org/trunk/methods/dft/convergence.html>
> - <https://manual.cp2k.org/trunk/methods/dft/cutoff.html>
> - <https://manual.cp2k.org/trunk/getting-started/troubleshooting.html>（SCF 相关条目）
> **抓取日期**：2026-09-08

---

## 第一部分：如何让 SCF 收敛（官方 `convergence.html`）

### 1.1 最重要的行为变更：不收敛默认 ABORT

> **官方明确说明**：**从 CP2K 2024.1 起，SCF 不收敛时默认中止运行**（源码位置 `qs_scf.F:702`）。

相关关键字：

| 关键字 | 官方语义 |
|---|---|
| `IGNORE_CONVERGENCE_FAILURE` | 忽略收敛失败继续运行。**官方把它标为最后手段（last resort），并附风险警告** |

**官方风险警告的实质**：忽略收敛失败意味着后续得到的能量、力、应力都基于未收敛的电子结构，不可信。对几何优化/MD 而言，这会污染结构、下一步的外推波函数，甚至导致结构"爆炸"。

**F 层对应经验**：F 层 `playbook.md` §1 的症状→处方表。**凡涉及该关键字，一律先按 G 层这一节排查，不要直接开 `IGNORE_CONVERGENCE_FAILURE`。**

---

### 1.2 一般考虑（官方）

#### 结构要合理
- 官方要求从**化学与物理上合理**的结构开始。严重的近距接触、非现实的配位环境或准备不当的晶胞会导致**受力不稳定、SCF 失败、非物理的原子位移**。
- 官方举例：**"amorphous cell" 结构（随机堆积分子/原子）极难优化**，尤其当化学键被严重打乱时；同理，**来自高温 MD 的汽化或熔化状态、含大量断键的构型**也如此。

#### 电荷与自旋
- 必须正确设置 `CHARGE` 与 `MULTIPLICITY`。
- 官方给出典型例子：**O₂ 需要 `MULTIPLICITY 3` 与 UKS（`LSD`）**，否则无法正确描述三重态基态。

#### 初始猜测（`SCF_GUESS`）

| 取值 | 官方说明 |
|---|---|
| `ATOMIC` | **默认**。用原子电荷密度重叠生成初始密度 |
| `EXTERNAL_DENSITY` | 从 cube 文件读入外部密度 |
| `RESTART` | 从波函数重启文件读取，配合 `WFN_RESTART_FILE_NAME` |

**`EXTERNAL_DENSITY` 的官方限制**：
- **cube 网格必须与最细的 CP2K 网格一致**；
- **不支持含动能密度的泛函、DFT+U、`DRHO_BY_COLLOCATION`**。

**`RESTART` 的官方推荐场景（六种）**：官方列出六类适合用波函数重启的情形（续算、参数微调后继续、相似体系等）。

**波函数文件格式差异（官方重要提醒）**：
- **gamma-only 的 `-RESTART.wfn` 与 k 点的 `-RESTART.kp` 不可互换。**
- **2026.2 起**可经 **Harris 能量修正**做转换（见 `07_restarting.md` §3）。

#### 数值参数
- **官方关键洞察**：**调高 `EPS_DEFAULT` / `CUTOFF` / `REL_CUTOFF` 可能总耗时不变。**
  - 原因：更严的容差可能反而让 SCF 更快收敛，抵消掉单步成本的增加。
  - 所以**不要假设"调松就一定更快"**。
- **k 点更多可能有助收敛**（官方原文）。

---

### 1.3 对角化算法（MIXING）

- 默认混合方法为 **`DIRECT_P_MIXING`**。
- 官方列出可换用的方法：**`BROYDEN_MIXING`**、**`PULAY_MIXING`**、**`KERKER_MIXING`**。
- **`MIXING` 段仅适用于传统对角化方法**；OT 使用不同的电荷混合方式（官方静态计算教程明确说明）。

#### SMEAR（smearing）

| 方法 | 官方说明 |
|---|---|
| `FERMI_DIRAC` | **需外推到 0 温度**（`ELECTRONIC_TEMPERATURE` → 0） |
| `GAUSSIAN` | **需 `SIGMA` → 0 外推** |

**官方补充**：smearing 会导致分子轨道被占据到导带，**必须设置 `ADDED_MOS`** 纳入额外空轨道（否则为降成本会被省略）。带 smearing 的输出会多出熵项，**最终自由能 = 总 DFT 能量 + 熵能**，**应引用 TS→0 外推的自由能**（详见 `01_global_and_units.md` §5.7）。

---

### 1.4 OT 算法（官方）

相关关键字：
- `ALGORITHM`（默认 `STRICT`）
- `LINESEARCH`
- `MINIMIZER`（默认 `CG`）
- `PRECONDITIONER`

#### OUTER_SCF 机制（官方）

OT 有两层 SCF 循环：
- **内层**：`SCF/MAX_SCF` 控制 OT 的迭代步数；
- **外层**：`SCF/OUTER_SCF/MAX_SCF` 控制重置 OT 预条件子的次数。

**官方给出的关键数值建议**：

| 关键字 | 官方建议 |
|---|---|
| `SCF/MAX_SCF` | **可降到 16–32** |
| `SCF/OUTER_SCF/MAX_SCF` | **设 8–16 对多数情形够用** |

> 这是 G 层里少见的"官方直接给数值区间"的地方，价值很高。

**官方在 DFT+U HowTo 中的实际取值（示例，非推荐）**：`MAX_SCF 21` + `&OUTER_SCF on / MAX_SCF 20`。

---

### 1.5 SCF 收敛排查的官方思路（汇总）

按官方 `convergence.html` 与 `troubleshooting.html` 的信息，建议顺序：

```
1. 检查结构与初始几何（近距接触 / 断键 / 随机堆积）
2. 检查 CHARGE / MULTIPLICITY（自旋态是否正确，O2 需 MULTIPLICITY 3 + UKS）
3. 检查初始猜测（ATOMIC / RESTART / EXTERNAL_DENSITY 是否合适）
4. 检查 smearing 设置（金属/小带隙必须开；FERMI_DIRAC 需外推 0）
5. 检查网格参数（CUTOFF / REL_CUTOFF 是否足够，见第二部分）
6. 检查混合方法（对角化路径可换 BROYDEN / PULAY / KERKER）
7. 检查 OT 参数（PRECONDITIONER / MINIMIZER / ALGORITHM）
8. 检查内层/外层 SCF 步数（16–32 / 8–16）
9. 最后才考虑 IGNORE_CONVERGENCE_FAILURE（官方标为最后手段）
```

**官方相关报错原文**（详见 `08_errors_and_faq.md`）：
- `SCF run NOT converged`
- `KS energy is an abnormal value (NaN/Inf)` → 官方指向本页

---

## 第二部分：CUTOFF 与 REL_CUTOFF 收敛（官方 `cutoff.html`）

> 这一节是官方**完整的收敛教程**，包含原理、流程、脚本与实测数据表。

### 2.1 原理（官方）

- CP2K 用**多重网格（multi-grid）**表示高斯函数。
- 默认参数：
  - **`NGRIDS 4`** — 4 层网格
  - **`CUTOFF`** — 最细网格的平面波截断，单位 **Ry**
  - **`PROGRESSION_FACTOR 3.0`** — 网格之间的递进因子
  - **`REL_CUTOFF`** — 控制高斯函数如何映射到各层网格
- 网格截断的递推关系（官方给出）：

```
Ecutᵢ = Ecut₁ / α⁽ⁱ⁻¹⁾
```

其中 `Ecut₁` 是最细层的 `CUTOFF`，`α` 是 `PROGRESSION_FACTOR`。

- **狭窄尖锐的高斯函数**映射到**更细的网格**；**宽而平滑的高斯函数**映射到**更粗的网格**（官方静态计算教程原文）。
- **`REL_CUTOFF` 的含义**：任何高斯函数下方的网格间距应比等效平面波截断 `REL_CUTOFF` 更细（官方静态计算教程原文）。

### 2.2 关键洞察（官方，最重要的一条）

> **单独提高 `CUTOFF` 而不提高 `REL_CUTOFF` 会让高斯被推到粗网格，抵消效果。**

这是很多人的误区。**两者必须一起收敛。**

### 2.3 收敛流程（官方教程结构）

官方给出的标准流程：

1. **模板输入**：`template.inp`，其中用占位标记 `LT_cutoff` / `LT_rel_cutoff`。
2. **`sed` 替换**：用脚本把标记替换成具体数值，生成一组输入。
3. **三个 shell 脚本**：
   - `inputs` — 生成输入文件
   - `run` — 提交运行
   - `analyse` — 提取结果并分析
4. **跳 SCF 的技巧**：`MAX_SCF 1` 可用于跳过 SCF（只做网格/能量评估的快速扫描）。
5. **看网格信息**：`PRINT_LEVEL MEDIUM` 可看到 `MULTIGRID INFO`。
6. **并行注意**：SLURM 下**不要用 `--bind-to none`**。

### 2.4 实测数据表（官方，Si bulk8）

**CUTOFF 收敛（固定 REL_CUTOFF）**：

| CUTOFF [Ry] | 误差 [Ha] |
|---|---|
| 250 及以上 | **< 1e-8** |

**REL_CUTOFF 收敛（固定 CUTOFF）**：

| REL_CUTOFF [Ry] | 误差 [Ha] |
|---|---|
| ≥ 60 | **< 1e-8** |

### 2.5 官方最终推荐

```
CUTOFF 250
REL_CUTOFF 60
```

> **注意适用范围**：这是**Si bulk8 这个测试体系**的收敛结果。官方教程的意图是**教方法**——对其它体系（尤其是含过渡金属、需要高精度应力/力的体系），**必须自己重跑收敛测试**。

### 2.6 与其它文档的关系

- 官方静态计算教程（`howto:static_calculation`）用的是 `CUTOFF 300` / `REL_CUTOFF 60`，并明确说"示例计算所用的积分网格设置，已经选定为对该精度足够"，同时指向 `howto:converging_cutoff`。
- 官方 MD 页（`sampling/molecular_dynamics.html`）给出**AIMD 可以比静态计算更松**的官方说明：**若某元素在优化/能量任务中用 `CUTOFF 400`，在 AIMD 中可设为 `CUTOFF 300`**。
  - **反面警告（官方）**：设置过松会造成**噪声力、差的能量守恒、人为加热或错误的动力学**。

---

## 3. 交叉索引

| 主题 | G 层 | A/F 层 |
|---|---|---|
| CUTOFF / REL_CUTOFF 数值速查 | 本文 §2.4–2.5 | A `decide.md`；F `playbook.md` §0 |
| SCF 不收敛症状→处方 | 本文 §1.5 | F §1（更细的症状表） |
| `IGNORE_CONVERGENCE_FAILURE` | 本文 §1.1 | F §1 |
| 金属体系 smearing | 本文 §1.3；`01` §5.7 | A；F |
| OT vs 对角化 | 本文 §1.4；`02` §3 | A `decide.md` §28 |
| 优化过程中的 SCF 质量 | `05_optimization.md` §6 | A；F |
