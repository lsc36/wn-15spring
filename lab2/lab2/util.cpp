#include "lab2.h"

unsigned btoi(int *seq, int st, int ed)
{
    unsigned ret = 0;
    for (int i = st; i < ed; i++) ret = (ret << 1) | seq[i];
    return ret;
}

void itob(int *seq, int st, int ed, unsigned n)
{
    for (int i = ed - 1; i >= st; i--, n >>= 1) seq[i] = n & 1;
}

int intval(char *s)
{
    int ret = 0;
    int i;
    for(i = 0;s[i] != 0;i++) {
        ret = ret * 10 + s[i] - '0';
    }
    return ret;
}
