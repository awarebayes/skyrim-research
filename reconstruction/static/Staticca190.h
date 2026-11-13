// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca190, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca190;
extern void construct(Staticca190*, const Descriptor*);
extern void destroy(Staticca190*);
struct Staticca190 {
    void* value;
    Staticca190() { construct(this, &descriptor); }
    ~Staticca190() { destroy(this); }
};
