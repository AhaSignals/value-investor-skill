"""Loopback research desk. Fixed routes, bounded input, no shell or arbitrary files."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import secrets
import threading
from urllib.parse import urlparse
from .research import ResearchError
from .valuation import calculate, pit_check, review_forecasts

ROOT = Path(__file__).resolve().parents[1]
MAX_BODY = 1_000_000


def case_view(bundle, ticker='', context=None):
    latest = bundle['financials'][-1]
    cfo, capex, shares = (latest.get(k) for k in ('operating_cash_flow','capex','diluted_shares'))
    proxy = (cfo-capex)/shares if all(v is not None for v in (cfo,capex,shares)) and shares>0 else None
    return {'company':bundle['company'],'ticker':ticker,'cutoff':bundle['cutoff'], 'rows':bundle['financials'],
            'cash_proxy_per_share':proxy,'source':latest.get('source'),
            'basis':'CFO less cash PP&E / annual weighted diluted shares. A screening proxy, not normalized owner earnings or current shares.',
            'context':{k:context.get(k) for k in ('latest_valuation','missing_fields','provider_errors','industry')} if context else None}


def examples():
    result=[]
    for ticker, filename in [('MSFT','msft-financials-2026-11-04.json'),('KO','ko-financials-2026-11-05.json'),('CAT','cat-financials-2026-11-05.json')]:
        path=ROOT/'examples'/filename
        if path.is_file():
            case = case_view(json.loads(path.read_text(encoding='utf-8')),ticker)
            case['illustration'] = json.loads((ROOT/'examples/valuation'/(ticker.lower()+'.json')).read_text(encoding='utf-8'))
            result.append(case)
    return result


class DeskServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, workspace):
        if address[0] != '127.0.0.1': raise ResearchError('Desk binds only to 127.0.0.1')
        self.workspace=Path(workspace)
        self.workspace.mkdir(parents=True,exist_ok=True)
        self.jobs={}; self.lock=threading.Lock(); self.token=secrets.token_urlsafe(32)
        super().__init__(address, Handler)
        self.origin='http://127.0.0.1:%d' % self.server_port

    def start_research(self, query):
        if not isinstance(query,str) or not query.strip() or len(query)>120 or any(ord(c)<32 for c in query):
            raise ResearchError('Enter one stock name or ticker (maximum 120 characters)')
        with self.lock:
            if any(j['state']=='running' for j in self.jobs.values()): raise ResearchError('A source capture is already running; wait for it to finish')
            if len(self.jobs)>=30: raise ResearchError('Session capture limit reached; restart the local desk for another session')
            job_id=secrets.token_hex(12)
            self.jobs[job_id]={'state':'running'}
        def work():
            try:
                from .us_research import collect
                folder=self.workspace/job_id
                receipt=collect(query,folder)
                bundle=json.loads((folder/'screen/inputs.json').read_text(encoding='utf-8'))
                context=json.loads((folder/'research.json').read_text(encoding='utf-8'))['context']
                value={'state':'complete','receipt':receipt,'case':case_view(bundle,receipt['ticker'],context),'report':'/reports/'+job_id+'/research.html'}
            except ResearchError as exc: value={'state':'error','error':str(exc)}
            except Exception: value={'state':'error','error':'Capture could not finish. Check source availability and the local output; no value was inferred.'}
            with self.lock: self.jobs[job_id]=value
        threading.Thread(target=work,daemon=True).start()
        return {'job':job_id}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def send(self, status, value, kind='application/json'):
        raw=json.dumps(value,ensure_ascii=False,allow_nan=False).encode() if kind=='application/json' else value
        self.send_response(status)
        for k,v in {'Content-Type':kind+'; charset=utf-8','Content-Length':str(len(raw)), 'Cache-Control':'no-store',
                    'X-Content-Type-Options':'nosniff', 'Referrer-Policy':'no-referrer',
                    'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"}.items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(raw)

    def allowed(self, mutation=False):
        expected='127.0.0.1:%d' % self.server.server_port
        if self.headers.get('Host')!=expected: return False
        origin=self.headers.get('Origin')
        if origin and origin!=self.server.origin: return False
        if self.headers.get('Sec-Fetch-Site')=='cross-site': return False
        if mutation and (self.headers.get('X-Desk-Token')!=self.server.token or self.headers.get_content_type()!='application/json'): return False
        return True

    def do_GET(self):
        if not self.allowed(): return self.send(403,{'error':'Local same-origin access required'})
        path=urlparse(self.path).path
        if path=='/api/session': return self.send(200,{'token':self.server.token,'cases':examples()})
        if path.startswith('/api/jobs/'):
            with self.server.lock: result=self.server.jobs.get(path.rsplit('/',1)[-1])
            return self.send(200 if result else 404,result or {'error':'Unknown capture'})
        files={'/':('desk.html','text/html'),'/desk.js':('desk.js','text/javascript'),'/desk.css':('desk.css','text/css')}
        if path in files:
            name,kind=files[path]; return self.send(200,(ROOT/'assets'/name).read_bytes(),kind)
        if path.startswith('/reports/'):
            parts=path.split('/'); job=parts[2] if len(parts)>=4 else ''
            rel='/'.join(parts[3:])
            kinds={'research.html':'text/html','research.md':'text/plain','screen/scan.html':'text/html',
                   'screen/cash-vs-profit.svg':'image/svg+xml','screen/pe-history.svg':'image/svg+xml','screen/price-context.svg':'image/svg+xml'}
            if job in self.server.jobs and self.server.jobs[job]['state']=='complete' and rel in kinds:
                file=self.server.workspace/job/rel
                if file.is_file() and not file.is_symlink(): return self.send(200,file.read_bytes(),kinds[rel])
        return self.send(404,{'error':'Unknown resource'})

    def do_POST(self):
        if not self.allowed(True): return self.send(403,{'error':'Local session token and JSON required'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<=0 or size>MAX_BODY: return self.send(413,{'error':'Input must be at most 1 MB'})
            data=json.loads(self.rfile.read(size))
            route=urlparse(self.path).path
            if route=='/api/research': result=self.server.start_research(data.get('company'))
            elif route=='/api/value': result=calculate(data)
            elif route=='/api/pit': result=pit_check(data)
            elif route=='/api/review': result=review_forecasts(data)
            else: return self.send(404,{'error':'Unknown operation'})
            self.send(200,result)
        except (ResearchError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
            self.send(400,{'error':'Input cannot be used. Check method, finite numbers, source dates and review rationale; discount rate must exceed terminal growth.'})


def serve(workspace,port=8765):
    server=DeskServer(('127.0.0.1',port),workspace)
    print('Value Investor Desk: '+server.origin,flush=True)
    print('Local research only. Stop with Ctrl+C. Public data is fetched only when requested.',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
