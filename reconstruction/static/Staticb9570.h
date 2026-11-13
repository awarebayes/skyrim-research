// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9570, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9570;
extern void construct(Staticb9570*, const Descriptor*);
extern void destroy(Staticb9570*);
struct Staticb9570 {
    void* value;
    Staticb9570() { construct(this, &descriptor); }
    ~Staticb9570() { destroy(this); }
};
