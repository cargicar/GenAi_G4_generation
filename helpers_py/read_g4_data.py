#from ROOT import TFile,  TCanvas, TH1F, TH2F, gPad
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
    """Pads or truncates the list of particles to ensure a fixed length."""
    if len(Nparticles) > max_particles:
        print(f"Warning: Number of particles {len(Nparticles)} exceeds max_particles {max_particles}. Not Truncating.")
        return None
        #return Nparticles[:max_particles]
    else:
        # Pad with zeros
        padding = [[0, 0, 0, 0]]* (max_particles - len(Nparticles))
        stack = np.vstack([Nparticles, padding])
        return stack

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

   
def read_data_g4(folder_path_root,labels=None, histogram = False):
    """Walks through the root files in the given folder path, extracts data from each file
    Returns a dict with key initialEnergy and value (x,y,z,Edep)"""
    train = {
        #'data':[],# (N,30,4)=(Number of jets, max number of particles, particle_features[eta,phi,pt,mask])
        'showers':[], # (N=primary_particles, max_number of particles in shower = 1000,feat= individual particle features)
        # e.g (N = 1000, sd = 1000, feat= (x,y,z,E))
        'layers':[], #(N=primary_particles, layer_features= [nLayers, thickness, material])
        # e.g (N = 1000, feat=[40, 4 mm ,one_hot_encoded_material])
        'pid':[], # (N,7)=(Number of primaries, one hot encoded particles type)
        # eg: (N = 1000, one hot encoded particle type [gamma,electron,muon,pi+,pi-,pi0,kaon,p,neutron])
        'energies':[], # (N,)=(Inital energies of primaries,)
        'gap_pid':[], #(N,4) one hot encoded gap material
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
    if histogram:
      nparts_all_e = []
      nparts_all_mu = []
      nparts_all_gamma = []
      nparts_all_neutron = []
      nparts_all_proton = [] 
      nparts_all_pi = []
      nparts_all_kaon = [] 
      nparts_all = {}

    all_showers=[]
    all_energies = []
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
        
        for energy, feats in events.items():
          #breakpoint()
          # convert feats to numpy array
          if len(feats[0])> 1000:
            print(f"Skipping event from {particle} with initial energy {energy} due to more than 1000 particles.")
            continue
          feature = np.array(feats).T # shape (Nparticles, 4) with
          feature_padded = _pad(feature, max_particles=1000) # Pad to 1000 particles
          all_showers.append(feature_padded)
          all_energies.append(energy)
          #breakpoint()
        npShowers = np.array(all_showers, dtype=object)
        npEnergies = np.array(all_energies, dtype=object)
        breakpoint()
        pid = to_categorical(particle_labels[particle]*np.ones(shape=(npEnergies.shape[0],1)), num_classes=7)
        gap_pid = to_categorical(gap_labels[gap]*np.ones(shape=(npEnergies.shape[0],1)), num_classes=4)
        train['showers'].append(npShowers)
        train['energies'].append(npEnergies)
        train['pid'].append(pid)
        train['pid'].append(gap_pid)

        if histogram:
          nparticles_per_energy = [(key,len(events[key][0])) for key in events] # list of tuples (initialEnergy, number of particles)
          #nparticles_per_energy.sort() # sort by initial energy
          if particle == "e-":
             nparts_all_e.extend(nparticles_per_energy)
          elif particle == "mu-":
             nparts_all_mu.extend(nparticles_per_energy)
          elif particle == "gamma":
             nparts_all_gamma.extend(nparticles_per_energy)
          elif particle == "neutron":
             nparts_all_neutron.extend(nparticles_per_energy)
          elif particle == "proton":
             nparts_all_proton.extend(nparticles_per_energy)
          elif particle == "pi+":
              nparts_all_pi.extend(nparticles_per_energy)
          elif particle == "kaon0L":
              nparts_all_kaon.extend(nparticles_per_energy)

    if histogram: 

      nparts_all["e-"] = nparts_all_e
      nparts_all["mu-"] = nparts_all_mu 
      nparts_all["gamma"] = nparts_all_gamma
      nparts_all["neutron"] = nparts_all_neutron
      nparts_all["proton"] = nparts_all_proton
      nparts_all["pi+"] = nparts_all_pi
      nparts_all["kaon0L"] = nparts_all_kaon

      with open('nparts_all_dict.pkl', 'wb') as f:
        pickle.dump(nparts_all, f)
      
        
    print(f"Total non-empty files processed: {NonEmpty}")
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot GEANT4 root output file')

    parser.add_argument('--in-file', '-i', action="store", required=True,
                        help='input ROOT file')
    #parser.add_argument('--particle', '-p' action="store", required=True, help='primary particle type (e.g., e-, pi+, etc.)')
    # parser.add_argument('--out-folder', '-o', action="store", required=True, help='output folder')
    # parser.add_argument('--tree', '-t', action="store", required=True,help='input tree for the ROOT file')

    args = parser.parse_args()

    #plots(args.in_file)
    read_data_g4(args.in_file, histogram=True)
