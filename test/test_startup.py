import subprocess
import sys


def test_fastapi_openapi_models_are_built_on_first_use():
    code = """
from lauschkiste.startup import import_fastapi
import_fastapi()
from fastapi.openapi.models import OpenAPI
from pydantic import BaseModel
assert OpenAPI.__pydantic_complete__ is False, 'pydantic no longer defers: lauschkiste.startup needs a look'
OpenAPI.model_validate({'openapi': '3.1.0', 'info': {'title': 't', 'version': '1'}, 'paths': {}})
class Later(BaseModel):
    x: int
assert Later.__pydantic_complete__ is True
"""
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_timeline_lists_the_steps_with_their_durations(monkeypatch):
    from lauschkiste import startup

    monkeypatch.setattr(startup, '_marks', [])
    assert startup.timeline() == ''
    startup.mark('logging')
    startup.mark('fastapi')
    startup.mark('daemon code')
    text = startup.timeline()
    assert text.startswith('Start-up: ')
    assert 'fastapi ' in text and 'daemon code ' in text and 'total ' in text
