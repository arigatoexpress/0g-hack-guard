const telegramApp = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
const telegramInitData = telegramApp && telegramApp.initData ? telegramApp.initData : '';

function miniappWriteJson(id, value){
  document.getElementById(id).textContent = JSON.stringify(value, null, 2);
}

function miniappSetPill(id, text, state){
  const node = document.getElementById(id);
  node.textContent = text;
  node.className = `pill ${state}`;
}

async function miniappPostJson(url, payload){
  const response = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  const body = await response.json().catch(() => ({error: response.statusText}));
  if(!response.ok){
    const error = new Error(body.error || response.statusText);
    error.payload = body;
    throw error;
  }
  return body;
}

function miniappBuildIntent(){
  const kind = document.getElementById('miniapp-intent-kind').value;
  const to = document.getElementById('miniapp-to').value;
  const chain = document.getElementById('miniapp-chain').value;
  const asset = document.getElementById('miniapp-asset').value;
  const amount = document.getElementById('miniapp-amount').value;
  if(kind === 'simulation'){
    return {
      action: 'read_balance',
      mode: 'simulation',
      method: 'eth_getBalance',
      requires_signature: false,
      chain
    };
  }
  if(kind === 'transfer'){
    return {
      type: 'transfer',
      asset,
      amount,
      to,
      chain
    };
  }
  return {
    action: 'approve',
    mode: 'live_transaction',
    requires_signature: true,
    target_contract: to,
    chain,
    asset,
    prompt_text: `Approve unlimited ${asset} allowance for ${to} on ${chain}.`,
    calldata: '0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
  };
}

function miniappPreviewPayload(){
  const payload = {
    address: document.getElementById('miniapp-wallet-address').value,
    intent: miniappBuildIntent(),
    max_alerts: 3
  };
  if(telegramInitData){
    payload.initData = telegramInitData;
  }
  return payload;
}

function miniappTonPayload(){
  const payload = {
    address: document.getElementById('miniapp-ton-address').value,
    network: 'mainnet',
    intent: {
      surface: 'telegram_mini_app',
      context: 'TON Risk Passport preview before any wallet prompt',
      walletAlertDecision: document.getElementById('miniapp-verdict').textContent
    },
    include_activity: false,
    live: false
  };
  if(telegramInitData){
    payload.initData = telegramInitData;
  }
  return payload;
}

function miniappRenderPreview(data){
  const verdict = data.uiSummary && data.uiSummary.verdict ? data.uiSummary.verdict : 'review';
  const reason = data.uiSummary && data.uiSummary.topReason ? data.uiSummary.topReason : 'No reason returned.';
  const message = data.message || 'No message preview returned.';
  document.getElementById('miniapp-flow').dataset.verdict = verdict;
  document.getElementById('miniapp-verdict').textContent = verdict;
  document.getElementById('miniapp-reason').textContent = reason;
  document.getElementById('miniapp-alert-message').textContent = message;
  miniappWriteJson('miniapp-output', data);
  miniappWriteJson('miniapp-mira-output', data.mira);
  miniappWriteJson('miniapp-quality-output', data.qualityPolicy);
}

async function miniappLoadSession(){
  const payload = telegramInitData ? {initData: telegramInitData} : {};
  try{
    const data = await miniappPostJson('/api/telegram/miniapp/session', payload);
    const isTelegram = data.launch && data.launch.openedInsideTelegram;
    const isValidated = data.auth && data.auth.validated;
    miniappSetPill(
      'miniapp-mode',
      isTelegram ? 'Telegram launch' : 'browser preview',
      isTelegram ? 'review' : 'allow'
    );
    miniappSetPill(
      'miniapp-auth-status',
      isValidated ? 'session verified' : 'local preview',
      isValidated ? 'allow' : 'deny'
    );
    miniappWriteJson('miniapp-session-output', data);
    miniappWriteJson('miniapp-quality-output', data.qualityPolicy);
  } catch(error){
    miniappSetPill('miniapp-auth-status', 'auth blocked', 'deny');
    miniappWriteJson('miniapp-session-output', error.payload || {error: error.message});
  }
}

async function miniappRunPreview(){
  const button = document.getElementById('miniapp-preview-alert');
  button.disabled = true;
  document.getElementById('miniapp-alert-message').textContent = 'Checking wallet intent...';
  try{
    const data = await miniappPostJson('/api/telegram/miniapp/preview', miniappPreviewPayload());
    miniappRenderPreview(data);
  } catch(error){
    const payload = error.payload || {error: error.message};
    miniappWriteJson('miniapp-output', payload);
    document.getElementById('miniapp-alert-message').textContent = payload.error || error.message;
  } finally {
    button.disabled = false;
  }
}

async function miniappRunMira(){
  const button = document.getElementById('miniapp-run-mira');
  button.disabled = true;
  try{
    const data = await miniappPostJson('/api/telegram/miniapp/preview', miniappPreviewPayload());
    miniappWriteJson('miniapp-mira-output', data.mira);
    if(data.mira && data.mira.message){
      document.getElementById('miniapp-alert-message').textContent = data.mira.message;
    }
  } catch(error){
    miniappWriteJson('miniapp-mira-output', error.payload || {error: error.message});
  } finally {
    button.disabled = false;
  }
}

async function miniappRunTonPreview(){
  const button = document.getElementById('miniapp-preview-ton');
  button.disabled = true;
  try{
    const data = await miniappPostJson('/api/telegram/miniapp/ton-preview', miniappTonPayload());
    miniappWriteJson('miniapp-ton-output', data);
    if(data.message){
      document.getElementById('miniapp-alert-message').textContent = data.message;
    }
  } catch(error){
    miniappWriteJson('miniapp-ton-output', error.payload || {error: error.message});
  } finally {
    button.disabled = false;
  }
}

function miniappWireTelegramChrome(){
  if(!telegramApp){
    return;
  }
  telegramApp.ready();
  telegramApp.expand();
  if(telegramApp.themeParams && telegramApp.themeParams.bg_color){
    document.documentElement.style.setProperty('--bg', telegramApp.themeParams.bg_color);
  }
  if(telegramApp.MainButton){
    telegramApp.MainButton.setText('Preview alert');
    telegramApp.MainButton.onClick(miniappRunPreview);
    telegramApp.MainButton.show();
  }
}

document.getElementById('miniapp-preview-alert').addEventListener('click', miniappRunPreview);
document.getElementById('miniapp-run-mira').addEventListener('click', miniappRunMira);
document.getElementById('miniapp-preview-ton').addEventListener('click', miniappRunTonPreview);
miniappWireTelegramChrome();
miniappLoadSession();
