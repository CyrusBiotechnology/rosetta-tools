#!/usr/bin/env python

'''run_iwyu.py - a script to run the clang tool "include-what-you-use" over
the Rosetta codebase, and adjust the output for the vagarities of the Rosetta coding style.

Run from the Rosetta/main/source directory and provide the script with files or directories,
and the .cc .hh and .fwd.hh files therein will be processed.

Because of order dependancy in removing headers, this script will only create an *.riwyuf
file in the same location, listing what should be done to the file.
'''

from __future__ import print_function

import sys, os
import subprocess
import codecs
from fnmatch import fnmatch
import json

from optparse import OptionParser

########## Internal config #############################

#These are the clang commandline flags for debug mode, stripped of warning issues
commandline_flags_linux = '''-c -std=c++11 -isystem external/boost_submod/ -isystem external/ -isystem external/include/ -isystem external/dbio/ -isystem external/rdkit -isystem external/libxml2/include -isystem external/cxxtest/ -pipe -Qunused-arguments -DUNUSUAL_ALLOCATOR_DECLARATION -ftemplate-depth-256 -stdlib=libstdc++ -Wno-long-long -Wno-strict-aliasing -O0 -g -DBOOST_ERROR_CODE_HEADER_ONLY -DBOOST_SYSTEM_NO_DEPRECATED -DBOOST_MATH_NO_LONG_DOUBLE_MATH_FUNCTIONS -DPTR_STD -Isrc -I./ -Itest/ -Isrc/platform/linux -ferror-limit=1 -DIWYU_SCAN'''.split()

commandline_flags = commandline_flags_linux

DEBUG = False

####################################

SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))

NONSTANDARD_FORWARDS = {}
if( os.path.exists(SCRIPTDIR+"/IWYU_nonstandard_fwd.txt") ):
  with open(SCRIPTDIR+"/IWYU_nonstandard_fwd.txt") as f:
    for line in f:
        line = line.split()
        if len(line) == 2 and not line[0].startswith("#"):
            if line[0] in NONSTANDARD_FORWARDS:
                print( "DUPLICATE ENTRY IN IWYU_nonstandard_fwd.txt!!!!!!! -", line[0] )
            NONSTANDARD_FORWARDS[ line[0] ] = line[1]

SHADOWING_PROVIDERS = {}
ADDDEL_SHADOWS = {}
GLOBBING_PROVIDERS = {}
if( os.path.exists(SCRIPTDIR+"/IWYU_provided_by.txt") ):
  with open(SCRIPTDIR+"/IWYU_provided_by.txt") as f:
    for full_line in f:
        line = full_line.split()
        if len(line) >= 2 and not line[0].startswith("#"):
            mainfile = line[0]
            if '*' in mainfile:
                provider_set = GLOBBING_PROVIDERS
            else:
                provider_set = SHADOWING_PROVIDERS
            for entry in line[1:]:
                if entry.startswith('#'):
                    break
                provider_set.setdefault(mainfile,[]).append(entry)
            if "ADDDEL" in full_line:
                for entry in line[1:]:
                    if entry.startswith('#'):
                        break
                    ADDDEL_SHADOWS.setdefault(mainfile,[]).append(entry)

FORCED_SUBS = {}
if( os.path.exists(SCRIPTDIR+"/IWYU_forced_subs.txt") ):
  with open(SCRIPTDIR+"/IWYU_forced_subs.txt") as f:
    for line in f:
        line = line.split()
        if len(line) >= 2 and not line[0].startswith("#"):
            if line[0] in FORCED_SUBS:
                print( "DUPLICATE ENTRY IN IWYU_forced_subs.txt !!!!!!! -", line[0] )
            FORCED_SUBS[ line[0] ] = line[1:]

UBIQUITOUS = set()
if( os.path.exists(SCRIPTDIR+"/IWYU_ubiquitous.txt") ):
  with open(SCRIPTDIR+"/IWYU_ubiquitous.txt") as f:
    for line in f:
        line = line.split()
        if len(line) >= 1 and not line[0].startswith("#"):
            if line[0] in UBIQUITOUS:
                print( "DUPLICATE ENTRY IN IWYU_forced_subs.txt !!!!!!! -", line[0] )
            UBIQUITOUS.add( line[0] )


###################################

def check_include_file_exists(filename):
    '''We assume we're running in the main/source directory'''
    return ( os.path.exists( 'src/' + filename ) or
        os.path.exists( 'external/include/' + filename ) or
        os.path.exists( 'external/' + filename ) or
        os.path.exists( 'external/boost_submod/' + filename ) or
        os.path.exists( 'external/dbio/' + filename )
    )

def convert_disk_to_include(filename):
    '''We assume we're running in the main/source directory'''
    if filename.startswith('src/'):
        return filename[4:]
    else:
        return filename

def process_namespace_line(line):
    '''Convert a namespace line (like `namespace core { namespace chemical { class ResidueType; } }`) to forward header name'''
    hierarchy = []
    nesting = 0
    for entry in line.split():
        if entry in ['namespace','{','template','class','struct','}']:
            continue
        nesting += entry.count('<')
        nesting -= entry.count('>')
        if nesting > 0 or '>' in entry:
            continue
        if entry.endswith(';'):
            hierarchy.append( entry[:-1] )
        else:
            hierarchy.append( entry )
    return hierarchy

def parse_current_includes(filename):
    '''Get the current list of includes.

    This is a little rough, as it doesn't consider issues with conditional compilation
    '''
    include_filenames = []
    with open(filename) as f:
        for line in f:
            line = line.split()
            if len(line) < 1 or not line[0] == '#include': continue
            include_filenames.append( line[1][1:-1] ) # Split off the surrounding delimiters.

    return include_filenames;

class IWYUChanges:
    def __init__(self, filename, additions, deletions, hh_adds=[]):
        self.filename = filename
        self.current_includes = parse_current_includes(filename)
        self.additions = self.process_additions( additions ) # {file:[why]}
        self.deletions = self.process_deletions( deletions ) # {file:[line]}
        self.hh_additions = self.process_additions( hh_adds )
        if DEBUG: self.prnt()
        self.cleanup()

    def process_deletions(self, deletions):
        '''Deletions are somewhat simple, in that we just want the filename and the line number.'''
        dels = {}
        for line in deletions:
            line = line.split()
            if line[1] == 'namespace':
                continue  # IWYU has some issues with unneeded forwards.
            if line[1] != '#include':
                print( "WARNING: Deletion line is malformed for ", self.filename, ':', ' '.join(line) )
                continue
            filename = line[2][1:-1] # Assume semi-well formed.
            lineno = line[-1].split('-')[0]
            dels.setdefault( filename, [] ).append(lineno) # In case there's multiple lines for same.
        return dels

    def process_additions(self, additions):
        adds = {}
        for line in additions:
            if line.startswith('#include'):
                # Regular include
                line = line.split()
                filename = line[1][1:-1]
                fors = line[4:]
                adds.setdefault( filename, []).extend(fors)
            elif line.startswith('namespace'):
                hierarchy = process_namespace_line(line)
                filename = '/'.join(hierarchy) + '.fwd.hh'
                if filename in NONSTANDARD_FORWARDS:
                    filename = NONSTANDARD_FORWARDS[filename]
                if not check_include_file_exists(filename):
                    print("WARNING: Can't find forward header file:", filename, "for", self.filename )
                else:
                    adds.setdefault( filename, [ hierarchy[-1] ] )
            else:
                print("WARNING: can't properly parse addition line: `", line, "` for", self.filename)
        return adds

    def cleanup(self):
        '''Do a bit of housekeeping.'''

        self.cleanup_parent_delete()
        self.cleanup_hh_additions()

        # This is near the top because we don't merge reasons in the combinations below
        self.cleanup_namespace_only()

        self.cleanup_forward_additions()

        # We want to make sure we do the other cleanups before we consider shadowing
        self.cleanup_shadowing()

        # Do forced subsitutions last, incase previous cleanups make them superfluous.
        self.cleanup_forced()

    def remove_deletion(self, fn):
        if fn not in self.deletions: return
        self.deletions[fn] = self.deletions[fn][1:] # Remove first
        if len( self.deletions[fn] ) == 0:
            del self.deletions[fn]

    def remove_addition(self, fn):
        if fn not in self.additions: return
        del self.additions[fn]

    def cleanup_parent_delete(self):
        '''For cc files, don't delete the corresponding hh file.
        For hh files, don't delete the corresponding fwd.hh file.
        '''
        if self.filename.endswith('.cc'):
            parent_header = convert_disk_to_include( self.filename[:-3] + ".hh" )
        elif self.filename.endswith('.hh'):
            parent_header = convert_disk_to_include( self.filename[:-3] + ".fwd.hh" )
        else:
            parent_header = None
        if parent_header in self.deletions:
            if DEBUG: print("%% NO DELETE PARENT", parent_header)
            self.remove_deletion( parent_header )

    def cleanup_hh_additions(self):
        '''IWYU has a habit of moving headers from the cc file to the hh file.
        (It prints out info for the header file when doing the cc file.)
        Since we explicitly run the hh files, and try to be minimal with the hh includes
        (just enough to get them to compile) don't delete headers from the cc file only
        to move them to the hh file.
        '''
        for fn in list( self.deletions.keys() ): # Copy as we're modifying structure in loop
            # If we deleted from the cc file but added to hh file, don't delete
            # The header should be processed separately.
            if fn in self.hh_additions:
                if DEBUG: print("%% NO DELETE ADDITION TO PARENT HEADER", fn)
                self.remove_deletion( fn )
                continue

    def cleanup_namespace_only(self):
        '''IWYU has a habit of ascribing namespaces to the first header which declares them,
        which means that it can add irrelevant headers just for the "declaration" of the namespace,
        even if another header we're adding/keeping also defines that namespace.
        '''
        for fn in list( self.additions.keys() ): # Copy as we're modifying structure in loop
            # If the only reason we're adding the header is a namespace, then don't add.
            reasons = self.additions[ fn ]
            namespaces = fn.split('/')[:-1] # Last is filename, not namespace
            trim_reasons = [ r for r in reasons if r not in namespaces and r != "std" ]
            if len(trim_reasons) == 0:
                if DEBUG: print("%% NO ADD NAMESPACE ONLY", fn)
                self.remove_addition( fn )
                continue
            elif len(trim_reasons) != reasons:
                self.additions[ fn ] = trim_reasons

    def cleanup_forward_additions(self):
        '''Some forward-related cleanups. Much of this has to do with the manual conversion of
        IWYU forward declarations to fwd header additions.

        * Don't both add and delete the same header.
        * Don't add the fwd.hh file if we already have the plain hh file
        * Don't add if we already exist.
        '''
        for fn in list( self.additions.keys() ): # Copy as we're modifying structure in loop
            #Don't delete then add.
            if fn in self.deletions:
                if DEBUG: print("%% NO ADD/DELETE", fn)
                self.remove_deletion( fn )
                self.remove_addition( fn )
                continue
            # Don't have both forward and regular
            if fn.endswith('.fwd.hh'):
                parent_fn = fn[:-7]+".hh"
                # Don't add both
                if parent_fn in self.additions:
                    if DEBUG: print("%% NO ADD BOTH", fn)
                    self.remove_addition( fn )
                    continue
                # Don't add if we already have the regular, and we're not deleting it
                if parent_fn in self.current_includes and parent_fn not in self.deletions:
                    if DEBUG: print("%% NO ADD, PARENT EXIST", fn)
                    self.remove_addition( fn )
                    continue
            # Don't add if we already exist and we're not being deleted. (Mainly for fwds)
            if fn in self.current_includes and fn not in self.deletions:
                if DEBUG: print("%% NO ADD, ALREADY EXIST", fn)
                self.remove_addition( fn )
                continue

    def cleanup_shadowing(self):
        '''Cleanup based on the provided shadowing definitions.'''
        for fn in list( self.additions.keys() ): # Copy as we're modifying structure in loop
            # Don't add if there's a shadowing provider
            if fn in SHADOWING_PROVIDERS:
                for entry in SHADOWING_PROVIDERS[fn]:
                    if entry in self.additions or (entry in self.current_includes and entry not in self.deletions):
                        if DEBUG: print("%% NO ADD DUE TO SHADOW", fn)
                        self.remove_addition( fn )
                        break
                    # We deliberately don't undo deletions, the added file might be more than we actually need
                    # (See the forced substitutions for alternative.)
            for gp in GLOBBING_PROVIDERS:
                if fnmatch(fn, gp):
                    for entry in GLOBBING_PROVIDERS[gp]:
                        if entry in self.additions or (entry in self.current_includes and entry not in self.deletions):
                            if DEBUG: print("%% NO ADD DUE TO GLOB SHADOW", fn)
                            self.remove_addition(fn)
                            break
                        # We deliberately don't undo deletions, the added file might be more than we actually need
                        # (See the forced substitutions for alternative.)
            for fn in ADDDEL_SHADOWS:
                for entry in ADDDEL_SHADOWS[fn]:
                    if entry in self.deletions:
                        if DEBUG: print("%% NO ADD/DEL DUE TO SHADOW", fn)
                        self.remove_deletion( entry )
                        self.remove_addition( fn )
                        break

    def cleanup_forced(self):
        '''Address situations where we specify we always want to add a different header,
        rather than the one auto-selected by IWYU.'''
        for fn in list( self.additions.keys() ): # Copy as we're modifying structure in loop
            if fn in UBIQUITOUS:
                if DEBUG: print("%% NO ADD UBIQUITOUS", fn)
                self.remove_addition( fn )
                continue
            if fn in FORCED_SUBS and self.filename not in FORCED_SUBS[fn]:
                replace = FORCED_SUBS[fn][0]
                if replace in self.deletions:
                    if DEBUG: print("%% NO ADD FORCE SUB DELETION REMOVAL", fn)
                    self.remove_deletion( replace )
                    self.remove_addition( fn )
                    continue
                elif replace in self.additions:
                    if DEBUG: print("%% NO ADD FORCE SUB ALREADY ADD", fn)
                    self.remove_additions( fn )
                    continue
                elif replace in self.current_includes:
                    if DEBUG: print("%% NO ADD FORCE SUB CURRENT", fn)
                    self.remove_addition( fn )
                    continue
                else:
                    if DEBUG: print("%% NO ADD FORCE SUB CONVERT", fn)
                    self.additions[ replace ] = self.additions[ fn ]
                    self.remove_addition( fn )
                    continue

    def prnt(self):
        if len(self.deletions) == 0 and len(self.additions) == 0:
            print("%%%%%%%%%% NO MOD NEEDED:", self.filename)
        else:
            print("%%%%%%%%%%%%%%%%%%%%%%%%%", self.filename)
            print("~~~~~ Deleting")
            print('\n'.join( fn + " // Line " + ','.join(lns) for fn, lns in self.deletions.items()))
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("~~~~~ Adding")
            print('\n'.join( "#include <" + fn + "> // For " + ' '.join(whys) for fn, whys in self.additions.items()))
            if DEBUG:
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print("~~~~~ Current")
                print('\n'.join( fn for fn in self.current_includes))
            print("%%%%%%%%%%%%%%%%%%%%%%%%%", self.filename)

    def save(self):
        '''Save to a json-formatted .riwyuf (Rosetta include-what-you-use-fixes'''
        if len(self.additions) == 0 and len(self.additions) == 0:
            return # Save nothing if there's nothing to do.
        ofn = self.filename + '.riwyuf'
        with open(ofn, 'w') as f:
            json.dump( {'additions':self.additions,'deletions':self.deletions}, f, indent=2 )

def get_output_for_file(filename, options):
    '''Get the raw iwyu output for the file, as lines'''
    if not os.path.exists( SCRIPTDIR + '/boost-all.imp' ):
        sys.stderr.write("Error: Please put IWYU's boost-all.imp file in the same directory as the script.\n")
        sys.exit()

    command = [ options.x, '-Xiwyu', '--mapping_file=' + SCRIPTDIR + '/Rosetta.imp', '-Xiwyu', '--max_line_length=120']
    for option in options.X:
        command += [ '-Xiwyu', option ]

    command += commandline_flags + [ filename ]

    run = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = run.communicate()
    stdout = codecs.decode( stdout, "UTF-8", "replace")
    stderr = codecs.decode( stderr, "UTF-8", "replace")

    if options.f:
        sys.stdout.write( ' '.join(command) + "\n")
        sys.stdout.write( stderr )
        sys.stdout.write( "%%%\n" )

    return stderr.split('\n')

def print_parse_error( filename, output, message  ):
    if ( 'src/devel/' in filename  or 'src/apps/pilot/' in filename ):
        print( "Skipping", filename, " -- does not appear to compile." )
        return
    # Give a detailed error report for the rest
    print( "###################################################" )
    print( ">>>> ERROR with", filename, "::", message, "<<<<" )
    sys.stdout.write('\n'.join(output)  )
    print( ">>>> Skipping processing for", filename, "<<<<")
    print( "###################################################")

def parse_output( filename, output ):
    hh_additions = []
    additions = None
    deletions = None
    in_add_block = False
    in_delete_block = False
    in_hh_add_block = False

    has_correct_includes = False

    # We parse the block for hh lines in cc run because IWYU tends to move them up.
    hh_filename = None
    if filename.endswith('.cc'):
        hh_filename = filename[:-3] + '.hh'

    for line in output:
        #Only trigger on the blocks for the file we're in.
        if filename + ' has correct #includes/fwd-decls' in line:
            has_correct_includes = True
            continue
        if line.startswith(filename):
            if 'should add these lines:' in line:
                in_add_block = True
                if additions is None:
                    additions = []
                continue
            elif 'should remove these lines:' in line:
                in_delete_block = True
                if deletions is None:
                    deletions = []
                continue
            # Oops, there's something off here
            print_parse_error( filename, output, "Unexpected filename line" )
            return None
        if hh_filename is not None and line.startswith(hh_filename):
            if 'should add these lines:' in line:
                in_hh_add_block = True
                continue
            # We don't care if there's other blocks.
        if line.strip() == "":
            # end processing of block on empty line
            in_add_block = False
            in_delete_block = False
            in_hh_add_block = False
            continue
        assert( not ( in_add_block and in_delete_block ) )
        if in_add_block:
            if not (line.startswith('#include') or line.startswith('namespace') or line.startswith('class') or line.startswith('struct')):
                print_parse_error( filename, output, "Addition block line doesn't start with include or namespace: " + line )
            additions.append( line )
            continue
        if in_hh_add_block:
            if not (line.startswith('#include') or line.startswith('namespace') or line.startswith('class') or line.startswith('struct')):
                print_parse_error( filename, output, "Addition block line doesn't start with include or namespace: " + line )
            hh_additions.append( line )
            continue
        if in_delete_block:
            if not line[0] == '-':
                print_parse_error( filename, output, "Deletion block line doesn't start with minus: " + line )
                return None
            deletions.append( line )
            continue


    if has_correct_includes:
        if DEBUG: print('>>>>', "No changes needed for", filename)
        return None
    elif additions is None or deletions is None:
        print_parse_error( filename, output, "Could not find addition and/or deletions block" )
        return None

    return IWYUChanges(filename, additions, deletions, hh_additions)

def check_file(filename, options):

    output = get_output_for_file(filename, options)
    mods = parse_output(filename, output)
    if mods is not None and options.f:
        mods.prnt()
    return mods

def process_file(filename, options):

    if options.nofwd and filename.endswith(".fwd.hh"):
        if DEBUG: print("Not processing forward header", filename)
        return
    if not ( filename.endswith(".hh") or filename.endswith(".cc") ):
        print("Skipping", filename, "-- not hh/cc")
        return
    if 'OptionKeys.cc.gen' in filename:
        # Not intended to compile on their own
        if DEBUG: print("Skipping", filename, "-- Options gen")
        return
    if filename.endswith('.py.hh'):
        #PyRosetta-specific files - skip
        if DEBUG: print("Skipping", filename, "-- PyRosetta specific")
        return

    print("Running IWYU analysis on", filename)
    mods = check_file(filename, options)

    if DEBUG and mods is not None:
        mods.prnt()

    if mods is not None:
        mods.save()


def process_dir(dirname):
    for item in os.listdir(dirname):
        name = os.path.join(dirname,item)
        if os.path.isdir(name):
            if name in ['src/platform','src/utility/pointer/boost','src/utility/py','src/ui']:
                # Specialty directories - don't bother traversing.
                continue
            for fn in process_dir(name):
                yield fn
        elif os.path.isfile(name):
            if name.endswith(".cc"):
                yield name
            elif name.endswith(".hh"):
                # While info for the header is reported when processing the cc file,
                # the info is different than when the hh file is processed itself,
                # and doesn't look to be a "compile on your own" sense.
                yield name

def find_files(pathlist):
    for name in pathlist:
        if os.path.isdir(name):
            for fn in process_dir(name):
                yield fn
        elif os.path.isfile(name):
            yield name
        else:
            print("Cannot find file or directory: "+name)

if __name__ == "__main__":
    if not os.path.exists( "./src" ):
        print( "Script must be run from within Rosetta/main/source/" )
        exit()

    parser = OptionParser(usage="usage: %prog [OPTIONS] [FILES|DIRECTORIES]")
    parser.set_description(__doc__)
    parser.add_option("-f",
      default=False, action="store_true",
      help="Print the full output of include_what_you_use prior to processing it." )
    parser.add_option("-I",
      default=[], action="append",
      help="Add the passed directories to the inclusion search path (good if the stdlib isn't being properly found." )
    parser.add_option("-x",
      default="include-what-you-use", type=str,
      help="The command (path) to the IWYU executable." )
    parser.add_option("-X",
      default=[], action="append",
      help="Add extra options to pass to Include What You Use." )
    parser.add_option("--debug",
      default=False, action="store_true",
      help="Print extra debugging info." )
    parser.add_option("-j",
      default=0, type=int,
      help="Number of processes to run." )
    parser.add_option("--nofwd",
      default=False, action="store_true",
      help="Don't process fwd.hh files." )

    (options, args) = parser.parse_args(args=sys.argv[1:])

    DEBUG = options.debug

    if len(options.I) > 0:
        commandline_flags += ['-I'+path for path in options.I]

    if options.j == 0:
        for fn in find_files(args):
            process_file(fn, options)
    else:
        import multiprocessing
        pool = multiprocessing.Pool(options.j)

        def callback(arg):
            print("Processing is done")

        for fn in find_files(args):
            pool.apply_async(process_file, (fn, options) )

        pool.close()
        pool.join()

