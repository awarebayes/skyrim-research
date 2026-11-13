// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static90090, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static90090;
extern void construct(Static90090*, const Descriptor*);
extern void destroy(Static90090*);
struct Static90090 {
    void* value;
    Static90090() { construct(this, &descriptor); }
    ~Static90090() { destroy(this); }
};
