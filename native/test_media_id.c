#include "cdrom_media_id.h"
#include <assert.h>
#include <string.h>
int main(void) {
    uint8_t reply[8];
    const uint8_t data[] = {2, 0, 0x20, 0, 'S', 'C', 'E', 'E'};
    const uint8_t audio[] = {0x0A, 0x90, 0, 0, 0, 0, 0, 0};
    cdrom_media_id(2, 0, data + 4, reply);
    assert(!memcmp(reply, data, 8));
    cdrom_media_id(2, 1, data + 4, reply);
    assert(!memcmp(reply, audio, 8));
    cdrom_media_id(0x22, 1, data + 4, reply);
    assert(reply[0] == 0x2A && reply[1] == 0x90 && reply[4] == 0);
    return 0;
}
