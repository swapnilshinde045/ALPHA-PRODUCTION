const puppeteer = require('puppeteer');

(async () => {
  try {
    const browser = await puppeteer.launch({ headless: 'new' });
    const page = await browser.newPage();
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('BROWSER_CONSOLE_ERROR:', msg.text());
      }
    });

    page.on('pageerror', error => {
      console.log('PAGE_EXCEPTION:', error.message);
    });

    await page.goto('http://localhost:5175', { waitUntil: 'load', timeout: 5000 }).catch(e => console.log("GOTO ERROR:", e.message));
    
    // Wait a brief moment to catch async init errors
    await new Promise(r => setTimeout(r, 2000));
    
    await browser.close();
  } catch(e) {
    console.log("PUPPETEER LAUNCH ERROR:", e.message);
  }
})();
