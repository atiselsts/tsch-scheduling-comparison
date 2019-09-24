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
#define NUM_CHANNELS 16
#define FIRST_CHANNEL 11

/*---------------------------------------------------------------------------*/
static uint16_t packets_rxed[NUM_NODES][NUM_CHANNELS];

/*---------------------------------------------------------------------------*/
PROCESS(node_process, "Link quality test");
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
my_tsch_schedule_init(void)
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

  printf("schedule %u packets...\n", NUM_PACKETS_PER_CHANNEL * NUM_ACTIVE_CHANNELS);

  for(i = 0; i < NUM_PACKETS_PER_CHANNEL * NUM_ACTIVE_CHANNELS; ++i) {
    if(tsch_send_eb() == 0) {
      /* printf("queue EB %u\n", i); */
    } else {
      printf("!failed to queue EB %u\n", i);
      break;
    }
  }
  printf("..done\n");
}
/*---------------------------------------------------------------------------*/
int
link_quality_test_packet_callback(void)
{
  /* allow EBs, drop all other packets */
  return packetbuf_attr(PACKETBUF_ATTR_FRAME_TYPE) == FRAME802154_BEACONFRAME ? 0 : -1;
}
/*---------------------------------------------------------------------------*/
void
app_eb_input(const linkaddr_t *src, uint8_t channel)
{
  uint16_t src_node_id = (src->u8[6] << 8) + src->u8[7];
  uint16_t src_id = get_schedule_id(src_node_id) - 1;
  /* printf(" packet from %u\n", src_id); */

  channel -= FIRST_CHANNEL;

  if(src_id < NUM_NODES && channel < NUM_CHANNELS) {
    packets_rxed[src_id][channel]++;
  }
}
/*---------------------------------------------------------------------------*/
static void
print_stats(void)
{
  int i, j;

  printf("packet statistics: %u expected per node, %u per channel\n",
         NUM_PACKETS_PER_CHANNEL * NUM_ACTIVE_CHANNELS, NUM_PACKETS_PER_CHANNEL);
  for(i = 0; i < NUM_NODES; ++i) {
    uint16_t total = 0;
    printf("%u:\n", i + 1);
    for(j = 0; j < NUM_CHANNELS; ++j) {
      if(packets_rxed[i][j]) {
        printf("  ch %u: %u\n", j + FIRST_CHANNEL, packets_rxed[i][j]);
        total += packets_rxed[i][j];
      }
    }
    printf("  %u total\n", total);
  }
  memset(packets_rxed, 0, sizeof(packets_rxed));
}
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(node_process, ev, data)
{
  static struct etimer full_et;
  static struct etimer send_et;

  PROCESS_BEGIN();

  printf("schedule ID is %u\n", get_schedule_id(node_id));
  printf("round full duration: %u sec, send duration: %u\n",
         ROUND_FULL_DURATION / CLOCK_SECOND,
         ROUND_SEND_DURATION / CLOCK_SECOND);

  setup_addrs();

  my_tsch_schedule_init();

  tsch_set_coordinator(get_schedule_id(node_id) == SCHEDULE_ID_COORDINATOR);

  NETSTACK_MAC.on();

  schedule_packets();
  etimer_set(&full_et, ROUND_FULL_DURATION);

  while(1) {
    PROCESS_YIELD_UNTIL(etimer_expired(&full_et));
    etimer_reset(&full_et);

    schedule_packets();
    etimer_set(&send_et, ROUND_SEND_DURATION - 2 * CLOCK_SECOND);
    PROCESS_YIELD_UNTIL(etimer_expired(&send_et));

    etimer_set(&send_et, 2 * CLOCK_SECOND);
    PROCESS_YIELD_UNTIL(etimer_expired(&send_et));
    print_stats();
  }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
