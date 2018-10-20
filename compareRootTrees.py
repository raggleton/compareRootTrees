#!/usr/bin/env python

"""
Produce comparison plots for all variable in all branches on two ROOT files
with same tree name. Each branch will be in its own subdirectory.
Histograms with differing # entries or means will have "DIFF_" prepended to their filename.

Returns exit code 0 if all branches are identical, 1 otherwise.
"""


from __future__ import print_function
import os
import ROOT
import sys
import argparse
from collections import OrderedDict
from array import array
import numpy as np


ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(1)
ROOT.TH1.SetDefaultSumw2()
# ROOT.gErrorIgnoreLevel = ROOT.kError
ROOT.gErrorIgnoreLevel = ROOT.kBreak  # to turn off all Error in <TCanvas::Range> etc


def do_comparison_plot(T1, T2, name, output_name, print_warning=True):
    """
    Make comparison plot for a branch name from 2 trees,
    and return whether they are different

    Note that in order to get the same binning and range for both trees,
    we make a temporary set of histograms since ROOT does some nice auto-ranging
    for us. Then we use that info to construct the final histograms.

    Parameters
    ----------
    T1 : ROOT.TTree
        Description
    T2 : ROOT.TTree
        Description
    name : str
        Branch name to get from both trees
    output_name : str
        Output plot filename
    print_warning : bool, optional
        If True, print when hists have differing means and/or # entries

    Returns
    -------
    bool
        True if the histograms are different
    """
    c = ROOT.TCanvas("c"+name, "", 800, 600)

    h1name = "h1_%s" % name
    h1name_tmp = h1name + "_tmp"
    T1.Draw(name + ">>" + h1name_tmp, "", "goff")
    # do it this way to let ROOT decide upon the axis range
    h1_tmp = ROOT.TH1F(ROOT.gROOT.FindObject(h1name_tmp))
    # Figure out range from ROOT hist info
    ax1 = h1_tmp.GetXaxis()
    xmin1, xmax1 = ax1.GetXmin(), ax1.GetXmax()

    h2name = "h2_%s" % name
    h2name_tmp = h2name + "_tmp"
    T2.Draw(name + ">>" + h2name_tmp, "", "goff")
    h2_tmp = ROOT.TH1F(ROOT.gROOT.FindObject(h2name_tmp))
    ax2 = h2_tmp.GetXaxis()
    xmin2, xmax2 = ax2.GetXmin(), ax2.GetXmax()

    xmin = min(xmin1, xmin2)
    xmax = max(xmax1, xmax2)

    # Check if our version of ROOT has TRatioPlot
    do_ratioplot = True
    try:
        ROOT.TRatioPlot
    except AttributeError:
        do_ratioplot = False

    # Now remake histograms, this time according to our binning
    # Yes this is kinda unnecessary, but have issues accessing branch data
    # directy in a generic manner
    nbins = 50
    h1 = ROOT.TH1F(h1name, ";%s;N" % name, nbins, xmin, xmax)
    T1.Draw(name + ">>" + h1name)
    h1_colour = ROOT.kBlack
    h1.SetLineColor(h1_colour)
    h1.SetLineWidth(2)
    h1.Draw("HISTE")
    c.Update()
    # Get stat boxes for repositioning
    # Draw hist by itself to get it, then plot them together afterwards
    stats1 = h1.GetListOfFunctions().FindObject("stats").Clone("stats1")
    stats1.SetY1NDC(0.72);
    stats1.SetX1NDC(0.825);
    stats1.SetX2NDC(0.99);
    stats1.SetY2NDC(0.9);
    stats1.SetTextColor(h1_colour);
    h1.SetStats(0)

    h2 = ROOT.TH1F(h2name, ";%s;N" % name, nbins, xmin, xmax)
    T2.Draw(name + ">>" + h2name)
    h2_colour = ROOT.kRed
    h2.SetLineColor(h2_colour)
    h2.SetLineStyle(2)
    h2.SetLineWidth(0)
    h2.SetMarkerColor(h2_colour)
    h2.SetMarkerStyle(33)
    h2.SetMarkerSize(1.5)
    h2.Draw("HISTE")
    c.Update()
    stats2 = h2.GetListOfFunctions().FindObject("stats").Clone("stats2")
    stats2.SetY1NDC(0.52);
    stats2.SetX1NDC(0.825);
    stats2.SetX2NDC(0.99);
    stats2.SetY2NDC(0.7);
    stats2.SetTextColor(h2_colour);
    h2.SetStats(0)

    if h1.GetEntries() == 0 and h2.GetEntries() == 0:
        return

    # Do a simple check to see if hists differ
    is_diff = False
    if print_warning and (h1.GetEntries() > 0 or h2.GetEntries() > 0):
        if h1.GetEntries() != h2.GetEntries():
            is_diff = True
            print(name, " has differing entries", h1.GetEntries(), "vs", h2.GetEntries())
        if h1.GetMean() != h2.GetMean():
            is_diff = True
            print(name, " has differing means", h1.GetMean(), "vs", h2.GetMean())

    if is_diff:
        basename = os.path.basename(output_name)
        output_name = output_name.replace(basename, "DIFF_"+basename)

    # Do final plotting
    if do_ratioplot:
        rp = ROOT.TRatioPlot(h1, h2)
        rp.SetGridlines(array('d', [1.]), 1)
        rp.SetRightMargin(0.18)
        rp.SetUpTopMargin(0.1)
        rp.Draw("grid")
        lower_gr = rp.GetLowerRefGraph()
        lower_gr.SetMinimum(0.8)
        lower_gr.SetMaximum(1.2)
        rp.GetLowerRefYaxis().SetTitle("h1 / h2")
        c.Update()
    else:
        hst = ROOT.THStack("hst"+name, ";"+name+";N")
        hst.Add(h1)
        hst.Add(h2)
        hst.Draw("NOSTACK HISTE")

    c.cd()
    stats1.Draw()
    stats2.Draw()
    c.Modified()
    c.SaveAs(output_name)

    return is_diff


def check_tobj(tobj):
    if tobj == None or tobj.IsZombie():
        raise IOError("Cannot access %s" % tobj.GetName())


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filename1", help="Reference ROOT filename")
    parser.add_argument("filename2", help="Comparison ROOT filename")
    default_dir = "ComparisonPlots"
    parser.add_argument("--outputDir", help="Output directory for plots, defaults to %s" % default_dir, default=default_dir)
    default_tree = "AnalysisTree"
    parser.add_argument("--treeName", help="Name of TTree, defaults to %s" % default_tree, default=default_tree)
    default_fmt = "pdf"
    parser.add_argument("--outputFmt", help="Output format for plots, defaults to %s" % default_fmt, default=default_fmt)
    parser.add_argument("-v", "--verbose", help="More verbose output", action='store_true')
    args = parser.parse_args()

    f1 = ROOT.TFile.Open(args.filename1)
    f2 = ROOT.TFile.Open(args.filename2)

    check_tobj(f1)
    check_tobj(f2)

    T1 = f1.Get(args.treeName)
    T2 = f2.Get(args.treeName)

    check_tobj(T1)
    check_tobj(T2)

    br_list1 = T1.GetListOfBranches()
    # br_list2 = T2.GetListOfBranches()

    results = OrderedDict()

    print("Plots produced in", args.outputDir)
    ROOT.gSystem.mkdir(args.outputDir)
    for i in range(br_list1.GetEntries()):
        branch1 = br_list1.At(i)
        branch_name = branch1.GetName()
        if args.verbose:
            print("BRANCH", i, ":", branch_name)
        branch2 = T2.GetBranch(branch_name)
        if branch2 is None:
            print("WARNING Tree2 doesn't have branch ", branch_name)
            continue

        ROOT.gSystem.mkdir(os.path.join(args.outputDir, branch_name))

        leaves1 = branch1.GetListOfBranches()
        leaves2 = branch2.GetListOfBranches()

        if leaves1.GetEntries() == 0:
            # means its a leaf not a branch
            output_name = os.path.join(args.outputDir, branch_name, branch_name+"_compare.%s" % args.outputFmt)
            is_diff = do_comparison_plot(T1, T2, branch_name, output_name)
            results[branch_name] = is_diff
        else:
            for j in range(leaves1.GetEntries()):
                leaf1 = leaves1.At(j)
                leaf2 = leaves2.At(j)

                leaf_type = leaf1.GetTypeName()
                if leaf_type.startswith("map"):
                    # don't know how to print these yet
                    continue

                var_name = leaf1.GetName()
                if var_name != leaf2.GetName():
                    print("WARNING diff leaf names", var_name, "vs", leaf2.GetName())

                # print(var_name)
                parts = var_name.replace(branch_name+".", "").replace(".", "_")
                output_name = os.path.join(args.outputDir, branch_name, parts + "_compare.%s" % args.outputFmt)
                is_diff = do_comparison_plot(T1, T2, var_name, output_name, args.verbose)
                results[var_name] = is_diff

    f1.Close()
    f2.Close()

    # Print results
    if any(results.values()):
        if args.verbose:
            max_len = max([len(x) for x in results.keys()])
            print("*" * max_len)
            print("Differing vars:")
            print("*" * max_len)
            for name, result in results.items():
                if result:
                    print(name)
            print("*" * max_len)
        else:
            print("Not all distributions same")
        sys.exit(1)
    else:
        print("All distributions same")
        sys.exit(0)
