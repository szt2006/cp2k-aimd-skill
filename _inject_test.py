#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""注入测试：**故意造错**，证明每个护栏真的会红。

**为什么必须有**：一个"永远是绿的"检查等于没有检查。本轮就踩过这个坑 ——
`_validate_all.py` 曾经因为把生成失败静默 `continue` 掉、分母写死、`main()`
不返回，于是无论输入多烂都印 "0 errors, 0 warnings" 并 exit 0（**假绿**）。
所以每个护栏都要有一条"注入错 → 必须报红"的证据。

做法：每条注入都在**可回滚**的前提下进行 ——
  * 需要改真实文件的（笔记、cases 副本）：先读进内存备份，`try/finally` 保证还原，
    还原后再算 sha256 与备份比对，**不还原成功就报 FAIL**；
  * 需要改源码的（postprocess / CLI）：改的是**临时副本**，真实文件不碰。

用法：
    python _inject_test.py            # 跑全部注入
    python _inject_test.py --list
    python _inject_test.py --json
"""
import argparse
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
try:
    import _console  # noqa: F401
except Exception:
    pass

PY = sys.executable
NOTES = os.path.join(HERE, "references", "h_tutorials", "notes")
CASES = os.path.join(HERE, "references", "h_tutorials", "cases")


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run(args, env=None, timeout=240):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          cwd=HERE, env=e, timeout=timeout)


class Res:
    def __init__(self, name, expect, got, ok, note=""):
        self.name, self.expect, self.got, self.ok, self.note = (
            name, expect, got, ok, note)


RESULTS = []


def record(name, expect, got, ok, note=""):
    RESULTS.append(Res(name, expect, got, ok, note))
    print("  [{}] {:<52} 期望 {} / 实得 {}".format(
        "OK" if ok else "FAIL", name, expect, got))
    if note:
        for ln in note.splitlines():
            print("         " + ln)


# --------------------------------------------------------------------------
# 1. 引用审计：塞一个越界页码，必须报「页码越界」
# --------------------------------------------------------------------------
def inject_citation():
    target = None
    for f in sorted(glob.glob(os.path.join(NOTES, "*.md"))):
        if os.path.getsize(f) > 5000:
            target = f
            break
    if not target:
        record("引用审计：注入越界页码", "exit 1 且报越界", "找不到可注入的笔记",
               False)
        return
    before = open(target, "rb").read()
    before_h = hashlib.sha256(before).hexdigest()
    restored_ok = True
    try:
        with io.open(target, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n<!-- 注入测试：故意写一个该教程不存在的页 -->\n"
                     "注入测试 T05 P999。\n")
        r = run([PY, os.path.join(HERE, "_audit_h_citations.py")])
        oob = re.search(r"页码越界（硬错误）:\s*(\d+)", r.stdout)
        n = int(oob.group(1)) if oob else None
        record("引用审计：注入越界页码 T05 P999",
               "exit 1 且越界 >0",
               "exit={} 越界={}".format(r.returncode, n),
               r.returncode == 1 and n and n > 0,
               "护栏确实会红 ⇒ `_audit_h_citations.py` 不是假绿")
    finally:
        # 注意：不能在 finally 里 return（Python 3.14 起是 SyntaxWarning，
        # 将来会变错误）。用标志位记下，出了 finally 再决定。
        with open(target, "wb") as fh:
            fh.write(before)
        restored_ok = hashlib.sha256(open(target, "rb").read()).hexdigest() \
            == before_h
    if not restored_ok:
        record("引用审计：还原被注入的笔记", "sha256 复原", "**未复原**", False,
               target)
        return
    # 还原后必须恢复绿
    r = run([PY, os.path.join(HERE, "_audit_h_citations.py")])
    oob = re.search(r"页码越界（硬错误）:\s*(\d+)", r.stdout)
    n = int(oob.group(1)) if oob else None
    record("引用审计：还原后恢复绿", "exit 0 且越界=0",
           "exit={} 越界={}".format(r.returncode, n),
           r.returncode == 0 and n == 0)


# --------------------------------------------------------------------------
# 2. 溯源核验：改一个字节，必须报「副本被改动」
# --------------------------------------------------------------------------
def inject_provenance():
    cards = sorted(glob.glob(os.path.join(CASES, "*_cp2k.inp")))
    if not cards:
        record("溯源核验：篡改副本", "exit 1", "找不到 cases 副本", False)
        return
    target = cards[0]
    before = open(target, "rb").read()
    before_h = hashlib.sha256(before).hexdigest()
    restored_ok = True
    try:
        with open(target, "ab") as fh:
            fh.write(b"\n# injection-test: tampered\n")
        r = run([PY, os.path.join(HERE, "_verify_case_provenance.py")])
        bad = re.search(r"副本被改动\s*:\s*(\d+)", r.stdout)
        n = int(bad.group(1)) if bad else None
        record("溯源核验：篡改 {} 一个字节".format(os.path.basename(target)),
               "exit 1 且「副本被改动」>0",
               "exit={} 被改动={}".format(r.returncode, n),
               r.returncode == 1 and n and n > 0,
               "护栏确实会红 ⇒ `_verify_case_provenance.py` 不是假绿")
    finally:
        with open(target, "wb") as fh:
            fh.write(before)
        restored_ok = hashlib.sha256(open(target, "rb").read()).hexdigest() \
            == before_h
    if not restored_ok:
        record("溯源核验：还原副本", "sha256 复原", "**未复原**", False, target)
        return
    r = run([PY, os.path.join(HERE, "_verify_case_provenance.py")])
    record("溯源核验：还原后恢复绿", "exit 0", "exit={}".format(r.returncode),
           r.returncode == 0)


# --------------------------------------------------------------------------
# 3. RDF 校验：把归一化挪回帧循环体内（复现原始 bug），必须报错
# --------------------------------------------------------------------------
def inject_rdf():
    src = os.path.join(HERE, "scripts", "postprocess.py")
    text = io.open(src, encoding="utf-8").read()
    # 找"帧循环之外的归一化"块，改成在循环内逐帧归一化（= 原 bug 的形态）
    marker = "    for (a, b) in pairs:\n        ia = idx_by_elem.get(a, [])\n" \
             "        ib = idx_by_elem.get(b, [])\n        if not ia or not ib:\n" \
             "            continue\n"
    i = text.find(marker)
    if i < 0:
        record("RDF 校验：注入帧循环内归一化", "exit 1",
               "在 postprocess.py 里找不到归一化块（结构变了？）", False,
               "注入点位需要按当前代码更新")
        return
    # 把归一化搬进帧循环末尾
    patched = text[:i] + text[i:].replace(marker, "", 1)
    loop_tail = ("                    if bin_idx < nbins:\n"
                 "                            hist[(a, b)][bin_idx] += 1\n")
    j = patched.find(loop_tail)
    if j < 0:
        record("RDF 校验：注入帧循环内归一化", "exit 1",
               "找不到帧循环末尾注入点", False)
        return
    ins = j + len(loop_tail)
    inj = ("            for (a, b) in pairs:\n"
           "                ia = idx_by_elem.get(a, [])\n"
           "                ib = idx_by_elem.get(b, [])\n"
           "                if not ia or not ib:\n"
           "                    continue\n"
           "                norm = len(ia) * M * 4 * math.pi * r_centers**2 * dr * (len(ib) / V)\n"
           "                hist[(a, b)] = hist[(a, b)] / norm\n")
    patched = patched[:ins] + inj + patched[ins:]
    with tempfile.TemporaryDirectory() as td:
        bad = os.path.join(td, "postprocess_bug.py")
        io.open(bad, "w", encoding="utf-8", newline="\n").write(patched)
        r = run([PY, os.path.join(HERE, "_validate_rdf_cn.py"),
                 "--postprocess", bad])
        record("RDF 校验：注入「归一化写在帧循环内」",
               "exit 1（判为归一化错误）",
               "exit={}".format(r.returncode),
               r.returncode == 1,
               "护栏确实会红 ⇒ `_validate_rdf_cn.py` 不是假绿")
    # 真实文件未被碰过
    r = run([PY, os.path.join(HERE, "_validate_rdf_cn.py")])
    record("RDF 校验：注入只作用于临时副本（真实脚本仍绿）",
           "exit 0", "exit={}".format(r.returncode), r.returncode == 0)


# --------------------------------------------------------------------------
# 4. FIXED_ATOMS：3 原子体系写 LIST 99..100，必须报越界
# --------------------------------------------------------------------------
def inject_fixed_atoms():
    card = """&GLOBAL
  PROJECT inject
  RUN_TYPE MD
&END GLOBAL
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME BASIS_MOLOPT
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    &MGRID
      CUTOFF 300
    &END MGRID
    &SCF
    &END SCF
    &XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 10.0 10.0 10.0
    &END CELL
    &COORD
      O 0.0 0.0 0.0
      H 0.0 0.0 0.99
      H 0.96 0.0 -0.25
    &END COORD
    &KIND O
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q6
    &END KIND
    &KIND H
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q1
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
&MOTION
  &CONSTRAINT
    &FIXED_ATOMS
      LIST 99..100
    &END FIXED_ATOMS
  &END CONSTRAINT
&END MOTION
"""
    with tempfile.TemporaryDirectory() as td:
        bad = os.path.join(td, "bad.inp")
        io.open(bad, "w", encoding="utf-8", newline="\n").write(card)
        r = run([PY, os.path.join(HERE, "scripts", "validate_inp.py"), bad])
        ok = r.returncode == 1 and "越界" in r.stdout
        record("validate_inp：3 原子体系注入 LIST 99..100",
               "exit 1 且报越界", "exit={} 含越界={}".format(
                   r.returncode, "越界" in r.stdout), ok,
               "这是真实算例里 4/5 张卡都犯、而 CP2K 静默通过的错")
        # 合法写法必须过
        good = os.path.join(td, "good.inp")
        io.open(good, "w", encoding="utf-8", newline="\n").write(
            card.replace("LIST 99..100", "LIST 1..2"))
        r2 = run([PY, os.path.join(HERE, "scripts", "validate_inp.py"), good])
        record("validate_inp：合法 LIST 1..2 不误报",
               "exit 0", "exit={}".format(r2.returncode), r2.returncode == 0,
               "反向对照 —— 防止护栏把合法输入也判死")


# --------------------------------------------------------------------------
# 5. GBK 扫描：造一个漏挂兼容层的 CLI，必须被扫出来
# --------------------------------------------------------------------------
def inject_gbk():
    with tempfile.TemporaryDirectory() as td:
        bad = os.path.join(HERE, "_inject_gbk_tmp.py")
        io.open(bad, "w", encoding="utf-8", newline="\n").write(
            "# 注入测试用：**故意不挂** scripts/_console.py\n"
            "import sys\n"
            "if '--help' in sys.argv:\n"
            "    print('故意打印 GBK 无法表示的符号：✓ ✗ • ⚠ ✖ ⑪ ↻ Å ² ³')\n"
            "    sys.exit(0)\n"
            "sys.exit(2)\n")
        try:
            r = run([PY, bad, "--help"], env={"PYTHONIOENCODING": "gbk",
                                              "PYTHONUTF8": "0"})
            blob = (r.stdout or "") + (r.stderr or "")
            caught = "UnicodeEncodeError" in blob
            record("GBK 扫描：漏挂 _console 的脚本必须被判定为崩",
                   "出现 UnicodeEncodeError",
                   "出现={} exit={}".format(caught, r.returncode), caught,
                   "证明 `_validate_gbk.py` 的判据有效 —— 它的全绿不是假绿")
        finally:
            if os.path.isfile(bad):
                os.remove(bad)


# --------------------------------------------------------------------------
# 6. PERIODIC 一致性：只设一段必须报，两段一致不许报
# --------------------------------------------------------------------------
PERIODIC_BASE = """&GLOBAL
  PROJECT t
  RUN_TYPE ENERGY_FORCE
&END GLOBAL
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME BASIS_MOLOPT
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    &MGRID
      CUTOFF 300
    &END MGRID
{poisson}
    &SCF
    &END SCF
    &XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 10.0 10.0 10.0
{cell}
    &END CELL
    &COORD
      O 0.0 0.0 0.0
      H 0.0 0.0 0.99
    &END COORD
    &KIND O
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q6
    &END KIND
    &KIND H
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q1
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
"""

_P_NONE = "    &POISSON\n      PERIODIC NONE\n      PSOLVER WAVELET\n    &END POISSON"
_P_XY = "    &POISSON\n      PERIODIC XY\n    &END POISSON"


def inject_periodic_consistency():
    """官方原文：`&POISSON/PERIODIC` 只管静电、`&CELL/PERIODIC` 管 pair list，
    "Typically the settings should be the same." ⇒ 只设一段就必须提醒。

    这个检查是**由「存疑查证」推出来的**：定案了"非周期要两段都写"之后，
    回头一看 `gen_inp.py --periodic none` 原来只发 `&POISSON` ⇒ 顺手修了工具，
    再顺手给校验器补了这条规则。**定案一条知识，应当顺带检查工具是否也符合它。**
    """
    cases = [
        ("两段都 NONE（一致）", _P_NONE, "      PERIODIC NONE", False),
        ("只设 &POISSON NONE（漏 &CELL）", _P_NONE, "", True),
        ("只设 &CELL NONE（漏 &POISSON）", "", "      PERIODIC NONE", True),
        ("两段都 XY（一致）", _P_XY, "      PERIODIC XY", False),
        ("两段都不写（都取默认 XYZ）", "", "", False),
    ]
    with tempfile.TemporaryDirectory() as td:
        for label, poisson, cell, want in cases:
            p = os.path.join(td, "t.inp")
            io.open(p, "w", encoding="utf-8", newline="\n").write(
                PERIODIC_BASE.format(poisson=poisson, cell=cell))
            r = run([PY, os.path.join(HERE, "scripts", "validate_inp.py"), p])
            got = "两项 PERIODIC 不一致" in r.stdout
            record("PERIODIC 一致性：{}".format(label),
                   "报警={}".format(want), "报警={}".format(got), got == want,
                   "含反向对照 —— 一致时**不许**报警")


def inject_kw_alias():
    """`_kw_probe.py --find` 必须**搜到别名**。

    这条守的是一个我**差点据此得出错误结论**的工具盲区：真实生产卡 7/7 张都写
    `WF_INTERPOLATION ASPC`，而只按默认名搜会得到"0 命中"——
    差一点就判定"生产卡写了个不存在的关键字"。真相是
    `WF_INTERPOLATION` 是 `EXTRAPOLATION` 的**别名**。
    """
    kw = os.path.join(HERE, "_kw_probe.py")
    if not os.path.isfile(kw):
        record("关键字别名搜索：_kw_probe.py 存在", "存在", "缺失", False)
        return
    r = run([PY, kw, "--find", "WF_INTERPOLATION"])
    hit = r.returncode == 0 and "EXTRAPOLATION" in r.stdout
    record("关键字别名搜索：--find WF_INTERPOLATION 命中默认名",
           "命中且显示 EXTRAPOLATION", "exit={} 命中={}".format(
               r.returncode, "EXTRAPOLATION" in r.stdout), hit,
           "只搜默认名会 0 命中 ⇒ 会把合法写法误判成'关键字不存在'")
    # 反向对照：不存在的名字必须 0 命中、非 0 退出
    r2 = run([PY, kw, "--find", "NO_SUCH_KEYWORD_XYZ"])
    miss = r2.returncode != 0 and "0 处" in r2.stdout
    record("关键字别名搜索：不存在的名字必须 0 命中",
           "0 处且 exit≠0", "exit={} 报 0 处={}".format(
               r2.returncode, "0 处" in r2.stdout), miss,
           "反向对照 —— 别名搜索不能变成'什么都搜得到'")
    # **段名也要能搜到**：同一个盲区的第二例 —— `--find SWARM` 曾返回 0 处，
    # 于是有人据此写下"现行 XML 无 SWARM"（而 &SWARM 是 14 个顶层段之一）。
    r3 = run([PY, kw, "--find", "SWARM"])
    sec = r3.returncode == 0 and "&SWARM" in r3.stdout and "段 1" in r3.stdout
    record("段名搜索：--find SWARM 必须命中顶层段",
           "命中 &SWARM 且报'段 1'", "exit={} 命中={}".format(
               r3.returncode, "&SWARM" in r3.stdout), sec,
           "只搜 KEYWORD 会 0 命中 ⇒ 会把存在的段误判成不存在")


def inject_ener_columns():
    """守一个**静默错值**缺陷：真实 7 列 `.ener` 曾被读成最后一列 `UsedTime`。

    CP2K 官方 `.ener` 列序：
        Step  Time[fs]  Kin.[a.u.]  Temp[K]  Pot.[a.u.]  Cons Qty[a.u.]  UsedTime[s]
    早先走"两列退化分支"时取 `parts[-1]` ⇒ 拿到的是**每步墙钟耗时（秒）**。
    实测 7 列样例报 `final = 17.5 a.u.`（真实势能 −100.05）且 **exit 0** ——
    用户拿它画"能量漂移"会得到完全无意义的图，还看不出错。
    """
    with tempfile.TemporaryDirectory() as td:
        p7 = os.path.join(td, "PROJECT-1.ener")
        rows = []
        for i in range(4):
            rows.append("{:6d} {:9.3f} {:13.8f} {:9.2f} {:17.10f} {:17.10f} {:11.3f}"
                        .format(i * 10, i * 5.0, 0.01, 300.0 + i,
                                -100.0 - i * 0.01, -99.99 - i * 0.01, 12.5 + i))
        io.open(p7, "w", encoding="utf-8", newline="\n").write(
            "\n".join(rows) + "\n")
        r = run([PY, os.path.join(HERE, "scripts", "postprocess.py"),
                 "energy", p7, "--prefix", os.path.join(td, "e7")])
        ok7 = "-100.03" in (r.stdout or "")
        record("`.ener` 7 列：必须取 Pot 列，不许取到 UsedTime",
               "final = -100.03", "stdout 含 -100.03 = {}".format(ok7), ok7,
               "取错列是静默错值 —— 会把 15.5 秒当成能量")
        # 反向对照：2 列简写仍必须支持（修 7 列不许把 2 列弄坏）
        p2 = os.path.join(td, "simple.ener")
        io.open(p2, "w", encoding="utf-8", newline="\n").write(
            "1 -100.0\n2 -100.5\n3 -101.0\n")
        r2 = run([PY, os.path.join(HERE, "scripts", "postprocess.py"),
                  "energy", p2, "--prefix", os.path.join(td, "e2")])
        ok2 = "-101.0" in (r2.stdout or "")
        record("`.ener` 2 列简写：仍取最后一列",
               "final = -101.0", "stdout 含 -101.0 = {}".format(ok2), ok2,
               "反向对照 —— 修 7 列不许把 2 列弄坏")


def inject_md_temperature():
    """守一个**能力缺失 + 假阳性**双重缺陷。

    缺失：`guide.py` 到处承诺 diagnose 能看「温度/能量漂移」，但 diagnose.py
    早先**只解析能量**（`res` 里连一个温度键都没有）—— 承诺是空的。
    现在补了温度层，就必须证明它**既会红、也不会乱红**。

    假阳性对照用真实算例标定：NVT / Nose-Hoover-Chains，目标 300 K，2534 步，
    瞬时温度 179.3–369.7 K（峰值 1.23×目标），末段平均 290.8 K（偏 3.1%），
    守恒量漂移 0.797 K/原子 —— **三项都不许报 WARN**。
    """
    def build(temps, drifts, target=300.0):
        out = [
            " MD| Ensemble Type                                                           NVT",
            " THERMOSTAT| Type of thermostat                               Nose-Hoover-Chains",
            " MD| Temperature [K]                                             %13.2f" % target,
            " MD| Temperature tolerance [K]                                              0.00",
            " INITIAL TEMPERATURE[K]                =                        %13.3f" % target,
        ]
        for i, (t, d) in enumerate(zip(temps, drifts)):
            run_t = sum(temps[:i + 1]) / (i + 1)
            run_d = sum(drifts[:i + 1]) / (i + 1)
            out += [
                " ENSEMBLE TYPE                =                                              NVT",
                " STEP NUMBER                  = %49d" % (i + 1),
                " TEMPERATURE [K]              =  %19.3f %19.3f" % (t, run_t),
                " ENERGY DRIFT PER ATOM [K]    =  %19.12E %19.12E" % (d, run_d),
            ]
        return "\n".join(out) + "\n"

    DP = os.path.join(HERE, "scripts", "diagnose.py")
    healthy_t = [294.7, 281.4, 265.0, 251.5, 310.0, 340.0, 369.7,
                 200.0, 179.3, 300.0, 291.0]
    healthy_d = [0.8] * len(healthy_t)

    with tempfile.TemporaryDirectory() as td:
        def check(name, text, must_have, must_lack):
            p = os.path.join(td, name + ".out")
            io.open(p, "w", encoding="utf-8", newline="\n").write(text)
            r = run([PY, DP, p])
            so = r.stdout or ""
            hit = [s for s in must_have if s in so]
            bad = [s for s in must_lack if s in so]
            ok = len(hit) == len(must_have) and not bad
            record("温度层：" + name,
                   "必含 {} / 必不含 {}".format(must_have, must_lack or "—"),
                   "含 {} / 误含 {}".format(hit or "无", bad or "无"), ok,
                   (so.strip().splitlines() or [""])[-1][:110])
            return so

        # ① 假阳性对照：真实算例的健康跑法，三项都不许报
        #    判据必须带 '[WARN] ' 前缀 —— 「守恒量漂移」在**统计量**区里永远会打印
        #    （那是好事，说明解析到了），只按词判会把正常输出误判成告警。
        so = check("真实NVT健康跑法(不报)", build(healthy_t, healthy_d),
                   must_have=[],
                   must_lack=["[WARN] 温度失控", "[WARN] 平均温度",
                              "[WARN] 守恒量漂移"])
        ok_parse = "瞬时 179.3" in so and "Nose-Hoover-Chains" in so
        record("温度层：解析值必须精确",
               "瞬时 179.3 K / 恒温器 Nose-Hoover-Chains",
               "解析正确 = {}".format(ok_parse), ok_parse,
               "峰值 369.7<450(1.5×300)、末段平均偏 3.1%<20%、漂移 0.80<1.0")
        # ② 温度失控必须红
        check("温度失控(必报)", build(healthy_t[:5] + [600.0] + healthy_t[6:],
                                     healthy_d),
              must_have=["[WARN] 温度失控"], must_lack=[])
        # ③ 平均温度没到目标必须红
        check("平均温度偏目标(必报)", build([150.0] * 8, healthy_d[:8]),
              must_have=["[WARN] 平均温度"], must_lack=["[WARN] 温度失控"])
        # ④ 守恒量漂移超标必须红
        check("守恒量漂移超标(必报)", build(healthy_t, [50.0] * len(healthy_t)),
              must_have=["[WARN] 守恒量漂移"],
              must_lack=["[WARN] 温度失控", "[WARN] 平均温度"])


def inject_videonotes_citations():
    """守一个**没有任何工具在守**的层：E 层 `videonotes/` 的引用可溯源性。

    本轮把 6 份视频精读笔记的成果并进 A/B/C/F，新增 173 条
    `videonotes/<笔记名> L###` 引用。H 层有 `_audit_h_citations.py` 守 `T** P**`，
    **这一层此前是空白** —— 行号写错或笔记名写残（本轮真出现过两条
    `videonotes/… L565`，光一个省略号，读者根本回不去原文），没有任何东西会报。

    做法：往仓库根**临时**放一个带坏引用的 `.md`（审计脚本扫全仓 `*.md`），
    跑完在 `finally` 里删掉并核对确实删掉了 —— 不留痕。
    """
    AUD = os.path.join(HERE, "_audit_videonotes_citations.py")
    probe = os.path.join(HERE, "_inject_vn_probe.md")
    try:
        # ① 笔记名写残（光一个省略号）必须报"解析不了"
        io.open(probe, "w", encoding="utf-8", newline="\n").write(
            "# 注入探针\n\n引用：`videonotes/… L565`\n")
        r = run([PY, AUD])
        so = (r.stdout or "") + (r.stderr or "")
        bad_name = ("笔记名解析不了" in so) and r.returncode == 1
        record("videonotes 引用：笔记名写残（光省略号）必须报红",
               "exit=1 且报「笔记名解析不了」",
               "exit={} 报错={}".format(r.returncode, "笔记名解析不了" in so), bad_name)

        # ② 行号越界必须报红（cp2k-1-1 只有 1195 行）
        io.open(probe, "w", encoding="utf-8", newline="\n").write(
            "# 注入探针\n\n引用：`videonotes/cp2k-1-1-…-精读笔记 L99999`\n")
        r = run([PY, AUD])
        so = (r.stdout or "") + (r.stderr or "")
        oob = ("行号越界" in so) and r.returncode == 1
        record("videonotes 引用：行号越界（L99999）必须报红",
               "exit=1 且报「行号越界」",
               "exit={} 报错={}".format(r.returncode, "行号越界" in so), oob)

        # ③ 反向对照：合法引用不许报红（护栏不能变成"什么都报"）
        io.open(probe, "w", encoding="utf-8", newline="\n").write(
            "# 注入探针\n\n引用：`videonotes/cp2k-1-1-…-精读笔记 L312 [12:05–13:10]`\n")
        r = run([PY, AUD])
        so = (r.stdout or "") + (r.stderr or "")
        clean = (r.returncode == 0) and ("无越界" in so)
        record("videonotes 引用：合法引用必须放行（反向对照）",
               "exit=0 且报「无越界」",
               "exit={} 结论含'无越界'={}".format(r.returncode, "无越界" in so), clean)

        # ④ 反向对照：**占位符**（`L###`）不是引用，不许报红。
        #    文档里举例说明"笔记名写残"这种坏写法时用 `L###` 占位；
        #    正则只认 `L` 后跟数字，所以占位符天然跳过。这条钉住该约定 ——
        #    否则写文档的人一举例就会把自己的审计弄红（本轮踩过）。
        io.open(probe, "w", encoding="utf-8", newline="\n").write(
            "# 注入探针\n\n坏写法形如 `videonotes/… L###`（笔记名被省掉）。\n")
        r = run([PY, AUD])
        so = (r.stdout or "") + (r.stderr or "")
        ph_ok = (r.returncode == 0) and ("无越界" in so)
        record("videonotes 引用：`L###` 占位符不算引用（不许报红）",
               "exit=0 且报「无越界」",
               "exit={} 结论含'无越界'={}".format(r.returncode, "无越界" in so), ph_ok)

        # ⑤ 第二类引用（`S*.txt:<行号>`，库里 545 条、比 videonotes 还多）：
        #    字幕行号越界必须报红（S5.txt 实测 4519 行）。
        io.open(probe, "w", encoding="utf-8", newline="\n").write(
            "# 注入探针\n\n引用：`S5.txt:99999`\n")
        r = run([PY, AUD])
        so = (r.stdout or "") + (r.stderr or "")
        s_oob = ("字幕行号越界" in so) and r.returncode == 1
        record("字幕引用：`S5.txt:99999` 行号越界必须报红",
               "exit=1 且报「字幕行号越界」",
               "exit={} 报错={}".format(r.returncode, "字幕行号越界" in so), s_oob)

        # ⑥ 字幕文件名写错必须报红（`S9.txt` 不存在）
        io.open(probe, "w", encoding="utf-8", newline="\n").write(
            "# 注入探针\n\n引用：`S9.txt:100`\n")
        r = run([PY, AUD])
        so = (r.stdout or "") + (r.stderr or "")
        s_miss = ("字幕文件不存在" in so) and r.returncode == 1
        record("字幕引用：不存在的 `S9.txt` 必须报红",
               "exit=1 且报「字幕文件不存在」",
               "exit={} 报错={}".format(r.returncode, "字幕文件不存在" in so), s_miss)

        # ⑦ 反向对照：合法字幕引用必须放行（`S5.txt:2071` 是真实的 TiO₂ 那句）
        io.open(probe, "w", encoding="utf-8", newline="\n").write(
            "# 注入探针\n\n引用：`S5.txt:2071`、区间 `S4.txt:2447–2448`\n")
        r = run([PY, AUD])
        so = (r.stdout or "") + (r.stderr or "")
        s_ok = (r.returncode == 0) and ("无越界" in so)
        record("字幕引用：合法引用必须放行（反向对照）",
               "exit=0 且报「无越界」",
               "exit={} 结论含'无越界'={}".format(r.returncode, "无越界" in so), s_ok)
    finally:
        if os.path.isfile(probe):
            os.remove(probe)
        left = os.path.isfile(probe)
        record("videonotes 注入：探针文件必须被删掉",
               "不存在", "仍存在={}".format(left), not left)


def inject_plus_keyword_shim():
    """守一个**上游工具链的假 error**，并证明本仓库的补丁**确实是承重的**。

    `IONS+CENTERS` 是官方 `cp2k_input.xml` 里**唯一含 `+` 的关键字名**
    （`<NAME type="default">IONS+CENTERS</NAME>` 出现 19 次、同名，全在 Wannier
    打印段下，官方默认 `F`）。而 cp2k-input-tools 0.9.1 的关键字正则写作
    `(?P<name>[\\w\\-_]+)` —— **字符类里没有 `+`** —— 于是解析到这一行时在 `+` 处
    截断、把 `IONS` 当关键字名，报
        `InvalidNameError: invalid keyword 'IONS' specified ...`
    **这是假 error，输入完全合法**。`gen_inp.py --properties wannier` 正会发射它。

    `_official_validate.py` / `_validate_all.py` 顶部各有一段补丁把它修掉。
    本注入证两个方向：
      * **正向**：走本仓库的 `_official_validate.py` ⇒ 必须放行；
      * **反向**：把正则**还原成上游那版** ⇒ 必须复现那个假 error。
    只证正向，补丁可能是死代码；只证反向，说明不了仓库已修好。
    """
    UPSTREAM_PROBE = '''\
import re, sys
import cp2k_input_tools.parser as P
from cp2k_input_tools.parser import CP2KInputParser
# 刻意还原成**上游原始**正则（即"假设本仓库没打补丁"）
P._KEYWORD_MATCH = re.compile(r"(?P<name>[\\w\\-_]+)\\s*(?P<value>.*)")
try:
    P.UREG.define("fs = femtosecond")
except Exception:
    pass
with open(sys.argv[1], encoding="utf-8") as fh:
    CP2KInputParser().parse(fh)
print("PARSED-OK")
'''
    with tempfile.TemporaryDirectory() as td:
        xyz = os.path.join(td, "a.xyz")
        io.open(xyz, "w", encoding="utf-8", newline="\n").write(
            "3\nCu O H\nCu 0 0 0\nO 1.8 0 0\nH 2.7 0 0\n")
        inp = os.path.join(td, "wc.inp")
        # 用 gen_inp 真生成（手写容易把段路径写错，生成物才是用户真会拿到的东西）
        g = run([PY, os.path.join(HERE, "scripts", "gen_inp.py"),
                 "--type", "aimd_md", "--project", "wc",
                 "--elem", "Cu", "O", "H",
                 "--basis", "DZVP-MOLOPT-SR-GTH", "DZVP-MOLOPT-SR-GTH",
                 "DZVP-MOLOPT-SR-GTH",
                 "--potential", "GTH-PBE", "GTH-PBE-q6", "GTH-PBE-q1",
                 "--periodic", "xyz", "--xyz", xyz,
                 "--cell", "12", "0", "0", "0", "12", "0", "0", "0", "12",
                 "--properties", "wannier", "-o", inp])
        has = os.path.isfile(inp) and "IONS+CENTERS" in io.open(
            inp, encoding="utf-8", errors="replace").read()
        record("`IONS+CENTERS`：gen_inp --properties wannier 必须真的发射它",
               "生成物含 IONS+CENTERS",
               "生成={} 含关键字={}".format(os.path.isfile(inp), has), has,
               "它是官方 XML 里唯一含 `+` 的关键字名")

        # 正向：本仓库校验器必须放行
        r = run([PY, os.path.join(HERE, "_official_validate.py"), inp])
        so = (r.stdout or "") + (r.stderr or "")
        ok = r.returncode == 0 and "ALL OK" in so
        record("`IONS+CENTERS`：本仓库校验器必须放行（补丁生效）",
               "exit=0 且 ALL OK",
               "exit={} ALL OK={}".format(
                   r.returncode, "ALL OK" in so), ok)

        # 反向：还原上游正则，必须复现假 error（证明补丁承重、bug 是真的）
        probe = os.path.join(td, "probe_upstream.py")
        io.open(probe, "w", encoding="utf-8", newline="\n").write(UPSTREAM_PROBE)
        r2 = run([PY, probe, inp])
        so2 = (r2.stdout or "") + (r2.stderr or "")
        reproduced = r2.returncode != 0 and "IONS" in so2
        record("`IONS+CENTERS`：还原上游正则必须复现假 error（反向对照）",
               "非零退出且报 invalid keyword 'IONS'",
               "exit={} 含 IONS={}".format(r2.returncode, "IONS" in so2),
               reproduced,
               "证明上游确有此缺陷、且本仓库补丁不是死代码")


def inject_energy_line_format():
    """守一个**跨版本输出格式变化**导致的静默失效（2026-10 真机实测发现）。

    CP2K 的能量行换过写法：
        旧版（课程那批 5.x/6.x）：`ENERGY| Total FORCE_EVAL ( QS ) energy (a.u.):  -29.06...`
        CP2K 2022.1          ：`ENERGY| Total FORCE_EVAL ( QS ) energy [a.u.]:  -29.06...`
    `diagnose.py` 早先只写死**圆括号**的 `"energy (a.u.)"` ⇒ 在 2022.1 输出上
    **一个都匹配不到** ⇒ `res["energies"]` 恒空 ⇒ **整条「AIMD 能量漂移」诊断静默失效**
    （同一份文件 `parse_output.py` 却能数出 19 个，因为它的正则对格式不敏感）。

    两个方向都要证：**两种写法都必须数到**；并**反向对照**——非 MD 的多能量
    （如频率分析的逐个位移）**不许**被当成能量漂移报警。
    """
    def mk(brackets, n=4, md=False):
        out = []
        if md:
            out.append(" MD| Ensemble Type                                                           NVT")
        for i in range(n):
            if md:
                out.append(" STEP NUMBER                  = %49d" % (i + 1))
            out.append(" ENERGY| Total FORCE_EVAL ( QS ) energy %s:   %20.12f"
                       % (brackets, -29.0 - i * 0.01))
        return "\n".join(out) + "\n"

    with tempfile.TemporaryDirectory() as td:
        for tag, br in (("paren", "(a.u.)"), ("brack", "[a.u.]")):
            p = os.path.join(td, tag + ".out")
            io.open(p, "w", encoding="utf-8", newline="\n").write(mk(br))
            r = run([PY, os.path.join(HERE, "scripts", "diagnose.py"), p])
            so = r.stdout or ""
            ok = ("能量采样点: 4 个" in so)
            record("能量行 `%s` 必须被数到（跨版本格式）" % br,
                   "能量采样点: 4 个",
                   "数到 = {}".format(ok), ok,
                   "只认圆括号会让 2022.1 输出的能量漂移诊断**静默失效**")

        # 反向对照：非 MD（无 STEP NUMBER）的多能量，不许报「能量漂移」
        p = os.path.join(td, "vib.out")
        io.open(p, "w", encoding="utf-8", newline="\n").write(
            mk("[a.u.]", n=5, md=False))
        r = run([PY, os.path.join(HERE, "scripts", "diagnose.py"), p])
        so = r.stdout or ""
        quiet = ("[WARN] 能量跨度" not in so) and ("这不是 MD 轨迹" in so)
        record("非 MD 的多能量不许报「能量漂移」（反向对照）",
               "无 WARN 且给出「这不是 MD 轨迹」说明",
               "合格 = {}".format(quiet), quiet,
               "频率分析/几何优化的各能量来自不同构型，跨度大是正常的")


def inject_periodic_none_and_force_sum():
    """守 2026-10 真机实测揪出的四个缺陷（都是"不报错但结果错"或"开关静默失效"）。

    ① `--periodic none` 必须自动补 `&TOPOLOGY/&CENTER_COORDINATES`：
       WAVELET 求解器要求分子居于单胞中心，否则静默算错（实测能量差 12 Ha、|ΣF|=24.7）。
    ② `--nproc-rep N` 必须真的写进 vib 输出：模板原先把 `NPROC_REP 8` 写死、
       没有 `__NPROC_REP__` 占位符 ⇒ **开关静默失效**（工具还一边打印"NPROC_REP
       取太大会让频率不可信"的建议）。
    ③ `validate_inp` 对 `&TOPOLOGY/&CENTER_COORDINATES` **不许**报"内联 &COORD 被忽略"
       （假阳性，会吓到用户）；但对真的 `COORD_FILE_NAME` **必须**照旧报。
    ④ `diagnose` 必须能报 `|ΣF|` 异常 —— 那是这类静默错误**唯一可见的症状**。
    """
    with tempfile.TemporaryDirectory() as td:
        xyz = os.path.join(td, "h2o.xyz")
        io.open(xyz, "w", encoding="utf-8", newline="\n").write(
            "3\n\nO 0.0 0.0 0.1173\nH 0.0 0.7572 -0.4692\nH 0.0 -0.7572 -0.4692\n")

        # ① --periodic none ⇒ 必须有 CENTER_COORDINATES
        inp = os.path.join(td, "c.inp")
        run([PY, os.path.join(HERE, "scripts", "gen_inp.py"), "--type", "vib",
             "--project", "c", "--elem", "O", "H",
             "--basis", "DZVP-MOLOPT-SR-GTH", "DZVP-MOLOPT-SR-GTH",
             "--potential", "GTH-PBE-q6", "GTH-PBE-q1",
             "--periodic", "none", "--xyz", xyz,
             "--cell", "12", "0", "0", "0", "12", "0", "0", "0", "12",
             "--nproc-rep", "4", "-o", inp])
        txt = io.open(inp, encoding="utf-8").read()
        ok = "&CENTER_COORDINATES" in txt
        record("--periodic none 必须补 &CENTER_COORDINATES（WAVELET 硬前提）",
               "生成物含 &CENTER_COORDINATES",
               "含 = {}".format(ok), ok,
               "不补则分子横跨单胞边界，静默算错（实测能量差 12 Ha）")

        # ② --nproc-rep 4 ⇒ 必须写进 NPROC_REP
        ok = "NPROC_REP 4" in txt
        record("--nproc-rep 必须真的写进 vib 卡（模板曾写死 8）",
               "生成物含 NPROC_REP 4",
               "含 = {}".format(ok), ok,
               "模板原缺 __NPROC_REP__ 占位符 ⇒ 开关静默失效")

        # ③ validate_inp：CENTER_COORDINATES 不许误报；COORD_FILE_NAME 必须报
        r = run([PY, os.path.join(HERE, "scripts", "validate_inp.py"), inp])
        so = (r.stdout or "") + (r.stderr or "")
        quiet = "内联 &COORD 被忽略" not in so
        record("validate_inp 对 &CENTER_COORDINATES 不许误报",
               "不出现「内联 &COORD 被忽略」",
               "安静 = {}".format(quiet), quiet,
               "该写法下内联 &COORD 完全生效（实测 |ΣF|=0.0002）")

        topo = os.path.join(td, "t.inp")
        io.open(topo, "w", encoding="utf-8", newline="\n").write(
            "&GLOBAL\n  PROJECT t\n  RUN_TYPE ENERGY\n&END GLOBAL\n"
            "&FORCE_EVAL\n  METHOD Quickstep\n  &DFT\n    &SCF\n    &END SCF\n  &END DFT\n"
            "  &SUBSYS\n    &CELL\n      ABC 10 10 10\n    &END CELL\n"
            "    &TOPOLOGY\n      COORD_FILE_NAME mol.xyz\n    &END TOPOLOGY\n"
            "    &COORD\n      O 0 0 0\n      H 0 0 1\n    &END COORD\n"
            "  &END SUBSYS\n&END FORCE_EVAL\n")
        r = run([PY, os.path.join(HERE, "scripts", "validate_inp.py"), topo])
        so = (r.stdout or "") + (r.stderr or "")
        caught = "内联 &COORD 被忽略" in so
        record("validate_inp 对真 COORD_FILE_NAME 必须照旧报（反向对照）",
               "出现「内联 &COORD 被忽略」",
               "报出 = {}".format(caught), caught,
               "收紧规则时不能把真问题一起放过")

        # ④ diagnose：ΣF 异常必须报
        def mkout(sf):
            return (" GLOBAL| Run type: ENERGY\n"
                    " ENERGY| Total FORCE_EVAL ( QS ) energy [a.u.]:   -17.120191736671\n"
                    " SUM OF ATOMIC FORCES         -0.00000000    0.00000000 "
                    "  -0.00198248    %12.8f\n" % sf)
        p = os.path.join(td, "bad.out")
        io.open(p, "w", encoding="utf-8", newline="\n").write(mkout(24.72427756))
        r = run([PY, os.path.join(HERE, "scripts", "diagnose.py"), p])
        so = r.stdout or ""
        hit = "ΣF" in so
        record("diagnose 必须报 |ΣF| 异常（静默错误的唯一症状）",
               "输出含 ΣF 警告", "报出 = {}".format(hit), hit,
               "偏心 WAVELET 时 ΣF=24.7，CP2K 自己不报任何错")
        p = os.path.join(td, "good.out")
        io.open(p, "w", encoding="utf-8", newline="\n").write(mkout(0.0005))
        r = run([PY, os.path.join(HERE, "scripts", "diagnose.py"), p])
        so = r.stdout or ""
        quiet = "ΣF" not in so
        record("diagnose 对正常 |ΣF| 不许误报（反向对照）",
               "输出不含 ΣF 警告", "安静 = {}".format(quiet), quiet,
               "合法算例实测 0.0002~0.0020，阈值 0.05 有三个数量级安全带")


def inject_md_flags_reach_output():
    """守"取值开关必须真的落进生成物"这一类缺陷。

    2026-10 真机验证期间连抓两个同族缺陷：
      * `--nproc-rep` 对 `--type vib` 静默失效（模板 `NPROC_REP 8` 写死、无占位符）；
      * **`--temperature` 根本不存在**（模板 `TEMPERATURE 600.0` / `450.0` 写死），
        而 MD 的目标温度是这套工具里最关键的旋钮之一。
    两者的共同点是：**命令行接受了参数、也没报错，但输出里看不到它** ——
    用户以为自己设了，其实没有。这类"静默不生效"必须靠行为测试守，不能靠读代码。

    做法：给每个开关一个**独特且可辨识**的值，生成后断言它出现在输出里。
    """
    with tempfile.TemporaryDirectory() as td:
        xyz = os.path.join(td, "h2o.xyz")
        io.open(xyz, "w", encoding="utf-8", newline="\n").write(
            "3\n\nO 0.0 0.0 0.1173\nH 0.0 0.7572 -0.4692\nH 0.0 -0.7572 -0.4692\n")

        def gen(typ, out, extra):
            run([PY, os.path.join(HERE, "scripts", "gen_inp.py"),
                 "--type", typ, "--project", "F", "--elem", "O", "H",
                 "--basis", "DZVP-MOLOPT-SR-GTH", "DZVP-MOLOPT-SR-GTH",
                 "--potential", "GTH-PBE-q6", "GTH-PBE-q1",
                 "--periodic", "none", "--xyz", xyz,
                 "--cell", "12", "0", "0", "0", "12", "0", "0", "0", "12",
                 "-o", out] + extra)
            return io.open(out, encoding="utf-8").read()

        # MD 类开关：每个都给独特值
        txt = gen("aimd_md", os.path.join(td, "md.inp"),
                  ["--ensemble", "nvt", "--steps", "7", "--timestep", "0.25",
                   "--temperature", "333", "--thermostat", "nose",
                   "--timecon", "44"])
        for label, want in (("--ensemble nvt", "ENSEMBLE NVT"),
                            ("--steps 7", "STEPS 7"),
                            ("--timestep 0.25", "TIMESTEP 0.25"),
                            ("--temperature 333", "TEMPERATURE 333"),
                            ("--thermostat nose", "TYPE NOSE"),
                            ("--timecon 44", "TIMECON [fs] 44")):
            ok = want in txt
            record("MD 开关必须落进输出：{}".format(label),
                   "生成物含 `{}`".format(want),
                   "含 = {}".format(ok), ok,
                   "命令行收下了却不写进输出 = 用户以为设了、其实没设")

        # 每模板的**原值**必须保持（不给开关时零行为变化）
        for typ, want in (("aimd_md", "TEMPERATURE 600.0"),
                          ("metadyn", "TEMPERATURE 450.0")):
            txt = gen(typ, os.path.join(td, typ + ".inp"), [])
            ok = want in txt
            record("不给 --temperature 时 {} 沿用原值".format(typ),
                   "生成物含 `{}`".format(want),
                   "含 = {}".format(ok), ok,
                   "补开关不能让既有默认值悄悄变掉")

        # vib 的 --nproc-rep（同类缺陷的另一个实例）
        txt = gen("vib", os.path.join(td, "v.inp"), ["--nproc-rep", "3"])
        ok = "NPROC_REP 3" in txt
        record("vib 的 --nproc-rep 必须落进输出",
               "生成物含 NPROC_REP 3",
               "含 = {}".format(ok), ok,
               "模板曾写死 NPROC_REP 8")


def inject_ener_header_columns():
    """守 `.ener` 的**列映射**（2026-10 真机验证抓到的静默错值）。

    CP2K 官方 `.ener` 表头比数据行**多出 `#`、`Nr.`、`Qty[a.u.]` 三个 token**
    （`Step Nr.` 与 `Cons Qty[a.u.]` 各是两个 token 描述一列）。早先按 token 序号
    定位 ⇒ 整体右移 ⇒ 表头 `Pot` 落在第 6 位，而数据第 6 列其实是 **UsedTime（秒）**：

        真实文件      →  工具报出
        Pot  = -17.12     energy final = 14.79   ← 秒数！
        Temp =  334.11    temperature  = -17.12  ← 能量！

    **退出码 0、照常出图出 CSV** —— 答案全错却毫无提示。
    """
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "x.ener")
        io.open(p, "w", encoding="utf-8", newline="\n").write(
            "#     Step Nr.          Time[fs]        Kin.[a.u.]          "
            "Temp[K]            Pot.[a.u.]        Cons Qty[a.u.]        UsedTime[s]\n"
            "           1            0.500000         0.001659460       "
            "349.343501168       -17.120353288       -17.118620261        96.067028747\n"
            "           2            1.000000         0.001646737       "
            "346.665137202       -17.120506495       -17.118624483        26.208263858\n")
        r = run([PY, os.path.join(HERE, "scripts", "postprocess.py"), "energy", p])
        so = (r.stdout or "") + (r.stderr or "")
        # 能量必须是 Pot（-17.12…），不能是 UsedTime（26.2…）
        e_ok = "-17.12" in so and "26.20" not in so and "14.79" not in so
        record("`.ener` 能量必须取 Pot 列，不许取 UsedTime（秒）",
               "报出 -17.12 且不含 26.20",
               "含 -17.12 且无 26.20 = {}".format(e_ok), e_ok,
               "表头多出 # / Nr. / Qty[a.u.] 三个 token，按序号定位会整体右移")
        t_ok = "346.6" in so              # 末行 Temp=346.665137202 → 打印 346.67
        record("`.ener` 温度必须取 Temp 列，不许取 Pot",
               "报出 346.6x（末行 Temp 列）",
               "取到温度 = {}".format(t_ok), t_ok,
               "错位时会把能量当温度（-17.12 K 这种明显荒谬值）")


def inject_verify_forces():
    """守 `verify_forces.py`（力-能量交叉验证）。

    这个工具是**唯一**能自动判"物理算得对不对"的判据，所以它自己错不起：
      * `emit` 必须把坐标恰好位移 ±h（多一点少一点，判据就废了）
      * `check` 对自洽数据必须通过、对矛盾数据必须**不通过**（反向对照）
      * 力太小的几何必须**警告灵敏度不足** —— 否则会给出"虚假的安全感"
    实测背景：B_ana12 那种接近 PBE 极小点的几何，所有原子力只有 ~0.02 a.u.，
    而"彻底算错"能造成的残差也是这个量级 ⇒ 若只用绝对容差 0.02，**错误的计算会"通过"**。
    所以判据改成 max(绝对下限, 2%×|F|)。
    """
    V = os.path.join(HERE, "scripts", "verify_forces.py")
    REF_INP = ("&GLOBAL\n  PROJECT ref\n  RUN_TYPE ENERGY_FORCE\n&END GLOBAL\n"
               "&FORCE_EVAL\n  METHOD Quickstep\n  &DFT\n    &SCF\n    &END SCF\n  &END DFT\n"
               "  &SUBSYS\n    &CELL\n      ABC 12 12 12\n      PERIODIC NONE\n    &END CELL\n"
               "    &COORD\n      O 0.000000 0.000000 0.117300\n"
               "      H 0.000000 0.757200 -0.469200\n"
               "      H 0.000000 -0.757200 -0.469200\n    &END COORD\n"
               "  &END SUBSYS\n&END FORCE_EVAL\n")
    F = {1: (0.0, 0.0, 0.01931835), 3: (0.0, -0.01496160, -0.01065042)}
    E0 = -17.120191736671362
    HB = 0.01 / 0.529177210903

    def mkout(E):
        rows = "\n".join("     %d      1      %s %18.8f %14.8f %14.8f"
                         % (i, "O" if i == 1 else "H", *F.get(i, (0, 0, 0)))
                         for i in (1, 2, 3))
        return (" GLOBAL| Run type: ENERGY_FORCE\n"
                " ENERGY| Total FORCE_EVAL ( QS ) energy [a.u.]:   %.15f\n"
                " ATOMIC FORCES in [a.u.]\n"
                " # Atom   Kind   Element          X              Y              Z\n"
                "%s\n" % (E, rows))

    with tempfile.TemporaryDirectory() as td:
        inp = os.path.join(td, "ref.inp")
        io.open(inp, "w", encoding="utf-8", newline="\n").write(REF_INP)
        re0 = os.path.join(td, "ref.out")
        io.open(re0, "w", encoding="utf-8", newline="\n").write(mkout(E0))
        vf = os.path.join(td, "vf")
        run([PY, V, "emit", inp, "--ref-out", re0, "-o", vf,
             "--atoms", "1", "--max-atoms", "1"])

        # ① 位移必须**恰好** ±h
        p = io.open(os.path.join(vf, "vf_a1dx_p.inp"), encoding="utf-8").read()
        m = re.search(r"(?m)^\s*O\s+([-\d.]+)\s", p)
        ok = m and abs(float(m.group(1)) - 0.01) < 1e-9
        record("emit 的 +h 位移必须恰好是 +0.01 Å",
               "O 的 x 变成 0.010000", "实得 {}".format(m.group(1) if m else "?"),
               bool(ok), "位移不准，F=−dE/dx 的判据就整体失准")

        def put(tag, E):
            io.open(os.path.join(vf, tag + ".out"), "w",
                    encoding="utf-8", newline="\n").write(mkout(E))

        # ② 自洽 ⇒ 必须通过
        for d, di in (("x", 0), ("y", 1), ("z", 2)):
            put("vf_a1d%s_p" % d, E0 - F[1][di] * HB)
            put("vf_a1d%s_m" % d, E0 + F[1][di] * HB)
        r = run([PY, V, "check", re0, vf])
        so = (r.stdout or "")
        record("check 对自洽数据必须通过（反向对照）",
               "exit=0 且含「✅ 通过」",
               "exit={} 通过={}".format(r.returncode, "✅ 通过" in so),
               r.returncode == 0 and "✅ 通过" in so,
               "工具对正确结果误报，等于废掉")

        # ③ 矛盾 ⇒ 必须不通过（z 方向两点同能量 ⇒ dE/dx=0 而 F=0.0193）
        put("vf_a1dz_p", E0)
        put("vf_a1dz_m", E0)
        r = run([PY, V, "check", re0, vf])
        so = (r.stdout or "")
        record("check 对矛盾数据必须不通过",
               "exit=1 且含「❌ 不通过」",
               "exit={} 不通过={}".format(r.returncode, "❌ 不通过" in so),
               r.returncode == 1 and "❌ 不通过" in so,
               "只用一个宽松的绝对容差时，0.0193 的残差会**蒙混过关**")

        # ④ 灵敏度预警
        r = run([PY, V, "emit", inp, "--ref-out", re0, "-o", os.path.join(td, "vf2"),
                 "--atoms", "1", "--max-atoms", "1"])
        so = (r.stdout or "")
        record("emit 对「力太小」的几何必须警告灵敏度不足",
               "含「灵敏度不足」",
               "含 = {}".format("灵敏度不足" in so), "灵敏度不足" in so,
               "力 0.019 a.u. 时信噪比太差，错误的计算也可能「通过」")

        # ⑤ 检验二：ΣF ≠ 0 必须报（这是唯一免费、且能抓"边界削密度"的信号）
        #    实测：偏心 WAVELET → 24.7；正确算例 → 0.0020。阈值 0.05。
        bad_sf = mkout(E0).replace(
            " ATOMIC FORCES in [a.u.]",
            " SUM OF ATOMIC FORCES         -1.0 -1.0 -1.0     24.72427756\n"
            " ATOMIC FORCES in [a.u.]")
        re_bad = os.path.join(td, "bad_sf.out")
        io.open(re_bad, "w", encoding="utf-8", newline="\n").write(bad_sf)
        r = run([PY, V, "check", re_bad, vf])
        so = r.stdout or ""
        ok = ("❌ 检验二" in so) and r.returncode == 1
        record("检验二：|ΣF| 超限必须判不通过",
               "exit=1 且「❌ 检验二」",
               "exit={} 报出={}".format(r.returncode, "❌ 检验二" in so), ok,
               "ΣF≠0 是「静电解错」唯一免费可见的症状")

        # ⑥ 检验三：整体平移 ΔE 超限必须报
        #    实测：正确算例 ΔE = 1.0e-4；偏心 WAVELET ΔE = 1.2e+1 —— 差 5 个数量级。
        #    这一条**才是**抓偏心 WAVELET 的关键：检验一（F=−dE/dx）对它**判通过**。
        put("vf_shift", E0 + 12.204442)
        r = run([PY, V, "check", re0, vf])
        so = r.stdout or ""
        ok = ("❌ 检验三" in so) and r.returncode == 1
        record("检验三：整体平移 ΔE 超限必须判不通过",
               "exit=1 且「❌ 检验三」",
               "exit={} 报出={}".format(r.returncode, "❌ 检验三" in so), ok,
               "偏心 WAVELET 下检验一误判通过，只有平移不变性能抓它")

        # ⑦ 反向对照：平移量正常时必须**不**报，且总结论仍为通过
        put("vf_shift", E0 + 1.0e-4)          # 实测正确算例的量级
        r = run([PY, V, "check", re0, vf])
        so = r.stdout or ""
        ok = ("❌ 检验三" not in so) and r.returncode == 1   # dz 仍是矛盾的 ⇒ 总体仍应失败
        record("检验三：平移量正常时不许误报（反向对照）",
               "无「❌ 检验三」（总结论仍因检验一失败）",
               "无误报={} exit={}".format("❌ 检验三" not in so, r.returncode), ok,
               "1.0e-4 是实测正确算例的量级，阈值 1e-2 需留足余量")


def main():
    ap = argparse.ArgumentParser(description="注入测试：证明护栏会红")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    steps = [("引用审计（越界页码）", inject_citation),
             ("溯源核验（篡改副本）", inject_provenance),
             ("RDF 归一化（挪回帧循环）", inject_rdf),
             ("FIXED_ATOMS 越界", inject_fixed_atoms),
             ("PERIODIC 两段一致性", inject_periodic_consistency),
             ("关键字别名搜索", inject_kw_alias),
             ("`.ener` 列解析", inject_ener_columns),
             ("MD 温度层（解析/假阳性/三类告警）", inject_md_temperature),
             ("videonotes 引用可溯源性", inject_videonotes_citations),
             ("上游工具链 `+` 关键字假 error", inject_plus_keyword_shim),
             ("能量行跨版本格式（(a.u.) vs [a.u.]）", inject_energy_line_format),
             ("非周期居中 / NPROC_REP / TOPOLOGY 告警 / ΣF 护栏",
              inject_periodic_none_and_force_sum),
             ("MD 取值开关必须落进输出（防静默失效）", inject_md_flags_reach_output),
             ("`.ener` 列映射（UsedTime 不许当能量）", inject_ener_header_columns),
             ("力-能量交叉验证（emit/check/灵敏度）", inject_verify_forces),
             ("GBK 兼容层缺失", inject_gbk)]
    if args.list:
        for n, _ in steps:
            print("  " + n)
        return 0

    print("=" * 78)
    print("注入测试：故意造错，看护栏会不会红")
    print("=" * 78)
    for name, fn in steps:
        print("\n### " + name)
        try:
            fn()
        except Exception as e:            # 注入本身出错也要算 FAIL，不能静默
            record(name + "（注入过程异常）", "正常完成",
                   "{}: {}".format(type(e).__name__, e), False)

    bad = [r for r in RESULTS if not r.ok]
    print()
    print("=" * 78)
    print("  注入项 {} 条：按预期响应 {} / 未按预期 {}".format(
        len(RESULTS), len(RESULTS) - len(bad), len(bad)))
    print("结论：{}".format("全部护栏都会红、且写完能复原 ✓"
                          if not bad else "{} 项未达预期 ✗".format(len(bad))))
    if args.json:
        print(json.dumps([{"case": r.name, "expect": r.expect,
                           "got": r.got, "ok": r.ok, "note": r.note}
                          for r in RESULTS], ensure_ascii=False, indent=2))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
