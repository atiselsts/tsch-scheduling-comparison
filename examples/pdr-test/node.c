#include "contiki.h"
#include "sys/node-id.h"
#include "sys/log.h"
#include "net/ipv6/uip.h"
#include "net/ipv6/uiplib.h"
#include "net/ipv6/uip-ds6.h"
#include "net/mac/tsch/tsch.h"

#if CONTIKI_TARGET_COOJA
#include "node-id-mapping-cooja.h"
#else
#include "node-id-mapping-iot-lab.h"
#endif

/*---------------------------------------------------------------------------*/
static uint16_t packets_rxed[NUM_NODES + 1];

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
        LINK_TYPE_ADVERTISING_ONLY, &tsch_broadcast_address,
        i, 0);
  }

  return true;
}
/*---------------------------------------------------------------------------*/
static void
schedule_packets(void)
{
  int i;

  printf("schedule packets\n");

  for(i = 0; i < NUM_PACKETS_TO_SEND; ++i) {
    if(tsch_send_eb() == 0) {
      /* printf("queue EB %u\n", i); */
    } else {
      printf("!failed to queue EB %u\n", i);
      break;
    }
  }
}
/*---------------------------------------------------------------------------*/
void
app_eb_input(const linkaddr_t *src)
{
  uint16_t src_node_id = (src->u8[6] << 8) + src->u8[7];
  uint16_t src_id = get_schedule_id(src_node_id);
  /* printf(" packet from %u\n", src_id); */

  if(src_id <= NUM_NODES) {
    packets_rxed[src_id]++;
  }
}
/*---------------------------------------------------------------------------*/
static void
print_stats(void)
{
  int i;
  printf("print stats\n");
  for(i = 1; i <= NUM_NODES; ++i) {
    printf("%u: %u\n", i, packets_rxed[i]);
  }
  memset(packets_rxed, 0, sizeof(packets_rxed));
}
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(node_process, ev, data)
{
  bool is_coordinator;
  static struct etimer full_et;
  static struct etimer send_et;

  PROCESS_BEGIN();

  printf("round full duration: %u sec, send duration: %u\n",
      ROUND_FULL_DURATION / CLOCK_SECOND,
      ROUND_SEND_DURATION / CLOCK_SECOND);

  setup_addrs();

  printf("schedule ID is %u\n", get_schedule_id(node_id));

  if(get_schedule_id(node_id) == SCHEDULE_ID_COORDINATOR) {
    is_coordinator = true;
  } else {
    is_coordinator = false;
  }

  my_tsch_schedule_init(is_coordinator);

  tsch_set_coordinator(is_coordinator);

  NETSTACK_MAC.on();

  schedule_packets();
  etimer_set(&full_et, ROUND_FULL_DURATION);

  while(1) {
    PROCESS_YIELD_UNTIL(etimer_expired(&full_et));
    etimer_reset(&full_et);

    schedule_packets();
    etimer_set(&send_et, ROUND_SEND_DURATION - CLOCK_SECOND);
    PROCESS_YIELD_UNTIL(etimer_expired(&send_et));

    etimer_set(&send_et, CLOCK_SECOND);
    PROCESS_YIELD_UNTIL(etimer_expired(&send_et));
    print_stats();
  }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
