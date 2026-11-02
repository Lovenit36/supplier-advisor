"""Regression tests from the Nov 2 AI-review mismatch and new PDF/chat workflow."""
import io
import fitz
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import CompareInput
from app.rules import analyze

client=TestClient(app)

def data():
    return {'installation':{'existing_model':'Yonos PICO 25/1-6','connection':'G1.5','length_mm':180,'voltage_v':230,'medium':'heating_water','labour_rate_eur':60},'offers':[
        {'supplier_name':'Berlin Heating Supplies','catalogue_id':'wilo-4215516','model_text':'Yonos PICO 25/1-6-130','article_number':'4215516','source_text':'Product: Wilo Yonos PICO 25/1-6-130\nArticle number: 4215516','quantity':1,'unit_price_eur':400,'vat_basis':'gross','delivery_status':'included','extras_status':'entered','extras_eur':120,'labour_status':'none'},
        {'supplier_name':'German Pump Solutions','catalogue_id':'wilo-4215515','model_text':'Yonos PICO 25/1-6','article_number':'4215515','source_text':'Product: Wilo Yonos PICO 25/1-6\nArticle number: 4215515','quantity':1,'unit_price_eur':450,'vat_basis':'gross','delivery_status':'included','extras_status':'none','labour_status':'none'}]}

def test_correct_quote_products_and_conflict():
    r=client.post('/api/supplier/analyze',json=data())
    assert r.status_code==200
    d=r.json()
    assert d['results'][0]['product']['article']=='4215516'
    assert d['results'][1]['product']['article']=='4215515'
    assert d['results'][0]['fit']['status']=='conflict'
    assert d['results'][1]['fit']['status']=='checks_pending'
    assert d['results'][0]['cost']['total_gross']==520
    assert d['results'][1]['cost']['total_gross']==450

def test_user_facing_original_screen_failure_is_blocked():
    payload=data()
    payload['offers'][0].update(catalogue_id='wilo-4215513',article_number='4215513',model_text='Yonos PICO 25/1-4')
    payload['offers'][1].update(catalogue_id='wilo-4215514',article_number='4215514',model_text='Yonos PICO 25/1-4-130')
    r=client.post('/api/supplier/analyze',json=payload)
    assert r.status_code==422
    assert 'Original quotation' in r.json()['detail']
    assert '4215516' in r.json()['detail']

def test_source_excerpt_mismatch_blocked_without_original_text():
    payload=data()
    payload['offers'][0]['source_text']=''
    payload['offers'][0]['evidence']=['Product: Wilo Yonos PICO 25/1-6-130','Article number: 4215516']
    payload['offers'][0].update(catalogue_id='wilo-4215513',article_number='4215513',model_text='Yonos PICO 25/1-4')
    r=client.post('/api/supplier/analyze',json=payload)
    assert r.status_code==422

def test_pdf_export_is_valid_and_contains_actual_compared_models():
    r=client.post('/api/supplier/report.pdf',json=data())
    assert r.status_code==200
    assert r.headers['content-type']=='application/pdf'
    assert r.content.startswith(b'%PDF')
    with fitz.open(stream=r.content,filetype='pdf') as pdf:
        content='\n'.join(page.get_text() for page in pdf)
        assert 'Supplier' in content
        assert 'Yonos PICO 25/1-6-130' in content
        assert 'Yonos PICO 25/1-6' in content
        assert '520.00' in content and '450.00' in content
        assert 'Not an installation approval' in content

def test_pdf_rejects_mismatched_source():
    d=data()
    d['offers'][0]['catalogue_id']='wilo-4215513'
    assert client.post('/api/supplier/report.pdf',json=d).status_code==422

def test_chat_no_key_honestly_fails(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    r=client.post('/api/supplier/chat',json={'comparison':data(),'question':'Which one should I order?'})
    assert r.status_code==503
    assert 'OPENAI_API_KEY' in r.json()['detail']

def test_chat_send_verified_context_and_no_raw_quote(monkeypatch):
    from app import chat
    observed={}
    class FakeResponse:
        status_code=200
        def json(self):return {'choices':[{'message':{'content':'Offer B has a lower entered installed cost, but hydraulic fit is still unverified.'}}]}
    class FakeClient:
        def __init__(self, **kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,url,headers,json):
            observed.update(json)
            return FakeResponse()
    monkeypatch.setenv('OPENAI_API_KEY','unit-test-secret')
    monkeypatch.setattr(chat.httpx,'AsyncClient',FakeClient)
    d=data()
    d['offers'][0]['source_text']='Original secret quotation note: ABC123\n'+d['offers'][0]['source_text']
    r=client.post('/api/supplier/chat',json={'comparison':d,'question':'Which pump has a confirmed fit?'})
    assert r.status_code==200
    assert 'hydraulic' in r.json()['answer']
    assert 'temperature' not in observed
    assert observed['reasoning_effort']=='low'
    assert 'ABC123' not in str(observed)
    assert '4215516' in str(observed)


def test_source_evidence_blocks_different_article_without_catalogue_selection():
    d=data()
    d['offers'][0].update(catalogue_id='',article_number='4215513',model_text='Yonos PICO 25/1-4')
    r=client.post('/api/supplier/analyze',json=d)
    assert r.status_code==422 and 'Original quotation' in r.json()['detail']

def test_unknown_article_is_not_falsely_approved():
    d=data()
    d['offers'][0].update(catalogue_id='',article_number='9988776',model_text='Unrecognised pump')
    r=client.post('/api/supplier/analyze',json=d)
    assert r.status_code==200
    assert r.json()['results'][0]['fit']['status']=='cannot_verify'
