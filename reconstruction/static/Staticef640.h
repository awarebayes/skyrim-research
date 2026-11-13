// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef640, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef640;
extern void construct(Staticef640*, const Descriptor*);
extern void destroy(Staticef640*);
struct Staticef640 {
    void* value;
    Staticef640() { construct(this, &descriptor); }
    ~Staticef640() { destroy(this); }
};
