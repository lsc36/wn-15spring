#include "lab2.h"

JJYSender JJY;
WWVBSender WWVB;
SignalSender *sender;

void increment(DateTime &t)
{
    int monthday[] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    bool leapyear = t.year % 400 == 0 || (t.year % 100 != 0 && t.year % 4 == 0);
    if (leapyear) monthday[2]++;
    t.minutes = (t.minutes + 1) % 60;
    if (t.minutes != 0) goto finish;
    t.hours = (t.hours + 1) % 24;
    if (t.hours != 0) goto finish;
    t.dow = (t.dow + 1) % 7;
    t.day = t.day % monthday[t.month] + 1;
    if (t.day != 1) goto finish;
    t.month = t.month % 12 + 1;
    if (t.month != 1) goto finish;
    t.year = t.year + 1;
finish:
    sender->setTime(t);
}

DateTime datetime = (DateTime){2015, 4, 15, 20, 0, 3};

void printTime()
{
    Serial.print("Current time is: ");
    switch (datetime.dow) {
    case 0: Serial.print("Sun "); break;
    case 1: Serial.print("Mon "); break;
    case 2: Serial.print("Tue "); break;
    case 3: Serial.print("Wed "); break;
    case 4: Serial.print("Thu "); break;
    case 5: Serial.print("Fri "); break;
    case 6: Serial.print("Sat ");
    }
    if (datetime.year < 10) Serial.print("0");
    Serial.print(datetime.year); Serial.print("/");
    if (datetime.month < 10) Serial.print("0");
    Serial.print(datetime.month); Serial.print("/");
    if (datetime.day < 10) Serial.print("0");
    Serial.print(datetime.day); Serial.print(" ");
    if (datetime.hours < 10) Serial.print("0");
    Serial.print(datetime.hours); Serial.print(":");
    if (datetime.minutes < 10) Serial.print("0");
    Serial.print(datetime.minutes); Serial.print(" ");
    if (sender == &JJY) Serial.print("(JJY)");
    else Serial.print("(WWVB)");
    Serial.println();
}

void setup()
{
    sender = &JJY;
    sender->setTime(datetime);
    pinMode(5, OUTPUT);
    TCCR3A = 0;
    TCCR3B = _BV(WGM32) | _BV(CS30);
    OCR3A = 133;  // 60kHz
    //OCR3A = 200;  // 40kHz
    Serial.begin(9600);
}

int lastindex = 59;
unsigned start = 0;
char str[128];

void loop()
{
    unsigned year,month,day;
    unsigned leapyear,off,delta;

    if(Serial.available()) {
        Serial.readBytes(str,128);
        str[4] = 0;
        str[7] = 0;
        str[10] = 0;
        str[13] = 0;
        str[16] = 0;

        datetime.year = intval(str + 0);
        datetime.month = intval(str + 5);
        datetime.day = intval(str + 8);
        datetime.hours = intval(str + 11);
        datetime.minutes = intval(str + 14);
        datetime.setdow();

        switch (str[17]) {
            case 'J': sender = &JJY; break;
            case 'W': sender = &WWVB; break;
        }
        sender->setTime(datetime);

        printTime();
        start = millis();
        lastindex = 0;
    }

    unsigned long time = millis();
    int index = ((time - start) / 1000) % 60, offset = (time - start) % 1000;
    if (index == 0 && lastindex != index) {
        increment(datetime);
        printTime();
    }
    sender->emit(index, offset);
    lastindex = index;
}
