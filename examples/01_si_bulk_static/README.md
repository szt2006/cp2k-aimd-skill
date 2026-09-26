# 示例 01 · Si 块体 8 原子（静态计算）

**难度**：★☆☆☆☆（新手第一个示例）
**目标**：跑通 CP2K 最小闭环——生成输入 → 校验 → 提交 → 读结果
**体系**：Si 金刚石结构，8 原子，晶格常数 5.4307 Å
**来源**：CP2K 官方示例 `Si_bulk8`（见 `references/official/01_global_and_units.md` §5.2）

---

## 文件

| 文件 | 说明 |
|---|---|
| `si_bulk8.xyz` | 8 个 Si 原子的坐标（Å） |
| `si_bulk8.inp` | 由 `gen_inp.py` 生成、已通过校验的输入文件 |
| `README.md` | 本文件 |

## 复现（4 步）

```bash
# 1) 环境自检（第一次用必跑）
python scripts/doctor.py

# 2) 生成输入（本例已生成好 si_bulk8.inp，这步是演示怎么来的）
python scripts/gen_inp.py \
    --type static \
    --project si_bulk8 \
    --elem Si \
    --basis DZVP-GTH-PADE \
    --potential GTH-PADE-q4 \
    --periodic xyz \
    --cell 5.4306975 0 0 0 5.4306975 0 0 0 5.4306975 \
    --xyz examples/01_si_bulk_static/si_bulk8.xyz \
    -o examples/01_si_bulk_static/si_bulk8.inp

# 3) 校验语法（提交前必做）
python scripts/validate_inp.py examples/01_si_bulk_static/si_bulk8.inp

# 4) 提交（需你本机有 cp2k）
cd examples/01_si_bulk_static
mpirun -n 4 cp2k.popt si_bulk8.inp 1>si_bulk8.out 2>si_bulk8.err
```

跑完读结果：

```bash
python scripts/parse_output.py examples/01_si_bulk_static/si_bulk8.out
python scripts/diagnose.py    examples/01_si_bulk_static/si_bulk8.out
```

## 该看什么

| 指标 | 预期 | 不对怎么办 |
|---|---|---|
| SCF 是否收敛 | `SCF run converged` | 查 `references/playbook.md` §1.1 |
| 总能量 | 约 −22 Ha（8 个 Si） | 数量级差太远 → 检查基组/赝势 |
| 受力 | 有限且小 | NaN/极大 → 检查坐标与晶胞 |

## 学到什么

- **`--periodic xyz`** 表示三维周期（块体）；表面用 `xy`，分子用 `none`
- **`--cell`** 即使是分子计算也要给（定义泊松求解器的盒子）
- **赝势的 `q` 必须与元素匹配**：Si 是 `GTH-PADE-q4`（`gen_inp.py` 已按元素查好）

## 下一步

- 想做**晶胞优化**（找平衡晶格常数）→ 把 `--type static` 换成 `--type cell_opt`
- 想看**能带/PDOS** → 加 `--kpoints "6 6 6"` 并设 `--properties pdos`
- 想学完整流程 → `python scripts/guide.py show static`（展开「⑥ 静态计算与电子结构性质」阶段）
