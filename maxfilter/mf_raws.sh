#!/bin/bash

# This script runs the same Maxfilter command for all identified files.
# Files are searched according to project name and file name tag.
# Results are written to folder "maxfiltered" and logs to "logs".
# NOTE! replace "id" and "project" with project-specific names!
# NOTE! edit the MaxFilter command options according to need

id="subj01" # identifier for target files
project="meg" # the project name under /projects/ folder
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
