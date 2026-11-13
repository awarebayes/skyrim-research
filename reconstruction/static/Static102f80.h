// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static102f80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static102f80;
extern void construct(Static102f80*, const Descriptor*);
extern void destroy(Static102f80*);
struct Static102f80 {
    void* value;
    Static102f80() { construct(this, &descriptor); }
    ~Static102f80() { destroy(this); }
};
