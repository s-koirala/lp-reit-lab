"""Headless smoke test: the Streamlit screener runs end-to-end without exceptions."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

_APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")


def test_app_runs_without_exception():
    at = AppTest.from_file(_APP, default_timeout=90)
    at.run()
    assert not at.exception
