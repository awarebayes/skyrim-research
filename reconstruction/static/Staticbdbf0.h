// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbdbf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbdbf0;
extern void construct(Staticbdbf0*, const Descriptor*);
extern void destroy(Staticbdbf0*);
struct Staticbdbf0 {
    void* value;
    Staticbdbf0() { construct(this, &descriptor); }
    ~Staticbdbf0() { destroy(this); }
};
