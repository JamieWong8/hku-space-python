#!/usr/bin/env python3
import sys, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(here, os.pardir))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
print('[DIAG] sys.path[0]:', sys.path[0])
try:
    import model
    print('[DIAG] model imported successfully')
    print('[DIAG] data_source:', getattr(model, 'data_source', None))
    sd = getattr(model, 'sample_data', None)
    print('[DIAG] sample_data len:', len(sd) if sd is not None else None)
    clf = getattr(model, 'startup_classifier', None)
    reg = getattr(model, 'startup_regressor', None)
    print('[DIAG] models:', type(clf).__name__ if clf else None, type(reg).__name__ if reg else None)
except Exception as e:
    print('[DIAG] ERROR importing model:', e)
    traceback.print_exc()
    raise
