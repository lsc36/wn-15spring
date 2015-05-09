#ifndef __LAB2_H_
#define __LAB2_H_

#include <Arduino.h>

class DateTime
{
public:
    unsigned year;
    unsigned month;
    unsigned day;
    unsigned hours;
    unsigned minutes;
    unsigned dow;
    unsigned getdoy();
    void setdow();
};

class SignalSender
{
public:
    virtual void emit(int index, int offset) = 0;
    virtual void setTime(DateTime &t) = 0;
};

class JJYSender: public SignalSender
{
private:
    int seq[60] = {
2,0,0,0,0,0,0,0,0,2,
0,0,0,0,0,0,0,0,0,2,
0,0,0,0,0,0,0,0,0,2,
0,0,0,0,0,0,0,0,0,2,
0,0,0,0,0,0,0,0,0,2,
0,0,0,0,0,0,0,0,0,2
};
public:
    void emit(int index, int offset);
    void setTime(DateTime &t);
};

class WWVBSender: public SignalSender
{
private:
    int seq[60] = {
2,0,0,0,0,0,0,0,0,2,
0,0,0,0,0,0,0,0,0,2,
0,0,0,0,0,0,0,0,0,2,
0,0,0,0,0,0,0,0,0,2,
0,0,0,0,0,0,0,0,0,2,
0,0,0,0,0,0,0,0,0,2
};
public:
    void emit(int index, int offset);
    void setTime(DateTime &t);
};

unsigned btoi(int *seq, int st, int ed);
void itob(int *seq, int st, int ed, unsigned n);
int intval(char *s);

#endif
