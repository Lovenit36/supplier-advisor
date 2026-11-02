from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_health_and_catalogue_live_local_api():
    assert client.get('/health').status_code==200
    obj=client.get('/api/catalogue').json()
    assert len(obj['products'])==9
    assert client.get('/').status_code==200
    assert 'Compatibility Advisor' in client.get('/').text

def test_manual_api_flow_with_manufacturer_match_and_real_cost_math():
    payload={'installation':{'connection':'G1.5','length_mm':180,'voltage_v':230,'medium':'heating_water','labour_rate_eur':80},'offers':[
        {'catalogue_id':'wilo-4215515','model_text':'Yonos PICO 25/1-6','article_number':'4215515','quantity':1,'unit_price_eur':400,'vat_basis':'gross','delivery_status':'included','extras_status':'entered','extras_eur':50,'labour_status':'entered','labour_hours':1},
        {'catalogue_id':'grundfos-99260497','model_text':'ALPHA2 25-40 180','article_number':'99260497','quantity':1,'unit_price_eur':450,'vat_basis':'gross','delivery_status':'included','extras_status':'none','labour_status':'none'}]}
    r=client.post('/api/supplier/analyze',json=payload)
    assert r.status_code==200
    d=r.json()
    assert d['results'][0]['cost']['total_gross']==530
    assert d['results'][1]['cost']['total_gross']==450
    assert d['status']=='checks_pending'
    assert 'Offer B' in d['price_message']
    assert d['results'][0]['fit']['checks'][0]['source'].startswith('https://')

def test_missing_ai_key_fails_closed(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    r=client.post('/api/supplier/extract',data={'offer_a':'Wilo Yonos PICO 25/1-6 for €100','offer_b':'Grundfos ALPHA2 25-40 180 for €120'})
    assert r.status_code==503
    assert 'OPENAI_API_KEY' in r.json()['detail']

def test_image_upload_rejected_when_not_image():
    r=client.post('/api/installation/extract-label',files={'file':('label.jpg',b'wrong data','image/jpeg')})
    assert r.status_code==400

def test_invalid_offer_quantity_rejected():
    r=client.post('/api/supplier/analyze',json={'installation':{},'offers':[{'quantity':0},{}]})
    assert r.status_code==422

def test_actual_event_is_persisted(tmp_path,monkeypatch):
    import app.main as main
    db=tmp_path/'events.sqlite3'
    monkeypatch.setattr(main,'DB',db)
    r=client.post('/api/events',json={'event':'tool_started','session_id':'manualtestsession123','experiment_id':'supplier_advisor'})
    assert r.status_code==200 and r.json()['recorded']
    import sqlite3
    with sqlite3.connect(db) as conn:
        assert conn.execute('select event from events').fetchone()[0]=='tool_started'

def test_metrics_api_requires_secret(monkeypatch):
    monkeypatch.delenv('METRICS_TOKEN',raising=False)
    assert client.get('/api/admin/metrics').status_code==503

def test_metrics_api_real_counts(tmp_path,monkeypatch):
    import app.main as main
    monkeypatch.setattr(main,'DB',tmp_path/'events.sqlite3')
    monkeypatch.setenv('METRICS_TOKEN','testing-strong-token')
    for name in ('landing_view','tool_started','comparison_completed','plancraft_cta_clicked'):
        assert client.post('/api/events',json={'event':name,'session_id':'testsession987654','experiment_id':'supplier_advisor'}).status_code==200
    assert client.get('/api/admin/metrics').status_code==403
    r=client.get('/api/admin/metrics',headers={'X-Metrics-Key':'testing-strong-token'})
    assert r.status_code==200
    assert r.json()['unique_comparison_sessions']==1
    assert r.json()['unique_cta_sessions_after_completion']==1
    assert r.json()['cta_rate_percent']==100
