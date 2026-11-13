// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7910, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7910;
extern void construct(Staticb7910*, const Descriptor*);
extern void destroy(Staticb7910*);
struct Staticb7910 {
    void* value;
    Staticb7910() { construct(this, &descriptor); }
    ~Staticb7910() { destroy(this); }
};
