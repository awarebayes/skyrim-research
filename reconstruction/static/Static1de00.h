// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1de00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1de00;
extern void construct(Static1de00*, const Descriptor*);
extern void destroy(Static1de00*);
struct Static1de00 {
    void* value;
    Static1de00() { construct(this, &descriptor); }
    ~Static1de00() { destroy(this); }
};
