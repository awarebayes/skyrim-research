// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24050, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24050;
extern void construct(Static24050*, const Descriptor*);
extern void destroy(Static24050*);
struct Static24050 {
    void* value;
    Static24050() { construct(this, &descriptor); }
    ~Static24050() { destroy(this); }
};
