// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica0a20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica0a20;
extern void construct(Statica0a20*, const Descriptor*);
extern void destroy(Statica0a20*);
struct Statica0a20 {
    void* value;
    Statica0a20() { construct(this, &descriptor); }
    ~Statica0a20() { destroy(this); }
};
