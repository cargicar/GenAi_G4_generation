import pickle
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

def npart_histogram(Nparticles, title=f"nparts_histogram.png"):
    #nparts = [len(events[key][0]) for key in events]
    #breakpoint()
    #plt.hist(Nparticles, bins=20)
    
    MIN, MAX = 30, 3000
    plt.hist(Nparticles, bins=np.logspace(np.log10(MIN),np.log10(MAX), 20))
    plt.xscale('log')
    plt.xlabel("Number of particles (log scale)")
    plt.ylabel("Number of events")
    plt.title(title[:-4])
    plt.savefig(title)
    plt.close()

with open('nparts_all_dict.pkl', 'rb') as f:
    nparts_all = pickle.load(f)
all_simulations_nparticles = []
for particle, nparts in nparts_all.items():
    try:
        energies, Nparticles = zip(*nparts)  # Unzip the list of tuples
    except ValueError:
        print(f"Skipping particle {particle} due to ValueError in unpacking.")
        continue
    all_simulations_nparticles.extend(Nparticles)
    
npart_histogram(all_simulations_nparticles, title= f"Nparticles_in_all_showers Max : {max(all_simulations_nparticles)}. Min: {min(all_simulations_nparticles)}.png")
#histo_Ebins(energies,Nparticles, title= f"nparts_histogram_{particle}.png")

    
    