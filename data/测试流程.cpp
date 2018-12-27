//test nesting define

#ifndef x
    #define x
    #ifdef y
        #define z 4
        #undef x
    #else
        #define z 5
    #endif
#endif