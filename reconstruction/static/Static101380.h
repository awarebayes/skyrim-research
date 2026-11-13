// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101380, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101380;
extern void construct(Static101380*, const Descriptor*);
extern void destroy(Static101380*);
struct Static101380 {
    void* value;
    Static101380() { construct(this, &descriptor); }
    ~Static101380() { destroy(this); }
};
