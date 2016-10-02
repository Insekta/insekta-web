import re

import bleach


PARAGRAPH_SPLIT_RE = re.compile(r'\n([\t ]*\n)+')
DEFAULT_TAG_WHITELIST = ['a', 'p', 'br', 'em', 'strong', 'code', 'pre', 'blockquote']
DEFAULT_ATTR_WHITELIST = {'a': ['href']}


def describe_allowed_markup(tag_whitelist=None, attr_whitelist=None):
    if tag_whitelist is None:
        tag_whitelist = DEFAULT_TAG_WHITELIST
    if attr_whitelist is None:
        attr_whitelist = DEFAULT_ATTR_WHITELIST
    tag_desc = []
    for tag in tag_whitelist:
        if tag in attr_whitelist:
            tag_desc.append('{}[{}]'.format(tag, ', '.join(attr_whitelist[tag])))
        else:
            tag_desc.append(tag)

    return ', '.join(tag_desc)


def sanitize_markup(markup, tag_whitelist=None, attr_whitelist=None):
    if tag_whitelist is None:
        tag_whitelist = DEFAULT_TAG_WHITELIST
    if attr_whitelist is None:
        attr_whitelist = DEFAULT_ATTR_WHITELIST

    markup = markup.replace('\r\n', '\n').strip()

    # Only assume paragraphs line breaks should be handled if the user
    # did not show he wants to do paragraph/line break markup himself
    if not ('<p ' in markup or '<p>' in markup):
        markup_paragraphs = PARAGRAPH_SPLIT_RE.split(markup)
        markup = ''.join('<p>{}</p>'.format(p) for p in markup_paragraphs)
        if not '<br' in markup:
            markup = '<br>'.join(markup.split('\n'))

    return bleach.clean(bleach.linkify(markup),
                             tags=tag_whitelist,
                             attributes=attr_whitelist)
