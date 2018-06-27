#!/bin/bash

for k in *_raw.fif
do
echo "MaxFiltering $k..."
nice /neuro/bin/util/maxfilter-3.0 -v -f $k -autobad on -origin fit -hpicons -st -movecomp inter -ds 3 -force > "MF_log_$k.txt"
done
mkdir logs
mv MF_log_*.txt logs/
echo "MaxFiltering log outputs saved to logs/"

