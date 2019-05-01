#!/usr/bin/python

import sys, os, copy
import subprocess

SELF_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OUT_DIRECTORY = os.path.join(SELF_PATH, "simulations")

SIMULATION_FILE_DIR = SELF_PATH
SIMULATION_FILE_WILDCARDS = ["sparse-*.csc", "e-sparse-*.csc", "dense-*.csc", "e-dense-*.csc"]

########################################

def create_out_dir(name):
    try:
        os.mkdir(name)
    except:
        pass

########################################

env = {
    "FIRMWARE_TYPE" : "1",
}

all_directories = []

def generate_simulations(name, env, wildcards=SIMULATION_FILE_WILDCARDS):
    makefile = open("Makefile.tmpl", "r").read()

    # replace the template symbols with their values
    for key in env:
        makefile = makefile.replace("@" + key + "@", str(env[key]))

    dirname = os.path.join(OUT_DIRECTORY, name)
    create_out_dir(dirname)
    print("dirname=", dirname)

    filenames = []
    for fs in wildcards:
        fs = os.path.join(SIMULATION_FILE_DIR, fs)
        try:
            filenames += subprocess.check_output("ls " + fs, shell=True).split()
        except Exception as ex:
            print(ex)

    for filename in filenames:
        sim_name = os.path.basename(os.path.splitext(filename)[0])
        sim_dirname = os.path.join(dirname, sim_name)
        create_out_dir(sim_dirname)

        all_directories.append(sim_dirname)

        subprocess.call("cp " + filename + " " + sim_dirname + "/sim.csc", shell=True)
        subprocess.call("cp ../common-conf.h " + sim_dirname, shell=True)
        with open(sim_dirname + "/Makefile.common", "w") as f:
            f.write(makefile)

        create_out_dir(sim_dirname + "/node")
        subprocess.call("cp ../node/project-conf.h " + sim_dirname + "/node", shell=True)
        subprocess.call("cp ../node/Makefile " + sim_dirname + "/node", shell=True)
        subprocess.call("cp ../node/node.c " + sim_dirname + "/node", shell=True)

########################################

def generate_runner():
    with open("run.sh", "w") as f:
        f.write("#!/bin/bash\n")

        for i, dirname in enumerate(all_directories):
            f.write("./run_cooja.py " + dirname + " &\n")
            if i % 4 == 3:
                f.write("wait\n\n")
        f.write("wait\n")

    os.chmod("run.sh", 0o755)

########################################
def main():
    create_out_dir(OUT_DIRECTORY)

    cenv = copy.copy(env)
    cenv["FIRMWARE_TYPE"] = "1"
    generate_simulations("orchestra_sb", cenv)

    cenv = copy.copy(env)
    cenv["FIRMWARE_TYPE"] = "2"
    generate_simulations("orchestra_rb_s", cenv)

    cenv = copy.copy(env)
    cenv["FIRMWARE_TYPE"] = "3"
    generate_simulations("orchestra_rb_ns", cenv)

    if 0:
        cenv = copy.copy(env)
        cenv["FIRMWARE_TYPE"] = "4"
        generate_simulations("alice", cenv)

        cenv = copy.copy(env)
        cenv["FIRMWARE_TYPE"] = "5"
        generate_simulations("msf", cenv)

    generate_runner()


########################################
if __name__ == '__main__':
    main()
    print("all done!")

