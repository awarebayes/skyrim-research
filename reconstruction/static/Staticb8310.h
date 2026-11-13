// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb8310, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb8310;
extern void construct(Staticb8310*, const Descriptor*);
extern void destroy(Staticb8310*);
struct Staticb8310 {
    void* value;
    Staticb8310() { construct(this, &descriptor); }
    ~Staticb8310() { destroy(this); }
};
