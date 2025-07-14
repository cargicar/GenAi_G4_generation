#from ROOT import TFile,  TCanvas, TH1F, TH2F, gPad
import ROOT
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import argparse
import os
import h5py as h5
import uproot

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

def preprocess(folder_path_root,labels=None):
    """Walks through the root files in the given folder path, extracts data from each file
    Returns a dict with key initialEnergy and value (x,y,z,Edep)"""
    train = {
        'data':[],# (N,30,4)=(Number of jets, max number of particles, particle_features[eta,phi,pt,mask])
        # calo analog: (N=total number of particles,max=max_number of particles per layer,feat= individual particle features)
        # e.g (N = 10, max = 50, feat= (x,y,z,E))
        'jet':[], # (N,4)=(Number of jets, jet_features[pt,eta,phi,m])
        # calo analog: (N=total number of layers, feat= individual layer features)
        # e.g (N = 10, feat=(x_pos, thickness, material))
        'pid':[], # (N,5)=(Number of jets, one hot encoded jet type [g,q,t,w,z])
        # calo analog: (Number of layers, one hot encoded particle type [gamma,electron,muon,pi+,pi-,pi0,kaon,p,neutron])
    }
    test = {
        'data':[],
        'jet':[],
        'pid':[],
    }
    val = {
        'data':[],
        'jet':[],
        'pid':[],
    }
    folder_list = os.listdir(folder_path_root)
    # file is tipically something like genAi_e-_brass_G4_lXe
    NonEmpty=0
    simulations = []
    for folder in folder_list:
      root_file_path = os.path.join(folder_path_root, folder, "generated_calo.root")
      trees, keys = tress_and_keys(root_file_path)
      if trees is not None:
        NonEmpty+=1
        sepIdx = [index for index, char in enumerate(folder) if char == '_']
        particle = folder[sepIdx[0]+1:sepIdx[1]] # Extract particle name from folder name
        if "G4" in folder[sepIdx[1]+1:sepIdx[2]]:
          absorber = folder[sepIdx[1]+1:sepIdx[3]]
          gap= folder[sepIdx[3]+1:]
        else:
          absorber = folder[sepIdx[1]+1:sepIdx[2]] # Extract material name from folder name
          gap= folder[sepIdx[2]+1:] # Extract gap name from folder name
        print(f"Processing file: {root_file_path} with particle: {particle}, absorber: {absorber}, gap: {gap}")
        particleFromRoot, events = read_root(root_file_path)
        assert particle == particleFromRoot, f"Particle mismatch: folder has {particle}, root file has {particleFromRoot}"
        breakpoint() 
        #simulations.append((initial_energies, particle, absorber, gap, xs, ys, zs, es))
        
    print(f"Total non-empty files processed: {NonEmpty}")
    
        
    
def read_root(file_path):
    """Walks the ttree and extract data. each event is an individual particle. 
    Retunrs a dict with key initialEnergy and value (x,y,z,Edep)"""
    particle_idx = file_path.find("genAi")
    parts_forlder_name = file_path[particle_idx:].split("_")
    if len(parts_forlder_name) >= 2:
      particle = parts_forlder_name[1]
    else:
      particle = "" # Or handle the error as appropriate if there's no second underscore
    root_file = ROOT.TFile(file_path, "READ")
    #myfile = TFile("build/calogan.root")
    tree = root_file.Get("StepData")

    if not tree:
        print(f"Error: TTree 'StepData' not found in file '{file_path}'")
        exit()

    # Create lists to store the data 
    x_positions = []
    y_positions = []
    z_positions = []
    energy_depositions= []
    initial_energies = []
    events = {} # dict holding event data. keys (initialEnergy: value (x,y,z,Edep)
    #TODO: particle name might  go into the h5 file, so will use an h5 per particle as in jetnet
    gaps = []
    # Loop over the entries in the TTree
    n = 0
    for event in tree:
        n+=1
        _Ienergy = event.InitialEnergy
        gap = event.VolumeGap
        gaps.append(gap)
        if _Ienergy !=0:
          initial_energies.append(_Ienergy)
        if len(initial_energies) == 1:
          if gap != 0:
              x_positions.append(event.position_x)
              y_positions.append(event.position_y)
              z_positions.append(event.position_z)
              energy_depositions.append(event.EnergyDep)
        else:
          Ienergy = initial_energies.pop(0)
          events[Ienergy]=(x_positions, y_positions, z_positions, energy_depositions)
          x_positions = []
          y_positions = []
          z_positions = []
          energy_depositions= []
            
  # Close the ROOT file
    root_file.Close()
    return particle, events

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot GEANT4 root output file')

    parser.add_argument('--in-file', '-i', action="store", required=True,
                        help='input ROOT file')
    #parser.add_argument('--particle', '-p' action="store", required=True, help='primary particle type (e.g., e-, pi+, etc.)')
    # parser.add_argument('--out-folder', '-o', action="store", required=True, help='output folder')
    # parser.add_argument('--tree', '-t', action="store", required=True,help='input tree for the ROOT file')

    args = parser.parse_args()

    #plots(args.in_file)
    preprocess(args.in_file)
