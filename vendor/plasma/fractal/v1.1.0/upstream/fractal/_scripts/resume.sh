#!/usr/bin/env bash
set -euo pipefail

# Relaunch a paused node's loop to adopt its open run
# ---------------------------------------------------

usage() {
    cat <<USAGE
Usage: resume.sh <path>

Relaunch a paused node's loop to adopt its open run.

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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# derive the session name (mirrors start.sh) to catch a resume racing a loop
# that is still parking -- start.sh's own session-exists refusal suggests
# kill, which would destroy the paused run; the right move is to retry
REPO_NAME=${WORKTREE_DIR##*/}
if COMMON_DIR=$(git -C "$WORKTREE_DIR" rev-parse --git-common-dir 2>/dev/null); then
    if [[ "$COMMON_DIR" = /* ]]; then
        REPO_ROOT=$(cd "$COMMON_DIR/.." && pwd)
    else
        REPO_ROOT=$(cd "$WORKTREE_DIR/$COMMON_DIR/.." && pwd)
    fi
    REPO_NAME=${REPO_ROOT##*/}
fi
TMUX_SESSION_NAME="${REPO_NAME//[.:]/-}"
if BRANCH=$(git -C "$WORKTREE_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null); then
    TMUX_SESSION_NAME="${REPO_NAME//[.:]/-} (${BRANCH//./-})"
fi
# grep -qxF (exact match), not tmux -t: -t resolves targets by
# prefix/fnmatch, so a short name false-matches longer session names
if tmux list-sessions -F '#{session_name}' 2>/dev/null \
    | grep -qxF "$TMUX_SESSION_NAME"; then
    echo "Error: the loop is still running or parking: $TMUX_SESSION_NAME" >&2
    echo "Retry once it exits" >&2
    exit 1
fi

# start.sh hosts the tmux launch; --resume makes the loop adopt the
# paused run instead of opening a fresh one
exec bash "$SCRIPT_DIR/start.sh" "$WORKTREE_DIR" --resume
