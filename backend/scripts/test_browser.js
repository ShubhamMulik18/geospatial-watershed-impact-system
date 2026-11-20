const { spawn } = require('child_process');
const http = require('http');

const BROWSER_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PHOTO_PATH = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\935cb3df-b208-41dd-82ef-3918ed2235ee\\.user_uploaded\\media_1793182873195_11e6a5ea.jpg';

async function main() {
  console.log('Starting headless browser...');
  const browserProc = spawn(BROWSER_PATH, [
    '--headless=new',
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--no-sandbox',
    '--user-data-dir=C:\\Users\\Admin\\AppData\\Local\\Temp\\edge_test_profile'
  ]);

  browserProc.on('error', err => console.error('Browser spawn error:', err));

  // Wait for remote debugging to be ready
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
  console.log('Browser connected. WebSocketDebuggerUrl:', versionData.webSocketDebuggerUrl);

  // Create or get target
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
      console.log('[NETWORK FAILED]', msg.params.errorText, msg.params.canceled, msg.params.type);
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

  // Wait 3 seconds for datasets to load
  await new Promise(r => setTimeout(r, 3000));

  // Check DOM text for datasets
  const evalDatasets = await send('Runtime.evaluate', {
    expression: 'document.body.innerText'
  });
  console.log('--- PAGE TEXT SNIPPET ---');
  console.log(evalDatasets.result.value.substring(0, 500));
  console.log('-------------------------');

  // Find file input element and upload photo
  const doc = await send('DOM.getDocument');
  const fileInputNode = await send('DOM.querySelector', {
    nodeId: doc.root.nodeId,
    selector: 'input[type="file"]'
  });

  if (!fileInputNode.nodeId) {
    console.error('File input not found in DOM!');
  } else {
    console.log('Found file input node. Uploading photo:', PHOTO_PATH);
    await send('DOM.setFileInputFiles', {
      files: [PHOTO_PATH],
      nodeId: fileInputNode.nodeId
    });

    // Wait 4 seconds for OCR upload response and UI update
    await new Promise(r => setTimeout(r, 4000));

    const evalAfterUpload = await send('Runtime.evaluate', {
      expression: 'document.body.innerText'
    });
    console.log('--- PAGE TEXT AFTER PHOTO UPLOAD ---');
    console.log(evalAfterUpload.result.value.substring(0, 800));
    console.log('------------------------------------');

    const screenshot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
    const fs = require('fs');
    fs.writeFileSync('C:\\Users\\Admin\\.gemini\\antigravity\\brain\\935cb3df-b208-41dd-82ef-3918ed2235ee\\browser_verification_success.png', Buffer.from(screenshot.data, 'base64'));
    console.log('Screenshot saved to browser_verification_success.png');
  }

  // Cleanup
  ws.close();
  browserProc.kill();
  console.log('Test complete.');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
