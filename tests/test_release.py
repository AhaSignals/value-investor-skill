import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check_public_identity import findings, inspect
sys.path.insert(0, str(ROOT))
from core import __version__


class ReleaseTests(unittest.TestCase):
    def test_identity_patterns_and_neutral_attribution(self):
        self.assertTrue(findings(('/' + 'Users/' + 'private-operator/project').encode()))
        self.assertTrue(findings(('C:' + '\\Users\\' + 'private-operator\\project').encode()))
        self.assertTrue(findings(('private-person' + '@' + 'example.org').encode()))
        self.assertFalse(findings(b'Copyright 2026 AhaSignals'))

    def test_reproducible_archive_and_clean_extraction(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            out = parent / 'packages'
            cmd = [sys.executable, str(ROOT / 'scripts/package_release.py'), '--out', str(out)]
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            # Filesystem enumeration order differs across hosts. Select the source
            # archive explicitly; the upload archive intentionally omits README files.
            archive = out / ('value-investor-skill-v' + __version__ + '.zip')
            initial = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), initial)
            self.assertEqual(inspect(archive=archive), [])
            with zipfile.ZipFile(archive) as package:
                self.assertFalse(any('.git/' in n or '__pycache__' in n or n.endswith('.sqlite') for n in package.namelist()))
                self.assertTrue(all('value-investor-skill/README.' + locale + '.md' in package.namelist() for locale in ('ja','ko','de','fr','es')))
                self.assertTrue(all(i.date_time == (1980, 1, 1, 0, 0, 0) for i in package.infolist()))
                package.extractall(parent / 'extracted')
            script = parent / 'extracted/value-investor-skill/scripts/investor.py'
            run = subprocess.run([sys.executable, str(script), 'demo', '--out', str(parent / 'demo')], cwd=parent, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)


if __name__ == '__main__':
    unittest.main()
