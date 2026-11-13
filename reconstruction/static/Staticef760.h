// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef760, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef760;
extern void construct(Staticef760*, const Descriptor*);
extern void destroy(Staticef760*);
struct Staticef760 {
    void* value;
    Staticef760() { construct(this, &descriptor); }
    ~Staticef760() { destroy(this); }
};
