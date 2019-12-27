#include <stdint.h>
#include <stdlib.h>

#define WORD_BITSIZE (sizeof(uint_fast32_t)*8)

#define min(a, b) (((a) < (b)) ? (a) : (b))
#define max(a, b) (((a) > (b)) ? (a) : (b))

void *aligned_malloc(size_t size, size_t alignment) {
    void *p1;
    void **p2;
    int offset = alignment - 1 + sizeof(void*);
    p1 = malloc(size + offset);
    p2=(void**)(((size_t)(p1)+offset)&~(alignment-1));
    p2[-1]=p1;
    return p2;
}

void aligned_free( void* p ) {
    void* p1 = ((void**)p)[-1];         // get the pointer to the buffer we allocated
    free( p1 );
}

uint_fast32_t pg_typing_get_word(uint_fast32_t* cmd, uint_fast32_t width, uint_fast32_t offset) {
    uint_fast32_t val         = 0;
    uint_fast32_t cmd_word    = offset / WORD_BITSIZE;
    uint_fast32_t word_offset = offset % WORD_BITSIZE;
    uint_fast32_t cur_width   = min(WORD_BITSIZE - word_offset, width);
    uint_fast32_t mask        = ((1L << cur_width) - 1) << word_offset;

    val = cmd[cmd_word] >> word_offset;

    // If whole width didn't fit inside current word
    if (cur_width < width)
    {
        cmd_word++;
        mask = (1 << (width - cur_width)) - 1;

        val |= (cmd[cmd_word] & mask) << cur_width;
    }

    return val;
}

void pg_typing_get(uint_fast32_t* cmd, void* pval, uint_fast32_t offset, uint_fast32_t width) {
    uint_fast32_t* ptr         = (uint_fast32_t*)pval;
    uint_fast32_t  word_width  = width;
    uint_fast32_t  word_offset = offset;
    for (int i = 0; i < (width + WORD_BITSIZE - 1) / WORD_BITSIZE; ++i)
    {
        ptr[i] = pg_typing_get_word(cmd, min(word_width, WORD_BITSIZE), word_offset);
        word_width -= WORD_BITSIZE;
        word_offset += WORD_BITSIZE;
    }
}

void pg_typing_set_word(uint_fast32_t* cmd, uint_fast32_t val, uint_fast32_t width, uint_fast32_t offset) {
    uint_fast32_t cmd_word = offset / WORD_BITSIZE;
    uint_fast32_t word_offset = offset % WORD_BITSIZE;
    uint_fast32_t cur_width = min(WORD_BITSIZE - word_offset, width);
    uint_fast32_t mask = ((1L << cur_width) - 1) << word_offset;

    cmd[cmd_word] &= ~mask;
    cmd[cmd_word] |= val << word_offset;

    // If whole width didn't fit inside current word
    if (cur_width < width) {
        val >>= cur_width;
        cur_width = width - cur_width;
        cmd_word++;
        mask = (1 << cur_width) - 1;

        cmd[cmd_word] &= ~mask;
        cmd[cmd_word] |= val;
    }
}

void pg_typing_set(uint_fast32_t* cmd, void* pval, uint_fast32_t offset, uint_fast32_t width) {
    uint_fast32_t* ptr = (uint_fast32_t*) pval;
    uint_fast32_t word_width = width;
    uint_fast32_t word_offset = offset;
    for (int i = 0; i < (width + WORD_BITSIZE - 1)/WORD_BITSIZE; ++i) {
        pg_typing_set_word(cmd, ptr[i], min(word_width, WORD_BITSIZE), word_offset);
        word_width -= WORD_BITSIZE;
        word_offset += WORD_BITSIZE;
    }
}

