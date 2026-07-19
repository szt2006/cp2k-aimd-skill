#!/usr/bin/env python3
# 学习辅助：按路径抽取某 SECTION 的关键字详情（名称/类型/默认值/单位/描述/是否废弃）
# 用法：python _manual_kw.py "FORCE_EVAL/DFT/XC"   （路径用 / 分隔；空路径=顶层）
import os
import sys
import xml.etree.ElementTree as ET

# 定位 cp2k_input.xml：优先用已安装的 cp2k_input_tools 包，其次环境变量 CP2K_INPUT_XML，最后回退当前目录
try:
    import cp2k_input_tools
    XML = os.path.join(os.path.dirname(os.path.abspath(cp2k_input_tools.__file__)), "cp2k_input.xml")
except Exception:
    XML = os.environ.get("CP2K_INPUT_XML", "cp2k_input.xml")

def child_text(el, tag):
    c = el.find(tag)
    return (c.text or "").strip() if c is not None else ""

def find_section(root, path):
    # path like "FORCE_EVAL/DFT/XC" or "" for top-level list
    if not path:
        return root  # root CP2K_INPUT
    parts = [p.strip().upper() for p in path.split("/") if p.strip()]
    cur = root
    # descend: match SECTION by NAME
    for part in parts:
        found = None
        for sec in cur.findall("SECTION"):
            if child_text(sec, "NAME").upper() == part:
                found = sec
                break
        if found is None:
            return None
        cur = found
    return cur

def dump(section, max_desc=160):
    name = child_text(section, "NAME")
    desc = child_text(section, "DESCRIPTION")
    print(f"\n### SECTION {name}")
    if desc:
        print(f"  描述: {desc[:max_desc]}")
    # keywords
    kws = section.findall("KEYWORD")
    if kws:
        print(f"  关键字 ({len(kws)}):")
    for kw in kws:
        kn = child_text(kw, "NAME")
        kd = child_text(kw, "DEFAULT")
        kt = child_text(kw, "TYPE")
        ku = child_text(kw, "UNIT")
        kdesc = child_text(kw, "DESCRIPTION")
        removed = kw.get("removed", "no")
        flag = " [REMOVED]" if removed == "yes" else ""
        line = f"    - {kn}  (type={kt or '-'}"
        if kd:
            line += f", default={kd}"
        if ku:
            line += f", unit={ku}"
        line += f"){flag}"
        print(line)
        if kdesc:
            print(f"        {kdesc[:max_desc]}")
    # subsections
    subs = section.findall("SECTION")
    if subs:
        print(f"  子 SECTION ({len(subs)}): " + ", ".join(child_text(s, "NAME") for s in subs))

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else ""
    tree = ET.parse(XML)
    root = tree.getroot()
    if not path:
        print("TOP-LEVEL SECTIONS:")
        for sec in root.findall("SECTION"):
            print("  -", child_text(sec, "NAME"))
        return
    sec = find_section(root, path)
    if sec is None:
        print(f"未找到路径: {path}")
        # suggest: list top-level
        print("可用顶层:", ", ".join(child_text(s, "NAME") for s in root.findall("SECTION")))
        return
    dump(sec)

if __name__ == "__main__":
    main()
