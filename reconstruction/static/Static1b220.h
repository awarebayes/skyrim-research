// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1b220, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1b220;
extern void construct(Static1b220*, const Descriptor*);
extern void destroy(Static1b220*);
struct Static1b220 {
    void* value;
    Static1b220() { construct(this, &descriptor); }
    ~Static1b220() { destroy(this); }
};
