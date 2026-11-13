// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb8d90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb8d90;
extern void construct(Staticb8d90*, const Descriptor*);
extern void destroy(Staticb8d90*);
struct Staticb8d90 {
    void* value;
    Staticb8d90() { construct(this, &descriptor); }
    ~Staticb8d90() { destroy(this); }
};
