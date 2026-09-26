#!/usr/bin/env python3
"""文档口径一致性自检（零依赖，纯标准库）。

背景：本 skill 的文档里散布着若干「数字口径」——阶段数、模板数、校验用例数、
子命令数、示例输入数等。这些数字一旦和代码实际行为脱节，就会误导使用者
（历史上前一版本就出现过 "23 类" vs "15 类" 同页自相矛盾）。

本脚本的做法是**不硬编码真值**，而是：
  1) 从代码/目录**实测**出真值（数模板文件、数 STAGES、数子命令…）；
  2) 扫描文档中的口径表述，检查是否与真值一致；
  3) 报出所有不一致处，退出码非 0。

用法：
    python _doc_consistency.py           # 检查全部
    python _doc_consistency.py --list    # 只打印实测真值

退出码：0 = 全部一致；1 = 发现不一致；3 = 环境问题（脚本缺失等）。

G 层（references/official/）额外检查：
  * 每个 G 层 .md 是否带「来源：」与「抓取日期：」头部（溯源合规）；
  * SKILL.md / README.md 的分层表是否收录 G 层。
"""
import os
import re
import sys

# --- 控制台编码兼容层（中文 Windows/GBK 下输出 ✓ ⑪ Å 等符号不再抛异常）---
try:
    import os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    for _d in (_here, _os.path.join(_here, "scripts")):
        if _d not in _sys.path:
            _sys.path.insert(0, _d)
    import _console  # noqa: F401  导入即生效，见 scripts/_console.py
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 真值探测：全部来自实测，不写死
# ---------------------------------------------------------------------------
def truth_templates():
    """references/templates/*.inp 的实际数量。"""
    d = os.path.join(HERE, "references", "templates")
    if not os.path.isdir(d):
        return None
    return len([f for f in os.listdir(d) if f.endswith(".inp")])


def truth_stages():
    """guide.py 中 STAGES 的总条数 / 主线数 / 续算分支数。"""
    p = os.path.join(HERE, "scripts", "guide.py")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as fh:
        src = fh.read()
    m = re.search(r"^STAGES\s*=\s*\[", src, re.M)
    if not m:
        return None
    # 用 key 出现次数估算阶段条数（每个 stage dict 恰好一个 "key":）
    seg_start = m.start()
    # 截到 STAGE_BY_KEY 定义处
    end = src.find("STAGE_BY_KEY", seg_start)
    seg = src[seg_start:end if end > 0 else len(src)]
    keys = re.findall(r'"key"\s*:\s*"([a-z_]+)"', seg)
    total = len(keys)
    resume = 1 if "resume" in keys else 0
    return {"total": total, "main": total - resume, "resume": resume, "keys": keys}


def truth_validate_cases():
    """_validate_all.py 实跑时报告的用例数。

    脚本里用例是 `cases = [ ("name", [args...]), ... ]` 的元组列表，
    这里按缩进为 8 空格的元组首元素计数（与脚本实际结构一致）。
    """
    p = os.path.join(HERE, "_validate_all.py")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as fh:
        src = fh.read()
    m = re.search(r"^\s*cases\s*=\s*\[(.*?)\n\s*\]", src, re.S | re.M)
    if not m:
        return None
    body = m.group(1)
    # 每个用例以 `("name", [` 开头
    names = re.findall(r'\(\s*"([A-Za-z0-9_]+)"\s*,\s*\[', body)
    return len(names) or None


def truth_verify_out():
    """verify_out/*.inp 数量。"""
    d = os.path.join(HERE, "verify_out")
    if not os.path.isdir(d):
        return None
    return len([f for f in os.listdir(d) if f.endswith(".inp")])


def truth_subcommands():
    """postprocess.py 的子命令数量（从源码 argparse 定义数）。"""
    p = os.path.join(HERE, "scripts", "postprocess.py")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as fh:
        src = fh.read()
    m = re.search(r"add_subparsers\((.*?)\)", src, re.S)
    if not m:
        return None
    # 数 add_parser( 调用次数
    return len(re.findall(r"add_parser\(", src))


def truth_layer_count():
    """知识分层数：references 目录下 A–H 各层实际存在的文件数（信息性）。"""
    refs = os.path.join(HERE, "references")
    if not os.path.isdir(refs):
        return None
    layers = {
        "A": ["decide.md"],
        "B": ["course_learned.md"],
        "C": ["course_notes.md", "course_survey.md"],
        "D": ["manual_notes.md", "_manual_tree.txt", "sections.md"],
        "E": ["pdf_text"],
        "F": ["playbook.md"],
        "G": ["official"],
        "H": ["h_tutorials"],
    }
    out = {}
    for k, files in layers.items():
        out[k] = sum(1 for f in files if os.path.exists(os.path.join(refs, f)))
    return out


def truth_h_tutorials():
    """H 层（官方教程与实战算例）的文件统计。

    与 G 层的区别：G 是官网/手册的**参考条目**采集；H 是**官方教材正文**
    ＋ **真实生产算例**（可运行的输入卡与真实 .out）。两者都要在文档里登记。
    """
    d = os.path.join(HERE, "references", "h_tutorials")
    if not os.path.isdir(d):
        return None
    txt = os.path.join(d, "txt")
    notes = os.path.join(d, "notes")
    cases = os.path.join(d, "cases")
    return {
        "exists": True,
        "n_txt": len([f for f in os.listdir(txt)
                      if f.endswith(".txt")]) if os.path.isdir(txt) else 0,
        "n_notes": len([f for f in os.listdir(notes)
                        if f.endswith(".md")]) if os.path.isdir(notes) else 0,
        "n_cases": len([f for f in os.listdir(cases)
                        if f.endswith(".inp")]) if os.path.isdir(cases) else 0,
        "has_readme": os.path.isfile(os.path.join(d, "README.md")),
        "has_extract": os.path.isfile(os.path.join(d, "extract_tutorials.py")),
    }


def truth_videonotes():
    """E 层的 `videonotes/` 子层（课程视频精读笔记·第二轮）的文件统计。

    它和 `learn_L*.md`（第一轮）是**两次独立通读**，互补：第一轮读讲义+字幕、
    第二轮读**录屏**（带 `[mm:ss]` 时间戳，且 6 份与 `S1.1–S5.txt` 一一对应）。
    单列统计的用途：**防止这个子层被误删或漏登记而无人发现** ——
    它不在 SKILL.md 自动加载范围内，没有护栏就很容易在重构里悄悄消失。
    """
    d = os.path.join(HERE, "references", "pdf_text", "videonotes")
    if not os.path.isdir(d):
        return None
    n_md = 0
    for sub in os.listdir(d):
        p = os.path.join(d, sub)
        if os.path.isdir(p):
            n_md += len([f for f in os.listdir(p) if f.endswith(".md")])
    return {
        "exists": True,
        "n_notes": n_md,
        "has_readme": os.path.isfile(os.path.join(d, "README.md")),
    }


def truth_official_files():
    """G 层 references/official/*.md 的数量（不含 README/_sources 则另行区分）。"""
    d = os.path.join(HERE, "references", "official")
    if not os.path.isdir(d):
        return None
    names = sorted(f for f in os.listdir(d) if f.endswith(".md"))
    return {"total": len(names), "names": names}


def truth_official_sources():
    """G 层每个 .md 是否带「来源：」与「抓取日期」头部（溯源合规性）。"""
    d = os.path.join(HERE, "references", "official")
    if not os.path.isdir(d):
        return None
    missing = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".md"):
            continue
        p = os.path.join(d, f)
        with open(p, encoding="utf-8", errors="replace") as fh:
            head = fh.read(2000)
        # _sources.md 与 README.md 自身即溯源清单，放宽要求
        if f in ("_sources.md", "README.md"):
            continue
        if "来源" not in head or "抓取日期" not in head:
            missing.append(f)
    return missing


def truth_examples():
    """examples/NN_xxx/ 示例目录数（不含 examples/README.md）。"""
    d = os.path.join(HERE, "examples")
    if not os.path.isdir(d):
        return None
    dirs = sorted(n for n in os.listdir(d)
                  if os.path.isdir(os.path.join(d, n)) and not n.startswith("."))
    # 每个示例目录必须含 README.md 与至少一个 .inp
    incomplete = []
    for n in dirs:
        p = os.path.join(d, n)
        has_readme = os.path.isfile(os.path.join(p, "README.md"))
        has_inp = any(f.endswith(".inp") for f in os.listdir(p))
        if not (has_readme and has_inp):
            incomplete.append(n)
    return {"total": len(dirs), "names": dirs, "incomplete": incomplete}


def truth_entry_files():
    """跨 agent 入口文件是否齐备。AGENTS.md 为唯一真源，其余为指针。"""
    required = ["AGENTS.md"]
    pointers = ["CLAUDE.md", ".cursorrules", "GEMINI.md",
                os.path.join(".github", "copilot-instructions.md")]
    missing_req = [f for f in required if not os.path.isfile(os.path.join(HERE, f))]
    missing_ptr = [f for f in pointers if not os.path.isfile(os.path.join(HERE, f))]
    return {"required_missing": missing_req, "pointer_missing": missing_ptr}


def truth_cli_json_support():
    """各 CLI 是否支持 --json。

    注意 `--json` 可能挂在**子命令**上而不是顶层：
    `postprocess.py --help` 不含 `--json`，但 `postprocess.py rdf --help` 含
    （17 个子命令各自都有）。所以顶层 help 查不到时，再探几个子命令 help，
    否则会误报"postprocess.py 不支持 --json"。
    """
    import subprocess
    clis = ["guide.py", "recommend.py", "gen_inp.py", "validate_inp.py",
            "parse_output.py", "diagnose.py", "postprocess.py", "doctor.py"]
    # 顶层 help 查不到时，用这些子命令名再探一次
    SUBCOMMAND_PROBES = ("rdf", "list", "energy")

    def _has_json(args):
        # 子进程经 _console 统一输出 UTF-8，这里必须按 UTF-8 解码，
        # 否则中文 Windows(GBK) 下会 UnicodeDecodeError → 误报"不支持 --json"。
        r = subprocess.run([sys.executable] + args,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        return ("--json" in r.stdout) or ("--json" in r.stderr)

    out = {}
    for c in clis:
        p = os.path.join(HERE, "scripts", c)
        if not os.path.isfile(p):
            continue
        try:
            found = _has_json([p, "--help"])
            if not found:
                for sub in SUBCOMMAND_PROBES:
                    try:
                        if _has_json([p, sub, "--help"]):
                            found = True
                            break
                    except Exception:
                        continue
            out[c] = found
        except Exception:
            out[c] = False
    return out


# ---------------------------------------------------------------------------
# 代码健壮性不变量
# 防止「中文 Windows(GBK) 下崩溃」这一类缺陷回归（v2.7.0 实测缺陷）。
# ---------------------------------------------------------------------------
ENTRY_POINTS = [
    "scripts/doctor.py", "scripts/wizard.py", "scripts/guide.py",
    "scripts/recommend.py", "scripts/gen_inp.py", "scripts/validate_inp.py",
    "scripts/parse_output.py", "scripts/diagnose.py", "scripts/postprocess.py",
    # 力-能量交叉验证：唯一能自动判"物理算得对不对"的判据（F = −dE/dx）
    "scripts/verify_forces.py",
    "_doc_consistency.py", "_validate_all.py", "_validate_postprocess.py",
    "_validate_postprocess_analytic.py", "_official_validate.py",
    # E 层的维护脚本也面向用户直接运行，同样要能在中文 Windows 下不崩
    "references/pdf_text/extract_pdf.py",
    "references/pdf_text/extract_subtitles.py",
    "references/pdf_text/build_mapping.py",
    # H 层（官方教程与实战算例）的抽取脚本同理
    "references/h_tutorials/extract_tutorials.py",
    # H 层的非 PDF 素材抽取（旧版 .doc → 文本，纯标准库 OLE2 解析）
    "references/h_tutorials/extract_doc.py",
    # 维护审计工具：抽【新】条目并核对是否落进消费层（MAINTENANCE.md Phase 3 的核验手段）
    "_collect_new_items.py",
    # 权威查询工具：直查官方 cp2k_input.xml 拿关键字的默认值/单位
    "_kw_probe.py",
    # 默认值断言审计：把 A–G 层"某关键字默认是 X"的断言机器抽出来，对 XML 逐条核
    # （此前只有 48 条被人工核过，其余全靠"写的时候是对的"）
    "_audit_claims.py",
    # H 层引用审计：核验 notes/*.md 的 T** P** 页码能否回 txt/ 对上（H 层的核心承诺）
    "_audit_h_citations.py",
    # E 层 videonotes 引用审计：笔记名能否唯一解析 + L### 行号是否越界
    # （本轮新增 173 条 `videonotes/… L###` 引用，此前这一层没有任何工具在守）
    "_audit_videonotes_citations.py",
    # RDF 归一化的解析型验证（多帧配位数 = 直接计数）
    "_validate_rdf_cn.py",
    # cases/ 溯源核验（清单 sha256 vs 副本/源文件重算）
    "_verify_case_provenance.py",
    # 真实数据回归（真实 .out / 轨迹；源目录不可用时如实 SKIP）
    "_validate_real_data.py",
    # GBK 控制台回归（强制 GBK 编码跑全部入口，抓"忘挂 _console 兼容层"）
    "_validate_gbk.py",
    # 注入测试：故意造错证明各护栏会红（防"假绿"）
    "_inject_test.py",
    # 一键跑全部验证（分组呈现，区分 PASS / SKIP）
    "_validate_all_suites.py",
    # 由官方 cp2k_input.xml 重新生成 scripts/_cp2k_sections.py（校验器的段名全量表）
    "_gen_cp2k_sections.py",
]


def truth_wizard_flags():
    """`gen_inp.py` 的**带值开关**是否都登记进了 `wizard.py` 的旗标集合。

    `wizard.py` 用 `VALUE_FLAGS` / `MULTI_VALUE_FLAGS` 拆用户手改过的命令行；
    漏登记一个带值开关，它就会把该开关的**值**当成独立 token
    （删开关时值残留，或反过来把值当开关）。

    两份清单原先是各自手工维护的，**已经漂移**：实测漏了 27 个
    （`--timestep`/`--timecon`/`--steps`/`--walltime`/`--xyz-init`/`--xyz-final`/
    `--rotate-frames`/`--align-frames`/`--plus-u-method`/`--qs-eps`/`--print-style` …）。
    所以这里**不硬编码清单**，而是直接解析 `gen_inp.py` 的 argparse 调用实测。
    """
    import ast
    gi = os.path.join(HERE, "scripts", "gen_inp.py")
    wz = os.path.join(HERE, "scripts", "wizard.py")
    if not (os.path.isfile(gi) and os.path.isfile(wz)):
        return []
    try:
        with open(gi, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError) as e:
        # **不能静默返回 []** —— 那会让"无法核验"看起来像"核验通过"。
        # 本项目对 SKIP 的态度是"SKIP 不是通过"，这里同理：解析不了就如实报。
        return ["无法解析 scripts/gen_inp.py（{}: {}）⇒ "
                "本项**没有核验**，别当成通过".format(type(e).__name__, e)]
    single, multi = set(), set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and getattr(node.func, "attr", "") == "add_argument"):
            continue
        opts = [a.value for a in node.args
                if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        if not opts:
            continue
        kw = {k.arg: k.value for k in node.keywords}
        if getattr(kw.get("action"), "value", None) in (
                "store_true", "store_false", "count", "help", "version"):
            continue                      # 布尔开关不带值
        name = ([o for o in opts if o.startswith("--")] or opts)[0]
        (multi if getattr(kw.get("nargs"), "value", None) in ("+", "*")
         else single).add(name)
    with open(wz, encoding="utf-8") as fh:
        wsrc = fh.read()

    def grab(n):
        m = re.search(n + r"\s*=\s*\{(.*?)\}", wsrc, re.S)
        return set(re.findall(r'"(--?[\w\-]+)"', m.group(1))) if m else set()

    known = grab("VALUE_FLAGS") | grab("MULTI_VALUE_FLAGS")
    out = []
    miss_s = sorted(single - known)
    miss_m = sorted(multi - known)
    if miss_s:
        out.append("gen_inp.py 的带值开关漏在 wizard.py `VALUE_FLAGS` 里（{} 个）：{}"
                   .format(len(miss_s), "、".join(miss_s)))
    if miss_m:
        out.append("gen_inp.py 的多值开关（nargs=+/*）漏在 wizard.py "
                   "`MULTI_VALUE_FLAGS` 里（{} 个）：{}"
                   .format(len(miss_m), "、".join(miss_m)))
    return out


def truth_console_compat():
    """入口脚本是否都挂了 scripts/_console.py 控制台兼容层。

    没挂的入口在中文 Windows（控制台代码页 936/GBK）下，一旦 print 出
    ✓ ✗ • ⚠ ✖ ⑪ ↻ Å ² ³ 这类 GBK 无法表示的字符，就会抛
    UnicodeEncodeError 并打印 traceback —— 违反 AGENTS.md §6.3 健壮性基线。
    """
    import ast
    missing = []
    for rel in ENTRY_POINTS:
        p = os.path.join(HERE, rel)
        if not os.path.isfile(p):
            continue
        try:
            tree = ast.parse(open(p, encoding="utf-8").read())
        except SyntaxError:
            missing.append(rel)
            continue
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(a.name == "_console" for a in node.names):
                    found = True
            elif isinstance(node, ast.ImportFrom):
                if node.module == "_console":
                    found = True
        if not found:
            missing.append(rel)
    return missing


def truth_locale_safe_io():
    """文本 I/O 是否都可能跟随 locale（中文 Windows = GBK）。

    检查两类：
      1. 文本 open() 未指定 encoding → 读 UTF-8 模板抛 UnicodeDecodeError
         （曾使 `--type aimd_md` 完全不可用），写文件遇 GBK 无法表示的字符抛
         UnicodeEncodeError。
      2. subprocess 用了 text=True 却未指定 encoding → 按 locale 解码子进程
         输出。子进程经 _console 统一输出 UTF-8，解码失败会让内部读取线程抛
         UnicodeDecodeError，返回值属性变成 None（随后 AttributeError）。

    两类**误报**要排除（否则护栏会变噪音、被人无视）：
      * `xxx.open(...)` 这类**属性调用**是第三方库自己的 API（如
        `pdfplumber.open`），它自己管编码，不是内建 `open`；
      * 二进制模式（`"rb"`/`"wb"`/`"ab"`）**本来就不接受 encoding**。
    返回人类可读的问题列表。
    """
    import ast
    bad = []
    for rel in ENTRY_POINTS:
        p = os.path.join(HERE, rel)
        if not os.path.isfile(p):
            continue
        src = open(p, encoding="utf-8").read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        lines = src.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            kw = {k.arg for k in node.keywords}
            if isinstance(fn, ast.Name) and fn.id == "open":
                if "encoding" in kw:
                    continue
                # 取 mode：第 2 个位置参数或关键字 mode
                mode = None
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                for k in node.keywords:
                    if k.arg == "mode" and isinstance(k.value, ast.Constant):
                        mode = k.value.value
                if isinstance(mode, str) and "b" in mode:
                    continue  # 二进制模式不涉及编码
                bad.append("{0}:{1}  open() 未指定 encoding —— {2}".format(
                    rel, node.lineno, lines[node.lineno - 1].strip()[:60]))
            elif isinstance(fn, ast.Attribute) and fn.attr in (
                    "run", "Popen", "check_output", "call"):
                # 只看真正做文本解码的调用
                textual = ("text" in kw) or ("universal_newlines" in kw) \
                    or ("encoding" in kw)
                if textual and "encoding" not in kw:
                    bad.append("{0}:{1}  subprocess 文本模式未指定 encoding —— {2}".format(
                        rel, node.lineno, lines[node.lineno - 1].strip()[:60]))
    return bad


# ---------------------------------------------------------------------------
# 文档扫描：检查口径表述是否与真值一致
# ---------------------------------------------------------------------------
DOCS = ["SKILL.md", "README.md", "USAGE.md", "AGENTS.md",
        "references/workflow.md", "references/MAINTENANCE.md",
        "references/playbook.md", "references/decide.md",
        "references/postprocess.md"]

problems = []


def _read(rel):
    p = os.path.join(HERE, rel)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read().splitlines()


def _scan(rel, patterns, label, expected, allow=()):
    """在 rel 中扫 patterns（正则，需含一个数字组），比对 expected。

    ⚠️ 匹配前会**剥掉 markdown 强调/代码标记**（`*`、`_`、`` ` ``）。
    起因是本轮实测到的**两处盲区**：
      * `**28 类**特征输入` —— 数字与单位被 `**` 切开，`(\\d+)\\s*类特征输入` 匹配不到；
      * `` `17` 个子命令 `` —— 反引号夹在数字与单位之间，`(\\d+)\\s*个子命令` 也匹配不到。
    两个都是**真写错的数字却没人报**。剥标记是**单点修复**，一次覆盖所有检查项；
    比逐个给正则加 `\\**` 更不容易再漏。
    """
    lines = _read(rel)
    if lines is None:
        return
    for i, line in enumerate(lines, 1):
        plain = re.sub(r"[*_`]", "", line)
        for pat in patterns:
            for m in re.finditer(pat, plain):
                got = int(m.group(1))
                if got in allow:
                    continue
                if got != expected:
                    problems.append(
                        f"{rel}:{i}  [{label}] 写作 {got}，实测应为 {expected}\n"
                        f"      > {line.strip()[:110]}"
                    )


def main():
    tpl = truth_templates()
    st = truth_stages()
    cases = truth_validate_cases()
    vout = truth_verify_out()
    subs = truth_subcommands()

    if "--list" in sys.argv or "-l" in sys.argv:
        print("=== 实测真值 ===")
        print(f"模板数 (references/templates/*.inp)      : {tpl}")
        if st:
            print(f"阶段数 (guide.py STAGES)                : "
                  f"主线 {st['main']} + 续算 {st['resume']} = {st['total']}")
            print(f"  阶段 key: {', '.join(st['keys'])}")
        print(f"校验用例数 (_validate_all.py)            : {cases}")
        print(f"示例输入数 (verify_out/*.inp)            : {vout}")
        print(f"后处理子命令数 (postprocess.py)          : {subs}")
        print(f"知识分层实际文件数                       : {truth_layer_count()}")
        og = truth_official_files()
        if og:
            print(f"G 层文件数 (references/official/*.md)    : {og['total']}")
            print(f"  文件: {', '.join(og['names'])}")
            miss = truth_official_sources()
            print(f"  缺溯源头部: {miss if miss else '无（全部合规）'}")
        h = truth_h_tutorials()
        if h:
            print(f"H 层官方教程与算例                       : "
                  f"教程 {h['n_txt']} 份 | 精读笔记 {h['n_notes']} 篇 | "
                  f"算例输入卡 {h['n_cases']} 个 | README "
                  f"{'有' if h['has_readme'] else '**缺**'}")
        ex = truth_examples()
        if ex:
            print(f"示例工程数 (examples/NN_*/)              : {ex['total']}")
            print(f"  目录: {', '.join(ex['names'])}")
            if ex.get("incomplete"):
                print(f"  ⚠ 缺 README.md 或 .inp: {', '.join(ex['incomplete'])}")
        ent = truth_entry_files()
        print(f"跨 agent 入口: 真源缺 {ent['required_missing'] or '无'} | "
              f"指针缺 {ent['pointer_missing'] or '无'}")
        js = truth_cli_json_support()
        if js:
            no_json = [k for k, v in js.items() if not v]
            print(f"--json 支持 ({len(js) - len(no_json)}/{len(js)})          : "
                  f"缺 {no_json or '无'}")
        print(f"控制台兼容层 (scripts/_console.py)       : "
              f"{len(ENTRY_POINTS) - len(truth_console_compat())}/{len(ENTRY_POINTS)} "
              f"入口已挂 | 缺 {truth_console_compat() or '无'}")
        print(f"未指定 encoding 的文本 I/O                : "
              f"{len(truth_locale_safe_io())} 处")
        return 0

    # --- 口径检查 -----------------------------------------------------------
    # 1) 模板数：文中「N 类 .inp 模板」/「N 类模板」应为实测值
    if tpl is not None:
        _scan("README.md",
              [r"(\d+)\s*类\s*\.inp\s*模板", r"(\d+)\s*类模板"],
              "模板数", tpl)
        _scan("SKILL.md",
              [r"(\d+)\s*类模板"],
              "模板数", tpl)
        _scan("USAGE.md",
              [r"(\d+)\s*类模板"],
              "模板数", tpl)

    # 2) 阶段数：主线 11
    if st:
        for doc in ["SKILL.md", "README.md", "USAGE.md", "references/workflow.md"]:
            _scan(doc,
                  [r"(\d+)\s*个主线阶段", r"(\d+)\s*阶段顺序", r"全\s*(\d+)\s*个阶段",
                   r"看全\s*(\d+)\s*个"],
                  "主线阶段数", st["main"])

    # 3) 校验用例数：_validate_all.py 实测
    if cases:
        _scan("SKILL.md",
              [r"(\d+)\s*类特征输入", r"(\d+)\s*类特征组合", r"生成\s*(\d+)\s*类输入"],
              "校验用例数", cases)
        _scan("README.md",
              [r"(\d+)\s*类特征输入"],
              "校验用例数", cases)
        _scan("USAGE.md",
              [r"(\d+)\s*类特征输入", r"校验\s*(\d+)\s*类"],
              "校验用例数", cases)

    # 4) 示例输入数：verify_out
    if vout:
        _scan("SKILL.md",
              [r"(\d+)\s*个已通过权威校验的示例输入"],
              "示例输入数", vout)

    # 5) 后处理子命令数：postprocess.py 实测
    if subs:
        # 两种词序都要认：`N 个子命令` 与 `子命令 N 个`。
        # 早先只认前者，于是 USAGE.md 末尾汇总表里的「子命令 17 个」**一直在盲区里**
        # （正文两处早就改到 24 了，那处仍写 17 却没人报）。
        _scan("USAGE.md",
              [r"(\d+)\s*个子命令", r"子命令\s*(\d+)\s*个"],
              "后处理子命令数", subs)

    # 6) G 层文件数：references/official/*.md 实测
    og_files = truth_official_files() or {}
    if og_files.get("total"):
        _scan("USAGE.md",
              [r"G 层[^0-9\n]*(\d+)\s*个文件", r"G 层\s*(\d+)\s*文件"],
              "G 层文件数", og_files["total"])

    # 6b) H 层：新层必须真存在，且四个关键入口都要在文档里登记
    #
    # 注意这里**不能**写成 `if h: ... elif os.path.isdir(...): problem` ——
    # 那样"目录整个不见了"两个分支都不成立，护栏静默失效（实测踩过：
    # 把 videonotes/ 改名后检查照样报 OK）。**目录必须在**是第一条断言。
    h = truth_h_tutorials()
    if h is None:
        problems.append("references/h_tutorials/  [H 层] **目录不存在**"
                        "（H 层是已登记的正式层，消失必须是有意为之；"
                        "若确实要撤，请同时改 SKILL.md/AGENTS.md/README.md 的分层表）")
    else:
        if not h["has_readme"]:
            problems.append("references/h_tutorials/  [H 层] 缺 README.md（层定位文档）")
        if not h["has_extract"]:
            problems.append("references/h_tutorials/  [H 层] 缺 extract_tutorials.py（抽取脚本）")
        if h["n_txt"] == 0:
            problems.append("references/h_tutorials/txt/  [H 层] 没有任何教程文本 T*.txt")
        # 分层表里必须出现 H 层（SKILL.md / AGENTS.md / README.md 三处）
        for doc in ("SKILL.md", "AGENTS.md", "README.md"):
            lines = _read(doc)
            if lines is None:
                continue
            txt = "\n".join(lines)
            if "h_tutorials" not in txt:
                problems.append(
                    f"{doc}  [H 层] 未登记 references/h_tutorials/"
                    f"（新增知识层必须在分层表/目录树里出现）")

    # 6c) E 层的 videonotes 子层：同样**先断言目录在**，再查内容与登记
    vn = truth_videonotes()
    if vn is None:
        problems.append("references/pdf_text/videonotes/  [E 层·视频精读] **目录不存在**"
                        "（应有 6 份课程视频精读笔记）")
    else:
        if vn["n_notes"] == 0:
            problems.append("references/pdf_text/videonotes/  [E 层·视频精读] "
                            "一个笔记都没有（应有 6 份）")
        if not vn["has_readme"]:
            problems.append("references/pdf_text/videonotes/  [E 层·视频精读] 缺 README.md"
                            "（该子层与 learn_L*.md 的关系必须写清楚）")
        for doc in ("SKILL.md", "AGENTS.md", "README.md"):
            lines = _read(doc)
            if lines is None:
                continue
            if "videonotes" not in "\n".join(lines):
                problems.append(
                    f"{doc}  [E 层·视频精读] 未登记 references/pdf_text/videonotes/")


    # 7) 示例工程数：examples/NN_xxx/ 实测
    ex = truth_examples() or {}
    if ex.get("total"):
        _scan("AGENTS.md",
              [r"(\d+)\s*个开箱即用的示例", r"(\d+)\s*个示例"],
              "示例工程数", ex["total"])
        _scan("README.md",
              [r"(\d+)\s*个开箱即用的示例", r"(\d+)\s*个示例工程"],
              "示例工程数", ex["total"])
        # 每个示例目录必须同时有 README.md 与 .inp
        if ex.get("incomplete"):
            problems.append(
                "examples/  [结构] 以下示例目录缺 README.md 或 .inp："
                + "、".join(ex["incomplete"])
            )

    # 8) 跨 agent 入口：AGENTS.md 必在；指针文件应齐备
    ent = truth_entry_files()
    if ent["required_missing"]:
        problems.append(
            "根目录  [跨 agent 入口] 缺少唯一真源：" + "、".join(ent["required_missing"])
        )
    if ent["pointer_missing"]:
        problems.append(
            "根目录  [跨 agent 入口] 缺少指针文件：" + "、".join(ent["pointer_missing"])
        )
    # AGENTS.md 里提到的指针文件必须真实存在
    agents = _read("AGENTS.md")
    if agents is not None:
        txt = "\n".join(agents)
        for f in ["CLAUDE.md", ".cursorrules", "GEMINI.md",
                  "copilot-instructions.md"]:
            if f in txt and not os.path.isfile(os.path.join(HERE, f)) \
                    and not os.path.isfile(os.path.join(HERE, ".github", f)):
                problems.append(
                    f"AGENTS.md  [指针] 提到了 {f} 但该文件不存在"
                )
        # AGENTS.md 宣称的「零依赖」必须与 requirements 口径一致
        if "标准库" in txt and "postprocess.py" not in txt:
            problems.append(
                "AGENTS.md  [依赖口径] 声称只用标准库但未说明 postprocess.py 例外"
            )

    # --- 交叉检查：分层表是否漏了 F / G 层 --------------------------------
    skill = _read("SKILL.md")
    if skill is not None:
        txt = "\n".join(skill)
        if os.path.isfile(os.path.join(HERE, "references", "playbook.md")):
            if "playbook.md" not in txt:
                problems.append(
                    "SKILL.md  [分层表] 存在 references/playbook.md 但入口未收录"
                )
            elif "F 实战手册" not in txt and "**F " not in txt:
                problems.append(
                    "SKILL.md  [分层表] 提到了 playbook.md 但没有 F 层条目"
                )
        # G 层：官方权威层
        if os.path.isdir(os.path.join(HERE, "references", "official")):
            if "official/" not in txt and "references/official" not in txt:
                problems.append(
                    "SKILL.md  [分层表] 存在 references/official/ 但入口未收录"
                )
            elif "G 官方" not in txt and "**G " not in txt:
                problems.append(
                    "SKILL.md  [分层表] 提到了 official 目录但没有 G 层条目"
                )
    readme = _read("README.md")
    if readme is not None:
        txt = "\n".join(readme)
        if os.path.isfile(os.path.join(HERE, "references", "playbook.md")):
            if "知识分层（A–E）" in txt:
                problems.append(
                    "README.md  [分层表] 标题仍写「A–E」，但已存在 F 层 playbook.md"
                )
        if os.path.isdir(os.path.join(HERE, "references", "official")):
            if "知识分层（A–F）" in txt or "知识分层（A–E）" in txt:
                problems.append(
                    "README.md  [分层表] 标题仍写「A–F/A–E」，但已存在 G 层 references/official/"
                )
            if "references/official" not in txt and "official/" not in txt:
                problems.append(
                    "README.md  [分层表] 存在 references/official/ 但未收录"
                )

    # 9) 控制台编码兼容：每个入口都必须挂 scripts/_console.py，
    #    否则中文 Windows(GBK) 下输出 ✓ ✗ • ⚠ ✖ ⑪ ↻ Å ² ³ 会抛 traceback
    if not os.path.isfile(os.path.join(HERE, "scripts", "_console.py")):
        problems.append(
            "scripts/  [控制台兼容] scripts/_console.py 不存在。"
            "入口的 import 被 try/except 吞掉，崩溃会**静默复发**"
        )
    missing_console = truth_console_compat()
    if missing_console:
        problems.append(
            "scripts/  [控制台兼容] 以下入口未挂 scripts/_console.py，"
            "中文 Windows(GBK) 下会抛 UnicodeEncodeError："
            + "、".join(missing_console)
        )

    # 10) 文本 I/O / 子进程解码必须显式 encoding，否则跟随 locale(GBK)
    bad_io = truth_locale_safe_io()
    if bad_io:
        problems.append(
            "scripts/  [I/O 编码] 以下文本 I/O 未指定 encoding=（GBK 环境下会崩）：\n      "
            + "\n      ".join(bad_io)
        )

    # 11) wizard.py 的旗标集合必须覆盖 gen_inp.py 的全部带值开关
    #     （两份清单手工维护过，实测已漂移 27 个；改为从 argparse 实测比对）
    bad_flags = truth_wizard_flags()
    if bad_flags:
        problems.append(
            "scripts/wizard.py  [旗标集合漂移] "
            + "\n      ".join(bad_flags)
            + "\n      ⇒ 往 gen_inp.py 加带值开关时，同步登记到 wizard.py 的两个集合。"
        )

    # --- 输出 ---------------------------------------------------------------
    if problems:
        print(f"发现 {len(problems)} 处口径不一致：\n")
        for p in problems:
            print("  ✗ " + p)
        print("\n提示：真值可用 `python _doc_consistency.py --list` 查看。")
        return 1

    og = truth_official_files() or {}
    print("OK：文档口径全部一致。")
    print(f"  模板 {tpl} 类 | 主线阶段 {st['main'] if st else '?'} "
          f"(+续算 {st['resume'] if st else '?'}) | 校验用例 {cases} 类 | "
          f"示例输入 {vout} 个 | 后处理子命令 {subs} 个 | "
          f"G 层文件 {og.get('total', '?')} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
