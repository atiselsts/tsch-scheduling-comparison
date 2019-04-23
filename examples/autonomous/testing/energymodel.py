#!/usr/bin/python3

# the values are approximate, and for TSCH on CC2650
# (using the data from "Technical Report: Energy usage on SPES-2 nodes")

# assume 3.3 volts
VOLTAGE = 3.3

# all charges given in microcoulumbs

# assume full byte packet
CHARGE_FOR_PACKET_TX = 80

# assume ~50 byte adv
CHARGE_FOR_ADV_TX = 40

# assume ~10 byte ack
CHARGE_FOR_ADV_ACK_RX = 10

# depends on the number of ACK slots
NUM_ACKS = 3

CHARGE_FOR_ADV_TX_WITH_ACKS = CHARGE_FOR_ADV_TX + CHARGE_FOR_ADV_ACK_RX * NUM_ACKS


CHARGE_FOR_RX_IDLE = 20
CHARGE_FOR_RX_UC = 60 # assume ~100 bytes
CHARGE_FOR_RX_BC = 60 # assume ~100 bytes

CHARGE_FOR_TX_UC = 70 # assume ~100 bytes
CHARGE_FOR_TX_BC = 55 # assume ~100 bytes


# convert from microcoulumbs to millijoules, assuming fixed voltage
def to_millijoules(uc):
    return uc * VOLTAGE / 1000.0


def account(num_sent, num_probing_sent):
    energy_packets = to_millijoules(num_sent * CHARGE_FOR_PACKET_TX)
    energy_advertisements = to_millijoules(num_probing_sent * CHARGE_FOR_ADV_TX_WITH_ACKS)
    return energy_packets + energy_advertisements

def account_ex(num_sent, num_probing_sent, rxi, rxuc, rxbc, txuc, txbc):
    energy = 0
    energy += to_millijoules(rxi * CHARGE_FOR_RX_IDLE)
    energy += to_millijoules(rxuc * CHARGE_FOR_RX_UC)
    energy += to_millijoules(rxbc * CHARGE_FOR_RX_BC)
    energy += to_millijoules(txuc * CHARGE_FOR_TX_UC)
    energy += to_millijoules(txbc * CHARGE_FOR_TX_BC)
    return account(num_sent, num_probing_sent) + energy
