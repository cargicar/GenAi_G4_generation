import os
import pickle
import h5py
import numpy as np
from tqdm import tqdm

def convert_pkl_to_h5(input_dir, output_h5_path):
    """
    Converts a directory of pickle files into a single HDF5 file.

    Each pickle file is expected to contain a dictionary with the keys
    'showers', 'energies', 'pid', and 'gap_pid'. Each file's data is stored
    as a separate group within the HDF5 file.

    Args:
        input_dir (str): Path to the directory containing the pickle files.
        output_h5_path (str): Path where the final HDF5 file will be saved.
    """
    # Get a list of all .pkl files in the directory
    pkl_files = [f for f in os.listdir(input_dir) if f.endswith('.pkl')]
    if not pkl_files:
        print(f"No .pkl files found in '{input_dir}'. Exiting.")
        return

    print(f"Found {len(pkl_files)} files to convert.")
    
    # Use h5py to create a new HDF5 file. The 'w' mode means it will overwrite
    # the file if it already exists.
    with h5py.File(output_h5_path, 'w') as hf:
        # Wrap the loop with tqdm for a progress bar
        for filename in tqdm(pkl_files, desc="Converting files"):
            pkl_path = os.path.join(input_dir, filename)
            
            try:
                # Load the data from the pickle file
                with open(pkl_path, 'rb') as f:
                    data = pickle.load(f)
                
                # Create a group in the HDF5 file for each pickle file.
                # We use the filename without the extension as the group name.
                group_name = filename.replace('.pkl', '')
                group = hf.create_group(group_name)

                # Store the data as datasets within the group
                # Each piece of data gets its own dataset.
                group.create_dataset('showers', data=data['showers'][0])
                group.create_dataset('energies', data=data['energies'][0])
                group.create_dataset('pid', data=data['pid'][0])
                group.create_dataset('gap_pid', data=data['gap_pid'][0])
                
            except (pickle.UnpicklingError, FileNotFoundError, KeyError, IndexError) as e:
                print(f"\nError processing file '{pkl_path}': {e}. Skipping.")
    
    print(f"\nConversion complete. Data saved to '{output_h5_path}'.")

if __name__ == '__main__':
    # Define your input and output paths
    input_directory = '/pscratch/sd/c/ccardona/datasets/G4_individual_sims_pkl'
    output_hdf5_file = '/pscratch/sd/c/ccardona/datasets/all_sims_combined_temp.h5'
    
    # Check if the input directory exists
    if os.path.isdir(input_directory):
        convert_pkl_to_h5(input_directory, output_hdf5_file)
    else:
        print(f"Error: Input directory '{input_directory}' not found.")
