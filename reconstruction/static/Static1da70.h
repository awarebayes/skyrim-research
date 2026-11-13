// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1da70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1da70;
extern void construct(Static1da70*, const Descriptor*);
extern void destroy(Static1da70*);
struct Static1da70 {
    void* value;
    Static1da70() { construct(this, &descriptor); }
    ~Static1da70() { destroy(this); }
};
