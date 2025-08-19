
import sys, asyncio, os

# Python her çalışmada otomatik yükler (sys.path içinde kök varsa).
import sys, pathlib
root = pathlib.Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# Ensure Windows event loop policy compatible with many libs
try:
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except Exception:
    pass

# Provide a safe get_event_loop fallback for non-main threads (Streamlit ScriptRunner)
try:
    _orig_get_event_loop = asyncio.get_event_loop
    def _safe_get_event_loop():
        try:
            return _orig_get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
    asyncio.get_event_loop = _safe_get_event_loop  # monkey-patch (non-invasive: only fallback path)
except Exception:
    pass
