import sys
if sys.version_info.minor >= 11:
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

def to_float(s):
    try:
        return float(s)
    except:
        return None
    
