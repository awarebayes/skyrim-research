// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef670, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef670;
extern void construct(Staticef670*, const Descriptor*);
extern void destroy(Staticef670*);
struct Staticef670 {
    void* value;
    Staticef670() { construct(this, &descriptor); }
    ~Staticef670() { destroy(this); }
};
