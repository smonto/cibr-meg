function ROI=FS_annotation_to_ROI(parc, fwd_op, label_path)
% ROI=FS_annotation_to_ROI(parcellation, forward_op_file, path_to_FS_labels)
% 
% Transforms the cortical parcellation data
% obtained from FreeSurfer to ROI Matlab custom format
% and saves it to ./ROI_FS.mat
% often, parc='aparc.a2005s' or 'aparc' or 'aparc.a2009s' or 'StrictlyLobes'
% forward_op_file is the fif-format forward operator
% label_path is the path to FreeSurfer's label-directory

ROI.forw_file=fwd_op;

F=mne_read_forward_solution(ROI.forw_file,1);
ROI.n_sources=[F.src(1).nuse;F.src(2).nuse];
ROI.surf_ids={[int2str(F.src(1).id) ':' int2str(F.src(1).np)];
    [int2str(F.src(2).id) ':' int2str(F.src(2).np)]}; % ROIs in node indexing

[vert,label,ct]=read_cortical_annotation(label_path,parc);
for kk=1:length(ct.table)
    ROI.surf_ROIs{kk}=vert(label==ct.table(kk,5));
end
ROI.nROI=length(ROI.surf_ROIs);
ROI.colors=ct.table(:,1:3);
ROI.labels=ct.struct_names;
ROI.method=['FreeSurfer' int2str(ROI.nROI) '_' parc];

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

save('ROI_FS.mat','ROI');

end