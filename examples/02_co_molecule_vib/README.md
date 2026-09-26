# 示例 02 · CO 分子振动分析（VIBRATIONAL_ANALYSIS）

**难度**：★★☆☆☆
**目标**：学会**非周期（分子）**计算的正确设置，并跑出第一个振动频率
**体系**：CO 分子，C–O = 1.128 Å，放在 12 Å 立方盒中（盒子只用来定泊松求解器边界）
**特点**：这是最容易出错的一类——分子计算忘了 `PERIODIC NONE`，或忘了给盒子

---

## 文件

| 文件 | 说明 |
|---|---|
| `co.xyz` | 2 个原子的坐标（Å） |
| `co_vib.inp` | 由 `gen_inp.py` 生成、已通过校验的输入文件 |
| `README.md` | 本文件 |

## 复现（4 步）

```bash
# 1) 环境自检（第一次用必跑）
python scripts/doctor.py

# 2) 生成输入（本例已生成好 co_vib.inp，这步是演示怎么来的）
python scripts/gen_inp.py \
    --type vib \
    --project co_vib \
    --elem C O \
    --basis DZVP-GTH-PADE DZVP-GTH-PADE \
    --potential GTH-PADE-q4 GTH-PADE-q6 \
    --multiplicity 1 \
    --periodic none \
    --cell 12.0 0 0 0 12.0 0 0 0 12.0 \
    --xyz examples/02_co_molecule_vib/co.xyz \
    -o examples/02_co_molecule_vib/co_vib.inp

# 3) 校验语法（提交前必做）
python scripts/validate_inp.py examples/02_co_molecule_vib/co_vib.inp

# 4) 提交（需你本机有 cp2k）
cd examples/02_co_molecule_vib
mpirun -n 8 cp2k.popt co_vib.inp 1>co_vib.out 2>co_vib.err
```

> 振动分析是**有限差分**：对每个自由度做 ±DX 位移（本例 2 原子 × 3 方向 = 6 次额外 SCF），
> 所以耗时约为静态计算的 7 倍。`NPROC_REP 8` 表示每个位移用 8 个进程，按你机器的核数调整。

跑完读结果：

```bash
python scripts/parse_output.py examples/02_co_molecule_vib/co_vib.out
```

## 该看什么

| 指标 | 预期 | 不对怎么办 |
|---|---|---|
| SCF 是否收敛 | `SCF run converged` | 分子体系振荡 → 查 `references/playbook.md` §1.2 |
| C–O 伸缩频率 | 约 **2150–2250 cm⁻¹**（PBE 略高估） | 差很多 → 检查 `MULTIPLICITY` 与自旋态 |
| 频率是否全为正 | 全部 > 0 | 出现虚频（负数）→ 结构不在极小点 |
| 强度输出 | 有 `INTENSITIES` 表 | 无 → 检查 `&VIBRATIONAL_ANALYSIS INTENSITIES T` |

> 参考实验值：CO 气相伸缩振动 **2143 cm⁻¹**。GGA 泛函通常高估 1–3%，属正常。

## 学到什么

- **分子计算四件套**：`--periodic none` + **`&CELL PERIODIC NONE`** + `&POISSON PERIODIC NONE` + `POISSON_SOLVER WAVELET`。
  > **更正记录（原写"三件套"）**：原来说的三件只提了 `&POISSON`，**漏了 `&CELL PERIODIC NONE`**。
  > 官方 schema 对 `&POISSON/PERIODIC` 的原话是 *"this only applies to the **electrostatics**.
  > See the **CELL** section to specify the periodicity used for e.g. the pair lists.
  > **Typically the settings should be the same.**"* —— 只设 `&POISSON` 会让
  > **静电按非周期、而 pair list / 结构仍按三维周期**，邻居表白算镜像。
  > `gen_inp.py` 与 `validate_inp.py` 均已相应修正（前者两段成对发射，后者检查两者一致）。
- **`--cell` 对分子计算仍然必填**——它给泊松求解器定边界，不是"周期"才需要
- **`--multiplicity 1`** 表示闭壳层单重态；CO 是 14 个电子，闭壳层正确
- **UKS**：`gen_inp.py` 在给出 `--multiplicity` 时自动加 `UKS`（自旋极化）

## 下一步

- 想算**红外光谱**（带强度）→ 保持 `INTENSITIES T`，用 `postprocess.py ir` 画谱
- 想算**更大分子** → 用 `--periodic none` 但要重新检查 `--cell` 是否够大（原子离盒壁 ≥ 5 Å）
- 想了解振动分析的完整流程 → `python scripts/guide.py show static`（振动分析在「⑥ 静态计算与电子结构性质」阶段）
