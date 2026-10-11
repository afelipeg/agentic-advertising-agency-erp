"""Release packaging: app-uploadable skill zips and assistant files."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_release import build, INSTRUCTION_LIMIT, DESCRIPTION_LIMIT


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.temp.name)
        build(cls.out)
        cls.skills = sorted(p.name for p in (ROOT / 'skills').iterdir() if p.is_dir())

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_one_zip_per_skill_with_folder_at_top_level(self):
        for name in self.skills:
            with zipfile.ZipFile(self.out / f'{name}.zip') as archive:
                names = archive.namelist()
            self.assertIn(f'{name}/SKILL.md', names)
            self.assertTrue(all(n.startswith(f'{name}/') for n in names))
            self.assertFalse(any(n.endswith('.pyc') or '__pycache__' in n or '.DS_Store' in n for n in names))
            self.assertIn(f'{name}/scripts/agency_tools.py', names)

    def test_descriptions_fit_app_limits(self):
        for name in self.skills:
            text = (ROOT / 'skills' / name / 'SKILL.md').read_text()
            description = json.loads(text.split('\n')[2][len('description: '):])
            self.assertLessEqual(len(description), DESCRIPTION_LIMIT)
            self.assertLessEqual(len(name), 64)

    def test_assistant_files(self):
        instructions = (self.out / 'assistant-instructions.txt').read_text()
        self.assertLessEqual(len(instructions), INSTRUCTION_LIMIT)
        self.assertIn('A human approves', instructions)
        knowledge = (self.out / 'agency-erp-knowledge.md').read_text()
        for name in self.skills:
            self.assertIn(f'# SKILL: {name}', knowledge)
        self.assertIn('## tiered_commission', knowledge)
        self.assertEqual((self.out / 'agency_tools.py').read_bytes(), (ROOT / 'tools/agency_tools.py').read_bytes())

    def test_all_skills_bundle_and_checksums(self):
        with zipfile.ZipFile(self.out / 'agency-erp-all-skills.zip') as archive:
            self.assertEqual(len(archive.namelist()), len(self.skills))
        sums = dict(reversed(line.split('  ')) for line in (self.out / 'SHA256SUMS.txt').read_text().splitlines())
        for name, digest in sums.items():
            self.assertEqual(hashlib.sha256((self.out / name).read_bytes()).hexdigest(), digest)

    def test_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as other:
            build(Path(other))
            self.assertEqual((Path(other) / 'SHA256SUMS.txt').read_text(), (self.out / 'SHA256SUMS.txt').read_text())


if __name__ == '__main__':
    unittest.main()
