/*
 * Data query test.
 * The root issues periodic query messages to all of the nodes in the routing table.
 * The query messages are sent one after another, with a second in-between for different nodes.
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

#define UDP_PORT	8765

#define WARM_UP_TIME    (1 * 60 * CLOCK_SECOND)

/* Note: the max number of nodes that can be queried is equal to MAIN_INTERVAL / QUERY_INTERVAL == 60 */
#define MAIN_INTERVAL   (60 * CLOCK_SECOND)
#define QUERY_INTERVAL  (CLOCK_SECOND)

/*---------------------------------------------------------------------------*/
static struct simple_udp_connection udp_conn;

extern uip_ipaddr_t network_nodes_with_routes[];
extern unsigned num_network_nodes_with_routes;
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

  if(node_id != MAIN_GW_ID) {
    /* simply send back the same data to the sender */
    simple_udp_sendto(&udp_conn, &seqnum, sizeof(seqnum), sender_addr);
  }
}
/*---------------------------------------------------------------------------*/
PROCESS(node_process, "Node");
AUTOSTART_PROCESSES(&node_process);
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(node_process, ev, data)
{
  static struct etimer periodic_timer;
  static struct etimer query_timer;
  static uint32_t seqnum;
  static unsigned int last_queried_id = -1u;

  PROCESS_BEGIN();

  printf("FIRMWARE_TYPE=%u\n", FIRMWARE_TYPE);

  simple_udp_register(&udp_conn, UDP_PORT, NULL,
                      UDP_PORT, udp_rx_callback);

  if(node_id == MAIN_GW_ID) {
    /* RPL root automatically becomes coordinator */  
    LOG_INFO("set as root\n");
    NETSTACK_ROUTING.root_start();
  }

  /* start TSCH */
  NETSTACK_MAC.on();

  LOG_INFO("exp-query node started\n");

  if(node_id == MAIN_GW_ID) {
    /* start the queries */
    etimer_set(&periodic_timer, WARM_UP_TIME);

    while(1) {
      PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&periodic_timer) || etimer_expired(&query_timer));

      if(etimer_expired(&periodic_timer)) {
        /* update the seqnum */
        seqnum++;

        /* reset the interval and query timers */
        etimer_set(&periodic_timer, MAIN_INTERVAL);
        etimer_set(&query_timer, QUERY_INTERVAL);
      }

      if(etimer_expired(&query_timer)) {
        /* find the first / next route */
        last_queried_id++;
        if(last_queried_id < num_network_nodes_with_routes) {
          uip_ipaddr_t *addr = &network_nodes_with_routes[last_queried_id];
          simple_udp_sendto(&udp_conn, &seqnum, sizeof(seqnum), addr);
          LOG_INFO("seqnum=%" PRIu32 " to=", seqnum);
          LOG_INFO_6ADDR(addr);
          LOG_INFO_("\n");
          /* reset the query timer */
          etimer_set(&query_timer, QUERY_INTERVAL);
        } else {
          last_queried_id = -1u;
        }
      }
    }
  }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
