# Python her çalışmada otomatik yükler (sys.path içinde kök varsa).
import sys, pathlib
root = pathlib.Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
