// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1bd80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1bd80;
extern void construct(Static1bd80*, const Descriptor*);
extern void destroy(Static1bd80*);
struct Static1bd80 {
    void* value;
    Static1bd80() { construct(this, &descriptor); }
    ~Static1bd80() { destroy(this); }
};
