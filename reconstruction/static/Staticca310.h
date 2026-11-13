// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca310, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca310;
extern void construct(Staticca310*, const Descriptor*);
extern void destroy(Staticca310*);
struct Staticca310 {
    void* value;
    Staticca310() { construct(this, &descriptor); }
    ~Staticca310() { destroy(this); }
};
