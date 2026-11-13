// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1d620, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1d620;
extern void construct(Static1d620*, const Descriptor*);
extern void destroy(Static1d620*);
struct Static1d620 {
    void* value;
    Static1d620() { construct(this, &descriptor); }
    ~Static1d620() { destroy(this); }
};
