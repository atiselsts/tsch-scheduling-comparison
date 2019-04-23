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

/*******************************************************/
/******************* Configure TSCH ********************/
/*******************************************************/

/* TSCH and RPL callbacks */
#define RPL_CALLBACK_PARENT_SWITCH tsch_rpl_callback_parent_switch
#define RPL_CALLBACK_NEW_DIO_INTERVAL tsch_rpl_callback_new_dio_interval

/* Custom schedule, not 6TiSCH minimal */
#define TSCH_SCHEDULE_CONF_WITH_6TISCH_MINIMAL 1

/* TSCH slotframe size */
#ifndef TSCH_SCHEDULE_CONF_DEFAULT_LENGTH
#define TSCH_SCHEDULE_CONF_DEFAULT_LENGTH 11
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

/*******************************************************/
/************* Other system configuration **************/
/*******************************************************/

/* Logging */
#define LOG_CONF_LEVEL_RPL                         LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_TCPIP                       LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_IPV6                        LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_6LOWPAN                     LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_MAC                         LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_FRAMER                      LOG_LEVEL_WARN
#define TSCH_LOG_CONF_PER_SLOT                     0
