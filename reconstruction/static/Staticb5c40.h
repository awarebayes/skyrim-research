// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5c40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5c40;
extern void construct(Staticb5c40*, const Descriptor*);
extern void destroy(Staticb5c40*);
struct Staticb5c40 {
    void* value;
    Staticb5c40() { construct(this, &descriptor); }
    ~Staticb5c40() { destroy(this); }
};
