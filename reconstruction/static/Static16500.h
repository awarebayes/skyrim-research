// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static16500, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static16500;
extern void construct(Static16500*, const Descriptor*);
extern void destroy(Static16500*);
struct Static16500 {
    void* value;
    Static16500() { construct(this, &descriptor); }
    ~Static16500() { destroy(this); }
};
