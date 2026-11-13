// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf5a90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf5a90;
extern void construct(Staticf5a90*, const Descriptor*);
extern void destroy(Staticf5a90*);
struct Staticf5a90 {
    void* value;
    Staticf5a90() { construct(this, &descriptor); }
    ~Staticf5a90() { destroy(this); }
};
