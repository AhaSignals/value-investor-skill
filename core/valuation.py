"""Explicit per-share equity scenarios; never infer assumptions from a ticker."""
import math
import json
from .research import ResearchError, digest


def number(data, key, low=None, high=None):
    value = data.get(key)
    try:
        valid = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ResearchError(key + ' must be a finite number')
    if low is not None and value < low or high is not None and value > high:
        raise ResearchError(key + ' is outside the supported range')
    return float(value)


def calculate(data, sensitivity=True):
    if not isinstance(data, dict):
        raise ResearchError('Valuation input must be an object')
    try:
        json.dumps(data, allow_nan=False)
    except (ValueError, TypeError, OverflowError):
        raise ResearchError('Valuation input must contain finite JSON values') from None
    method = data.get('method')
    if method not in {'equity_dcf', 'earnings_power', 'residual_income'}:
        raise ResearchError('Choose equity_dcf, earnings_power or residual_income')
    if data.get('reviewed') is not True or not isinstance(data.get('rationale'), str) or len(data['rationale'].strip()) < 20:
        raise ResearchError('Review cash/share basis and explain the assumptions (at least 20 characters)')
    r = number(data, 'required_return', .005, .8)
    price = number(data, 'price', .000001, 1e9)
    rows, warnings = [], []
    terminal_pv = 0.0
    if method == 'earnings_power':
        cash = number(data, 'cash_per_share', .000001, 1e9)
        value = cash / r
        warnings.append('Zero growth in normalized equity cash forever; normalization and maintenance investment require evidence.')
    else:
        years = number(data, 'years', 1, 20)
        if not years.is_integer():
            raise ResearchError('years must be an integer')
        years = int(years)
        if method == 'equity_dcf':
            cash = number(data, 'cash_per_share', .000001, 1e9)
            growth = number(data, 'growth', -.9, 1)
            terminal = number(data, 'terminal_growth', -.1, .1)
            dilution = number(data, 'dilution', 0, .5)
            if terminal >= r:
                raise ResearchError('terminal_growth must be below required_return')
            g = (1 + growth) / (1 + dilution) - 1
            terminal_g = (1 + terminal) / (1 + dilution) - 1
            for year in range(1, years + 1):
                cf = cash * (1 + g) ** year
                rows.append({'year': year, 'cash_per_share': cf, 'present_value': cf / (1+r)**year})
            terminal_pv = rows[-1]['cash_per_share'] * (1+terminal_g) / (r-terminal_g) / (1+r)**years
            value = sum(row['present_value'] for row in rows) + terminal_pv
            if terminal_pv/value > .7:
                warnings.append('More than 70% of scenario value comes after the explicit forecast horizon.')
            warnings.append('Equity cash is after interest, reinvestment and financing needs; do not subtract debt again. No automatic excess-cash addition.')
            warnings.append('Dilution reduces cash per share; do not charge the same stock compensation both in base cash and share growth.')
        else:
            book = number(data, 'book_per_share', .000001, 1e9)
            roe = number(data, 'roe', -.5, 1)
            payout = number(data, 'payout', 0, 1)
            value = book
            for year in range(1, years + 1):
                residual = (roe-r)*book
                pv = residual/(1+r)**year
                rows.append({'year':year, 'opening_book_per_share':book, 'residual_income':residual,'present_value':pv})
                value += pv
                book *= 1+roe*(1-payout)
            warnings.append('ROE falls to the required return after the horizon: terminal excess income is zero. Clean-surplus accounting, common-equity scope and regulatory capital need review.')
    result = {'method':method, 'status':'ILLUSTRATIVE_SCENARIO', 'value_per_share':value,
              'price':price, 'price_vs_value':None if value <= 0 else 1-price/value,
              'terminal_present_value':terminal_pv, 'projection':rows, 'warnings':warnings,
              'input_sha256':digest(data), 'assumptions':data,
              'interpretation':'Conditional arithmetic, not fair-value certification, a recommendation or a statistical confidence interval.'}
    if method == 'equity_dcf':
        lo, hi = -.9, 1.0
        def at(growth):
            return calculate(dict(data,growth=growth),sensitivity=False)['value_per_share']
        # Avoid recursively solving the reverse problem inside scalar calculations.
        if sensitivity:
            lower, upper = at(lo), at(hi)
            implied = None
            if lower <= price <= upper:
                for _ in range(70):
                    mid = (lo+hi)/2
                    if at(mid) < price: lo = mid
                    else: hi = mid
                implied = (lo+hi)/2
            result['price_required_growth'] = implied
            result['reverse_scope'] = 'One growth solution with every other assumption held fixed; not a market forecast. Null means outside -90% to +100% bounds.'
    if sensitivity:
        result['sensitivity'] = []
        for rr in (r-.02, r-.01, r, r+.01, r+.02):
            if not .005 <= rr <= .8: continue
            if method == 'equity_dcf' and rr <= data['terminal_growth']: continue
            result['sensitivity'].append({'required_return':rr,'value_per_share':calculate(dict(data,required_return=rr),False)['value_per_share']})
    return result


def pit_check(payload):
    """Use the real optional AhaSignals PIT library; missing checker is never PASS."""
    try:
        from ahasignals_pit import audit_batch
    except ImportError:
        return {'gate':'UNKNOWN','tool':'ahasignals-pit','reason':'Optional ahasignals-pit package is not installed in this interpreter.',
                'guide':'https://ahasignals.com/guides/financial-research-workflow/'}
    return audit_batch(payload)


def review_forecasts(bundle):
    """Score explicitly frozen financial forecasts, not returns or stock selections."""
    from .research import timestamp
    if not isinstance(bundle, dict) or not isinstance(bundle.get('rows'),list) or not 1<=len(bundle['rows'])<=200:
        raise ResearchError('Supply 1–200 frozen forecast observations')
    try:
        digest(bundle)
    except (ValueError, TypeError, OverflowError):
        raise ResearchError('Forecast input must contain finite JSON values') from None
    result=[]
    for row in bundle['rows']:
        if not isinstance(row, dict):
            raise ResearchError('Each forecast observation must be an object')
        for name in ('metric','unit','source'):
            if not isinstance(row.get(name),str) or not row[name].strip(): raise ResearchError('Forecast review requires '+name)
        forecast=number(row,'forecast'); actual=number(row,'actual')
        if not timestamp(row.get('frozen_at')) < timestamp(row.get('period_end')) < timestamp(row.get('actual_available_at')):
            raise ResearchError('Forecast must be frozen before the outcome period ends; actual availability must follow it')
        error=actual-forecast
        percentage = None if actual==0 else abs(error/actual)
        if not math.isfinite(error) or (percentage is not None and not math.isfinite(percentage)):
            raise ResearchError('Forecast error exceeds the supported numeric range')
        result.append(dict(row, error=error, absolute_error=abs(error), absolute_percentage_error=percentage))
    return {'status':'DECLARED_FORECAST_REVIEW','rows':result,'input_sha256':digest(bundle),
            'limitations':['Dates are caller declarations, not independently attested freezes.', 'No pooled error across unlike metrics/units. No price returns, alpha, survivor-bias or model-memory validation.']}
