#include "contiki.h"
#include "sys/node-id.h"
#include "sys/log.h"
// #include "net/ipv6/uip-sr.h"
#include "net/ipv6/uip.h"
#include "net/ipv6/uiplib.h"
#include "net/ipv6/uip-ds6.h"
#include "net/mac/tsch/tsch.h"
//#include "net/routing/routing.h"

// #define DEBUG DEBUG_PRINT
// #include "net/ipv6/uip-debug.h"

#if CONTIKI_TARGET_COOJA
#include "node-id-mapping-cooja.h"
#else
#include "node-id-mapping-iot-lab.h"
#endif

/*---------------------------------------------------------------------------*/
static uip_ipaddr_t mcast_addr;
/*---------------------------------------------------------------------------*/
PROCESS(node_process, "PDR test");
AUTOSTART_PROCESSES(&node_process);
/*---------------------------------------------------------------------------*/
static bool
setup_addrs(void)
{
  uip_ipaddr_t ipaddr;
  uip_ds6_addr_t *addr;

  /* add the local address */
  uip_ip6addr(&ipaddr, UIP_DS6_DEFAULT_PREFIX, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0);
  uip_ds6_set_addr_iid(&ipaddr, &uip_lladdr);
  addr = uip_ds6_addr_add(&ipaddr, 0, ADDR_MANUAL);
  if(addr == NULL) {
    printf("initialization failed: failed to add local address!\n");
    return false;
  }

  uip_create_linklocal_allnodes_mcast(&mcast_addr);

  return true;
}
/*---------------------------------------------------------------------------*/
static bool
my_tsch_schedule_init(bool is_coordinator)
{
  struct tsch_slotframe *sf;
  int i;
  int own_id = get_schedule_id(node_id);

  /* First, empty current schedule */
  tsch_schedule_remove_all_slotframes();

  /* Choose slotframe handle 0, set slotframe length to TSCH_SCHEDULE_DEFAULT_LENGTH */
  sf = tsch_schedule_add_slotframe(0, TSCH_SCHEDULE_DEFAULT_LENGTH);

  for(i = 0; i < TSCH_SCHEDULE_DEFAULT_LENGTH; i++) {
    tsch_schedule_add_link(sf,
        i == own_id ? LINK_OPTION_TX : LINK_OPTION_RX,
        LINK_TYPE_ADVERTISING, &tsch_broadcast_address,
        i, 0);
  }

  return true;
}
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(node_process, ev, data)
{
  bool is_coordinator;

  PROCESS_BEGIN();

  setup_addrs();

  if(get_schedule_id(node_id) == SCHEDULE_ID_COORDINATOR) {
    is_coordinator = true;
  } else {
    is_coordinator = false;
  }

  my_tsch_schedule_init(is_coordinator);

  tsch_set_coordinator(is_coordinator);

  NETSTACK_MAC.on();

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
