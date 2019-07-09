/*
 * Copyright (c) 2015, SICS Swedish ICT.
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
 * \author Simon Duquennoy <simonduq@sics.se>
 */

#ifndef PROJECT_CONF_H_
#define PROJECT_CONF_H_

/* Set to enable TSCH security */
#ifndef WITH_SECURITY
#define WITH_SECURITY 0
#endif /* WITH_SECURITY */

/* USB serial takes space, free more space elsewhere */
#define SICSLOWPAN_CONF_FRAG 0
#define UIP_CONF_BUFFER_SIZE 160





/*******************************************************/
/******************* Configure Node Num ********************/  //ksh..
/*******************************************************/


#define MAX_NODE_NUM 20 //70 //ksh.. maximum number of nodes
#undef UIP_CONF_MAX_ROUTES
#define UIP_CONF_MAX_ROUTES MAX_NODE_NUM /* No need for routes */

#undef NBR_TABLE_CONF_MAX_NEIGHBORS
#define NBR_TABLE_CONF_MAX_NEIGHBORS MAX_NODE_NUM //ksh.. modified. original:10

#define TSCH_SCHEDULE_CONF_MAX_LINKS MAX_NODE_NUM //ksh.. as escalator..


/*******************************************************/
/******************* Configure RPL ********************/
/*******************************************************/


#undef NETSTACK_CONF_ROUTING
#define NETSTACK_CONF_ROUTING       rpl_classic_driver    //ksh..

#define RPL_CONF_WITH_NON_STORING    0 // original : 1 //ksh..
#define RPL_CONF_MOP                RPL_MOP_STORING_NO_MULTICAST  //ksh..
#define RPL_CONF_WITH_DAO_ACK       1 //ksh..


#undef ROUTING_CONF_RPL_LITE
#define ROUTING_CONF_RPL_LITE     0 //ksh..

#define ROUTING_CONF_RPL_CLASSIC     1 //ksh..






/*******************************************************/
/******************* Configure TSCH ********************/
/*******************************************************/

/* IEEE802.15.4 PANID */
#define IEEE802154_CONF_PANID 0x81a5

/* Do not start TSCH at init, wait for NETSTACK_MAC.on() */
#define TSCH_CONF_AUTOSTART 0

/* 6TiSCH minimal schedule length.
 * Larger values result in less frequent active slots: reduces capacity and saves energy. */
#define TSCH_SCHEDULE_CONF_DEFAULT_LENGTH 3

#if WITH_SECURITY

/* Enable security */
#define LLSEC802154_CONF_ENABLED 1

#endif /* WITH_SECURITY */



/*******************************************************/
/******************* Orchestra Scheduler ***************/
/*******************************************************/

#define SEND_INTERVAL   	((60) * (CLOCK_SECOND))
#define SEND_TIME		(random_rand() % (SEND_INTERVAL)) //backoff 

#define UDP_CLIENT_PORT	8765
#define UDP_SERVER_PORT	5678






#define ORCHESTRA_CONF_COMMON_SHARED_PERIOD 31 //ksh.. original: 31. (broadcast and default slotframe length)
#define ORCHESTRA_CONF_UNICAST_PERIOD 17 // 7, 11, 23, 31, 43, 47, 59, 67, 71    
//#define ORCHESTRA_CONF_EBSF_PERIOD 397//.. original: 397. (EB slotframe)




#define CURRENT_TSCH_SCHEDULER 3 //MAKE_WITH_SCHEDULER,  1: orchestra 2:mc-orchestra 3:ALICE



#if CURRENT_TSCH_SCHEDULER > 1
#define ORCHESTRA_CONF_RULES { &eb_per_time_source, &default_common , &unicast_per_neighbor_rpl_storing}
#define ALICE_UNICAST_SF_ID 2 //slotframe handle of unicast slotframe
#define ALICE_BROADCAST_SF_ID 1 //slotframe handle of broadcast/default slotframe
#ifndef MULTIPLE_CHANNEL_OFFSETS
#define MULTIPLE_CHANNEL_OFFSETS 1 //ksh.. allow multiple channel offsets.
#endif
#endif



/**********************************************************************/
/*******   orchestra sender-based  vs. receiver-based    **************/
#define ORCHESTRA_CONF_UNICAST_SENDER_BASED 1 //1:sender-based 0:receiver-based
#define ORCHESTRA_ONE_CHANNEL_OFFSET 0 //mc-orchestra -> 1:single channel offset, 0:multiple channel offsets
/**********************************************************************/




#if CURRENT_TSCH_SCHEDULER == 3 //ALICE
#define WITH_ALICE   1//KSH
#undef ORCHESTRA_CONF_UNICAST_SENDER_BASED
#define ORCHESTRA_CONF_UNICAST_SENDER_BASED 1 //1:sender-based 0:receiver-based

#else //CURRENT_TSCH_SCHEDULER != 3
#define WITH_ALICE  0 //KSH
#endif


#if WITH_ALICE
#define ALICE_CALLBACK_PACKET_SELECTION alice_callback_packet_selection //ksh. alice packet selection
#define ALICE_TSCH_CALLBACK_SLOTFRAME_START alice_callback_slotframe_start //ksh. alice time varying slotframe schedule
#endif
/**********************************************************************/
/**********************************************************************/













/*******************************************************/
/************* Other system configuration **************/
/*******************************************************/

/* Logging */
#define LOG_CONF_LEVEL_RPL                         LOG_LEVEL_INFO
#define LOG_CONF_LEVEL_TCPIP                     0//  LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_IPV6                      0//  LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_6LOWPAN                   0//  LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_MAC                       0//  LOG_LEVEL_INFO
#define LOG_CONF_LEVEL_FRAMER                    0//  LOG_LEVEL_DBG
#define TSCH_LOG_CONF_PER_SLOT                   0//  1

#endif /* PROJECT_CONF_H_ */
