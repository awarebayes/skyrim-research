// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc5420, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc5420;
extern void construct(Staticc5420*, const Descriptor*);
extern void destroy(Staticc5420*);
struct Staticc5420 {
    void* value;
    Staticc5420() { construct(this, &descriptor); }
    ~Staticc5420() { destroy(this); }
};
