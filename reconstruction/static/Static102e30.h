// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static102e30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static102e30;
extern void construct(Static102e30*, const Descriptor*);
extern void destroy(Static102e30*);
struct Static102e30 {
    void* value;
    Static102e30() { construct(this, &descriptor); }
    ~Static102e30() { destroy(this); }
};
