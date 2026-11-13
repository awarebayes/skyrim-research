// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static100f30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static100f30;
extern void construct(Static100f30*, const Descriptor*);
extern void destroy(Static100f30*);
struct Static100f30 {
    void* value;
    Static100f30() { construct(this, &descriptor); }
    ~Static100f30() { destroy(this); }
};
