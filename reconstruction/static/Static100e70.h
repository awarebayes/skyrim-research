// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static100e70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static100e70;
extern void construct(Static100e70*, const Descriptor*);
extern void destroy(Static100e70*);
struct Static100e70 {
    void* value;
    Static100e70() { construct(this, &descriptor); }
    ~Static100e70() { destroy(this); }
};
