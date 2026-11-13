// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef790, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef790;
extern void construct(Staticef790*, const Descriptor*);
extern void destroy(Staticef790*);
struct Staticef790 {
    void* value;
    Staticef790() { construct(this, &descriptor); }
    ~Staticef790() { destroy(this); }
};
