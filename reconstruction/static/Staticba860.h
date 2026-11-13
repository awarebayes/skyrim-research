// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticba860, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticba860;
extern void construct(Staticba860*, const Descriptor*);
extern void destroy(Staticba860*);
struct Staticba860 {
    void* value;
    Staticba860() { construct(this, &descriptor); }
    ~Staticba860() { destroy(this); }
};
