// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice4320, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice4320;
extern void construct(Statice4320*, const Descriptor*);
extern void destroy(Statice4320*);
struct Statice4320 {
    void* value;
    Statice4320() { construct(this, &descriptor); }
    ~Statice4320() { destroy(this); }
};
