// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static17d40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static17d40;
extern void construct(Static17d40*, const Descriptor*);
extern void destroy(Static17d40*);
struct Static17d40 {
    void* value;
    Static17d40() { construct(this, &descriptor); }
    ~Static17d40() { destroy(this); }
};
