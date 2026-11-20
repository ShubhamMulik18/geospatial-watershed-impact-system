const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const BROWSER_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const ARTIFACT_DIR = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\935cb3df-b208-41dd-82ef-3918ed2235ee';

async function runAuthVerification() {
  console.log('--- Starting Auth E2E Verification ---');
  
  const browserProc = spawn(BROWSER_PATH, [
    '--headless=new',
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--no-sandbox',
    '--window-size=1440,1080',
    '--user-data-dir=C:\\Users\\Admin\\AppData\\Local\\Temp\\edge_auth_profile_' + Date.now()
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
    }
  };

  await new Promise(r => ws.onopen = r);
  await send('Page.enable');
  await send('Runtime.enable');

  async function takeScreenshot(fileName) {
    const result = await send('Page.captureScreenshot', { format: 'png' });
    const buffer = Buffer.from(result.data, 'base64');
    const outPath = path.join(ARTIFACT_DIR, fileName);
    fs.writeFileSync(outPath, buffer);
    console.log(`Saved screenshot: ${outPath} (${buffer.length} bytes)`);
  }

  async function evaluate(expression) {
    const res = await send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise: true
    });
    return res.result?.value;
  }

  try {
    // 1. Navigate to protected dashboard route while unauthenticated
    console.log('Navigating to http://127.0.0.1:5173/dashboard ...');
    await send('Page.navigate', { url: 'http://127.0.0.1:5173/dashboard' });
    await new Promise(r => setTimeout(r, 2000));

    let currentUrl = await evaluate('window.location.href');
    console.log('Current URL after navigation:', currentUrl);
    if (!currentUrl.includes('/login')) {
      throw new Error(`Expected redirection to /login, but got ${currentUrl}`);
    }
    console.log('PASS: Unauthenticated redirect to /login verified.');
    await takeScreenshot('01_login_page.png');

    // 2. Submit wrong password to test error banner
    console.log('Submitting invalid credentials...');
    await evaluate(`
      (() => {
        const setVal = (el, val) => {
          const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
          setter.call(el, val);
          el.dispatchEvent(new Event('input', { bubbles: true }));
        };
        const u = document.querySelector('#username');
        const p = document.querySelector('#password');
        const btn = document.querySelector('button[type="submit"]');
        setVal(u, 'admin');
        setVal(p, 'WrongPassword999!');
        btn.click();
      })()
    `);
    await new Promise(r => setTimeout(r, 1500));

    const alertText = await evaluate(`document.querySelector('[role="alert"]')?.innerText`);
    console.log('Alert banner text:', alertText);
    if (!alertText || !alertText.toLowerCase().includes('invalid')) {
      throw new Error(`Expected invalid credentials alert, but got: ${alertText}`);
    }
    console.log('PASS: Invalid credentials rejected with alert banner.');
    await takeScreenshot('02_login_error.png');

    // 3. Submit valid credentials
    console.log('Submitting valid credentials (admin / WatershedAdmin2026!)...');
    await evaluate(`
      (() => {
        const setVal = (el, val) => {
          const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
          setter.call(el, val);
          el.dispatchEvent(new Event('input', { bubbles: true }));
        };
        const u = document.querySelector('#username');
        const p = document.querySelector('#password');
        const btn = document.querySelector('button[type="submit"]');
        setVal(u, 'admin');
        setVal(p, 'WatershedAdmin2026!');
        btn.click();
      })()
    `);
    await new Promise(r => setTimeout(r, 2500));

    currentUrl = await evaluate('window.location.href');
    console.log('Current URL after login:', currentUrl);
    if (!currentUrl.includes('/dashboard')) {
      throw new Error(`Expected redirection to /dashboard, but got ${currentUrl}`);
    }
    console.log('PASS: Valid login redirects to /dashboard.');

    // 4. Verify user avatar and header elements
    const avatarText = await evaluate(`document.querySelector('[data-testid="user-avatar"]')?.innerText`);
    const displayName = await evaluate(`document.querySelector('[data-testid="user-display-name"]')?.innerText`);
    console.log(`Header user badge: Avatar="${avatarText}", DisplayName="${displayName}"`);
    if (avatarText !== 'AD' || displayName !== 'admin') {
      throw new Error(`Unexpected header user details: Avatar="${avatarText}", DisplayName="${displayName}"`);
    }
    console.log('PASS: Header displays authenticated user credentials.');
    await takeScreenshot('03_dashboard_authenticated.png');

    // 5. Test logout
    console.log('Clicking Log Out button...');
    await evaluate(`document.querySelector('[data-testid="logout-button"]')?.click()`);
    await new Promise(r => setTimeout(r, 1500));

    currentUrl = await evaluate('window.location.href');
    console.log('Current URL after logout:', currentUrl);
    if (!currentUrl.includes('/login')) {
      throw new Error(`Expected redirection to /login after logout, but got ${currentUrl}`);
    }
    console.log('PASS: Logout revokes session and redirects to /login.');
    await takeScreenshot('04_login_after_logout.png');

    console.log('ALL AUTH E2E CHECKS PASSED SUCCESSFULLY!');
  } finally {
    ws.close();
    browserProc.kill();
  }
}

runAuthVerification().catch(err => {
  console.error('E2E Verification failed:', err);
  process.exit(1);
});
