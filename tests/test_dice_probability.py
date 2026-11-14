"""Regression checks for reduced third-consecutive-six probability."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def test_python_games_reduce_only_third_six_probability():
    for path in (
        ROOT / "reference/Ludo_Original_Design_GUI_Match_v20.py",
        ROOT / "reference/original_python_ludo.py",
    ):
        source = path.read_text(encoding="utf-8")
        assert "six_chance = 0.02 if self.six_streak >= 2 else 0.35" in source

def test_web_game_reduces_only_third_six_probability():
    source = (ROOT / "www/app.js").read_text(encoding="utf-8")
    assert "state.sixStreak>=2?.02:.35" in source
