"""macOS Vision OCR subprocess, fixed executable and args; no model-supplied code."""
import subprocess,tempfile,json,sys
from pathlib import Path

def extract(raw):
    root=Path(__file__).resolve().parent
    binary=root.parent/'local/vision-ocr'
    if sys.platform!='darwin':raise RuntimeError('NATIVE_OCR_UNAVAILABLE')
    if not binary.exists():
        binary.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['/usr/bin/swiftc',str(root/'ocr.swift'),'-o',str(binary)],check=True,capture_output=True,timeout=90)
    with tempfile.NamedTemporaryFile(suffix='.png') as f:
        f.write(raw);f.flush()
        out=subprocess.run([str(binary),f.name],check=True,capture_output=True,timeout=20)
    return json.loads(out.stdout)
