function smoothed_data=smooth_ROI(ROI_path,n,varargin)
% smoothed_data=smooth_ROI(ROI_path,n_smooth,varargin)
%
% takes a ROI structure input and returns a smoothed and checked version
% of the ROI on the full cortical surface (for visualization purposes)
% varargin may include ROI indices to visualize

R=load(ROI_path);
ROI=R.ROI;
sfp=strfind(ROI_path,filesep);
if isempty(sfp)
    sfp=0;
end
%fwd_path=[ROI_path(1:sfp(end)) 'forw_ops/forw_op.fif'];
fwd_path=ROI.forw_path;
disp(['Found forward op surface at: ' fwd_path]);
if isfield(ROI,'IndepHemi') && ~ROI.IndepHemi
    disp('Hemispheres should be independent!');
    return
end

if ~isempty(varargin)
    ROI_inds=varargin{1};
else
    ROI_inds=1:ROI.nROI;
end
ROI
src=mne_read_source_spaces(fwd_path,0); % read src spaces
disp(['Looking for ' int2str(length(ROI_inds)) ' ROI ind values for smoothing...']);
vals=compute_ROI_value_set(length(ROI_inds)); % use as values for each ROI
%load('/volatile/home/smonto/Dropbox/Connectivity/Software/constants/ROI_values_250.mat');
vals=sort(vals);
if length(unique(vals))~=length(ROI_inds)
    disp('vals and ROI inds length mismatch');
end
disp(['Found ' int2str(length(unique(vals))) ' values for ROIs!']);
disp(['Max. ROI coding value: ' num2str(max(vals)) '.']);
disp(['Min. ROI coding value: ' num2str(min(vals)) '.']);
% move to full node space if max(ROI.ROIs)<sum(src.nuse)
if max([ROI.ROIs{:}])<=(src(1).nuse+src(2).nuse)
    smoothed_data=zeros(src(1).nuse+src(2).nuse,1);
else
    smoothed_data=zeros(src(1).np+src(2).np,1);
end
disp(['Initial data length: ' int2str(length(smoothed_data))]);
for kk=ROI_inds
    smoothed_data(ROI.ROIs{kk})=vals(kk);
end
%all_nodes2=zeros(ROI.n_sources(2),1);
%vertnos=double([src(1).vertno src(2).vertno+src(1).np]);

for ss=1:n % do each smoothing in a separate round to control for inter-ROI effects
disp(['Smoothing round: ' int2str(ss)]);
disp(['Data length: ' int2str(length(smoothed_data))]);
disp(['Non-zero data: ' int2str(nnz(smoothed_data))]);
disp(['Different data values before smoothing: ' int2str(length(unique(smoothed_data)))]);
% assign new, smoothed data only when previously zero:
smoothed_data_new=smooth_source_data(smoothed_data,fwd_path,1);
if length(smoothed_data)==length(smoothed_data_new)
    smoothed_data(~logical(smoothed_data))=smoothed_data_new(~logical(smoothed_data));
else
    smoothed_data=smoothed_data_new;
end
disp(['Non-zero data after smoothing: ' int2str(nnz(smoothed_data))]);
% How to make sure that the values are not interpolated, or how originals found?
% use "mode" in the 1-environment of nodes: unique(tri(find==kk,:))
% Use the list of values in "vals"
sm=size(smoothed_data);
if sm(1)>sm(2)
    smoothed_data=smoothed_data.';
end
% find values not in vals and not 0 (i.e. not assigned to a ROI)
v=setdiff(smoothed_data,[0 vals]);
disp(['Different data values after smoothing: ' int2str(length(unique(smoothed_data)))]);
while ~isempty(v)
  disp(['Number of non-desired values: ' int2str(length(v))]);
  for nn=1:length(v) % for each undesired value
    indv=find(smoothed_data==v(nn)); % all the instances of value v
    %disp(['Number of non-ROI elements for ' num2str(v(nn)) ' : ' int2str(length(indv))]);
    for zz1=indv(indv<=src(1).np) % belongs to hemi-1
        %if ~isempty(zz1)
        [indr,~]=find(src(1).tris==zz1);
        % get the nodes that neighbour this non-ROI value
        nnodes1=setdiff(unique(src(1).tris(indr,:)),zz1);
        x=smoothed_data(nnodes1);
        %disp(['Data around false value in hemi1: ' num2str(x)]);
        % set the value to the most common value in vals
        x=x(ismember(x,vals));
        smoothed_data(zz1)=max(0,mode(x));
        %if any(isnan(smoothed_data))
        %    return;
        %end
        %end
    end
    for zz2=indv(indv>src(1).np) % belongs to hemi-2
        %if ~isempty(zz2)
        zz2p=zz2-(src(1).np);
        [indr,~]=find(src(2).tris==zz2p);
        % get the nodes that neighbour this non-ROI value
        nnodes2=setdiff(unique(src(2).tris(indr,:)),zz2p);
        nnodes2=nnodes2+src(1).np;
        x=smoothed_data(nnodes2);
        %disp(['Data around false value in hemi2: ' num2str(x)]);
        % set the value to the most common vals value
        x=x(ismember(x,vals));
        %if mode(smoothed_data(nnodes2))==round(mode(smoothed_data(nnodes2)))
        smoothed_data(zz2)=max(0,mode(x));
        %if any(isnan(smoothed_data))
        %    return;
        %end
        %end
    end
  end
  v=setdiff(smoothed_data,[0 vals]);
  disp([int2str(length(v)) ' values not related to any ROI remaining']);
end
%SM_D(ss,:)=smoothed_data;
end
disp(['Different data values after final smoothing round: ' int2str(length(unique(smoothed_data)))]);
%ROI.surf_ROIs{1}=smoothed_data(1:src(1).np);
%ROI.surf_ROIs{2}=smoothed_data(1+src(1).np:end);
% replace by a function surf_values_to_ROIs()
for kk=ROI_inds
    smoothed_data(smoothed_data==vals(kk))=kk;
end
%min(smoothed_data)
%max(smoothed_data)

end