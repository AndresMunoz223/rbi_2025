import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/eia/rbi_2025/scara/scara_ws/install/premade_path_publisher'
