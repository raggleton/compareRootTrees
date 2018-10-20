# compareRootTrees

Handy utility to make comparison plots for every branch in 2 ROOT files that have the same TTree name & structure.
Also summarises which branches are differing.

## Install

```
git clone https://github.com/raggleton/compareRootTrees.git
cd compareRootTrees
pip install -e .
```

## Usage

```
./compareRootTrees.py one.root another.root --outputDir compareOneAnother
```

