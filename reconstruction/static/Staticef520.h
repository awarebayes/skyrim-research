// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef520, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef520;
extern void construct(Staticef520*, const Descriptor*);
extern void destroy(Staticef520*);
struct Staticef520 {
    void* value;
    Staticef520() { construct(this, &descriptor); }
    ~Staticef520() { destroy(this); }
};
