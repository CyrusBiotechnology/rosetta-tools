#!/usr/bin/env python

'''include_what_you_use.py - a script to run the clang tool "include-what-you-use" over
the Rosetta codebase, and adjust the output for the vagarities of the Rosetta coding style.

Run from the Rosetta/main/source directory and provide the script with files or directories,
and the .cc .hh and .fwd.hh files therein will be processed.

Because of order dependancy in removing headers, the default behavior is to create an *.iwyu
file in the same location, listing what should be done to the file.
Using the -m option will cause this script to read the *.iwyu file,
and actually modify the files.

Behavior of the script can be modified by the IWYU_nonstandard_fwd.txt and IWYU_provided_by.txt
files in the same directory as the script.
'''

import sys, os
import subprocess
from fnmatch import fnmatch

from optparse import OptionParser

scriptdir = os.path.dirname(os.path.realpath(__file__))

NONSTANDARD_FORWARDS = {}
if( os.path.exists(scriptdir+"/IWYU_nonstandard_fwd.txt") ):
  with open(scriptdir+"/IWYU_nonstandard_fwd.txt") as f:
    for line in f:
        line = line.split()
        if len(line) == 2 and line[0] != "#":
            NONSTANDARD_FORWARDS[ line[0] ] = line[1]

# Because the IWYU pragmas aren't working for me, and we don't want to clutter, anyway
class PROVIDERS_t:
    def __init__(self):
        self.files = {}
        self.globs = []
        if( os.path.exists(scriptdir+"/IWYU_provided_by.txt") ):
            with open(scriptdir+"/IWYU_provided_by.txt") as f:
                 for line in f:
                    line = line.split()
                    if len(line) < 2 or line[0][0] == "#":
                        continue
                    if "*" in line[0] or "?" in line[0]:
                        self.globs.append( line )
                    else:
                        self.files[ line[0] ] = line[1:]

    def __call__(self, name):
        providers = []
        if name in self.files:
            providers.extend( self.files[name] )
        for entry in self.globs:
            if fnmatch(name, entry[0]):
                providers.extend( entry[1:] )
        return providers

    def has(self, name):
        if name in self.files:
            return True
        for entry in self.globs:
            if fnmatch(name, entry[0]):
                return True
        return False

PROVIDERS = PROVIDERS_t()


#These are the clang commandline flags for debug mode, stripped of warning issues
commandline_flags = '''-c -std=c++98 -isystem external/boost_1_55_0/ -isystem external/include/ -isystem external/dbio/ -pipe -Qunused-arguments -DUNUSUAL_ALLOCATOR_DECLARATION -ftemplate-depth-256 -stdlib=libstdc++ -Wno-long-long -Wno-strict-aliasing -O0 -g -fPIC -DBOOST_ERROR_CODE_HEADER_ONLY -DBOOST_SYSTEM_NO_DEPRECATED -DPTR_BOOST -Isrc -Iexternal/include -Isrc/platform/linux/32/clang/3.4 -Isrc/platform/linux/32/clang -Isrc/platform/linux/32 -Isrc/platform/linux -Iexternal/boost_1_55_0 -Iexternal/dbio -Iexternal/cxxtest/ -I./ -Itest/ -ferror-limit=1'''.split()

## -I/usr/include -I/usr/local/include

executable = 'include-what-you-use'

class IWYUChanges:
    def __init__(self, lines=None):
        self.additions = []
        self.deletions = []
        #self.fulllist = []
        self.forwards = set()
        self.allheaders = set()
        self.alldeletions = set()
        self.filename = ''

        if lines is not None:
            self.parse(lines)
            self.cleanup()

    def prnt(self):
        if len(self.deletions) == 0 and len(self.additions) == 0:
            print "%%%%%%%%%% NO MOD NEEDED:", self.filename
        else:
            print "%%%%%%%%%%%%%%%%%%%%%%%%%", self.filename
            print "~~~~~ Deleting"
            print '\n'.join( v for k, v in self.deletions)
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            print "~~~~~ Adding"
            print '\n'.join( v for k, v in self.additions)
            print "%%%%%%%%%%%%%%%%%%%%%%%%%", self.filename

    def parse(self, lines):
        stage = ''
        for line in lines:
            line = line.strip()
            split_line = line.split()
            if not line:
                continue
            if line.endswith("should add these lines:"):
                stage = 'adding'
                if self.filename and split_line[0] != self.filename:
                    raise ValueError("Inconsistent filename in output: " + split_line[0] + " versus " + self.filename)
                self.filename = split_line[0]
                continue
            if line.endswith("should remove these lines:"):
                stage = 'removing'
                if self.filename and split_line[0] != self.filename:
                    raise ValueError("Inconsistent filename in output: " + split_line[0] + " versus " + self.filename)
                self.filename = split_line[0]
                continue
            if line.startswith("The full include-list"):
                stage = 'fullist'
                if self.filename and split_line[-1][:-1] != self.filename:
                    raise ValueError("Inconsistent filename in output: " + split_line[0][:-1] + " versus " + self.filename)
                self.filename = split_line[-1][:-1]
                continue

            if stage == 'adding':
                if line.startswith("namespace"):
                    self.forwards.add( self.normalize(line) )
                else:
                    self.additions.append( (split_line[1][1:-1], line) )
            elif stage == 'removing':
                if split_line[1] != "namespace":
                    self.deletions.append( (split_line[2][1:-1], line) )
                    self.alldeletions.add( split_line[2][1:-1] )
            elif stage == 'fullist':
                if not line.startswith("namespace"):
                    self.allheaders.add( split_line[1][1:-1] )
                    #self.fulllist.append( (split_line[1][1:-1], line) )
            else:
                pass
                #print "Unexpected value '"+line+"' for line in output"

    def cleanup(self):
        newdel = []
        for name, line in self.deletions:
            if (line.find("DO NOT AUTO-REMOVE") != -1 or
                    line.find("DO NOT AUTOREMOVE") != -1):
                # Note that this isn't going to trigger as
                # IWYU strips out the comments from the line
                self.allheaders.add(name)
                self.alldeletions.remove(name)
            elif name in self.forwards:
                # Don't delete a forward we need.
                self.forwards.remove(name)
                self.alldeletions.remove(name)
                self.allheaders.add(name)
                #self.fulllist.append( (name, "#include <"+name+"> //FWD") )
            elif name.endswith(".fwd.hh") and self.filename[:-3].endswith(name[:-7]):
                # Don't delete our own forward
                self.allheaders.add(name)
                self.alldeletions.remove(name)
                #self.fulllist.append( (name, "#include <"+name+"> //FWD") )
            elif name.endswith("OptionKeys.gen.hh") and "basic/options/option_macros.hh" in self.allheaders:
                # The option macros don't see the option keys appropriately - ignore if present
                self.allheaders.add(name)
                self.alldeletions.remove(name)
            elif name in ("fstream","basic/datacache/BasicDataCache.hh"):
                # Problematic headers when deleting - just skip
                self.allheaders.add(name)
                self.alldeletions.remove(name)
            else:
                newdel.append( (name,line) )
        self.deletions = newdel

        newadd = []
        for name, line in self.additions:
            if name.endswith(".fwd.hh") and name[:-7]+".hh" in self.allheaders:
                #Don't add a forward if we have or will have the regular header
                self.allheaders.remove(name)
            elif self.filename.endswith(".hh") and name[:-3]+".fwd.hh" in self.alldeletions:
                #Fix an over-zealous issue (Seen with Pose.hh)
                #We assume that all headers compile on their own, so we probably don't need
                #to replace a forward with a regular one. And even if we do, we should probably
                #alter things manually such that the regular header isn't needed anyway.
                fwd = name[:-3]+".fwd.hh"
                self.alldeletions.remove(fwd)
                self.allheaders.add(fwd)
                self.allheaders.remove(name)
                found = None
                for ii, (dname, dline) in enumerate(self.deletions):
                    if dname == fwd:
                        found = ii
                if found is not None:
                    del self.deletions[found]
            elif PROVIDERS.has(name):
                providers = PROVIDERS(name)
                if any( n in self.allheaders for n in providers ):
                    #Don't add a header if we have any alternates which provide it.
                    self.allheaders.remove(name)
                elif any( n in self.alldeletions for n in providers ):
                    #Don't delete a header that provides another, if we just want to add it back
                    found = None
                    found_dname = None
                    for ii, (dname, dline) in enumerate(self.deletions):
                        #First-come, first-serve is probably not ideal.
                        if dname in providers:
                            found = ii
                            found_dname = dname
                            break
                    if found is not None:
                        del self.deletions[found]
                        self.alldeletions.remove(found_dname)
                        self.allheaders.add(found_dname)
                        self.allheaders.remove(name)
                    else:
                        #Something went wrong - punt
                        newadd.append( (name,line) )
                elif len(providers) == 1:
                    #If it's provided by a single header, then replace it - but only if we don't already have it
                    self.allheaders.remove(name)
                    replacement_name = providers[0]
                    if replacement_name not in self.allheaders:
                        #print "REPLACING", name, "with", replacement_name
                        if '//' in line:
                            comment = " " + line[line.index('//'):]
                        else:
                            comment = ''
                        newadd.append( (replacement_name, "#include <"+replacement_name+">"+comment))
                        self.allheaders.add(replacement_name)
                else:
                    #Spoilt for choice, stick to the current one
                    newadd.append( (name,line) )
            else:
                newadd.append( (name,line) )
        self.additions = newadd

        #Only add forwards if we don't already have them present (and won't be adding them)
        for name in list(self.forwards): # List so we don't modify while iterating
            if name not in self.allheaders:
                self.additions.append( (name, "#include <"+name+">") )
                self.allheaders.add(name)
        self.forwards.clear()

        # Special casing - Don't add owning_ptr and ReferenceCount if we're not in a fwd header
        if not self.filename.endswith(".fwd.hh"):
            for ii, (name, line) in enumerate( list(self.additions) ): #list() to make copy
                if name == "utility/pointer/owning_ptr.hh" or name == "utility/pointer/ReferenceCount.hh":
                    self.additions.remove( (name, line) )
                    self.allheaders.remove( name )


    def nested_prune(self, other):
        # Don't add headers if other (our upwardly nested header) already has them
        newadd = []
        for name, line in self.additions:
            if name in other.allheaders:
                self.allheaders.remove(name)
            elif PROVIDERS.has(name):
                #Don't add if we have a provided by in the other
                for n in PROVIDERS(name):
                    if n in other.allheaders:
                        break
                else:
                    # Only if we fall off the end without breaking
                    # i.e. we don't have a provided by
                    newadd.append( (name,line) )
            else:
                newadd.append( (name,line) )
        self.additions = newadd

    def write_cache(self):
        '''Write out information needed for changing the file'''
        with open(self.filename + ".iwyu", 'w') as f:
            for name, line in self.deletions:
                f.write( name + "|" + line + "\n" )
            f.write(80*'~' +'\n')
            for name, line in self.additions:
                f.write( name + "|" + line + "\n" )

    def change(self):
        '''Actually change the file on disk for the modifications'''
        if len(self.additions) == 0 and len(self.deletions) == 0:
            # Nothing to do
            # print "NO MODIFICATION NEEDED:", self.filename
            return
        print "%%%%%%%%%%%%%%%%%%%%%%%%%", self.filename

        # Figure out the deletions

        deletion_lines = []
        for name, line in self.deletions:
            lineno = line.rsplit('-', 1)[-1]
            deletion_lines.append( int(lineno) )
        deletion_lines.sort(reverse=True) # Reversed so the numbers won't shift during deletion

        #Figure out the additions
        additional_lines = []
        if self.additions:
            additional_lines = ["//Auto Headers\n"]

            incs = {}
            for name, line in self.additions:
                first = name.split('/')[0]
                if '/' in name and first in ("devel","protocols","core","basic","numeric","utility","ObjexxFCL"):
                    incs.setdefault(first,[]).append( (name,line) )
                else:
                    incs.setdefault("other",[]).append( (name,line) )

            for first in ("devel","protocols","core","basic","numeric","utility","ObjexxFCL", "other"):
                if first not in incs:
                    continue
                group_lines = incs[first]
                group_lines.sort()
                for name, line in group_lines:
                    split_comment = line.split("//")
                    if len(split_comment) >= 2:
                        comment = " //" + split_comment[-1]
                    else:
                        comment = ''
                    additional_lines.append( "#include <"+name+">" + comment + "\n")

            #additional_lines.append("\n")

        # Now actually modify

        with open( self.filename ) as f:
            lines = f.readlines()

        insertion_pos = 0
        for ii, line in enumerate(lines):
            line = line.strip()
            if len(line) == 0 or line.startswith("//"):
                continue
            if line.startswith("#"):
                insertion_pos = ii+1
            else:
                break

        print "~~~~~ Deleting"
        for lineno in deletion_lines:
            if ("DO NOT AUTO-REMOVE" in lines[ lineno - 1 ] or
                    "DO NOT AUTOREMOVE" in lines[ lineno - 1 ]):
                # We have to do this here, as earlier IWYU striped out the comments
                continue
            newline = "// AUTO-REMOVED " + lines[ lineno - 1 ]
            sys.stdout.write(newline)
            lines[ lineno - 1 ] = newline

        print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        print "~~~~~ Adding"
        if additional_lines:
            if insertion_pos == 0:
                raise ValueError("Cannot find appropriate place to put added lines for "+self.filename)
            if lines[insertion_pos-1].strip() != "":
                additional_lines = ["\n"] + additional_lines
            if lines[insertion_pos].strip() != "":
                additional_lines = additional_lines + ["\n"]

            sys.stdout.write( ''.join(additional_lines) )
            lines = lines[:insertion_pos] + additional_lines + lines[insertion_pos:]
        print "%%%%%%%%%%%%%%%%%%%%%%%%%", self.filename

        with open( self.filename, 'w' ) as f:
            f.writelines(lines)


    def normalize(self, line):
        if not line.startswith('namespace'):
            return line

        name = []
        for l in line.split():
            if l in ['namespace','{','template','<typename','>','class','struct','}']:
                continue
            if '<' in l or '>' in l:
                continue
            name.append( l )
        name = '/'.join(name)

        # [:-1] to get rid of the semicolon
        name = name[:-1] + ".fwd.hh"
        if name in NONSTANDARD_FORWARDS:
            name = NONSTANDARD_FORWARDS[ name ]
        if not os.path.exists( 'src/' + name ) and not os.path.exists( 'external/include/' + name ) and not os.path.exists( 'external/dbio/'+name ):
            raise ValueError("Forward header '"+name+"' not found - either create or list in NONSTANDARD_FORWARDS")
        return name


def read_mod_file(fn):
    '''Read in information needed for changing the file'''
    print "Reading file ", fn
    mod = IWYUChanges()
    mod.filename = fn
    with open(fn + ".iwyu") as f:
        read_add = False
        for line in f:
            line = line.strip()
            if line.startswith(80*'~'):
                read_add = True
                continue
            if read_add == True:
                name, l = line.split('|',1)
                mod.additions.append( (name, l) )
            else:
                name, l = line.split('|',1)
                mod.deletions.append( (name, l) )
    return mod

def check_file(filename, options):
    print "%%% Processing ", filename
    command = [executable] + commandline_flags + [ filename ]

    run = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = run.communicate()

    if options.f:
        sys.stdout.write( ''.join(command) + "\n")
        sys.stdout.write( stderr )
        sys.stdout.write( "%%%\n" )

    lines = stderr.split('\n')

    mods = []
    block = []
    for line in lines:
        if line.startswith('---'):
            # Really hacky error detecting code, but ...
            if not block[1].endswith("should add these lines:") and "has correct" not in ''.join(block):
                print "###################################################"
                print ">>>> ERROR with", filename, "<<<<"
                sys.stdout.write('\n'.join(lines)  )
                print ">>>> Skipping processing for", filename, "<<<<"
                print "###################################################"
                return [] # Abort the whole processing endeavor
            else:
                mods.append( IWYUChanges(block) )
            block = []
        else:
            block.append(line)

    return mods

def process_file(filename, options):

    if not os.path.exists( filename + ".iwyu" ):
        mods = []
        if os.path.exists( filename[:-3] + ".fwd.hh" ):
            mods.extend( check_file(filename[:-3] + ".fwd.hh", options) )

        #Headers are automatically checked for hh files.
        mods.extend( check_file(filename, options) )

        # Remove added includes if nested headers have them
        # Should be in nested include order
        for ii in range( len(mods) ):
            for jj in range( ii+1, len(mods) ):
                if not mods[ii].filename.startswith( mods[jj].filename[:-3] ):
                    raise ValueError("File "+mods[ii].filename+" is not in series with "+mods[jj].filename)
                mods[jj].nested_prune( mods[ii] )

        for mod in mods:
            mod.write_cache()
            mod.prnt()

    if options.m:
        files = [filename]
        if not filename.endswith(".fwd.hh") and os.path.exists( filename[:-3] + ".fwd.hh" ):
            files.append( filename[:-3] + ".fwd.hh" )
        if filename.endswith(".cc") and os.path.exists( filename[:-3] + ".hh" ):
            files.append( filename[:-3] + ".hh" )
        for fn in files:
            if os.path.exists( fn ):
                mod = read_mod_file(fn)
                mod.change()
                os.remove(fn +".iwyu" )
            else:
                print "%%% Ignoring", fn, "- no change file found."

def process_dir(dirname, options):
    for item in os.listdir(dirname):
        name = os.path.join(dirname,item)
        if os.path.isdir(name):
            process_dir(name, options)
        elif os.path.isfile(name):
            if name.endswith(".cc"):
                #print ">>> CC: ", name
                process_file(name, options)
            elif name.endswith(".fwd.hh"):
                if not os.path.exists( name[:-7] + ".cc" ):
                    #print ">>> FWD: ", name, name[:-7] + ".cc"
                    process_file(name, options)
            elif name.endswith(".hh"):
                if not os.path.exists( name[:-3]+".cc" ):
                    #print ">>> HH: ", name, name[:-3] + ".cc"
                    process_file(name, options)

if __name__ == "__main__":
    if not os.path.exists( "./src" ):
        print "Script must be run from within Rosetta/main/source/"
        exit()

    parser = OptionParser(usage="usage: %prog [OPTIONS] [FILES|DIRECTORIES]")
    parser.set_description(__doc__)
    parser.add_option("-m",
      default=False, action="store_true",
      help="Actually modify the files on-disk. It's recommended to have a clean git working directory first" )
    parser.add_option("-f",
      default=False, action="store_true",
      help="Print the full output of include_what_you_use prior to processing it." )

    (options, args) = parser.parse_args(args=sys.argv[1:])

    for name in args:
        if os.path.isdir(name):
            process_dir(name, options)
        elif os.path.isfile(name):
            process_file(name, options)
        else:
            print "Cannot find file or directory: "+name
            exit()
