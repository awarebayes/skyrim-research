// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd570, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd570;
extern void construct(Staticd570*, const Descriptor*);
extern void destroy(Staticd570*);
struct Staticd570 {
    void* value;
    Staticd570() { construct(this, &descriptor); }
    ~Staticd570() { destroy(this); }
};
