// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefe80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefe80;
extern void construct(Staticefe80*, const Descriptor*);
extern void destroy(Staticefe80*);
struct Staticefe80 {
    void* value;
    Staticefe80() { construct(this, &descriptor); }
    ~Staticefe80() { destroy(this); }
};
