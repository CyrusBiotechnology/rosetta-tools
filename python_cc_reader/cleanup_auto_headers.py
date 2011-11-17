from code_utilities import load_source_tree, directories_with_ccfiles_to_examine
from add_headers import write_file
import sys

# $1..$n the specific files to apply the cleanup to; if none given, then all files are cleaned.

def cleanup_autoheaders_for_lines( flines ) :
    newlines = []
    found_auto_headers = False
    auto_header_begin = -1
    count_line = 0
    for line in flines :
        if found_auto_headers :
            if len(line) >= len("// AUTO-REMOVED ") and line[:len("// AUTO-REMOVED ")] == "// AUTO-REMOVED " :
                # if this is an auto-header and it's been auto-removed, remove it for real
                count_line += 1
                continue
            If line == "\n" and (count_line == auto_header_begin + 1)
                count_line += 1
                continue
            elif line == "\n" and  (count_line == auto_header_begin + 2 ) :
                count_line += 1
                continue
            else :
                newlines.append( "//Auto Headers\n" )
        elif line == "//Auto Headers\n" :
            found_auto_headers = True
            auto_header_begin = count_line
            count_line += 1
            continue
        newlines.append( line )
        count_line += 1
    return newlines

if __name__ == "__main__" :
    if len(sys.argv) < 2 :
        print "cleaning autoheaders for all files..."
        compilable_files, all_includes, file_contents = load_source_tree()
        for fname in file_contents :
            toks = fname.split("/")
            if len(toks) < 0 or toks[0] not in directories_with_ccfiles_to_examine() :
                continue
            print "processing", fname
            flines = file_contents[ fname ]
            newlines = cleanup_autoheaders_for_lines( flines )
            write_file( fname, newlines )
    else:
        files = sys.argv[1:]
        for fname in files :
            print "cleaning autoheaders from file:", fname
            flines = open(fname).readlines()
            newlines = cleanup_autoheaders_for_lines( flines )
            write_file( fname, newlines )
