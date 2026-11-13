// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static23c60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static23c60;
extern void construct(Static23c60*, const Descriptor*);
extern void destroy(Static23c60*);
struct Static23c60 {
    void* value;
    Static23c60() { construct(this, &descriptor); }
    ~Static23c60() { destroy(this); }
};
