// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15640, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15640;
extern void construct(Static15640*, const Descriptor*);
extern void destroy(Static15640*);
struct Static15640 {
    void* value;
    Static15640() { construct(this, &descriptor); }
    ~Static15640() { destroy(this); }
};
