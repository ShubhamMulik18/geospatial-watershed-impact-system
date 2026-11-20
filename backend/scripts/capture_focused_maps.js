const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const BROWSER_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const ARTIFACT_DIR = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\935cb3df-b208-41dd-82ef-3918ed2235ee';
const ANALYSIS_ID = 'abf3a7b1-7109-4e4e-b029-d8988bc86df7';
const TARGET_URL = `http://localhost:5173/analyses/${ANALYSIS_ID}`;

async function main() {
  const browserProc = spawn(BROWSER_PATH, [
    '--headless=new',
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--no-sandbox',
    '--window-size=1440,1200',
    '--user-data-dir=C:\\Users\\Admin\\AppData\\Local\\Temp\\edge_profile_focused_maps_' + Date.now()
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
  await send('Runtime.enable');
  await send('DOM.enable');

  // Login
  await send('Page.navigate', { url: 'http://localhost:5173/login' });
  await new Promise(r => setTimeout(r, 2000));
  await send('Runtime.evaluate', {
    expression: `
      (() => {
        const setVal = (el, val) => {
          const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
          setter.call(el, val);
          el.dispatchEvent(new Event('input', { bubbles: true }));
        };
        const u = document.querySelector('#username');
        const p = document.querySelector('#password');
        const btn = document.querySelector('button[type="submit"]');
        if (u && p && btn) {
          setVal(u, 'admin');
          setVal(p, 'WatershedAdmin2026!');
          btn.click();
        }
      })()
    `
  });
  await new Promise(r => setTimeout(r, 2000));

  // Navigate to results
  await send('Page.navigate', { url: TARGET_URL });
  await new Promise(r => setTimeout(r, 5000));

  // Scroll to the map comparison section
  await send('Runtime.evaluate', {
    expression: `
      (() => {
        const h2 = Array.from(document.querySelectorAll('h2')).find(el => el.innerText.includes('Satellite Impact Comparison'));
        if (h2) {
          h2.closest('section').scrollIntoView({ behavior: 'instant', block: 'start' });
        }
      })()
    `
  });
  await new Promise(r => setTimeout(r, 1000));

  // Capture focused viewport screenshot of NDVI maps
  const ndviClip = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(ARTIFACT_DIR, 'satellite_maps_ndvi_focused.png'), Buffer.from(ndviClip.data, 'base64'));

  // Switch to MNDWI Water
  await send('Runtime.evaluate', {
    expression: `
      (() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const waterBtn = buttons.find(b => b.innerText.includes('Surface Water (MNDWI)'));
        if (waterBtn) waterBtn.click();
      })()
    `
  });
  await new Promise(r => setTimeout(r, 2000));

  const waterClip = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(ARTIFACT_DIR, 'satellite_maps_water_focused.png'), Buffer.from(waterClip.data, 'base64'));

  console.log('Focused screenshots captured successfully.');
  ws.close();
  browserProc.kill();
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});

