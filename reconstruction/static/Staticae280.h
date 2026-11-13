// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticae280, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticae280;
extern void construct(Staticae280*, const Descriptor*);
extern void destroy(Staticae280*);
struct Staticae280 {
    void* value;
    Staticae280() { construct(this, &descriptor); }
    ~Staticae280() { destroy(this); }
};
