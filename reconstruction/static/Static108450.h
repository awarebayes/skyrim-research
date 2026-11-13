// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108450, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108450;
extern void construct(Static108450*, const Descriptor*);
extern void destroy(Static108450*);
struct Static108450 {
    void* value;
    Static108450() { construct(this, &descriptor); }
    ~Static108450() { destroy(this); }
};
