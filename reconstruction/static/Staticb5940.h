// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5940, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5940;
extern void construct(Staticb5940*, const Descriptor*);
extern void destroy(Staticb5940*);
struct Staticb5940 {
    void* value;
    Staticb5940() { construct(this, &descriptor); }
    ~Staticb5940() { destroy(this); }
};
