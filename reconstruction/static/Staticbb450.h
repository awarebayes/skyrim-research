// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb450, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb450;
extern void construct(Staticbb450*, const Descriptor*);
extern void destroy(Staticbb450*);
struct Staticbb450 {
    void* value;
    Staticbb450() { construct(this, &descriptor); }
    ~Staticbb450() { destroy(this); }
};
