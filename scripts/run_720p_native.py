"""Run unchanged long 720p video fixtures in the local timed simulation runtime."""
from pathlib import Path
import argparse
import runpy
import sys
import refined_testlib
from refined_native_testlib import run_native

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("fixture", choices=("video", "live"))
parser.add_argument("arguments", nargs=argparse.REMAINDER)
args = parser.parse_args()
fixture = Path(__file__).with_name("test_refined_" + args.fixture + ".py")
refined_testlib.run = run_native
sys.argv = [str(fixture), *args.arguments]
runpy.run_path(str(fixture), run_name="__main__")
