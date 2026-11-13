// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8b720, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8b720;
extern void construct(Static8b720*, const Descriptor*);
extern void destroy(Static8b720*);
struct Static8b720 {
    void* value;
    Static8b720() { construct(this, &descriptor); }
    ~Static8b720() { destroy(this); }
};
