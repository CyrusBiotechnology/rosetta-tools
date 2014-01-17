// -*- mode:c++;tab-width:2;indent-tabs-mode:t;show-trailing-whitespace:t;rm-trailing-spaces:t -*-
// vi: set ts=2 noet:
//
// (c) Copyright Rosetta Commons Member Institutions.
// (c) This file is part of the Rosetta software suite and is made available under license.
// (c) The Rosetta software is developed by the contributing members of the Rosetta Commons.
// (c) For more information, see http://www.rosettacommons.org. Questions about this can be
// (c) addressed to University of Washington UW TechTransfer, email: license@u.washington.edu.

/// @file 		core/membrane/geometry/util.cc
///
/// @brief 		Utility methods for defining membranes and membrane embeddings
/// @detailed 	Helps to check for internal errors, bounds, and object equality
///
/// @author		Rebecca Alford (rfalford12@gmail.com)

#ifndef INCLUDED_core_membrane_geometry_util_cc
#define INCLUDED_core_membrane_geometry_util_cc

// Unit Headers
#include <core/membrane/geometry/util.hh>

// Project Headers
#include <core/membrane/properties/SpanningTopology.hh>
#include <core/membrane/util/Exceptions.hh>

// Package Headers
#include <core/conformation/Residue.hh>
#include <core/conformation/ResidueFactory.hh>

#include <core/chemical/ResidueTypeSet.hh>
#include <core/chemical/ChemicalManager.hh>

#include <basic/resource_manager/ResourceManager.hh>
#include <basic/resource_manager/util.hh>

#include <core/pose/Pose.hh>
#include <core/types.hh>

// Utility Headers
#include <utility/pointer/ReferenceCount.hh>
#include <utility/tag/Tag.hh>

#include <basic/Tracer.hh>

// C++ Headers
#include <algorithm>
#include <string>
#include <cstdlib>
#include <cmath>

static basic::Tracer TR("core.membrane.geometry.util");

using basic::Error;
using basic::Warning;

using namespace core::membrane::properties;

namespace core {
namespace membrane {
namespace geometry {

    /// @brief      Virtual residue Equals
    /// @details    Custom equality method - Checks two virtual atoms are equal in typesets
    ///             and cartesian coordinates
    ///
    /// Precondition: (Checked) Both residues are virtual residues
    ///
    /// @param 	rsd1
    ///				first atom to investigate
    /// @param 	rsd2
    ///				second residue to investigate
    /// @param fullatom
    ///				specifies if the atom typesef of the pose is fullatom
    ///
    ///	@return	bool
    bool virtual_rsd_equal( core::conformation::ResidueOP rsd1, core::conformation::ResidueOP rsd2 ) {

        // The first two conditions check that each residue is a virtual residue
        // which allows us to surpass additiona typeset checking. These are fatal cases
        // indicating misuse of the method and will cause Rosetta to fail.

        // Check that the first residue is virtual
        if ( rsd1->aa() != core::chemical::aa_vrt ) { return false; }
        if ( rsd2->aa() != core::chemical::aa_vrt ) { return false; }

        // Checks virtual atom coordinates are equal
        if ( rsd1->atom(2).xyz().x() != rsd2->atom(2).xyz().x() ) { return false; }
        if ( rsd1->atom(2).xyz().y() != rsd2->atom(2).xyz().y() ) { return false; }
        if ( rsd1->atom(2).xyz().z() != rsd2->atom(2).xyz().z() ) { return false; }
        
        // All of the conditions have been met!
        return true;
    }

    /// @brief      Get Residue Depth in Membrane
    /// @details    Calculate the depth of a residue with respect to membrane players
    ///
    /// @param  normal
    /// @param center
    core::Real get_mpDepth( core::Vector normal, core::Vector center, core::conformation::Residue rsd ) {
        
        // Get membrane xyz
        Vector const & xyz( rsd.atom( 2 ).xyz() );
        core::Real depth = dot( xyz-center, normal )+30;
        return depth;
    }
    
    /// @brief Check Membrane Spanning
    /// @details Check that caucluated membrane spanning respects new
    ///          normal and center definitions
    ///
    /// @throws <none>
	bool
    check_spanning(
                   core::pose::Pose const & pose,
                   core::Vector const & normal,
                   core::Vector const & center,
                   SpanningTopologyOP topology
                   ) {
        
        // Loop Through the Pose
        for( Size i = 1; i <= topology->total_tmhelix()-1 ; ++i ) {
            
            // If scoring allowed at position, continue
            if ( ! topology->allow_tmh_scoring()[i] ) continue;
            
            Vector const & start_i( pose.residue( topology->span()(i, 1) ).atom( 2 ).xyz());
            bool start_i_side=(dot(start_i-center,normal) > 0);
            bool span_check=false;
            
            // Loop through iteratively
            for( Size j = i+1; j <= topology->total_tmhelix(); ++j) {
                
                // Check scoring is allowed at given position
                if( !topology->allow_tmh_scoring()[j] || span_check ) continue;
                span_check=true;
                
                Vector const & start_j( pose.residue( topology->span()(j, 2) ).atom( 2 ).xyz());
                bool start_j_side=(dot(start_j-center,normal) > 0);
                bool coord_para=(start_i_side==start_j_side);
                
                if ( topology->helix_id()[i]-topology->helix_id()[i] % 2 == 0 ) {
                    
                    if(!(coord_para)) { return false; }
                    
                } else {
                    
                    if(coord_para) { return false; }
                }
            }
        }
        return true;
    }
    
} // geometry
} // membrane
} // core

#endif // INCLUDED_core_membrane_geometry_util_cc

