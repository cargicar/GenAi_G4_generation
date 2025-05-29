import uproot
import numpy as np
import os
import glob

def get_calogan_root_files(folder_path):
  """
  Returns a list of file names within the specified folder that start with "calogan".

  Args:
    folder_path: The path to the folder to search.

  Returns:
    A list of strings, where each string is the name of a file starting with "calogan".
    Returns an empty list if no such files are found or if the folder path is invalid.
  """
  try:
    # glob to find all files matching the pattern
    pattern = os.path.join(folder_path, "calogan*")
    calogan_files = glob.glob(pattern)
    #breakpoint()
    #return [os.path.basename(f) for f in calogan_files if os.path.isfile(f)]
    return calogan_files
  except OSError:
    print(f"Error: Invalid folder path - {folder_path}")
    return []
  

def save_concatenated_root(output_filename, all_data, tree_name="concatenated_tree"):
    """
    Saves a dictionary of NumPy arrays to a new ROOT file as branches in a TTree.

    Args:
        output_filename (str): The name of the ROOT file to create.
        all_data (dict): A dictionary where keys are branch names and values are
                         NumPy arrays (the concatenated data).
        tree_name (str): The name of the TTree to create in the ROOT file.
    """
    try:
        with uproot.create(output_filename) as f:
            branches = {}
            for branch_name, data in all_data.items():
                # Determine the appropriate ROOT data type based on the NumPy dtype
                if data.dtype == np.int32:
                    dtype = "int32"
                elif data.dtype == np.float32:
                    dtype = "float32"
                elif data.dtype == np.float64:
                    dtype = "float64"
                elif data.dtype == np.bool_:
                    dtype = "bool"
                else:
                    print(f"Warning: Unsupported NumPy dtype {data.dtype} for branch {branch_name}. Attempting to write as float64.")
                    dtype = "float64"
                    data = data.astype(np.float64)  # Attempt to cast
                branches[branch_name] = data

            f[tree_name] = branches
            print(f"Successfully saved concatenated data to '{output_filename}' in tree '{tree_name}'.")

    except Exception as e:
        print(f"An error occurred while saving to ROOT file: {e}")

#folder = "."
#folder = "/global/homes/c/ccardona/G4_MyTestEm3/build"
folder = "/home/carlos/Rnet_local/GENAI_for_particle_phys/My_TestEm3/build"
file_list = calogan_file_list = get_calogan_root_files(folder)

tree_name = "fancy_tree" 

cell_branches = [f"cell_{i}" for i in range(507)]
energy_branch = "TotalEnergy"
cell_branches.append(energy_branch)
branches_to_read = cell_branches

all_data = uproot.concatenate(
    [f"{f}:{tree_name}" for f in file_list],
    branches_to_read,
    library="np"  # Or "pd" for Pandas DataFrame, "ak" for Awkward Array
)

save_concatenated_root("/home/carlos/Rnet_local/GENAI_for_particle_phys/datasets_from_calogan_rep/calogan_interactive_concat_run01.root", all_data, tree_name="fancy_tree")

# Access your data like:
# if library="np":
#     branch1_data = all_data["branch1"]
# elif library="pd":
#     branch1_data = all_data["branch1"].values
# elif library="ak":
#     branch1_data = all_data["branch1"]

