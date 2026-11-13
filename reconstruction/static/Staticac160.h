// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticac160, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticac160;
extern void construct(Staticac160*, const Descriptor*);
extern void destroy(Staticac160*);
struct Staticac160 {
    void* value;
    Staticac160() { construct(this, &descriptor); }
    ~Staticac160() { destroy(this); }
};
