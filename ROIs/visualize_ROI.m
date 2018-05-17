function [p,verts_l,verts_r,faces_l,faces_r,cdata_l,cdata_r,curvs_l,curvs_r,ROI]=visualize_ROI(ROI_path,smooth_rounds,varargin)
% p=visualize_ROI(ROI_path,smooth_rounds,varargin)
%
% p is handle to the figure
%
% ROI_path is a path to a ROI .mat-file
% subj_id is the ID of the subject used in anatomical data organization
% smooth_rounds is the number of smoothing rounds for the data
% varargin may include ROI indices to visualize
%
% NOTE: you need to have MNE environment to set up!

surf_type='inflated';%'pial'
R=load(ROI_path);
ROI=R.ROI;
forw_ops=ROI.forw_path;
[FSpath,FSdir]=fileparts(ROI.FS_dir);
FSpath=[FSpath '/'];
subj_id=FSdir;

src=mne_read_source_spaces(forw_ops,0);
surfs=mne_read_surfaces('inflated',1,1,1,FSdir,FSpath,0);
curvs_l=surfs(1).curv;
curvs_r=surfs(2).curv;

if ~isempty(varargin)
    ROI_ind=varargin{1};
else
    ROI_ind=1:ROI.nROI;
end

if ~isfield(ROI,'surf_ROIs')
    D=smooth_ROI(ROI_path,smooth_rounds,ROI_ind);
else
    D=zeros(src(1).np+src(2).np,1);
    for kk=ROI_ind
        D(ROI.surf_ROIs{kk})=kk;
    end
end

if size(D,1)<size(D,2)
    D=D.';
end
size(D)
cdata_l=D(1:src(1).np,:);
cdata_r=D(1+src(1).np:end,:);
[verts_l,faces_l]=mne_read_surface([FSpath subj_id '/surf/lh.' surf_type]);
[verts_r,faces_r]=mne_read_surface([FSpath subj_id '/surf/rh.' surf_type]);
p(1)=do_SurfPlot(faces_l,verts_l,(D(1:src(1).np)),1);
title([ROI_path ', left, ' int2str(smooth_rounds)]);
p(2)=do_SurfPlot(faces_r,verts_r,(D(1+src(1).np:end)),1);
title([ROI_path ', right, ' int2str(smooth_rounds)]);
for kk=ROI_ind
    ROI.surf_ROIs{kk}=find(D==kk);
end
end