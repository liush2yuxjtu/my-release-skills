"""Distribution checks: linked workflows must ship their actual dependencies."""
import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


PACKAGE = Path(__file__).resolve().parents[1]


class SkillPackageChecks(unittest.TestCase):
    def test_bundled_markdown_links_resolve(self):
        missing = []
        for document in PACKAGE.rglob('*.md'):
            for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)', document.read_text()):
                address = urlsplit(target.strip('<>'))
                if address.scheme or not address.path:
                    continue
                linked = document.parent / unquote(address.path)
                if not linked.exists():
                    missing.append(f'{document.relative_to(PACKAGE)} -> {target}')
        self.assertEqual(missing, [], '\n'.join(missing))

    def test_distributed_json_templates_are_readable(self):
        templates = list((PACKAGE / 'assets').glob('*.json'))
        self.assertTrue(templates)
        for template in templates:
            with self.subTest(template=template.name):
                self.assertIsInstance(json.loads(template.read_text()), dict)


if __name__ == '__main__':
    unittest.main()
