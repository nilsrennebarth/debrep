#
# We want modules in this package to work when being imported,
# but also when called directly, even when not installed
#
import os.path, sys
sys.path.append(os.path.dirname(__file__))
