function [psol,ch_names] = get_inverse_sol(inv,dSPM)
% [pre_solution,channel_list] = get_inverse_sol(inv_op, dSPM?)
%
% gives the pre-solution term, so that solution can be completed simply
% with sol=psol*data
% also returns the channel name list

trans=diag(sparse(inv.reginv))*inv.eigen_fields.data*inv.whitener*inv.proj;
if inv.eigen_leads_weighted
    psol=inv.eigen_leads.data*trans;
else
    psol=diag(sparse(sqrt(inv.source_cov.data)))*inv.eigen_leads.data*trans;
end

if dSPM
    psol=inv.noisenorm*psol;
end

ch_names=inv.eigen_fields.col_names;

end