// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109f50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109f50;
extern void construct(Static109f50*, const Descriptor*);
extern void destroy(Static109f50*);
struct Static109f50 {
    void* value;
    Static109f50() { construct(this, &descriptor); }
    ~Static109f50() { destroy(this); }
};
