import code_utilities
import library_levels
import pygraph
import inclusion_graph
import sys

# returns a tuple -- an integer and a string -- representing the library name and column.
def library_level_and_column_from_src_settingsfile_name( libprefix, lib_srcsettings_fname ) :
   assert( lib_srcsettings_fname.find( libprefix ) != -1 )
   suffix = lib_srcsettings_fname[len(libprefix):][:-13]
   print libprefix, suffix, lib_srcsettings_fname[len(libprefix):]
   if len( suffix ) == 2 :
      return int(suffix[-1:]), ""
   elif len( suffix ) == 4 :
      return int( suffix[-1:]), suffix[-3:2]

if __name__ == "__main__" :

   graphviz_output = False;
   if len( sys.argv ) > 1 and sys.argv[1] == "--graphviz" :
      graphviz_output = True

   #inclusion_graph.remove_known_circular_dependencies_from_graph( g )
   #tg = inclusion_graph.transitive_closure( g )

   prot_levels = library_levels.protocols_levels()

   protocols_library_graph = pygraph.digraph()
   projects = code_utilities.rosetta_projects()
   for lib in projects[ "src" ] :
      #print lib
      if lib.find( "protocols" ) != -1 :
         suffix = lib[9:]
         if len( suffix ) == 2 :
            protocols_library_graph.add_node( lib[-1:] ) # e.g. "7" for protocols.7
         elif len( suffix ) == 4 :
            protocols_library_graph.add_node( lib[-1:] + lib[-3:-2] ) # e.g. 4a for protocols_a.4

   #for node in protocols_library_graph.nodes() :
   #    print " protols libray graph node:", node

   #lev, column = library_levels.library_and_column_for_file( prot_levels, "protocols/abinitio/ClassicAbinitio.hh" )
   #print "protocols/abinitio/ClassicAbinitio.hh", str(lev) + str(column)
   #lev, column = library_levels.library_and_column_for_file( prot_levels, "protocols/init/init.hh" )
   #print "protocols/init/init.hh", str(lev) + str(column)

   #sys.exit(0)

   compilable_files, all_includes, file_contents = code_utilities.load_source_tree()
   #print "...source tree loaded"
   g = inclusion_graph.create_graph_from_includes( all_includes )
   #print "...inclusion graph created"

   for edge in g.edges() :
      file1,file2 = edge
      lib1 = library_levels.libname_for_file( file1 )
      lib2 = library_levels.libname_for_file( file2 )
      if lib1 != "protocols" or lib2 != "protocols" : continue
      lev1,col1 = library_levels.library_and_column_for_file( prot_levels, file1 )
      lev2,col2 = library_levels.library_and_column_for_file( prot_levels, file2 )
      node1 = str(lev1) + col1
      node2 = str(lev2) + col2
      if node2 not in protocols_library_graph.neighbors( node1 ) :
          #print "adding edge", node1, node2
          protocols_library_graph.add_edge( node1, node2 )

   #protocols_tg = inclusion_graph.transitive_closure( protocols_library_graph )
   if not graphviz_output :
      protocols_tg = protocols_library_graph
      for node in protocols_tg.nodes() :
         print "Dependencies for node", node
         for node_neighbor in protocols_tg.neighbors( node ) :
            print "  ", node_neighbor
   else :
      print "digraph G {"
      for level in xrange(len(prot_levels)) :
         print "subgraph level" + str(level+1) + " { rank = same; ",
         if len(prot_levels[level]) == 1 :
            print "p" + str(level+1) + ";}"
         else:
            for column in xrange(len(prot_levels[level])) :
               print "p" + str(level+1) + chr( ord('a') + column ) + ";",
            print "}"
      for node in protocols_library_graph.nodes() :
         print "p" + node + ";"
      for node in protocols_library_graph.nodes() :
         for node2 in protocols_library_graph.neighbors( node ) :
            if node == node2 : continue
            print "p"+ node2, "-> p" + node + " [ dir=back ];"
      print "}"

