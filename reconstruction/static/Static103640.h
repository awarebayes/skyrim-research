// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103640, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103640;
extern void construct(Static103640*, const Descriptor*);
extern void destroy(Static103640*);
struct Static103640 {
    void* value;
    Static103640() { construct(this, &descriptor); }
    ~Static103640() { destroy(this); }
};
