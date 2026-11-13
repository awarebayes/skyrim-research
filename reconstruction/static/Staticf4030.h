// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf4030, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf4030;
extern void construct(Staticf4030*, const Descriptor*);
extern void destroy(Staticf4030*);
struct Staticf4030 {
    void* value;
    Staticf4030() { construct(this, &descriptor); }
    ~Staticf4030() { destroy(this); }
};
