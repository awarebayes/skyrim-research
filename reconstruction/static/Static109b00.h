// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109b00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109b00;
extern void construct(Static109b00*, const Descriptor*);
extern void destroy(Static109b00*);
struct Static109b00 {
    void* value;
    Static109b00() { construct(this, &descriptor); }
    ~Static109b00() { destroy(this); }
};
