#ifdef MC1
    #ifdef MC2
        #define x 1
    #else
        #define x 2
    #endif //end MC2
#else
    #ifdef MC2
        #define x 3
    #else
        #define x 4
    #endif //end MC2
#endif //MC1