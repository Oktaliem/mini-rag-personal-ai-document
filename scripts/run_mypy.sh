#!/bin/bash

# Mini RAG - Mypy Type Check Script
# Consistent runner similar to unit/api/e2e scripts

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

TARGET_PATH="src"
STRICT=false
INSTALL_TYPES=false
SKIP_DEPS=false

print() { echo -e "$1"; }
info() { print "${BLUE}[INFO]${NC} $1"; }
ok() { print "${GREEN}[SUCCESS]${NC} $1"; }
warn() { print "${YELLOW}[WARNING]${NC} $1"; }
err() { print "${RED}[ERROR]${NC} $1"; }
header() { print "${PURPLE}================================${NC}\n${PURPLE}$1${NC}\n${PURPLE}================================${NC}"; }

usage() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -p, --path PATH        Target path/package to check (default: src)"
  echo "  -s, --strict           Run with --strict"
  echo "  -i, --install-types    Run 'mypy --install-types --non-interactive' before checking"
  echo "      --skip-deps        Skip dependency checks"
  echo "  -h, --help             Show this help"
}

command_exists() { command -v "$1" >/dev/null 2>&1; }

ensure_python() {
  if command_exists python3; then PY=python3; elif command_exists python; then PY=python; else err "Python not found"; exit 1; fi
  ok "Python: $($PY --version 2>&1)"
}

ensure_deps() {
  if [ "$SKIP_DEPS" = true ]; then
    warn "Skipping dependency checks (--skip-deps)"
    return
  fi
  info "Checking mypy availability..."
  if ! $PY -m mypy --version >/dev/null 2>&1; then
    if [ -f requirements.txt ]; then
      info "Installing mypy from requirements.txt..."
      pip3 install -r requirements.txt >/dev/null 2>&1 || pip install -r requirements.txt >/dev/null 2>&1
    fi
  fi
  if ! $PY -m mypy --version >/dev/null 2>&1; then
    info "Installing mypy directly..."
    pip3 install mypy >/dev/null 2>&1 || pip install mypy >/dev/null 2>&1 || true
  fi
  $PY -m mypy --version >/dev/null 2>&1 && ok "mypy available: $($PY -m mypy --version)" || { err "mypy not available"; exit 1; }
}

run_install_types() {
  if [ "$INSTALL_TYPES" = true ]; then
    info "Installing missing type stubs..."
    set +e
    $PY -m mypy --install-types --non-interactive "$TARGET_PATH" || true
    set -e
  fi
}

run_mypy() {
  header "Mypy Type Checking"
  CMD="$PY -m mypy $TARGET_PATH"
  if [ "$STRICT" = true ]; then CMD="$CMD --strict"; fi
  info "Executing: $CMD"
  set +e
  OUTPUT=$($CMD 2>&1)
  EXIT=$?
  set -e
  echo "$OUTPUT"
  echo ""
  if [ $EXIT -eq 0 ]; then
    ok "Type check passed"
  else
    err "Type check failed ($EXIT)"
  fi
  return $EXIT
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--path) TARGET_PATH="$2"; shift 2;;
    -s|--strict) STRICT=true; shift;;
    -i|--install-types) INSTALL_TYPES=true; shift;;
    --skip-deps) SKIP_DEPS=true; shift;;
    -h|--help) usage; exit 0;;
    *) err "Unknown option: $1"; usage; exit 1;;
  esac
done

ensure_python
ensure_deps
run_install_types
run_mypy
exit $?


