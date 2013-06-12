#!/usr/bin/perl

# init
if ($#ARGV < 1) {
    print STDERR "usage: $0 <pdb> <chain>\n";
    print STDERR "removes all ATOM entries with the selected chain\n";
    exit -1;
}
$rosetta_pdb = shift @ARGV;
$chain = shift @ARGV;
$chain = ($chain eq '_') ? ' ' : uc $chain;

if (! -f $rosetta_pdb) {
    print STDERR "$0: filenotfound: $rosetta_pdb\n";
    exit -1;
}
@pdb_buf = &fileBufArray ($rosetta_pdb);


# body
for ($i=0; $i <= $#pdb_buf; ++$i) {
    if ($pdb_buf[$i] =~ /^ATOM|^HETATM/) {
#	print substr ($pdb_buf[$i], 21, 1),$chain;
	if (! (substr ($pdb_buf[$i], 21, 1) eq $chain)) {
          print $pdb_buf[$i] , "\n";
	}
    }
    else {
	print $pdb_buf[$i] , "\n";
    }
}

exit 0;


###############################################################################
# util
###############################################################################

# fileBufString()
#
sub fileBufString {
    local $file = shift;
    local $oldsep = $/;
    undef $/;
    if (! open (FILE, $file)) {
        &abort ("$0: unable to open file $file for reading");
    }
    local $buf = <FILE>;
    close (FILE);
    $/ = $oldsep;
    return $buf;
}

# fileBufArray()
#
sub fileBufArray {
    local $file = shift;
    local $oldsep = $/;
    undef $/;
    if (! open (FILE, $file)) {
        &abort ("$0: unable to open file $file for reading");
    }
    local $buf = <FILE>;
    close (FILE);
    $/ = $oldsep;
    @buf = split (/$oldsep/, $buf);
    pop (@buf)  if ($buf[$#buf] eq '');
    return @buf;
}

###############################################################################
# end
###############################################################################
