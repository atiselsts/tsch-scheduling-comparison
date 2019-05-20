/*
 * Copyright (c) 2019, Institute of Electronics and Computer Science (EDI)
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the Institute nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE INSTITUTE AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE INSTITUTE OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 */
/**
 * \file
 *         Orchestra: a slotframe dedicated to unicast data transmission. Designed for
 *         RPL storing mode only, as this is based on the knowledge of the children (and parent).
 *         Communication to children:
 *           Nodes listen at a timeslot defined as hash(MAC)
 *           Nodes transmit at a timeslot defined as hash(MAC)+ ORCHESTRA_SB_UNICAST_PERIOD / 2
 *         Communication to parent:
 *           Nodes listen at a timeslot defined as hash(parent.MAC) + ORCHESTRA_SB_UNICAST_PERIOD / 2
 *           Nodes transmit at a timeslot defined as hash(parent.MAC)
 *
 * \author Atis Elsts <atis.elsts@edi.lv>
 */

#include "contiki.h"
#include "orchestra.h"
#include "net/ipv6/uip-ds6-route.h"
#include "net/packetbuf.h"
#include "net/routing/routing.h"

static uint16_t slotframe_handle = 0;
static uint16_t channel_offset = 0;
static struct tsch_slotframe *sf_unicast;

static bool is_parent;

/*---------------------------------------------------------------------------*/
static uint16_t
get_node_timeslot(const linkaddr_t *addr)
{
  if(addr != NULL && ORCHESTRA_UNICAST_PERIOD > 0) {
    return ORCHESTRA_LINKADDR_HASH(addr) % ORCHESTRA_UNICAST_PERIOD;
  } else {
    return 0xffff;
  }
}
/*---------------------------------------------------------------------------*/
static void
add_uc_link(const linkaddr_t *linkaddr)
{
  if(linkaddr != NULL) {
    const uint16_t timeslot = get_node_timeslot(linkaddr);
    const uint8_t link_options = LINK_OPTION_RX | LINK_OPTION_TX | LINK_OPTION_SHARED;

    /* Add/update link (for Rx only) */
    tsch_schedule_add_link(sf_unicast, link_options, LINK_TYPE_NORMAL, &tsch_broadcast_address,
                           timeslot, channel_offset);
  }
}
/*---------------------------------------------------------------------------*/
static void
remove_uc_link(const linkaddr_t *linkaddr)
{
  if(linkaddr != NULL) {
    const uint16_t timeslot = get_node_timeslot(linkaddr);
    uint8_t link_options = LINK_OPTION_TX | LINK_OPTION_SHARED;
    uint16_t own_timeslot = get_node_timeslot(&linkaddr_node_addr);

    if(timeslot == own_timeslot) {
      /* we need this timeslot */
      link_options |= LINK_OPTION_RX;
    } else if(is_parent) {
      if(timeslot == (own_timeslot + ORCHESTRA_UNICAST_PERIOD / 2) % ORCHESTRA_UNICAST_PERIOD) {
        /* we need this timeslot */
        link_options |= LINK_OPTION_RX;
      }
    }

    /* Add/update link */
    tsch_schedule_add_link(sf_unicast, link_options, LINK_TYPE_NORMAL, &tsch_broadcast_address,
                           timeslot, channel_offset);
  }
}
/*---------------------------------------------------------------------------*/
static int
select_packet(uint16_t *slotframe, uint16_t *timeslot)
{
  /* Select data packets we have a unicast link to */
  const linkaddr_t *dest = packetbuf_addr(PACKETBUF_ADDR_RECEIVER);
  if(packetbuf_attr(PACKETBUF_ATTR_FRAME_TYPE) != FRAME802154_DATAFRAME
      || dest == NULL
      || linkaddr_cmp(dest, &linkaddr_null)
      || linkaddr_cmp(dest, &tsch_broadcast_address)) {
    return 0;
  }

  if(slotframe != NULL) {
    *slotframe = slotframe_handle;
  }

  /* handle the child case (valid for storing mode only) */
  if(nbr_table_get_from_lladdr(nbr_routes, (linkaddr_t *)dest) != NULL) {
    if(timeslot != NULL) {
      /* select the timeslot of the local node */
      *timeslot = get_node_timeslot(&linkaddr_node_addr);
    }
    return 1;
  }

  if(orchestra_parent_knows_us && linkaddr_cmp(&orchestra_parent_linkaddr, dest)) {
    /* select the timeslot of the remote node */
    *timeslot = (get_node_timeslot(dest) + ORCHESTRA_UNICAST_PERIOD / 2) % ORCHESTRA_UNICAST_PERIOD;
    return 1;
  }

  /* handle the case of other nodes (including parent) */
  if(timeslot != NULL) {
    /* select the timeslot of the remote node */
    *timeslot = get_node_timeslot(dest);
  }
  return 1;
}
/*---------------------------------------------------------------------------*/
static void
new_time_source(const struct tsch_neighbor *old, const struct tsch_neighbor *new)
{
  if(new != old) {
    const linkaddr_t *old_addr = old != NULL ? &old->addr : NULL;
    const linkaddr_t *new_addr = new != NULL ? &new->addr : NULL;
    if(new_addr != NULL) {
      linkaddr_copy(&orchestra_parent_linkaddr, new_addr);
    } else {
      linkaddr_copy(&orchestra_parent_linkaddr, &linkaddr_null);
    }
    remove_uc_link(old_addr);
    add_uc_link(new_addr);
  }
}
/*---------------------------------------------------------------------------*/
static void
add_child(const linkaddr_t *linkaddr)
{
  if(!is_parent) {
    uint16_t timeslot;
    is_parent = 1;

    timeslot = (get_node_timeslot(&linkaddr_node_addr) + ORCHESTRA_UNICAST_PERIOD / 2) % ORCHESTRA_UNICAST_PERIOD;
    tsch_schedule_add_link(sf_unicast,
        LINK_OPTION_SHARED | LINK_OPTION_TX | LINK_OPTION_RX,
        LINK_TYPE_NORMAL, &tsch_broadcast_address,
        timeslot, channel_offset);
  }
}
/*---------------------------------------------------------------------------*/
static void
remove_child(const linkaddr_t *linkaddr)
{
  if(uip_ds6_route_num_routes() == 0) {
    uint16_t timeslot;
    is_parent = 0;

    timeslot = (get_node_timeslot(&linkaddr_node_addr) + ORCHESTRA_UNICAST_PERIOD / 2) % ORCHESTRA_UNICAST_PERIOD;
    // if(timeslot == get_node_timeslot(&linkaddr_node_addr)) {
    //   return;
    // }
    // if(!linkaddr_cmp(&orchestra_parent_linkaddr, &linkaddr_null)) {
    //   if(timeslot == get_node_timeslot(&orchestra_parent_linkaddr)) {
    //     return;
    //   }
    // }
    tsch_schedule_add_link(sf_unicast,
        LINK_OPTION_SHARED | LINK_OPTION_TX,
        LINK_TYPE_NORMAL, &tsch_broadcast_address,
        timeslot, channel_offset);
  }
}
/*---------------------------------------------------------------------------*/
static void
init(uint16_t sf_handle)
{
  int i;
  uint16_t own_timeslot;

  slotframe_handle = sf_handle;
  channel_offset = sf_handle;
  /* Slotframe for unicast transmissions */
  sf_unicast = tsch_schedule_add_slotframe(slotframe_handle, ORCHESTRA_UNICAST_PERIOD);
  own_timeslot = get_node_timeslot(&linkaddr_node_addr);
  /* Add a Tx link at each available timeslot. Make the link Rx at our own timeslot. */
  for(i = 0; i < ORCHESTRA_UNICAST_PERIOD; i++) {
    tsch_schedule_add_link(sf_unicast,
        LINK_OPTION_SHARED | LINK_OPTION_TX |
           ( i == own_timeslot ? LINK_OPTION_RX : 0 ),
        LINK_TYPE_NORMAL, &tsch_broadcast_address,
        i, channel_offset);
  }
}
/*---------------------------------------------------------------------------*/
struct orchestra_rule unicast_emsf = {
  init,
  new_time_source,
  select_packet,
  add_child,
  remove_child,
  "unicast EMSF"
};
