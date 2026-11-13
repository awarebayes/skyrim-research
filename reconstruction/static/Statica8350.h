// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica8350, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica8350;
extern void construct(Statica8350*, const Descriptor*);
extern void destroy(Statica8350*);
struct Statica8350 {
    void* value;
    Statica8350() { construct(this, &descriptor); }
    ~Statica8350() { destroy(this); }
};
