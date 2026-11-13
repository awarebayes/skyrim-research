// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticfe1b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticfe1b0;
extern void construct(Staticfe1b0*, const Descriptor*);
extern void destroy(Staticfe1b0*);
struct Staticfe1b0 {
    void* value;
    Staticfe1b0() { construct(this, &descriptor); }
    ~Staticfe1b0() { destroy(this); }
};
