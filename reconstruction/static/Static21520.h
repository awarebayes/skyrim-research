// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21520, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21520;
extern void construct(Static21520*, const Descriptor*);
extern void destroy(Static21520*);
struct Static21520 {
    void* value;
    Static21520() { construct(this, &descriptor); }
    ~Static21520() { destroy(this); }
};
