"""Validate dated research, calculate scenarios, and render inspectable reports."""
import hashlib
import html
import json
import math
from datetime import datetime, timezone
from urllib.parse import urlparse


class ResearchError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError()
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError):
        raise ResearchError("Timestamps must be ISO 8601 with an explicit time zone")


def number(value, label, minimum=None, positive=False):
    try:
        finite = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ResearchError(label + " must be a finite number")
    if (minimum is not None and value < minimum) or (positive and value <= 0):
        raise ResearchError(label + " is outside its allowed range")
    return float(value)


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ResearchError(label + " must be nonempty text")
    return value


def unique(items, label):
    if not isinstance(items, list) or not items:
        raise ResearchError(label + " must be a nonempty list")
    ids = [text(x.get("id"), label + ".id") for x in items if isinstance(x, dict)]
    if len(ids) != len(items) or len(set(ids)) != len(ids):
        raise ResearchError(label + " contains invalid or duplicate IDs")
    return set(ids)


def validate(bundle):
    """Reject malformed inputs; dated inadmissibility is a reported abstention."""
    if not isinstance(bundle, dict) or bundle.get("schema_version") != 1:
        raise ResearchError("Expected a schema_version 1 research bundle")
    for k in ("id", "company", "currency", "business", "event", "resolution_rule", "horizon", "model_limits"):
        text(bundle.get(k), k)
    if bundle.get("archetype") not in ("clinical", "cash_merger", "general_scenarios"):
        raise ResearchError("Unsupported archetype")
    if not isinstance(bundle.get("fictional"), bool):
        raise ResearchError("fictional must be an explicit boolean")
    cutoff = timestamp(bundle.get("cutoff"))
    if bundle.get("mode") not in ("historical_public", "as_observed"):
        raise ResearchError("mode must be historical_public or as_observed")
    evidence_ids = unique(bundle.get("evidence"), "evidence")
    unique(bundle.get("scenarios"), "scenarios")
    for ev in bundle["evidence"]:
        for k in ("title", "claim", "rights", "version"):
            text(ev.get(k), "evidence." + k)
        if ev.get("kind") not in ("reported_fact", "management_statement", "assumption", "counterevidence"):
            raise ResearchError("Unknown evidence kind")
        if ev.get("status") not in ("active", "withdrawn", "superseded"):
            raise ResearchError("Unknown evidence status")
        published, observed = timestamp(ev.get("published_at")), timestamp(ev.get("observed_at"))
        if observed < published:
            raise ResearchError("Evidence cannot be observed before its declared publication")
        if not bundle["fictional"]:
            url = ev.get("url", "")
            if not isinstance(url, str) or not url.startswith(("https://", "http://")) or not urlparse(url).netloc:
                raise ResearchError("Real research requires an HTTP(S) source URL for every evidence item")
        if "content_sha256" in ev:
            v = ev["content_sha256"]
            if not isinstance(v, str) or len(v) != 64 or any(c not in "0123456789abcdef" for c in v):
                raise ResearchError("content_sha256 must be a lowercase SHA-256 digest")
    for s in bundle["scenarios"]:
        text(s.get("label"), "scenario.label")
        text(s.get("assumptions"), "scenario.assumptions")
        refs = s.get("evidence_ids")
        if not isinstance(refs, list) or not refs or not all(isinstance(x, str) and x in evidence_ids for x in refs):
            raise ResearchError("Each scenario must reference known evidence IDs")
        for k in ("operating_value_pv", "cash", "debt", "other_claims", "new_capital_net", "future_costs_pv", "shares", "new_shares"):
            number(s.get(k), "scenario." + k, minimum=None if k == "operating_value_pv" else 0, positive=k == "shares")
    price = bundle.get("price")
    if not isinstance(price, dict):
        raise ResearchError("price must contain value, as_of and max_age_hours")
    number(price.get("value"), "price.value", positive=True)
    timestamp(price.get("as_of"))
    number(price.get("max_age_hours"), "price.max_age_hours", minimum=0)
    for key in ("counterevidence", "unknowns", "invalidation_conditions"):
        values = bundle.get(key)
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ResearchError(key + " must explicitly list at least one item")
    weights = bundle.get("scenario_weights")
    if weights is not None:
        ids = {s["id"] for s in bundle["scenarios"]}
        if not isinstance(weights, dict) or set(weights) != ids:
            raise ResearchError("scenario_weights must cover exactly all scenario IDs")
        values = [number(v, "scenario weight", minimum=0) for v in weights.values()]
        if any(v > 1 for v in values) or not math.isclose(sum(values), 1, abs_tol=1e-9):
            raise ResearchError("Scenario weights must sum to one and lie within [0,1]")
        text(bundle.get("weight_basis"), "weight_basis")
    return cutoff


def analyze(bundle):
    cutoff = validate(bundle)
    evidence = {}
    for e in bundle["evidence"]:
        reasons = []
        if timestamp(e["published_at"]) > cutoff:
            reasons.append("published_after_cutoff")
        if bundle["mode"] == "as_observed" and timestamp(e["observed_at"]) > cutoff:
            reasons.append("observed_after_cutoff")
        if e["status"] != "active":
            reasons.append(e["status"])
        evidence[e["id"]] = {"admissible": not reasons, "reasons": reasons}
    scenarios = []
    for s in bundle["scenarios"]:
        blocked = [ref for ref in s["evidence_ids"] if not evidence[ref]["admissible"]]
        equity = (s["operating_value_pv"] + s["cash"] - s["debt"] - s["other_claims"]
                  + s["new_capital_net"] - s["future_costs_pv"])
        denominator = s["shares"] + s["new_shares"]
        number(equity, "calculated equity")
        number(denominator, "calculated diluted shares", positive=True)
        raw = equity / denominator
        number(raw, "calculated value per share")
        scenarios.append({"id": s["id"], "label": s["label"],
                          "status": "NEEDS_REVIEW" if blocked else "SCENARIO_ONLY",
                          "blocked_by": blocked, "equity_value": None if blocked else equity,
                          "per_share": None if blocked else max(0.0, raw),
                          "equity_floor_applied": False if blocked else raw < 0})
    age = (cutoff - timestamp(bundle["price"]["as_of"])).total_seconds() / 3600
    price_ok = 0 <= age <= bundle["price"]["max_age_hours"]
    valid = [s for s in scenarios if s["per_share"] is not None]
    inversions = []
    if price_ok:
        p = bundle["price"]["value"]
        for low in valid:
            for high in valid:
                if high["per_share"] <= low["per_share"]:
                    continue
                w = (p - low["per_share"]) / (high["per_share"] - low["per_share"])
                inversions.append({"low": low["id"], "high": high["id"],
                                   "status": "FEASIBLE" if 0 <= w <= 1 else "OUTSIDE_PAIR",
                                   "high_weight": w if 0 <= w <= 1 else None})
    all_valid = len(valid) == len(scenarios)
    weights = bundle.get("scenario_weights")
    weighted = sum(s["per_share"] * weights[s["id"]] for s in scenarios) if weights and all_valid else None
    return {"tool_version": "0.1.0", "bundle_hash": digest(bundle), "id": bundle["id"],
            "status": "SCENARIO_ONLY" if all_valid else "NEEDS_REVIEW",
            "decision_status": "NO_QUOTE", "probability_status": "NOT_ESTIMATED",
            "price_status": "ADMISSIBLE" if price_ok else "STALE_OR_FUTURE",
            "evidence": evidence, "scenarios": scenarios, "pairwise_price_weights": inversions,
            "weighted_scenario_value": weighted,
            "warning": "Scenario arithmetic is not a calibrated forecast. Price-matching weights are not real-world probabilities. NO_QUOTE: no validated probability or full cost/model-risk policy."}


def md(value):
    # Inputs are data, never markup or instructions. Neutralize Markdown/HTML.
    value = html.escape(str(value), quote=True).replace("\n", " ")
    for char in ("\\", "`", "*", "_", "[", "]", "|", "#"):
        value = value.replace(char, "\\" + char)
    return value


def markdown(bundle, result):
    lines = ["# " + md(bundle["company"]) + " — value research", "",
             "**" + ("FICTIONAL DEMO" if bundle["fictional"] else "USER-SUPPLIED RESEARCH") + " · " + result["status"] + "**", "",
             "Cutoff: " + md(bundle["cutoff"]) + " · " + md(bundle["mode"]) + " · " + md(bundle["currency"]), "",
             "## Business and material event", "", md(bundle["business"]), "", md(bundle["event"]), "",
             "Resolution: " + md(bundle["resolution_rule"]), "", "Horizon: " + md(bundle["horizon"]), "",
             "## What could it be worth?", "", "All amounts are in the stated currency; state values are present-value assumptions, not targets.", "",
             "| Scenario | Value per share | Status | Depends on |", "|---|---:|---|---|"]
    for s, original in zip(result["scenarios"], bundle["scenarios"]):
        value = "withheld" if s["per_share"] is None else "%.2f" % s["per_share"]
        lines.append("| %s | %s | %s | %s |" % (md(s["label"]), value, s["status"], md(", ".join(original["evidence_ids"]))))
    if any(s["equity_floor_applied"] for s in result["scenarios"]):
        lines += ["", "Equity floor applied: negative modeled net equity is displayed as zero, not a guaranteed recovery."]
    lines += ["", "## What does the price require?", "", "Price input: %.2f · %s · %s" % (bundle["price"]["value"], md(bundle["price"]["as_of"]), result["price_status"]), "",
              "Each row is a separate two-state slice, not an exhaustive multi-state solution or a market probability.", "",
              "| Lower-value state | Higher-value state | Price-matching higher-state weight |", "|---|---|---:|"]
    for row in result["pairwise_price_weights"]:
        value = "outside this pair" if row["high_weight"] is None else "%.1f%%" % (row["high_weight"] * 100)
        lines.append("| %s | %s | %s |" % (md(row["low"]), md(row["high"]), value))
    if not result["pairwise_price_weights"]:
        lines += ["", "No valid price comparison: check price age, evidence, and distinct scenario values."]
    if result["weighted_scenario_value"] is not None:
        lines += ["", "User-weighted scenario value: %.2f (not a validated expected value)." % result["weighted_scenario_value"], "", "Weight basis: " + md(bundle["weight_basis"])]
    for title, key in (("What am I missing?", "unknowns"), ("Counterevidence", "counterevidence"), ("What would change the answer?", "invalidation_conditions")):
        lines += ["", "## " + title, ""] + ["- " + md(x) for x in bundle[key]]
    lines += ["", "## Sources and assumptions", ""]
    for e in bundle["evidence"]:
        status = "admissible" if result["evidence"][e["id"]]["admissible"] else ", ".join(result["evidence"][e["id"]]["reasons"])
        lines += ["- **%s · %s · %s**: %s" % (md(e["id"]), md(e["kind"]), md(status), md(e["claim"])),
                  "  Published: %s; observed: %s; version: %s. Source: %s. Rights: %s." % tuple(md(e.get(k, "fictional")) for k in ("published_at", "observed_at", "version", "url", "rights"))]
    lines += ["", "## Model assumptions", ""] + ["- " + md(s["label"]) + ": " + md(s["assumptions"]) for s in bundle["scenarios"]]
    lines += ["", "## Research boundary", "", result["warning"], "", md(bundle["model_limits"]), "",
              "AhaSignals · independent research and education only. No investment, trading, legal, tax or medical advice; no affiliation or endorsement by source owners.", "",
              "Input SHA-256: `" + result["bundle_hash"] + "`", ""]
    return "\n".join(lines)


def html_report(bundle, result):
    """Semantic offline report; all user content is escaped and no scripts run."""
    esc = lambda value: html.escape(str(value), quote=True)
    money = lambda value: "Withheld" if value is None else format(value, ",.2f")
    tag = "FICTIONAL DEMO" if bundle["fictional"] else "USER-SUPPLIED RESEARCH"
    state = result["status"]
    rows = []
    for scenario, original in zip(result["scenarios"], bundle["scenarios"]):
        rows.append("<tr><th scope=\"row\">" + esc(scenario["label"]) + "</th><td class=number>" + money(scenario["per_share"]) + "</td><td>" + esc(scenario["status"]) + "</td><td>" + esc(", ".join(original["evidence_ids"])) + "</td></tr>")
    weights = []
    for row in result["pairwise_price_weights"]:
        weight = "Outside this pair" if row["high_weight"] is None else format(row["high_weight"] * 100, ".1f") + "%"
        weights.append("<tr><td>" + esc(row["low"]) + "</td><td>" + esc(row["high"]) + "</td><td class=number>" + weight + "</td></tr>")
    lists = ""
    for heading, key in (("What am I missing?", "unknowns"), ("Counterevidence", "counterevidence"), ("What would change the answer?", "invalidation_conditions")):
        lists += "<section><h2>" + heading + "</h2><ul>" + "".join("<li>" + esc(item) + "</li>" for item in bundle[key]) + "</ul></section>"
    sources = ""
    for ev in bundle["evidence"]:
        check = result["evidence"][ev["id"]]
        status = "Admissible" if check["admissible"] else ", ".join(check["reasons"])
        sources += "<article class=source><h3>" + esc(ev["id"] + " · " + ev["title"]) + "</h3><p class=eyebrow>" + esc(ev["kind"] + " · " + status) + "</p><p>" + esc(ev["claim"]) + "</p><dl>"
        for title, key in (("Published", "published_at"), ("Observed", "observed_at"), ("Version", "version"), ("Source", "url"), ("Rights", "rights")):
            sources += "<dt>" + title + "</dt><dd>" + esc(ev.get(key, "Fictional")) + "</dd>"
        sources += "</dl></article>"
    assumption_rows = ""
    for original in bundle["scenarios"]:
        assumption_rows += "<details><summary>" + esc(original["label"]) + " — inspect inputs</summary><p>" + esc(original["assumptions"]) + "</p><dl>"
        for key in ("operating_value_pv", "cash", "debt", "other_claims", "new_capital_net", "future_costs_pv", "shares", "new_shares"):
            assumption_rows += "<dt>" + esc(key.replace("_", " ")) + "</dt><dd>" + money(original[key]) + "</dd>"
        assumption_rows += "</dl></details>"
    floor = "<p>Negative modeled net equity is floored at zero; this is not a guaranteed recovery.</p>" if any(s["equity_floor_applied"] for s in result["scenarios"]) else ""
    weighted = "" if result["weighted_scenario_value"] is None else "<p>User-weighted scenario value: " + money(result["weighted_scenario_value"]) + ". Not a validated expected value. Basis: " + esc(bundle["weight_basis"]) + "</p>"
    comparisons = ("<div class=scroll><table><thead><tr><th>Lower state</th><th>Higher state</th><th>Price-matching weight</th></tr></thead><tbody>" + "".join(weights) + "</tbody></table></div>") if weights else "<p class=notice>No valid price comparison. Review source dependencies, quote freshness and distinct scenario values.</p>"
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>Value Investor Skill · Research</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f6f3;color:#203e32;font:16px/1.65 system-ui,-apple-system,sans-serif}main{max-width:1080px;margin:auto;padding:48px 28px}header{padding:24px 0 36px}h1{font-size:clamp(30px,5vw,48px);line-height:1.16;letter-spacing:-1.5px;max-width:850px;margin:18px 0}h2{font-size:24px;letter-spacing:-.5px;margin:0 0 16px}h3{font-size:17px;margin:0}p{margin:12px 0}.eyebrow{font-size:12px;letter-spacing:1.2px;text-transform:uppercase;color:#526c60}.status{display:inline-block;padding:6px 12px;border-radius:8px;background:#e6efe7;font-size:13px;font-weight:650}.review{background:#fff0d5;color:#775116}.subtitle{font-size:21px;color:#52685e}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:0 0 24px}.stat,section{background:white;border-radius:18px;padding:26px}.stat strong{display:block;font-size:25px;letter-spacing:-.5px}.stat span{font-size:13px;color:#52685e}section{margin:18px 0}table{width:100%;border-collapse:collapse;text-align:left;font-size:14px}th,td{padding:14px 12px;border-bottom:1px solid #e8ede8}thead{color:#64776c;font-size:12px}tbody th{font-weight:500}.number{text-align:right;font-variant-numeric:tabular-nums;font-weight:650}.scroll{overflow-x:auto}.note,footer{font-size:13px;color:#5b7165}.notice{background:#fff5e2;border-radius:10px;padding:16px}.source{padding:20px 0;border-top:1px solid #e8ede8}dl{display:grid;grid-template-columns:160px 1fr;font-size:13px;gap:5px}dt{color:#65796d}dd{margin:0;overflow-wrap:anywhere}details{padding:16px 0;border-top:1px solid #e8ede8}summary{cursor:pointer;font-weight:600}li{margin:8px 0}footer{padding:18px 0;overflow-wrap:anywhere}@media(max-width:650px){main{padding:20px 14px}.grid{grid-template-columns:1fr}.stat{padding:16px}section{padding:20px}dl{grid-template-columns:110px 1fr}th,td{padding:10px 8px}}@media print{body{background:white}main{padding:0}section,.stat{border:1px solid #ddd}details{break-inside:avoid}}
</style></head><body><main><header><div class=eyebrow>AhaSignals / Value Investor Skill</div>""" + '<h1>' + esc(bundle["company"]) + '</h1><p class=subtitle>What must be true? What would prove it wrong?</p><span class="status ' + ('review' if state == 'NEEDS_REVIEW' else '') + '">' + esc(tag + " · " + state) + '</span><p class=note>Evidence cutoff: ' + esc(bundle["cutoff"]) + " · " + esc(bundle["mode"]) + '</p></header><div class=grid><div class=stat><span>Price input · ' + esc(bundle["currency"]) + '</span><strong>' + money(bundle["price"]["value"]) + '</strong><span>' + esc(result["price_status"]) + '</span></div><div class=stat><span>Calibrated probability</span><strong>Not estimated</strong><span>Price-matching weights are conditional</span></div><div class=stat><span>Investment recommendation</span><strong>Not issued</strong><span>Research only · NO_QUOTE</span></div></div><section><h2>The business and the event</h2><p>' + esc(bundle["business"]) + '</p><p>' + esc(bundle["event"]) + '</p><p class=note>Resolution: ' + esc(bundle["resolution_rule"]) + '<br>Horizon: ' + esc(bundle["horizon"]) + '</p></section><section><h2>What could it be worth?</h2><p class=note>Present-value assumptions per share, in ' + esc(bundle["currency"]) + '. These are scenarios, not targets.</p><div class=scroll><table><thead><tr><th>Scenario</th><th>Value / share</th><th>Status</th><th>Evidence</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>' + floor + weighted + '</section><section><h2>What does the price require?</h2><p>Each row is a separate two-state calculation. Several assumptions can fit one price; these weights are not event probabilities.</p>' + comparisons + '</section>' + lists + '<section><h2>Inspect the assumptions</h2><p class=note>(Operating PV + cash − debt − other claims + net new capital − future costs PV) / (shares + new shares)</p>' + assumption_rows + '</section><section><h2>Sources and declared timestamps</h2>' + sources + '</section><section><h2>Research boundary</h2><p>' + esc(result["warning"]) + '</p><p>' + esc(bundle["model_limits"]) + '</p></section><footer>AhaSignals · independent research and education. No investment, trading, legal, tax or medical advice. No source-owner affiliation or endorsement.<p>Input SHA-256: ' + esc(result["bundle_hash"]) + '</p></footer></main></body></html>'
