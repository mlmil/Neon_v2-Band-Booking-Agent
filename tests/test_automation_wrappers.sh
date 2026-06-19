#!/bin/bash
set -e

REPO_DIR="/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2"
cd "$REPO_DIR"

echo "Running wrapper checks..."

# Check syntax
for wrapper in scripts/automation/*.sh; do
    echo "Checking syntax: $wrapper"
    bash -n "$wrapper"
done

# Check executable bit
for wrapper in scripts/automation/*.sh; do
    if [ ! -x "$wrapper" ]; then
        echo "Error: $wrapper is not executable"
        exit 1
    fi
done

echo "Running plist validation..."

# Check plist syntax
for plist in launch_agents/*.plist; do
    echo "Checking plist: $plist"
    plutil -lint "$plist"
done

echo "Running dry-run overlap simulation..."

# Overlap simulation for health_check
LOCKDIR="/tmp/neon_health_check.lock"
rm -rf "$LOCKDIR"
mkdir "$LOCKDIR"

# Should immediately exit 0 because lock exists
if scripts/automation/wrapper_health_check.sh 2>&1 | grep -q "Already running"; then
    echo "Overlap protection works."
else
    echo "Overlap protection failed!"
    rm -rf "$LOCKDIR"
    exit 1
fi
rm -rf "$LOCKDIR"

echo "All tests passed successfully!"
