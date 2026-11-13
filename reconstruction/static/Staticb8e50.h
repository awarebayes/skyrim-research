// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb8e50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb8e50;
extern void construct(Staticb8e50*, const Descriptor*);
extern void destroy(Staticb8e50*);
struct Staticb8e50 {
    void* value;
    Staticb8e50() { construct(this, &descriptor); }
    ~Staticb8e50() { destroy(this); }
};
