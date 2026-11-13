// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5a30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5a30;
extern void construct(Staticb5a30*, const Descriptor*);
extern void destroy(Staticb5a30*);
struct Staticb5a30 {
    void* value;
    Staticb5a30() { construct(this, &descriptor); }
    ~Staticb5a30() { destroy(this); }
};
