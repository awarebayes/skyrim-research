// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef40;
extern void construct(Staticef40*, const Descriptor*);
extern void destroy(Staticef40*);
struct Staticef40 {
    void* value;
    Staticef40() { construct(this, &descriptor); }
    ~Staticef40() { destroy(this); }
};
