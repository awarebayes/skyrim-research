// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24650, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24650;
extern void construct(Static24650*, const Descriptor*);
extern void destroy(Static24650*);
struct Static24650 {
    void* value;
    Static24650() { construct(this, &descriptor); }
    ~Static24650() { destroy(this); }
};
