import uproot
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from keras.utils import to_categorical
import numpy as np
import argparse
import os
import h5py as h5
import uproot
import pickle
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import itertools

# particles=("e-" "mu-" "gamma" "neutron" "proton" "pi+" "kaon0L")
# absorbers=("G4_Pb" "G4_W" "G4_U" "G4_Cu" "brass" "StainlessSteel")
# Gaps liquidArgon, liquidXenon, Scintillator, Silicon
# gaps=("liquidArgon" "G4_lXe" "Scintillator" "G4_Si")
particle_labels = {
  "e-":0,
  "mu-":1, 
  "gamma":2,
  "neutron":3,
  "proton":4, 
  "pi+":5,
  "kaon0L":6
  }
absorber_labels = {
  "G4_Pb":0,
  "G4_W":1,
  "G4_U":2,
  "G4_Cu":3,
  "brass":4,
  "StainlessSteel":5
  }
gap_labels = {
  "liquidArgon":0,
  "G4_lXe":1,
  "Scintillator":2,
  "G4_Si":3
  }
#TODO detector geometry hardcoded, should be read from bash run file.
detector_geometry = {"nLayers":40,
  "abso_thick":2, # mm
  "gap_thick":4, # mm
  "YZ_size":120, # cm
}

def _pad(Nparticles, max_particles=50):
    """Pads or truncates the list of particles to ensure a fixed length.
    input: Nparticles=[number_of_points, features]"""
    assert isinstance(Nparticles, np.ndarray), f"input data must be a numpy array"
    assert Nparticles.shape[-1]==4, f"last component of input is expected to be 4 features"
    if Nparticles.shape[0] == max_particles:
       return Nparticles
    elif Nparticles.shape[0] < max_particles: # padd it 
        padding = [[0, 0, 0, 0]]* (max_particles - len(Nparticles))
        stack = np.vstack([Nparticles, padding])
        return stack
    else:
        x = Nparticles[:max_particles]
        return x

def tress_and_keys(file_path):
  try:
      with uproot.open(file_path) as root_file:
          key_names = [key for key in root_file.keys()]
          tree_names = [key for key in root_file.keys() if isinstance(root_file[key], uproot.TTree)]
  except FileNotFoundError:
      print(f"Error: File not found at '{file_path}'")
  except Exception as e:
      print(f"An error occurred: {e}")
  if tree_names and key_names:
    return tree_names, key_names
  else:
    print(f"Error: No trees or keys found in the file '{file_path}")
    return None, None


def get_root_parent(filename):
  """
  Extracts the root parent directory from a given filename.

  Args:
    filename: The path to the file.

  Returns:
    The path to the root parent directory, or None if an error occurs.
  """
  try:
    # Normalize the path to handle different path formats
    normalized_path = os.path.normpath(filename)
    # Get the absolute path to handle relative paths
    absolute_path = os.path.abspath(normalized_path)
    # Extract the directory part of the path
    dirname = os.path.dirname(absolute_path)
    # Return the directory name
    return dirname
  except Exception as e:
    print(f"An error occurred: {e}")
    return None

def read_root_uproot(file_path):
    """
    Walks the TTree and extracts data using uproot.
    Returns a dict with key initialEnergy and value (x, y, z, Edep).
    """
    #max_events = 999 
    particle_idx = file_path.find("genAi")
    parts_forlder_name = file_path[particle_idx:].split("_")
    if len(parts_forlder_name) >= 2:
      particle = parts_forlder_name[1]
    else:
      particle = ""
      
    try:
        with uproot.open(f"{file_path}:StepData") as tree:
            branches_to_read = [
                "InitialEnergy",
                "VolumeGap",
                "position_x",
                "position_y",
                "position_z",
                "EnergyDep"
            ]
            
            # Read all required branches into NumPy arrays
            data = tree.arrays(branches_to_read, library="np")

            # Extract numpy arrays from the dictionary
            initial_energies = data["InitialEnergy"]
            gaps = data["VolumeGap"]
            x_positions = data["position_x"]
            y_positions = data["position_y"]
            z_positions = data["position_z"]
            energy_depositions = data["EnergyDep"]

            # Events dictionary to store the result
            events = {}
            current_energy = 0
            current_event_data = []
            event_count = 0
            
            # Group data by InitialEnergy
            # A new event starts when InitialEnergy is non-zero
            for i in range(len(initial_energies)):
                print(f"Processing simulation {i+1}/{len(initial_energies)}", end='\r')
                # Check for a new event (InitialEnergy > 0)
                if initial_energies[i] > 0:
                    # If this is not the first event, save the previous one
                    if current_energy > 0:
                        events[current_energy] = np.array(current_event_data).T
                        event_count += 1
                    
                    # Start a new event
                    current_energy = initial_energies[i]
                    current_event_data = []

                # Collect data for the current event
                if gaps[i] != 0:
                    current_event_data.append([
                        x_positions[i],
                        y_positions[i],
                        z_positions[i],
                        energy_depositions[i]
                    ])

                # Break the loop if the maximum number of events is reached
                # if event_count >= max_events:
                #     break

            # Save the last event
            if current_energy > 0:
                events[current_energy] = np.array(current_event_data).T
            
            return particle, events
            
    except Exception as e:
        print(f"An error occurred while reading {file_path}: {e}")
        return particle, {}

def process_single_folder(folder_info):
    """
    Processes a single folder to extract and save simulation data.
    """
    folder_path_root, folder, out_path, max_particles = folder_info
    
    # create a data dict for each folder, i.e, each simulation
    data = {
        'showers': [],
        'energies': [],
        'gap_pid': [],
        'pid': [],
    }

    root_file_path = os.path.join(folder_path_root, folder, "generated_calo.root")
    
    # Check if the output file already exists to avoid reprocessing
    output_pkl_path = os.path.join(out_path, f"all_sims_{folder}.pkl")
    if os.path.exists(output_pkl_path):
        print(f"Skipping {folder}: output file already exists.")
        return 0

    trees, keys = tress_and_keys(root_file_path)

    if trees is not None:
        # Extract particle and gap info from folder name
        try:
            sepIdx = [index for index, char in enumerate(folder) if char == '_']
            particle = folder[sepIdx[0]+1:sepIdx[1]]
            if len(sepIdx) > 2 and "G4" in folder[sepIdx[1]+1:sepIdx[2]]:
                gap = folder[sepIdx[3]+1:]
            else:
                gap = folder[sepIdx[2]+1:]
            
            # --- The core processing logic from your original `read_data_g4` function ---
            print(f"Processing file: {root_file_path} with particle: {particle}, gap: {gap}")
            
            # Ensure particle and gap labels exist before proceeding
            if particle not in particle_labels or gap not in gap_labels:
                print(f"Warning: Missing labels for particle '{particle}' or gap '{gap}'. Skipping.")
                return 0

            # Call the new uproot function
            particleFromRoot, events = read_root_uproot(root_file_path)
          
            if particle != particleFromRoot:
                 print(f"Particle mismatch: folder has {particle}, root file has {particleFromRoot}. Skipping.")
                 return 0

            all_showers = []
            all_energies = []
            for energy, feats in events.items():
                feature_padded = _pad(feats, max_particles=max_particles)
                all_showers.append(feature_padded)
                all_energies.append(np.float32(energy))
            
            if not all_showers:
                print(f"No events found in {root_file_path}. Skipping.")
                return 0

            npShowers = np.array(all_showers, dtype=np.float32)
            npEnergies = np.array(all_energies, dtype=np.float32)

            pid = particle_labels[particle]
            gap_pid = gap_labels[gap]

            data['showers'].append(npShowers)
            data['energies'].append(npEnergies)
            data['gap_pid'].append(gap_pid)
            data['pid'].append(pid)

            with open(output_pkl_path, 'wb') as f:
                pickle.dump(data, f)
            
            return 1 # Return 1 for a successful processing
        
        except IndexError:
            print(f"Could not parse folder name: {folder}. Skipping.")
            return 0
    
    return 0 # Return 0 for a failed or skipped processing

def read_data_g4_parallel(folder_path_root, out_path, max_particles=1000):
    """Walks through the root files and processes them in parallel."""
    
    # Get the list of folders
    folder_list = os.listdir(folder_path_root)
    
    # Get the number of available CPU cores
    num_processes = cpu_count()
    print(f"Using {num_processes} processes to speed up data loading.")

    # Prepare a list of tuples with all arguments for the worker function
    tasks = [(folder_path_root, folder, out_path, max_particles) for folder in folder_list]
    
    # Create a multiprocessing pool
    with Pool(processes=num_processes) as pool:
        # Map the worker function to the list of tasks
        results = pool.map(process_single_folder, tasks)
    
    # Count the number of successfully processed files
    non_empty_count = sum(results)
    
    print(f"Total non-empty files processed: {non_empty_count}")

# ... (rest of the script, including __main__ block) ...

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot GEANT4 root output file')
    # ... (existing argparse arguments) ...
    parser.add_argument('--in-file', '-i', action="store", default='/pscratch/sd/c/ccardona/datasets/data_generated_point_clouds/',
                        help='input ROOT file') #requiered=True,
    parser.add_argument('--out-file', '-o', action="store",  default='/pscratch/sd/c/ccardona/datasets/G4_individual_sims_pkl',
                        help='output hf5 data file') #requiered=True,

    args = parser.parse_args()

    # Call the new parallel function
    read_data_g4_parallel(args.in_file, args.out_file)