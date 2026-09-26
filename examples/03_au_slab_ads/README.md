# 示例 03 · Au(100) slab 吸附 O（几何优化 + 色散 + 自旋 + 金属 smearing）

**难度**：★★★☆☆
**目标**：学会**表面吸附**这一类最常见的计算——把"周期 slab + 吸附物 + 金属特性"一次性配齐
**体系**：Au(100) 三层 2×2（12 个 Au）+ 顶位吸附 1 个 O，真空层约 19 Å
**特点**：这是**配置项最多**的示例，也是新手最容易漏项的一类

---

## 文件

| 文件 | 说明 |
|---|---|
| `au_slab_o.xyz` | 13 个原子的坐标（Å） |
| `au_slab_o.inp` | 由 `gen_inp.py` 生成、已通过校验的输入文件 |
| `README.md` | 本文件 |

## 复现（4 步）

```bash
# 1) 环境自检（第一次用必跑）
python scripts/doctor.py

# 2) 生成输入（本例已生成好 au_slab_o.inp，这步是演示怎么来的）
python scripts/gen_inp.py \
    --type geo_opt \
    --project au_slab_o \
    --elem Au O \
    --basis DZVP-MOLOPT-SR-GTH DZVP-GTH-PADE \
    --potential GTH-PBE-q11 GTH-PADE-q6 \
    --multiplicity 3 \
    --dispersion \
    --periodic xy \
    --smear \
    --kpoints "4 4 1" \
    --cell 8.156 0 0 0 8.156 0 0 0 25.0 \
    --cutoff 400 --eps-scf 1.0E-6 --max-scf 500 --eps-diis 0.05 \
    --added-mos 500 --cholesky INVERSE --mixing-alpha 0.1 --mixing-beta 1.5 \
    --mixing-nbroyden 8 --diagonalization-eps-adapt 0.01 \
    --xyz examples/03_au_slab_ads/au_slab_o.xyz \
    -o examples/03_au_slab_ads/au_slab_o.inp

# 3) 校验语法（提交前必做）
python scripts/validate_inp.py examples/03_au_slab_ads/au_slab_o.inp

# 4) 提交（需你本机有 cp2k）
cd examples/03_au_slab_ads
mpirun -n 8 cp2k.popt au_slab_o.inp 1>au_slab_o.out 2>au_slab_o.err
```

跑完读结果：

```bash
python scripts/parse_output.py examples/03_au_slab_ads/au_slab_o.out
python scripts/diagnose.py    examples/03_au_slab_ads/au_slab_o.out
```

## 该看什么

| 指标 | 预期 | 不对怎么办 |
|---|---|---|
| SCF 是否收敛 | `SCF run converged` | 金属体系难收敛 → 查 `references/playbook.md` §1.3 |
| 几何优化是否收敛 | `GEOMETRY OPTIMIZATION COMPLETED` | 跑满 `MAX_ITER 400` → 放宽 `MAX_FORCE` 或换 `CG` |
| Au–O 距离 | 约 2.0–2.2 Å | 差很多 → 检查初始位置与自旋态 |
| 能量单调下降 | 每步下降且逐渐变平 | 上下抖动 → 检查 smearing 温度与混合参数 |

**吸附能怎么算**（表面计算的核心产出）：

```
E_ads = E(slab + O) − E(slab) − ½·E(O₂)
```

本例只给了 `slab + O` 一个输入。要算吸附能，你需要再跑两次：

```bash
# 把 O 原子行删掉 → 干净的 slab（坐标取 au_slab_o.xyz 去掉最后一行）
python scripts/gen_inp.py --type geo_opt --project au_slab --elem Au \
    --basis DZVP-MOLOPT-SR-GTH --potential GTH-PBE-q11 \
    --dispersion --periodic xy --smear --kpoints "4 4 1" \
    --cell 8.156 0 0 0 8.156 0 0 0 25.0 \
    --xyz slab.xyz -o slab.inp

# 孤立的 O2 分子（--periodic none）
python scripts/gen_inp.py --type geo_opt --project o2 --elem O \
    --basis DZVP-GTH-PADE --potential GTH-PADE-q6 --multiplicity 3 \
    --periodic none --cell 12 0 0 0 12 0 0 0 12 \
    --xyz o2.xyz -o o2.inp
```

> 三次计算的 `CUTOFF`、`k 点`、`--cell` 必须完全一致，否则能量不可比。

## 学到什么

| 配置 | 为什么必须有 |
|---|---|
| `--periodic xy` | slab 在 x/y 方向周期、z 方向真空；**用 `xyz` 会把真空也当周期，完全错** |
| `--cell` 的 C 轴 25 Å | 真空层 ≥ 15 Å，否则相邻 slab 会相互作用 |
| `--smear` | **金属必须有**，否则费米面附近占据数跳变 → SCF 不收敛 |
| `--kpoints "4 4 1"` | 金属需要 k 点采样；**z 方向是 1**（真空方向不需要采样） |
| `--dispersion` | Au 的范德华作用不可忽略；不加会低估吸附能 |
| `--multiplicity 3` | O 吸附后可能是开壳层；**生产计算必须测试 1/3/5 取最低能量** |
| `--cutoff 400` + 精细 SCF | 金属体系的收敛保险，见下 |

> **注意**：`recommend.py` 对 Au–O 的**默认**建议其实是**闭壳层**（Au 的自旋猝灭），
> 并推荐 `CUTOFF 400 Ry`、`EPS_SCF 1e-6`、`MAX_SCF 500`、`ADDED_MOS 500`、
> `CHOLESKY INVERSE`、`BROYDEN(α=0.1, β=1.5)` —— 本例已按此配置。
> 我额外把 `--multiplicity` 设成 3 是为了演示**自旋态测试**的写法；
> 生产计算请分别跑 1 / 3 / 5，取能量最低且 SCF 收敛的那个。

## 下一步

- 想加**偶极修正**（slab 有净偶极时）→ 加 `--surface-dipole`
- 想算**态密度/功函数** → 加 `--properties pdos` 并提高 `--kpoints`
- 大 slab 想省钱 → 用 `--fixed-atoms` 冻住底层原子，只放松表层与吸附质
- 想学表面计算完整方法论 → `python scripts/guide.py show optimize`（「⑤ 几何/晶胞优化」）和
  `references/playbook.md` §4（建模实操）
