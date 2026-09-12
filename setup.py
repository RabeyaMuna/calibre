#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai


__license__ = 'GPL v3'
__copyright__ = '2009, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import os
import re
import sys

src_base = os.path.dirname(os.path.abspath(__file__))


def check_version_info():
    with open(os.path.join(src_base, 'pyproject.toml')) as f:
        raw = f.read()
    m = re.search(r'''^requires-python\s*=\s*['"](.+?)['"]''', raw, flags=re.MULTILINE)
    assert m is not None
    minver = m.group(1)
    m = re.match(r'(>=?)(\d+)\.(\d+)', minver)
    q = int(m.group(2)), int(m.group(3))
    if m.group(1) == '>=':
        is_ok = sys.version_info >= q
    else:
        is_ok = sys.version_info > q
    if not is_ok:
        exit(f'calibre requires Python {minver}. Current Python version: {".".join(map(str, sys.version_info[:3]))}')


check_version_info()

sys.path.insert(0, src_base)

import setup.commands as commands
from setup import get_warnings, prints


def option_parser():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option(
        '-c',
        '--clean',
        default=False,
        action='store_true',
        help=('Instead of running the command delete all files generated '
              'by the command'))
    parser.add_option(
        '--clean-backups',
        default=False,
        action='store_true',
        help='Delete all backup files from the source tree')
    parser.add_option(
        '--clean-all',
        default=False,
        action='store_true',
        help='Delete all machine generated files from the source tree')
    return parser


def clean_backups():
    for root, _, files in os.walk('.'):
        for name in files:
            for t in ('.pyc', '.pyo', '~', '.swp', '.swo'):
                if name.endswith(t):
                    os.remove(os.path.join(root, name))


def main(args=sys.argv):
    if len(args) == 1 or args[1] in ('-h', '--help'):
        print('Usage: python', args[0], 'command', '[options]')
        print('\nWhere command is one of:')
        print()
        for x in sorted(commands.__all__):
            print(f'{x:20} -', end=' ')
            c = getattr(commands, x)
            desc = getattr(c, 'short_description', c.description)
            print(desc)

        print('\nTo get help on a particular command, run:')
        print('\tpython', args[0], 'command -h')
        return 1

    command = args[1]
    if command not in commands.__all__:
        print(command, 'is not a recognized command.')
        print('Valid commands:', ', '.join(commands.__all__))
        return 1

    command = getattr(commands, command)

    parser = option_parser()
    command.add_all_options(parser)
    parser.set_usage(
        f'Usage: python setup.py {args[1]} [options]\n\n' + command.description)

    opts, args = parser.parse_args(args)
    opts.cli_args = args[2:]

    if opts.clean_backups:
        clean_backups()

    if opts.clean:
        prints('Cleaning', args[1])
        command.clean()
        return 0

    if opts.clean_all:
        for cmd in commands.__all__:
            prints('Cleaning', cmd)
            getattr(commands, cmd).clean()
        return 0

    # Preflight check for required Qt components (e.g. Qt::GuiPrivate)
    # Try several heuristics: pkg-config check for common Qt packages and common env vars
    import shutil, subprocess, os

    def _qt_available():
        # pkg-config names vary; try common variants
        if shutil.which('pkg-config'):
            for name in ('Qt6Gui', 'Qt5Gui', 'QtGui'):
                try:
                    subprocess.check_call(['pkg-config', '--exists', name],
                                          stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
                    return True
                except subprocess.CalledProcessError:
                    continue
                except OSError:
                    break
        # common environment variables pointing to Qt installations
        for var in ('Qt_DIR', 'QTDIR', 'QT_DIR'):
            if os.environ.get(var):
                return True
        return False

    if not _qt_available():
        print('\nError: Required Qt components (including Qt::GuiPrivate) not found.')
        print('Please install/configure Qt and ensure Qt_DIR or pkg-config paths are set.')
        print('On many systems you can install Qt dev packages or set the Qt_DIR environment variable to the Qt CMake directory.')
        return 1

    try:
        command.run_all(opts)
    except subprocess.CalledProcessError as e:
        print()
        prints('Error: external command failed with return code', getattr(e, 'returncode', '<unknown>'))
        prints('Failed command:', getattr(e, 'cmd', '<unknown>'))
        return 2
    except Exception as e:
        print()
        prints('Unexpected error while running command:', e)
        return 3

    warnings = get_warnings()
    if warnings:
        print()
        prints('There were', len(warnings), 'warning(s):')
        print()
        for args, kwargs in warnings:
            prints('*', *args, **kwargs)
            print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
