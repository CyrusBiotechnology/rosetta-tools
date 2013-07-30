#! /usr/bin/env python
import argparse
import tempfile
import subprocess
import shutil
from renumber_pdb_in_place import renumber_pdb
from parse_options import get_ints
from rosetta_exe import rosetta_exe

parser = argparse.ArgumentParser(description='Run rna_helix to build a helix')
parser.add_argument('-seq', required=True, help='Sequence of the helix, in the format: ggaa uucc', nargs=2 )
parser.add_argument('-resnum', nargs=2, help='Renumber the residues with inputformat: 13-16 30-33')
parser.add_argument('-o', default='helix.pdb', help='Filename of output pdb')
parser.add_argument('-weights', default='', help='Weights file defining score function')
parser.add_argument('-finish_weights', default='', help='Weights file defining a finisher score function')
parser.add_argument('-silent', default='', help='silent file output')
parser.add_argument('-dump', action='store_true', default=False, help='dump intermediate pdbs')
args = parser.parse_args()


#Build the helix
temp = tempfile.NamedTemporaryFile(delete=False)
cmdline  = rosetta_exe('rna_helix')
cmdline += (' -rna::corrected_geo  '+
            '-score:rna_torsion_potential RNA11_based_new ' +
            '-geom_sol_correct_acceptor_base -chemical::enlarge_H_lj ' +
            '-analytic_etable_evaluation 0 ')
cmdline += '-o %s ' % temp.name
cmdline += '-seq '
for i in args.seq:    cmdline += i + ' '
if len( args.weights ) > 0:        cmdline += '-score:weights %s ' % args.weights
if len( args.finish_weights ) > 0: cmdline += '-finish_weights %s ' % args.finish_weights
if len( args.silent ) > 0: cmdline += '-out:file:silent %s ' % args.silent
if args.dump: cmdline += '-dump '

print 'Rosetta cmdline:', cmdline
subprocess.check_call(cmdline.split())

output_file = args.o
# slightly weird

#Renumber the pdb
if args.resnum is None:
    temp.close()
    shutil.move(temp.name, output_file)
else: #renumbering
    new_numbers = []
    for i in args.resnum:
        get_ints(i, new_numbers)
    renumber_pdb([temp.name], new_numbers)
    temp.close()
    shutil.move(temp.name, output_file)

