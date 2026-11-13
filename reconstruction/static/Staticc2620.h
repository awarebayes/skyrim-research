// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc2620, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc2620;
extern void construct(Staticc2620*, const Descriptor*);
extern void destroy(Staticc2620*);
struct Staticc2620 {
    void* value;
    Staticc2620() { construct(this, &descriptor); }
    ~Staticc2620() { destroy(this); }
};
