// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9f940, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9f940;
extern void construct(Static9f940*, const Descriptor*);
extern void destroy(Static9f940*);
struct Static9f940 {
    void* value;
    Static9f940() { construct(this, &descriptor); }
    ~Static9f940() { destroy(this); }
};
