function ROI=FS_parcellation_to_ROI(parc,varargin)
% ROI=FS_parcellation_to_ROI(parc,varargin)
% 
% Transforms the cortical parcellation data
% obtained from FreeSurfer to ROI-data format
% and saves it to current_subject/fs/ROI.mat
% often, parc='aparc.a2005s' or 'aparc' or 'aparc.a2009s' or 'StrictlyLobes'
% varargin=true if want to write to MAIN_DIR

% MNE_ANNOT2LABELS
%parc='aparc.a2005s'
% find the vertices that are in use for the subject (surface data)
global MAIN_DIR SUBJECT_NAME

write=false;
if nargin==2
    write=varargin{1};
end

if isempty(SUBJECT_NAME)
    try
        init_globals
    catch ME
        disp('Uninitialized SUBJECT_NAME!');
        return
    end
end
ROI.forw_file=[MAIN_DIR 'forw_ops/forw_op.fif'];

F=mne_read_forward_solution(ROI.forw_file,1);
ROI.n_sources=[F.src(1).nuse;F.src(2).nuse];
ROI.surf_ids={[int2str(F.src(1).id) ':' int2str(F.src(1).np)];
    [int2str(F.src(2).id) ':' int2str(F.src(2).np)]}; % ROIs in node indexing

[vert,label,ct]=read_cortical_parcellation(SUBJECT_NAME,parc);
for kk=1:length(ct.table)
    ROI.surf_ROIs{kk}=vert(label==ct.table(kk,5));
end
ROI.nROI=length(ROI.surf_ROIs);
ROI.colors=ct.table(:,1:3);
ROI.labels=ct.struct_names;
ROI.method=['FreeSurfer' int2str(ROI.nROI) '_' parc];
ROI.subjname=SUBJECT_NAME;

srcnode=logical([F.src(1).inuse F.src(2).inuse]); % combine source node lists
srcind=[F.src(1).vertno F.src(2).vertno+F.src(1).np]; % combine index lists

for kk=1:ROI.nROI % find the source indices corresponding to node indices
    kkind=ROI.surf_ROIs{kk}(srcnode(ROI.surf_ROIs{kk}));
    nnind=zeros(size(kkind));
    for nn=1:length(kkind)
        nnind(nn)=find(srcind==kkind(nn));
    end
    ROI.ROIs{kk}=nnind.';
    lROIs(kk)=length(nnind);
    lsurfROIs(kk)=length(ROI.surf_ROIs{kk});
end
ROI.sources_in_ROIs=sum(lROIs);
ROI.sources_in_surfROIs=sum(lsurfROIs);
disp(['The ROI parcellation includes ' int2str(sum(lROIs)) ' nodes out of the ' int2str(sum(ROI.n_sources)) ' in the source space!'])

if exist([MAIN_DIR 'fs/'],'dir')
    save([MAIN_DIR 'fs/ROI_' ROI.method '.mat'],'ROI');
else
    mkdir([MAIN_DIR 'fs']);
    save([MAIN_DIR 'fs/ROI_' ROI.method '.mat'],'ROI');
end
if write
    save([MAIN_DIR 'ROI.mat'],'ROI');
end
end