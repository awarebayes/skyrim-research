// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static102ec0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static102ec0;
extern void construct(Static102ec0*, const Descriptor*);
extern void destroy(Static102ec0*);
struct Static102ec0 {
    void* value;
    Static102ec0() { construct(this, &descriptor); }
    ~Static102ec0() { destroy(this); }
};
