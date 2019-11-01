/*
 * Copyright (c) 2015, Swedish Institute of Computer Science.
 * All rights reserved.
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
 *         If receiver-based:
 *           Nodes listen at a timeslot defined as hash(MAC) % ORCHESTRA_SB_UNICAST_PERIOD
 *           Nodes transmit at: for each nbr in RPL children and RPL preferred parent,
 *                                             hash(nbr.MAC) % ORCHESTRA_SB_UNICAST_PERIOD
 *         If sender-based: the opposite
 *
 * \author Simon Duquennoy <simonduq@sics.se>
 */

#include "contiki.h"
#include "orchestra.h"
#include "net/ipv6/uip-ds6-route.h"
#include "net/packetbuf.h"
#include "net/routing/routing.h"
#include "net/mac/tsch/tsch-schedule.h"//ksh..
#include "net/mac/tsch/tsch.h" //ksh..

#include "net/routing/rpl-classic/rpl.h"
#include "net/routing/rpl-classic/rpl-private.h"

#define DEBUG DEBUG_PRINT
#include "net/ipv6/uip-debug.h"


/*
 * The body of this rule should be compiled only when "nbr_routes" is available,
 * otherwise a link error causes build failure. "nbr_routes" is compiled if
 * UIP_MAX_ROUTES != 0. See uip-ds6-route.c.
 */
#if UIP_MAX_ROUTES != 0

#if ORCHESTRA_UNICAST_SENDER_BASED && ORCHESTRA_COLLISION_FREE_HASH
#define UNICAST_SLOT_SHARED_FLAG    ((ORCHESTRA_UNICAST_PERIOD < (ORCHESTRA_MAX_HASH + 1)) ? LINK_OPTION_SHARED : 0)
#else
#define UNICAST_SLOT_SHARED_FLAG      LINK_OPTION_SHARED
#endif



uint16_t sfid_schedule=0; //absolute slotframe number for ALICE time varying scheduling

static uint16_t slotframe_handle = 0;
//static uint16_t channel_offset = 0;
static struct tsch_slotframe *sf_unicast;

uint8_t link_option_rx = LINK_OPTION_RX ;
uint8_t link_option_tx = LINK_OPTION_TX | UNICAST_SLOT_SHARED_FLAG ; //ksh.. If it is a shared link, backoff will be applied.



/*---------------------------------------------------------------------------*/
static uint16_t
get_node_timeslot(const linkaddr_t *addr1, const linkaddr_t *addr2)
{

  if(addr1 != NULL && addr2 != NULL && ORCHESTRA_UNICAST_PERIOD > 0) {
 return real_hash5(((uint32_t)ORCHESTRA_LINKADDR_HASH2(addr1, addr2)+(uint32_t)sfid_schedule), (ORCHESTRA_UNICAST_PERIOD)); //link-based
  } else {
    return 0xffff;
  }
}

/*-----------------*/
//ksh. newly defined function
static uint16_t
get_node_channel_offset(const linkaddr_t *addr1, const linkaddr_t *addr2)
{

#if ALICE_RX_BASED_MULTICHANNEL
  return TSCH_DYNAMIC_CHANNEL_OFFSET;
#endif


#if ORCHESTRA_ONE_CHANNEL_OFFSET
  return slotframe_handle; //ksh.. only one channel offset is allowed for unicast slotframe.
#endif

  int num_ch = (sizeof(TSCH_DEFAULT_HOPPING_SEQUENCE)/sizeof(uint8_t))-1; //ksh.
  if(addr1 != NULL && addr2 != NULL  && num_ch > 0) { //ksh.   
       return 1+real_hash5(((uint32_t)ORCHESTRA_LINKADDR_HASH2(addr1, addr2)+(uint32_t)sfid_schedule),num_ch); //link-based
  } else {
    return 1+0; 
  }

}
/*---------------------------------------------------------------------------*/
uint16_t
is_root(){
  rpl_instance_t *instance =rpl_get_default_instance();
  if(instance!=NULL && instance->current_dag!=NULL){
       uint16_t min_hoprankinc = instance->min_hoprankinc;
       uint16_t rank=(uint16_t)instance->current_dag->rank;
       if(min_hoprankinc == rank){
          return 1;
       }
  }
  return 0;
}

/*---------------------------------------------------------------------------*/
static void
alice_schedule_unicast_slotframe(void){ //ksh.  //remove current slotframe scheduling and re-schedule this slotframe.

  uint16_t timeslot_us, timeslot_ds, channel_offset_us, channel_offset_ds;
  uint16_t timeslot_us_p, timeslot_ds_p, channel_offset_us_p, channel_offset_ds_p; //parent's schedule
  uint8_t link_option_up, link_option_down;

//remove the whole links scheduled in the unicast slotframe
  struct tsch_link *l;
  l = list_head(sf_unicast->links_list);
  while(l!=NULL) {    
    tsch_schedule_remove_link(sf_unicast, l);
    l = list_head(sf_unicast->links_list);
  }




 if(is_root()!=1){
//schedule the links between parent-node and current node

     timeslot_us_p = get_node_timeslot(&linkaddr_node_addr, &orchestra_parent_linkaddr);
     channel_offset_us_p = get_node_channel_offset(&linkaddr_node_addr, &orchestra_parent_linkaddr);
     link_option_up=link_option_tx;
     tsch_schedule_add_link_alice(sf_unicast, link_option_up, LINK_TYPE_NORMAL, &tsch_broadcast_address,  &orchestra_parent_linkaddr, timeslot_us_p, channel_offset_us_p);

     timeslot_ds_p = get_node_timeslot(&orchestra_parent_linkaddr, &linkaddr_node_addr);
     channel_offset_ds_p = get_node_channel_offset(&orchestra_parent_linkaddr, &linkaddr_node_addr);
     link_option_down=link_option_rx;
     tsch_schedule_add_link_alice(sf_unicast, link_option_down, LINK_TYPE_NORMAL, &tsch_broadcast_address,  &orchestra_parent_linkaddr, timeslot_ds_p, channel_offset_ds_p);


 }//is_root end

//schedule the links between child-node and current node   //(lookup all route next hops)
  nbr_table_item_t *item = nbr_table_head(nbr_routes);
  while(item != NULL) {

    linkaddr_t *addr = nbr_table_get_lladdr(nbr_routes, item);
    //ts and choff allocation



    timeslot_us = get_node_timeslot(addr, &linkaddr_node_addr); 
    channel_offset_us = get_node_channel_offset(addr, &linkaddr_node_addr);
    link_option_up = link_option_rx; //20190507 ksh..
    //add links (upstream)
    tsch_schedule_add_link_alice(sf_unicast, link_option_up, LINK_TYPE_NORMAL, &tsch_broadcast_address, addr,  timeslot_us, channel_offset_us);


    timeslot_ds = get_node_timeslot(&linkaddr_node_addr, addr); 
    channel_offset_ds = get_node_channel_offset(&linkaddr_node_addr, addr);
    link_option_down = link_option_tx; //20190507 ksh..
    //add links (downstream)
    tsch_schedule_add_link_alice(sf_unicast, link_option_down, LINK_TYPE_NORMAL, &tsch_broadcast_address, addr, timeslot_ds, channel_offset_ds);

    //move to the next item for while loop.
    item = nbr_table_next(nbr_routes, item);
  }


}




/*---------------------------------------------------------------------------*/
static int
neighbor_has_uc_link(const linkaddr_t *linkaddr)
{
  if(linkaddr != NULL && !linkaddr_cmp(linkaddr, &linkaddr_null)) {
    if((orchestra_parent_knows_us || !ORCHESTRA_UNICAST_SENDER_BASED)
       && linkaddr_cmp(&orchestra_parent_linkaddr, linkaddr)) {
      return 1;
    }
    if(nbr_table_get_from_lladdr(nbr_routes, (linkaddr_t *)linkaddr) != NULL) {
      return 1;
    }
  }
  return 0;
}
/*---------------------------------------------------------------------------*/

/*---------------------------------------------------------------------------*/ //ksh. packet_selection_callback. 
#ifdef ALICE_CALLBACK_PACKET_SELECTION
int alice_callback_packet_selection (uint16_t* ts, uint16_t* choff, const linkaddr_t rx_lladdr){
//packet destination is rx_lladdr. Checks if rx_lladdr is still the node's RPL neighbor. and checks wether this can be transmitted at the current link's cell (*ts,*choff). 

  uint16_t cur_ts = *ts;
  uint16_t cur_choff = *choff;
  int is_neighbor = 0;
 
//schedule the links between parent-node and current node
  if(linkaddr_cmp(&orchestra_parent_linkaddr, &rx_lladdr)){
     is_neighbor = 1;

    *ts= get_node_timeslot(&linkaddr_node_addr, &orchestra_parent_linkaddr);
    *choff= get_node_channel_offset(&linkaddr_node_addr, &orchestra_parent_linkaddr);       

    if(*ts == cur_ts && *choff == cur_choff){
         return is_neighbor ; //is_neighbor =1; (parent)
    }

    return is_neighbor ;
  }



//schedule the links between child-node and current node   //(lookup all route next hops)
  nbr_table_item_t *item = nbr_table_get_from_lladdr(nbr_routes, &rx_lladdr);
  if(item != NULL){
      is_neighbor = 1;
      *ts= get_node_timeslot(&linkaddr_node_addr, &rx_lladdr);
      *choff= get_node_channel_offset(&linkaddr_node_addr, &rx_lladdr); 

      if(*ts == cur_ts && *choff == cur_choff){
         return is_neighbor ; //is_neighbor =1; (child)
      }
      return is_neighbor; //is_neighbor =1; (child)    
  }

 // this packet's receiver is not the node's RPL neighbor. 

  *ts =0;
  *choff= ALICE_BROADCAST_SF_ID;
  //-----------------------
  return is_neighbor ; // returns 0; //will be early packet dropped

}
#endif //ALICE_CALLBACK_PACKET_SELECTION

/*---------------------------------------------------------------------------*/ //ksh. slotframe_callback. 
#ifdef ALICE_TSCH_CALLBACK_SLOTFRAME_START
void alice_callback_slotframe_start (uint16_t sfid, uint16_t sfsize){  
   sfid_schedule=sfid; //ksh.. update curr sfid_schedule.
//   PRINTF("SFID: %u\n", sfid);  
     
  alice_schedule_unicast_slotframe(); //ksh.. 20190508
}
#endif

/*---------------------------------------------------------------------------*/
static void
child_added(const linkaddr_t *linkaddr)
{
//  PRINTF("NBR CHILD ADDED \n");
  alice_schedule_unicast_slotframe();
}
/*---------------------------------------------------------------------------*/
static void
child_removed(const linkaddr_t *linkaddr)
{
//  PRINTF("NBR CHILD REMOVED \n");
  alice_schedule_unicast_slotframe();
}
/*---------------------------------------------------------------------------*/
static int
select_packet(uint16_t *slotframe, uint16_t *timeslot, uint16_t *channel_offset)
{
  const linkaddr_t *dest = packetbuf_addr(PACKETBUF_ADDR_RECEIVER);
  if(packetbuf_attr(PACKETBUF_ATTR_FRAME_TYPE) == FRAME802154_DATAFRAME && neighbor_has_uc_link(dest)) {
    if(slotframe != NULL) {
      *slotframe = slotframe_handle;
    }
    if(timeslot != NULL) {        
        //if the destination is the parent node, schedule it in the upstream period, if the destination is the child node, schedule it in the downstream period.
        if(linkaddr_cmp(&orchestra_parent_linkaddr, dest)){
           *timeslot = get_node_timeslot(&linkaddr_node_addr, dest); //parent node (upstream)
         //  *timeslot=0;
        }else{
           *timeslot = get_node_timeslot(&linkaddr_node_addr, dest);  //child node (downstream)
         //  *timeslot=0;
        }
    }
    if(channel_offset != NULL) { //ksh.
        //if the destination is the parent node, schedule it in the upstream period, if the destination is the child node, schedule it in the downstream period.
        if(linkaddr_cmp(&orchestra_parent_linkaddr, dest)){
           *channel_offset = get_node_channel_offset(&linkaddr_node_addr, dest); //child node (upstream)
         //  *channel_offset=0;
        }else{
           *channel_offset = get_node_channel_offset(&linkaddr_node_addr, dest); //child node (downstream)
         //  *channel_offset=0;
        }
    }

    return 1;
  }
  return 0;
}

/*---------------------------------------------------------------------------*/

/*---------------------------------------------------------------------------*/
static void
new_time_source(const struct tsch_neighbor *old, const struct tsch_neighbor *new)
{

//  PRINTF("NBR NEW TIME SOURCE \n");

  if(new != old) {   
    const linkaddr_t *new_addr = new != NULL ? &new->addr : NULL;
    if(new_addr != NULL) {
      linkaddr_copy(&orchestra_parent_linkaddr, new_addr);    
    } else {
      linkaddr_copy(&orchestra_parent_linkaddr, &linkaddr_null);
    }

#ifdef ALICE_TSCH_CALLBACK_SLOTFRAME_START//ksh..
            uint16_t mod=TSCH_ASN_MOD(tsch_current_asn, sf_unicast->size);
            struct tsch_asn_t newasn;
            TSCH_ASN_COPY(newasn, tsch_current_asn);
            TSCH_ASN_DEC(newasn, mod);
            currSFID = TSCH_ASN_DEVISION(newasn, sf_unicast->size);
            nextSFID = currSFID;
#endif


#ifdef ALICE_TSCH_CALLBACK_SLOTFRAME_START
  sfid_schedule = alice_tsch_schedule_get_current_sfid(sf_unicast);//ksh..
#endif

    alice_schedule_unicast_slotframe(); 




  }
}
/*---------------------------------------------------------------------------*/
static void
init(uint16_t sf_handle)
{
  slotframe_handle = sf_handle;
  /* Slotframe for unicast transmissions */
  sf_unicast = tsch_schedule_add_slotframe(slotframe_handle, ORCHESTRA_UNICAST_PERIOD);


  PRINTF("AILCE: unicast sf length: %u\n", ORCHESTRA_UNICAST_PERIOD);

#ifdef ALICE_TSCH_CALLBACK_SLOTFRAME_START
  limitSFID = (uint16_t)((uint32_t)65536/(uint32_t)ORCHESTRA_UNICAST_PERIOD); //65535= 4Byte max value (0,65535) #65536
  printf("limitSFID: %u\n",limitSFID);
#endif 




#ifdef ALICE_TSCH_CALLBACK_SLOTFRAME_START
  sfid_schedule = alice_tsch_schedule_get_current_sfid(sf_unicast);//ksh..
#else
  sfid_schedule = 0; //sfid (ASN) will not be used.
#endif

}
/*---------------------------------------------------------------------------*/
struct orchestra_rule unicast_per_neighbor_rpl_storing = {
  init,
  new_time_source,
  select_packet,
  child_added,
  child_removed,
};

#endif /* UIP_MAX_ROUTES */
