"""Browser regression for source mismatch block and new chat UI (no live AI mocked)."""
from browser_flow import page_with_app
from playwright.sync_api import sync_playwright
from pathlib import Path

ROOT=Path(__file__).parents[1]

def fields(page,i,product,article,cat,price,extra):
    scope=f'[data-offer="{i}"]'
    page.locator(scope+'[data-key="catalogue_id"]').select_option(cat)
    page.locator(scope+'[data-key="model_text"]').fill(product)
    page.locator(scope+'[data-key="article_number"]').fill(article)
    page.locator(scope+'[data-key="quantity"]').fill('1')
    page.locator(scope+'[data-key="unit_price_eur"]').fill(str(price))
    page.locator(scope+'[data-key="vat_basis"]').select_option('gross')
    page.locator(scope+'[data-key="delivery_status"]').select_option('included')
    page.locator(scope+'[data-key="extras_status"]').select_option('entered' if extra else 'none')
    if extra:page.locator(scope+'[data-key="extras_eur"]').fill(str(extra))
    page.locator(scope+'[data-key="labour_status"]').select_option('none')

def run():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page,errors=page_with_app(b,1280,900)
        page.locator('#connection').select_option('G1.5')
        page.locator('#length_mm').select_option('180')
        page.locator('#voltage_v').select_option('230')
        page.locator('#offer-text').fill('Supplier: Berlin Heating Supplies\nProduct: Wilo Yonos PICO 25/1-6-130\nArticle number: 4215516\nProduct price: EUR 400 including VAT')
        page.locator('[data-edit="1"]').click()
        page.locator('#offer-text').fill('Supplier: German Pump Solutions\nProduct: Wilo Yonos PICO 25/1-6\nArticle number: 4215515\nProduct price: EUR 450 including VAT')
        page.locator('#manual-btn').click()
        # Enter wrong selections mirroring the user's earlier screenshot.
        fields(page,0,'Yonos PICO 25/1-4','4215513','wilo-4215513',400,120)
        fields(page,1,'Yonos PICO 25/1-4-130','4215514','wilo-4215514',450,0)
        page.locator('#compare-btn').click()
        page.wait_for_selector('#review-error:not([hidden])',timeout=6000)
        assert 'Original quotation' in page.locator('#review-error').inner_text()
        assert page.locator('#report-state').is_hidden()
        # Now correct the catalogue selection and details without rewriting source evidence.
        fields(page,0,'Yonos PICO 25/1-6-130','4215516','wilo-4215516',400,120)
        fields(page,1,'Yonos PICO 25/1-6','4215515','wilo-4215515',450,0)
        page.locator('#compare-btn').click()
        page.wait_for_selector('#report-state:not([hidden])',timeout=6000)
        assert 'Yonos PICO 25/1-6-130' in page.locator('#report-grid').inner_text()
        assert '520,00' in page.locator('#report-grid').inner_text()
        assert '450,00' in page.locator('#report-grid').inner_text()
        assert page.locator('#advisor-chat').is_visible()
        assert 'Download PDF report' in page.locator('#export-btn').inner_text()
        # The chat form is connected and fails honestly without a configured API key.
        page.locator('#chat-question').fill('Which offer is fully safe to install?')
        page.locator('#chat-send').click()
        page.wait_for_selector('#chat-error:not([hidden])',timeout=6000)
        assert 'OPENAI_API_KEY' in page.locator('#chat-error').inner_text()
        page.screenshot(path=str(ROOT/'preview-revised-report.png'),full_page=True)
        assert not errors,errors
        print('Browser: source mismatch blocked; corrected quote compared; PDF action shown; grounded chat error handled.')
        b.close()

if __name__=='__main__':run()
