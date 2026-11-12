# Smoke test of the runner: environment and tools.
echo "repo: $REPO"; git -C "$REPO" log --oneline -1; "$PY" --version; "$CLI" --version; nproc
