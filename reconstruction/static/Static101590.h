// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101590, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101590;
extern void construct(Static101590*, const Descriptor*);
extern void destroy(Static101590*);
struct Static101590 {
    void* value;
    Static101590() { construct(this, &descriptor); }
    ~Static101590() { destroy(this); }
};
