// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1af50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1af50;
extern void construct(Static1af50*, const Descriptor*);
extern void destroy(Static1af50*);
struct Static1af50 {
    void* value;
    Static1af50() { construct(this, &descriptor); }
    ~Static1af50() { destroy(this); }
};
