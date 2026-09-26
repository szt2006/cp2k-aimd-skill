#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""控制台输出兼容层 —— 让 CLI 在任意代码页下都不抛异常（中文 Windows 关键）。

问题（v2.7.0 实测缺陷）
----------------------
Windows 中文版控制台默认代码页 936(GBK)，Python 按区域编码写 stdout。
本 skill 的输出含 GBK **无法表示**的字符：

    ✓ U+2713   ✗ U+2717   • U+2022   ⚠ U+26A0   ✖ U+2716
    ↻ U+21BB   ⑪ U+246A   Å U+00C5  ² U+00B2   ³ U+00B3   ö U+00F6

于是 print() 直接抛

    UnicodeEncodeError: 'gbk' codec can't encode character '\\u2713'

并打印 traceback —— 违反 AGENTS.md §6.3「不抛 traceback」的健壮性基线。
实测崩溃的命令恰好覆盖文档主推的新手路径：
  * doctor.py   默认模式（✓）
  * recommend.py 主输出（•）
  * guide.py list（⑪）
  * diagnose.py  只要出现 WARN/ERROR 结论（⚠/✖）

策略（分层，永不抛异常）
------------------------
  1) Windows 且 stdout 是终端 → 先把控制台输出代码页切到 UTF-8(65001)；
     成功则 stdout/stderr 一律 UTF-8，✓ ⑪ Å ² 等符号**原样显示**。
  2) 输出被重定向（管道/文件）→ 直接 UTF-8：日志统一编码，便于 grep、
     跨平台、与本 skill 的 UTF-8 文档一致。
  3) 以上都不可行 → 保留原编码，但设 errors="replace"：
     最坏情况是少数符号显示成 "?"，**绝不抛 traceback**。

说明与边界
----------
  * 只改**输出**：不动 stdin，也不动输入代码页，所以交互式输入中文的行为
    与改动前完全一致。
  * `SetConsoleOutputCP` 会作用于进程共享的那个控制台，脚本退出后该控制台的
    输出代码页保持 UTF-8。这是 `chcp 65001` 的程序化等价物，也是中文环境下
    显示 UTF-8 的通行做法；失败时自动回落到策略 3，不影响功能。
  * 幂等：重复调用无副作用；任何内部异常都被吞掉——兼容层自己出问题也绝不能
    影响主功能。

用法（9 个 CLI + 4 个 harness 统一用同一段引导代码）
----------------------------------------------------
    try:
        import os as _os, sys as _sys
        _here = _os.path.dirname(_os.path.abspath(__file__))
        for _d in (_here, _os.path.join(_here, "scripts")):
            if _d not in _sys.path:
                _sys.path.insert(0, _d)
        import _console  # noqa: F401  导入即生效
    except Exception:
        pass

零依赖，只用标准库。
"""
import os
import sys

__all__ = ["install", "CONSOLE_CP"]

CONSOLE_CP = 65001  # UTF-8 代码页


def _switch_console_to_utf8():
    """Windows：把控制台输出代码页切到 UTF-8。成功返回 True，永不抛异常。"""
    if os.name != "nt":
        return False
    try:
        import ctypes

        return bool(ctypes.windll.kernel32.SetConsoleOutputCP(CONSOLE_CP))
    except Exception:
        return False


def _is_tty(stream):
    """stream 是否为终端。永不抛异常。"""
    try:
        return bool(stream is not None and stream.isatty())
    except Exception:
        return False


def install():
    """让 stdout/stderr 在任何代码页下都能安全输出。

    返回生效的编码名（str）或 None（表示保留本地编码 + 有损兜底）。
    本函数保证不抛异常。
    """
    try:
        tty = _is_tty(getattr(sys, "stdout", None))

        # 目标编码：重定向 → UTF-8；
        # 终端 → 只有代码页切换成功才敢用 UTF-8，否则保留本地编码
        target = "utf-8"
        if os.name == "nt" and tty and not _switch_console_to_utf8():
            target = None

        for name in ("stdout", "stderr"):
            stream = getattr(sys, name, None)
            if stream is None:  # pythonw 下 sys.stdout 可能为 None
                continue
            try:
                if target:
                    stream.reconfigure(encoding=target, errors="replace")
                else:
                    stream.reconfigure(errors="replace")
            except Exception:
                # reconfigure 不可用（被包装过的流、老 Python）→ 尽力而为
                pass

        if target:
            return target
        return getattr(sys.stdout, "encoding", None)
    except Exception:
        return None


# 导入即生效：调用方只需 `import _console`
install()
