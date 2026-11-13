// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8f880, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8f880;
extern void construct(Static8f880*, const Descriptor*);
extern void destroy(Static8f880*);
struct Static8f880 {
    void* value;
    Static8f880() { construct(this, &descriptor); }
    ~Static8f880() { destroy(this); }
};
