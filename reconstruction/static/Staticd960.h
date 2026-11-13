// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd960, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd960;
extern void construct(Staticd960*, const Descriptor*);
extern void destroy(Staticd960*);
struct Staticd960 {
    void* value;
    Staticd960() { construct(this, &descriptor); }
    ~Staticd960() { destroy(this); }
};
