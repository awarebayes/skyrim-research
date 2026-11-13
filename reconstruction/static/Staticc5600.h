// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc5600, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc5600;
extern void construct(Staticc5600*, const Descriptor*);
extern void destroy(Staticc5600*);
struct Staticc5600 {
    void* value;
    Staticc5600() { construct(this, &descriptor); }
    ~Staticc5600() { destroy(this); }
};
