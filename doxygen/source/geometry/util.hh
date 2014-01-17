// -*- mode:c++;tab-width:2;indent-tabs-mode:t;show-trailing-whitespace:t;rm-trailing-spaces:t -*-
// vi: set ts=2 noet:
//
// (c) Copyright Rosetta Commons Member Institutions.
// (c) This file is part of the Rosetta software suite and is made available under license.
// (c) The Rosetta software is developed by the contributing members of the Rosetta Commons.
// (c) For more information, see http://www.rosettacommons.org. Questions about this can be
// (c) addressed to University of Washington UW TechTransfer, email: license@u.washington.edu.

/// @file 		core/membrane/geometry/util.hh
///
/// @brief 		Utility methods for defining membranes and membrane embeddings
/// @detailed 	Helps to check for internal errors, bounds, and object equality
///
/// @author		Rebecca Alford (rfalford12@gmail.com)

#ifndef INCLUDED_core_membrane_geometry_util_hh
#define INCLUDED_core_membrane_geometry_util_hh

// Project Headers
#include <core/membrane/properties/SpanningTopology.hh>

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

// C++ Headers
#include <algorithm>
#include <string>
#include <cstdlib>
#include <cmath>

using namespace core::membrane::properties;

namespace core {
namespace membrane {
namespace geometry {

    /// @brief	Virtual residue Equals
    /// @detail Custom equality method - Checks two virtual atoms are equal in typesets
    ///			and cartesian coordinates
    ///
    /// @param 	rsd1
    ///				first atom to investigate
    /// @param 	rsd2
    ///				second residue to investigate
    ///
    ///	@return	bool
    bool virtual_rsd_equal( core::conformation::ResidueOP rsd1, core::conformation::ResidueOP rsd2 );
        
    /// @brief      Get Residue Depth in Membrane
    /// @details    Calculate the depth of a residue with respect to membrane players
    ///
    /// @param  normal
    /// @param center
    core::Real get_mpDepth( core::Vector normal, core::Vector center, core::conformation::Residue rsd );
    
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
                   );
    

} // geometry
} // membrane
} // core

#endif // INCLUDED_core_membrane_geometry_util_hh

