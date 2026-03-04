#!/bin/bash

here=$PWD
# echo "--> Data processing in directory $here"
# echo "---> First round of processing"
function d8_round1() {
	here=$PWD
	for i in run*; do
		cd $i
		xds_par
		cd $here
	done

}
# After round 1, check that integration worked and that unti cell and space
# group number are consistent. If not, append to XDS.INP 'UNIT_CELL_CONSTANTS= ' and 
# 'SPACE_GROUP_NUMBER= ' and repeat with 'JOB= IDXREF'
# once all is fine, continue with round 2
function d8_round2() {
	sed -i "s/^ JOB=.*/ JOB= DEFPIX INTEGRATE CORRECT/" run*/XDS.INP
	for i in run*; do
		cd $i
		mv GXPARM.XDS XPARM.XDS
		xds_par
		cd $here
	done
}

function d8_round3() {
	sed -i "s/^ JOB=.*/ JOB= DEFPIX INTEGRATE CORRECT/" run*/XDS.INP
	for i in run*; do
		cd $i
		grep -A2 SUGG INTEGRATE.LP | tail -n2 >> XDS.INP
		mv GXPARM.XDS XPARM.XDS
		xds_par
		cd $here
	done
}

function my_xds2sad() {
	for i in run*; do
		cd $i
		xds2sad
		cd $here
	done
}

function unit_cell() {
  len=$#
  if [ $len -eq 6 ]; then
    for i in run*; do
      echo " UNIT_CELL_CONSTANTS= $1 $2 $3 $4 $5 $6" >> $i/XDS.INP
    done
  else
    echo "Error: please pass exactly 6 numbers (a b c alpha, beta, gamma) as argument"
  fi
}

function spacegroup() {
  len=$#
  if [ $len -eq 1 ]; then
    for i in run*; do
      echo " SPACE_GROUP_NUMBER= $1" >> $i/XDS.INP
    done
  else
    echo "Error: please pass 1 number (SG number) as argument"
  fi
}


# copy or link xds.sad into sadabs directory
function prep_sadabs() {
 here=$PWD; 
 # for i in run*; do cd $i; xds2sad; cd $here; done
 mkdir sadabs
 cd sadabs
 count=0
 for i in $(find ../ -name xds.sad | sort); do
 	let "count=$count+1"
	ln -s $i run${count}.sad
 done
}


# sequence of commands from above for a all-in-one go
function d8_procall {
  d8_round1 && 
  d8_round2 && 
  d8_round3 && 
  d8_round3 && 
  my_xds2sad && 
  prep_sadabs && 
  weightedcell -w ../run* | tee XSCALE.INP
}

