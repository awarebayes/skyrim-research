// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103520, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103520;
extern void construct(Static103520*, const Descriptor*);
extern void destroy(Static103520*);
struct Static103520 {
    void* value;
    Static103520() { construct(this, &descriptor); }
    ~Static103520() { destroy(this); }
};
