try:
    import kagglehub
    print('kagglehub available')
    print('version:', kagglehub.__version__)
except ImportError:
    print('kagglehub not installed')
except Exception as e:
    print('kagglehub error:', e)