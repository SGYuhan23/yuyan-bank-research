from runtime import configure
configure()
import sys
from runtime import PLATFORM
sys.path.insert(0, str(PLATFORM / 'backend'))
import uvicorn
uvicorn.run('app.gateway.app:app', host='127.0.0.1', port=8001, log_level='warning')
