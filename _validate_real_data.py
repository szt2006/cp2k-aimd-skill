#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""真实数据回归：用「庚子计算整理」的 5 个真实生产算例当锚点，锁住本轮修掉的 bug。

**为什么必须有这个 harness**：本轮所有最有价值的缺陷，**没有一个**是合成数据
harness 抓到的 ——

| 缺陷 | 合成 harness 为什么漏掉 |
|---|---|
| RDF 归一化写在帧循环体内 | 锚点是**单帧**随机气体，单帧只除一次正好正确 |
| `&MULLIKEN` 被误报成 typo | 合成用例从不写 `&MULLIKEN` |
| `BASIS_SET_FILE_NAME` 只比全路径 | 合成用例写裸文件名，真实卡写 `${DATAPATH}/BASIS_MOLOPT` |
| `parse_output.py` 找 `Max. force` | 合成用例不产真实收敛表（真实输出里 `Max. force` **0 次**） |
| `diagnose.py` 不识别作业被 kill | 合成用例都是"正常结束" |
| `energy` 静默吃下轨迹文件 | 没人拿 `.xyz` 去喂 `energy` |

所以这个 harness 的作用是**把真实数据钉成回归基线**。真实数据是 15 MB 的 `.out`
与 2535 帧轨迹，**不入库**（见 `cases/README.md` 的打包约定），因此本脚本在
**源目录不可用时如实 SKIP**，绝不假装跑过。

用法：
    python _validate_real_data.py              # 用默认/环境变量指定的源目录
    python _validate_real_data.py --src <目录>
    python _validate_real_data.py --json

源目录也可用环境变量 `CP2K_CASE_SRC` 指定。退出码：0 全通过（或 SKIP），1 有失败。
"""
import argparse
import glob
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
try:
    import _console  # noqa: F401  中文 Windows(GBK) 下输出符号不再抛异常
except Exception:
    pass

PY = sys.executable
PP = os.path.join(HERE, "scripts", "postprocess.py")
PO = os.path.join(HERE, "scripts", "parse_output.py")
DG = os.path.join(HERE, "scripts", "diagnose.py")
VI = os.path.join(HERE, "scripts", "validate_inp.py")

DEFAULT_SRC = r"D:\cp2k-aimd\study\庚子计算整理-cp2k资料-持续更新"
CASES = os.path.join(HERE, "references", "h_tutorials", "cases")

# 真实数据里实测到的、**钉死**的期望值（改这些数字前先确认真实文件没变）
EXP_OPT_ENERGIES = 172            # opt 的 ENERGY| 记录数
EXP_OPT_MAX_GRAD = 4.539073e-4    # 收敛表最后一行的 Max. gradient
EXP_AIMD_STEPS_DONE = 2534        # 被 kill 时实际跑到的步数
EXP_AIMD_STEPS_REQ = 5000         # 输入请求的步数
EXP_AIMD_DONE_PCT = 50.68         # 完成度 %
EXP_RDF_CN = 1.0000               # H 恰好连 1 个 O ⇒ r≤1.3 Å 的配位数
RDF_CELL = "10.242489 0 0 0 10.242489 0 0 0 23.0"
# 真实 AIMD 的温度层实测值（NVT / Nose-Hoover-Chains，目标 300 K，2534 步）
EXP_AIMD_ENSEMBLE = "NVT"
EXP_AIMD_THERMOSTAT = "Nose-Hoover-Chains"
EXP_AIMD_T_TARGET = 300.0
EXP_AIMD_T_MIN = 179.3            # 瞬时温度最低
EXP_AIMD_T_MAX = 369.7            # 瞬时温度最高（= 目标的 1.23 倍）
EXP_AIMD_T_END_AVG = 290.8        # 末段滑动平均（偏目标 3.1%）
EXP_AIMD_DRIFT = 0.797            # ENERGY DRIFT PER ATOM 滑动平均 [K/原子]
# 真实交付文件的组成（数元素得到；用于定案课程口述的"晶面/水分子数"两说）
#   opt  = 48 Cu + 46 H2O = 186 原子  ← 与讲义 L2.txt P61 题注 "Cu(100) + 46H2O" 吻合
#   aimd = 48 Cu + 28 H2O = 132 原子  ← AIMD 实跑文件（讲师口述"30 个"是演示口误）
# 48 Cu = 4×4 × 3 层。晶面由 &CELL 的 ALPHA_BETA_GAMMA 90 90 90（正方胞）定为 Cu(100)。
EXP_COMPOSITION = {
    "cu100-h2o-opt": {"Cu": 48, "O": 46, "H": 92, "total": 186},
    "cu100-h2o-aimd": {"Cu": 48, "O": 28, "H": 56, "total": 132},
}
EXP_CELL_ORTHO = ("10.242489", "90")   # ABC 前两个分量相等 + ALPHA_BETA_GAMMA 90 90 90


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


class Report:
    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail, skip=False):
        self.rows.append({"name": name, "ok": bool(ok),
                          "detail": detail, "skip": bool(skip)})
        mark = "SKIP" if skip else ("PASS" if ok else "FAIL")
        print("  [{}] {}".format(mark, name))
        for ln in str(detail).splitlines():
            print("         " + ln)

    def failures(self):
        return [r for r in self.rows if not r["ok"] and not r["skip"]]

    def skips(self):
        return [r for r in self.rows if r["skip"]]


def find(src, *parts):
    """在源目录下按相对片段找文件（目录名带【】等特殊字符，用 glob 更稳）。"""
    pat = os.path.join(src, "**", *parts)
    hits = sorted(glob.glob(pat, recursive=True))
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser(description="真实算例数据回归（锁住真实数据才发现的问题）")
    ap.add_argument("--src", default=os.environ.get("CP2K_CASE_SRC", DEFAULT_SRC))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    r = Report()
    src = args.src
    if not os.path.isdir(src):
        print("=" * 74)
        print("真实数据回归 —— **SKIP**")
        print("=" * 74)
        print("  源目录不在本机: {}".format(src))
        print("  真实 .out（15 MB）与轨迹（2535 帧）按打包约定不入库，")
        print("  所以没有它们就无法跑这组回归。**这不是通过，是跳过。**")
        print("  指定源目录: python _validate_real_data.py --src <目录>")
        print("           或设置环境变量 CP2K_CASE_SRC")
        if args.json:
            print(json.dumps({"skipped": True, "reason": "source-not-available",
                              "src": src}, ensure_ascii=False, indent=2))
        return 0

    opt_out = find(src, "cu100-h2o-opt", "cp2k.out")
    aimd_out = find(src, "cu100-h2o-aimd", "cp2k.out")
    aimd_xyz = find(src, "cu100-h2o-aimd", "cp2k-pos-1.xyz")

    print("=" * 74)
    print("真实数据回归（源: {}）".format(src))
    print("=" * 74)

    # ---- 1. parse_output：几何优化收敛表的梯度必须取得到 -------------------
    if opt_out:
        p = run([PY, PO, opt_out])
        n_en = None
        m = re.search(r"Energy records found:\s*(\d+)", p.stdout)
        if m:
            n_en = int(m.group(1))
        has_grad = "Max. gradient" in p.stdout and "None" not in p.stdout
        ok = (n_en == EXP_OPT_ENERGIES) and has_grad
        r.add("parse_output 取到几何优化梯度（旧版恒为 null）", ok,
              "ENERGY 记录 {}（期望 {}）；Max. gradient {}；PROGRAM ENDED {}".format(
                  n_en, EXP_OPT_ENERGIES, "有" if has_grad else "**缺**",
                  "识别" if "PROGRAM ENDED" in p.stdout else "**未识别**"))
    else:
        r.add("parse_output 真实 opt 回归", True, "找不到 opt cp2k.out，跳过", skip=True)

    # ---- 2. diagnose：必须认出「作业被 kill」并算完成度 -------------------
    if aimd_out:
        p = run([PY, DG, aimd_out])
        killed = "被 kill" in p.stdout or "BAD TERMINATION" in p.stdout
        pct = re.search(r"完成度\s*([\d.]+)%", p.stdout)
        pct_v = float(pct.group(1)) if pct else None
        stepinfo = re.search(r"实际\s*(\d+)\s*/\s*请求\s*(\d+)", p.stdout)
        ok = (killed and pct_v is not None
              and abs(pct_v - EXP_AIMD_DONE_PCT) < 0.5)
        r.add("diagnose 识别「作业被 kill」并给出完成度", ok,
              "识别 kill: {}；完成度 {}%（期望 {}%）；步数 {}（期望 {}/{}）".format(
                  "是" if killed else "**否**", pct_v, EXP_AIMD_DONE_PCT,
                  stepinfo.group(0).replace(" ", "") if stepinfo else "**未给出**",
                  EXP_AIMD_STEPS_DONE, EXP_AIMD_STEPS_REQ))
    else:
        r.add("diagnose 真实被 kill 作业回归", True, "找不到 aimd cp2k.out，跳过", skip=True)

    # ---- 3. energy 必须**拒绝**轨迹文件（旧版静默产出 7 MB 垃圾） ----------
    if aimd_xyz:
        pref = os.path.join(os.environ.get("TEMP", "."), "_rd_energy")
        p = run([PY, PP, "energy", aimd_xyz, "--prefix", pref])
        refused = p.returncode != 0
        # 抓真正的提示行（`[ERROR] ...` / `请...`），别把分隔线当提示
        msg = ""
        for ln in (p.stderr or "").splitlines() + (p.stdout or "").splitlines():
            s = ln.strip()
            if not s or set(s) <= set("=- "):
                continue
            if s.startswith(("[ERROR]", "错误", "请")):
                msg = s
                break
        r.add("energy 拒绝轨迹文件（旧版静默产出垃圾、exit 0）", refused,
              "exit={}（期望 ≠0）；提示: {}".format(
                  p.returncode, msg[:120] if msg else "(未找到提示行)"))
    else:
        r.add("energy 输入类型校验回归", True, "找不到轨迹，跳过", skip=True)

    # ---- 4. RDF 配位数：真实轨迹上 H 恰好连 1 个 O ------------------------
    if aimd_xyz:
        pref = os.path.join(os.environ.get("TEMP", "."), "_rd_rdf")
        p = run([PY, PP, "rdf", aimd_xyz, "--pairs", "H O", "--rmax", "3.0",
                 "--bins", "300", "--cell", RDF_CELL, "--prefix", pref])
        csv = pref + "_rdf.csv"
        cn = None
        if p.returncode == 0 and os.path.isfile(csv):
            rows = [ln.split(",") for ln in
                    io.open(csv, encoding="utf-8").read().splitlines() if ln.strip()]
            hdr = rows[0]
            cand = [i for i, h in enumerate(hdr)
                    if h.startswith("g_") and {*h[2:].split("-")} == {"H", "O"}]
            if cand:
                icol, rcol = cand[0], hdr.index("r[A]")
                # 元素组成：从轨迹头数
                L = io.open(aimd_xyz, encoding="utf-8",
                            errors="replace").read().splitlines()
                nat = int(L[0].split()[0])
                els = [ln.split()[0] for ln in L[2:2 + nat] if ln.split()]
                nO = sum(1 for e in els if e == "O")
                V = 10.242489 * 10.242489 * 23.0
                rho = nO / V
                import math
                cn, prev = 0.0, None
                for row in rows[1:]:
                    rv, g = float(row[rcol]), float(row[icol])
                    if prev is not None:
                        dr = rv - prev
                        rc = 0.5 * (rv + prev)
                        if rc <= 1.3:
                            cn += g * rho * 4 * math.pi * rc * rc * dr
                    prev = rv
        ok = cn is not None and abs(cn - EXP_RDF_CN) < 0.05
        r.add("RDF 归一化：真实 2535 帧轨迹的 H–O 配位数", ok,
              "CN(r≤1.3 Å) = {}（期望 ≈ {}；未修版本给 0.0004，偏 2500 倍）".format(
                  "{:.4f}".format(cn) if cn is not None else "**算不出**", EXP_RDF_CN))
    else:
        r.add("RDF 真实轨迹回归", True, "找不到轨迹，跳过", skip=True)

    # ---- 5. validate_inp 对真实卡不应有误报 --------------------------------
    cards = sorted(glob.glob(os.path.join(CASES, "*_cp2k.inp")))
    if cards:
        p = run([PY, VI] + cards)
        bad = [w for w in p.stdout.splitlines()
               if "[warn]" in w and ("MULLIKEN" in w or "BASIS_MOLOPT" in w)]
        n_err = len([l for l in p.stdout.splitlines() if "[ERROR]" in l])
        r.add("validate_inp 对真实生产卡无误报（&MULLIKEN / 基组库路径）",
              not bad,
              "误报 {} 条（期望 0）；error {} 条（`@INCLUDE 'coord.inc'` 找不到是"
              "打包方式的必然结果，见 cases/README.md）".format(len(bad), n_err))
    else:
        r.add("validate_inp 真实卡回归", True, "cases/ 里没有卡，跳过", skip=True)

    # ---- 6. diagnose 的温度层：真实 NVT 跑法必须被正确解析且**不误报** -----
    #     这条同时守两件事：① 解析对了（值必须与独立测量一致）；
    #     ② 阈值不假阳性 —— 真实算例瞬时温度峰值是目标的 1.23 倍、末段平均偏
    #     3.1%、漂移 0.80 K/原子，三项阈值（1.5×/20%/1.0）都不该被触发。
    if aimd_out:
        p = run([PY, DG, aimd_out])
        so = p.stdout or ""

        def g(pat, cast=float, default=None):
            m = re.search(pat, so)
            return cast(m.group(1)) if m else default

        ens = g(r"系综:\s*(\S+)\s*\|", str)
        # 注意：不能用 '.+?$' —— 这是在**整段输出**上 search，'$' 不带 MULTILINE
        # 只匹配串尾，'.' 又不吃换行，于是永远匹配不上（本轮实测踩过）。
        therm = (g(r"恒温器:\s*([^\n]+)", str) or "").strip()
        tgt = g(r"目标\s*([\d.]+)\s*K")
        tmin = g(r"瞬时\s*([\d.]+)[–-]")
        tmax = g(r"瞬时\s*[\d.]+[–-]([\d.]+)\s*K")
        tend = g(r"末段平均\s*([\d.]+)\s*K")
        drift = g(r"守恒量漂移:\s*([-\d.]+)\s*K/原子")
        got = (ens == EXP_AIMD_ENSEMBLE and therm == EXP_AIMD_THERMOSTAT
               and tgt == EXP_AIMD_T_TARGET
               and tmin == EXP_AIMD_T_MIN and tmax == EXP_AIMD_T_MAX
               and tend == EXP_AIMD_T_END_AVG
               and drift is not None and abs(drift - EXP_AIMD_DRIFT) < 0.001)
        false_warn = [w for w in ("[WARN] 温度失控", "[WARN] 平均温度",
                                  "[WARN] 守恒量漂移") if w in so]
        r.add("diagnose 温度层：真实 NVT 解析正确且不误报", got and not false_warn,
              "系综 {} / 恒温器 {} / 目标 {}；瞬时 {}-{} K；末段平均 {} K；"
              "漂移 {} K/原子\n误报 {}".format(
                  ens, therm, tgt, tmin, tmax, tend, drift,
                  false_warn if false_warn else "无（期望无）"))
    else:
        r.add("diagnose 真实温度层回归", True, "找不到 aimd cp2k.out，跳过", skip=True)

    # ---- 7. 真实交付文件的组成 + 正交胞：定案课程的「晶面 / 水分子数」两说 -----
    #     两说原先靠"10.2239 Å 对得上哪个面"来判，那条几何论证**前提有误**：
    #     Cu(100) 的**素胞**边长也是 a/√2，与 (111) 面胞的最近邻间距相同，
    #     所以 10.22 Å 根本不能区分两面。真正的判据是 &CELL 的 γ：
    #     (111) 面胞必为六方（γ=60/120°），正交化后是 a × a√3，**不可能 a = b 且 γ=90°**。
    comp_rows, bad_comp, n_comp = [], [], 0
    for name, exp in EXP_COMPOSITION.items():
        # 注意：源目录的**直接子目录名带【】前缀且以"-计算输入文件和结构"结尾**，
        # 所以不能写 `*cu100-h2o-opt`（要求目录名以它结尾，永远匹配不上 → 假绿）。
        # 正确做法是把它当**中间某一层**，让 `**` 去穿。
        xyz = find(src, name, "cp2k-pos-1.xyz")
        if not xyz:
            continue
        import collections
        with io.open(xyz, encoding="utf-8", errors="replace") as fh:
            nat = int(fh.readline().split()[0])
            fh.readline()
            els = collections.Counter(fh.readline().split()[0] for _ in range(nat))
        got = {"Cu": els.get("Cu", 0), "O": els.get("O", 0), "H": els.get("H", 0),
               "total": nat}
        n_comp += 1
        ok = got == exp
        if not ok:
            bad_comp.append(name)
        comp_rows.append("{}: {} Cu + {} H₂O = {} 原子（期望 {} Cu + {} H₂O = {}）{}".format(
            name, got["Cu"], got["O"], nat, exp["Cu"], exp["O"], exp["total"],
            "" if ok else "  ← 不符"))
    if n_comp:
        r.add("真实交付文件组成（定案 Cu 晶面与水分子数两说）", not bad_comp,
              "\n".join(comp_rows))
    else:
        r.add("真实交付文件组成回归", True, "两份算例的轨迹都没找到，跳过", skip=True)

    # ---- 8. &CELL 必须是正交正方胞（排除 Cu(111)）---------------------------
    cell_msgs, bad_cell, n_cell = [], [], 0
    for name in EXP_COMPOSITION:
        p = find(src, name, "cp2k.inp")
        if not p:
            continue
        n_cell += 1
        txt = io.open(p, encoding="utf-8", errors="replace").read()
        m_abc = re.search(r"ABC\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", txt)
        m_ang = re.search(r"ALPHA_BETA_GAMMA\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", txt)
        if not (m_abc and m_ang):
            bad_cell.append(name)
            cell_msgs.append("{}: **未找到 ABC / ALPHA_BETA_GAMMA**".format(name))
            continue
        a, b, c = m_abc.groups()
        al, be, ga = m_ang.groups()
        square = (a == b) and (al == be == ga == "90")
        if not square:
            bad_cell.append(name)
        cell_msgs.append(
            "{}: ABC {} {} {} / αβγ {} {} {} ⇒ 面内{}".format(
                name, a, b, c, al, be, ga,
                "**正方胞**（⇒ Cu(100)；(111) 面胞必为六方，γ 不可能是 90°）"
                if square else "**非正方胞** ← 与 (100) 判定矛盾"))
    if n_cell:
        r.add("&CELL 为正方正交胞 ⇒ 排除 Cu(111)", not bad_cell, "\n".join(cell_msgs))
    else:
        r.add("&CELL 正方胞回归", True, "找不到 cp2k.inp，跳过", skip=True)

    print()
    print("-" * 74)
    print("  共 {} 项：通过 {} / 失败 {} / 跳过 {}".format(
        len(r.rows), len(r.rows) - len(r.failures()) - len(r.skips()),
        len(r.failures()), len(r.skips())))
    print("结论：{}".format("真实数据回归全部通过 ✓" if not r.failures()
                          else "{} 项失败 ✗".format(len(r.failures()))))
    if args.json:
        print(json.dumps({"summary": {"total": len(r.rows),
                                      "failed": len(r.failures()),
                                      "skipped": len(r.skips())},
                          "rows": r.rows}, ensure_ascii=False, indent=2))
    return 1 if r.failures() else 0


if __name__ == "__main__":
    sys.exit(main())
