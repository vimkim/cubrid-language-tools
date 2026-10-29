"""Dependency-free bootstrap for the optional stdio language server."""

import sys


def main():
    arguments = tuple(sys.argv[1:])
    if arguments in (('--help',), ('-h',)):
        print('Usage: cubrid-language-server [--version | --help | -h]\n'
              'With no arguments, start the stdio language server.\n'
              '  --version  Show the installed package version.\n'
              '  --help, -h  Show this help.')
        return 0
    if arguments == ('--version',):
        from importlib.metadata import PackageNotFoundError, version
        try:
            installed_version = version('cubrid-language-tools')
        except PackageNotFoundError:
            print('cubrid-language-tools distribution metadata is unavailable. '
                  'Install the package to query its version.', file=sys.stderr)
            return 3
        print(f'cubrid-language-server {installed_version}')
        return 0
    if arguments:
        print('Invalid arguments. Use --help for usage.', file=sys.stderr)
        return 3
    try:
        from .lsp_server import create_server
    except ImportError:
        print('Install the optional server dependencies: pip install "cubrid-language-tools[lsp]"',
              file=sys.stderr)
        return 3
    server = create_server()
    server.start_io()
    return server.exit_status


if __name__ == '__main__':
    raise SystemExit(main())
