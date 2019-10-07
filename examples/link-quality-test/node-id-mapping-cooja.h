#ifndef NODE_ID_MAPPING_H_
#define NODE_ID_MAPPING_H_

/* For Cooja tests, simply use the node IDs as the schedule IDs */
static inline uint8_t
get_schedule_id(uint16_t node_id)
{
  return (uint8_t)node_id;
}

#endif /* NODE_ID_MAPPING */
