// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7090, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7090;
extern void construct(Staticb7090*, const Descriptor*);
extern void destroy(Staticb7090*);
struct Staticb7090 {
    void* value;
    Staticb7090() { construct(this, &descriptor); }
    ~Staticb7090() { destroy(this); }
};
