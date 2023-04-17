# import re
import sys
from mcpyrate.repl.macropython import main, import_module_as_main
from pathlib import Path

def run():
    sys.argv = ['macropython', '-m', 'main']
    exit(main())

run()
