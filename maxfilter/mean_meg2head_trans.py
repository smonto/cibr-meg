'''
Plotting head movement and computing the average
head position transform over several .pos-files.
Saves a new device->head transformation.
User specifies the working directory as an argument --
the script will loop over all the .pos files in that directory.

sipemont 180404
'''

import mne
import numpy as np
import matplotlib.pyplot as plt
import glob, os, sys
from scipy.stats import circmean

# USER DEFINES UPON SCRIPT CALL:
try:
    print("Working directory is " + sys.argv[1])
    basepath=sys.argv[1]
except (NameError, IndexError):
    print('Give the working directory as the argument!')
    raise

startpath=os.path.abspath(os.curdir)

def rotangles(T):
    # find Euler angles as written by Samu Taulu
    # T is the rotation matrix
    beta = -np.arcsin(T[2,0])
    cosb = np.cos(beta)
    alpha = np.arcsin(T[2,1]/cosb)
    gamma = np.arccos(T[0,0]/cosb)
    angles = [alpha, beta, gamma]
    return angles

def euler2rotmat(angles):
    # turn Euler rotation angles to rotation matrix
    # angles is [alpha, beta, gamma]
    rot=[[np.cos(angles[1])*np.cos(angles[2]),
        -np.cos(angles[0])*np.sin(angles[2]) + np.sin(angles[0])*np.sin(angles[1])*np.cos(angles[2]),
        np.sin(angles[0])*np.sin(angles[2]) + np.cos(angles[0])*np.sin(angles[1])*np.cos(angles[2])],
        [np.cos(angles[1])*np.sin(angles[2]),
        np.cos(angles[0])*np.cos(angles[2]) + np.sin(angles[0])*np.sin(angles[1])*np.sin(angles[2]),
        -np.sin(angles[0])*np.cos(angles[2]) + np.cos(angles[0])*np.sin(angles[1])*np.sin(angles[2])],
        [-np.sin(angles[1]),
        np.sin(angles[0])*np.cos(angles[1]),
        np.cos(angles[0])*np.cos(angles[1])]]
    return rot # size 3x3 rotation matrix

# list all head position files and loop over
os.chdir(basepath)
pos_files=glob.glob('*.pos')
HP=np.zeros((0,3)) # stores the (x,y,z) of head origin for plotting
net_trans=np.zeros((0,3)) # for storing the device->head translations
net_rot=np.zeros((0,3,3)) # for storing the device->head rotations

for pos_file in pos_files:
    print("File: " + pos_file)
    quats=mne.chpi.read_head_pos(pos_file) # load head positions from ASCII file
    trans, rot, t = mne.chpi.head_pos_to_trans_rot_t(quats) # convert quaternions
    net_trans=np.concatenate((net_trans,trans),axis=0) # add movement in this file
    net_rot=np.concatenate((net_rot,rot),axis=0) # add rotation in this file
    hp=np.zeros(trans.shape) # initialize head origin location
    # compute head origin position in device coordinates in every time point:
    for k in range(trans.shape[0]):
        hp[k]=np.matmul(-rot[k,:,:].T, trans[k,:])
    HP=np.concatenate((HP,hp),axis=0)

plt.figure()
plt.suptitle('Head movement over all files (in mm in x, y, z)')
for subplt in range(3):
    plt.subplot(3,1,subplt+1)
    plt.plot(1000*HP[:,subplt])
plt.show()

print('Saving the mean transformation to file ' + basepath + '/mean-trans.fif...\n')
mean_tr=np.diagflat(np.ones(4)) # initialize device->head transformation matrix
mean_tr[0:3,3]=net_trans.mean(axis=0)  # set the translation part to the mean
rots=np.zeros((net_rot.shape[0],3))
for tind in range(net_rot.shape[0]):
    rots[tind,:]=rotangles(net_rot[tind,:,:]) # turn rotation matrices to Euler angles
m_rot=circmean(rots,axis=0) # set mean rotations to circular mean of all rotations
mean_tr[0:3,0:3]=euler2rotmat(m_rot) # set the rotation part of the transform matrix
A=mne.Transform('meg','head',mean_tr)
mne.write_trans('mean-trans.fif',A)
print('Done!')

print('Mean head position over following files: \n')
print(pos_files)
print('\nis\n')
print(1000*mean_tr[0:3,3])

os.chdir(startpath)
