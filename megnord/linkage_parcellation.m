function [ROI, SS]=linkage_parcellation(forw_file, inv_file, nROI, SSs)

% ROI=linkage_parcellation(forward_file, inverse_file, number_ROIs, clustering_methods)
%
% Accepts   - forward operator file name
%           - inverse operator file name
%           - nROI, number of resulting parcels
%           - SSs, options for constructing the parcellation (+weights?)
%           -
%
% Returns   - ROI: a struct including source nodes belonging to each parcel
%           - path where the FreeSurfer-format parcellation is saved
%
% OPTIONS "SSs"
%   (1) Forward solution only (3) distance (4) source correlation (5) FreeSurfer-limitation
%   (6) source correlation profiles

%% TODO:
% write annotations and/or labels
% save pre-computed distances
% gather all non-mne (+Fieldtrip?) functions together
% visualization?
% morphing?

% percentiles for discarding invisible sources based on forward solution by sensor type
gradlim=0;
maglim=0;
eeglim=0;

% load forward and inverse operators
F=mne_read_forward_solution(forw_file,1); % use fixed-orientation
try
    M=mne_read_inverse_operator(inv_file);
    M=mne_prepare_inverse_operator(M,1,0.02,0,0); % minimum regularization
catch me
    M=[];
    disp('No inverse solution file found.');
    disp('Inverse solution not loaded, only SS=1 in use.')
end

if ~isnumeric(SSs)
    disp('Parcellation method needs to be of numbers!')
    return
end
disp(['Linkage method: ' int2str(SSs)]);
if any(SSs==6) % method (4) needed to do method (6)
    SSs=unique([SSs 4]);
end
% Weights for each method: SS -> SS^(w_SS)
% if ~exist('w_SS','var')
%     w_SS=[1 1 1 1 1 1];
% end
sF=F.nsource; % total #sources
sF1=F.src(1).nuse; % # sources in the first hemisphere

% Separate the hemispheres
IndepHemi=1; % 0 == dependent

% Compute signal space angles, if wanted:
if any(SSs==1)
disp('Computing signal space angles...');
FD=F.sol.data;
SS1=zeros(sF);
nFD=zeros(sF,1); % pre-compute signal space vector norms
nFD(1)=norm(FD(:,1));
if IndepHemi
    nFD(sF1+1)=norm(FD(:,sF1+1));
    for n=2:sF1
        disp([int2str(n) ' / ' int2str(sF)]);
        nFD(n)=norm(FD(:,n));
        for m=1:(n-1)
            SS1(n,m)=acos(abs((FD(:,n)'*FD(:,m))/(nFD(n)*nFD(m))));
        end
    end
    for n=sF1+2:sF
        disp([int2str(n) ' / ' int2str(sF)]);
        nFD(n)=norm(FD(:,n));
        for m=sF1+1:(n-1)
            SS1(n,m)=acos(abs((FD(:,n)'*FD(:,m))/(nFD(n)*nFD(m))));
        end
    end
else
    for n=2:sF
        disp([int2str(n) ' / ' int2str(sF)]);
        nFD(n)=norm(FD(:,n));
        for m=1:(n-1)
            SS1(n,m)=acos(abs((FD(:,n)'*FD(:,m))/(nFD(n)*nFD(m))));
        end
    end
end
SS1=SS1+SS1.';
SS1=SS1./max(SS1(isfinite(SS1)));
clear FD;
else
SS1=1;
end

SS2=1; % for future

% Add distance weighting by computing inter-source cortical distances and
% weighting the clustering by it (inter-hemispheric=Inf?), if wanted:
% separately for hemispheres, for now!
if any(SSs==3)
disp('Computing source distances');
SS3=compute_source_distance(F,sF,sF1,100,0);
SS3=SS3./max(SS3(isfinite(SS3)));
SS3=SS3-diag(diag(SS3));
SS3(1:sF1,sF1+1:end)=Inf; % make hemispheres independent
SS3(sF1+1:end,1:sF1)=Inf;
else
    SS3=1;
end

if any(SSs==4) % compute source-to-source artificial correlations
    [MD,~]=get_inverse_sol(M,0);
    try
        L=MD*F.sol.data; % point spread matrix
    catch mult_error
        L=MD*F.sol.data(1:360,:); % point spread matrix
    end
    SS4=L*L'; % source covariance
    S=inv(sqrt(diag(diag(SS4)))); % for turning cov to correlation
    SS4=S*SS4*S; % source-to-source correlation matrix
    SS4=1-SS4; % correlation to distance
    %SS4=SS4-diag(diag(SS4));
    %SS4=abs(SS4./max(abs(SS4(isfinite(SS4)))));
    clear MD L S;
else
    SS4=1;
end

% Limit the parcels to FreeSurfer regions (Desikan-Killiany?)
% NOTE: Also exclude nodes that are not present in this parcellation!
if any(SSs==5)
    % template parcellation file name
    templateROI='aparc' %.a2009s'
    try
        tmpROI=FS_parcellation_to_ROI(templateROI);
    catch ME
        tmpROI.ROIs={1:10^4};
        tmpROI.labels{1}='tmpROI';
        tmpROI.nROI=1;
    end
    if ~isfield(tmpROI,'nROI')
        tmpROI.nROI=length(tmpROI.ROIs);
    end
    SS5=ones(sF).*Inf;
    src_inc=unique([tmpROI.ROIs{:}]);
    for rr=1:tmpROI.nROI % set within-parcel distances to 1
        SS5(tmpROI.ROIs{rr},tmpROI.ROIs{rr})=1;
    end
    disp(['Clustering now restricted to ' int2str(tmpROI.nROI) ' anatomical labels.']);
    SS5=SS5-diag(diag(SS5)); % zeros along the diagonal - no need to scale
else
    SS5=1;
    templateROI='';
    src_inc=1:sF;
end

% Correlation profiles of sources, not only source-to-source correlations
if any(SSs==6)
    SS6=SS4;
    disp('Computing artefactual synchrony profiles');
%    SS6=zeros(sF);
%     for n=2:sF
%         disp([int2str(n) ' / ' int2str(sF)]);
%         ss4n=SS4(n,:);
%         tmp_m=zeros(1,n-1);
%         for m=1:(n-1)
%             %SS6(n,m)=1./abs(min(min(corrcoef(SSn,SS4(m,:)))));
%             tmp_x=corrcoef(ss4n,SS4(m,:));
%             tmp_m(m)=abs(tmp_x(1,2));
%         end
%         SS6(n,1:(n-1))=1./tmp_m;
%     end
%   SS6=SS6+SS6.';
    SS6=abs(corrcoef(SS4));
    SS4=1; % no longer consider individual correlations
%   SS6=SS6-diag(diag(SS6));
    SS6=1-SS6; % turn proximity to distance
else
    SS6=1;
end

% Combine the dissimilarity matrices SSn
%SS=SS1.^(w_SS(1)).*SS2.^(w_SS(2)).*SS3.^(w_SS(3)).*SS4.^(w_SS(4)).*SS5.^(w_SS(5)).*SS6.^(w_SS(6));
SS=SS1.*SS2.*SS3.*SS4.*SS5.*SS6;
clear SS1 SS2 SS3 SS4 SS5 SS6;

if IndepHemi
    SS(1:sF1,sF1+1:end)=Inf;
    SS(sF1+1:end,1:sF1)=Inf;
    disp('Hemisphere clusterings now independent.');
end

%% NEEDS RE-WRITING!
% prune out those sources that are not well visible using forward solution
invisible_ind=[];
if maglim>0 % for magnetometers
    FD=sum(abs(F.sol.data(match_str(ft_channelselection('MEGMAG',metadata.ch_names),metadata.ch_names),:)),1);
    maglim=prctile(FD,maglim);
    invisible_ind=find(FD<maglim);
end
if gradlim>0 % for gradiometers
    FD=sum(abs(F.sol.data(match_str(ft_channelselection('MEGGRAD',metadata.ch_names),metadata.ch_names),:)),1);
    gradlim=prctile(FD,gradlim);
    prune_grad=find(FD<gradlim);
    if exist('invisible_ind','var')
        invisible_ind=intersect(invisible_ind,prune_grad);
    else
        invisible_ind=prune_grad;
    end
end
if eeglim>0 % for electrodes
    FD=sum(abs(F.sol.data(match_str(ft_channelselection('EEG',metadata.ch_names),metadata.ch_names),:)),1);
    eeglim=prctile(FD,eeglim);
    prune_eeg=find(FD<eeglim);
    if exist('invisible_ind','var')
        invisible_ind=intersect(invisible_ind,prune_eeg);
    else
        invisible_ind=prune_eeg;
    end
end
disp(['Pruned ' int2str(length(invisible_ind)) ' invisible sources.']);
src_inc=setdiff(src_inc,invisible_ind);
%%
SS=SS(src_inc,src_inc); % parcellate only sources that are in the used template
                        % AND have a reasonable forward solution

% Do linkage clustering on dissimilarities SS (complete=furthest distance)
disp('Computing the linkage...');
Z=linkage(squareform(SS), 'complete');

disp(['Clustering the data to ' int2str(nROI) ' labels.']);
T=cluster(Z,'MaxClust',nROI);

% Build clusters to a cell array - and get back to original source
% numbering by src_inc(n)
C=cell(max(T),1);
for n=1:length(T)
    C{T(n)}=[C{T(n)} src_inc(n)];
end

% The parcellation struct to be returned
disp('Saving the parcellations...');
ROI=struct('nROI',max(T));
ROI.linkage_out=Z;
ROI.distances=Z(:,3);
ROI.ROIs=C;
ROI.IndepHemi=IndepHemi;
ROI.method=['max_linkage_' genvarname(int2str(SSs))];
%ROI.subjname=NN;
ROI.surf_ids={[int2str(F.src(1).id) ':' int2str(F.src(1).np)];
    [int2str(F.src(2).id) ':' int2str(F.src(2).np)]};
ROI.n_sources=[F.src(1).nuse;F.src(2).nuse];
ROI.in_template=src_inc;
ROI.in_template_name=templateROI;
if exist('tmpROI','var')
    for rr=1:length(ROI.ROIs)
        for tt_ind=1:length(tmpROI.ROIs)
            if ~isempty(intersect(tmpROI.ROIs{tt_ind},ROI.ROIs{rr}))
                ROI.template_label{rr}=tmpROI.labels{tt_ind};
            end
        end
        sz(rr)=length(ROI.ROIs{rr});
    end
else
    sz=0;
end
ROI.sizes=sz;
%save(['ROI_' int2str(ROI.nROI) '_' ROI.method],'ROI');
disp('Clustering parcellation completed!');
% Visualization
dendrogram(Z,300, 'ColorThreshold',Z(size(Z,1)-ROI.nROI+1,3)); % color the clustering tree
% draw ROIs?
% save label files or .annot file?
end
