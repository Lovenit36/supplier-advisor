import os, json, sqlite3, time, io, re, hmac
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict, deque
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image
import fitz
from dotenv import load_dotenv
load_dotenv(Path(__file__).parents[1]/'.env')
from .catalogue import CATALOGUE
from .models import CompareInput
from .rules import analyze
from .pdf_report import render_pdf
from .chat import answer_about_report
from .ai import extract_one, extract_label

ROOT=Path(__file__).parents[1]
app=FastAPI(title='Supplier Offer & Compatibility Advisor', version='1.1')
app.mount('/assets',StaticFiles(directory=ROOT/'static'),name='assets')
EVENT_NAMES={'landing_view','tool_started','ai_result_generated','comparison_completed','result_used','plancraft_cta_clicked'}
RATE=defaultdict(deque)

@app.middleware('http')
async def security_headers(request:Request, call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['Cache-Control']='no-store' if request.url.path.startswith('/api/') else 'public, max-age=60'
    return response

@app.get('/')
def home():
    return FileResponse(ROOT/'static'/'index.html')

@app.get('/health')
def health():
    return {'ok':True, 'ai_configured':bool(os.getenv('OPENAI_API_KEY')),'catalogue_count':len(CATALOGUE)}

@app.get('/api/catalogue')
def catalogue():
    return {'products':CATALOGUE,'scope':'Domestic heating circulation pumps. Exact model variants, not a general compatibility guarantee.'}

@app.post('/api/supplier/analyze')
def analyze_offers(payload:CompareInput):
    try:
        return analyze(payload)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

async def extract_upload(file: UploadFile | None):
    if not file or not file.filename:
        return '',None
    raw=await file.read(8*1024*1024+1)
    if len(raw)>8*1024*1024:
        raise HTTPException(413,'File too large. Maximum 8 MB.')
    if not raw:
        return '',None
    suffix=Path(file.filename).suffix.lower()
    if suffix=='.pdf':
        if not raw.startswith(b'%PDF'):
            raise HTTPException(400,'This is not a readable PDF.')
        try:
            with fitz.open(stream=raw,filetype='pdf') as doc:
                if doc.page_count>8:
                    raise HTTPException(400,'Use a supplier PDF of eight pages or fewer for the first version.')
                extracted='\n'.join(page.get_text('text') for page in doc)
        except (ValueError,RuntimeError) as exc:
            raise HTTPException(400,'Cannot read this PDF. Try pasting the offer text.') from exc
        if not extracted.strip():
            raise HTTPException(400,'This PDF contains no selectable text. Upload a screenshot/image instead, or paste the quotation.')
        return extracted[:18000],None
    if suffix in ('.png','.jpg','.jpeg','.webp'):
        try:
            with Image.open(io.BytesIO(raw)) as img:
                if img.width*img.height>16_000_000:
                    raise HTTPException(413,'Image too large. Please resize it to fewer than 16 million pixels.')
                fmt=img.format
                img.verify()
        except (ValueError,OSError) as exc:
            raise HTTPException(400,'This is not a readable image.') from exc
        if fmt not in ('PNG','JPEG','WEBP'):
            raise HTTPException(400,'Supported images: PNG, JPG and WEBP.')
        mime={'PNG':'image/png','JPEG':'image/jpeg','WEBP':'image/webp'}[fmt]
        return '',(mime,raw)
    if suffix=='.txt':
        try:
            return raw.decode('utf-8')[:18000],None
        except UnicodeDecodeError:
            raise HTTPException(400,'Text file must be UTF-8.')
    raise HTTPException(400,'Supported uploads: text PDF, PNG, JPG, WEBP or TXT.')

@app.post('/api/installation/extract-label')
async def installation_label(file: UploadFile=File(...)):
    _,image=await extract_upload(file)
    if not image:
        raise HTTPException(400,'Upload a pump-label image (PNG, JPG or WEBP).')
    return await extract_label(image)

@app.post('/api/supplier/extract')
async def extract_offers(request: Request, offer_a: str=Form(''), offer_b: str=Form(''), file_a: UploadFile | None=File(None),file_b: UploadFile | None=File(None)):
    ip=request.client.host if request.client else 'anonymous'
    now=time.monotonic()
    recent=RATE[ip]
    while recent and now-recent[0]>60:
        recent.popleft()
    if len(recent)>=6:
        raise HTTPException(429,'Too many AI extraction requests. Please try again shortly.')
    recent.append(now)
    if len(offer_a)>18000 or len(offer_b)>18000:
        raise HTTPException(400,'Offer text is too long (18,000 characters maximum each).')
    text_a,img_a=await extract_upload(file_a)
    text_b,img_b=await extract_upload(file_b)
    if not (offer_a.strip() or text_a or img_a) or not (offer_b.strip() or text_b or img_b):
        raise HTTPException(400,'Provide both supplier offers as text or uploaded files.')
    # Requests run sequentially to keep provider rate/cost bounded.
    result_a=await extract_one((offer_a+'\n'+text_a).strip(),img_a)
    result_b=await extract_one((offer_b+'\n'+text_b).strip(),img_b)
    # Preserve source text extracted from PDF too; it must not be silently replaced by UI selections.
    result_a['source_text']=(offer_a+'\n'+text_a).strip()[:18000]
    result_b['source_text']=(offer_b+'\n'+text_b).strip()[:18000]
    return {'offers':[result_a,result_b], 'review_required':True, 'method':'openai_live'}

@app.post('/api/supplier/report.pdf')
def export_pdf(payload: CompareInput):
    try:
        report=analyze(payload)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    pdf=render_pdf(report)
    return Response(pdf,media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="supplier-comparison.pdf"'})

class ChatMessage(BaseModel):
    role: str=Field(pattern='^(user|assistant)$')
    content: str=Field(min_length=1,max_length=2000)

class ChatRequest(BaseModel):
    comparison: CompareInput
    question: str=Field(min_length=1,max_length=1200)
    history: list[ChatMessage]=Field(default_factory=list,max_length=8)

CHAT_RATE=defaultdict(deque)

@app.post('/api/supplier/chat')
async def supplier_chat(payload:ChatRequest,request:Request):
    ip=request.client.host if request.client else 'anonymous'
    now=time.monotonic()
    recent=CHAT_RATE[ip]
    while recent and now-recent[0]>60: recent.popleft()
    if len(recent)>=12:
        raise HTTPException(429,'Too many advisor messages. Please try again in a minute.')
    recent.append(now)
    try:
        report=analyze(payload.comparison)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    answer=await answer_about_report(report,payload.question,[m.model_dump() for m in payload.history])
    return {'answer':answer,'scope':'Verified report and user-entered offer figures only. Not a product approval.'}

class Event(BaseModel):
    event: str=Field(min_length=1,max_length=60)
    session_id: str=Field(pattern=r'^[a-zA-Z0-9_-]{12,90}$')
    experiment_id: str='supplier_advisor'
    campaign: str=Field(default='direct',max_length=60)
    outcome: str=Field(default='',max_length=60)

DB=Path(os.getenv('EVENTS_DB_PATH',str(ROOT/'data'/'events.sqlite3')))

def record_event(data: Event):
    DB.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(DB,timeout=4) as db:
        db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, session_id TEXT NOT NULL, experiment_id TEXT NOT NULL, event TEXT NOT NULL, campaign TEXT NOT NULL, outcome TEXT NOT NULL)')
        db.execute('INSERT INTO events (timestamp, session_id, experiment_id, event, campaign, outcome) VALUES (?,?,?,?,?,?)',
                  (datetime.now(timezone.utc).isoformat(),data.session_id,'supplier_advisor',data.event,data.campaign,data.outcome))

@app.post('/api/events')
def events(event:Event):
    if event.event not in EVENT_NAMES or event.experiment_id!='supplier_advisor':
        raise HTTPException(400,'Unknown experiment event.')
    try:
        record_event(event)
    except sqlite3.Error:
        raise HTTPException(503,'Event tracking is unavailable. This event was not recorded.')
    return {'recorded':True}

@app.get('/api/status')
def status():
    return {'ai_configured':bool(os.getenv('OPENAI_API_KEY')),'event_persistence':'sqlite','catalogue_count':len(CATALOGUE)}

@app.get('/api/admin/metrics')
def metrics(request:Request):
    """Authenticated, real recorded event counts. No fabricated conversion fields."""
    secret=os.getenv('METRICS_TOKEN','').strip()
    if not secret:
        raise HTTPException(503,'Metrics API is disabled. Set METRICS_TOKEN on the server.')
    supplied=request.headers.get('x-metrics-key','')
    if not hmac.compare_digest(secret,supplied):
        raise HTTPException(403,'Unauthorized.')
    if not DB.exists():
        return {'measured_events':{},'unique_comparison_sessions':0,'unique_cta_sessions_after_completion':0,'cta_rate_percent':None,'note':'No actual events have been recorded.'}
    try:
        with sqlite3.connect(DB,timeout=4) as db:
            events=dict((name, {'events':count,'unique_sessions':sessions}) for name,count,sessions in db.execute('SELECT event,COUNT(*),COUNT(DISTINCT session_id) FROM events WHERE experiment_id=? GROUP BY event',('supplier_advisor',)))
            completions=db.execute('SELECT COUNT(DISTINCT session_id) FROM events WHERE experiment_id=? AND event=?',('supplier_advisor','comparison_completed')).fetchone()[0]
            clickers=db.execute('SELECT COUNT(DISTINCT c.session_id) FROM events c WHERE c.experiment_id=? AND c.event=? AND EXISTS (SELECT 1 FROM events b WHERE b.session_id=c.session_id AND b.event=? AND b.timestamp<=c.timestamp)',('supplier_advisor','plancraft_cta_clicked','comparison_completed')).fetchone()[0]
    except sqlite3.Error:
        raise HTTPException(503,'Cannot read metrics database.')
    return {'measured_events':events,'unique_comparison_sessions':completions,'unique_cta_sessions_after_completion':clickers,'cta_rate_percent':round(100*clickers/completions,2) if completions else None,'note':'Anonymous browser sessions, not known unique people. Outbound clicks are not confirmed leads or signups.'}
