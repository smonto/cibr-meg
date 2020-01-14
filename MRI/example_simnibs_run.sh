#!/bin/bash
#SUBJECT=$1
#INPUTFILE=$2
SUBJECT='cibr_test_adult1'
INPUTFILE='/opt/freesurfer/subjects/cibr_test_adult1/mri/T1.mgz'

export SIMNIBSDIR=/opt/simnibs-2.1.2-Linux64/
source $SIMNIBSDIR/simnibs_conf.sh

#cd /projects/myproject/

headreco preparevols --cat_no_print --cat ${SUBJECT} ${INPUTFILE}
headreco preparecat --cat ${SUBJECT}
# headreco check ${SUBJECT}
headreco cleanvols --cat ${SUBJECT}
headreco surfacemesh --cat ${SUBJECT}
cd m2m_${SUBJECT} && mkdir -p fsmesh

# generate MNE-friendly BEM surfaces
meshfix skin.stl -u 10 --vertices 5120 --fsmesh -o fsmesh/outer_skin
mris_transform --dst ref_FS.nii.gz --src ref_FS.nii.gz fsmesh/outer_skin.fsmesh unity.xfm outer_skin.surf
mv fsmesh/rh.outer_skin.surf fsmesh/outer_skin.surf

meshfix bone.stl -u 10 --vertices 5120 --fsmesh -o fsmesh/outer_skull
mris_transform --dst ref_FS.nii.gz --src ref_FS.nii.gz fsmesh/outer_skull.fsmesh unity.xfm outer_skull.surf
mv fsmesh/rh.outer_skull.surf fsmesh/outer_skull.surf

meshfix csf.stl -u 10 --vertices 5120 --fsmesh -o fsmesh/inner_skull
mris_transform --dst ref_FS.nii.gz --src ref_FS.nii.gz fsmesh/inner_skull.fsmesh unity.xfm inner_skull.surf
mv fsmesh/rh.inner_skull.surf fsmesh/inner_skull.surf
