// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108000, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108000;
extern void construct(Static108000*, const Descriptor*);
extern void destroy(Static108000*);
struct Static108000 {
    void* value;
    Static108000() { construct(this, &descriptor); }
    ~Static108000() { destroy(this); }
};
