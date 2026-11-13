// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7570, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7570;
extern void construct(Staticb7570*, const Descriptor*);
extern void destroy(Staticb7570*);
struct Staticb7570 {
    void* value;
    Staticb7570() { construct(this, &descriptor); }
    ~Staticb7570() { destroy(this); }
};
