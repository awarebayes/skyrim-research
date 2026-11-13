// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd870, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd870;
extern void construct(Staticd870*, const Descriptor*);
extern void destroy(Staticd870*);
struct Staticd870 {
    void* value;
    Staticd870() { construct(this, &descriptor); }
    ~Staticd870() { destroy(this); }
};
