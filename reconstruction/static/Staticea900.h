// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticea900, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticea900;
extern void construct(Staticea900*, const Descriptor*);
extern void destroy(Staticea900*);
struct Staticea900 {
    void* value;
    Staticea900() { construct(this, &descriptor); }
    ~Staticea900() { destroy(this); }
};
