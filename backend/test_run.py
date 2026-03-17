import sys
import traceback
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

try:
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
except Exception:
    traceback.print_exc()
