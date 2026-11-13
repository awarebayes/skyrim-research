// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbafe0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbafe0;
extern void construct(Staticbafe0*, const Descriptor*);
extern void destroy(Staticbafe0*);
struct Staticbafe0 {
    void* value;
    Staticbafe0() { construct(this, &descriptor); }
    ~Staticbafe0() { destroy(this); }
};
