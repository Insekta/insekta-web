from django.test import TestCase
from insekta.base.utils import sanitize_markup

class TestMarkup(TestCase):
    def test_sanitize_markup(self):
        markup = 'foo\n\nbar<script>alert(document.cookie);</script>\n\n\nquxbaz'
        sanitized_markup = sanitize_markup(markup, tag_whitelist=['p', 'br'])
        expected_markup = '<p>foo</p><p>bar&lt;script&gt;alert(document.cookie);&lt;/script&gt;<br>quxbaz'
        print(repr(sanitized_markup))
        print(repr(expected_markup))
        self.assertEqual(sanitized_markup, expected_markup)
        print(sanitized_markup)
        return False
