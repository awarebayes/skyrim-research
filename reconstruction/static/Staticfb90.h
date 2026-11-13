// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticfb90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticfb90;
extern void construct(Staticfb90*, const Descriptor*);
extern void destroy(Staticfb90*);
struct Staticfb90 {
    void* value;
    Staticfb90() { construct(this, &descriptor); }
    ~Staticfb90() { destroy(this); }
};
