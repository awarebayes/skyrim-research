// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8af10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8af10;
extern void construct(Static8af10*, const Descriptor*);
extern void destroy(Static8af10*);
struct Static8af10 {
    void* value;
    Static8af10() { construct(this, &descriptor); }
    ~Static8af10() { destroy(this); }
};
