#ifndef NODE_ID_MAPPING_H_
#define NODE_ID_MAPPING_H_

/* For the IoT lab testbed in Strasbourgh */
static inline uint8_t
get_schedule_id(uint16_t node_id)
{
  int i;
  static const uint16_t table[] = {
    0,

    42116,  //  1
    38791,  //  3
    39049,  //  5
    45444,  //  7
    47237,  //  9

    0x8984, // 11
    0xb384, // 13
    0x9488, // 15
    0xb585, // 17
    0x9083, // 19

    0xa385, // 21
    0xa984, // 23
    0xa187, // 25
    0xa185, // 27
    0xa284, // 29

    0xa885, // 31
    0xb286, // 33
    0xa784, // 35
    0xa386, // 37
    0xa184, // 39

    0x9885, // 41
    0x9285, // 43
    0xb385, // 45
    0xa487, // 47
    0xa186, // 49

    0xa585, // 51
    0x9890, // 53
    0xb486, // 55
    0x9986, // 57
    0x9586, // 59

    0xa988, // 61
    0x9887, // 63

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
