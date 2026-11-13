// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb3d40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb3d40;
extern void construct(Staticb3d40*, const Descriptor*);
extern void destroy(Staticb3d40*);
struct Staticb3d40 {
    void* value;
    Staticb3d40() { construct(this, &descriptor); }
    ~Staticb3d40() { destroy(this); }
};
