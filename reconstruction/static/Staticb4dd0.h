// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb4dd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb4dd0;
extern void construct(Staticb4dd0*, const Descriptor*);
extern void destroy(Staticb4dd0*);
struct Staticb4dd0 {
    void* value;
    Staticb4dd0() { construct(this, &descriptor); }
    ~Staticb4dd0() { destroy(this); }
};
