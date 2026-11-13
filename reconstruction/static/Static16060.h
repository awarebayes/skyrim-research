// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static16060, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static16060;
extern void construct(Static16060*, const Descriptor*);
extern void destroy(Static16060*);
struct Static16060 {
    void* value;
    Static16060() { construct(this, &descriptor); }
    ~Static16060() { destroy(this); }
};
