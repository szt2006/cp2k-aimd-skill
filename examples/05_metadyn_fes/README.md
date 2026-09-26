# 示例 05 · TiO₂ 元动力学自由能面（Metadynamics + DFT+U）

**难度**：★★★★☆（最难的示例）
**目标**：跑通**增强采样**，从 metadynamics 得到自由能面（FES）
**体系**：TiO₂ 分子（1 Ti + 2 O），Ti–O = 1.62 Å，O–Ti–O = 110°，放在 15 Å 盒中
**特点**：把三个高阶概念串在一起——**集合变量（COLVAR）+ 元动力学（METADYN）+ DFT+U**

---

## 文件

| 文件 | 说明 |
|---|---|
| `tio2.xyz` | 3 个原子的坐标（Å）；**原子顺序 = Ti, O1, O2**，与 COLVAR 定义强绑定 |
| `metadyn.inp` | 由 `gen_inp.py` 生成、已通过校验的输入文件 |
| `README.md` | 本文件 |

## 复现（4 步）

```bash
# 1) 环境自检（第一次用必跑）
python scripts/doctor.py

# 2) 生成输入（本例已生成好 metadyn.inp，这步是演示怎么来的）
python scripts/gen_inp.py \
    --type metadyn \
    --project tio2_metadyn \
    --kinds "Ti:DZVP-MOLOPT-SR-GTH:GTH-PBE-q12:U=3.5:L=2" \
            "O:DZVP-GTH-PADE:GTH-PADE-q6" \
    --plus-u-method mulliken \
    --periodic none \
    --well-tempered \
    --metadyn-ww 0.5 \
    --steps 2000 \
    --cell 15.0 0 0 0 15.0 0 0 0 15.0 \
    --xyz examples/05_metadyn_fes/tio2.xyz \
    -o examples/05_metadyn_fes/metadyn.inp

# 3) 校验语法（提交前必做）
python scripts/validate_inp.py examples/05_metadyn_fes/metadyn.inp

# 4) 提交（需你本机有 cp2k）
cd examples/05_metadyn_fes
mpirun -n 8 cp2k.popt metadyn.inp 1>metadyn.out 2>metadyn.err
```

跑完出图：

```bash
# 方式 A：直接从 CP2K 的 metadyn restart 文件重跑 graph 并出图
python scripts/postprocess.py fes \
    --restart examples/05_metadyn_fes/tio2_metadyn-1.restart \
    --ndim 2 \
    --cell 15 0 0 0 15 0 0 0 15

# 方式 B：如果你已经手动跑过 cp2k graph，直接对 fes.dat 出图
python scripts/postprocess.py fes --fesdat examples/05_metadyn_fes/fes.dat
```

> **`--ndim` 必须填真实的 CV 维数（本例 2）**。填错会导致 FES 投影完全错乱，
> 这是元动力学后处理最常见的坑。

## 该看什么

| 指标 | 预期 | 不对怎么办 |
|---|---|---|
| SCF 是否收敛 | `SCF run converged` | +U 体系难收敛 → 查 `references/playbook.md` §1.4 |
| 高斯是否在堆积 | 输出有 `HILL NR` 递增 | 不堆 → 检查 `DO_HILLS` 与 `NT_HILLS` |
| CV 是否被填满 | 两个 Ti–O 距离都遍历到 1.6–2.4 Å | 卡在一个值 → 调整 `WW` 或加墙位置 |
| FES 是否闭合 | 两个极小之间有鞍点 | 只有一片 → 采样不够，加步数 |

> 本示例只跑 **2000 步**，只够看到"高斯在堆"这个现象。
> 真实的 FES 收敛需要 **数万到数十万步**，取决于体系自由度与 CV 选择。

## 学到什么

### 1. 集合变量（COLVAR）怎么定义

```cp2k
&COLVAR
  &DISTANCE
    ATOMS 1 2      ← 第 1 个原子（Ti）到第 2 个原子（O1）的距离
  &END DISTANCE
&END COLVAR
&COLVAR
  &DISTANCE
    ATOMS 1 3      ← Ti 到 O2 的距离
  &END DISTANCE
&END COLVAR
```

`ATOMS` 用的是 **1-based 的坐标顺序索引**，所以 `tio2.xyz` 里原子必须是 `Ti, O1, O2`。
**改了坐标顺序却不改 COLVAR，是最隐蔽的错误。**

### 2. METAVAR 怎么引用 COLVAR

```cp2k
&METADYN
  DO_HILLS
  NT_HILLS 50        ← 每 50 步放一个高斯
  WW 0.5             ← well-tempered 的偏置因子 γ
  WELL_TEMPERED T
  &METAVAR
    SCALE 0.3        ← 该 CV 的高斯宽度
    COLVAR 1         ← 引用第 1 个 COLVAR（1-based）
    &WALL ...        ← 给这个 CV 加边界墙
  &END METAVAR
```

### 3. `&WALL` 的位置必须按真实键长设

模板里 `POSITION 4.00` / `0.6` 是**占位值**，对任何真实体系都不成立。本例已按
Ti–O 键长改成 **`POSITION [angstrom] 2.20` + `DIRECTION WALL_PLUS`**：

- 物理含义：只允许 Ti–O 距离**不超过** 2.20 Å（解离方向被墙挡住）
- `WALL_PLUS` = 只挡"增大方向"；`WALL_MINUS` = 只挡"减小方向"
- `K [kcalmol] 40.0` 是墙的力常数，越大越硬

> **改体系一定要改 WALL**。墙位置离真实键长太远 → 墙不起作用；太近 → 把体系压在墙上，
> FES 完全失真。

### 4. DFT+U 为什么必须加

Ti 是 3d 过渡金属，PBE 会严重低估强关联效应（TiO₂ 被算成金属）。加 `U_MINUS_J = 3.5 eV`
（`L=2` 表示 d 轨道）是 TiO₂ 的标准做法。`--plus-u-method mulliken` 指定投影方式，
`gen_inp.py` 只在**存在 `U=` 的 kind** 时才注入 `PLUS_U_METHOD`。

## 下一步

- 想换 CV（如角度、配位数）→ 改 `&SUBSYS &COLVAR`，支持 28 种 CV 类型，
  见 `references/decide.md` §17
- 想用 **PLUMED** → 加 `--plumed --plumed-file plumed.dat`
- 想用**多 walker** → 加 `--multi-walker`
- 想学增强采样完整方法论 → `references/course_learned.md`（FES 专题）与
  `python scripts/guide.py show react`（「⑧ 反应路径（NEB / 元动力学）」）
