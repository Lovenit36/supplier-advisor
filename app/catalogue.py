from pathlib import Path
import json, re

CATALOGUE = json.loads((Path(__file__).parents[1] / 'data' / 'pumps.json').read_text())
BY_ID = {p['id']: p for p in CATALOGUE}

def normalize(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())

def find_product(model_text: str, article: str = '', catalogue_id: str = ''):
    if catalogue_id in BY_ID:
        chosen = BY_ID[catalogue_id]
        # Never silently accept a conflicting explicit manufacturer article number.
        if article and normalize(article) != normalize(chosen['article']):
            return None, 'Selected catalogue model and quoted article number disagree.'
        if model_text and normalize(model_text) not in (normalize(chosen['model']), normalize(chosen['brand']+' '+chosen['model'])):
            return None, 'Selected catalogue model and quoted model name disagree.'
        return chosen, None
    if article:
        matches = [p for p in CATALOGUE if normalize(article) == normalize(p['article'])]
        if len(matches) == 1:
            chosen=matches[0]
            if model_text:
                named=[p for p in CATALOGUE if normalize(model_text) in (normalize(p['model']),normalize(p['brand']+' '+p['model']))]
                if named and named[0]['id']!=chosen['id']:
                    return None, 'Quoted article number and quoted model name identify different pumps.'
            return chosen, None
        return None, 'Quoted article number is not present in the verified catalogue.'
    model_n = normalize(model_text)
    if not model_n:
        return None, 'No exact pump model was supplied.'
    matches = [p for p in CATALOGUE if normalize(p['model']) == model_n or normalize(p['brand']+' '+p['model']) == model_n]
    if len(matches) == 1:
        return matches[0], None
    return None, 'Exact variant not found. Select a catalogue model or provide an article number (130 mm and 180 mm versions differ).'
