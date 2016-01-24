#!/usr/bin/env python3
"""
This scripts finds the correct YUI compressor binary if --find is given.
Otherwise it behaves like YUI compressor itself, except for compressing.
"""
import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description='Annotate text with comment id attributes.')
    parser.add_argument('filename', nargs='?', help='The file to compress')
    parser.add_argument('--find', action='store_const', const=True, default=False,
                        help='Find YUI compressor binary')
    parser.add_argument('--type', help='Will be ignored')
    parser.add_argument('--charset', help='Will be ignored')
    parser.add_argument('-o', default='-', help='The outfile')

    args = parser.parse_args()

    if args.find:
        binary = find_binary('yui_compressor')
        if not binary:
            binary = find_binary('yuicompressor')
        if not binary:
            binary = find_binary('yui-compressor')
        if not binary:
            binary = __file__
        print(binary)
    else:
        if args.filename:
            with open(args.filename) as f:
                contents = f.read()
        else:
            contents = sys.stdin.read()

        if args.o == '-':
            print(contents, end='')
        else:
            with open(args.o, 'w') as f:
                f.write(contents)


def find_binary(name):
    try:
        return subprocess.check_output(['/usr/bin/which', name]).decode().strip()
    except subprocess.CalledProcessError:
        return ''


if __name__ == '__main__':
    main()