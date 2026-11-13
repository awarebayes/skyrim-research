// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static80590, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static80590;
extern void construct(Static80590*, const Descriptor*);
extern void destroy(Static80590*);
struct Static80590 {
    void* value;
    Static80590() { construct(this, &descriptor); }
    ~Static80590() { destroy(this); }
};
