// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7630, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7630;
extern void construct(Staticb7630*, const Descriptor*);
extern void destroy(Staticb7630*);
struct Staticb7630 {
    void* value;
    Staticb7630() { construct(this, &descriptor); }
    ~Staticb7630() { destroy(this); }
};
