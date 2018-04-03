'''
Plotting head movement and computing the average head position over files
Saves a device->head transformation using average quaternion transform

sipemont 180320
'''

import mne
import numpy as np
import matplotlib.pyplot as plt
import glob, os

# USER DEFINED:
basepath='/home/sipemont/data/tmp/'
#--------------

# list all head position files and loop over
os.chdir(basepath)
pos_files=glob.glob('*.pos')
HP=np.array([]).reshape(0,3) # for storing the (x,y,z) of head origin
#net_trans=np.array([]).reshape(0,3) # for storing the device->head translations
#net_rot=np.zeros((0,3,3)) # for storing the device->head rotations
mean_pos=np.zeros((0,10)) # for storing the mean transformation

for pos_file in pos_files:
    pos=mne.chpi.read_head_pos(pos_file) # load head positions from ASCII file
    mean_pos=np.mean(pos,axis=0) # mean quaternion transformation for this file
    m_trans, m_rot, m_t = mne.chpi.head_pos_to_trans_rot_t(mean_pos) # convert mean quaternion
    trans, rot, t = mne.chpi.head_pos_to_trans_rot_t(pos) # convert quaternions
    hp=np.zeros(trans.shape) # initialize to correct size
    # compute head origin position in device coordinates in every time point:
    for k in range(trans.shape[0]):
        hp[k]=np.matmul(-rot[k,:,:].T, trans[k,:])
    HP=np.concatenate((HP,hp),axis=0)
    #net_trans=np.concatenate((net_trans,trans),axis=0)
    #net_rot=np.concatenate((net_rot,rot),axis=0)

plt.figure()
plt.title('Head movement over all files (in mm)')
for subplt in range(3):
    plt.subplot(3,1,subplt+1)
    plt.plot(1000*HP[:,subplt])
plt.show()

print('Mean head position over following files: \n')
print(pos_files)
print('\nis\n')
print(1000*HP.mean(axis=0))

print('Saving the mean transformation to file ' + basepath + 'mean-trans.fif...\n')
mean_tr=np.diagflat(np.ones(4))
#mean_tr[0:3,3]=net_trans.mean(axis=0)
mean_tr[0:3,3]=m_trans
mean_tr[0:3,0:3]=m_rot
A=mne.Transform('meg','head',mean_tr)
mne.write_trans('mean-trans.fif',A)
print('Done!')
