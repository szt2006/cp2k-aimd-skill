# 示例工程 · 五个能直接跑通的最小案例

这里是**开箱即用**的示例。每个目录里都有：
- 一份**已经校验通过**的 `.inp` 输入文件
- 坐标文件（`.xyz`）
- 一份 `README.md`，讲清「怎么跑、该看什么、学到什么、下一步」

**第一次用这个 skill，从这里开始。**

---

## 先做这一步

```bash
python scripts/doctor.py
```

它会告诉你：Python 版本够不够、脚本齐不齐、缺哪些依赖、下一步该干什么。
看到 `结论：核心功能可用 ✓` 就可以往下走了。

---

## 五个示例一览

| # | 目录 | 体系 | 难度 | 学到什么 | 大概耗时 |
|---|---|---|---|---|---|
| 01 | [`01_si_bulk_static`](01_si_bulk_static/) | Si 块体 8 原子 | ★☆☆☆☆ | 最小闭环：生成 → 校验 → 提交 → 读结果 | 几分钟 |
| 02 | [`02_co_molecule_vib`](02_co_molecule_vib/) | CO 分子 | ★★☆☆☆ | 非周期（分子）计算 + 振动频率 | 十几分钟 |
| 03 | [`03_au_slab_ads`](03_au_slab_ads/) | Au(100) slab + O | ★★★☆☆ | 表面吸附：真空层 / k 点 / smearing / 色散 | 数小时 |
| 04 | [`04_cu_aimd`](04_cu_aimd/) | Cu 金属 4 原子 | ★★★☆☆ | AIMD：系综 / 时间步长 / 恒温器 | 几十分钟（500 步） |
| 05 | [`05_metadyn_fes`](05_metadyn_fes/) | TiO₂ 分子 | ★★★★☆ | 增强采样：COLVAR / METADYN / DFT+U | 数小时（2000 步） |

> 耗时按单机 8 核估算，实际取决于你的硬件与并行规模。

---

## 推荐顺序

**完全新手**：01 → 02 → 03 → 04 → 05

**只想跑通流程**：只做 01，把「生成 → 校验 → 提交 → 读结果」这条链路走一遍。

**有明确目标**：

| 你想做的事 | 直接看 |
|---|---|
| 算一个分子/团簇的能量 | 02（把 `--type vib` 改成 `--type static`） |
| 算表面吸附能 | 03 |
| 算扩散系数 / RDF | 04 |
| 找反应路径 / 自由能面 | 05（或看 `--type neb`，见 `references/decide.md` §17） |
| 算能带 / PDOS | 01（加 `--kpoints` 和 `--properties pdos`） |

---

## 不想手写命令行？

用交互式向导，它会一步步问你：

```bash
python scripts/wizard.py
```

或者用「思考层」拿推荐参数，再复制它的生成命令：

```bash
python scripts/recommend.py --elements Au O --goal geo_opt --periodic xy
```

---

## 每个示例的通用四步

```bash
# 1) 环境自检
python scripts/doctor.py

# 2) 生成输入（示例已生成好，这步是演示来源）
python scripts/gen_inp.py ... -o <目录>/<名字>.inp

# 3) 校验语法（提交前必做）
python scripts/validate_inp.py <目录>/<名字>.inp

# 4) 提交（需你本机有 cp2k）
cd <目录> && mpirun -n 8 cp2k.popt <名字>.inp 1><名字>.out 2><名字>.err
```

跑完统一用这两个脚本读结果：

```bash
python scripts/parse_output.py <目录>/<名字>.out    # 提取能量/力/收敛信息
python scripts/diagnose.py    <目录>/<名字>.out    # 诊断问题并给处方
```

---

## 重要提醒

- 这些示例的**参数是为了演示流程**，不是针对具体科学问题的最优参数。
  真实研究请用 `recommend.py` 重新推荐，并做收敛性测试（`guide.py show converge`）。
- 04 和 05 的**步数被刻意调小**（`--steps 500` / `--steps 2000`），
  只为让你几分钟内看到"能跑通"。**生产计算请放大到 5 万步以上**。
- 提交前**一定**先跑 `validate_inp.py`。它能抓住大部分语法错误，
  省掉排队几小时后才发现输错关键字的痛苦。

---

## 遇到问题

| 现象 | 先看 |
|---|---|
| 脚本报错 / 缺依赖 | 重跑 `python scripts/doctor.py` |
| CP2K 不收敛 | `references/playbook.md` §1（症状 → 处方） |
| 不知道怎么配参数 | `python scripts/wizard.py` 或 `recommend.py` |
| 不知道该做什么 | `python scripts/guide.py scan .` |
| 结果看不懂 | `python scripts/diagnose.py <out>` |
