#!/usr/bin/env python3
"""从官方 cp2k_input.xml 生成 `scripts/_cp2k_sections.py`（全量 SECTION 名）。

**为什么需要**：`validate_inp.py` 用白名单判断"这个段名是不是拼错了"。原先手工
维护的名单只有 156 个，而官方 XML 里有 **1342 个** SECTION —— 覆盖率 12%，
于是 `&MULLIKEN`（官方 `&DFT/&PRINT` 下的布局分析段）这类**完全合法**的段
会被报成 "possible typo"。这是**拿真实生产输入卡去跑才暴露出来**的假阳性。

生成的模块是**纯数据、无依赖**，所以 skill 的"零依赖"承诺不受影响；
运行时 `validate_inp.py` 直接 import 它，缺了就退回手工名单（脚本仍可用）。
"""
import glob
import io
import os
import sys
import xml.etree.ElementTree as ET

# --- 控制台编码兼容层（中文 Windows/GBK 下输出不再抛异常）---
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "scripts"))
try:
    import _console  # noqa: F401
except Exception:
    pass

try:
    import cp2k_input_tools
except ImportError as e:
    sys.exit("缺少 cp2k-input-tools：{}\n安装："
             "python -m pip install --no-deps cp2k-input-tools==0.9.1".format(e))

# 相对本文件定位仓库根 —— 不要写死盘符，否则换机器/换目录就跑不了
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "scripts", "_cp2k_sections.py")

base = os.path.dirname(cp2k_input_tools.__file__)
_hits = glob.glob(os.path.join(base, "**", "cp2k_input.xml"), recursive=True)
if not _hits:
    sys.exit("在 cp2k-input-tools 包里找不到 cp2k_input.xml：{}".format(base))
xml = _hits[0]
tree = ET.parse(xml)
root = tree.getroot()


def _txt(el):
    return el.text.strip() if el is not None and el.text else ""


version = _txt(root.find("CP2K_VERSION")) or "unknown"

names = set()
for sec in root.iter("SECTION"):
    nm = _txt(sec.find("NAME"))
    if nm:
        names.add(nm.upper())

# 顶层段单独列出来，方便人读（顶层 = CP2K_INPUT 的直接 SECTION 子元素）
top = set()
for sec in list(root):
    if sec.tag == "SECTION":
        nm = _txt(sec.find("NAME"))
        if nm:
            top.add(nm.upper())

lines = [
    '"""CP2K 官方 SECTION 名全集 —— 本文件由工具生成，请勿手改。',
    "",
    "来源：cp2k-input-tools 自带的官方 `cp2k_input.xml`（CP2K {}）。".format(version),
    "生成：`python _gen_cp2k_sections.py`",
    "",
    "用途：`scripts/validate_inp.py` 拿它判断段名是否拼错。手工维护的子集",
    "（`KNOWN_SECTIONS`）覆盖率只有 12%，会把 `&MULLIKEN` 这类官方段误报成",
    "typo —— 这是拿真实生产输入卡测试时才暴露的假阳性。",
    "",
    "本模块**纯数据、无第三方依赖**，因此不影响 skill 的\"零依赖\"承诺。",
    '"""',
    "",
    "# 顶层段（CP2K_INPUT 的直接子段）",
    "TOP_LEVEL = frozenset({",
]
tl = sorted(top)
for i in range(0, len(tl), 4):
    lines.append("    " + " ".join('"{}",'.format(x) for x in tl[i:i + 4]))
lines += ["})", "", "# 全部 SECTION 名（含所有子段）", "SECTIONS = frozenset({"]
alln = sorted(names)
for i in range(0, len(alln), 4):
    lines.append("    " + " ".join('"{}",'.format(x) for x in alln[i:i + 4]))
lines += ["})", "",
          "# 从 cp2k_input.xml 读到的 CP2K 版本（用于核对资料的时效）",
          'CP2K_VERSION = "{}"'.format(version), ""]

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("写出 {} : {} 个 SECTION（顶层 {} 个）, CP2K 版本 {}"
      .format(os.path.relpath(OUT, ROOT), len(names), len(top), version))
sys.exit(0)
