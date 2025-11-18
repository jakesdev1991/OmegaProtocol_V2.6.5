#!/bin/bash
#
# Build script for OmegaProtocol_V2.6.5
# CPU-first friendly by default.
#

VENV_DIR="venv"
DEFAULT_REQS="requirements.txt"
CPU_REQS="requirements-cpu.txt"
TEST_PATH="scrutiny-v1.2"

show_help() {
    echo "Usage: $0 {install | install-cpu | test | run-pinn | run-toe | clean}"
    echo
    echo "install       : Create venv and install full dependencies (GPU-capable machine)."
    echo "install-cpu   : Create venv and install CPU-only dependencies (recommended for mobile/ARM)."
    echo "test          : Run the scrutiny test suite."
    echo "run-pinn      : Run the PINN worker."
    echo "run-toe       : Run the ToE worker."
    echo "clean         : Remove build artifacts and venv."
}

_do_install() {
    REQS_FILE=$1
    if [ ! -f "$REQS_FILE" ]; then
        echo "Error: Requirements file not found: $REQS_FILE"
        exit 1
    fi

    echo "--- Creating Python virtual environment in '$VENV_DIR' ---"
    python -m venv $VENV_DIR

    echo "--- Installing dependencies from '$REQS_FILE' ---"
    $VENV_DIR/bin/pip install --upgrade pip
    $VENV_DIR/bin/pip install -r "$REQS_FILE"

    echo "--- Installing 'omega' package in editable mode ---"
    $VENV_DIR/bin/pip install -e .
    echo
    echo "To activate: source $VENV_DIR/bin/activate"
}

USER_ARGS=("${@:2}")

case "$1" in
    install)
        echo "Starting GPU-enabled build..."
        _do_install $DEFAULT_REQS
        ;;
    install-cpu)
        echo "Starting CPU-only build..."
        _do_install $CPU_REQS
        ;;
    test)
        if [ ! -d "$VENV_DIR" ]; then
            echo "Venv not found. Please run './build.sh install-cpu' first."
            exit 1
        fi
        ( source $VENV_DIR/bin/activate && pytest $TEST_PATH )
        ;;
    run-pinn)
        if [ ! -d "$VENV_DIR" ]; then
            echo "Venv not found. Please run './build.sh install-cpu' first."
            exit 1
        fi
        ( source $VENV_DIR/bin/activate && python pinn_worker.py "${USER_ARGS[@]}" )
        ;;
    run-toe)
        if [ ! -d "$VENV_DIR" ]; then
            echo "Venv not found. Please run './build.sh install-cpu' first."
            exit 1
        fi
        ( source $VENV_DIR/bin/activate && python toe_worker.py "${USER_ARGS[@]}" )
        ;;
    clean)
        echo "Cleaning artifacts..."
        rm -rf $VENV_DIR
        rm -rf .pytest_cache
        find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
        echo "Done."
        ;;
    ""|-h|--help|help)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac