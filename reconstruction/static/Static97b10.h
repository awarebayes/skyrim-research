// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97b10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97b10;
extern void construct(Static97b10*, const Descriptor*);
extern void destroy(Static97b10*);
struct Static97b10 {
    void* value;
    Static97b10() { construct(this, &descriptor); }
    ~Static97b10() { destroy(this); }
};
