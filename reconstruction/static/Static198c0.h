// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static198c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static198c0;
extern void construct(Static198c0*, const Descriptor*);
extern void destroy(Static198c0*);
struct Static198c0 {
    void* value;
    Static198c0() { construct(this, &descriptor); }
    ~Static198c0() { destroy(this); }
};
