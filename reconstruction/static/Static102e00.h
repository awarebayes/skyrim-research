// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static102e00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static102e00;
extern void construct(Static102e00*, const Descriptor*);
extern void destroy(Static102e00*);
struct Static102e00 {
    void* value;
    Static102e00() { construct(this, &descriptor); }
    ~Static102e00() { destroy(this); }
};
