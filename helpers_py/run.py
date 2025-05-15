import os
import subprocess
#particles. Leptons and some hadrons
#particles= ["e-", "e+", "mu-", "mu+", "tau-", "tau+", "nu_e", "anti_nu_e", "nu_mu", "anti_nu_mu", "nu_tau", "anti_nu_tau","p+", "n0", "pi+", "pi-", "pi0", "kaon+", "kaon-", "kaon0S", "lambda", "d"]

#materials
#absorbers= ["Lead", "Aluminium", "U235", "U238", "enriched Uranium", "Hydrogen", "Nitrogen", "Oxygen"]

#Iron, Tungsten, Copper, "Carbon", "Silicon","liquidArgon",   "Mylar","quartz", "Air", "Aerogel", "CarbonicGas", "WaterSteam"]
#gaps = ["liquidArgon", "liquidXenon","Scintillator", "Galactic","Water", "Beam", "Air"]

particles= ["e-", "mu+"]

#materials
absorbers= ["Lead"]

#Iron, Tungsten, Copper, "Carbon", "Silicon","liquidArgon",   "Mylar","quartz", "Air", "Aerogel", "CarbonicGas", "WaterSteam"]
gaps = ["liquidArgon"]

#output_directory = "particle_macros" 
output_directory = f"../data_generated/" 

#grid parameters:
nLayers = 80
abso_thick = 2 #mm
gap_thick = 4 # mm
YZ_size =120 # cm
# Energy
min_e = 1
max_e = 100
# number of particles
nParticles = 10
os.makedirs(output_directory, exist_ok=True)

#Set ENV variables

#subprocess.check_call(['sqsub', '-np', sys.argv[1], '/path/to/executable'],env=dict(os.environ, SQSUB_VAR="visible in this subprocess"))


n=0
for particle in particles:
    for abso in absorbers:
        for gap in gaps:
            n+=1
            #mac_file = os.path.join(output_directory, f"genAi_{particle.replace('+', 'plus').replace('-', 'minus').replace('0', 'zero')}_{abso}_{gap}.mac")
            folder_name = os.path.join(output_directory, f"genAi_{particle.replace('+', 'plus').replace('-', 'minus').replace('0', 'zero')}_{abso}_{gap}")
            os.makedirs(folder_name, exist_ok=True)
            # make folder to store plots
            os.makedirs(f"{folder_name}/plots", exist_ok=True)
            mac_file = os.path.join(folder_name, f"genAi_{particle.replace('+', 'plus').replace('-', 'minus').replace('0', 'zero')}_{abso}_{gap}.mac")
            stdout_file = os.path.join(folder_name, f"genAi_{particle.replace('+', 'plus').replace('-', 'minus').replace('0', 'zero')}_{abso}_{gap}.txt")
            os.environ['GAN_FNAME'] = os.path.join(folder_name, f"generated_calo.root") # visible in this process + all children
            print(f"Run. Creating Macro File for this run\n")
            with open(mac_file, "w") as f:
                f.write(f"/N03/det/setNbOfLayers {nLayers}\n")
                f.write(f"/N03/det/setAbsMat {abso}\n")
                f.write(f"/N03/det/setAbsThick  {abso_thick} mm\n")
                f.write(f"/N03/det/setGapMat {gap}\n")
                f.write(f"/N03/det/setGapThick {gap_thick} mm\n")
                f.write(f"/N03/det/setSizeYZ  {YZ_size} cm\n")
                f.write(f"/N03/det/update\n")
                f.write(f"/run/initialize\n")
                f.write(f"/run/printProgress 1\n")
                f.write(f"/run/verbose 2\n")
                f.write(f"/gps/particle {particle}\n")
                f.write(f"/gps/pos/type Beam\n")
                f.write(f"/gps/pos/centre -30.0 0.0 0.0\n")
                f.write(f"/gps/direction 1 0 0\n")
                f.write(f"/gps/ene/type Lin\n")
                f.write(f"/gps/ene/min {min_e} GeV\n")	
                f.write(f"/gps/ene/max {max_e} GeV\n")
                f.write(f"/gps/ene/gradient 0.\n")
                f.write(f"/gps/ene/intercept 1\n")	
                f.write(f"/gps/number 1\n") 
                f.write(f"/run/beamOn {nParticles}\n")
            print(f"mac_file {mac_file}")
            print(f"\nRunning Geant4 simulation\n")
            result = subprocess.run(['./build/generation', mac_file, "&>stdout_file"], capture_output=True, text=True)
            print(f"Run. Saving sdtout and stderr\n")
            with open(stdout_file, "w") as f:
                 f.write(f'Return Code: {result.returncode}\n')
                 f.write(f'Standard Output: {result.stdout}\n')
                 f.write(f'Standard Error: {result.stderr}\n')
            print(f"\nOutputfiles created in the '{folder_name}' directory.")
            print(f"Run. Creating Plots")
            plts_folder = os.path.join(folder_name, f'generated_calo.root')
            subprocess.run(['python', 'helpers_py/plot_1D_features_ROOT_x_z.py', '--in-file', plts_folder])
            print("Run Terminated!!")
            
            

        
