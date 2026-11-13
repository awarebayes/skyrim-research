// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108300, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108300;
extern void construct(Static108300*, const Descriptor*);
extern void destroy(Static108300*);
struct Static108300 {
    void* value;
    Static108300() { construct(this, &descriptor); }
    ~Static108300() { destroy(this); }
};
