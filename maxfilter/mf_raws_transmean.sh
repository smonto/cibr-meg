#!/bin/bash
#
# This script performs Maxfiltering for files with given id in the project folder.
# Head position is transformed to the mean of all found files.
# The head positions description file is /projects/${project}/maxfiltered/${id}/mean-trans.fif
# NOTE! replace "id" and "project" with correct names!
# NOTE! edit the MaxFilter command according to need

id="subject_code"
project="project_folder_name"
combined_file_name="dummy.fif"
file_list=($(find /projects/${project}/orig/ -iname "*${id}*.fif"))
echo "Found these files:"
printf '%s\n' "${file_list[@]}"

# STEP1: run maxfilter with -headpos to get .pos head position files
for RAWFILE in ${file_list[@]}
    do
        echo "Finding head movements in $RAWFILE..."
        mkdir -p /projects/${project}/maxfiltered/${id}
        NOPATH=$(basename $RAWFILE)
        OUTNAME=${NOPATH%%.fif}
        nice /neuro/bin/util/maxfilter-3.0 -hp -headpos -frame head -o /projects/${project}/maxfiltered/${id}/${OUTNAME}_tsss_quat.fif -f $RAWFILE -autobad on -origin fit -hpicons -st -force | tee /projects/${project}/maxfiltered/logs/${OUTNAME}_quat.log
    done

# STEP2: run mean_meg2head to obtain mean head position over runs
/opt/anaconda/bin/python /opt/tools/cibr-meg/maxfilter/mean_meg2head_trans.py /projects/${project}/maxfiltered/${id}

# STEP3: run MaxFilter to clean data and transform to mean head position
mkdir -p /projects/${project}/maxfiltered/logs
n=0
for RAWFILE in ${file_list[@]}
    do
        echo "MaxFiltering $RAWFILE..."
        NOPATH=$(basename $RAWFILE)
        OUTNAME=${NOPATH%%.fif}
        nice /neuro/bin/util/maxfilter-3.0 -movecomp inter -autobad on -frame head -o /projects/${project}/maxfiltered/${id}/${OUTNAME}_tsss_mc.fif -trans /projects/${project}/maxfiltered/${id}/mean-trans.fif -f $RAWFILE -origin fit -hpicons -st -ds 4 -force | tee /projects/${project}/maxfiltered/logs/${OUTNAME}.log
        #mf_list[n]=/projects/${project}/maxfiltered/${id}/${OUTNAME}_tsss_mc.fif
        n=n+1
    done
echo "Maxfiltering ready!"

# STEP4: combine resulting Maxfiltered files
#/opt/anaconda/bin/python /opt/tools/cibr-meg/combine_fifs.py combined_file_name "${mf_list[*]}"
