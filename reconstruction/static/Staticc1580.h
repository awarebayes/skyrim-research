// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc1580, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc1580;
extern void construct(Staticc1580*, const Descriptor*);
extern void destroy(Staticc1580*);
struct Staticc1580 {
    void* value;
    Staticc1580() { construct(this, &descriptor); }
    ~Staticc1580() { destroy(this); }
};
