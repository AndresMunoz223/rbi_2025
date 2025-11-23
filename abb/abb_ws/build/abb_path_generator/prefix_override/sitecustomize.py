import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/eia/rbi_2025/abb/abb_ws/install/abb_path_generator'
