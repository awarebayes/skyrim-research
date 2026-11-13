// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticac900, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticac900;
extern void construct(Staticac900*, const Descriptor*);
extern void destroy(Staticac900*);
struct Staticac900 {
    void* value;
    Staticac900() { construct(this, &descriptor); }
    ~Staticac900() { destroy(this); }
};
