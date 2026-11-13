// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc1700, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc1700;
extern void construct(Staticc1700*, const Descriptor*);
extern void destroy(Staticc1700*);
struct Staticc1700 {
    void* value;
    Staticc1700() { construct(this, &descriptor); }
    ~Staticc1700() { destroy(this); }
};
