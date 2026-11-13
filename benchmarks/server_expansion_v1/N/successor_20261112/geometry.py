"""Zero-forward dense seq0 geometry, never native observations or timing.

The q=32/P=256 defaults describe the prospective N candidate profile.  They
do not certify its C4096 adapter, physical cache head, arithmetic or placement.
All extents below are predictions from token positions.  LOCAL outer envelopes
are not counted as attention work: its predicted attention subgroups are.
"""


def _integer(name, value, minimum):
    if type(value) is not int or value < minimum:
        raise ValueError(name + ' must be an integer >= ' + str(minimum))


def _call(position, width, padding):
    return dict(position=position, width=width,
                predicted_attention_extent=((position+width-1)//padding+1)*padding)


def _split(position, width, padding):
    out=[];done=0
    while done<width:
        count=min(width-done,padding-(position+done)%padding)
        out.append(_call(position+done,count,padding));done+=count
    return out


def _partition(calls):
    return [(x['position'],x['width'])for x in calls]


def _summary(calls):
    return dict(call_count=len(calls),token_rows=sum(x['width']for x in calls),
                predicted_padded_attention_work=sum(x['width']*x['predicted_attention_extent']for x in calls))


def schedule(head, append, q=32, padding=256, capacity=4096):
    """Return exact ordered partitions under one declared static dense model.

    ``head`` is the predicted number of materialized tokens before this append;
    the caller owns pending/template/prefix accounting.  No native head is
    inferred from provided conversation text.  Capacity-rejected rows are
    returned explicitly with null schedules, so they remain in denominators.
    """
    for name,value,minimum in [('head',head,0),('append',append,0),('q',q,1),
                               ('padding',padding,1),('capacity',capacity,1)]:
        _integer(name,value,minimum)
    if capacity%padding:
        raise ValueError('Declared dense capacity must be divisible by padding')
    admitted=head<=capacity and append<=capacity-head
    result=dict(schema='heterospec.N.dense-geometry-prediction.v1',
        status='PREDICTED_HEAD_REQUIRES_NATIVE_CHECK'if admitted else'UNSUPPORTED_CAPACITY',
        head_source='token_geometry_prediction',head_observed=False,
        native_head=None,native_head_status='NOT_OBSERVED_ZERO_FORWARD',
        head=head,append=append,q=q,padding=padding,capacity=capacity,
        capacity_admitted=admitted,not_dropped_from_denominator=True,
        profile_status='PROSPECTIVE_NOT_NATIVE_QUALIFIED',
        no_latency_or_acceptance_selection=True,
        not_performance_or_numerical_evidence=True,
        work_unit='sum(token_rows * predicted_padded_attention_extent)',
        whole_fixed=None,whole_rechunk=None,local_outer=None,local_inner=None,
        comparisons=None)
    if not admitted:
        result['unsupported_reason']='Materialized head plus appended rows exceed declared dense capacity'
        return result
    # Weak fixed caller keeps its original q grid, then splits each caller
    # group at a padding boundary.  These are whole-graph physical predictions.
    outer=[];whole_fixed=[];inner=[];done=0
    while done<append:
        width=min(q,append-done);position=head+done;groups=_split(position,width,padding)
        envelope=_call(position,width,padding)
        envelope['predicted_graph_extent_envelope']=envelope.pop('predicted_attention_extent')
        envelope['extent_scope']='Outer graph envelope only; attention executes predicted subgroups'
        envelope['attention_groups']=[dict(x)for x in groups]
        outer.append(envelope)
        for group in groups:
            whole_fixed.append(dict(group));inner.append(dict(group))
        done+=width
    # Strong whole-rechunk restarts full q groups immediately after each
    # boundary; it never resumes the weak caller's old grid.
    rechunk=[];done=0
    while done<append:
        position=head+done;width=min(q,append-done,padding-position%padding)
        rechunk.append(_call(position,width,padding));done+=width
    fixed_summary=_summary(whole_fixed);rechunk_summary=_summary(rechunk);inner_summary=_summary(inner)
    if not fixed_summary['token_rows']==rechunk_summary['token_rows']==inner_summary['token_rows']==append:
        raise ValueError('Geometry token conservation violated')
    if not fixed_summary['predicted_padded_attention_work']==rechunk_summary['predicted_padded_attention_work']==inner_summary['predicted_padded_attention_work']:
        raise ValueError('Declared per-token dense extent work differs between partitions')
    bound=(append+q-1)//q+1
    if padding%q==0 and len(rechunk)>bound:
        raise ValueError('Declared dense rechunk call bound violated')
    projection_calls=len(outer)
    result.update(
        whole_fixed=dict(calls=whole_fixed,**fixed_summary,
                         caller_policy='fixed_q_grid_then_boundary_split'),
        whole_rechunk=dict(calls=rechunk,**rechunk_summary,
                           caller_policy='restart_q_after_each_boundary',
                           ceil_append_over_q=(append+q-1)//q,
                           divisible_padding_bound_applicable=padding%q==0,
                           divisible_padding_call_bound=bound if padding%q==0 else None),
        local_outer=dict(calls=outer,call_count=projection_calls,token_rows=append,
                         projection_call_count=projection_calls,
                         count_scope='Outer graph/projection-group boundaries, not CUDA kernel dispatch counts',
                         native_kernel_dispatches=None,
                         attention_group_count=len(inner),
                         split_outer_calls=sum(len(x['attention_groups'])>1 for x in outer),
                         predicted_padded_attention_work=inner_summary['predicted_padded_attention_work'],
                         work_scope='Sum of inner attention groups; not outer max-extent envelopes'),
        local_inner=dict(calls=inner,**inner_summary),
        comparisons=dict(
            whole_fixed_vs_rechunk_identical_ordered_partition=_partition(whole_fixed)==_partition(rechunk),
            whole_rechunk_vs_local_outer_identical_ordered_partition=_partition(rechunk)==_partition(outer),
            whole_rechunk_vs_local_inner_identical_ordered_partition=_partition(rechunk)==_partition(inner),
            whole_fixed_vs_local_inner_identical_ordered_partition=_partition(whole_fixed)==_partition(inner),
            predicted_padded_attention_work_equal=True,
            whole_fixed_extra_graph_calls_over_rechunk=len(whole_fixed)-len(rechunk),
            rechunk_extra_graph_calls_over_local_projection=len(rechunk)-projection_calls,
            local_extra_attention_groups_over_rechunk=len(inner)-len(rechunk),
            projection_partition_distinct=_partition(rechunk)!=_partition(outer),
            native_execution_or_arithmetic_equivalence='NOT_ESTABLISHED_BY_GEOMETRY'))
    return result
