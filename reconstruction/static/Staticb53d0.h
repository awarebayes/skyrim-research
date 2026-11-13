// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb53d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb53d0;
extern void construct(Staticb53d0*, const Descriptor*);
extern void destroy(Staticb53d0*);
struct Staticb53d0 {
    void* value;
    Staticb53d0() { construct(this, &descriptor); }
    ~Staticb53d0() { destroy(this); }
};
