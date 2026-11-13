// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fdf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fdf0;
extern void construct(Static8fdf0*, const Descriptor*);
extern void destroy(Static8fdf0*);
struct Static8fdf0 {
    void* value;
    Static8fdf0() { construct(this, &descriptor); }
    ~Static8fdf0() { destroy(this); }
};
