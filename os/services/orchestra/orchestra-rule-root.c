/* -*- c -*- */
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
 *         Orchestra: a slotframe dedicated to unicast data transmission.
 *         Root node listens to every slot.
 *         Nodes directly connected to root transmit at a timeslot defined as hash(MAC) % ORCHESTRA_ROOT_PERIOD
 *         This slotframe has priority lower than that of all other slotframes.
 *
 * \author Atis Elsts <atis.elsts@edi.lv>
 */

#include "contiki.h"
#include "orchestra.h"
#include "net/ipv6/uip-ds6-route.h"
#include "net/packetbuf.h"

#if ORCHESTRA_ROOT_RULE

static uint16_t slotframe_handle = 0;
static uint16_t channel_offset = 0;
static struct tsch_slotframe *sf_unicast;

/*---------------------------------------------------------------------------*/
static uint16_t
get_node_timeslot(const linkaddr_t *addr)
{
  if(addr != NULL && ORCHESTRA_ROOT_PERIOD > 0) {
    return ORCHESTRA_LINKADDR_HASH(addr) % ORCHESTRA_ROOT_PERIOD;
  } else {
    return 0xffff;
  }
}
/*---------------------------------------------------------------------------*/
static int
select_packet(uint16_t *slotframe, uint16_t *timeslot)
{
  /* Select data packets we have a unicast link to */
  const linkaddr_t *dest = packetbuf_addr(PACKETBUF_ADDR_RECEIVER);
  if(packetbuf_attr(PACKETBUF_ATTR_FRAME_TYPE) == FRAME802154_DATAFRAME
     && !ORCHESTRA_IS_ROOT()
     && linkaddr_cmp(dest, &orchestra_linkaddr_root)) {
    if(slotframe != NULL) {
      *slotframe = slotframe_handle;
    }
    if(timeslot != NULL) {
      *timeslot = get_node_timeslot(dest);
    }
    return 1;
  }
  return 0;
}
/*---------------------------------------------------------------------------*/
static void
init(uint16_t sf_handle)
{
  int i;
  uint16_t timeslot;

  slotframe_handle = sf_handle | TSCH_LOW_PRIO_SLOTFRAME_FLAG;
  channel_offset = sf_handle;

  if(ORCHESTRA_IS_ROOT()) {
    /* Slotframe for unicast reception */
    sf_unicast = tsch_schedule_add_slotframe(slotframe_handle, 1);
    timeslot = 0;
    tsch_schedule_add_link(sf_unicast,
        LINK_OPTION_SHARED | LINK_OPTION_RX,
        LINK_TYPE_NORMAL, &tsch_broadcast_address,
        timeslot, channel_offset);
  } else {
    /* Slotframe for unicast transmissions */
    sf_unicast = tsch_schedule_add_slotframe(slotframe_handle, ORCHESTRA_ROOT_PERIOD);
    timeslot = get_node_timeslot(&linkaddr_node_addr);
    tsch_schedule_add_link(sf_unicast,
        LINK_OPTION_SHARED | LINK_OPTION_TX,
        LINK_TYPE_NORMAL, &tsch_broadcast_address,
        timeslot, channel_offset);
  }
}
/*---------------------------------------------------------------------------*/
struct orchestra_rule unicast_special_for_root = {
  init,
  NULL,
  select_packet,
  NULL,
  NULL,
  "special for root"
};

#endif /* ORCHESTRA_ROOT_RULE */
