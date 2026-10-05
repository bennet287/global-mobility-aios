// Operational probe: no fixture routing, trace, HAR, screenshot, or storage export.
import { createRequire } from 'node:module';
import { createHmac, timingSafeEqual } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
const require = createRequire(new URL('../apps/web/e2e/package.json', import.meta.url));
let browser;
const proof = {};
function check(value) { if (!value) throw new Error('probe_failed'); }
async function readInput() {
  let input = ''; for await (const chunk of process.stdin) {
    input += chunk; check(Buffer.byteLength(input) <= 4194304);
  }
  return JSON.parse(input);
}
export function verifiedClaims(token, key, ttl) {
  const [payload, signature, extra] = token.split('.'); check(!extra && payload && signature);
  const expected = createHmac('sha256', key).update(payload).digest('hex');
  check(signature.length === expected.length && timingSafeEqual(Buffer.from(signature), Buffer.from(expected)));
  const claims = JSON.parse(Buffer.from(payload, 'base64url').toString());
  check(claims.v === 1 && Number.isInteger(claims.iat) && Number.isInteger(claims.exp));
  check(claims.exp - claims.iat === ttl && Math.abs(Date.now()/1000 - claims.iat) < 60);
  return claims;
}
async function main() {
try {
  const config = await readInput();
  const { chromium } = require('@playwright/test');
  check(config.api.startsWith('https://') && config.web.startsWith('https://'));
  check(Number.isInteger(config.ttl) && config.ttl >= 300 && config.ttl <= 86400);
  check(config.maxWait >= config.ttl + 10 && config.maxWait <= 86520);
  browser = await chromium.launch({headless: true});
  const context = await browser.newContext({ignoreHTTPSErrors: false, serviceWorkers: 'block'});
  const page = await context.newPage();
  page.setDefaultTimeout(30000);
  // Observe original compiled fetch arguments. Never change arguments or responses.
  await page.addInitScript(({ api }) => {
    const native = window.fetch;
    window.__phase22Requests = [];
    window.fetch = function(input, init) {
      const url = new URL(typeof input === 'string' ? input : input.url, location.href);
      if (url.origin === api && url.pathname === '/api/v1/organization/activities') {
        const headers = new Headers(init?.headers || (input instanceof Request ? input.headers : undefined));
        window.__phase22Requests.push({credentials: init?.credentials ?? input.credentials,
          roleHeader: headers.has('x-gmai-role'), userHeader: headers.has('x-gmai-user')});
      }
      return native.apply(this, arguments);
    };
  }, { api: config.api });
  async function boundedJson(response) {
    check(Number(response.headers()['content-length'] || 0) <= 2_000_000);
    const text = await response.text(); check(Buffer.byteLength(text) <= 2_000_000); return JSON.parse(text);
  }
  async function compiled(status) {
    const responsePromise = page.waitForResponse(r => {
      const url = new URL(r.url());
      return url.origin === config.api && url.pathname === '/api/v1/organization/activities' && r.request().method() === 'GET';
    });
    await page.goto(config.web + '/cockpit/v2', {waitUntil:'domcontentloaded'});
    const response = await responsePromise;
    check(response.status() === status);
    const observations = await page.evaluate(() => window.__phase22Requests);
    check(observations.length && observations.every(x => x.credentials === 'include' && !x.roleHeader && !x.userHeader));
    if (status === 200) {
      const body = await boundedJson(response); check(Array.isArray(body.data) && Number.isInteger(body.total) && Number.isInteger(body.total_pages) && body.page===1 && body.page_size===12);
      const headers = await response.request().allHeaders(); check(Boolean(headers.cookie));
      check(response.headers()['access-control-allow-origin'] === config.web);
      check(response.headers()['access-control-allow-credentials'] === 'true');
    }
    check((await page.content()).length < 2_000_000);
    return await page.content();
  }
  async function login(ctx, role, username = config.username, password = config.password) {
    const p = await ctx.newPage();
    await p.goto(config.api + '/auth/login');
    const html = await p.content();
    check(html.length<2_000_000 && !html.includes('Default local credentials') && !html.includes(config.password));
    check(await p.locator('#username').inputValue()==='');
    await p.locator('#username').fill(username); await p.locator('#password').fill(password);
    await p.locator('#role').selectOption(role);
    const pending = p.waitForResponse(r => new URL(r.url()).pathname === '/auth/login' && r.request().method() === 'POST');
    await p.getByRole('button', {name:'Sign in', exact:true}).click();
    const response = await pending;
    await p.close(); return response;
  }
  async function status(ctx, path, expected, headers = {}) {
    const r = await ctx.request.get(config.api + path, {headers, maxRedirects:0}); check(r.status() === expected); return r;
  }
  await compiled(401); proof.unauthenticated_denial_verified = true;
  const cors401=await status(context,'/debug/controlled-agents',401,{Origin:config.web});
  check(cors401.headers()['access-control-allow-origin']===config.web && cors401.headers()['access-control-allow-credentials']==='true');
  await status(context, '/debug/controlled-agents', 401, {'X-GMAI-Role':'admin', 'X-GMAI-User':'forged'});
  proof.forged_header_denial_verified = true;
  for (const [username,password] of [['admin','admin'],[config.username,'phase22-invalid-' + Date.now()]]) {
    const denied = await browser.newContext();
    const result = await login(denied,'admin',username,password);
    check(result.status() === 200 && !(await denied.cookies()).some(c => c.name === config.cookieName));
    await status(denied,'/debug/controlled-agents',401); await denied.close();
  }
  proof.default_invalid_login_denial_verified = true;
  const issuedMonotonic=performance.now(); const issuedWall=Date.now();
  const loginResponse = await login(context,'admin'); check(loginResponse.status() === 303);
  const setCookie = (await loginResponse.headersArray()).filter(h=>h.name.toLowerCase()==='set-cookie').map(h=>h.value).find(h=>h.startsWith(config.cookieName+'='));
  check(setCookie && /;\s*Secure(?:;|$)/i.test(setCookie) && /;\s*HttpOnly(?:;|$)/i.test(setCookie));
  check(/;\s*SameSite=Lax(?:;|$)/i.test(setCookie) && !/;\s*Domain=/i.test(setCookie));
  check(new RegExp(';\\s*Max-Age=' + config.ttl + '(?:;|$)','i').test(setCookie));
  const cookies = await context.cookies(config.api);
  const cookie = cookies.find(c=>c.name===config.cookieName);
  check(cookie && cookie.secure && cookie.httpOnly && cookie.sameSite==='Lax' && cookie.domain===new URL(config.api).hostname && cookie.path==='/');
  check(Math.abs(cookie.expires - Date.now()/1000 - config.ttl)<60);
  const originalToken = cookie.value;
  const claims = verifiedClaims(originalToken,config.jwt,config.ttl); check(claims.role==='admin' && claims.username===config.username);
  proof.cookie_policy_verified = true;
  await status(context,'/debug/controlled-agents',200);
  const me = await status(context,'/auth/me',200); check((await me.json()).role==='admin');
  proof.browser_login_verified = true;
  const html = await compiled(200);
  check(!config.secrets.some(s=>html.includes(s))); proof.rendered_page_scan_verified=true;
  proof.web_compiled_request_verified = true;
  const restricted = await browser.newContext(); await login(restricted,'read_only');
  const restrictedCookie=(await restricted.cookies(config.api)).find(c=>c.name===config.cookieName);
  check(restrictedCookie && verifiedClaims(restrictedCookie.value,config.jwt,config.ttl).role==='read_only');
  const corsDeniedRole=await status(restricted,'/debug/controlled-agents',403,{Origin:config.web});
  check(corsDeniedRole.headers()['access-control-allow-origin']===config.web && corsDeniedRole.headers()['access-control-allow-credentials']==='true');
  const restrictedPage = await restricted.newPage(); await restrictedPage.goto(config.web + '/cockpit/v2');
  const cors403 = await restrictedPage.evaluate(async api=> {
    const r=await fetch(api+'/debug/controlled-agents',{credentials:'include'});
    return {status:r.status(),allowed:r.headers.get('access-control-allow-origin')};
  },config.api); check(cors403.status===403); await restricted.close();
  proof.signed_role_denial_verified=true;
  const approved = await context.request.fetch(config.api+'/debug/controlled-agents',{method:'OPTIONS',headers:{Origin:config.web,'Access-Control-Request-Method':'GET'}});
  check(approved.status()===200 && approved.headers()['access-control-allow-origin']===config.web && approved.headers()['access-control-allow-credentials']==='true');
  const deniedOrigin = 'https://phase22-denied.invalid';
  const rejected = await context.request.fetch(config.api+'/debug/controlled-agents',{method:'OPTIONS',headers:{Origin:deniedOrigin,'Access-Control-Request-Method':'GET'}});
  check(rejected.status()===400 && !rejected.headers()['access-control-allow-origin']);
  const nullOriginResponse=await context.request.get(config.api+'/debug/controlled-agents',{headers:{Origin:'null'}});
  check(nullOriginResponse.status()===200 && !nullOriginResponse.headers()['access-control-allow-origin']);
  const crossOriginDenied = await page.evaluate(api => new Promise(resolve => {
    const frame=document.createElement('iframe'); frame.sandbox='allow-scripts';
    const marker='phase22-cors-'+Math.random();
    const timer=setTimeout(()=>{frame.remove();resolve(false)},15000);
    const handler=event=>{if(event.source===frame.contentWindow && event.data?.marker===marker){
      clearTimeout(timer);window.removeEventListener('message',handler);frame.remove();resolve(event.data.denied===true)}};
    window.addEventListener('message',handler);
    frame.srcdoc='<script>fetch('+JSON.stringify(api+'/debug/controlled-agents')+', {credentials:"include"})'
      +'.then(()=>parent.postMessage({marker:'+JSON.stringify(marker)+',denied:false},"*"))'
      +'.catch(()=>parent.postMessage({marker:'+JSON.stringify(marker)+',denied:true},"*"))</script>';
    document.body.append(frame);
  }),config.api); check(crossOriginDenied);
  proof.cors_verified=true;
  const until = (claims.exp*1000 - Date.now()) + 2500;
  check(until > 0 && until <= config.maxWait*1000);
  // No clock override, TTL mutation, cookie deletion or fabricated expired token.
  await new Promise(resolve=>setTimeout(resolve,Math.max(until,config.ttl*1000+1000)));
  const monotonicElapsed=(performance.now()-issuedMonotonic)/1000;
  check(monotonicElapsed>=config.ttl && Math.abs((Date.now()-issuedWall)/1000-monotonicElapsed)<5);
  await compiled(401);
  proof.real_session_expiry_verified=true;
  const renewed = await browser.newContext(); await login(renewed,'admin'); await status(renewed,'/debug/controlled-agents',200);
  const renewedCookie=(await renewed.cookies(config.api)).find(c=>c.name===config.cookieName);
  check(renewedCookie && verifiedClaims(renewedCookie.value,config.jwt,config.ttl).role==='admin');
  const replay = await renewed.request.get(config.api+'/debug/controlled-agents',{headers:{Cookie:config.cookieName+'='+originalToken}});
  check(replay.status()===401); await renewed.close(); proof.expired_token_replay_denied=true;
  proof.waited_seconds = Math.floor(monotonicElapsed);
  await context.close();
  console.log(JSON.stringify({proof}));
} catch {
  console.log(JSON.stringify({failure_code:'browser_probe_failed'})); process.exitCode=1;
} finally { if(browser) await browser.close().catch(()=>{}); }

}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) await main();
