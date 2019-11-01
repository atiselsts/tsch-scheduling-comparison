#include <stdint.h>
#include <inttypes.h>

/*******************************************************/
/******************* Configure network stack ***********/
/*******************************************************/

#define SICSLOWPAN_CONF_FRAG 0 /* No fragmentation */
#define UIP_CONF_BUFFER_SIZE 200

/* IEEE802.15.4 PANID */
#undef IEEE802154_CONF_PANID
#define IEEE802154_CONF_PANID 0xdada

#ifndef MAIN_GW_ID
#if CONTIKI_TARGET_COOJA
#define MAIN_GW_ID 1
#else
#define MAIN_GW_ID 12385 /* IoT lab in Grenoble, node m3-177 */
#endif
#endif

/* Queue size */
#define QUEUEBUF_CONF_NUM                   8

/* Number of neighbors */
#undef NBR_TABLE_CONF_MAX_NEIGHBORS
#define NBR_TABLE_CONF_MAX_NEIGHBORS        50

/* Number of routes */
#undef UIP_CONF_MAX_ROUTES
#define UIP_CONF_MAX_ROUTES                 50

/* max routes on the root for the non-storing mode */
#undef UIP_SR_CONF_LINK_NUM
#define UIP_SR_CONF_LINK_NUM                UIP_CONF_MAX_ROUTES

/* Enable printing of packet counters */
#define LINK_STATS_CONF_PACKET_COUNTERS          1

#define UDP_PORT	8765

/*******************************************************/
/************* Other system configuration **************/
/*******************************************************/

/* Logging */
#define LOG_CONF_LEVEL_RPL                         LOG_LEVEL_ERR
#define LOG_CONF_LEVEL_TCPIP                       LOG_LEVEL_ERR
#define LOG_CONF_LEVEL_IPV6                        LOG_LEVEL_ERR
#define LOG_CONF_LEVEL_6LOWPAN                     LOG_LEVEL_ERR
#define LOG_CONF_LEVEL_MAC                         LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_FRAMER                      LOG_LEVEL_ERR
#define TSCH_LOG_CONF_PER_SLOT                     0


/*******************************************************/
/******************* Configure TSCH ********************/
/*******************************************************/

/* TSCH and RPL callbacks */
#define RPL_CALLBACK_PARENT_SWITCH tsch_rpl_callback_parent_switch
#define RPL_CALLBACK_NEW_DIO_INTERVAL tsch_rpl_callback_new_dio_interval

/* Do not start TSCH at init, wait for NETSTACK_MAC.on() */
#define TSCH_CONF_AUTOSTART 0

#define TSCH_CONF_ADAPTIVE_TIMESYNC 0

/* Packet timeout after which to leave the network  */
#if CONTIKI_TARGET_COOJA
/* Never desync in the simulator */
#define TSCH_CONF_DESYNC_THRESHOLD (3600 * CLOCK_SECOND)
#else
#define TSCH_CONF_DESYNC_THRESHOLD   (60 * CLOCK_SECOND)
#endif

/* Disable security */
#define USE_TSCH_SECURITY 0

/* disable packet bursts! */
#define TSCH_CONF_BURST_MAX_LEN 0

/* increase the number of links */
#define TSCH_SCHEDULE_CONF_MAX_LINKS 120

/* reduce */
#define TSCH_CONF_MAC_MAX_BE 3

/*******************************************************/
/****************** Firmware Type options **************/
/*******************************************************/

/* sender based, storing Orchestra + RPL */
#define FIRMWARE_TYPE_ORCHESTRA_SB 1
/* receiver based, storing Orchestra + RPL */
#define FIRMWARE_TYPE_ORCHESTRA_RB_S 2
/* receiver based, nonstoring Orchestra, nonstoring RPL */
#define FIRMWARE_TYPE_ORCHESTRA_RB_NS 3
/* receiver based, nonstoring Orchestra, storing RPL */
#define FIRMWARE_TYPE_ORCHESTRA_RB_NS_SR 4
/* link based */
#define FIRMWARE_TYPE_LINK 5
/* MSF (version 03) */
#define FIRMWARE_TYPE_MSF 6
/* extended MSF (modification of the version 03) */
#define FIRMWARE_TYPE_EMSF 7
/* ALICE as implemented by S.Kim */
#define FIRMWARE_TYPE_ALICE 8
/* ALICE with the new multichannel approach  */
#define FIRMWARE_TYPE_ALICE_RX_MULTICHANNNEL 9

/*******************************************************/
/******************* Configure Orchestra ***************/
/*******************************************************/

/* slotframe size */
#ifndef ORCHESTRA_CONF_UNICAST_PERIOD
#define ORCHESTRA_CONF_UNICAST_PERIOD             19
#endif

#define ORCHESTRA_CONF_UNICAST_SENDER_BASED       (FIRMWARE_TYPE == FIRMWARE_TYPE_ORCHESTRA_SB)

/* Enable special rule for root? */
#ifndef ORCHESTRA_CONF_ROOT_RULE
#define ORCHESTRA_CONF_ROOT_RULE 0
#endif

/* Select Orchestra rules depending on the schedule type */
#if FIRMWARE_TYPE == FIRMWARE_TYPE_ORCHESTRA_SB
/* include the storing rule */
#  define FIRMWARE_UNICAST_RULE unicast_per_neighbor_rpl_storing
#elif FIRMWARE_TYPE == FIRMWARE_TYPE_ORCHESTRA_RB_S
/* include the storing rule */
#  define FIRMWARE_UNICAST_RULE unicast_per_neighbor_rpl_storing
#elif FIRMWARE_TYPE == FIRMWARE_TYPE_ORCHESTRA_RB_NS || FIRMWARE_TYPE == FIRMWARE_TYPE_ORCHESTRA_RB_NS_SR
/* include the non-storing rule */
#  define FIRMWARE_UNICAST_RULE unicast_per_neighbor_rpl_ns
#elif FIRMWARE_TYPE == FIRMWARE_TYPE_LINK
/* include the link rule */
#  define FIRMWARE_UNICAST_RULE unicast_link
#elif FIRMWARE_TYPE == FIRMWARE_TYPE_MSF
/* include the msf rule */
#  define FIRMWARE_UNICAST_RULE unicast_msf
#elif FIRMWARE_TYPE == FIRMWARE_TYPE_EMSF
/* include the emsf rule */
#  define FIRMWARE_UNICAST_RULE unicast_emsf
#elif FIRMWARE_TYPE == FIRMWARE_TYPE_ALICE || FIRMWARE_TYPE == FIRMWARE_TYPE_ALICE_RX_MULTICHANNNEL
/* will define its own scheduler */
#endif

/* Enable multiple channels? */
#ifndef ORCHESTRA_CONF_MULTIPLE_CHANNELS
#define ORCHESTRA_CONF_MULTIPLE_CHANNELS 1
#endif

/* If this is enabled, the EBSF rule is prioritized above all */
#ifndef TSCH_CONF_PRIORITIZE_SLOTFRAME_ZERO
#define TSCH_CONF_PRIORITIZE_SLOTFRAME_ZERO 1
#endif

#if FIRMWARE_TYPE != FIRMWARE_TYPE_ALICE && FIRMWARE_TYPE != FIRMWARE_TYPE_ALICE_RX_MULTICHANNNEL
/* For root: the root rule (Rx) comes last */
# define ORCHESTRA_CONF_RULES_ROOT { &eb_per_time_source, &FIRMWARE_UNICAST_RULE, &default_common, &special_for_root }
/* For other nodes: root rule (Tx) comes before the unicast neigbhor rules and the default rule */
# define ORCHESTRA_CONF_RULES_NONROOT { &eb_per_time_source, &special_for_root, &FIRMWARE_UNICAST_RULE, &default_common }

#else /* FIRMWARE_TYPE == FIRMWARE_TYPE_ALICE || FIRMWARE_TYPE == FIRMWARE_TYPE_ALICE_RX_MULTICHANNNEL */

/* KSH: alice implementation */
# define WITH_ALICE   1
# undef ORCHESTRA_CONF_UNICAST_SENDER_BASED
# define ORCHESTRA_CONF_UNICAST_SENDER_BASED 1
# define ALICE_CALLBACK_PACKET_SELECTION alice_callback_packet_selection
# define ALICE_TSCH_CALLBACK_SLOTFRAME_START alice_callback_slotframe_start

# define ORCHESTRA_CONF_RULES { &eb_per_time_source, &default_common , &unicast_per_neighbor_rpl_storing}
# define ALICE_UNICAST_SF_ID 2 //slotframe handle of unicast slotframe
# define ALICE_BROADCAST_SF_ID 1 //slotframe handle of broadcast/default slotframe
# ifndef MULTIPLE_CHANNEL_OFFSETS
#  define MULTIPLE_CHANNEL_OFFSETS 1 //ksh.. allow multiple channel offsets.
# endif

#if FIRMWARE_TYPE == FIRMWARE_TYPE_ALICE_RX_MULTICHANNNEL
#define ALICE_RX_BASED_MULTICHANNEL 1
#endif

#endif /* FIRMWARE_TYPE == FIRMWARE_TYPE_ALICE || FIRMWARE_TYPE == FIRMWARE_TYPE_ALICE_RX_MULTICHANNNEL */

/*******************************************************/
/*************** Configure other settings **************/
/*******************************************************/

#ifndef SEND_INTERVAL_SEC
#define SEND_INTERVAL_SEC 6
#endif

#define WARM_UP_PERIOD_SEC (60 * 30)
