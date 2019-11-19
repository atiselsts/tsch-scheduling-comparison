#!/usr/bin/python

import sys, os, copy, errno
import multiprocessing
import subprocess

from parameters import *

OUT_DIRECTORY = os.path.join(SELF_PATH, "simulations")

# tailor the workload depending on the number of cores;
# but leave some cores free for other things
NUM_CORES = multiprocessing.cpu_count() * 7 // 8

ENV = {
    "FIRMWARE_TYPE" : "1",
    "ORCHESTRA_CONF_UNICAST_PERIOD" : "11",
    "ORCHESTRA_CONF_ROOT_RULE" : "0"
}

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

def generate_source_dirs(dirname, env, experiments):
    makefile = open("Makefile.tmpl", "r").read()

    # replace the template symbols with their values
    for key in env:
        makefile = makefile.replace("@" + key + "@", str(env[key]))

    contiki = os.path.dirname(os.path.dirname(SELF_PATH))
    makefile = makefile.replace("CONTIKI=../../../../../../../../..", "CONTIKI=" + contiki)

    print("dirname=", dirname)

    all_directories = []
    for exp in experiments:
        exp_dirname = os.path.join(dirname, exp)
        create_out_dir(exp_dirname)

        all_directories.append(exp_dirname)

        subprocess.call("cp ../common-conf.h " + exp_dirname, shell=True)
        with open(exp_dirname + "/Makefile.common", "w") as f:
            f.write(makefile)

        # all files go into "node"
        create_out_dir(exp_dirname + "/node")
        subprocess.call("cp ../" + exp + "/project-conf.h " + exp_dirname + "/node", shell=True)
        subprocess.call("cp ../" + exp + "/node.c " + exp_dirname + "/node", shell=True)
        with open(exp_dirname + "/node/Makefile", "w") as f:
            f.write("include " + exp_dirname + "/Makefile.common\n")
    return all_directories

########################################

def generate_runner(description, all_directories, do_overwrite):
    open_as = "w" if do_overwrite else "a+"
    with open("run-" + description + ".sh", open_as) as f:
        if do_overwrite:
            f.write("#!/bin/bash\n")
        for i, dirname in enumerate(all_directories):
            f.write("./run_cooja.py " + dirname + " &\n")
            if i % NUM_CORES == NUM_CORES - 1:
                f.write("wait\n\n")
        f.write("wait\n")

    os.chmod("run-" + description + ".sh", 0o755)

########################################

def generate_builder(description, all_directories, do_overwrite):
    open_as = "w" if do_overwrite else "a+"
    with open("compile-" + description + ".sh", open_as) as f:
        if do_overwrite:
            f.write("#!/bin/bash\n")
        f.write("export TARGET=iotlab\n")
        f.write("export BOARD=m3\n")
        f.write("export ARCH_PATH=/home/atis.elsts/work/iot-lab/parts/iot-lab-contiki-ng/arch/\n")
        f.write("mkdir -p iot-lab-firmwares\n")
        for i, dirname in enumerate(all_directories):
            sim_desc = dirname.split("/")[-4:]
            sim_desc = "_".join(sim_desc)
            f.write("echo building " + sim_desc + "\n")
            f.write("make -C " + dirname + "/node TARGET=iotlab -j >/dev/null || exit -1\n")
            f.write("cp " + dirname + "/node/node.iotlab iot-lab-firmwares/" + sim_desc + ".iotlab\n")
        f.write("echo 'all done!'\n")

    os.chmod("compile-" + description + ".sh", 0o755)

########################################
def main():
    # sparse, medium, and dense networks - depending on the neighbor count
    all_directories = []
    dirname1 = OUT_DIRECTORY
    create_out_dir(dirname1)
    for a in ALGORITHMS:
        firmware_type = FIRMWARE_TYPES[a]
        dirname2 = os.path.join(dirname1, a)
        create_out_dir(dirname2)
        for si in SEND_INTERVALS:
            dirname3 = os.path.join(dirname2, "si_{}".format(si))
            create_out_dir(dirname3)
            for ss in SLOTFRAME_SIZES:
                dirname4 = os.path.join(dirname3, "sf_{}".format(ss))
                create_out_dir(dirname4)
                cenv = copy.copy(ENV)
                cenv["FIRMWARE_TYPE"] = str(firmware_type)
                cenv["SEND_INTERVAL_SEC"] = str(si)
                cenv["ORCHESTRA_CONF_UNICAST_PERIOD"] = str(ss)
                all_directories += generate_source_dirs(dirname4, cenv, EXPERIMENTS)
    generate_builder("all", all_directories, True)
    generate_runner("all", all_directories, True)


########################################
if __name__ == '__main__':
    main()
    print("all done!")

