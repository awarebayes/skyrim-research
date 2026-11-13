// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3710, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3710;
extern void construct(Statica3710*, const Descriptor*);
extern void destroy(Statica3710*);
struct Statica3710 {
    void* value;
    Statica3710() { construct(this, &descriptor); }
    ~Statica3710() { destroy(this); }
};
