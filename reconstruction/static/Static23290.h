// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static23290, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static23290;
extern void construct(Static23290*, const Descriptor*);
extern void destroy(Static23290*);
struct Static23290 {
    void* value;
    Static23290() { construct(this, &descriptor); }
    ~Static23290() { destroy(this); }
};
