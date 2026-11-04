"""Dated, offline research screens. Descriptive flags are not investment ratings."""
from datetime import date
from statistics import mean, median
from urllib.parse import urlparse
import html
import json

from .research import ResearchError, digest, number as finite_number, text, timestamp


def number(value, label, **kwargs):
    result = finite_number(value, label, **kwargs)
    if abs(result) > 1e100:
        raise ResearchError(label + " exceeds supported numeric magnitude; check units")
    return result


def day(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ResearchError("Dates must be YYYY-MM-DD")


def validate(bundle):
    if not isinstance(bundle, dict) or bundle.get("scan_schema") != 1:
        raise ResearchError("Expected scan_schema 1")
    for key in ("company", "currency", "comparability_notes"):
        text(bundle.get(key), key)
    if not isinstance(bundle.get("fictional"), bool) or not isinstance(bundle.get("comparable_regime"), bool):
        raise ResearchError("fictional and comparable_regime must be explicit booleans")
    if bundle.get("sector") != "nonfinancial":
        raise ResearchError("This screen supports nonfinancial operating companies only")
    if bundle.get("units") != "whole_currency_and_shares":
        raise ResearchError("Use whole currency units and whole shares")
    if bundle.get("price_basis") != "split_adjusted_not_dividend_adjusted":
        raise ResearchError("Prices and EPS must use the same split adjustment; no dividend-adjusted P/E")
    cutoff = timestamp(bundle.get("cutoff"))
    for group in ("financials", "valuations", "bars"):
        rows = bundle.get(group)
        if not isinstance(rows, list):
            raise ResearchError(group + " must be a list (empty means unavailable)")
        dates = []
        for row in rows:
            if not isinstance(row, dict):
                raise ResearchError("Each observation must be an object")
            d = day(row.get("date"))
            dates.append(d)
            available = timestamp(row.get("available_at"))
            observed = timestamp(row.get("observed_at"))
            if available.date() < d or observed < available:
                raise ResearchError("An observation cannot precede its period/close or availability")
            for key in ("source", "basis"):
                text(row.get(key), key)
            if not bundle["fictional"]:
                u = urlparse(row["source"])
                if u.scheme not in ("https", "http") or not u.netloc:
                    raise ResearchError("Real observations require an HTTP(S) source")
            if row.get("status") not in ("active", "withdrawn", "superseded"):
                raise ResearchError("Unknown source status")
            if group == "financials":
                if row.get("period_type") != "FY":
                    raise ResearchError("Financial screen requires full fiscal years; no quarterly/YTD mixing")
                start = day(row.get("period_start"))
                if not 350 <= (d - start).days <= 380:
                    raise ResearchError("Fiscal year length must be 350–380 days")
                for key in ("revenue", "capex", "cash", "debt", "diluted_shares"):
                    if key not in row:
                        raise ResearchError("Missing financial field; use explicit null for unknown")
                    if row[key] is not None:
                        number(row[key], key, minimum=0, positive=key == "diluted_shares")
                for key in ("net_income", "operating_cash_flow"):
                    if key not in row:
                        raise ResearchError("Missing financial field; use explicit null for unknown")
                    if row[key] is not None:
                        number(row[key], key)
            elif group == "valuations":
                number(row.get("close"), "close", positive=True)
                number(row.get("eps_ttm"), "eps_ttm")
                known = timestamp(row.get("eps_available_at"))
                close_time = timestamp(row.get("close_at"))
                if close_time.date() != d or available < close_time or known > close_time:
                    raise ResearchError("P/E requires EPS available by the historical close, not later restated earnings")
                text(row.get("eps_source"), "eps_source")
                if not bundle["fictional"]:
                    u = urlparse(row["eps_source"])
                    if u.scheme not in ("http", "https") or not u.netloc:
                        raise ResearchError("Real EPS requires an HTTP(S) source")
            else:
                for key in ("open", "high", "low", "close"):
                    number(row.get(key), key, positive=True)
                if not row["low"] <= min(row["open"], row["close"]) <= max(row["open"], row["close"]) <= row["high"]:
                    raise ResearchError("OHLC bar is inconsistent")
        if dates != sorted(dates) or len(set(dates)) != len(dates):
            raise ResearchError(group + " must be sorted, with unique dates")
        if group == "valuations" and len({(d.year, d.month) for d in dates}) != len(dates):
            raise ResearchError("Use one consistently sampled P/E observation per month")
    # Catch non-finite derived arithmetic as a controlled error, never emit NaN/Infinity.
    try:
        digest(bundle)
    except (ValueError, OverflowError, TypeError):
        raise ResearchError("Scan bundle must contain finite JSON values")
    return cutoff


def ratio(a, b):
    return a / b if a is not None and b is not None and b > 0 else None


def difference(a, b):
    return a - b if a is not None and b is not None else None


def scan(bundle):
    cutoff = validate(bundle)
    excluded, selected, findings = [], {}, []

    def flag(code, observation, question):
        findings.append({"code": code, "observation": observation, "next_question": question})

    for group in ("financials", "valuations", "bars"):
        selected[group] = []
        for row in bundle[group]:
            reasons = []
            if row["status"] != "active":
                reasons.append(row["status"])
            if timestamp(row["available_at"]) > cutoff:
                reasons.append("available_after_cutoff")
            if timestamp(row["observed_at"]) > cutoff:
                reasons.append("observed_after_cutoff")
            if reasons:
                excluded.append({"group": group, "date": row["date"], "reasons": reasons})
            else:
                selected[group].append(row)
    financials, valuations, bars = (selected[k] for k in ("financials", "valuations", "bars"))
    result = {"scan_version": "1.1.0", "company": bundle["company"], "currency": bundle["currency"],
              "cutoff": bundle["cutoff"], "fictional": bundle["fictional"], "input_sha256": digest(bundle),
              "status": "DESCRIPTIVE_ONLY", "excluded": excluded, "findings": findings,
              "comparability_notes": bundle["comparability_notes"], "sources": selected}
    f = {"status": "NO_DATA"}
    if financials:
        cur = financials[-1]
        f = {"status": "AVAILABLE", "period_end": cur["date"], "periods": len(financials),
             "free_cash_flow": difference(cur["operating_cash_flow"], cur["capex"]),
             "cash_conversion": ratio(cur["operating_cash_flow"], cur["net_income"]),
             "net_margin": ratio(cur["net_income"], cur["revenue"]), "net_debt": difference(cur["debt"], cur["cash"]),
             "revenue_growth": None, "share_growth": None}
        if any(cur[k] is None for k in ('net_income','operating_cash_flow','capex','revenue','cash','debt','diluted_shares')):
            f['status'] = 'PARTIAL'
            flag('MISSING_FINANCIAL_FIELDS', 'Some financial fields are unknown; dependent metrics are withheld.', 'Inspect field_sources and missing_fields; missing debt or capex must not be treated as zero.')
        if (cutoff.date() - day(cur["date"])).days > 550:
            f["status"] = "STALE"
            flag("STALE_FINANCIALS", "Last admissible fiscal year ended over 550 days before cutoff.", "Obtain the next filed annual report; do not treat this screen as current.")
        if cur["net_income"] is not None and cur["net_income"] > 0 and f["free_cash_flow"] is not None and f["free_cash_flow"] < 0:
            flag("PROFIT_WITHOUT_FREE_CASH", "Positive net income, negative CFO minus capex.", "Is working capital or growth capex temporary, or are reported profits failing to produce cash?")
        if cur["net_income"] is not None and cur["net_income"] > 0 and cur["operating_cash_flow"] is not None and cur["operating_cash_flow"] < cur["net_income"]:
            flag("CASH_BELOW_PROFIT", "Operating cash flow is below net income.", "Reconcile receivables, inventories, noncash items and seasonality in the cash-flow notes.")
        if len(financials) >= 2:
            prev = financials[-2]
            comparable_years = (day(cur["period_start"]) - day(prev["date"])).days == 1 and cur["basis"] == prev["basis"]
            if comparable_years:
                growth = ratio(cur["revenue"], prev["revenue"])
                f["revenue_growth"] = growth - 1 if growth is not None else None
                shares = ratio(cur["diluted_shares"], prev["diluted_shares"])
                f["share_growth"] = shares - 1 if shares is not None else None
                if f["share_growth"] is not None and f["share_growth"] > 0:
                    flag("DILUTION", "Diluted weighted-average shares increased year over year.", "How much is stock compensation, new issuance or acquisition consideration; was per-share value created?")
                prior_debt = difference(prev['debt'],prev['cash'])
                if f['net_debt'] is not None and prior_debt is not None and f['net_debt'] > prior_debt:
                    flag("NET_DEBT_INCREASED", "Net debt increased year over year.", "Check maturities, covenants, refinancing costs and the use of proceeds.")
            else:
                flag("NONCOMPARABLE_YEARS", "Latest annual periods are not adjacent or use different accounting bases.", "Reconcile periods and accounting policies before measuring growth.")
    result["financials"] = f
    v = {"status": "NO_DATA", "current_pe": None, "historical_mean": None, "historical_median": None, "percentile": None}
    if valuations:
        cur = valuations[-1]
        # Current observation is excluded from the baseline. At most 60 prior months.
        history = valuations[:-1][-60:]
        valid = [r["close"] / r["eps_ttm"] for r in history if r["eps_ttm"] > 0]
        v.update({"as_of": cur["date"], "prior_observations": len(history), "positive_eps_observations": len(valid),
                  "nonpositive_eps_observations": len(history) - len(valid), "status": "INSUFFICIENT_HISTORY"})
        months = [day(r["date"]).year * 12 + day(r["date"]).month for r in history + [cur]]
        contiguous = all(b - a == 1 for a, b in zip(months, months[1:]))
        v["contiguous_months"] = contiguous
        if cur["eps_ttm"] <= 0:
            v["status"] = "NOT_MEANINGFUL"
            flag("NONPOSITIVE_EPS", "Current trailing earnings are zero or negative; P/E is withheld.", "Examine cash runway, assets and supported operating scenarios instead of a negative P/E ranking.")
        else:
            v["current_pe"] = cur["close"] / cur["eps_ttm"]
            descriptive_only = bundle.get('descriptive_history') is True and not bundle['comparable_regime']
            if len(valid) >= 12 and len(valid) == len(history) and contiguous and (bundle["comparable_regime"] or descriptive_only) and len({r["basis"] for r in history + [cur]}) == 1:
                current = v["current_pe"]
                med = median(valid)
                v.update({"status": "DESCRIPTIVE_HISTORY", "historical_mean": mean(valid), "historical_median": med,
                          "percentile": 100 * (sum(x < current for x in valid) + .5 * sum(x == current for x in valid)) / len(valid),
                          "distance_from_median": current / med - 1,
                          "window_start": history[0]["date"], "window_end": history[-1]["date"]})
                if current < med:
                    flag("PE_BELOW_HISTORY", "P/E is below the supplied prior-month median.", "Did sustainable earnings, growth, rates, risk or capital allocation change enough to justify a lower multiple?")
                if descriptive_only:
                    v['status'] = 'DESCRIPTIVE_NONCOMPARABLE'
                    flag('REGIME_NOT_REVIEWED', 'Historical P/E statistics are displayed, but economic comparability has not been established.', 'Review growth, business mix, accounting and risk before using history as a valuation baseline.')
            else:
                flag("PE_BASELINE_WITHHELD", "Historical comparison needs 12+ consecutive prior monthly observations, positive EPS throughout and a declared comparable basis/regime.", "Resolve loss years, missing months, split adjustments, reporting definitions and business changes before invoking mean reversion.")
        if (cutoff.date() - day(cur["date"])).days > 45:
            v["freshness"] = "STALE"
            flag("STALE_VALUATION", "Last admissible P/E observation is over 45 days old.", "Obtain a dated current price and the latest published trailing EPS; do not present this as current valuation.")
    result["valuation"] = v
    p = {"status": "NO_DATA", "sma_50": None, "sma_200": None}
    if bars:
        closes = [b["close"] for b in bars]
        cur = closes[-1]
        recent = closes[-252:]
        peak, mdd = recent[0], 0
        for c in recent:
            peak = max(peak, c)
            mdd = min(mdd, c / peak - 1)
        p.update({"status": "DESCRIPTIVE_HISTORY", "as_of": bars[-1]["date"], "observations": len(bars), "last_close": cur,
                  "window_observations": len(recent), "drawdown_from_window_high": cur / max(recent) - 1, "max_drawdown_in_window": mdd})
        # Trading calendars are not inferred. Suppress averages on gaps over 7 calendar days or changed bases.
        gaps = any((day(b["date"]) - day(a["date"])).days > 7 for a, b in zip(bars, bars[1:]))
        uniform = len({b["basis"] for b in bars}) == 1
        if uniform and not gaps:
            for n in (50, 200):
                if len(closes) >= n:
                    p["sma_" + str(n)] = mean(closes[-n:])
                    p["distance_from_sma_" + str(n)] = cur / p["sma_" + str(n)] - 1
        else:
            p = {"status": "NONCOMPARABLE_HISTORY", "as_of": bars[-1]["date"], "observations": len(bars), "sma_50": None, "sma_200": None}
            flag("PRICE_HISTORY_REVIEW", "Price history has a gap over seven days or different adjustment bases.", "Resolve suspensions, missing bars and corporate-action adjustments before interpreting chart statistics.")
        if (cutoff.date() - day(bars[-1]["date"])).days > 7:
            p["freshness"] = "STALE"
            flag("STALE_PRICE", "Latest admissible daily bar is over seven days old.", "Check suspension, market calendar and missing data before treating the price as current.")
    result["price_context"] = p
    if excluded:
        flag("EXCLUDED_EVIDENCE", "Some supplied observations were withdrawn, superseded or unavailable at the cutoff.", "Inspect excluded dates before using older admissible data; a missing latest row is not a clean result.")
    flag("MEAN_REVERSION_NOT_ESTIMATED", "No reversion probability, timing, fair value or expected return is estimated.", "What economic mechanism would restore cash earnings, and what evidence would show permanent impairment?")
    try:
        digest(result)
    except (ValueError, OverflowError):
        raise ResearchError("Calculated values exceed finite numeric limits; check units and magnitudes")
    return result


def chart(title, series):
    """Accessible static SVG; each series is a sequence of finite values or None."""
    values = [v for _, ys in series for v in ys if v is not None]
    if not values:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 260"><title>' + html.escape(title) + '</title><text x="30" y="70">No admissible data</text></svg>'
    lo, hi = min(0, min(values)), max(values)
    span = hi - lo or 1
    colors = ["#14634c", "#a3472f", "#486db5"]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 320" role="img"><title>' + html.escape(title) + '</title><rect width="800" height="320" fill="#f5f7f5"/>',
             '<text x="28" y="30" font-family="sans-serif" font-size="17">' + html.escape(title) + '</text>']
    for i, (label, ys) in enumerate(series):
        color = colors[i % len(colors)]
        for j, val in enumerate(ys):
            if val is None:
                continue
            x = 65 + 690 * j / max(1, len(ys) - 1)
            y = 245 - 185 * (val - lo) / span
            parts.append('<circle cx="%.2f" cy="%.2f" r="3" fill="%s"/>' % (x, y, color))
            if j and ys[j-1] is not None:
                px, py = 65 + 690 * (j-1) / max(1, len(ys)-1), 245 - 185 * (ys[j-1] - lo) / span
                parts.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="2"/>' % (px, py, x, y, color))
        parts.append('<text x="%d" y="290" fill="%s" font-family="sans-serif" font-size="13">%s</text>' % (28+i*250, color, html.escape(label)))
    parts.extend('<text x="5" y="%d" font-family="sans-serif" font-size="11">%.3g</text>' % (y, v) for y,v in ((65,hi),(245,lo)))
    parts.append('</svg>')
    return ''.join(parts)


def figures(result):
    f, v, bars = (result["sources"][k] for k in ("financials", "valuations", "bars"))
    span = lambda rows: rows[0]["date"] + " to " + rows[-1]["date"] if rows else "no data"
    prefix = "FICTIONAL · " if result["fictional"] else ""
    out = {}
    if len({r["basis"] for r in f}) <= 1:
        out["cash-vs-profit.svg"] = chart(prefix + "Annual cash and profit · " + result["currency"] + " · " + span(f), [
            ("Net income", [r["net_income"] for r in f]), ("CFO minus capex", [difference(r["operating_cash_flow"], r["capex"]) for r in f])])
    if result["valuation"]["status"] in ("DESCRIPTIVE_HISTORY", "DESCRIPTIVE_NONCOMPARABLE"):
        out["pe-history.svg"] = chart(prefix + "Monthly trailing P/E (x) · " + span(v), [("P/E", [r["close"]/r["eps_ttm"] if r["eps_ttm"] > 0 else None for r in v]), ("Prior-month median", [result["valuation"]["historical_median"]]*len(v))])
    if result["price_context"]["status"] == "DESCRIPTIVE_HISTORY":
        cs = [r["close"] for r in bars]
        out["price-context.svg"] = chart(prefix + "Daily price context · " + result["currency"] + " · " + span(bars), [("Split-adjusted close", cs)] + [(str(n)+"-observation average", [mean(cs[j+1-n:j+1]) if j+1>=n and result["price_context"]["sma_"+str(n)] is not None else None for j in range(len(cs))]) for n in (50,200)])
    return out


def markdown(result):
    label = "FICTIONAL · " if result["fictional"] else ""
    lines = ["# " + label + result["company"] + " — research screen", "", "Cutoff: " + result["cutoff"],
             "", "Descriptive observations from supplied data. No buy/sell rating or estimated reversion probability.",
             "", "Comparability declaration: " + result["comparability_notes"], "", "## Measurements"]
    for name in ("financials", "valuation", "price_context"):
        lines += ["", "### " + name.replace('_', ' ').title(), "", "```json", json.dumps(result[name], indent=2, allow_nan=False), "```"]
    lines += ["", "## What to investigate"]
    for f in result["findings"]:
        lines += ["", "- " + f["code"] + ": " + f["observation"], "  Next: " + f["next_question"]]
    lines += ["", "## Exclusions", "", json.dumps(result["excluded"], ensure_ascii=False), "", "## Source observations", "", "```json", json.dumps(result["sources"], indent=2, ensure_ascii=False), "```", "", "Input SHA-256: " + result["input_sha256"], "", "Research only. Source timestamps, units and adjustment bases are user declarations, not independently verified facts."]
    return '\n'.join(lines) + '\n'


def save(out, bundle, result):
    from pathlib import Path
    directory = Path(out)
    if directory.exists() and any(directory.iterdir()):
        raise ResearchError("Scan output must be a new or empty directory")
    directory.mkdir(parents=True, exist_ok=True)
    md = markdown(result)
    svgs = figures(result)
    sections = ''.join('<figure>'+svg+'<figcaption>Observation order; full dates and inputs below. Descriptive history, not a forecast.</figcaption></figure>' for svg in svgs.values())
    measurements = []
    percent_keys = {'net_margin', 'revenue_growth', 'share_growth', 'distance_from_median',
                    'drawdown_from_window_high', 'max_drawdown_in_window', 'distance_from_sma_50', 'distance_from_sma_200'}
    for name in ('financials', 'valuation', 'price_context'):
        rows = []
        for key, value in result[name].items():
            if value is None:
                display = 'Not available'
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                display = ('%.2f%%' % (value * 100)) if key in percent_keys else format(value, ',.3f').rstrip('0').rstrip('.')
                if key == 'percentile': display += 'th percentile'
                if key == 'cash_conversion': display += 'x CFO / net income'
                if key in ('free_cash_flow', 'net_debt', 'last_close', 'sma_50', 'sma_200'): display += ' ' + result['currency']
            else:
                display = str(value)
            rows.append('<tr><th scope="row">' + html.escape(key.replace('_',' ')) + '</th><td>' + html.escape(display) + '</td></tr>')
        measurements.append('<section><h2>' + name.replace('_',' ').title() + '</h2><table>' + ''.join(rows) + '</table></section>')
    questions = ''.join('<li><strong>' + html.escape(f['observation']) + '</strong><p>' + html.escape(f['next_question']) + '</p></li>' for f in result['findings'])
    label = 'Fictional example' if result['fictional'] else 'Supplied-data research screen'
    valuation, financial = result['valuation'], result['financials']
    pe = valuation.get('current_pe')
    fcf = financial.get('free_cash_flow')
    overview = '<p><strong>Trailing P/E: ' + ('not meaningful or unavailable' if pe is None else format(pe, '.2f') + 'x') + '</strong> (' + html.escape(valuation.get('as_of', 'no date')) + '). '
    overview += '<strong>Annual CFO minus capex: ' + ('unavailable' if fcf is None else format(fcf, ',.0f') + ' ' + html.escape(result['currency'])) + '</strong> (year ended ' + html.escape(financial.get('period_end', 'unknown')) + ').</p>'
    page = ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Value Investor research screen</title><style>body{max-width:960px;margin:40px auto;padding:0 20px;font:16px/1.6 system-ui;color:#111714;background:#fbfcfa}'
            'h1{font-size:clamp(1.8rem,4vw,2.8rem);line-height:1.2;letter-spacing:-.025em}h2{font-size:1.4rem}section{margin:40px 0}svg{width:100%;height:auto}figure{margin:28px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}'
            'table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{padding:9px 4px;border-bottom:1px solid #d7ded9;overflow-wrap:anywhere}th{text-align:left;font-weight:500}td{text-align:right;max-width:45vw}'
            'li{margin:18px 0}li p{margin:5px 0}figcaption,.clock{font-size:13px;color:#5b665f}summary{cursor:pointer;min-height:44px;padding:10px 0}a{color:#087653}:focus-visible{outline:3px solid #087653;outline-offset:3px}'
            'footer{margin-top:36px;border-top:1px solid #d7ded9;padding-top:20px}details{margin:20px 0}ul{padding-left:22px}</style><main>'
            '<p>AhaSignals / ' + label + '</p><h1>' + html.escape(result['company']) + '</h1><p class="clock">Research cutoff: ' + html.escape(result['cutoff']) + '</p>'
            '<p>Start with the cash, then ask what could explain the valuation. Price history supplies context.</p>'
            + overview +
            '<section><h2>What needs a closer look?</h2><ul>' + questions + '</ul></section>'
            '<details><summary>Comparability and excluded evidence (' + str(len(result['excluded'])) + ')</summary><p>' + html.escape(result['comparability_notes']) + '</p><pre>' + html.escape(json.dumps(result['excluded'], indent=2)) + '</pre></details>'
            + ''.join(measurements) + '<section><h2>Historical views</h2>' + sections + '</section>'
            '<details><summary>Inspect source observations, dates and input hash</summary><pre>' + html.escape(md) + '</pre></details>'
            '<footer>Research only. No reversion forecast, fair-value estimate or investment rating. Source dates and adjustment bases are supplied declarations. '
            '<a href="https://ahasignals.com/methodology/">AhaSignals research method</a>.</footer></main></html>')
    for filename, content in dict(svgs, **{"scan.md":md, "scan.html":page, "scan.json":json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False), "inputs.json":json.dumps(bundle, indent=2, ensure_ascii=False, allow_nan=False)}).items():
        (directory / filename).write_text(content, encoding="utf-8")
