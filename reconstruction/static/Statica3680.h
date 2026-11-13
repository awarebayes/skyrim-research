// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3680, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3680;
extern void construct(Statica3680*, const Descriptor*);
extern void destroy(Statica3680*);
struct Statica3680 {
    void* value;
    Statica3680() { construct(this, &descriptor); }
    ~Statica3680() { destroy(this); }
};
