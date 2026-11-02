from .models import CompareInput
from .catalogue import CATALOGUE, find_product, normalize
import re


def finding(label, status, detail, source=None):
    return {'label':label,'status':status,'detail':detail,'source':source}


def compare_pump(installation, product, reason=None):
    if product is None:
        return {'status':'cannot_verify','checks':[finding('Product identity','unknown',reason or 'Exact pump model not recognised.')], 'open_checks':['Identify exact manufacturer model/article number.']}
    source = product['details']
    checks = []
    def spec(label, actual, target, fmt, unit='', missing='Installation information not supplied'):
        if target is None:
            checks.append(finding(label,'unknown',missing,source))
        else:
            status = 'verified_match' if actual == target else 'verified_conflict'
            checks.append(finding(label,status,fmt.format(actual, target) + unit,source))
    spec('Connection thread', product['connection'], installation.connection if installation.connection!='unknown' else None,
         'Manufacturer: {} · existing installation: {}')
    spec('Port-to-port length',product['length_mm'],installation.length_mm,
         'Manufacturer: {} mm · existing space: {} mm')
    spec('Electrical supply',product['voltage_v'],installation.voltage_v,
         'Manufacturer: {} V · existing supply: {} V')
    if installation.medium == 'unknown':
        checks.append(finding('Working fluid','unknown','Confirm whether the circuit contains heating water, glycol or another liquid.',source))
    elif installation.medium == 'heating_water':
        checks.append(finding('Working fluid','verified_match','Manufacturer lists this pump family for heating-water circulation. Check water treatment and site conditions.',source))
    else:
        checks.append(finding('Working fluid','unknown','Fluid/additive compatibility and viscosity need manufacturer confirmation; not assumed safe.',source))
    if installation.pressure_bar is None or product.get('max_pressure_bar') is None:
        checks.append(finding('System pressure','unknown','Confirm system pressure and the exact pump pressure rating.',source))
    else:
        match = installation.pressure_bar <= product['max_pressure_bar']
        checks.append(finding('System pressure','verified_match' if match else 'verified_conflict',f'System {installation.pressure_bar:g} bar vs published maximum {product["max_pressure_bar"]:g} bar.',source))
    if installation.temp_c is None or product.get('max_temp_c') is None:
        checks.append(finding('Fluid temperature','unknown','Temperature suitability cannot be established from provided data.',source))
    elif installation.temp_c > product['max_temp_c']:
        checks.append(finding('Fluid temperature','verified_conflict',f'System {installation.temp_c:g}°C exceeds published maximum {product["max_temp_c"]:g}°C.',source))
    elif installation.temp_c >= 0:
        checks.append(finding('Fluid temperature','verified_match',f'System {installation.temp_c:g}°C is below the published maximum {product["max_temp_c"]:g}°C; other operating limits still apply.',source))
    else:
        checks.append(finding('Fluid temperature','unknown','Subzero system temperatures require separate fluid/installation assessment.',source))
    if installation.control == 'unknown':
        checks.append(finding('Control / signal','unknown','Confirm required control mode and electrical interface; matching supply voltage does not prove a compatible controller.',source))
    elif installation.control in product.get('controls',[]):
        checks.append(finding('Control / signal','verified_match',f'Published control features include {installation.control}. Confirm external wiring and commissioning.',source))
    elif installation.control == 'external':
        checks.append(finding('Control / signal','unknown','External controller or signal compatibility is not established from this product entry.',source))
    else:
        checks.append(finding('Control / signal','verified_conflict',f'The required {installation.control} mode is not listed for this exact model.',source))
    hydraulic_conflicts = []
    if installation.head_m is not None and product.get('max_head_m') is not None and installation.head_m > product['max_head_m']:
        hydraulic_conflicts.append(f'Required head {installation.head_m:g} m exceeds max head {product["max_head_m"]:g} m.')
    if installation.flow_m3h is not None and product.get('max_flow_m3h') is not None and installation.flow_m3h > product['max_flow_m3h']:
        hydraulic_conflicts.append(f'Required flow {installation.flow_m3h:g} m³/h exceeds max flow {product["max_flow_m3h"]:g} m³/h.')
    if hydraulic_conflicts:
        checks.append(finding('Hydraulic performance','verified_conflict',' '.join(hydraulic_conflicts),source))
    else:
        checks.append(finding('Hydraulic performance','unknown','Check the actual flow AND head together on the manufacturer pump curve at the required duty point. Separate maximum values never prove simultaneous performance.',source))
    checks.append(finding('Site & accessories','unknown','Confirm clearance, unions, wiring, safety isolation, fittings, installation orientation and accessories on site. No adapter is presumed.',source))
    has_conflict=any(c['status']=='verified_conflict' for c in checks)
    return {
        'status':'conflict' if has_conflict else 'checks_pending',
        'checks':checks,
        'open_checks':[c['label']+': '+c['detail'] for c in checks if c['status']=='unknown']
    }


def money(value):
    return None if value is None else round(value+1e-8,2)


def costs(offer, install, vat_percent):
    questions=[]; base = None; delivery=None; extras=None; labour=None
    if offer.quantity is None:
        questions.append('Confirm quoted quantity.')
    if offer.unit_price_eur is None:
        questions.append('Confirm unit purchase price.')
    if offer.vat_basis == 'unknown':
        questions.append('Confirm whether the supplier price includes VAT.')
    if offer.quantity is not None and offer.unit_price_eur is not None and offer.vat_basis != 'unknown':
        base = offer.quantity * offer.unit_price_eur * (1+(vat_percent/100) if offer.vat_basis=='net' else 1)
    if offer.delivery_status == 'included':
        delivery=0.0
    elif offer.delivery_status == 'quoted' and offer.delivery_eur is not None and offer.vat_basis!='unknown':
        delivery=offer.delivery_eur * (1+(vat_percent/100) if offer.vat_basis=='net' else 1)
    else:
        questions.append('Confirm delivery price or that delivery is included.')
    if offer.extras_status=='none':
        extras=0.0
    elif offer.extras_status=='entered' and offer.extras_eur is not None:
        extras=offer.extras_eur # explicitly installer-entered gross amount
    else:
        questions.append('Confirm extra parts/adapter costs or mark none after checking.')
    if offer.labour_status=='none':
        labour=0.0
    elif offer.labour_status=='entered' and offer.labour_hours is not None and install.labour_rate_eur is not None:
        labour=offer.labour_hours*install.labour_rate_eur # installer-entered gross hourly rate
    else:
        questions.append('Confirm extra labour hours and hourly rate or mark none.')
    known = sum(x for x in [base,delivery,extras,labour] if x is not None)
    complete = all(x is not None for x in [base,delivery,extras,labour]) and offer.quantity==1
    if offer.quantity is not None and offer.quantity!=1:
        questions.append('Quoted quantity is not one pump; compare like-for-like quantities before choosing.')
    return {'purchase_gross':money(base),'delivery_gross':money(delivery),'extras_gross':money(extras),'labour_gross':money(labour),'known_subtotal_gross':money(known),'complete':complete,'total_gross':money(known) if complete else None,'questions':questions,'basis':'Gross EUR; quote amounts converted using entered VAT rate; extra parts and labour entered as gross EUR.'}


def quoted_identity_conflict(offer):
    """Compare a proposed product against original user-source text/evidence.

    Do not trust a replacement catalogue selection to rewrite the quote.
    Manufacturer article and exact model identity must agree with original evidence.
    """
    product, reason = find_product(offer.model_text, offer.article_number, offer.catalogue_id)
    if product is None:
        # Unrecognised products remain 'cannot verify', not forcibly blocked.
        # But contradictory identified variants must not slip through.
        if reason and ('disagree' in reason or 'different pumps' in reason):
            return reason
        return None
    # The source fields are original pasted quote text and short AI-cited excerpts.
    # Both are untrusted inputs, used here only to detect self-contradictions.
    sources = [offer.source_text] + list(offer.evidence)
    for source in sources:
        for candidate in re.findall(r'(?:article\s*(?:number|no\.?|nr\.?)|art\.?[- ]?nr\.?|sku|artikelnummer)\s*[:#-]?\s*(\d{6,12})\b', source, re.I):
            if normalize(candidate) != normalize(product['article']):
                return f'Original quotation states article {candidate}, but the selected catalogue product is article {product["article"]}. Correct the selected product or source quotation before comparing.'
        for found in re.findall(r'(?:^|\n|[“"])\s*(?:product|model|produkt|modell)\s*:\s*([^\r\n”"]+)',source, re.I):
            identified=normalize(found.strip())
            if identified and identified not in (normalize(product['model']),normalize(product['brand']+' '+product['model'])):
                return f'Original quotation states model "{found.strip()[:90]}" but the selected catalogue model is {product["model"]}. Correct the source mismatch before comparing.'
    return None

def analyze(payload: CompareInput):
    results=[]
    existing_product, _ = find_product(payload.installation.existing_model) if payload.installation.existing_model else (None,None)
    existing_reference = None
    if existing_product:
        existing_reference = {
            'model':f"{existing_product['brand']} {existing_product['model']}",
            'connection':existing_product['connection'],
            'length_mm':existing_product['length_mm'],
            'source':existing_product['details'],
            'note':'Published product dimensions only; verify the actual installed pump, fittings and clearances on site.'
        }
    for offer in payload.offers:
        source_conflict=quoted_identity_conflict(offer)
        if source_conflict:
            raise ValueError(source_conflict)
        product, reason = find_product(offer.model_text,offer.article_number,offer.catalogue_id)
        fit=compare_pump(payload.installation,product,reason)
        price=costs(offer,payload.installation,payload.vat_rate_percent)
        results.append({'offer':offer.model_dump(),'product':product,'identity_issue':reason,'fit':fit,'cost':price})
    prices=[r['cost']['total_gross'] for r in results]
    prices_comparable=all(p is not None for p in prices)
    no_conflicts=all(r['fit']['status']!='conflict' for r in results)
    if prices_comparable:
        if prices[0] == prices[1]:
            price_message='Both entered installed-cost totals are equal.'
        else:
            idx=0 if prices[0]<prices[1] else 1
            price_message=f'Offer {"A" if idx==0 else "B"} has a €{abs(prices[0]-prices[1]):,.2f} lower entered installed cost. Technical approval is separate.'
    else:
        price_message='Cannot identify the cheapest installed option until all material costs, VAT basis and quantities are confirmed.'
    if not no_conflicts:
        status='conflict'
        title='One or more confirmed installation conflicts'
    else:
        status='checks_pending'
        title='Initial checks completed — installer review needed'
    # No blanket verified compatibility, even when mechanical checks pass.
    candidates=[]
    used={r['product']['id'] for r in results if r['product'] is not None}
    for p in CATALOGUE:
        if p['id'] in used:
            continue
        assessment=compare_pump(payload.installation,p)
        if assessment['status']=='conflict':
            continue
        mechanical=[c for c in assessment['checks'] if c['label'] in ('Connection thread','Port-to-port length')]
        if all(c['status']=='verified_match' for c in mechanical):
            candidates.append({'product':p,'status':'Mechanical match only — hydraulic suitability and price unverified'})
    return {'status':status,'title':title,'existing_reference':existing_reference,'results':results,'cost_comparable':prices_comparable,'price_message':price_message,'alternatives':candidates[:4], 'disclaimer':'This is a preliminary evidence-backed screening tool, not a pump sizing or installation approval. Confirm actual duty-point pump curves and site conditions before ordering.'}
