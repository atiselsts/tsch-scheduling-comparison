#!/usr/bin/python

import sys, os, copy, errno
import multiprocessing
import subprocess

# the path of "examples/autonomous"
SELF_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OUT_DIRECTORY = os.path.join(SELF_PATH, "simulations")

# tailor the workload depending on the number of cores;
# but leave some cores free for other things
NUM_CORES = multiprocessing.cpu_count() * 7 // 8

ENV = {
    "FIRMWARE_TYPE" : "1",
    "ORCHESTRA_CONF_UNICAST_PERIOD" : "11"
}

EXPERIMENTS = [
  "exp-collection",
  "exp-query",
  "exp-local"
]

SLOTFRAME_SIZES =[
    7,
    11,
    15,
    19,
    23,
    27,
    31
]

########################################

def create_out_dir(name):
    try:
        os.mkdir(name)
    except IOError as e:
        if e.errno != errno.EEXIST:
           print("Failed to create " + name)
           print(e)
        pass
    except Exception as ex:
        pass


########################################

def generate_simulations(name, env, wildcards, experiments):
    makefile = open("Makefile.tmpl", "r").read()

    # replace the template symbols with their values
    for key in env:
        makefile = makefile.replace("@" + key + "@", str(env[key]))

    dirname = os.path.join(OUT_DIRECTORY, name)
    create_out_dir(dirname)
    print("dirname=", dirname)

    filenames = []
    for fs in wildcards:
        fs = os.path.join(SELF_PATH, fs)
        try:
            filenames += subprocess.check_output("ls " + fs, shell=True).split()
        except Exception as ex:
            print(ex)

    all_directories = []
    for exp in experiments:
        exp_dirname = os.path.join(dirname, exp)
        create_out_dir(exp_dirname)

        for filename in filenames:
            sim_name = os.path.basename(os.path.splitext(filename)[0])
            sim_dirname = os.path.join(exp_dirname, sim_name)
            create_out_dir(sim_dirname)

            all_directories.append(sim_dirname)

            subprocess.call("cp " + filename + " " + sim_dirname + "/sim.csc", shell=True)
            subprocess.call("cp ../common-conf.h " + sim_dirname, shell=True)
            with open(sim_dirname + "/Makefile.common", "w") as f:
                f.write(makefile)

            # all files go into "node"
            create_out_dir(sim_dirname + "/node")
            subprocess.call("cp ../" + exp + "/project-conf.h " + sim_dirname + "/node", shell=True)
            subprocess.call("cp ../" + exp + "/Makefile " + sim_dirname + "/node", shell=True)
            subprocess.call("cp ../" + exp + "/node.c " + sim_dirname + "/node", shell=True)
    return all_directories

########################################

def generate_runner(description, all_directories):
    with open("run-" + description + ".sh", "w") as f:
        f.write("#!/bin/bash\n")

        for i, dirname in enumerate(all_directories):
            f.write("./run_cooja.py " + dirname + " &\n")
            if i % NUM_CORES == NUM_CORES - 1:
                f.write("wait\n\n")
        f.write("wait\n")

    os.chmod("run-" + description + ".sh", 0o755)

########################################
def generate_sims(wildcards, description, ss, experiments=EXPERIMENTS):
    all_directories = []

    ENV["ORCHESTRA_CONF_UNICAST_PERIOD"] = ss

    cenv = copy.copy(ENV)
    cenv["FIRMWARE_TYPE"] = "1"
    all_directories += generate_simulations("orchestra_sb_{}".format(ss), cenv, wildcards, experiments)

    cenv = copy.copy(ENV)
    cenv["FIRMWARE_TYPE"] = "2"
    all_directories += generate_simulations("orchestra_rb_s_{}".format(ss), cenv, wildcards, experiments)

    cenv = copy.copy(ENV)
    cenv["FIRMWARE_TYPE"] = "3"
    all_directories += generate_simulations("orchestra_rb_ns_{}".format(ss), cenv, wildcards, experiments)

#    cenv = copy.copy(ENV)
#    cenv["FIRMWARE_TYPE"] = "4"
#    generate_simulations("orchestra_rb_ns_sr_{}".format(ss), cenv, wildcards, experiments)

    if 0:
        cenv = copy.copy(ENV)
        cenv["FIRMWARE_TYPE"] = "5"
        all_directories += generate_simulations("alice_{}".format(ss), cenv, wildcards, experiments)

        cenv = copy.copy(ENV)
        cenv["FIRMWARE_TYPE"] = "6"
        all_directories += generate_simulations("msf_{}".format(ss), cenv, wildcards, experiments)

    generate_runner(description, all_directories)

########################################
def main():
    create_out_dir(OUT_DIRECTORY)
    # full simulations
    for ss in SLOTFRAME_SIZES:
        generate_sims(["e-sparse-*.csc", "e-dense-*.csc"], "all", ss)
    # lite version, usefull for running quick check to make sure all the configs compile and linkl
    generate_sims(["3nodes-cooja-ll.csc"], "lite", 7)

########################################
if __name__ == '__main__':
    main()
    print("all done!")

