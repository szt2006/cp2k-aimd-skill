#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从官方 cp2k_input.xml 查询指定 SECTION/KEYWORD 的类型、默认值、单位。

用途：课程字幕里讲师对某些关键字的**单位/默认值**口述含糊或有误（例如
`TIMECON` 被说成"波数"），而 cp2k-input-tools 自带官方输入参考 XML，
可以直接查出权威答案，不必靠猜。

用法：
    python _kw_probe.py MOTION/MD/THERMOSTAT/NOSE/TIMECON
    python _kw_probe.py MOTION/MD/THERMOSTAT/CSVR/TIMECON
    python _kw_probe.py --section MOTION/MD/THERMOSTAT/NOSE
    python _kw_probe.py --section MOTION/MD/THERMOSTAT/NOSE --json
    python _kw_probe.py --find EMAX_SPLINE      # **全库**搜同名关键字属于哪些段
    python _kw_probe.py --find RUN_TYPE --json

`--section` 只是**显式声明"我要列子项"**；不给也按节点类型自动判断
（SECTION 列子项、KEYWORD 打详情）。给个不存在的路径会以 exit 1 退出。

`--find` 是查证教材"存疑"的主力：教材常出现一个关键字却说不清它属于哪一段，
这时**猜路径是查不到的**。实测 `EMAX_SPLINE` 其实在
`FORCE_EVAL/MM/FORCEFIELD/SPLINE`（经典 MM 样条），而不是 QS 的
`&KIND/&BASIS_SET` —— 靠猜会得出完全相反的结论。

关键字详情里现在也**列出 ENUMERATION**（合法取值），
用来判定 `RUN_TYPE` / `XC_FUNCTIONAL` 这类枚举关键字的写法是否过时。

⚠️ **版本前提（很重要，2026-10 补记）**：本脚本查的是 **`cp2k-input-tools` 随包分发的
`cp2k_input.xml`，它是 CP2K **9.0** 的**（XML 里 `<CP2K_VERSION>CP2K version 9.0</CP2K_VERSION>`）。
所以它给出的每个"默认值"严格说都是"**CP2K 9.0 的默认值**"：
① 引用时**不要写成无版本的"官方默认"**，本仓库统一写作"（9.0 XML）"；
② **跨版本会变**——例如 `&CELL_OPT TYPE` 在 2026.2 被移除，这个 9.0 的 XML 就看不出来；
③ **要核对你手上那个版本**：设环境变量 **`CP2K_INPUT_XML`** 指向你自己 CP2K 安装里的
`cp2k_input.xml`（通常在 `data/` 下），本工具就改查那一版；也可以是官方手册上任意版本的 XML。
不设则用 `cp2k-input-tools` 随包那份。`_kw_probe.py --version` 看当前用的是哪份。
脚本现在会在输出头部打印版本，避免"结论脱离了它成立的前提"。

📌 **两版交叉核验的结论（2026-10，可复现）**：把本库**断言过的 48 项核心默认值**
在 **9.0 与 2022.1** 两份官方 XML 上逐条比对，**全部一致、零差异**；
两版之间总共只有 **63 处默认值差异，且全在 `PW_DFT`（平面波 DFPT）/`ATOM`/RI-RPA
等旁支**，与 Quickstep 主线无关。唯一与知识库相关的一处是
`FORCE_EVAL/DFT/ENERGY_CORRECTION/EPS_DEFAULT`（9.0 = `1E-12`，2022.1 = `1E-7`），
已在 `decide.md §7.1` 就地标明。⇒ **本库的默认值语料是跨版本稳健的**，
但仍建议按上面 ③ 用自己那版复核一次。
"""
import sys

# --- 控制台编码兼容层（中文 Windows/GBK 下输出不再抛异常）---
try:
    import os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    for _d in (_here, _os.path.join(_here, "scripts")):
        if _d not in _sys.path:
            _sys.path.insert(0, _d)
    import _console  # noqa: F401  导入即生效，见 scripts/_console.py
except Exception:
    pass

try:
    from cp2k_input_tools.parser import CP2KInputParser  # noqa: F401
    import cp2k_input_tools
    import os
    # ---- 用哪份 XML？优先级：环境变量 > 包内自带 ----------------
    # 为什么允许覆盖：包内自带的是**某一个固定版本**（当前 9.0），而默认值会跨版本变。
    # 想核对自己手上那版 CP2K，只要把它安装目录里的 `cp2k_input.xml` 指过来即可：
    #     set CP2K_INPUT_XML=D:\path\to\cp2k_input.xml        (Windows)
    #     export CP2K_INPUT_XML=/path/to/cp2k_input.xml       (Linux，通常在 CP2K 的 data/ 下)
    # 官方各版本的 XML 也能直接下：https://manual.cp2k.org/cp2k-<版本带下划线>-branch/cp2k_input.xml
    # （例：https://manual.cp2k.org/cp2k-2022_1-branch/cp2k_input.xml）
    _env = os.environ.get("CP2K_INPUT_XML")
    if _env:
        if not os.path.isfile(_env):
            sys.exit(f"CP2K_INPUT_XML 指向的文件不存在：{_env}")
        XML = _env
    else:
        # cp2k-input-tools 把官方输入参考 XML 直接放在包根目录下
        XML = os.path.join(os.path.dirname(cp2k_input_tools.__file__),
                           "cp2k_input.xml")
        if not os.path.isfile(XML):  # 兼容个别版本放在 data/ 下
            XML = os.path.join(os.path.dirname(cp2k_input_tools.__file__),
                               "data", "cp2k_input.xml")
except SystemExit:
    raise
except Exception as e:
    sys.exit(f"缺少 cp2k-input-tools：{e}\n安装："
             f"python -m pip install --no-deps cp2k-input-tools==0.9.1")

import xml.etree.ElementTree as ET

# XML 的版本前提：本工具给的每个默认值都属于**这个版本**。
# 早先没打印它，于是"结论"和"结论成立的前提"分家了（读者拿别的版本一对就懵）。
try:
    _root0 = ET.parse(XML).getroot()
    _vnode = _root0.find(".//CP2K_VERSION")
    XML_VERSION = (_vnode.text or "").strip() if _vnode is not None else "(未标注)"
except Exception:
    XML_VERSION = "(读取失败)"


def version_line():
    return "XML 版本: {}   [{}]".format(XML_VERSION, XML)


def find(node, name):
    """按**默认名或别名**找子节点。

    CP2K 的 schema 里一个关键字可以有多个 `<NAME>`：第一个是默认名、其余
    `type="alias"` 是别名。例如 `EXTRAPOLATION` 的别名是 `INTERPOLATION` 与
    **`WF_INTERPOLATION`** —— 教材与真实生产卡用的是别名，只比默认名会**查不到**，
    从而把合法写法误判成"关键字不存在"。
    """
    want = name.strip().upper()
    for ch in node:
        if ch.tag in ("SECTION", "KEYWORD"):
            for n in ch.findall("NAME"):
                if (n.text or "").strip().upper() == want:
                    return ch
    return None


def names_of(k):
    """返回 (默认名, [别名...])。"""
    ns = k.findall("NAME")
    if not ns:
        return "?", []
    default = (ns[0].text or "").strip()
    aliases = [(n.text or "").strip() for n in ns[1:] if (n.text or "").strip()]
    return default, aliases


def kw_info(k):
    out = {}
    for tag in ("TYPE", "DEFAULT_VALUE", "DEFAULT_UNIT", "UNIT", "DESCRIPTION"):
        el = k.find(tag)
        out[tag] = (el.text or "").strip() if el is not None else None
    # 枚举值（RUN_TYPE / XC_FUNCTIONAL / METHOD … 这类关键字的合法取值）
    vals = [e.text.strip() for e in k.findall("ENUMERATION")
            if e.text and e.text.strip()]
    if vals:
        out["ENUMERATION"] = ", ".join(vals)
    return out


def _walk(node, path=()):
    """深度优先遍历，产出 (section_path, element)。

    同时产出 **SECTION** 与 **KEYWORD** 两类节点 —— 只产出 KEYWORD 会让
    `--find <段名>` 得到"0 命中"，进而把**存在的段误判成不存在**
    （实测踩过：`--find SWARM` 报 0 处，而 `&SWARM` 其实是 14 个顶层段之一，
    结果笔记里写下了"现行 XML 无 SWARM"这个**错误结论**）。
    """
    for ch in node:
        if ch.tag == "SECTION":
            n = ch.find("NAME")
            nm = (n.text or "").strip() if n is not None else "?"
            yield path + (nm,), ch
            yield from _walk(ch, path + (nm,))
        elif ch.tag == "KEYWORD":
            yield path, ch


def find_all(name):
    """在整个官方 XML 里找**所有**同名（或同别名）的**段与关键字**。

    返回 ``[(路径, kind, info)]``，``kind`` 是 ``"SECTION"`` 或 ``"KEYWORD"``。

    为什么必须有这个：教材里出现一个关键字（如 `EMAX_SPLINE`）却说不出它属于
    哪一段时，只按猜的路径去查是查不到的 —— 得全库搜。实测 `EMAX_SPLINE`
    其实在 `FORCE_EVAL/MM/FORCEFIELD/SPLINE`（经典 MM 样条），而不是
    QS 的 `&KIND/&BASIS_SET`；靠猜会得出完全相反的结论。

    **别名也要搜**：`WF_INTERPOLATION` 是 `EXTRAPOLATION` 的别名，只搜默认名
    会 0 命中，进而误判"生产卡写了个不存在的关键字"。

    **段名也要搜**：见 `_walk()` 的说明 —— 不搜段名会把存在的段误判成不存在。
    """
    root = ET.parse(XML).getroot()
    want = name.strip().upper()
    hits = []
    for path, el in _walk(root):
        if el.tag == "SECTION":
            if path and path[-1].upper() == want:
                info = {"SECTION": "(段)", "CHILDREN": str(
                    len([c for c in el if c.tag == "SECTION"])) + " 个子段, "
                    + str(len([c for c in el if c.tag == "KEYWORD"])) + " 个关键字"}
                hits.append(("/".join(path), "SECTION", info))
            continue
        default, aliases = names_of(el)
        if default.upper() == want or any(a.upper() == want for a in aliases):
            info = kw_info(el)
            info["DEFAULT_NAME"] = default
            if aliases:
                info["ALIASES"] = ", ".join(aliases)
            hits.append(("/".join(path) or "(ROOT)", "KEYWORD", info))
    return hits


def main():
    # 早先的实现直接取 `sys.argv[-1]` 当路径，`--section` 这个标志**根本没被解析**
    # —— 文档里写了、代码里没有，只是"最后一个参数恰好是路径"才碰巧能用；
    # `python _kw_probe.py --section` 会把 "--section" 本身当路径去查。
    argv = sys.argv[1:]
    as_json = False
    want_section = False
    find_name = None
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            print(__doc__)
            return 0
        if a == "--version":
            # 让"结论"与"结论成立的前提"绑定：本工具的默认值都属于这个版本
            print(version_line())
            return 0
        if a == "--json":
            as_json = True
        elif a == "--section":
            want_section = True
        elif a == "--find":
            i += 1
            if i >= len(argv):
                sys.exit("--find 后面要跟关键字名")
            find_name = argv[i]
        elif a.startswith("-") and a != "-":
            sys.exit(f"未知选项 {a}\n\n{__doc__}")
        else:
            rest.append(a)
        i += 1

    # ---- --find：全库搜同名**段与关键字**（教材说不出它属于哪一段时用）----
    if find_name:
        hits = find_all(find_name)
        if as_json:
            import json
            print(json.dumps({"query": find_name,
                              "hits": [{"path": s, "kind": k, **inf}
                                       for s, k, inf in hits]},
                             ensure_ascii=False, indent=2))
        else:
            n_sec = len([1 for _s, k, _i in hits if k == "SECTION"])
            n_kw = len(hits) - n_sec
            print("=== 全库搜 '{}'：{} 处（段 {} / 关键字 {}）===".format(
                find_name, len(hits), n_sec, n_kw))
            print(version_line())
            for sec, kind, inf in hits:
                print("  {}{}".format("&" if kind == "SECTION" else "", sec))
                if kind == "SECTION":
                    print("      （段）{}".format(inf.get("CHILDREN", "")))
                    continue
                if inf.get("ALIASES"):
                    print("      默认名 {} | 别名 {}".format(
                        inf.get("DEFAULT_NAME"), inf["ALIASES"]))
                for k in ("TYPE", "DEFAULT_VALUE", "DEFAULT_UNIT", "UNIT",
                          "ENUMERATION"):
                    if inf.get(k):
                        print(f"      {k:<14}: {inf[k][:170]}")
                if inf.get("DESCRIPTION"):
                    print(f"      DESCRIPTION   : {inf['DESCRIPTION'][:170]}")
        return 0 if hits else 1

    if not rest:
        print(__doc__, file=sys.stderr)
        return 2
    if len(rest) > 1:
        sys.exit(f"只接受一个路径，收到 {len(rest)} 个: {rest}\n\n{__doc__}")
    path = rest[0].strip("/")
    root = ET.parse(XML).getroot()
    node = root
    parts = path.split("/")
    trail = []
    for i, p in enumerate(parts):
        nxt = find(node, p)
        if nxt is None:
            sys.exit(f"未找到 {p}（在 {'/'.join(parts[:i]) or 'ROOT'} 下）")
        node = nxt
        trail.append(p)
    if node.tag == "KEYWORD":
        if want_section:
            sys.exit(f"{path} 是 KEYWORD，不是 SECTION（去掉 --section 看它的详情）")
        info = kw_info(node)
        if as_json:
            import json
            print(json.dumps({"path": path, "kind": "keyword", **info},
                             ensure_ascii=False, indent=2))
        else:
            print(f"=== {path} ===")
            print("  " + version_line())
            for k, v in info.items():
                if v:
                    print(f"  {k:<14}: {v[:400]}")
    else:
        kids = []
        for ch in node:
            if ch.tag == "KEYWORD":
                n = ch.find("NAME").text
                info = kw_info(ch)
                kids.append({
                    "name": n, "kind": "keyword",
                    "type": info.get("TYPE") or "",
                    "unit": info.get("UNIT") or info.get("DEFAULT_UNIT") or "",
                    "default": info.get("DEFAULT_VALUE") or "",
                })
            elif ch.tag == "SECTION":
                kids.append({"name": ch.find("NAME").text, "kind": "section"})
        if as_json:
            import json
            print(json.dumps({"path": path, "kind": "section", "children": kids},
                             ensure_ascii=False, indent=2))
        else:
            print(f"=== {path}（SECTION） ===")
            for k in kids:
                if k["kind"] == "section":
                    print(f"  &{k['name']}")
                else:
                    print(f"  {k['name']:<22} type={k['type'] or '-':<10} "
                          f"unit={k['unit'] or '-':<16} "
                          f"default={k['default'] or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
