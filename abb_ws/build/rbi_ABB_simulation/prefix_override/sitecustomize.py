import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/eia/repo/rbi_2025_2/abb_ws/install/rbi_ABB_simulation'
