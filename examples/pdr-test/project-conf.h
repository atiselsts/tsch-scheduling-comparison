#ifndef PROJECT_CONF_H_
#define PROJECT_CONF_H_

#include <stdint.h>
#include <stdbool.h>

#define SICSLOWPAN_CONF_FRAG 0
#define UIP_CONF_BUFFER_SIZE 160

#define IEEE802154_CONF_PANID 0x81a5
#define TSCH_CONF_AUTOSTART 0
#define TSCH_SCHEDULE_CONF_WITH_6TISCH_MINIMAL 0
#define TSCH_SCHEDULE_CONF_DEFAULT_LENGTH 71
#define TSCH_SCHEDULE_CONF_MAX_LINKS (TSCH_SCHEDULE_CONF_DEFAULT_LENGTH + 10)

/* Logging */
#define LOG_CONF_LEVEL_RPL                         LOG_LEVEL_INFO
#define LOG_CONF_LEVEL_TCPIP                       LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_IPV6                        LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_6LOWPAN                     LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_MAC                         LOG_LEVEL_INFO
#define LOG_CONF_LEVEL_FRAMER                      LOG_LEVEL_DBG
#define TSCH_LOG_CONF_PER_SLOT                     1

#define SCHEDULE_ID_COORDINATOR 1

#endif /* PROJECT_CONF_H_ */
