// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5b50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5b50;
extern void construct(Staticb5b50*, const Descriptor*);
extern void destroy(Staticb5b50*);
struct Staticb5b50 {
    void* value;
    Staticb5b50() { construct(this, &descriptor); }
    ~Staticb5b50() { destroy(this); }
};
