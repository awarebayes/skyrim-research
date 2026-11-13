// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static80650, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static80650;
extern void construct(Static80650*, const Descriptor*);
extern void destroy(Static80650*);
struct Static80650 {
    void* value;
    Static80650() { construct(this, &descriptor); }
    ~Static80650() { destroy(this); }
};
