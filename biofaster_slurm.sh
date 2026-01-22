#!/bin/bash
## specify an email address
#SBATCH --mail-user=uneri@lbl.gov
## specify when to send the email when job is (a)borted, (b)egins, or (e)nds
#SBATCH --mail-type=FAIL
## specify allocation - we want jgi_shared since we don't want to use the whole node for nothing
#SBATCH -A grp-org-sc-metagen
#SBATCH -q jgi_normal
## specify number of nodes
#SBATCH -N 1
#######SBATCH --exclusive
## specify number of procs
#SBATCH -c 8
## specify ram  
#SBATCH --mem=70G 
## specify runtime
#SBATCH -t 72:00:00
## specify job name
#SBATCH -J biofaster
## specify output and error file
#SBATCH -o /clusterfs/jgi/scratch/science/metagen/neri/code/blits/biofaster/slurm.out
#SBATCH -e /clusterfs/jgi/scratch/science/metagen/neri/code/blits/biofaster/slurm.err



cd /clusterfs/jgi/scratch/science/metagen/neri/code/blits/biofaster/
pixi run bash ./run_all_benchmarks.sh  -S --warmup 1 -r 2 --sizes "0.1m,1m,20m,50m,70m,100m" 2>&1 | tee benchmark_run_$(date +%Y%m%d_%H%M%S).log # running externally
