// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static92260, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static92260;
extern void construct(Static92260*, const Descriptor*);
extern void destroy(Static92260*);
struct Static92260 {
    void* value;
    Static92260() { construct(this, &descriptor); }
    ~Static92260() { destroy(this); }
};
