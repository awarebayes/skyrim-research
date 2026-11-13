// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf3b80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf3b80;
extern void construct(Staticf3b80*, const Descriptor*);
extern void destroy(Staticf3b80*);
struct Staticf3b80 {
    void* value;
    Staticf3b80() { construct(this, &descriptor); }
    ~Staticf3b80() { destroy(this); }
};
