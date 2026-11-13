// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticddd70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticddd70;
extern void construct(Staticddd70*, const Descriptor*);
extern void destroy(Staticddd70*);
struct Staticddd70 {
    void* value;
    Staticddd70() { construct(this, &descriptor); }
    ~Staticddd70() { destroy(this); }
};
