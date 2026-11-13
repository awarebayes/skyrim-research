// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbdce0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbdce0;
extern void construct(Staticbdce0*, const Descriptor*);
extern void destroy(Staticbdce0*);
struct Staticbdce0 {
    void* value;
    Staticbdce0() { construct(this, &descriptor); }
    ~Staticbdce0() { destroy(this); }
};
