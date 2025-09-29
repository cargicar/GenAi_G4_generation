import os
import h5py
import uproot
import numpy as np
import argparse
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

# This is the full list of labels from your original script
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

def _pad(Nparticles, max_particles=50):
    """Pads or truncates the list of particles to ensure a fixed length."""
    assert isinstance(Nparticles, np.ndarray), f"input data must be a numpy array"
    assert Nparticles.shape[-1]==4, f"last component of input is expected to be 4 features"
    if Nparticles.shape[0] == max_particles:
        return Nparticles
    elif Nparticles.shape[0] < max_particles:
        padding = np.zeros((max_particles - len(Nparticles), 4))
        stack = np.vstack([Nparticles, padding])
        return stack
    else:
        x = Nparticles[:max_particles]
        return x

def tress_and_keys(file_path):
    """Checks for trees and keys in a ROOT file."""
    try:
        with uproot.open(file_path) as root_file:
            key_names = [key for key in root_file.keys()]
            tree_names = [key for key in root_file.keys() if isinstance(root_file[key], uproot.TTree)]
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None
    if tree_names and key_names:
        return tree_names, key_names
    else:
        print(f"Error: No trees or keys found in the file '{file_path}'")
        return None, None

def read_root(file_path):
    """Walks the ttree and extracts event data. Returns a dict."""
    particle_idx = file_path.find("genAi")
    parts_forlder_name = file_path[particle_idx:].split("_")
    if len(parts_forlder_name) >= 2:
        particle = parts_forlder_name[1]
    else:
        particle = ""
    try:
        tree = uproot.open(f"{file_path}:StepData")
    except KeyError:
        print(f"Error: TTree 'StepData' not found in file '{file_path}'")
        return None, None
    except uproot.exceptions.KeyInFileError:
        print(f"Error: TTree 'StepData' not found in file '{file_path}'")
        return None, None
    except Exception as e:
        print(f"An error occurred while opening file '{file_path}': {e}")
        return None, None

    try:
        data = tree.arrays(["InitialEnergy", "VolumeGap", "position_x", "position_y", "position_z", "EnergyDep"], library="np")
        
        initial_energies = data["InitialEnergy"]
        event_indices = np.where(initial_energies != 0)[0]
        
        events_dict = {}
        for i, start_idx in enumerate(event_indices):
            end_idx = event_indices[i+1] if i+1 < len(event_indices) else len(data["InitialEnergy"])
            
            x = data["position_x"][start_idx:end_idx]
            y = data["position_y"][start_idx:end_idx]
            z = data["position_z"][start_idx:end_idx]
            edep = data["EnergyDep"][start_idx:end_idx]
            
            feats = np.stack([x, y, z, edep], axis=1)
            
            initial_energy = initial_energies[start_idx]
            events_dict[initial_energy] = feats
            
    except Exception as e:
        print(f"An error occurred while reading data from file '{file_path}': {e}")
        return particle, {}
        
    return particle, events_dict

def process_and_save_to_h5(task_info):
    """
    Worker function to process a single folder and save to an individual HDF5 file.
    
    Args:
        task_info (tuple): Contains folder path, output path, and max particles.
    Returns:
        int: 1 if successful, 0 otherwise.
    """
    folder_path_root, folder, out_path, max_particles = task_info
    
    root_file_path = os.path.join(folder_path_root, folder, "generated_calo.root")
    
    if not os.path.exists(root_file_path):
        return 0

    output_h5_path = os.path.join(out_path, f"all_sims_{folder}.h5")
    if os.path.exists(output_h5_path):
        return 0

    trees, keys = tress_and_keys(root_file_path)

    if trees is not None:
        try:
            sepIdx = [index for index, char in enumerate(folder) if char == '_']
            particle = folder[sepIdx[0]+1:sepIdx[1]]
            gap = folder[sepIdx[-1]+1:]
            
            if particle not in particle_labels or gap not in gap_labels:
                return 0

            particle_from_root, events = read_root(root_file_path)
            if particle_from_root != particle:
                return 0

            all_showers = []
            all_energies = []
            for energy, feats in events.items():
                feature_padded = _pad(feats, max_particles=max_particles)
                all_showers.append(feature_padded)
                all_energies.append(np.float32(energy))
            
            if not all_showers:
                return 0

            np_showers = np.array(all_showers, dtype=np.float32)
            np_energies = np.array(all_energies, dtype=np.float32)
            num_events = len(np_showers)
            
            pid = np.full((num_events,), particle_labels[particle], dtype=np.int32)
            gap_pid = np.full((num_events,), gap_labels[gap], dtype=np.int32)

            with h5py.File(output_h5_path, 'w') as hf:
                hf.create_dataset('showers', data=np_showers)
                hf.create_dataset('energies', data=np_energies)
                hf.create_dataset('pid', data=pid)
                hf.create_dataset('gap_pid', data=gap_pid)

            return 1 # Success
            
        except IndexError:
            return 0
    
    return 0 # Failed or skipped

def read_data_g4_parallel(folder_path_root, out_path, max_particles=1000):
    """Walks through the root files and processes them in parallel."""
    
    folder_list = os.listdir(folder_path_root)
    total_files = len(folder_list)
    
    num_processes = cpu_count()
    print(f"Using {num_processes} processes to speed up data loading.")

    # Create a list of tuples with all arguments for the worker function
    tasks = [(folder_path_root, folder, out_path, max_particles) for folder in folder_list]
    
    with Pool(processes=num_processes) as pool:
        # Pass the function and the list of tasks directly
        results = list(tqdm(pool.imap(
            process_and_save_to_h5, tasks), total=total_files, desc="Converting files"))
    
    processed_count = sum(results)
    
    print(f"\nTotal non-empty files processed: {processed_count}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert GEANT4 root output to HDF5')
    parser.add_argument('--in-file', '-i', action="store", 
                        default='/pscratch/sd/c/ccardona/datasets/data_generated_point_clouds/',
                        help='input ROOT file directory')
    parser.add_argument('--out-dir', '-o', action="store", 
                        default='/pscratch/sd/c/ccardona/datasets/G4_individual_sims_h5',
                        help='output directory for the HDF5 file')

    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    read_data_g4_parallel(args.in_file, args.out_dir)
