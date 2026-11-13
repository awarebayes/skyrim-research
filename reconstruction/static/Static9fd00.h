// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9fd00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9fd00;
extern void construct(Static9fd00*, const Descriptor*);
extern void destroy(Static9fd00*);
struct Static9fd00 {
    void* value;
    Static9fd00() { construct(this, &descriptor); }
    ~Static9fd00() { destroy(this); }
};
