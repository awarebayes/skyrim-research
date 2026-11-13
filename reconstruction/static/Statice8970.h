// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8970, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8970;
extern void construct(Statice8970*, const Descriptor*);
extern void destroy(Statice8970*);
struct Statice8970 {
    void* value;
    Statice8970() { construct(this, &descriptor); }
    ~Statice8970() { destroy(this); }
};
