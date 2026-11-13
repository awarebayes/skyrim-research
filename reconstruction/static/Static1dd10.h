// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1dd10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1dd10;
extern void construct(Static1dd10*, const Descriptor*);
extern void destroy(Static1dd10*);
struct Static1dd10 {
    void* value;
    Static1dd10() { construct(this, &descriptor); }
    ~Static1dd10() { destroy(this); }
};
