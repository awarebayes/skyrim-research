// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbddd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbddd0;
extern void construct(Staticbddd0*, const Descriptor*);
extern void destroy(Staticbddd0*);
struct Staticbddd0 {
    void* value;
    Staticbddd0() { construct(this, &descriptor); }
    ~Staticbddd0() { destroy(this); }
};
