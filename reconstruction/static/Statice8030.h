// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8030, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8030;
extern void construct(Statice8030*, const Descriptor*);
extern void destroy(Statice8030*);
struct Statice8030 {
    void* value;
    Statice8030() { construct(this, &descriptor); }
    ~Statice8030() { destroy(this); }
};
