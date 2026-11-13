// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static102fb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static102fb0;
extern void construct(Static102fb0*, const Descriptor*);
extern void destroy(Static102fb0*);
struct Static102fb0 {
    void* value;
    Static102fb0() { construct(this, &descriptor); }
    ~Static102fb0() { destroy(this); }
};
