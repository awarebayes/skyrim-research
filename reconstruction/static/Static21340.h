// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21340, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21340;
extern void construct(Static21340*, const Descriptor*);
extern void destroy(Static21340*);
struct Static21340 {
    void* value;
    Static21340() { construct(this, &descriptor); }
    ~Static21340() { destroy(this); }
};
