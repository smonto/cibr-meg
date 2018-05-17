function smoothed_data=smooth_source_data(data,src_name,n,varargin)
% function smooth_source_data(source_data_in,source_space_filename,n_smoothing_rounds,varargin)
%
% requires ~/mne_setup_script.sh
%
% the source space can be read e.g. from:
% $SUBJECTS_DIR/<id>/bem/<id>-oct-6-src.fif or the inv op
% src=mne_read_source_spaces('forw_ops/forw_op.fif',0)
% source space file must include the field vertno
% input data must have the same number of elements as sources (either in
% one or both hemispheres, sparse or dense nodes)
% NOTE: zeros in w.data must not be written - a bug in mne_smooth! - 
% - the search for these could be done nicer...
% varargin adjusts 1 or 2 if both could work

% it seems to be good idea to turn the data vector horizontal:
if size(data,1)>size(data,2)
    data=data.';
end

src=mne_read_source_spaces(src_name,0); % read src
if ~isempty(varargin)
    opt_choice=varargin{1};
else
    opt_choice=0;
end
% check if 1- or 2-hemi data:
switch length(data)
    case src(1).nuse+src(2).nuse
        smoothed_data=zeros(1,src(1).np+src(2).np);
        log_d1=logical(data(1:src(1).nuse));
        log_d2=logical(data((1+src(1).nuse):length(data)));
        w1.vertices=src(1).vertno(log_d1)-1; % move to 0-based indexing
        w2.vertices=src(2).vertno(log_d2)-1; % move to 0-based indexing
        %w2.vertices=find(logical(data(1+src(1).nuse:end)))-1;
        log_d2=logical([zeros(1,src(1).nuse) log_d2]);
        w1.data=data(log_d1);
        w2.data=data(log_d2);
        filenames={'smoothing-lh.w';'smoothing-rh.w'};
        smoothed_filenames={'smoothing-smooth-lh.w';'smoothing-smooth-rh.w'};
        disp('Smoothing left and right source hemispheres.');
        try
            mne_write_w_file(filenames{1},w1);
            mne_write_w_file(filenames{2},w2);
        catch ME
            disp('Could not mne_write_w_file to current directory!');
            throw(ME);
        end
    case src(1).nuse
        if opt_choice==2 && length(data)==src(2).nuse
            smoothed_data=zeros(1,src(2).np);
            w.vertices=src(2).vertno(logical(data))-1; % move to 0-based indexing
            filenames={'smoothing-rh.w'};
            smoothed_filenames={'smoothing-smooth-rh.w'};
            disp('Smoothing right source hemisphere.');
        else
            smoothed_data=zeros(1,src(2).np);
            w.vertices=src(1).vertno(logical(data))-1; % move to 0-based indexing
            filenames={'smoothing-lh.w'};
            smoothed_filenames={'smoothing-smooth-lh.w'};
            disp('Smoothing left source hemisphere.');
        end
        w.data=data(logical(data));
        try
            mne_write_w_file(filenames{1},w);
        catch ME
            disp('Could not mne_write_w_file to current directory!');
            throw(ME);
        end
    case src(2).nuse % NOTE: may be the same as above!
        smoothed_data=zeros(1,src(2).np);
        w.vertices=src(2).vertno(logical(data))-1; % move to 0-based indexing
        w.data=data(logical(data));
        filenames={'smoothing-rh.w'};
        smoothed_filenames={'smoothing-smooth-rh.w'};
        disp('Smoothing right source hemisphere.');
        try
            mne_write_w_file(filenames{1},w);
        catch ME
            disp('Could not mne_write_w_file to current directory!');
            throw(ME);
        end
    case src(1).np+src(2).np
        smoothed_data=zeros(1,src(1).np+src(2).np);
        log_d1=logical(data(1:src(1).np));
        log_d2=logical([zeros(1,src(1).np) data((1+src(1).np):length(data))]);
        w1.vertices=find(log_d1)-1; % move to 0-based indexing
        w2.vertices=find(data((1+src(1).np):length(data)))-1;
        w1.data=data(log_d1);
        w2.data=data(log_d2);
%        w1.data=data(logical(data(1:src(1).np)));
%        w1.vertices=find(w1.data)-1; % move to 0-based indexing
%        w2.data=data(logical(data));
%        w2.data=w2.data(1+src(1).np:end);
%        w2.vertices=find(w2.data)-1;
        filenames={'smoothing-lh.w';'smoothing-rh.w'};
        smoothed_filenames={'smoothing-smooth-lh.w';'smoothing-smooth-rh.w'};
        disp('Smoothing full-blown left and right hemispheres.');
        try
            mne_write_w_file(filenames{1},w1);
            mne_write_w_file(filenames{2},w2);
        catch ME
            disp('Could not mne_write_w_file to current directory!');
            throw(ME);
        end
    case src(1).np
        smoothed_data=zeros(1,src(1).np);
        w.vertices=find(logical(data))-1; % move to 0-based indexing
        w.data=data(w.vertices+1);
        filenames={'smoothing-lh.w'};
        smoothed_filenames={'smoothing-smooth-lh.w'};
        disp('Smoothing full-blown left hemisphere.');
        try
            mne_write_w_file(filenames{1},w);
        catch ME
            disp('Could not mne_write_w_file to current directory!');
            throw(ME);
        end
    case src(2).np
        smoothed_data=zeros(1,src(2).np);
        w.vertices=find(logical(data))-1; % move to 0-based indexing
        w.data=data(w.vertices+1);
        filenames={'smoothing-rh.w'};
        smoothed_filenames={'smoothing-smooth-rh.w'};
        disp('Smoothing full-blown right hemisphere.');
        try
            mne_write_w_file(filenames{1},w);
        catch ME
            disp('Could not mne_write_w_file to current directory!');
            throw(ME);
        end        
    otherwise
        disp('Could not relate data to hemispheres!');
        smoothed_data=0;
        return
end

infiles=[];
for kk=1:length(filenames)
    infiles=[infiles ' --in ' filenames{kk}];
end
% construct the smoothing shell script
[fid,~]=fopen('smoothing_w.sh','w'); % open as a new file
fprintf(fid,'%s\n','source ~/mne_setup_script.sh'); % launch mne environ
fprintf(fid,'%s\n',['mne_smooth --src ' src_name infiles ' --smooth ' int2str(n)]); % do the smoothing
fclose(fid);
try
    system('source ./smoothing_w.sh'); % execute the script
    disp('Smoothing source data ... ');
catch ME
    disp('Could not execute ./smoothing_w.sh!');
    throw(ME);
end
%smoothed_data=zeros(1,src(1).np+src(2).np);
for kk=1:length(filenames) % TODO: use real data lengths!
    ww(kk)=mne_read_w_file(smoothed_filenames{kk});
    if strfind(smoothed_filenames{kk},'-lh')>0
        smoothed_data(double(ww(kk).vertices)+1)=ww(kk).data;
%   ww(kk).data(logical(ww(kk).data))
%   smoothed_data(length(smoothed_data)+1:length(smoothed_data)+length(ww(kk).data))=ww(kk).data;
    else if strfind(smoothed_filenames{kk},'-rh')>0
            smoothed_data(double(ww(kk).vertices)+1+double(src(1).np))=ww(kk).data;
        end
    end
    delete(filenames{kk});
    delete(smoothed_filenames{kk});
end
delete('smoothing_w.sh');
disp('Smoothing ready!');
end