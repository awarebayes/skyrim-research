// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15970, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15970;
extern void construct(Static15970*, const Descriptor*);
extern void destroy(Static15970*);
struct Static15970 {
    void* value;
    Static15970() { construct(this, &descriptor); }
    ~Static15970() { destroy(this); }
};
