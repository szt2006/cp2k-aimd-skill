#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「庚子计算整理-cp2k资料」里的**非 PDF 素材** `CP2K User Self Support.doc` 抽成可读文本。

背景与更正留痕
--------------
`references/h_tutorials/README.md` §8 曾把这份 `.doc` 记为：**「旧版 Word 二进制格式，
`pdfplumber` 无法解析；如实标注为未抽取，需要时用 Word/LibreOffice 另存为 docx/pdf」**。
**该表述已被证伪**：本机没有 `olefile` / `soffice` / `antiword`，但
OLE2/Word97 的文本层**可以直接用标准库读出来** —— 只要解析 OLE2 复合文档头
（512 字节头 / FAT / 目录项）找到 `WordDocument` 流，再按该流 FIB 里的
`fcMin`/`fcMac` 切出正文，按 **cp1252** 解码即可。

所以本脚本**只用标准库**（`struct`/`io`/`os`/`sys`/`argparse`/`re`）实现一个
**最小 OLE2/Word97 抽取器**，兑现本 skill「核心零依赖」的承诺，不再需要
Word / LibreOffice / `olefile` / `antiword`。

它与 `extract_tutorials.py` 的关系
----------------------------------
| 脚本 | 输入 | 产物 | 编号空间 |
|---|---|---|---|
| `extract_tutorials.py` | 官方教程 **PDF** | `txt/T01–T24_*.txt`（带 `========== PAGE N ==========`） | **T 编号** |
| `extract_doc.py`（本脚本） | 非 PDF 素材（**.doc**） | `doc_text/*.txt`（**无页码标记**） | **不占 T 编号** |

> **为什么不叫 `T25`**：`T01–T24` 是"**PDF 逐页抽取 + `========== PAGE N ==========`
> 页码标记**"的专用编号空间。`.doc` 里没有页标记，塞进该空间会同时破坏
> `_audit_h_citations.py` 的页码审计与全仓库「24 份教程 / 701 页」的口径。
> 因此产物放与 `txt/` **平行**的 `doc_text/` 子目录。

抽取的已知局限
--------------
* **只用正文文字**：FIB 的 `ccpText` 指向文本层，只覆盖**正文**。
  表格、图片、批注、脚注、页眉页脚、修订记录**都不保留**；
  域代码（`HYPERLINK` 等）会以"域结果 + 少量残留控制字符"的形式出现。
* **控制字符会被删掉**（保留换行/Tab）：Word97 用 `\\x07` 标记单元格结束、
  `\\x13/\\x14/\\x15` 标记域开始/分隔/结束、`\\x01` 标记图片，这些**不是原文可见字符**。
  删掉后可能**丢掉表格的行列边界** —— 读到时按语义还原。
* **编码固定按 cp1252 解码**：旧版 Word 的中文 Windows 文档也可能用 cp936，
  但本文件的实测文本层是 cp1252（见下"抽取统计"）。脚本不做编码猜测，
  解码失败一律 `errors="replace"`，**绝不因为一个字节抛异常**。

用法
----
    set CP2K_TUTORIAL_SRC=D:\\cp2k-aimd\\study\\庚子计算整理-cp2k资料-持续更新
    python extract_doc.py
或
    python extract_doc.py --src "<目录或 .doc 文件>" [--out <目录>] [--list]

源目录约定与 `extract_tutorials.py` 一致：`--src` 参数 → 环境变量
`CP2K_TUTORIAL_SRC`。**两者都没有时不猜路径**，直接给 usage 并 exit 2。

退出码（AGENTS.md §6.3 健壮性基线）：
  0 = 成功；1 = 路径不存在、源里没有 `.doc`、抽取失败（**一律友好中文，不抛 traceback**）；
  2 = 参数不全（无 `--src` 且无 `CP2K_TUTORIAL_SRC`）。
"""
import argparse
import io
import os
import re
import struct
import sys

# --- 控制台编码兼容层（中文 Windows/GBK 下输出不再抛异常）---
# 与同目录 extract_tutorials.py 完全一致的引导：_console.py 在仓库根的 scripts/ 下，
# 本脚本在 references/h_tutorials/ 下，所以要往上走两级再补 scripts/。
try:
    import os as _os, sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _scripts = _os.path.join(_here, _os.pardir, _os.pardir, "scripts")
    for _d in (_here, _scripts):
        if _d not in _sys.path:
            _sys.path.insert(0, _d)
    import _console  # noqa: F401  导入即生效，见 scripts/_console.py
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

# 默认产物目录：与 txt/ 平行，理由见模块 docstring。
DEFAULT_OUT = os.path.join(HERE, "doc_text")

# 本机「庚子计算整理-cp2k资料-持续更新」的位置。**只用于报错时提示**，
# 绝不作为默认源自动生效 —— 否则"无参数"会静默去抽一个没被指定的目录，
# 既违反 AGENTS.md §6.3（无参数应 usage + exit 2），也让脚本在别人机器上乱跑。
HINT_SRC = r"D:\cp2k-aimd\study\庚子计算整理-cp2k资料-持续更新"

OLE_SIG = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
# FAT 里 >= 0xFFFFFFFA 的都是特殊值（FREESECT 0xFFFFFFFF / ENDOFCHAIN 0xFFFFFFFE /
# FATSECT / DIFSECT），一律表示"链到此结束"，不指向数据 sector。
SPECIAL_FROM = 0xFFFFFFFA
DIR_ENTRY_SIZE = 128
MAXREG = 0xFFFFFFF0          # 防呆：单条链最长这么多个 sector，超过即判为 FAT 损坏


class OLEError(Exception):
    """OLE2 解析失败。message 里带上失败在**哪一步**，便于友好报错。"""


# ---------------------------------------------------------------------------
# 最小 OLE2（复合文档）读取器
# ---------------------------------------------------------------------------
def _u16(buf, off):
    return struct.unpack_from("<H", buf, off)[0]


def _u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


def parse_header(raw):
    """解析 512 字节 OLE2 头，返回给后续步骤用的参数字典。

    检查点（失败即抛 OLEError，并说明卡在哪一步）：
      ① 魔数 `D0 CF 11 E0 A1 B1 1A E1`；② 文件至少 512 字节；
      ③ sector shift 在 7–20（sector 128 B – 1 MB）。
    """
    if len(raw) < 512:
        raise OLEError("文件只有 %d 字节，不足 OLE2 头的 512 字节" % len(raw))
    if raw[:8] != OLE_SIG:
        raise OLEError("不是 OLE2 复合文档（前 8 字节为 %s，期望 %s）"
                       % (raw[:8].hex(), OLE_SIG.hex()))
    sect_shift = _u16(raw, 30)
    if not 7 <= sect_shift <= 20:
        raise OLEError("OLE2 头的 sector shift=%d 不合理（应在 7–20）" % sect_shift)
    ssz = 1 << sect_shift
    if len(raw) < 512 + ssz:
        raise OLEError("文件只有 %d 字节，连第 1 个 sector（%d 字节）都不完整"
                       % (len(raw), ssz))
    return {
        "sector_size": ssz,
        "num_fat": _u32(raw, 44),          # FAT 占用的 sector 数
        "dir_start": _u32(raw, 48),        # 目录流首 sector
        "mini_cutoff": _u32(raw, 56),
        "difat": list(struct.unpack_from("<109I", raw, 76)),  # 头内嵌的 FAT sector 号
    }


def read_fat(raw, hdr):
    """读 FAT（先取头内嵌的 109 项 DIFAT；本文件 num_difat=0，用不到扩展 DIFAT）。

    扩展 DIFAT（头里放不下的 FAT sector 号，存在 `_u32(raw,68)` 起点的链上）
    **未实现** —— 那需要 FAT 本身才能遍历，属于"够用就行"之外。
    真遇到时 `num_fat > 109` 会在这里明确报错，而不是静默抽出半截文本。
    """
    ssz = hdr["sector_size"]
    per_sector = ssz // 4
    fat_sids = []
    for sid in hdr["difat"]:
        if len(fat_sids) >= hdr["num_fat"]:
            break
        if sid >= SPECIAL_FROM:
            continue
        if sid >= (len(raw) - 512) // ssz:
            raise OLEError("FAT sector 号 %d 越界（文件只有 %d 个 sector）"
                           % (sid, (len(raw) - 512) // ssz))
        fat_sids.append(sid)
    if len(fat_sids) < hdr["num_fat"]:
        raise OLEError(
            "FAT 需要 %d 个 sector，但头内嵌 DIFAT 只给出 %d 个"
            "（本脚本不支持扩展 DIFAT）" % (hdr["num_fat"], len(fat_sids)))
    fat = []
    for sid in fat_sids:
        off = 512 + sid * ssz
        blk = raw[off:off + ssz]
        if len(blk) < ssz:
            raise OLEError("读 FAT 时 sector %d 不完整（文件被截断？）" % sid)
        fat.extend(struct.unpack("<%dI" % per_sector, blk))
    return fat


def sector_offset(sid, ssz):
    """sector 号 → 文件偏移。头本身占第 0 个 512 字节块，数据 sector 从 512 起。"""
    if sid >= SPECIAL_FROM:
        raise OLEError("sector 号 0x%08X 是特殊值，不指向数据" % sid)
    return 512 + sid * ssz


def chain_of(fat, start, what, maxreg=MAXREG):
    """按 FAT 走一条 sector 链，返回 sector 号列表（含环检测）。"""
    out = []
    seen = set()
    sid = start
    while sid < SPECIAL_FROM:
        if len(out) > maxreg:
            raise OLEError("走 %s 的 sector 链超过 %d 个 sector，疑为 FAT 损坏"
                           % (what, maxreg))
        if sid in seen:
            raise OLEError("走 %s 的 sector 链出现环（sector %d 重复）" % (what, sid))
        if sid >= len(fat):
            raise OLEError("走 %s 的 sector 链时 sector %d 超出 FAT 长度 %d"
                           % (what, sid, len(fat)))
        seen.add(sid)
        out.append(sid)
        sid = fat[sid]
    return out


def read_stream(raw, fat, ssz, start, size, what, mini_cutoff=4096):
    """读一条普通的（非 mini）流，按目录项里的 size 截断。

    本文件的 `WordDocument` 有 51 234 字节（> mini_cutoff 4096），是**常规流**，
    所以不需要 mini-FAT。小于 cutoff 的流走 mini 流（存在 Root Entry 的流里），
    本脚本不实现 —— 真遇到时在这里**明确报错**，而不是抽出一堆垃圾字节。
    """
    if size == 0:
        raise OLEError("%s 流长度为 0" % what)
    if size < mini_cutoff:
        raise OLEError("%s 流只有 %d 字节（< mini cutoff %d），属于 mini 流，"
                       "本脚本不支持" % (what, size, mini_cutoff))
    sids = chain_of(fat, start, what)
    data = b"".join(raw[sector_offset(s, ssz):sector_offset(s, ssz) + ssz]
                    for s in sids)
    if len(data) < size:
        raise OLEError("%s 流不完整：目录项声明 %d 字节，链上只取到 %d 字节"
                       % (what, size, len(data)))
    return data[:size]


def read_directory(raw, fat, hdr):
    """读目录流，返回 [(名字, 类型, 首sector, 字节数), ...]。"""
    ssz = hdr["sector_size"]
    sids = chain_of(fat, hdr["dir_start"], "目录流")
    per_sector = ssz // DIR_ENTRY_SIZE
    entries = []
    for sid in sids:
        blk = raw[sector_offset(sid, ssz):sector_offset(sid, ssz) + ssz]
        for j in range(per_sector):
            e = blk[j * DIR_ENTRY_SIZE:(j + 1) * DIR_ENTRY_SIZE]
            if len(e) < DIR_ENTRY_SIZE:
                continue
            nlen = _u16(e, 64)                      # 名字字节数（含结尾 NUL）
            if nlen < 2 or nlen > DIR_ENTRY_SIZE:
                continue
            name = e[:nlen - 2].decode("utf-16-le", "replace")
            etype = e[66]
            start = _u32(e, 116)
            size = _u32(e, 120)
            entries.append((name, etype, start, size))
    if not entries:
        raise OLEError("目录流里没有任何有效目录项")
    return entries


def find_stream(raw, fat, hdr, entries, want):
    """在目录项里按名字找流（类型 2 = stream）。返回 (首sector, 字节数)。"""
    for name, etype, start, size in entries:
        if etype == 2 and name == want:
            return start, size
    names = ", ".join(repr(n) for n, t, _s, _z in entries if t == 2)
    raise OLEError("目录里没有 %s 流（现有流：%s）" % (want, names or "无"))


# ---------------------------------------------------------------------------
# Word97（.doc）正文抽取
# ---------------------------------------------------------------------------
def extract_fib_range(wd):
    """从 WordDocument 流的 FIB 取 (fcMin, fcMac)。

    Word 97 FIB 的**前 32 字节是 Word 6/95 兼容区**，`fcMin`/`fcMac` 就落在
    偏移 24 / 28（这也是网上"`fcMin=1536`"这个说法的来源）。本文件实测：
    `wIdent=0xA5EC`（Word 文档魔数）、`nFib=193`（Word 97）、`fcMin=1536`、
    `fcMac=36840`。
    """
    if len(wd) < 32:
        raise OLEError("WordDocument 流只有 %d 字节，放不下 FIB 前 32 字节" % len(wd))
    w_ident = _u16(wd, 0)
    n_fib = _u16(wd, 2)
    fc_min = _u32(wd, 24)
    fc_mac = _u32(wd, 28)
    if w_ident != 0xA5EC:
        raise OLEError("WordDocument 流的 wIdent=0x%04X ≠ 0xA5EC，不像 Word 文档"
                       % w_ident)
    if not 0 < fc_min < fc_mac <= len(wd):
        raise OLEError("FIB 的 fcMin=%d / fcMac=%d 不合理（流长 %d）"
                       % (fc_min, fc_mac, len(wd)))
    return fc_min, fc_mac, {"wIdent": w_ident, "nFib": n_fib}


def decode_text(data):
    """cp1252 解码 + 删不可打印控制字符（保留换行与 Tab）。返回 (文本, 统计)。

    处理规则（"够用就行"，不做版式还原）：
      * `\\r\\n` / 单独 `\\r` / `\\n` → `\\n`（统一 LF，产物才可跨平台 diff）；
      * `\\x0b`（垂直制表）/ `\\x0c`（换页）→ `\\n`（Word 用它们断行/断页）；
      * `\\t` 保留（原文缩进有意义）；
      * 其余 C0/C1 控制字符删掉 —— 它们是 Word 的**结构标记**而非可见字符：
        `\\x07` 单元格结束、`\\x13/\\x14/\\x15` 域开始/分隔/结束、`\\x01` 图片、
        `\\x00` 填充。删掉会丢表格边界，这是本脚本**声明的局限**。
    """
    txt = data.decode("cp1252", "replace")
    n_raw = len(txt)
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    txt = txt.replace("\x0b", "\n").replace("\x0c", "\n")
    kept = []
    n_ctrl = 0
    for ch in txt:
        if ch in "\n\t":
            kept.append(ch)
        elif ch < " " or "\x7f" <= ch <= "\x9f":
            n_ctrl += 1
        else:
            kept.append(ch)
    txt = "".join(kept)
    n_print = sum(1 for ch in txt if ch.isprintable() or ch in "\n\t")
    stats = {
        "chars_raw": n_raw,
        "chars": len(txt),
        "ctrl_removed": n_ctrl,
        "printable": n_print,
        "printable_ratio": (n_print / len(txt)) if txt else 0.0,
    }
    return txt, stats


def extract_doc(path):
    """抽一个 .doc 文件。成功返回 (文本, 元信息)；失败抛 OLEError（带失败步骤）。"""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise OLEError("读文件失败：%s" % exc)

    hdr = parse_header(raw)                        # ① 头
    fat = read_fat(raw, hdr)                       # ② FAT
    entries = read_directory(raw, fat, hdr)        # ③ 目录
    start, size = find_stream(raw, fat, hdr, entries, "WordDocument")  # ④ 流
    wd = read_stream(raw, fat, hdr["sector_size"], start, size, "WordDocument",
                     mini_cutoff=hdr["mini_cutoff"])
    fc_min, fc_mac, fib = extract_fib_range(wd)    # ⑤ FIB
    text, stats = decode_text(wd[fc_min:fc_mac])   # ⑥ 解码

    meta = {
        "file_size": len(raw),
        "sector_size": hdr["sector_size"],
        "wd_size": size,
        "fcMin": fc_min,
        "fcMac": fc_mac,
        "nFib": fib["nFib"],
    }
    meta.update(stats)
    return text, meta


# ---------------------------------------------------------------------------
# 源定位与产物命名
# ---------------------------------------------------------------------------
def slug_of(name):
    """源文件名 → 产物文件名。风格与 `txt/T01_<slug>.txt` 对齐（小写 + 下划线）。"""
    base = os.path.splitext(os.path.basename(name))[0]
    slug = re.sub(r"[^0-9A-Za-z]+", "_", base).strip("_").lower()
    return (slug or "doc") + ".txt"


def find_docs(src):
    """src 是文件 → [它]（只要不是 .docx）；是目录 → 递归收集所有 .doc。

    注意 `.docx` 是 zip 包、不是 OLE2，**明确排除**（`endswith(".doc")` 本身
    就不会匹配 `.docx`，这里再显式说明一次，免得后来人改成 startswith）。
    """
    if os.path.isfile(src):
        if src.lower().endswith(".doc"):
            return [src]
        return []
    docs = []
    for dp, _dns, fns in os.walk(src):
        for fn in fns:
            if fn.lower().endswith(".doc"):
                docs.append(os.path.join(dp, fn))
    docs.sort()
    return docs


def write_out(out_path, text, meta, src_name):
    """写产物：UTF-8 **无 BOM**、**LF** 换行、开头几行 `#` 注释头。"""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# SOURCE: %s\n" % src_name)
        fh.write("# FORMAT: OLE2 / Word97 (fcMin=%d fcMac=%d)\n"
                 % (meta["fcMin"], meta["fcMac"]))
        fh.write("# ENCODING: cp1252\n")
        fh.write("# NOTE: 正文文字抽取，未保留表格/图片/批注\n")
        fh.write("\n")
        fh.write(text)
        if not text.endswith("\n"):
            fh.write("\n")


def path_ok(path):
    """路径存在性检查，且**永不抛异常**。

    `os.path.exists()` 遇到含代理字符（surrogateescape）的路径会抛
    UnicodeEncodeError —— 中文 Windows 上设 `CP2K_TUTORIAL_SRC` 这类
    **非 ASCII 环境变量**（PowerShell 的 `$env:X='中文'` 传给 os.environ 时
    常见）就会踩到。这里按"路径不可用"处理，交给调用方友好报错。
    """
    try:
        return os.path.exists(path)
    except (OSError, ValueError, UnicodeError):
        return False


def main():
    ap = argparse.ArgumentParser(
        description="抽取非 PDF 素材（.doc / OLE2 Word97）到 H 层 doc_text/")
    ap.add_argument("--src", default=os.environ.get("CP2K_TUTORIAL_SRC"),
                    help="源目录或单个 .doc 文件；也可用环境变量 CP2K_TUTORIAL_SRC")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="输出目录，默认 references/h_tutorials/doc_text/")
    ap.add_argument("--list", action="store_true",
                    help="只列出源里的 .doc 清单（含每个 .doc 的 FC 区间与可打印率），不抽取")
    args = ap.parse_args()

    # 0) 参数不全 → usage + exit 2（与 extract_tutorials.py 同款提示）
    if not args.src:
        print("请用 --src 指定目录或单个 .doc 文件，或设置环境变量 CP2K_TUTORIAL_SRC。",
              file=sys.stderr)
        print("（本机该资料目录通常为：%s）" % HINT_SRC, file=sys.stderr)
        ap.print_usage(sys.stderr)
        return 2

    # 1) 源不存在 → 友好中文 + exit 1（不抛 traceback）
    if not path_ok(args.src):
        print("错误：源路径不存在 —— %s" % args.src, file=sys.stderr)
        print("提示：用 --src 指定目录或单个 .doc 文件，"
              "或设置环境变量 CP2K_TUTORIAL_SRC。", file=sys.stderr)
        print("      本机该资料目录通常为：%s" % HINT_SRC, file=sys.stderr)
        return 1

    docs = find_docs(args.src)
    if not docs:
        kind = "文件" if path_ok(args.src) and not os.path.isdir(args.src) else "目录"
        print("错误：%s里没有 .doc 文件 —— %s" % (kind, args.src), file=sys.stderr)
        print("提示：本脚本只处理旧版 Word 二进制（OLE2/Word97）。"
              ".docx / .pdf 请分别用 python-docx 与 extract_tutorials.py。",
              file=sys.stderr)
        return 1

    if args.list:
        print("源：%s" % args.src)
        print("发现 %d 个 .doc：" % len(docs))
        rc = 0
        for p in docs:
            try:
                text, meta = extract_doc(p)
            except OLEError as exc:
                print("  [解析失败] %s\n      失败在：%s" % (p, exc))
                rc = 1
                continue
            print("  %s" % p)
            print("      大小 %d 字节 | sector %d B | WordDocument %d 字节 | "
                  "fcMin=%d fcMac=%d | nFib=%d"
                  % (meta["file_size"], meta["sector_size"], meta["wd_size"],
                     meta["fcMin"], meta["fcMac"], meta["nFib"]))
            print("      文本 %d 字符（可打印 %.2f%%，删控制字符 %d 个）→ 将写 %s"
                  % (meta["chars"], meta["printable_ratio"] * 100,
                     meta["ctrl_removed"], slug_of(p)))
        return rc

    n_ok = 0
    for p in docs:
        out_path = os.path.join(args.out, slug_of(p))
        try:
            text, meta = extract_doc(p)
        except OLEError as exc:
            print("错误：抽取失败 —— %s" % p, file=sys.stderr)
            print("      失败在：%s" % exc, file=sys.stderr)
            print("      请确认它是旧版 Word 二进制（OLE2）且未加密/未损坏。",
                  file=sys.stderr)
            n_ok -= 1
            continue

        if not text.strip():
            print("错误：抽取结果为空 —— %s" % p, file=sys.stderr)
            print("      失败在：fcMin=%d..fcMac=%d 区间解不出可见字符"
                  % (meta["fcMin"], meta["fcMac"]), file=sys.stderr)
            n_ok -= 1
            continue

        write_out(out_path, text, meta, os.path.basename(p))
        n_lines = text.count("\n") + (0 if text.endswith("\n") else 1)
        size = os.path.getsize(out_path)
        print("WROTE %s" % os.path.relpath(out_path, HERE))
        print("      源 %s（%d 字节）| OLE2 sector %d B | WordDocument %d 字节"
              % (os.path.basename(p), meta["file_size"], meta["sector_size"],
                 meta["wd_size"]))
        print("      FIB fcMin=%d fcMac=%d nFib=%d | 编码 cp1252"
              % (meta["fcMin"], meta["fcMac"], meta["nFib"]))
        print("      正文 %d 字符 | 可打印 %.2f%% | 删控制字符 %d 个 | "
              "产物 %d 行 / %d 字节"
              % (meta["chars"], meta["printable_ratio"] * 100,
                 meta["ctrl_removed"], n_lines, size))
        n_ok += 1

    return 0 if n_ok > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
