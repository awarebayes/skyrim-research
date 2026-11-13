// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static87680, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static87680;
extern void construct(Static87680*, const Descriptor*);
extern void destroy(Static87680*);
struct Static87680 {
    void* value;
    Static87680() { construct(this, &descriptor); }
    ~Static87680() { destroy(this); }
};
