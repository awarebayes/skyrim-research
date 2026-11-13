// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static12560, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static12560;
extern void construct(Static12560*, const Descriptor*);
extern void destroy(Static12560*);
struct Static12560 {
    void* value;
    Static12560() { construct(this, &descriptor); }
    ~Static12560() { destroy(this); }
};
