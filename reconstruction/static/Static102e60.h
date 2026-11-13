// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static102e60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static102e60;
extern void construct(Static102e60*, const Descriptor*);
extern void destroy(Static102e60*);
struct Static102e60 {
    void* value;
    Static102e60() { construct(this, &descriptor); }
    ~Static102e60() { destroy(this); }
};
