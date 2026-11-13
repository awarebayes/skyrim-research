// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5820, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5820;
extern void construct(Staticb5820*, const Descriptor*);
extern void destroy(Staticb5820*);
struct Staticb5820 {
    void* value;
    Staticb5820() { construct(this, &descriptor); }
    ~Staticb5820() { destroy(this); }
};
