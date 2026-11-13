// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticfe000, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticfe000;
extern void construct(Staticfe000*, const Descriptor*);
extern void destroy(Staticfe000*);
struct Staticfe000 {
    void* value;
    Staticfe000() { construct(this, &descriptor); }
    ~Staticfe000() { destroy(this); }
};
