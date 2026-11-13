// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24410, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24410;
extern void construct(Static24410*, const Descriptor*);
extern void destroy(Static24410*);
struct Static24410 {
    void* value;
    Static24410() { construct(this, &descriptor); }
    ~Static24410() { destroy(this); }
};
