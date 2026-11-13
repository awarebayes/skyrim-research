// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb420, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb420;
extern void construct(Staticbb420*, const Descriptor*);
extern void destroy(Staticbb420*);
struct Staticbb420 {
    void* value;
    Staticbb420() { construct(this, &descriptor); }
    ~Staticbb420() { destroy(this); }
};
