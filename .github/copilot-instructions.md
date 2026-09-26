# GitHub Copilot instructions

完整说明见 [`AGENTS.md`](../AGENTS.md)（本文件只是指针，不重复内容）。

本项目是 **CP2K 计算顾问 skill**：知识库 + 零依赖命令行工具链，不是自动跑计算的流水线。

## 要点

- 核心 7 个脚本只需 Python 标准库；仅 `scripts/postprocess.py` 另需 numpy + matplotlib。
- 用户第一次使用，先引导执行 `python scripts/doctor.py`（环境自检）。
- 新手引导顺序：`doctor.py` → `wizard.py` → `examples/01_si_bulk_static/`。
- 不确定参数时用 `python scripts/recommend.py` 取推荐，不要凭记忆编。
- 知识引用优先用 `references/official/`（G 层官方权威层）。
- 改动后必须串行重跑三项校验，规则见 `CONTRIBUTING.md`。
