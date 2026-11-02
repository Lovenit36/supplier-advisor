"""Browser interaction smoke tests; container browser cannot navigate localhost directly.
The Playwright page renders real HTML/CSS/JS and fetch requests are bridged to the running local FastAPI server.
No AI calls are mocked or presented as live. The supplier quotes entered below are synthetic test inputs.
"""
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).parents[1]


def page_with_app(browser,width,height):
    def proxy(path,method,body):
        r=requests.request(method,'http://127.0.0.1:8765'+path,json=body if body is not None else None,timeout=4)
        return {'status':r.status_code,'body':r.text}
    page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.expose_function('serverFetch',proxy)
    html=(ROOT/'static/index.html').read_text().replace('<link rel="stylesheet" href="/assets/styles.css">','').replace('<script src="/assets/app.js" defer></script>','')
    page.set_content(html,wait_until='domcontentloaded')
    page.evaluate('''() => {const store=new Map(); Object.defineProperty(window,'sessionStorage',{configurable:true,value:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)}});Object.defineProperty(window.crypto,'randomUUID',{value:()=> '12345678-1111-4111-8111-111111111111'}); window.fetch = async (u,opt={}) => {let data=typeof opt.body === 'string'?JSON.parse(opt.body):null;let r=await window.serverFetch(u,opt.method||'GET',data);return new Response(r.body,{status:r.status,headers:{'Content-Type':'application/json'}});};}''')
    page.add_style_tag(content=(ROOT/'static/styles.css').read_text())
    page.add_script_tag(content=(ROOT/'static/app.js').read_text())
    page.wait_for_timeout(150)
    assert not errors,errors
    return page,errors


def choose(page,i,cat,price,extra_status='none',extra=None):
    page.locator(f'[data-offer="{i}"][data-key="catalogue_id"]').select_option(cat)
    page.locator(f'[data-offer="{i}"][data-key="unit_price_eur"]').fill(str(price))
    page.locator(f'[data-offer="{i}"][data-key="vat_basis"]').select_option('gross')
    page.locator(f'[data-offer="{i}"][data-key="delivery_status"]').select_option('included')
    page.locator(f'[data-offer="{i}"][data-key="extras_status"]').select_option(extra_status)
    if extra is not None:
        page.locator(f'[data-offer="{i}"][data-key="extras_eur"]').fill(str(extra))
    page.locator(f'[data-offer="{i}"][data-key="labour_status"]').select_option('none')


def run():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page,errors=page_with_app(b,1440,990)
        assert page.locator('#empty-state').is_visible()
        assert page.locator('#review-state').is_hidden()
        page.screenshot(path=str(ROOT/'preview-empty.png'),full_page=True)
        page.select_option('#connection','G1.5');page.select_option('#length_mm','180');page.select_option('#voltage_v','230')
        page.click('#manual-btn')
        assert page.locator('#review-state').is_visible()
        choose(page,0,'wilo-4215515',400,'entered',120)
        choose(page,1,'grundfos-99260497',450)
        page.click('#compare-btn')
        page.wait_for_selector('#report-state:not([hidden])',timeout=5000)
        assert 'Offer B' in page.locator('#key-difference').inner_text()
        assert 'Not known' not in page.locator('#report-grid').inner_text()
        assert 'Hydraulic' not in page.locator('#report-grid').inner_text()
        page.locator('.technical-details summary').click()
        assert page.locator('#check-grid').is_visible()
        page.screenshot(path=str(ROOT/'preview-synthetic-desktop.png'),full_page=True)
        print('Desktop: input → review → real local API calculation → expandable evidence OK')
        assert not errors,errors
        page.close()
        page,errors=page_with_app(b,390,844)
        assert page.locator('#empty-state').is_visible()
        assert page.evaluate('document.body.scrollWidth <= window.innerWidth+2'), 'Mobile horizontal overflow'
        page.select_option('#connection','G1.5');page.select_option('#length_mm','130')
        page.click('#manual-btn')
        choose(page,0,'wilo-4215515',200)
        choose(page,1,'wilo-4215516',220)
        page.click('#compare-btn')
        page.wait_for_selector('#report-state:not([hidden])',timeout=5000)
        assert 'confirmed installation conflicts' in page.locator('#summary-banner').inner_text()
        assert page.evaluate('document.body.scrollWidth <= window.innerWidth+2'), 'Mobile report horizontal overflow'
        page.screenshot(path=str(ROOT/'preview-synthetic-mobile.png'),full_page=True)
        print('Mobile: responsive input → conflict result → no horizontal overflow OK')
        assert not errors,errors
        b.close()

if __name__=='__main__':run()
