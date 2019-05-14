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
]

ALGONAMES = [
    "Orchestra SB",
    "Orchestra RB / Storing",
    "Orchestra RB / Non-Storing",
    # "Orchestra RB / Non-Storing (SR)", # with RPL storing rule
    # "ALICE",
    # "MSF",
]

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

SEND_INTERVALS = [
    8,  # ~8 packets per second
    15, # 4
    30, # 2
    60, # 1
    120 # 0.5
]

#sim-3-neigh
NUM_NEIGHBORS = [
    3,
    7,
    11
]
