import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/eia/rbi_2025/rov/rov_ws/install/rov_path_follower'
