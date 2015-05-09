#include "lab2.h"

unsigned DateTime::getdoy()
{
    unsigned monthday[] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    bool leapyear = year % 400 == 0 || (year % 100 != 0 && year % 4 == 0);
    if (leapyear) monthday[2]++;
    unsigned doy = day;
    for (int i = 1; i < this->month; i++) doy += monthday[i];
    return doy;
}

void DateTime::setdow()
{
    unsigned off, delta;
    bool leapyear = year % 400 == 0 || (year % 100 != 0 && year % 4 == 0);
    off = (year - 1900);
    delta = (off - 1) / 4 - (off - 1) / 100 + ((year - 1) - 1600) / 400;
    off = off * 365 + delta;
    unsigned monthday[] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    unsigned doy = day;
    if (leapyear) monthday[2]++;
    for (int i = 1; i < month; i++) {
        doy += monthday[i];
    }
    off = (off + doy) % 7;
    dow = off;
}
