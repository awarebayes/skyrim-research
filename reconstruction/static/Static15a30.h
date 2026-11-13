// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15a30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15a30;
extern void construct(Static15a30*, const Descriptor*);
extern void destroy(Static15a30*);
struct Static15a30 {
    void* value;
    Static15a30() { construct(this, &descriptor); }
    ~Static15a30() { destroy(this); }
};
