import copy
import tempfile
import unittest
from pathlib import Path
from html.parser import HTMLParser
from unittest.mock import Mock
from src.report_generator.generator import ReportGenerator

class Nodes(HTMLParser):
    def __init__(self):
        super().__init__(); self.nodes = []; self.text = []
    def handle_starttag(self, tag, attrs): self.nodes.append((tag, dict(attrs)))
    def handle_data(self, text): self.text.append(text)

class ReportSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.storage = Mock()
        self.storage.get_document.return_value = {'id': 'doc', 'title': '<img id="bad-title" src="x">', 'filename': '<img id="bad-file" src="x">', 'content': 'ordinary document text'}
        self.generator = ReportGenerator(self.temp.name, self.storage)
    def tearDown(self): self.temp.cleanup()
    def render(self, match):
        results = {'id': 'search', 'matchCount': 1, 'matches': [{'documentId': 'doc', 'pattern': '<img id="bad-pattern" src="x">', 'score': 1.0, **match}]}
        result = self.generator.generate_report(results, 'html')
        html = Path(result['path']).read_text(); nodes = Nodes(); nodes.feed(html)
        return html, nodes
    def assert_no_injected_nodes(self, nodes):
        self.assertFalse(any(attrs.get('id', '').startswith('bad-') or 'onerror' in attrs for _, attrs in nodes.nodes))
    def test_plain_slices_are_data_and_static_mark_remains(self):
        html, nodes = self.render({'text': '<img id="bad-match" src="x" onerror="marker">', 'context_before': '<img id="bad-before" src="x">', 'context_after': '<img id="bad-after" src="x">'})
        self.assert_no_injected_nodes(nodes); self.assertTrue(any(tag == 'mark' for tag, _ in nodes.nodes))
        self.assertIn('&lt;img', html); self.assertIn('ordinary document text', html)
    def test_legacy_rich_formatting_is_preserved_without_attributes(self):
        html, nodes = self.render({'matchedText': 'test <strong>keyword</strong><img id="bad-legacy" src="x">', 'context': '<span class="highlight" onclick="marker">context</span><script id="bad-script">marker</script>'})
        self.assert_no_injected_nodes(nodes); self.assertTrue(any(tag == 'strong' for tag, _ in nodes.nodes))
        self.assertTrue(any(tag == 'span' and attrs.get('class') == 'highlight' for tag, attrs in nodes.nodes))
        self.assertFalse(any('onclick' in attrs and attrs['onclick'] == 'marker' for _, attrs in nodes.nodes))
    def test_unbalanced_legacy_tags_cannot_close_outer_report(self):
        html, nodes = self.render({'matchedText': '</div><strong>keyword', 'context': '<svg><foreignObject><img id="bad-svg" src="x"></foreignObject></svg>'})
        self.assert_no_injected_nodes(nodes); self.assertIn('<strong>keyword</strong>', html)
        self.assertFalse(any(tag in ['svg', 'foreignobject'] for tag, _ in nodes.nodes))
    def test_json_report_keeps_original_data(self):
        results = {'id': 'search', 'matchCount': 1, 'matches': [{'documentId': 'doc', 'matchedText': '<strong>keyword</strong><img id="bad-json">'}]}
        original = copy.deepcopy(results['matches']); metadata = self.generator.generate_report(results, 'json')
        import json
        data = json.loads(Path(metadata['path']).read_text()); self.assertEqual(data['results']['matches'], original)
    def test_malformed_legacy_markup_fails_closed_to_text(self):
        with self.assertLogs('src.report_generator.formatting', level='WARNING') as logs:
            html, nodes = self.render({'matchedText': '<![bogus]><img id="bad-malformed" src="x">'})
        self.assert_no_injected_nodes(nodes)
        self.assertIn('&lt;![bogus]&gt;', html)
        self.assertTrue(any('rendering as text' in message for message in logs.output))
    def test_fallback_template_uses_same_safe_filter(self):
        root = Path(self.temp.name) / 'templates'; root.mkdir()
        from jinja2 import FileSystemLoader
        self.generator.jinja_env.loader = FileSystemLoader(str(root))
        # Actual fallback creation uses __file__ templates; create its own missing-template target under a mocked module directory.
        import src.report_generator.generator as module
        from unittest.mock import patch
        with patch.object(module, '__file__', str(Path(self.temp.name) / 'generator.py')):
            html, nodes = self.render({'matchedText': '<strong>keyword</strong><img id="bad-default" src="x">', 'context': '<script id="bad-default-script">marker</script>'})
        self.assert_no_injected_nodes(nodes); self.assertTrue(any(tag == 'strong' for tag, _ in nodes.nodes))

if __name__ == '__main__': unittest.main()
