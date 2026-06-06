"""Guard: the generated web/ engine fixtures match the Python engine.

The TS finance mirror (web/src/lib/engine) is parity-tested against
web/src/lib/engine/__fixtures__/golden_vectors.json and reads
web/src/lib/engine/config.generated.json at runtime. Both are emitted by
scripts/export_web_engine_fixtures.py from the canonical Python engine + config
YAMLs. This test fails if they have drifted (i.e. the exporter was not re-run
after an engine/config change), the same check the pre-commit `web-engine-fixtures`
hook enforces.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "web" / "src" / "lib" / "engine" / "__fixtures__" / "golden_vectors.json"


def test_web_engine_fixtures_are_current():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "export_web_engine_fixtures.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,  # we assert on returncode ourselves to surface the stderr hint
    )
    assert result.returncode == 0, (
        "web engine fixtures are stale — run "
        "`uv run python scripts/export_web_engine_fixtures.py`.\n" + result.stderr
    )


def test_golden_vectors_cover_both_terminal_bases():
    """Pin reversion-branch coverage so a CASES edit can't silently de-cover the
    appreciation (NOI<=0) fallback — the Round-1 finding it remediated."""
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    bases = {c["expected"]["terminal_basis"] for c in golden["cases"]}
    assert bases == {"exit-cap", "appreciation"}, bases
