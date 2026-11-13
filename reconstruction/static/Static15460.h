// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15460, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15460;
extern void construct(Static15460*, const Descriptor*);
extern void destroy(Static15460*);
struct Static15460 {
    void* value;
    Static15460() { construct(this, &descriptor); }
    ~Static15460() { destroy(this); }
};
