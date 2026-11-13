// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21430, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21430;
extern void construct(Static21430*, const Descriptor*);
extern void destroy(Static21430*);
struct Static21430 {
    void* value;
    Static21430() { construct(this, &descriptor); }
    ~Static21430() { destroy(this); }
};
