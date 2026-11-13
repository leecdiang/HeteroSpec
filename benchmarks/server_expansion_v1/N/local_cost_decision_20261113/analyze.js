'use strict';
// One-off CPU analysis of frozen receipts and source-conditioned work models.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const assert = require('assert/strict');
const base = path.resolve(__dirname, '..');
const out = path.resolve(process.argv[2] || path.join(__dirname, 'RESULTS'));
assert(!fs.existsSync(out), 'use a fresh output; preserve prior evidence');
fs.mkdirSync(out, { recursive: true });
const inputs = [
  'free_service_retry_20261113/EVIDENCE/EPISODES.json',
  'resident_opportunity_20261113/RESULTS/REPORT.json',
  'resident_opportunity_20261113/RESULTS/MINIMAL_AB_FIXTURE.json'
];
const buffers = inputs.map(file => fs.readFileSync(path.join(base, file)));
const [episodes, opportunity, fixture] = buffers.map(b => JSON.parse(b));
const measured = episodes.filter(e => e.stage === 'MEASURE');
assert.equal(measured.length, 8);
const sum = xs => xs.reduce((a, b) => a + b, 0);
const mean = xs => sum(xs) / xs.length;
const spread = xs => ({
  values_ms: xs.map(x => x * 1000),
  range_ms: (Math.max(...xs) - Math.min(...xs)) * 1000,
  sample_sd_ms: Math.sqrt(sum(xs.map(x => (x - mean(xs)) ** 2)) / (xs.length - 1)) * 1000,
  caution: 'scatter of two ordered contrasts; not a calibrated append-only noise distribution'
});
const pairs = [];
const cases = [];
for (const name of ['C0', 'C1']) {
  const rows = [];
  for (const round of [0, 1]) {
    const W = measured.find(e => e.case === name && e.round === round && e.arm === 'W');
    const L = measured.find(e => e.case === name && e.round === round && e.arm === 'L');
    assert(W && L);
    const row = {
      case: name, round,
      W_episode_s: W.timing.controller_service_plus_reset_s,
      L_episode_s: L.timing.controller_service_plus_reset_s,
      W_decode_sync_budget_s: W.phases.decode_sync_and_budget_s,
      L_decode_sync_budget_s: L.phases.decode_sync_and_budget_s,
      W_sampling_s: W.phases.greedy_sampling_s,
      L_sampling_s: L.phases.greedy_sampling_s,
      benefit_episode_s: W.timing.controller_service_plus_reset_s - L.timing.controller_service_plus_reset_s,
      benefit_decode_sync_budget_s: W.phases.decode_sync_and_budget_s - L.phases.decode_sync_and_budget_s,
      benefit_sampling_s: W.phases.greedy_sampling_s - L.phases.greedy_sampling_s
    };
    row.benefit_nonsampling_residual_s = row.benefit_episode_s - row.benefit_sampling_s;
    pairs.push(row);
    rows.push(row);
  }
  const service = mean(rows.map(x => x.W_episode_s));
  const decode = mean(rows.map(x => x.W_decode_sync_budget_s));
  const W = measured.filter(e => e.case === name && e.arm === 'W');
  cases.push({
    case: name,
    W_mean_episode_s: service,
    W_mean_decode_sync_budget_s: decode,
    W_mean_physical_calls: mean(W.map(e => e.physical_calls)),
    mean_benefit_episode_ms: mean(rows.map(x => x.benefit_episode_s)) * 1000,
    mean_benefit_decode_sync_budget_ms: mean(rows.map(x => x.benefit_decode_sync_budget_s)) * 1000,
    mean_benefit_nonsampling_residual_ms: mean(rows.map(x => x.benefit_nonsampling_residual_s)) * 1000,
    episode_contrast_scatter: spread(rows.map(x => x.benefit_episode_s)),
    decode_contrast_scatter: spread(rows.map(x => x.benefit_decode_sync_budget_s)),
    nonsampling_contrast_scatter: spread(rows.map(x => x.benefit_nonsampling_residual_s)),
    uniform_nonnegative_per_call_cost_ceiling_ms: decode / mean(W.map(e => e.physical_calls)) * 1000,
    ceiling_assumption: 'one identical nonnegative fixed charge per call; all remaining decode/sync/budget costs nonnegative. Not a hardware or shape-dependent saving bound.'
  });
}

function work(name, arm, calls) {
  let columns = 0, attention = 0, concat = 0, concatUnits = 0, maskElements = 0;
  let requiredBuilds = 0, previousKey = null;
  let maskContNodes = 0, maskContElements = 0;
  const tilePositions = [], attentionPositions = [], keys = [];
  calls.forEach((g, index) => {
    assert.equal(g.width, g.expected_extents.length);
    const requestedOutputs = index === calls.length - 1 ? 1 : 0;
    const key = JSON.stringify([g.width, g.expected_extents, requestedOutputs]);
    if (key !== previousKey) requiredBuilds++;
    previousKey = key;
    keys.push({ position: g.position, width: g.width, requestedOutputs, extent_runs: [...new Set(g.expected_extents)] });
    maskElements += g.width * Math.max(...g.expected_extents);
    for (let i = 0; i < g.width; i += 4) {
      columns++;
      tilePositions.push([g.position + i, Math.min(4, g.width - i)]);
    }
    const tiles = [];
    let start = 0;
    for (let i = 1; i <= g.width; i++) {
      if (i === g.width || g.expected_extents[i] !== g.expected_extents[start]) {
        for (let j = start; j < i; j += 4) {
          const width = Math.min(4, i - j);
          tiles.push(width);
          const extent = g.expected_extents[start];
          if (width > 1 && extent < Math.max(...g.expected_extents)) {
            maskContNodes++;
            maskContElements += width * extent;
          }
          attentionPositions.push([g.position + j, width, g.expected_extents[start]]);
        }
        start = i;
      }
    }
    attention += tiles.length;
    concat += Math.max(0, tiles.length - 1);
    let cumulative = 0;
    tiles.forEach((n, i) => { cumulative += n; if (i) concatUnits += cumulative; });
  });
  return {
    name, arm, rows: sum(calls.map(g => g.width)), calls: calls.length,
    projection_4column_groups_per_fully_consumed_projection: columns,
    attention_4query_tiles_per_layer: attention,
    attention_concat_nodes_per_layer: concat,
    concat_logical_output_token_vectors_per_layer: concatUnits,
    guaranteed_strided_mask_cont_nodes_per_layer: maskContNodes,
    guaranteed_strided_mask_cont_logical_F32_bytes_per_layer: maskContElements * 4,
    mask_cont_scope: 'lower-extent views with query width>1 necessarily require cont in the fixed builder; this counts created nodes/logical data, not optimized CUDA launches, and conservatively excludes singleton views',
    logical_F32_mask_elements: maskElements,
    logical_F32_mask_bytes: maskElements * 4,
    minimum_required_graph_key_transitions: requiredBuilds,
    all_calls_rebuilt_if_reuse_disabled: calls.length,
    graph_key_scope: 'width, exact per-row extents, output count; equal key permits but does not prove full reuse. Other input checks and runtime reuse setting unknown.',
    projection_tile_positions: tilePositions, attention_tile_positions: attentionPositions, keys
  };
}
const actual = opportunity.actual_candidate_work.map(e => work(e.case, e.arm, e.append_calls));
function plan(head, n, arm) {
  const calls = [];
  for (let done = 0; done < n;) {
    const position = head + done;
    const width = Math.min(32, n - done, arm === 'W' ? 256 - position % 256 : n);
    calls.push({ position, width, expected_extents: Array.from({ length: width }, (_, i) => Math.ceil((position + i + 1) / 256) * 256) });
    done += width;
  }
  return calls;
}
assert.equal(fixture.head, 232);
assert.equal(fixture.append, 89);
const proposal = ['W', 'L'].map(arm => work('proposed supplied-history append', arm, plan(fixture.head, fixture.append, arm)));
assert.equal(proposal[0].calls, 4);
assert.equal(proposal[1].calls, 3);
assert.deepEqual(proposal[0].projection_tile_positions, proposal[1].projection_tile_positions);
assert.deepEqual(proposal[0].attention_tile_positions, proposal[1].attention_tile_positions);
assert.equal(proposal[1].logical_F32_mask_bytes - proposal[0].logical_F32_mask_bytes, 24576);
assert.equal(proposal[1].attention_concat_nodes_per_layer - proposal[0].attention_concat_nodes_per_layer, 1);
assert.equal(proposal[1].guaranteed_strided_mask_cont_nodes_per_layer, 6);
assert.equal(proposal[0].guaranteed_strided_mask_cont_nodes_per_layer, 0);
assert.equal(proposal[0].minimum_required_graph_key_transitions, 3);
assert.equal(proposal[1].minimum_required_graph_key_transitions, 3);

const c1 = cases.find(x => x.case === 'C1');
const sensitivity = [0.05, 0.1, 0.5, 1, 5, 20, 100].map(netAppendBenefitMs => ({
  assumed_net_append_benefit_ms: netAppendBenefitMs,
  corresponding_current_C1_episode_reduction_percent: netAppendBenefitMs / (c1.W_mean_episode_s * 1000) * 100,
  interpretation: 'hypothesis, not an estimated or measured GPU saving'
}));
const noise = [0.1, 0.5, 1, 5, 10, 50].map(sigma => ({
  assumed_append_pair_sd_ms: sigma,
  known_sigma_normal_95_halfwidth_two_pairs_ms: 1.96 * sigma / Math.sqrt(2),
  known_sigma_normal_approx_80pct_power_MDE_ms: (1.96 + 0.84) * sigma / Math.sqrt(2),
  unknown_sigma_t_df1_95_halfwidth_ms: 12.706204736 * sigma / Math.sqrt(2),
  caveat: 'normal/iid planning assumption only; two ordered pairs do not establish these assumptions or population effects'
}));
const report = {
  status: 'CPU_COST_AND_INFORMATION_YIELD_NO_GO',
  source_PR238: '01d1c98001126ff15fae9fcb49185fe8be20ab76',
  timing_source_PR236: '6597489d01d0fa1fb17dce8bf6cade2c53e3a463',
  benefit_sign: 'positive W minus L favors LOCAL',
  pairs, same_panel_cases: cases, source_derived_actual_append_work: actual,
  source_derived_proposed_append_work: proposal,
  conditional_uniform_call_ceiling_C1_episode_percent: c1.uniform_nonnegative_per_call_cost_ceiling_ms / (c1.W_mean_episode_s * 1000) * 100,
  hypothetical_append_benefit_sensitivity: sensitivity,
  two_pair_noise_sensitivity: noise,
  unknowns: ['append-only wall time and pair variance', 'per-call ledger duration', 'actual ggml graph builds/reuses', 'CUDA primitive/quantizer/concat launch counts and times', 'shape/tail/fusion effects', 'runtime graph reuse enabled/disabled state'],
  decision: 'Do not launch the conditional8-request replay for the current service/paper question. It can supply a descriptive append number, but no established signal/noise or component attribution justifies it; service and natural prevalence remain unidentified.',
  scope_caution: 'Work models are source-derived, not new native/GPU observations. Same-panel scatter is not an append noise estimate. Uniform per-call ceiling is conditional and not a general upper bound.',
  conditionally_authorized: { requests: 8, rows: 2568, deployments: 3 },
  actual_new_consumed: { requests: 0, rows: 0, deployments: 0, GPU_contexts: 0, tokenizer_calls: 0 },
  inputs: inputs.map((file, i) => ({ file, bytes: buffers[i].length, sha256: crypto.createHash('sha256').update(buffers[i]).digest('hex') }))
};
fs.writeFileSync(path.join(out, 'REPORT.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ decision: report.status, cases, proposed_work: proposal.map(x => ({ arm: x.arm, calls: x.calls, mask: x.logical_F32_mask_bytes, concat: x.attention_concat_nodes_per_layer, concat_units: x.concat_logical_output_token_vectors_per_layer, required_graph_transitions: x.minimum_required_graph_key_transitions })) }, null, 2));
