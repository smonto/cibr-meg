function [ROI, SS]=linkage_parcellation(forw_file, inv_file, nROI, SSs)

% ROI=linkage_parcellation(forward_file, inverse_file, number_ROIs, clustering_methods)
%
% Accepts   - forward_file; forward operator file name
%           - inverse_file; inverse operator file name
%           - number_ROIs; number of resulting parcels
%           - clustering_methods; options for constructing the ROIs
%
% Returns   - ROI; a struct including source nodes belonging to each parcel
%           - path where the FreeSurfer-format parcellation is saved
%
% Available clustering methods:
%   (1) signal space angles (forward solution) (3) node-to-node distance
%   (4) source-to-source correlation (5) FreeSurfer-based limitation
%   (6) source-to-source correlation profiles
%
% Notes:
% * needs fixed-orientation solutions -- free orientations possible in future
% * some parameters tuned in the code
%       - FreeSurfer parcellation
%       - pruning of weakly visible sources
%
% simo.monto@gmail.com
% last edited:
% 17052018

%% TODO:

% linkage: mean, complete or shortest?
% save pre-computed distances
% visualization?
% morphing?

%% Some parameters and preparations
% set percentiles for discarding invisible sources based on forward solution
%  - discard a source if not visible by any sensor type set here
gradlim=0;
maglim=0;
eeglim=0;

% FreeSurfer-directory
FS_dir='/Users/simo/Documents/Data/FreeSurfer/lp100131/';

% template parcellation file
templateROI='aparc'; %.a2009s'; 'StrictlyLobes';

% load forward and inverse operators
F=mne_read_forward_solution(forw_file,1); % use fixed-orientation
try
    M=mne_read_inverse_operator(inv_file);
    M=mne_prepare_inverse_operator(M,1,0.02,0,0); % minimum regularization
catch me
    M=[];
    disp('No inverse solution file found.');
    disp('Inverse solution not loaded, only SS=1 in use.')
    throw(me);
end

% match channel selectors in the operators:
if length(F.sol.row_names)>length(M.noise_cov.names)
    Fsel=fiff_pick_channels(F.sol.row_names, M.noise_cov.names, []);
%elseif length(F.sol.row_names)<length(M.noise_cov.names)
%    Isel=fiff_pick_channels(M.noise_cov.names, F.sol.row_names, []);
    disp('Channel selections in forward and inverse matched!');
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
IndepHemi=1; % 0 == dependent -- for now independent recommended

%% Option 1: signal space angles
if any(SSs==1)
disp('Computing signal space angles...');
FD=F.sol.data(Fsel,:);
SS1=zeros(sF);
nFD=zeros(sF,1); % pre-compute signal space vector norms
nFD(1)=norm(FD(:,1));
if IndepHemi
    nFD(sF1+1)=norm(FD(:,sF1+1));
    for n=2:sF1
        disp([int2str(n) ' / ' int2str(sF)]);
        nFD(n)=norm(FD(:,n));
        for m=1:(n-1) % could be parallelized
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
SS1=SS1+SS1.'; % make symmetric
SS1=SS1./max(abs(SS1(isfinite(SS1)))); % scale to max==1
clear FD;
else % if no signal space angle information wanted
SS1=1;
end

%%
SS2=1; % Option 2 saved for future

%% Option 3: source-to-source distance
% Add distance weighting by computing inter-source distances along cortex.
% Separately for hemispheres, for now!
if any(SSs==3)
disp('Computing source distances...');
SS3=compute_source_distance(F,sF,sF1,100,0); % option for Euclidean distances
SS3=SS3./max(SS3(isfinite(SS3)));
SS3=SS3-diag(diag(SS3)); % ensure zero diagonal
SS3(1:sF1,sF1+1:end)=Inf; % ensure hemispheres independent (distance=Inf)
SS3(sF1+1:end,1:sF1)=Inf;
else
    SS3=1;
end

%% Option 4: source-to-source correlation
if any(SSs==4) % artificial correlations based on inverse * forward
    [MD,~]=get_inverse_sol(M,0); % get the inverse matrix
    L=MD*F.sol.data(Fsel,:); % point spread matrix
    SS4=L*L'; % source-to-source covariance
    S=inv(sqrt(diag(diag(SS4)))); % normalization for turning cov to corr
    SS4=S*SS4*S.'; % source-to-source corr matrix
    SS4=1-abs(SS4); % turn corr linearly to distance (sign unimportant)
    clear MD L S;
else
    SS4=1;
end

%% Option 5: FreeSurfer-based parcel limitation
% NOTE: excludes nodes that are not present in this parcellation
% NOTE: you should ask for more ROIs than you have parcels
if any(SSs==5)
    try % templateROI and FS_dir defined in the beginning
        tmpROI=FS_annotation_to_ROI(templateROI, forw_file, [FS_dir '/label/']);
    catch ME % make a single proxy template if failed to load
        disp('Template ROI not loaded!')
        tmpROI.ROIs={1:sF};
        tmpROI.labels{1}='tmpROI';
        tmpROI.nROI=1;
    end
    if ~isfield(tmpROI,'nROI')
        tmpROI.nROI=length(tmpROI.ROIs);
    end
    SS5=ones(sF).*Inf; % all source dissociated by default
    src_inc=unique([tmpROI.ROIs{:}]); % use only sources in the template
    for rr=1:tmpROI.nROI % set within-parcel distances to 1
        SS5(tmpROI.ROIs{rr},tmpROI.ROIs{rr})=1;
    end
    disp(['Clustering now restricted to ' int2str(tmpROI.nROI) ' anatomical labels.']);
    SS5=SS5-diag(diag(SS5)); % zeros along the diagonal - no need to scale
else
    SS5=1;
    templateROI='';
    src_inc=1:sF; % include all sources
end

%% Option 6: Correlation profiles of sources
if any(SSs==6)
    disp('Computing artefactual synchrony profiles');
    SS6=SS4; % initialize source-to-source correlations
    SS6=abs(corrcoef(SS4)); % correlations between source-wise profiles
    SS4=1; % no longer consider individual correlations (even if asked)
    SS6=1-SS6; % turn correlations linearly to distance
    SSs=setdiff(SSs,4); % fix naming
else
    SS6=1;
end

%% Start building the final distance matrix, needed by linkage clutering
% Combine the dissimilarity matrices (without weighting for now)
%SS=SS1.^(w_SS(1)).*SS2.^(w_SS(2)).*SS3.^(w_SS(3)).*SS4.^(w_SS(4)).*SS5.^(w_SS(5)).*SS6.^(w_SS(6));
SS=SS1.*SS2.*SS3.*SS4.*SS5.*SS6;
clear SS1 SS2 SS3 SS4 SS5 SS6; % save some memory please
SS=triu(SS,1)+triu(SS,1).'; % saving symmetry & diagonal from rounding errors

if IndepHemi % override possible other distance assignments
    SS(1:sF1,sF1+1:end)=Inf;
    SS(sF1+1:end,1:sF1)=Inf;
    disp('Hemisphere clusterings now independent.');
end

% Prune out sources that are not well visible using forward solution
if maglim>0 % check for magnetometers
    magind=regexp(F.sol.row_names,'MEG...1'); % MAG names end in "1"
    FD=sum(abs(F.sol.data(not(cellfun('isempty', magind)),:)),1);
    maglim=prctile(FD,maglim); % forward solution discard limit set above
    invisible_ind=find(FD<maglim); % list those that are below limit
end
if gradlim>0 % check for gradiometers
    gradind=regexp(F.sol.row_names,'MEG...[2,3]');
    FD=sum(abs(F.sol.data(not(cellfun('isempty', gradind)),:)),1);
    gradlim=prctile(FD,gradlim);
    prune_grad=find(FD<gradlim);
    if exist('invisible_ind','var')
        invisible_ind=intersect(invisible_ind,prune_grad); % combine by "or"
    else
        invisible_ind=prune_grad;
    end
end
if eeglim>0 % check for electrodes
    eegind=regexp(F.sol.row_names,'EEG');
    if not(isempty(eegind))
    FD=sum(abs(F.sol.data(not(cellfun('isempty', eegind)),:)),1);
    eeglim=prctile(FD,eeglim);
    prune_eeg=find(FD<eeglim);
    if exist('invisible_ind','var')
        invisible_ind=intersect(invisible_ind,prune_eeg);
    else
        invisible_ind=prune_eeg;
    end
    end
end
if exist('invisible_ind','var')
    if ~isempty(invisible_ind)
        src_inc=setdiff(src_inc,invisible_ind);
        disp(['Pruned ' int2str(length(invisible_ind)) ' invisible sources.']);
    end
end
%% Do linkage clustering
SS=SS(src_inc,src_inc); % parcellate only sources that are in the used template
                        % and have a reasonable forward solution

imagesc(SS(1:200,1:200))

% Do linkage clustering on distance matrix SS
disp('Computing the linkage...');
Z=linkage(squareform(SS), 'complete'); % complete=furthest distance

disp(['Clustering the data to ' int2str(nROI) ' labels.']);
T=cluster(Z,'MaxClust',nROI);

% Build clusters to a cell array - and get back to original source
% numbering by src_inc(n)
C=cell(max(T),1);
for n=1:length(T)
    C{T(n)}=[C{T(n)} src_inc(n)];
end

%% Build the parcellation struct ('ROI') to be returned:
disp('Saving the parcellations...');
ROI=struct('nROI',max(T));
ROI.linkage_out=Z;
ROI.distances=Z(:,3);
ROI.ROIs=C;
ROI.IndepHemi=IndepHemi;
ROI.method=['max_linkage_' genvarname(int2str(SSs))];
ROI.surf_ids={[int2str(F.src(1).id) ':' int2str(F.src(1).np)];
    [int2str(F.src(2).id) ':' int2str(F.src(2).np)]};
ROI.n_sources=[F.src(1).nuse; F.src(2).nuse];
ROI.n_vertices=[F.src(1).np; F.src(2).np];
ROI.in_template=src_inc;
ROI.in_template_name=templateROI;
for rr=1:length(ROI.ROIs)
    ROI.labels{rr}=['ROI' int2str(rr)]; % initialize ROI names
    if exist('tmpROI','var')
        for tt_ind=1:length(tmpROI.ROIs) % name after template names
            if ~isempty(intersect(tmpROI.ROIs{tt_ind},ROI.ROIs{rr}))
                ROI.template_label{rr}=tmpROI.labels{tt_ind};
                ROI.labels{rr}=[ROI.labels{rr} '_' tmpROI.labels{tt_ind}];
            end
        end
        ROI.sizes(rr)=length(ROI.ROIs{rr});
    end
end
ROI.name=['ROI_' ROI.method];
ROI.forw_path=[pwd '/' forw_file];
ROI.inv_path=[pwd '/' inv_file];
ROI.FS_dir=FS_dir; % FreeSurfer-directory
disp('Clustering parcellation completed!');
% Visualization
disp('Visualizing the linkage dendrogram ...');
figure
dendrogram(Z,500, 'ColorThreshold',Z(size(Z,1)-ROI.nROI+1,3));
% save .annot file
disp('Writing annotation file...');
save_ROI_annotation(ROI);
disp('Done.');
save(ROI.name ,'ROI'); % save to working directory
disp(['Parcellation saved as ' ROI.name]);
end
