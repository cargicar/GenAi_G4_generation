import uproot

# Replace 'your_file.root' with the actual path to your ROOT file
file_path ='/pscratch/sd/c/ccardona/datasets/data_generated_point_clouds1/genAi_e-_brass_G4_lXe/generated_calo.root'


try:
    with uproot.open(file_path) as root_file:
        key_names = [key for key in root_file.keys()]
        tree_names = [key for key in root_file.keys() if isinstance(root_file[key], uproot.TTree)]
        print(f"key names in the file: {key_names}")
        print("Tree names in the file:")
        for name in tree_names:
            print(f"- {name}")
except FileNotFoundError:
    print(f"Error: File not found at '{file_path}'")
except Exception as e:
    print(f"An error occurred: {e}")
