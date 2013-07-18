#!/bin/zsh

# Handy shortcuts for working with antibodies, antibody repertoires, and cluster job evaluation

#alias calcdecoytime='grep attempted out | awk "{j+=\$10;n+=\$6;print n,\$10, j, j/n;}"'
function calcdecoytime(){
	grep attempted $@ | awk "{j+=\$10;n+=\$6;print n,\$10, j, j/n;}"
}

# note: ${1+$1/} expands to $1/ if $1 exists, otherwise empty.  allows a directory prefix or not
function lastpdb() {
	for d in ${1+$1/}*/pdbs; do echo -n $d/; 'ls' $d | tail -1; done
}

## loop statistics from grafting output.
# first argument is repertoire directory (default: ./)
# second argument is loop (default:He)
function looplengths() {
	for f in ${1+$1/}*/grafting/details/${2:-H3}.fasta; do echo -n $f\ ;tail -1 $f | wc | awk {'print $3-1'} ; done
}

function looplist() {
	for f in ${1+$1/}*/grafting/details/${2:-H3}.fasta; do echo -n $f\ ;tail -1 $f; done
}

function looplengthshist() {
	for f in ${1+$1/}*/grafting/details/${2:-H3}.fasta; do tail -1 $f | wc | awk {'print $3-1'} ; done | sort -n | uniq -c
}

# output files with histograms of all loop lengths
looplengthshist.all() {
	loops="L1 L2 L3 H1 H2 H3"
	for loop in $loops
	do
		echo $loop:
		looplengthshist ${1:-.} $loop > hist-$loop
		cat hist-$loop
	done
}

function H3lengths()     { looplengths     ${1:-.} H3 }
function H3list()        { looplist        ${1:-.} H3 }
function H3lengthshist() { looplengthshist ${1:-.} H3 }

function Abjobtime() {
	for d in ${1+$1/}*/outerr
	do
		dirn=`dirname $d`
		H3length=$(tail -1 $d/../grafting/details/H3.fasta | wc | awk {'print $3-1'})
		#mins=$(grep real $d/*err | cut -d'm' -f1 | cut -f2 | awk '{sum+=$1} END {print sum}')
		elapsed=$(grep elapsed $d/*err | cut -d' ' -f3 )
		timeout=$(cat $d/*err | grep -c -i 'time limit')
		#echo $dirn: H3 $H3length residues, $mins minutes + $timeout timeouts
		echo $dirn: H3 $H3length residues, $elapsed + $timeout timeouts
	done
	echo
	grep 'SBATCH -t' ${1+$1/}abH3.sbatch
}


function pp_H3 () {
	# postprocess one H3 modeling run
	ab=$(basename $PWD)
	# sort score file by score and chainbreak
	head -2 remodel_h3.fasc | tail -1 > remodel_h3.fasc.sort
	sort -n -k  2 remodel_h3.fasc |grep -vE 'SEQUENCE|H1_RMS' >> remodel_h3.fasc.sort
	head -2 remodel_h3.fasc | tail -1 > remodel_h3.fasc.chainbreak
	sort -n -k 11 remodel_h3.fasc |grep -vE 'SEQUENCE|H1_RMS' >> remodel_h3.fasc.chainbreak

	# find filenames
	filenamecol=$(findColumn.pl description remodel_h3.fasc.sort | awk '{print $4}')
	(( filenamecol ++ ))

	head     remodel_h3.fasc.sort | awk '{print $1, $2, $'$filenamecol'}' > top10.scores
	head -11 remodel_h3.fasc.sort | tail | awk '{print $'$filenamecol'}' > top10.models
	head -11 remodel_h3.fasc.sort > remodel_h3.fasc.sort.top10

	mkdir top10
	i=0;for d in `tail -10 top10.models`; do ; (( i += 1 )) ;  ln -s ../pdbs/$d.pdb.gz top10/$ab-m$i.pdb.gz; done
	#scp -r top10 jeff@$SSH_CLIENT_IP:$(basename $PWD)
}


pp_H3_set () {
	if [ -z "$1" ]
	then
		echo Usage: $0 repertoire_directory
		echo Post-processes the repertoire by sorting Abs by score and extracting the top10
		return
	fi
	owd=$PWD
	cd $1
	for d in *(/)
	do
		if [ -d "$d" ]
		then
			echo -n "Antibody $d..."
			cd $d
			pp_H3
			echo done
			cd ../
		fi
	done
	cd $owd
}


pp_zip_set () {
	if [ -z "$1" ]
	then
		echo Usage: $0 repertoire_directory
		echo Zip the top structures, fastas, and grafting log
		return
	fi
	#tar -cvzhf $1-top.tgz $1/*/top10 $1/*/*fasc* $1/*/top10* $1/*/*fasta $1/*/grafting.log
	tar -cvzhf $1-top.tgz $1/*/top10 $1/*/*fasc* $1/*/top10* $1/*/*constr* $1/*/*pdb $1/abH3*
}

pp_kink_testset() {
	if [ -z "$1" ]
	then
		echo Usage: $0 repertoire_directory
		echo Post-processes for kink plots
		return
	fi
	owd=$PWD
	cd $1
	for d in *(/)
	do
		if [ -d "$d" ]
		then
			echo "Antibody $d..."
			cd $d
			kink_geom.py LH_renumbered.pdb
			head -11 remodel_h3.fasc.sort > remodel_h3.fasc.sort.top10
			echo done
			cd ../
		fi
	done
	cd $owd
}

