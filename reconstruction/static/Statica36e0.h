// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica36e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica36e0;
extern void construct(Statica36e0*, const Descriptor*);
extern void destroy(Statica36e0*);
struct Statica36e0 {
    void* value;
    Statica36e0() { construct(this, &descriptor); }
    ~Statica36e0() { destroy(this); }
};
