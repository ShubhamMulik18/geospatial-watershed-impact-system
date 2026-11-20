const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const BROWSER_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const ARTIFACT_DIR = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\935cb3df-b208-41dd-82ef-3918ed2235ee';
const ANALYSIS_ID = 'abf3a7b1-7109-4e4e-b029-d8988bc86df7';
const TARGET_URL = `http://localhost:5173/analyses/${ANALYSIS_ID}`;

async function main() {
  console.log('=== Starting Satellite Raster Layer Verification ===');

  const browserProc = spawn(BROWSER_PATH, [
    '--headless=new',
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--no-sandbox',
    '--window-size=1440,2400',
    '--user-data-dir=C:\\Users\\Admin\\AppData\\Local\\Temp\\edge_profile_raster_test_' + Date.now()
  ]);

  browserProc.on('error', err => console.error('Browser spawn error:', err));

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
    console.error('Failed to connect to browser CDP.');
    browserProc.kill();
    process.exit(1);
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

  const networkResponses = [];

  ws.onmessage = event => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const p = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) p.reject(msg.error);
      else p.resolve(msg.result);
      return;
    }

    if (msg.method === 'Network.responseReceived') {
      const resp = msg.params.response;
      if (resp.url.includes('/artifacts/') || resp.url.includes('/report') || resp.url.includes('/analyses/')) {
        networkResponses.push({
          url: resp.url,
          status: resp.status,
          mimeType: resp.mimeType,
          statusText: resp.statusText,
        });
        console.log(`[NETWORK RESPONSE] ${resp.status} ${resp.url.split('/').slice(-3).join('/')} (${resp.mimeType})`);
      }
    } else if (msg.method === 'Console.messageAdded') {
      console.log('[BROWSER CONSOLE]', msg.params.message.level, msg.params.message.text);
    } else if (msg.method === 'Runtime.consoleAPICalled') {
      console.log('[BROWSER CONSOLE]', msg.params.type, ...msg.params.args.map(a => a.value || a.description));
    }
  };

  await new Promise(r => ws.onopen = r);
  console.log('Page WebSocket open.');

  await send('Page.enable');
  await send('Network.enable');
  await send('Console.enable');
  await send('Runtime.enable');
  await send('DOM.enable');

  // Step 1: Login
  console.log('Navigating to http://localhost:5173/login...');
  await send('Page.navigate', { url: 'http://localhost:5173/login' });
  await new Promise(r => setTimeout(r, 2000));

  console.log('Entering login credentials...');
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
  await new Promise(r => setTimeout(r, 2500));

  // Step 2: Navigate to Analysis Results Dashboard
  console.log(`Navigating to ${TARGET_URL}...`);
  await send('Page.navigate', { url: TARGET_URL });

  // Wait 5 seconds for maps, tiles, and raster overlays to fetch and render
  await new Promise(r => setTimeout(r, 5000));

  // Step 3: Verify Raster Overlays in DOM
  const evalResult = await send('Runtime.evaluate', {
    expression: `
      (() => {
        const imageOverlays = Array.from(document.querySelectorAll('img.leaflet-image-layer'));
        const imagesInfo = imageOverlays.map(img => ({
          src: img.src.substring(0, 100),
          complete: img.complete,
          naturalWidth: img.naturalWidth,
          naturalHeight: img.naturalHeight,
          width: img.width,
          height: img.height,
          display: window.getComputedStyle(img).display,
          opacity: window.getComputedStyle(img).opacity,
        }));

        const panels = Array.from(document.querySelectorAll('.grid > div')).map(p => {
          const title = p.querySelector('h4')?.innerText || '';
          const subtitle = p.querySelector('p')?.innerText || '';
          const crs = p.querySelector('strong')?.innerText || '';
          const hasImg = Boolean(p.querySelector('img.leaflet-image-layer'));
          return { title, subtitle, crs, hasImg };
        });

        return {
          totalImageOverlays: imageOverlays.length,
          images: imagesInfo,
          panels: panels,
          pageTitle: document.title,
          heading: document.querySelector('h1')?.innerText,
        };
      })()
    `,
    returnByValue: true
  });

  console.log('DOM Evaluation Result:', JSON.stringify(evalResult.result.value, null, 2));

  // Step 4: Capture full page screenshot
  console.log('Capturing full dashboard screenshot...');
  const fullScreenshot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
  const fullScreenshotPath = path.join(ARTIFACT_DIR, 'dashboard_with_satellite_layers.png');
  fs.writeFileSync(fullScreenshotPath, Buffer.from(fullScreenshot.data, 'base64'));
  console.log('Saved screenshot to:', fullScreenshotPath);

  // Step 5: Test MNDWI water toggle
  console.log('Toggling indicator to Surface Water (MNDWI)...');
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

  const waterScreenshot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
  const waterScreenshotPath = path.join(ARTIFACT_DIR, 'dashboard_satellite_layers_mndwi.png');
  fs.writeFileSync(waterScreenshotPath, Buffer.from(waterScreenshot.data, 'base64'));
  console.log('Saved MNDWI screenshot to:', waterScreenshotPath);

  console.log('=== Artifact Network Responses Summary ===');
  console.table(networkResponses);

  ws.close();
  browserProc.kill();
  console.log('Verification completed successfully!');
}

main().catch(err => {
  console.error('Error running verification:', err);
  process.exit(1);
});

