// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3770, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3770;
extern void construct(Statica3770*, const Descriptor*);
extern void destroy(Statica3770*);
struct Statica3770 {
    void* value;
    Statica3770() { construct(this, &descriptor); }
    ~Statica3770() { destroy(this); }
};
