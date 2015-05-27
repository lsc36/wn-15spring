#define DISCO_CTRL_MAGIC	0x573
#define DISCO_CTRL_QUERY	0x1
#define DISCO_CTRL_BROADCAST	0x2
#define DISCO_QLEN		8

#pragma pack(push)
#pragma pack(1)
struct disco_ctrl_hdr {
    uint16_t magic;
    uint8_t type;
};
struct disco_query {
    struct disco_ctrl_hdr hdr;
    uint16_t target_addr;
    uint16_t version;
};
struct disco_broadcast {
    struct disco_ctrl_hdr hdr;
    uint16_t target_addr;
    uint16_t version;
};

struct disco_query_entry {
    uint16_t target_addr;
    uint16_t version;
};
struct disco_broadcast_entry {
    uint16_t target_addr;
    uint16_t version;
    int counter;
};
#pragma pack(pop)

struct disco_query_entry disco_query_vec[DISCO_QLEN];
struct disco_broadcast_entry disco_broadcast_vec[DISCO_QLEN];

int disco_query_dispatch_idx;
int disco_broadcast_dispatch_idx;
