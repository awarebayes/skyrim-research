// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticde700, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticde700;
extern void construct(Staticde700*, const Descriptor*);
extern void destroy(Staticde700*);
struct Staticde700 {
    void* value;
    Staticde700() { construct(this, &descriptor); }
    ~Staticde700() { destroy(this); }
};
