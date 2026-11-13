// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1db60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1db60;
extern void construct(Static1db60*, const Descriptor*);
extern void destroy(Static1db60*);
struct Static1db60 {
    void* value;
    Static1db60() { construct(this, &descriptor); }
    ~Static1db60() { destroy(this); }
};
