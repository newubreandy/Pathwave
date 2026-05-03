import puppeteer from 'puppeteer';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const EXPORT_DIR = path.join(__dirname, '..', '.figma-exports', 'current-web');

const pages = [
  { name: '01_로그인', path: '/login', waitFor: 1000 },
  { name: '02_회원가입', path: '/signup', waitFor: 1000 },
  { name: '03_대시보드', path: '/dashboard', waitFor: 1500 },
  { name: '04_매장정보', path: '/dashboard/store', waitFor: 1500 },
  { name: '05_와이파이설정', path: '/dashboard/wifi', waitFor: 1000 },
  { name: '06_직원관리', path: '/dashboard/staff', waitFor: 1000 },
  { name: '07_알림관리', path: '/dashboard/notifications', waitFor: 1000 },
  { name: '08_스탬프관리', path: '/dashboard/stamps', waitFor: 1000 },
  { name: '09_스탬프등록', path: '/dashboard/stamps/create', waitFor: 1000 },
  { name: '10_쿠폰관리', path: '/dashboard/coupons', waitFor: 1000 },
  { name: '11_쿠폰등록', path: '/dashboard/coupons/create', waitFor: 1000 },
  { name: '12_결제관리', path: '/dashboard/payments', waitFor: 1000 },
  { name: '13_설정', path: '/dashboard/settings', waitFor: 1000 },
  { name: '14_고객채팅', path: '/dashboard/chat', waitFor: 1000 },
  { name: '15_리포트', path: '/dashboard/report', waitFor: 1000 },
];

async function capturePages() {
  const browser = await puppeteer.launch({ headless: true });
  
  // Mobile viewport (390 x 844)
  for (const page of pages) {
    try {
      const tab = await browser.newPage();
      await tab.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });
      await tab.goto(`http://localhost:5173${page.path}`, { waitUntil: 'networkidle2', timeout: 10000 });
      await new Promise(r => setTimeout(r, page.waitFor));
      await tab.screenshot({
        path: path.join(EXPORT_DIR, `mobile_${page.name}.png`),
        fullPage: true
      });
      console.log(`✅ Mobile captured: ${page.name}`);
      await tab.close();
    } catch (e) {
      console.log(`❌ Failed: ${page.name} - ${e.message}`);
    }
  }
  
  // PC viewport (1440 x 900) - key pages only
  const pcPages = pages.filter(p => ['01_로그인', '03_대시보드', '04_매장정보', '07_알림관리', '08_스탬프관리', '09_스탬프등록', '10_쿠폰관리'].includes(p.name));
  for (const page of pcPages) {
    try {
      const tab = await browser.newPage();
      await tab.setViewport({ width: 1440, height: 900, deviceScaleFactor: 2 });
      await tab.goto(`http://localhost:5173${page.path}`, { waitUntil: 'networkidle2', timeout: 10000 });
      await new Promise(r => setTimeout(r, page.waitFor));
      await tab.screenshot({
        path: path.join(EXPORT_DIR, `pc_${page.name}.png`),
        fullPage: true
      });
      console.log(`✅ PC captured: ${page.name}`);
      await tab.close();
    } catch (e) {
      console.log(`❌ PC Failed: ${page.name} - ${e.message}`);
    }
  }
  
  await browser.close();
  console.log('\n🎉 All pages captured!');
}

capturePages();
