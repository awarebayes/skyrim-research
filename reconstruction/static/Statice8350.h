// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8350, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8350;
extern void construct(Statice8350*, const Descriptor*);
extern void destroy(Statice8350*);
struct Statice8350 {
    void* value;
    Statice8350() { construct(this, &descriptor); }
    ~Statice8350() { destroy(this); }
};
