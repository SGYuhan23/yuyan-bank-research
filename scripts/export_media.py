"""Crop only the private sidebar from actual browser recordings; preserve real sequence."""
import os,subprocess,json
from pathlib import Path
ffmpeg=os.environ.get('FFMPEG','ffmpeg')
for name in ('overview','fuling','supplier-ai'):
 subprocess.run([ffmpeg,'-y','-i',f'tmp/portfolio-recordings/{name}.webm','-vf','crop=1244:1000:256:0','-c:v','libx264','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',f'docs/media/{name}.mp4'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run([ffmpeg,'-y','-ss','3','-t','12','-i','docs/media/overview.mp4','-filter_complex','fps=8,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse','-loop','0','docs/media/overview-preview.gif'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print('3 actual recordings exported; 12-second preview; only sidebar cropped')
