// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8850, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8850;
extern void construct(Statice8850*, const Descriptor*);
extern void destroy(Statice8850*);
struct Statice8850 {
    void* value;
    Statice8850() { construct(this, &descriptor); }
    ~Statice8850() { destroy(this); }
};
