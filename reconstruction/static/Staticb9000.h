// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9000, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9000;
extern void construct(Staticb9000*, const Descriptor*);
extern void destroy(Staticb9000*);
struct Staticb9000 {
    void* value;
    Staticb9000() { construct(this, &descriptor); }
    ~Staticb9000() { destroy(this); }
};
