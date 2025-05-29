import numpy as np
import h5py

# with h5py.File("./t0.hdf5", "r") as hdf:
#     ls = list(hdf.keys())
#     print(f"List of folders in this file {ls}")
#     for data_name in ls:
#         data = hdf.get(data_name)
#         dataset = np.array(data)
#         print(f"dataset {data_name}, shape {dataset}")

#f = h5py.File
import h5py
import numpy as np
import argparse

def read_hdf5_file(infile):
    """
    Reads data from an HDF5 file created by the ROOT conversion script.

    Args:
        infile (str): Path to the input HDF5 file.
    """
    try:
        with h5py.File(infile, 'r') as h5:
            print(f"Opened HDF5 file: {infile}")

            layer_data = {}
            i = 0
            while f'layer_{i}' in h5:
                layer_data[f'layer_{i}'] = h5[f'layer_{i}'][:]
                print(f"  Read layer: layer_{i} with shape {layer_data[f'layer_{i}'].shape}")
                i += 1

            overflow_data = h5['overflow'][:]
            print(f"  Read overflow data with shape {overflow_data.shape}")

            energy_data = h5['energy'][:]
            print(f"  Read energy data with shape {energy_data.shape}")

            return layer_data, overflow_data, energy_data

    except Exception as e:
        print(f"An error occurred while reading the HDF5 file: {e}")
        return None, None, None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read HDF5 files created from GEANT4 ROOT output.')

    parser.add_argument('--in-file', '-i', action="store", required=True,
                        help='input HDF5 file')

    args = parser.parse_args()

    layer_data, overflow_data, energy_data = read_hdf5_file(infile=args.in_file)

    if layer_data:
        for layer_name, data in layer_data.items():
            print(f"\n--- {layer_name} ---")
            #print(f"First 5 entries:\n{data[:5]}")
            print(f"Data shape: {data.shape}")

        print(f"\n--- Overflow Data ---")
        #print(f"First 5 entries:\n{overflow_data[:100]}")
        print(f"Data shape: {overflow_data.shape}")

        print(f"\n--- Energy Data ---")
        #print(f"First 5 entries:\n{energy_data[:5]}")
        print(f"Data shape: {energy_data.shape}")