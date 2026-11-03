#!/usr/bin/env python3
"""Check the local package and Python runtime without network calls or credentials."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT):
    required = ('SKILL.md', 'core/research.py', 'core/ledger.py', 'scripts/investor.py',
                'references/input-contract.md', 'references/research-protocol.md',
                'examples/clinical.json', 'examples/merger.json', 'prompts/START_HERE.md')
    checks = {'python_3_9_or_newer': sys.version_info >= (3, 9),
              'complete_package': all((root / p).is_file() for p in required)}
    try:
        with sqlite3.connect(':memory:') as connection:
            checks['sqlite_available'] = connection.execute('select 1').fetchone() == (1,)
    except sqlite3.Error:
        checks['sqlite_available'] = False
    return {'ready': all(checks.values()), 'checks': checks,
            'scope': 'Local files and runtime only; no model, browsing or account access tested.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    result = check()
    if args.json:
        print(json.dumps(result))
    else:
        for name, okay in result['checks'].items():
            print(('OK   ' if okay else 'FAIL ') + name.replace('_', ' '))
        print(result['scope'])
        print('Next: ask your assistant to show the fictional $40 demo.' if result['ready'] else 'Next: use Python 3.9+ and extract the complete release package.')
    return 0 if result['ready'] else 2


if __name__ == '__main__':
    sys.exit(main())
