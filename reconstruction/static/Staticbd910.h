// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbd910, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbd910;
extern void construct(Staticbd910*, const Descriptor*);
extern void destroy(Staticbd910*);
struct Staticbd910 {
    void* value;
    Staticbd910() { construct(this, &descriptor); }
    ~Staticbd910() { destroy(this); }
};
