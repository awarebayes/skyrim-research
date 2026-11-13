// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf0140, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf0140;
extern void construct(Staticf0140*, const Descriptor*);
extern void destroy(Staticf0140*);
struct Staticf0140 {
    void* value;
    Staticf0140() { construct(this, &descriptor); }
    ~Staticf0140() { destroy(this); }
};
