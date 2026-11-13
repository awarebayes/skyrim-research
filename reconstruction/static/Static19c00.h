// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static19c00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static19c00;
extern void construct(Static19c00*, const Descriptor*);
extern void destroy(Static19c00*);
struct Static19c00 {
    void* value;
    Static19c00() { construct(this, &descriptor); }
    ~Static19c00() { destroy(this); }
};
