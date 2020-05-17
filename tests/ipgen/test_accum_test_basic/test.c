#include "accum.h"
#include <stdint.h>
#include <stdio.h>

uint32_t buff[8] = {0, 1, 2, 3, 4, 5, 6, 7};

int run_test() {
  accum h;

  accum_init(&h, 0);
  accum_din_send(&h, buff, 8);

  if (accum_dout_read(&h) != 30)
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
