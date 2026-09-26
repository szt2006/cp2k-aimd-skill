#!/usr/bin/env python3
"""Authoritative CP2K input validation via the official cp2k-input-tools
CP2KInputParser (validates against CP2K's own cp2k_input.xml reference).

Compat shims (all tooling-only, NOT input changes):
  * pint 0.23+ dropped numpy.cumproduct -> restore alias (cumproduct==cumprod).
  * cp2k-input-tools 0.9.1's pint_units.txt does NOT define CP2K's time unit
    'fs' (femtosecond); pint therefore reads '[fs]' as femtosiemens and the
    unit check crashes. We inject fs == femtosecond into the registry so the
    unit check matches CP2K's actual semantics. This is a known tooling
    limitation; '[fs]' is 100% correct CP2K syntax.
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


def _die_missing_deps(missing, detail):
    """友好报错并退出，不打印 traceback。exit 3 = 环境依赖缺失。"""
    sys.stderr.write("\n".join([
        "", "=" * 70,
        f"缺少依赖：{missing}", "",
        "本脚本属于开发依赖（用官方解析器校验输入），普通用户无需运行。",
        "",
        "安装方式：", "",
        "  pip install -r requirements-dev.txt",
        "",
        detail,
        "=" * 70, "",
    ]))
    sys.exit(3)


try:
    import numpy as np
except ImportError as _exc:
    _die_missing_deps(getattr(_exc, "name", "numpy"), "numpy 是 pint 的底层依赖。")

if not hasattr(np, "cumproduct"):
    np.cumproduct = np.cumprod  # compatibility shim for pint

try:
    import cp2k_input_tools.parser as P
    from cp2k_input_tools.parser import CP2KInputParser
except ImportError as _exc:
    _die_missing_deps(
        getattr(_exc, "name", "cp2k-input-tools"),
        "需要 cp2k-input-tools（自带官方 cp2k_input.xml）及其依赖 pint/lxml：\n"
        "  pip install cp2k-input-tools pint lxml",
    )

# Inject CP2K's femtosecond unit (pint calls it femtosiemens by default).
try:
    P.UREG.define("fs = femtosecond")
except Exception:
    try:
        P.UREG._units.pop("fs", None)
        P.UREG.define("fs = femtosecond")
    except Exception:
        pass

# `IONS+CENTERS` 是**官方 XML 里唯一含 `+` 的关键字名**（`<NAME type="default">IONS+CENTERS</NAME>`
# 在 XML 里出现 19 次、同名，全在 `&WANNIER_CENTERS` 下，官方默认 `F`）。
# 而 cp2k-input-tools 0.9.1 的关键字正则 `(?P<name>[\w\-_]+)` **不含 `+`**，解析到该行时
# 在 `+` 处截断、把 `IONS` 当关键字名，报
#     InvalidNameError: invalid keyword 'IONS' specified and no default keyword for this section
# —— **假 error**，输入本身合法。`gen_inp.py --properties wannier` 就会发射它。
# 把字符类补上 `+`：只放宽一个字符，对不含 `+` 的名字行为不变。
try:
    import re as _re
    P._KEYWORD_MATCH = _re.compile(r"(?P<name>[\w\-_+]+)\s*(?P<value>.*)")
except Exception:
    pass

# 同一类 tooling 缺陷的第二例：cp2k-input-tools 0.9.1 的 pint_units.txt 把
# `wavenumber_t` **注释掉了**，于是 parser 报 `'wavenumber_t' is not defined in
# the unit registry`。但 `[wavenumber_t]` 是**合法的 CP2K 时间单位**（G 层
# references/official/01_global_and_units.md 列出；真实生产 .out 回显
# `Nose-Hoover-Chain time constant [  fs] 33.36` 佐证 `[wavenumber_t] 1000` = 33.36 fs）。
#
# 不补这一条，**真实生产卡的写法反而过不了官方校验** —— 那是最不该发生的事。
# 量纲取 1/长度（值就是波数 cm^-1）；这里只让它**可被识别**。
try:
    P.UREG.define("wavenumber_t = 1 / centimeter")
except Exception:
    try:
        P.UREG._units.pop("wavenumber_t", None)
        P.UREG.define("wavenumber_t = 1 / centimeter")
    except Exception:
        pass

parser = CP2KInputParser()  # uses bundled cp2k_input.xml reference


# ---------------------------------------------------------------------------
# 第三类已知 tooling 限制：官方 schema 里 DEFAULT_UNIT = `internal_cp2k` 的关键字
#
# 这类关键字的单位**由上下文决定**（例如 METAVAR/WALL 的 POSITION：值是该 colvar
# 的取值，单位取决于所选 COLVAR 是距离、角度还是配位数），所以官方把它标成伪单位
# `internal_cp2k`。pint 只能做**线性**单位换算，遇到 `POSITION [angstrom] 2.20`
# 这种"给伪单位关键字显式覆盖单位"的写法就报
# `InvalidParameterError('invalid values for keyword: POSITION')`。
#
# **不能一刀切放行** —— 那样真的写错单位也会被吞掉。所以只在
# 「官方 schema 确实把该关键字标成 internal_cp2k」时才降级成 NOTE，
# 其余一律照常判错。
# ---------------------------------------------------------------------------
_INTERNAL_UNIT_KEYWORDS = None


def _xml_path():
    """官方 cp2k_input.xml 的位置（cp2k-input-tools 把它放在包根目录）。"""
    import os as _o
    base = _o.path.dirname(_o.path.abspath(P.__file__))
    for cand in (_o.path.join(base, "cp2k_input.xml"),
                 _o.path.join(base, "data", "cp2k_input.xml")):
        if _o.path.isfile(cand):
            return cand
    return None


def _internal_unit_keywords():
    global _INTERNAL_UNIT_KEYWORDS
    if _INTERNAL_UNIT_KEYWORDS is None:
        import xml.etree.ElementTree as _ET
        names = set()
        xml = _xml_path()
        if xml:
            try:
                root = _ET.parse(xml).getroot()
                for kw in root.iter("KEYWORD"):
                    du = kw.find("DEFAULT_UNIT")
                    nm = kw.find("NAME")
                    if (du is not None and nm is not None
                            and (du.text or "").strip() == "internal_cp2k"):
                        names.add((nm.text or "").strip().upper())
            except Exception:
                pass
        _INTERNAL_UNIT_KEYWORDS = names
    return _INTERNAL_UNIT_KEYWORDS


def _known_unit(unit):
    """该单位名 pint 认不认（不认就不是"工具算不了"，而是用户写错了）。"""
    try:
        P.UREG.parse_units(unit)
        return True
    except Exception:
        return False


def _scan_internal_unit_overrides(path):
    """找出「在 internal_cp2k 关键字上做了**合法**显式单位覆盖」的行。

    返回 ``[(lineno, 原行, 去掉[unit]后的行)]``，只收同时满足三条的：
      1. 关键字在官方 schema 里是 DEFAULT_UNIT = internal_cp2k
      2. 方括号里的单位名 pint **认得**（不认得 ⇒ 用户真写错了，不能放过）
      3. 值全是数字（不是数字 ⇒ 真错误，不能放过）

    这样"降级成 NOTE"就只在**确实是工具能力不足**时发生 —— 早先只按异常消息里的
    关键字名判断，结果 `POSITION [nonsense_unit] 2.20` 和 `POSITION [angstrom] abc`
    这两种**真错误**也被放行了（反向对照抓到的）。
    """
    kws = _internal_unit_keywords()
    if not kws:
        return []
    hits = []
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return []
    for i, ln in enumerate(lines, 1):
        m = re.match(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*([^\]]+?)\s*\]\s*(.*?)\s*$",
                     ln)
        if not m:
            continue
        indent, kw, unit, value = m.groups()
        if kw.upper() not in kws:
            continue
        if not _known_unit(unit):
            continue
        toks = value.replace(",", " ").split()
        if not toks:
            continue
        try:
            [float(t) for t in toks]
        except ValueError:
            continue
        hits.append((i, ln, "{}{} {}".format(indent, kw, value)))
    return hits


def validate_file(path):
    errors = []
    overrides = _scan_internal_unit_overrides(path)
    parse_path = path
    tmp = None
    if overrides:
        # 把无法校验的单位覆盖剥掉，再让官方 parser 校验**其余全部内容** ——
        # 这样既能给出 NOTE，又不会因此漏掉文件里别处的真错误。
        import tempfile
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines(True)
        for lineno, _old, new in overrides:
            lines[lineno - 1] = new + "\n"
        fd, tmp = tempfile.mkstemp(suffix=".inp")
        with open(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("".join(lines))
        parse_path = tmp
    try:
        with open(parse_path, "r", encoding="utf-8", errors="replace") as fh:
            list(parser.parse(fh))  # force the generator so all errors surface
    except Exception as e:  # InvalidSectionError / InvalidKeywordError / etc.
        # Re-classify the known pint 'fs' collision as a non-fatal tooling note.
        msg = str(e)
        if "femtosiemens" in msg or "femtosecond" in msg:
            errors.append("NOTE(unit-tooling): pint mis-reads CP2K '[fs]' as "
                          "femtosiemens; this is a cp2k-input-tools limitation, "
                          "not an input error. ('[fs]' = femtosecond is correct.)")
        elif "wavenumber_t" in msg:
            # `[wavenumber_t]` 是合法 CP2K 时间单位，但**它和时间的换算是反比的**
            # （值取波数 ν̃，时间是该振子的周期 t[fs] = 33356.40952/ν̃[cm⁻¹]），
            # 而 pint 只能做**线性**单位换算 —— 量纲上就没法建模。
            #
            # 所以这里**不当错误**：单位确实存在、语法确实合法，只是工具算不了它的
            # 数值。真实生产卡（7/7 张）都写 `TIMECON [wavenumber_t] 1000`，把这种
            # 写法判死是最不该发生的事。
            errors.append("NOTE(unit-tooling): CP2K '[wavenumber_t]' is a valid time "
                          "unit (value = wavenumber; t[fs] = 33356.40952/nu[cm^-1], "
                          "so 1000 -> 33.36 fs). pint can only do *linear* unit "
                          "conversion while this relation is inverse, so it cannot "
                          "convert it. Not an input error.")
        else:
            errors.append(f"{type(e).__name__}: {msg}")
    finally:
        if tmp and os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
    # 剥掉单位后**其余内容全部通过** ⇒ 未通过的只有那些覆盖本身
    for lineno, old, _new in overrides:
        errors.append(
            "NOTE(unit-tooling): line {}: keyword has DEFAULT_UNIT "
            "'internal_cp2k' in the official schema (its unit is decided by "
            "context -- for METAVAR/WALL it is the unit of the chosen COLVAR), "
            "so this tool cannot check the explicit unit override. The rest of "
            "the file WAS validated. Please confirm the unit yourself: {}"
            .format(lineno, old.strip()))
    return errors


if __name__ == "__main__":
    import glob
    import sys

    # `--help` / `-h` 必须 exit 0（AGENTS.md §6.3 健壮性基线）。
    # 之前没有这一步，`--help` 会被当成**文件名**喂给官方解析器，抛
    # `FileNotFoundError: [Errno 2] No such file or directory: '--help'`
    # 然后 exit 1 —— 用户最常打的第一个参数反而给出 Python 异常。
    # 是 `_validate_gbk.py`（GBK 回归扫描 21 个入口的 --help）把它抓出来的。
    argv = sys.argv[1:]
    if any(a in ("-h", "--help") for a in argv):
        print("用官方 cp2k-input-tools 的解析器逐个校验 .inp。")
        print("比自带的 validate_inp.py 更权威（直查官方 cp2k_input.xml），"
              "但需要 cp2k-input-tools。")
        print()
        print("用法：python _official_validate.py <file.inp> [file2.inp ...]")
        print("例：  python _official_validate.py verify_out/*.inp")
        print("      python _official_validate.py "
              "examples/01_si_bulk_static/si_bulk8.inp")
        print()
        print("退出码：0 全部通过 / 1 有失败 / 2 没给文件或给了未知选项 / 3 缺依赖")
        sys.exit(0)
    unknown = [a for a in argv if a.startswith("-") and a != "-"]
    if unknown:
        sys.stderr.write(
            "\n[ERROR] 未知选项：{}\n"
            "  本脚本只接受 .inp 文件路径（可含通配符），没有其它选项。\n"
            "  用 --help 看用法。\n\n".format(", ".join(unknown)))
        sys.exit(2)

    if not argv:
        sys.stderr.write(
            "\n用法：python _official_validate.py <file.inp> [file2.inp ...]\n"
            "例：  python _official_validate.py verify_out/*.inp\n"
            "      python _official_validate.py examples/01_si_bulk_static/si_bulk8.inp\n\n"
        )
        sys.exit(2)

    # 自行展开通配符：bash 会替程序展开，但 Windows 的 cmd / PowerShell 对原生
    # 程序**不展开**，于是文档里的 `python _official_validate.py verify_out/*.inp`
    # 在 Windows 上会把字面量 'verify_out/*.inp' 当文件名 → OSError。
    files = []
    unmatched = []
    for arg in argv:
        hits = sorted(glob.glob(arg))
        if hits:
            files.extend(hits)
        elif any(c in arg for c in "*?["):
            unmatched.append(arg)
        else:
            files.append(arg)  # 非通配符路径原样传入，照常报"文件不存在"

    all_ok = True
    for pat in unmatched:
        all_ok = False
        print(f"[FAIL] {pat}")
        print(f"    找不到匹配「{pat}」的文件（请检查路径或通配符）")

    for path in files:
        errs = validate_file(path)
        real_errs = [e for e in errs if not e.startswith("NOTE")]
        if real_errs:
            all_ok = False
            print(f"[FAIL] {path}")
            for e in errs:
                print(f"    {e}")
        elif errs:
            print(f"[OK*]  {path}  (only tooling unit note)")
        else:
            print(f"[OK]   {path}")
    print()
    print("ALL OK" if all_ok else "SOME FAILED")
    sys.exit(0 if all_ok else 1)
