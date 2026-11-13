// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97720, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97720;
extern void construct(Static97720*, const Descriptor*);
extern void destroy(Static97720*);
struct Static97720 {
    void* value;
    Static97720() { construct(this, &descriptor); }
    ~Static97720() { destroy(this); }
};
