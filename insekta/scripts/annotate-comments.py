#!/usr/bin/env python3
import argparse
import base64
import os
import sys


def add_comment_ids(html, tag='pc', new_tag='p', attr_name='data-comment-id'):
    parts = html.split('</{}>'.format(tag))
    new_parts = []
    lineno = 1
    tag_start = '<{}'.format(tag)
    for part in parts[:-1]:
        lineno += part.count('\n')
        pos = part.rfind(tag_start)
        if pos == -1:
            raise ValueError(
                    'Missing beginning tag for closing tag on line {}'.format(lineno))
        pos2 = part.rfind(tag_start, 0, pos)
        if pos2 != -1:
            open_lineno = lineno - part[pos2:].count('\n')
            open_lineno2 = lineno - part[pos:].count('\n')
            error_msg = ('Duplicate open tag, lines {} and {}. '
                         'Closing p tag was on line {}.')
            raise ValueError(error_msg.format(open_lineno, open_lineno2, lineno))
        # attr_starts excludes the space after the tag
        attrs_start = pos + len(tag) + 2
        if part[attrs_start:attrs_start + len(attr_name)] == attr_name:
            new_part = '{}<{} {}'.format(part[:pos], new_tag, part[attrs_start:])
        else:
            # 5 random bytes equal 40 bits, by birthday paradox we expect
            # a collision after about 20 bits, which are far more paragraphs
            # than you will ever have per scenario (approx. 1 million).
            # Additionally 40 bits fit perfectly in 8 base32 characters.
            random_bytes = os.urandom(5)
            comment_id = base64.b32encode(random_bytes).decode().lower()
            new_part = '{}<{} {}="{}"{}'.format(
                    part[:pos], new_tag, attr_name, comment_id, part[attrs_start - 1:])
        new_parts.append(new_part)
    new_parts.append(parts[-1])
    new_content = '</{}>'.format(new_tag).join(new_parts)
    return new_content


def main():
    parser = argparse.ArgumentParser(description='Annotate text with comment id attributes.')
    parser.add_argument('filename', help='The file to annotate')
    parser.add_argument('--nobak', action='store_const', const=True, default=False,
                        help='Do not create backup file')
    parser.add_argument('--tag', default='pc', help='The tag to search for')
    parser.add_argument('--newtag', default='p', help='The tag after replacement')
    parser.add_argument('--attrname', default='data-comment-id', help='The attribute name')


    args = parser.parse_args()

    try:
        with open(args.filename) as f:
            contents = f.read()
    except IOError as e:
        print('Could not open input file', file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(1)

    try:
        new_contents = add_comment_ids(contents, args.tag, args.newtag, args.attrname)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    if not args.nobak:
        try:
            with open(args.filename + '.bak', 'w') as f:
                f.write(contents)
        except IOError as e:
            print('Could not write backup file, exiting without modifications.',
                  file=sys.stderr)
            print(str(e), file=sys.stderr)
            sys.exit(1)

    try:
        with open(args.filename, 'w') as f:
            f.write(new_contents)
    except IOError as e:
        print('Could not write output file', file=sys.stderr)
        print(str(e), file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
