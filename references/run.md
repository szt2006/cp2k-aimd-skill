# CP2K 提交运行（来自讲义）

## 本地（MPI）
```bash
# 先加载编译环境（示例，按你的安装路径改）
source /home/test/opt/cp2k-7.1/tools/toolchain/install/setup
export PATH=$PATH:/home/test/opt/cp2k-7.1/exe/local/

# 纯 MPI 提交（讲义示例：4 核跑 Si_bulk8）
mpirun -n 4 cp2k.popt Si_bulk8.inp 1>cp2k.out 2>cp2k.err
```

## Slurm 集群（讲义示例：pg2_64_pool 队列，20 核 1 节点）
```bash
srun -p pg2_64_pool -n 20 -N 1 cp2k.popt cp2k.inp 1>cp2k.out 2>cp2k.err
```
也可写 sbatch 脚本：
```bash
#!/bin/bash
#SBATCH -p pg2_64_pool
#SBATCH -n 20
#SBATCH -N 1
#SBATCH -J cp2k_job
mpirun -n 20 cp2k.popt cp2k.inp > cp2k.out 2> cp2k.err
```

## 可执行文件选择
- `cp2k.popt` —— MPI（推荐大多数集群）
- `cp2k.ssmp` —— OpenMP only
- `cp2k.psmp` —— MPI + OpenMP（设好 OMP_NUM_THREADS）

## 续算（RESTART）
把上一步的 `-1.ener` / `-1.restart` / `-pos-1.xyz` 等作为输入，加：
```
&EXT_RESTART
  RESTART_FILE_NAME <prefix>-1.restart
&END EXT_RESTART
```
并在 GLOBAL 改 RUN_TYPE（如接着做 MD）。

## 输出文件
- `cp2k.out` —— 主日志（能量、SCF、受力、收敛信息）
- `cp2k-pos-1.xyz` / 每步 `-1.xyz` —— 轨迹（MD 时）
- `cp2k-1.restart` —— 重启文件
- `cp2k-<kind>_k1-1.pdos` —— 投影态密度
- `cp2k-cube-ELECTRON_DENSITY-1_0.cube` —— 电荷密度 cube（bader 用）
- 报错先 `grep -i "error\|warning\|abort" cp2k.out`。
