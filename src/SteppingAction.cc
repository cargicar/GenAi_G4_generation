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
// 

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#include "SteppingAction.hh"
#include "RunData.hh" //Calogan
#include "DetectorConstruction.hh"
#include "EventAction.hh"

#include "G4Step.hh"
#include "G4RunManager.hh"

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

SteppingAction::SteppingAction()                                         
{
  detector = (DetectorConstruction*)
             G4RunManager::GetRunManager()->GetUserDetectorConstruction();
  eventaction = (EventAction*)
                G4RunManager::GetRunManager()->GetUserEventAction();               
  // G4UserSteppingAction()//Calogan
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

SteppingAction::~SteppingAction()
{ }

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......


//....oooOO0OOooo........oooOO0OOoooCalorGan Grid block. Begin .oooOO0OOooo........oooOO0OOooo......

// Parameters based on exo0.mac. Notice that they are very different from CaloGan dataset
//8 layers, Gap size 2cm, Abs size 1cm, YZ size 10cm
// x len= 8*(2+1)=24, x=(-12,12), y=(-5,5), z = (-5,5)
int SteppingAction::WhichXBin(double xpos){
 
  //  G4cout << "###### Xpos ###########" << xpos << G4endl;
  // Lets split the calorimeter in 3 equal spaced sections in x-dim
  //  x=(-12,12), zsegmentation = [-12, -8, 8, 12]
  if (xpos < -8.) return 0;
  else if (xpos < 0.) return 1;
  else return 2;

}

int SteppingAction::WhichZYbin(double zpos, double ypos, int xbin){
  int zbin = -1;
  int ybin = -1;
  // number of bins in first section
  int nbins1z = 3;
  int nbins1y = 96;
  // number of bins in second section
  int nbins2z = 12;
  int nbins2y = 12;
  // number of bins in third section
  int nbins3z = 12;
  int nbins3y = 6;
  int nbinsz[]={nbins1z,nbins2z,nbins3z};
  int nbinsy[]={nbins1y,nbins2y,nbins3y};
  //Given (xpos, ypos, zbin), give corresponding 2D bin in zbin (xbin, ybin)
  
  for (int i=1; i<=nbinsz[xbin]; i++){
    // z = (-5,5)
    if ((zpos < -5 + i*10/nbinsz[xbin]) && (zpos > -5)){
      zbin = i - 1;
      //G4cout << "###### Zpos ###########" << zpos << G4endl;
      //G4cout << "###### Ypos ###########" << ypos << G4endl; 
      break;
    }
  }
  // y=(-5,5),
  for (int i=1; i<=nbinsy[xbin]; i++){
    if ((ypos < -5 +i*10/nbinsy[xbin]) && (ypos > -5)){
      ybin = i - 1;
      break;
    }
  }


  int lvl1 = nbins1z * nbins1y;
  int lvl2 = nbins2z * nbins2y;
  int lvl3 = nbins3z * nbins3y;



  if ((zbin == -1) || (ybin == -1)) { // Outside the bins?
    return lvl1 + lvl2 + lvl3 + xbin;
  }

  if (xbin == 0) { 
    return zbin * nbins1y + ybin;
  } 
  else if (xbin == 1) {
    return lvl1 + (zbin * nbins2y + ybin);
  }
  else {
    return (lvl1 + lvl2) + (zbin * nbins3y + ybin);
  }



  // return zbin*1e4 + xbin*1e2 + ybin;
  //sampling1_eta = TH2F("","",3,-240.,240.,480/5,-240.,240.)
  //sampling2_eta = TH2F("","",480/40,-240.,240.,480/40,-240.,240.)
  //sampling3_eta = TH2F("","",480/40,-240.,240.,480/80,-240.,240.)
}

//....oooOO0OOooo........oooOO0OOooo.Calogan grid block. end.oooOO0OOooo........oooOO0OOooo......


void SteppingAction::UserSteppingAction(const G4Step* aStep)
{
  // get volume of the current step
  G4VPhysicalVolume* volume 
  = aStep->GetPreStepPoint()->GetTouchableHandle()->GetVolume();
  
  // collect energy and track length step by step
  G4double edep = aStep->GetTotalEnergyDeposit();

  //....oooOO0OOooo........oooOO0OOooo.Calogan block. Begin oooOO0OOooo........oooOO0OOooo......
  G4StepPoint* point1 = aStep->GetPreStepPoint();
  G4StepPoint* point2 = aStep->GetPostStepPoint();
  G4ThreeVector pos1 = point1->GetPosition();
  G4ThreeVector pos2 = point2->GetPosition();

  //G4cout <<  "sqr " << pos1.z() << " " << pos2.z() << " " << pos1.x() << " " << pos2.x() << " " << edep << " " << step->GetTrack()->GetDefinition()->GetParticleName() << " " << step->GetTrack()->GetKineticEnergy() << G4endl;
      
  //G4cout << "sqr " << pos1.x() << " " << pos1.y() << " " << pos1.z() << " " << edep << G4endl;
  int mybin = WhichZYbin(pos1.z(),pos1.y(),WhichXBin(pos1.x()));
  // int mybin = 0;
  //G4cout << "zbin " << WhichZBin(pos1.z()) << " which bin " << mybin << " " << mybin%100 << std::endl;
  
  RunData* runData = static_cast<RunData*>(G4RunManager::GetRunManager()->GetNonConstCurrentRun());

  // runData->Add(mybin, edep, stepLength); 

  runData->Add(mybin, edep); //Maybde this should be replicated as last two lines below?

   //....oooOO0OOooo........oooOO0OOooo.Calogan block. end oooOO0OOooo........oooOO0OOooo......
  G4double stepl = 0.;
  if (aStep->GetTrack()->GetDefinition()->GetPDGCharge() != 0.)
    stepl = aStep->GetStepLength();
      
  if (volume == detector->GetAbsorber()) eventaction->AddAbs(edep,stepl);
  if (volume == detector->GetGap())      eventaction->AddGap(edep,stepl);
  
  //example of saving random number seed of this event, under condition
  //// if (condition) G4RunManager::GetRunManager()->rndmSaveThisEvent(); 
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
