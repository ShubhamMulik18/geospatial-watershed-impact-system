const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

const BROWSER_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const ANALYSIS_ID = 'cdab12a3-1c89-4e1e-9af9-d3a87fb3d4bf';
const TARGET_URL = `http://localhost:5173/analyses/${ANALYSIS_ID}`;
const SCREENSHOT_PATH = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\935cb3df-b208-41dd-82ef-3918ed2235ee\\results_dashboard_verified.png';

async function main() {
  console.log(`Starting headless browser to verify Results Dashboard for ${ANALYSIS_ID}...`);
  const browserProc = spawn(BROWSER_PATH, [
    '--headless=new',
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--no-sandbox',
    '--window-size=1440,2200',
    '--user-data-dir=C:\\Users\\Admin\\AppData\\Local\\Temp\\edge_test_profile_results'
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

  ws.onmessage = event => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const p = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) p.reject(msg.error);
      else p.resolve(msg.result);
      return;
    }

    if (msg.method === 'Console.messageAdded') {
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

  console.log(`Navigating to ${TARGET_URL}...`);
  await send('Page.navigate', { url: TARGET_URL });

  // Wait 4 seconds for analysis results and leaflet map to load
  await new Promise(r => setTimeout(r, 4000));

  // Extract page content details to verify
  const pageVerification = await send('Runtime.evaluate', {
    expression: `
      (() => {
        const text = document.body.innerText;
        return {
          hasDashboardTitle: text.includes('Watershed Results Dashboard'),
          hasVerifiedScientificResults: text.includes('Verified Scientific Results'),
          hasScientificMeasurements: text.includes('Scientific Measurements'),
          hasBeforeAndAfter: text.includes('Before and After Comparison'),
          hasMultiDate: text.includes('Multi-date Measurements'),
          hasGeospatialLayers: text.includes('Geospatial Result Layers'),
          hasDownloadReport: text.includes('Download Report'),
          hasDevelopmentAdapterWarning: text.includes('Development geospatial adapter does not perform scientific analysis'),
          bodySnippet: text.substring(0, 1000)
        };
      })()
    `,
    returnByValue: true
  });

  console.log('Verification result:', JSON.stringify(pageVerification.result.value, null, 2));

  // Capture full page screenshot
  console.log('Capturing full-page screenshot of Results Dashboard...');
  const screenshot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
  fs.writeFileSync(SCREENSHOT_PATH, Buffer.from(screenshot.data, 'base64'));
  console.log('Screenshot saved to:', SCREENSHOT_PATH);

  // Cleanup
  ws.close();
  browserProc.kill();
  console.log('Browser verification completed successfully.');
}

main().catch(err => {
  console.error('Error during test:', err);
  process.exit(1);
});
