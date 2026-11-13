// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109dd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109dd0;
extern void construct(Static109dd0*, const Descriptor*);
extern void destroy(Static109dd0*);
struct Static109dd0 {
    void* value;
    Static109dd0() { construct(this, &descriptor); }
    ~Static109dd0() { destroy(this); }
};
