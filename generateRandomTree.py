#!/usr/bin/env python
# coding: utf-8

"""Generate a TTree with a set of branches filled with random floats"""


import ROOT
from array import array
import sys
import argparse

ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(1)


def make_random_ttree(tree_name, n_entries, n_branches, random_seed):
    """Generate a TTree filled with random floats
    
    Parameters
    ----------
    tree_name : str
        Name for TTree
    n_entries : int
        Number of entries to fill in the tree
    n_branches : int
        Number of branches in the tree
    random_seed : int
        Random number seed. 0 for random seed
    
    Returns
    -------
    ROOT.TTree
        Filled tree
    """
    tree = ROOT.TTree(tree_name, "my dummy tree")
    arrays = [array('f', [0.])]*n_branches
    # setup branches to map to arrays
    for i, arr in enumerate(arrays):
        tree.Branch("branch%d" % i, arr, "branch%d/F" % i)
    # fill branches
    rando = ROOT.TRandom()
    rando.SetSeed(random_seed)  # 0 for random seed
    for i in range(n_entries):
        for arr in arrays:
            arr[0] = rando.Rndm()
        tree.Fill()
    return tree


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nbranches", help="Number of branches in tree", default=10, type=int)
    parser.add_argument("--nentries", help="Number of entries in tree", default=100, type=int)
    parser.add_argument("--output", help="Output ROOT filename", default="tree.root")
    parser.add_argument("--treeName", help="Name of TTree", default="tree")
    parser.add_argument("--randomSeed", help="Seed for random number generator", default=0)
    args = parser.parse_args()

    tree = make_random_ttree(
        tree_name=args.treeName,
        n_entries=args.nentries,
        n_branches=args.nbranches,
        random_seed=args.randomSeed
    )
    outf = ROOT.TFile(args.output, "RECREATE")
    tree.Write()
    outf.Close()

