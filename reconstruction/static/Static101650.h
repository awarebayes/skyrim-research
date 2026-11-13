// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101650, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101650;
extern void construct(Static101650*, const Descriptor*);
extern void destroy(Static101650*);
struct Static101650 {
    void* value;
    Static101650() { construct(this, &descriptor); }
    ~Static101650() { destroy(this); }
};
