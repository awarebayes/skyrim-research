// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd120, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd120;
extern void construct(Staticd120*, const Descriptor*);
extern void destroy(Staticd120*);
struct Staticd120 {
    void* value;
    Staticd120() { construct(this, &descriptor); }
    ~Staticd120() { destroy(this); }
};
