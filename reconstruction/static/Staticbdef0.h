// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbdef0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbdef0;
extern void construct(Staticbdef0*, const Descriptor*);
extern void destroy(Staticbdef0*);
struct Staticbdef0 {
    void* value;
    Staticbdef0() { construct(this, &descriptor); }
    ~Staticbdef0() { destroy(this); }
};
