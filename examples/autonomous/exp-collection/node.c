/*
 * Data collection test.
 * Nodes periodically generate traffic, the root collects it.
 */
#include "contiki.h"
#include "node-id.h"
#include "random.h"
#include "net/ipv6/uip-ds6.h"
#include "net/ipv6/simple-udp.h"
#include "net/routing/routing.h"

#include "sys/log.h"
#define LOG_MODULE "Node"
#define LOG_LEVEL LOG_LEVEL_INFO

/*---------------------------------------------------------------------------*/
static struct simple_udp_connection udp_conn;
static uip_ipaddr_t anycast_address;
/*---------------------------------------------------------------------------*/
static void
udp_rx_callback(struct simple_udp_connection *c,
         const uip_ipaddr_t *sender_addr,
         uint16_t sender_port,
         const uip_ipaddr_t *receiver_addr,
         uint16_t receiver_port,
         const uint8_t *data,
         uint16_t datalen)
{
  uint32_t seqnum;
  memcpy(&seqnum, data, sizeof(seqnum));
  LOG_INFO("seqnum=%" PRIu32 " from=", seqnum);
  LOG_INFO_6ADDR(sender_addr);
  LOG_INFO_("\n");
}
/*---------------------------------------------------------------------------*/
PROCESS(node_process, "Node");
AUTOSTART_PROCESSES(&node_process);
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(node_process, ev, data)
{
  static struct etimer periodic_timer;
  static uint32_t seqnum;

  PROCESS_BEGIN();

  printf("FIRMWARE_TYPE=%u\n", FIRMWARE_TYPE);
  printf("ORCHESTRA_CONF_UNICAST_PERIOD=%u\n", ORCHESTRA_CONF_UNICAST_PERIOD);
  printf("SEND_INTERVAL_SEC=%u\n", SEND_INTERVAL_SEC);

  uip_ip6addr(&anycast_address, UIP_DS6_DEFAULT_PREFIX, 0x0, 0x0, 0x0, 0x1, 0x2, 0x3, 0x4);

  simple_udp_register(&udp_conn, UDP_PORT, NULL,
                      UDP_PORT, udp_rx_callback);

  if(node_id == MAIN_GW_ID) {
    uip_ds6_addr_t *addr;

    /* Add the local anycast address */
    addr = uip_ds6_addr_add(&anycast_address, 0, ADDR_MANUAL);
    if(addr == NULL) {
      LOG_ERR("***  initialization: failed to add local anycast address!\n");
    }

    /* RPL root automatically becomes coordinator */  
    LOG_INFO("set as root\n");
    NETSTACK_ROUTING.root_start();
  }

  /* start TSCH */
  NETSTACK_MAC.on();

  LOG_INFO("collection-exp node started\n");

  etimer_set(&periodic_timer, WARM_UP_PERIOD_SEC * CLOCK_SECOND + random_rand() % (SEND_INTERVAL_SEC * CLOCK_SECOND));
  while(1) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&periodic_timer));

    if(node_id != MAIN_GW_ID) {
      seqnum++;
      simple_udp_sendto(&udp_conn, &seqnum, sizeof(seqnum), &anycast_address);
    }

    etimer_set(&periodic_timer, SEND_INTERVAL_SEC * CLOCK_SECOND);
  }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
