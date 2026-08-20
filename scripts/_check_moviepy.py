import sys
try:
    import moviepy
    print("moviepy version:", getattr(moviepy, '__version__', 'unknown'))
    print("Available:", [x for x in dir(moviepy) if not x.startswith('_')])
except Exception as e:
    print("Error:", e)
    sys.exit(1)
