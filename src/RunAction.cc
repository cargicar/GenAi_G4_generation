//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
//
// $Id$
//
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#include "RunAction.hh"
#include "RunData.hh"
#include "Analysis.hh"

#include "G4SystemOfUnits.hh"
#include <sstream>

#include "G4Run.hh"
#include "G4RunManager.hh"
#include "G4UnitsTable.hh"

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

//RunAction::RunAction()
//{}

//RunAction::~RunAction()
//{}

//....oooOO0OOooo........oooOO0OOooo.calogan block. begin oooOO0OOooo........oooOO0OOooo......
RunAction::RunAction()
 : G4UserRunAction()
{ 
  // set printing event number per each event
  G4RunManager::GetRunManager()->SetPrintProgress(1);     

  // Create analysis manager
  // The choice of analysis technology is done via selectin of a namespace
  // in Analysis.hh
  G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
  G4cout << "Using " << analysisManager->GetType() << G4endl;

  // Create directories 
  //analysisManager->SetHistoDirectoryName("histograms");
  //analysisManager->SetNtupleDirectoryName("ntuple");
  analysisManager->SetVerboseLevel(1);
  analysisManager->SetFirstHistoId(1);

  // Book histograms, ntuple
  //
  
  // Creating histograms
  // analysisManager->CreateH1("1","Edep in absorber", 100, 0., 800*MeV);
  // analysisManager->CreateH1("2","Edep in gap", 100, 0., 100*MeV);
  // analysisManager->CreateH1("3","trackL in absorber", 100, 0., 1*m);
  // analysisManager->CreateH1("4","trackL in gap", 100, 0., 50*cm);

  // Creating ntuple
  //

  char const* val = getenv("GAN_TREENAME"); 
  std::string fname = (val == NULL ? std::string("fancy_tree") : std::string(val));


  analysisManager->CreateNtuple(fname.c_str(), "Edep and TrackL");

  int total_bins = 504 + 3;  // 3 overflow bins for the three calo layers

  for (int i = 0; i < total_bins; ++i) {

    std::stringstream out;
    out << i;
    analysisManager->CreateNtupleDColumn("cell_" + out.str());
  }
  analysisManager->CreateNtupleDColumn("TotalEnergy");
  
  // analysisManager->CreateNtupleDColumn("Eabs");
  // analysisManager->CreateNtupleDColumn("Egap");
  // analysisManager->CreateNtupleDColumn("Labs");
  // analysisManager->CreateNtupleDColumn("Lgap");



  analysisManager->FinishNtuple();
}


RunAction::~RunAction()
{
  delete G4AnalysisManager::Instance();  
}

G4Run* RunAction::GenerateRun()
{
  return (new RunData);
}

//....oooOO0OOooo........oooOO0OOooo.calogan block. end oooOO0OOooo........oooOO0OOooo......

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......


void RunAction::BeginOfRunAction(const G4Run* aRun)
{ 
  G4cout << "### Run " << aRun->GetRunID() << " start." << G4endl;

  //inform the runManager to save random number seed
  G4RunManager::GetRunManager()->SetRandomNumberStore(true);
    
  //initialize cumulative quantities
  //
  sumEAbs = sum2EAbs =sumEGap = sum2EGap = 0.;
  sumLAbs = sum2LAbs =sumLGap = sum2LGap = 0.;

  //....oooOO0OOooo........oooOO0OOooo.calogan block. begin oooOO0OOooo........oooOO0OOooo......
    // Get analysis manager
  G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();

  // Open an output file
  //

  char const* val = getenv("GAN_FNAME"); 
  //std::string fname = (val == NULL ? std::string("plz_work_kthxbai") : std::string(val));
  std::string fname = (val == NULL ? std::string("calogan.root") : std::string(val));


  G4String fileName = fname.c_str();
  analysisManager->OpenFile(fileName);
  //....oooOO0OOooo........oooOO0OOooo.calogan block. end oooOO0OOooo........oooOO0OOooo......

}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void RunAction::fillPerEvent(G4double EAbs, G4double EGap,
                                  G4double LAbs, G4double LGap)
{
  //accumulate statistic
  //
  sumEAbs += EAbs;  sum2EAbs += EAbs*EAbs;
  sumEGap += EGap;  sum2EGap += EGap*EGap;
  
  sumLAbs += LAbs;  sum2LAbs += LAbs*LAbs;
  sumLGap += LGap;  sum2LGap += LGap*LGap;  
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void RunAction::EndOfRunAction(const G4Run* aRun)
{
  G4int NbOfEvents = aRun->GetNumberOfEvent();
  if (NbOfEvents == 0) return;
  
  //compute statistics: mean and rms
  //
  sumEAbs /= NbOfEvents; sum2EAbs /= NbOfEvents;
  G4double rmsEAbs = sum2EAbs - sumEAbs*sumEAbs;
  if (rmsEAbs >0.) rmsEAbs = std::sqrt(rmsEAbs); else rmsEAbs = 0.;
  
  sumEGap /= NbOfEvents; sum2EGap /= NbOfEvents;
  G4double rmsEGap = sum2EGap - sumEGap*sumEGap;
  if (rmsEGap >0.) rmsEGap = std::sqrt(rmsEGap); else rmsEGap = 0.;
  
  sumLAbs /= NbOfEvents; sum2LAbs /= NbOfEvents;
  G4double rmsLAbs = sum2LAbs - sumLAbs*sumLAbs;
  if (rmsLAbs >0.) rmsLAbs = std::sqrt(rmsLAbs); else rmsLAbs = 0.;
  
  sumLGap /= NbOfEvents; sum2LGap /= NbOfEvents;
  G4double rmsLGap = sum2LGap - sumLGap*sumLGap;
  if (rmsLGap >0.) rmsLGap = std::sqrt(rmsLGap); else rmsLGap = 0.;

  G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
  //print
  //
  G4cout
     << "\n--------------------End of Run------------------------------\n"
     << "\n mean Energy in Absorber : " << G4BestUnit(sumEAbs,"Energy")
     << " +- "                          << G4BestUnit(rmsEAbs,"Energy")  
     << "\n mean Energy in Gap      : " << G4BestUnit(sumEGap,"Energy")
     << " +- "                          << G4BestUnit(rmsEGap,"Energy")
     << G4endl;
     
  G4cout
     << "\n mean trackLength in Absorber : " << G4BestUnit(sumLAbs,"Length")
     << " +- "                               << G4BestUnit(rmsLAbs,"Length")  
     << "\n mean trackLength in Gap      : " << G4BestUnit(sumLGap,"Length")
     << " +- "                               << G4BestUnit(rmsLGap,"Length")
     << "\n------------------------------------------------------------\n"
     << G4endl;
  analysisManager->Write();
  analysisManager->CloseFile();

}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
