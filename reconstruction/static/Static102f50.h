// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static102f50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static102f50;
extern void construct(Static102f50*, const Descriptor*);
extern void destroy(Static102f50*);
struct Static102f50 {
    void* value;
    Static102f50() { construct(this, &descriptor); }
    ~Static102f50() { destroy(this); }
};
