// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb8f40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb8f40;
extern void construct(Staticb8f40*, const Descriptor*);
extern void destroy(Staticb8f40*);
struct Staticb8f40 {
    void* value;
    Staticb8f40() { construct(this, &descriptor); }
    ~Staticb8f40() { destroy(this); }
};
