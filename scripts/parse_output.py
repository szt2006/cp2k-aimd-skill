#!/usr/bin/env python3
"""Parse a CP2K output (.out) for energy / forces / convergence summary.

Usage:
  python parse_output.py cp2k.out

Prints: SCF/MD energy records, final total energy, last max force,
and whether geometry optimization reached convergence.
"""
import re
import sys


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: parse_output.py cp2k.out")
    path = sys.argv[1]
    lines = open(path, errors="ignore").read().splitlines()
    print(f"== {path} ==")

    energies = []
    for ln in lines:
        m = re.search(r"ENERGY\|\s+Total FORCE_EVAL.*?:\s*([-\d.]+)", ln)
        if m:
            energies.append(float(m.group(1)))
    if energies:
        print(f"Energy records found: {len(energies)}")
        for e in energies[-5:]:
            print(f"  E = {e:.8f} a.u.")
        print(f"  Final total energy: {energies[-1]:.8f} a.u.")
    else:
        print("No ENERGY records found (maybe a non-ENERGY run, or still running).")

    maxf = None
    for ln in lines:
        if "Max. force" in ln:
            mm = re.search(r"([\d.E+-]+)", ln.split("Max. force")[-1])
            if mm:
                maxf = mm.group(1)
    if maxf:
        print(f"Last max force: {maxf}")
    else:
        print("No 'Max. force' line found.")

    if any("GEOMETRY OPTIMIZATION COMPLETE" in l for l in lines):
        print("Convergence: YES (geometry optimization complete)")
    else:
        print("Convergence: not explicitly flagged in this log.")


if __name__ == "__main__":
    main()
