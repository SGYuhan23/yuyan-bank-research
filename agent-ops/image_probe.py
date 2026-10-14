"""One real image request; no retries, no mock, no credential logging."""
from runtime import configure,OPS
configure()
from media import ImageProvider,ImageUnavailable
import os,json,time
start=time.monotonic()
result={'mock':False,'model':os.environ['QWEN_IMAGE_MODEL']}
try:
 data,meta=ImageProvider(os.environ['QWEN_IMAGE_ENDPOINT'],os.environ['QWEN_IMAGE_MODEL'],os.environ['QWEN_API_KEY']).generate('一只橘色小猫坐在窗边，窗外有绿色树木，温暖柔和的水彩插画，无文字。','1024*1024')
 (OPS/'evidence/qwen-image-probe.png').write_bytes(data)
 result.update(status='success',bytes=len(data),metadata=meta)
except ImageUnavailable as exc:result.update(status='unavailable',reason=str(exc))
result['seconds']=round(time.monotonic()-start,2)
(OPS/'evidence/image-provider.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
