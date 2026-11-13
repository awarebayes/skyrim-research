// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24170, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24170;
extern void construct(Static24170*, const Descriptor*);
extern void destroy(Static24170*);
struct Static24170 {
    void* value;
    Static24170() { construct(this, &descriptor); }
    ~Static24170() { destroy(this); }
};
