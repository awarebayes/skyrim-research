// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static90000, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static90000;
extern void construct(Static90000*, const Descriptor*);
extern void destroy(Static90000*);
struct Static90000 {
    void* value;
    Static90000() { construct(this, &descriptor); }
    ~Static90000() { destroy(this); }
};
