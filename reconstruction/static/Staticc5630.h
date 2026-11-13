// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc5630, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc5630;
extern void construct(Staticc5630*, const Descriptor*);
extern void destroy(Staticc5630*);
struct Staticc5630 {
    void* value;
    Staticc5630() { construct(this, &descriptor); }
    ~Staticc5630() { destroy(this); }
};
