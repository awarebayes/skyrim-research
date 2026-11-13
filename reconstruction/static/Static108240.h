// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108240, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108240;
extern void construct(Static108240*, const Descriptor*);
extern void destroy(Static108240*);
struct Static108240 {
    void* value;
    Static108240() { construct(this, &descriptor); }
    ~Static108240() { destroy(this); }
};
