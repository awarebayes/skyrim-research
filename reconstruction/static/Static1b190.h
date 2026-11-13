// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1b190, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1b190;
extern void construct(Static1b190*, const Descriptor*);
extern void destroy(Static1b190*);
struct Static1b190 {
    void* value;
    Static1b190() { construct(this, &descriptor); }
    ~Static1b190() { destroy(this); }
};
