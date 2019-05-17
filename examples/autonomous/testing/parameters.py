import os

# the path of "examples/autonomous"
SELF_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ALGORITHMS = [
    "orchestra_sb", # 1
    "orchestra_rb_s", # 2
    "orchestra_rb_ns", # 3
    #"orchestra_rb_ns_sr", # 4
    #"alice", # 5
    #"msf", # 6
    #"emsf", # 7
]

ALGONAMES = [
    "Orchestra SB",
    "Orchestra RB / Storing",
    "Orchestra RB / Non-Storing",
    # "Orchestra RB / Non-Storing (SR)", # with RPL storing rule
    # "ALICE",
    # "MSF",
    # "Extended MSF",
]

EXPERIMENTS = [
  "exp-collection",
  "exp-query",
  "exp-local"
]

SLOTFRAME_SIZES_A =[
    7,  # initial
    11, # =7+4
    19, # =11+8
    35, # =19+16
    67, # =35+32
    101 # =67+34
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
    8,  # ~8 packets per second
    15, # 4
    30, # 2
    60, # 1
    120 # 0.5
]

NUM_NEIGHBORS = [
    3, # sparse
    10 # dense
]
