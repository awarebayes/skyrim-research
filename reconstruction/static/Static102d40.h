// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static102d40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static102d40;
extern void construct(Static102d40*, const Descriptor*);
extern void destroy(Static102d40*);
struct Static102d40 {
    void* value;
    Static102d40() { construct(this, &descriptor); }
    ~Static102d40() { destroy(this); }
};
