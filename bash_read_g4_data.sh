#!/bin/bash
#SBATCH --job-name=read_data_generation
#SBATCH --nodes=1
#SBATCH --time=10:00:00
#SBATCH --constraint=cpu
#SBATCH --mem=32GB
#SBATCH --qos=regular # or qos=debug
#SBATCH --account=m3246
##SBATCH  --image=docker:geant4/geant4:11.0.3

#mkdir -p "$output_directory"
module load conda
conda activate g4plots

#srun -n 1  python helpers_py/read_g4_data.py 
srun -n 1 python helpers_py/read_g4_data.py -i /pscratch/sd/c/ccardona/datasets/data_generated_val/genAi_e-_G4_Cu_liquidArgon -o /pscratch/sd/c/ccardona/datasets/G4_individual_sims_pkl_val/ --val True
echo "All  completed."
echo "End of script."
