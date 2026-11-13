// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef820, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef820;
extern void construct(Staticef820*, const Descriptor*);
extern void destroy(Staticef820*);
struct Staticef820 {
    void* value;
    Staticef820() { construct(this, &descriptor); }
    ~Staticef820() { destroy(this); }
};
