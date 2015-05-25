#include <ZigduinoRadio.h>

#define BROADCAST_ID	0xFFFF
#define NODE_ID		0x0001
#define PAN_ID		0xABCD
#define CHANNEL		26

#define DIFS		128
#define BACKOFF		4096

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

struct tx_data {
    uint8_t buffer[256];
    size_t len;
    int difs_ts;
    int backoff;
    uint8_t seq;
};
struct rx_data {
    uint8_t buffer[256];
    size_t len;
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
    struct tx_header *rx_hdr = (struct tx_header*)frm;

    if(len < (sizeof(struct tx_header) + 2)) {
	goto out;
    }

    //Remove unused HWACK
    len -= 2;

    if(rx_hdr->panid != PAN_ID) {
	goto out;
    }
    if(rx_hdr->dst_addr != NODE_ID && rx_hdr->dst_addr != BROADCAST_ID) {
	goto out;
    }
    if(get_checksum(frm,len) != 0x0) {
	goto out;
    }

    memcpy(rx.buffer,frm,len);
    rx.len = len;

out:

    return rx.buffer;
}
int rx_dispatch() {
    struct tx_header *rx_hdr = (struct tx_header*)rx.buffer;

    Serial.println(rx_hdr->src_addr);

    rx.len = 0;
    pkt_tx_ack.seq = rx_hdr->seq;
    ZigduinoRadio.txFrame((uint8_t*)&pkt_tx_ack,sizeof(pkt_tx_ack));

    return 0;
}

int tx_check() {
    int rssi = ZigduinoRadio.getRssiNow();
    int ts = micros();
    int ret = 0;

    if(rssi > -91) {
	if((ts - tx.difs_ts) > DIFS) {
	    tx.backoff -= (ts - tx.difs_ts - DIFS);
	}
	tx.difs_ts = ts;
	goto out;
    }
    if((ts - tx.difs_ts) > (DIFS + tx.backoff)) {
	tx.difs_ts = ts;
	tx.backoff = BACKOFF;
	ret = 1;
    }

out:

    return ret;
}
int tx_build(uint16_t dst_addr,uint8_t *payload,size_t len) {
    struct tx_header *tx_hdr = (struct tx_header*)tx.buffer;
    uint16_t checksum;

    tx_hdr->ctrl[0] = 0x41;
    tx_hdr->ctrl[1] = 0x88;
    tx_hdr->seq = tx.seq;
    tx_hdr->panid = PAN_ID;
    tx_hdr->dst_addr = dst_addr;
    tx_hdr->src_addr = NODE_ID;
    tx.len = sizeof(*tx_hdr);

    memcpy(tx.buffer + tx.len,payload,len);
    tx.len += len;

    checksum = get_checksum(tx.buffer,tx.len);
    memcpy(tx.buffer + tx.len,&checksum,sizeof(checksum));
    tx.len += sizeof(checksum);

    //Add unused HWACK
    tx.len += 2;

    tx.seq += 1;
    return 0;
}

void setup() {
    struct tx_header *tx_hdr;

    pinMode(13,OUTPUT);   
    digitalWrite(13,HIGH);

    tx_hdr = (struct tx_header*)tx.buffer;
    tx_hdr->ctrl[0] = 0x41;
    tx_hdr->ctrl[1] = 0x88;
    tx_hdr->seq = 0x0;
    tx_hdr->panid = PAN_ID;
    tx_hdr->dst_addr = 0x0;
    tx_hdr->src_addr = NODE_ID;
    tx.difs_ts = micros();
    tx.backoff = BACKOFF;
    tx.seq = 0;
    tx.len = 0;

    rx.len = 0;

    pkt_tx_ack.ctrl[0] = 0x42;
    pkt_tx_ack.ctrl[1] = 0x88;

    ZigduinoRadio.begin(CHANNEL,(uint8_t*)tx_hdr);
    ZigduinoRadio.setParam(phyPanId,(uint16_t)PAN_ID);
    ZigduinoRadio.setParam(phyShortAddr,(uint16_t)NODE_ID);
    ZigduinoRadio.setParam(phyCCAMode,(uint8_t)0x3);
    Serial.begin(9600);

    ZigduinoRadio.attachReceiveFrame(rx_hlr);
}
void loop() {
    if(rx.len > 0) {
	rx_dispatch();
    }else if(tx_check()) {
	tx_build((NODE_ID % 2) + 1,(uint8_t*)"Hello",5);
	ZigduinoRadio.txFrame(tx.buffer,tx.len);
    }
}
