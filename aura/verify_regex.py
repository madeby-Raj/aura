import traceback
try:
    import regex
    print("regex loaded from:", getattr(regex, "__file__", "unknown"))
    print("regex version:", getattr(regex, "__version__", "unknown"))
except Exception:
    traceback.print_exc()
