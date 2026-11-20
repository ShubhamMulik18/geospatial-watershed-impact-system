const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

const BROWSER_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PHOTO_PATH = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\935cb3df-b208-41dd-82ef-3918ed2235ee\\.user_uploaded\\media_1793182873195_11e6a5ea.jpg';
const SCREENSHOT_PATH = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\935cb3df-b208-41dd-82ef-3918ed2235ee\\analysis_workflow_completed.png';

async function main() {
  console.log('Starting headless browser for analysis workflow test...');
  const browserProc = spawn(BROWSER_PATH, [
    '--headless=new',
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--no-sandbox',
    '--user-data-dir=C:\\Users\\Admin\\AppData\\Local\\Temp\\edge_test_profile_analysis'
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
    } else if (msg.method === 'Network.responseReceived') {
      console.log('[NETWORK RESPONSE]', msg.params.response.status, msg.params.response.url);
    } else if (msg.method === 'Network.loadingFailed') {
      console.log('[NETWORK FAILED]', msg.params.errorText, msg.params.type);
    }
  };

  await new Promise(r => ws.onopen = r);
  console.log('Page WebSocket open.');

  await send('Page.enable');
  await send('Network.enable');
  await send('Console.enable');
  await send('Runtime.enable');
  await send('DOM.enable');

  console.log('Navigating to http://localhost:5173/new-analysis...');
  await send('Page.navigate', { url: 'http://localhost:5173/new-analysis' });

  // Wait 3 seconds for initial datasets and page load
  await new Promise(r => setTimeout(r, 3000));

  // Step 1: Upload Photo
  const doc = await send('DOM.getDocument');
  const fileInputNode = await send('DOM.querySelector', {
    nodeId: doc.root.nodeId,
    selector: 'input[type="file"]'
  });

  if (!fileInputNode.nodeId) {
    throw new Error('File input not found');
  }

  console.log('Uploading photo:', PHOTO_PATH);
  await send('DOM.setFileInputFiles', {
    files: [PHOTO_PATH],
    nodeId: fileInputNode.nodeId
  });

  // Wait 4 seconds for OCR extraction and photo metadata
  await new Promise(r => setTimeout(r, 4000));

  // Step 2: Confirm study area polygon via context helper
  console.log('Configuring inputs (polygon, datasets, indicators)...');
  await send('Runtime.evaluate', {
    expression: `
      window.__analysisContext.confirmPolygon({
        type: 'Polygon',
        coordinates: [
          [
            [74.230, 16.660],
            [74.240, 16.660],
            [74.240, 16.670],
            [74.230, 16.670],
            [74.230, 16.660]
          ]
        ]
      });
      window.__analysisContext.setDatasetIds([
        '20260000-0000-0000-0000-000000002026',
        '20230000-0000-0000-0000-000000002023'
      ]);
      window.__analysisContext.setIndicators(['vegetation']);
    `
  });

  await new Promise(r => setTimeout(r, 1000));

  // Step 3: Select Comparison Mode (Before / After) by clicking its button
  console.log('Selecting Comparison Mode...');
  await send('Runtime.evaluate', {
    expression: `
      const buttons = Array.from(document.querySelectorAll('button'));
      const modeBtn = buttons.find(b => b.innerText.includes('Before / After'));
      if (modeBtn) modeBtn.click();
    `
  });

  await new Promise(r => setTimeout(r, 1000));

  // Check state before clicking start
  const stateCheck = await send('Runtime.evaluate', {
    expression: `
      const startBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Start Watershed Analysis'));
      JSON.stringify({
        disabled: startBtn ? startBtn.disabled : 'not found',
        datasetIds: window.__analysisContext.datasetIds,
        indicators: window.__analysisContext.indicators,
        hasConfirmedPolygon: Boolean(window.__analysisContext.confirmedPolygon)
      });
    `
  });
  console.log('State check before start:', stateCheck.result.value);

  // Click Start Watershed Analysis
  console.log('Clicking Start Watershed Analysis button...');
  const clickEval = await send('Runtime.evaluate', {
    expression: `
      (() => {
        const startBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Start Watershed Analysis'));
        if (!startBtn) return 'Button not found';
        if (startBtn.disabled) return 'Button is disabled';
        startBtn.click();
        return 'Button clicked successfully!';
      })()
    `
  });
  console.log('Click evaluation result:', clickEval.result ? clickEval.result.value : clickEval);

  // Poll processing status in UI for up to 15 seconds
  console.log('Polling processing status in browser UI...');
  for (let i = 0; i < 15; i++) {
    await new Promise(r => setTimeout(r, 1000));
    const statusText = await send('Runtime.evaluate', {
      expression: `
        (() => {
          const statusDiv = Array.from(document.querySelectorAll('section')).find(s => s.innerText.includes('Processing Status'));
          return statusDiv ? statusDiv.innerText : document.body.innerText.substring(0, 300);
        })()
      `
    });
    const txt = statusText.result ? statusText.result.value : '';
    console.log(`Poll ${i + 1}s status:`, txt.replace(/\\n/g, ' '));
    if (txt.includes('completed') || txt.includes('Completed') || txt.includes('failed') || txt.includes('Failed')) {
      break;
    }
  }

  // Capture full page screenshot
  console.log('Capturing full-page screenshot...');
  const screenshot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
  fs.writeFileSync(SCREENSHOT_PATH, Buffer.from(screenshot.data, 'base64'));
  console.log('Screenshot saved to:', SCREENSHOT_PATH);

  // Cleanup
  ws.close();
  browserProc.kill();
  console.log('Browser test complete.');
}

main().catch(err => {
  console.error('Error during test:', err);
  process.exit(1);
});
