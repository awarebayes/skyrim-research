// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6b50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6b50;
extern void construct(Staticb6b50*, const Descriptor*);
extern void destroy(Staticb6b50*);
struct Staticb6b50 {
    void* value;
    Staticb6b50() { construct(this, &descriptor); }
    ~Staticb6b50() { destroy(this); }
};
