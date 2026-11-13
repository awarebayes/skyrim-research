// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static102fe0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static102fe0;
extern void construct(Static102fe0*, const Descriptor*);
extern void destroy(Static102fe0*);
struct Static102fe0 {
    void* value;
    Static102fe0() { construct(this, &descriptor); }
    ~Static102fe0() { destroy(this); }
};
