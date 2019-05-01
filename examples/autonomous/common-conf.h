#include <stdint.h>

/*******************************************************/
/******************* Configure network stack ***********/
/*******************************************************/

#define SICSLOWPAN_CONF_FRAG 0 /* No fragmentation */
#define UIP_CONF_BUFFER_SIZE 200

/* IEEE802.15.4 PANID */
#undef IEEE802154_CONF_PANID
#define IEEE802154_CONF_PANID 0xdada

#ifndef MAIN_GW_ID
#define MAIN_GW_ID 1
#endif

/* Queue size */
#define QUEUEBUF_CONF_NUM                   8

/* Number of neighbors */
#undef NBR_TABLE_CONF_MAX_NEIGHBORS
#define NBR_TABLE_CONF_MAX_NEIGHBORS        50

/* Number of routes */
#undef UIP_CONF_MAX_ROUTES
#define UIP_CONF_MAX_ROUTES                 50

/* Enable printing of packet counters */
#define LINK_STATS_CONF_PACKET_COUNTERS          1

/*******************************************************/
/************* Other system configuration **************/
/*******************************************************/

/* Logging */
#define LOG_CONF_LEVEL_RPL                         LOG_LEVEL_ERR
#define LOG_CONF_LEVEL_TCPIP                       LOG_LEVEL_ERR
#define LOG_CONF_LEVEL_IPV6                        LOG_LEVEL_ERR
#define LOG_CONF_LEVEL_6LOWPAN                     LOG_LEVEL_ERR
#define LOG_CONF_LEVEL_MAC                         LOG_LEVEL_ERR
#define LOG_CONF_LEVEL_FRAMER                      LOG_LEVEL_ERR
#define TSCH_LOG_CONF_PER_SLOT                     0


/*******************************************************/
/******************* Configure TSCH ********************/
/*******************************************************/

/* TSCH and RPL callbacks */
#define RPL_CALLBACK_PARENT_SWITCH tsch_rpl_callback_parent_switch
#define RPL_CALLBACK_NEW_DIO_INTERVAL tsch_rpl_callback_new_dio_interval

/* TSCH slotframe size */
#ifndef TSCH_SCHEDULE_CONF_DEFAULT_LENGTH
#define TSCH_SCHEDULE_CONF_DEFAULT_LENGTH 17
#endif

/* Do not start TSCH at init, wait for NETSTACK_MAC.on() */
#define TSCH_CONF_AUTOSTART 0

//#define TSCH_CONF_INIT_SCHEDULE_FROM_EB 0

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

/* sender based, storing */
#define FIRMWARE_TYPE_ORCHESTRA_SB 1
/* receiver based, storing */
#define FIRMWARE_TYPE_ORCHESTRA_RB_S 2
/* receiver based, nonstoring (this is the default in contiki ng) */
#define FIRMWARE_TYPE_ORCHESTRA_RB_NS 3
/* in the future - when implemented */
#define FIRMWARE_TYPE_ALICE 4
/* in the future - when implemented */
#define FIRMWARE_TYPE_MSF 5

/*******************************************************/
/******************* Configure Orchestra ***************/
/*******************************************************/

#define ORCHESTRA_CONF_UNICAST_PERIOD             17

#define ORCHESTRA_CONF_UNICAST_SENDER_BASED       (FIRMWARE_TYPE == FIRMWARE_TYPE_ORCHESTRA_SB)

/* Select Orchestra rules depending on the schedule type */
#if FIRMWARE_TYPE == FIRMWARE_TYPE_ORCHESTRA_SB || FIRMWARE_TYPE == FIRMWARE_TYPE_ORCHESTRA_RB_S
/* include the storing rule */
#  define ORCHESTRA_CONF_RULES { &eb_per_time_source, &unicast_per_neighbor_rpl_storing, &default_common }
#elif FIRMWARE_TYPE == FIRMWARE_TYPE_ORCHESTRA_RB_NS
/* include the non-storing rule */
#  define ORCHESTRA_CONF_RULES { &eb_per_time_source, &unicast_per_neighbor_rpl_ns, &default_common }
#elif FIRMWARE_TYPE == FIRMWARE_TYPE_ALICE
#  error "Implement me!"
#elif FIRMWARE_TYPE == FIRMWARE_TYPE_MSF
#  error "Implement me!"
#endif
