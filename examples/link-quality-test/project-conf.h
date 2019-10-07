#ifndef PROJECT_CONF_H_
#define PROJECT_CONF_H_

#include <stdint.h>
#include <stdbool.h>

#define IEEE802154_CONF_PANID 0x1515
#define TSCH_CONF_AUTOSTART 0
#define TSCH_SCHEDULE_CONF_WITH_6TISCH_MINIMAL 0
#define TSCH_SCHEDULE_CONF_DEFAULT_LENGTH 37  /* 71 */
#define TSCH_SCHEDULE_CONF_MAX_LINKS (TSCH_SCHEDULE_CONF_DEFAULT_LENGTH + 10)

#define TSCH_CONF_EB_PERIOD 0
#define TSCH_CONF_MAX_EB_PERIOD 0

/* Logging */
#define LOG_CONF_LEVEL_RPL                         LOG_LEVEL_INFO
#define LOG_CONF_LEVEL_TCPIP                       LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_IPV6                        LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_6LOWPAN                     LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_MAC                         LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_FRAMER                      LOG_LEVEL_WARN
#define TSCH_LOG_CONF_PER_SLOT                     0

#define SCHEDULE_ID_COORDINATOR 1

/* ------------------------------------------------------- */
/* Application config */
/* ------------------------------------------------------- */

#define NUM_ACTIVE_CHANNELS     4

#define NUM_PACKETS_PER_CHANNEL 10
#define QUEUEBUF_CONF_NUM       128 /* must be at least the number of packets to send + 1 */

#define MAX_NUM_NODES           32  /* must be <=  TSCH_SCHEDULE_CONF_DEFAULT_LENGTH and the actual node count + 1 */
#define SLOTS_PER_SECOND        100

#define NODE_SEND_DURATION_SLOTS  (NUM_PACKETS_PER_CHANNEL * NUM_ACTIVE_CHANNELS * TSCH_SCHEDULE_CONF_DEFAULT_LENGTH)
#define ROUND_SEND_DURATION  ((NODE_SEND_DURATION_SLOTS * CLOCK_SECOND + SLOTS_PER_SECOND - 1) / SLOTS_PER_SECOND + 2 * CLOCK_SECOND)
#define ROUND_FULL_DURATION  (ROUND_SEND_DURATION + 4 * CLOCK_SECOND)

#define TSCH_EB_INPUT_CALLBACK app_eb_input

/* disable keepalives and leaving the network (at least in short timescale) */
#define TSCH_CONF_KEEPALIVE_TIMEOUT (1000 * CLOCK_SECOND)
#define TSCH_CONF_MAX_KEEPALIVE_TIMEOUT (1000 * CLOCK_SECOND)

/* reduce tx power in the IoT lab testbed */
/* #define RF2XX_TX_POWER  PHY_POWER_m30dBm */

#define TSCH_CALLBACK_PACKET_READY link_quality_test_packet_callback

/* ------------------------------------------------------- */

#endif /* PROJECT_CONF_H_ */
