import sys
import os
curr = os.getcwd()

if curr not in sys.path():
    sys.path.append(curr)
