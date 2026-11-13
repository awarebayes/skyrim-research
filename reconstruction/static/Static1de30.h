// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1de30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1de30;
extern void construct(Static1de30*, const Descriptor*);
extern void destroy(Static1de30*);
struct Static1de30 {
    void* value;
    Static1de30() { construct(this, &descriptor); }
    ~Static1de30() { destroy(this); }
};
