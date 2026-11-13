// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static10460, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static10460;
extern void construct(Static10460*, const Descriptor*);
extern void destroy(Static10460*);
struct Static10460 {
    void* value;
    Static10460() { construct(this, &descriptor); }
    ~Static10460() { destroy(this); }
};
