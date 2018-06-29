% TODO: make a ROI by (eliminating 'unknown' vertices and) adding to cell list
function [vertices, labels, colortable]=read_cortical_annotation(label_path,annot)
% function [vertices, labels, colortable]=read_cortical_parcellation(path_to_FS_label_dir,annotation_name)
%
% Just combines the data from the two hemisphere-specific runs of 
% read_annotation.m
%

unwanted_structs=[{'Unknown_L'}
    {'Unknown_R'}
    {'Corpus_callosum_L'}
    {'Corpus_callosum_R'}
    {'G_and_S_Insula_ONLY_AVERAGE_L'}
    {'G_and_S_Insula_ONLY_AVERAGE_R'}
    {'Medial_wall_L'}
    {'Medial_wall_R'}];

%apath=['D:\Data\MRI\' subj_id '\label\'];
[lvertices,llabel,colortable]=read_annotation([label_path '/lh.' annot '.annot']);
[rvertices,rlabel,rcolortable]=read_annotation([label_path '/rh.' annot '.annot']);

% change numbering to 1 ... n_vertices
lvertices=lvertices+1;
rvertices=rvertices+1+lvertices(end);
vertices=[lvertices;rvertices];

for kk=1:rcolortable.numEntries
    rcolortable.table(kk,1:3)=rcolortable.table(kk,1:3)+1;
    kk_new=rcolortable.table(kk,1)+rcolortable.table(kk,2)*2^8+rcolortable.table(kk,3)*2^16;
    rlabel(rlabel==rcolortable.table(kk,5))=kk_new;
    rcolortable.table(kk,5)=kk_new;
    colortable.struct_names{kk}=[colortable.struct_names{kk} '_L'];
    rcolortable.struct_names{kk}=[rcolortable.struct_names{kk} '_R'];
end

colortable.table=[colortable.table;rcolortable.table];
colortable.struct_names=[colortable.struct_names;rcolortable.struct_names];

if length(colortable.table)==length(colortable.struct_names)
    colortable.numEntries=length(colortable.struct_names);
else
    disp('Colortable length mismatch!');
    return;
end

if length(unique(colortable.table(:,5)))~=2*kk
    disp('Colortable size mismatch!');
    return;
end

labels=[llabel;rlabel];

%if length(unique(labels))~=length(labels)
%    disp('Colortable size mismatch 2 !');
%    return;
%end

% Remove unknowns and unwanted anatomical structures
% -remove from the ct.struct list
% -remove corresponding labels (entries in ct.table(:,4))
% 'Unknown_L','Unknown_R','Corpus_callosum_L','Corpus_callosum_R'
% 'G_and_S_Insula_ONLY_AVERAGE_L','G_and_S_Insula_ONLY_AVERAGE_R'
% 'Medial_wall_L','Medial_wall_R'
for zz=1:length(unwanted_structs)
    rm_zz=strcmp(colortable.struct_names,unwanted_structs{zz});
    if any(rm_zz)
        colortable.struct_names=colortable.struct_names(logical(~rm_zz));
        colortable.table=colortable.table(logical(~rm_zz),:);
        if any(labels==colortable.table(rm_zz,5))
            disp(['Warning: removed anatomical structure with active nodes: ' unwanted_structs{zz}]);
        end
    end
end

end