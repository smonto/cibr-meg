function saved=save_ROI_annotation(ROI)

ct.numEntries = ROI.nROI;
ct.orig_tab = 'even_cubic';
ct.struct_names=ROI.labels;

% create a max-sparse parcel color grid in RGB space:
n_div=floor(ROI.nROI^(1/3)); % how many points on every direction
[X,Y,Z]=meshgrid([0:round(255/n_div):255 255]); % include edges
ct.table=[X(:) Y(:) Z(:)];
ct.table(:,4)=0;
ct.table(:,5)=ct.table(:,1)+ct.table(:,2)*2^8+ct.table(:,3)*2^16;
ct.table=ct.table(1:ROI.nROI,:);

% deal annotation values to vertex labels
verts=zeros(sum(ROI.n_sources),1);
for nn=1:ROI.nROI
    verts(ROI.ROIs{nn})=ct.table(nn,5);
end

write_annotation([ROI.name '.annot'],0:sum(ROI.n_sources)-1,verts,ct)

saved=1;
end