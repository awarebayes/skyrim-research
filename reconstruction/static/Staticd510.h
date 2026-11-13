// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd510, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd510;
extern void construct(Staticd510*, const Descriptor*);
extern void destroy(Staticd510*);
struct Staticd510 {
    void* value;
    Staticd510() { construct(this, &descriptor); }
    ~Staticd510() { destroy(this); }
};
