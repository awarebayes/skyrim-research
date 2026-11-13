// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef850, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef850;
extern void construct(Staticef850*, const Descriptor*);
extern void destroy(Staticef850*);
struct Staticef850 {
    void* value;
    Staticef850() { construct(this, &descriptor); }
    ~Staticef850() { destroy(this); }
};
