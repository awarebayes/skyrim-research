// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice5170, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice5170;
extern void construct(Statice5170*, const Descriptor*);
extern void destroy(Statice5170*);
struct Statice5170 {
    void* value;
    Statice5170() { construct(this, &descriptor); }
    ~Statice5170() { destroy(this); }
};
