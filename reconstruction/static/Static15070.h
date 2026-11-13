// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15070, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15070;
extern void construct(Static15070*, const Descriptor*);
extern void destroy(Static15070*);
struct Static15070 {
    void* value;
    Static15070() { construct(this, &descriptor); }
    ~Static15070() { destroy(this); }
};
