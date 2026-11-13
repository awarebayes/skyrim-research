// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbdd70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbdd70;
extern void construct(Staticbdd70*, const Descriptor*);
extern void destroy(Staticbdd70*);
struct Staticbdd70 {
    void* value;
    Staticbdd70() { construct(this, &descriptor); }
    ~Staticbdd70() { destroy(this); }
};
