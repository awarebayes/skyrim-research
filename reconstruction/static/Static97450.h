// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97450, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97450;
extern void construct(Static97450*, const Descriptor*);
extern void destroy(Static97450*);
struct Static97450 {
    void* value;
    Static97450() { construct(this, &descriptor); }
    ~Static97450() { destroy(this); }
};
