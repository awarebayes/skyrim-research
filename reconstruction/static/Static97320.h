// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97320, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97320;
extern void construct(Static97320*, const Descriptor*);
extern void destroy(Static97320*);
struct Static97320 {
    void* value;
    Static97320() { construct(this, &descriptor); }
    ~Static97320() { destroy(this); }
};
