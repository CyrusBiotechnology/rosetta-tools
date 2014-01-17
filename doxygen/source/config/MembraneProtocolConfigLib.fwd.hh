// -*- mode:c++;tab-width:2;indent-tabs-mode:t;show-trailing-whitespace:t;rm-trailing-spaces:t -*-
// vi: set ts=2 noet:
//
// (c) Copyright Rosetta Commons Member Institutions.
// (c) This file is part of the Rosetta software suite and is made available under license.
// (c) The Rosetta software is developed by the contributing members of the Rosetta Commons.
// (c) For more information, see http://www.rosettacommons.org. Questions about this can be
// (c) addressed to University of Washington UW TechTransfer, email: license@u.washington.edu.

/// @file MembraneProtocolConfigLib.fwd.hh
///
/// @brief Stores membrane specific protocol changes
/// @detail Stores option changes, weights patches, and apply changes for specific protocols
///         that are now membrane compatible
///
/// @author Rebecca Alford

#ifndef INCLUDED_core_membrane_config_MembraneProtocolConfigLib_fwd_hh
#define INCLUDED_core_membrane_config_MembraneProtocolConfigLib_fwd_hh

// Utility Headers
#include <utility/pointer/owning_ptr.hh>

namespace core {
namespace membrane {
namespace config {

/// @brief Membrane Library Class
class MembraneProtocolConfigLib;
typedef utility::pointer::owning_ptr< MembraneProtocolConfigLib > MembraneProtocolConfigLibOP;

} // config
} // membrane
} // core

#endif INCLUDED_core_membrane_config_MembraneProtocolConfigLib_fwd_hh