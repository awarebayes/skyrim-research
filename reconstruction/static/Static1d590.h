// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1d590, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1d590;
extern void construct(Static1d590*, const Descriptor*);
extern void destroy(Static1d590*);
struct Static1d590 {
    void* value;
    Static1d590() { construct(this, &descriptor); }
    ~Static1d590() { destroy(this); }
};
