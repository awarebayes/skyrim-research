// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static23e70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static23e70;
extern void construct(Static23e70*, const Descriptor*);
extern void destroy(Static23e70*);
struct Static23e70 {
    void* value;
    Static23e70() { construct(this, &descriptor); }
    ~Static23e70() { destroy(this); }
};
