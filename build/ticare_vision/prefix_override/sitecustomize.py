import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/luisgfgetino/ticare_ws/src/install/ticare_vision'
