#!/usr/bin/env python

import sys, os, re, random, math
import numpy as np
from subprocess import Popen, PIPE, STDOUT

cooja = 'java -jar /home/atis/work/scheduling-comparison-contiki/tools/cooja/dist/cooja.jar'
cooja_input = './sim.csc'
cooja_output = 'COOJA.testlog'

#######################################################
def run_subprocess(args, input_string):
    retcode = -1
    stdoutdata = ''
    try:
        proc = Popen(args, stdout = PIPE, stderr = STDOUT, stdin = PIPE, shell = True)
        (stdoutdata, stderrdata) = proc.communicate(input_string)
        if not stdoutdata:
            stdoutdata = ''
        if stderrdata:
            stdoutdata += stderrdata
        retcode = proc.returncode
    except OSError as e:
        sys.stderr.write("runSubprocess OSError:" + str(e))
    except CalledProcessError as e:
        sys.stderr.write("runSubprocess CalledProcessError:" + str(e))
        retcode = e.returncode
    except Exception as e:
        sys.stderr.write("runSubprocess exception:" + str(e))
    finally:
        return (retcode, stdoutdata)


#######################################################
def execute_test(directory, cooja_file):
    os.chdir(directory)

    # cleanup
    try:
        os.rm(cooja_output)
    except:
        pass

    args = " ".join([cooja, "-nogui=" + cooja_file])
    sys.stdout.write("  Running Cooja on {}\n".format(
        os.path.join(directory, cooja_file)))

    (retcode, output) = run_subprocess(args, '')
    if retcode != 0:
        sys.stderr.write("Failed, retcode=" + str(retcode) + ", output:")
        sys.stderr.write(output)
        return False

    sys.stdout.write("  Checking for output...")

    is_done = False
    with open(cooja_output, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line == "TEST OK":
                sys.stdout.write(" done.\n")
                is_done = True
                continue

    if not is_done:
        sys.stdout.write("  test failed.\n")
        return False

    sys.stdout.write(" test done\n")
    return True

#######################################################

def execute_test_run(directory):
    execute_test(directory, "sim.csc")

#######################################################

def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "./"
    execute_test_run(arg)
    print("all done")

#######################################################

if __name__ == '__main__':
    main()
