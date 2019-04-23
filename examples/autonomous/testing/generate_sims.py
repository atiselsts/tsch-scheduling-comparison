#!/usr/bin/python

import sys, os, copy
import subprocess

OUT_DIRECTORY="../simulations"

SIMULATION_FILE_WILDCARDS = ["*grid*.csc", "*random*.csc"]

SIMULATION_FILE_DIR = "/home/atis/sphere/write/mobility/simulator/lib/"

########################################

def create_out_dir(name):
    try:
        os.mkdir(name)
    except:
        pass

########################################

env = {
    "INERTIA" : "1",
    "CONNECTIONS" : "0",
    "ORCHESTRA" : "0",
    "ORCHESTRA_GREEDY" : "0",
    "ORCHESTRA_RANDOMIZE" : "0",
    "RPL_DIO_DOUBLINGS" : "2", # corresponds to 8 seconds
    "RPL_PROBING_INTERVAL" : "20",
    "ROUTING" : "NULLROUTING",
}

all_directories = []

def generate_simulations(name, env, wildcards=SIMULATION_FILE_WILDCARDS):
    makefile = open("Makefile.tmpl", "r").read()

    # replace the template symbols with their values
    for key in env:
        makefile = makefile.replace("@" + key + "@", str(env[key]))

    dirname = os.path.join(OUT_DIRECTORY, name)
    create_out_dir(dirname)

    filenames = []
    for fs in wildcards:
        fs = SIMULATION_FILE_DIR + fs
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
        subprocess.call("cp " + filename.replace(".csc", ".dat") + " " + sim_dirname, shell=True)
        subprocess.call("cp ../common-conf.h " + sim_dirname, shell=True)
        with open(sim_dirname + "/Makefile.common", "w") as f:
            f.write(makefile)

        create_out_dir(sim_dirname + "/gw")
        subprocess.call("cp ../gw/project-conf.h " + sim_dirname + "/gw", shell=True)
        subprocess.call("cp ../gw/Makefile " + sim_dirname + "/gw", shell=True)
        subprocess.call("cp ../gw/node.c " + sim_dirname + "/gw", shell=True)

        create_out_dir(sim_dirname + "/wearable")
        subprocess.call("cp ../wearable/project-conf.h " + sim_dirname + "/wearable", shell=True)
        subprocess.call("cp ../wearable/Makefile " + sim_dirname + "/wearable", shell=True)
        subprocess.call("cp ../wearable/node.c " + sim_dirname + "/wearable", shell=True)

########################################

def generate_runner():
    with open("run.sh", "w") as f:
        f.write("#!/bin/bash\n")

        for i, dirname in enumerate(all_directories):
            f.write("./run_cooja.py " + dirname + " &\n")
            if i % 8 == 7:
                f.write("wait\n\n")
        f.write("wait\n")

    os.chmod("run.sh", 0o755)

########################################
def main():
    create_out_dir(OUT_DIRECTORY)

    cenv = copy.copy(env)
    generate_simulations("instant", cenv)

    cenv = copy.copy(env)
    cenv["CONNECTIONS"] = "1"
    generate_simulations("connections", cenv)

    cenv = copy.copy(env)
    cenv["ORCHESTRA"] = "1"
    cenv["ROUTING"] = "RPL_CLASSIC"
    generate_simulations("orchestra", cenv)

    cenv["ORCHESTRA_GREEDY"] = "1"
    generate_simulations("orchestra-greedy", cenv)

    # for the RPL optimization experiment
    cenv["ROUTING"] = "RPL_CLASSIC"
    for dbl in [0, 1, 2, 3, 4]: # 0=2^1=2 seconds; 4=2^5=32 seconds
        cenv["RPL_DIO_DOUBLINGS"] = str(dbl)
        generate_simulations("rpl-dio-optimization-{}".format(dbl), cenv, wildcards=["random-m3w-*.csc"])

    cenv["RPL_DIO_DOUBLINGS"] = "1"
    for interval in [5, 10, 15, 20, 25]:
        cenv["RPL_PROBING_INTERVAL"] = str(interval)
        generate_simulations("rpl-probing-optimization-{}".format(interval), cenv, wildcards=["random-m3w-*.csc"])

    generate_runner()


########################################
if __name__ == '__main__':
    main()
    print("all done!")

