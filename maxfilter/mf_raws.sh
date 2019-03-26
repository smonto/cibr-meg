#!/bin/bash

# NOTE! replace "id" and "project" with project-specific names!
# NOTE! edit the MaxFilter command according to need

id="01"
project="meg"
file_list=($(find /projects/${project}/orig/ -name "*${id}*.fif"))
for RAWFILE in ${file_list[@]}
    do
        echo "MaxFiltering $RAWFILE..."
        mkdir -p /projects/${project}/maxfiltered/${id}
        NOPATH=$(basename $RAWFILE)
        OUTNAME=${NOPATH%%.fif}
        nice /neuro/bin/util/maxfilter-2.2 -movecomp inter -bad $(/neuro/bin/util/xscan -f $RAWFILE) -frame head -o /projects/${project}/maxfiltered/${id}/${OUTNAME}_tsss_mc.fif -trans trans_median.fif -v -f $RAWFILE -autobad off -origin $(/neuro/bin/util/fit_sphere_to_isotrak -f $RAWFILE) -hpicons -st -ds 3 -force | tee /projects/${project}/logs/${OUTNAME}.log
    done
echo "Maxfiltering ready!"
