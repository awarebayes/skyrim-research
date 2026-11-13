// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd300, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd300;
extern void construct(Staticd300*, const Descriptor*);
extern void destroy(Staticd300*);
struct Staticd300 {
    void* value;
    Staticd300() { construct(this, &descriptor); }
    ~Staticd300() { destroy(this); }
};
