// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24500, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24500;
extern void construct(Static24500*, const Descriptor*);
extern void destroy(Static24500*);
struct Static24500 {
    void* value;
    Static24500() { construct(this, &descriptor); }
    ~Static24500() { destroy(this); }
};
