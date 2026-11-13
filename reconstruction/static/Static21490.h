// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21490, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21490;
extern void construct(Static21490*, const Descriptor*);
extern void destroy(Static21490*);
struct Static21490 {
    void* value;
    Static21490() { construct(this, &descriptor); }
    ~Static21490() { destroy(this); }
};
