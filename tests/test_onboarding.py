import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import install
import doctor


class OnboardingTests(unittest.TestCase):
    def test_host_scope_resolves_under_requested_base(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            self.assertEqual(install.destination('codex', 'user', base/'project', base/'account'), base/'account/.agents/skills/value-investor-skill')
            self.assertEqual(install.destination('claude', 'project', base/'project', base/'account'), base/'project/.claude/skills/value-investor-skill')

    def test_project_install_runs_from_another_directory_and_preserves_existing(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t);project = base/'project with spaces'
            command = [sys.executable, str(ROOT/'scripts/install.py'), '--host', 'claude', '--scope', 'project', '--project', str(project)]
            result = subprocess.run(command, cwd=base, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            folder = project/'.claude/skills/value-investor-skill'
            private = folder/'keep.txt';private.write_text('keep existing work')
            self.assertEqual(subprocess.run(command, cwd=base, capture_output=True).returncode, 2)
            self.assertEqual(private.read_text(), 'keep existing work')
            run = subprocess.run([sys.executable, str(folder/'scripts/investor.py'), 'demo', '--out', str(base/'demo')], cwd=base, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)

    def test_new_host_installs_execute_from_outside_the_project(self):
        for host, directory in [('gemini', '.gemini'), ('kimi', '.agents')]:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as t:
                base = Path(t); project = base/'project with spaces'
                cmd = [sys.executable, str(ROOT/'scripts/install.py'), '--host', host,
                       '--scope', 'project', '--project', str(project)]
                result = subprocess.run(cmd, cwd=base, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                folder = project/directory/'skills/value-investor-skill'
                run = subprocess.run([sys.executable, str(folder/'scripts/investor.py'),
                                      'demo', '--out', str(base/'demo')], cwd=base, capture_output=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(subprocess.run(cmd, cwd=base, capture_output=True).returncode, 2)

    def test_gemini_shared_alias_is_preserved_without_shadow_copy(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t); shared = base/'.agents/skills/value-investor-skill'
            shared.mkdir(parents=True); marker = shared/'keep.txt'; marker.write_text('existing')
            self.assertEqual(install.main(['--host', 'gemini', '--scope', 'project', '--project', str(base)]), 2)
            self.assertEqual(marker.read_text(), 'existing')
            self.assertFalse((base/'.gemini').exists())

    def test_kimi_does_not_duplicate_shared_codex_installation(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            self.assertEqual(install.main(['--host', 'codex', '--scope', 'project', '--project', str(base)]), 0)
            folder = base/'.agents/skills/value-investor-skill'
            marker = folder/'keep.txt'; marker.write_text('saved work')
            self.assertEqual(install.main(['--host', 'kimi', '--scope', 'project', '--project', str(base)]), 2)
            self.assertEqual(marker.read_text(), 'saved work')

    def test_legacy_codex_copy_is_not_duplicated_or_deleted(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t);legacy = base/'.codex/skills/value-investor-skill';legacy.mkdir(parents=True)
            marker = legacy/'keep.txt';marker.write_text('old installation')
            with patch.object(install.Path, 'home', return_value=base):
                self.assertEqual(install.main(['--host', 'codex']), 2)
            self.assertEqual(marker.read_text(), 'old installation')
            self.assertFalse((base/'.agents').exists())

    def test_missing_source_does_not_create_a_partial_installation(self):
        with tempfile.TemporaryDirectory() as t:
            dest = Path(t)/'copy'
            with self.assertRaises(ValueError):
                install.install(dest, Path(t)/'missing')
            self.assertFalse(dest.exists())

    @unittest.skipIf(os.name == 'nt', 'Windows symlink creation may require administrator privileges')
    def test_dangling_destination_symlink_is_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            dest = Path(t)/'copy';dest.symlink_to(Path(t)/'missing')
            with self.assertRaises(ValueError):
                install.install(dest)
            self.assertTrue(dest.is_symlink())

    def test_noninteractive_chooser_does_not_write(self):
        with tempfile.TemporaryDirectory() as t:
            result = subprocess.run([sys.executable, str(ROOT/'scripts/install.py')], cwd=t, input='', capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn('No files changed', result.stdout)
            self.assertEqual(list(Path(t).iterdir()), [])

    def test_doctor_detects_incomplete_package(self):
        self.assertTrue(doctor.check()['ready'])
        with tempfile.TemporaryDirectory() as t:
            result = doctor.check(Path(t))
            self.assertFalse(result['ready'])
            self.assertFalse(result['checks']['complete_package'])

    def test_upload_zip_is_self_contained_without_installer_or_git_metadata(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            result = subprocess.run([sys.executable, str(ROOT/'scripts/package_release.py'), '--out', str(base/'dist')], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            archive = next((base/'dist').glob('*-upload-*.zip'))
            with zipfile.ZipFile(archive) as z:
                self.assertTrue(all(n.startswith('value-investor-skill/') for n in z.namelist()))
                self.assertNotIn('value-investor-skill/scripts/install.py', z.namelist())
                self.assertFalse(any('/.git' in n for n in z.namelist()))
                z.extractall(base/'extracted')
            folder = base/'extracted/value-investor-skill'
            check = subprocess.run([sys.executable, str(folder/'scripts/doctor.py'), '--json'], cwd=base, capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertTrue(json.loads(check.stdout)['ready'])
            run = subprocess.run([sys.executable, str(folder/'scripts/investor.py'), 'demo', '--out', str(base/'demo')], cwd=base, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
