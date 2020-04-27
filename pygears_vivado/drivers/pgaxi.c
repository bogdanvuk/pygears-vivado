#include <stdint.h>
#include <stdlib.h>
#include "pgaxi.h"

#define CMD_CONTROL 0x0
#define CMD_UNUSED_1 0x1
#define CMD_ADDRLO 0x2
#define CMD_ADDRHI 0x3
#define CMD_UNUSED_2 0x4
#define CMD_UNUSED_3 0x5
#define CMD_LENLO 0x6
#define CMD_LENHI 0x7

#define CMD_CONTROL_R_BUSY(val) ((val) & (1 << 31))
#define CMD_CONTROL_R_ERR (1 << 30)
#define CMD_CONTROL_R_COMPLETE (1 << 29)

void pgaxi_init(pgaxi *h, uintptr_t reg_base) { h->reg_base = reg_base; }

uint32_t pgaxi_dma_ctrl_reg(pgaxi *h) { return *(volatile uint32_t *)h->reg_base; }

int pgaxi_dma_busy(pgaxi *h) { return CMD_CONTROL_R_BUSY(pgaxi_dma_ctrl_reg(h)); }

void pgaxi_dma_set(pgaxi *h, uint32_t reg, uint32_t val) {
  	volatile uint32_t* reg_addr = (volatile uint32_t *)h->reg_base + reg;
    *reg_addr = val;
}

void pgaxi_dma_send(pgaxi *h, void *data, size_t len) {
    while (pgaxi_dma_busy(h))
        ;

    pgaxi_dma_set(h, CMD_ADDRLO, (uintptr_t)data);
    pgaxi_dma_set(h, CMD_ADDRHI, ((uintptr_t)data) >> 32);

    pgaxi_dma_set(h, CMD_LENLO, len);
    pgaxi_dma_set(h, CMD_LENHI, len >> 32);

    pgaxi_dma_set(h, CMD_CONTROL, 0x80000000);
}

void pgaxi_write32(pgaxi *h, uint32_t val, uintptr_t addr) {
    *((volatile uint32_t *)h->reg_base + addr) = val;
}

void pgaxi_write64(pgaxi *h, uint64_t val, uintptr_t addr) {
    *((volatile uint64_t *)h->reg_base + addr) = val;
}

uint32_t pgaxi_read32(pgaxi *h, uintptr_t addr) {
    return *((volatile uint32_t *)h->reg_base + addr);
}

uint64_t pgaxi_read64(pgaxi *h, uintptr_t addr) {
    return *((volatile uint64_t *)h->reg_base + addr);
}
