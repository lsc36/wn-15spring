#include "lab2.h"

void WWVBSender::emit(int index, int offset)
{
    switch (this->seq[index]) {
    case 0:
        if (offset > 200) TCCR3A = _BV(COM3A0);
        else TCCR3A = 0;
        break;
    case 1:
        if (offset > 500) TCCR3A = _BV(COM3A0);
        else TCCR3A = 0;
        break;
    case 2:
        if (offset > 800) TCCR3A = _BV(COM3A0);
        else TCCR3A = 0;
    }
}

void WWVBSender::setTime(DateTime &t)
{
    itob(seq, 1, 4, t.minutes / 10); itob(seq, 5, 9, t.minutes % 10);
    itob(seq, 12, 14, t.hours / 10); itob(seq, 15, 19, t.hours % 10);
    int doy = t.getdoy();
    itob(seq, 22, 24, doy / 100); itob(seq, 25, 29, doy / 10 % 10); itob(seq, 30, 34, doy % 10);
    itob(seq, 45, 49, t.year / 10 % 10); itob(seq, 50, 54, t.year % 10);
    bool leapyear = t.year % 400 == 0 || (t.year % 100 != 0 && t.year % 4 == 0);
    itob(seq, 55, 56, leapyear);
}
