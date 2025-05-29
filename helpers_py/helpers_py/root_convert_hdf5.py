import uproot
import h5py
import numpy as np
import os
import argparse

#### simple convert
def root_to_hdf5(input_root_file, output_hdf5_file, tree_name=None):
    """
    Converts a ROOT TTree to an HDF5 file.

    Args:
        input_root_file (str): Path to the input .root file.
        output_hdf5_file (str): Path to the output .hdf5 file.
        tree_name (str): Name of the TTree to convert.
    """
    try:
        with uproot.open(input_root_file) as root_file:
            if tree_name not in root_file:
                print(f"Error: TTree '{tree_name}' not found in '{input_root_file}'")
                return

            tree = root_file[tree_name]
            branches = tree.keys()
            data = tree.arrays(branches)

            with h5py.File(output_hdf5_file, 'w') as hdf5_file:
                for branch in branches:
                    # Convert ROOT's awkward arrays to NumPy arrays for h5py
                    if isinstance(data[branch], np.ndarray):
                        hdf5_file.create_dataset(branch, data=data[branch])
                    else:
                        # Handle cases where the branch might be a list of arrays
                        numpy_data = np.array(data[branch].tolist())
                        hdf5_file.create_dataset(branch, data=numpy_data)

        print(f"Successfully converted '{input_root_file}:{tree_name}' to '{output_hdf5_file}'")

    except Exception as e:
        print(f"An error occurred: {e}")

#### converting following original convert.py. I needed to rewrite this file cause rootpy.io
##### wasn't working for me, so i needed to use uproot instead

### run as python convert.py --in-file plz_work_kthxbai.root --out-file test.h5 --tree fancy_tree
LAYER_SPECS = [(3, 96), (12, 12), (12, 6)]
LAYER_DIV = np.cumsum(list(map(np.prod, LAYER_SPECS))).tolist()
LAYER_DIV = list(zip([0] + LAYER_DIV, LAYER_DIV))
OVERFLOW_BINS = 3

def write_out_file(infile, outfile, tree_name=None):
    try:
        with uproot.open(infile) as f:
            if tree_name not in f:
                raise ValueError(f"Tree '{tree_name}' not found in ROOT file '{infile}'")
            T = f[tree_name]
            branches = T.keys()
            cells = sorted([b for b in branches if b.startswith('cell')])

            assert len(cells) == sum(map(np.prod, LAYER_SPECS)) + OVERFLOW_BINS

            X_arrays = T.arrays(cells, library="pd")
            X = X_arrays.values

            E_arrays = T.arrays(['TotalEnergy'], library="pd")
            E = E_arrays['TotalEnergy'].values.ravel()

            with h5py.File(outfile, 'w') as h5:
                for layer, (sh, (l, u)) in enumerate(zip(LAYER_SPECS, LAYER_DIV)):
                    h5[f'layer_{layer}'] = X[:, l:u].reshape((-1,) + sh)

                h5['overflow'] = X[:, -OVERFLOW_BINS:]
                h5['energy'] = E.reshape(-1, 1)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert GEANT4 output files into ML-able HDF5 files using uproot')

    parser.add_argument('--in-file', '-i', action="store", required=True,
                        help='input ROOT file')
    parser.add_argument('--out-file', '-o', action="store", required=True,
                        help='output HDF5 file')
    parser.add_argument('--tree', '-t', action="store", required=True,
                        help='input tree for the ROOT file')

    args = parser.parse_args()

    write_out_file(infile=args.in_file, outfile=args.out_file, tree_name=args.tree)
