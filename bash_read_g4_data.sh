#!/bin/bash
#SBATCH --job-name=read_data_generation
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=10:00:00
#SBATCH --constraint=cpu
#SBATCH --cpus-per-task=32
#SBATCH --mem=32GB
#SBATCH --qos=regular # or qos=debug
#SBATCH --account=m3246
##SBATCH  --image=docker:geant4/geant4:11.0.3

#mkdir -p "$output_directory"
module load conda
conda activate g4plots

#srun -n 1  python helpers_py/read_g4_data.py 
echo "Total allocated CPUs: $SLURM_CPUS_ON_NODE"
srun -n 1 python helpers_py/read_g4_multiprocess_uproot.py --pad False
echo "All  completed."
echo "End of script."
