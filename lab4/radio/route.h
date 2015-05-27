#define ROUTE_MAX_HOPS 8
#define ROUTE_TABLE_SIZE 16

#define ROUTE_CTRL_MAGIC 0x5566
#define ROUTE_CTRL_REQUEST 0x1
#define ROUTE_CTRL_REPLY 0x2
#define ROUTE_CTRL_PING 0x4
#define ROUTE_CTRL_PING_REPLY 0x8

#define ROUTE_STATE_IDLE 0

#define VISITED_SIZE 16

#define OFFSET(T, m) ((size_t)&((T*)0)->m)

struct route_entry_t {
    uint16_t dst_addr;
    uint8_t hops;
    uint16_t path[ROUTE_MAX_HOPS];
};

struct route_ctrl_hdr {
    uint16_t magic;
    uint8_t type;
    uint16_t id;
};
