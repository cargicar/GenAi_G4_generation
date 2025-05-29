#from ROOT import TFile,  TCanvas, TH1F, TH2F, gPad
import ROOT
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import argparse
import os

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

def plots(file_path):
    
    root_file = ROOT.TFile(file_path, "READ")
    #myfile = TFile("build/calogan.root")
    parent = get_root_parent(file_path)
    plot_folder = os.path.join(parent, f"plots")
    # Get the TTree
    tree = root_file.Get("StepData")

    if not tree:
        print(f"Error: TTree 'StepData' not found in file '{file_path}'")
        exit()

    # Create lists to store the data
    x_positions = []
    y_positions = []
    z_positions = []
    energy_depositions= []
    

    # Loop over the entries in the TTree
    for event in tree:
        x_positions.append(event.position_x)
        y_positions.append(event.position_y)
        z_positions.append(event.position_z)
        energy_depositions.append(event.EnergyDep)

    # Convert lists to NumPy arrays for easier plotting
    x_np = np.array(x_positions)
    y_np = np.array(y_positions)
    z_np = np.array(z_positions)
    energy_np = np.array(energy_depositions)

    # --- Plotting the 3D trajectory ---
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    #ax.scatter(x_np, y_np, z_np, s=10, alpha=0.5)  # Adjust 's' for marker size, 'alpha' for transparency
    scatter = ax.scatter(x_np, y_np, z_np, c=energy_np, cmap='viridis', s=10, alpha=0.7)

    ax.set_xlabel('X Position')
    ax.set_ylabel('Y Position')
    ax.set_zlabel('Z Position')
    ax.set_title('Particle Trajectory with Edep')
    ax.view_init(elev=30, azim=45)
    # Add a colorbar
    cbar = fig.colorbar(scatter, ax=ax, label='Energy Deposition', shrink=0.8) # Added 'ax=ax'
    plt.grid(True)
    #plt.savefig(plot_folder)
    plt.savefig(f"plots/trajectory_plot_with edep.png", dpi=300, bbox_inches='tight')

    # Close the ROOT file
    root_file.Close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot GEANT4 root output file')

    parser.add_argument('--in-file', '-i', action="store", required=True,
                        help='input ROOT file')
    # parser.add_argument('--out-folder', '-o', action="store", required=True, help='output folder')
    # parser.add_argument('--tree', '-t', action="store", required=True,help='input tree for the ROOT file')

    args = parser.parse_args()

    plots(args.in_file)
