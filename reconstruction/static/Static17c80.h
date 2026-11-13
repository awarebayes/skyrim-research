// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static17c80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static17c80;
extern void construct(Static17c80*, const Descriptor*);
extern void destroy(Static17c80*);
struct Static17c80 {
    void* value;
    Static17c80() { construct(this, &descriptor); }
    ~Static17c80() { destroy(this); }
};
