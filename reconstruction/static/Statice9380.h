// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice9380, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice9380;
extern void construct(Statice9380*, const Descriptor*);
extern void destroy(Statice9380*);
struct Statice9380 {
    void* value;
    Statice9380() { construct(this, &descriptor); }
    ~Statice9380() { destroy(this); }
};
