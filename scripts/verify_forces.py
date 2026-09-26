#!/usr/bin/env python3
"""力-能量交叉验证：用三个"物理不变量"去查 CP2K 算出来的东西对不对。

**这个工具解决什么问题**

CP2K 有一类缺陷：**输入完全合法、CP2K 不报任何错、SCF 照常"收敛"，但结果是错的**。
实测过的实例（2026-10 真机）：

    POISSON_SOLVER WAVELET 而分子没居中
      ⇒ 总能量差 12 Ha、O 上的力 23 a.u.（正确值 0.02）、|ΣF| 达 24.7
      ⇒ CP2K 一声不吭

本仓库其它所有护栏（`validate_inp` / `_validate_all` / 12 项套件 / 注入测试）
**对这类错误全部无效** —— 它们查的是"语法与自洽"，而这类错误是"物理算错了"。

**三个检验，各管一类（务必看清各自的边界）**

① **力-能量自洽**：`F = −dE/dx`
   把某个原子挪 ±h，中心差分 `[E(+h)−E(−h)]/(2h)` 必须等于 `−F`。
   抓的是**力与能量面是否自洽** —— 能查出不收敛的 SCF、应力/梯度实现不一致、
   基组与赝势族不匹配、约束处理错误。
   ⚠️ **它抓不到"能量面整体被扭曲、但扭曲得自洽"的错误。** 这不是理论顾虑，是实测：
   偏心 WAVELET 那个错（差 12 Ha）在本检验下**残差只有 0.067%，判通过** ——
   因为解析力仍是那个**错误**能量面的**正确**导数。**别把"检验一通过"读成"算对了"。**

② **力平衡**：`|ΣF| = 0`
   孤立体系内力之和必须为零（牛顿第三定律）。**不花额外机时** —— 参考输出里就有。
   实测：正确计算 `0.0002~0.0020`；偏心 WAVELET `24.7`。**三个数量级的安全带。**

③ **整体平移不变性**：孤立体系整体平移，能量必须一分不变
   偏心 WAVELET 破坏的正是这一条（求解器假定"单胞边界处电子密度为 0"，
   分子贴着边界时密度被削掉，一挪动能量就变）。**成本只多 1 个单点。**
   只对 `PERIODIC NONE` 有意义 —— 周期体系整体平移会改变结构本身，不是不变量。

**实测对照（CP2K 2022.1，H2O，16 核）**

| 设置 | ① 力-能量残差 | ② |SF| | ③ 平移 dE |
|---|---|---|---|
| `ANALYTIC`（正确）      | 1.5e-4              | 0.0020 | 见 README/CHANGELOG 实测 |
| 偏心 `WAVELET`（错 12 Ha）| 6.8e-3（相对 0.07%）**误判通过** | **24.7** | 同上 |

⇒ **①不能单独用。②③才是抓这类错误的主力，而且都很便宜。**

**两相式用法**（本 skill 不替用户跑计算，只生成输入与判定）

    # 1) 生成：参考 + 每个选中自由度的 ±h 位移输入 + 1 张整体平移卡
    python scripts/verify_forces.py emit cp2k.inp --ref-out cp2k.out -o vf/

    # 2) 用户把 vf/*.inp 跑完（都只要单点），再判定
    python scripts/verify_forces.py check cp2k.out vf/

**成本**：每个 checked 自由度 2 次单点，另加 1 次平移（非周期体系）。
默认只挑**受力最大的 2 个原子**（力越大有限差分信噪比越好）；`--max-atoms` / `--atoms` 可调。

**局限（写清楚，不含糊）**
  * 只支持**内联 `&COORD`**；`@INCLUDE` / `&TOPOLOGY COORD_FILE_NAME` 要先展开进卡里。
  * ①只对**单点**有意义 —— 约束优化/MD 里"力"不是纯势能梯度；
    `&FIXED_ATOMS` 约束住的原子会被自动剔除并提示。
  * ①的信噪比正比于 `|F|`：力太小时**错误的计算也可能"通过"**（`emit` 会主动告警）。
  * ②③对**带外场**（`&EFIELD`）或**周期体系**不适用，工具会跳过并说明。
"""
import argparse
import json
import math
import os
import re
import sys

# --- 控制台编码兼容层（中文 Windows/GBK 下输出不再抛异常）---
try:
    import os as _os
    import sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    for _d in (_here, _os.path.dirname(_here)):
        if _d not in _sys.path:
            _sys.path.insert(0, _d)
    import _console  # noqa: F401  导入即生效，见 scripts/_console.py
except Exception:
    pass

# 1 Bohr = 0.529177210903 Å（CODATA）。位移以 Å 给（CP2K `&COORD` 默认 Å），
# 但有限差分要换算成 Bohr 才能和 CP2K 的原子力（hartree/bohr）对齐。
BOHR_PER_ANG = 1.0 / 0.529177210903

# 灵敏度下限：待测原子上的 |F| 低于这个值时，有限差分信噪比太差，
# **一个彻底算错的设置也可能"通过"**。实测一个接近 PBE 极小点的水分子
# 所有力只有 ~0.02 a.u.，正好落在"不可信"区间 ⇒ 必须先扰动几何再测。
_F_SMALL = 0.05

# 沿用 gen_inp.py / parse_output.py 的数值正则：CP2K 输出里 `1.0E-5`、`0.171186202615E+02`
# 这类 Fortran D/E 指数都要认。
_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eEdD][-+]?\d+)?"


def _f(tok):
    """把 CP2K 的数字串转 float（兼容 Fortran 的 D 指数）。"""
    return float(tok.replace("D", "E").replace("d", "e"))


def _num_fmt(v):
    """坐标写回输入卡时的格式：固定 6 位小数，与模板一致。"""
    return "{:.6f}".format(v)


# --------------------------------------------------------------------------
# 解析参考输入卡
# --------------------------------------------------------------------------
def read_coord_block(text):
    """取出内联 `&COORD` 的行区间与逐原子数据。

    返回 ``(start, end, atoms)``：``start``/``end`` 是**行号区间**（0-based 半开），
    ``atoms`` 是 ``[{'name': 'O', 'xyz': [x, y, z]}, ...]``。

    只认形如 ``O  0.0 0.0 0.1173`` 的行；带 `@INCLUDE`、`COORD_FILE_NAME`
    或非笛卡尔写法的一律返回 ``None``（由调用方给出明确提示，**不猜**）。
    """
    lines = text.splitlines()
    start = end = None
    depth = 0
    for i, ln in enumerate(lines):
        s = ln.strip()
        if re.match(r"^&\s*COORD\b", s, re.I) and not s.upper().startswith("&END"):
            start = i
            depth = 1
            continue
        if start is not None and depth:
            if re.match(r"^&\s*END\s+COORD\b", s, re.I):
                end = i
                break
            depth += 1
    if start is None or end is None:
        return None
    atoms = []
    for ln in lines[start + 1:end]:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("&"):        # &SCALED_UPDATE 之类子段：不支持，明说
            return None
        p = s.split()
        if len(p) < 4:
            continue
        try:
            xyz = [_f(p[1]), _f(p[2]), _f(p[3])]
        except ValueError:
            return None
        atoms.append({"name": p[0], "xyz": xyz})
    if not atoms:
        return None
    return start, end, atoms


def ensure_forces_printed(text):
    """确保 CP2K 会写出原子力。

    没有 `ATOMIC FORCES` 就没有解析力可比 —— 这个检查会**静默变成空转**，
    所以必须主动补。已有 `&FORCES` 就不动（避免重复段）。
    """
    if re.search(r"&\s*FORCES\b", text, re.I):
        return text, False
    block = ("  &PRINT\n"
             "    &FORCES\n"
             "      &EACH\n"
             "        QS_SCF 0\n"
             "      &END EACH\n"
             "    &END FORCES\n"
             "  &END PRINT\n")
    new, n = re.subn(r"(?m)^(\s*)&END\s+FORCE_EVAL\b",
                     lambda m: block + m.group(0), text, count=1)
    return (new, True) if n else (text, False)


def parse_forces_from_out(path):
    """从 .out 里取最后一块 `ATOMIC FORCES in [a.u.]`。

    跨版本注意：这块的标题在 CP2K 5.x~2022.1 之间**没变**（实测 2022.1 仍是
    `ATOMIC FORCES in [a.u.]`），但仍只认这一种写法并**如实报告"没找到"**，
    不拿别的数字顶替。
    """
    if not os.path.isfile(path):
        return None, "找不到文件：{}".format(path)
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            lines = fh.read().splitlines()
    except OSError as e:
        return None, "读不了 {}：{}".format(path, e)
    blocks = []
    for i, ln in enumerate(lines):
        if "ATOMIC FORCES" in ln.upper():
            rows = []
            for j in range(i + 1, min(i + 400, len(lines))):
                s = lines[j].strip()
                if not s:
                    if rows:
                        break
                    continue
                p = s.split()
                if len(p) >= 6 and p[0].isdigit():
                    try:
                        rows.append((int(p[0]), p[2],
                                     _f(p[3]), _f(p[4]), _f(p[5])))
                    except ValueError:
                        break
                elif rows:
                    break
                if s.upper().startswith("SUM OF ATOMIC FORCES"):
                    break
            if rows:
                blocks.append(rows)
    if not blocks:
        return None, ("{} 里没有 `ATOMIC FORCES in [a.u.]` 块 —— "
                      "多半是输入没开力输出（本工具 emit 会自动补 `&FORCES`），"
                      "或作业没跑完。".format(os.path.basename(path)))
    return blocks[-1], None


def parse_energy_from_out(path):
    """取最后一条 `ENERGY| Total FORCE_EVAL`。

    ⚠️ **跨版本写法不同**（2026-10 实测）：旧版 `energy (a.u.)`、CP2K 2022.1
    `energy [a.u.]`。这里用**格式无关**的写法，只认 `ENERGY|` + `Total FORCE_EVAL` + 冒号后的数。
    """
    if not os.path.isfile(path):
        return None, "找不到文件：{}".format(path)
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            lines = fh.read().splitlines()
    except OSError as e:
        return None, "读不了 {}：{}".format(path, e)
    last = None
    for ln in lines:
        if "ENERGY|" in ln and "Total FORCE_EVAL" in ln:
            m = re.search(r":\s*(" + _NUM + r")\s*$", ln)
            if m:
                last = _f(m.group(1))
    if last is None:
        return None, "{} 里没有 `ENERGY| Total FORCE_EVAL` 记录。".format(
            os.path.basename(path))
    return last, None


# --------------------------------------------------------------------------
# emit
# --------------------------------------------------------------------------
def cmd_emit(args):
    ref = args.ref_inp
    if not os.path.isfile(ref):
        print("错误：找不到参考输入卡 {}（emit 需要一个含内联 &COORD 的 .inp）".format(ref))
        return 1
    with open(ref, encoding="utf-8", errors="ignore") as fh:
        text = fh.read()

    got = read_coord_block(text)
    if not got:
        print("错误：在 {} 里找不到可用的**内联 `&COORD`** 段。".format(ref))
        print("  本工具只支持内联笛卡尔坐标；若你的卡用 `@INCLUDE` / "
              "`&TOPOLOGY COORD_FILE_NAME` 读外部结构，")
        print("  请先把坐标展开进卡里（例如把 inc 文件内容粘进 `&COORD ... &END COORD`）。")
        return 1
    start, end, atoms = got

    # 选哪些原子：优先用参考 .out 的解析力挑"受力最大"的（信噪比最好）
    selected, how = None, ""
    fmap = {}
    if args.ref_out:
        _forces, _err = parse_forces_from_out(args.ref_out)
        if not _err:
            fmap = {r[0]: r for r in _forces}
    if args.atoms:
        try:
            selected = [int(x) for x in re.split(r"[,\s]+", args.atoms.strip()) if x]
        except ValueError:
            print("错误：--atoms 要是原子序号列表，例如 --atoms 1,3")
            return 1
        bad = [a for a in selected if a < 1 or a > len(atoms)]
        if bad:
            print("错误：--atoms 里有超出范围的序号 {}（体系只有 {} 个原子）".format(bad, len(atoms)))
            return 1
        how = "由 --atoms 指定"
    elif args.ref_out:
        if not fmap:
            print("错误：{}".format(err or "参考输出里没有可用的原子力"))
            print("  提示：--ref-out 用来挑「受力最大」的原子；若还没有参考输出，"
                  "请直接给 --atoms。")
            return 1
        rank = [(math.sqrt(f[2] ** 2 + f[3] ** 2 + f[4] ** 2), f[0])
                for f in fmap.values()]
        rank.sort(reverse=True)
        n = max(1, min(args.max_atoms, len(rank)))
        selected = [a for _m, a in rank[:n]]
        how = "按参考输出里的 |F| 取前 {} 个".format(n)
    else:
        selected = list(range(1, min(args.max_atoms, len(atoms)) + 1))
        how = "默认取前 {} 个（未给 --ref-out，无法按受力排序）".format(len(selected))

    # 约束住的原子不能测：&FIXED_ATOMS 下"力"不是纯势能梯度，恒等式不成立
    fixed = set()
    for m in re.finditer(r"&\s*FIXED_ATOMS\b(.*?)&\s*END\s+FIXED_ATOMS", text, re.I | re.S):
        body = m.group(1)
        for tok in re.findall(r"(\d+)\s*\.\.\s*(\d+)", body):
            fixed.update(range(int(tok[0]), int(tok[1]) + 1))
        for tok in re.findall(r"(?<![\d.])(\d+)(?![\d.])", re.sub(r"\d+\s*\.\.\s*\d+", " ", body)):
            fixed.add(int(tok))
    dropped = [a for a in selected if a in fixed]
    if dropped:
        print("提示：原子 {} 在 `&FIXED_ATOMS` 里，已从测试中剔除 —— "
              "约束下「力」不是纯势能梯度，F = −dE/dx 不成立。".format(dropped))
        selected = [a for a in selected if a not in fixed]
    if not selected:
        print("错误：没有可测的自由度了（全被 --atoms 或 &FIXED_ATOMS 排除）。")
        return 1

    dirs = [d for d in (args.dirs or "xyz").lower() if d in "xyz"]
    if not dirs:
        print("错误：--dirs 只能是 x/y/z 的组合，例如 --dirs xz")
        return 1
    h = args.h
    if h <= 0:
        print("错误：--h 必须为正（单位 Å）")
        return 1

    outdir = args.out
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(ref))[0]
    fixed_text, injected = ensure_forces_printed(text)

    jobs = []

    def write_one(tag, shift_atom=None, shift_dir=None, shift=None):
        """把坐标按需位移后写出一个输入卡。"""
        ls = fixed_text.splitlines()
        newc = []
        idx = 0
        for i, ln in enumerate(ls):
            if start < i < end and ln.strip() and not ln.strip().startswith("#"):
                p = ln.split()
                if len(p) >= 4 and idx == shift_atom and shift_dir is not None:
                    xyz = [_f(p[1]), _f(p[2]), _f(p[3])]
                    xyz[shift_dir] += shift
                    newc.append("{} {} {} {}".format(
                        p[0], _num_fmt(xyz[0]), _num_fmt(xyz[1]), _num_fmt(xyz[2])))
                    idx += 1
                    continue
                idx += 1
            newc.append(ln)
        txt = "\n".join(newc) + "\n"
        # PROJECT 改成唯一名，避免同目录下 replica/重启文件互相覆盖
        # （实测踩过：PROJECT 重名会覆盖 `*-r-0.out` 与 `*-RESTART.wfn`）
        txt = re.sub(r"(?m)^(\s*PROJECT\s+)\S+", r"\g<1>" + tag, txt, count=1)
        path = os.path.join(outdir, tag + ".inp")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(txt)
        jobs.append((tag, path))
        return path

    write_one("vf_ref")
    plan = []
    for a in sorted(selected):
        for d in dirs:
            di = "xyz".index(d)
            write_one("vf_a{}d{}_p".format(a, d), a - 1, di, +h)
            write_one("vf_a{}d{}_m".format(a, d), a - 1, di, -h)
            plan.append((a, d, atoms[a - 1]["name"]))

    # ---- 🔴 整体平移不变性：**这才是能抓住"边界削密度"那类错误的不变量** ----
    # 为什么必须有它（2026-10 真机实测的教训）：偏心 `POISSON_SOLVER WAVELET` 把静电能
    # 整个解错（差 12 Ha），但错得**自洽** —— 解析力仍是那个错误能量面的正确导数，
    # 于是 `F = −dE/dx` **判它通过**（实测残差只有 0.067%）。真正被它破坏的是
    # **平移不变性**：孤立体系整体平移，能量必须一分不变；而 wavelet 求解器假定
    # "单胞边界处电子密度为 0"，分子贴着边界时密度被削掉，一挪动能量就变。
    # 成本：**只多 1 个单点**。只对 `PERIODIC NONE` 有意义
    # （周期体系整体平移会改变结构本身，不是不变量）。
    nonper = bool(re.search(r"PERIODIC\s+NONE", fixed_text, re.I))
    shifted = False
    if nonper and not args.no_shift:
        _ls = fixed_text.splitlines()
        _nc = []
        for _i, _ln in enumerate(_ls):
            if start < _i < end and _ln.strip() and not _ln.strip().startswith("#"):
                _p = _ln.split()
                if len(_p) >= 4:
                    _xyz = [_f(_p[1]) + args.shift, _f(_p[2]) + args.shift,
                            _f(_p[3]) + args.shift]
                    _nc.append("{} {} {} {}".format(
                        _p[0], _num_fmt(_xyz[0]), _num_fmt(_xyz[1]), _num_fmt(_xyz[2])))
                    continue
            _nc.append(_ln)
        _txt = re.sub(r"(?m)^(\s*PROJECT\s+)\S+", r"\g<1>vf_shift",
                      "\n".join(_nc) + "\n", count=1)
        _sp = os.path.join(outdir, "vf_shift.inp")
        with open(_sp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(_txt)
        jobs.append(("vf_shift", _sp))
        shifted = True

    print("== 力-能量交叉验证 · 输入已生成 ==")
    print("  参考卡      : {}".format(ref))
    print("  输出目录    : {}".format(outdir))
    print("  原子选择    : {}（{}）".format(sorted(selected), how))
    print("  位移        : h = {} Å = {:.6f} Bohr，方向 {}".format(
        h, h * BOHR_PER_ANG, "".join(dirs)))
    print("  待测自由度  : {} 个 → {} 个单点作业（含参考共 {} 个）".format(
        len(plan), len(plan) * 2 + 1, len(plan) * 2 + 1))
    # ---- 🔴 灵敏度预警：力太小的话，这个检查会**给出虚假的安全感** ----
    # 为什么必须有这一条：有限差分的信噪比正比于 |F|。实测一个已接近 PBE 极小点的
    # 水分子，所有原子力只有 ~0.02 a.u.；而"完全算错"能造成的残差同样是这个量级
    # ⇒ 容差若设成 0.02，**一个彻底错的计算也会"通过"**。必须先把力做大再测。
    if fmap:
        fmags = [(math.sqrt(fmap[a][2] ** 2 + fmap[a][3] ** 2 + fmap[a][4] ** 2), a)
                 for a in selected if a in fmap]
        if fmags:
            mx, ma = max(fmags)
            if mx < _F_SMALL:
                print()
                print("  ⚠️ **灵敏度不足**：待测原子里最大的 |F| 只有 {:.4f} a.u."
                      "（第 {} 号原子）。".format(mx, ma))
                print("     有限差分的信噪比正比于 |F|；力这么小的时候，"
                      "**一个完全算错的设置也可能「通过」**。")
                print("     建议：先把几何明显扰动再测 —— 例如把一根键拉长 0.1 Å，"
                      "让 |F| 达到 0.1 a.u. 量级，")
                print("     或者显式 `--atoms` 指定某个受力大的原子。")
    else:
        print("  （未给 --ref-out ⇒ 无法按受力排序，也无法评估灵敏度；"
              "建议补上参考输出）")
    if injected:
        print("  已自动补 `&FORCE_EVAL/&PRINT/&FORCES`（原卡没有力输出，"
              "不补的话这个检查会静默空转）")
    else:
        print("  原卡已有 `&FORCES`，未改动")
    print("\n  下一步：把这些卡跑成单点（都很快），然后判定：")
    # 注意 `${{...}}` 的双花括号：这是给 shell 的，`{{}}` 才是 `.format()` 想要的字面花括号
    print("    cd {d} && for f in vf_*.inp; do cp2k -i $f -o ${{f%.inp}}.out; done"
          .format(d=outdir))
    print("    python scripts/verify_forces.py check {r} {d}".format(
        r=args.ref_out or "<参考卡对应的 .out>", d=outdir))
    print("\n  ⚠️ 恒等式 F = −dE/dx 只在**单点**上成立。若参考卡是 GEO_OPT/MD，")
    print("     请改成对应几何的 ENERGY_FORCE 单点再测。")
    if args.json:
        print(json.dumps({"outdir": outdir, "atoms": selected, "dirs": dirs,
                          "h_angstrom": h, "n_jobs": len(jobs),
                          "injected_forces_print": injected}, ensure_ascii=False))
    return 0


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------
def parse_sum_force(path):
    """取输出里最后一条 `SUM OF ATOMIC FORCES … |ΣF|` 的模。

    **这是"边界削密度"那类错误的直接症状**：孤立体系内力之和必须为 0（牛顿第三定律）。
    实测偏心 WAVELET 给 24.7 a.u.，而正确计算是 0.0002~0.0020。取它**不花任何额外机时**
    —— 参考输出里本来就有。
    """
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None
    last = None
    for ln in lines:
        if "SUM OF ATOMIC FORCES" in ln:
            nums = re.findall(_NUM, ln)
            if len(nums) >= 4:
                try:
                    last = abs(_f(nums[3]))
                except ValueError:
                    pass
    return last


def cmd_check(args):
    ref_out = args.ref_out
    outdir = args.outdir
    if not os.path.isfile(ref_out):
        print("错误：找不到参考输出 {}".format(ref_out))
        return 1
    if not os.path.isdir(outdir):
        print("错误：找不到目录 {}（应该先跑 emit 生成、再把 .inp 跑成 .out）".format(outdir))
        return 1

    forces, err = parse_forces_from_out(ref_out)
    if err:
        print("错误：{}".format(err))
        return 1
    fmap = {r[0]: r for r in forces}

    # 找出所有 vf_a<A>d<D>_{p,m}.out
    pat = re.compile(r"^vf_a(\d+)d([xyz])_([pm])\.out$")
    found = {}
    for fn in sorted(os.listdir(outdir)):
        m = pat.match(fn)
        if not m:
            continue
        found.setdefault((int(m.group(1)), m.group(2)), {})[m.group(3)] = os.path.join(outdir, fn)
    if not found:
        print("错误：在 {} 里没找到 `vf_a<原子号>d<x|y|z>_<p|m>.out`。".format(outdir))
        print("  请先跑 emit，再把生成的 .inp 都跑成同名 .out。")
        return 1

    h_bohr = args.h * BOHR_PER_ANG
    rows, missing = [], []
    for (a, d) in sorted(found):
        pair = found[(a, d)]
        if "p" not in pair or "m" not in pair:
            missing.append("vf_a{}d{}（缺 {}）".format(a, d, "+h" if "p" not in pair else "−h"))
            continue
        ep, e1 = parse_energy_from_out(pair["p"])
        em, e2 = parse_energy_from_out(pair["m"])
        if e1 or e2:
            missing.append("vf_a{}d{}：{}".format(a, d, e1 or e2))
            continue
        if a not in fmap:
            missing.append("vf_a{}d{}：参考输出里没有第 {} 个原子的力".format(a, d, a))
            continue
        g_fd = (ep - em) / (2.0 * h_bohr)         # ha/bohr
        di = "xyz".index(d)
        f_an = fmap[a][2 + di]                     # ha/bohr
        # 判据：g ≈ −F
        resid = g_fd + f_an
        # **相对 + 绝对混合判据**（为什么不能只用绝对容差，见 cmd_check 里的长注释）
        scale = max(abs(f_an), abs(g_fd))
        limit = max(args.tol, args.tol_rel * scale)
        rows.append({"atom": a, "elem": fmap[a][1], "dir": d,
                     "F_analytic": f_an, "grad_fd": g_fd,
                     "residual": resid, "limit": limit,
                     "rel": (abs(resid) / scale) if scale > 0 else None,
                     "ok": abs(resid) <= limit})

    print("== 力-能量交叉验证 · 判定 ==")
    print("  参考输出 : {}".format(ref_out))
    print("  位移 h   : {} Å = {:.6f} Bohr（中心差分）".format(args.h, h_bohr))
    print("  恒等式   : F = −dE/dx  ⇒  残差 = dE/dx + F 应 ≈ 0")
    print()
    if not rows:
        print("没有可判定的自由度。")
        for m in missing[:10]:
            print("  · {}".format(m))
        return 1

    print("  {:<4} {:<4} {:>13} {:>13} {:>12} {:>10} {:>5}".format(
        "原子", "方向", "F(解析)", "dE/dx(差分)", "残差", "容差", "判定"))
    print("  " + "-" * 72)
    worst_ratio, n_bad = 0.0, 0
    for r in rows:
        print("  {:<4} {:<4} {:>13.6f} {:>13.6f} {:>12.6f} {:>10.2e} {:>5}".format(
            "{}{}".format(r["elem"], r["atom"]), r["dir"],
            r["F_analytic"], r["grad_fd"], r["residual"], r["limit"],
            "OK" if r["ok"] else "FAIL"))
        if not r["ok"]:
            n_bad += 1
            worst_ratio = max(worst_ratio, abs(r["residual"]) / max(r["limit"], 1e-30))

    print()
    for m in missing:
        print("  ⚠️ 跳过：{}".format(m))

    # ---- 🔴 检验二：ΣF = 0（免费，读参考输出即可）----
    sf = parse_sum_force(ref_out)
    sf_ok = None
    if sf is not None:
        sf_ok = sf <= args.tol_sumforce
        print("  {} 检验二 · 力平衡：|ΣF| = {:.4f} a.u.（上限 {:.2f}）{}".format(
            "✅" if sf_ok else "❌", sf, args.tol_sumforce,
            "" if sf_ok else " ← **孤立体系必须为 0**"))

    # ---- 🔴 检验三：整体平移不变性（这才是抓"边界削密度"的关键）----
    sh_ok, dE_shift, e_ref, e_shift = None, None, None, None
    sp = os.path.join(outdir, "vf_shift.out")
    if os.path.isfile(sp):
        e_ref, _e1 = parse_energy_from_out(ref_out)
        e_shift, _e2 = parse_energy_from_out(sp)
        if e_ref is not None and e_shift is not None:
            dE_shift = e_shift - e_ref
            lim = max(args.tol_shift, args.tol_shift_rel * abs(e_ref))
            sh_ok = abs(dE_shift) <= lim
            print("  {} 检验三 · 平移不变性：整体平移后 ΔE = {:+.6f} a.u."
                  "（上限 {:.2e}）{}".format(
                      "✅" if sh_ok else "❌", dE_shift, lim,
                      "" if sh_ok else " ← **孤立体系整体平移，能量必须不变**"))
    else:
        print("  · 检验三 · 平移不变性：未找到 `vf_shift.out`（"
              "要么卡是周期体系、要么用了 `--no-shift`、要么还没跑）—— 跳过")

    # ---- 总判定 ----
    resid_bad = [r for r in rows if not r["ok"]]
    print()
    if resid_bad or sf_ok is False or sh_ok is False:
        print("  ❌ 不通过。")
        if resid_bad:
            print("     · 检验一（力-能量自洽）失败 {} 个自由度（最坏超 {:.0f} 倍）"
                  .format(len(resid_bad), worst_ratio))
        if sf_ok is False:
            print("     · 检验二（力平衡 ΣF=0）失败：|ΣF| = {:.4f} a.u.".format(sf))
        if sh_ok is False:
            print("     · 检验三（平移不变性）失败：ΔE = {:+.6f} a.u.".format(dE_shift))
        print()
        print("     这不是数值噪声。按下面顺序排查：")
        print("       ① **静电解**（最常见）：`POISSON_SOLVER WAVELET` 要求分子居于单胞中心")
        print("          —— 官方 T24 §3.4「确保单胞的边界处电子密度为 0」。")
        print("          实测偏心时能量差 12 Ha、|ΣF| 达 24.7 a.u.，而 CP2K **不报任何错**。")
        print("          修法：加 `&SUBSYS/&TOPOLOGY/&CENTER_COORDINATES`，或改用 ANALYTIC/MT。")
        print("       ② **`&CELL` 与 `&POISSON` 的 `PERIODIC` 不一致**（官方：两者应当一致）。")
        print("       ③ **基组/赝势不匹配**（给某元素配了别族的 POTENTIAL）。")
        print("       ④ **`CUTOFF`/`REL_CUTOFF` 太粗**：提到 400–600 再看残差是否变小。")
        print("       ⑤ **SCF 没真收敛**：把 `EPS_SCF` 收到 1e-7 复测。")
        rc = 1
    else:
        print("  ✅ 通过：{} 个自由度自洽{}。".format(
            len(rows), "、|ΣF| 正常" if sf_ok else ""))
        print("     ⇒ 解析力与能量梯度一致{}。**但这只证明「自洽」，不证明「算对了」**".format(
            "、且满足平移不变性" if sh_ok else ""))
        print("       —— 见本工具 docstring 里那段实测教训。")
        rc = 0

    if args.json:
        print()
        print(json.dumps({"ref_out": ref_out, "h_angstrom": args.h,
                          "pass": rc == 0,
                          "sum_force": sf, "sum_force_ok": sf_ok,
                          "shift_dE": dE_shift, "shift_ok": sh_ok,
                          "rows": rows, "skipped": missing},
                         ensure_ascii=False, indent=2))
    return rc


# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="verify_forces.py",
        description="力-能量交叉验证：用中心差分 dE/dx 验 CP2K 报的解析力 F（判据 F = −dE/dx）。",
        epilog="例如：python scripts/verify_forces.py emit cp2k.inp --ref-out cp2k.out -o vf/ "
               "&& python scripts/verify_forces.py check cp2k.out vf/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd")

    e = sub.add_parser("emit", help="生成参考 + ±h 位移的单点输入卡")
    e.add_argument("ref_inp", nargs="?", help="参考输入卡（需含内联 &COORD）")
    e.add_argument("--ref-out", default=None,
                   help="参考输出（可选；给了就按 |F| 挑受力最大的原子，信噪比最好）")
    e.add_argument("-o", "--out", default="vf", help="输出目录（默认 vf/）")
    e.add_argument("--atoms", default=None, help="手动指定原子序号，如 1,3（1-based）")
    e.add_argument("--max-atoms", type=int, default=2,
                   help="自动挑选时最多测几个原子（默认 2）")
    e.add_argument("--dirs", default="xyz", help="测哪些方向，默认 xyz")
    e.add_argument("--h", type=float, default=0.01, help="位移步长 Å（默认 0.01）")
    e.add_argument("--shift", type=float, default=0.5,
                   help="整体平移量 Å（默认 0.5）；用于**平移不变性**检验，"
                        "只对 `PERIODIC NONE` 生成")
    e.add_argument("--no-shift", action="store_true",
                   help="不生成整体平移的对照卡（默认会生成 —— 它是抓"
                        "「边界削密度」那类错误的关键不变量）")
    e.add_argument("--json", action="store_true", help="额外输出 JSON 摘要")

    c = sub.add_parser("check", help="比对 dE/dx 与解析力并给判定")
    c.add_argument("ref_out", nargs="?", help="参考输出（提供解析力）")
    c.add_argument("outdir", nargs="?", help="emit 的输出目录（内含 vf_*.out）")
    c.add_argument("--h", type=float, default=0.01, help="与 emit 相同的 h（Å）")
    c.add_argument("--tol", type=float, default=1e-3,
                   help="残差**绝对下限** a.u.（默认 1e-3）")
    c.add_argument("--tol-rel", type=float, default=0.02,
                   help="残差**相对**上限（默认 2%%×|F|）")
    c.add_argument("--tol-sumforce", type=float, default=0.05,
                   help="|ΣF| 上限 a.u.（默认 0.05；孤立体系必须为 0，"
                        "合法算例实测 0.0002~0.0020）")
    # 阈值**按实测标定**（CP2K 2022.1，H2O，平移 0.5 Å）：
    #   正确算例（ANALYTIC）      ΔE = 1.0e-4 a.u.  ← ANALYTIC 求解器本身有这点盒依赖
    #   偏心 WAVELET（错 12 Ha）  ΔE = 1.22e+1 a.u.
    # 两者差 **5 个数量级**，取 1e-2 作绝对下限：比"正确"高 100 倍、
    # 比"错误"低 1000 倍，中间是极宽的安全带，不会误报也不会漏报。
    c.add_argument("--tol-shift", type=float, default=1e-2,
                   help="整体平移后 |ΔE| 的**绝对**上限 a.u.（默认 1e-2；实测正确约 1e-4、"
                        "偏心 WAVELET 约 1.2e+1）")
    c.add_argument("--tol-shift-rel", type=float, default=1e-4,
                   help="整体平移后 |ΔE| 的**相对**上限（默认 1e-4×|E|）")
    c.add_argument("--json", action="store_true", help="额外输出 JSON 明细")

    args = ap.parse_args(argv)

    if not args.cmd:
        ap.print_help()
        print("\n错误：请给出子命令 emit 或 check，例如：")
        print("  python scripts/verify_forces.py emit cp2k.inp --ref-out cp2k.out -o vf/")
        return 2

    if args.cmd == "emit":
        if not args.ref_inp:
            e.print_help()
            print("\n错误：emit 需要参考输入卡路径。")
            return 2
        return cmd_emit(args)
    if not args.ref_out or not args.outdir:
        c.print_help()
        print("\n错误：check 需要 <参考输出> 与 <目录> 两个参数。")
        return 2
    return cmd_check(args)


if __name__ == "__main__":
    sys.exit(main())
