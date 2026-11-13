// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticacd20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticacd20;
extern void construct(Staticacd20*, const Descriptor*);
extern void destroy(Staticacd20*);
struct Staticacd20 {
    void* value;
    Staticacd20() { construct(this, &descriptor); }
    ~Staticacd20() { destroy(this); }
};
