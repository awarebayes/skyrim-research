// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1ab90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1ab90;
extern void construct(Static1ab90*, const Descriptor*);
extern void destroy(Static1ab90*);
struct Static1ab90 {
    void* value;
    Static1ab90() { construct(this, &descriptor); }
    ~Static1ab90() { destroy(this); }
};
