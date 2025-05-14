import uproot
import numpy as np
import matplotlib.pyplot as plt
import argparse
import os

nbins1z = 3
nbins1y = 96
nbins2y = 12
nbins2z = 12
nbins3z = 12
nbins3y = 6


lvl1 = nbins1z * nbins1y
lvl2 = nbins2z * nbins2y
lvl3 = nbins3z * nbins3y

def get_x(myindex):
    if myindex == 504:
        return 0
    elif myindex == 505:
        return 1
    elif myindex == 506:
        return 2
    elif myindex >= lvl1 + lvl2:
        return 2
    elif myindex >= lvl1:
        return 1
    else:
        return 0

def get_y(myindex, xbin):
    if myindex >= 504:
        return -1
    elif xbin == 0:
        return myindex % nbins1y
    elif xbin == 1:
        return myindex % nbins2y
    else:
        return myindex % nbins3y

def get_z(myindex, ybin, xbin):
    if myindex >= 504:
        return -1
    elif xbin == 0:
        return (myindex - ybin) // nbins1y
    elif xbin == 1:
        return (myindex - lvl1 - ybin) // nbins2y
    else:
        return (myindex - lvl1 - lvl2 - ybin) // nbins3y

def analyze_root_file(infile, outfolder):
        with uproot.open(infile) as myfile:
            if "fancy_tree" not in myfile:
                print(f"Error: Tree 'fancy_tree' not found in '{infile}'")
                return

            mytree = myfile["fancy_tree"]
            num_entries = int(mytree.num_entries)
            
#            x_segmentation_bins = np.array([-240., -150., 197., 240.])
            x_segmentation_bins = np.array([0., 30., 90., 120.])
            x_segmentation_values = np.zeros(len(x_segmentation_bins) - 1)

            sampling1_eta = np.zeros((nbins1z, nbins1y))
            sampling2_eta = np.zeros((nbins2z, nbins2y))
            sampling3_eta = np.zeros((nbins3z, nbins3y))

            fraction_in_thirdlayer = []
            fraction_not_in = []
            middle_lateral_width = []
            front_lateral_width = []
            shower_depth = []
            shower_depth_width = []

            cell_branches = [f"cell_{i}" for i in range(507)]
            energy_branch = "TotalEnergy"

            all_data = mytree.arrays(cell_branches + [energy_branch], library="np")
            total_energies = all_data[energy_branch]
            
            for i in range(min(1000, num_entries)):
                if (i % 100 == 0):
                    print(f" i: {i}, mytree entries: {num_entries}")

                event_cells = {f"cell_{j}": all_data[f"cell_{j}"][i] for j in range(507)}
                total_energy = 0.
                third_layer_energy = 0.
                not_in_energy = 0.
                lateral_depth_sum = 0.
                lateral_depth_sum2 = 0.
                second_layer_weighted_z = 0.
                second_layer_weighted_z2 = 0.
                first_layer_weighted_z = 0.
                first_layer_weighted_z2 = 0.
                front_energy = 0.
                middle_energy = 0.

                for j in range(507):
                    energy = event_cells[f"cell_{j}"]
                    xbin = get_x(j)
                    ybin = get_y(j, xbin)
                    zbin = get_z(j, ybin, xbin)

                    x_segmentation_bin_index = np.digitize(x_segmentation_bins[:-1] + np.diff(x_segmentation_bins) / 2, x_segmentation_bins) - 1
                    if 0 <= xbin < len(x_segmentation_values):
                        x_segmentation_values[xbin] += energy

                    xvalue = x_segmentation_bins[xbin] + (x_segmentation_bins[xbin + 1] - x_segmentation_bins[xbin]) / 2
                    zvalue = 0.
                    yvalue = 0.
                    total_energy += energy
                    lateral_depth_sum += xbin * energy
                    lateral_depth_sum2 += xbin * xbin * energy

                    if xbin == 2:
                        third_layer_energy += energy

                    if zbin < 0 or ybin < 0:
                        not_in_energy += energy

                    if xbin == 0 and 0 <= zbin < nbins1z and 0 <= ybin < nbins1y:
                        sampling1_eta[zbin, ybin] += energy
                        # z= (-5, 5)
                        zvalue = (np.linspace(-5, 5, nbins1z + 1)[:-1] + np.diff(np.linspace(-5, 5, nbins1z + 1)) / 2)[zbin]
                        # zvalue = (np.linspace(-240, 240, nbins1z + 1)[:-1] + np.diff(np.linspace(-240, 240, nbins1z + 1)) / 2)[zbin]
                        yvalue = (np.linspace(-20, 20, nbins1y + 1)[:-1] + np.diff(np.linspace(-20, 20, nbins1y + 1)) / 2)[ybin]

                        # yvalue = (np.linspace(-240, 240, nbins1y + 1)[:-1] + np.diff(np.linspace(-240, 240, nbins1y + 1)) / 2)[ybin]
                    elif xbin == 1 and 0 <= zbin < nbins2z and 0 <= ybin < nbins2y:
                        sampling2_eta[zbin, ybin] += energy
                        zvalue = (np.linspace(-5, 5, nbins2z + 1)[:-1] + np.diff(np.linspace(-5, 5, nbins2z + 1)) / 2)[zbin]
                        yvalue = (np.linspace(-20, 20, nbins2y + 1)[:-1] + np.diff(np.linspace(-20, 20, nbins2y + 1)) / 2)[ybin]
                    elif xbin == 2 and 0 <= zbin < nbins3z and 0 <= ybin < nbins3y:
                        sampling3_eta[zbin, ybin] += energy
                        zvalue = (np.linspace(-5, 5, nbins3z + 1)[:-1] + np.diff(np.linspace(-5, 5, nbins3z + 1)) / 2)[zbin]
                        yvalue = (np.linspace(-20, 20, nbins3y + 1)[:-1] + np.diff(np.linspace(-20, 20, nbins3y + 1)) / 2)[ybin]

                    if xbin == 0:
                        first_layer_weighted_z += zvalue * energy
                        first_layer_weighted_z2 += zvalue * zvalue * energy
                        front_energy += energy
                    elif xbin == 1:
                        second_layer_weighted_z += zvalue * energy
                        second_layer_weighted_z2 += zvalue * zvalue * energy
                        middle_energy += energy

                fraction_in_thirdlayer.append(third_layer_energy / total_energy if total_energy > 0 else 0)
                fraction_not_in.append(not_in_energy / total_energy if total_energy > 0 else 0)
                shower_depth.append(lateral_depth_sum / total_energy if total_energy > 0 else 0)

                if middle_energy > 0:
                    middle_lateral_width.append(((second_layer_weighted_z2 / middle_energy) - (second_layer_weighted_z / middle_energy)**2)**0.5)
                if front_energy > 0:
                    front_lateral_width.append((first_layer_weighted_z2 / front_energy - (first_layer_weighted_z / front_energy)**2)**0.5)

                shower_depth_width.append((lateral_depth_sum2 / total_energy - (lateral_depth_sum / total_energy)**2)**0.5 if total_energy > 0 else 0)

            # Plotting
            
            plt.figure(figsize=(8, 6))
            plt.bar(x_segmentation_bins[:-1] + np.diff(x_segmentation_bins) / 2, x_segmentation_values, width=np.diff(x_segmentation_bins))
            plt.xlabel("X")
            plt.ylabel("Energy")
            plt.title("Total X Profile")
            file_name = "tot_xprofil_uproot.pdf"
            save_path = os.path.join(outfolder, file_name)
            plt.savefig(save_path)
            plt.close()

            plt.figure(figsize=(8, 6))
            plt.imshow(sampling1_eta.T, origin='lower', aspect='auto')#, extent=[-5, 5, -5, 5])
            plt.colorbar(label="Energy")
            plt.xlabel("Z")
            plt.ylabel("Y")
            plt.title("Total ZY Layer 1")
            #plt.savefig("plots/tot_zy_layer1_uproot.pdf")
            file_name = "tot_zy_layer1_uproot.pdf"
            save_path = os.path.join(outfolder, file_name)
            plt.savefig(save_path)
            plt.close()

            plt.figure(figsize=(8, 6))
            plt.imshow(sampling2_eta.T, origin='lower', aspect='auto')#, extent=[-5, 5, -5, 5])
            plt.colorbar(label="Energy")
            plt.xlabel("Z")
            plt.ylabel("Y")
            plt.title("Total ZY Layer 2")
#            plt.savefig("plots/tot_zy_layer2_uproot.pdf")
            file_name = "tot_zy_layer2_uproot.pdf"
            save_path = os.path.join(outfolder, file_name)
            plt.savefig(save_path)
            plt.close()

            plt.figure(figsize=(8, 6))
            plt.imshow(sampling3_eta.T, origin='lower', aspect='auto', extent=[-5, 5, -5, 5], norm='log')
            breakpoint()
            plt.colorbar(label="Log(Energy)")
            plt.xlabel("Z")
            plt.ylabel("Y")
            #plt.title("Total ZY Layer 3 (Log Scale)")
            file_name = "Total ZY Layer 3 (Log Scale)"
            save_path = os.path.join(outfolder, file_name)
            plt.savefig(save_path)
            plt.close()

            plt.figure(figsize=(8, 6))
            plt.hist(fraction_in_thirdlayer, bins=np.linspace(0, 0.01, 101))
            plt.xlabel("Fraction in Third Layer")
            plt.ylabel("Counts")
            plt.title("Fraction of Energy in Third Layer")
            #plt.savefig("plots/Fraction_in_thirdlayer_uproot.pdf")
            file_name = "Fraction_in_thirdlayer_uproot.pdf"
            save_path = os.path.join(outfolder, file_name)
            plt.savefig(save_path)
            plt.close()

            plt.figure(figsize=(8, 6))
            plt.hist(fraction_not_in, bins=np.linspace(0, 0.01, 101))
            plt.xlabel("Fraction Not In Active Area")
            plt.ylabel("Counts")
            plt.title("Fraction of Energy Not in Active Area")
            # plt.savefig("plots/Fraction_not_in_uproot.pdf")
            file_name = "Fraction_not_in_uproot.pdf"
            save_path = os.path.join(outfolder, file_name)
            plt.savefig(save_path)
            plt.close()

            plt.figure(figsize=(8, 6))
            plt.hist(shower_depth, bins=np.linspace(0, 1.5, 101))
            plt.xlabel("Shower Depth")
            plt.ylabel("Counts")
            plt.title("Shower Depth")
            #plt.savefig("plots/Shower_Depth_uproot.pdf")
            file_name = "Shower_Depth_uproot.pdf"
            save_path = os.path.join(outfolder, file_name)
            plt.savefig(save_path)
            plt.close()

            plt.figure(figsize=(8, 6))
            plt.hist(middle_lateral_width, bins=np.linspace(0, 100, 101))
            plt.xlabel("Middle Lateral Width")
            plt.ylabel("Counts")
            plt.title("Middle Lateral Width")
            #plt.savefig("plots/Middle_lateral_width_uproot.pdf")
            file_name = "Middle_lateral_width_uproot.pdf"
            save_path = os.path.join(outfolder, file_name)
            plt.savefig(save_path)
            plt.close()

            plt.figure(figsize=(8, 6))
            plt.hist(front_lateral_width, bins=np.linspace(0, 100, 101))
            plt.xlabel("Front Lateral Width")
            plt.ylabel("Counts")
            plt.title("Front Lateral Width")
            #plt.savefig("plots/Front_lateral_width_uproot.pdf")
            file_name = "Front_lateral_width_uproot.pdf"
            save_path = os.path.join(outfolder, file_name)
            plt.savefig(save_path)
            plt.close()

            plt.figure(figsize=(8, 6))
            plt.hist(shower_depth_width, bins=np.linspace(0, 1.0, 101))
            plt.xlabel("Shower Depth Width")
            plt.ylabel("Counts")
            plt.title("Shower Depth Width")
            #plt.savefig("plots/Shower_Depth_width_uproot.pdf")
            file_name = "Shower_Depth_width_uproot.pdf"
            save_path = os.path.join(outfolder, file_name)
            plt.savefig(save_path)
            plt.close()

    # except Exception as e:
    #     print(f"An error occurred: {e}")

if __name__ == '__main__':
    #python helpers_py/plot_1D_features_X_to_Z.py --infile build/calogan.root --outfolder ~/Rnet_local/GENAI_for_particle_phys/datasets_from_calogan_rep/plots

    parser = argparse.ArgumentParser(description='Analyze GEANT4 ROOT output using uproot and plot results.')
    parser.add_argument('--infile', help='Input ROOT file name')
    parser.add_argument('--outfolder', help='Output folder name ')
    args = parser.parse_args()
    analyze_root_file(infile=args.infile, outfolder=args.outfolder)
