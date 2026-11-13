// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static17e90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static17e90;
extern void construct(Static17e90*, const Descriptor*);
extern void destroy(Static17e90*);
struct Static17e90 {
    void* value;
    Static17e90() { construct(this, &descriptor); }
    ~Static17e90() { destroy(this); }
};
