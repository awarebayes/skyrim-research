// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1e370, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1e370;
extern void construct(Static1e370*, const Descriptor*);
extern void destroy(Static1e370*);
struct Static1e370 {
    void* value;
    Static1e370() { construct(this, &descriptor); }
    ~Static1e370() { destroy(this); }
};
