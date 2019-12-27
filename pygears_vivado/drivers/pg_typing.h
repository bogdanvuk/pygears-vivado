#ifndef PG_TYPING_H
#define PG_TYPING_H

#include <stdlib.h>
#include <stdint.h>

void *aligned_malloc(size_t size, size_t alignment);

void aligned_free( void* p );

void pg_typing_get(uint_fast32_t* cmd, void* pval, uint_fast32_t offset, uint_fast32_t width);
uint_fast32_t pg_typing_get_word(uint_fast32_t* cmd, uint_fast32_t width, uint_fast32_t offset);

void pg_typing_set(uint_fast32_t* cmd, void* pval, uint_fast32_t offset, uint_fast32_t width);
void pg_typing_set_word(uint_fast32_t* cmd, uint_fast32_t val, uint_fast32_t width, uint_fast32_t offset);

#endif
