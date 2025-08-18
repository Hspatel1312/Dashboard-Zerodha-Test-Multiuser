#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import locale

# Force UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Set console to UTF-8 (Windows)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Override print function to handle encoding issues
def safe_print(*args, **kwargs):
    """Print function that handles Unicode encoding issues on Windows"""
    try:
        # Try to encode all arguments as ASCII-safe strings
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # Replace any problematic Unicode characters
                safe_arg = arg.encode('ascii', 'replace').decode('ascii')
                safe_args.append(safe_arg)
            else:
                safe_args.append(str(arg))
        
        # Use the original print with safe arguments
        __builtin__print__(*safe_args, **kwargs)
    except Exception:
        # Fallback: convert everything to ASCII
        ascii_args = [str(arg).encode('ascii', 'replace').decode('ascii') for arg in args]
        __builtin__print__(*ascii_args, **kwargs)

# Store original print and replace it
__builtin__print__ = print
print = safe_print

if __name__ == "__main__":
    print("[INFO] Starting Investment Rebalancing Backend...")
    print("[INFO] UTF-8 encoding forced")
    print("[INFO] Unicode issues should be resolved")
    
    import uvicorn
    from app.main import app
    
    print("[INFO] Backend starting on http://127.0.0.1:8001")
    print("[INFO] API docs available at http://127.0.0.1:8001/docs")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8001, 
        reload=True,
        access_log=False  # Reduce console output
    )