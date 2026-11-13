// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef460, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef460;
extern void construct(Staticef460*, const Descriptor*);
extern void destroy(Staticef460*);
struct Staticef460 {
    void* value;
    Staticef460() { construct(this, &descriptor); }
    ~Staticef460() { destroy(this); }
};
