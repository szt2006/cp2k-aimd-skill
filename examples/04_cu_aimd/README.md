# 示例 04 · Cu 金属 AIMD（NVT 系综 + Langevin 恒温器）

**难度**：★★★☆☆
**目标**：跑通第一个**从头算分子动力学**，理解"步数 / 时间步长 / 系综 / 恒温器"四个开关
**体系**：Cu fcc 常规胞，4 个原子，a = 3.615 Å（金属 → 必须 smearing + k 点）
**特点**：MD 是"时间尺度"最容易踩坑的地方——**跑 500 步 ≠ 得到物理结果**

---

## 文件

| 文件 | 说明 |
|---|---|
| `cu.xyz` | 4 个 Cu 原子的坐标（Å） |
| `cu_aimd.inp` | 由 `gen_inp.py` 生成、已通过校验的输入文件 |
| `README.md` | 本文件 |

## 复现（4 步）

```bash
# 1) 环境自检（第一次用必跑）
python scripts/doctor.py

# 2) 生成输入（本例已生成好 cu_aimd.inp，这步是演示怎么来的）
python scripts/gen_inp.py \
    --type aimd_md \
    --project cu_aimd \
    --elem Cu \
    --basis DZVP-MOLOPT-SR-GTH \
    --potential GTH-PBE-q11 \
    --periodic xyz \
    --smear \
    --kpoints "2 2 2" \
    --cell 3.615 0 0 0 3.615 0 0 0 3.615 \
    --ensemble nvt \
    --thermostat langevin \
    --restart-freq 100 \
    --steps 500 \
    --xyz examples/04_cu_aimd/cu.xyz \
    -o examples/04_cu_aimd/cu_aimd.inp

# 3) 校验语法（提交前必做）
python scripts/validate_inp.py examples/04_cu_aimd/cu_aimd.inp

# 4) 提交（需你本机有 cp2k）
cd examples/04_cu_aimd
mpirun -n 8 cp2k.popt cu_aimd.inp 1>cu_aimd.out 2>cu_aimd.err
```

跑完读结果：

```bash
python scripts/parse_output.py examples/04_cu_aimd/cu_aimd.out
python scripts/postprocess.py energy examples/04_cu_aimd/cu_aimd-1.ener
```

## 该看什么

| 指标 | 预期 | 不对怎么办 |
|---|---|---|
| MD 是否正常推进 | 输出有 `MD| Step number` 递增 | 立即崩溃 → 查 `references/playbook.md` §1.5 |
| 温度 | 在 600 K 附近**波动**（±50 K 正常） | 单调漂移 → 恒温器参数不对 |
| 能量守恒/漂移 | 总能量无系统性漂移 | 持续上升 → TIMESTEP 太大 |
| SCF 每步是否收敛 | 每步都 `converged` | 某步不收敛 → MD 会中断，需降 TIMESTEP |

> **本示例只跑 500 步（0.25 ps）**，是为了让你几分钟内看到"能跑通"。
> **这不是生产计算**。真实 AIMD 通常需要 **10–100 ps**（即 2 万–20 万步），
> 因为 500 步根本不足以让体系达到平衡、更不足以做统计平均。

**改步数**：

```bash
# 冒烟测试（推荐先跑这个）
--steps 500

# 生产计算（按你的机时决定）
--steps 50000
```

## 学到什么

| 参数 | 含义 | 怎么选 |
|---|---|---|
| `TIMESTEP 0.5` | 时间步长（fs） | 含氢体系 0.5 fs；纯金属可到 1–2 fs |
| `ENSEMBLE NVT` | 恒定原子数/体积/温度 | 平衡体系用 NVT；要找密度用 NPT |
| `THERMOSTAT AD_LANGEVIN` | 自适应 Langevin 恒温器 | 金属传热快，Langevin 稳；也可用 `csvr` |
| `TEMPERATURE 600.0` | 目标温度（K） | Cu 熔点 1358 K，600 K 是合理的工作温度 |
| `--smear` + `--kpoints` | 金属电子结构 | **金属 AIMD 不加 smearing 几乎必然 SCF 失败** |
| `--restart-freq 100` | 每 100 步写一次重启文件 | 长跑必开；断点续算靠它 |

> **`--steps` 是本 skill 新增的参数**。模板默认是 500000 步（生产级），
> 新手直接跑会以为"卡住了"。先用 `--steps 500` 确认流程，再放大。

## 下一步

- 想看**径向分布函数 / 扩散系数** → `postprocess.py rdf`、`postprocess.py diffusion`
- 想算**振动态密度 / 红外** → `postprocess.py vacf`、`postprocess.py ir`
- 想跑**退火**（降温找结构）→ 在 inp 里取消 `ANNEALING 0.98` 注释
- 想学 AIMD 完整方法论 → `python scripts/guide.py show dynamics`（「⑦ 分子动力学」）和 `references/playbook.md` §5
