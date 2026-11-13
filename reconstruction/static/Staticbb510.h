// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb510, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb510;
extern void construct(Staticbb510*, const Descriptor*);
extern void destroy(Staticbb510*);
struct Staticbb510 {
    void* value;
    Staticbb510() { construct(this, &descriptor); }
    ~Staticbb510() { destroy(this); }
};
