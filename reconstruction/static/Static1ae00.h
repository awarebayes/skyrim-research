// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1ae00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1ae00;
extern void construct(Static1ae00*, const Descriptor*);
extern void destroy(Static1ae00*);
struct Static1ae00 {
    void* value;
    Static1ae00() { construct(this, &descriptor); }
    ~Static1ae00() { destroy(this); }
};
