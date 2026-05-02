#!/bin/bash
# Parallel linting for all code (Node, Python)
# Runs all linting tasks concurrently for faster execution

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Track all background jobs
declare -a PIDS
declare -a NAMES

run_task() {
    local name="$1"
    local dir="$2"
    shift 2
    local cmd="$@"

    (
        cd "$dir"
        if OUTPUT=$($cmd 2>&1); then
            echo "OK" > "$TEMP_DIR/$name.status"
        else
            echo "FAIL" > "$TEMP_DIR/$name.status"
            echo "$OUTPUT" > "$TEMP_DIR/$name.output"
        fi
    ) &
    PIDS+=($!)
    NAMES+=("$name")
}

echo "  Syncing Python dependencies..."
# Run uv sync first to avoid race conditions when multiple uv run commands
# try to reinstall local packages in parallel (e.g., after version bump)
uv sync --quiet

echo "  Running lints in parallel..."

# Node/TypeScript tasks
run_task "eslint" "$REPO_ROOT/entelechy-control-plane" "npx eslint --fix src/**/*.{ts,tsx}"
run_task "prettier" "$REPO_ROOT/entelechy-control-plane" "npx prettier --write src/**/*.{ts,tsx}"
run_task "prettier-ts-client" "$REPO_ROOT/entelechy-clients/typescript" "npx --yes prettier --write --config $REPO_ROOT/.prettierrc.json --ignore-path $REPO_ROOT/.gitignore ."
run_task "prettier-all-npm" "$REPO_ROOT/entelechy-all-npm" "npx --yes prettier --write --config $REPO_ROOT/.prettierrc.json --ignore-path $REPO_ROOT/.gitignore ."

# Python entelechy-api-slim tasks
run_task "ruff-api-check" "$REPO_ROOT/entelechy-api-slim" "uv run ruff check --fix ."
run_task "ruff-api-format" "$REPO_ROOT/entelechy-api-slim" "uv run ruff format ."
run_task "ty-api" "$REPO_ROOT/entelechy-api-slim" "uv run ty check entelechy_api"

# Python entelechy-dev tasks
run_task "ruff-dev-check" "$REPO_ROOT/entelechy-dev" "uv run ruff check --fix ."
run_task "ruff-dev-format" "$REPO_ROOT/entelechy-dev" "uv run ruff format ."
run_task "ty-dev" "$REPO_ROOT/entelechy-dev" "uv run ty check entelechy_dev benchmarks"

# Python entelechy-embed tasks
run_task "ruff-embed-check" "$REPO_ROOT/entelechy-embed" "uv run ruff check --fix ."
run_task "ruff-embed-format" "$REPO_ROOT/entelechy-embed" "uv run ruff format ."
run_task "ty-embed" "$REPO_ROOT/entelechy-embed" "uv run ty check entelechy_embed"

# Integrations: lint packages with modifications vs HEAD locally; lint all in CI.
# Python integrations use shared ruff.toml; Node integrations use shared .prettierrc.json.
INTEGRATIONS_DIR="$REPO_ROOT/entelechy-integrations"
if [ -n "$CI" ] || [ -n "$LINT_ALL_INTEGRATIONS" ]; then
    LINT_ALL=1
    CHANGED_FILES=""
else
    LINT_ALL=0
    CHANGED_FILES=$( { git -C "$REPO_ROOT" diff --name-only HEAD -- "entelechy-integrations/"; \
                       git -C "$REPO_ROOT" ls-files --others --exclude-standard -- "entelechy-integrations/"; } | sort -u )
fi

integration_changed() {
    [ "$LINT_ALL" = "1" ] && return 0
    local rel="entelechy-integrations/$1/"
    echo "$CHANGED_FILES" | grep -q "^$rel" && return 0 || return 1
}

if [ -d "$INTEGRATIONS_DIR" ] && { [ "$LINT_ALL" = "1" ] || [ -n "$CHANGED_FILES" ]; }; then
    for dir in "$INTEGRATIONS_DIR"/*/; do
        name=$(basename "$dir")
        integration_changed "$name" || continue

        if [ -f "$dir/pyproject.toml" ]; then
            run_task "ruff-int-$name-check" "$dir" "uv run --no-project ruff check --fix --config $REPO_ROOT/ruff.toml ."
            run_task "ruff-int-$name-format" "$dir" "uv run --no-project ruff format --config $REPO_ROOT/ruff.toml ."
        elif [ -f "$dir/package.json" ]; then
            run_task "prettier-int-$name" "$dir" "npx --yes prettier --write --config $REPO_ROOT/.prettierrc.json --ignore-path $REPO_ROOT/.gitignore ."
        fi
    done
fi

# Entelechy tools (Node packages under entelechy-tools/)
TOOLS_DIR="$REPO_ROOT/entelechy-tools"
if [ -n "$CI" ] || [ -n "$LINT_ALL_INTEGRATIONS" ]; then
    LINT_TOOLS_ALL=1
    TOOLS_CHANGED=""
else
    LINT_TOOLS_ALL=0
    TOOLS_CHANGED=$( { git -C "$REPO_ROOT" diff --name-only HEAD -- "entelechy-tools/"; \
                       git -C "$REPO_ROOT" ls-files --others --exclude-standard -- "entelechy-tools/"; } | sort -u )
fi

if [ -d "$TOOLS_DIR" ] && { [ "$LINT_TOOLS_ALL" = "1" ] || [ -n "$TOOLS_CHANGED" ]; }; then
    for dir in "$TOOLS_DIR"/*/; do
        name=$(basename "$dir")
        if [ "$LINT_TOOLS_ALL" != "1" ]; then
            echo "$TOOLS_CHANGED" | grep -q "^entelechy-tools/$name/" || continue
        fi
        if [ -f "$dir/package.json" ]; then
            run_task "prettier-tool-$name" "$dir" "npx --yes prettier --write --config $REPO_ROOT/.prettierrc.json --ignore-path $REPO_ROOT/.gitignore ."
        fi
    done
fi

# Wait for all tasks to complete
for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
done

# Check results
FAILED=0
for name in "${NAMES[@]}"; do
    if [ -f "$TEMP_DIR/$name.status" ]; then
        STATUS=$(cat "$TEMP_DIR/$name.status")
        if [ "$STATUS" = "FAIL" ]; then
            echo ""
            echo "  ❌ $name failed:"
            cat "$TEMP_DIR/$name.output"
            FAILED=1
        fi
    else
        echo "  ❌ $name: no status (crashed?)"
        FAILED=1
    fi
done

if [ $FAILED -eq 1 ]; then
    exit 1
fi

echo "  All lints passed ✓"
