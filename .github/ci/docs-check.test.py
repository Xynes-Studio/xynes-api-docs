"""Executable negative fixtures; no MDX execution, network, install or provider."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('docs-check.py')
spec = importlib.util.spec_from_file_location('docs_check', SCRIPT)
docs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs)


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)
        (self.root / 'guide.md').write_text('# Guide\n')
        (self.root / 'api.mdx').write_text('# API\n[Guide](guide.md#guide)\n[External](https://example.invalid/api)\n[Mail](mailto:fixture@example.invalid)\n[Here](#api)\n')

    def test_manifest_is_deterministic_and_matches_source_bytes(self):
        record = docs.validate(self.root, ['guide.md', 'api.mdx', 'ignored.txt'])
        self.assertEqual(record, docs.validate(self.root, ['api.mdx', 'guide.md']))
        self.assertEqual(record['kind'], 'inert-documentation-source')
        self.assertEqual(record['documents'][0]['sha256'], hashlib.sha256((self.root / 'api.mdx').read_bytes()).hexdigest())
        self.assertEqual(record['documents'][1]['bytes'], len(b'# Guide\n'))

    def test_invalid_paths_content_and_inventory_fail_closed(self):
        for names in [[], ['guide.md', 'guide.md'], ['/guide.md'], ['../guide.md'], ['bad\\guide.md'], ['missing.md']]:
            with self.subTest(names=names), self.assertRaises(ValueError): docs.validate(self.root, names)
        path = self.root / 'bad.md'
        for raw in [b'', b'\xff', b'# bad\0', b'x' * (docs.MAX_DOCUMENT_BYTES + 1)]:
            path.write_bytes(raw)
            with self.subTest(size=len(raw)), self.assertRaises(ValueError): docs.validate(self.root, ['bad.md'])

    def test_links_cannot_escape_or_execute_and_missing_targets_fail(self):
        path = self.root / 'bad.md'
        for target in ['javascript:alert', 'file:///tmp/fixture', '//example.invalid/file', '../outside.md', '%2e%2e/outside.md', 'missing.md', 'bad%00.md', 'bad\\guide.md']:
            path.write_text('[fixture](' + target + ')\n')
            with self.subTest(target=target), self.assertRaises(ValueError): docs.validate(self.root, ['bad.md'])

    def test_symlink_documents_parents_and_link_targets_are_rejected(self):
        (self.root / 'alias.md').symlink_to(self.root / 'guide.md')
        with self.assertRaises(ValueError): docs.validate(self.root, ['alias.md'])
        (self.root / 'directory').mkdir()
        (self.root / 'directory/nested.md').write_text('# Nested\n')
        (self.root / 'alias').symlink_to(self.root / 'directory', target_is_directory=True)
        with self.assertRaises(ValueError): docs.validate(self.root, ['alias/nested.md'])
        (self.root / 'bad.md').write_text('[Alias](alias.md)\n')
        with self.assertRaises(ValueError): docs.validate(self.root, ['bad.md'])

    def test_cli_manifest_and_failure_exit_are_real(self):
        with patch.object(Path, 'cwd', return_value=self.root), patch.object(subprocess, 'check_output', return_value=b'api.mdx\0guide.md\0'), contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(docs.main(['--manifest']), 0)
            self.assertEqual(len(json.loads(stdout.getvalue())['documents']), 2)
        with patch.object(Path, 'cwd', return_value=self.root), patch.object(subprocess, 'check_output', return_value=b'guide.md\0'), contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(docs.main([]), 0)
            self.assertIn('PASS:', stdout.getvalue())
        for error in [OSError('inert failure'), subprocess.CalledProcessError(1, ['git'])]:
            with patch.object(subprocess, 'check_output', side_effect=error), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(docs.main([]), 1)
        result = subprocess.run([sys.executable, str(SCRIPT)], cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)  # Fixture is not a Git checkout.


if __name__ == '__main__':
    if '--coverage' in sys.argv:
        with tempfile.TemporaryDirectory(prefix='xynes-docs-coverage-') as folder:
            result = subprocess.run([sys.executable, '-m', 'trace', '--count', '--missing', '--coverdir', folder, str(Path(__file__).resolve())])
            if result.returncode:
                raise SystemExit(result.returncode)
            files = list(Path(folder).glob('*docs-check.cover'))
            if len(files) != 1:
                raise SystemExit('Missing production validator trace evidence')
            lines = files[0].read_text().splitlines()
            covered = sum(bool(re.match(r'^\s*\d+:', line)) for line in lines)
            missed = sum(line.startswith('>>>>>>') for line in lines)
            total = covered + missed
            percent = 100 * covered / total if total else 0
            print(f'docs-check.py executable-line coverage: {percent:.2f}% ({covered}/{total}); no function/branch percentage claimed')
            raise SystemExit(0 if total and percent >= 80 else 1)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DocumentationTests)
    if suite.countTestCases() == 0:
        raise SystemExit('No documentation tests discovered')
    result = unittest.TextTestRunner().run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
