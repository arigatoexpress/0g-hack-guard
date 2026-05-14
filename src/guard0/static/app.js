const denySample = {
  action: 'swap',
  mode: 'live_transaction',
  value_eth: 0.05,
  calldata: '0x095ea7b3000000000000000000000000a0b86a33e6776808dc56eb68bb0a0f74ff38ffff',
  requires_signature: true
};
const allowSample = {
  action: 'simulate',
  mode: 'simulation',
  value_eth: 0,
  method: 'eth_call',
  requires_signature: false
};
let latestTelegramChallenge = null;
let latestTelegramRecord = null;

function writeJson(id, value){
  document.getElementById(id).textContent = JSON.stringify(value, null, 2);
}
function sourceStatusLabel(status){
  return {
    reviewed_cache: 'reviewed cache',
    degraded_cache_fallback: 'cache fallback',
    injected_records: 'fixture',
    live_fetch_disabled: 'not live',
    ok: 'live ok'
  }[status] || status || 'unknown';
}
function writeProvenanceSummary(matrix){
  const summary = document.getElementById('provenance-summary');
  if(!matrix || !matrix.coverage){
    return;
  }
  const coverage = matrix.coverage;
  const missing = (matrix.rows || [])
    .filter((row) => !row.evidence || row.evidence.length === 0)
    .map((row) => row.protocol)
    .slice(0, 4);
  const missingText = missing.length ? missing.join(', ') : 'none';
  summary.innerHTML = `
    <div class="metric"><span>Source matches</span><strong class="ok">${coverage.withMatchedEvidence}/${coverage.incidentCount}</strong></div>
    <div class="metric"><span>High confidence</span><strong>${coverage.highConfidenceEvidenceCount}</strong></div>
    <div class="metric"><span>Needs proof</span><strong class="${missing.length ? 'review' : 'ok'}">${coverage.aggregateOnlyCount}</strong></div>
    <div class="metric"><span>Mode</span><strong>${matrix.live ? 'live' : 'cached'}</strong></div>
    <div class="metric"><span>Source</span><strong>${sourceStatusLabel(matrix.sourceStatus.status)}</strong></div>
    <div class="metric"><span>Missing</span><strong class="${missing.length ? 'review' : 'ok'}">${missingText}</strong></div>
  `;
}
function updateDecision(decision){
  const pill = document.getElementById('decision-pill');
  pill.className = 'pill ' + (decision || 'review');
  pill.textContent = decision || 'review';
}
async function evaluateIntent(){
  const body = JSON.parse(document.getElementById('intent-input').value);
  const r = await fetch('/api/evaluate', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({intent: body})
  });
  const j = await r.json();
  updateDecision(j.decision);
  writeJson('result-output', j);
}
async function hackCheck(){
  const body = JSON.parse(document.getElementById('hack-input').value);
  const r = await fetch('/api/hack-check', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(body)
  });
  const j = await r.json();
  writeJson('result-output', j);
}
async function domainCheck(){
  const url = encodeURIComponent(document.getElementById('domain-input').value);
  const r = await fetch('/api/domain?url=' + url);
  const j = await r.json();
  writeJson('result-output', j);
}
async function loadContracts(){
  const r = await fetch('/api/external-action-contracts');
  const j = await r.json();
  writeJson('contract-output', j);
}
async function load0gStatus(){
  const r = await fetch('/api/0g/status');
  const j = await r.json();
  writeJson('zg-status-output', j);
}
async function verifyReceipt(){
  const receiptHash = encodeURIComponent(document.getElementById('verify-receipt-hash').value);
  const r = await fetch('/api/0g/receipt?receipt_hash=' + receiptHash);
  const j = await r.json();
  writeJson('zg-status-output', j);
}
async function loadDataSummary(){
  const r = await fetch('/api/data/summary');
  const j = await r.json();
  writeJson('data-flow-output', j);
}
async function loadProvenanceMatrix(){
  const r = await fetch('/api/data/provenance');
  const j = await r.json();
  writeProvenanceSummary(j);
  writeJson('data-flow-output', j);
}
async function loadLiveProvenanceMatrix(){
  const r = await fetch('/api/data/provenance?live=1');
  const j = await r.json();
  writeProvenanceSummary(j);
  writeJson('data-flow-output', j);
}
async function loadDetectionCoverage(){
  const r = await fetch('/api/data/detection-coverage');
  const j = await r.json();
  writeJson('data-flow-output', j);
}
async function loadSignatureMap(){
  const r = await fetch('/api/data/signature-map');
  const j = await r.json();
  writeJson('data-flow-output', j);
}
async function loadOsintSources(){
  const r = await fetch('/api/osint/sources');
  const j = await r.json();
  writeJson('osint-output', j);
}
async function loadOsintReadiness(){
  const r = await fetch('/api/osint/readiness');
  const j = await r.json();
  writeJson('osint-output', j);
}
async function loadOsintSignals(){
  const r = await fetch('/api/osint/signals?live=1&limit=10');
  const j = await r.json();
  writeJson('osint-output', j);
}
async function loadSubmissionBrief(){
  const r = await fetch('/api/hackathon/submission-brief');
  const j = await r.json();
  writeJson('osint-output', j);
}
async function loadTelegramStatus(){
  const r = await fetch('/api/telegram/status');
  const j = await r.json();
  writeJson('telegram-register-output', j);
}
async function createTelegramRegistration(){
  const userLabel = document.getElementById('telegram-user-label').value;
  const r = await fetch('/api/telegram/registrations', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({user_label:userLabel, scopes:['mira_alerts','security.digest']})
  });
  const j = await r.json();
  latestTelegramChallenge = j.challenge || null;
  writeJson('telegram-register-output', j);
}
async function completeTelegramOptIn(){
  if(!latestTelegramChallenge){
    await createTelegramRegistration();
  }
  const r = await fetch('/api/telegram/opt-ins', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      token_id:latestTelegramChallenge.start_payload,
      telegram_user:{
        id:'demo-local-user',
        username:'demo_operator',
        language_code:'en',
        is_bot:false
      },
      scopes:['mira_alerts','security.digest']
    })
  });
  const j = await r.json();
  latestTelegramRecord = j.record || null;
  writeJson('telegram-register-output', j);
}
async function runMiraPreview(){
  const intent = JSON.parse(document.getElementById('intent-input').value);
  const body = {intent};
  if(latestTelegramRecord && latestTelegramRecord.record_id){
    body.record_id = latestTelegramRecord.record_id;
  }
  const r = await fetch('/api/telegram/mira-preview', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(body)
  });
  const j = await r.json();
  writeJson('mira-output', j);
}
document.getElementById('run-evaluate').addEventListener('click', evaluateIntent);
document.getElementById('run-hack-check').addEventListener('click', hackCheck);
document.getElementById('run-domain-check').addEventListener('click', domainCheck);
document.getElementById('verify-receipt').addEventListener('click', verifyReceipt);
document.getElementById('load-data-summary').addEventListener('click', loadDataSummary);
document.getElementById('load-provenance-matrix').addEventListener('click', loadProvenanceMatrix);
document.getElementById('load-live-provenance').addEventListener('click', loadLiveProvenanceMatrix);
document.getElementById('load-detection-coverage').addEventListener('click', loadDetectionCoverage);
document.getElementById('load-signature-map').addEventListener('click', loadSignatureMap);
document.getElementById('load-osint-sources').addEventListener('click', loadOsintSources);
document.getElementById('load-osint-readiness').addEventListener('click', loadOsintReadiness);
document.getElementById('load-osint-signals').addEventListener('click', loadOsintSignals);
document.getElementById('load-submission-brief').addEventListener('click', loadSubmissionBrief);
document.getElementById('create-telegram-registration').addEventListener('click', createTelegramRegistration);
document.getElementById('complete-telegram-opt-in').addEventListener('click', completeTelegramOptIn);
document.getElementById('run-mira-preview').addEventListener('click', runMiraPreview);
document.getElementById('load-deny-sample').addEventListener('click', () => {
  document.getElementById('intent-input').value = JSON.stringify(denySample, null, 2);
});
document.getElementById('load-allow-sample').addEventListener('click', () => {
  document.getElementById('intent-input').value = JSON.stringify(allowSample, null, 2);
});
loadContracts();
load0gStatus();
loadDataSummary();
loadOsintSources();
loadTelegramStatus();
