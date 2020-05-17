#include "add.h"
#include <stdio.h>

int run_test() {
  add h;

  add_init(&h, 0);
  add_s_axi_write(&h, 0x00010002);

  if (add_s_axi_read(&h) != 3)
    return -1;

  add_s_axi_write(&h, 0x00060003);

  if (add_s_axi_read(&h) != 9)
    return -1;

  add_s_axi_write(&h, 0x00090002);

  if (add_s_axi_read(&h) != 11)
    return -1;

  return 0;
}

int main() {
  if (run_test()) {
    printf("FAIL\r\n");
  } else {
    printf("SUCCESS\r\n");
  }

  return 0;
}
