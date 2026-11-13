// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9090, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9090;
extern void construct(Staticb9090*, const Descriptor*);
extern void destroy(Staticb9090*);
struct Staticb9090 {
    void* value;
    Staticb9090() { construct(this, &descriptor); }
    ~Staticb9090() { destroy(this); }
};
