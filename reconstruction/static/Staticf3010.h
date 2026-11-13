// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf3010, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf3010;
extern void construct(Staticf3010*, const Descriptor*);
extern void destroy(Staticf3010*);
struct Staticf3010 {
    void* value;
    Staticf3010() { construct(this, &descriptor); }
    ~Staticf3010() { destroy(this); }
};
