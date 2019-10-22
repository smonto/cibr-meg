#!/bin/bash
#
# This script performs Maxfiltering for given subject, with
# head position transformed to the mean over all runs with this id
# NOTE! replace "id" and "project" with correct names!
# NOTE! edit the MaxFilter command according to need

id="elpis15"
project="elpis"
file_list=($(find /projects/${project}/testmf/ -iname "*${id}*.fif"))

# STEP1: run maxfilter -headpos to get .pos files
for RAWFILE in ${file_list[@]}
    do
        echo "Finding head movements in $RAWFILE..."
        mkdir -p /projects/${project}/maxfiltered/${id}
        NOPATH=$(basename $RAWFILE)
        OUTNAME=${NOPATH%%.fif}
        nice /neuro/bin/util/maxfilter-3.0 -headpos -frame head -o /projects/${project}/maxfiltered/${id}/${OUTNAME}_tsss_quat.fif -v -f $RAWFILE -autobad on -origin fit -hpicons -st -force
    done

# STEP2: run mean_meg2head to obtain mean head position over runs
python /opt/tools/cibr-meg/maxfilter/mean_meg2head_trans.py /projects/${project}/maxfiltered/${id}

# STEP3: run MaxFilter to clean data and transform to mean head position
mkdir -p /projects/${project}/maxfiltered/logs
for RAWFILE in ${file_list[@]}
    do
        echo "MaxFiltering $RAWFILE..."
        NOPATH=$(basename $RAWFILE)
        OUTNAME=${NOPATH%%.fif}
        nice /neuro/bin/util/maxfilter-3.0 -movecomp inter -autobad on -frame head -o /projects/${project}/maxfiltered/${id}/${OUTNAME}_tsss_mc.fif -trans /projects/${project}/maxfiltered/${id}/mean-trans.fif -v -f $RAWFILE -origin fit -hpicons -st -ds 4 -force | tee /projects/${project}/maxfiltered/logs/${OUTNAME}.log
    done
echo "Maxfiltering ready!"
