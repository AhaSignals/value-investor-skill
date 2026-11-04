"""US issuer discovery, dated public-source capture and deterministic replay.

Raw provider responses stay in the caller's output folder, outside the package.
"""
from datetime import datetime, date, time as day_time, timedelta, timezone
import hashlib
from html.parser import HTMLParser
import json
import math
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

from .research import ResearchError, digest, timestamp
from .scanner import scan, save

UTC = timezone.utc
SEC_AGENT = "AhaSignals value-investor-skill research@ahasignals.com"
TICKERS = "https://www.sec.gov/files/company_tickers.json"
MAX_BYTES = 24_000_000
ALLOWED_HOSTS = {"www.sec.gov", "data.sec.gov", "query1.finance.yahoo.com"}
FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A"}
TAGS = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax", "Revenues", "SalesRevenueNet"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "diluted_shares": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
}


def utc_now():
    return datetime.now(UTC).isoformat()


def json_write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def safe_source(url):
    u = urlparse(url)
    if u.scheme != "https" or u.hostname not in ALLOWED_HOSTS or u.username or u.password or u.port not in (None, 443):
        raise ResearchError("Source URL is outside the supported public providers")
    return url


class Capture:
    """One bounded request at a time. No login, proxy, crumb or blocking workaround."""
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir()
        self.entries = []
        self.last_request = 0.0

    def get(self, role, url, as_json=True):
        safe_source(url)
        if not re.fullmatch(r"[a-z_]+", role):
            raise ResearchError("Invalid source role")
        wait = 1.05 - (time.monotonic() - self.last_request)
        if wait > 0:
            time.sleep(wait)
        ua = os.environ.get("SEC_USER_AGENT", SEC_AGENT) if urlparse(url).hostname.endswith("sec.gov") else "AhaSignals value-investor-skill/0.5.0"
        if not ua.strip() or '\n' in ua or '\r' in ua:
            raise ResearchError("Invalid SEC_USER_AGENT; use an organization/contact identifier")
        self.last_request = time.monotonic()
        try:
            with urlopen(Request(url, headers={"User-Agent": ua, "Accept": "application/json" if as_json else "text/html"}), timeout=35) as response:
                safe_source(response.geturl())
                raw = response.read(MAX_BYTES + 1)
        except HTTPError as error:
            raise ResearchError("%s provider returned HTTP %s; stopped without bypassing access limits" % (role, error.code))
        except (URLError, TimeoutError, OSError):
            raise ResearchError(role + " source unavailable; check network access or replay a saved capture")
        if len(raw) > MAX_BYTES:
            raise ResearchError(role + " response exceeded the size limit")
        observed = utc_now()
        if as_json:
            try:
                data = json.loads(raw)
            except (ValueError, UnicodeError):
                raise ResearchError(role + " did not return valid JSON")
        else:
            data = raw.decode('utf-8', errors='replace')
        name = role + ('.json' if as_json else '.html')
        (self.directory / name).write_bytes(raw)
        self.entries.append({"role": role, "file": name, "url": url, "observed_at": observed,
                             "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        return data


def normalize_name(value):
    return ' '.join(re.findall(r'[a-z0-9]+', value.lower()))


def company_name(value):
    words = normalize_name(value).split()
    while words and words[-1] in {'inc','corp','corporation','co','company','ltd','plc','limited'}:
        words.pop()
    return ' '.join(words)


def resolve_company(query, index):
    if not isinstance(query, str) or not query.strip() or len(query) > 120:
        raise ResearchError("Enter a US stock ticker or company name")
    if not isinstance(index, dict):
        raise ResearchError("Invalid SEC company directory")
    rows = [r for r in index.values() if isinstance(r, dict) and isinstance(r.get('ticker'), str) and isinstance(r.get('title'), str)]
    aliases = {'微软':'MSFT','苹果':'AAPL','英伟达':'NVDA','亚马逊':'AMZN','特斯拉':'TSLA','谷歌':'Alphabet'}
    query = aliases.get(query.strip(),query)
    symbol = query.strip().upper().replace('.', '-')
    exact = [r for r in rows if r['ticker'].upper().replace('.', '-') == symbol]
    if not exact:
        q = normalize_name(query)
        exact = [r for r in rows if company_name(r['title']) == company_name(query)]
        if not exact and q:
            exact = [r for r in rows if (' ' + q + ' ') in (' ' + normalize_name(r['title']) + ' ')]
    if not exact:
        raise ResearchError("No SEC-listed match. Try the US ticker or the issuer's English name")
    if len(exact) > 1:
        names = ', '.join(r['ticker'] + ' (' + r['title'] + ')' for r in exact[:8])
        raise ResearchError("Several securities match; choose a ticker: " + names)
    row = exact[0]
    cik = str(row.get('cik_str', ''))
    ticker = row['ticker'].upper()
    if not re.fullmatch(r'\d{1,10}', cik) or not re.fullmatch(r'[A-Z0-9]+(?:[.-][A-Z0-9]+)?', ticker):
        raise ResearchError("Unsupported SEC identifier or ticker format")
    return {"ticker": ticker, "name": row['title'], "cik": cik.zfill(10)}


def filing_rows(submissions):
    recent = submissions.get('filings', {}).get('recent', {})
    rows = []
    for i, accession in enumerate(recent.get('accessionNumber', [])):
        def field(k):
            values = recent.get(k, [])
            return values[i] if i < len(values) else None
        form = field('form')
        if form not in FORMS:
            continue
        accepted = field('acceptanceDateTime')
        if accepted:
            timestamp(accepted)
        document = field('primaryDocument')
        if not re.fullmatch(r'\d{10}-\d{2}-\d{6}', str(accession)) or not re.fullmatch(r'[A-Za-z0-9_.-]+', str(document)):
            raise ResearchError("Unsupported SEC filing document name")
        rows.append({"accession": accession, "form": form, "filed": field('filingDate'),
                     "accepted_at": accepted, "document": document, "report_date": field('reportDate')})
    return rows


def accession_url(cik, accession):
    if not re.fullmatch(r'\d{10}-\d{2}-\d{6}', accession):
        raise ResearchError("Invalid accession in XBRL data")
    return 'https://www.sec.gov/Archives/edgar/data/%d/%s/%s-index.html' % (int(cik), accession.replace('-', ''), accession)


def available_at(fact, accepted):
    value = accepted.get(fact.get('accn'))
    if value:
        return timestamp(value)
    try:
        # With only a filing date, wait until the next UTC day. Never assume midnight publication.
        d = date.fromisoformat(fact['filed']) + timedelta(days=1)
        return datetime.combine(d, day_time(), UTC)
    except (ValueError, KeyError, TypeError):
        raise ResearchError("XBRL fact has no valid filing date")


def facts_for(facts, tag, unit, cutoff, accepted):
    rows = facts.get('facts', {}).get('us-gaap', {}).get(tag, {}).get('units', {}).get(unit, [])
    usable = []
    for r in rows:
        if r.get('form') not in FORMS:
            continue
        val = r.get('val')
        if not isinstance(val, (int, float)) or isinstance(val, bool) or not math.isfinite(val):
            continue
        try:
            date.fromisoformat(r['end'])
            if r.get('start'): date.fromisoformat(r['start'])
        except (KeyError, ValueError, TypeError):
            continue
        if available_at(r, accepted) <= cutoff:
            usable.append(dict(r, tag=tag, unit=unit))
    return usable


def select_fact(facts, tags, unit, end, start, cutoff, accepted):
    for tag in tags:
        rows = [r for r in facts_for(facts, tag, unit, cutoff, accepted)
                if r['end'] == end and r.get('start') == start]
        if rows:
            latest = max(available_at(r, accepted) for r in rows)
            same = [r for r in rows if available_at(r, accepted) == latest]
            if len({r['val'] for r in same}) != 1:
                return None  # Do not select an arbitrary context among conflicting facts.
            return sorted(same, key=lambda r: (r.get('accn',''), r.get('frame','')))[0]
    return None


def provenance(fact, cik, accepted):
    return {"tag": fact['tag'], "unit": fact['unit'], "value": fact['val'], "period_start": fact.get('start'),
            "period_end": fact['end'], "accession": fact['accn'], "available_at": available_at(fact, accepted).isoformat(),
            "source": accession_url(cik, fact['accn'])}


def annual_financials(facts, issuer, cutoff, observed, accepted):
    anchors = facts_for(facts, 'NetIncomeLoss', 'USD', cutoff, accepted)
    if not anchors:
        anchors = facts_for(facts, 'ProfitLoss', 'USD', cutoff, accepted)
    periods = sorted({(r['start'], r['end']) for r in anchors if r.get('start') and r['form'].startswith('10-K')
                      and 350 <= (date.fromisoformat(r['end'])-date.fromisoformat(r['start'])).days <= 380}, key=lambda p:p[1])[-5:]
    rows, gaps = [], []
    for start, end in periods:
        used, missing, values = {}, [], {}
        for metric, tags in TAGS.items():
            unit = 'shares' if metric == 'diluted_shares' else 'USD'
            fact = select_fact(facts, tags, unit, end, None if metric == 'cash' else start, cutoff, accepted)
            if fact is None or (metric in {'revenue','cash','capex','diluted_shares'} and fact['val'] < 0):
                values[metric] = None
                missing.append(metric)
            else:
                values[metric] = fact['val']
                used[metric] = [provenance(fact, issuer['cik'], accepted)]
        # Only total debt or an explicitly complete component set can populate total debt.
        debt = select_fact(facts, ['DebtCurrentAndNoncurrent','LongTermDebtAndShortTermBorrowings'], 'USD', end, None, cutoff, accepted)
        if debt:
            values['debt'] = debt['val']
            used['debt'] = [provenance(debt, issuer['cik'], accepted)]
        else:
            long = select_fact(facts, ['LongTermDebt'], 'USD', end, None, cutoff, accepted)
            if long is None:
                current = select_fact(facts, ['LongTermDebtCurrent'], 'USD', end, None, cutoff, accepted)
                noncurrent = select_fact(facts, ['LongTermDebtNoncurrent'], 'USD', end, None, cutoff, accepted)
                longs = [current, noncurrent] if current and noncurrent else []
            else:
                longs = [long]
            short = select_fact(facts, ['ShortTermBorrowings'], 'USD', end, None, cutoff, accepted)
            # Commercial paper alone cannot establish that other short-term borrowing is zero.
            if longs and short and all(r['val'] >= 0 for r in longs + [short]):
                values['debt'] = sum(r['val'] for r in longs + [short])
                used['debt'] = [provenance(r, issuer['cik'], accepted) for r in longs + [short]]
            else:
                values['debt'] = None
                missing.append('debt: complete short/long-term definition unavailable; no zero assumed')
        ev = [p for parts in used.values() for p in parts]
        if not ev:
            continue
        row = {"date": end, "period_start": start, "period_type": "FY", "available_at": max(p['available_at'] for p in ev),
               "observed_at": observed, "status": "active", "source": 'https://data.sec.gov/api/xbrl/companyfacts/CIK%s.json' % issuer['cik'],
               "basis": "US GAAP annual consolidated; latest filed values at capture; reported share basis requires split review",
               "field_sources": used, "missing_fields": missing, **values}
        rows.append(row)
        gaps.extend(end + ': ' + m for m in missing)
    return rows, gaps


def chart_rows(chart, issuer, cutoff, observed):
    try:
        if chart.get('chart', {}).get('error'):
            raise ResearchError("Price provider returned a ticker error")
        data = chart['chart']['result'][0]
        meta = data['meta']
        if meta.get('currency') != 'USD' or meta.get('instrumentType') != 'EQUITY':
            raise ResearchError("Automatic price research requires a USD equity")
        if meta.get('exchangeTimezoneName') != 'America/New_York':
            raise ResearchError('Automatic price research requires a US Eastern market session')
        if meta.get('symbol','').upper().replace('.','-') != issuer['ticker'].replace('.','-'):
            raise ResearchError("Price response does not match the requested ticker")
        quotes = data['indicators']['quote'][0]
        moments = data['timestamp']
    except (KeyError, TypeError, IndexError):
        raise ResearchError("Price response has an unsupported shape")
    rows, rejected = [], []
    source = 'https://finance.yahoo.com/quote/' + quote(issuer['ticker'].replace('.','-'), safe='') + '/history/'
    for i, moment in enumerate(moments):
        try:
            d = datetime.fromtimestamp(moment, UTC).date()
            # Today's candle may still be incomplete. Deliberately use previous UTC dates only.
            if d >= cutoff.date():
                rejected.append({'date':d.isoformat(), 'reason':'current_or_future_UTC_date'})
                continue
            vals = {k: quotes[k][i] for k in ('open','high','low','close')}
            if not all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) and x > 0 for x in vals.values()):
                raise ValueError()
            # Tiny floating-point disagreements are normalized within 1e-6 relative tolerance only.
            low, high = min(vals.values()), max(vals.values())
            if vals['low'] > min(vals['open'],vals['close'])*(1+1e-6) or vals['high'] < max(vals['open'],vals['close'])*(1-1e-6):
                raise ValueError()
            vals['low'], vals['high'] = low, high
        except (ValueError, TypeError, KeyError, IndexError, OverflowError):
            rejected.append({'index':i, 'reason':'missing_or_invalid_OHLC'})
            continue
        rows.append({'date':d.isoformat(), 'available_at':d.isoformat()+'T23:59:59Z', 'observed_at':observed,
                     'source':source, 'status':'active', 'basis':'Provider close/OHLC split-adjusted at capture; excludes dividend-adjusted close', **vals})
    if len({r['date'] for r in rows}) != len(rows):
        raise ResearchError("Price source has duplicate daily observations")
    splits = []
    for event in data.get('events', {}).get('splits', {}).values():
        try:
            factor = float(event['numerator']) / float(event['denominator'])
            when = datetime.fromtimestamp(event['date'], UTC)
            if not math.isfinite(factor) or factor <= 0:
                raise ValueError()
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            raise ResearchError("Unusable split event; historical P/E requires a reviewed adjustment")
        splits.append((when, factor))
    return sorted(rows,key=lambda r:r['date']), splits, rejected


def adjusted_eps(fact, accepted, splits):
    value = fact['val']
    published = available_at(fact, accepted)
    for when, factor in splits:
        if when > published:
            value /= factor
    return value


def ttm_eps(facts, at, accepted, splits, cik):
    eps = facts_for(facts, 'EarningsPerShareDiluted', 'USD/shares', at, accepted)
    annuals = [r for r in eps if r.get('start') and 350 <= (date.fromisoformat(r['end'])-date.fromisoformat(r['start'])).days <= 380]
    if not annuals:
        return None
    year_end = max(r['end'] for r in annuals)
    annual = select_fact(facts, ['EarningsPerShareDiluted'], 'USD/shares', year_end,
                         min(r['start'] for r in annuals if r['end']==year_end), at, accepted)
    if not annual:
        return None
    next_start = (date.fromisoformat(year_end) + timedelta(days=1)).isoformat()
    ytds = [r for r in eps if r.get('start')==next_start and r['end'] > year_end and 60 <= (date.fromisoformat(r['end'])-date.fromisoformat(next_start)).days <= 300]
    components, value, period_end = [annual], adjusted_eps(annual,accepted,splits), year_end
    if ytds:
        end = max(r['end'] for r in ytds)
        current = select_fact(facts, ['EarningsPerShareDiluted'], 'USD/shares', end, next_start, at, accepted)
        duration = (date.fromisoformat(end)-date.fromisoformat(next_start)).days
        previous = [r for r in eps if r.get('start')==annual['start'] and abs((date.fromisoformat(r['end'])-date.fromisoformat(r['start'])).days-duration)<=7]
        if not current or not previous:
            return None
        prior_end = max(r['end'] for r in previous)
        prior = select_fact(facts, ['EarningsPerShareDiluted'], 'USD/shares', prior_end, annual['start'], at, accepted)
        if not prior:
            return None
        components += [current, prior]
        value += adjusted_eps(current,accepted,splits)-adjusted_eps(prior,accepted,splits)
        period_end = end
    if (at.date() - date.fromisoformat(period_end)).days > 200:
        return None
    return {'value':value, 'available_at':max(available_at(r,accepted) for r in components).isoformat(),
            'period_end':period_end, 'components':[provenance(r,cik,accepted) for r in components]}


def us_session_times(d):
    # US DST rules since 2007. Data collection is bounded to ten recent years.
    march = date(d.year,3,8)
    start = march + timedelta(days=(6-march.weekday()) % 7)
    november = date(d.year,11,1)
    end = november + timedelta(days=(6-november.weekday()) % 7)
    offset = 4 if start <= d < end else 5
    return (datetime.combine(d,day_time(9+offset,30),UTC), datetime.combine(d,day_time(16+offset),UTC))


def valuation_rows(facts, bars, accepted, splits, issuer, cutoff, observed):
    monthly = {}
    for bar in bars:
        monthly[bar['date'][:7]] = bar
    result, missing = [], []
    # Completed months only for the descriptive historical comparison.
    for month, bar in sorted(monthly.items()):
        if month >= cutoff.date().isoformat()[:7]:
            continue
        session_open, nominal_close = us_session_times(date.fromisoformat(bar['date']))
        close_at = nominal_close.isoformat()
        # Pre-open information avoids falsely using an intraday/early-close filing for that session's price.
        eps = ttm_eps(facts, session_open, accepted, splits, issuer['cik'])
        if not eps:
            missing.append(month + ': trailing EPS unavailable or stale')
            continue
        result.append({**bar, 'close_at':close_at, 'eps_ttm':eps['value'], 'eps_available_at':eps['available_at'],
                       'eps_source':eps['components'][-1]['source'], 'eps_components':eps['components'],
                       'basis':'Monthly final supplied session; pre-open diluted TTM EPS = annual + YTD - prior YTD; later splits aligned at capture; nominal regular close'})
    return result[-61:], missing


class FilingText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','ix:header','ix:hidden'):
            self.skip += 1
        if not self.skip and tag in ('p','div','tr','br','h1','h2','h3'):
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style','ix:header','ix:hidden') and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def filing_excerpts(document):
    parser = FilingText()
    parser.feed(document)
    lines = [' '.join(line.split()) for line in ''.join(parser.parts).splitlines()]
    lines = [line for line in lines if len(line) >= 120 and not re.fullmatch(r'[\d\s.,()%$\-]+',line)
             and not re.search(r'forward-looking|private securities litigation|table of contents',line,re.I)]
    topics = {
        'business':r'\b(we offer|we develop|our business|our products|our segments|reportable segments)\b',
        'cash_and_investment':r'\b(capital expenditures?|capital spending|cash flows from operati(?:ng|ons)|capital investments?)\b',
        'risks':r'\b(risks? include|could adversely|may adversely|competition|competitive)\b',
        'financing':r'\b(debt maturities|credit facility|repurchase|borrowing|lease commitments)\b'}
    return {key: [line[:1800] for line in lines if re.search(pattern,line,re.I)][:3] for key,pattern in topics.items()}


def build_bundle(raw, manifest):
    entries = {e['role']:e for e in manifest['sources']}
    cutoff = timestamp(manifest['cutoff'])
    issuer = manifest['issuer']
    facts, submissions = raw['facts'], raw['submissions']
    if str(facts.get('cik')).zfill(10) != issuer['cik'] or str(submissions.get('cik')).zfill(10) != issuer['cik']:
        raise ResearchError("SEC response CIK does not match the resolved issuer")
    sic = str(submissions.get('sic',''))
    if not re.fullmatch(r'\d{4}',sic) or 6000 <= int(sic) <= 6999 or not any(r['form']=='10-K' for r in filing_rows(submissions)):
        raise ResearchError("Automatic screen supports US GAAP 10-K nonfinancial operating companies; this issuer needs a sector-specific review")
    if issuer['ticker'] not in [str(t).upper() for t in submissions.get('tickers',[])]:
        raise ResearchError("SEC submissions do not confirm this security ticker")
    filings = filing_rows(submissions)
    accepted = {r['accession']:r['accepted_at'] for r in filings if r['accepted_at']}
    financials, missing = annual_financials(facts,issuer,cutoff,entries['facts']['observed_at'],accepted)
    if not financials:
        raise ResearchError("No supported USD annual financial periods; custom taxonomy or issuer review required")
    bars, splits, rejected, valuations, pe_missing = [], [], [], [], []
    provider_errors = list(manifest.get('errors',[]))
    if 'prices' in raw:
        try:
            bars, splits, rejected = chart_rows(raw['prices'],issuer,cutoff,entries['prices']['observed_at'])
            valuations, pe_missing = valuation_rows(facts,bars,accepted,splits,issuer,cutoff,entries['facts']['observed_at'])
        except ResearchError as error:
            bars, splits, valuations = [], [], []
            provider_errors.append(str(error))
    # A split can make reported annual share counts incomparable; keep levels, withhold growth.
    if splits:
        for row in financials:
            row['basis'] += '; annual share basis unverified for ' + row['date']
    bundle = {'scan_schema':1,'company':submissions.get('name',issuer['name']), 'currency':'USD','sector':'nonfinancial',
              'units':'whole_currency_and_shares','fictional':False,'cutoff':manifest['cutoff'],
              'price_basis':'split_adjusted_not_dividend_adjusted','comparable_regime':False,'descriptive_history':True,
              'comparability_notes':'Automatic current-source reconstruction, not a point-in-time backtest. Economic comparability is unreviewed. Historical P/E statistics describe this sample, not a fair-value baseline. Split alignment uses provider event dates and EPS publication dates; verify complex corporate actions.',
              'financials':financials,'valuations':valuations,'bars':bars[-1260:]}
    latest_eps = ttm_eps(facts,cutoff,accepted,splits,issuer['cik']) if bars else None
    latest = None
    if bars and latest_eps:
        latest = {'price_date':bars[-1]['date'], 'close':bars[-1]['close'], 'eps_period_end':latest_eps['period_end'],
                  'eps_available_at':latest_eps['available_at'], 'eps_ttm':latest_eps['value'],
                  'pe':bars[-1]['close']/latest_eps['value'] if latest_eps['value']>0 else None,
                  'basis':'Latest captured EPS with latest completed daily close; may differ from completed-month historical screen',
                  'eps_components':latest_eps['components']}
    context = {'issuer':issuer,'industry':submissions.get('sicDescription'),'sic':sic,'filings':filings[:12],
               'missing_fields':missing,'missing_pe_months':pe_missing,'rejected_price_rows':rejected,
               'provider_errors':provider_errors,'latest_valuation':latest,
               'filing_excerpts':filing_excerpts(raw['annual_filing']) if 'annual_filing' in raw else {},
               'capture_sources':manifest['sources'], 'cutoff':manifest['cutoff']}
    return bundle, context


def fresh_output(out):
    out = Path(out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ResearchError("Use a new or empty output directory; prior research is preserved")
    out.mkdir(parents=True,exist_ok=True)
    return out


def collect(query, out):
    out = fresh_output(out)
    cap = Capture(out / 'sources')
    index = cap.get('directory',TICKERS)
    issuer = resolve_company(query,index)
    submissions = cap.get('submissions','https://data.sec.gov/submissions/CIK%s.json' % issuer['cik'])
    facts = cap.get('facts','https://data.sec.gov/api/xbrl/companyfacts/CIK%s.json' % issuer['cik'])
    raw, errors = {'directory':index,'submissions':submissions,'facts':facts}, []
    # Ten years of split events cover the five-year display and earlier EPS publication bases.
    price_url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + quote(issuer['ticker'].replace('.','-'),safe='') + '?' + urlencode({'range':'10y','interval':'1d','events':'splits,div'})
    try:
        raw['prices'] = cap.get('prices',price_url)
    except ResearchError as error:
        errors.append(str(error))
    annuals = [r for r in filing_rows(submissions) if r['form']=='10-K' and r['accepted_at'] and timestamp(r['accepted_at']) <= timestamp(utc_now())]
    if annuals:
        row = max(annuals,key=lambda r:r['accepted_at'])
        url = 'https://www.sec.gov/Archives/edgar/data/%d/%s/%s' % (int(issuer['cik']),row['accession'].replace('-',''),row['document'])
        try:
            raw['annual_filing'] = cap.get('annual_filing',url,as_json=False)
        except ResearchError as error:
            errors.append(str(error))
    manifest = {'capture_version':1,'issuer':issuer,'cutoff':utc_now(),'sources':cap.entries,'errors':errors,
                'rights':'Local research capture. Provider rights remain separate from MIT code; do not redistribute raw responses.'}
    json_write(out/'capture.json',manifest)
    return write_research(out,raw,manifest)


def replay(capture_dir, out):
    root = Path(capture_dir)
    try:
        manifest = json.loads((root/'capture.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):
        raise ResearchError("Cannot read the saved capture manifest")
    if manifest.get('capture_version') != 1:
        raise ResearchError("Unsupported capture version")
    raw = {}
    for entry in manifest.get('sources',[]):
        role = entry.get('role')
        if role not in {'directory','facts','submissions','prices','annual_filing'} or role in raw:
            raise ResearchError("Invalid or duplicate capture role")
        expected = role + ('.html' if role=='annual_filing' else '.json')
        if entry.get('file') != expected:
            raise ResearchError("Unsafe capture file name")
        path = root/'sources'/expected
        if path.is_symlink() or (root/'sources').is_symlink():
            raise ResearchError("Capture files must not be symbolic links")
        data = path.read_bytes()
        if len(data)>MAX_BYTES or hashlib.sha256(data).hexdigest()!=entry.get('sha256'):
            raise ResearchError("Capture integrity check failed")
        safe_source(entry['url'])
        if timestamp(entry['observed_at'])>timestamp(manifest['cutoff']):
            raise ResearchError("Capture observation is later than cutoff")
        raw[role] = data.decode('utf-8',errors='replace') if role=='annual_filing' else json.loads(data)
    if not {'facts','submissions','directory'} <= set(raw):
        raise ResearchError("Capture lacks required SEC responses")
    if resolve_company(manifest['issuer']['ticker'],raw['directory']) != manifest['issuer']:
        raise ResearchError("Capture issuer does not match its directory")
    return write_research(fresh_output(out),raw,manifest)


def write_research(out, raw, manifest):
    bundle, context = build_bundle(raw,manifest)
    result = scan(bundle)
    save(out/'screen',bundle,result)
    json_write(out/'research.json',{'context':context,'scan':result})
    from .us_report import research_markdown, research_html
    markdown = research_markdown(bundle,result,context)
    (out/'research.md').write_text(markdown,encoding='utf-8')
    (out/'research.html').write_text(research_html(bundle,result,context),encoding='utf-8')
    report = {'company':bundle['company'],'ticker':manifest['issuer']['ticker'],'cutoff':manifest['cutoff'],
              'status':'PARTIAL' if context['provider_errors'] or context['missing_fields'] or not bundle['bars'] else 'RESEARCH_READY',
              'annual_periods':len(bundle['financials']),'daily_bars':len(bundle['bars']),'monthly_pe_observations':len(bundle['valuations']),
              'report':'research.html','input_sha256':digest(bundle),'scan_sha256':digest(result),
              'next':'Read research.md and source excerpts; distinguish reported facts, interpretation and unresolved questions.'}
    json_write(out/'receipt.json',report)
    return report
