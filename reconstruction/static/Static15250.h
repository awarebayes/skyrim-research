// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15250, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15250;
extern void construct(Static15250*, const Descriptor*);
extern void destroy(Static15250*);
struct Static15250 {
    void* value;
    Static15250() { construct(this, &descriptor); }
    ~Static15250() { destroy(this); }
};
