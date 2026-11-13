// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101020, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101020;
extern void construct(Static101020*, const Descriptor*);
extern void destroy(Static101020*);
struct Static101020 {
    void* value;
    Static101020() { construct(this, &descriptor); }
    ~Static101020() { destroy(this); }
};
