// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fb20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fb20;
extern void construct(Static8fb20*, const Descriptor*);
extern void destroy(Static8fb20*);
struct Static8fb20 {
    void* value;
    Static8fb20() { construct(this, &descriptor); }
    ~Static8fb20() { destroy(this); }
};
