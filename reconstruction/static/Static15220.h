// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15220, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15220;
extern void construct(Static15220*, const Descriptor*);
extern void destroy(Static15220*);
struct Static15220 {
    void* value;
    Static15220() { construct(this, &descriptor); }
    ~Static15220() { destroy(this); }
};
