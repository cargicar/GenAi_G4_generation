#!/bin/bash

#SBATCH --job-name=genai_datageneration
#SBATCH --nodes=1
#SBATCH --ntasks=32 # Request one task per item in the list
#SBATCH --cpus-per-task=1  # Or more if ./a.out can use them
#SBATCH --time=10:00:00
#SBATCH --constraint=cpu
#SBATCH --qos=regular
#SBATCH --account=m3246
#SBATCH  --image=docker:geant4/geant4:11.0.3

## Run as sbatch --env-file=datasets.env ./slurm_bash.sh
#Debug
# env G4FORCENUMBEROFTHREADS=4
#/run/numberOfThreads 32
#particles=("e-" "mu+")
#absorbers=("Lead")
#gaps=("liquidArgon")
#output_directory="../data_generated_debug/"

# Particles. Leptons and some hadrons
particles=("e-" "e+" "mu-" "mu+" "tau-" "tau+" "nu_e" "anti_nu_e" "nu_mu" "anti_nu_mu" "nu_tau" "anti_nu_tau" "p+" "n0" "pi+" "pi-" "pi0" "kaon+" "kaon-" "kaon0S" "lambda" "d")

# Materials
absorbers=("Lead" "Aluminium" "Hydrogen" "Nitrogen" "Oxygen")
# absorbers=("Iron" "Tungsten" "Copper" "Carbon" "Silicon" "liquidArgon" "Mylar" "quartz" "Air" "Aerogel" "CarbonicGas" "WaterSteam")

# Gaps
gaps=("liquidArgon" "liquidXenon" "Scintillator" "Galactic" "Water" "Beam" "Air")
output_directory="../data_generated_scheduled/"

mkdir -p "$output_directory"

# Grid parameters:
nLayers=80
abso_thick=2 # mm
gap_thick=4 # mm
YZ_size=120 # cm
# Energy
min_e=1
max_e=100
# Number of particles
nParticles=1000

n=0
for particle in "${particles[@]}"; do
  for abso in "${absorbers[@]}"; do
    for gap in "${gaps[@]}"; do
      n=$((n+1))
      #folder_name="${output_directory}genAi_${particle//+/plus//-/minus//0/zero}_${abso}_${gap}"
      folder_name="${output_directory}genAi_${particle}_${abso}_${gap}"
      mkdir -p "$folder_name"
      mkdir -p "${folder_name}/plots"
      #mac_file="${folder_name}/genAi_${particle//+/plus//-/minus//0/zero}_${abso}_${gap}.mac"
      mac_file="${folder_name}/genAi_${particle}_${abso}_${gap}.mac"
      #stdout_file="${folder_name}/genAi_${particle//+/plus//-/minus//0/zero}_${abso}_${gap}.txt"
      stdout_file="${folder_name}/genAi_${particle}_${abso}_${gap}.txt"
      export GAN_FNAME="${folder_name}/generated_calo.root"
      echo "Run. Creating Macro File for this run"

      cat > "$mac_file" <<EOF
/N03/det/setNbOfLayers $nLayers
/N03/det/setAbsMat "$abso"
/N03/det/setAbsThick  ${abso_thick} mm
/N03/det/setGapMat "$gap"
/N03/det/setGapThick ${gap_thick} mm
/N03/det/setSizeYZ  ${YZ_size} cm
/N03/det/update
/run/initialize
/run/printProgress 1
/run/verbose 2
/gps/particle $particle
/gps/pos/type Beam
/gps/pos/centre -30.0 0.0 0.0
/gps/direction 1 0 0
/gps/ene/type Lin
/gps/ene/min ${min_e} GeV
/gps/ene/max ${max_e} GeV
/gps/ene/gradient 0.
/gps/ene/intercept 1
/gps/number 1
/run/beamOn $nParticles
EOF

      echo "mac_file $mac_file"
      echo ""
      echo "Running Geant4 simulation"
      echo "Outputfiles to be store in '$folder_name' directory."
      srun -n 1  shifter  --env-file=datasets.env ./build/generation "$mac_file" &> "$stdout_file" &
      echo "Run. Saving stdout and stderr"
      #echo "Return Code: $?" > "$stdout_file"
      #cat "$stdout_file"
      echo ""
      echo "Outputfiles created in the '$folder_name' directory."
      echo "Run. Creating Plots"
      plts_folder="${folder_name}/generated_calo.root"
      conda activate geant4_study
      python helpers_py/plot_1D_features_ROOT_x_z.py --in-file "$plts_folder"
      echo "Run Terminated!!"
    done
  done
done
wait
