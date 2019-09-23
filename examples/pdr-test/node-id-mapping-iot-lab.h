#ifndef NODE_ID_MAPPING_H_
#define NODE_ID_MAPPING_H_

/* For IoT lab in Strasbourgh */
static inline uint8_t
get_schedule_id(uint16_t node_id)
{
  int i;
  static const uint16_t table[] = {
    0,
    42116,
    42629,
    38791,
    37768,
    39049,
    37511,
    45444,
    43143,
    47237,
    37767,
    0xffff
  };

  for(i = 1; table[i] != 0xffff; i++) {
    if(table[i] == node_id) {
      return i;
    }
  }
  return 0;
}

#endif /* NODE_ID_MAPPING */
