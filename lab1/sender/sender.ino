int pinR = 3;
int pinG = 5;
int pinB = 6;
int ch = 0;

int fix_one = 16658 / 2;
int base = fix_one;

int data1 = 0x0;
int data2 = 0x0;
int data3 = 0x5557;
int mixer = 0xD573;
int off = 0;
int count = 0;

char msg[2048];
char buf[2048];
int st = 0,et = 0;

void setup() {           
  pinMode(pinB,OUTPUT);
  pinMode(pinR,OUTPUT);
  pinMode(pinG,OUTPUT);
  digitalWrite(pinB,LOW);
  digitalWrite(pinR,LOW);
  digitalWrite(pinG,LOW);
  
  Serial.begin(9600);
  Serial.setTimeout(50);
  
  noInterrupts();
  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1 = 0;
  OCR1A = base - 1;
  TCCR1B = _BV(WGM12) | _BV(CS10);
  TIMSK1 = _BV(OCIE1A);
  
  TCCR3A = 0;
  TCCR3B = 0;
  TCNT3 = 0;
  OCR3A = 1023; //G
  OCR3B = 512;  //B
  OCR3C = 1023; //R
  TCCR3A = _BV(WGM30) |_BV(WGM31);
  TCCR3B = _BV(WGM32) | _BV(CS30);
  TIMSK3 = 0;
  
  interrupts();
}

ISR(TIMER1_COMPA_vect) {
  if(count == 0) {
    if(data3 == 0x55D7) {
      data3 = 0x5557;      
    } else {
      data3 = 0x55D7; 
    }
    if(st != et) {
      data1 = *(short*)&msg[st + 2];
      data2 = *(short*)&msg[st];
      st = (st + 4) & 1023;
    } else {
      data1 = 0;
      data2 = 0; 
    }
    data1 ^= mixer;
    data2 ^= mixer;
  }
  count = (count + 1) % 64;
  
  TCCR3A = (((data3 >> off) & 1) << COM3A1) | \
           (((data1 >> off) & 1) << COM3B1) | \
           (((data2 >> off) & 1) << COM3C1) | \
           _BV(WGM30) |_BV(WGM31);
  
  //digitalWrite(pinB,(data1 >> off) & 1);
  //digitalWrite(pinR,(data2 >> off) & 1);
  //digitalWrite(pinG,(data3 >> off) & 1); 
  off = (off + 1) & 15;
}

void loop() {
  int i,tmp,len;
  if(Serial.available() > 0) {
     len = Serial.readBytes(buf,2048);
     Serial.println(buf);
     
     tmp = len & 3;
     if(tmp) {
       tmp = 4 - tmp;
       for(i = 0;i < tmp;i++) {
         buf[len + i] = 0;
       }
       len += i;
     }
     
     tmp = et;
     for(i = 0;i < len;i++) {
       msg[tmp & 1023] = buf[i];
       tmp = (tmp + 1) & 1023;
     }
     et = tmp;
  }
}
