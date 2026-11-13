// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24530, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24530;
extern void construct(Static24530*, const Descriptor*);
extern void destroy(Static24530*);
struct Static24530 {
    void* value;
    Static24530() { construct(this, &descriptor); }
    ~Static24530() { destroy(this); }
};
