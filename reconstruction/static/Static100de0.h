// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static100de0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static100de0;
extern void construct(Static100de0*, const Descriptor*);
extern void destroy(Static100de0*);
struct Static100de0 {
    void* value;
    Static100de0() { construct(this, &descriptor); }
    ~Static100de0() { destroy(this); }
};
