// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21460, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21460;
extern void construct(Static21460*, const Descriptor*);
extern void destroy(Static21460*);
struct Static21460 {
    void* value;
    Static21460() { construct(this, &descriptor); }
    ~Static21460() { destroy(this); }
};
