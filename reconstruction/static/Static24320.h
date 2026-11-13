// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24320, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24320;
extern void construct(Static24320*, const Descriptor*);
extern void destroy(Static24320*);
struct Static24320 {
    void* value;
    Static24320() { construct(this, &descriptor); }
    ~Static24320() { destroy(this); }
};
