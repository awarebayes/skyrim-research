// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1e340, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1e340;
extern void construct(Static1e340*, const Descriptor*);
extern void destroy(Static1e340*);
struct Static1e340 {
    void* value;
    Static1e340() { construct(this, &descriptor); }
    ~Static1e340() { destroy(this); }
};
