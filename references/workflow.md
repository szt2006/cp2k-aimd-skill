# CP2K 项目阶段向导（workflow）

> **这不是一个"自动跑命令的工作流"。** 它是一个陪你走完整项目的辅助：
> 在**每个阶段**告诉你——现在该做什么、为什么、用什么命令、做完长什么样、掉进哪些坑。
> 真正的计算化学是"具体问题具体分析、按结果不断调整"的过程，本向导的定位是**把课题组的经验固化成可随时调用的判断**，而不是替你盲点"运行"。

---

## 怎么用

```bash
python scripts/guide.py list                       # 看全部 11 个阶段
python scripts/guide.py show optimize              # 展开"几何优化"阶段的完整指引
python scripts/guide.py scan /path/to/project      # 扫描你的项目目录，推断卡在哪、下一步做什么
python scripts/guide.py next /path/to/project      # 只给下一步行动（scan 的精简版）
```

`scan` / `next` 会读你目录里的真实文件（`.inp` / `.out` / `*-pos-1.xyz` 轨迹 / `*.pdos` / `*.cube` / `ACF.dat` / `HILLS` / `fes.dat`），
据此判断你**已经做完了哪些阶段、当前在哪个阶段、下一步最该做什么**——这是它和"空壳工作流"最大的区别。

### 一个项目的标准陪跑路径

1. 开新项目 → `guide.py show define` 想清楚要算什么。
2. 结构就绪 → `guide.py show decide` + 跑 `recommend.py` 定参数。
3. 生成 `.inp` 后 → `guide.py scan .` 确认"输入已生成、下一步去提交"。
4. 跑完 → `guide.py scan .` 看它提示你做收敛检查 / 后处理 / 诊断。
5. 每一步都对照 `show <stage>` 的"决策点"和"常见坑"，别跳过收敛测试、别拿未收敛当结果。

---

## 11 个阶段（顺序即项目推进顺序）

### ① 立项与问题定义
**目标**：把科学问题翻译成可计算的任务。
- **该做的**：明确要算什么量（吸附能 / 反应能垒 / 扩散系数 / IR 谱 / 电荷转移 / 表面重构）；选定 `RUN_TYPE`；判断化学环境（气相 / 表面 slab / 块体 / 溶液）；粗估规模（决定能否上杂化泛函）。
- **决策点**：静态优化 vs AIMD（表面反应、有限温、扩散必须有限温动力学）；是否需要反应路径（NEB / 元动力学）。
- **坑**：任务类型选错导致白算；用 0 K 优化外推有限温结论。
- **命令**：`recommend.py --elements ... --goal <energy|geo_opt|md|ts> --periodic <none|xy|xyz>`（先用它梳理方法）。

### ② 体系构建（初始结构）
**目标**：干净、无重叠、真空层/晶胞合理的初始结构。
- **该做的**：获取初始结构（实验 CIF / Materials Project / 自己搭 / PACKMOL 建溶液盒——本 skill 不生成溶剂盒）；表面 slab 切表面 + 加真空层（≥15 Å）+ 固定底层 + 判断终止面；块体确认晶格；吸附质放合理初位。
- **决策点**：真空层厚度；固定哪些原子；表面超胞大小；吸附位点初猜。
- **坑**：真空层不足→镜像相互作用；底层未固定→slab 漂移；原子重叠→发散/怪结构。
- **命令**：`gen_inp.py --type <...> --topology POSCAR.cif --topology-format cif`（从 CIF 读）/ `--xyz init.xyz`。

### ③ 计算方法与参数决策（安全起点）
**目标**：选定泛函/基组/赭势/自旋/色散/k点/SMEAR/CUTOFF，得到可跑的"安全起点"。
- **该做的**：跑 `recommend.py` 拿逐项推荐 + 理由 + 可直接执行的 `gen_inp` 命令；逐项确认泛函阶梯、UKS、DFT-D3、k 点、SMEAR、DFT+U；确认赝势/基组（轻元素 GTH-PADE、过渡金属 GTH-PBE，已按元素查好 q）。
- **决策点**：
  - 泛函阶梯：PBE（默认，筛选/结构）→ TPSS/SCAN（吸附/表面反应更准，~1.5-2x）→ HSE06/B3LYP（反应能/带隙最准，**必须 +ADMM**）。
  - DFT+U：含 Fe/Ti/Co/Ni/Mn/Cu/Cr/Ce 等 d 电子过渡金属的氧化物/硫化物——几乎必加，否则电子结构错（`recommend.py` 会自动建议，用 `--kinds 'Fe:...:U=3'` 发射 `&DFT_PLUS_U`）。
  - SMEAR：任何金属/窄带隙体系必加 FERMI_DIRAC。
- **坑**：金属不加 SMEAR→SCF 不收敛；TM 氧化物不加 DFT+U→能带/d 带中心错；大体系直接 HSE06（无 ADMM）→成本上天。
- **命令**：`recommend.py --elements Au O --goal geo_opt --periodic xy --multiplicity 3 --vdw auto --accuracy balanced`。

### ④ 收敛性测试
**目标**：确认 CUTOFF / REL_CUTOFF / k 点密度 / SMEAR 宽度足够（结果不再随参数明显变化）。
- **该做的**：CUTOFF 扫描（300→400→500 Ry），能量变化 < 1 meV/atom 即收敛；块体 k 点密度扫描（4³→6³→8³）；金属 SMEAR 宽度扫描（100→300→500 K）；REL_CUTOFF 一般 60 足够，不必扫。
- **决策点**：选"性价比最高"的收敛参数，不是无限大。
- **坑**：跳过收敛测试→结果不可信/不可比；CUTOFF 太低→能量漂移、几何/频率错。
- **命令**：`gen_inp.py ... --cutoff 300/400/500` 各跑一遍，`parse_output.py cp2k.out` 取能量做收敛曲线。

### ⑤ 几何/晶胞优化
**目标**：得到能量最低、合理的结构（局域极小点）。
- **该做的**：分子/表面用 `GEO_OPT`，块体/高压用 `CELL_OPT`；检查收敛（MAX_FORCE 达标、几何趋稳、无虚频——用 `VIBRATIONAL_ANALYSIS` 验证极小点）；吸附体系确认吸附质没飞走、键长合理；多初位确认不是错误极小。
- **决策点**：OPTIMIZER（块体 BFGS、slab/缺陷 LBFGS 或 CG）；是否 CELL_OPT；固定哪些原子。
- **坑**：未收敛就拿结构用→后续全错；优化到错误极小点；虚频未检查→把鞍点当极小点。
- **命令**：`gen_inp.py --type geo_opt [--optimizer lbfgs] [--fixed-atoms '1..54']`；`gen_inp.py --type cell_opt`；`diagnose.py cp2k.out`。

### ⑥ 静态计算与电子结构性质
**目标**：在优化结构上算电子结构性质，直接回答科学问题。
- **该做的**：在优化结构上跑单点，开 `--properties`；PDOS 看 d 带中心/带隙/元素贡献（催化关键）；布居分析（MULLIKEN/LOWDIN/HIRSHFELD）看电荷转移；Bader（需 cube + `bader` 二进制）、cube（密度/ELF）看成键/孤对；含 DFT+U 体系确认自旋态/磁矩正确。
- **决策点**：用哪个性质回答你的问题（吸附强度→d 带中心/电荷转移；成键→ELF/cube；离子性→Bader）。
- **坑**：在没优化的结构上算性质→无意义；PDOS 费米能级定错→能级对齐错（`postprocess.py pdos` 自动探测费米面）。
- **命令**：`gen_inp.py --type static --properties pdos charges cube [--ldos-list '1..26']`；`postprocess.py pdos`；`postprocess.py bader`。

### ⑦ 分子动力学（AIMD / MD）
**目标**：在有限温下观察体系真实行为（是否反应、如何扩散、结构演化）。
- **该做的**：选系综（NVT 常用 / NPT 看体积涨落）、恒温器（CSVR/Nose/LANGEVIN，表面催化 LANGEVIN 更稳）；TIMESTEP 0.5 fs；分平衡段 + 采样段；开 `--restart-freq` 续算；打印轨迹 + 速度（默认开 `&VELOCITIES`）；跑后查能量/温度漂移。
- **决策点**：温度/恒温器/是否 NPT/步长；采样长度（扩散需足够长 MSD 线性区）。
- **坑**：TIMESTEP 太大→爆炸；未平衡就采样→统计偏；温度/能量漂移→步长过大或未收敛。
- **命令**：`gen_inp.py --type aimd_md --thermostat langevin --ensemble nvt --restart-freq 1000 --steps 50000`；`diagnose.py cp2k.out`。

### ⑧ 反应路径（NEB / 元动力学）
**目标**：算反应能垒（NEB）或自由能面（元动力学 FES）。
- **该做的**：NEB（CI-NEB，初末态都优化好，中间副本插值，K_SPRING 0.02-0.08，收敛后验证过渡态有且仅有 1 个虚频）；元动力学（选 CV——DISTANCE 已支持，COORDINATION 需手加 `&COLVAR`，墙约束，NT_HILLS，后用 CP2K `graph` 重建 FES）。
- **决策点**：NEB vs 元动力学（离散已知路径→NEB；连续 CV、探索未知路径→元动力学）；CV 选择（元动力学最关键）。
- **坑**：初末态未优化→能垒错；NEB 收敛判据太松→过渡态不准；元动力学 `graph -ndim` 必须 = 真实 CV 数，否则 FES 重建错误。
- **命令**：`gen_inp.py --type neb --xyz-replicas ./0.xyz ... --optimize-band DIIS --k-spring 0.05`；`gen_inp.py --type metadyn`；`postprocess.py fes`。

### ⑨ 后处理与动力学分析
**目标**：从轨迹/输出算出物理量（RDF / MSD / 扩散 / VACF / IR / 键角 / PDOS / Bader / FES）。
- **该做的**：结构→`rdf`/`cn`/`bond`/`angle`；动力学→`msd`→`diffusion`、`vacf`→`ir`/`power`；电子→`pdos`/`bader`；自由能→`fes`。
- **决策点**：按科学问题选量（扩散→MSD；振动/IR→VACF；局域结构→RDF/CN）。
- **坑**：MSD 没解包裹→错（postprocess 已处理）；RDF 没给晶胞→归一化错（`--cell` 或自动从 `.out` 解析）；IR 无速度文件→用位置差分近似，须知高频段偏差。
- **命令**：`postprocess.py rdf/msd/diffusion/vacf/ir/pdos/bader/fes`（全部出 `.png` + `.csv`）。详见 `postprocess.md`。

### ⑩ 结果判读与诊断
**目标**：判断结果可信、发现异常、决定下一步（收工 or 回去调参重算）。
- **该做的**：`diagnose.py` 自动看 SCF/几何/能量漂移/虚频/ABORT，给"改哪行"建议；对照 `decide.md` 结果判读对照表；问自己：收敛了吗？物理上合理吗？和文献/化学直觉一致吗？
- **决策点**：结果可信→进 report；未收敛/异常→回到 optimize/static/dynamics 调参重算（闭环迭代）。
- **坑**：忽视警告、把未收敛当结果；只看能量不看结构/性质是否合理。
- **命令**：`diagnose.py cp2k.out`；`parse_output.py cp2k.out`。

### ⑪ 总结与报告
**目标**：汇总数据、回答科学问题、形成可交付/可发表结论。
- **该做的**：整理能量/结构/谱图/电荷，回答立项时的问题；复查方法描述完整（泛函/基组/参数/U值/k点/温度）；出最终图。
- **坑**：方法描述不全→别人无法复现；只给图不给误差/收敛信息。
- **命令**：`postprocess.py <子命令>`（复出最终图）。

---

## 与其他脚本的关系

| 脚本 | 在流程里的角色 |
|------|----------------|
| `recommend.py` | ③ 决策阶段：体系 → 有理由的参数推荐 + 起步阶梯 + 生成命令 |
| `gen_inp.py` | ②/③/⑤/⑥/⑦/⑧：由模板生成 `.inp`（全部进阶开关） |
| `validate_inp.py` / `_validate_all.py` | ③ 之后：输入语法校验（零依赖 / 权威 CP2K 解析器） |
| `parse_output.py` | ④/⑤/⑦/⑩：取能量/受力/收敛 |
| `diagnose.py` | ⑤/⑦/⑩：诊断问题、给改哪行的建议 |
| `postprocess.py` | ⑥/⑧/⑨：后处理引擎（RDF/MSD/扩散/VACF/IR/PDOS/Bader/FES） |
| `guide.py` | **总入口**：每个阶段告诉你该做什么、现在卡在哪 |

> 闭环不是直线的——⑩ 诊断常常把你要打回 ⑤/⑥/⑦ 调参重算。这正是计算化学"按结果不断调整"的常态，`guide.py scan` 会如实反映你回到哪个阶段。
