const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

const BROWSER_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const ARTIFACT_DIR = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\935cb3df-b208-41dd-82ef-3918ed2235ee';

async function captureUrl(url, outputPath, delayMs = 3000) {
  console.log(`Navigating to ${url}...`);
  const browserProc = spawn(BROWSER_PATH, [
    '--headless=new',
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--no-sandbox',
    '--window-size=1440,2400',
    '--user-data-dir=C:\\Users\\Admin\\AppData\\Local\\Temp\\edge_profile_' + Date.now()
  ]);

  let versionData = null;
  for (let i = 0; i < 20; i++) {
    await new Promise(r => setTimeout(r, 500));
    try {
      versionData = await new Promise((resolve, reject) => {
        http.get('http://127.0.0.1:9222/json/version', res => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => resolve(JSON.parse(data)));
        }).on('error', reject);
      });
      if (versionData) break;
    } catch {}
  }

  if (!versionData) {
    console.error('Failed to connect to CDP.');
    browserProc.kill();
    return;
  }

  const targets = await new Promise((resolve, reject) => {
    http.get('http://127.0.0.1:9222/json/list', res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    }).on('error', reject);
  });

  const pageTarget = targets.find(t => t.type === 'page') || targets[0];
  const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
  let id = 1;
  const pending = new Map();

  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const msgId = id++;
      pending.set(msgId, { resolve, reject });
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });
  }

  ws.onmessage = event => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const p = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) p.reject(msg.error);
      else p.resolve(msg.result);
    }
  };

  await new Promise(r => ws.onopen = r);
  await send('Page.enable');
  await send('Page.navigate', { url });
  await new Promise(r => setTimeout(r, delayMs));

  const screenshot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
  fs.writeFileSync(outputPath, Buffer.from(screenshot.data, 'base64'));
  console.log(`Screenshot saved: ${outputPath} (${fs.statSync(outputPath).size} bytes)`);

  ws.close();
  browserProc.kill();
}

async function main() {
  try {
    await captureUrl('http://localhost:5173/', `${ARTIFACT_DIR}\\dashboard_verified_v3.png`, 3000);
    await captureUrl('http://localhost:5173/analyses/303af3e9-fbd5-496d-930e-5144661b62fc', `${ARTIFACT_DIR}\\results_3dates_verified.png`, 4000);
  } catch (err) {
    console.error('Verification failed:', err);
  }
}

main();

