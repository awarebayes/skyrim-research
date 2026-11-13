// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5910, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5910;
extern void construct(Staticb5910*, const Descriptor*);
extern void destroy(Staticb5910*);
struct Staticb5910 {
    void* value;
    Staticb5910() { construct(this, &descriptor); }
    ~Staticb5910() { destroy(this); }
};
