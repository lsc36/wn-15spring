#include <ZigduinoRadio.h>
#include "disco.h"

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
#define MAX_RETRY 5
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

#define NEIGHBOR_TABLE_SIZE 64
#define NEIGHBOR_TABLE_MASK (NEIGHBOR_TABLE_SIZE - 1)
uint32_t neighbor_lastalive[NEIGHBOR_TABLE_SIZE];

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
        // record neighbor
        if (neighbor_lastalive[rx_hdr->src_addr & NEIGHBOR_TABLE_MASK] == 0) {
            Serial.print("new neighbor ");
            Serial.println(rx_hdr->src_addr);
        }
        neighbor_lastalive[rx_hdr->src_addr & NEIGHBOR_TABLE_MASK] = micros();
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
        Serial.print("received frame from ");
        Serial.println(rx_hdr->src_addr);
        pkt_tx_ack.seq = rx_hdr->seq;
        ZigduinoRadio.txFrame((uint8_t*)&pkt_tx_ack,sizeof(pkt_tx_ack));
        //if (*(uint16_t*)&rx.buffer[qid][sizeof(tx_header)] == ROUTE_CTRL_MAGIC)
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

int disco_init() {
    int i;

    for(i = 0;i < DISCO_QLEN;i++) {
	disco_query_vec[i].target_addr = 0xFFFF;
	disco_broadcast_vec[i].target_addr = 0xFFFF;
    }
    disco_query_dispatch_idx = 0;
    disco_broadcast_dispatch_idx = 0;

    return 0;
}
int disco_query(uint16_t target_addr,uint16_t version) {
    struct disco_query query;

    query.hdr.magic = DISCO_CTRL_MAGIC;
    query.hdr.type = DISCO_CTRL_QUERY;
    query.target_addr = target_addr;
    query.version = version;

    tx_build(BROADCAST_ID,(uint8_t*)&query,sizeof(query));
    return 0;
}
int disco_broadcast(uint16_t target_addr,uint16_t version) {
    struct disco_broadcast broadcast;

    broadcast.hdr.magic = DISCO_CTRL_MAGIC;
    broadcast.hdr.type = DISCO_CTRL_QUERY;
    broadcast.target_addr = target_addr;
    broadcast.version = version;

    tx_build(BROADCAST_ID,(uint8_t*)&broadcast,sizeof(broadcast));
    return 0;
}

int disco_query_dispatch() {
    int i;
    int idx = -1;

    for(i = 0;i < DISCO_QLEN;i++) {
	disco_query_dispatch_idx = (disco_query_dispatch_idx + 1) % DISCO_QLEN;
	if(disco_query_vec[disco_query_dispatch_idx].target_addr != 0xFFFF) {
	    idx = disco_query_dispatch_idx;
	    break;
	}
    }
    if(idx == -1) {
	return -1;
    }

    disco_query(disco_query_vec[idx].target_addr,disco_query_vec[idx].version);

    return 0;
}
int disco_broadcast_dispatch() {
    int i;
    int idx = -1;

    for(i = 0;i < DISCO_QLEN;i++) {
	disco_broadcast_dispatch_idx = (disco_broadcast_dispatch_idx + 1) % DISCO_QLEN;
	if(disco_broadcast_vec[disco_broadcast_dispatch_idx].target_addr != 0xFFFF) {
	    idx = disco_broadcast_dispatch_idx;
	    break;
	}
    }
    if(idx == -1) {
	return -1;
    }

    disco_broadcast(disco_broadcast_vec[idx].target_addr,disco_broadcast_vec[idx].version);

    disco_broadcast_vec[idx].counter -= 1;
    if(disco_broadcast_vec[idx].counter <= 0) {
	disco_broadcast_vec[idx].target_addr = 0xFFFF;
    }
    return 0;
}
int disco_query_add(uint16_t target_addr,uint16_t version) {
    int i;

    for(i = 0;i < DISCO_QLEN;i++) {
	if(disco_query_vec[i].target_addr == 0xFFFF) {
	    disco_query_vec[i].target_addr = target_addr;
	    disco_query_vec[i].version = version;
	    break;
	}
    }
    if(i == DISCO_QLEN) {
	return -1;
    }
    return 0;
}
int disco_broadcast_add(uint16_t target_addr,uint16_t version) {
    int i;

    for(i = 0;i < DISCO_QLEN;i++) {
	if(disco_broadcast_vec[i].target_addr == 0xFFFF) {
	    disco_broadcast_vec[i].target_addr = target_addr;
	    disco_broadcast_vec[i].version = version;
	    break;
	}
    }
    if(i == DISCO_QLEN) {
	return -1;
    }
    return 0;
}

void setup() {
    struct tx_header *tx_hdr;

    randomSeed(analogRead(0));
    pinMode(13,OUTPUT);
    digitalWrite(13,HIGH);

    node_id = random(1, 0xFFFF);

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
    Serial.begin(9600);

    Serial.print("node_id = ");
    Serial.println(node_id);

    ZigduinoRadio.attachReceiveFrame(rx_hlr);

    for (int i = 0; i < NEIGHBOR_TABLE_SIZE; i++) neighbor_lastalive[i] = 0;
}

int okack = 0;
int noack = 0;
uint16_t counter = 0;

void loop() {
    int ret;

    if(rx.qfront != rx.qback) {
        rx_dispatch();
    }

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
