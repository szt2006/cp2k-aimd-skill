#!/usr/bin/env python3
"""Parse a CP2K output (.out) for energy / forces / convergence summary.

Usage:
  python parse_output.py cp2k.out
  python parse_output.py --json cp2k.out

Prints: SCF/MD energy records, final total energy, last gradients/forces,
and whether geometry optimization reached convergence.

力的字段命名（历史坑，别再来一次）:
  CP2K 的收敛表用词随 RUN_TYPE 变 —— 几何/晶胞优化用
  `Max. gradient` / `RMS gradient`，MD 等才可能用 `Max. force` /
  `RMS force`。本脚本四个都收，分别放在 max_gradient / rms_gradient /
  max_force_value / rms_force。`max_force` 这个键**保留**（下游脚本在用），
  几何优化时它的值就是 `Max. gradient`；这是历史命名，新代码请用新键。
"""
import argparse
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


def parse(path):
    """Return a dict with the parsed quantities. Never raises on missing data."""
    if not os.path.isfile(path):
        return {"error": "找不到文件: {}（请检查路径；解析需要 CP2K 的 .out 输出文件）".format(path)}
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        return {"error": "无法读取 {}: {}".format(path, exc)}

    energies = []
    for ln in lines:
        m = re.search(r"ENERGY\|\s+Total FORCE_EVAL.*?:\s*([-\d.]+)", ln)
        if m:
            try:
                energies.append(float(m.group(1)))
            except ValueError:
                pass

    # --- 收敛表里的力/梯度 ---
    # CP2K 的用词随 RUN_TYPE 变：
    #   * 几何/晶胞优化（GEO_OPT / CELL_OPT）的收敛表用 **Max. gradient /
    #     RMS gradient**（真实 opt .out 实测：Max. gradient 148 次、
    #     RMS gradient 190 次、Max. force 0 次）；
    #   * 部分 RUN_TYPE（MD / 旧版打印）才用 Max. force / RMS force。
    # 旧实现只找 "Max. force"，于是**几何优化的力永远是 None**。
    # 现在四个都收，并且**分别**给出；`max_force` 这个键保留（向后兼容），
    # 几何优化时它就是 `Max. gradient` 的值 —— 历史命名，见下方说明。
    grad = {"max_gradient": None, "rms_gradient": None,
            "max_force": None, "rms_force": None}
    _LABELS = (
        ("Max. gradient", "max_gradient"),
        ("RMS gradient", "rms_gradient"),
        ("Max. force", "max_force"),
        ("RMS force", "rms_force"),
    )
    for ln in lines:
        for label, key in _LABELS:
            if label in ln:
                mm = re.search(r"([-+]?\d+\.\d+(?:[eEdD][-+]?\d+)?)",
                               ln.split(label)[-1])
                if mm:
                    grad[key] = mm.group(1)
                    break
    # 向后兼容：max_force 这个键位历史上就是"最后一步的最大力/梯度"。
    # 几何优化时 CP2K 打的是 Max. gradient，所以这里回填它的值，
    # 免得下游脚本（以及用户）以为"没找到力"。
    max_force_compat = grad["max_force"] or grad["max_gradient"]

    scf_converged = sum(1 for l in lines if "SCF run converged" in l)
    scf_not_converged = sum(1 for l in lines if "SCF run NOT converged" in l)
    geo_done = any("GEOMETRY OPTIMIZATION COMPLETE" in l for l in lines)
    program_ended = any("PROGRAM ENDED" in l for l in lines)

    return {
        "path": path,
        "n_energy_records": len(energies),
        "last_energies": energies[-5:],
        "final_energy_au": energies[-1] if energies else None,
        "final_energy_ev": energies[-1] * 27.211386 if energies else None,
        # 向后兼容键（几何优化时 = max_gradient；MD 时 = Max. force）。
        # 新代码请用 max_gradient / rms_gradient / max_force / rms_force。
        "max_force": max_force_compat,
        "max_gradient": grad["max_gradient"],
        "rms_gradient": grad["rms_gradient"],
        "max_force_value": grad["max_force"],
        "rms_force": grad["rms_force"],
        "scf_converged_count": scf_converged,
        "scf_not_converged_count": scf_not_converged,
        "geometry_complete": geo_done,
        "program_ended": program_ended,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Parse a CP2K .out for energy / forces / convergence.",
        epilog="Example: python parse_output.py cp2k.out",
    )
    ap.add_argument("out", nargs="?", help="CP2K output file (.out)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args(argv)

    if not args.out:
        ap.print_help()
        print("\n错误：请给出 CP2K 输出文件路径，例如：python parse_output.py cp2k.out")
        return 2

    r = parse(args.out)

    if args.json:
        import json
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if "error" not in r else 1

    if "error" in r:
        print(f"错误：{r['error']}")
        return 1

    print(f"== {r['path']} ==")
    if r["n_energy_records"]:
        print(f"Energy records found: {r['n_energy_records']}")
        for e in r["last_energies"]:
            print(f"  E = {e:.8f} a.u.")
        print(f"  Final total energy: {r['final_energy_au']:.8f} a.u."
              f"  (= {r['final_energy_ev']:.4f} eV)")
    else:
        print("No ENERGY records found (maybe a non-ENERGY run, or still running).")

    # 力/梯度：四个量分别报（几何优化看 gradient，MD/其它看 force）
    if r["max_gradient"] is not None or r["rms_gradient"] is not None:
        print("Last gradient (几何优化收敛表，a.u./bohr):")
        if r["max_gradient"] is not None:
            print(f"  Max. gradient = {r['max_gradient']}")
        if r["rms_gradient"] is not None:
            print(f"  RMS gradient  = {r['rms_gradient']}")
    if r["max_force_value"] is not None or r["rms_force"] is not None:
        print("Last force (MD / 其它 RUN_TYPE):")
        if r["max_force_value"] is not None:
            print(f"  Max. force = {r['max_force_value']}")
        if r["rms_force"] is not None:
            print(f"  RMS force  = {r['rms_force']}")
    if r["max_force"] is not None:
        # 向后兼容键：几何优化时它就是 Max. gradient 的值
        print(f"max_force (兼容键) = {r['max_force']}")
    else:
        print("No 'Max. gradient' / 'Max. force' line found.")

    if r["scf_not_converged_count"]:
        print(f"SCF: converged {r['scf_converged_count']} / "
              f"NOT converged {r['scf_not_converged_count']}"
              "  <-- 注意：CP2K 不收敛也会继续下一步，需人工检查")
    else:
        print(f"SCF: converged {r['scf_converged_count']} times, no non-convergence.")

    if r["geometry_complete"]:
        print("Convergence: YES (geometry optimization complete)")
    else:
        print("Convergence: not explicitly flagged in this log.")

    if r["program_ended"]:
        print("Run status: PROGRAM ENDED (normal termination)")
    else:
        print("Run status: no 'PROGRAM ENDED' — 可能仍在运行或异常中断")
    return 0


if __name__ == "__main__":
    sys.exit(main())
