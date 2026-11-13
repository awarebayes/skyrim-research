// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24200, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24200;
extern void construct(Static24200*, const Descriptor*);
extern void destroy(Static24200*);
struct Static24200 {
    void* value;
    Static24200() { construct(this, &descriptor); }
    ~Static24200() { destroy(this); }
};
