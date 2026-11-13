// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static93140, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static93140;
extern void construct(Static93140*, const Descriptor*);
extern void destroy(Static93140*);
struct Static93140 {
    void* value;
    Static93140() { construct(this, &descriptor); }
    ~Static93140() { destroy(this); }
};
