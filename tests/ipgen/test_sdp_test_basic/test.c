#include "sdp.h"
#include <stdio.h>

int run_test() {
    sdp sh;

    sdp_init(&sh, 0);
    sdp_s_axi_write(&sh, 0xaa, 1);

    if (sdp_s_axi_read(&sh, 1) != 0xaa)
        return -1;

    if (sdp_s_axi_read(&sh, 255) != 0)
      return -1;

    sdp_s_axi_write(&sh, 0xaa, 255);

    if (sdp_s_axi_read(&sh, 1) != 0xaa)
      return -1;

    if (sdp_s_axi_read(&sh, 255) != 0xaa)
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
