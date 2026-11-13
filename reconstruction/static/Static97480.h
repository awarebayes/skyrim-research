// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97480, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97480;
extern void construct(Static97480*, const Descriptor*);
extern void destroy(Static97480*);
struct Static97480 {
    void* value;
    Static97480() { construct(this, &descriptor); }
    ~Static97480() { destroy(this); }
};
