// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8b240, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8b240;
extern void construct(Static8b240*, const Descriptor*);
extern void destroy(Static8b240*);
struct Static8b240 {
    void* value;
    Static8b240() { construct(this, &descriptor); }
    ~Static8b240() { destroy(this); }
};
