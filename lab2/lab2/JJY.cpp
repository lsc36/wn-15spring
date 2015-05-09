#include "lab2.h"

void JJYSender::emit(int index, int offset)
{
    switch (seq[index]) {
    case 0:
        if (offset < 800) TCCR3A = _BV(COM3A0);
        else TCCR3A = 0;
        break;
    case 1:
        if (offset < 500) TCCR3A = _BV(COM3A0);
        else TCCR3A = 0;
        break;
    case 2:
        if (offset < 200) TCCR3A = _BV(COM3A0);
        else TCCR3A = 0;
    }
}

void JJYSender::setTime(DateTime &t)
{
    itob(seq, 1, 4, t.minutes / 10); itob(seq, 5, 9, t.minutes % 10);
    itob(seq, 12, 14, t.hours / 10); itob(seq, 15, 19, t.hours % 10);
    int doy = t.getdoy();
    itob(seq, 22, 24, doy / 100); itob(seq, 25, 29, doy / 10 % 10); itob(seq, 30, 34, doy % 10);
    itob(seq, 41, 45, t.year / 10 % 10); itob(seq, 45, 49, t.year % 10);
    itob(seq, 50, 53, t.dow);
    // parity
    seq[36] = seq[12] ^ seq[13] ^ seq[14] ^ seq[15] ^ seq[16] ^ seq[17] ^ seq[18];
    seq[37] = seq[1] ^ seq[2] ^ seq[3] ^ seq[4] ^ seq[5] ^ seq[6] ^ seq[7] ^ seq[8];
}
