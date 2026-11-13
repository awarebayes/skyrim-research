// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice9620, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice9620;
extern void construct(Statice9620*, const Descriptor*);
extern void destroy(Statice9620*);
struct Statice9620 {
    void* value;
    Statice9620() { construct(this, &descriptor); }
    ~Statice9620() { destroy(this); }
};
