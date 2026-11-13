// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8880, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8880;
extern void construct(Statice8880*, const Descriptor*);
extern void destroy(Statice8880*);
struct Statice8880 {
    void* value;
    Statice8880() { construct(this, &descriptor); }
    ~Statice8880() { destroy(this); }
};
