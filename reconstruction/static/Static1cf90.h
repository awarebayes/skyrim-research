// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1cf90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1cf90;
extern void construct(Static1cf90*, const Descriptor*);
extern void destroy(Static1cf90*);
struct Static1cf90 {
    void* value;
    Static1cf90() { construct(this, &descriptor); }
    ~Static1cf90() { destroy(this); }
};
