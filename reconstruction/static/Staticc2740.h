// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc2740, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc2740;
extern void construct(Staticc2740*, const Descriptor*);
extern void destroy(Staticc2740*);
struct Staticc2740 {
    void* value;
    Staticc2740() { construct(this, &descriptor); }
    ~Staticc2740() { destroy(this); }
};
