// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefd90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefd90;
extern void construct(Staticefd90*, const Descriptor*);
extern void destroy(Staticefd90*);
struct Staticefd90 {
    void* value;
    Staticefd90() { construct(this, &descriptor); }
    ~Staticefd90() { destroy(this); }
};
