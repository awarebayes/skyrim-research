// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21250, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21250;
extern void construct(Static21250*, const Descriptor*);
extern void destroy(Static21250*);
struct Static21250 {
    void* value;
    Static21250() { construct(this, &descriptor); }
    ~Static21250() { destroy(this); }
};
