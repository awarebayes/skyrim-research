// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15550, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15550;
extern void construct(Static15550*, const Descriptor*);
extern void destroy(Static15550*);
struct Static15550 {
    void* value;
    Static15550() { construct(this, &descriptor); }
    ~Static15550() { destroy(this); }
};
