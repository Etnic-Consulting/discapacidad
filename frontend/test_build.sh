#!/usr/bin/env bash
# ============================================================
# SMT-ONIC Frontend Build Test
# ============================================================
# Runs: npm run build, checks dist/ output, verifies no
# "discapacidad" appears in user-facing text in built JS.
# ============================================================

set -e

FRONTEND_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$FRONTEND_DIR"

PASS=0
FAIL=0

report() {
    local name="$1"
    local ok="$2"
    local detail="$3"
    if [ "$ok" = "true" ]; then
        PASS=$((PASS + 1))
        echo "  PASS  $name"
    else
        FAIL=$((FAIL + 1))
        echo "  FAIL  $name  -- $detail"
    fi
}

echo ""
echo "=== FRONTEND BUILD TEST ==="
echo ""

# 1. Run npm run build
echo "Running npm run build..."
if npm run build > /tmp/smt_build_output.txt 2>&1; then
    report "npm run build exits with code 0" "true"
else
    BUILD_EXIT=$?
    report "npm run build exits with code 0" "false" "exit code $BUILD_EXIT"
    echo "Build output:"
    cat /tmp/smt_build_output.txt
    echo ""
    echo "============================================================"
    echo "RESULTS: $PASS passed, $FAIL failed"
    echo "============================================================"
    exit 1
fi

# 2. Check dist/ directory exists and has content
if [ -d "dist" ] && [ "$(ls -A dist 2>/dev/null)" ]; then
    report "dist/ directory exists and has content" "true"
else
    report "dist/ directory exists and has content" "false" "dist/ is missing or empty"
fi

# 3. Check dist/index.html exists
if [ -f "dist/index.html" ]; then
    report "dist/index.html exists" "true"
else
    report "dist/index.html exists" "false" "not found"
fi

# 4. Check JS assets exist
JS_COUNT=$(find dist -name "*.js" 2>/dev/null | wc -l)
if [ "$JS_COUNT" -gt 0 ]; then
    report "JS assets exist in dist/" "true"
else
    report "JS assets exist in dist/" "false" "no .js files found"
fi

# 5. Check CSS assets exist
CSS_COUNT=$(find dist -name "*.css" 2>/dev/null | wc -l)
if [ "$CSS_COUNT" -gt 0 ]; then
    report "CSS assets exist in dist/" "true"
else
    report "CSS assets exist in dist/" "false" "no .css files found"
fi

# 6. Grep for "discapacidad" in built JS (should NOT appear in user-facing text)
#    Note: it may appear in variable names/code paths, so we check for
#    human-readable contexts (preceded/followed by spaces, in strings)
DISCAP_HITS=""
for jsfile in $(find dist -name "*.js" 2>/dev/null); do
    # Search for discapacidad as a standalone word (case-insensitive)
    hits=$(grep -ioP '\bdiscapacidad\b' "$jsfile" 2>/dev/null || true)
    if [ -n "$hits" ]; then
        count=$(echo "$hits" | wc -l)
        DISCAP_HITS="$DISCAP_HITS $jsfile($count)"
    fi
done

if [ -z "$DISCAP_HITS" ]; then
    report "No 'discapacidad' in user-facing JS text" "true"
else
    report "No 'discapacidad' in user-facing JS text" "false" "found in:$DISCAP_HITS"
fi

# Summary
echo ""
echo "============================================================"
echo "RESULTS: $PASS passed, $FAIL failed, $((PASS + FAIL)) total"
echo "============================================================"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
