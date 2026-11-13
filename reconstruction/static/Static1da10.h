// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1da10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1da10;
extern void construct(Static1da10*, const Descriptor*);
extern void destroy(Static1da10*);
struct Static1da10 {
    void* value;
    Static1da10() { construct(this, &descriptor); }
    ~Static1da10() { destroy(this); }
};
