"""Compatibility entrypoint; final trace now records proposal, correction and confirmation."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('final_trace_acceptance.py')),run_name='__main__')
