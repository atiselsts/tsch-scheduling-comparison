import os

# the path of "examples/autonomous"
SELF_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ALGORITHMS = [
    "orchestra_sb", # 1
#    "orchestra_rb_s", # 2
    "orchestra_rb_ns", # 3
    #"orchestra_rb_ns_sr", # 4
    "link", # 5
 #   "msf", # 6
#    "emsf", # 7
    "alice", # 8
]

BEST_ALGORITHMS = [
    "orchestra_sb",
    "orchestra_rb_ns",
    "link",
    "alice",
]

COMPARATIVE_ALGORITHMS = [
    "dataset1",
    "dataset2",
]

ALGONAMES = {
    "orchestra_sb" : "Orchestra SB",
    "orchestra_rb_s" : "Orchestra RB / Storing",
    "orchestra_rb_ns" : "Orchestra RB / Non-Storing",
    "orchestra_rb_ns_sr" : "Orchestra RB / Non-Storing (SR)", # with RPL storing rule
    "link" : "Link-based", # ALICE-like - do not use the name ALICE because it implies other features!
    "msf" : "MSF",
    "emsf" : "Extended MSF",
    "alice" : "ALICE",

    # generic names
    "dataset1" : "Dataset 1",
    "dataset2" : "Dataset 2",
}

COLORS = {
    "orchestra_sb" : "green",
    "orchestra_rb_s" : "slateblue",
    "orchestra_rb_ns" : "orange",
    "orchestra_rb_ns_sr" : "grey",
    "link" : "lightblue",
    "msf" : "red",
    "emsf" : "brown",
    "alice" : "blue",

    "dataset1" : "red",
    "dataset2" : "green",
}

FIRMWARE_TYPES = {
    "orchestra_sb" : 1,
    "orchestra_rb_s" : 2,
    "orchestra_rb_ns" : 3,
    "orchestra_rb_ns_sr" : 4,
    "link" : 5,
    "msf" : 6,
    "emsf" : 7,
    "alice" : 8,
}

EXPERIMENTS = [
    "exp-collection",
#    "exp-query",
#    "exp-local"
]

SLOTFRAME_SIZES_A =[
#    7,  # initial
#    11, # =7+4
    19, # =11+8
 #   35, # =19+16
#    67, # =35+32
#    101 # =67+34
]

SLOTFRAME_SIZES_B =[
    7,  # initial
    15, # =7+8
    31, # =15+16
    63, # =31+32
    101 # =63+39
]

SLOTFRAME_SIZES = SLOTFRAME_SIZES_A

SEND_INTERVALS = [
    6,   # 10 packets per minute  (6x5^0)
#    30,  # 2 packets per minute   (6x5^1)
#    150  # packet per 2.5 minutes (6x5^2)
]

NUM_NEIGHBORS = [
    4, # sparse
    10 # dense
]
