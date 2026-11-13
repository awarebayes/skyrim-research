// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15c10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15c10;
extern void construct(Static15c10*, const Descriptor*);
extern void destroy(Static15c10*);
struct Static15c10 {
    void* value;
    Static15c10() { construct(this, &descriptor); }
    ~Static15c10() { destroy(this); }
};
