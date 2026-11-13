// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8f940, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8f940;
extern void construct(Static8f940*, const Descriptor*);
extern void destroy(Static8f940*);
struct Static8f940 {
    void* value;
    Static8f940() { construct(this, &descriptor); }
    ~Static8f940() { destroy(this); }
};
