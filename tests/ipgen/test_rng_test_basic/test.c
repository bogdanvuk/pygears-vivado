#include "qrange.h"
#include "xil_cache.h"
#include <stdint.h>
#include <stdio.h>

uint32_t buff[8];

int run_test() {
  qrange h;

  qrange_init(&h, 0);

  qrange_stop_write(&h, 8);

  Xil_DCacheInvalidateRange((UINTPTR)buff, 8 * 4);

  qrange_dout_recv(&h, buff, 8);

  Xil_DCacheInvalidateRange((UINTPTR)buff, 8 * 4);

  for (int i = 0; i < 8; ++i) {
    if (buff[i] != i) {
      return -1;
    }
  }

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
