// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice9690, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice9690;
extern void construct(Statice9690*, const Descriptor*);
extern void destroy(Statice9690*);
struct Statice9690 {
    void* value;
    Statice9690() { construct(this, &descriptor); }
    ~Statice9690() { destroy(this); }
};
