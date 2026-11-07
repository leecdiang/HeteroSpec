"""Prospective recipe routing, not an endpoint oracle or numerical safety proof."""
from protocol import require


def route(features: dict, pilot_admitted: bool, rule: str) -> str:
    allowed={'dtype','flash_attention','streams','max_q','prompt_tokens','known_graph_path','state_origin'}
    require(set(features)==allowed,'routing must not read outputs, margin, latency or validation labels')
    require(rule in ('always_reference','shape_only','producer_guarded'),'unknown frozen rule')
    static=(features['dtype']=='F16' and features['flash_attention'] is False and features['streams']==1
            and type(features['max_q']) is int and features['max_q']<=2 and features['max_q']>=1 and 64<=features['prompt_tokens']<=512
            and features['known_graph_path'] is True)
    require(features['state_origin']=='fresh_request','UNKNOWN_STATE_REQUIRES_RESTART_FROM_PROMPT_NOT_LIVE_REFERENCE_SWITCH')
    if rule=='always_reference' or not static:return 'R'
    if rule=='shape_only':return 'C_B_QB'
    # This path recreates state naturally from the prompt; it does not import/cache-patch it.
    # It may still be wrong on unseen inputs. Acceptance is an empirical prediction.
    return 'C_R_QB' if pilot_admitted and features['state_origin']=='fresh_request' else 'R'


def pilot_decision(evidence: dict) -> str:
    required={'original_reference_stable','rebuilt_reference_matches','observer_controls_match',
              'all_controls_provenance_valid','C_R_QB_sentinel_qualification','C_R_PQ_sentinel_qualification',
              'C_R_QB_actual_multirow_witness','port_repair_cycles'}
    require(set(evidence)==required,'pilot gate schema; no speed-based early stopping')
    if not all(evidence[k] is True for k in ('original_reference_stable','rebuilt_reference_matches',
              'observer_controls_match','all_controls_provenance_valid')):
        return 'STOP_CONTROL_OR_INFRASTRUCTURE'
    if evidence['port_repair_cycles']>2:return 'STOP_NO_MORE_PORT_TUNING'
    if not (evidence['C_R_QB_sentinel_qualification'] is True and evidence['C_R_PQ_sentinel_qualification'] is True):
        return 'STOP_NO_QUALIFIED_LOCAL_COMPOSITION'
    if evidence['C_R_QB_actual_multirow_witness'] is not True:return 'STOP_NO_BATCHING_LEVER'
    return 'PILOT_FEASIBLE_REQUEST_AUTHOR_GO_FOR_HOLDOUT'
