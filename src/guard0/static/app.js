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
loadTelegramStatus();
