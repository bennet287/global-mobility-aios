#!/usr/bin/env bash
set -euo pipefail

# Hook for post-unretire logic (called after status is reset to idle)
# -------------------------------------------------------------------

usage() {
    cat <<USAGE
Usage: unretire.sh <path>

Hook for post-unretire logic.

Options:
    --help|-h    Show this help message
USAGE
    exit 0
}

WORKTREE_DIR=""

for arg in "$@"; do
    case "$arg" in
        --help | -h) usage ;;
        *)
            if [[ -z "$WORKTREE_DIR" ]]; then
                WORKTREE_DIR="$arg"
            fi
            ;;
    esac
done

if [[ -z "$WORKTREE_DIR" ]]; then
    echo "Error: path is required" >&2
    exit 1
fi

if [[ ! "$WORKTREE_DIR" = /* ]]; then
    WORKTREE_DIR="$(cd "$WORKTREE_DIR" && pwd)"
fi

# Python handles the unretire -- extend here if needed
