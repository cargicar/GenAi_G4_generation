# from ROOT import TFile, TCanvas, TH1F, TH2F, gPad
import ROOT
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

# particles=("e-" "mu-" "gamma" "neutron" "proton" "pi+" "kaon0L")
# absorbers=("G4_Pb" "G4_W" "G4_U" "G4_Cu" "brass" "StainlessSteel")
# Gaps liquidArgon, liquidXenon, Scintillator, Silicon
# gaps=("liquidArgon" "G4_lXe" "Scintillator" "G4_Si")
particle_labels = {
    "e-": 0,
    "mu-": 1,
    "gamma": 2,
    "neutron": 3,
    "proton": 4,
    "pi+": 5,
    "kaon0L": 6
}
absorber_labels = {
    "G4_Pb": 0,
    "G4_W": 1,
    "G4_U": 2,
    "G4_Cu": 3,
    "brass": 4,
    "StainlessSteel": 5
}
gap_labels = {
    "liquidArgon": 0,
    "G4_lXe": 1,
    "Scintillator": 2,
    "G4_Si": 3
}
# TODO detector geometry hardcoded, should be read from bash run file.
detector_geometry = {
    "nLayers": 40,
    "abso_thick": 2,  # mm
    "gap_thick": 4,  # mm
    "YZ_size": 120,  # cm
}


def _pad(Nparticles, max_particles=50):
    """Pads or truncates the list of particles to ensure a fixed length.
    input: Nparticles=[number_of_points, features]"""
    assert isinstance(Nparticles, np.ndarray), f"input data must be a numpy array"
    assert Nparticles.shape[-1] == 4, f"last component of input is expected to be 4 features"
    if Nparticles.shape[0] == max_particles:
        return Nparticles
    elif Nparticles.shape[0] < max_particles:  # padd it
        padding = np.zeros((max_particles - len(Nparticles), 4))
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
        return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None
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


def read_root(file_path, val = False):
    """Walks the ttree and extract data. each event is an individual particle.
    Retunrs a dict with key initialEnergy and value (x,y,z,Edep)"""
    # FIXME Put a cap in the max number of simulations cause I was running out of time in perlmutter
    max_events = 999999
    particle_idx = file_path.find("genAi")
    parts_forlder_name = file_path[particle_idx:].split("_")
    if len(parts_forlder_name) >= 2:
        particle = parts_forlder_name[1]
    else:
        particle = ""  # Or handle the error as appropriate if there's no second underscore
    root_file = ROOT.TFile(file_path, "READ")
    # myfile = TFile("build/calogan.root")
    tree = root_file.Get("StepData")

    if not tree:
        print(f"Error: TTree 'StepData' not found in file '{file_path}'")
        exit()

    # Create lists to store the data
    x_positions = []
    y_positions = []
    z_positions = []
    energy_depositions = []
    initial_energies = []
    events = {}  # dict holding event data. keys (initialEnergy: value (x,y,z,Edep)
    # TODO: particle name might go into the h5 file, so will use an h5 per particle as in jetnet
    gaps = []
    # Loop over the entries in the TTree
    n = 0
    m = 0
    for event in tree:
        n += 1
        if m < max_events:
            _Ienergy = event.InitialEnergy
            gap = event.VolumeGap
            gaps.append(gap)
            if _Ienergy != 0:
                initial_energies.append(_Ienergy)
            if len(initial_energies) == 1:
                if gap != 0:
                    x_positions.append(event.position_x)
                    y_positions.append(event.position_y)
                    z_positions.append(event.position_z)
                    energy_depositions.append(event.EnergyDep)
            else:
                m += 1
                Ienergy = initial_energies.pop(0)
                if val:
                    Ienergy = Ienergy+ m*0.01 # use a different key for event dict, even tho all primary energies are the same in val    
                events[Ienergy] = (x_positions, y_positions, z_positions, energy_depositions)
                x_positions = []
                y_positions = []
                z_positions = []
                energy_depositions = []
                print(f"Processed {m} events, total entries {n} from file {file_path}")
        else:
            root_file.Close()
            break
            
    # Close the ROOT file
    root_file.Close()
    return particle, events


def process_single_folder(folder_info):
    """
    Processes a single folder to extract and save simulation data.
    """
    folder_path_root, folder, out_path, max_particles, val = folder_info
    # create a data dict for each folder, i.e, each simulation
    all_showers = []
    all_energies = []
    all_gaps = []

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
    folder_cfg = folder # the file name contating the simulation config values
    if val:
        folder_cfg = folder_path_root[52:] #FIXME position of str genAi harcoded. the file name contating the simulation config values. 
    if trees is not None:
        # Extract particle and gap info from folder name
        try:
            sepIdx = [index for index, char in enumerate(folder_cfg) if char == '_']
            particle = folder_cfg[sepIdx[0] + 1:sepIdx[1]]
            if len(sepIdx) > 2 and "G4" in folder_cfg[sepIdx[1] + 1:sepIdx[2]]:
                gap = folder_cfg[sepIdx[3] + 1:]
            else:
                gap = folder_cfg[sepIdx[2] + 1:]

            # --- The core processing logic from your original `read_data_g4` function ---
            print(f"Processing file: {root_file_path} with particle: {particle}, gap: {gap}")
            # Ensure particle and gap labels exist before proceeding
            if particle not in particle_labels or gap not in gap_labels:
                print(f"Warning: Missing labels for particle '{particle}' or gap '{gap}'. Skipping.")
                return 0

            particleFromRoot, events = read_root(root_file_path, val = val)
            if particle != particleFromRoot:
                print(f"Particle mismatch: folder has {particle}, root file has {particleFromRoot}. Skipping.")
                return 0

            for energy, feats in events.items():
                feature = np.array(feats).T
                feature_padded = _pad(feature, max_particles=max_particles)
                all_showers.append(feature_padded)
                all_energies.append(np.float32(energy))
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

            return 1  # Return 1 for a successful processing

        except IndexError:
            print(f"Could not parse folder name: {folder}. Skipping.")
            return 0

    return 0  # Return 0 for a failed or skipped processing


def read_data_g4(folder_path_root, out_path, max_particles=1000, val = False):
    """Walks through the root files and processes them sequentially."""

    # Get the list of folders
    folder_list = os.listdir(folder_path_root)
    non_empty_count = 0
    # Process each folder one by one
    for folder in tqdm(folder_list, desc="Processing folders"):
        folder_info = (folder_path_root, folder, out_path, max_particles, val)
        result = process_single_folder(folder_info)
        non_empty_count += result

    print(f"\nTotal non-empty files processed: {non_empty_count}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot GEANT4 root output file')
    # ... (existing argparse arguments) ...
    parser.add_argument('--in-file', '-i', action="store",
                        default='/pscratch/sd/c/ccardona/datasets/data_generated_point_clouds/',
                        help='input ROOT file') 
    parser.add_argument('--out-file', '-o', action="store",
                        default='/pscratch/sd/c/ccardona/datasets/G4_individual_sims_pkl',
                        help='output hf5 data file') 
    parser.add_argument("--max_particles",type=int, default=1000, help="Max number of particles to keep per shower")

    parser.add_argument(
        "--val",
        type=bool,
        default=False,
        help="Whether read multi-single simulation for validation histograms",
    )

    args = parser.parse_args()

    # Call the new sequential function
    read_data_g4(args.in_file, args.out_file, val = args.val, max_particles=args.max_particles)