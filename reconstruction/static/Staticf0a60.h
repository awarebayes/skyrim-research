// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf0a60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf0a60;
extern void construct(Staticf0a60*, const Descriptor*);
extern void destroy(Staticf0a60*);
struct Staticf0a60 {
    void* value;
    Staticf0a60() { construct(this, &descriptor); }
    ~Staticf0a60() { destroy(this); }
};
