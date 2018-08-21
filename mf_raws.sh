#!/bin/bash

# replace "meg" with project-specific names!

id="01"
file_list=($(find ./ -name "meg${id}*_raw.fif"))
for RAWFILE in ${file_list[@]}
    do
        echo "MaxFiltering $RAWFILE..."
        mkdir -p /projects/meg/maxfiltered/meg${id}
        NOPATH=$(basename $RAWFILE)
        OUTNAME=${NOPATH%%.fif}
        nice /neuro/bin/util/maxfilter-2.2 -movecomp inter -bad $(/neuro/bin/util/xscan -st -corr 0.95 -f $RAWFILE) -frame head -o /projects/meg/maxfiltered/meg${id}/${OUTNAME}_tsss_mc.fif -trans trans_median.fif -v -f $RAWFILE -autobad off -origin $(/neuro/bin/util/fit_sphere_to_isotrak -f $RAWFILE) -hpicons -st -ds 3 -force | tee /projects/meg/logs/${OUTNAME}.log
    done
echo "Maxfiltering ready!"
