// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6680, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6680;
extern void construct(Staticb6680*, const Descriptor*);
extern void destroy(Staticb6680*);
struct Staticb6680 {
    void* value;
    Staticb6680() { construct(this, &descriptor); }
    ~Staticb6680() { destroy(this); }
};
