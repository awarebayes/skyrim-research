// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd5a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd5a0;
extern void construct(Staticd5a0*, const Descriptor*);
extern void destroy(Staticd5a0*);
struct Staticd5a0 {
    void* value;
    Staticd5a0() { construct(this, &descriptor); }
    ~Staticd5a0() { destroy(this); }
};
