#!/usr/bin/env python3
# 学习辅助：从 cp2k_input.xml 抽出完整 SECTION 树（仅结构）。
# 用法：python _manual_tree.py            # 打印到 stdout
#      python _manual_tree.py > refs.txt   # 存盘
import os
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

def walk(section, depth, out):
    name = child_text(section, "NAME")
    nk = len(section.findall("KEYWORD"))
    nsub = len(section.findall("SECTION"))
    out.append((depth, name, nk, nsub))
    for sub in section.findall("SECTION"):
        walk(sub, depth + 1, out)

tops = ET.parse(XML).getroot().findall("SECTION")
out = []
for top in tops:
    walk(top, 0, out)

for depth, name, nk, nsub in out:
    print(f"{'  '*depth}- {name}  (kw={nk}, sub={nsub})")

total_sec = len(out) - len(tops)
total_kw = sum(k for _, _, k, _ in out)
print(f"\nTOTAL sections (incl nested, excl {len(tops)} top): {total_sec}")
print(f"TOTAL keywords: {total_kw}")
