// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc1520, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc1520;
extern void construct(Staticc1520*, const Descriptor*);
extern void destroy(Staticc1520*);
struct Staticc1520 {
    void* value;
    Staticc1520() { construct(this, &descriptor); }
    ~Staticc1520() { destroy(this); }
};
