#!/bin/zsh
set -e
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python || ! -f frontend/dist/index.html ]]; then
  print 'Complete the setup steps in README.md first, then reopen this launcher.'
  read '?Press Return to close.'
  exit 1
fi
print 'Starting HandoffReady with the installed local model.'
print 'Open http://127.0.0.1:8877/ after the ready message.'
print 'Keep this window open. Press Ctrl+C to stop the app.'
.venv/bin/python scripts/start.py --with-model
