// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef910, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef910;
extern void construct(Staticef910*, const Descriptor*);
extern void destroy(Staticef910*);
struct Staticef910 {
    void* value;
    Staticef910() { construct(this, &descriptor); }
    ~Staticef910() { destroy(this); }
};
