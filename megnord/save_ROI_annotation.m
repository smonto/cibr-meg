function [lh_name,rh_name]=save_ROI_annotation(ROI)

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
if isfield(ROI,'surf_ROIs')
    verts=zeros(sum(ROI.n_vertices),1);
    verts_l=zeros(ROI.n_vertices(1),1);
    verts_r=zeros(ROI.n_vertices(2),1);
    for nn=1:ROI.nROI
        verts(ROI.surf_ROIs{nn})=ct.table(nn,5);
        if any(ROI.surf_ROIs{nn}<ROI.n_vertices(1)) % belongs to lh
            verts_l(ROI.surf_ROIs{nn})=ct.table(nn,5);
        elseif any(ROI.surf_ROIs{nn}>ROI.n_vertices(1)) % belongs to rh
            verts_r(ROI.surf_ROIs{nn}-double(ROI.n_vertices(1)))=ct.table(nn,5);
        end
    end
    lh_name=['lh.' ROI.name '.annot'];
    rh_name=['rh.' ROI.name '.annot'];
    write_annotation(lh_name,0:ROI.n_vertices(1)-1,verts(1:ROI.n_vertices(1)),ct)
    write_annotation(rh_name,0:ROI.n_vertices(2)-1,verts(1+ROI.n_vertices(1):end),ct)
else
    disp('Could not write full surface annotations; writing nodes only.');
    verts=zeros(sum(ROI.n_sources),1);
    for nn=1:ROI.nROI
        verts(ROI.ROIs{nn})=ct.table(nn,5);
    end
    write_annotation([ROI.name '.annot'],0:sum(ROI.n_sources)-1,verts,ct)
end

end