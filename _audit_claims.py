#!/usr/bin/env python3
"""核对知识库里"某关键字默认是 X"这类断言，对官方 `cp2k_input.xml` 逐条验证。

**为什么需要它**

知识库（A–G 层）里散着大量形如"`EPS_SCF` 默认 `1.0E-5`"的断言。它们是**结论**，
但结论会漂：抄错一位、把模板值当官方默认、跨版本改了没跟上……
2026-10 之前**只有 48 条被人工核过**，其余全靠"写的时候是对的"。

本工具把这些断言**机器抽出来、对官方 XML 逐条比对**，输出四类：

    符合      声明的默认值与 XML 一致
    不符      不一致                ← 这是要修的东西
    多义      同名关键字在多个段下默认值不同，且断言没指明是哪一段
    未解析    找不到该关键字 / 抽不出值 / 值不是可比形式（**如实列出，不假装覆盖**）

**精度优先，不追求召回。** 只抽"关键字紧邻'默认'、且后面紧跟一个值"的断言；
宁可漏掉，不可误报 —— 一个天天误报的审计工具等于没有。所以：

  * `--sample N`   看它到底抽出了什么（**用这个判断精度**）
  * `--unresolved` 看它抽到了但没核成的（**用这个判断召回损失在哪**）

**多版本**：`--xml` 可给多次（例如同时给 9.0 与 2022.1），会额外报**跨版本差异** ——
本仓库实测过这类差异确实影响结论（`ENERGY_CORRECTION/EPS_DEFAULT` 在 9.0 是 `1E-12`、
2022.1 是 `1E-7`）。

用法：

    python _audit_claims.py                        # 核 A–G 层，用随包 9.0 XML
    python _audit_claims.py --sample 25            # 看抽取质量
    python _audit_claims.py --unresolved           # 看没核成的
    python _audit_claims.py --xml a.xml --xml b.xml  # 多版本 + 跨版本差异
"""
import argparse
import glob
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

try:
    import os as _os
    import sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    for _d in (_here, _os.path.join(_here, "scripts")):
        if _d not in _sys.path:
            _sys.path.insert(0, _d)
    import _console  # noqa: F401
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))

# 只核 A–G 层（**不含** E 层原文与 H 层教材 —— 那些是"引用原文，逐字勿改"，
# 里面的"默认"可能是讲师口述或官方 PDF 的转述，不是本仓库自己的断言）。
SKIP_DIRS = (os.sep + "pdf_text" + os.sep, os.sep + "h_tutorials" + os.sep)

# 🔴 **紧邻式**断言正则 —— 这是本工具精度的全部来源。
# 第一版用"在'默认'前后各开 70/34 字符窗口里找关键字和值"，结果把大量**非断言**
# 也抽了进来（实测样本）：
#     「AIMD 默认打印的速度轨迹 `*-vel-1.xyz`」      → 抽成 AIMD 默认 -1   ✗ 行为默认
#     「PBE（默认）→ `--functional TPSS`/`SCAN`」    → 抽成 PBE 默认 SCAN   ✗ 选项默认
#     「别名是 INTERPOLATION 与 WF_INTERPOLATION」   → 抽成 默认 0.0        ✗ 根本没有默认
#     「模板默认 **50 万步**」                        → 抽成 AIMD 默认 50   ✗ 是模板默认、不是 XML
# 这些都是"默认"这个词的**其它用法**，窗口式无法区分。收紧成
#     关键字 +（≤6 个填充字）+ 默认(值) +（≤6 个填充字）+ 值
# 之后，上面四条**全部自然落选**，而真断言（`EPS_SCF` 默认值是 `1.0E-5`）照旧命中。
_FILL = r"[\s的值为是：:官方（）()]{0,6}"
# 数值：CP2K 输出/输入里 `1.0E-5`、`0.171186202615E+02` 这类 Fortran D/E 指数都要认
RE_NUM = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eEdD][-+]?\d+)?")

RE_CLAIM = re.compile(
    r"(?P<key>`[^`\n]+`|[A-Z][A-Z0-9_+]{2,})"
    + _FILL + r"默认(?:值)?" + _FILL +
    r"(?P<val>`[^`\n]+`|[-+]?\d+(?:\.\d+)?(?:[eEdD][-+]?\d+)?"
    r"|TRUE|FALSE|ON|OFF|T|F)")

# 生成型/变更记录类文件不是"知识断言"，不进审计
SKIP_FILES = ("CHANGELOG.md", "_new_items_report.md")

# **反面举例 / 更正记录**标记：这类句子里出现的"默认是 X"是**被否定的那个说法**，
# 不是本仓库的主张。实测样本：
#     「容易被读成"**CP2K 的 `MAX_FORCE` 默认是 0.0006**"」
#     「📌 更正记录二（"`L` 默认 2"）：本行原写"`L` 默认 2"，那指的是 gen_inp.py 发射的…」
# 把它们算成"不符"是**误报**，会让人不再信任审计结果。单独归类、不判不符。
CAUTION_MARKERS = ("容易被读成", "会被读成", "误读", "误以为", "误认为", "并非",
                   "不是 CP2K 默认", "更正记录", "原写", "原先", "写成", "指的是",
                   "常被当成", "有人会", "别混", "注意别", "已就地", "由 `_audit_claims")
# **工具发射值**标记：说的是 gen_inp/模板**发射**的默认，不是 CP2K 的默认。
# 这类断言本身可以是对的，只是**来源不同** —— 报成"来源需限定"而不是"不符"。
EMIT_MARKERS = ("gen_inp", "模板", "发射", "你生成", "skill 默认", "本工具")


def norm_value(text):
    """把断言里的"值"归一化成可比形式。

    返回 ``("num", float)`` / ``("logic", "T"/"F")`` / ``("word", "UPPER")`` / ``None``。
    """
    if text is None:
        return None
    s = text.strip().strip("`").strip()
    s = s.strip("，。；,;、（）()【】[]")
    if not s:
        return None
    # 纯数字（含 Fortran 指数、千分位不认）
    m = re.fullmatch(RE_NUM, s)
    if m:
        try:
            return ("num", float(s.replace("D", "E").replace("d", "e")))
        except ValueError:
            return None
    u = s.upper()
    if u in ("T", "TRUE", "ON", "YES"):
        return ("logic", "T")
    if u in ("F", "FALSE", "OFF", "NO"):
        return ("logic", "F")
    # 纯 ASCII 词（枚举值，如 NVE / ASPC / MULLIKEN）
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_\-]*", s):
        return ("word", u)
    return None


def xml_value(text):
    """把 XML 里的 DEFAULT_VALUE 归一化成同一种形式。

    ⚠️ 有些关键字的默认值是**向量**（如 `EXTERNAL_PRESSURE` 的
    `1.0E2 0 0 0 1.0E2 0 0 0 1.0E2`：3×3 张量、对角 100 bar）。
    先前一律按标量比，于是"`EXTERNAL_PRESSURE` 默认 100 bar"这条**正确**的断言
    被误判成"不符"。这里的分派：

      * 全部分量相等 ⇒ 取该标量（张量对角各向同性，断言写标量是合理的）
      * 分量不全等 ⇒ 返回 ``(word, "<向量:a b c…>")``，与标量断言**天然不可比**，
        由调用方归入"不可比"并如实说明 —— **不猜**。
    """
    if text is None:
        return None
    s = text.strip()
    if not s or s == "-":
        return None
    parts = s.split()
    if len(parts) > 1:
        nums = []
        for p in parts:
            n = norm_value(p)
            if not n or n[0] != "num":
                return ("word", "<向量:{}>".format(s[:40]))
            nums.append(n[1])
        if all(abs(x - nums[0]) <= max(1e-12, 1e-9 * abs(nums[0])) for x in nums):
            return ("num", nums[0])
        # 3×3 **对称张量**（9 个分量，如 EXTERNAL_PRESSURE 的
        # `1E2 0 0 0 1E2 0 0 0 1E2`）：对角各向同性时，断言写"默认 = 对角值"
        # 是物理上正确的读法（三个方向各 1 atm）。先前一律判"不可比"，
        # 把 `EXTERNAL_PRESSURE` 官方默认 100 bar 这条**正确**断言误判成了"不符"。
        if len(nums) == 9:
            diag = (nums[0], nums[4], nums[8])
            off = [nums[i] for i in (1, 2, 3, 5, 6, 7)]
            if all(abs(x - diag[0]) <= max(1e-12, 1e-9 * abs(diag[0])) for x in diag) \
                    and all(abs(x) <= 1e-12 for x in off):
                return ("num", diag[0])
        return ("word", "<向量:{}>".format(s[:40]))
    n = norm_value(s)
    if n:
        return n
    if s.upper() in ("T", "F"):
        return ("logic", s.upper())
    return ("word", s.upper())


# 常见的 **VASP** 关键字（本课程同时讲 VASP，知识库里混着两套关键字）。
# 它们不该被当成"CP2K 关键字没找到" —— 那是**归错类**，会制造噪声。
VASP_KEYWORDS = {
    "SMASS", "EDIFFG", "NBLOCK", "KBLOCK", "ISIF", "ISMEAR", "SIGMA", "ENCUT",
    "EDIFF", "PREC", "IBRION", "NSW", "POTIM", "TEBEG", "TEEND", "NELM",
    "ALGO", "LREAL", "LWAVE", "LCHARG", "ICHARG", "NBANDS", "ISPIN", "MAGMOM",
    "NEDOS", "LORBIT", "IDIPOL", "LDIPOL", "DIPOL", "INCREM", "ICONST",
    "LBLUEOUT", "REPORT", "SHAKETOL", "SHAKEMAXITER", "MDALGO", "ANDERSEN_PROB",
    "NOSE_H", "PMASS", "POMASS", "ROPT", "ZVAL", "ISTART", "INIWAV", "NELMIN",
    "NELMDL", "BMIX", "AMIX", "IMIX", "LMAXMIX", "IVDW", "LVDW", "LASPH",
}


def cmp_value(a, b):
    """比较断言值与 XML 值。数字用相对/绝对混合容差。"""
    if a is None or b is None:
        return None
    if a[0] != b[0]:
        # 允许 "1" 与 "T"？不允许 —— 类型不同就是不符，但要能说清楚
        return False
    if a[0] == "num":
        x, y = a[1], b[1]
        scale = max(abs(x), abs(y), 1e-30)
        return abs(x - y) <= max(1e-12, 1e-4 * scale)
    return a[1] == b[1]


# --------------------------------------------------------------------------
# XML 索引
# --------------------------------------------------------------------------
class XmlIndex:
    """把 XML 展平成 ``path/tuple -> info`` 与 ``NAME -> [(path, info)]`` 两张表。"""

    def __init__(self, path):
        self.path = path
        self.by_path = {}
        self.by_name = {}
        self.version = "(未标注)"
        root = ET.parse(path).getroot()
        v = root.find(".//CP2K_VERSION")
        if v is not None and v.text:
            self.version = v.text.strip()

        def walk(node, trail):
            for ch in node:
                if ch.tag == "SECTION":
                    nm = ch.find("NAME")
                    if nm is None or not nm.text:
                        continue
                    walk(ch, trail + (nm.text.strip().upper(),))
                elif ch.tag == "KEYWORD":
                    names = [n.text.strip().upper() for n in ch.findall("NAME")
                             if n.text and n.text.strip()]
                    if not names:
                        continue
                    d = ch.find("DEFAULT_VALUE")
                    u = ch.find("DEFAULT_UNIT")
                    en = [n.text.strip().upper()
                          for n in ch.findall("DATA_TYPE/ENUMERATION/ITEM/NAME")
                          if n.text and n.text.strip()]
                    info = {"default": xml_value(d.text if d is not None else None),
                            "unit": (u.text or "").strip() if u is not None else "",
                            "enum": en, "path": "/".join(trail + (names[0],))}
                    self.by_path[trail + (names[0],)] = info
                    for nm in names:
                        self.by_name.setdefault(nm, []).append(info)

        walk(root, ())

    def resolve(self, token):
        """解析断言里的关键字，返回 ``(candidates, note)``。

        **刻意返回候选列表而不是单个结果**：本仓库大量断言只写
        `` `MAX_FORCE` 默认 `4.5E-4` `` 而**不写它在哪一段**，而 `MAX_FORCE`
        在 XML 里出现在多个段、默认值各不相同（实测这类占未解析项的 ~65%）。
        把"没写段"一律报成"多义"等于把最有价值的一批断言扔进垃圾桶；
        正确做法是**拿断言给的值去候选里找** —— 找得到就是"符合（但建议补段）"，
        一个都找不到才是真"不符"。
        """
        t = token.strip().strip("`")
        if "/" in t:
            key = tuple(x.strip().upper() for x in t.split("/") if x.strip())
            info = self.by_path.get(key)
            if info:
                return [info], ""
            cands = [v for k, v in self.by_path.items() if k[-len(key):] == key]
            if len(cands) == 1:
                return cands, "按路径后缀唯一匹配"
            if len(cands) > 1:
                return cands, "路径后缀匹配到 {} 处".format(len(cands))
            return [], "XML 里没有这个路径"
        name = t.upper()
        hits = self.by_name.get(name, [])
        if not hits:
            return [], "XML 里没有这个关键字名"
        if len(hits) == 1:
            return hits, ""
        return hits, "同名 {} 处".format(len(hits))


# --------------------------------------------------------------------------
# 断言抽取
# --------------------------------------------------------------------------
class Claim:
    __slots__ = ("file", "line", "key", "val", "raw")

    def __init__(self, file, line, key, val, raw):
        self.file, self.line, self.key, self.val, self.raw = file, line, key, val, raw


def extract_claims(path):
    """从一份文档里抽"关键字 + 默认值"断言。

    **只认紧邻式写法**（见 `RE_CLAIM` 上方注释）。宁可少抽，不可误报 ——
    一个总是误报的审计工具会让人直接忽略它，比没有更糟。
    召回损失由 `--unresolved` 与 `--sample` 如实呈现。
    """
    out = []
    try:
        text = io.open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return out
    for ln_no, line in enumerate(text.splitlines(), 1):
        for m in RE_CLAIM.finditer(line):
            key = m.group("key").strip().strip("`").strip()
            if not key or key[0].isdigit():
                continue
            # 关键字形状校验：全大写（可带 _ + 数字与 / 路径），或反引号里的路径
            if "/" not in key and not re.fullmatch(r"[A-Z][A-Z0-9_+\-]*", key):
                continue
            if "/" in key and not re.fullmatch(r"[A-Za-z0-9_+/]+", key):
                continue
            val = norm_value(m.group("val"))
            if val is None:
                continue
            out.append(Claim(os.path.relpath(path, ROOT), ln_no, key, val,
                             line.strip()[:150]))
    return out


# --------------------------------------------------------------------------
def collect_files():
    pats = [os.path.join(ROOT, "references", "**", "*.md"),
            os.path.join(ROOT, "*.md")]
    files = []
    for p in pats:
        for f in glob.glob(p, recursive=True):
            if any(s in f for s in SKIP_DIRS):
                continue
            if os.path.basename(f) in SKIP_FILES:
                continue
            files.append(f)
    return sorted(set(files))


def default_xmls():
    """默认用随包那份 XML；`CP2K_INPUT_XML` 环境变量（与 `_kw_probe.py` 同一约定）
    可指向别的版本 —— 多版本差异正是这个工具要报的东西之一。"""
    xs = []
    try:
        import cp2k_input_tools
        p = os.path.join(os.path.dirname(cp2k_input_tools.__file__), "cp2k_input.xml")
        if not os.path.isfile(p):
            p = os.path.join(os.path.dirname(cp2k_input_tools.__file__),
                             "data", "cp2k_input.xml")
        if os.path.isfile(p):
            xs.append(p)
    except Exception:
        pass
    # 与 `_kw_probe.py` 同一约定：设了 `CP2K_INPUT_XML` 就用它（可指向任意版本，
    # 例如官方手册上的 `https://manual.cp2k.org/cp2k-2022_1-branch/cp2k_input.xml`）。
    env = os.environ.get("CP2K_INPUT_XML")
    if env and os.path.isfile(env):
        xs.append(env)
    # 去重（env 可能指的就是随包那份）
    seen, uniq = set(), []
    for x in xs:
        rp = os.path.realpath(x)
        if rp not in seen:
            seen.add(rp)
            uniq.append(x)
    return uniq


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="核对知识库里「关键字默认值」断言 vs 官方 cp2k_input.xml",
        epilog="精度优先：--sample 看抽到了什么，--unresolved 看漏在哪。")
    ap.add_argument("--xml", action="append", default=None,
                    help="官方输入参考 XML（可重复给多个版本）；不给则用随包的 9.0")
    ap.add_argument("--sample", type=int, default=0, metavar="N",
                    help="打印前 N 条抽到的断言（用于人工判断抽取精度）")
    ap.add_argument("--unresolved", action="store_true",
                    help="列出「抽到了但没核成」的断言与原因（召回损失所在）")
    ap.add_argument("--mismatch-only", action="store_true", help="只打印不符项")
    args = ap.parse_args(argv)

    xmls = args.xml or default_xmls()
    if not xmls:
        print("错误：找不到官方 cp2k_input.xml。请装 cp2k-input-tools，或用 --xml 指定。")
        return 3
    idxs = []
    for x in xmls:
        if not os.path.isfile(x):
            print("错误：--xml 指向的文件不存在：{}".format(x))
            return 1
        try:
            idxs.append(XmlIndex(x))
        except Exception as e:
            print("错误：解析不了 {}：{}".format(x, e))
            return 1

    files = collect_files()
    claims = []
    for f in files:
        claims.extend(extract_claims(f))

    primary = idxs[0]
    ok = ok_amb = bad = unres = 0
    bad_list, amb_list, unres_list = [], [], []
    version_diff = []

    for c in claims:
        cands, note = primary.resolve(c.key)
        if not cands:
            unres += 1
            tag = note
            if c.key.upper() in VASP_KEYWORDS:
                tag = "疑似 **VASP** 关键字（本课程同时讲 VASP，不属 CP2K XML）"
            unres_list.append((c, tag))
            continue
        usable = [x for x in cands if x["default"] is not None]
        if not usable:
            unres += 1
            unres_list.append((c, "XML 里该关键字没有 DEFAULT_VALUE"))
            continue
        hit = [x for x in usable if cmp_value(c.val, x["default"]) is True]
        if hit:
            if len(usable) > 1:
                # 值对上了，但断言没写在哪一段 —— 记一笔"建议补段"，不算错
                ok_amb += 1
                amb_list.append((c, "同名 {} 处，值匹配其中 {} 处（结论对，但建议补上段路径）"
                                 .format(len(usable), len(hit))))
            else:
                ok += 1
            # 跨版本差异：**只对"在本版通过"的断言才有意义** ——
            # 本版就不通过的另有"不符"一节在管，重复报只会制造噪声。
            if len(idxs) > 1:
                others = []
                for o in idxs[1:]:
                    oc, _n = o.resolve(c.key)
                    ovs = {x["default"] for x in oc if x["default"] is not None}
                    if ovs and not any(cmp_value(c.val, v) for v in ovs):
                        others.append((o.version, sorted(str(v) for v in ovs)[:3]))
                if others:
                    version_diff.append((c, others))
        else:
            # 先分辨两种"看起来像错、其实不是错"的情况，避免误报
            _raw = c.raw
            if any(k in _raw for k in CAUTION_MARKERS):
                unres += 1
                unres_list.append((c, "反面举例/更正记录（句中那个说法是被否定的），不判不符"))
            elif any(k in _raw for k in EMIT_MARKERS):
                unres += 1
                unres_list.append((c, "说的是 **gen_inp/模板发射值**，不是 CP2K 默认 —— "
                                      "建议在原文里写明来源限定词"))
            else:
                bad += 1
                bad_list.append((c, usable, note))
        # （跨版本差异已在上面的 `if hit:` 分支里记 —— 那里的注释说明了为什么
        #   只对"在本版通过"的断言才报：本版就不通过的另有"不符"一节在管。）

    total = len(claims)
    print("=" * 74)
    print("默认值断言核对　·　知识库 A–G 层")
    print("=" * 74)
    print("  扫描文件   : {} 个".format(len(files)))
    print("  抽到断言   : {} 条（精度优先策略，**召回有意保守**）".format(total))
    for x in idxs:
        print("  XML        : {}  ←  {}".format(x.version, x.path))
    print()
    print("  ✅ 符合     : {}（其中 {} 条同名多处、按值匹配成功，**建议补上段路径**）".format(
        ok + ok_amb, ok_amb))
    print("  ❌ 不符     : {}".format(bad))
    print("  ❔ 未解析   : {}（找不到关键字 / XML 无默认值 / 值不可比）".format(unres))
    if total:
        print("  可核对率   : {:.1f}%（= (符合+不符) / 抽到）".format(
            100.0 * (ok + ok_amb + bad) / total))

    if args.sample and total:
        print("\n--- 抽取抽样（人工判断**精度**用）---")
        for c in claims[:args.sample]:
            print("  {}:{}  key={}  val={}  | {}".format(
                c.file, c.line, c.key, c.val, c.raw[:80]))

    if bad_list and not args.sample:
        print("\n--- ❌ 不符（**这些是要修的**）---")
        for c, cands, note in bad_list:
            print("  {}:{}".format(c.file, c.line))
            print("     断言 : {} 默认 {}".format(c.key, c.val))
            for info in cands[:3]:
                print("     XML  : {} = {} {}".format(
                    info["path"], info["default"],
                    "[{}]".format(info["unit"]) if info["unit"] else ""))
            if len(cands) > 3:
                print("     …另有 {} 处候选".format(len(cands) - 3))
            print("     原文 : {}".format(c.raw[:118]))

    if amb_list and args.unresolved:
        print("\n--- ⚠️ 结论对、但断言没写明段（建议补路径）---")
        for c, note in amb_list[:25]:
            print("  {}:{}  {}  ← {}".format(c.file, c.line, c.key, note))

    if args.unresolved:
        print("\n--- ❔ 未解析（召回损失所在；**不是错误**）---")
        for c, note in unres_list[:40]:
            print("  {}:{}  {}  ← {}".format(c.file, c.line, c.key, note))
        if len(unres_list) > 40:
            print("  …还有 {} 条".format(len(unres_list) - 40))

    if version_diff:
        print("\n--- 🔀 跨版本差异（同一断言在别的 CP2K 版本上对不上）---")
        for c, others in version_diff:
            print("  {}:{}  {}（断言 {}）".format(c.file, c.line, c.key, c.val))
            for v, d in others:
                print("     {} 上候选默认值：{}".format(v, " / ".join(d)))

    print()
    # 稳定的**机器可判**结论行（CI 与 `_validate_all_suites.py` 按它判红/绿）。
    # 不要拿"不符"这种子串去判 —— `不符     : 0` 与 `不符     : 5` 都含它。
    if bad:
        print("结论：{} 条不符 ✗（见上方清单；按项目约定就地更正并留更正记录）".format(bad))
    else:
        print("结论：无不符 ✓（符合 {} / 未解析 {}，共 {} 条）".format(
            ok + ok_amb, unres, total))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
