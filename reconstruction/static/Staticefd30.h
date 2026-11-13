// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefd30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefd30;
extern void construct(Staticefd30*, const Descriptor*);
extern void destroy(Staticefd30*);
struct Staticefd30 {
    void* value;
    Staticefd30() { construct(this, &descriptor); }
    ~Staticefd30() { destroy(this); }
};
