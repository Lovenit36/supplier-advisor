import pytest
from app.catalogue import CATALOGUE, find_product
from app.models import CompareInput, Installation
from app.rules import analyze, compare_pump, costs
from app.models import Offer


def make(offer_a=None,offer_b=None,install=None,vat_rate=19):
    default={'catalogue_id':'wilo-4215513','quantity':1,'unit_price_eur':200,'vat_basis':'gross','delivery_status':'included','extras_status':'none','labour_status':'none'}
    a={**default,**(offer_a or {})};b={**default,**(offer_b or {})}
    return CompareInput.model_validate({'installation':{'connection':'G1.5','length_mm':180,'voltage_v':230,'medium':'heating_water',**(install or {})},'offers':[a,b], 'vat_rate_percent':vat_rate})

def check(r,label):
    return next(x for x in r['checks'] if x['label']==label)

def test_verified_catalogue_has_evidence_and_two_brands():
    assert len(CATALOGUE)==9
    assert {p['brand'] for p in CATALOGUE}=={'Wilo','Grundfos'}
    for p in CATALOGUE:
        assert p['article'] and p['source'].startswith('https://') and p['length_mm'] in (130,180)

def test_exact_variant_differs_on_length():
    i=Installation(connection='G1.5',length_mm=180,voltage_v=230)
    result=compare_pump(i,find_product('','4215516')[0])
    assert check(result,'Port-to-port length')['status']=='verified_conflict'
    assert result['status']=='conflict'

def test_matching_dimensions_never_mark_hydraulic_approved():
    r=compare_pump(Installation(connection='G1.5',length_mm=180,voltage_v=230),find_product('','4215515')[0])
    assert check(r,'Port-to-port length')['status']=='verified_match'
    assert check(r,'Hydraulic performance')['status']=='unknown'
    assert r['status']=='checks_pending'

def test_max_head_exceeded_confirmed_conflict():
    r=compare_pump(Installation(connection='G1.5',length_mm=180,head_m=8),find_product('','4215515')[0])
    assert check(r,'Hydraulic performance')['status']=='verified_conflict'

def test_glycol_is_not_automatically_approved():
    r=compare_pump(Installation(medium='glycol'),find_product('','4215515')[0])
    assert check(r,'Working fluid')['status']=='unknown'

def test_unknown_product_never_passes():
    r=analyze(make(offer_a={'catalogue_id':'','model_text':'Yonos PICO 25/1-6 generic'},offer_b={'catalogue_id':'','article_number':'999999'}))
    assert all(x['fit']['status']=='cannot_verify' for x in r['results'])

def test_vat_normalization_net_gross():
    data=make(offer_a={'unit_price_eur':100,'vat_basis':'net'},offer_b={'unit_price_eur':119,'vat_basis':'gross'})
    r=analyze(data)
    assert r['results'][0]['cost']['total_gross']==119
    assert r['results'][1]['cost']['total_gross']==119

def test_missing_parts_no_false_full_total():
    r=analyze(make(offer_a={'extras_status':'unknown'},offer_b={'extras_status':'entered','extras_eur':80}))
    assert r['results'][0]['cost']['total_gross'] is None
    assert r['results'][0]['cost']['known_subtotal_gross']==200
    assert r['cost_comparable'] is False

def test_quote_quantity_difference_disables_cost_winner():
    r=analyze(make(offer_a={'quantity':2},offer_b={'quantity':1}))
    assert r['cost_comparable'] is False
    assert 'quantity' in ' '.join(r['results'][0]['cost']['questions']).lower()

def test_installer_added_costs_are_not_made_up():
    r=analyze(make(offer_a={'unit_price_eur':400,'extras_status':'entered','extras_eur':50,'labour_status':'entered','labour_hours':1.5},offer_b={'unit_price_eur':450},install={'labour_rate_eur':60}))
    assert r['results'][0]['cost']['total_gross']==540
    assert r['results'][1]['cost']['total_gross']==450
    assert 'Offer B' in r['price_message']

def test_no_double_charge_when_parts_included():
    r=analyze(make(offer_a={'included_accessories':['gaskets'],'extras_status':'none'}))
    assert r['results'][0]['cost']['extras_gross']==0

def test_voltage_conflict_blocks_fit_even_when_cheapest():
    r=analyze(make(offer_a={'unit_price_eur':50},install={'voltage_v':400}))
    assert r['status']=='conflict'
    assert r['results'][0]['fit']['status']=='conflict'

def test_no_catalogue_price_fabricated_for_alternatives():
    r=analyze(make())
    assert r['alternatives']
    assert all('price' not in a for a in r['alternatives'])

def test_server_validation_rejects_negative_price():
    with pytest.raises(Exception):
        make(offer_a={'unit_price_eur':-4})

def test_article_model_disagreement_never_silently_passes():
    p,reason=find_product('Yonos PICO 25/1-6','4215514')
    assert p is None and 'different pumps' in reason

def test_existing_model_yields_source_hint_not_assumed_site_measurement():
    r=analyze(make(install={'existing_model':'Yonos PICO 25/1-4-130','length_mm':None}))
    assert r['existing_reference']['length_mm']==130
    assert all(next(c for c in x['fit']['checks'] if c['label']=='Port-to-port length')['status']=='unknown' for x in r['results'])
