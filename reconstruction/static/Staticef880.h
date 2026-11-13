// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef880, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef880;
extern void construct(Staticef880*, const Descriptor*);
extern void destroy(Staticef880*);
struct Staticef880 {
    void* value;
    Staticef880() { construct(this, &descriptor); }
    ~Staticef880() { destroy(this); }
};
