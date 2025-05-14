from ROOT import TFile,  TCanvas, TH1F, TH2F, gPad
import numpy as np
import matplotlib.pyplot as plt
import argparse
import os

nbins1x = 3
nbins1y = 96
nbins2y = 12
nbins2x = 12
nbins3x = 12
nbins3y = 6


lvl1 = nbins1x * nbins1y
lvl2 = nbins2x * nbins2y
lvl3 = nbins3x * nbins3y

def get_x(myindez):
    if myindez == 504:
        return 0
    elif myindez == 505:
        return 1
    elif myindez == 506:
        return 2
    elif (myindez >= lvl1 + lvl2):
        return 2
    elif (myindez >= lvl1):
        return 1
    else:
        return 0
    pass

def get_y(myindez,xbin):
    if (myindez >=504):
        return -1
    elif (xbin==0):
        return myindez % nbins1y
    elif (xbin==1):
        return myindez % nbins2y
    else:
        return myindez % nbins3y
    pass

def get_z(myindez,ybin,xbin):
    if (myindez >=504):
        return -1
    elif (xbin==0):
        return (myindez - ybin)/nbins1y
    elif (xbin==1):
        return (myindez - lvl1 - ybin)/nbins2y
    else:
        return (myindez - lvl1 - lvl2 - ybin)/nbins3y
    pass

myfile = TFile("build/calogan.root")
#pion-10GeV-1k.root
#electrons-10GeV-5k.root 
#photons-10GeV-1k.root
mytree = myfile.Get("fancy_tree")

c = TCanvas("a","a",500,500)
xsegmentation = TH1F("","",3,np.array([-240.,-150.,197.,240.]))
sampling1_eta = TH2F("","",3,-240.,240.,96,-240.,240.) # 480/5 = 96
sampling2_eta = TH2F("","",12,-240.,240.,12,-240.,240.) # 480/40 = 12
sampling3_eta = TH2F("","",12,-240.,240., 6,-240.,240.)  # 480/80 = 6

Fraction_in_thirdlayer = TH1F("","",100,0,0.01)
Fraction_not_in = TH1F("","",100,0,0.01)
Middle_lateral_width = TH1F("","",100,0,100)
Front_lateral_width = TH1F("","",100,0,100)
Shower_Depth = TH1F("","",100,0,1.5)
Shower_Depth_width = TH1F("","",100,0,1.0)

for i in range(min(1000,mytree.GetEntries())):
    mytree.GetEntry(i)
    if (i%100==0):
        print(f"i: {i}, mytree.GetEntries {mytree.GetEntries()}")
        pass
    y = "energy"
    exec("%s = %s" % (y,"mytree.cell_0"))
    total_energy = 0.
    third_layer = 0.
    not_in = 0.
    lateral_depth = 0.
    lateral_depth2 = 0.
    second_layer_z = 0.
    second_layer_Z2 = 0.
    first_layer_z = 0.
    first_layer_Z2 = 0.
    front_energy = 0.
    middle_energy = 0.
    for j in range(507):
        exec("%s = %s" % (y,"mytree.cell_"+str(j)))
        zbin = int(get_z(j,get_y(j,get_x(j)),get_x(j)))
        ybin = int(get_y(j,get_x(j)))
        xbin = int(get_x(j))
        xsegmentation.Fill(xsegmentation.GetXaxis().GetBinCenter(xbin+1),energy)
        #breakpoint()
        xvalue = xsegmentation.GetXaxis().GetBinCenter(xbin+1)
        yvalue = 0.;
        zvalue = 0.;
        total_energy+=energy
        lateral_depth+=xbin*energy
        lateral_depth2+=xbin*xbin*energy
        if (xbin==2):
            third_layer+=energy
            pass
        if (zbin < 0 or ybin < 0):
            not_in+=energy
            pass
        if (xbin==0):
            sampling1_eta.Fill(sampling1_eta.GetXaxis().GetBinCenter(zbin+1),sampling1_eta.GetYaxis().GetBinCenter(ybin+1),energy)
            zvalue = sampling1_eta.GetXaxis().GetBinCenter(zbin+1)
            yvalue = sampling1_eta.GetYaxis().GetBinCenter(ybin+1)
        elif (xbin==1):
            sampling2_eta.Fill(sampling2_eta.GetXaxis().GetBinCenter(zbin+1),sampling2_eta.GetYaxis().GetBinCenter(ybin+1),energy)
            zvalue = sampling2_eta.GetXaxis().GetBinCenter(zbin+1)
            yvalue = sampling2_eta.GetYaxis().GetBinCenter(ybin+1)
        else:
            sampling3_eta.Fill(sampling3_eta.GetXaxis().GetBinCenter(zbin+1),sampling3_eta.GetYaxis().GetBinCenter(ybin+1),energy)
            zvalue = sampling3_eta.GetXaxis().GetBinCenter(zbin+1)
            yvalue = sampling3_eta.GetYaxis().GetBinCenter(ybin+1)
            pass
        if (xbin==0):
            first_layer_z += zvalue*energy
            first_layer_Z2 += zvalue*zvalue*energy
            front_energy+=energy
        elif (xbin==1):
            second_layer_z += zvalue*energy
            second_layer_Z2 += zvalue*zvalue*energy
            middle_energy+=energy
            pass
        pass
    Fraction_in_thirdlayer.Fill(third_layer/total_energy)
    Fraction_not_in.Fill(not_in/total_energy)
    Shower_Depth.Fill(lateral_depth/total_energy)
    if (middle_energy > 0):
        Middle_lateral_width.Fill(((second_layer_Z2/middle_energy) - (second_layer_z/middle_energy)**2)**0.5)
        pass
    if (front_energy > 0):
        Front_lateral_width.Fill((first_layer_Z2/front_energy - (first_layer_z/front_energy)**2)**0.5)
        pass
    Shower_Depth_width.Fill((lateral_depth2/total_energy - (lateral_depth/total_energy)**2)**0.5)
    pass
xsegmentation.Draw()
c.Print("plots/tot_xprofil.pdf")
sampling1_eta.Draw("colx")
c.Print("plots/tot_zy_layer1.pdf")
sampling2_eta.Draw("colx")
c.Print("plots/tot_zy_layer2.pdf")
gPad.SetLogz()
sampling3_eta.Draw("colx")
for i in range(1,sampling3_eta.GetNbinsX()+1):
    for j in range(1,sampling3_eta.GetNbinsY()+1):
        #breakpoint()
        print(f" (i,j): {i,j} ,sampling3_eta.GetBinContent(i,j): {sampling3_eta.GetBinContent(i,j)}")
        pass
    pass
c.Print("plots/tot_zy_layer3.pdf")
gPad.SetLogx(0)
Fraction_in_thirdlayer.Draw()
c.Print("plots/Fraction_in_thirdlayer.pdf")
Fraction_not_in.Draw()
c.Print("plots/Fraction_not_in.pdf")
Shower_Depth.Draw()
c.Print("plots/Shower_Depth.pdf")
Middle_lateral_width.Draw()
c.Print("plots/Middle_lateral_width.pdf")
Front_lateral_width.Draw()
c.Print("plots/Front_lateral_width.pdf")
Shower_Depth_width.Draw()
c.Print("plots/Shower_Depth_width.pdf")
