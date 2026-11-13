// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static23a20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static23a20;
extern void construct(Static23a20*, const Descriptor*);
extern void destroy(Static23a20*);
struct Static23a20 {
    void* value;
    Static23a20() { construct(this, &descriptor); }
    ~Static23a20() { destroy(this); }
};
