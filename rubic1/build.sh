#!/usr/bin/env bash
# build.sh — Build the Trivia application into a standalone executable.
#
# What this script does:
#   1. Compiles the React frontend into a production build (frontend/build/)
#   2. Installs Python runtime dependencies
#   3. Installs PyInstaller (build-time only)
#   4. Packages everything into a single self-contained executable via PyInstaller
#
# Output: dist/trivia  (or dist/trivia.exe on Windows)
#
# Prerequisites:
#   - Node.js + npm  (https://nodejs.org)
#   - Python 3.8+    (https://python.org)
#   - pip
#   - PostgreSQL running somewhere accessible at runtime (NOT required to build)
#
# Usage:
#   chmod +x build.sh
#   ./build.sh
#
# After building, run the app:
#   First-time install (creates the database and seeds data):
#     ./dist/trivia --setup-db --db-password YOUR_PASSWORD
#
#   Subsequent runs (database already exists):
#     ./dist/trivia --db-password YOUR_PASSWORD

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; RESET='\033[0m'
info()    { echo -e "${GREEN}[build]${RESET} $*"; }
warning() { echo -e "${YELLOW}[warn] ${RESET} $*"; }
error()   { echo -e "${RED}[error]${RESET} $*"; exit 1; }

echo ""
echo "=================================================="
echo "  Trivia App — Build Script"
echo "=================================================="

# ---------------------------------------------------------------------------
# Step 1: Build React frontend
# ---------------------------------------------------------------------------
info "Step 1/3 — Building React frontend..."

if ! command -v node &>/dev/null; then
    error "Node.js not found. Install it from https://nodejs.org and re-run."
fi
if ! command -v npm &>/dev/null; then
    error "npm not found. Install Node.js from https://nodejs.org and re-run."
fi

cd frontend
npm install --silent
npm run build
cd "$SCRIPT_DIR"

info "Frontend built → frontend/build/"

# ---------------------------------------------------------------------------
# Step 2: Install Python runtime dependencies
# ---------------------------------------------------------------------------
info "Step 2/3 — Installing Python dependencies..."

if ! command -v pip &>/dev/null && ! command -v pip3 &>/dev/null; then
    error "pip not found. Install Python 3 and pip, then re-run."
fi

PIP_CMD="pip"
command -v pip3 &>/dev/null && PIP_CMD="pip3"

$PIP_CMD install --quiet -r backend/requirements.txt
info "Runtime dependencies installed."

# ---------------------------------------------------------------------------
# Step 3: Package with PyInstaller
# ---------------------------------------------------------------------------
info "Step 3/3 — Packaging with PyInstaller..."

$PIP_CMD install --quiet pyinstaller

pyinstaller --clean trivia.spec

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
EXEC_PATH="dist/trivia"
[[ "$(uname -s)" == MINGW* || "$(uname -s)" == CYGWIN* ]] && EXEC_PATH="dist/trivia.exe"

echo ""
echo "=================================================="
echo -e "  ${GREEN}Build complete!${RESET}"
echo ""
echo "  Executable : $EXEC_PATH"
echo ""
echo "  First-time setup (creates DB + seeds data + starts server):"
echo "    ./$EXEC_PATH --setup-db --db-password YOUR_PASSWORD"
echo ""
echo "  Subsequent runs (DB already exists):"
echo "    ./$EXEC_PATH --db-password YOUR_PASSWORD"
echo ""
echo "  All options:"
echo "    ./$EXEC_PATH --help"
echo "=================================================="
echo ""
