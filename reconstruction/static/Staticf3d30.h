// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf3d30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf3d30;
extern void construct(Staticf3d30*, const Descriptor*);
extern void destroy(Staticf3d30*);
struct Staticf3d30 {
    void* value;
    Staticf3d30() { construct(this, &descriptor); }
    ~Staticf3d30() { destroy(this); }
};
