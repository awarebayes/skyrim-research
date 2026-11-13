// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101500, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101500;
extern void construct(Static101500*, const Descriptor*);
extern void destroy(Static101500*);
struct Static101500 {
    void* value;
    Static101500() { construct(this, &descriptor); }
    ~Static101500() { destroy(this); }
};
