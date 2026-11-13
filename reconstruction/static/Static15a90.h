// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15a90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15a90;
extern void construct(Static15a90*, const Descriptor*);
extern void destroy(Static15a90*);
struct Static15a90 {
    void* value;
    Static15a90() { construct(this, &descriptor); }
    ~Static15a90() { destroy(this); }
};
