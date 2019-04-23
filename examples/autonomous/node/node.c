#include "contiki.h"
#include "node-id.h"
#include "sys/log.h"
#include "tsch.h"
#include "random.h"
#include "net/ipv6/uip-ds6.h"
#include "net/ipv6/uip-ds6-route.h"
#include "net/routing/routing.h"
#include "net/ipv6/simple-udp.h"

#include "sys/log.h"
#define LOG_MODULE "Node"
#define LOG_LEVEL LOG_LEVEL_INFO

#define UDP_CLIENT_PORT	8765
#define UDP_SERVER_PORT	5678

#define SEND_INTERVAL   (60 * CLOCK_SECOND)

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
void
print_network_status(void)
{
  int i;
  uint8_t state;
  uip_ds6_defrt_t *default_route;
  uip_ds6_route_t *route;

  LOG_INFO("--- Network status ---\n");

  /* Our IPv6 addresses */
  LOG_INFO("-- Server IPv6 addresses:\n");
  for(i = 0; i < UIP_DS6_ADDR_NB; i++) {
    state = uip_ds6_if.addr_list[i].state;
    if(uip_ds6_if.addr_list[i].isused &&
       (state == ADDR_TENTATIVE || state == ADDR_PREFERRED)) {
      LOG_INFO("-- ");
      LOG_INFO_6ADDR(&uip_ds6_if.addr_list[i].ipaddr);
      LOG_INFO_("\n");
    }
  }

  /* Our default route */
  LOG_INFO("-- Default route:\n");
  default_route = uip_ds6_defrt_lookup(uip_ds6_defrt_choose());
  if(default_route != NULL) {
    LOG_INFO("-- ");
    LOG_INFO_6ADDR(&default_route->ipaddr);
    LOG_INFO(" (lifetime: %lu seconds)\n", (unsigned long)default_route->lifetime.interval);
  } else {
    LOG_INFO("-- None\n");
  }

  /* Our routing entries */
  LOG_INFO("-- Routing entries (%u in total):\n", uip_ds6_route_num_routes());
  route = uip_ds6_route_head();
  while(route != NULL) {
    LOG_INFO("-- ");
    LOG_INFO_6ADDR(&route->ipaddr);
    LOG_INFO_(" via ");
    LOG_INFO_6ADDR(uip_ds6_route_nexthop(route));
    LOG_INFO_(" (lifetime: %lu seconds)\n", (unsigned long)route->state.lifetime);
    route = uip_ds6_route_next(route);
  }

  LOG_INFO("----------------------\n");
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

  /* Initialize UDP connection */
  simple_udp_register(&udp_conn, UDP_CLIENT_PORT, NULL,
                      UDP_SERVER_PORT, udp_rx_callback);

  /* uip_ip6addr(&ipaddr, INSTANT_NETWORK_PREFIX, 0, 0, 0, 0, 0, 0, 0); */
  /* uip_ds6_set_addr_iid(&ipaddr, &uip_lladdr); */
  /* uip_ds6_addr_add(&ipaddr, 0, ADDR_AUTOCONF); */

  /* instant_init(); */

  uip_ip6addr(&anycast_address, UIP_DS6_DEFAULT_PREFIX, 0x0, 0x0, 0x0, 0x1, 0x2, 0x3, 0x4);

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

  LOG_INFO("node started\n");

  etimer_set(&periodic_timer, random_rand() % SEND_INTERVAL);
  while(1) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&periodic_timer));

    seqnum++;
    simple_udp_sendto(&udp_conn, &seqnum, sizeof(seqnum), &anycast_address);

    etimer_set(&periodic_timer, SEND_INTERVAL);
  }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
