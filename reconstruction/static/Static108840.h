// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108840, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108840;
extern void construct(Static108840*, const Descriptor*);
extern void destroy(Static108840*);
struct Static108840 {
    void* value;
    Static108840() { construct(this, &descriptor); }
    ~Static108840() { destroy(this); }
};
