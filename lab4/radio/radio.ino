#include <ZigduinoRadio.h>
#include "route.h"

#define BROADCAST_ID	0xFFFF
#define PAN_ID		0xABCD
#define CHANNEL		24

uint16_t node_id;

#define DIFS		4096
#define TIMEOUT		8192
#define BACKOFF		4096
uint32_t backoff_window	=   16;

#pragma pack(push)
#pragma pack(1)
struct tx_header {
    uint8_t ctrl[2];
    uint8_t seq;
    uint16_t panid;
    uint16_t dst_addr;
    uint16_t src_addr;
};
struct tx_ack {
    uint8_t ctrl[2];
    uint8_t seq;
    uint8_t pad[2];
};
#pragma pack(pop)

#define QLEN 16
#define MAX_RETRY 16
struct tx_data {
    uint8_t buffer[QLEN][64];
    size_t len[QLEN];
    int qfront, qback;
    int difs_ts;
    int timeout_ts;
    int backoff;
    uint8_t seq;
    int state;
    int retry;
};
struct rx_data {
    uint8_t buffer[QLEN][64];
    size_t len[QLEN];
    int qfront, qback;
};

struct tx_data tx;
struct rx_data rx;
struct tx_ack pkt_tx_ack;

uint16_t get_checksum(uint8_t *data,int len) {
    int i;
    uint8_t checksum = 0;
    for(i = 0; i < len; i++) {
        checksum ^= data[i];
    }
    return checksum;
}

uint8_t* rx_hlr(uint8_t len,uint8_t *frm,uint8_t lqi,uint8_t crc_fail) {
    int qid = rx.qback;
    if(frm[0] == 0x42) {
        if(len < sizeof(struct tx_ack)) {
            goto out;
        }
    } else if(frm[0] == 0x41) {
        struct tx_header *rx_hdr = (struct tx_header*)frm;

        if(len < sizeof(struct tx_header)) {
            goto out;
        }

        //Remove unused HWACK
        len -= 2;

        if(rx_hdr->ctrl[0] == 0x42) {
            goto out;
        }

        if(rx_hdr->panid != PAN_ID) {
            goto out;
        }
        if(rx_hdr->dst_addr != node_id && rx_hdr->dst_addr != BROADCAST_ID) {
            goto out;
        }
        if(get_checksum(frm,len) != 0x0) {
            goto out;
        }
    }

    rx.qback = (rx.qback + 1) % QLEN;
    memcpy(rx.buffer[qid],frm,len);
    rx.len[qid] = len;

out:

    return rx.buffer[qid];
}

int rx_dispatch() {
    int qid = rx.qfront; rx.qfront = (rx.qfront + 1) % QLEN;
    int type = rx.buffer[qid][0];

    rx.len[qid] = 0;

    if(type == 0x42 && tx.qfront != tx.qback) {
        struct tx_ack *rx_ack = (struct tx_ack*)rx.buffer[qid];
        struct tx_header *tx_hdr = (struct tx_header*)tx.buffer[tx.qfront];
        if(rx_ack->seq == tx_hdr->seq) {
            tx.state = 5;
        }
    } else if(type == 0x41) {
        struct tx_header *rx_hdr = (struct tx_header*)rx.buffer[qid];
        pkt_tx_ack.seq = rx_hdr->seq;
        ZigduinoRadio.txFrame((uint8_t*)&pkt_tx_ack,sizeof(pkt_tx_ack));
        Serial.print("received frame from ");
        Serial.println(rx_hdr->src_addr);
        if (*(uint16_t*)&rx.buffer[qid][sizeof(tx_header)] == ROUTE_CTRL_MAGIC)
            route_dispatch(rx.buffer[qid]);
    }
    return 0;
}

int tx_state() {
    int rssi;
    int ts = micros();

    if(tx.state == -1 && tx.qfront != tx.qback) tx.state = 0;
    if(tx.state >= 0 && tx.state <= 1) {
        rssi = ZigduinoRadio.getRssiNow();
        if(tx.state == 0) {
            //start DIFS
            tx.difs_ts = ts;
            tx.state = 1;
        }
        if(rssi > -91) {
            if((ts - tx.difs_ts) > DIFS) {
                tx.backoff -= (ts - tx.difs_ts - DIFS);
            }
            tx.difs_ts = ts;
        } else if((ts - tx.difs_ts) > (DIFS + tx.backoff)) {
            tx.backoff = BACKOFF + random(1,backoff_window) * 512;
            tx.state = 2;
            return 1;
        }
    } else if(tx.state >= 3) {
        if(tx.state == 5) {
            tx.qfront = (tx.qfront + 1) % QLEN;
            tx.state = -1;
            return 2;
        }
        if(tx.state == 3) {
            //start TIMEOUT
            tx.timeout_ts = ts;
            tx.state = 4;
        }
        if((ts - tx.timeout_ts) > TIMEOUT) {
            if (tx.retry == MAX_RETRY) {
                tx.retry = 0;
                tx.qfront = (tx.qfront + 1) % QLEN;
            } else tx.retry++;
            tx.state = -1;
            return 3;
        }
    }

    return 0;
}
int tx_build(uint16_t dst_addr,uint8_t *payload,size_t len) {
    Serial.print("sending frame to ");
    Serial.println(dst_addr);
    int qid = tx.qback; tx.qback = (tx.qback + 1) % QLEN;
    struct tx_header *tx_hdr = (struct tx_header*)tx.buffer[qid];
    uint16_t checksum;

    tx.seq += 1;

    tx_hdr->ctrl[0] = 0x41;
    tx_hdr->ctrl[1] = 0x88;
    tx_hdr->seq = tx.seq;
    tx_hdr->panid = PAN_ID;
    tx_hdr->dst_addr = dst_addr;
    tx_hdr->src_addr = node_id;
    tx.len[qid] = sizeof(*tx_hdr);

    memcpy(tx.buffer[qid] + tx.len[qid],payload,len);
    tx.len[qid] += len;

    checksum = get_checksum(tx.buffer[qid],tx.len[qid]);
    memcpy(tx.buffer[qid] + tx.len[qid],&checksum,sizeof(checksum));
    tx.len[qid] += sizeof(checksum);

    //Add unused HWACK
    tx.len[qid] += 2;
    return 0;
}
int tx_dispatch() {
    int qid = tx.qfront;
    struct tx_header *tx_hdr = (struct tx_header*)tx.buffer[qid];
    Serial.print("!");
    tx.state = 3;
    ZigduinoRadio.txFrame(tx.buffer[qid],tx.len[qid]);
    tx_hdr->seq--;
    return 0;
}


/**************** start of route section ****************/


int route_state;
char buf[64];

void send_ping(route_entry_t *r_entry, uint16_t ping_id)
{
    route_ctrl_hdr hdr;
    hdr.magic = ROUTE_CTRL_MAGIC;
    hdr.type = ROUTE_CTRL_PING;
    hdr.id = ping_id;
    size_t len = 0;
    memcpy(buf, &hdr, sizeof(hdr));
    len += sizeof(hdr);
    memcpy(buf + len, r_entry, OFFSET(route_entry_t, path));
    len += OFFSET(route_entry_t, path);
    memcpy(buf + len, r_entry->path, r_entry->hops * sizeof(uint16_t));
    len += r_entry->hops * sizeof(uint16_t);
    tx_build(BROADCAST_ID, (uint8_t*)buf, len);
}

void send_ping_reply(route_entry_t *r_entry, uint16_t dst_addr, uint16_t ping_id)
{
    route_ctrl_hdr hdr;
    hdr.magic = ROUTE_CTRL_MAGIC;
    hdr.type = ROUTE_CTRL_PING_REPLY;
    hdr.id = ping_id;
    size_t len = 0;
    memcpy(buf, &hdr, sizeof(hdr));
    len += sizeof(hdr);
    memcpy(buf + len, r_entry, OFFSET(route_entry_t, path));
    len += OFFSET(route_entry_t, path);
    memcpy(buf + len, r_entry->path, r_entry->hops * sizeof(uint16_t));
    len += r_entry->hops * sizeof(uint16_t);
    tx_build(dst_addr, (uint8_t*)buf, len);
}

uint16_t visited_list[VISITED_SIZE];
int visited_pos;
uint16_t last_ping_id;
uint32_t last_ping_time;

void route_dispatch(uint8_t *frm)
{
    route_ctrl_hdr *hdr = (route_ctrl_hdr*)&frm[sizeof(tx_header)];
    route_entry_t *r_entry = (route_entry_t*)&frm[sizeof(tx_header) + sizeof(route_ctrl_hdr)];
    bool visited;
    switch (hdr->type) {
    case ROUTE_CTRL_PING:
        visited = false;
        for (int i = 0; i < VISITED_SIZE; i++) {
            if (visited_list[i] == hdr->id) { visited = true; break; }
        }
        if (visited) break;
        visited_list[visited_pos] = hdr->id;
        visited_pos = (visited_pos + 1) % VISITED_SIZE;

        Serial.print("received ping: hops = ");
        Serial.print(r_entry->hops);
        Serial.print(" ");
        Serial.print(r_entry->path[0]);
        for (int i = 1; i < r_entry->hops; i++) {
            Serial.print(" -> ");
            Serial.print(r_entry->path[i]);
        }
        if (r_entry->dst_addr == node_id) {
            Serial.print(" -> ");
            Serial.println(r_entry->dst_addr);
            if (r_entry->hops >= ROUTE_MAX_HOPS) break;
            Serial.print("sending ping reply to ");
            Serial.println(r_entry->path[r_entry->hops - 1]);
            route_entry_t new_entry;
            new_entry.dst_addr = r_entry->path[0];
            new_entry.hops = r_entry->hops + 1;
            for (int i = 0; i < r_entry->hops; i++)
                new_entry.path[i] = r_entry->path[i];
            new_entry.path[r_entry->hops] = node_id;
            send_ping_reply(&new_entry, r_entry->path[r_entry->hops - 1], hdr->id);
        } else {
            Serial.print(" -> ... -> ");
            Serial.println(r_entry->dst_addr);

            if (r_entry->hops >= ROUTE_MAX_HOPS) break;
            route_entry_t new_entry;
            new_entry.dst_addr = r_entry->dst_addr;
            new_entry.hops = r_entry->hops + 1;
            for (int i = 0; i < r_entry->hops; i++)
                new_entry.path[i] = r_entry->path[i];
            new_entry.path[r_entry->hops] = node_id;
            send_ping(&new_entry, hdr->id);
            Serial.println("rebroadcasting ping");
        }
        break;
    case ROUTE_CTRL_PING_REPLY:
        Serial.println("received ping reply");
        if (r_entry->dst_addr == node_id && last_ping_id == hdr->id) {
            route_state = ROUTE_STATE_IDLE;
            last_ping_id = 0;
            uint32_t rtt = micros() - last_ping_time;
            Serial.print("rtt = ");
            Serial.print(rtt / 1000.0);
            Serial.println("ms");
            Serial.print("hops = ");
            Serial.print(r_entry->hops);
            Serial.print(" ");
            Serial.print(r_entry->path[0]);
            for (int i = 1; i < r_entry->hops; i++) {
                Serial.print(" -> ");
                Serial.print(r_entry->path[i]);
            }
            Serial.println();
        } else if (r_entry->dst_addr == node_id) {
        } else {
            uint16_t dst_addr = 0;
            for (int i = 1; i < r_entry->hops; i++) {
                if (r_entry->path[i] == node_id) {
                    dst_addr = r_entry->path[i - 1];
                    break;
                }
            }
            if (!dst_addr) break;
            route_entry_t new_entry;
            new_entry.dst_addr = r_entry->dst_addr;
            new_entry.hops = r_entry->hops;
            for (int i = 0; i < r_entry->hops; i++)
                new_entry.path[i] = r_entry->path[i];
            send_ping_reply(&new_entry, dst_addr, hdr->id);
            Serial.print("resending ping reply to ");
            Serial.println(dst_addr);
        }
        break;
    }
}

void route_setup()
{
    route_state = ROUTE_STATE_IDLE;
    last_ping_id = 0;
    for (int i = 0; i < VISITED_SIZE; i++) visited_list[i] = 0;
    visited_pos = 0;
}

void route_loop()
{
    if (route_state == ROUTE_STATE_IDLE && Serial.available()) {
        size_t len = Serial.readBytes(buf, 128);
        buf[len] = 0;
        uint16_t ping_dst_addr = atoi(buf);
        route_entry_t new_entry;
        new_entry.dst_addr = ping_dst_addr;
        new_entry.hops = 1;
        new_entry.path[0] = node_id;
        uint16_t ping_id = random(1, 65535);
        send_ping(&new_entry, ping_id);
        last_ping_id = ping_id;
        last_ping_time = micros();
        visited_list[visited_pos] = ping_id;
        visited_pos = (visited_pos + 1) % VISITED_SIZE;
        route_state = ROUTE_STATE_WAIT_PING_REPLY;
    } else if (route_state == ROUTE_STATE_WAIT_PING_REPLY
            && micros() - last_ping_time > PING_TIMEOUT) {
        Serial.println("ping timeout");
        last_ping_id = 0;
        route_state = ROUTE_STATE_IDLE;
    }
}


/**************** end of route section ****************/


void setup() {
    struct tx_header *tx_hdr;

    randomSeed(analogRead(0));
    pinMode(13,OUTPUT);
    digitalWrite(13,HIGH);

    node_id = 1;  // [1, 65534]

    tx.qfront = tx.qback = 0;
    tx.difs_ts = micros();
    tx.timeout_ts = micros();
    tx.backoff = BACKOFF + random(1,backoff_window) * 512;
    tx.seq = 0;
    tx.state = -1;
    tx.retry = 0;

    for (int i = 0; i < QLEN; i++) {
        tx_hdr = (struct tx_header*)tx.buffer[i];
        tx_hdr->ctrl[0] = 0x41;
        tx_hdr->ctrl[1] = 0x88;
        tx_hdr->seq = 0x0;
        tx_hdr->panid = PAN_ID;
        tx_hdr->dst_addr = 0x0;
        tx_hdr->src_addr = node_id;
    }

    rx.qfront = rx.qback = 0;

    pkt_tx_ack.ctrl[0] = 0x42;
    pkt_tx_ack.ctrl[1] = 0x88;

    ZigduinoRadio.begin(CHANNEL,(uint8_t*)tx_hdr);
    ZigduinoRadio.setParam(phyPanId,(uint16_t)PAN_ID);
    ZigduinoRadio.setParam(phyShortAddr,(uint16_t)node_id);
    ZigduinoRadio.setParam(phyCCAMode,(uint8_t)0x3);
    Serial.begin(115200);

    Serial.print("node_id = ");
    Serial.println(node_id);

    ZigduinoRadio.attachReceiveFrame(rx_hlr);

    route_setup();
}

int okack = 0;
int noack = 0;
uint16_t counter = 0;

void loop() {
    int ret;

    if(rx.qfront != rx.qback) {
        rx_dispatch();
    }

    route_loop();

    ret = tx_state();
    if(ret == 1) {
        tx_dispatch();
    } else if(ret == 2) {
        backoff_window = 1;
        okack += 1;
        //Serial.println("OKACK");
    } else if(ret == 3) {
        backoff_window = min(backoff_window * 2,8192);
        noack += 1;
        //Serial.println("NOACK");
    }

    if(counter == 0) {
        Serial.print(okack);
        Serial.print(" ");
        Serial.println(noack);
    }
    counter += 1;
}
