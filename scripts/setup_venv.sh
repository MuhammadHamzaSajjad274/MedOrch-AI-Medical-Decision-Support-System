#!/bin/bash
# Setup venv and install all backend dependencies.
# Run from project root: ./scripts/setup_venv.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/.venv"
REQUIREMENTS="$PROJECT_ROOT/backend/requirements.txt"

echo "Project root: $PROJECT_ROOT"

# Create venv if missing
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating venv at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
else
    echo "Venv already exists at $VENV_PATH"
fi

PYTHON="$VENV_PATH/bin/python"
PIP="$VENV_PATH/bin/pip"

# Upgrade pip
echo "Upgrading pip..."
"$PYTHON" -m pip install --upgrade pip

# Install requirements
echo "Installing backend requirements..."
"$PIP" install -r "$REQUIREMENTS"

# Verify env
echo "Running verify_env.py..."
export PYTHONPATH="$PROJECT_ROOT/backend"
"$PYTHON" "$PROJECT_ROOT/scripts/verify_env.py"

echo "Setup complete. Activate with: source .venv/bin/activate"
