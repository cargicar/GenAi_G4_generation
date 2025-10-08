#include <TFile.h>
#include <TTree.h>
#include <TBranch.h>
#include <iostream>
#include <vector>
#include <map>
#include <cmath>
#include <numeric>
#include <TString.h>

// A structure to hold the data for a single point (step)
struct StepData {
    Float_t position_x;
    Float_t position_y;
    Float_t position_z;
    Float_t EnergyDep;
};

// Map to store the final grouped data: InitialEnergy -> vector of Steps
std::map<Float_t, std::vector<StepData>> events_map;

void read_root_cpp(const std::string& file_path, std::string& particle_name) {
    // 1. Open the ROOT file
    TFile* file = TFile::Open(file_path.c_str());
    if (!file || file->IsZombie()) {
        std::cerr << "Error opening file: " << file_path << std::endl;
        return;
    }

    // 2. Get the TTree
    TTree* tree = dynamic_cast<TTree*>(file->Get("StepData"));
    if (!tree) {
        std::cerr << "Error: TTree 'StepData' not found." << std::endl;
        file->Close();
        return;
    }

    // 3. Set up variables to hold branch data
    Float_t initial_energy_val = 0;
    Int_t volume_gap_val = 0;
    Float_t x_pos_val = 0;
    Float_t y_pos_val = 0;
    Float_t z_pos_val = 0;
    Float_t energy_dep_val = 0;

    // 4. Link branches to local variables
    tree->SetBranchAddress("InitialEnergy", &initial_energy_val);
    tree->SetBranchAddress("VolumeGap", &volume_gap_val);
    tree->SetBranchAddress("position_x", &x_pos_val);
    tree->SetBranchAddress("position_y", &y_pos_val);
    tree->SetBranchAddress("position_z", &z_pos_val);
    tree->SetBranchAddress("EnergyDep", &energy_dep_val);
    
    // (Optional: Extract particle name from file path here)
    // particle_name = ...

    // 5. Loop through all entries and group the data
    Float_t current_energy = 0;
    Long64_t nentries = tree->GetEntries();
    
    for (Long64_t i = 0; i < nentries; ++i) {
        tree->GetEntry(i);

        // A new event starts when InitialEnergy is non-zero
        if (initial_energy_val > 0) {
            current_energy = initial_energy_val;
        }

        // Only collect data if it is within a Gap (VolumeGap != 0)
        if (volume_gap_val != 0 && current_energy > 0) {
            StepData step = {x_pos_val, y_pos_val, z_pos_val, energy_dep_val};
            events_map[current_energy].push_back(step);
        }
        
        // Progress display (like your Python script)
        if (i % 100000 == 0) {
            std::cout << "Processing simulation " << i << "/" << nentries << "\r" << std::flush;
        }
    }

    // Clean up
    file->Close();
}

int main() {
    std::string particle_name;
    read_root_cpp("path_to_your_file.root", particle_name);

    // Example: Print out the number of events for each initial energy
    for (const auto& [energy, steps] : events_map) {
        std::cout << "Initial Energy: " << energy << " MeV, Number of Steps: " << steps.size() << std::endl;
    }

    return 0;
}