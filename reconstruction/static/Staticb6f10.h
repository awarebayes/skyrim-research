// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6f10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6f10;
extern void construct(Staticb6f10*, const Descriptor*);
extern void destroy(Staticb6f10*);
struct Staticb6f10 {
    void* value;
    Staticb6f10() { construct(this, &descriptor); }
    ~Staticb6f10() { destroy(this); }
};
