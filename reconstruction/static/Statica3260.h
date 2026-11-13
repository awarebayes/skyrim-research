// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3260, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3260;
extern void construct(Statica3260*, const Descriptor*);
extern void destroy(Statica3260*);
struct Statica3260 {
    void* value;
    Statica3260() { construct(this, &descriptor); }
    ~Statica3260() { destroy(this); }
};
