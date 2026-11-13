// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3110, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3110;
extern void construct(Statica3110*, const Descriptor*);
extern void destroy(Statica3110*);
struct Statica3110 {
    void* value;
    Statica3110() { construct(this, &descriptor); }
    ~Statica3110() { destroy(this); }
};
