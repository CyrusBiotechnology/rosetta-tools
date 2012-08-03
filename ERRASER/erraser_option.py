import os.path
import imp

file_path = os.path.split( os.path.abspath(__file__) ) [0]
imp.load_source('erraser_util', file_path + '/erraser_util.py')

from erraser_util import *

class erraser_option :

    def __init__( self ) :
        #General options
        self.input_pdb = ''
        self.map_file = ''
        self.out_pdb = ''
        self.out_prefix = ''
        self.map_reso = 2.5
        self.rosetta_folder = ''
        self.debug = False
        self.verbose = False
        self.kept_temp_folder = False
        self.use_existing_temp_folder = True
        self.new_torsional_potential = True
        self.rosetta_folder = ""
        self.log_out = ""
        self.log_err = ""

        #erraser options
        self.n_iterate = 1
        self.rebuild_rmsd = True
        self.rebuild_all = True
        self.fixed_res = []
        self.cutpoint = []
        self.extra_res = []
        self.fixed_res_rs = []
        self.cutpoint_rs = []
        self.rebuild_res_pdb = ""

        #Minimize
        self.vary_geometry = True
        self.constrain_phosphate = True
        self.res_slice = []

        #SWA rebuilding
        self.native_screen_RMSD = 3.0
        self.use_native_edensity_cutoff = False
        self.native_edensity_cutoff = 0.8
        self.ideal_geometry = True
        self.include_native = False
        self.slice_nearby = True
        self.finer_sampling = False
        self.rebuild_res = 0
        self.scoring_file = ''
        self.cluster_RMSD = 0.3
        self.is_append = True
        self.constrain_chi = True
        self.native_screen_RMSD = 3.0
        self.num_pose_kept = 100
        self.num_pose_kept_cluster = 10
        self.rebuild_res_list = []


    def read_cmdline_full( self, argv ) :
        #General options
        self.input_pdb = parse_options( argv, 'pdb', '' )
        self.map_file = parse_options( argv, 'map', '' )
        self.out_pdb = parse_options( argv, 'out_pdb', '' )
        self.out_prefix = parse_options( argv, 'out_prefix', '' )
        self.map_reso = parse_options( argv, 'map_reso', 2.5 )
        self.debug = parse_options( argv, "debug", "False" )
        self.verbose = parse_options( argv, "verbose", "False" )
        self.kept_temp_folder = parse_options( argv, "kept_temp_folder", "False" )
        self.use_existing_temp_folder = parse_options( argv, "use_existing_temp_folder", "True" )
        self.new_torsional_potential = parse_options( argv, "new_torsional_potential", "True" )
        self.rosetta_folder = parse_options( argv, 'rosetta_folder', '')

        #erraser options
        self.n_iterate = parse_options( argv, 'n_iterate', 1 )
        self.rebuild_rmsd = parse_options( argv, "rebuild_rmsd", "True" )
        self.rebuild_all = parse_options( argv, "rebuild_all", "False" )
        self.fixed_res = parse_option_chain_res_list ( argv, 'fixed_res' )
        self.cutpoint = parse_option_chain_res_list ( argv, 'cutpoint' )
        self.extra_res = parse_option_chain_res_list ( argv, 'rebuild_extra_res' )
        self.fixed_res_rs = parse_option_int_list ( argv, 'fixed_res_rs' )
        self.cutpoint_rs = parse_option_int_list ( argv, 'cutpoint_rs' )
        self.rebuild_res_pdb = parse_options( argv, "rebuild_res_pdb", '' )

        #Minimize
        self.vary_geometry = parse_options( argv, "vary_geometry", "True" )
        self.constrain_phosphate = parse_options( argv, "constrain_phosphate", "True" )
        self.res_slice = parse_option_int_list ( argv, 'res_slice' )

        #SWA rebuilding
        self.native_screen_RMSD = parse_options( argv, "native_screen_RMSD", 3.0 )
        self.native_edensity_cutoff = parse_options(argv, "native_edensity_cutoff", 0.8)
        self.use_native_edensity_cutoff = parse_options(argv, "use_native_edensity_cutoff", "False")
        self.ideal_geometry =  parse_options( argv, "ideal_geometry", "True" )
        self.include_native =  parse_options( argv, "include_native", "False" )
        self.slice_nearby =  parse_options( argv, "slice_nearby", "True" )
        self.finer_sampling = parse_options( argv, 'finer_sampling', 'False' )
        self.rebuild_res = parse_options( argv, "rebuild_res", 0 )
        self.scoring_file = parse_options( argv, "scoring_file", "" )
        self.cluster_RMSD = parse_options( argv, "cluster_RMSD", 0.3 )
        self.is_append = parse_options( argv, "is_append", "True" )
        self.constrain_chi = parse_options( argv, "constrain_chi", "True" )
        self.native_screen_RMSD = parse_options( argv, "native_screen_RMSD", 3.0 )
        self.num_pose_kept =  parse_options( argv, "num_pose_kept", 100 )
        self.num_pose_kept_cluster =  parse_options( argv, "num_pose_kept_cluster", 10 )
        self.rebuild_res_list = parse_option_int_list ( argv, 'rebuild_res_list' )
        self.finalize()

    def read_cmdline_erraser( self, argv ) :
        #General options
        self.input_pdb = parse_options( argv, 'pdb', '' )
        self.map_file = parse_options( argv, 'map', '' )
        self.out_pdb = parse_options( argv, 'out_pdb', '' )
        self.map_reso = parse_options( argv, 'map_reso', 2.5 )
        self.debug = parse_options( argv, "debug", "False" )
        self.rosetta_folder = parse_options( argv, 'rosetta_folder', '')

        #erraser options
        self.n_iterate = parse_options( argv, 'n_iterate', 1 )
        self.rebuild_all = parse_options( argv, "rebuild_all", "False" )
        self.fixed_res = parse_option_chain_res_list ( argv, 'fixed_res' )

        #SWA rebuilding
        self.native_screen_RMSD = parse_options( argv, "native_screen_RMSD", 3.0 )
        self.constrain_chi = parse_options( argv, "constrain_chi", "True" )
        self.finalize()

    def finalize( self ) :
        if self.input_pdb == '' :
            error_exit( 'input_pdb not specified for erraser_option!!!' )
        check_path_exist( self.input_pdb )
        self.input_pdb = abspath( self.input_pdb )

        if self.out_pdb == "" :
            self.out_pdb = basename( self.input_pdb ).replace('.pdb', '_erraser.pdb')
        self.out_pdb = abspath( self.out_pdb )
        if exists(self.out_pdb) :
            print "Output pdb file %s exists... Remove it..." % self.out_pdb
            remove(self.out_pdb)

        if self.map_file != "" :
            check_path_exist( self.map_file )
            self.map_file = abspath( self.map_file )

        if self.debug :
            self.verbose = True
            self.kept_temp_folder = True
            if self.num_pose_kept_cluster < 10 :
                self.num_pose_kept_cluster = 10

        if not self.use_native_edensity_cutoff :
            self.native_edensity_cutoff = -1

