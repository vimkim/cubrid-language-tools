"""Dependency-free bootstrap for the optional stdio language server."""

import sys


def main():
    if len(sys.argv) != 1:
        print('cubrid-language-server uses stdio and accepts no arguments.', file=sys.stderr)
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
