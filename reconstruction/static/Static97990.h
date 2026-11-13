// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97990, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97990;
extern void construct(Static97990*, const Descriptor*);
extern void destroy(Static97990*);
struct Static97990 {
    void* value;
    Static97990() { construct(this, &descriptor); }
    ~Static97990() { destroy(this); }
};
