// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static87750, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static87750;
extern void construct(Static87750*, const Descriptor*);
extern void destroy(Static87750*);
struct Static87750 {
    void* value;
    Static87750() { construct(this, &descriptor); }
    ~Static87750() { destroy(this); }
};
