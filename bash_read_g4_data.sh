#!/bin/bash
#SBATCH --job-name=genai_datageneration
#SBATCH --nodes=1
#SBATCH --ntasks=1 # Request one task per item in the list
#SBATCH --cpus-per-task=1  # Or more if ./a.out can use them
#SBATCH --time=10:00:00
#SBATCH --constraint=cpu
#SBATCH --mem=32GB
#SBATCH --qos=regular # or qos=debug
#SBATCH --account=m3246
##SBATCH  --image=docker:geant4/geant4:11.0.3

#mkdir -p "$output_directory"
module load conda
conda activate g4plots

srun -n 1  python helpers_py/read_g4_data.py

echo "All  completed."
echo "End of script."