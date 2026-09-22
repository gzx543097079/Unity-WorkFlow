#!/usr/bin/env python3
"""从项目内 Skill 加载 unity-work-flow 唯一实现。"""
import runpy
from pathlib import Path

_source = Path(__file__).resolve().parents[1] / '.agents/skills/unity-work-flow/scripts/teamflow.py'
globals().update(runpy.run_path(str(_source), run_name=__name__))
