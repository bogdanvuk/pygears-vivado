#ifndef PGAXI_H
#define PGAXI_H

#include <stdint.h>
#include <stdlib.h>

typedef struct {
  uintptr_t reg_base;
} pgaxi;

void pgaxi_init(pgaxi *h, uintptr_t reg_base);

void pgaxi_dma_send(pgaxi *h, const void *data, size_t len);

void pgaxi_dma_recv(pgaxi *h, void *data, size_t len);

void pgaxi_write32(pgaxi *h, uint32_t val, uintptr_t addr);

void pgaxi_write64(pgaxi *h, uint64_t val, uintptr_t addr);

uint32_t pgaxi_read32(pgaxi *h, uintptr_t addr);

uint64_t pgaxi_read64(pgaxi *h, uintptr_t addr);

#endif
