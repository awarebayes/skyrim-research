// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7b50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7b50;
extern void construct(Staticb7b50*, const Descriptor*);
extern void destroy(Staticb7b50*);
struct Staticb7b50 {
    void* value;
    Staticb7b50() { construct(this, &descriptor); }
    ~Staticb7b50() { destroy(this); }
};
