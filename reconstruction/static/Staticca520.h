// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca520, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca520;
extern void construct(Staticca520*, const Descriptor*);
extern void destroy(Staticca520*);
struct Staticca520 {
    void* value;
    Staticca520() { construct(this, &descriptor); }
    ~Staticca520() { destroy(this); }
};
