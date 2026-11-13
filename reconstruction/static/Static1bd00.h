// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1bd00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1bd00;
extern void construct(Static1bd00*, const Descriptor*);
extern void destroy(Static1bd00*);
struct Static1bd00 {
    void* value;
    Static1bd00() { construct(this, &descriptor); }
    ~Static1bd00() { destroy(this); }
};
