// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd600, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd600;
extern void construct(Staticd600*, const Descriptor*);
extern void destroy(Staticd600*);
struct Staticd600 {
    void* value;
    Staticd600() { construct(this, &descriptor); }
    ~Staticd600() { destroy(this); }
};
