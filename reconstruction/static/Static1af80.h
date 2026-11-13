// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1af80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1af80;
extern void construct(Static1af80*, const Descriptor*);
extern void destroy(Static1af80*);
struct Static1af80 {
    void* value;
    Static1af80() { construct(this, &descriptor); }
    ~Static1af80() { destroy(this); }
};
