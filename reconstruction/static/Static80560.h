// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static80560, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static80560;
extern void construct(Static80560*, const Descriptor*);
extern void destroy(Static80560*);
struct Static80560 {
    void* value;
    Static80560() { construct(this, &descriptor); }
    ~Static80560() { destroy(this); }
};
