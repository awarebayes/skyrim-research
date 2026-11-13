// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef610, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef610;
extern void construct(Staticef610*, const Descriptor*);
extern void destroy(Staticef610*);
struct Staticef610 {
    void* value;
    Staticef610() { construct(this, &descriptor); }
    ~Staticef610() { destroy(this); }
};
