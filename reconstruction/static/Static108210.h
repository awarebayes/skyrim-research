// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108210, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108210;
extern void construct(Static108210*, const Descriptor*);
extern void destroy(Static108210*);
struct Static108210 {
    void* value;
    Static108210() { construct(this, &descriptor); }
    ~Static108210() { destroy(this); }
};
